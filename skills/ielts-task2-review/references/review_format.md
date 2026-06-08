# Reviewed DOCX Format

Use this structure for every reviewed IELTS Task 2 document.

## Sections

1. Original DOCX content
   - Keep the student's original file content at the start of the reviewed DOCX.
   - For DOCX input, this preserves the original prompt and student essay, so do not repeat the prompt.
2. Reviewed essay content
   - Use `review_units.original` to locate the matching original essay paragraph in the copied DOCX.
   - Word comments must be anchored directly to specific target words/phrases inside the original paragraph.
   - For DOCX input, the matched paragraph must be one of the extracted student essay paragraphs, not the prompt or outline.
   - Do not append a second copy of the student's essay just to hold comments.
   - Insert the italic rewrite immediately after the matched original paragraph when improvement is useful.
   - Do not use a visible `Reviewed Essay` heading.
3. Score lines and focused feedback
   - Start this page after the reviewed essay content.
   - Do not use a visible `Score` heading.
   - Task Response
   - Coherence & Cohesion
   - Lexical Resource
   - Grammatical Range & Accuracy
   - Overall
   - Each score may be a whole or half band; do not round criterion estimates to integers.
   - One or a few short evidence-based scoring notes.
4. `To Reach Band 7.5 / 8.0`
   - This is the only visible section title retained after the essay review.
   - Concise focus list.
   - Mention blockers preventing stable Band 7.5 first.
   - Then mention the most useful move toward 8.0.
5. Model essay
   - Start this on a new page after the score and focus feedback page.
   - Do not use a visible `Model Essay` heading.
   - 250-300 words.
   - Exactly 4 paragraphs:
     1. Introduction: paraphrase the prompt and state the essay's position.
     2. Body paragraph 1.
     3. Body paragraph 2.
     4. Conclusion: begin with `In conclusion`.
   - Leave one blank line between model essay paragraphs.
   - Use the student's core ideas where possible.
   - Correct off-topic or flawed logic.
   - Stable Band 8.0 standard: clear and well-developed position, relevant and well-extended support, well-managed cohesion, flexible topic vocabulary, and mostly error-free grammar.

## Filename Rules

- DOCX input: output beside the input file.
  - `MyEssay.docx` -> `MyEssay(reviewed).docx`
  - If that exists, use `MyEssay(reviewed) 2.docx` or another non-overwriting variant.
- Pasted text input: output to `/Users/aaronliang/Desktop/IELTS_Task2_Reviewed_YYYYMMDD_HHMM.docx`.
- Never overwrite the original essay unless explicitly requested.

## Input Parsing Rules

- Normal DOCX input should be an unreviewed student file containing only the prompt, optional outline, and student essay.
- For DOCX input, run `scripts/extract_task2_input.py` before reviewing.
- Exclude outline/planning bullets from the scored essay.
- Existing comments, italic rewrites, feedback, or a model essay are accidental leftovers, not normal input. If detected, ignore them for scoring and rewriting; score only the student's original essay.
- Use `scripts/find_teacher_sample.py` to avoid filename mismatch between names with spaces and bundled samples with underscores.

## Cleanup Rules

- Remove temporary files created only for the review process after the final DOCX passes validation.
- Typical byproducts include `review_plan_*.json`, scratch extracted text files, or temporary unpacked DOCX folders.
- Prefer writing temporary files to `/private/tmp`.
- Do not delete the source essay, the final reviewed DOCX, or bundled Skill reference files.

## Comment Rules

- Use real Word comments.
- Use `Cyber Esme` as the Word comment author.
- Anchor comments to the shortest useful phrase.
- For DOCX input, comments must be placed in the copied original essay paragraphs, not in newly appended duplicate essay text.
- Do not anchor comments to prompt text, outline bullets, score sections, model essays, or other non-essay paragraphs.
- If a non-empty `target` cannot be found inside the matched essay paragraph, fix the review plan instead of falling back to the whole paragraph.
- Use English.
- Keep comments short and teacher-like.
- If a comment applies to a whole sentence because the issue is logic or task response, anchor it to the most problematic phrase or the first key phrase.

## Rewrite Rules

- Italicize rewritten sentences/paragraphs.
- Put the italic rewrite after the original unit.
- Do not rewrite every sentence when the original is already acceptable.
- Rewrites should reach a stable Band 7.5 standard while staying close to the student's intended meaning.
- Prefer focused, realistic improvements over a complete Band 9 transformation.

## Font And Pagination Rules

- Use Times New Roman for all added review text and comments.
- Keep the copied original document content at the start.
- Preserve the copied DOCX's original `word/document.xml` root namespace declarations and `mc:Ignorable` prefix list.
- Do not add big visible section headings such as `Task`, `Reviewed Essay`, `Score`, or `Model Essay`.
- Insert a page break before the score and feedback page.
- Keep the score lines and `To Reach Band 7.5 / 8.0` together after that page break.
- Insert another page break before the model essay.
