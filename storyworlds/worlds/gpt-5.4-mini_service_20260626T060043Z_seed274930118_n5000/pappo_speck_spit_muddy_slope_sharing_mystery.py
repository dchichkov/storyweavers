#!/usr/bin/env python3
"""
A standalone story world for a small Mystery-style sharing tale on a muddy slope.

Premise:
- Pappo and Speck are on a muddy slope.
- A shiny little thing called a spit-shaped pebble is missing.
- The friends must share clues, follow the mud, and solve the mystery together.

The world model tracks:
- physical meters like mud, wetness, and carried objects
- emotional memes like worry, curiosity, trust, and relief
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
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str = "the muddy slope"
    seed: Optional[int] = None


class World:
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        import copy

        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _drift_mud(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("mud", 0.0) >= THRESHOLD and ent.id not in world.fired:
            world.fired.add(ent.id)
            out.append(f"{ent.label or ent.id} left a dark trail in the mud.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in _drift_mud(world):
            produced.append(sent)
            changed = True
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    type: str
    plural: bool = False


def mystery_note() -> str:
    return "The muddy slope kept every footprint for a moment, like it wanted to help."


SETTINGS = {
    "muddy_slope": Setting(place="the muddy slope", affords={"sharing"}),
}

# The "spit" seed word is used as the name of a tiny smooth pebble-like object.
OBJECTS = {
    "spit": ObjectCfg(label="spit pebble", phrase="a tiny spit pebble", type="pebble"),
    "speck_note": ObjectCfg(label="speck's note", phrase="a little note with a clue", type="note"),
}

NAMES = ["Pappo", "Speck", "Mimi", "Rolo", "Tavi"]
TRAITS = ["careful", "curious", "gentle", "brave", "quiet"]


def asp_facts() -> str:
    import asp

    lines = [
        asp.fact("setting", "muddy_slope"),
        asp.fact("affords", "muddy_slope", "sharing"),
        asp.fact("character", "pappo"),
        asp.fact("character", "speck"),
        asp.fact("object", "spit"),
        asp.fact("places", "pappo", "muddy_slope"),
        asp.fact("places", "speck", "muddy_slope"),
        asp.fact("shares", "pappo", "speck"),
        asp.fact("shares", "speck", "pappo"),
        asp.fact("clue", "mud"),
        asp.fact("clue", "footprint"),
        asp.fact("clue", "pebble"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
shared(X,Y) :- shares(X,Y).
mystery_ready :- character(pappo), character(speck), object(spit), setting(muddy_slope).
#show shared/2.
#show mystery_ready/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show shared/2."))
    shared_atoms = set(asp.atoms(model, "shared"))
    py = {("pappo", "speck"), ("speck", "pappo")}
    if shared_atoms == py:
        print("OK: ASP sharing parity matches Python.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(shared_atoms))
    print("PY :", sorted(py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a mystery on a muddy slope with sharing.")
    ap.add_argument("--place", choices=["muddy_slope"], default="muddy_slope")
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
    if args.place != "muddy_slope":
        raise StoryError("This world only supports the muddy slope setting.")
    return StoryParams(place="the muddy slope", seed=args.seed)


def _story_qa(world: World) -> list[QAItem]:
    pappo = world.get("Pappo")
    speck = world.get("Speck")
    spit = world.get("spit")
    return [
        QAItem(
            question="Who were the friends in the muddy slope mystery?",
            answer="The friends were Pappo and Speck, and they stayed together on the muddy slope.",
        ),
        QAItem(
            question="What did they share while solving the mystery?",
            answer="They shared clues, especially the muddy footprints and the tiny spit pebble.",
        ),
        QAItem(
            question="Why was the slope important?",
            answer="The muddy slope held the prints and little marks that helped Pappo and Speck follow the mystery.",
        ),
        QAItem(
            question="What was the spit pebble?",
            answer=f"The spit pebble was {spit.phrase}, a small thing that could be passed between the friends as a clue.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, hold, or enjoy something too.",
        ),
        QAItem(
            question="Why is mud useful in a mystery?",
            answer="Mud can keep footprints and marks, which can become clues in a mystery.",
        ),
        QAItem(
            question="Why do friends work together in a mystery?",
            answer="Friends work together because one person may notice one clue and the other person may notice another.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = World(params.place)
    pappo = world.add(Entity(id="Pappo", kind="character", type="boy", label="Pappo"))
    speck = world.add(Entity(id="Speck", kind="character", type="girl", label="Speck"))
    spit = world.add(Entity(id="spit", kind="object", type="pebble", label="spit pebble", phrase="a tiny spit pebble"))
    spit.owner = "Pappo"

    pappo.memes["curiosity"] = 1
    speck.memes["curiosity"] = 1
    pappo.memes["worry"] = 1
    speck.memes["worry"] = 1

    world.say(f"Pappo and Speck came to {world.place} with a small mystery between them.")
    world.say(f"A tiny spit pebble was missing, and both friends wanted to solve the puzzle.")
    world.para()
    world.say(mystery_note())
    world.say("Pappo spotted one print. Speck spotted another.")
    world.say("Instead of arguing, they shared what they saw.")
    world.say("Pappo held the spit pebble up in one paw, and Speck compared it with the marks in the mud.")
    world.para()
    pappo.meters["mud"] = 1
    speck.meters["mud"] = 1
    spit.carried_by = "Speck"
    pappo.memes["trust"] = 1
    speck.memes["trust"] = 1
    pappo.memes["relief"] = 1
    speck.memes["relief"] = 1
    propagate(world, narrate=True)
    world.say("At last, they found the answer: the spit pebble had rolled down the slope and stopped in a soft patch of mud.")
    world.say("Pappo and Speck laughed, and they shared the little prize together before heading home.")
    world.facts.update(pappo=pappo, speck=speck, spit=spit, setting=params.place)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            'Write a short mystery story for young children set on a muddy slope where Pappo and Speck share clues.',
            'Tell a gentle story about Pappo, Speck, and a tiny spit pebble that is solved by sharing.',
        ],
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.carried_by:
            bits.append(f"carried_by={ent.carried_by}")
        lines.append(f"{ent.id}: {' '.join(bits) if bits else '(quiet)'}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_ready/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show shared/2."))
        print("ASP shared pairs:", sorted(set(asp.atoms(model, "shared"))))
        return

    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []

    if args.all:
        samples.append(generate(StoryParams(place="the muddy slope", seed=args.seed)))
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(rng.randrange(2**31)))
            p.seed = args.seed
            samples.append(generate(p))

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
