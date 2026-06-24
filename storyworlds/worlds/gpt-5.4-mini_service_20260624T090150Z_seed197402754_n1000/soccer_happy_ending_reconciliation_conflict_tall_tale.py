#!/usr/bin/env python3
"""
Storyworld: a tall-tale soccer trouble that ends in a happy reconciliation.

A child loves soccer and wants to kick a ball with wild, giant-boot energy.
A parent worries that the ball will smash a window or trample a garden.
They argue, then notice a gentler way: a soft practice ball, a marked goal,
and a careful game that keeps everybody smiling.

This world is deliberately tiny and self-contained, but state-driven:
- meters track size, speed, damage, and play
- memes track excitement, worry, conflict, and reconciliation
- the ending changes because the world changes, not because of swapped nouns
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass(frozen=True)
class Setting:
    place: str
    indoors: bool
    affords: set[str]


@dataclass(frozen=True)
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Ball:
    label: str
    phrase: str
    size: str
    bounce: str
    kindness: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    guards: set[str]


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        return clone


def _r_damage(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("kick", 0.0) < THRESHOLD:
            continue
        for obj in world.entities.values():
            if obj.kind == "thing" and obj.id.startswith("target_"):
                continue
        for item in world.entities.values():
            if item.id == "window" and item.meters.get("near", 0.0) >= THRESHOLD:
                if ("damage", item.id) in world.fired:
                    continue
                if actor.meters.get("wild", 0.0) < THRESHOLD:
                    continue
                world.fired.add(("damage", item.id))
                item.meters["crack"] = item.meters.get("crack", 0.0) + 1
                out.append("A crack spidered across the window like a grumpy little lightning bolt.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    parent = world.get("parent")
    if hero.memes.get("conflict", 0.0) >= THRESHOLD and parent.memes.get("worry", 0.0) >= THRESHOLD:
        if ("reconcile", "talk") in world.fired:
            return out
        world.fired.add(("reconcile", "talk"))
        hero.memes["conflict"] = 0.0
        hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
        parent.memes["worry"] = 0.0
        parent.memes["relief"] = parent.memes.get("relief", 0.0) + 1
        out.append("Then they took a breath, and the storm in their voices blew clear.")
    return out


def _r_happy(world: World) -> list[str]:
    hero = world.get("hero")
    parent = world.get("parent")
    ball = world.get("ball")
    goal = world.get("goal")
    if ball.meters.get("play", 0.0) >= THRESHOLD and goal.meters.get("set", 0.0) >= THRESHOLD:
        if ("happy", "ending") in world.fired:
            return []
        world.fired.add(("happy", "ending"))
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        parent.memes["joy"] = parent.memes.get("joy", 0.0) + 1
        return [f"In the end, {hero.id} sailed the ball through the goal, and the whole yard rang with laughter."]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_damage, _r_reconcile, _r_happy):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "yard": Setting("the backyard", False, {"soccer"}),
    "field": Setting("the open field", False, {"soccer"}),
    "gym": Setting("the school gym", True, {"soccer"}),
}

ACTIVITIES = {
    "soccer": Activity(
        id="soccer",
        verb="kick the soccer ball",
        gerund="playing soccer",
        rush="charge at the ball",
        mess="wild",
        soil="all scuffed up",
        zone={"feet", "legs"},
        keyword="soccer",
        tags={"soccer", "ball"},
    )
}

BALLS = {
    "bigball": Ball(
        label="soccer ball",
        phrase="a brand-new soccer ball",
        size="giant",
        bounce="like a cannon-shot rubber moon",
        kindness="soft enough for careful feet",
        tags={"soccer", "ball"},
    )
}

FIXES = {
    "softball": Fix(
        id="softball",
        label="a softer practice ball",
        prep="switch to a softer practice ball",
        tail="swapped in the softer practice ball and set a careful goal",
        protects={"feet", "legs"},
        guards={"wild"},
    ),
    "cones": Fix(
        id="cones",
        label="two bright cones",
        prep="set up two bright cones",
        tail="pushed the cones into place and made a tiny goal",
        protects={"feet", "legs"},
        guards={"wild"},
    ),
}

HERO_NAMES = ["Milo", "Nina", "Toby", "Luna", "Ivy", "Jax", "Piper", "Zoe"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["bold", "curious", "spirited", "cheerful"]


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    trait: str
    fix: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for bid, b in BALLS.items():
        lines.append(asp.fact("ball", bid))
        for t in sorted(b.tags):
            lines.append(asp.fact("tagged", bid, t))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for p in sorted(f.protects):
            lines.append(asp.fact("covers", fid, p))
        for g in sorted(f.guards):
            lines.append(asp.fact("guards", fid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(S, A, B, F) :- affords(S, A), activity(A), ball(B), fix(F),
                           splashes(A, R), covers(F, R), guards(F, M), mess_of(A, M).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for aid in s.affords:
            act = ACTIVITIES[aid]
            for bid in BALLS:
                for fid, f in FIXES.items():
                    if act.zone & f.protects and act.mess in f.guards:
                        out.append((sid, aid, fid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale soccer storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--fix", choices=FIXES)
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
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.fix:
        combos = [c for c in combos if c[2] == args.fix]
    if not combos:
        raise StoryError("No valid soccer story matches those options.")
    place, _, fix = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(PARENT_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, parent=parent, trait=trait, fix=fix)


def _hero_word(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=_hero_word(params.gender), label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    ball = world.add(Entity(id="ball", kind="thing", type="ball", label="soccer ball", phrase=BALLS["bigball"].phrase))
    goal = world.add(Entity(id="goal", kind="thing", type="goal", label="goal", phrase="two bright cones"))
    window = world.add(Entity(id="window", kind="thing", type="window", label="window"))
    window.meters["near"] = 1.0

    hero.memes["love"] = 1.0
    parent.memes["worry"] = 1.0
    ball.meters["play"] = 0.0
    ball.meters["size"] = 3.0
    hero.meters["kick"] = 0.0
    hero.meters["wild"] = 1.0

    world.say(f"{params.name} was a {params.trait} {hero.type} who loved soccer more than clouds love thunder.")
    world.say(f"{hero.id} dreamed of kicking a ball so hard it would bounce like a moon across the yard.")
    world.say(f"One day, {hero.id} found a {BALLS['bigball'].size} soccer ball waiting by {setting.place}.")
    world.para()
    world.say(f"{hero.id} wanted to {ACTIVITIES['soccer'].verb}, but {parent.label_word} frowned at the nearby window.")
    world.say(f'"That ball could fly off and make a crack in the glass," {parent.label_word} said, worried and stern.')
    hero.memes["conflict"] = 1.0
    hero.meters["kick"] = 1.0
    propagate(world, narrate=True)
    world.para()
    fix = FIXES[params.fix]
    world.say(f"Then {parent.label_word} had a wiser thought than a fox in a henhouse.")
    world.say(f'"How about we {fix.prep}?" {parent.label_word} asked.')
    if fix.id == "softball":
        world.say(f"{hero.id} nodded, and the giant old ball was traded for one {BALLS['bigball'].kindness}.")
    else:
        world.say(f"{hero.id} helped push the cones into place, and the yard got a tiny goal as neat as a button.")
    ball.meters["play"] = 1.0
    goal.meters["set"] = 1.0
    hero.meters["wild"] = 0.0
    hero.memes["conflict"] = 1.0
    propagate(world, narrate=True)
    world.facts.update(hero=hero, parent=parent, ball=ball, goal=goal, window=window, fix=fix, params=params)
    world.say(f"{hero.id} kicked, the ball whooshed, and the day ended with grins wider than a wagon wheel.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent = f["hero"], f["parent"]
    return [
        f'Write a short tall-tale soccer story for young children about a child named {hero.label} and a worried {parent.type}.',
        f"Tell a funny, gentle story where {hero.label} wants to play soccer but the grown-up fears a window getting broken.",
        f'Write a story that uses the word "soccer" and ends in reconciliation and a happy ending after a conflict.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, fix, params = f["hero"], f["parent"], f["fix"], f["params"]
    return [
        QAItem(
            question=f"Who wanted to play soccer in the story?",
            answer=f"{hero.label} wanted to play soccer. {hero.label} was the {params.trait} {hero.type} at the center of the tall-tale trouble.",
        ),
        QAItem(
            question=f"Why was the {parent.label_word} worried?",
            answer=f"{parent.label_word.capitalize()} was worried that the soccer ball could fly off and crack the window.",
        ),
        QAItem(
            question=f"How did they solve the conflict?",
            answer=f"They reconciled by using {fix.label} so the game could stay safe and still feel exciting.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is soccer?",
            answer="Soccer is a game where players kick a ball and try to score goals.",
        ),
        QAItem(
            question="What does a goal do in soccer?",
            answer="A goal is the place where the ball goes when a team scores a point.",
        ),
        QAItem(
            question="Why can a soft practice ball help?",
            answer="A softer ball is gentler and is less likely to hurt things or make a big mess.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    for title, items in [
        ("(1) Generation prompts", sample.prompts),
        ("(2) Story questions", sample.story_qa),
        ("(3) World-knowledge questions", sample.world_qa),
    ]:
        lines.append(f"== {title} ==")
        if title.startswith("(1)"):
            for i, p in enumerate(items, 1):
                lines.append(f"{i}. {p}")
        else:
            for item in items:
                lines.append(f"Q: {item.question}")
                lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    out.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible soccer-story combos:\n")
        for row in combos:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="yard", name="Milo", gender="boy", parent="father", trait="bold", fix="softball"),
            StoryParams(place="field", name="Luna", gender="girl", parent="mother", trait="curious", fix="cones"),
            StoryParams(place="gym", name="Piper", gender="girl", parent="father", trait="spirited", fix="softball"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
