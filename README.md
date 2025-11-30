# QuizCrafter – Multi-Agent Practice Quiz Generator

QuizCrafter is a **multi-agent system** that turns lecture notes, slides, topic lists, or old quizzes into **new practice quizzes** with:

- Original questions  
- Optional hints  
- Detailed step-by-step solutions  
- Export to **Markdown** and **PDF**

It is built using Google’s **Agent Development Kit (ADK)** as a capstone project for the **Google / Kaggle AI Agents Intensive** in the **Agents for Good (Education)** track.

---

## 🎯 Problem

Students usually have **plenty of content** (slides, notes, PDFs) but **not enough practice questions**:

- Lecture decks explain concepts but include few worked problems.  
- Past exams give limited coverage and are often reused.  
- Writing new practice questions (and full solutions) by hand takes a lot of time and energy.

As a result:

- Students practice less than they should.  
- Instructors and TAs burn time making similar questions over and over.  
- It’s hard to get targeted practice on specific topics and difficulty levels.

---

## ✅ Solution

**QuizCrafter** automates the practice quiz workflow:

1. **Ingest materials**  
   - Text, Markdown, or PDF notes  
   - Old quizzes or PDF slides (via glob patterns such as `examples/*.pdf`)

2. **Plan a quiz**  
   - Number of questions  
   - Difficulty mix (easy / medium / hard)  
   - Topic coverage and question types

3. **Generate the quiz**  
   - Questions labeled `Q1`, `Q2`, …  
   - Difficulty + topic tags  
   - A “Hints” section  
   - A “Solutions” section with step-by-step explanations

4. **Export**  
   - Save to **Markdown** (`.md`) for easy editing and GitHub display  
   - Save to **PDF** for printing or sharing

This lets students and instructors quickly turn their own materials into high-quality practice sets instead of starting from a blank page.

---

## 🧠 Why Agents?

QuizCrafter is intentionally designed as a **multi-agent system** instead of a single “do everything” LLM call:

- `materials_agent` specializes in **reading and summarizing** study materials (including PDFs).  
- `planner_agent` specializes in **assessment design** and turns the summary + user goal into a JSON quiz blueprint.  
- `writer_agent` specializes in **question & solution authoring**, using the plan to create a structured quiz with hints and full solutions.

These are orchestrated by a **SequentialAgent** pipeline (`quiz_buddy_pipeline`), which makes the process:

- **Modular** – easy to swap or improve individual stages.  
- **Traceable** – each step has a clear responsibility.  
- **Re-usable** – the same pipeline can be run on different courses or subjects.

---

## 🏗 Architecture

Core components:

- **Agents**  
  - `materials_agent` (LlmAgent, `gemini-2.0-flash`)  
    - Uses the `load_documents` tool to read `.txt`, `.md`, and `.pdf` files.  
    - Produces `study_material_summary` in the session state.  
  - `planner_agent` (LlmAgent, `gemini-2.0-flash`)  
    - Reads `{study_material_summary}` and the user goal.  
    - Outputs a JSON quiz plan as `quiz_plan_json`.  
  - `writer_agent` (LlmAgent, `gemini-2.0-flash`)  
    - Reads `{quiz_plan_json}` and `{study_material_summary}`.  
    - Generates a full Markdown quiz + hints + solutions into `quiz_markdown`.  
    - Can call file-saving tools when requested.

- **Root pipeline**  
  - `root_agent = SequentialAgent(name="quiz_buddy_pipeline", sub_agents=[materials_agent, planner_agent, writer_agent])`

- **Tools (custom)**  
  - `load_documents(glob_pattern: str)`  
    - Reads multiple files matching a glob pattern (e.g., `examples/*.pdf`).  
    - Supports `.txt`, `.md`, `.pdf`.  
    - Returns paths and combined text with simple file headers.  
  - `save_quiz_to_markdown(markdown_content: str, output_path: str)`  
    - Writes quiz content to disk as `.md`.  
  - `save_quiz_to_pdf(markdown_content: str, output_path: str)`  
    - Writes a simple text-based PDF using `fpdf2`.

- **Sessions & State**  
  - ADK session state is used to pass outputs between agents:  
    - `study_material_summary` → from `materials_agent`  
    - `quiz_plan_json` → from `planner_agent`  
    - `quiz_markdown` → from `writer_agent`

This uses several key concepts from the Agents Intensive:

- **Multi-agent system** with multiple LLM-powered agents  
- **SequentialAgent** orchestration  
- **Custom tools** (document loading + file export)  
- **Sessions & state management** via ADK output keys  
- **Gemini** (`gemini-2.0-flash`) as the underlying model for all agents

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

`requirements.txt` includes:

- `google-adk`
- `google-generativeai`
- `python-dotenv`
- `pypdf`
- `fpdf2`

### 3. Configure API key

Create a `.env` file in the project root:

```text
GOOGLE_API_KEY="YOUR_REAL_API_KEY_HERE"
```

Make sure `.env` is **not** checked into Git (it should be listed in `.gitignore`).

### 4. Run the ADK web UI

From the project root:

```bash
adk web
```

In the browser:

1. Select the **`quiz_buddy_pipeline`** agent.  
2. Start a new conversation with a concrete request, for example:

> Generate an 8–10 question mixed-difficulty practice quiz for my Calc III exam.  
> Focus on gradient, divergence, curl, and Green’s theorem.  
> Use `examples/sample_notes_calc3.txt` as the source material.  
> Include a Hints section and a detailed Solutions section.

3. After the quiz is generated, you can ask:

> Save this quiz as `examples/calc3_practice.md`.  
> Also save this quiz as `examples/calc3_practice.pdf`.

---

## 📂 Project Structure

```text
quizcrafter-agent/
├─ quizcrafter/
│  ├─ agent.py            # Agents, tools, and root SequentialAgent
│  └─ __init__.py
├─ examples/
│  └─ sample_notes_calc3.txt
├─ README.md
├─ requirements.txt
├─ .env.example
└─ .gitignore
```

---

## 📈 Value & Future Work

**Value today:**

- Turns existing lecture materials into structured quizzes in minutes.  
- Encourages more practice, not just more reading.  
- Produces detailed solutions to help with self-study and review.

**Possible future extensions:**

- Subject-specific templates (e.g., physics vs. math vs. programming).  
- Integration with spaced repetition tools (e.g., export to Anki).  
- Agent evaluation scripts to check topic coverage and difficulty balance.  
- Cloud or classroom deployment so instructors can share quiz recipes.

---
