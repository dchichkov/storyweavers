#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/boob_amputate_pantry_happy_ending_foreshadowing_curiosity.py
==================================================================================================

A standalone storyworld for a tiny rhyming tale about curiosity in a pantry,
with foreshadowing, a happy ending, and a very careful use of the word
"amputate" in a child-safe, toy-repair sense.

The seed idea:
- A small curious character named Boob explores a pantry.
- A loose shelf and a frayed toy arm foreshadow trouble.
- An adult warns that if the broken toy gets torn worse, they may have to
  amputate the damaged thread-and-stuffing arm.
- The child chooses a safer way to look, and the ending is warm and happy.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports storyworlds/results eagerly
- lazy ASP import inside helper functions
- typed entities with meters and memes
- state-driven prose, Q&A, tracing, CLI, and ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
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
    place: str = "the pantry"
    affords: set[str] = field(default_factory=set)
    indoor: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.worn_by == actor.id and region in g.covers for g in self.entities.values())


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "pantry": Setting(place="the pantry", affords={"peek", "reach"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek in the pantry",
        gerund="peeking in the pantry",
        rush="rush to the pantry shelf",
        mess="jostled",
        zone={"hands", "torso"},
        keyword="pantry",
        tags={"curiosity", "pantry"},
    ),
    "reach": Activity(
        id="reach",
        verb="reach for the cookie tin",
        gerund="reaching for the cookie tin",
        rush="dash for the cookie tin",
        mess="jostled",
        zone={"hands", "torso"},
        keyword="tin",
        tags={"curiosity", "pantry"},
    ),
}

PRIZES = {
    "bunny": Prize(
        label="bunny",
        phrase="a stitched plush bunny with a loose arm",
        type="toy",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="stepstool",
        label="a little step stool",
        covers={"feet", "hands"},
        guards={"jostled"},
        prep="use the little step stool",
        tail="used the little step stool and kept the pantry still",
    ),
    Gear(
        id="tape",
        label="soft cloth tape",
        covers={"torso"},
        guards={"jostled"},
        prep="wrap the bunny arm with soft cloth tape",
        tail="wrapped the bunny arm with soft cloth tape",
    ),
]

GIRL_NAMES = ["Mia", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Boob", "Theo", "Ben", "Noah"]
TRAITS = ["curious", "gentle", "bright", "spry"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not realistically endanger {prize.label} here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming pantry storyworld about curiosity and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait")
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
    if args.activity and args.prize:
        act, prize = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, prize) and select_gear(act, prize)):
            raise StoryError(explain_rejection(act, prize))
    place = args.place or "pantry"
    activity = args.activity or rng.choice(list(ACTIVITIES))
    prize = args.prize or "bunny"
    gender = args.gender or "boy"
    name = args.name or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _rhyming_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.traits[0]} little {hero.type} with eyes that loved to shine.")
    world.say(f"{hero.pronoun().capitalize()} liked to ask, \"What's in there?\" and march in curious time.")


def _setup(world: World, hero: Entity, parent: Entity, prize: Entity) -> None:
    world.say(f"In the pantry, shelves stood neat, with jars in a tidy line.")
    world.say(f"But one small shelf gave a tiny creak, a clue that seemed to twine.")
    world.say(f"{parent.pronoun().capitalize()} had bought {hero.pronoun('object')} {prize.phrase}, soft and sweet and fine.")
    prize.worn_by = hero.id
    hero.memes["love"] = 1.0


def _foreshadow(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(f"{hero.id} leaned in close to peek and grin; the pantry called like rhyme.")
    world.say(f"{parent.pronoun().capitalize()} frowned at the wobble on the shelf and spoke before the climb:")
    world.say(f"\"If that loose box should snag {prize.label}'s arm, we may need to amputate the torn part in good time.\"")


def _resolution(world: World, hero: Entity, parent: Entity, gear: Gear, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["fear"] = 0.0
    world.say(f"{hero.id} slowed down, smiled, and chose the safer way to play.")
    world.say(f"{hero.pronoun().capitalize()} fetched {gear.label} and helped {parent.pronoun('object')} make things stay in place that day.")
    world.say(f"Together they {gear.tail}, and the bunny's arm stayed stitched and bright.")
    world.say(f"No amputate was needed after all; the pantry ended in a happy, snuggly night.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=hero_traits))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=parent_type))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    _rhyming_intro(world, hero)
    _setup(world, hero, parent, prize)
    world.para()
    _foreshadow(world, hero, parent, activity, prize)
    gear = select_gear(activity, prize)
    world.para()
    if gear is None:
        raise StoryError("No compatible gear for this story.")
    _resolution(world, hero, parent, gear, prize)
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, gear=gear, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a rhyming story for a small child named {hero.id} who feels curious about {f["setting"].place}.',
        f'Tell a gentle pantry story that foreshadows trouble, then ends in a happy ending.',
        f'Use the words "boob", "amputate", and "pantry" in a child-safe story with a soft rhyme.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little curious {hero.type} who explores the pantry with care.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the shelf?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because the shelf gave a foreshadowing creak, and the loose toy arm could have been torn worse.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.id} used {gear.label}, the bunny stayed safe, and no amputate was needed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pantry?",
            answer="A pantry is a small room or cupboard where people keep food, jars, and snacks.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the wish to look, ask, and learn about new things.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little clue early in a story that hints something important may happen later.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters feel safe, glad, or loved.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.worn_by:
            parts.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A prize is at risk if the activity touches the same region.
prize_at_risk(A, P) :- zone(A, R), region(P, R).

% A compatible fix must exist.
has_fix(A, P) :- gear(G), guards(G, M), mess(A, M), prize_at_risk(A, P).

valid(Place, A, P) :- setting(Place), affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("pantry", a, p) for a in ACTIVITIES for p in PRIZES if prize_at_risk(ACTIVITIES[a], PRIZES[p]) and select_gear(ACTIVITIES[a], PRIZES[p])}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params_list = [
            StoryParams(place="pantry", activity="peek", prize="bunny", name="Boob", gender="boy", parent="mother", trait="curious")
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 10, 10):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
