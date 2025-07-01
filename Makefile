.PHONY: setup test data api cpu-api train-cpu benchmark

setup:
	python -m venv .venv
	.venv/bin/pip install -e ".[test]"
	.venv/bin/python scripts/setup_dirs.py

test:
	pytest

data:
	python -m src.data_pipeline.cli process
	python -m src.data_pipeline.cli split

api:
	uvicorn src.deployment.inference_server:app --host 0.0.0.0 --port 8000

cpu-api:
	DEVICE=cpu MODEL_QUANTIZATION=int4 uvicorn src.deployment.inference_server:app --host 0.0.0.0 --port 8000

train-cpu:
	python -m src.training.trainer --config configs/cpu_tiny.yaml

benchmark:
	python scripts/benchmark.py

