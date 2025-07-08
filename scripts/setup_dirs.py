from pathlib import Path

for directory in (
    "data/raw", "data/processed", "data/splits", "checkpoints", "models", "reports",
):
    Path(directory).mkdir(parents=True, exist_ok=True)
print("EDSPiKE project directories are ready.")

