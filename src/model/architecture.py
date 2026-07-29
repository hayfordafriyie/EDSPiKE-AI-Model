from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: str | Path = "configs/base_config.yaml") -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


class EDSPiKEAgent:
    @staticmethod
    def initialize_llama_style(config_path: str = "configs/base_config.yaml"):
        try:
            from transformers import LlamaConfig, LlamaForCausalLM
        except ImportError as exc:
            raise RuntimeError("Install the ml dependencies: pip install -e '.[ml]'") from exc
        cfg = load_config(config_path)["model"]
        config = LlamaConfig(
            vocab_size=cfg["vocab_size"],
            hidden_size=cfg["hidden_size"],
            intermediate_size=cfg["intermediate_size"],
            num_hidden_layers=cfg["num_hidden_layers"],
            num_attention_heads=cfg["num_attention_heads"],
            num_key_value_heads=cfg.get("num_key_value_heads", cfg["num_attention_heads"]),
            max_position_embeddings=cfg["max_sequence_length"],
            attention_dropout=cfg.get("dropout", 0.0),
        )
        return LlamaForCausalLM(config)

    @staticmethod
    def _quantize_cpu(model, quantization: str):
        import torch
        if quantization not in ("int4", "int8"):
            return model
        qconfig = torch.quantization.QConfig(
            activation=torch.quantization.MinMaxObserver.with_args(dtype=torch.quint8),
            weight=torch.quantization.PerChannelMinMaxObserver.with_args(dtype=torch.qint8),
        )
        quantizable = set()
        for name, module in model.named_modules():
            if isinstance(module, (torch.nn.Linear,)):
                quantizable.add(name)
        if not quantizable:
            return model
        try:
            model = torch.quantization.quantize_dynamic(
                model, {torch.nn.Linear}, dtype=torch.qint8,
            )
        except Exception:
            pass
        return model

    @staticmethod
    def load_pretrained(model_id: str, quantization: str | None = None, device: str = "auto"):
        try:
            import torch
            from transformers import AutoModelForCausalLM, BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError("Install the ml dependencies: pip install -e '.[ml]'") from exc
        if device == "cpu":
            kwargs: dict[str, Any] = {"device_map": None, "trust_remote_code": False, "low_cpu_mem_usage": True}
            try:
                if quantization in ("int4", "nf4"):
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True,
                        bnb_4bit_compute_dtype=torch.float32,
                    )
                elif quantization == "int8":
                    kwargs["load_in_8bit"] = True
                model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
            except (ImportError, RuntimeError, ValueError):
                model = AutoModelForCausalLM.from_pretrained(
                    model_id, device_map=None, trust_remote_code=False, low_cpu_mem_usage=True,
                )
                if quantization:
                    model = EDSPiKEAgent._quantize_cpu(model, quantization)
            return model.to("cpu")
        kwargs: dict[str, Any] = {"device_map": "auto", "trust_remote_code": False}
        if torch.cuda.is_available():
            kwargs["torch_dtype"] = torch.bfloat16
        if quantization == "nf4":
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
        return AutoModelForCausalLM.from_pretrained(model_id, **kwargs)

