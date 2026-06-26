#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cafe_caption_twist_tall_tale.py
==============================================================================================================

A small, self-contained storyworld about a cafe, a caption, and a twisty,
tall-tale-sized misunderstanding that gets set right.

The world is built from a tiny source tale:
- A child visits a cafe with a grown-up.
- A big caption under a giant pastry seems to tell the wrong story.
- The child worries the mistake will spoil the cafe's famous treat.
- A twist reveals the caption belongs to something else entirely.
- The ending shows the new understanding, with the cafe brighter than before.

The prose is meant to feel like a cheerful tall tale: a little larger than life,
but still grounded in concrete simulated state.
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
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def display(self) -> str:
        return self.label or self.type


@dataclass
class Cafe:
    name: str = "the lantern cafe"
    busy: bool = True
    tall: bool = True
    has_caption_board: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    grownup: str
    cafe_name: str
    pastry: str
    seed: Optional[int] = None


class World:
    def __init__(self, cafe: Cafe) -> None:
        self.cafe = cafe
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.cafe)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_confusion(world: World) -> list[str]:
    out = []
    child = world.get("child")
    board = world.get("caption")
    pastry = world.get("pastry")
    if child.memes.get("confused", 0.0) < THRESHOLD:
        return out
    sig = ("confusion",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    board.memes["attention"] = board.memes.get("attention", 0.0) + 1
    pastry.memes["mystery"] = pastry.memes.get("mystery", 0.0) + 1
    out.append(f"The caption looked twice as puzzling as a snowstorm in a teacup.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    board = world.get("caption")
    hidden = world.get("hidden")
    child = world.get("child")
    if board.memes.get("turned", 0.0) < THRESHOLD:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hidden.meters["revealed"] = 1
    child.memes["wonder"] = child.memes.get("wonder", 0.0) + 1
    out.append("That was when the twist came tumbling out: the caption belonged to the hidden treat, not the giant pastry.")
    return out


CAUSAL_RULES = [
    Rule("confusion", _r_confusion),
    Rule("twist", _r_twist),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_story_model(params: StoryParams) -> World:
    cafe = Cafe(name=params.cafe_name)
    world = World(cafe)

    child = world.add(Entity(id="child", kind="character", type=params.gender, label=params.name))
    grownup = world.add(Entity(id="grownup", kind="character", type=params.grownup, label=params.grownup))
    pastry = world.add(Entity(
        id="pastry",
        type="thing",
        label=params.pastry,
        phrase=f"a towering {params.pastry}",
        caretaker="grownup",
    ))
    caption = world.add(Entity(
        id="caption",
        type="thing",
        label="caption card",
        phrase="a handwritten caption card",
        owner="grownup",
    ))
    hidden = world.add(Entity(
        id="hidden",
        type="thing",
        label="tiny jam tart",
        phrase="a tiny jam tart under a glass dome",
        caretaker="grownup",
    ))

    world.say(
        f"At {cafe.name}, everything seemed built by a giant with a sweet tooth: "
        f"the tables were broad as wagon wheels, the cups were deep as little wells, and "
        f"{child.display()} walked in beside {grownup.display()} with wide eyes."
    )
    world.say(
        f"{child.display().capitalize()} loved the cafe's famous {pastry.label}, but the big caption "
        f"under its picture said, \"Small as a pebble,\" and that made no sense at all."
    )
    child.memes["curiosity"] = 1
    child.memes["confused"] = 1
    board_state = world.get("caption")
    board_state.meters["wrong"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.display().capitalize()} pointed at the sign and said, "
        f"\"If that caption is for the {pastry.label}, somebody mixed up the whole circus of breakfast!\""
    )
    grownup.memes["worry"] = 1
    world.say(
        f"{grownup.display().capitalize()} lifted the card, looked behind it, and found a second picture waiting there like a squirrel under a hat."
    )
    board_state.memes["turned"] = 1
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"The second picture showed {hidden.phrase}, and its caption had been hiding the real joke all along."
    )
    world.say(
        f"The cafe was not wrong at all; the caption had simply chosen the smallest treat in the room, while the big {pastry.label} stood nearby as proud as a parade horse."
    )
    child.memes["joy"] = 1
    grownup.memes["relief"] = 1
    world.say(
        f"{child.display().capitalize()} grinned, {grownup.display()} laughed, and the whole lantern cafe seemed to glow brighter, as if the teacups themselves had learned the punch line."
    )

    world.facts.update(
        child=child,
        grownup=grownup,
        pastry=pastry,
        caption=caption,
        hidden=hidden,
        cafe=cafe,
        wrong_caption=True,
        twist_revealed=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pastry = f["pastry"]
    return [
        "Write a short tall-tale-style story set in a cafe where a caption causes a twist.",
        f"Tell a child-friendly story about {child.label} at {world.cafe.name} when a caption under {pastry.label} seems wrong.",
        "Write a funny cafe story that begins with confusion, turns on a hidden caption, and ends with a cheerful surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    pastry = f["pastry"]
    hidden = f["hidden"]
    cafe = f["cafe"]
    return [
        QAItem(
            question=f"Where did {child.label} go with {grownup.display()}?",
            answer=f"{child.label} went to {cafe.name} with {grownup.display()}. It was a bright, bustling cafe with a giant-feeling room."
        ),
        QAItem(
            question=f"What looked wrong about the caption at first?",
            answer=f"At first, the caption seemed to describe the {pastry.label} as small as a pebble, which did not match the huge pastry on display."
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that the caption belonged to a hidden jam tart, not to the {pastry.label}. Once the card was turned, the surprise made sense."
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"{child.label} ended up smiling at the clever trick, while the cafe felt warm and cheerful again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cafe?",
            answer="A cafe is a place where people sit, drink, and eat small treats like cakes, tarts, and muffins."
        ),
        QAItem(
            question="What is a caption?",
            answer="A caption is a short line of words that explains a picture or sign."
        ),
        QAItem(
            question="What does a twist mean in a story?",
            answer="A twist is a surprising turn that changes what you thought was happening."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.phrase:
            parts.append(f'phrase="{e.phrase}"')
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for (n,) in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("setting", "cafe"),
        asp.fact("has", "cafe", "caption_board"),
        asp.fact("has", "cafe", "hidden_tart"),
        asp.fact("event", "wrong_caption"),
        asp.fact("event", "twist_reveal"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
wrong_caption :- event(wrong_caption), setting(cafe), has(cafe,caption_board).
twist_reveal :- event(twist_reveal), wrong_caption, has(cafe,hidden_tart).
valid_story :- wrong_caption, twist_reveal.
#show valid_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/0."))
    ok = any(sym.name == "valid_story" for sym in model)
    if ok:
        print("OK: ASP gate accepts the cafe caption twist story.")
        return 0
    print("MISMATCH: ASP gate rejected the story.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall-tale cafe storyworld with a caption twist.")
    ap.add_argument("--name", choices=["Mina", "Leo", "Ivy", "Noah"], default=None)
    ap.add_argument("--gender", choices=["girl", "boy"], default=None)
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"], default=None)
    ap.add_argument("--cafe-name", default=None)
    ap.add_argument("--pastry", choices=["muffin", "cake", "tart", "bun"], default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name is None:
        args.name = rng.choice(["Mina", "Leo", "Ivy", "Noah"])
    if args.grownup is None:
        args.grownup = rng.choice(["mother", "father", "grandmother", "grandfather"])
    if args.cafe_name is None:
        args.cafe_name = rng.choice(["the lantern cafe", "the comet cafe", "the honeybell cafe"])
    if args.pastry is None:
        args.pastry = rng.choice(["muffin", "cake", "tart", "bun"])
    return StoryParams(
        name=args.name,
        gender=gender,
        grownup=args.grownup,
        cafe_name=args.cafe_name,
        pastry=args.pastry,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_model(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(name="Mina", gender="girl", grownup="mother", cafe_name="the lantern cafe", pastry="cake"),
    StoryParams(name="Leo", gender="boy", grownup="grandfather", cafe_name="the comet cafe", pastry="muffin"),
    StoryParams(name="Ivy", gender="girl", grownup="grandmother", cafe_name="the honeybell cafe", pastry="tart"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/0."))
        print("valid_story" if any(sym.name == "valid_story" for sym in model) else "no model")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
