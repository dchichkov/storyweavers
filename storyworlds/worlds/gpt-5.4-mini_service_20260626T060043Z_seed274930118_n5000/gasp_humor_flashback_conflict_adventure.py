#!/usr/bin/env python3
"""
gasp_humor_flashback_conflict_adventure.py
==========================================

A small adventure storyworld with a gasp-worthy turn, a brief flashback,
light humor, and a clear conflict/resolution arc.

Seed tale:
---
Milo the fox cub wanted to cross the wobbly old bridge and reach the shiny kite
stuck on the far hill. When the bridge creaked, Milo gasped and almost turned
back. Then he remembered the kind old map maker's advice: "Slow feet, brave heart."
Milo laughed at how his knees shook, but he kept going. At the end, he carefully
brought the kite home and felt proud that the scary bridge had become a story
he could tell.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "cub", "boy", "rabbit", "child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "foxling", "squirrel"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    weather: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Goal:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"


@dataclass
class Helper:
    id: str
    label: str
    advice: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hills": Setting(place="the windy hills", weather="windy", affords={"kite"}),
    "bridge": Setting(place="the old bridge", weather="windy", affords={"kite"}),
    "meadow": Setting(place="the meadow path", weather="breezy", affords={"kite"}),
}

GOALS = {
    "kite": Goal(
        id="kite",
        verb="fetch the kite",
        gerund="fetching the kite",
        risk="the kite might blow away",
        zone={"hands", "arms", "torso"},
        keyword="gasp",
        tags={"wind", "kite"},
    ),
}

PRIZES = {
    "kite": Prize(
        label="kite",
        phrase="a bright red kite",
        region="hands",
        type="thing",
    ),
}

HELPERS = {
    "mapmaker": Helper(
        id="mapmaker",
        label="the map maker",
        advice="Slow feet, brave heart.",
        tail="followed the old advice and took careful steps",
    ),
    "goat": Helper(
        id="goat",
        label="a very opinionated goat",
        advice="Do not rush a squeaky bridge.",
        tail="laughed and kept one hoof steady at a time",
    ),
}

HEROES = {
    "fox": ("Milo", "fox"),
    "squirrel": ("Tessa", "squirrel"),
    "rabbit": ("Pip", "rabbit"),
}

TRAITS = ["curious", "brave", "silly", "careful", "bouncy"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    goal: str
    prize: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def goal_at_risk(goal: Goal, prize: Prize) -> bool:
    return prize.region in goal.zone or goal.id == "kite"


def resolve_helper(goal: Goal, helper: Helper) -> bool:
    return goal.id == "kite" and helper.id in HELPERS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for goal_id in setting.affords:
            goal = GOALS[goal_id]
            for prize_id, prize in PRIZES.items():
                if goal_at_risk(goal, prize):
                    combos.append((place, goal_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, goal: Goal, prize: Prize, hero_name: str, hero_type: str,
         helper: Helper, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            meters={}, memes={"joy": 0.0, "fear": 0.0, "conflict": 0.0,
                                              "humor": 0.0, "curiosity": 1.0, "gasp": 0.0}))
    prize_ent = world.add(Entity(id="prize", kind="thing", type=prize.type,
                                 label=prize.label, phrase=prize.phrase,
                                 owner=hero.id, carried_by=hero.id))
    helper_ent = world.add(Entity(id=helper.id, kind="character", type="adult",
                                  label=helper.label))

    # Act 1
    world.say(f"{hero_name} was a {trait} little {hero_type} who loved adventures.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {goal.verb}, because {goal.risk}.")
    world.say(f"One day, {hero_name} found {prize.phrase} resting far across {setting.place}.")

    # Flashback
    world.para()
    world.say(f"Then {hero_name} remembered a tiny flashback: {helper.label} had once said, "
              f"\"{helper.advice}\"")
    hero.memes["humor"] += 1
    world.say(f"{hero_name} almost laughed, because {hero.pronoun('possessive')} knees wobbled so hard "
              f"they looked like jelly.")

    # Conflict
    world.para()
    hero.memes["fear"] += 1
    hero.memes["gasp"] += 1
    world.say(f"The bridge gave a long creak, and {hero_name} went, gasp.")
    world.say(f"{hero_name} froze for a moment, because the wind tugged at {prize_ent.label} and made "
              f"the whole path feel tricky.")
    world.say(f"That was the problem: if {hero_name} rushed, {prize_ent.label} could blow away.")

    # Turn / resolution
    world.para()
    hero.memes["conflict"] += 1
    world.say(f"Still, {hero_name} took a breath, remembered the flashback, and {helper.tail}.")
    world.say(f"{hero_name} used {hero.pronoun('possessive')} careful paws, one step at a time.")
    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    world.say(f"At last, {hero_name} reached the kite, carried it home, and smiled at the silly little gasp "
              f"that had started the whole adventure.")

    world.facts.update(
        hero=hero,
        prize=prize_ent,
        goal=goal,
        helper=helper_ent,
        helper_cfg=helper,
        setting=setting,
        resolved=True,
        flashback=True,
        conflict=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    goal = f["goal"]
    prize = f["prize"]
    return [
        f'Write a short adventure story for a small child that includes the word "gasp".',
        f"Tell a gentle story where {hero.id} wants to {goal.verb} and worries about {prize.label}, but remembers helpful advice.",
        f"Write a humorous adventure with a flashback and a brave ending on {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    prize = f["prize"]
    helper = f["helper"]
    goal = f["goal"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {goal.verb} and bring home the {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered {helper.label} saying, \"{f['helper_cfg'].advice}\"",
        ),
        QAItem(
            question=f"Why did {hero.id} gasp on the bridge?",
            answer=f"{hero.id} gasped because the bridge creaked and the wind made the adventure feel scary for a moment.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the problem?",
            answer=f"{hero.id} slowed down, remembered the advice, and crossed carefully until the {prize.label} was safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier, so the character can remember it.",
        ),
        QAItem(
            question="Why can a windy place be tricky?",
            answer="Windy places can be tricky because wind can push things around, like hats, kites, or loose papers.",
        ),
        QAItem(
            question="What does gasp mean?",
            answer="Gasp means to take a quick breath because you are surprised, shocked, or startled.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
goal_at_risk(G,P) :- zone(G,R), prize_region(P,R).
valid(Place,G,P) :- affords(Place,G), goal_at_risk(G,P).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for g in sorted(s.affords):
            lines.append(asp.fact("affords", sid, g))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        for r in sorted(g.zone):
            lines.append(asp.fact("zone", gid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with gasp, humor, flashback, and conflict.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
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
    filtered = [c for c in combos
                if (args.place is None or c[0] == args.place)
                and (args.goal is None or c[1] == args.goal)
                and (args.prize is None or c[2] == args.prize)]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, goal, prize = rng.choice(sorted(filtered))
    hero_key = args.hero or rng.choice(list(HEROES))
    helper_key = args.helper or rng.choice(list(HELPERS))
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal, prize=prize, hero=hero_key, helper=helper_key, trait=trait)


def generate(params: StoryParams) -> StorySample:
    hero_name, hero_type = HEROES[params.hero]
    world = tell(
        SETTINGS[params.place],
        GOALS[params.goal],
        PRIZES[params.prize],
        hero_name,
        hero_type,
        HELPERS[params.helper],
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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
    StoryParams(place="bridge", goal="kite", prize="kite", hero="fox", helper="mapmaker", trait="curious"),
    StoryParams(place="hills", goal="kite", prize="kite", hero="squirrel", helper="goat", trait="silly"),
]


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
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
