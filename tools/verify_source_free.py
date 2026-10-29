"""Rebuild a committed public export with optional fresh isolated dependencies."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

from audit_public import MUTABLE_REPORTS, ROOT, public_files


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_command(command, cwd, environment, timeout=300):
    result = subprocess.run(
        command, cwd=cwd, env=environment, capture_output=True,
        text=True, encoding="utf-8", timeout=timeout,
    )
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true")
    parser.add_argument(
        "--git", action="store_true",
        help="Export committed HEAD using git archive",
    )
    parser.add_argument(
        "--install", action="store_true",
        help="Create a fresh venv and install the exported requirements",
    )
    args = parser.parse_args()
    parent = ROOT / "work" / "source-free"
    parent.mkdir(parents=True, exist_ok=True)
    export = Path(tempfile.mkdtemp(prefix="export-", dir=parent))
    files = public_files(release=True)
    commit = None
    if args.git:
        committed = subprocess.check_output(
            ["git", "ls-files", "-z"], cwd=ROOT
        )
        tracked = set(committed.decode("utf-8").strip("\0").split("\0"))
        allowed = {p.relative_to(ROOT).as_posix() for p in files}
        if tracked != allowed:
            raise ValueError("Git inventory differs from public package")
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        archive = subprocess.check_output(
            ["git", "archive", "--format=tar", "HEAD"], cwd=ROOT
        )
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(export, filter="data")
    else:
        for source in files:
            target = export / source.relative_to(ROOT)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    before = {p.name: sha(p) for p in export.glob("*.html")}
    core_hashes = {
        p.relative_to(ROOT).as_posix(): sha(export / p.relative_to(ROOT))
        for p in files if p.relative_to(ROOT).as_posix() not in MUTABLE_REPORTS
    }
    temporary = export / "work" / "tmp"
    temporary.mkdir(parents=True)
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment.update(
        TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary),
        PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1",
        PIP_CACHE_DIR=str(export / "work" / "pip-cache"),
        PIP_CONFIG_FILE=os.devnull,
        PLAYWRIGHT_BROWSERS_PATH=str(export / "work" / "browser-cache"),
        OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2",
    )
    python = sys.executable
    installation = []
    packages = []
    isolated = False
    if args.install:
        virtual = export / "work" / "dependency-env"
        installation.append(run_command(
            [sys.executable, "-I", "-B", "-m", "venv", str(virtual)],
            export, environment,
        ))
        if installation[-1]["returncode"] == 0:
            python = str(virtual / (
                "Scripts/python.exe" if os.name == "nt" else "bin/python"
            ))
            configuration = (virtual / "pyvenv.cfg").read_text()
            isolated = "include-system-site-packages = false" in configuration
            installation.append(run_command(
                [
                    python, "-I", "-B", "-m", "pip", "install",
                    "--isolated", "--no-cache-dir",
                    "--disable-pip-version-check", "--requirement",
                    str(export / "requirements.txt"),
                ],
                export, environment, timeout=900,
            ))
            installation.append(run_command(
                [python, "-I", "-B", "-m", "pip", "check"],
                export, environment,
            ))
            frozen = run_command(
                [python, "-I", "-B", "-m", "pip", "freeze", "--all"],
                export, environment,
            )
            installation.append(frozen)
            packages = frozen["stdout"].splitlines()
    install_passed = (
        not args.install
        or isolated and len(installation) == 4
        and all(item["returncode"] == 0 for item in installation)
    )
    commands = [
        ["tools/build_book.py"],
        ["tools/check_chapter_code.py"],
        ["numerical_lab.py"],
        ["tools/validate_books.py"] + (
            ["--browser"] if args.browser else []
        ),
        ["tools/audit_public.py", "--release"],
    ]
    results = []
    if install_passed:
        for command in commands:
            result = run_command(
                [python, "-B", "-X", "utf8", *command],
                export, environment, timeout=600,
            )
            # Public reports contain portable commands, never local paths.
            result["command"] = "python -B -X utf8 " + " ".join(command)
            results.append(result)
    changed = [
        name for name, digest in before.items() if sha(export / name) != digest
    ]
    passed = (
        install_passed and len(results) == len(commands)
        and not changed and all(r["returncode"] == 0 for r in results)
    )
    # Installer output contains environment paths. Preserve its full logs only
    # in ignored work; publish versions, requirements hash and exit statuses.
    (export / "work" / "dependency-installation.json").write_text(
        json.dumps(installation, indent=2) + "\n", encoding="utf-8"
    )
    report = {
        "passed": passed,
        "public_file_count": len(files),
        "html_count": len(before),
        "byte_identical_html_rebuild": not changed,
        "changed_html": changed,
        "raw_source_files_available": False,
        "browser_checks_requested": args.browser,
        "git_archive_commit": commit,
        "export_method": (
            "git archive HEAD" if args.git else "allowlisted file copy"
        ),
        "fresh_isolated_dependency_install": args.install and install_passed,
        "system_site_packages_available": not isolated if args.install else None,
        "requirements_sha256": sha(export / "requirements.txt"),
        "dependency_install_returncodes": [
            r["returncode"] for r in installation
        ],
        "installed_packages": packages,
        "scope": (
            "Public-only export without acquisition sources/private reviews; "
            "fresh local venv installation from exported pinned requirements "
            "when --install is set. Installed system headless Chromium and "
            "the interpreter standard library remain host prerequisites."
        ),
        "html_sha256": before,
        "public_payload_sha256": core_hashes,
        "checks": results,
    }
    (ROOT / "source-free-validation.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Source-free export:", passed,
        "; identical HTML:", len(before) - len(changed),
        "; fresh isolated install:", report["fresh_isolated_dependency_install"],
    )
    if not passed:
        print(json.dumps(report, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
