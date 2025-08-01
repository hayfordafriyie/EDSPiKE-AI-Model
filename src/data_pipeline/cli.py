import argparse
import json

from .collector import DataCollector
from .preprocessor import DataPreprocessor
from .splitter import DataSplitter


def main() -> None:
    parser = argparse.ArgumentParser(description="EDSPiKE data pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    collect = sub.add_parser("collect")
    collect.add_argument("source")
    collect.add_argument("--name", default="import")
    process = sub.add_parser("process")
    process.add_argument("--raw-dir", default="data/raw")
    process.add_argument("--output", default="data/processed/processed_data.jsonl")
    split = sub.add_parser("split")
    split.add_argument("--input", default="data/processed/processed_data.jsonl")
    split.add_argument("--output-dir", default="data/splits")
    args = parser.parse_args()
    if args.command == "collect":
        collector = DataCollector()
        print(collector.save_raw_data(collector.collect_directory(args.source), args.name))
    elif args.command == "process":
        print(json.dumps({"processed": DataPreprocessor().process_all_sources(args.raw_dir, args.output)}))
    else:
        print(json.dumps(DataSplitter().split(args.input, args.output_dir)))


if __name__ == "__main__":
    main()
