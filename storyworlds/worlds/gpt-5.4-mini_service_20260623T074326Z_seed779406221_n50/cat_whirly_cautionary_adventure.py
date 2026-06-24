#!/usr/bin/env python3
"""
Standalone storyworld: cat + whirly cautionary adventure.

A small, child-facing simulation about a curious cat, a whirly thing, and a
wise ending that shows why caution matters. The world supports prose, Q&A, trace,
JSON, and an ASP twin for parity checking.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    role: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, object] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "cat":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "child":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    danger: float = 0.0
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Whirly:
    id: str
    label: str
    scene: str
    risky_near: str
    makes_tangle: bool = True
    gives_breeze: bool = False
    lift: int = 1


@dataclass
class SafeChoice:
    id: str
    label: str
    phrase: str
    effect: str


@dataclass
class StoryParams:
    cat_name: str
    helper_name: str
    whirly: str
    place: str
    safe_choice: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.place: Place | None = None
        self.whirly: Whirly | None = None
        self.safe_choice: SafeChoice | None = None
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self._fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def trace(self) -> str:
        parts = ["--- world trace ---"]
        for e in self.entities.values():
            bits = []
            if e.meters:
                bits.append(f"meters={e.meters}")
            if e.memes:
                bits.append(f"memes={e.memes}")
            if e.role:
                bits.append(f"role={e.role}")
            parts.append(f"{e.id}: {' '.join(bits)}")
        if self.place:
            parts.append(f"place={self.place.id} danger={self.place.danger}")
        return "\n".join(parts)


THEMES = {
    "harbor": "a bright harbor",
    "garden": "a windy garden",
    "attic": "a dusty attic",
}

PLACES = {
    "dock": Place(id="dock", label="the dock"),
    "garden": Place(id="garden", label="the garden"),
    "attic": Place(id="attic", label="the attic"),
}

WHIRLIES = {
    "kite": Whirly(id="kite", label="kite", scene="a kite that looped in the wind", risky_near="the tall mast"),
    "pinwheel": Whirly(id="pinwheel", label="pinwheel", scene="a pinwheel spinning like a tiny storm", risky_near="the ledge"),
    "drone": Whirly(id="drone", label="drone", scene="a whirly little drone buzzing overhead", risky_near="the water"),
}

SAFE_CHOICES = {
    "string": SafeChoice(id="string", label="string", phrase="a long string", effect="held the thing steady"),
    "stick": SafeChoice(id="stick", label="stick", phrase="a sturdy stick", effect="kept their paws away from danger"),
    "ribbon": SafeChoice(id="ribbon", label="ribbon", phrase="a bright ribbon", effect="made the game gentle and safe"),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cat and whirly cautionary adventure storyworld.")
    ap.add_argument("--cat", choices=["Milo", "Pip", "Nico", "Luna", "Ziggy"])
    ap.add_argument("--helper", choices=["June", "Ollie", "Mira", "Bea", "Toby"])
    ap.add_argument("--whirly", choices=WHIRLIES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--safe-choice", choices=SAFE_CHOICES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        cat_name=args.cat or rng.choice(list(["Milo", "Pip", "Nico", "Luna", "Ziggy"])),
        helper_name=args.helper or rng.choice(list(["June", "Ollie", "Mira", "Bea", "Toby"])),
        whirly=args.whirly or rng.choice(list(WHIRLIES)),
        place=args.place or rng.choice(list(PLACES)),
        safe_choice=args.safe_choice or rng.choice(list(SAFE_CHOICES)),
        seed=args.seed,
    )


def _story_setup(world: World, p: StoryParams) -> tuple[Entity, Entity]:
    cat = world.add(Entity(id=p.cat_name, kind="character", type="cat", role="curious", label=p.cat_name))
    helper = world.add(Entity(id=p.helper_name, kind="character", type="child", role="cautious", label=p.helper_name))
    cat.memes["curiosity"] = 1.0
    helper.memes["care"] = 1.0
    return cat, helper


def _risk_rule(world: World, cat: Entity, helper: Entity) -> None:
    if "risk" in world._fired:
        return
    world._fired.add("risk")
    if world.place:
        world.place.danger += 1
    cat.memes["excitement"] = cat.memes.get("excitement", 0.0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0.0) + 1


def tell_story(params: StoryParams) -> World:
    world = World()
    world.place = PLACES[params.place]
    world.whirly = WHIRLIES[params.whirly]
    world.safe_choice = SAFE_CHOICES[params.safe_choice]
    cat, helper = _story_setup(world, params)

    world.say(
        f"One breezy afternoon, {cat.id} the cat padded into {world.place.label}, "
        f"where {world.whirly.scene}."
    )
    world.say(
        f"{cat.id} swished {cat.pronoun('possessive')} tail. "
        f'"Look!" {helper.id} said. "That whirly thing is spinning so fast!"'
    )

    world.say(
        f"{cat.id} wanted to leap toward it, but {helper.id} peered closer and "
        f"noticed that it could tangle near {world.whirly.risky_near}."
    )
    world.say(
        f'"Hold on," {helper.id} warned. "We need a safer way to play."'
    )

    _risk_rule(world, cat, helper)

    world.say(
        f"Instead of chasing the whirly thing, {helper.id} brought out {world.safe_choice.phrase}. "
        f"It {world.safe_choice.effect}."
    )
    world.say(
        f"{cat.id} batted at the safe toy, and the breeze became part of the game, not a problem."
    )
    world.say(
        f"In the end, {cat.id} learned that a quick paw can wait, and a careful plan makes the adventure better."
    )

    world.facts = {
        "cat": params.cat_name,
        "helper": params.helper_name,
        "whirly": params.whirly,
        "place": params.place,
        "safe_choice": params.safe_choice,
        "danger": world.place.danger if world.place else 0.0,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a child-friendly cautionary adventure about {world.facts['cat']} and a whirly thing in {world.place.label}.",
        f"Tell a story where {world.facts['helper']} warns {world.facts['cat']} before the whirly thing causes trouble.",
        f"End with a safe choice that keeps the adventure playful and calm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Who was the curious cat in the story?",
            answer=f"The curious cat was {world.facts['cat']}.",
        ),
        QAItem(
            question=f"Who gave the warning?",
            answer=f"{world.facts['helper']} gave the warning and helped find a safer way to play.",
        ),
        QAItem(
            question=f"What safer thing did they use instead of chasing the whirly thing?",
            answer=f"They used {SAFE_CHOICES[world.facts['safe_choice']].phrase} so the game stayed safe.",
        ),
        QAItem(
            question=f"Why was the whirly thing risky?",
            answer=f"It could tangle and cause trouble near {WHIRLIES[world.facts['whirly']].risky_near}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should you be careful around spinning things?",
            answer="Spinning things can grab string, paws, or hair, so it is safer to keep a little distance.",
        ),
        QAItem(
            question="What should a child do if a game starts to feel risky?",
            answer="Stop, listen to a grown-up or a careful friend, and choose a safer way to play.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
cat_story(C,H,W,P) :- cat(C), helper(H), whirly(W), place(P).
safe_end(C,H) :- cat_story(C,H,_,_), warning(H), safe_choice(H).
warning(H) :- helper(H).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for c in ["Milo", "Pip", "Nico", "Luna", "Ziggy"]:
        lines.append(asp.fact("cat", c))
    for h in ["June", "Ollie", "Mira", "Bea", "Toby"]:
        lines.append(asp.fact("helper", h))
    for w in WHIRLIES:
        lines.append(asp.fact("whirly", w))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for s in SAFE_CHOICES:
        lines.append(asp.fact("safe_choice", s))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show cat_story/4.\n#show safe_end/2."))
    ok = bool(model)
    print("OK: ASP program solved." if ok else "MISMATCH: ASP program had no model.")
    return 0 if ok else 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show cat_story/4.\n#show safe_end/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("", "#show cat_story/4.\n#show safe_end/2."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = [
            StoryParams("Pip", "June", "kite", "harbor", "string"),
            StoryParams("Luna", "Mira", "pinwheel", "garden", "ribbon"),
            StoryParams("Nico", "Ollie", "drone", "attic", "stick"),
        ]
        samples = [generate(p) for p in params]
    else:
        for i in range(args.n):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
