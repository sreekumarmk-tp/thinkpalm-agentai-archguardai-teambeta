# ArchGuard AI: Agentic Architecture Assistant

**A multi-agent system for deep repository analysis, security auditing, and architectural health assessments using LLMs.**

---

## Project name and problem statement

**Project name:** **ArchGuard AI** (Agentic Architecture Assistant).

**Problem statement:** Teams spend too much time understanding unfamiliar repositories and judging architectural risk. Single-shot LLM prompts cannot reliably cover a whole codebase, and shallow linting misses cross-cutting concerns (security posture, performance, structural maintainability). Context limits and weak grounding to real files make one-off reviews inconsistent. ArchGuard AI addresses this by orchestrating specialist agents that **list and read real files** from GitHub, score domains, and synthesize an evidence-based engineering report with diagrams and export options.

---

## Team members and their contributions

| Team member | Contribution |
| :--- | :--- |
| **Arjun P Kumar** | Primary implementation and iteration (majority of commits): multi-agent orchestration, Streamlit app, CLI, GitHub tooling, LLM integration, tests, and documentation. *(Includes commits authored as Arjun P K.)* |
| **Sreekumar M K** | Project direction, architecture alignment, and codebase contributions. |

*Summarized from repository git history; update this table if your course or organization needs a different format.*

---

## Tech stack and versions

**Runtime:** Python **3.10+** (CI and local development; the example lock below was produced with Python **3.13**).

**Direct dependencies** (from `requirements.txt`; install with `pip install -r requirements.txt`):

| Package | Example resolved version¹ |
| :--- | :--- |
| streamlit | 1.56.0 |
| langchain-openai | 1.1.14 |
| langchain-groq | 1.1.2 |
| langgraph | 1.1.8 |
| python-dotenv | 1.2.2 |
| requests | 2.33.1 |
| pytest | 9.0.3 |
| pytest-dotenv | 0.5.2 |
| python-docx | 1.2.0 |
| fpdf2 | 2.8.7 |
| markdown2 | 2.5.5 |

**Transitive / notable stack** (same environment as above): `langchain-core` 1.3.0, `openai` 2.32.0, `pydantic` 2.13.2, `httpx` 0.28.1, `pillow` 12.2.0, `pandas` 3.0.2, `numpy` 2.4.4.

**External services (no pip version):** [OpenRouter](https://openrouter.ai/), [Groq](https://groq.com/), [GitHub REST API v3](https://docs.github.com/en/rest), [Mermaid.ink](https://mermaid.ink/) (diagram rendering in the UI).

¹ *Example versions from `pip freeze` after `pip install -r requirements.txt`. Your versions may differ; run `pip freeze > requirements.lock.txt` for an exact snapshot.*

**Capability map**

| Layer | Technology |
| :--- | :--- |
| **User interface** | [Streamlit](https://streamlit.io/) |
| **Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) and [LangChain](https://www.langchain.com/) |
| **Model gateway** | [OpenRouter](https://openrouter.ai/) and [Groq](https://groq.com/) |
| **Persistence** | [SQLite](https://www.sqlite.org/) (Cross-session memory) |
| **Version control** | [GitHub REST API v3](https://docs.github.com/en/rest) |
| **Visualization** | [Mermaid.ink](https://mermaid.ink/) |
| **Testing** | [Pytest](https://pytest.org/) |

---

## Run the project locally (step-by-step)

1. **Install Python**  
   Use Python **3.10** or newer (`python3 --version`).

2. **Clone the repository**  
   ```bash
   git clone <repository-url>
   cd thinkpalm-agentai-sreekumarmk-archguardai
   ```
   *(Adjust the directory name if your clone path differs.)*

3. **Create and activate a virtual environment** (recommended)  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate          # macOS / Linux
   # .venv\Scripts\activate           # Windows PowerShell
   ```

4. **Install dependencies**  
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Configure environment variables**  
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set at least one LLM provider key, for example:  
   `OPENROUTER_API_KEY`, and/or `GROQ_API_KEY`, optional `GITHUB_TOKEN` (higher rate limits), and `DEFAULT_LLM_PROVIDER` (`openrouter` or `groq`).

6. **Run the Streamlit dashboard**  
   From the **repository root** (so `src` imports resolve):  
   ```bash
   streamlit run src/app.py
   ```
   Open the URL shown in the terminal (default `http://localhost:8501`).

7. **Use the app**  
   Enter a public (or token-accessible) **GitHub repository URL**, adjust sidebar options if needed, then click **Analyze Now**.

8. **Optional: run a headless analysis (CLI)**  
   From the repository root:  
   ```bash
   python src/cli.py --repo-url "https://github.com/owner/repo"
   ```
   Use `python src/cli.py --help` for workers, retries, sequential mode, and output paths.

9. **Optional: run tests**  
   ```bash
   python -m pytest tests/ -v
   ```

---

## Working prototype (screenshots)

Screenshots below are stored under [`screenshots/`](screenshots/).

| Step | Screenshot |
| :---: | :---: |
| Initial dashboard | ![Initial dashboard](screenshots/01_initial.png) |
| Specialist agent 1 (in progress) | ![Agent 1](screenshots/02_Agent%201.png) |
| Specialist agent 2 (in progress) | ![Agent 2](screenshots/03_Agent%202.png) |
| Specialist agent 3 (in progress) | ![Agent 3](screenshots/04_Agent%203.png) |
| Analysis completed | ![Completed](screenshots/05_Completed.png) |
| Full-page report (Groq example) | ![Full page result](screenshots/06_groq_full_page_result.png) |
| Specialist intelligence section | ![Specialist intelligence](screenshots/07_specialist_intelligence.png) |
| Export data UI | ![Export data](screenshots/08_export_data.png) |
| Document download | ![Document download](screenshots/09_document_download.png) |

---

## Overview

ArchGuard AI orchestrates a **Council of Specialists** so reviews go beyond simple linting: evidence-based insights into tech stack maturity, security posture, design integrity, and performance efficiency.

Specialists use a **ReAct-style** loop (list repository files, read selected paths, analyze) backed by **LangChain** tool agents. A **report synthesizer** merges outputs into a single roadmap-style report. **LangGraph** is included for reporter graph compilation; the live Streamlit and CLI flows are driven by the specialist factory and synthesizer described in the project layout below.

---

## Key features

- **Council of specialists:** three domain agents (Architecture/Design, Security/Quality, Performance/Testing) plus synthesis.
- **Evidence-based findings:** findings tied to files fetched via GitHub tools.
- **LLM adapter layer:** OpenRouter and Groq with dynamic model discovery and fallbacks.
- **Cross-session memory:** SQLite-backed persistence ensuring specialists remember previous runs across UI refreshes and CLI sessions.
- **Parallel execution swarm:** optional parallel specialist runs (Streamlit sidebar / CLI flags).
- **Visual reporting:** Mermaid in reports, cleaned and rendered via **Mermaid.ink** in Streamlit.
- **Runtime resilience:** retries, backoff, and model fallback chains.
- **CLI and UI:** Streamlit dashboard and CLI with unified memory state.

---

## System architecture

The **LLM adapter layer** routes to OpenRouter or Groq. The **Specialist Factory** runs the council, then the **report synthesizer** produces enriched markdown and diagrams.

```mermaid
graph TD
    subgraph Input_Layer
        A[GitHub Repository URL]
        B[API Keys: OR/Groq]
    end

    subgraph Orchestration_Layer
        D[Specialist Factory]
        E[Parallel/Sequential Swarm]
    end

    subgraph Agent_Council
        direction LR
        G[Architecture & Design]
        H[Security & Quality]
        I[Performance & QA]
    end

    subgraph Storage_Layer
        M1[(SQLite Memory Store)]
    end

    A & B --> D
    D --> E
    E <--> M1
    E --> G & H & I
    G & H & I --> JS[Report Synthesizer]
    JS --> N[Enriched Markdown + Diagrams]
    N --> M1

    style Orchestration_Layer fill:#fff9c4,stroke:#fbc02d,stroke-width:2px
    style Agent_Council fill:#f0f4c3,stroke:#827717,stroke-width:2px
    style Storage_Layer fill:#e1f5fe,stroke:#01579b,stroke-width:2px
```

---

## Functional flow

### 1. Model discovery and routing

Provider model lists are queried; routing uses model naming and configuration (for example `groq/` vs OpenRouter-style ids).

```mermaid
flowchart LR
    A[Agent Task] --> B{LLM Factory}
    B -->|Suffix Discovery| C[Groq Cloud]
    B -->|Suffix Discovery| D[OpenRouter]
```

### 2. Specialist investigation (ReAct pattern)

- **Observation:** review the file tree.  
- **Action:** call `read_specific_file` for evidence.  
- **Thinking:** analyze against domain prompts.  
- **Scoring:** numeric score 0–100 in the specialist output template.

### 3. Resilience and fallback

On failure: retry with backoff, then try the next model in the candidate chain.

### 4. Synthesis and rendering

The synthesizer builds the final narrative and Mermaid blocks; the UI sanitizes Mermaid and renders images via **Mermaid.ink**.

---

## Project structure

```text
.
├── src/
│   ├── agents/
│   │   ├── specialists/
│   │   │   ├── factory.py      # Specialist runner with swarm logic
│   │   │   ├── base.py         # Base ReAct agent core
│   │   │   ├── architect.py    # Arch, Design & Maintainability
│   │   │   ├── security.py     # Security, Quality & Standards
│   │   │   └── performance.py  # Performance, Efficiency & QA
│   │   └── synthesizer.py      # Final report aggregator
│   ├── config/
│   │   └── settings.py         # Centralised settings & constants
│   ├── memory/
│   │   ├── store.py            # SQLite database connector
│   │   └── manager.py          # Two-layer cross-session persistence
│   ├── tools/
│   │   └── github.py           # GitHub REST API connectors
│   ├── ui/
│   │   └── components.py       # Sidebar & Export UI widgets
│   ├── utils/
│   │   ├── export.py           # Word (.docx) export logic
│   │   ├── llm_factory.py      # Provider-agnostic adapter
│   │   ├── models.py           # Dynamic model discovery
│   │   ├── rendering.py        # Enriched report display
│   │   └── mermaid_cleanup.py  # Mermaid syntax sanitization
│   └── app.py                  # Streamlit Application
├── screenshots/                # Prototype screenshots (see above)
├── tests/                      # Unit, CLI E2E, Streamlit UI E2E
├── ADR.md                      # Architecture Decision Records
└── .env.example                # Configuration template
```

### Key components

- **`src/agents/specialists/factory.py`:** parallel swarms, model fallback, retries.  
- **`src/utils/llm_factory.py`:** Groq / OpenRouter routing.  
- **`src/utils/mermaid_cleanup.py`:** diagram sanitization.  
- **`src/app.py`:** Streamlit entrypoint.  
- **`src/cli.py`:** headless CLI for CI-style runs.

---

## Usage (Streamlit)

1. Enter a **GitHub repository URL**.  
2. Use the **sidebar** for provider, parallel vs sequential execution, and retry settings.  
3. Click **Analyze Now**.  
4. Review the report and diagrams.  
5. **Export** Word or JSON where offered in the UI.

---

## Testing and validation

The suite includes unit tests, CLI E2E, and Streamlit `AppTest` flows (see `tests/`).

```bash
python3 -m pytest tests/ -v
python3 -m pytest tests/unit/ -v
```

Coverage (optional):

```bash
python -m pytest --cov=src --cov-report=term-missing tests/
python -m pytest --cov=src --cov-report=html tests/
```

### UI E2E pattern (excerpt)

```python
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("src/app.py").run()
assert len(at.exception) == 0
at.sidebar.radio[0].set_value("Groq").run()
assert at.sidebar.selectbox[0].options[0].startswith("groq/")
```

---

## Contributing

Contributions are welcome. Read [ADR.md](ADR.md) for design context before opening a PR.

---

## License

MIT License — Copyright (c) 2026 ArchGuard AI Team.
