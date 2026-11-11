"""Dictionary residual stream -> causal identity blocks -> sparse readout head."""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Iterable, Iterator

from .head import FrequencyHead, Readout
from .latents import WordNetLexicon, encode, tokenize


def causal_mask(length: int) -> list[list[bool]]:
    """True means visible: each query can read itself and earlier positions."""
    if length < 0:
        raise ValueError("length must be nonnegative")
    return [[key <= query for key in range(length)] for query in range(length)]


@dataclass(frozen=True)
class CausalAttention:
    """A block receives only its query's visible prefix, never future latents.

    No Q/K similarity, softmax attention, or learned value projection yet.
    This is the causal memory interface for those future symbolic operations.
    """

    visible: tuple[dict, ...]


@dataclass(frozen=True)
class PassThroughBlock:
    index: int

    def forward(self, latent: dict, attention: CausalAttention) -> dict:
        return latent


@dataclass(frozen=True)
class TrainingExample:
    context: tuple[str, ...]
    target: str
    target_position: int


@dataclass
class ForwardResult:
    residual_stream: list[dict]
    predictions: list[Readout]
    next_token: Readout


class Storyformer:
    def __init__(self, *, context_size: int = 256, num_blocks: int = 2,
                 top_k: int = 10, lexicon=None, head: FrequencyHead | None = None):
        if context_size < 2 or num_blocks < 0 or top_k < 1:
            raise ValueError("context_size >= 2, num_blocks >= 0, and top_k >= 1 are required")
        self.context_size, self.top_k = context_size, top_k
        self.blocks = tuple(PassThroughBlock(i) for i in range(num_blocks))
        self.lexicon = lexicon  # Lazy loading permits count training without WordNet IO.
        self.head = head if head is not None else FrequencyHead()

    def training_examples(self, document: str) -> Iterator[TrainingExample]:
        """Teacher forcing: tokens strictly before target i predict target i.

        Long documents get sliding windows; no target is lost at chunk boundaries.
        Position zero has empty context and teaches the unigram fallback.
        """
        tokens = tokenize(document)
        for i, target in enumerate(tokens):
            yield TrainingExample(tuple(tokens[max(0, i - self.context_size):i]), target, i)

    def fit(self, documents: Iterable[str]):
        # With identity blocks, counting the last two input tokens is exactly the
        # token-channel training transform. Avoid repeated lexical lookup and
        # 256-token window allocation for every target during corpus training.
        if not all(type(block) is PassThroughBlock for block in self.blocks):
            raise NotImplementedError("count training currently requires pass-through blocks")
        self.head.fit(documents)
        return self

    def forward(self, text: str) -> ForwardResult:
        tokens = tokenize(text)
        offset = max(0, len(tokens) - self.context_size)
        if self.lexicon is None:
            self.lexicon = WordNetLexicon()
        stream = encode(tokens[offset:], self.lexicon, offset=offset)
        for block in self.blocks:
            stream = [block.forward(latent, CausalAttention(tuple(stream[:i + 1])))
                      for i, latent in enumerate(stream)]
        predictions = [self.head.read(stream[:i + 1], top_k=self.top_k)
                       for i in range(len(stream))]
        next_token = predictions[-1] if predictions else self.head.read([], top_k=self.top_k)
        return ForwardResult(stream, predictions, next_token)

    def predict(self, text: str) -> dict[str, float]:
        return self.forward(text).next_token.distribution

    def save(self, path: str | Path):
        payload = {
            "format": "storyformers-v1",
            "config": {"context_size": self.context_size, "num_blocks": len(self.blocks),
                       "top_k": self.top_k},
            "counts": self.head.to_rows(),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")

    @classmethod
    def load(cls, path: str | Path, *, lexicon=None):
        payload = json.loads(Path(path).read_text())
        if payload.get("format") != "storyformers-v1":
            raise ValueError("unsupported storyformers model format")
        return cls(**payload["config"], lexicon=lexicon,
                   head=FrequencyHead.from_rows(payload["counts"]))
