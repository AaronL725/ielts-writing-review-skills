#!/usr/bin/env python3
"""Extract complete IELTS Writing Task 2 band descriptors from a PDF."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean_cell(value: str | None) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    replacements = {
        "skilfuluse": "skilful use",
        "inappropriaciesoccur": "inappropriacies occur",
        "over-generaliseor": "over-generalise or",
        "Organisationis": "Organisation is",
        "organisationalfeatures": "organisational features",
        "recognisablestrings": "recognisable strings",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def extract(pdf_path: Path) -> dict[str, dict[str, str]]:
    try:
        import pdfplumber
    except ImportError as exc:
        raise SystemExit("pdfplumber is required: python -m pip install pdfplumber") from exc

    descriptors: dict[str, dict[str, str]] = {}
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if "Writing Task 2" not in text and "Task Response" not in text:
                continue
            for table in page.extract_tables():
                if not table or len(table) < 2:
                    continue
                headers = [clean_cell(cell) for cell in table[0]]
                if "Task Response" not in headers:
                    continue
                for row in table[1:]:
                    cells = [clean_cell(cell) for cell in row]
                    if not cells or not re.fullmatch(r"\d", cells[0]):
                        continue
                    band = cells[0]
                    descriptors[band] = {}
                    for index, header in enumerate(headers[1:], start=1):
                        if index < len(cells):
                            descriptors[band][header] = cells[index]
    return dict(sorted(descriptors.items(), key=lambda item: int(item[0]), reverse=True))


def write_markdown(descriptors: dict[str, dict[str, str]], path: Path) -> None:
    lines = [
        "# IELTS Writing Task 2 Band Descriptors",
        "",
        "Extracted from the local IELTS writing band descriptors PDF. Use these official criteria before giving improvement advice.",
        "",
        "## Scoring Use",
        "",
        "- Score the student's original essay first.",
        "- Score four criteria separately: Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy.",
        "- Target stable Band 7 first, then push toward 7.5 by borrowing achievable Band 8 features.",
        "",
    ]
    for band, criteria in descriptors.items():
        lines.append(f"## Band {band}")
        lines.append("")
        for criterion, description in criteria.items():
            lines.append(f"### {criterion}")
            lines.append(description)
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--md", type=Path, required=True)
    args = parser.parse_args()

    descriptors = extract(args.pdf)
    if not descriptors:
        raise SystemExit("No Task 2 band descriptors were extracted")
    args.json.write_text(json.dumps(descriptors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(descriptors, args.md)
    print(f"Extracted Task 2 descriptors for bands: {', '.join(descriptors.keys())}")


if __name__ == "__main__":
    main()
