"""Inspect docs/: does every PDF parse, and does it yield extractable text?

Run this before building the index. A PDF that "looks fine" in a viewer can
still fail to yield text (scanned images, broken object streams), which would
silently produce empty chunks and useless retrieval.

``--repair`` rewrites any file that fails a lenient pypdf read, keeping the
original under ``docs/_originals/``.

Usage:  python tools/inspect_corpus.py [--repair]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.rag.ingest import pdf_files  # noqa: E402

BACKUP_DIR = PROJECT_ROOT / "docs" / "_originals"
MIN_USEFUL_CHARS = 200


def parse_report(path: Path) -> tuple[int, int, bool]:
    """Return ``(pages, characters, parsed_cleanly)`` for one PDF."""
    cleanly = True
    try:
        reader = PdfReader(str(path), strict=True)
    except Exception:
        cleanly = False
        reader = PdfReader(str(path), strict=False)

    characters = 0
    for page in reader.pages:
        characters += len((page.extract_text() or "").strip())
    return len(reader.pages), characters, cleanly


def repair(path: Path) -> None:
    """Rewrite a damaged PDF from a lenient read, keeping the original."""
    reader = PdfReader(str(path), strict=False)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup = BACKUP_DIR / path.name
    if not backup.exists():
        shutil.copy2(path, backup)

    temp = path.with_name(f"{path.name}.repaired")
    with temp.open("wb") as handle:
        writer.write(handle)
    temp.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair", action="store_true", help="rewrite unreadable PDFs")
    args = parser.parse_args()

    targets = pdf_files()
    if not targets:
        print("No PDFs found in docs/. Run 'python tools/make_sample_docs.py' for a demo corpus.")
        return 1

    problems = 0
    total_chars = 0
    print(f"{'file':<42} {'pages':>6} {'chars':>8}  status")
    print("-" * 70)

    for path in targets:
        try:
            pages, characters, cleanly = parse_report(path)
        except Exception as error:
            print(f"{path.name:<42} {'-':>6} {'-':>8}  UNREADABLE: {error}")
            problems += 1
            if args.repair:
                repair(path)
                print(f"{'':<42} {'':>6} {'':>8}  repaired (original in _originals/)")
            continue

        total_chars += characters
        if characters < MIN_USEFUL_CHARS:
            status = "WARNING: little or no extractable text (scanned?)"
            problems += 1
        elif not cleanly:
            status = "ok (lenient recovery)"
        else:
            status = "ok"
        print(f"{path.name:<42} {pages:>6} {characters:>8}  {status}")

    print("-" * 70)
    print(f"{len(targets)} file(s), {total_chars:,} characters, {problems} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
