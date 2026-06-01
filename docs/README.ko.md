<div align="center">
  <img src="../assets/ielts-skills-hero.svg" alt="IELTS Writing Review Skills" width="100%">

  <h1>IELTS Writing Review Skills</h1>

  <p>
    Codex 및 Claude Code용 IELTS Academic Writing Task 1 / Task 2 로컬 리뷰 skill입니다.
    DOCX 실제 코멘트, 공식 채점 기준, 교사 스타일 피드백, rewrite, model answer를 지원합니다.
  </p>

  <p>
    <a href="../README.md">简体中文</a>
    · <a href="./README.en.md">English</a>
    · <a href="./README.ja.md">日本語</a>
    · <a href="./README.ko.md"><strong>한국어</strong></a>
    · <a href="./README.es.md">Español</a>
  </p>
</div>

## 이 저장소 소개

이 저장소는 로컬 AI agent에서 IELTS Writing을 검토하기 위한 두 개의 skill을 제공합니다. 단순한 일반 첨삭이 아니라 과제와 학생 답안을 구분하고, Word 실제 코멘트를 삽입하며, 공식 IELTS band descriptors에 따라 채점하고, 간결한 rewrite와 model answer를 생성합니다.

**기본 목표 band는 7.5입니다.** 목표 band를 따로 지정하지 않으면 두 skill은 model answer와 피드백을 안정적인 Band 7.5 수준에 맞춥니다. prompt에 `Target band: 7.0` 또는 `Target band: 8.0`처럼 적어 변경할 수 있습니다.

| Skill | 용도 | 기본 출력 |
| --- | --- | --- |
| `$ielts-task1-review` | Academic Task 1 그래프, 표, 지도, 과정, 복합 시각 자료 | 코멘트가 포함된 reviewed DOCX, 점수, 피드백, 4문단 Band 7.5 model answer |
| `$ielts-task2-review` | Task 2 의견형, 토론형, 문제해결형, 장단점형, 복합 essay | 코멘트가 포함된 reviewed DOCX, 점수, 피드백, 4문단 Band 7.5 model essay |

## 설치

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

## Prompt 예시

```text
Use $ielts-task1-review to review my IELTS Academic Writing Task 1 answer: [paste the path of your answer]
```

```text
Use $ielts-task2-review to review my IELTS Writing Task 2 essay: [paste the path of your essay]
```

```text
Use $ielts-task2-review to review my IELTS Writing Task 2 essay. Target band: [your target band]. File: [paste the path of your essay]
```
