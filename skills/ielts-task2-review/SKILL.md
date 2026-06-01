---
name: ielts-task2-review
description: Use this skill to review IELTS Writing Task 2 essays in a specific teacher's style. Trigger when the user asks for IELTS Task 2 correction, Band 7 or 7.5 improvement, teacher-style essay marking, reviewed Word DOCX output, comments on a Task 2 essay, or a full Task 2 model essay based on a student's draft. Supports both pasted prompt+essay text and simple .docx input containing the task prompt and student essay.
---

# IELTS Task 2 Review

## Core Rule

Imitate the teacher's marking style before giving generic IELTS advice. Use the full teacher samples and the official descriptors as the two authorities:

1. Read `references/teacher_style.md` before reviewing.
2. Read `references/ielts_task2_band_descriptors.md` before scoring.
3. Use `references/teacher_samples_index.md` to find relevant sample files, then read specific full samples from `references/teacher_samples/` when needed.
4. Use `references/review_format.md` for the output structure.

## Workflow

1. Identify the Task 2 prompt and the student's essay.
   - Normal DOCX input should be an unreviewed student file containing the prompt, optional outline, and the student's essay.
   - For a `.docx`, first run `scripts/extract_task2_input.py` to separate the prompt, optional outline, and student essay.
   - Preserve `student_essay_paragraph_indices` from the extraction result and include it in the review plan.
   - Treat short outline bullets after the prompt as planning notes, not as the scored essay.
   - Existing comments, italic rewrites, feedback, or model essays are not expected in normal use. If they are detected, treat them as accidental leftover material only; do not score, rewrite, or copy them as part of the student's essay.
   - For pasted text, separate prompt and essay from headings, blank lines, or explicit labels.
2. Check task fit before polishing language.
   - If the essay content, position, or logic is significantly off-topic, mark this first in comments.
   - Later italic rewrites and the final model essay must redirect the mistaken idea back to the task.
3. Select relevant teacher samples before writing comments.
   - Use `scripts/find_teacher_sample.py` with the input filename or prompt.
   - The script normalizes spaces/underscores, so `C17T3 Writing Task 2.docx` maps to `C17T3_Writing_Task_2.json`.
   - If the exact file sample is not relevant, use `references/teacher_samples_index.md` and the prompt wording to choose a closer sample.
4. Split the essay into review units.
   - Use sentence-level units when problems are local.
   - Use paragraph-level units when logic, task response, or coherence needs bigger repair.
5. Add teacher-style comments.
   - Comments must be short, English, practical, and anchored to specific words or phrases.
   - A non-empty comment target must match text inside the selected student essay paragraph; do not fall back to prompt, outline, or the whole wrong paragraph.
   - Prefer concrete notes: `informal`, `repetition`, `unnatural`, `could be more concise`, `Careful with articles`, `Off-topic`, `This is vague`.
6. Add italic rewrites after the relevant original unit.
   - Rewrites should be concise, formal, natural, and Band 7/7.5 appropriate.
   - Avoid making the essay sound like an over-polished Band 9 sample.
7. Score the student's original essay strictly using official Task 2 descriptors.
   - Score Task Response, Coherence & Cohesion, Lexical Resource, Grammatical Range & Accuracy, and estimated overall band.
   - Do this before giving improvement advice.
8. Give concise Band 7 / 7.5-oriented feedback.
   - Separate issues blocking stable Band 7 from improvements needed to move toward 7.5.
   - Keep this section short, like the teacher samples.
9. Write a 250-300 word model essay at a stable Band 7.5 standard.
   - Use exactly four paragraphs:
     1. Introduction: paraphrase the prompt and state the essay's position.
     2. Body paragraph 1.
     3. Body paragraph 2.
     4. Conclusion: begin with `In conclusion`.
   - Leave one blank line between model essay paragraphs in the output DOCX.
   - Align it with the official criteria.
   - Preserve the student's main position when it is on-topic and defensible.
   - Correct any flawed or off-topic logic from the original draft.
   - It must be strong enough for Band 7.5: a clear and sustained position, relevant and sufficiently developed support, logical paragraph progression, natural topic vocabulary, and frequent error-free sentences.
   - Keep it realistic and teacher-like, not an over-polished Band 9 essay.
10. Generate a reviewed `.docx` by default.
   - For input `MyEssay.docx`, output `MyEssay(reviewed).docx` in the same folder unless the user specifies another path.
   - For DOCX input, create the reviewed file by copying the original DOCX first.
   - Write comments directly into the copied original essay paragraphs; do not create a second copy of the student's essay for comments.
   - Anchor comments only inside extracted student essay paragraphs, never inside prompt or outline paragraphs.
   - Insert italic rewrites immediately after the matched original essay paragraph.
   - Keep the original prompt and student essay in place; do not repeat the task prompt.
   - For pasted text, output to `/Users/aaronliang/Desktop/IELTS_Task2_Reviewed_YYYYMMDD_HHMM.docx`.
   - Use Times New Roman for all added review text and comments.
   - Use `Cyber Esme` as the Word comment author.
   - Do not add big visible section headings such as `Task`, `Reviewed Essay`, `Score`, or `Model Essay`.
   - Preserve the original `word/document.xml` root namespace declarations and `mc:Ignorable`; do not leave undeclared prefixes such as `w14`, `w15`, `w16*`, or `wp14`.
   - Insert a page break before the score and feedback page; keep the score lines and `To Reach Band 7 / 7.5` together; insert another page break before the model essay.
   - Never overwrite the original essay unless explicitly requested.
11. Clean up temporary byproducts after a successful review.
   - Delete temporary review plan files such as `review_plan_c17t3.json`.
   - Prefer creating review plans in `/private/tmp` or use `--cleanup-plan` when running `scripts/create_review_docx.py`.
   - Do not delete source essays, final reviewed `.docx` files, or bundled reference files.

## Bundled Resources

- `references/teacher_style.md`: teacher imitation rules distilled from the 11 samples.
- `references/teacher_samples_index.md`: prompt and count index for all samples.
- `references/teacher_samples/*.json` and `*.md`: full extracted teacher-reviewed samples.
- `references/ielts_task2_band_descriptors.md`: complete Task 2 descriptors extracted from the local PDF.
- `references/review_format.md`: canonical reviewed document structure.
- `scripts/extract_task2_input.py`: extract prompt, optional outline, and student essay from a Task 2 DOCX; it also protects against accidental leftover reviewed content.
- `scripts/find_teacher_sample.py`: find matching bundled teacher samples using normalized filename and prompt overlap.
- `scripts/create_review_docx.py`: create a reviewed DOCX from a JSON review plan; DOCX input is copied first, comments are anchored into extracted student essay paragraphs, and score/model sections are appended.
- `scripts/validate_review_docx.py`: verify comments, italic rewrites, student-essay paragraph comment anchoring when `--input-docx` is supplied, root namespace compatibility, score lines, retained `To Reach Band 7 / 7.5` title, removed old headings, and model essay length/four-paragraph structure.
- `scripts/extract_teacher_samples.py`: regenerate sample references from the 11 source DOCX files.
- `scripts/extract_task2_band_descriptors.py`: regenerate descriptors from the PDF.

## JSON Review Plan For DOCX Creation

When using `scripts/create_review_docx.py`, first produce a JSON file with this shape:

```json
{
  "prompt": "Task prompt",
  "student_essay_paragraph_indices": [12, 14, 16, 18],
  "review_units": [
    {
      "original": "Student sentence or paragraph.",
      "comments": [{"target": "specific phrase", "text": "Short teacher-style comment"}],
      "rewrite": "Italic teacher-style improvement."
    }
  ],
  "scores": {
    "Task Response": "6.5",
    "Coherence & Cohesion": "7",
    "Lexical Resource": "6.5",
    "Grammatical Range & Accuracy": "6.5",
    "Overall": "6.5"
  },
  "score_explanation": ["Short evidence-based scoring note."],
  "focus_feedback": ["Focus on grammar accuracy and natural collocations."],
  "model_essay": [
    "Paragraph 1: introduction with paraphrase and position.",
    "Paragraph 2: body paragraph 1.",
    "Paragraph 3: body paragraph 2.",
    "Paragraph 4: In conclusion, ..."
  ]
}
```

Then run:

```bash
python scripts/create_review_docx.py review_plan.json --input-docx MyEssay.docx --cleanup-plan
python scripts/validate_review_docx.py "MyEssay(reviewed).docx" --input-docx MyEssay.docx
```

For pasted text, omit `--input-docx` and the script will default to the Desktop output path.
If the review plan is a permanent example/reference file, omit `--cleanup-plan`.

## Quality Bar

- The reviewed DOCX must contain real Word comments, not plain bracketed notes.
- At least the most important local issues must be anchored to specific text.
- Italic rewrites must appear after the original unit.
- The score must evaluate the original essay, not the revised essay.
- The model essay must be exactly 4 paragraphs with one blank line between paragraphs, 250-300 words, and should stand securely at Band 7.5 according to the official Task 2 descriptors.
- The style should look closer to the teacher's samples than to a generic IELTS tutor.
- Temporary files from the review process should be removed after successful validation.
