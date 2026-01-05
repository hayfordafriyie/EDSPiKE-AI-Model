from __future__ import annotations

import argparse
from pathlib import Path


def quantize_awq(model_path: str, output_dir: str, calibration_file: str) -> None:
    """Quantize a trained model using AWQ with representative EDSPiKE prompts."""
    try:
        from awq import AutoAWQForCausalLM
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("Install AutoAWQ in a CUDA environment before quantizing") from exc
    prompts = [
        line.strip() for line in Path(calibration_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if len(prompts) < 32:
        raise ValueError("Provide at least 32 representative calibration prompts")
    model = AutoAWQForCausalLM.from_pretrained(model_path, low_cpu_mem_usage=True)
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=False)
    model.quantize(
        tokenizer,
        quant_config={"zero_point": True, "q_group_size": 128, "w_bit": 4, "version": "GEMM"},
        calib_data=prompts,
    )
    model.save_quantized(output_dir)
    tokenizer.save_pretrained(output_dir)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output-dir", default="checkpoints/awq-4bit")
    parser.add_argument("--calibration-file", required=True)
    args = parser.parse_args()
    quantize_awq(args.model_path, args.output_dir, args.calibration_file)


if __name__ == "__main__":
    main()

