"""Check this graph-theory edition's served bytes and optional live reader controls."""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from audit_public import ROOT, public_files


def fetch(url):
    request = Request(url, headers={'User-Agent': 'Algebraic-graph-notes-check/1.0',
                                    'Cache-Control': 'no-cache'})
    with urlopen(request, timeout=40) as response:
        return response.read()


def browser_checks(base):
    from playwright.sync_api import sync_playwright
    temporary = ROOT / 'work' / 'publication-browser'
    temporary.mkdir(parents=True, exist_ok=True)
    os.environ.update(TEMP=str(temporary), TMP=str(temporary))
    tempfile.tempdir = str(temporary)
    chapters = sorted(ROOT.glob('chapter-??-*.html'))
    if not chapters:
        raise ValueError('No authored chapters')
    selected = dict.fromkeys([chapters[0].name, chapters[len(chapters)//2].name,
                              chapters[-1].name])
    pages = ['index.html', *selected, 'numerical-lab.html']
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE') or None,
            headless=True, args=['--disable-gpu'])
        for width in (1440, 390):
            context = browser.new_context(viewport={'width': width, 'height': 1000})
            for filename in pages:
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda error: errors.append(str(error)))
                response = page.goto(base+filename)
                page.wait_for_function('!window.MathJax || !!MathJax.startup?.promise')
                page.evaluate('async () => {if(window.MathJax) await MathJax.startup.promise}')
                count = page.locator('mjx-container').count()
                math_errors = page.locator('mjx-merror,[data-mml-node="merror"]').count()
                overflow = page.evaluate('document.documentElement.scrollWidth > innerWidth+2')
                page.locator('#theme-toggle').click()
                theme = page.locator('body.light').count() == 1
                page.locator('#theme-toggle').click()
                page.locator('#text-toggle').click()
                text = page.locator('body.large-text').count() == 1
                page.locator('#text-toggle').click()
                page.locator('#solutions-toggle').click()
                solutions = (page.locator('article details').count()
                             == page.locator('article details[open]').count())
                page.locator('#solutions-toggle').click()
                extra = True
                if filename == 'index.html':
                    page.locator('#lecture-search').fill('hypercubes')
                    extra = page.locator('[data-lecture]:visible').count() == 1
                    page.locator('#lecture-search').fill('')
                if filename == 'numerical-lab.html':
                    extra = page.locator('#lab-tree-count').inner_text() == '8'
                    page.locator('#edge-2-4').uncheck()
                    extra = extra and page.locator('#lab-tree-count').inner_text() == '0'
                    page.locator('#lab-reset').click()
                    page.locator('#edge-0-2').uncheck()
                    extra = extra and page.locator('#lab-tree-count').inner_text() == '4'
                    page.locator('#lab-reset').click()
                needs_math = filename.startswith('chapter-')
                passed = (response is not None and response.status == 200 and not errors
                          and not overflow and not math_errors
                          and (not needs_math or count > 0)
                          and all((theme, text, solutions, extra)))
                results.append({'page': filename, 'width': width, 'passed': passed,
                    'math_count': count, 'math_errors': math_errors, 'javascript_errors': errors,
                    'horizontal_overflow': overflow, 'theme': theme, 'text_size': text,
                    'solutions': solutions, 'page_specific_controls': extra})
                page.close()
            context.close()
        browser.close()
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True, help='This course GitHub Pages base URL')
    parser.add_argument('--repo', required=True, help='This course GitHub repository URL')
    parser.add_argument('--browser', action='store_true', help='Run hidden desktop/mobile checks')
    parser.add_argument('--bootstrap', action='store_true', help='Permit an existing pending served report on the first deployment only')
    args = parser.parse_args()
    base = args.base.rstrip('/')+'/'
    if not (base.startswith('https://') and args.repo.startswith('https://github.com/')):
        raise ValueError('Use explicit HTTPS publication URLs')
    repository_name = urlparse(args.repo).path.rstrip('/').split('/')[-1]
    if urlparse(base).path.rstrip('/').split('/')[-1] != repository_name:
        raise ValueError('Repository and project-Pages path disagree')
    exclusions = {'publication-validation.json':
        'A report cannot contain a verifiable hash of itself; existence and JSON shape are checked separately.'}
    records = []
    for path in public_files(release=True):
        relative = path.relative_to(ROOT).as_posix()
        if relative in exclusions:
            continue
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        error, actual = None, None
        for attempt in range(3):
            try:
                actual = hashlib.sha256(fetch(base+quote(relative))).hexdigest()
                if actual == expected:
                    break
                error = 'served bytes differ'
            except Exception as exception:
                error = str(exception)
            if attempt < 2:
                time.sleep(2)
        records.append({'path': relative, 'sha256': expected, 'served_sha256': actual,
                        'passed': actual == expected,
                        'error': None if actual == expected else error})
    # The self-hash exclusion must never hide a missing served report.
    report_present, served_report_passed, report_error = False, False, None
    try:
        existing = json.loads(fetch(base+'publication-validation.json'))
        report_present = isinstance(existing, dict) and isinstance(existing.get('passed'), bool)
        served_report_passed = report_present and existing.get('passed') is True
    except Exception as exception:
        report_error = str(exception)
    reader = browser_checks(base) if args.browser else []
    preview_error, preview = None, False
    try:
        readme = (ROOT/'README.md').read_text(encoding='utf-8')
        match = re.search(r'!\[([^\]]+)\]\(assets/site-preview\.png\)', readme)
        if match is None:
            raise ValueError('README has no local site-preview image')
        document = BeautifulSoup(fetch(args.repo), 'html.parser')
        for image in document.find_all('img', alt=match[1]):
            link = image.find_parent('a')
            if link and link.get('href', '').rstrip('/')+'/' == base:
                preview = True
    except Exception as exception:
        preview_error = str(exception)
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    passed = (bool(records) and all(row['passed'] for row in records)
              and report_present and (args.bootstrap or served_report_passed)
              and preview and all(row['passed'] for row in reader))
    report = {'passed': passed,
        'checked_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'base_url': base, 'repository_url': args.repo, 'payload_commit': commit,
        'served_file_count': len(records), 'files': records,
        'excluded_from_served_hashes': exclusions,
        'served_report_exists_and_is_json': report_present,
        'served_report_passed': served_report_passed, 'bootstrap_probe': args.bootstrap,
        'served_report_error': report_error, 'browser_checks_requested': args.browser,
        'live_reader': reader, 'github_readme_preview_links_to_book': preview,
        'preview_error': preview_error,
        'scope': 'Exact public payload bytes (including completion.json), served-report presence, '
                 'rendered GitHub README preview/link, and representative hidden browser checks '
                 'only when --browser is selected. No new mathematical or audiovisual review.'}
    (ROOT/'publication-validation.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Publication:', passed, '; served files:', len(records), '; reader checks:', len(reader))
    if not passed:
        print(json.dumps({'files': [row for row in records if not row['passed']],
                          'reader': [row for row in reader if not row['passed']],
                          'report_present': report_present, 'report_error': report_error,
                          'preview': preview, 'preview_error': preview_error}, indent=2))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
