#!/usr/bin/env python3
"""Extract Task 1 DOCX structure for safe answer-only review anchoring."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
V_NS = "urn:schemas-microsoft-com:vml"
W = f"{{{W_NS}}}"
A = f"{{{A_NS}}}"
V = f"{{{V_NS}}}"


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


def has_image(paragraph: ET.Element) -> bool:
    for child in paragraph.iter():
        if child.tag in {qn("drawing"), f"{A}blip", f"{V}imagedata"}:
            return True
    return False


@dataclass
class Paragraph:
    index: int
    text: str
    italic_text: str
    has_image: bool
    comment_ids: list[str]


def direct_paragraphs(doc_root: ET.Element) -> list[ET.Element]:
    body = doc_root.find(qn("body"))
    if body is None:
        return []
    return [child for child in list(body) if child.tag == qn("p")]


def extract_paragraphs(doc_root: ET.Element) -> list[Paragraph]:
    paragraphs: list[Paragraph] = []
    for p_index, para in enumerate(direct_paragraphs(doc_root), start=1):
        chunks: list[str] = []
        italic_chunks: list[str] = []
        comment_ids: list[str] = []
        for child in list(para):
            if child.tag == qn("commentRangeStart"):
                cid = child.get(qn("id"))
                if cid is not None:
                    comment_ids.append(cid)
            elif child.tag == qn("r"):
                run_text = text_of(child)
                if run_text:
                    chunks.append(run_text)
                    if is_italic_run(child):
                        italic_chunks.append(run_text)
                for cref in child.findall(qn("commentReference")):
                    cid = cref.get(qn("id"))
                    if cid is not None and cid not in comment_ids:
                        comment_ids.append(cid)
            else:
                child_text = text_of(child)
                if child_text:
                    chunks.append(child_text)
        paragraph_text = "".join(chunks).strip()
        italic_text = "".join(italic_chunks).strip()
        paragraphs.append(Paragraph(p_index, paragraph_text, italic_text, has_image(para), comment_ids))
    return paragraphs


def is_review_or_feedback_marker(text: str, collected_count: int) -> bool:
    normalized = " ".join(text.split())
    lower = normalized.lower()
    if not lower:
        return False
    hard_markers = (
        "to reach band",
        "model answer",
        "visual facts",
        "task achievement:",
        "coherence & cohesion:",
        "lexical resource:",
        "grammatical range & accuracy:",
        "overall:",
    )
    if any(marker in lower for marker in hard_markers):
        return True
    teacher_feedback_markers = (
        "you’re already",
        "you're already",
        "focus on:",
        "eliminate small grammar errors",
        "avoid repetition",
        "advanced comparison structures",
        "be concise",
        "you repeat:",
        "replace with:",
        "you already have:",
        "you just need:",
    )
    if collected_count >= 2 and any(marker in lower for marker in teacher_feedback_markers):
        return True
    if collected_count >= 3 and re.match(r"^\d+\.\s+\S+", normalized):
        return True
    return False


def split_prompt_and_answer(paragraphs: list[Paragraph]) -> tuple[list[str], list[str], list[int]]:
    image_indices = [p.index for p in paragraphs if p.has_image]
    start_index = max(image_indices) + 1 if image_indices else 1
    prompt: list[str] = []
    answer: list[str] = []
    answer_indices: list[int] = []
    for para in paragraphs:
        text = " ".join(para.text.split())
        if not text:
            continue
        if para.index < start_index:
            prompt.append(text)
            continue
        if para.italic_text and para.italic_text == para.text:
            continue
        if is_review_or_feedback_marker(text, len(answer)):
            break
        if len(text.split()) < 4 and not answer:
            prompt.append(text)
            continue
        answer.append(text)
        answer_indices.append(para.index)
    return prompt, answer, answer_indices


def extract_docx(path: Path) -> dict[str, object]:
    with ZipFile(path) as zf:
        doc_root = ET.fromstring(zf.read("word/document.xml"))
        image_files = sorted(name for name in zf.namelist() if name.startswith("word/media/"))
    paragraphs = extract_paragraphs(doc_root)
    prompt, answer, answer_indices = split_prompt_and_answer(paragraphs)
    return {
        "source_file": str(path),
        "prompt": prompt,
        "student_answer": answer,
        "student_answer_paragraph_indices": answer_indices,
        "image_count": len(image_files),
        "image_files": image_files,
        "paragraphs": [asdict(p) for p in paragraphs if p.text or p.has_image or p.comment_ids],
        "counts": {
            "paragraphs": len(paragraphs),
            "prompt_paragraphs": len(prompt),
            "student_answer_paragraphs": len(answer),
            "images": len(image_files),
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
