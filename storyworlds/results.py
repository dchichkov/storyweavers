#!/usr/bin/env python3
"""
storyworlds/results.py
======================

Shared result containers for every storyworld script (``storyworlds/worlds/*``).

These are deliberately *domain-agnostic*: a script defines its own
``StoryParams`` dataclass (the per-world set of knobs -- place, activity, prize,
...), and these containers carry whatever that script produced.  Keeping them in
one place means every world serializes the same way and tooling can consume any
world's JSON without knowing the world's internals.

Contract (see ``storyworlds/AGENTS.md``):

* ``StoryParams`` lives **in each script** (its fields are world-specific) and is
  a ``@dataclass`` -- so ``dataclasses.asdict`` can serialize it here.
* ``generate(params) -> StorySample`` is the script's core entry point.
* ``StorySample.world`` holds the live world model for ``--trace`` and is *not*
  serialized.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


class StoryError(Exception):
    """Raised when the requested options describe an unreasonable/invalid story."""


@dataclass
class QAItem:
    """One question/answer pair."""
    question: str
    answer: str

    def __iter__(self):
        """Allow generated worlds to treat QAItem like a ``(question, answer)`` pair."""
        yield self.question
        yield self.answer


@dataclass
class StorySample:
    """A generated story plus its three Q&A sets and the params/seed used.

    ``params`` is the script's own ``StoryParams`` dataclass; ``world`` is the
    live world-model object (kept for ``--trace``, excluded from serialization).
    """
    params: Any                                                # a @dataclass of per-script params
    story: str
    prompts: list[str] = field(default_factory=list)           # (1) generation asks
    story_qa: list[QAItem] = field(default_factory=list)       # (2) grounded in this story
    world_qa: list[QAItem] = field(default_factory=list)       # (3) generic world knowledge
    world: Optional[Any] = field(default=None, repr=False, compare=False)  # not serialized

    def to_dict(self) -> dict:
        return {
            "params": asdict(self.params),
            "story": self.story,
            "prompts": list(self.prompts),
            "story_qa": [asdict(q) for q in self.story_qa],
            "world_qa": [asdict(q) for q in self.world_qa],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
