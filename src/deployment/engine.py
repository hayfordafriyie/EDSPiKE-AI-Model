from __future__ import annotations

import os
import threading
from abc import ABC, abstractmethod


class InferenceEngine(ABC):
    model_name: str

    @abstractmethod
    def generate_batch(
        self, prompts: list[str], max_tokens: int, temperature: float, top_p: float,
    ) -> tuple[list[str], list[int]]:
        raise NotImplementedError


class TransformersEngine(InferenceEngine):
    def __init__(self, model_path: str, device: str = "auto") -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError as exc:
            raise RuntimeError("Production ML dependencies are not installed") from exc
        self.torch = torch
        self.model_name = model_path
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        if self.tokenizer.padding_side != "left":
            self.tokenizer.padding_side = "left"
        quant = os.getenv("MODEL_QUANTIZATION") or None
        if device == "cpu":
            try:
                kwargs = {"device_map": None, "trust_remote_code": False, "low_cpu_mem_usage": True}
                if quant in ("int4", "nf4"):
                    kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True, bnb_4bit_quant_type="nf4",
                        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.float32,
                    )
                elif quant == "int8":
                    kwargs["load_in_8bit"] = True
                self.model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs).to("cpu")
            except (ImportError, RuntimeError, ValueError):
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_path, device_map=None, trust_remote_code=False, low_cpu_mem_usage=True,
                ).to("cpu")
                if quant:
                    self.model = self._quantize_cpu(self.model, quant)
        else:
            dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float32
            kwargs = {"torch_dtype": dtype, "device_map": "auto", "trust_remote_code": False}
            if quant == "nf4":
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                )
            self.model = AutoModelForCausalLM.from_pretrained(model_path, **kwargs)
        self.model.eval()
        self.lock = threading.Lock()

    @staticmethod
    def _quantize_cpu(model, quantization: str):
        import torch
        if quantization not in ("int4", "int8"):
            return model
        try:
            model = torch.quantization.quantize_dynamic(
                model, {torch.nn.Linear}, dtype=torch.qint8,
            )
        except Exception:
            pass
        return model

    def generate_batch(self, prompts, max_tokens, temperature, top_p):
        encoded = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
        device = next(self.model.parameters()).device
        encoded = {key: value.to(device) for key, value in encoded.items()}
        with self.lock, self.torch.inference_mode():
            outputs = self.model.generate(
                **encoded,
                max_new_tokens=max_tokens,
                do_sample=temperature > 0,
                temperature=max(temperature, 1e-5),
                top_p=top_p,
                repetition_penalty=1.05,
            )
        input_width = encoded["input_ids"].shape[1]
        generated = outputs[:, input_width:]
        responses = self.tokenizer.batch_decode(generated, skip_special_tokens=True)
        counts = [int((row != self.tokenizer.pad_token_id).sum()) for row in generated]
        return responses, counts


class VLLMEngine(InferenceEngine):
    def __init__(self, model_path: str) -> None:
        try:
            from vllm import LLM
        except ImportError as exc:
            raise RuntimeError("vLLM is not installed; use the production image") from exc
        self.model_name = model_path
        self.engine = LLM(
            model=model_path,
            quantization=os.getenv("MODEL_QUANTIZATION") or None,
            gpu_memory_utilization=float(os.getenv("GPU_MEMORY_UTILIZATION", "0.9")),
            max_model_len=int(os.getenv("MAX_MODEL_LEN", "2048")),
            trust_remote_code=False,
        )

    def generate_batch(self, prompts, max_tokens, temperature, top_p):
        from vllm import SamplingParams
        params = SamplingParams(
            max_tokens=max_tokens, temperature=temperature, top_p=top_p, repetition_penalty=1.05,
        )
        outputs = self.engine.generate(prompts, params, use_tqdm=False)
        return (
            [item.outputs[0].text for item in outputs],
            [len(item.outputs[0].token_ids) for item in outputs],
        )


def _get_device() -> str:
    return os.getenv("DEVICE", os.getenv("CUDA_VISIBLE_DEVICES", "auto")).lower()


def create_engine() -> InferenceEngine:
    model_path = os.getenv("MODEL_PATH", "checkpoints/final")
    backend = os.getenv("INFERENCE_BACKEND", "transformers").lower()
    device = _get_device()
    if backend == "vllm":
        return VLLMEngine(model_path)
    return TransformersEngine(model_path, device=device)

