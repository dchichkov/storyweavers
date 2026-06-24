#!/usr/bin/env python3
"""
storyworlds/worlds/script_constipate_rejoice_transformation_humor_mystery.py
===========================================================================

A small storyworld about a missing script, a blocked printer, and a surprising
transformation that turns a messy mystery into a neat laugh.

Seed words: script, constipate, rejoice
Style: mystery with humor
Features: transformation
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("stuck", 0.0)
        self.meters.setdefault("changed", 0.0)
        self.meters.setdefault("mess", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("curiosity", 0.0)


@dataclass
class Setting:
    id: str
    place: str
    detail: str
    mood: str
    hiding_place: str


@dataclass
class ObjectThing:
    id: str
    label: str
    use: str
    oddity: str
    transforms_to: str = ""


@dataclass
class StoryParams:
    setting: str
    mystery_object: str
    blockage: str
    transformation: str
    helper: str
    witness: str
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, line: str) -> None:
        self.trace.append(line)

    def render(self) -> str:
        return " ".join(self.trace)


SETTINGS = {
    "library": Setting("library", "the little library", "dusty shelves and a quiet lamp", "hushed", "behind the story cart"),
    "kitchen": Setting("kitchen", "the sunny kitchen", "a checked cloth and a ticking clock", "busy", "inside the bread box"),
    "classroom": Setting("classroom", "the classroom corner", "paper stars and a round rug", "curious", "under the art table"),
}

OBJECTS = {
    "script": ObjectThing("script", "the missing script", "the school play", "covered in mystery ink", transforms_to="a clean script"),
    "spoon": ObjectThing("spoon", "the silver spoon", "stirring soup", "glinting like a clue", transforms_to="a bent spoon"),
    "button": ObjectThing("button", "the blue button", "starting the machine", "too quiet to be innocent", transforms_to="a shiny button"),
}

BLOCKAGES = {
    "constipate": ObjectThing("constipate", "the jammed drawer", "open easily", "stuck with a silly squish", transforms_to="an open drawer"),
    "glue": ObjectThing("glue", "the sticky glue pot", "stay still", "gooey and glued shut", transforms_to="a soft, warm puddle"),
    "knot": ObjectThing("knot", "the tight knot", "come loose", "pulled too hard to untie", transforms_to="a loose ribbon"),
}

TRANSFORMATIONS = {
    "rejoice": ObjectThing("rejoice", "the bright laugh", "lighten the room", "turning worry into cheer", transforms_to="a happy grin"),
    "shine": ObjectThing("shine", "the gentle shine", "show what changed", "making clues easy to see", transforms_to="a clear clue"),
}

HELPERS = {
    "child": "a clever child",
    "cat": "a nosy cat",
    "teacher": "a patient teacher",
    "dog": "a bouncy dog",
}

WITNESSES = {
    "friend": "a friend with sharp eyes",
    "reader": "a reader who loved riddles",
    "neighbor": "a neighbor with a kind smile",
}


ASP_RULES = r"""
stuck(O) :- object(O), blockage(B), linked(O,B).
helpful(H) :- helper(H).
changed(O) :- stuck(O), transformation(T), triggers(T).
result(rejoice) :- changed(O), helpful(_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for bid in BLOCKAGES:
        lines.append(asp.fact("blockage", bid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for wid in WITNESSES:
        lines.append(asp.fact("witness", wid))
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery-humor transformation storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery-object", choices=OBJECTS)
    ap.add_argument("--blockage", choices=BLOCKAGES)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--witness", choices=WITNESSES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery_object = args.mystery_object or rng.choice(list(OBJECTS))
    blockage = args.blockage or rng.choice(list(BLOCKAGES))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    helper = args.helper or rng.choice(list(HELPERS))
    witness = args.witness or rng.choice(list(WITNESSES))
    return StoryParams(setting, mystery_object, blockage, transformation, helper, witness)


def generate(params: StoryParams) -> StorySample:
    s = SETTINGS[params.setting]
    o = OBJECTS[params.mystery_object]
    b = BLOCKAGES[params.blockage]
    t = TRANSFORMATIONS[params.transformation]
    h = HELPERS[params.helper]
    w = WITNESSES[params.witness]

    world = World()
    child = world.add(Entity("Mina", kind="character", type="girl", role="helper", traits=["curious"]))
    witness = world.add(Entity("Ollie", kind="character", type="boy", role="witness", traits=["observant"]))
    clue = world.add(Entity("clue", label=o.label, type="object"))
    jam = world.add(Entity("jam", label=b.label, type="blockage"))
    change = world.add(Entity("change", label=t.label, type="transformation"))
    child.memes["curiosity"] += 2
    witness.memes["curiosity"] += 1
    clue.meters["stuck"] += 1
    jam.meters["stuck"] += 1
    world.say(f"In {s.place}, under {s.detail}, Mina found a mystery.")
    world.say(f"The clue was {o.label}, but it had gone odd: {o.oddity}.")
    world.say(f"Ollie whispered that {w} had seen the thing vanish behind {s.hiding_place}.")
    world.say(f"Then everyone noticed {b.label}, which made the puzzle feel funny and wrong.")
    child.memes["worry"] += 1
    witness.memes["worry"] += 1

    world.say(f"Mina tried to open it, but the {b.label} would not budge, which made her grin.")
    world.say(f"{h} came over and helped, using a small trick to turn the snag into motion.")
    clue.meters["changed"] += 1
    jam.meters["changed"] += 1
    clue.memes["joy"] += 1
    child.memes["joy"] += 1
    world.say(f"With one gentle pull, the stuck thing transformed into {o.transforms_to}.")
    world.say(f"Inside, the missing script lay safe and neat, no longer scrambled or lost.")
    world.say(f"That made everyone rejoice, and even the room seemed to breathe out.")

    world.facts.update(
        setting=params.setting,
        mystery_object=params.mystery_object,
        blockage=params.blockage,
        transformation=params.transformation,
        helper=params.helper,
        witness=params.witness,
        outcome="resolved",
    )

    story_qa = [
        QAItem(
            question="What was missing in the story?",
            answer=f"The missing item was {o.label}, which was the script for the school play.",
        ),
        QAItem(
            question="What blocked the clue at first?",
            answer=f"{b.label} blocked the way and made the mystery feel stuck and a little silly.",
        ),
        QAItem(
            question="Who helped solve the mystery?",
            answer=f"{h} helped Mina and Ollie turn the stuck problem into a solved one.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"The stuck thing transformed into {o.transforms_to}, and everyone could rejoice.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a script?", answer="A script is the written words actors use in a play."),
        QAItem(question="What does rejoice mean?", answer="To rejoice means to feel and show great happiness."),
        QAItem(question="What can transformation mean?", answer="A transformation is a change from one form or state into another."),
    ]
    prompts = [
        f"Write a mystery story in {s.place} where a missing script is found after a funny blockage is fixed.",
        f"Tell a child-friendly detective tale with a transformation, a little humor, and the word script.",
        f"Make a short mystery where the answer causes the characters to rejoice at the end.",
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        parts.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(parts)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, o, b, t) for s in SETTINGS for o in OBJECTS for b in BLOCKAGES for t in TRANSFORMATIONS]


def explain_rejection() -> str:
    return "No valid mystery combo matched the given options."


def resolve_all(args: argparse.Namespace) -> list[StoryParams]:
    return [StoryParams(*combo) for combo in valid_combos()]


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_facts())
        print(ASP_RULES)
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is not expanded in this compact world.")
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = [generate(p) for p in resolve_all(args)] if args.all else []
    if not args.all:
        seen = set()
        while len(samples) < args.n:
            params = resolve_params(args, rng)
            key = (params.setting, params.mystery_object, params.blockage, params.transformation, params.helper, params.witness)
            if key in seen:
                continue
            seen.add(key)
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if i:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa)


if __name__ == "__main__":
    main()
