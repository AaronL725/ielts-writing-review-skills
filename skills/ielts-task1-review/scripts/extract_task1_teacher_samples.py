#!/usr/bin/env python3
"""Extract teacher-reviewed IELTS Academic Task 1 DOCX samples.

Preserves prompt text, embedded visual assets, student text, comments, italic
rewrites, feedback, and model answer evidence for teacher-style imitation.
"""

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
        for p in comment.findall(qn("p")):
            text = text_of(p).strip()
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
    for p_index, p in enumerate(doc_root.iter(qn("p")), start=1):
        chunks: list[str] = []
        italic_chunks: list[str] = []
        active: list[str] = []
        paragraph_comment_ids: list[str] = []
        span_chunks: dict[str, list[str]] = {}
        for child in list(p):
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


def extract_images(zf: ZipFile, docx_path: Path, image_out: Path) -> list[dict[str, object]]:
    image_out.mkdir(parents=True, exist_ok=True)
    images = []
    for name in sorted(n for n in zf.namelist() if n.startswith("word/media/")):
        suffix = Path(name).suffix.lower() or ".bin"
        output_name = f"{docx_path.stem.replace(' ', '_')}_{Path(name).stem}{suffix}"
        output_path = image_out / output_name
        output_path.write_bytes(zf.read(name))
        images.append({"source_part": name, "path": f"references/sample_images/{output_name}", "filename": output_name})
    return images


def find_prompt(paragraphs: list[Paragraph]) -> str:
    prompt_parts = []
    for para in paragraphs[:10]:
        text = para.text.strip()
        if not text:
            continue
        if text.startswith("C") and "Writing Task 1" in text:
            continue
        if text.startswith("Write at least"):
            break
        if "Summarise the information" in text or re.search(
            r"\b(The chart|The graph|The table|The diagram|The plans|The maps|The map)s?\s+below\b",
            text,
            flags=re.I,
        ):
            prompt_parts.append(text)
    return " ".join(prompt_parts).strip()


def classify_sections(paragraphs: list[Paragraph]) -> dict[str, object]:
    texts = [p.text for p in paragraphs]
    feedback_start = None
    for i, text in enumerate(texts):
        if re.search(r"(Eliminate|Avoid repetition|Use advanced|Be concise|You already have|You just need|Band|Focus on)", text, re.I):
            feedback_start = i
            break
    model_start = None
    search_start = feedback_start + 1 if feedback_start is not None else 0
    for i in range(search_start, len(texts)):
        remaining_words = sum(len(t.split()) for t in texts[i:])
        if len(texts[i].split()) >= 15 and remaining_words >= 130:
            model_start = i
            break
    if model_start is None:
        for i, text in enumerate(texts):
            if re.search(r"\(\d+\s*words\)", text, re.I):
                model_start = max(0, i - 3)
                break
    return {
        "feedback_paragraphs": texts[feedback_start:model_start] if feedback_start is not None and model_start is not None else [],
        "model_answer_paragraphs": texts[model_start:] if model_start is not None else [],
    }


def extract_docx(path: Path, image_out: Path) -> dict[str, object]:
    with ZipFile(path) as zf:
        doc_root = ET.fromstring(zf.read("word/document.xml"))
        raw_comments = read_comments(zf)
        images = extract_images(zf, path, image_out)
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
    sections = classify_sections(paragraphs)
    return {
        "source_file": str(path),
        "title": paragraphs[0].text if paragraphs else "",
        "prompt": find_prompt(paragraphs),
        "images": images,
        "paragraphs": [asdict(p) for p in paragraphs],
        "comments": [asdict(c) for c in comments],
        "italic_rewrites": [
            {"paragraph_index": p.index, "paragraph_text": p.text, "italic_text": p.italic_text}
            for p in paragraphs
            if p.italic_text
        ],
        **sections,
        "counts": {
            "paragraphs": len(paragraphs),
            "comments": len(comments),
            "italic_rewrites": sum(1 for p in paragraphs if p.italic_text),
            "images": len(images),
        },
    }


def write_markdown(sample: dict[str, object], path: Path) -> None:
    lines = [
        f"# {Path(str(sample['source_file'])).name}",
        "",
        "## Prompt",
        str(sample.get("prompt", "")),
        "",
        "## Images",
    ]
    for image in sample.get("images", []):  # type: ignore[assignment]
        lines.append(f"- {image['filename']}: {image['path']}")
    lines.extend(["", "## Counts", json.dumps(sample["counts"], ensure_ascii=False), "", "## Comments"])
    for comment in sample["comments"]:  # type: ignore[index]
        lines.append(f"- `{comment['target']}` -> {comment['text']}")
    lines.extend(["", "## Italic Rewrites"])
    for rewrite in sample["italic_rewrites"]:  # type: ignore[index]
        lines.append(f"- Original/context: {rewrite['paragraph_text']}")
        lines.append(f"  Rewrite: {rewrite['italic_text']}")
    lines.extend(["", "## Feedback"])
    lines.extend(str(x) for x in sample.get("feedback_paragraphs", []))  # type: ignore[arg-type]
    lines.extend(["", "## Model Answer"])
    lines.extend(str(x) for x in sample.get("model_answer_paragraphs", []))  # type: ignore[arg-type]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def iter_docx(input_path: Path):
    if input_path.is_file():
        yield input_path
    else:
        yield from sorted(input_path.glob("*.docx"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--image-out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    args.image_out.mkdir(parents=True, exist_ok=True)
    samples = []
    for docx_path in iter_docx(args.input):
        sample = extract_docx(docx_path, args.image_out)
        stem = docx_path.stem.replace(" ", "_")
        (args.out / f"{stem}.json").write_text(json.dumps(sample, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        write_markdown(sample, args.out / f"{stem}.md")
        samples.append(
            {
                "file": docx_path.name,
                "json": f"teacher_samples/{stem}.json",
                "markdown": f"teacher_samples/{stem}.md",
                "prompt": sample["prompt"],
                "counts": sample["counts"],
                "images": [img["filename"] for img in sample["images"]],  # type: ignore[index]
            }
        )
    lines = [
        "# Teacher Sample Index",
        "",
        "Full teacher-reviewed IELTS Academic Task 1 samples extracted from DOCX files.",
        "",
    ]
    for item in samples:
        counts = item["counts"]
        lines.append(
            f"- {item['file']}: images={counts['images']}, comments={counts['comments']}, italic_rewrites={counts['italic_rewrites']}, prompt={item['prompt']}, image_files={', '.join(item['images'])}"
        )
    (args.out.parent / "teacher_samples_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Extracted {len(samples)} Task 1 sample(s) to {args.out}")


if __name__ == "__main__":
    main()
