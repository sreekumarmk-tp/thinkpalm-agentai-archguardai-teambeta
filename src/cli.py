import sys
from pathlib import Path

# Add project root to sys.path to handle 'src' imports when running directly
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple
from uuid import uuid4

from dotenv import load_dotenv

from src.config.settings import AGENT_DEFINITIONS, MAX_MEMORY_REPORT_CHARS
from src.tools.github import parse_github_repo
from src.utils.models import (
    fetch_available_free_models,
    get_model_candidates_for_agent,
    select_model_for_agent,
)
from src.agents.specialist import run_specialist_agent_with_retries
from src.agents.synthesizer import synthesize_report

load_dotenv()

DEFAULT_MANUAL_MODEL = "openai/gpt-oss-120b:free"
DEFAULT_MEMORY_PATH = Path(".agent_memory_cli.json")
MAX_MEMORY_RUNS = 3

def load_memory(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload[-MAX_MEMORY_RUNS:]
        return []
    except Exception:
        return []

def save_memory(path: Path, memory: List[Dict[str, str]]) -> None:
    path.write_text(json.dumps(memory[-MAX_MEMORY_RUNS:], indent=2), encoding="utf-8")

def build_memory_context(memory_runs: List[Dict[str, str]]) -> str:
    if not memory_runs:
        return "No previous analysis memory available."
    blocks = []
    for run in memory_runs[-MAX_MEMORY_RUNS:]:
        blocks.append(
            f"- Run ID: {run.get('run_id', 'unknown')}\n"
            f"  Repository: {run.get('repo_url', 'unknown')}\n"
            f"  Generated At (UTC): {run.get('generated_at_utc', 'unknown')}\n"
            f"  Report Excerpt:\n{run.get('report_excerpt', '')}"
        )
    return "Previous analysis memory:\n" + "\n".join(blocks)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run multi-agent repository architecture analysis.")
    parser.add_argument("--repo-url", required=True, help="Target GitHub repository URL.")
    parser.add_argument("--manual-model", default=DEFAULT_MANUAL_MODEL, help="Fallback model.")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers (1-10).")
    parser.add_argument("--retries", type=int, default=2, help="Attempts per model.")
    parser.add_argument("--backoff", type=float, default=2.0, help="Base backoff seconds.")
    parser.add_argument("--no-auto-models", action="store_true", help="Disable free-model discovery.")
    parser.add_argument("--sequential", action="store_true", help="Disable parallel specialist execution.")
    parser.add_argument(
        "--memory-file",
        default=str(DEFAULT_MEMORY_PATH),
        help="Path for CLI memory file.",
    )
    parser.add_argument(
        "--output-prefix",
        default="multi_agent_report",
        help="Output filename prefix (without extension).",
    )
    return parser.parse_args()

def main() -> int:
    args = parse_args()

    from src.config.settings import GROQ_API_KEY
    if not os.getenv("OPENROUTER_API_KEY") and not GROQ_API_KEY:
        print("Error: OPENROUTER_API_KEY or GROQ_API_KEY is missing. Set it in .env or environment variables.")
        return 1

    try:
        parse_github_repo(args.repo_url)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    auto_pick_models = not args.no_auto_models
    run_in_parallel = not args.sequential
    max_workers = max(1, min(10, args.workers))
    retries = max(1, args.retries)

    print("Discovering available free models...")
    available_free_models = fetch_available_free_models() if auto_pick_models else set()

    memory_path = Path(args.memory_file)
    memory_runs = load_memory(memory_path)
    memory_context = build_memory_context(memory_runs)

    specialist_results: Dict[str, str] = {}
    selected_models: Dict[str, str] = {}
    model_plan: List[Tuple[Dict[str, str], List[str]]] = []
    for spec in AGENT_DEFINITIONS:
        candidates = (
            get_model_candidates_for_agent(spec["id"], available_free_models, args.manual_model)
            if auto_pick_models
            else [args.manual_model]
        )
        selected_models[spec["title"]] = candidates[0]
        model_plan.append((spec, candidates))

    if run_in_parallel:
        print(f"Running {len(model_plan)} specialist agents in parallel (workers={max_workers})...")
        with ThreadPoolExecutor(max_workers=min(max_workers, len(model_plan))) as executor:
            futures = {
                executor.submit(
                    run_specialist_agent_with_retries,
                    args.repo_url,
                    spec,
                    candidates,
                    retries,
                    args.backoff,
                    memory_context,
                ): (spec, candidates)
                for spec, candidates in model_plan
            }
            for future in as_completed(futures):
                spec, candidates = futures[future]
                try:
                    content, used_model = future.result()
                    specialist_results[spec["title"]] = content
                    selected_models[spec["title"]] = used_model
                except Exception as exc:
                    specialist_results[spec["title"]] = f"Agent execution failed: {str(exc)}"
                    selected_models[spec["title"]] = candidates[0] if candidates else "unknown-model"
                print(f"Completed: {spec['title']} ({selected_models[spec['title']]})")
    else:
        print(f"Running {len(model_plan)} specialist agents sequentially...")
        for index, (spec, candidates) in enumerate(model_plan, start=1):
            print(f"[{index}/{len(model_plan)}] {spec['title']} ({candidates[0]})")
            content, used_model = run_specialist_agent_with_retries(
                args.repo_url,
                spec,
                candidates,
                retries,
                args.backoff,
                memory_context,
            )
            specialist_results[spec["title"]] = content
            selected_models[spec["title"]] = used_model

    synthesizer_model = (
        select_model_for_agent("report_synthesizer", available_free_models)
        if auto_pick_models
        else args.manual_model
    )
    print(f"Synthesizing final report with {synthesizer_model}...")
    final_report = synthesize_report(
        args.repo_url, 
        synthesizer_model, 
        specialist_results, 
        memory_context,
        max_attempts_per_model=retries,
        base_backoff_seconds=args.backoff
    )

    run_id = uuid4().hex[:8]
    generated_at_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    memory_runs.append(
        {
            "run_id": run_id,
            "repo_url": args.repo_url,
            "generated_at_utc": generated_at_utc,
            "report_excerpt": final_report[:MAX_MEMORY_REPORT_CHARS],
        }
    )
    save_memory(memory_path, memory_runs)

    markdown_path = Path(f"{args.output_prefix}.md")
    json_path = Path(f"{args.output_prefix}.json")
    markdown_path.write_text(final_report, encoding="utf-8")
    json_path.write_text(
        json.dumps(
            {
                "repository": args.repo_url,
                "run_id": run_id,
                "generated_at_utc": generated_at_utc,
                "models": {
                    "specialists": selected_models,
                    "report_synthesizer": synthesizer_model,
                },
                "specialist_outputs": specialist_results,
                "final_report_markdown": final_report,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Done. Markdown: {markdown_path} | JSON: {json_path} | Memory: {memory_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
