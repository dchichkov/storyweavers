#!/usr/bin/env python3
"""
storyworlds/worlds/deep_mystery_to_solve_moral_value_reconciliation.py
======================================================================

A small pirate-tale story world about a mystery that must be solved,
a moral value that is tested, and a reconciliation that repairs the crew.

Seed tale premise:
---
On a deep-sea voyage, a young deckhand spots a mystery: the captain's map
is gone, and everyone starts guessing who took it. The crew must choose
between blame and honesty. After a tense search, the real hiding place is
found, the truth comes out, and the captain and deckhand make peace again.

The generated stories are built from world state:
- a pirate ship or harbor setting
- a mystery object that is missing
- a moral value under pressure, usually honesty or fairness
- a reconciliation action that resolves the conflict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    deep: bool
    afford: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    thing: str
    hiding_place: str
    clue: str
    danger: str
    verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    name: str
    pressure: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reconciliation:
    id: str
    action: str
    result: str
    promise: str
    tags: set[str] = field(default_factory=set)


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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "ship": Setting(place="the deep-blue ship", deep=True, afford={"search", "sail"}),
    "harbor": Setting(place="the harbor", deep=False, afford={"search"}),
    "cove": Setting(place="the hidden cove", deep=True, afford={"search"}),
    "island": Setting(place="the island shore", deep=True, afford={"search"}),
}

MYSTERIES = {
    "map": Mystery(
        id="map",
        thing="captain's map",
        hiding_place="inside a rope chest",
        clue="a scrap of chart cloth",
        danger="the crew might sail the wrong way",
        verb="search for the missing map",
        tags={"map", "sea"},
    ),
    "compass": Mystery(
        id="compass",
        thing="old brass compass",
        hiding_place="under the galley bench",
        clue="a tiny brass gleam",
        danger="the ship might drift off course",
        verb="search for the missing compass",
        tags={"compass", "sea"},
    ),
    "lantern": Mystery(
        id="lantern",
        thing="lantern",
        hiding_place="behind a barrel of apples",
        clue="a smell of warm oil",
        danger="the deck would stay dark at night",
        verb="search for the missing lantern",
        tags={"lantern", "light"},
    ),
}

VALUES = {
    "honesty": MoralValue(
        id="honesty",
        name="honesty",
        pressure="to speak the truth",
        kind="truth",
        tags={"honesty", "truth"},
    ),
    "fairness": MoralValue(
        id="fairness",
        name="fairness",
        pressure="to judge carefully before blaming anyone",
        kind="fair",
        tags={"fairness", "blame"},
    ),
    "kindness": MoralValue(
        id="kindness",
        name="kindness",
        pressure="to speak gently even while upset",
        kind="kind",
        tags={"kindness", "gentle"},
    ),
}

RECONCILIATIONS = {
    "apology": Reconciliation(
        id="apology",
        action="apologize and share the truth",
        result="the crew could breathe again",
        promise="they would trust one another more carefully",
        tags={"apology", "truth"},
    ),
    "shakehands": Reconciliation(
        id="shakehands",
        action="shake hands and forgive the mistake",
        result="the captain's face softened",
        promise="they would ask before accusing",
        tags={"forgive", "trust"},
    ),
    "sharetea": Reconciliation(
        id="sharetea",
        action="share tea and listen to every side",
        result="the whole deck felt calmer",
        promise="they would listen before leaping to conclusions",
        tags={"listen", "calm"},
    ),
}

HERO_NAMES = ["Mara", "Ned", "Lia", "Finn", "Ivy", "Joss", "Tara", "Ben"]
CAPTAIN_NAMES = ["Captain Brine", "Captain Salt", "Captain Mara", "Captain Reed"]
SIDEKICK_NAMES = ["Patch", "Wren", "Peg", "Ollie", "Sailor Jo"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    value: str
    reconciliation: str
    hero: str
    captain: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for v in VALUES:
                for r in RECONCILIATIONS:
                    if s == "ship" and m in {"map", "compass", "lantern"}:
                        combos.append((s, m, v, r))
                    elif s != "ship" and m in {"map", "compass", "lantern"}:
                        combos.append((s, m, v, r))
    return combos


def intro(world: World, hero: Entity, captain: Entity, helper: Entity, mystery: Mystery, value: MoralValue) -> None:
    world.say(
        f"{hero.id} was a small pirate with quick eyes and a brave grin, sailing on "
        f"{world.setting.place} with {captain.id} and {helper.id}."
    )
    world.say(
        f"{hero.id} loved the sea, but that day a mystery stirred the deck: "
        f"{mystery.thing} was gone, and everyone had to {value.pressure}."
    )


def start_conflict(world: World, hero: Entity, captain: Entity, mystery: Mystery, value: MoralValue) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    captain.memes["strain"] = captain.memes.get("strain", 0.0) + 1
    world.say(
        f"The captain frowned and said the loss was serious, because {mystery.danger}."
    )
    world.say(
        f"{hero.id} wanted to help, but the crew began to whisper, and the air on deck felt tight."
    )


def clue_search(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.meters["searching"] = hero.meters.get("searching", 0.0) + 1
    helper.meters["searching"] = helper.meters.get("searching", 0.0) + 1
    world.say(
        f"{hero.id} and {helper.id} looked low and high, until they found {mystery.clue} near {mystery.hiding_place}."
    )
    world.say(
        f"That clue pointed to the right place, so the crew stopped guessing and followed the trail."
    )


def reveal(world: World, hero: Entity, captain: Entity, mystery: Mystery, value: MoralValue) -> None:
    world.say(
        f"At last, {hero.id} found {mystery.thing} where it had been tucked away all along."
    )
    world.say(
        f"{hero.id} told the captain the truth, because {value.name} mattered more than staying silent."
    )


def reconcile(world: World, hero: Entity, captain: Entity, helper: Entity, rec: Reconciliation, value: MoralValue) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    captain.memes["relief"] = captain.memes.get("relief", 0.0) + 1
    world.say(
        f"Then {hero.id} and {captain.id} {rec.action}, and {rec.result}."
    )
    world.say(
        f"The captain nodded, the helper smiled, and {rec.promise}, all because {value.name} had won the day."
    )


def tell(setting: Setting, mystery: Mystery, value: MoralValue, rec: Reconciliation,
         hero_name: str, captain_name: str, helper_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate"))
    captain = world.add(Entity(id=captain_name, kind="character", type="captain"))
    helper = world.add(Entity(id=helper_name, kind="character", type="pirate"))

    world.facts.update(
        hero=hero,
        captain=captain,
        helper=helper,
        mystery=mystery,
        value=value,
        reconciliation=rec,
        setting=setting,
    )

    intro(world, hero, captain, helper, mystery, value)
    world.para()
    start_conflict(world, hero, captain, mystery, value)
    clue_search(world, hero, helper, mystery)
    world.para()
    reveal(world, hero, captain, mystery, value)
    reconcile(world, hero, captain, helper, rec, value)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    mystery = f["mystery"]
    value = f["value"]
    rec = f["reconciliation"]
    return [
        QAItem(
            question=f"What problem had to be solved on {world.setting.place}?",
            answer=f"The crew had to solve the mystery of the missing {mystery.thing}, which had been hidden {mystery.hiding_place}.",
        ),
        QAItem(
            question=f"What moral value mattered when the crew started guessing?",
            answer=f"{value.name.capitalize()} mattered most, because the crew needed {value.pressure}.",
        ),
        QAItem(
            question=f"How did {hero.id} help fix the trouble?",
            answer=f"{hero.id} searched for clues, found the hidden {mystery.thing}, and told the truth instead of letting the blame grow.",
        ),
        QAItem(
            question=f"How did {hero.id} and {captain.id} make peace again?",
            answer=f"They {rec.action}, and that helped everyone feel calm and ready to sail on together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why is honesty helpful when people are upset?",
            answer="Honesty helps because telling the truth clears up confusion and makes it easier to fix the problem.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people who were upset make peace again and can be friendly once more.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a pirate tale for a child about a missing {f['mystery'].thing}, a lesson about {f['value'].name}, and a happy ending.",
        f"Tell a short sea story where {f['hero'].id} solves a mystery on {world.setting.place} and then makes peace with {f['captain'].id}.",
        f"Create a gentle pirate story with clues, truth, and reconciliation on {world.setting.place}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this pirate mystery setup needs a missing thing, a moral pressure, and a reconciliation plan.)"


CURATED = [
    StoryParams(setting="ship", mystery="map", value="honesty", reconciliation="apology", hero="Mara", captain="Captain Brine", helper="Patch"),
    StoryParams(setting="cove", mystery="compass", value="fairness", reconciliation="shakehands", hero="Ned", captain="Captain Salt", helper="Wren"),
    StoryParams(setting="harbor", mystery="lantern", value="kindness", reconciliation="sharetea", hero="Ivy", captain="Captain Reed", helper="Peg"),
]


ASP_RULES = r"""
setting(S) :- place(S).
mystery(M) :- thing(M,_).
value(V) :- moral(V).
recon(R) :- action(R,_).

valid_story(S,M,V,R) :- setting(S), mystery(M), value(V), recon(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("thing", mid, m.thing))
        lines.append(asp.fact("hiding", mid, m.hiding_place))
    for vid, v in VALUES.items():
        lines.append(asp.fact("moral", vid))
    for rid, r in RECONCILIATIONS.items():
        lines.append(asp.fact("action", rid, r.action))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(s, m, v, r) for s in SETTINGS for m in MYSTERIES for v in VALUES for r in RECONCILIATIONS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate mystery story world with truth and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--reconciliation", choices=RECONCILIATIONS)
    ap.add_argument("--hero")
    ap.add_argument("--captain")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.value is None or c[2] == args.value)
              and (args.reconciliation is None or c[3] == args.reconciliation)]
    if not combos:
        raise StoryError(explain_rejection())
    s, m, v, r = rng.choice(combos)
    hero = args.hero or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    helper = args.helper or rng.choice(SIDEKICK_NAMES)
    return StoryParams(setting=s, mystery=m, value=v, reconciliation=r, hero=hero, captain=captain, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], VALUES[params.value],
                 RECONCILIATIONS[params.reconciliation], params.hero, params.captain, params.helper)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
