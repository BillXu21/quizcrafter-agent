"""
QuizCrafter – Multi-Agent Practice Quiz Generator

Features:
- Takes lecture slides / notes / topics as input (text, markdown, or PDF via glob patterns).
- Plans a quiz (question types, difficulty, coverage).
- Generates questions, step-by-step solutions, and optional hints.
- Can save the quiz into Markdown and PDF files on disk.

Intended usage with Google ADK:
  1. pip install -r requirements.txt
  2. Put GOOGLE_API_KEY in .env (GOOGLE_API_KEY="...").
  3. From the project root: `adk web`
  4. In the ADK UI, select `quiz_buddy_pipeline` and chat with it.
"""

from __future__ import annotations

import glob
from pathlib import Path
from typing import Dict, List

from fpdf import FPDF
from pypdf import PdfReader

from google.adk.agents import LlmAgent, SequentialAgent


# ---------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------


def load_documents(glob_pattern: str) -> Dict[str, str]:
    """Load multiple text-like files (txt, md, pdf) into memory.

    Args:
        glob_pattern: A glob pattern relative to the project root
                      (e.g., 'examples/*.txt', 'notes/**/*.pdf').

    Returns:
        A dict with:
          - 'files': list of file paths loaded
          - 'combined_text': concatenated text from all files
    """
    matched_paths: List[str] = sorted(glob.glob(glob_pattern, recursive=True))

    texts: List[str] = []

    for p in matched_paths:
        path_obj = Path(p)
        if not path_obj.is_file():
            continue

        suffix = path_obj.suffix.lower()

        if suffix in {".txt", ".md"}:
            # Plain text / markdown
            try:
                text = path_obj.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path_obj.read_text(encoding="latin-1")
        elif suffix == ".pdf":
            # PDF -> extract text from all pages
            try:
                reader = PdfReader(str(path_obj))
                page_texts = []
                for page in reader.pages:
                    page_texts.append(page.extract_text() or "")
                text = "\n".join(page_texts)
            except Exception as e:  # pragma: no cover - defensive
                text = f"[ERROR reading PDF {path_obj.name}: {e}]"
        else:
            # Unsupported type – skip, but annotate
            text = f"[Skipping unsupported file type: {path_obj.name}]"

        texts.append(f"\n\n===== FILE: {path_obj} =====\n\n{text}")

    combined = "\n".join(texts) if texts else ""

    return {
        "files": matched_paths,
        "combined_text": combined,
    }


def save_quiz_to_markdown(
    markdown_content: str,
    output_path: str = "quiz_output.md",
) -> Dict[str, str]:
    """Save the generated quiz (Markdown) to a local file.

    Args:
        markdown_content: The quiz + solutions in Markdown format.
        output_path: Path to save the file (default: 'quiz_output.md').

    Returns:
        A dict with:
          - 'status': 'saved'
          - 'path': the resolved file path (if saved)
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(markdown_content, encoding="utf-8")

    return {
        "status": "saved",
        "path": str(out_path.resolve()),
    }


def save_quiz_to_pdf(
    markdown_content: str,
    output_path: str = "quiz_output.pdf",
) -> Dict[str, str]:
    """Save the generated quiz (Markdown-ish text) to a simple PDF.

    Notes:
        - This is a very lightweight exporter: it does NOT render full markdown,
          but writes the text line-by-line into a PDF.
        - Good enough for printing or sharing, not for fancy layouts.

    Args:
        markdown_content: The quiz content in Markdown/plain text.
        output_path: Target PDF filename (default: 'quiz_output.pdf').

    Returns:
        A dict with:
          - 'status': 'saved'
          - 'path': absolute path to the PDF
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=11)

    for line in markdown_content.splitlines():
        pdf.multi_cell(0, 6, line)

    pdf.output(str(out_path))

    return {
        "status": "saved",
        "path": str(out_path.resolve()),
    }


# ---------------------------------------------------------------------
# Agent definitions
# ---------------------------------------------------------------------

materials_agent = LlmAgent(
    name="materials_agent",
    model="gemini-2.0-flash",
    description=(
        "Loads study materials from files (slides, notes, prior quizzes) "
        "and produces a concise summary for quiz generation."
    ),
    instruction=(
        "You are a study assistant that prepares raw material for quiz generation.\n\n"
        "The user may either:\n"
        "  - Paste text directly (lecture notes, slides, prior quizzes), OR\n"
        "  - Provide one or more file glob patterns such as 'examples/*.txt', "
        "    'notes/week2/*.md', or 'slides/**/*.pdf'.\n\n"
        "If the user mentions file paths or folders, ALWAYS call the 'load_documents' tool "
        "with an appropriate glob pattern to pull the content into context. You may call "
        "the tool multiple times if needed.\n\n"
        "Then, produce a concise summary of the important concepts, formulas, definitions, "
        "and typical question styles that appear in the material. The summary should be "
        "friendly to another agent that will later write questions.\n\n"
        "Output format:\n"
        "  - Start with a short bullet list of key topics.\n"
        "  - Then provide a section 'Concept Summary' with 3–8 paragraphs summarizing "
        "    what a student should know.\n"
        "  - If you called 'load_documents', mention which files were used.\n"
    ),
    tools=[load_documents],
    output_key="study_material_summary",
)


planner_agent = LlmAgent(
    name="planner_agent",
    model="gemini-2.0-flash",
    description=(
        "Designs a quiz blueprint (topics, counts, difficulty mix, and question types)."
    ),
    instruction=(
        "You are an expert instructor and assessment designer.\n\n"
        "You will receive:\n"
        "  - The user's goal (e.g., exam prep, quick practice, concept review).\n"
        "  - A summary of the material in {study_material_summary}, if available.\n\n"
        "Your job is to design a quiz plan that balances conceptual understanding and "
        "calculation / procedure skills.\n\n"
        "The user may optionally specify:\n"
        "  - Total number of questions\n"
        "  - Allowed question types (e.g., multiple choice, short answer, FRQ)\n"
        "  - Desired difficulty (e.g., mostly medium, some hard)\n\n"
        "If the user does not specify these, choose reasonable defaults for a focused "
        "practice quiz (e.g., 8–12 questions).\n\n"
        "Output your plan as JSON only, no extra prose. Use this schema:\n\n"
        "{\n"
        '  "total_questions": int,\n'
        '  "question_types": ["multiple_choice", "short_answer", "free_response"],\n'
        '  "difficulty_mix": {"easy": int, "medium": int, "hard": int},\n'
        '  "topics": [\n'
        "    {\n"
        '      "name": "string (topic name)",\n'
        '      "weight": "short description of importance or coverage",\n'
        '      "target_skills": ["concept recall", "calculation", "proof/derivation"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Requirements:\n"
        "  - Ensure the counts in difficulty_mix approximately add up to total_questions.\n"
        "  - Keep topic names short but descriptive.\n"
        "  - Use plain JSON (no comments, no markdown)."
    ),
    output_key="quiz_plan_json",
)


writer_agent = LlmAgent(
    name="writer_agent",
    model="gemini-2.0-flash",
    description=(
        "Writes quiz questions, hints, and step-by-step solutions based on a quiz plan "
        "and study material."
    ),
    instruction=(
        "You are a careful exam writer and tutor.\n\n"
        "You will receive:\n"
        "  - The quiz plan in {quiz_plan_json} (JSON describing topics, difficulty mix, and types).\n"
        "  - The study material summary in {study_material_summary}, if available.\n"
        "  - The original user request.\n\n"
        "Using that information, generate a full practice quiz in Markdown with:\n"
        "  1. A title (e.g., '# Practice Quiz: <Course / Topic>').\n"
        "  2. An instructions section (time suggestions, allowed tools if user specified).\n"
        "  3. A list of questions. For each question, label as 'Q1', 'Q2', etc., tag the difficulty, and tag the topic.\n"
        "  4. A 'Hints' section where each question has an optional hint.\n"
        "  5. A 'Solutions' section with detailed, step-by-step solutions for every question.\n\n"
        "When writing solutions:\n"
        "  - Show intermediate steps and reasoning.\n"
        "  - For math, clearly state formulas used and why.\n"
        "  - If there are common mistakes, briefly point them out.\n\n"
        "After you generate the quiz Markdown, consider whether the user might want it saved.\n"
        "  - If they ask for a Markdown file, call 'save_quiz_to_markdown'.\n"
        "  - If they ask for a PDF file, call 'save_quiz_to_pdf'.\n"
        "If you call a saving tool, STILL include the full quiz Markdown in your final answer "
        "so the user can copy/paste or inspect it directly.\n"
    ),
    tools=[save_quiz_to_markdown, save_quiz_to_pdf],
    output_key="quiz_markdown",
)


# ---------------------------------------------------------------------
# Root agent (multi-step pipeline)
# ---------------------------------------------------------------------

root_agent = SequentialAgent(
    name="quiz_buddy_pipeline",
    description=(
        "A multi-step study assistant that loads materials, plans a quiz, and generates "
        "practice questions with hints and detailed solutions."
    ),
    sub_agents=[
        materials_agent,
        planner_agent,
        writer_agent,
    ],
)


__all__ = ["root_agent"]
