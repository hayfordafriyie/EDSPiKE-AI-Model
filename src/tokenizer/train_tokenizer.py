from __future__ import annotations

import argparse
import json
from pathlib import Path


def training_corpus(files: list[str]):
    for filename in files:
        with Path(filename).open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                yield "\n".join([row.get("instruction", ""), row.get("input", ""), row.get("output", "")])


def train_custom_tokenizer(data_files: list[str], output: str, vocab_size: int = 32000) -> Path:
    try:
        from tokenizers import Tokenizer, decoders, normalizers, pre_tokenizers, processors
        from tokenizers.models import BPE
        from tokenizers.trainers import BpeTrainer
    except ImportError as exc:
        raise RuntimeError("Install the ml dependencies: pip install -e '.[ml]'") from exc
    tokenizer = Tokenizer(BPE(unk_token="<unk>"))
    tokenizer.normalizer = normalizers.NFKC()
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    trainer = BpeTrainer(
        vocab_size=vocab_size,
        min_frequency=2,
        special_tokens=["<pad>", "<unk>", "<s>", "</s>"],
    )
    tokenizer.train_from_iterator(training_corpus(data_files), trainer=trainer)
    tokenizer.post_processor = processors.ByteLevel(trim_offsets=False)
    tokenizer.decoder = decoders.ByteLevel()
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(target))
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--output", default="configs/tokenizer.json")
    parser.add_argument("--vocab-size", type=int, default=32000)
    args = parser.parse_args()
    print(train_custom_tokenizer(args.files, args.output, args.vocab_size))


if __name__ == "__main__":
    main()

