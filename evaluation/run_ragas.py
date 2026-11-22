"""RAGAS evaluation of the RAG pipeline against the golden dataset.

Usage:  python -m evaluation.run_ragas [--limit N] [--strict]

Computes faithfulness, answer_relevancy, context_precision and context_recall, saves per-question
scores (CSV) and a summary with PASS/FAIL per metric (JSON) to evaluation/results/.
"""
from __future__ import annotations

import argparse
import json
import logging
import warnings
from datetime import datetime, timezone

import pandas as pd

from config import ConfigError, get_config
from evaluation.golden_dataset import GOLDEN_DATASET

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("ragas_eval")

THRESHOLDS = {
    "faithfulness": 0.80,        # answers must be grounded in the retrieved context (no hallucination)
    "answer_relevancy": 0.70,    # answers must address the question
    "context_precision": 0.70,   # relevant chunks should be ranked first
    "context_recall": 0.70,      # retrieved context must cover the reference answer
}


def collect_samples(engine, golden: list[dict], k: int | None = None) -> list[dict]:
    """Run every golden question through the real pipeline and keep answer + retrieved contexts."""
    samples = []
    for i, item in enumerate(golden, start=1):
        response = engine.ask(item["question"], k=k)
        logger.info("[%d/%d] %s -> %d sources%s", i, len(golden), item["question"][:60],
                    len(response.sources), " (BLOCKED)" if response.blocked else "")
        samples.append({
            "user_input": item["question"],
            "response": response.answer,
            "retrieved_contexts": response.contexts or [""],
            "reference": item["ground_truth"],
        })
    return samples


def evaluate_samples(samples: list[dict], cfg) -> pd.DataFrame:
    from ragas import EvaluationDataset, evaluate
    from ragas.embeddings import LangchainEmbeddingsWrapper
    from ragas.llms import LangchainLLMWrapper
    from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness

    from src.vector_store import get_embeddings, get_llm

    result = evaluate(
        EvaluationDataset.from_list(samples),
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=LangchainLLMWrapper(get_llm(cfg)),
        embeddings=LangchainEmbeddingsWrapper(get_embeddings(cfg)),
    )
    return result.to_pandas()


def summarise(scores: pd.DataFrame, thresholds: dict[str, float] = THRESHOLDS) -> dict:
    """Mean score per metric with PASS/FAIL against the threshold."""
    summary = {}
    for metric, threshold in thresholds.items():
        if metric not in scores:
            summary[metric] = {"score": None, "threshold": threshold, "status": "MISSING"}
            continue
        mean = float(scores[metric].mean(skipna=True))
        summary[metric] = {"score": round(mean, 4), "threshold": threshold,
                           "status": "PASS" if mean >= threshold else "FAIL"}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "num_questions": int(len(scores)),
        "metrics": summary,
        "overall": "PASS" if all(m["status"] == "PASS" for m in summary.values()) else "FAIL",
    }


def save_results(scores: pd.DataFrame, summary: dict, results_dir) -> tuple:
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = results_dir / f"ragas_scores_{stamp}.csv"
    json_path = results_dir / f"ragas_summary_{stamp}.json"
    scores.to_csv(csv_path, index=False)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return csv_path, json_path


def main() -> int:
    parser = argparse.ArgumentParser(description="RAGAS evaluation for the WanderNest RAG chatbot")
    parser.add_argument("--limit", type=int, default=None, help="evaluate only the first N golden questions")
    parser.add_argument("--strict", action="store_true", help="exit with code 1 if any metric fails")
    args = parser.parse_args()

    try:
        cfg = get_config()
    except ConfigError as exc:
        raise SystemExit(str(exc))

    from src.search_engine import TravelSearchEngine

    golden = GOLDEN_DATASET[: args.limit] if args.limit else GOLDEN_DATASET
    engine = TravelSearchEngine.from_config(cfg)
    scores = evaluate_samples(collect_samples(engine, golden), cfg)
    summary = summarise(scores)
    csv_path, json_path = save_results(scores, summary, cfg.results_dir)

    print("\n=== RAGAS results ===")
    for metric, info in summary["metrics"].items():
        print(f"{metric:<20} {info['score']}  (threshold {info['threshold']})  {info['status']}")
    print(f"Overall: {summary['overall']}\nSaved: {csv_path}\n       {json_path}")
    return 1 if args.strict and summary["overall"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
