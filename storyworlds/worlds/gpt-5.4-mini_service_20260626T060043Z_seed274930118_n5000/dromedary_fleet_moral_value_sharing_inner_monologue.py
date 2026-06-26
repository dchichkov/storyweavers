#!/usr/bin/env python3
"""
storyworlds/worlds/dromedary_fleet_moral_value_sharing_inner_monologue.py
=========================================================================

A mythic storyworld about a dromedary fleet, a hard road, sharing, and the
quiet turning of an inner monologue into a moral choice.

Seed tale, used to shape the world:
---
A dromedary fleet crossed a vast desert under a pale moon. Their leader carried
a polished cup said to hold a little moral value: the kind that grows when it is
shared. One thirsty night, the youngest dromedary wanted the cup all to itself.
In its inner monologue, it imagined keeping the cup and drinking alone. But the
fleet was drying out, and the moon looked on. The youngster finally chose to
share the cup, and the fleet kept going together.
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
# World model
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"dromedary", "camel", "leader"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    color: str
    sky: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str = "hooves"
    value: int = 1


@dataclass
class StoryParams:
    setting: str
    relic: str
    leader_name: str
    young_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_dune": Setting(
        place="the moonlit dune sea",
        color="silver",
        sky="pale moon",
        affords={"share_water", "share_story"},
    ),
    "caravan_gate": Setting(
        place="the old caravan gate",
        color="red",
        sky="setting sun",
        affords={"share_water", "share_story"},
    ),
    "oasis_edge": Setting(
        place="the edge of the oasis",
        color="green",
        sky="warm stars",
        affords={"share_water"},
    ),
}

RELICS = {
    "cup": Relic(
        id="cup",
        label="silver cup",
        phrase="a polished silver cup that held a little moral value",
        region="mouth",
        value=2,
    ),
    "gourd": Relic(
        id="gourd",
        label="water gourd",
        phrase="a cool water gourd with a braided strap",
        region="mouth",
        value=2,
    ),
    "lamp": Relic(
        id="lamp",
        label="lantern lamp",
        phrase="a small lantern lamp said to warm the heart",
        region="hands",
        value=1,
    ),
}

DROMEDARY_NAMES = [
    "Sahir", "Nura", "Tala", "Iman", "Rami", "Zoya", "Mika", "Asha"
]

TRAITS = ["young", "quiet", "stubborn", "bright-eyed", "thoughtful", "dusty"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def setting_for(key: str) -> Setting:
    return SETTINGS[key]


def _introduce(world: World, leader: Entity, young: Entity, fleet: Entity, relic: Entity) -> None:
    world.say(
        f"Under {world.setting.sky}, a dromedary fleet crossed {world.setting.place}."
    )
    world.say(
        f"{leader.id} led the fleet with a steady step, and {young.id} walked near the middle, "
        f"where the wind was kindest."
    )
    world.say(
        f"The leader kept {relic.phrase}, and the whole fleet knew it was more than a cup: "
        f"it was a sign that strength could be shared."
    )


def _wish(young: Entity, relic: Entity) -> str:
    young.memes["desire"] = young.memes.get("desire", 0) + 1
    return (
        f"{young.id} wanted to keep the {relic.label} close. "
        f"In its inner monologue, it whispered, "
        f"\"If I drink first, maybe no one will notice how thirsty I am.\""
    )


def _predict_cost(world: World, young: Entity, relic: Entity) -> dict:
    sim = world.copy()
    sim.get(young.id).meters["thirst"] = sim.get(young.id).meters.get("thirst", 0) + 1
    sim.get(relic.id).carried_by = young.id
    fleet = sim.get("fleet")
    fleet.meters["hope"] = fleet.meters.get("hope", 0)
    return {
        "thirst_rises": sim.get(young.id).meters.get("thirst", 0) >= 1,
        "fleet_gain": fleet.meters.get("hope", 0),
    }


def _warn(world: World, leader: Entity, young: Entity, relic: Entity) -> None:
    pred = _predict_cost(world, young, relic)
    if pred["thirst_rises"]:
        world.say(
            f"{leader.id} watched the little hush in {young.id}'s face and said, "
            f"\"A cup kept alone dries out like a forgotten well.\""
        )


def _share(world: World, leader: Entity, young: Entity, relic: Entity) -> None:
    young.memes["greed"] = max(0.0, young.memes.get("greed", 0.0) - 1.0)
    young.memes["kindness"] = young.memes.get("kindness", 0) + 1
    fleet = world.get("fleet")
    fleet.memes["trust"] = fleet.memes.get("trust", 0) + 1
    relic.value += 1
    world.say(
        f"{young.id} held the {relic.label} out to the others and let them drink in turn."
    )
    world.say(
        f"The fleet's breaths slowed. The more the water moved from mouth to mouth, "
        f"the brighter the little moral value in the cup seemed to grow."
    )
    world.say(
        f"{young.id}'s inner monologue changed at last: "
        f"\"I thought keeping was safety, but sharing is the road that keeps us together.\""
    )


def tell(params: StoryParams) -> World:
    setting = setting_for(params.setting)
    world = World(setting)

    fleet = world.add(Entity(id="fleet", kind="character", type="fleet", label="fleet"))
    leader = world.add(Entity(id=params.leader_name, kind="character", type="dromedary", label="leader"))
    young = world.add(Entity(id=params.young_name, kind="character", type="dromedary", label="young dromedary"))
    relic = world.add(Entity(
        id=params.relic,
        kind="thing",
        type="relic",
        label=RELICS[params.relic].label,
        phrase=RELICS[params.relic].phrase,
        owner=leader.id,
    ))

    fleet.meters["hope"] = 1
    young.meters["thirst"] = 1
    young.memes["greed"] = 1
    world.facts["setting"] = setting
    world.facts["leader"] = leader
    world.facts["young"] = young
    world.facts["fleet"] = fleet
    world.facts["relic"] = relic

    _introduce(world, leader, young, fleet, relic)

    world.para()
    world.say(
        f"By the third stretch of dunes, the sun had left a hot taste in every mouth."
    )
    world.say(_wish(young, relic))
    _warn(world, leader, young, relic)

    world.para()
    world.say(
        f"{young.id} looked at the others and felt its own longing like a pebble under the tongue."
    )
    world.say(
        f"Then it remembered the fleet moving as one shadow under the moon, and the thought of that made the choice clear."
    )
    _share(world, leader, young, relic)

    world.para()
    world.say(
        f"When dawn came, the fleet went on across {setting.place}, and no one was left behind."
    )
    world.say(
        f"The {relic.label} stayed bright in the leader's pack, but its truest shine was the way the fleet had learned to trust one another."
    )
    world.facts["shared"] = True
    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    f = world.facts
    young = f["young"]
    relic = f["relic"]
    return [
        'Write a mythic short story about a dromedary fleet, a precious cup, and the power of sharing.',
        f"Tell a desert myth where {young.id} wants to keep the {relic.label} but learns to share it with the fleet.",
        "Write a gentle legend in which an inner monologue leads a thirsty traveler from selfishness to generosity.",
    ]


def story_qa(world: World) -> list[QAItem]:
    young = world.facts["young"]
    leader = world.facts["leader"]
    relic = world.facts["relic"]
    fleet = world.facts["fleet"]
    setting = world.facts["setting"]
    return [
        QAItem(
            question=f"Who wanted to keep the {relic.label} at first?",
            answer=f"{young.id} wanted to keep the {relic.label} close at first.",
        ),
        QAItem(
            question=f"What did {young.id}'s inner monologue say about the {relic.label}?",
            answer="It whispered that keeping the cup might hide how thirsty it was.",
        ),
        QAItem(
            question=f"What did the leader warn about when the {young.id} wanted to drink alone?",
            answer="The leader warned that a cup kept alone dries out like a forgotten well.",
        ),
        QAItem(
            question=f"What changed the story for the fleet in {setting.place}?",
            answer="The young dromedary chose to share the water, and that choice made trust grow in the fleet.",
        ),
        QAItem(
            question=f"How did the fleet feel at the end?",
            answer="The fleet felt steadier and safer, because everyone had shared and no one was left behind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dromedary?",
            answer="A dromedary is a one-humped camel that is strong at walking long distances in dry places.",
        ),
        QAItem(
            question="What is a fleet?",
            answer="A fleet is a group moving together, often many ships, animals, or travelers traveling as one.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or have part of something you have, so everyone can benefit.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet voice a character hears in its own mind when it thinks to itself.",
        ),
        QAItem(
            question="What kind of lesson is moral value?",
            answer="Moral value is the goodness or worth of a choice, like kindness, fairness, or generosity.",
        ),
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
    lines.append("== (3) World knowledge ==")
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: dromedary, fleet, sharing, inner monologue.")
    ap.add_argument("--setting", choices=sorted(SETTINGS), default=None)
    ap.add_argument("--relic", choices=sorted(RELICS), default=None)
    ap.add_argument("--leader-name", dest="leader_name")
    ap.add_argument("--young-name", dest="young_name")
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
    setting = args.setting or rng.choice(sorted(SETTINGS))
    relic = args.relic or rng.choice(sorted(RELICS))
    leader_name = args.leader_name or rng.choice(DROMEDARY_NAMES)
    young_choices = [n for n in DROMEDARY_NAMES if n != leader_name]
    young_name = args.young_name or rng.choice(young_choices)
    if leader_name == young_name:
        raise StoryError("leader and young dromedary must be different names")
    return StoryParams(setting=setting, relic=relic, leader_name=leader_name, young_name=young_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_name(moon_dune).
setting_name(caravan_gate).
setting_name(oasis_edge).

relic_name(cup).
relic_name(gourd).
relic_name(lamp).

shared_moral_value(S) :- setting_name(S).
good_story(S, R) :- setting_name(S), relic_name(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
    for r in RELICS:
        lines.append(asp.fact("relic_name", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    asp_pairs = sorted(set(asp.atoms(model, "good_story")))
    py_pairs = sorted((s, r) for s in SETTINGS for r in RELICS)
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python registry combinations ({len(py_pairs)}).")
        return 0
    print("MISMATCH between clingo and Python combinations:")
    if set(asp_pairs) - set(py_pairs):
        print("  only in ASP:", sorted(set(asp_pairs) - set(py_pairs)))
    if set(py_pairs) - set(asp_pairs):
        print("  only in Python:", sorted(set(py_pairs) - set(asp_pairs)))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/2."))
    return sorted(set(asp.atoms(model, "good_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="moon_dune", relic="cup", leader_name="Sahir", young_name="Nura"),
    StoryParams(setting="caravan_gate", relic="gourd", leader_name="Tala", young_name="Iman"),
    StoryParams(setting="oasis_edge", relic="lamp", leader_name="Rami", young_name="Zoya"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show good_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} valid setting/relic pairs:")
        for s, r in stories:
            print(f"  {s:12} {r}")
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
        header = f"### sample {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
