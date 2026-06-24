#!/usr/bin/env python3
"""
A small comedy-leaning story world about a sudden tilt, a remembered flashback,
and a playful fix.

Premise:
- Someone wants to use or carry something at a place where a tilt causes trouble.
- A flashback explains why the character is unusually careful.
- The ending resolves with a funny, concrete change in the world state.
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


# -----------------------------
# World model
# -----------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
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
    place: str
    afford_tilt: bool = True
    comic_detail: str = ""


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    trigger: str
    punchline: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


# -----------------------------
# Registries
# -----------------------------
SETTINGS = {
    "hall": Setting(place="the school hall", comic_detail="The floor was so shiny it looked like it could skate by itself."),
    "kitchen": Setting(place="the kitchen", comic_detail="The counter leaned a little, as if it had a secret joke."),
    "shed": Setting(place="the garden shed", comic_detail="One shelf always slanted like it was trying to whisper to the floor."),
    "stage": Setting(place="the tiny stage", comic_detail="Even the spotlight seemed to wobble with excitement."),
}

ACTIONS = {
    "tilt_cake": Action(
        id="tilt_cake",
        verb="carry the cake",
        gerund="carrying the cake",
        risk="slide off balance",
        trigger="tilt",
        punchline="the frosting made a tiny worried hat on the side",
        tags={"cake", "tilt", "dessert"},
    ),
    "tilt_tray": Action(
        id="tilt_tray",
        verb="carry the tray",
        gerund="carrying the tray",
        risk="dump the cookies",
        trigger="tilt",
        punchline="the cookies started to look like they were forming a parade",
        tags={"cookies", "tilt", "snack"},
    ),
    "tilt_stack": Action(
        id="tilt_stack",
        verb="balance the books",
        gerund="balancing the books",
        risk="topple the stack",
        trigger="tilt",
        punchline="the top book slid sideways like it had remembered a secret dance step",
        tags={"books", "tilt", "library"},
    ),
}

PRIZES = {
    "cake": Prize(label="cake", phrase="a tall birthday cake", type="cake", region="hands"),
    "tray": Prize(label="tray", phrase="a silver tray of cookies", type="tray", region="hands", plural=True),
    "books": Prize(label="books", phrase="a wobbly stack of books", type="books", region="hands", plural=True),
}

FIXES = {
    "two_hands": Fix(id="two_hands", label="two hands", prep="use two hands on it first", tail="held the prize steady"),
    "flat_step": Fix(id="flat_step", label="a flat step", prep="set it on a flat step first", tail="gave the tilted thing a safer place to sit"),
    "helper": Fix(id="helper", label="a helper", prep="ask a helper to carry it", tail="made the load much less silly"),
}

GIRL_NAMES = ["Mia", "Lena", "Ivy", "Nora", "Tia", "Pia"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Max", "Eli", "Noah"]
TRAITS = ["careful", "bouncy", "sly", "cheerful", "curious", "silly"]


# -----------------------------
# Params
# -----------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# -----------------------------
# Reasonableness / ASP twin
# -----------------------------
def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region == "hands"


def select_fix(action: Action, prize: Prize) -> Optional[Fix]:
    if action.id == "tilt_cake":
        return FIXES["two_hands"]
    if action.id == "tilt_tray":
        return FIXES["flat_step"]
    if action.id == "tilt_stack":
        return FIXES["helper"]
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for aid, act in ACTIONS.items():
            for pid, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_fix(act, prize):
                    out.append((place, aid, pid))
    return out


def asp_facts() -> str:
    import asp  # lazy
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.afford_tilt:
            lines.append(asp.fact("affords", sid, "tilt"))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("risk", aid, act.trigger))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_label", fid, fix.label))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- risk(A, tilt), worn_on(P, hands).
has_fix(A,P) :- prize_at_risk(A,P), A = tilt_cake.
has_fix(A,P) :- prize_at_risk(A,P), A = tilt_tray.
has_fix(A,P) :- prize_at_risk(A,P), A = tilt_stack.
valid(Place,A,P) :- affords(Place, tilt), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


# -----------------------------
# Story helpers
# -----------------------------
def choose_name(gender: str) -> str:
    return random.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def intro_line(hero: Entity, parent: Entity, prize: Entity, action: Action) -> str:
    return (
        f"{hero.id} was a {hero.pronoun('subject')} little {hero.type} who loved {action.gerund}. "
        f"{hero.pronoun('possessive').capitalize()} {parent.label} had just brought home {prize.phrase}."
    )


def flashback_line(hero: Entity, prize: Entity) -> str:
    return (
        f"Then {hero.id} remembered a funny flashback: one time {prize.label} had tipped, "
        f"and the whole room had gone quiet for one dramatic second before everyone laughed."
    )


def conflict_line(hero: Entity, parent: Entity, action: Action, prize: Entity) -> str:
    return (
        f"One day at {hero.id}'s {hero.memes.get('place', 'place')}, {hero.id} wanted to {action.verb}, "
        f"but the floor gave a sneaky little {action.trigger}."
    )


def resolution_line(hero: Entity, parent: Entity, action: Action, prize: Entity, fix: Fix) -> str:
    return (
        f"{parent.label.capitalize()} smiled and said, 'Let's {fix.prep}.' "
        f"That worked better, so {hero.id} could keep {action.gerund}, {fix.tail}, and the {prize.label} stayed safe."
    )


def ending_image(hero: Entity, prize: Entity, action: Action) -> str:
    return (
        f"At the end, {hero.id} was laughing so hard {hero.pronoun('possessive')} cheeks almost wiggled. "
        f"The {prize.label} was steady, the tilt looked smaller, and even the room seemed to be grinning."
    )


# -----------------------------
# Generation
# -----------------------------
def tell(setting: Setting, action: Action, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={"joy": 1.0, "place": setting.place}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, plural=prize_cfg.plural))
    hero.memes["trait"] = trait
    hero.memes["action"] = action.id

    world.say(f"At {setting.place}, {setting.comic_detail}")
    world.say(intro_line(hero, parent, prize, action))
    world.para()
    world.say(f"{hero.id} liked {action.gerund} because it felt like a tiny adventure.")
    world.say(f"{hero.id} also liked how {action.punchline}.")
    world.para()
    world.say(f"But then came the {action.trigger}.")
    world.say(f"{hero.id} froze and had a flashback to the one time {prize.label} almost went tumbling.")
    world.say(f"That old memory made {hero.id} hold still instead of wobbling around like a noodle.")
    fix = select_fix(action, prize)
    if fix is None:
        raise StoryError("No reasonable fix exists for this story.")
    world.para()
    world.say(f"{parent.label.capitalize()} noticed the wobble and helped right away.")
    world.say(resolution_line(hero, parent, action, prize, fix))
    world.say(ending_image(hero, prize, action))

    world.facts.update(hero=hero, parent=parent, prize=prize, action=action, setting=setting, fix=fix, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    action: Action = f["action"]
    return [
        f"Write a short comedy story for a child about {hero.id}, a sudden tilt, and {prize.label}.",
        f"Tell a funny story where {hero.id} wants to {action.verb} but remembers a flashback before things wobble too much.",
        f"Write a lighthearted story that includes the word 'tilt' and ends with a safe, silly solution.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    prize: Entity = f["prize"]
    action: Action = f["action"]
    fix: Fix = f["fix"]
    parent: Entity = f["parent"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do when the floor started to tilt?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} remember in the flashback?",
            answer=f"{hero.id} remembered the funny time {prize.label} had almost tipped and made everyone laugh.",
        ),
        QAItem(
            question=f"How did {parent.label} help {hero.id} at the end?",
            answer=f"{parent.label.capitalize()} suggested {fix.label}, which helped keep the {prize.label} safe.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tilt?",
            answer="A tilt is a lean or slant, like when something is not sitting flat and wants to slide to one side.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier.",
        ),
        QAItem(
            question="Why can laughing make a story feel funny?",
            answer="Laughing can make a story feel funny because the characters notice a silly mistake and react in a cheerful way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# -----------------------------
# Params / CLI
# -----------------------------
CURATED = [
    StoryParams(place="hall", action="tilt_cake", prize="cake", name="Mia", gender="girl", parent="mother", trait="careful"),
    StoryParams(place="kitchen", action="tilt_tray", prize="tray", name="Owen", gender="boy", parent="father", trait="silly"),
    StoryParams(place="stage", action="tilt_stack", prize="books", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy story world about tilt and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or choose_name(gender)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen = set()
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
