from __future__ import annotations

import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .collector import FeedbackCollector

logger = logging.getLogger(__name__)


def run_continuous_training(
    db_path: str | Path,
    output_dir: str | Path,
    base_model: str | None = None,
    domain: str | None = None,
    min_samples: int = 100,
    max_samples: int = 5000,
    **train_kwargs,
) -> int:
    collector = FeedbackCollector(db_path)
    untrained = collector.untrained_count(domain)

    if untrained < min_samples:
        logger.info(
            "Not enough untrained samples (%d < %d). Skipping retraining.",
            untrained, min_samples,
        )
        return 0

    count = min(untrained, max_samples)
    logger.info("Exporting %d training samples for retraining...", count)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".jsonl", delete=False, encoding="utf-8"
    ) as tmp:
        training_file = tmp.name

    exported = collector.export_training_data(training_file, domain)

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    config_path = os.getenv("TRAIN_CONFIG", "configs/base_config.yaml")
    if base_model:
        os.environ["BASE_MODEL"] = base_model

    cmd = [
        sys.executable, "-m", "src.training.trainer",
        "--config", config_path,
        "--resume", training_file,
        "--output", str(output_dir),
    ]
    for key, value in train_kwargs.items():
        cmd.extend([f"--{key.replace('_', '-')}", str(value)])

    logger.info("Launching retraining: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        logger.error("Retraining failed with exit code %d", result.returncode)
        return 0

    ids = [r["id"] for r in collector.fetch_untrained(domain=domain, limit=count)]
    collector.mark_trained(ids)

    if Path(training_file).exists():
        os.unlink(training_file)

    logger.info("Continuous training complete. %d samples trained.", len(ids))
    return len(ids)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Trigger continuous retraining from feedback data")
    parser.add_argument("--db", default="feedback.db", help="Path to feedback SQLite database")
    parser.add_argument("--output", default="checkpoints/continuous", help="Output directory for trained model")
    parser.add_argument("--base-model", type=str, default=None, help="Base model path or name")
    parser.add_argument("--domain", type=str, default=None, help="Train on specific domain only")
    parser.add_argument("--min-samples", type=int, default=100, help="Minimum samples to trigger retraining")
    parser.add_argument("--max-samples", type=int, default=5000, help="Maximum samples per training run")
    parser.add_argument("--epochs", type=int, default=3, help="Number of epochs")
    parser.add_argument("--learning-rate", type=float, default=2e-5, help="Learning rate")
    args = parser.parse_args()
    trained = run_continuous_training(
        args.db, args.output, args.base_model, args.domain,
        args.min_samples, args.max_samples,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
    )
    print(f"Trained on {trained} samples. Model saved to {args.output}")


if __name__ == "__main__":
    main()
