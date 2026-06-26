#!/usr/bin/env python3
"""
storyworlds/worlds/dictionary_cyst_misunderstanding_reconciliation_repetition_space_adventure.py
===============================================================================================

A small Space Adventure story world about a dictionary, a mysterious cyst-like
capsule, a misunderstanding that repeats, and a reconciliation that settles
the crew back into calm.

Seed tale:
---
On a tiny starship, a young cadet found a thick dictionary and loved using it
to learn alien words. One day the scanner found a strange cyst-shaped pod near
the hatch. The cadet kept repeating the same warning, but a friend misunderstood
and thought the pod was dangerous. The dictionary helped them realize it was
only a seed capsule from a friendly moon plant. They apologized, laughed, and
put the capsule in a warm light until it opened safely.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "cadet"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    window_view: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    misunderstanding: str
    resolution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    type: str
    risky: bool = False
    soothing: bool = False
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for crew in world.characters():
        if crew.memes.get("repetition", 0) < THRESHOLD:
            continue
        sig = ("repeat", crew.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crew.memes["worry"] = crew.memes.get("worry", 0) + 1
        out.append(f"{crew.label} said the warning again, and the words echoed in the cabin.")
    return out


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    for crew in world.characters():
        if crew.memes.get("misunderstanding", 0) < THRESHOLD:
            continue
        sig = ("misunderstanding", crew.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        crew.memes["tension"] = crew.memes.get("tension", 0) + 1
        out.append(f"That made the room feel tight and puzzled.")
    return out


CAUSAL_RULES = [
    _r_repeat,
    _r_misunderstanding,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prism_name(setting: Setting) -> str:
    return setting.window_view


def tell(setting: Setting, mission: Mission, hero_cfg: ObjectCfg, friend_cfg: ObjectCfg, cyst_cfg: ObjectCfg) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Ari", kind="character", type="cadet", label="Ari"))
    friend = world.add(Entity(id="Mina", kind="character", type="captain", label="Mina"))
    dictionary = world.add(Entity(id="dictionary", type=hero_cfg.type, label="dictionary", phrase=hero_cfg.phrase))
    cyst = world.add(Entity(id="cyst", type=cyst_cfg.type, label="cyst", phrase=cyst_cfg.phrase))

    hero.memes["curiosity"] = 1
    friend.memes["care"] = 1

    world.say(f"Ari kept a dictionary tucked in the pocket of the suit, because new star words were fun to learn.")
    world.say(f"Outside the ship, {prism_name(setting)} shimmered like spilled sugar in the dark.")

    world.para()
    world.say(f"One orbiting morning, the scanner beeped beside the hatch and found a strange cyst-shaped pod.")
    world.say(f"Mina squinted at it and said, \"Don't touch the cyst.\"")
    hero.memes["misunderstanding"] = 1
    hero.memes["repetition"] = 1
    propagate(world)
    world.say(f"Ari kept repeating the warning, \"A cyst! A cyst!\" because {mission.repeat_line}")

    world.para()
    world.say(f"That repetition made Mina think the pod was dangerous, so she reached for the emergency seal.")
    world.say(f"Ari opened the dictionary and found the right page.")
    world.say(f"It showed that the pod was really a seed capsule from a moon plant, not a problem to panic about.")
    hero.memes["misunderstanding"] = 0
    friend.memes["misunderstanding"] = 0
    friend.memes["reconciliation"] = 1

    world.para()
    world.say(f"Mina took a slow breath and smiled. \"I misunderstood,\" she said.")
    world.say(f"Ari nodded, and the two of them laughed at the echoing alarm words.")
    world.say(f"They moved the cyst-shaped capsule under a warm lamp, where it rested safely until it opened on its own.")

    world.facts.update(
        hero=hero,
        friend=friend,
        dictionary=dictionary,
        cyst=cyst,
        mission=mission,
        setting=setting,
        resolved=True,
        misunderstood=True,
    )
    return world


SETTINGS = {
    "starship": Setting(place="the starship", window_view="the blue curve of Earth", affords={"scan"}),
    "moonbase": Setting(place="the moonbase", window_view="the dusty horizon of the Moon", affords={"scan"}),
    "orbital_garden": Setting(place="the orbital garden", window_view="the bright ring of the station", affords={"scan"}),
}

MISSIONS = {
    "echo": Mission(
        id="echo",
        verb="scan the hatch",
        gerund="scanning the hatch",
        repeat_line="the alarm words kept bouncing around the cabin",
        misunderstanding="a warning sounded scary",
        resolution="the dictionary explained the real meaning",
        tags={"dictionary", "cyst", "misunderstanding", "repetition", "reconciliation"},
    ),
}

OBJECTS = {
    "dictionary": ObjectCfg(
        id="dictionary",
        label="dictionary",
        phrase="a thick dictionary full of alien words",
        type="book",
        soothing=True,
        tags={"dictionary"},
    ),
    "cyst": ObjectCfg(
        id="cyst",
        label="cyst",
        phrase="a cyst-shaped seed capsule",
        type="pod",
        risky=True,
        tags={"cyst"},
    ),
    "lamp": ObjectCfg(
        id="lamp",
        label="lamp",
        phrase="a warm lamp",
        type="lamp",
        soothing=True,
        tags={"reconciliation"},
    ),
}

CURATED = [
    ("starship", "echo"),
    ("moonbase", "echo"),
    ("orbital_garden", "echo"),
]


@dataclass
class StoryParams:
    place: str
    mission: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure storyworld with dictionary, cyst, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
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
    mission = args.mission or rng.choice(list(MISSIONS))
    return StoryParams(place=place, mission=mission)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MISSIONS[params.mission], OBJECTS["dictionary"], OBJECTS["cyst"], OBJECTS["lamp"])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a gentle space adventure for a young child about a dictionary, a cyst-shaped pod, and a misunderstanding.',
        'Tell a story where repeated warning words cause confusion, and a dictionary helps everyone reconcile.',
        f"Write a small starship story set near {world.setting.place} that ends with calm and a safe capsule.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    return [
        QAItem(
            question="What did Ari keep in the suit pocket?",
            answer="Ari kept a dictionary in the suit pocket so new star words would be easy to learn.",
        ),
        QAItem(
            question="Why did Mina misunderstand the situation?",
            answer="Mina misunderstood because the scanner found a cyst-shaped pod and the repeated warning words made it sound scary.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with Ari and Mina understanding each other, laughing, and placing the cyst-shaped seed capsule under a warm lamp.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dictionary for?",
            answer="A dictionary helps people learn what words mean.",
        ),
        QAItem(
            question="Why can repetition matter in a story?",
            answer="Repetition can make a warning or feeling stronger, which can help a story build tension.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people understand each other again after a problem or misunderstanding.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(starship). setting(moonbase). setting(orbital_garden).
mission(echo).

has_dictionary :- item(dictionary).
has_cyst :- item(cyst).

misunderstanding(S) :- setting(S), has_dictionary, has_cyst.
repetition(S) :- setting(S), has_dictionary.
reconciliation(S) :- misunderstanding(S), repetition(S).

valid_story(S,M) :- setting(S), mission(M), misunderstanding(S), repetition(S), reconciliation(S).

#show valid_story/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("item", "dictionary"),
        asp.fact("item", "cyst"),
        asp.fact("item", "lamp"),
    ]
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {(s, m) for s in SETTINGS for m in MISSIONS}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python ({len(py_set)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


def build_story_params(place: str, mission: str, seed: Optional[int] = None) -> StoryParams:
    return StoryParams(place=place, mission=mission, seed=seed)


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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, mission in CURATED:
            samples.append(generate(build_story_params(place, mission, seed=base_seed)))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
