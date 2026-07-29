from __future__ import annotations

import argparse
import json
from pathlib import Path

from .metrics import EvaluationMetrics


def evaluate_predictions(predictions_file: str, test_file: str, output: str) -> dict:
    predictions = [json.loads(line)["prediction"] for line in Path(predictions_file).read_text(encoding="utf-8").splitlines() if line]
    rows = [json.loads(line) for line in Path(test_file).read_text(encoding="utf-8").splitlines() if line]
    references = [row["output"] for row in rows]
    if len(predictions) != len(references):
        raise ValueError("Prediction and reference counts differ")
    result = {
        "examples": len(predictions),
        "exact_match": EvaluationMetrics.exact_match(predictions, references),
        "token_f1": EvaluationMetrics.token_f1(predictions, references),
        **EvaluationMetrics.domain_specific(predictions),
    }
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--test", default="data/splits/test.jsonl")
    parser.add_argument("--output", default="reports/evaluation.json")
    args = parser.parse_args()
    print(json.dumps(evaluate_predictions(args.predictions, args.test, args.output), indent=2))


if __name__ == "__main__":
    main()
