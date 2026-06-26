#!/usr/bin/env python3
"""
A small comedy-leaning cautionary farmyard storyworld about a child, a lunch
snack, and a dangerous presumption about flame.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict = {}
        self.bad_ending: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.bad_ending = self.bad_ending
        return c


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    snack: str = "bologna"
    place: str = "farmyard"
    seed: Optional[int] = None


CHAR_NAMES = ["Milo", "Tess", "Ivy", "Nora", "Owen", "Piper"]
PARENTS = ["mother", "father", "grandparent"]
SNACKS = {
    "bologna": {
        "label": "bologna sandwich",
        "phrase": "a thick bologna sandwich",
        "mess": "greasy",
        "tags": {"bologna", "lunch"},
    }
}
SETTINGS = {"farmyard": {"affords": {"picnic", "toast"}}}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy-leaning cautionary farmyard storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--name", choices=CHAR_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, snack) for place in SETTINGS for snack in SNACKS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("That place does not fit this small world.")
    if args.snack and args.snack not in SNACKS:
        raise StoryError("That snack does not fit this small world.")
    place = args.place or "farmyard"
    snack = args.snack or "bologna"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(CHAR_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent, snack=snack, place=place)


def predict_flame(world: World, snack: Entity) -> bool:
    return snack.memes.get("near_flame", 0.0) >= THRESHOLD


def tell(params: StoryParams) -> World:
    world = World(params.place)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    snack = world.add(Entity(
        id="snack",
        type="food",
        label="bologna",
        phrase=SNACKS["bologna"]["phrase"],
        owner=child.id,
        caretaker=parent.id,
    ))
    flame = world.add(Entity(id="flame", type="flame", label="flame"))

    world.say(f"{child.label} was a small {params.gender} who loved silly lunch adventures in the {params.place}.")
    world.say(f"{child.label} proudly carried {snack.phrase}, and {params.parent} tried not to laugh at how serious it looked.")
    world.say(f"Near the old barn, somebody had left a tiny flame in a metal lantern.")

    child.memes["curiosity"] = 1.0
    child.memes["presume"] = 1.0
    child.meters["close_to_flame"] = 1.0
    snack.meters["greasy"] = 1.0

    if child.memes["presume"] >= THRESHOLD:
        world.say(f"{child.label} presumed the flame was too small to matter, which was a bold and slightly wobbly idea.")
        snack.memes["near_flame"] = 1.0

    if predict_flame(world, snack):
        world.say(f"{child.label} waved the bologna near the flame to 'warm it up', and the sandwich got singed.")
        snack.meters["burned"] = 1.0
        flame.meters["used"] = 1.0
        parent.memes["alarm"] = 1.0
        world.say(f"The {params.parent} shouted, dropped a bucket of water, and made a comic sploosh that splattered both boots.")
        world.say(f"The lunch was ruined, the barn smelled like toasted lunch meat, and {child.label} ended up hungry and embarrassed.")
        world.bad_ending = True
    else:
        world.say(f"Luckily, nobody did anything silly with the flame, and the lunch stayed ordinary and safe.")

    world.facts.update(child=child, parent=parent, snack=snack, flame=flame)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short comedy about a child in a farmyard who presumes a tiny flame is harmless.',
        'Tell a cautionary story that includes bologna, flame, and a silly mistake near a barn.',
        'Write a farmyard story where lunch goes wrong after someone presumes too much about fire.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, snack = f["child"], f["parent"], f["snack"]
    return [
        QAItem(
            question=f"What did {child.label} think about the flame?",
            answer=f"{child.label} presumed the flame was too small to matter, which was a silly guess.",
        ),
        QAItem(
            question=f"What snack was involved in the mistake?",
            answer=f"It was a bologna sandwich, and it ended up singed after going too close to the flame.",
        ),
        QAItem(
            question=f"How did the story end for {child.label}?",
            answer=f"It ended badly and cautionary: the lunch was ruined, and {child.label} was left hungry and embarrassed.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bologna?",
            answer="Bologna is a sliced lunch meat often put into sandwiches.",
        ),
        QAItem(
            question="Why should children be careful around flame?",
            answer="A flame can burn things quickly, so even a small one can cause trouble.",
        ),
    ]


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "farmyard"),
        asp.fact("snack", "bologna"),
        asp.fact("affords", "farmyard", "picnic"),
        asp.fact("dangerous", "flame"),
        asp.fact("presume_risk", "bologna", "flame"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
presume_bad(S,F) :- presume_risk(S,F), dangerous(F).
valid_story(P,S) :- place(P), snack(S), affords(P,picnic), presume_bad(S,flame).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("farmyard", "bologna")}
    cl = set(asp_valid_combos())
    if py == cl:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== Story Q&A =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    lines.append(f"bad_ending={world.bad_ending}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} ASP-compatible combos:")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        for i, _ in enumerate(valid_combos()):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

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
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
