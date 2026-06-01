# Reviewed DOCX Format

Use this structure for every reviewed IELTS Academic Task 1 document.

## Sections

1. Original DOCX content
   - Keep the student's original file content at the start of the reviewed DOCX.
   - For DOCX input, this preserves the original prompt and embedded visual, so do not repeat them.
2. Internal visual facts note
   - Build this before reviewing, but do not show it in the DOCX by default.
   - Include a visible `Visual Facts` section only if the user explicitly asks for it.
3. Reviewed answer content
   - Use `review_units.original` to locate the matching original answer paragraph in the copied DOCX.
   - Word comments must be anchored directly to specific target words/phrases inside the original paragraph.
   - For DOCX input, the matched paragraph must be one of the extracted student answer paragraphs.
   - Do not append a second copy of the student's answer just to hold comments.
   - Insert the italic rewrite immediately after the matched original paragraph when useful.
   - Do not use a visible `Reviewed Answer` heading.
4. Score lines and focused feedback
   - Start this page after the reviewed answer content.
   - Do not use a visible `Score` heading.
   - Task Achievement
   - Coherence & Cohesion
   - Lexical Resource
   - Grammatical Range & Accuracy
   - Overall
5. `To Reach Band 7 / 7.5`
   - This is the only visible section title retained after the answer review.
   - Keep this on the same page as the score lines.
   - Mention blockers for stable Band 7 first.
   - Then mention the most useful move toward 7.5.
6. Model answer
   - Start this on a new page after the score/focus page.
   - Do not use a visible `Model Answer` heading.
   - 150-200 words.
   - Exactly 4 paragraphs:
     1. Introduction: paraphrase the task prompt.
     2. Overview: begin with `Overall` and summarize the main features.
     3. Body paragraph 1: report the first logical group of details.
     4. Body paragraph 2: report the second logical group of details.
   - Leave one blank line between model answer paragraphs.
   - Accurate to the visual.
   - Stable Band 7.5 standard: clear overview, well-selected key features, logical grouping, precise data language, and controlled grammar.

## Filename Rules

- DOCX input: output beside the input file.
  - `MyAnswer.docx` -> `MyAnswer(reviewed).docx`
  - If that exists, use `MyAnswer(reviewed 2).docx` or another non-overwriting variant.
- Pasted text input: output to `/Users/aaronliang/Desktop/IELTS_Task1_Reviewed_YYYYMMDD_HHMM.docx`.
- Never overwrite the original answer unless explicitly requested.

## Comment Rules

- Use real Word comments.
- Use `Cyber Esme` as the Word comment author.
- Anchor comments to the shortest useful phrase.
- For DOCX input, comments must be placed in the copied original answer paragraphs, not in newly appended duplicate answer text.
- Do not anchor comments to prompt text, image captions, score sections, model answers, or other non-answer paragraphs.
- If a non-empty `target` cannot be found inside the matched answer paragraph, fix the review plan instead of falling back to the whole paragraph.
- Use English.
- Mark Task Achievement problems early: wrong chart type, wrong units, missing overview, inaccurate values, or poor key feature selection.

## Font And Pagination Rules

- Use Times New Roman for all added review text and comments.
- Preserve the copied DOCX's original `word/document.xml` root namespace declarations and `mc:Ignorable` prefix list.
- Do not include `Visual Facts` in the reviewed DOCX unless specifically requested.
- Do not add big visible section headings such as `Task`, `Reviewed Answer`, `Score`, or `Model Answer`.
- Insert a page break before the score and feedback page.
- Keep the score lines and `To Reach Band 7 / 7.5` together.
- Insert another page break before the model answer.

## Cleanup Rules

- Remove temporary files created only for the review process after final DOCX validation.
- Typical byproducts: `review_plan_*.json`, `/private/tmp/ielts_task1_images_*` scratch image folders, temporary unpacked DOCX folders.
- Prefer writing temporary files to `/private/tmp`.
- Do not delete source answers, final reviewed DOCX files, or bundled Skill references.
