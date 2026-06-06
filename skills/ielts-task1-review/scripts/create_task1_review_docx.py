#!/usr/bin/env python3
"""Create an IELTS Academic Task 1 reviewed DOCX with comments and italic rewrites."""

from __future__ import annotations

import argparse
import copy
import html
import json
import re
import shutil
from datetime import datetime, timezone
from datetime import timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

from extract_task1_input import extract_docx as extract_task1_docx

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
FONT = "Times New Roman"
COMMENT_TZ = timezone(timedelta(hours=8))
ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)


def xml_escape(text: str) -> str:
    return html.escape(text, quote=False)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+", text))


def run_xml(text: str, italic: bool = False, bold: bool = False, style: str | None = None) -> str:
    if not text:
        return ""
    props = []
    if style:
        props.append(f'<w:rStyle w:val="{style}"/>')
    props.append(f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/>')
    if bold:
        props.append("<w:b/>")
    if italic:
        props.append("<w:i/>")
    rpr = f"<w:rPr>{''.join(props)}</w:rPr>"
    space = ' xml:space="preserve"' if text[:1].isspace() or text[-1:].isspace() else ""
    return f"<w:r>{rpr}<w:t{space}>{xml_escape(text)}</w:t></w:r>"


def paragraph_xml(runs: list[str], style: str | None = None) -> str:
    ppr = f'<w:pPr><w:pStyle w:val="{style}"/></w:pPr>' if style else ""
    return f"<w:p>{ppr}{''.join(runs)}</w:p>"


def heading(text: str, level: int = 1) -> str:
    return paragraph_xml([run_xml(text, bold=True)], style=f"Heading{level}")


def page_break() -> str:
    return '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def comment_reference_run(cid: int) -> str:
    return (
        '<w:r><w:rPr><w:rStyle w:val="CommentReference"/>'
        f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/></w:rPr>'
        f'<w:commentReference w:id="{cid}"/></w:r>'
    )


def add_comment_to_runs(original: str, comments: list[dict[str, str]], next_id: int) -> tuple[list[str], list[dict[str, Any]], int]:
    if not comments:
        return [run_xml(original)], [], next_id
    ranges = []
    used_spans: list[tuple[int, int]] = []
    for comment in comments:
        target = comment.get("target") or ""
        text = comment.get("text") or ""
        if not text:
            continue
        start = original.find(target) if target else -1
        if start < 0:
            start, end, target = 0, len(original), original
        else:
            end = start + len(target)
        if any(not (end <= a or start >= b) for a, b in used_spans):
            start, end, target = 0, len(original), original
        used_spans.append((start, end))
        ranges.append({"start": start, "end": end, "target": target, "text": text, "id": next_id})
        next_id += 1
    ranges.sort(key=lambda item: (item["start"], item["end"]))
    runs: list[str] = []
    emitted: list[dict[str, Any]] = []
    cursor = 0
    for item in ranges:
        start, end, cid = int(item["start"]), int(item["end"]), int(item["id"])
        if cursor < start:
            runs.append(run_xml(original[cursor:start]))
        runs.append(f'<w:commentRangeStart w:id="{cid}"/>')
        runs.append(run_xml(original[start:end]))
        runs.append(f'<w:commentRangeEnd w:id="{cid}"/>')
        runs.append(comment_reference_run(cid))
        emitted.append(item)
        cursor = end
    if cursor < len(original):
        runs.append(run_xml(original[cursor:]))
    return runs, emitted, next_id


def comments_xml(comments: list[dict[str, Any]], author: str) -> str:
    now = datetime.now(COMMENT_TZ).isoformat(timespec="seconds")
    body = []
    for item in comments:
        cid = int(item["id"])
        text = xml_escape(str(item["text"]))
        body.append(
            f'<w:comment w:id="{cid}" w:author="{xml_escape(author)}" w:date="{now}" w:initials="CE">'
            '<w:p><w:r><w:rPr><w:rStyle w:val="CommentReference"/></w:rPr><w:annotationRef/></w:r>'
            f'<w:r><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/></w:rPr><w:t>{text}</w:t></w:r></w:p></w:comment>'
        )
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>' + f'<w:comments xmlns:w="{W_NS}">{"".join(body)}</w:comments>'


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/comments.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def document_rels_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments" Target="comments.xml"/>
</Relationships>"""


def styles_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{W_NS}">
  <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="Heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:b/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="Heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:b/><w:sz w:val="26"/><w:szCs w:val="26"/></w:rPr></w:style>
  <w:style w:type="character" w:styleId="CommentReference"><w:name w:val="Comment Reference"/><w:semiHidden/><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}"/><w:vertAlign w:val="superscript"/><w:color w:val="0000FF"/></w:rPr></w:style>
</w:styles>"""


def app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Codex</Application></Properties>"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>IELTS Task 1 Reviewed Answer</dc:title><dc:creator>ielts-task1-review</dc:creator>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


def document_xml(plan: dict[str, Any], include_visual_facts: bool = False) -> tuple[str, list[dict[str, Any]]]:
    body: list[str] = []
    comments: list[dict[str, Any]] = []
    next_comment_id = 0
    prompt = str(plan.get("prompt", "")).strip()
    if prompt:
        body.append(paragraph_xml([run_xml(prompt)]))
    visual_facts = plan.get("visual_facts", [])
    if include_visual_facts and visual_facts:
        body.append(heading("Visual Facts", 2))
        for item in visual_facts:
            body.append(paragraph_xml([run_xml(str(item))]))
    for unit in plan.get("review_units", []):
        original = str(unit.get("original", "")).strip()
        if not original:
            continue
        runs, emitted, next_comment_id = add_comment_to_runs(original, list(unit.get("comments", [])), next_comment_id)
        comments.extend(emitted)
        body.append(paragraph_xml(runs))
        rewrite = str(unit.get("rewrite", "")).strip()
        if rewrite:
            body.append(paragraph_xml([run_xml(rewrite, italic=True)]))
    body.append(page_break())
    scores = plan.get("scores", {})
    if isinstance(scores, dict):
        for key in ["Task Achievement", "Coherence & Cohesion", "Lexical Resource", "Grammatical Range & Accuracy", "Overall"]:
            if key in scores:
                body.append(paragraph_xml([run_xml(f"{key}: ", bold=True), run_xml(str(scores[key]))]))
    for item in plan.get("score_explanation", []):
        body.append(paragraph_xml([run_xml(str(item))]))
    body.append(heading("To Reach Band 7.5 / 8.0", 2))
    for item in plan.get("focus_feedback", []):
        body.append(paragraph_xml([run_xml(str(item))]))
    body.append(page_break())
    model_paragraphs = plan.get("model_answer", [])
    if isinstance(model_paragraphs, str):
        model_paragraphs = [p.strip() for p in model_paragraphs.split("\n") if p.strip()]
    model_text = " ".join(str(p) for p in model_paragraphs)
    for idx, para in enumerate(model_paragraphs):
        body.append(paragraph_xml([run_xml(str(para))]))
        if idx < len(model_paragraphs) - 1:
            body.append(paragraph_xml([]))
    body.append(paragraph_xml([run_xml(f"({word_count(model_text)} words)")]))
    xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{W_NS}" xmlns:r="{R_NS}"><w:body>'
        + "".join(body)
        + '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
        + "</w:body></w:document>"
    )
    return xml, comments


def qn(ns: str, tag: str) -> str:
    return f"{{{ns}}}{tag}"


def register_document_namespaces(document_xml: str) -> None:
    match = re.search(r"<w:document\b([^>]*)>", document_xml)
    if not match:
        return
    attrs = match.group(1)
    for prefix, uri in re.findall(r'xmlns:([^=\s]+)="([^"]+)"', attrs):
        ET.register_namespace(prefix, uri)


def restore_document_root_namespaces(serialized_xml: str, original_xml: str) -> str:
    original_match = re.search(r"<w:document\b[^>]*>", original_xml)
    output_match = re.search(r"<w:document\b[^>]*>", serialized_xml)
    if not original_match or not output_match:
        return serialized_xml
    original_tag = original_match.group(0)
    output_tag = output_match.group(0)
    original_namespaces = dict(re.findall(r'xmlns:([^=\s]+)="([^"]+)"', original_tag))
    output_prefixes = set(re.findall(r'xmlns:([^=\s]+)="[^"]+"', output_tag))

    original_ignorable = re.search(r'\bmc:Ignorable="([^"]*)"', original_tag)
    if original_ignorable:
        ignorable_attr = f'mc:Ignorable="{original_ignorable.group(1)}"'
        if re.search(r'\b(?:mc|ns\d+):Ignorable="[^"]*"', output_tag):
            output_tag = re.sub(r'\b(?:mc|ns\d+):Ignorable="[^"]*"', ignorable_attr, output_tag)
        else:
            output_tag = output_tag[:-1] + f" {ignorable_attr}>"

    additions = []
    for prefix, uri in original_namespaces.items():
        if prefix not in output_prefixes:
            additions.append(f' xmlns:{prefix}="{html.escape(uri, quote=True)}"')
    if additions:
        output_tag = output_tag[:-1] + "".join(additions) + ">"
    restored = serialized_xml[: output_match.start()] + output_tag + serialized_xml[output_match.end():]
    original_decl = re.match(r"\s*(<\?xml[^>]*\?>)", original_xml)
    if original_decl and not restored.lstrip().startswith("<?xml"):
        restored = original_decl.group(1) + "\n" + restored
    return restored


def text_of(el: ET.Element) -> str:
    return "".join(t.text or "" for t in el.iter(qn(W_NS, "t")))


def normalize_spaces(text: str) -> str:
    return " ".join(text.split())


def normalized_with_map(text: str) -> tuple[str, list[int]]:
    chars: list[str] = []
    index_map: list[int] = []
    pending_space = False
    pending_index = 0
    for idx, char in enumerate(text):
        if char.isspace():
            if chars and not pending_space:
                pending_space = True
                pending_index = idx
            continue
        if pending_space:
            chars.append(" ")
            index_map.append(pending_index)
            pending_space = False
        chars.append(char)
        index_map.append(idx)
    return "".join(chars), index_map


def find_loose_span(text: str, needle: str, preferred: tuple[int, int] | None = None) -> tuple[int, int] | None:
    needle = needle.strip()
    if not needle:
        return None
    if preferred:
        start, end = preferred
        nested = find_loose_span(text[start:end], needle)
        if nested:
            return start + nested[0], start + nested[1]
    exact = text.find(needle)
    if exact >= 0:
        return exact, exact + len(needle)
    normalized_text, text_map = normalized_with_map(text.lower())
    normalized_needle = normalize_spaces(needle).lower()
    if not normalized_text or not normalized_needle:
        return None
    pos = normalized_text.find(normalized_needle)
    if pos < 0:
        return None
    end_pos = pos + len(normalized_needle) - 1
    return text_map[pos], text_map[end_pos] + 1


def normalize_plan_indices(value: Any, paragraph_count: int) -> set[int]:
    if value is None:
        return set()
    values = value if isinstance(value, list) else [value]
    positions: set[int] = set()
    for raw in values:
        try:
            index = int(raw)
        except (TypeError, ValueError):
            continue
        if 1 <= index <= paragraph_count:
            positions.add(index - 1)
        elif 0 <= index < paragraph_count:
            positions.add(index)
    return positions


def allowed_paragraph_positions(plan: dict[str, Any], paragraph_count: int) -> set[int] | None:
    for key in ("student_answer_paragraph_indices", "answer_paragraph_indices", "student_essay_paragraph_indices"):
        positions = normalize_plan_indices(plan.get(key), paragraph_count)
        if positions:
            return positions
    extraction = plan.get("input_extraction")
    if isinstance(extraction, dict):
        for key in ("student_answer_paragraph_indices", "student_essay_paragraph_indices"):
            positions = normalize_plan_indices(extraction.get(key), paragraph_count)
            if positions:
                return positions
    return None


def unit_paragraph_positions(unit: dict[str, Any], paragraph_count: int) -> set[int]:
    positions = set()
    for key in ("paragraph_index", "paragraph_indices", "student_answer_paragraph_index", "student_answer_paragraph_indices"):
        positions.update(normalize_plan_indices(unit.get(key), paragraph_count))
    return positions


def candidate_positions(paragraphs: list[ET.Element], search_from: int, allowed_positions: set[int] | None) -> list[int]:
    if allowed_positions is None:
        return list(range(search_from, len(paragraphs)))
    return sorted(idx for idx in allowed_positions if idx >= search_from)


def is_safe_reverse_paragraph_match(normalized_paragraph: str, normalized_unit: str) -> bool:
    if normalized_paragraph not in normalized_unit:
        return False
    if len(normalized_paragraph) < 40:
        return False
    if word_count(normalized_paragraph) < 8:
        return False
    return len(normalized_paragraph) / max(1, len(normalized_unit)) >= 0.35


def find_best_paragraph(
    paragraphs: list[ET.Element],
    unit_text: str,
    search_from: int,
    allowed_positions: set[int] | None = None,
) -> int | None:
    normalized_unit = normalize_spaces(unit_text).lower()
    if not normalized_unit:
        return None
    positions = candidate_positions(paragraphs, search_from, allowed_positions)
    for idx in positions:
        normalized_paragraph = normalize_spaces(text_of(paragraphs[idx])).lower()
        if not normalized_paragraph:
            continue
        if normalized_unit in normalized_paragraph or is_safe_reverse_paragraph_match(normalized_paragraph, normalized_unit):
            return idx
    unit_words = set(re.findall(r"[a-z0-9]+", normalized_unit))
    best_idx: int | None = None
    best_score = 0.0
    for idx in positions:
        normalized_paragraph = normalize_spaces(text_of(paragraphs[idx])).lower()
        if not normalized_paragraph:
            continue
        paragraph_words = set(re.findall(r"[a-z0-9]+", normalized_paragraph))
        if not paragraph_words:
            continue
        overlap = len(unit_words & paragraph_words) / max(1, len(unit_words))
        length_balance = min(len(normalized_unit), len(normalized_paragraph)) / max(len(normalized_unit), len(normalized_paragraph))
        score = (overlap * 0.75) + (length_balance * 0.25)
        if score > best_score:
            best_idx = idx
            best_score = score
    return best_idx if best_score >= 0.68 else None


def overlaps(span: tuple[int, int], ranges: list[dict[str, Any]]) -> bool:
    start, end = span
    return any(not (end <= int(item["start"]) or start >= int(item["end"])) for item in ranges)


def non_overlapping_span(text: str, start: int, end: int, ranges: list[dict[str, Any]]) -> tuple[int, int] | None:
    start = max(0, min(start, len(text)))
    end = max(start, min(end, len(text)))
    if start == end and start < len(text):
        end += 1
    if start < end and not overlaps((start, end), ranges):
        return start, end
    for match in re.finditer(r"\S+", text[start:end]):
        candidate = (start + match.start(), start + match.end())
        if not overlaps(candidate, ranges):
            return candidate
    for pos in range(start, end):
        candidate = (pos, min(pos + 1, len(text)))
        if not overlaps(candidate, ranges):
            return candidate
    return None


def runs_with_comment_ranges(text: str, ranges: list[dict[str, Any]]) -> list[str]:
    ranges = sorted(ranges, key=lambda item: (int(item["start"]), int(item["end"])))
    runs: list[str] = []
    cursor = 0
    for item in ranges:
        start, end, cid = int(item["start"]), int(item["end"]), int(item["id"])
        if cursor < start:
            runs.append(run_xml(text[cursor:start]))
        runs.append(f'<w:commentRangeStart w:id="{cid}"/>')
        runs.append(run_xml(text[start:end]))
        runs.append(f'<w:commentRangeEnd w:id="{cid}"/>')
        runs.append(comment_reference_run(cid))
        cursor = end
    if cursor < len(text):
        runs.append(run_xml(text[cursor:]))
    return runs


def parse_body_fragment(body_fragment: str) -> list[ET.Element]:
    wrapper = ET.fromstring(f'<w:wrapper xmlns:w="{W_NS}" xmlns:r="{R_NS}">{body_fragment}</w:wrapper>')
    return list(wrapper)


def replace_paragraph_runs(paragraph: ET.Element, ranges: list[dict[str, Any]]) -> None:
    original_text = text_of(paragraph)
    ppr = paragraph.find(qn(W_NS, "pPr"))
    ppr_copy = copy.deepcopy(ppr) if ppr is not None else None
    paragraph.clear()
    if ppr_copy is not None:
        paragraph.append(ppr_copy)
    for child in parse_body_fragment("".join(runs_with_comment_ranges(original_text, ranges))):
        paragraph.append(child)


def insert_body_fragment(body: ET.Element, body_fragment: str) -> None:
    insert_at = len(body)
    body_children = list(body)
    if body_children and body_children[-1].tag == qn(W_NS, "sectPr"):
        insert_at -= 1
    for child in parse_body_fragment(body_fragment):
        body.insert(insert_at, child)
        insert_at += 1


def review_tail_body_xml(plan: dict[str, Any], include_visual_facts: bool = False) -> str:
    body: list[str] = []
    visual_facts = plan.get("visual_facts", [])
    if include_visual_facts and visual_facts:
        body.append(heading("Visual Facts", 2))
        for item in visual_facts:
            body.append(paragraph_xml([run_xml(str(item))]))
    body.append(page_break())
    scores = plan.get("scores", {})
    if isinstance(scores, dict):
        for key in ["Task Achievement", "Coherence & Cohesion", "Lexical Resource", "Grammatical Range & Accuracy", "Overall"]:
            if key in scores:
                body.append(paragraph_xml([run_xml(f"{key}: ", bold=True), run_xml(str(scores[key]))]))
    for item in plan.get("score_explanation", []):
        body.append(paragraph_xml([run_xml(str(item))]))
    body.append(heading("To Reach Band 7.5 / 8.0", 2))
    for item in plan.get("focus_feedback", []):
        body.append(paragraph_xml([run_xml(str(item))]))
    body.append(page_break())
    model_paragraphs = plan.get("model_answer", [])
    if isinstance(model_paragraphs, str):
        model_paragraphs = [p.strip() for p in model_paragraphs.split("\n") if p.strip()]
    model_text = " ".join(str(p) for p in model_paragraphs)
    for idx, para in enumerate(model_paragraphs):
        body.append(paragraph_xml([run_xml(str(para))]))
        if idx < len(model_paragraphs) - 1:
            body.append(paragraph_xml([]))
    body.append(paragraph_xml([run_xml(f"({word_count(model_text)} words)")]))
    return "".join(body)


def apply_review_to_original_document_xml(
    document_bytes: bytes,
    plan: dict[str, Any],
    start_comment_id: int,
    include_visual_facts: bool = False,
) -> tuple[bytes, list[dict[str, Any]]]:
    register_document_namespaces(document_bytes.decode("utf-8"))
    document = ET.fromstring(document_bytes)
    body = document.find(qn(W_NS, "body"))
    if body is None:
        raise SystemExit("Could not find document body insertion point")
    paragraphs = [child for child in list(body) if child.tag == qn(W_NS, "p")]
    comment_ranges: dict[int, list[dict[str, Any]]] = {}
    rewrites: dict[int, list[str]] = {}
    new_comments: list[dict[str, Any]] = []
    unmatched: list[str] = []
    unmatched_targets: list[str] = []
    next_comment_id = start_comment_id
    search_from = 0
    allowed_positions = allowed_paragraph_positions(plan, len(paragraphs))

    for unit in plan.get("review_units", []):
        original = str(unit.get("original", "")).strip()
        if not original:
            continue
        unit_positions = unit_paragraph_positions(unit, len(paragraphs))
        match_positions = unit_positions or allowed_positions
        paragraph_idx = find_best_paragraph(paragraphs, original, search_from, match_positions)
        if paragraph_idx is None:
            unmatched.append(original[:100])
            continue
        paragraph_text = text_of(paragraphs[paragraph_idx])
        unit_span = find_loose_span(paragraph_text, original) or (0, len(paragraph_text))
        ranges = comment_ranges.setdefault(paragraph_idx, [])
        for comment in list(unit.get("comments", [])):
            comment_text = str(comment.get("text") or "").strip()
            if not comment_text:
                continue
            target = str(comment.get("target") or "").strip()
            span = find_loose_span(paragraph_text, target, unit_span) if target else None
            if span is None and target:
                span = find_loose_span(paragraph_text, target)
            if span is None and target:
                unmatched_targets.append(f"{target[:80]} -> {paragraph_text[:80]}")
                continue
            if span is None:
                span = unit_span
            usable_span = non_overlapping_span(paragraph_text, span[0], span[1], ranges)
            if usable_span is None:
                continue
            item = {
                "start": usable_span[0],
                "end": usable_span[1],
                "text": comment_text,
                "id": next_comment_id,
            }
            ranges.append(item)
            new_comments.append(item)
            next_comment_id += 1
        rewrite = str(unit.get("rewrite", "")).strip()
        if rewrite:
            rewrites.setdefault(paragraph_idx, []).append(rewrite)
        search_from = paragraph_idx

    if unmatched:
        joined = "; ".join(unmatched[:3])
        raise SystemExit(f"Could not anchor {len(unmatched)} review unit(s) in the original DOCX paragraphs: {joined}")
    if unmatched_targets:
        joined = "; ".join(unmatched_targets[:3])
        raise SystemExit(f"Could not anchor {len(unmatched_targets)} comment target(s) in the matched answer paragraph: {joined}")
    if plan.get("review_units") and not (new_comments or rewrites):
        raise SystemExit("No review units could be anchored in the original DOCX paragraphs")

    for paragraph_idx, ranges in comment_ranges.items():
        if ranges:
            replace_paragraph_runs(paragraphs[paragraph_idx], ranges)

    for paragraph_idx in sorted(rewrites):
        anchor = paragraphs[paragraph_idx]
        insert_at = list(body).index(anchor) + 1
        for rewrite in rewrites[paragraph_idx]:
            for child in parse_body_fragment(paragraph_xml([run_xml(rewrite, italic=True)])):
                body.insert(insert_at, child)
                insert_at += 1

    insert_body_fragment(body, review_tail_body_xml(plan, include_visual_facts=include_visual_facts))
    serialized = ET.tostring(document, encoding="unicode")
    serialized = restore_document_root_namespaces(serialized, document_bytes.decode("utf-8"))
    return serialized.encode("utf-8"), new_comments


def max_existing_comment_id(zf: ZipFile) -> int:
    if "word/comments.xml" not in zf.namelist():
        return -1
    root = ET.fromstring(zf.read("word/comments.xml"))
    ids = []
    for comment in root.findall(qn(W_NS, "comment")):
        cid = comment.get(qn(W_NS, "id"))
        if cid is not None and cid.isdigit():
            ids.append(int(cid))
    return max(ids) if ids else -1


def merge_comments_xml(existing: bytes | None, new_comments: list[dict[str, Any]], author: str) -> bytes:
    if existing:
        root = ET.fromstring(existing)
    else:
        root = ET.Element(qn(W_NS, "comments"))
    now = datetime.now(COMMENT_TZ).isoformat(timespec="seconds")
    for item in new_comments:
        comment = ET.SubElement(root, qn(W_NS, "comment"), {
            qn(W_NS, "id"): str(int(item["id"])),
            qn(W_NS, "author"): author,
            qn(W_NS, "date"): now,
            qn(W_NS, "initials"): "CE",
        })
        para = ET.SubElement(comment, qn(W_NS, "p"))
        ref_run = ET.SubElement(para, qn(W_NS, "r"))
        ref_pr = ET.SubElement(ref_run, qn(W_NS, "rPr"))
        ET.SubElement(ref_pr, qn(W_NS, "rStyle"), {qn(W_NS, "val"): "CommentReference"})
        ET.SubElement(ref_run, qn(W_NS, "annotationRef"))
        text_run = ET.SubElement(para, qn(W_NS, "r"))
        text_pr = ET.SubElement(text_run, qn(W_NS, "rPr"))
        ET.SubElement(text_pr, qn(W_NS, "rFonts"), {
            qn(W_NS, "ascii"): FONT,
            qn(W_NS, "hAnsi"): FONT,
            qn(W_NS, "cs"): FONT,
        })
        text_node = ET.SubElement(text_run, qn(W_NS, "t"))
        text_node.text = str(item["text"])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def ensure_comment_relationship(rels_bytes: bytes | None) -> bytes:
    root = ET.fromstring(rels_bytes) if rels_bytes else ET.Element(qn(PKG_REL_NS, "Relationships"))
    for rel in root.findall(qn(PKG_REL_NS, "Relationship")):
        if rel.get("Type") == "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments":
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    existing_ids = {rel.get("Id", "") for rel in root.findall(qn(PKG_REL_NS, "Relationship"))}
    next_num = 1
    while f"rId{next_num}" in existing_ids:
        next_num += 1
    ET.SubElement(root, qn(PKG_REL_NS, "Relationship"), {
        "Id": f"rId{next_num}",
        "Type": "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments",
        "Target": "comments.xml",
    })
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def ensure_comments_content_type(content_types_bytes: bytes) -> bytes:
    root = ET.fromstring(content_types_bytes)
    for override in root.findall(qn(CT_NS, "Override")):
        if override.get("PartName") == "/word/comments.xml":
            return ET.tostring(root, encoding="utf-8", xml_declaration=True)
    ET.SubElement(root, qn(CT_NS, "Override"), {
        "PartName": "/word/comments.xml",
        "ContentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml",
    })
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def default_output_path(input_path: Path | None) -> Path:
    if input_path:
        return input_path.with_name(f"{input_path.stem}(reviewed).docx")
    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    return Path("/Users/aaronliang/Desktop") / f"IELTS_Task1_Reviewed_{stamp}.docx"


def avoid_overwrite(path: Path) -> Path:
    if not path.exists():
        return path
    suffix = path.suffix
    stem = path.stem
    parent = path.parent
    if stem.endswith("(reviewed)"):
        prefix = stem[: -len("(reviewed)")]
        template = lambda n: parent / f"{prefix}(reviewed {n}){suffix}"
    else:
        template = lambda n: parent / f"{stem} {n}{suffix}"
    for n in range(2, 100):
        candidate = template(n)
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not find non-overwriting filename for {path}")


def write_docx(plan: dict[str, Any], output: Path, author: str, include_visual_facts: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    doc_xml, comments = document_xml(plan, include_visual_facts=include_visual_facts)
    with ZipFile(output, "w", ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml())
        zf.writestr("_rels/.rels", rels_xml())
        zf.writestr("docProps/app.xml", app_xml())
        zf.writestr("docProps/core.xml", core_xml())
        zf.writestr("word/_rels/document.xml.rels", document_rels_xml())
        zf.writestr("word/document.xml", doc_xml)
        zf.writestr("word/styles.xml", styles_xml())
        zf.writestr("word/comments.xml", comments_xml(comments, author))


def write_appended_docx(
    plan: dict[str, Any],
    input_docx: Path,
    output: Path,
    author: str,
    include_visual_facts: bool = False,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if input_docx.resolve() != output.resolve():
        shutil.copyfile(input_docx, output)
    if not allowed_paragraph_positions(plan, 10**9):
        extraction = extract_task1_docx(input_docx)
        indices = extraction.get("student_answer_paragraph_indices")
        if indices:
            plan = dict(plan)
            plan["student_answer_paragraph_indices"] = indices
        else:
            raise SystemExit("Could not determine student answer paragraph indices from input DOCX")
    with ZipFile(output, "r") as zin:
        existing = {name: zin.read(name) for name in zin.namelist()}
        start_comment_id = max_existing_comment_id(zin) + 1
    document_xml_bytes, new_comments = apply_review_to_original_document_xml(
        existing["word/document.xml"],
        plan,
        start_comment_id,
        include_visual_facts=include_visual_facts,
    )
    replacements = {
        "word/document.xml": document_xml_bytes,
        "word/comments.xml": merge_comments_xml(existing.get("word/comments.xml"), new_comments, author),
        "word/_rels/document.xml.rels": ensure_comment_relationship(existing.get("word/_rels/document.xml.rels")),
        "[Content_Types].xml": ensure_comments_content_type(existing["[Content_Types].xml"]),
    }
    with ZipFile(output, "w", ZIP_DEFLATED) as zout:
        for name, data in existing.items():
            zout.writestr(name, replacements.get(name, data))
        for name, data in replacements.items():
            if name not in existing:
                zout.writestr(name, data)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("review_json", type=Path)
    parser.add_argument("--input-docx", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--author", default="Cyber Esme")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--cleanup-plan", action="store_true")
    parser.add_argument(
        "--include-visual-facts",
        action="store_true",
        help="Include the internal visual facts note in the DOCX. By default it is used only to guide review decisions.",
    )
    args = parser.parse_args()
    plan = json.loads(args.review_json.read_text(encoding="utf-8"))
    output = args.output or default_output_path(args.input_docx)
    if not args.overwrite:
        output = avoid_overwrite(output)
    if args.input_docx:
        write_appended_docx(
            plan,
            args.input_docx,
            output,
            args.author,
            include_visual_facts=args.include_visual_facts,
        )
    else:
        write_docx(plan, output, args.author, include_visual_facts=args.include_visual_facts)
    print(output)
    if args.cleanup_plan:
        args.review_json.unlink()
        print(f"Deleted temporary review plan: {args.review_json}")


if __name__ == "__main__":
    main()
