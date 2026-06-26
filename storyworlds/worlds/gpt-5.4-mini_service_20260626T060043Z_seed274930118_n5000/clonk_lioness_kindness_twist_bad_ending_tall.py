#!/usr/bin/env python3
"""
storyworlds/worlds/clonk_lioness_kindness_twist_bad_ending_tall.py
==================================================================

A small tall-tale story world about a lioness, a clonk, a kindness, a twist,
and a bad ending that still resolves into a clear ending image.

Premise:
- A lioness hears a clonk in the tall grass and goes to investigate.
- She chooses kindness over pride and helps a smaller creature.
- A twist reveals the clonk was not a threat but a broken cart pin.
- The bad ending feature means the prized meal is lost, so the ending is
  bittersweet rather than triumphant.

The world is intentionally compact: a few plausible variants, all grounded in
state changes over meters and memes.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"lioness", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"lion", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    wind: str
    grass: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    risk: str
    guards: set[str] = field(default_factory=set)
    at_risk: str = "none"


@dataclass
class StoryParams:
    place: str
    object: str
    twist: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _clonk(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("clonk", 0.0) >= THRESHOLD and ("clonk", e.id) not in world.fired:
            world.fired.add(("clonk", e.id))
            e.memes["alert"] = e.memes.get("alert", 0.0) + 1
            out.append(f"A clonk went through the tall grass like a small drumbeat.")
    return out


def _kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("lioness")
    target = world.entities.get("small_one")
    if not helper or not target:
        return out
    if helper.memes.get("kindness", 0.0) >= THRESHOLD and ("kindness",) not in world.fired:
        world.fired.add(("kindness",))
        target.memes["safe"] = target.memes.get("safe", 0.0) + 1
        helper.memes["pride"] = max(0.0, helper.memes.get("pride", 0.0) - 1)
        out.append("The lioness chose kindness over a grand roar, and the smaller one stopped trembling.")
    return out


def _twist(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("twist_revealed") and ("twist",) not in world.fired:
        world.fired.add(("twist",))
        out.append(world.facts["twist_line"])
    return out


def _bad_ending(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("bad_ending") and ("bad_ending",) not in world.fired:
        world.fired.add(("bad_ending",))
        hunter = world.entities["hunter"]
        hunter.memes["loss"] = hunter.memes.get("loss", 0.0) + 1
        out.append("The feast was gone by the time the clouds opened, and nobody got the prize.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_clonk, _kindness, _twist, _bad_ending):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "savanna": Setting(place="the savanna", wind="hot", grass="tall", affords={"clonk"}),
    "riverbank": Setting(place="the riverbank", wind="warm", grass="long", affords={"clonk"}),
    "kopje": Setting(place="the rocky kopje", wind="dry", grass="thin", affords={"clonk"}),
}

OBJECTS = {
    "cart_pin": Thing(
        id="cart_pin",
        label="cart pin",
        phrase="a bent iron cart pin",
        risk="lost",
        guards={"kindness"},
        at_risk="feast",
    ),
    "gourd": Thing(
        id="gourd",
        label="gourd",
        phrase="a cracked water gourd",
        risk="spilled",
        guards={"kindness"},
        at_risk="water",
    ),
    "drum": Thing(
        id="drum",
        label="drum",
        phrase="a traveler’s drum",
        risk="silenced",
        guards={"kindness"},
        at_risk="song",
    ),
}

TWISTS = {
    "pin": {
        "line": "The twist was simple: the clonk came from a broken cart pin, not a wild beast.",
        "bad_ending": True,
    },
    "wind": {
        "line": "The twist was the wind itself, tapping a loose tin lid until it clonked like a spoon.",
        "bad_ending": True,
    },
    "camel": {
        "line": "The twist was that a sleepy camel had kicked a kettle, and the clonk was only metal on stone.",
        "bad_ending": True,
    },
}

GENTLE_NAMES = ["Mara", "Tala", "Nia", "Zuri", "Asha", "Lina"]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("risk", oid, o.risk))
        lines.append(asp.fact("at_risk", oid, o.at_risk))
        for g in sorted(o.guards):
            lines.append(asp.fact("guards", oid, g))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Obj, Twist) :- affords(Place, clonk), object(Obj), twist(Twist).
valid_story(Place, Obj, Twist) :- valid(Place, Obj, Twist).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set((p, o, t) for p in SETTINGS for o in OBJECTS for t in TWISTS)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python choices ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python choices:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall tale world: a lioness, a clonk, kindness, a twist, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object_ or rng.choice(list(OBJECTS))
    twist = args.twist or rng.choice(list(TWISTS))
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.object_ and args.object_ not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.twist and args.twist not in TWISTS:
        raise StoryError("Unknown twist.")
    return StoryParams(place=place, object=obj, twist=twist, name=args.name or rng.choice(GENTLE_NAMES))


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    obj = OBJECTS[params.object]
    twist = TWISTS[params.twist]
    world = World(setting)
    lioness = world.add(Entity(id="lioness", kind="character", type="lioness", label="lioness", traits=["tall", "bright-eyed"]))
    hunter = world.add(Entity(id="hunter", kind="character", type="hunter", label="hunter"))
    small = world.add(Entity(id="small_one", kind="character", type="gazelle", label="small gazelle"))
    clonk_obj = world.add(Entity(id=obj.id, kind="thing", type="thing", label=obj.label, phrase=obj.phrase))

    lioness.memes["kindness"] = 1
    lioness.meters["clonk"] = 1
    world.facts["twist_revealed"] = True
    world.facts["twist_line"] = twist["line"]
    world.facts["bad_ending"] = twist["bad_ending"]

    world.say(f"On {setting.place}, a lioness named {params.name} heard a clonk in the tall grass.")
    world.say(f"She lifted her head as high as a sunset tree and followed the sound.")
    world.para()
    world.say(f"There she found a small gazelle near a broken {obj.label}, blinking at the dust.")
    world.say(f"The lioness could have thundered in with pride, but she chose kindness instead.")
    propagate(world, narrate=True)
    world.para()
    world.say(twist["line"])
    world.say("The lioness helped the small gazelle step clear, but the good hunting was already gone.")
    propagate(world, narrate=True)
    world.para()
    world.say("So the lioness stood under the wide sky with empty paws and a calmer heart.")
    world.say("That was a bad ending for the feast, yet a fine ending for kindness.")

    world.facts.update(params=params, setting=setting, object=obj, twist=twist, lioness=lioness, hunter=hunter, small=small)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f"Write a tall tale about a lioness, a clonk, kindness, and a twist on {setting.place}.",
            f"Tell a child-friendly story where kindness changes what happens after a clonk in the grass.",
            f"Make a short story about {params.name} the lioness and end with a clear image after the bad ending.",
        ],
        story_qa=[
            QAItem(
                question="Who heard the clonk in the tall grass?",
                answer=f"The lioness named {params.name} heard it and raised her head to follow the sound.",
            ),
            QAItem(
                question="What was the twist in the story?",
                answer=twist["line"],
            ),
            QAItem(
                question="Was the ending happy or bad?",
                answer="It was a bad ending for the feast, because the prize was gone, but kindness still left the lioness with a calm heart.",
            ),
        ],
        world_qa=[
            QAItem(
                question="What does a clonk sound like?",
                answer="A clonk is a hard, hollow metal sound, like one thing bumping into another in a loud little knock.",
            ),
            QAItem(
                question="What is kindness?",
                answer="Kindness means helping, caring, or being gentle with someone who needs it.",
            ),
        ],
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="savanna", object="cart_pin", twist="pin", name="Mara"),
    StoryParams(place="riverbank", object="gourd", twist="wind", name="Tala"),
    StoryParams(place="kopje", object="drum", twist="camel", name="Nia"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_stories()
        print(f"{len(combos)} compatible stories:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
