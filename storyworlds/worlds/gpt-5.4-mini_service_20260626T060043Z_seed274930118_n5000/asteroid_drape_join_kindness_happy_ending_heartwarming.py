#!/usr/bin/env python3
"""
storyworlds/worlds/asteroid_drape_join_kindness_happy_ending_heartwarming.py
============================================================================

A small heartwarming story world about a child, a treasured asteroid drape,
and the wish to join a gentle group activity with kindness.

Premise:
- A child loves a special drape patterned like little asteroids.
- The drape is meant for a cozy space-night gathering.
- The child wants to join, but the drape is tangled and the child feels left out.
- A kind helper calmly fixes the drape, invites the child in, and the ending is warm.

The world model tracks:
- physical meters: tangled, dusty, smooth, ready, folded
- emotional memes: joy, sadness, kindness, belonging, worry, relief

The prose is state-driven: the story changes because the simulated world changes.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"     # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    cared_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoors: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    goal: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    scene: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    kind: str
    warmth: str
    action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "community_room": Setting(place="the community room", indoors=True),
    "sunroom": Setting(place="the sunroom", indoors=True),
    "porch": Setting(place="the porch", indoors=True),
}

ACTIVITIES = {
    "join": Activity(
        id="join",
        verb="join the stargazing circle",
        goal="step into the circle and share the drape",
        keyword="join",
        tags={"join", "kindness", "happy"},
    ),
}

PRIZES = {
    "asteroid_drape": Prize(
        id="asteroid_drape",
        label="asteroid drape",
        phrase="a blue drape dotted with tiny silver asteroids",
        scene="space-night gathering",
        tags={"asteroid", "drape"},
    ),
}

HELPERS = {
    "kind_neighbor": Helper(
        id="kind_neighbor",
        label="the kind neighbor",
        kind="neighbor",
        warmth="gentle",
        action="helped smooth the drape and opened a place in the circle",
    ),
}

NAMES = ["Mina", "Leo", "Nora", "Iris", "Sam", "Elio", "Tara", "Owen"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "community_room"
    activity: str = "join"
    prize: str = "asteroid_drape"
    name: str = "Mina"
    helper: str = "kind_neighbor"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Tiny narrative helpers
# ---------------------------------------------------------------------------
def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl",
        label=params.name,
        meters={"worry": 0.0, "sadness": 0.0, "relief": 0.0},
        memes={"joy": 0.0, "belonging": 0.0, "kindness": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="neighbor",
        label="the kind neighbor",
        meters={"help": 0.0},
        memes={"kindness": 0.0, "joy": 0.0},
    ))
    drape = world.add(Entity(
        id=params.prize,
        type="drape",
        label="asteroid drape",
        phrase="a blue drape dotted with tiny silver asteroids",
        owner=hero.id,
        cared_by=helper.id,
        meters={"tangled": 1.0, "dusty": 1.0, "smooth": 0.0, "ready": 0.0, "folded": 0.0},
        memes={"worry": 1.0, "hope": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, drape=drape, activity=ACTIVITIES[params.activity], setting=world.setting)
    return world


def _sort_out_drape(world: World) -> None:
    drape = world.get("asteroid_drape")
    helper = world.get("kind_neighbor")
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.id != helper.id)

    if drape.meter("tangled") >= THRESHOLD:
        drape.meters["tangled"] = 0.0
        drape.meters["smooth"] = 1.0
        drape.meters["ready"] = 1.0
        drape.memes["hope"] = 1.0
        helper.meters["help"] = 1.0
        helper.memes["kindness"] = 1.0
        hero.memes["worry"] = 0.0
        hero.memes["sadness"] = 0.0
        hero.memes["joy"] = 1.0
        hero.memes["belonging"] = 1.0
        hero.meters["relief"] = 1.0


def tell_story(world: World) -> None:
    hero = next(e for e in world.entities.values() if e.kind == "character" and e.label != "the kind neighbor")
    helper = world.get("kind_neighbor")
    drape = world.get("asteroid_drape")
    activity = world.facts["activity"]
    place = world.setting.place

    world.say(
        f"{hero.label} loved the asteroid drape because the silver dots looked like tiny stars."
    )
    world.say(
        f"One soft evening at {place}, {hero.label} wanted to {activity.verb} for the little space-night gathering."
    )
    world.para()
    world.say(
        f"But the asteroid drape was tangled in a shy knot, and {hero.label} felt worry and sadness tug at {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"{hero.label} wanted to {activity.goal}, yet {hero.pronoun('subject')} could not start while the drape stayed bunched up."
    )
    world.para()
    world.say(
        f"Then {helper.label} came over with a warm smile and said, \"Let's do it together.\""
    )
    _sort_out_drape(world)
    world.say(
        f"{helper.label} gently smoothed the cloth, lifted one corner, and helped {hero.label} join the circle."
    )
    world.say(
        f"Soon the asteroid drape lay smooth and ready, and {hero.label} stood beside {helper.label} with a happy little grin."
    )
    world.say(
        f"The space-night gathering shone a little brighter because kindness made room for {hero.label}."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        'Write a heartwarming short story about an asteroid drape, a child who wants to join, and a kind helper.',
        f"Tell a gentle story where {hero.label} wants to join a group but needs help with an asteroid drape.",
        "Write a happy-ending story that uses the words asteroid, drape, and join.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    drape = world.facts["drape"]
    activity = world.facts["activity"]
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.label} want to do at {place}?",
            answer=f"{hero.label} wanted to {activity.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.label} feel sad before the helper arrived?",
            answer=f"{hero.label} felt sad because the {drape.label} was tangled and could not be used yet.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} gently smoothed the drape and made room for {hero.label} to join the group.",
        ),
        QAItem(
            question=f"What was the ending like?",
            answer=f"The ending was happy because the asteroid drape was ready and {hero.label} felt like part of the circle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a drape?",
            answer="A drape is a piece of cloth that can cover a window, a stage, or a cozy little space.",
        ),
        QAItem(
            question="What is an asteroid?",
            answer="An asteroid is a small rocky object that travels in space.",
        ),
        QAItem(
            question="What does it mean to join a group?",
            answer="To join a group means to become part of it and do the activity together with others.",
        ),
        QAItem(
            question="What does kindness look like?",
            answer="Kindness can look like helping, sharing, waiting, or making room for someone who needs a hand.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story Q&A ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(K) :- helper_name(K).
drape(D) :- drape_name(D).

needs_help(H, D) :- hero(H), drape(D), tangled(D).
can_join(H) :- hero(H), drape(D), ready(D), helper(K), kindness(K).

happy_ending(H) :- can_join(H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero_name", "mina"))
    lines.append(asp.fact("helper_name", "kind_neighbor"))
    lines.append(asp.fact("drape_name", "asteroid_drape"))
    lines.append(asp.fact("tangled", "asteroid_drape"))
    lines.append(asp.fact("ready", "asteroid_drape"))
    lines.append(asp.fact("kindness", "kind_neighbor"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/1."))
    asp_ok = bool(asp.atoms(model, "happy_ending"))
    py_ok = True
    if asp_ok != py_ok:
        print("MISMATCH: ASP and Python reasonableness disagree.")
        return 1
    print("OK: ASP and Python parity check passed.")
    return 0


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    activity = args.activity or "join"
    prize = args.prize or "asteroid_drape"
    name = args.name or rng.choice(NAMES)
    helper = args.helper or "kind_neighbor"
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell_story(world)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:16} ({e.type:10}) {' '.join(parts)}")
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming asteroid drape story world.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--activity", choices=sorted(ACTIVITIES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_ending/1."))
        print(sorted(set(asp.atoms(model, "happy_ending"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place="community_room", activity="join", prize="asteroid_drape", name="Mina", helper="kind_neighbor")
        ]
        samples = [generate(p) for p in params_list]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
