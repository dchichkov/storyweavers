#!/usr/bin/env python3
"""
storyworlds/worlds/haggis_status_suspense_lesson_learned_animal_story.py
========================================================================

A small animal-story world about a haggis, status, suspense, and a lesson
learned.

Seed tale:
---
At the hill farm, Hattie the haggis wanted the high rock where the ponies could
see her. She felt small beside the tall animals and worried that nobody knew her
status. One windy afternoon, she climbed toward a shiny ledge to prove herself,
but the ledge wobbled and the burrow path below looked far away. A friendly
sheep called for help, and Hattie learned that real status came from being kind
and sensible, not from standing in the highest place.

This storyworld models:
- a small animal cast with typed entities
- physical meters: height, distance, wobble, and risk
- emotional memes: status, worry, courage, relief, pride, and lesson learned
- a suspense beat driven by a risky climb
- a resolution beat where help and humility change the ending
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"haggis", "animal", "sheep", "goat", "rabbit", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "female"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "male"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    goal: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _r_wobble(world: World) -> None:
    ledge = world.entities["ledge"]
    climber = world.entities["hero"]
    if climber.meters["climb"] >= THRESHOLD and ledge.meters["wobble"] < THRESHOLD:
        ledge.meters["wobble"] = 1.0
        world.facts["suspense"] = True


def _r_help(world: World) -> None:
    if world.entities["hero"].meters.get("risk", 0.0) >= THRESHOLD and "help" not in world.fired:
        world.fired.add("help")
        world.entities["helper"].memes["care"] += 1
        world.entities["hero"].memes["relief"] += 1


def propagate(world: World) -> None:
    _r_wobble(world)
    _r_help(world)


SETTINGS = {
    "hill": {
        "label": "the windy hill",
        "detail": "The grass bent low, and the stones looked slick with mist.",
    },
    "croft": {
        "label": "the quiet croft",
        "detail": "The path was soft, and the fence posts stood like little guards.",
    },
    "pasture": {
        "label": "the green pasture",
        "detail": "The meadow shone bright, with a stone ledge near the old wall.",
    },
}

HEROES = {
    "hattie": {"label": "Hattie", "type": "haggis"},
    "moss": {"label": "Moss", "type": "haggis"},
    "bramble": {"label": "Bramble", "type": "haggis"},
}

HELPERS = {
    "sheep": {"label": "Sheila", "type": "sheep"},
    "goat": {"label": "Gordon", "type": "goat"},
    "rabbit": {"label": "Rina", "type": "rabbit"},
}

GOALS = {
    "status": {
        "name": "status",
        "phrase": "the highest rock",
        "reason": "to look important",
        "lesson": "true status comes from kind, careful choices",
    },
    "view": {
        "name": "view",
        "phrase": "the sunny ledge",
        "reason": "to see the whole field",
        "lesson": "a good view is not worth a risky climb",
    },
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, h, g) for s in SETTINGS for h in HEROES for g in GOALS]


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for g in GOALS:
        lines.append(asp.fact("goal", g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,H,G) :- setting(S), hero(H), goal(G).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: haggis, status, suspense, lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--goal", choices=GOALS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.hero is None or c[1] == args.hero)
              and (args.goal is None or c[2] == args.goal)]
    if not combos:
        raise StoryError("No valid combination matches those choices.")
    setting, hero, goal = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, hero=hero, helper=helper, goal=goal)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hero not in HEROES or params.helper not in HELPERS or params.goal not in GOALS:
        raise StoryError("Invalid params.")
    w = World()
    hero_def = HEROES[params.hero]
    helper_def = HELPERS[params.helper]
    goal_def = GOALS[params.goal]
    hero = w.add(Entity(id="hero", kind="character", type=hero_def["type"], label=hero_def["label"],
                        meters={"climb": 0.0, "risk": 0.0}, memes={"status": 0.0, "worry": 0.0, "courage": 0.0, "relief": 0.0, "pride": 0.0, "lesson": 0.0},
                        attrs={"name": hero_def["label"]}, tags={"animal", "haggis"}))
    helper = w.add(Entity(id="helper", kind="character", type=helper_def["type"], label=helper_def["label"],
                          meters={"help": 0.0}, memes={"care": 0.0, "status": 0.0}, attrs={"name": helper_def["label"]}, tags={"animal"}))
    ledge = w.add(Entity(id="ledge", type="thing", label=goal_def["phrase"], meters={"wobble": 0.0}))
    w.facts.update(hero=hero, helper=helper, ledge=ledge, setting=params.setting, goal=goal_def, params=params)
    s = SETTINGS[params.setting]

    w.say(f"At {s['label']}, {hero.label} the haggis watched the tall animals and wondered about {goal_def['name']}.")
    w.say(s["detail"])
    w.say(f"{hero.label} wanted {goal_def['phrase']} {goal_def['reason']}, and that made {hero.pronoun('possessive')} whiskers twitch.")

    w.para()
    hero.memes["status"] += 1
    hero.memes["worry"] += 1
    hero.meters["climb"] += 1
    hero.meters["risk"] += 1
    propagate(w)
    w.say(f"Then {hero.label} climbed toward {goal_def['phrase']}, and the ledge gave a tiny wobble.")
    w.say(f"The little wobble felt like a big hush, and {hero.label} stopped to listen.")
    w.say(f"{helper.label} called out from below, gentle and clear, because {helper.label} knew a smart haggis should not chase status by standing too high.")

    w.para()
    hero.memes["courage"] += 1
    hero.memes["pride"] += 1
    hero.memes["status"] += 1
    helper.memes["status"] += 1
    hero.meters["climb"] = 0.0
    hero.meters["risk"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    w.say(f"{hero.label} climbed back down and smiled at {helper.label}.")
    w.say(f"Together they shared a calmer place on the grass, where {hero.label} could still be important without wobbling the rocks.")
    w.say(f"By the end, {goal_def['lesson']}, and {hero.label} felt proud in a kinder way.")

    w.facts["resolved"] = True
    w.facts["suspense"] = True
    return StorySample(
        params=params,
        story=w.render(),
        prompts=[
            f"Write an animal story about a haggis and {goal_def['name']} that includes suspense and a lesson learned.",
            f"Tell a child-friendly story where {hero_def['label']} the haggis worries about status at {params.setting}.",
        ],
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
    )


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    helper = world.facts["helper"]
    g = world.facts["goal"]
    return [
        QAItem(question=f"Why did {h.label} climb toward {g['phrase']}?", answer=f"{h.label} wanted {g['phrase']} {g['reason']}. {h.label} hoped that would raise {h.pronoun('possessive')} status."),
        QAItem(question=f"What made the scene suspenseful?", answer=f"The ledge wobbled while {h.label} was still climbing, so the moment felt unsure and tense. The quiet pause made everyone wait to see what would happen next."),
        QAItem(question=f"What helped {h.label} learn a better lesson?", answer=f"{helper.label} called from below and showed that kindness and safety mattered more than standing in the highest place. After that, {h.label} learned that real status comes from good choices."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a haggis in this storyworld?", answer="A haggis is a small animal character with quick feet and a brave heart."),
        QAItem(question="What does status mean here?", answer="Status means how important or respected someone feels. In this story, the haggis learns that good actions matter more than trying to look tall or grand."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"facts={world.facts}")
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
    StoryParams(setting="hill", hero="hattie", helper="sheep", goal="status"),
    StoryParams(setting="croft", hero="moss", helper="goat", goal="view"),
    StoryParams(setting="pasture", hero="bramble", helper="rabbit", goal="status"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set != py_set:
        print("MISMATCH between ASP and Python valid_combos")
        return 1
    print(f"OK: ASP and Python agree on {len(py_set)} combos.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))


if __name__ == "__main__":
    main()
