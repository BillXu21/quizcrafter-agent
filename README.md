# QuizCrafter – Multi-Agent Practice Quiz Generator

QuizCrafter is a multi-agent system that generates practice quizzes from lecture notes, topic lists, or existing practice exams. It produces original questions along with hints and detailed step-by-step solutions to help students study more effectively.

This project is built using Google's **Agent Development Kit (ADK)** as part of the **5-Day AI Agents Intensive – Capstone Project** in the **Agents for Good** track.

---

## ✨ Overview

Students often prepare for exams with:

* Lecture slides or notes
* One or two past exams
* Very limited practice questions

Writing additional questions by hand is slow and mentally exhausting. It also requires writing full solutions, which many students skip.

**QuizCrafter** turns raw study material into a complete practice quiz in minutes:

* Reads lecture notes, slides, or topic lists (from pasted text or files)
* Designs a quiz blueprint: topics, question types, difficulty mix
* Generates questions, hints, and detailed solutions
* Exports the quiz to **Markdown** so you can study or print

---

## 🧠 Problem Statement

Most students have **more content than questions**:

* Slides explain concepts but rarely include enough practice problems
* Past exams offer limited coverage and sometimes mismatched difficulty
* Writing your own practice problems takes time you don’t have

This leads to:

* Gaps in topic coverage
* Less targeted practice
* Lower confidence before exams

Students need a way to quickly transform their own notes into high-quality practice quizzes.

---

## ✅ Solution Statement

QuizCrafter uses a small team of AI agents to automate quiz creation:

1. **Analyze materials** – extract key topics, formulas, and question patterns
2. **Plan the quiz** – decide number of questions, difficulty mix, and topic coverage
3. **Write the quiz** – produce questions, hints, and detailed solutions in Markdown
4. **Optionally save** the quiz to a `.md` file for later use

The system focuses on being:

* **Simple** – one pipeline to run, no complex configuration
* **Flexible** – works with lecture notes, topic lists, or existing quizzes
* **Educational** – detailed solutions that show reasoning, not just final answers

---

## 🏗 Architecture

QuizCrafter is implemented as a **workflow agent** using ADK’s `SequentialAgent`:

```text
root_agent = SequentialAgent(
    name="quiz_buddy_pipeline",
    sub_agents=[
        materials_agent,
        planner_agent,
        writer_agent,
    ],
)
```

### 1. `materials_agent`

**Type:** `LlmAgent`
**Purpose:** Load and summarize study materials.

Responsibilities:

* Accepts:

  * Pasted text (lecture notes, slides, old quizzes), and/or
  * File patterns like `examples/*.txt`, `notes/week3/*.md`
* Uses the **`load_text_files`** tool to read multiple files and combine them
* Produces a **study material summary**:

  * Key topics
  * Important formulas and definitions
  * Typical exam question styles

The summary is written into `study_material_summary` in the session state, making it available to downstream agents.

---

### 2. `planner_agent`

**Type:** `LlmAgent`
**Purpose:** Design a quiz blueprint based on the summary and user preferences.

Responsibilities:

* Receives:

  * The user’s goal (e.g., “Calc III midterm practice”, “concept review”)
  * `{study_material_summary}` from the previous agent
* Produces a **JSON quiz plan**, stored as `quiz_plan_json`, containing:

  * `total_questions`
  * `question_types` (e.g., `multiple_choice`, `short_answer`, `free_response`)
  * `difficulty_mix` (`easy`, `medium`, `hard`)
  * `topics` list with weights and target skills

This blueprint describes *what kind* of questions should be generated, but not the questions themselves.

---

### 3. `writer_agent`

**Type:** `LlmAgent`
**Purpose:** Generate the full quiz in Markdown, including hints and solutions.

Responsibilities:

* Receives:

  * Quiz plan: `{quiz_plan_json}`
  * Material summary: `{study_material_summary}`
* Writes a complete quiz in **Markdown** with:

1. A title (e.g., `# Practice Quiz: Calc III – Vector Calculus`)
2. An instructions section (time suggestions, allowed tools if specified)
3. A list of questions:

   * Labels `Q1`, `Q2`, …
   * Difficulty tags (Easy / Medium / Hard)
   * Topic tags (from the quiz plan)
   * For MCQ: 4 options (A–D) and exactly one correct answer
4. A **Hints** section with optional hints per question
5. A **Solutions** section with **step-by-step solutions** for each question

The final Markdown is stored in `quiz_markdown` in the session state.

The `writer_agent` can optionally call the `save_quiz_to_markdown` tool to write the quiz out as a `.md` file.

---

## 🛠 Tools

QuizCrafter uses two custom tools to demonstrate ADK tool integration.

### `load_text_files(glob_pattern: str)`

* Reads all files matching a glob pattern (e.g., `examples/*.txt`)
* Attempts UTF-8, falls back to latin-1 if needed
* Returns:

  * `files`: list of file paths loaded
  * `combined_text`: concatenated content of all files

Used by `materials_agent` to pull in lecture notes, slides, or existing quizzes.

---

### `save_quiz_to_markdown(markdown_content: str, output_path: str = "quiz_output.md")`

* Writes the quiz Markdown to disk
* Returns:

  * `status`
  * `path` (absolute path to the file)

Used by `writer_agent` when you want to persist the quiz.

---

## 🧬 Sessions & State

QuizCrafter uses ADK’s built-in session state to pass information between agents:

* `study_material_summary` – output of `materials_agent`
* `quiz_plan_json` – JSON blueprint from `planner_agent`
* `quiz_markdown` – final quiz content from `writer_agent`

You can extend this to store:

* User’s default number of questions
* Preferred difficulty distribution
* Preferred question formats

for future runs.

---

## 📦 Project Structure

```text
quizcrafter-agent/
├─ agent.py                # All agent and tool definitions (root_agent = quiz_buddy_pipeline)
├─ README.md               # This file
├─ requirements.txt        # Python dependencies
├─ .env.example            # Template for API keys (copy to .env)
├─ .gitignore              # Ignore venv, __pycache__, .env, etc.
└─ examples/
    └─ sample_notes_calc3.txt  # Example input for testing
```

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/<your-username>/quizcrafter-agent.git
cd quizcrafter-agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file based on `.env.example`:

```text
GOOGLE_API_KEY="YOUR_REAL_API_KEY_HERE"
```

Make sure `.env` is *not* committed to Git (it should be listed in `.gitignore`).

### 4. Run with ADK

Make sure you have `google-adk` installed. Then from the project root:

```bash
adk web
```

In the ADK web UI:

1. Choose `quiz_buddy_pipeline` (the `root_agent`).

2. Describe your goal, e.g.:

   > "Make a 10-question mixed-difficulty practice quiz for my Calc III vector calculus midterm. Use the notes in `examples/sample_notes_calc3.txt`."

3. If you want to use files, tell the agent something like:

   > "Use the material from `examples/*.txt`."

   The `materials_agent` will call `load_text_files("examples/*.txt")` to read them.

4. Let the pipeline run; when it finishes, you’ll see the Markdown quiz.

5. If you want a file, say:

   > "Save this quiz to `examples/vector_calc_quiz.md`."

   The `writer_agent` can call `save_quiz_to_markdown` with that path.

---

## 🧪 Example

Try this scenario:

1. Edit `examples/sample_notes_calc3.txt` to include some of your actual course notes.

2. In the ADK UI, ask:

   > "Generate a medium-difficulty 8–10 question quiz for Calc III focusing on gradient, divergence, and curl. Use `examples/sample_notes_calc3.txt` as the source."

3. Inspect:

   * Coverage of the topics
   * Clarity of hints
   * Detail of step-by-step solutions

If needed, you can manually refine or regenerate individual questions.

---

## 📈 Value & Future Work

**Value:**
QuizCrafter reduces the time it takes to generate high-quality practice material from **hours** (writing questions and solutions manually) to **minutes**. Instead of spending time authoring exercises, students can spend more time solving problems and reviewing explanations.

**Potential extensions:**

* Subject-specific versions (math, physics, statistics, programming, etc.)
* Lightweight evaluation script to score consistency of difficulty mix and topic coverage
* Integration with spaced repetition tools (e.g., turning questions into Anki cards)
* Export to LMS-friendly formats (QTI, CSV for Canvas/Blackboard)
* A hint-only mode for use as an on-demand homework helper

---
