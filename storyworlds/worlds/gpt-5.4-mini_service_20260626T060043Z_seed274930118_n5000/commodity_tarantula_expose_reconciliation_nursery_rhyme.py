#!/usr/bin/env python3
"""
storyworlds/worlds/commodity_tarantula_expose_reconciliation_nursery_rhyme.py
==============================================================================

A small story world in a nursery-rhyme style about a child, a tarantula, a hidden
commodity, an exposure, and a reconciliation.

Premise:
- A child keeps a tiny tarantula as a careful helper in a nursery nook.
- The tarantula notices a covered commodity and pulls away the cloth.
- The expose reveals a missing treasure and briefly causes worry.
- The child and tarantula make peace and end in a gentle reconciliation.

The prose is kept simple, repetitive, and child-facing, like a short rhyme.
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the nursery"
    indoor: bool = True


@dataclass
class Commodity:
    id: str
    label: str
    phrase: str
    region: str
    value_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str = "tarantula"
    phrase: str = "a little tarantula"
    careful: bool = True
    tags: set[str] = field(default_factory=lambda: {"tarantula"})


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True),
}

COMMODITIES = {
    "buttons": Commodity(
        id="buttons",
        label="buttons",
        phrase="a little tin of bright buttons",
        region="shelf",
        value_word="shiny",
        tags={"buttons", "small", "trade"},
    ),
    "spools": Commodity(
        id="spools",
        label="spools",
        phrase="a basket of thread spools",
        region="table",
        value_word="neat",
        tags={"thread", "trade"},
    ),
    "candies": Commodity(
        id="candies",
        label="candies",
        phrase="a wrapped dish of candies",
        region="tray",
        value_word="sweet",
        tags={"sweet", "trade"},
    ),
}

CREATURE = Creature(id="tarry")


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    commodity: str
    child_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------
CHILD_NAMES = ["Mina", "Nell", "Pip", "Luna", "Ivy", "Rowan"]
TRAITS = ["gentle", "curious", "bright", "busy"]


def _meter(x: float) -> float:
    return 1.0 if x >= 1.0 else x


def _make_entity(id: str, type_: str, label: str = "", phrase: str = "", owner: str | None = None,
                 caretaker: str | None = None, plural: bool = False) -> Entity:
    return Entity(id=id, kind="character" if type_ in {"girl", "boy"} else "thing",
                  type=type_, label=label, phrase=phrase, owner=owner,
                  caretaker=caretaker, plural=plural)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
def tell(setting: Setting, commodity: Commodity, child_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="girl", label=child_name))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="mom"))
    tarry = world.add(Entity(id=CREATURE.id, kind="character", type="tarantula", label="tarry"))
    good = world.add(Entity(id=commodity.id, type=commodity.id, label=commodity.label,
                            phrase=commodity.phrase, owner=child.id, caretaker=parent.id))
    # Story state
    child.memes["love"] = 1.0
    child.memes["worry"] = 0.0
    tarry.memes["care"] = 1.0
    good.meters["covered"] = 1.0

    # Act 1: setup
    world.say(f"{child_name} was a bright little child in the nursery nook.")
    world.say(f"Near the cot sat {tarry.phrase}, as neat as a dot, with tiny feet and a careful trot.")
    world.say(f"{child_name} loved the {commodity.value_word} {commodity.label} in its little place, for it made the room feel warm and sweet.")

    # Act 2: reveal / expose
    world.para()
    world.say(f"One soft day, the cover slipped. Then tarry gave the cloth a nip and a flip.")
    good.meters["covered"] = 0.0
    good.meters["exposed"] = 1.0
    world.facts["exposed"] = commodity.id
    child.memes["surprise"] = 1.0
    world.say(f"Out came {commodity.phrase}, shining in the light; tarry had exposed it, quick and bright.")

    # Tension
    if commodity.id == "buttons":
        world.say("But the tin had tipped, and one small button rolled with a little click-clack sound.")
        good.meters["scattered"] = 1.0
    elif commodity.id == "spools":
        world.say("But one spool unrolled a thread, and a thin little line went looping over the bed.")
        good.meters["scattered"] = 1.0
    else:
        world.say("But the candies woke a sweet smell, and the shiny dish bumped the shelf as well.")
        good.meters["scattered"] = 1.0

    child.memes["worry"] = 1.0
    world.say(f"{child_name} frowned and said, 'Oh dear, oh no, my dear little show!'")

    # Act 3: reconciliation
    world.para()
    world.say("Tarry paused, then climbed back slow, as if to say, 'I did not mean to go.'")
    child.memes["worry"] = 0.0
    child.memes["love"] = 2.0
    child.memes["reconcile"] = 1.0
    tarry.memes["reconcile"] = 1.0
    world.say(f"{child_name} knelt down near the floor and said, 'I was cross, but I am not cross any more.'")
    world.say(f"Together they set the {commodity.label} right, and the nursery glowed all warm and light.")
    world.say(f"Then {child_name} patted tarry's shell and smiled so well; the two were friends again, and that was the tale.")

    world.facts.update(
        child=child,
        parent=parent,
        tarantula=tarry,
        commodity=good,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Prompts and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    commodity = f["commodity"]
    return [
        f'Write a short nursery-rhyme story about {child.id}, a tarantula, and a hidden {commodity.label}.',
        f"Tell a gentle rhyming story where tarry exposes {commodity.phrase} and then everyone makes peace.",
        f"Write a simple story in a nursery style using the words commodity, tarantula, expose, and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    commodity = f["commodity"]
    return [
        QAItem(
            question=f"Who found the hidden {commodity.label} in the nursery?",
            answer=f"The little tarantula, tarry, found it and exposed {commodity.phrase}.",
        ),
        QAItem(
            question=f"What happened after tarry exposed the {commodity.label}?",
            answer=f"The {commodity.label} got a little scattered, and {child.id} felt worried for a moment.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{child.id} and tarry made up, put the {commodity.label} right again, and ended in reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tarantula?",
            answer="A tarantula is a big, hairy spider with eight legs.",
        ),
        QAItem(
            question="What does expose mean?",
            answer="To expose something is to uncover it so it can be seen.",
        ),
        QAItem(
            question="What is a commodity?",
            answer="A commodity is a useful thing that people can keep, trade, or use, like buttons, thread, or candy.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making peace again after a worry or disagreement.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(nursery).
indoor(nursery).

commodity(buttons).
commodity(spools).
commodity(candies).

child(girl).
tarantula(tarry).

expose(commodity).
reconcile(reconciliation).

valid_story(S, C) :- setting(S), commodity(C), child(girl).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "nursery"), asp.fact("indoor", "nursery")]
    for cid in COMMODITIES:
        lines.append(asp.fact("commodity", cid))
    lines.append(asp.fact("child", "girl"))
    lines.append(asp.fact("tarantula", "tarry"))
    lines.append(asp.fact("reconcile", "reconciliation"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    return [("nursery", cid) for cid in COMMODITIES]


def explain_rejection(setting: str, commodity: str) -> str:
    return f"(No story: the setting {setting!r} or commodity {commodity!r} does not fit this small nursery rhyme world.)"


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme story world about a tarantula, a commodity, expose, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--commodity", choices=COMMODITIES)
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
    combos = valid_combos()
    if args.setting and args.commodity and (args.setting, args.commodity) not in combos:
        raise StoryError(explain_rejection(args.setting, args.commodity))
    choices = [c for c in combos
               if (args.setting is None or c[0] == args.setting)
               and (args.commodity is None or c[1] == args.commodity)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    setting, commodity = rng.choice(choices)
    name = args.name or rng.choice(CHILD_NAMES)
    return StoryParams(setting=setting, commodity=commodity, child_name=name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], COMMODITIES[params.commodity], params.child_name)
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {' '.join(bits)}")
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
        print(f"{len(combos)} valid story combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for setting, commodity in valid_combos():
            params = StoryParams(setting=setting, commodity=commodity, child_name="Mina")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
