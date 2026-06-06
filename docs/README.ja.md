<div align="center">
  <img src="../assets/ielts-writing-review-skills-hero.png" alt="IELTS Writing Review Skills" width="100%">

  <h1>IELTS Writing Review Skills</h1>

  <p>
    Codex と Claude Code 向けの IELTS Academic Writing Task 1 / Task 2 ローカルレビュー skill。
    DOCX の本物のコメント、公式基準での採点、教師風フィードバック、書き換え、モデル答案に対応します。
  </p>

  <p>
    <a href="../README.md">简体中文</a>
    · <a href="./README.en.md">English</a>
    · <a href="./README.ja.md"><strong>日本語</strong></a>
    · <a href="./README.ko.md">한국어</a>
    · <a href="./README.es.md">Español</a>
  </p>
</div>

## このリポジトリについて

このリポジトリには、IELTS Writing をローカル AI agent でレビューするための 2 つの skill が含まれています。一般的な添削ではなく、課題と学生答案を判別し、Word の実コメントを挿入し、公式 IELTS band descriptors に基づいて採点し、短い改善 rewrite とモデル答案を生成します。

**デフォルト目標は、斜体 rewrite が安定した Band 7.5、最後のモデル答案が安定した Band 8.0 です。** 目標 band を指定しない場合、局所的な rewrite は Band 7.5、最後の model answer / model essay は Band 8.0 に合わせられます。`Target band: 7.5` や `Target band: 8.0` のように prompt で変更できます。

| Skill | 用途 | デフォルト出力 |
| --- | --- | --- |
| `$ielts-task1-review` | Academic Task 1 のグラフ、表、地図、プロセス、複合図表 | コメント付き reviewed DOCX、採点、フィードバック、Band 7.5 の斜体 rewrite、4 段落の Band 8.0 モデル答案 |
| `$ielts-task2-review` | Task 2 の意見、議論、問題解決、利点欠点、複合型 essay | コメント付き reviewed DOCX、採点、フィードバック、Band 7.5 の斜体 rewrite、4 段落の Band 8.0 モデル essay |

## インストール

```bash
git clone https://github.com/AaronL725/ielts-writing-review-skills.git
cd ielts-writing-review-skills
```

Codex:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/ielts-task1-review skills/ielts-task2-review "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/ielts-task1-review skills/ielts-task2-review "$HOME/.claude/skills/"
```

Universal install prompt:

```text
Install the IELTS Writing Review Skills from this GitHub repository: https://github.com/AaronL725/ielts-writing-review-skills and put the two skills into the correct local skills directory.
```

## Prompt 例

```text
Use $ielts-task1-review to review my IELTS Academic Writing Task 1 answer: [paste the path of your answer]
```

```text
Use $ielts-task2-review to review my IELTS Writing Task 2 essay: [paste the path of your essay]
```

```text
Use $ielts-task2-review to review my IELTS Writing Task 2 essay. Target band: [your target band]. File: [paste the path of your essay]
```
