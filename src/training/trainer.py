from __future__ import annotations

import argparse
import os
from pathlib import Path

from src.model.architecture import EDSPiKEAgent, load_config


def _available_ram_gb() -> float:
    try:
        with Path("/proc/meminfo").open() as f:
            for line in f:
                if line.startswith("MemAvailable:"):
                    return int(line.split()[1]) / 1_048_576
    except OSError:
        pass
    return float("inf")


def _warn_low_ram(compute: dict) -> None:
    ram = _available_ram_gb()
    max_ram = compute.get("max_ram_gb", 0)
    limit = max_ram or 4.0
    if ram < limit:
        import logging
        logging.warning(
            "Available RAM is %.1f GB (limit: %.1f GB). "
            "Training may OOM or be extremely slow. "
            "Use configs/cpu_tiny.yaml for low-RAM environments.",
            ram, limit,
        )


def format_example(row: dict) -> str:
    context = f"\nContext: {row['input']}" if row.get("input") else ""
    return f"<s>[INST] {row['instruction']}{context} [/INST] {row['output']}</s>"


class EDSPiKETrainer:
    def __init__(self, config_path: str = "configs/base_config.yaml") -> None:
        self.config_path = config_path
        self.config = load_config(config_path)

    def train(self, from_scratch: bool = False) -> None:
        try:
            import torch
            from datasets import load_dataset
            from transformers import (
                AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments,
            )
        except ImportError as exc:
            raise RuntimeError("Install the ml dependencies: pip install -e '.[ml]'") from exc
        cfg, model_cfg = self.config["training"], self.config["model"]
        compute_cfg = self.config.get("compute", {})
        device = compute_cfg.get("device", "auto").lower()
        is_cpu = device == "cpu" or (not torch.cuda.is_available() and device == "auto")
        base_model = model_cfg["base_model"]
        if is_cpu:
            _warn_low_ram(compute_cfg)
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
            torch.set_num_threads(min(torch.get_num_threads(), compute_cfg.get("num_workers", 2)))
        tokenizer = AutoTokenizer.from_pretrained(base_model, use_fast=True)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        model = EDSPiKEAgent.initialize_llama_style(self.config_path) if from_scratch else EDSPiKEAgent.load_pretrained(
            base_model, device=device,
        )
        files = {
            "train": "data/splits/train.jsonl",
            "validation": "data/splits/val.jsonl",
        }
        missing = [path for path in files.values() if not Path(path).exists()]
        if missing:
            raise FileNotFoundError(f"Create dataset splits first; missing: {missing}")
        dataset = load_dataset("json", data_files=files)

        def tokenize(batch):
            texts = [
                format_example({
                    "instruction": instruction,
                    "input": input_text,
                    "output": output,
                })
                for instruction, input_text, output in zip(
                    batch["instruction"], batch["input"], batch["output"]
                )
            ]
            return tokenizer(
                texts, truncation=True, max_length=model_cfg["max_sequence_length"], padding=False,
            )

        columns = dataset["train"].column_names
        tokenized = dataset.map(tokenize, batched=True, remove_columns=columns)
        use_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        use_fp16 = torch.cuda.is_available() and not use_bf16
        eval_strat = cfg.get("eval_strategy", "steps")
        if eval_strat is False:
            eval_strat = "no"
        args = TrainingArguments(
            output_dir=cfg["output_dir"],
            learning_rate=cfg["learning_rate"],
            per_device_train_batch_size=cfg["per_device_batch_size"],
            per_device_eval_batch_size=cfg["per_device_batch_size"],
            gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
            num_train_epochs=cfg["num_epochs"],
            warmup_ratio=cfg["warmup_ratio"],
            weight_decay=cfg["weight_decay"],
            logging_steps=cfg["logging_steps"],
            eval_steps=cfg.get("eval_steps", 500) if eval_strat != "no" else 0,
            save_steps=cfg["save_steps"],
            eval_strategy=eval_strat if eval_strat != "no" else "no",
            save_strategy="steps",
            bf16=use_bf16 and not is_cpu,
            fp16=use_fp16 and not is_cpu,
            no_cuda=is_cpu,
            gradient_checkpointing=compute_cfg.get("gradient_checkpointing", False),
            dataloader_num_workers=compute_cfg.get("num_workers", 0),
            report_to="none",
            load_best_model_at_end=eval_strat != "no",
            ddp_find_unused_parameters=False if is_cpu else None,
        )
        trainer = Trainer(
            model=model,
            args=args,
            train_dataset=tokenized["train"],
            eval_dataset=tokenized["validation"] if eval_strat != "no" else None,
            data_collator=DataCollatorForLanguageModeling(tokenizer, mlm=False),
            processing_class=tokenizer,
        )
        trainer.train()
        final = Path(cfg["output_dir"]) / "final"
        trainer.save_model(final)
        tokenizer.save_pretrained(final)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base_config.yaml")
    parser.add_argument("--from-scratch", action="store_true")
    args = parser.parse_args()
    EDSPiKETrainer(args.config).train(args.from_scratch)


if __name__ == "__main__":
    main()
