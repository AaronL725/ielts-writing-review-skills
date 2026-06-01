#!/usr/bin/env python3
"""Find the closest bundled Task 2 teacher sample for an input name or prompt."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def sample_score(query: str, sample_path: Path, sample: dict[str, object]) -> tuple[int, int, int]:
    query_variants = {query, Path(query).name, Path(query).stem}
    query_norms = {normalize(item) for item in query_variants if item}
    stem_norm = normalize(sample_path.stem)
    source_norm = normalize(Path(str(sample.get("source_file", ""))).stem)
    prompt = str(sample.get("prompt", ""))
    q_tokens = token_set(query)
    p_tokens = token_set(prompt)
    exact = int(any(q in {stem_norm, source_norm} for q in query_norms))
    contains = int(
        any(q and (q in stem_norm or q in source_norm or stem_norm in q or source_norm in q) for q in query_norms)
    )
    overlap = len(q_tokens & p_tokens)
    return exact, contains, overlap


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Input DOCX filename, sample filename, or prompt text")
    parser.add_argument(
        "--samples",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "references" / "teacher_samples",
        help="Directory containing bundled teacher sample JSON files.",
    )
    parser.add_argument("--limit", type=int, default=3)
    args = parser.parse_args()

    matches = []
    for path in sorted(args.samples.glob("*.json")):
        sample = json.loads(path.read_text(encoding="utf-8"))
        score = sample_score(args.query, path, sample)
        if any(score):
            matches.append((score, path, sample))
    matches.sort(key=lambda item: item[0], reverse=True)

    if not matches:
        raise SystemExit(f"No matching teacher sample found for: {args.query}")

    for score, path, sample in matches[: args.limit]:
        print(json.dumps({
            "json": str(path),
            "markdown": str(path.with_suffix(".md")),
            "source_file": sample.get("source_file", ""),
            "prompt": sample.get("prompt", ""),
            "score": {"exact_name": score[0], "contains_name": score[1], "prompt_overlap": score[2]},
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
