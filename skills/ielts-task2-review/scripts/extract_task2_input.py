#!/usr/bin/env python3
"""Extract a new IELTS Task 2 DOCX into prompt, outline, student essay, and existing review evidence."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"


def qn(tag: str) -> str:
    return f"{W}{tag}"


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.iter(qn("t")))


def is_italic_run(run: ET.Element) -> bool:
    rpr = run.find(qn("rPr"))
    if rpr is None:
        return False
    for tag in ("i", "iCs"):
        node = rpr.find(qn(tag))
        if node is not None and node.get(qn("val")) != "0":
            return True
    return False


@dataclass
class Paragraph:
    index: int
    text: str
    italic_text: str
    comment_ids: list[str]


@dataclass
class Comment:
    id: str
    author: str | None
    date: str | None
    target: str
    paragraph_index: int | None
    paragraph_text: str
    text: str


def read_comments(zf: ZipFile) -> dict[str, dict[str, str | None]]:
    if "word/comments.xml" not in zf.namelist():
        return {}
    root = ET.fromstring(zf.read("word/comments.xml"))
    comments: dict[str, dict[str, str | None]] = {}
    for comment in root.findall(qn("comment")):
        cid = comment.get(qn("id"))
        if cid is None:
            continue
        body = []
        for para in comment.findall(qn("p")):
            text = text_of(para).strip()
            if text:
                body.append(text)
        comments[cid] = {
            "author": comment.get(qn("author")),
            "date": comment.get(qn("date")),
            "text": "\n".join(body),
        }
    return comments


def extract_paragraphs_and_anchors(doc_root: ET.Element) -> tuple[list[Paragraph], dict[str, dict[str, object]]]:
    paragraphs: list[Paragraph] = []
    anchors: dict[str, dict[str, object]] = {}
    for p_index, para in enumerate(doc_root.iter(qn("p")), start=1):
        chunks: list[str] = []
        italic_chunks: list[str] = []
        active: list[str] = []
        paragraph_comment_ids: list[str] = []
        span_chunks: dict[str, list[str]] = {}
        for child in list(para):
            if child.tag == qn("commentRangeStart"):
                cid = child.get(qn("id"))
                if cid is not None:
                    active.append(cid)
                    paragraph_comment_ids.append(cid)
                    span_chunks.setdefault(cid, [])
            elif child.tag == qn("commentRangeEnd"):
                cid = child.get(qn("id"))
                if cid in active:
                    active.remove(cid)
            elif child.tag == qn("r"):
                run_text = text_of(child)
                if run_text:
                    chunks.append(run_text)
                    if is_italic_run(child):
                        italic_chunks.append(run_text)
                    for cid in active:
                        span_chunks.setdefault(cid, []).append(run_text)
                for cref in child.findall(qn("commentReference")):
                    cid = cref.get(qn("id"))
                    if cid is not None and cid not in paragraph_comment_ids:
                        paragraph_comment_ids.append(cid)
            else:
                child_text = text_of(child)
                if child_text:
                    chunks.append(child_text)
                    for cid in active:
                        span_chunks.setdefault(cid, []).append(child_text)

        paragraph_text = "".join(chunks).strip()
        italic_text = "".join(italic_chunks).strip()
        if paragraph_text or italic_text or paragraph_comment_ids:
            paragraphs.append(Paragraph(p_index, paragraph_text, italic_text, paragraph_comment_ids))
        for cid, span in span_chunks.items():
            anchors[cid] = {
                "target": "".join(span).strip(),
                "paragraph_index": p_index,
                "paragraph_text": paragraph_text,
            }
    return paragraphs, anchors


def find_prompt(paragraphs: list[Paragraph]) -> tuple[str, int | None, int | None]:
    prompt_parts: list[str] = []
    start = None
    end = None
    started = False
    for i, para in enumerate(paragraphs[:14]):
        text = para.text.strip()
        if not text:
            continue
        lower = text.lower()
        if "write about the following topic" in lower:
            started = True
            start = i + 1
            continue
        if started:
            if lower.startswith(("give reasons", "write at least")):
                end = i
                break
            prompt_parts.append(text)
            end = i + 1
            continue
        if any(marker in text for marker in ("Some people", "In some", "Many people", "To what extent", "Do you agree", "Discuss both")):
            prompt_parts.append(text)
            start = i
            end = i + 1
            break
    return " ".join(prompt_parts).strip(), start, end


def is_likely_essay_start(text: str) -> bool:
    words = text.split()
    if len(words) < 18:
        return False
    starters = (
        "many people",
        "some people",
        "it is",
        "there is",
        "in recent",
        "nowadays",
        "while",
        "although",
        "whether",
        "the issue",
    )
    return text.strip().lower().startswith(starters) or "this essay" in text.lower()


def split_outline_and_essay(paragraphs: list[Paragraph], prompt_end: int | None) -> tuple[list[str], list[str], list[int]]:
    start_search = prompt_end or 0
    candidate_indices = []
    for i, para in enumerate(paragraphs[start_search:], start=start_search):
        text = para.text.strip()
        if not text or para.italic_text:
            continue
        if re.search(r"^(give reasons|write at least|write about)", text, flags=re.I):
            continue
        candidate_indices.append(i)

    essay_start = None
    for i in candidate_indices:
        if is_likely_essay_start(paragraphs[i].text):
            essay_start = i
            break
    if essay_start is None:
        for i in candidate_indices:
            if len(paragraphs[i].text.split()) >= 25:
                essay_start = i
                break

    if essay_start is None:
        return [paragraphs[i].text for i in candidate_indices], [], []

    outline = [paragraphs[i].text for i in candidate_indices if i < essay_start]
    essay: list[str] = []
    essay_indices: list[int] = []
    last_real_essay_index = -1
    for i in candidate_indices:
        if i < essay_start:
            continue
        para = paragraphs[i]
        lower = para.text.lower()
        if para.italic_text:
            continue
        if re.search(r"\(\d+\s*words\)", para.text, flags=re.I):
            break
        if "band 7" in lower or "to reach" in lower or "model essay" in lower:
            break
        if len(para.text.split()) >= 8:
            if last_real_essay_index >= 0 and para.index - last_real_essay_index > 4 and lower.startswith(
                ("many people", "some people", "it is", "there is", "in conclusion")
            ):
                break
            essay.append(para.text)
            essay_indices.append(para.index)
            last_real_essay_index = para.index
            if lower.startswith(("in conclusion", "to conclude", "overall,")) and len(essay) >= 3:
                break
    return outline, essay, essay_indices


def extract_docx(path: Path) -> dict[str, object]:
    with ZipFile(path) as zf:
        doc_root = ET.fromstring(zf.read("word/document.xml"))
        raw_comments = read_comments(zf)
    paragraphs, anchors = extract_paragraphs_and_anchors(doc_root)
    comments: list[Comment] = []
    for cid, data in sorted(raw_comments.items(), key=lambda item: int(item[0])):
        anchor = anchors.get(cid, {})
        comments.append(
            Comment(
                id=cid,
                author=data.get("author"),
                date=data.get("date"),
                target=str(anchor.get("target", "")),
                paragraph_index=anchor.get("paragraph_index") if isinstance(anchor.get("paragraph_index"), int) else None,
                paragraph_text=str(anchor.get("paragraph_text", "")),
                text=str(data.get("text", "")),
            )
        )
    prompt, prompt_start, prompt_end = find_prompt(paragraphs)
    outline, essay, essay_indices = split_outline_and_essay(paragraphs, prompt_end)
    return {
        "source_file": str(path),
        "prompt": prompt,
        "prompt_paragraph_range": [prompt_start, prompt_end],
        "outline": outline,
        "student_essay": essay,
        "student_essay_paragraph_indices": essay_indices,
        "paragraphs": [asdict(p) for p in paragraphs],
        "existing_comments": [asdict(c) for c in comments],
        "existing_italic_rewrites": [
            {"paragraph_index": p.index, "paragraph_text": p.text, "italic_text": p.italic_text}
            for p in paragraphs
            if p.italic_text
        ],
        "counts": {
            "paragraphs": len(paragraphs),
            "outline_paragraphs": len(outline),
            "student_essay_paragraphs": len(essay),
            "existing_comments": len(comments),
            "existing_italic_rewrites": sum(1 for p in paragraphs if p.italic_text),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", type=Path)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    result = extract_docx(args.docx)
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.write_text(text, encoding="utf-8")
        print(args.out)
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
