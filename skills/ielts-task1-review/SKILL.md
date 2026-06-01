---
name: ielts-task1-review
description: Use this skill to review IELTS Academic Writing Task 1 answers in a specific teacher's style. Trigger when the user asks for IELTS Task 1 correction, chart/table/map/process description review, Band 7 or 7.5 improvement, teacher-style marking, reviewed Word DOCX output, comments on a Task 1 answer, or a full Task 1 model answer based on a student's draft and visual prompt. Supports .docx input containing an embedded chart image and pasted text with an attached image or image path.
---

# IELTS Task 1 Review

## Core Rule

Analyze the visual prompt before correcting the student's writing. For Task 1, accurate chart/table/map/process understanding is part of Task Achievement, so do not polish language before identifying the main features.

Use these references in order:

1. Read `references/visual_analysis_protocol.md` to inspect the visual.
2. Read `references/teacher_style.md` for Task 1 teacher-style marking.
3. Read `references/ielts_task1_band_descriptors.md` before scoring.
4. Use `references/teacher_samples_index.md` to find relevant samples, then read full samples from `references/teacher_samples/` when useful.
5. Use `references/review_format.md` for DOCX layout and cleanup rules.

## Workflow

1. Identify the prompt, embedded image, and student answer.
   - For `.docx`, extract embedded images with `scripts/extract_docx_images.py`.
   - Inspect the extracted image directly before reviewing. This is mandatory: never score or rewrite a Task 1 answer from the text alone.
   - For `.docx`, also run `scripts/extract_task1_input.py` so the review plan can distinguish prompt text from student answer paragraphs.
   - For pasted text, require an image attachment or image path.
2. Build an internal visual facts note.
   - Identify visual type, units, categories, time periods, axes, legends, stages, and key values.
   - Identify overview-level features before local details.
   - Keep this note internal unless the user explicitly asks to see it.
3. Check the student's Task Achievement.
   - Mark inaccurate chart type, wrong units, missing overview, wrong key feature selection, inaccurate values, or irrelevant details in comments.
4. Select the closest teacher samples by visual type before writing comments.
   - First classify the new task as bar chart, line graph, table, pie chart, map, process, or mixed visual.
   - Use `references/teacher_samples_index.md` to find similar sample files, then inspect one or two matching full samples.
   - Prefer same visual type and same main challenge, such as trend comparison, proportions, maps, process sequencing, or mixed table/chart reporting.
5. Split the answer into review units.
   - Use sentence-level units for grammar, articles, plural forms, data phrasing, collocation, and formal wording.
   - Use paragraph-level units for overview errors, poor grouping, data misreading, map/process sequencing, or missing comparisons.
6. Add teacher-style comments.
   - Use short English comments anchored to specific words or phrases.
   - Use comments like `Specify type: bar chart`, `mention proportions`, `slightly repetitive`, `formal`, `Use comma`, `This is stated in overview`.
7. Add italic rewrites after relevant units.
   - Rewrites must be concise, formal, data-accurate, and Band 7/7.5 appropriate.
8. Score the student's original answer strictly using official Task 1 descriptors.
   - Score Task Achievement, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, and estimated overall band.
9. Give concise Band 7 / 7.5-oriented feedback.
   - Mention blockers for stable Band 7 first.
   - Then mention the most useful move toward 7.5.
10. Write a 150-200 word model answer at a stable Band 7.5 standard.
   - Use exactly four paragraphs:
     1. Introduction: paraphrase the task prompt.
     2. Overview: begin with `Overall` and summarize the main features.
     3. Body paragraph 1: report the first logical group of details.
     4. Body paragraph 2: report the second logical group of details.
   - Leave one blank line between model answer paragraphs in the output DOCX.
   - Align it with the visual and official criteria.
   - Correct any inaccurate visual interpretation.
   - It must be strong enough for Band 7.5: clear overview, accurate key feature selection, logical grouping, precise data language, natural comparisons, and consistently controlled grammar.
   - Keep it realistic and teacher-like, not an over-complex Band 9 answer.
11. Generate a reviewed `.docx` by default.
   - For input `MyAnswer.docx`, output `MyAnswer(reviewed).docx` in the same folder unless the user specifies another path.
   - For DOCX input, create the reviewed file by copying the original DOCX first.
   - Write comments directly into the copied original answer paragraphs; do not create a second copy of the student's answer for comments.
   - Insert italic rewrites immediately after the matched original answer paragraph.
   - Keep the original prompt and embedded visual in place; do not repeat the task prompt or image.
   - For pasted text, output to `/Users/aaronliang/Desktop/IELTS_Task1_Reviewed_YYYYMMDD_HHMM.docx`.
   - Use Times New Roman for all added review text and comments.
   - Use `Cyber Esme` as the Word comment author.
   - Do not include a visible `Visual Facts` section unless the user asks for it or `--include-visual-facts` is intentionally used.
   - Do not add big visible section headings such as `Task`, `Reviewed Answer`, `Score`, or `Model Answer`.
   - Preserve the original `word/document.xml` root namespace declarations and `mc:Ignorable`; do not leave undeclared prefixes such as `w14`, `w15`, `w16*`, or `wp14`.
   - Insert a page break before the score and feedback page; keep the score lines and `To Reach Band 7 / 7.5` together; insert another page break before the model answer.
   - Never overwrite the original answer unless explicitly requested.
12. Clean up temporary byproducts after a successful review.
   - Delete temporary files such as `review_plan_*.json`, extracted scratch images, and unpacked DOCX folders.
   - `scripts/extract_docx_images.py` creates a unique `/private/tmp/ielts_task1_images_*` directory by default; delete that scratch directory after validation.
   - Do not delete source answers, final reviewed DOCX files, or bundled reference files.

## Bundled Resources

- `references/visual_analysis_protocol.md`: checklist for charts, tables, maps, processes, and mixed visuals.
- `references/teacher_style.md`: Task 1 teacher-style rules distilled from samples.
- `references/teacher_samples_index.md`: sample index with image files and counts.
- `references/teacher_samples/*.json` and `*.md`: full extracted teacher-reviewed samples.
- `references/sample_images/*`: extracted visual prompts from the 12 sample DOCX files.
- `references/ielts_task1_band_descriptors.md`: complete Task 1 descriptors extracted from the local PDF.
- `references/review_format.md`: canonical reviewed document structure.
- `scripts/extract_docx_images.py`: extract visual prompts from new input DOCX files to a unique scratch directory by default.
- `scripts/extract_task1_input.py`: extract prompt, student answer, and student answer paragraph indices from a Task 1 DOCX.
- `scripts/create_task1_review_docx.py`: create a reviewed DOCX from a JSON review plan; DOCX input is copied first, comments are anchored into extracted student answer paragraphs, and score/model sections are appended.
- `scripts/create_and_validate_task1_review.py`: create a reviewed DOCX, validate it, and clean extracted scratch images in one command.
- `scripts/validate_task1_review_docx.py`: verify comments, italic rewrites, student-answer paragraph comment anchoring when `--input-docx` is supplied, root namespace compatibility, page breaks, font, author, score lines, retained `To Reach Band 7 / 7.5` title, removed old headings, and model answer length/four-paragraph structure.
- `scripts/extract_task1_teacher_samples.py`: regenerate teacher sample references.
- `scripts/extract_task1_band_descriptors.py`: regenerate descriptors from the PDF.

## JSON Review Plan For DOCX Creation

When using `scripts/create_task1_review_docx.py`, first produce a JSON file with this shape:

```json
{
  "prompt": "Task prompt or visual prompt summary",
  "student_answer_paragraph_indices": [4, 6, 8, 10],
  "visual_facts": ["Internal visual facts used for accuracy. These are not shown in the DOCX by default."],
  "review_units": [
    {
      "original": "Student sentence or paragraph.",
      "comments": [{"target": "specific phrase", "text": "Short teacher-style comment"}],
      "rewrite": "Italic teacher-style improvement."
    }
  ],
  "scores": {
    "Task Achievement": "6.5",
    "Coherence & Cohesion": "7",
    "Lexical Resource": "6.5",
    "Grammatical Range & Accuracy": "6.5",
    "Overall": "6.5"
  },
  "score_explanation": ["Short evidence-based scoring note."],
  "focus_feedback": ["Focus on overview accuracy and natural comparisons."],
  "model_answer": [
    "Paragraph 1: introduction/paraphrase.",
    "Paragraph 2: Overall ...",
    "Paragraph 3: first detail group.",
    "Paragraph 4: second detail group."
  ]
}
```

Then run:

```bash
python scripts/create_task1_review_docx.py review_plan.json --input-docx MyAnswer.docx --cleanup-plan
python scripts/validate_task1_review_docx.py "MyAnswer(reviewed).docx" --input-docx MyAnswer.docx
```

For a DOCX workflow with automatic image scratch cleanup, run:

```bash
python scripts/create_and_validate_task1_review.py review_plan.json --input-docx MyAnswer.docx
```

If the review plan is a permanent example/reference file, omit `--cleanup-plan`. Use `--include-visual-facts` only when the user explicitly asks to see the visual facts note in the reviewed DOCX.

## Quality Bar

- The visual must be inspected before scoring or rewriting.
- Similar teacher samples should be selected by visual type before writing the final comments and model answer.
- Comments must stay within the extracted student answer paragraphs; prompt text and image captions are not valid anchor targets.
- The reviewed DOCX must contain real Word comments, not bracketed notes.
- Important Task Achievement issues must be commented first.
- Italic rewrites must be data-accurate.
- The score must evaluate the original answer.
- The model answer must be exactly 4 paragraphs with one blank line between paragraphs, 150-200 words, and should stand securely at Band 7.5 according to the official Task 1 descriptors.
- The style should look closer to the teacher's Task 1 samples than to a generic IELTS tutor.
