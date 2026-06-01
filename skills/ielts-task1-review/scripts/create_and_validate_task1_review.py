#!/usr/bin/env python3
"""Create, validate, and clean up an IELTS Task 1 reviewed DOCX."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_json", type=Path)
    parser.add_argument("--input-docx", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--keep-images", action="store_true")
    parser.add_argument("--include-visual-facts", action="store_true")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    image_dir = Path(tempfile.mkdtemp(prefix="ielts_task1_images_", dir="/private/tmp"))
    try:
        image_result = run([sys.executable, str(script_dir / "extract_docx_images.py"), str(args.input_docx), "--out", str(image_dir)])
        print(image_result.stdout, end="")

        create_cmd = [
            sys.executable,
            str(script_dir / "create_task1_review_docx.py"),
            str(args.review_json),
            "--input-docx",
            str(args.input_docx),
            "--cleanup-plan",
        ]
        if args.output:
            create_cmd.extend(["--output", str(args.output)])
        if args.include_visual_facts:
            create_cmd.append("--include-visual-facts")
        create_result = run(create_cmd)
        print(create_result.stdout, end="")

        reviewed = None
        for line in create_result.stdout.splitlines():
            if line.endswith(".docx"):
                reviewed = Path(line)
                break
        if reviewed is None:
            raise SystemExit("Could not determine reviewed DOCX path from create script output.")

        validate_result = run([
            sys.executable,
            str(script_dir / "validate_task1_review_docx.py"),
            str(reviewed),
            "--input-docx",
            str(args.input_docx),
        ])
        print(validate_result.stdout, end="")
    finally:
        if not args.keep_images:
            shutil.rmtree(image_dir, ignore_errors=True)
            print(f"Deleted temporary image directory: {image_dir}")


if __name__ == "__main__":
    main()
