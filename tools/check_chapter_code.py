"""Execute every public teaching program and verify output and PEP8 parity."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pycodestyle
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]


class StyleReport(pycodestyle.BaseReport):
    """Collect the full default PEP8 check set."""

    def __init__(self, options):
        super().__init__(options)
        self.issues = []

    def error(self, line_number, offset, text, check):
        code = super().error(line_number, offset, text, check)
        if code:
            self.issues.append(f"{line_number}:{offset + 1}: {text}")
        return code


def style_issues(code):
    options = pycodestyle.StyleGuide(quiet=True).options
    report = StyleReport(options)
    checker = pycodestyle.Checker(
        lines=code.splitlines(True), options=options, report=report
    )
    checker.check_all()
    return report.issues


def main():
    temporary_root = ROOT / "work" / "code-checks"
    temporary_root.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(
        (ROOT / "source-manifest.json").read_text(encoding="utf-8")
    )
    expected_chapters = {row["file"] for row in manifest["chapters"]}
    chapters = sorted(ROOT.glob("chapter-*.html"))
    if {path.name for path in chapters} != expected_chapters:
        raise ValueError("Code-check chapter filenames differ from manifest")
    records = []
    for chapter in chapters:
        soup = BeautifulSoup(
            chapter.read_bytes().decode("utf-8"), "html.parser"
        )
        listings = soup.select("pre[data-run]")
        if len(listings) != 1:
            raise ValueError(f"{chapter.name}: expected exactly one program")
        for listing in listings:
            identity = listing["data-run"]
            code = listing.get_text()
            exported = ROOT / identity
            if (
                not identity.startswith("code/")
                or exported.suffix != ".py"
                or not exported.resolve().is_relative_to(
                    (ROOT / "code").resolve()
                )
                or not exported.is_file()
                or exported.read_bytes().decode("utf-8") != code
            ):
                raise ValueError(
                    f"{chapter.name}: code export missing, unsafe or differs"
                )
            outputs = soup.select(f'pre[data-output="{identity}"]')
            if len(outputs) != 1:
                raise ValueError(
                    f"{chapter.name}: expected exactly one displayed output"
                )
            issues = style_issues(code)
            with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
                result = subprocess.run(
                    [sys.executable, "-I", "-B", "-X", "utf8", "-c", code],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=90,
                )
            passed = (
                result.returncode == 0
                and result.stdout.strip()
                == outputs[0].get_text().replace("\r\n", "\n")
                .replace("\r", "\n").strip()
                and not issues
            )
            records.append(
                {
                    "chapter": chapter.name,
                    "listing": identity,
                    "code_sha256": hashlib.sha256(code.encode()).hexdigest(),
                    "download_byte_parity": True,
                    "returncode": result.returncode,
                    "pep8_issues": issues,
                    "maximum_line_length": max(map(len, code.splitlines())),
                    "passed": passed,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            print(chapter.name, identity, "PASS" if passed else "FAIL")
    laboratory = (ROOT / "numerical_lab.py").read_text(encoding="utf-8")
    laboratory_style = style_issues(laboratory)
    report = {
        "scope": (
            "Actual isolated execution, exact download/listing byte parity, "
            "displayed output comparison and full default pycodestyle checks. "
            "Finite numerical checks do not constitute a proof audit."
        ),
        "passed": (bool(records) and all(row["passed"] for row in records)
                   and not laboratory_style),
        "standalone_laboratory_pep8_issues": laboratory_style,
        "listing_count": len(records),
        "results": records,
    }
    (ROOT / "chapter-code-validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
