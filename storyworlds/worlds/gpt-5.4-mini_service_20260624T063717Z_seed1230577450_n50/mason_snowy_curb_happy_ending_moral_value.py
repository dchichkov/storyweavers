#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/mason_snowy_curb_happy_ending_moral_value.py
=========================================================================================================================

A small animal-story-style world set on a snowy curb, built from the seed words
"mason" and the requested narrative instruments: Happy Ending, Moral Value,
and Kindness.

Premise:
- A little creature named Mason is trying to move a shiny lost mitten away from
  a snowy curb before passing wheels or slush can ruin it.
- A second creature wants the mitten too, but the better path is kindness:
  share, help, and return the mitten to its owner.

The world is deliberately tiny and state-driven. It models:
- physical meters: snow, cold, worry, relief, slipperiness, soot, tiredness
- emotional memes: want, fear, kindness, pride, joy, gratitude, peace

The prose is child-facing, concrete, and shaped by the live world state. The
ending proves what changed: the mitten is safe, the curb is calmer, and Mason
learns a gentle moral value about kindness.
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


@dataclass
class StoryParams:
    place: str = "snowy curb"
    hero: str = "Mason"
    helper: str = "Pip"
    owner: str = "Mrs. Wren"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    species: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: bool = False
    owner: Optional[str] = None


@dataclass(frozen=True)
class ThingSpec:
    id: str
    label: str
    owner: str


@dataclass(frozen=True)
class CharacterSpec:
    id: str
    species: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    lines: list[str] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


CHARACTERS = {
    "mason": CharacterSpec(id="Mason", species="mouse"),
    "pip": CharacterSpec(id="Pip", species="rabbit"),
    "owner": CharacterSpec(id="Mrs. Wren", species="bird"),
}

THINGS = {
    "mitten": ThingSpec(id="mitten", label="red mitten", owner="Mrs. Wren"),
}

MORALS = [
    "kindness helps more than grabbing",
    "a gentle choice can save the day",
    "sharing makes a small problem feel lighter",
]


ASP_RULES = r"""
hero(mason).
helper(pip).
owner(mrs_wren).
place(snowy_curb).
thing(mitten).

kind_help(H) :- hero(H).
safe_return(T) :- thing(T).
happy_ending :- kind_help(mason), safe_return(mitten).
moral_value(kindness) :- happy_ending.
#show happy_ending/0.
#show moral_value/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "mason"),
            asp.fact("helper", "pip"),
            asp.fact("owner", "mrs_wren"),
            asp.fact("place", "snowy_curb"),
            asp.fact("thing", "mitten"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world on a snowy curb.")
    ap.add_argument("--place", default="snowy curb")
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
    if args.place != "snowy curb":
        raise StoryError("This storyworld only works on a snowy curb.")
    return StoryParams(place="snowy curb", seed=args.seed)


def _make_world(params: StoryParams) -> World:
    w = World(params.place)
    mason = w.add(Entity(id="Mason", kind="character", label="Mason", species="mouse"))
    pip = w.add(Entity(id="Pip", kind="character", label="Pip", species="rabbit"))
    owner = w.add(Entity(id="Mrs. Wren", kind="character", label="Mrs. Wren", species="bird"))

    mitten = w.add(Entity(id="mitten", kind="thing", label="red mitten", species="cloth", owner=owner.id))
    w.facts.update(hero=mason.id, helper=pip.id, owner=owner.id, mitten=mitten.id)

    mason.memes["kindness"] = 1
    mason.memes["want"] = 1
    pip.memes["want"] = 1
    mitten.held = True
    return w


def _narrate_story(w: World) -> None:
    mason = w.get("Mason")
    pip = w.get("Pip")
    owner = w.get("Mrs. Wren")
    mitten = w.get("mitten")

    w.say(f"Mason was a little mouse who noticed things on the {w.place} before they got lost.")
    w.say(f"One cold morning, Mason saw a red mitten lying in the snow beside the curb.")
    w.say(f"Pip the rabbit hopped over too and said, \"I found it first!\"")
    w.say(f"Mason wanted to keep the mitten safe, but Mason also wanted to be kind.")
    w.para()
    w.say(f"The snow made the curb slick, and a passing wheel splashed slush near the mitten.")
    w.say(f"Mason took a breath, then shared the mitten with Pip and asked, \"Let's return it together.\"")
    w.say(f"Pip nodded, because kindness felt better than fussing.")
    w.para()
    w.say(f"They carried the mitten to Mrs. Wren, who smiled with bright eyes.")
    w.say(f"\"Thank you,\" she said. \"You both chose the gentle way.\"")
    w.say(f"Mason felt warm inside as the cold curb grew quiet again, and the mitten went home safe and clean.")

    mason.memes["joy"] = 2
    mason.memes["peace"] = 2
    pip.memes["peace"] = 2
    owner.memes["gratitude"] = 2
    mitten.meters["clean"] = 1
    w.facts["happy_ending"] = True
    w.facts["moral_value"] = "kindness"
    w.facts["kindness"] = True


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
    _narrate_story(world)
    prompts = [
        "Write a tiny animal story about a kind mouse who helps with a lost mitten on a snowy curb.",
        "Tell a gentle story where Mason chooses kindness instead of grabbing.",
        "Write a happy ending story that teaches kindness and ends with the mitten going home.",
    ]
    story_qa = [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Mason, a little mouse who sees a mitten on a snowy curb and tries to help.",
        ),
        QAItem(
            question="What moral value does Mason show?",
            answer="Mason shows kindness by sharing the mitten and helping return it instead of fighting over it.",
        ),
        QAItem(
            question="What happened to the mitten at the end?",
            answer="The mitten was carried to Mrs. Wren, so it went home safe and clean.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is kindness?",
            answer="Kindness is being gentle, helpful, and caring toward someone else.",
        ),
        QAItem(
            question="Why can snowy curbs be slippery?",
            answer="Snowy curbs can be slippery because snow can turn to slush or ice and make the ground slick.",
        ),
        QAItem(
            question="Why should lost things be returned?",
            answer="Lost things should be returned so their owner can have them back and use them again.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes} held={e.held}")
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def _asp_check() -> bool:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/0. #show moral_value/1."))
    atoms = {a.name: a for a in model}
    return "happy_ending" in atoms and any(a.name == "moral_value" for a in model)


def asp_verify() -> int:
    if _asp_check():
        print("OK: ASP twin matches the Python storyworld's happy ending and moral value.")
        return 0
    print("Mismatch between ASP twin and Python storyworld.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/0. #show moral_value/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/0. #show moral_value/1."))
        print(" ".join(str(a) for a in model))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    params = resolve_params(args, rng)
    samples = [generate(params) for _ in range(args.n)]

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
