#!/usr/bin/env python3
"""
A small storyworld: animals in a dance studio, a paint-and-parfait mishap, and a
kindness-based fix.

Premise:
- A young animal loves dance studio play and colorful art.
- A special parfait has tidy layers that matter.
- Paint makes a mess that can spoil the parfait and the class mood.
- Kindness turns the problem into a gentle repair.

The world model tracks physical meters and emotional memes, and the prose is
built from simulated state rather than swapped nouns.
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
# Domain registries
# ---------------------------------------------------------------------------

@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    action: str
    result: str
    kindness_boost: float = 1.0


SETTINGS = {
    "studio": Setting(place="the dance studio", affords={"paint"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint bright stage signs",
        gerund="painting bright stage signs",
        mess="painted",
        soil="spotted with paint",
        zone={"hands", "torso"},
        keyword="paints",
        tags={"paint", "paints", "layer"},
    ),
}

PRIZES = {
    "parfait": Prize(
        label="parfait",
        phrase="a neat berry parfait with a careful layer of cream",
        region="hands",
    ),
}

HELPERS = {
    "kindness": Helper(
        id="kindness",
        label="Kindness",
        action="help everyone breathe and speak softly",
        result="made the room feel safe again",
        kindness_boost=2.0,
    ),
}

NAMES = ["Mina", "Pip", "Toby", "Luna", "Basil", "Coco"]
ANIMALS = ["rabbit", "bear", "fox", "mouse", "cat", "panda"]
TRAITS = ["curious", "gentle", "shy", "bouncy", "helpful", "bright"]


# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
# Simulation rules
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


def propagate(world: World) -> None:
    child = world.get("child")
    parfait = world.get("parfait")
    studio = world.setting.place
    if child.meters.get("painted", 0.0) >= THRESHOLD and parfait.meters.get("dirty", 0.0) < THRESHOLD:
        parfait.meters["dirty"] = parfait.meters.get("dirty", 0.0) + 1
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        world.say(f"A few paint specks drifted onto the parfait, and its careful layer stopped looking neat.")


def do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world)


def apply_kindness(world: World, helper: Helper) -> None:
    child = world.get("child")
    parfait = world.get("parfait")
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + helper.kindness_boost
    child.memes["worry"] = max(0.0, child.memes.get("worry", 0.0) - 1.0)
    parfait.meters["dirty"] = max(0.0, parfait.meters.get("dirty", 0.0) - 1.0)
    world.say("Kindness helped everyone pause, wipe carefully, and try again without rushing.")


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize: Prize, helper: Helper,
         name: str = "Mina", animal: str = "rabbit", trait: str = "gentle") -> World:
    world = World(setting)

    child = world.add(Entity(
        id="child",
        kind="character",
        type=animal,
        label=name,
        meters={"painted": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "kindness": 0.0},
    ))
    parent = world.add(Entity(
        id="coach",
        kind="character",
        type="adult",
        label="the dance coach",
        memes={"calm": 0.0},
    ))
    parfait = world.add(Entity(
        id="parfait",
        label="parfait",
        phrase=prize.phrase,
        owner=child.id,
        caretaker=parent.id,
        region=prize.region,
        meters={"dirty": 0.0},
    ))
    kindness = world.add(Entity(
        id="kindness",
        kind="abstract",
        type="virtue",
        label=helper.label,
        phrase=helper.result,
    ))

    world.say(
        f"{name} was a {trait} little {animal} who loved the dance studio because it was bright, "
        f"safe, and full of music."
    )
    world.say(
        f"{name} also loved {activity.gerund}, and {name} loved the sweet parfait "
        f"with its careful layer of cream and berries."
    )
    world.say(
        f"One afternoon at {studio_name(setting)}, {name} wanted to {activity.verb} before class started."
    )
    world.para()
    world.say(
        f"{name} dipped busy paws into paint and began {activity.gerund} beside the snack table."
    )
    do_activity(world, child, activity)
    world.say(
        f"The paint was fun, but it could reach the parfait and make the top layer look messy."
    )
    world.say(
        f"The dance coach watched the spill and said that {name} should slow down and choose a gentle way."
    )
    world.para()
    world.say(
        f"{name} frowned for a moment, then looked at the little mess and tried to be kind instead of upset."
    )
    apply_kindness(world, helper)
    world.say(
        f"Together, they set the parfait back in order and washed the paint from {name}'s paws."
    )
    world.say(
        f"Then {name} smiled, the studio felt calm again, and the parfait's layers looked neat and safe."
    )

    world.facts.update(
        child=child,
        coach=parent,
        parfait=parfait,
        activity=activity,
        helper=helper,
        setting=setting,
        resolved=True,
    )
    return world


def studio_name(setting: Setting) -> str:
    return setting.place


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    return [
        f'Write a short animal story set in {world.setting.place} about a little {child.type} who likes {activity.keyword} and learns kindness.',
        f'Tell a gentle story where paint, a parfait, and a dance class all become part of one small problem and fix.',
        f'Write a child-friendly story about a messy paint moment in a dance studio that ends with a calm kindness choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    activity = f["activity"]
    parfait = f["parfait"]
    return [
        QAItem(
            question=f"What kind of place was {child.label} in?",
            answer=f"{child.label} was in the dance studio, where music, practice, and gentle play happened together.",
        ),
        QAItem(
            question=f"What did {child.label} want to do before class?",
            answer=f"{child.label} wanted to {activity.verb}, because painting made the studio feel lively and bright.",
        ),
        QAItem(
            question=f"What was special about the parfait?",
            answer=f"The parfait had a careful layer of cream and berries, so paint specks would make it look messy.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with Kindness helping everyone slow down, clean up, and keep the parfait neat again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness is when someone helps gently, speaks softly, and makes things feel safer for others.",
        ),
        QAItem(
            question="What is a parfait?",
            answer="A parfait is a layered dessert, often with fruit, cream, and something crunchy or soft between the layers.",
        ),
        QAItem(
            question="What is paint for?",
            answer="Paint is used to add color to paper, signs, and pictures.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is compatible when the dance studio affords the activity,
% the activity can dirty the parfait's region, and kindness is present.
at_risk(A, P) :- activity(A), prize(P), splashes(A, R), worn_on(P, R).
valid_story(S, A, P) :- setting(S), affords(S, A), at_risk(A, P), has_fix(A, P).
has_fix(A, P) :- at_risk(A, P), helper(kindness).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    lines.append(asp.fact("helper", "kindness"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.affords:
            for pid, prize in PRIZES.items():
                act = ACTIVITIES[aid]
                if prize.region in act.zone:
                    combos.append((sid, aid, pid))
    return combos


def asp_verify() -> int:
    import storyworlds.asp as asp
    clingo_set = set(asp_valid_stories())
    py_set = set((s, a, p) for s, a, p in valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - py_set:
        print("only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# StorySample generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "studio"
    activity: str = "paint"
    prize: str = "parfait"
    name: str = "Mina"
    animal: str = "rabbit"
    trait: str = "gentle"
    seed: Optional[int] = None


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.activity and args.activity not in ACTIVITIES:
        raise StoryError("Unknown activity.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Unknown prize.")
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(sorted(SETTINGS[place].affords))
    prize = args.prize or "parfait"
    name = args.name or rng.choice(NAMES)
    animal = args.animal or rng.choice(ANIMALS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, animal=animal, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        HELPERS["kindness"],
        name=params.name,
        animal=params.animal,
        trait=params.trait,
    )
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
    if qa:
        print()
        print(format_qa(sample))


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
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world in a dance studio with paint, parfait, layer, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
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


CURATED = [
    StoryParams(place="studio", activity="paint", prize="parfait", name="Mina", animal="rabbit", trait="gentle"),
    StoryParams(place="studio", activity="paint", prize="parfait", name="Pip", animal="mouse", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story tuples:")
        for item in stories:
            print(" ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
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
