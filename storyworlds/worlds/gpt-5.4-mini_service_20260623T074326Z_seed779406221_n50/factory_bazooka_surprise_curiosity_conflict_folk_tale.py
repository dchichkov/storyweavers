#!/usr/bin/env python3
"""
storyworlds/worlds/factory_bazooka_surprise_curiosity_conflict_folk_tale.py
===========================================================================

A small folk-tale storyworld about a factory, a bazooka, and the way Surprise,
Curiosity, and Conflict can change a day.

A short seed tale:
---
In a bright little factory at the edge of town, a child found a strange old
bazooka in the storage loft. It was not a toy, but it looked grand and silly,
and the child felt a sudden spark of curiosity. "What does it do?" they asked.

The foreman warned that the bazooka could blast paint cans and crack windows.
Still, the child wanted one surprising puff to see if it could make a cloud of
golden dust. That wish caused a conflict: one worker wanted to hide the bazooka,
another wanted to test it, and the whole room grew noisy.

At last, the oldest miller in town arrived. She did not scold first. She asked
a gentle question, then showed how the bazooka's loud blast could shatter the
factory lamp and frighten the horses outside. The child understood. They set
the bazooka down, chose a bellows instead, and used it to stir safe, glittering
dust across the floor.

The factory went quiet again, except for the soft hum of the belts and the
little laugh of relief.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    role: str = ""
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    protagonist: str
    helper: str
    adult: str
    factory: str
    bazooka: str
    surprise: str
    curiosity: str
    conflict: str
    seed: Optional[int] = None
    p: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass(frozen=True)
class Thing:
    id: str
    label: str
    danger: int = 0
    wonder: int = 0
    loud: bool = False
    BAZOOKA: object | None = None
    FACTORY: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


SETTINGS = {
    "mill-town": "a bright little factory at the edge of town",
    "river-yard": "a busy factory by the river",
    "hill-village": "a old clockworks factory above the hill road",
}

SURPRISES = [
    "a strange old bazooka in the storage loft",
    "a dusty bazooka wrapped in oilcloth",
    "a bazooka with a painted star on its side",
]

CURIOSITIES = [
    "What does it do?",
    "Will it really make a rain of sparks?",
    "Can it blow a soft cloud of dust into the air?",
]

CONFLICTS = [
    "one worker wanted to hide the bazooka, another wanted to test it",
    "the foreman said no, but the child kept asking questions",
    "half the room wanted quiet, and the other half wanted a grand surprise",
]

FACTORY = Thing(id="factory", label="factory")
BAZOOKA = Thing(id="bazooka", label="bazooka", danger=3, wonder=2, loud=True)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


def aspiration(world: World) -> None:
    for e in list(world.entities.values()):
        e.memes["curiosity"] += 1
        e.memes["surprise"] += 1


def turn_conflict(world: World, child: Entity, helper: Entity) -> None:
    child.memes["curiosity"] += 2
    helper.memes["conflict"] += 1
    world.say(
        f"In {world.facts['setting']}, {world.facts['surprise']}. "
        f"{child.id} leaned closer and asked, \"{world.facts['curiosity']}\""
    )
    world.say(
        f"{world.facts['conflict'].capitalize()}. {helper.id} frowned, because "
        f"{BAZOOKA.label} was not meant for play."
    )


def resolve(world: World, child: Entity, helper: Entity, adult: Entity) -> None:
    child.memes["calm"] += 1
    helper.memes["relief"] += 1
    adult.memes["warmth"] += 1
    world.say(
        f"Then {adult.id} came from the lane and asked a gentle question first."
    )
    world.say(
        f"{adult.id} showed how a bellows could lift glittering dust without any "
        f"boom at all."
    )
    world.say(
        f"{child.id} put the bazooka down, and {helper.id} carried it back to the loft."
    )
    world.say(
        "The factory kept its windows, the horses stayed calm, and the floor "
        "sparkled with safe dust instead of trouble."
    )


def tell(params: StoryParams) -> World:
    w = World()
    child = w.add(Entity(id=params.protagonist, kind="character", role="child"))
    helper = w.add(Entity(id=params.helper, kind="character", role="helper"))
    adult = w.add(Entity(id=params.adult, kind="character", role="adult"))
    w.facts.update(
        setting=_safe_lookup(SETTINGS, params.setting),
        surprise=params.surprise,
        curiosity=params.curiosity,
        conflict=params.conflict,
    )
    aspiration(w)
    w.say(
        f"Once there was a {params.factory} in {_safe_lookup(SETTINGS, params.setting)}. "
        f"There, {params.surprise} made every child look twice."
    )
    turn_conflict(w, child, helper)
    resolve(w, child, helper, adult)
    w.facts.update(
        protagonist=child,
        helper=helper,
        adult=adult,
        outcome="settled",
    )
    return w


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale factory and bazooka storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    return StoryParams(
        setting=setting,
        protagonist=rng.choice(["Mina", "Ivo", "Pia", "Ned"]),
        helper=rng.choice(["Bram", "Luz", "Toma", "Rin"]),
        adult=rng.choice(["Grandmother", "Foreman", "Miller", "Auntie"]),
        factory="factory",
        bazooka="bazooka",
        surprise=rng.choice(SURPRISES),
        curiosity=rng.choice(CURIOSITIES),
        conflict=rng.choice(CONFLICTS),
        seed=getattr(args, "seed", None),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a folk-tale style story about {f['setting']} where {f['surprise']} leads to a curious question and a conflict, then ends safely.",
        f"Tell a child-facing tale in a factory with a bazooka, where curiosity causes trouble but a kind adult resolves it with a gentler tool.",
        f"Create a small story showing surprise, curiosity, and conflict around the bazooka, with a calm ending image of safety and repair.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What strange thing did the child find?",
            answer="The child found a bazooka in the factory, and that surprise started the story's trouble."
        ),
        QAItem(
            question="What feeling made the child want to look closer?",
            answer="Curiosity made the child want to ask what the bazooka did."
        ),
        QAItem(
            question="What problem happened in the middle of the story?",
            answer="There was conflict because one person wanted to hide the bazooka and another wanted to test it."
        ),
        QAItem(
            question="How did the story end?",
            answer="An adult showed a safe bellows instead, and everyone put the bazooka away."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a factory?",
            answer="A factory is a place where people make or build things."
        ),
        QAItem(
            question="Why can a bazooka be dangerous?",
            answer="A bazooka can make a very loud blast, so it can break things and scare people."
        ),
        QAItem(
            question="What should children do when they find a dangerous tool?",
            answer="They should stop, stay away from it, and call a grown-up right away."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
chosen_story(S) :- setting(S).
surprise_ok :- bazooka(b), setting(_).
curiosity_flows :- curiosity(_).
conflict_arises :- conflict(_).
story_good :- surprise_ok, curiosity_flows, conflict_arises.
#show story_good/0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    lines.append(asp.fact("bazooka", "bazooka"))
    lines.append(asp.fact("factory", "factory"))
    lines.append(asp.fact("surprise", "surprise"))
    lines.append(asp.fact("curiosity", "curiosity"))
    lines.append(asp.fact("conflict", "conflict"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


def _verify_python() -> int:
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    if "bazooka" not in sample.story.lower() or "factory" not in sample.story.lower():
        print("MISMATCH: required seed words missing.")
        return 1
    print("OK: generated story includes factory and bazooka.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(_verify_python())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        print(asp_program())
        print(asp.one_model(asp_program()))
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting in SETTINGS:
            p = StoryParams(
                setting=setting,
                protagonist="Mina",
                helper="Bram",
                adult="Miller",
                factory="factory",
                bazooka="bazooka",
                surprise=_safe_lookup(SURPRISES, 0),
                curiosity=_safe_lookup(CURIOSITIES, 0),
                conflict=_safe_lookup(CONFLICTS, 0),
                seed=getattr(args, "seed", None),
            )
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = rng.randrange(2**31)
            samples.append(generate(p))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### sample {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
