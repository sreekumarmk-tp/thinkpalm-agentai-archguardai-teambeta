#!/usr/bin/env python3
"""
Build docs/Architecture-Overview.pdf — narrative architecture overview
aligned with README.md (run: python scripts/generate_architecture_overview_pdf.py).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]


def clean_for_pdf(text: str) -> str:
    """Latin-1 safe text for core fonts (mirrors src.utils.export.clean_for_pdf)."""
    text = text.replace("**", "").replace("*", "").replace("`", "")
    return "".join(c if ord(c) < 256 else " " for c in text)


def _strip_md(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    return clean_for_pdf(s)


class ArchOverviewPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(format="A4")
        self.set_margins(22, 22, 22)
        self.set_auto_page_break(auto=True, margin=20)
        self.alias_nb_pages()

    def footer(self) -> None:
        self.set_y(-16)
        self.set_font("Helvetica", "I", 9)
        self.cell(0, 10, f"-- {self.page_no()} of {{nb}} --", align="C")

    def heading(self, text: str, size: int = 13) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "B", size)
        self.multi_cell(0, 7, _strip_md(text))
        self.ln(2)

    def body(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Helvetica", "", 10.5)
        self.multi_cell(0, 5.5, _strip_md(text))
        self.ln(3)

    def bullets(self, lines: list[str]) -> None:
        self.set_font("Helvetica", "", 10.5)
        for line in lines:
            self.set_x(self.l_margin)
            self.multi_cell(0, 5.5, _strip_md(f"- {line}"))
        self.ln(2)


def build_pdf(out_path: Path) -> None:
    pdf = ArchOverviewPDF()
    pdf.add_page()

    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "B", 16)
    pdf.multi_cell(0, 8, "ARCHITECTURE OVERVIEW: ArchGuard AI")
    pdf.ln(1)
    pdf.set_x(pdf.l_margin)
    pdf.set_font("Helvetica", "I", 11)
    pdf.multi_cell(0, 6, "(Agentic Architecture Assistant)")
    pdf.ln(5)

    pdf.heading("1. Context and Problem Statement", 12)
    pdf.body(
        "Engineering teams still spend disproportionate time onboarding to unfamiliar "
        "repositories and judging architectural risk. Single-shot LLM prompts cannot "
        "reliably span an entire codebase, and shallow linting misses cross-cutting "
        "concerns such as security posture, performance characteristics, and structural "
        "maintainability. ArchGuard AI addresses this gap with a production-oriented, "
        "multi-agent workflow that behaves more like a disciplined review council than "
        "a one-off chat completion: specialists gather evidence from the live repository, "
        "score domains numerically, and a synthesizer turns those signals into a "
        "prioritized engineering roadmap."
    )

    pdf.heading("2. Technical Architecture and Innovation", 12)
    pdf.body(
        "The system centers on a Specialist Factory that orchestrates three domain "
        "agents (Architecture and Design, Security and Quality, Performance and Testing) "
        "using LangChain tool-augmented agents with a ReAct-style loop: list the "
        "repository tree, selectively read files for evidence, then emit structured "
        "markdown findings. A unified LLM adapter routes calls to OpenRouter or Groq based "
        "on model naming and configuration, with dynamic discovery of available models "
        "from each provider. Runtime resilience combines per-model retries, backoff, "
        "and ordered fallback chains so transient rate limits or provider errors do not "
        "halt the entire review."
    )
    pdf.bullets(
        [
            "Council of Specialists: three converged domain agents plus a dedicated report synthesizer.",
            "Evidence-backed outputs: GitHub REST tools fetch real file trees and contents, not guessed snippets.",
            "Parallel execution swarm: Streamlit and CLI can run specialists concurrently or sequentially for stability.",
            "Cross-session memory: SQLite store (.archguard_memory.db by default) shared between UI and CLI; Streamlit session cache for in-session speed.",
            "CLI outputs: default prefix writes markdown, JSON, and Word under outputs/ using the same export_to_docx path as the Streamlit download.",
            "Visual reporting: synthesizer-produced Mermaid is sanitized and rendered via Mermaid.ink in the Streamlit UI.",
            "Professional src/ layout: application code, configuration, tools, memory, UI, and tests are separated per modern Python practice.",
            "LangChain agents with tools; LangGraph included for reporter state-graph compilation; live flows driven by factory and synthesizer per README.",
        ]
    )

    pdf.body(
        "Technology stack (aligned with README): User Interface - Streamlit; "
        "Orchestration - LangGraph and LangChain; Model Gateway - OpenRouter and Groq; "
        "Version Control - GitHub REST API v3; Logic and Runtime - Python 3.10 or newer; "
        "Visualization - Mermaid.ink; Testing - Pytest with pytest-cov for coverage, pytest.ini pythonpath, and tests/conftest.py for import path resilience."
    )

    pdf.heading("3. Data Flow and Execution", 12)
    pdf.body(
        "1. Ingestion: The operator supplies a GitHub repository URL through the "
        "Streamlit dashboard or the headless CLI, with optional parallel or sequential "
        "execution, worker counts, retry and backoff settings, model presets or manual "
        "models, and CLI --memory-db so SQLite matches the UI when desired."
    )
    pdf.body(
        "2. Model planning: The application queries provider model APIs, ranks free "
        "or configured model candidates per agent role, and prepares ordered fallback "
        "lists for each specialist and for the synthesizer."
    )
    pdf.body(
        "3. Specialist investigation: Each agent lists repository files, reads selected "
        "paths within configured size limits, and returns markdown with score, findings, "
        "recommendations, and quick wins grounded in cited paths."
    )
    pdf.body(
        "4. Synthesis: The report synthesizer merges specialist outputs with session "
        "memory context from prior runs, producing executive narrative, risk posture, "
        "roadmaps, comparative tables, and required Mermaid architecture and flow diagrams."
    )
    pdf.body(
        "5. Presentation and export: Streamlit renders markdown and diagram images and "
        "offers Word and JSON downloads. The CLI writes the synthesized report to "
        "outputs/ as .md, .json, and .docx by default (prefix configurable), using the same "
        "Word export pipeline as the UI."
    )

    pdf.heading("4. Quality Assurance and Validation", 12)
    pdf.body(
        "ArchGuard AI ships a multi-layer Pytest suite with on the order of sixty-six tests "
        "spanning unit modules for specialists, synthesizer behavior, LLM factory routing, "
        "model discovery, GitHub tooling, SQLite memory store and manager, rendering, "
        "schemas, export, and UI helpers. End-to-end coverage includes CLI flows that "
        "exercise SQLite memory persistence and outputs under outputs/, and Streamlit "
        "AppTest scenarios that load the application, drive sidebar configuration, and "
        "validate widget behavior without a full browser. pytest-cov supports coverage "
        "reports; pytest.ini sets pythonpath for reliable imports. This structure guards "
        "the contract between orchestration code, tools, and LLM integration against regressions."
    )

    pdf.heading("5. Conclusion and Scalability", 12)
    pdf.body(
        "The architecture is intentionally modular: new specialists or tools (for "
        "example, static analysis or AST-backed probes) can be registered in the "
        "factory without rewriting the Streamlit shell, and additional model providers "
        "can plug into the same adapter pattern. Horizontal scale can add more "
        "read-only intelligence sources; vertical scale could later introduce "
        "carefully scoped write actions once governance and safety models mature. "
        "Contributions should follow the Architecture Decision Records. Distribution "
        "uses the MIT License (Copyright 2026 ArchGuard AI Team) as stated in the README."
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(out_path))


def main() -> None:
    default_out = ROOT / "docs" / "Architecture-Overview.pdf"
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else default_out
    build_pdf(out)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
