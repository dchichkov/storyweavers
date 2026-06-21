#!/usr/bin/env python3
"""Train a small tokenizer for OpenAI-style StoryWorld chat JSONL."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Iterable


SPECIAL_TOKENS = [
    "<|pad|>",
    "<|begin_of_text|>",
    "<|endoftext|>",
    "<|im_start|>",
    "<|im_end|>",
]

CHAT_TEMPLATE = (
    "{% for message in messages %}"
    "<|im_start|>{{ message['role'] }}\n"
    "{{ message['content'] }}<|im_end|>\n"
    "{% endfor %}"
    "{% if add_generation_prompt %}<|im_start|>assistant\n{% endif %}"
)


def iter_text(jsonl: Path) -> Iterable[str]:
    with jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            for message in row.get("messages", []):
                role = message.get("role", "")
                content = message.get("content", "")
                if role and content:
                    yield f"<|im_start|>{role}\n{content}<|im_end|>\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--vocab-size", type=int, default=16000)
    parser.add_argument("--min-frequency", type=int, default=2)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers
        from transformers import PreTrainedTokenizerFast
    except ImportError as exc:
        raise SystemExit(
            "train_tokenizer.py requires `tokenizers` and `transformers` on the "
            "training machine."
        ) from exc

    args.out.mkdir(parents=True, exist_ok=True)

    # tokenizers trains from files, so materialize the chat text stream once.
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        for text in iter_text(args.input):
            tmp.write(text)

    tokenizer = Tokenizer(models.BPE(unk_token="<|endoftext|>"))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
    tokenizer.decoder = decoders.ByteLevel()
    trainer = trainers.BpeTrainer(
        vocab_size=args.vocab_size,
        min_frequency=args.min_frequency,
        special_tokens=SPECIAL_TOKENS,
    )
    tokenizer.train([str(tmp_path)], trainer)

    fast = PreTrainedTokenizerFast(
        tokenizer_object=tokenizer,
        bos_token="<|begin_of_text|>",
        eos_token="<|endoftext|>",
        unk_token="<|endoftext|>",
        pad_token="<|pad|>",
        additional_special_tokens=["<|im_start|>", "<|im_end|>"],
    )
    fast.chat_template = CHAT_TEMPLATE
    fast.save_pretrained(args.out)
    tmp_path.unlink(missing_ok=True)

    print(f"wrote tokenizer to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
