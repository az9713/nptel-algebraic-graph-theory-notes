"""Enumerate the explicit public package and reject private paths or source media."""
from __future__ import annotations

import hashlib
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {
    '.gitattributes', '.gitignore', '.nojekyll', 'README.md', 'WORKFLOW.md',
    'book-overview.html', 'index.html', 'references.html', 'source-map.html',
    'numerical-lab.html', 'numerical_lab.py', 'requirements.txt',
    'source-manifest.json', 'source-map.json', 'source-validation-summary.json',
    'content-inventory.json', 'completion.json', 'editorial-review-summary.json',
    'course-review.json', 'chapter-code-validation.json', 'reader-validation.json',
    'package-validation.json', 'public-package-validation.json',
    'source-free-validation.json', 'publication-validation.json',
}
CODE_FILES = {'code/ch09_walks.py', 'code/ch10_regular_graphs.py', 'code/ch11_cospectral.py', 'code/ch12_sensitivity.py', 'code/ch13_expanders.py', 'code/ch14_fiedler.py', 'code/ch15_balance.py', 'code/ch16_frustration_covers.py'}
TOOL_FILES = {'tools/'+name for name in (
    'build_book.py', 'check_chapter_code.py', 'update_metadata.py',
    'validate_books.py', 'audit_public.py', 'verify_source_free.py',
    'verify_publication.py')}
ASSET_FILES = {'assets/'+name for name in (
    'book.css', 'book.js', 'lab.js', 'site-preview.png', 'regular-and-friendship.svg', 'cospectral-structures.svg', 'mathjax-tex-svg.js',
    'mathjax-LICENSE', 'input/tex/extensions/boldsymbol.js',
    'input/tex/extensions/cancel.js', 'input/tex/extensions/mathtools.js')}


def public_files(root=ROOT, *, release=False, complete=False):
    result, errors = [], []
    for relative in sorted(ROOT_FILES | TOOL_FILES | ASSET_FILES | CODE_FILES):
        path = root / relative
        if path.is_file():
            result.append(path)
    for path in sorted(root.glob('chapter-*')):
        if path.name in ROOT_FILES:
            continue
        if re.fullmatch(r'chapter-\d{2}-[a-z0-9-]+\.(?:html|meta\.json)', path.name):
            result.append(path)
        else:
            errors.append('Unexpected chapter path: '+path.name)
    allowed = {p.relative_to(root).as_posix() for p in result}
    manifest = json.loads((root / 'source-manifest.json').read_text(encoding='utf-8'))
    expected_html = {chapter['file'] for chapter in manifest['chapters']}
    expected_meta = {name.replace('.html', '.meta.json') for name in expected_html}
    actual_html = {p.name for p in root.glob('chapter-??-*.html')}
    actual_meta = {p.name for p in root.glob('chapter-??-*.meta.json')}
    if actual_html != expected_html or actual_meta != expected_meta:
        errors.append('Exact chapter filenames differ from the source manifest')
    if len(expected_html) != len(manifest['chapters']):
        errors.append('Duplicate chapter filenames in the source manifest')
    if release:
        for relative in sorted(ROOT_FILES | TOOL_FILES | ASSET_FILES | CODE_FILES):
            if relative not in allowed:
                errors.append('Missing final-release public file: '+relative)
    for relative in ('README.md', 'index.html', 'source-manifest.json',
                     'editorial-review-summary.json', 'assets/site-preview.png',
                     'assets/mathjax-tex-svg.js', 'assets/mathjax-LICENSE'):
        if relative not in allowed:
            errors.append('Missing required public file: '+relative)
    if release and not errors:
        def record(name):
            return json.loads((root / name).read_text(encoding='utf-8'))
        source = record('source-validation-summary.json')
        expected_count = manifest['expected_recordings']
        for key in ('recording_count', 'complete_decoded_audio_count',
                    'complete_machine_transcript_count', 'complete_sequential_transcript_reading_count'):
            if source.get(key) != expected_count:
                errors.append('Incomplete source evidence: '+key)
        source_ids = {r.get('id') for r in source.get('recordings', [])}
        if source_ids != {r['id'] for r in manifest['lectures']}:
            errors.append('Source evidence identities differ from the manifest')
        if not all(r.get('complete_decoded_audio') for r in source.get('recordings', [])):
            errors.append('Incomplete decoded recording evidence')
        inventory = record('content-inventory.json')
        course = record('course-review.json')
        editorial = record('editorial-review-summary.json')
        number = len(manifest['chapters'])
        if (inventory.get('planned_chapter_count') != number
                or inventory.get('authored_chapter_count') != number
                or {r.get('file') for r in inventory.get('chapters', [])} != expected_html
                or not all(r.get('scientifically_accepted') for r in inventory.get('chapters', []))):
            errors.append('Incomplete authored/scientific chapter inventory')
        if (course.get('passed') is not True or course.get('chapter_count') != number
                or course.get('independent_scientific_rounds_per_chapter') != 2
                or len(course.get('chapters', [])) != number
                or not all(r.get('accepted') for r in course.get('chapters', []))
                or len(editorial.get('chapters', [])) != number
                or not all(r.get('accepted') for r in editorial.get('chapters', []))):
            errors.append('Incomplete independent scientific course record')
        for chapter in manifest['chapters']:
            filename = chapter['file']
            sidecar = record(filename.replace('.html', '.meta.json'))
            source_html = (root / filename).read_bytes().decode('utf-8')
            raw_body = source_html.split('<!-- BOOK-CONTENT-START -->', 1)[1].split('<!-- BOOK-CONTENT-END -->', 1)[0]
            digest = hashlib.sha256(raw_body.encode('utf-8')).hexdigest()
            related = [r for r in inventory['chapters'] if r.get('file') == filename]
            science = [r for r in course['chapters'] if r.get('file') == filename]
            rounds = sidecar.get('independent_review', {}).get('rounds', [])
            if (sidecar.get('authored_body_sha256') != digest
                    or len(related) != 1 or related[0].get('body_sha256') != digest
                    or len(science) != 1 or science[0].get('authored_body_sha256') != digest
                    or len(rounds) != 2 or {r.get('round') for r in rounds} != {1, 2}
                    or len({r.get('reviewer') for r in rounds}) != 2
                    or not all(r.get('verdict') == 'accepted' and r.get('authored_body_sha256') == digest for r in rounds)):
                errors.append('Stale or incomplete exact chapter scientific evidence: '+filename)
            if not all(r.get('complete_decoded_audio') and r.get('machine_transcript_complete')
                       and r.get('sequential_transcript_reading_complete') for r in sidecar.get('recordings', [])):
                errors.append('Incomplete chapter source-reading evidence: '+filename)
        completion = record('completion.json')
        if (completion.get('planned_chapters') != number
                or completion.get('authored_chapters') != number
                or completion.get('scientifically_accepted_chapters') != number
                or completion.get('complete_transcript_identities') != expected_count
                or completion.get('all_transcripts_read') is not True):
            errors.append('Stale/incomplete completion inventory')
        for filename in ('chapter-code-validation.json', 'reader-validation.json', 'package-validation.json'):
            if record(filename).get('passed') is not True:
                errors.append('Unpassed current release evidence: '+filename)
        code = record('chapter-code-validation.json')
        if code.get('listing_count') != inventory.get('executable_listing_count'):
            errors.append('Listing verification count differs from content inventory')
        if {r.get('chapter') for r in code.get('results', [])} != expected_html:
            errors.append('Listing verification chapter set differs from the manifest')
        pages = expected_html | {'index.html', 'source-map.html', 'references.html', 'numerical-lab.html'}
        expected_checks = {(name, width) for name in pages for width in (1440, 390)}
        if {(r.get('page'), r.get('width')) for r in record('reader-validation.json').get('results', [])} != expected_checks:
            errors.append('Reader verification lacks the exact complete page/viewport set')
        if complete:
            if completion.get('complete') is not True or not all(completion.get(k) is True for k in ('public_repository_created', 'committed', 'pushed')):
                errors.append('Completion/publication state is not final')
            for filename in ('source-free-validation.json', 'publication-validation.json'):
                if record(filename).get('passed') is not True:
                    errors.append('Unpassed final release evidence: '+filename)
            publication = record('publication-validation.json')
            if publication.get('bootstrap_probe') is not False or publication.get('served_report_passed') is not True:
                errors.append('Final live probe must verify an already accepted served report')
    for path in root.iterdir():
        if path.is_file() and path.name not in allowed and path.name not in ('README.txt', 'AGENTS.md', 'INITIAL_PROMPT.txt'):
            errors.append('Unrecognized root file: '+path.name)
    for path in result:
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            errors.append('Public path escapes package: '+str(path.relative_to(root)))
        if path.suffix in ('.html', '.json', '.md', '.py'):
            source = path.read_bytes().decode('utf-8-sig')
            if re.search(r'[A-Z]:[\\/](?:Users|home)[\\/]|file:///[A-Za-z]|/(?:home|Users)/[A-Za-z0-9]', source):
                errors.append('Private absolute path: '+path.name)
            if re.search(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,})', source):
                errors.append('Credential-like string: '+path.name)
    if errors:
        raise ValueError('\n'.join(errors))
    return sorted(set(result))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', action='store_true', help='Require the complete final public inventory')
    parser.add_argument('--complete', action='store_true', help='Require final completed source-free and live publication evidence')
    args = parser.parse_args()
    files = public_files(release=args.release or args.complete, complete=args.complete)
    report = {'passed': True, 'strict_release_inventory': args.release or args.complete, 'final_completion_gate': args.complete, 'file_count': len(files),
              'files': [p.relative_to(ROOT).as_posix() for p in files],
              'excluded': ['work/', 'README.txt', 'AGENTS.md', 'INITIAL_PROMPT.txt', '.git/', '.venv/', '__pycache__/'],
              'scope': 'Explicit public inventory and private-path/credential-pattern checks; '
                       'not a general security audit.'}
    (ROOT / 'public-package-validation.json').write_text(
        json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print('Public package:', len(files), 'files; privacy inventory passed')


if __name__ == '__main__':
    main()
