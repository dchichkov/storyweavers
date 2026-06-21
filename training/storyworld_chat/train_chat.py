#!/usr/bin/env python3
"""Train a from-scratch Llama-style chat model on OpenAI messages JSONL."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


IM_START = "<|im_start|>"
IM_END = "<|im_end|>"


class OpenAIChatJsonlDataset:
    """Map-style dataset for OpenAI-compatible chat JSONL.

    Labels are masked to assistant content plus the assistant turn terminator.
    System/user tokens provide context but do not contribute to the loss.
    """

    def __init__(self, path: Path, tokenizer: Any, max_length: int) -> None:
        self.path = path
        self.tokenizer = tokenizer
        self.max_length = max_length
        with path.open("r", encoding="utf-8") as handle:
            self.rows = [json.loads(line) for line in handle if line.strip()]

    def __len__(self) -> int:
        return len(self.rows)

    def _encode(self, text: str) -> list[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        row = self.rows[index]
        input_ids: list[int] = []
        labels: list[int] = []

        bos = self.tokenizer.bos_token
        if bos:
            bos_ids = self._encode(bos)
            input_ids.extend(bos_ids)
            labels.extend([-100] * len(bos_ids))

        for message in row["messages"]:
            role = message["role"]
            content = message["content"]
            header_ids = self._encode(f"{IM_START}{role}\n")
            content_ids = self._encode(content)
            footer_ids = self._encode(f"{IM_END}\n")

            input_ids.extend(header_ids)
            labels.extend([-100] * len(header_ids))
            input_ids.extend(content_ids)
            if role == "assistant":
                labels.extend(content_ids)
            else:
                labels.extend([-100] * len(content_ids))
            input_ids.extend(footer_ids)
            if role == "assistant":
                labels.extend(footer_ids)
            else:
                labels.extend([-100] * len(footer_ids))

        if len(input_ids) > self.max_length:
            input_ids = input_ids[: self.max_length]
            labels = labels[: self.max_length]
        return {"input_ids": input_ids, "labels": labels}


@dataclass
class CausalCollator:
    tokenizer: Any

    def __call__(self, features: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        pad_id = self.tokenizer.pad_token_id
        max_len = max(len(f["input_ids"]) for f in features)
        input_ids = []
        labels = []
        attention_mask = []
        for feature in features:
            ids = feature["input_ids"]
            labs = feature["labels"]
            pad = max_len - len(ids)
            input_ids.append(ids + [pad_id] * pad)
            labels.append(labs + [-100] * pad)
            attention_mask.append([1] * len(ids) + [0] * pad)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
            "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-jsonl", type=Path, required=True)
    parser.add_argument("--eval-jsonl", type=Path, default=None)
    parser.add_argument("--tokenizer", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--num-train-epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--min-lr-ratio", type=float, default=0.1)
    parser.add_argument("--warmup-ratio", type=float, default=0.03)
    parser.add_argument("--weight-decay", type=float, default=0.1)
    parser.add_argument("--max-grad-norm", type=float, default=1.0)
    parser.add_argument("--per-device-train-batch-size", type=int, default=8)
    parser.add_argument("--per-device-eval-batch-size", type=int, default=8)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=32)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--eval-steps", type=int, default=250)
    parser.add_argument("--save-steps", type=int, default=1000)
    parser.add_argument("--save-total-limit", type=int, default=3)
    parser.add_argument("--bf16", action="store_true")
    parser.add_argument("--gradient-checkpointing", action="store_true")
    parser.add_argument("--report-to", default="tensorboard")
    parser.add_argument("--seed", type=int, default=20260621)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        from transformers import (
            AutoConfig,
            AutoModelForCausalLM,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise SystemExit(
            "train_chat.py requires torch, transformers, and their training "
            "dependencies on the target machine."
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(args.tokenizer)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    config = AutoConfig.from_pretrained(args.config)
    config.vocab_size = len(tokenizer)
    config.max_position_embeddings = args.max_length
    config.pad_token_id = tokenizer.pad_token_id
    config.bos_token_id = tokenizer.bos_token_id
    config.eos_token_id = tokenizer.eos_token_id

    model = AutoModelForCausalLM.from_config(config)
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()
        model.config.use_cache = False

    train_dataset = OpenAIChatJsonlDataset(args.train_jsonl, tokenizer, args.max_length)
    eval_dataset = (
        OpenAIChatJsonlDataset(args.eval_jsonl, tokenizer, args.max_length)
        if args.eval_jsonl
        else None
    )

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        overwrite_output_dir=False,
        num_train_epochs=args.num_train_epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        per_device_eval_batch_size=args.per_device_eval_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_ratio=args.warmup_ratio,
        lr_scheduler_type="cosine",
        weight_decay=args.weight_decay,
        max_grad_norm=args.max_grad_norm,
        bf16=args.bf16,
        tf32=True,
        logging_steps=args.logging_steps,
        eval_strategy="steps" if eval_dataset is not None else "no",
        eval_steps=args.eval_steps if eval_dataset is not None else None,
        save_steps=args.save_steps,
        save_total_limit=args.save_total_limit,
        report_to=args.report_to.split(",") if args.report_to else [],
        remove_unused_columns=False,
        dataloader_num_workers=4,
        ddp_find_unused_parameters=False,
        seed=args.seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=CausalCollator(tokenizer),
        processing_class=tokenizer,
    )
    trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)

    if eval_dataset is not None:
        metrics = trainer.evaluate()
        if "eval_loss" in metrics:
            metrics["perplexity"] = math.exp(metrics["eval_loss"])
        print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
