#!/usr/bin/env python3
"""Extract embedded images from a Task 1 DOCX to a temporary directory."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path
from zipfile import ZipFile


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory. Defaults to a unique /private/tmp/ielts_task1_images_* directory.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Delete an existing output directory before extracting. Use only for scratch directories.",
    )
    args = parser.parse_args()
    out = args.out or Path(tempfile.mkdtemp(prefix="ielts_task1_images_", dir="/private/tmp"))
    if args.clean and out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    output_paths = []
    with ZipFile(args.docx) as zf:
        for name in sorted(n for n in zf.namelist() if n.startswith("word/media/")):
            suffix = Path(name).suffix.lower() or ".bin"
            output = out / f"{args.docx.stem.replace(' ', '_')}_{Path(name).stem}{suffix}"
            output.write_bytes(zf.read(name))
            output_paths.append(output)
    if not output_paths:
        raise SystemExit(f"No embedded images found in {args.docx}")
    for path in output_paths:
        print(path)


if __name__ == "__main__":
    main()
