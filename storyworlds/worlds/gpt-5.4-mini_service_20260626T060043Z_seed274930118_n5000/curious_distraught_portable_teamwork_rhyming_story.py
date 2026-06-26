#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/curious_distraught_portable_teamwork_rhyming_story.py
================================================================================================

A tiny standalone storyworld for a rhyming teamwork tale.

Premise:
- A curious child finds a portable parade drum.
- The drum slips into a muddy patch and the child grows distraught.
- Friends use teamwork to lift it free and carry it home.

This world is intentionally small and constraint-checked: only reasonable
story/gear pairings are allowed, and the prose is driven by a simulated world
model with meters (physical state) and memes (emotional state).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entities and world state
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    portable: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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


@dataclass
class Setting:
    place: str
    indoors: bool = False
    mud: bool = False
    puddle: bool = False


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    region: str
    portable: bool = True
    protects: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Helper:
    id: str
    label: str
    courage: str
    skill: str


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


# ---------------------------------------------------------------------------
# Story knobs
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    prize: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "field": Setting(place="the field", mud=True, puddle=True),
    "dock": Setting(place="the dock", mud=False, puddle=False),
    "yard": Setting(place="the yard", mud=True, puddle=True),
    "hall": Setting(place="the hall", indoors=True, mud=False, puddle=False),
}

PRIZES = {
    "drum": Item(
        id="drum",
        label="drum",
        phrase="a small portable parade drum",
        region="hands",
        portable=True,
        protects=set(),
    ),
    "lantern": Item(
        id="lantern",
        label="lantern",
        phrase="a bright portable lantern",
        region="hands",
        portable=True,
        protects={"dark"},
    ),
    "box": Item(
        id="box",
        label="box",
        phrase="a tiny portable song box",
        region="hands",
        portable=True,
        protects=set(),
    ),
}

HELPERS = {
    "mouse": Helper(id="mouse", label="mouse", courage="brave", skill="tiny hands"),
    "duck": Helper(id="duck", label="duck", courage="cheery", skill="steady feet"),
    "goat": Helper(id="goat", label="goat", courage="bold", skill="strong legs"),
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Ava", "Nora"]
BOY_NAMES = ["Leo", "Finn", "Max", "Theo", "Ben"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.
#show valid_story/4.

valid(Setting, Prize, Helper) :-
    setting(Setting),
    prize(Prize),
    helper(Helper),
    portable(Prize),
    teamwork_ok(Setting, Prize, Helper).

valid_story(Setting, Prize, Helper, Gender) :-
    valid(Setting, Prize, Helper),
    gender(Gender).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        if s.mud:
            lines.append(asp.fact("muddy", sid))
        if s.puddle:
            lines.append(asp.fact("puddle", sid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.portable:
            lines.append(asp.fact("portable", pid))
        for prot in sorted(p.protects):
            lines.append(asp.fact("protects", pid, prot))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("gender", g))
    for sid, s in SETTINGS.items():
        for pid, p in PRIZES.items():
            if p.portable and (s.mud or s.puddle or s.indoors):
                for hid in HELPERS:
                    lines.append(asp.fact("teamwork_ok", sid, pid, hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for pid, prize in PRIZES.items():
            if not prize.portable:
                continue
            if sid == "dock" and pid == "box":
                combos.append((sid, pid, "goat"))
            elif sid in {"field", "yard", "hall"}:
                for hid in HELPERS:
                    combos.append((sid, pid, hid))
    return combos


def explain_rejection(setting: Setting, prize: Item) -> str:
    return (
        f"(No story: {prize.phrase} is not a good fit for {setting.place}. "
        f"Try a portable item in a place where teamwork can actually matter.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def rhyme(a: str, b: str) -> str:
    return f"{a} {b}"


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a curious child with a quick little grin."


def helper_line(helper: Helper) -> str:
    return {
        "mouse": "A mouse came quick with tiny paws and a thoughtful blink.",
        "duck": "A duck came waddling by, with a quack and a wink.",
        "goat": "A goat came clopping over, strong and keen.",
    }[helper.id]


def setting_line(setting: Setting) -> str:
    return {
        "field": "The field was green, but muddy in spots.",
        "dock": "The dock was wide, with boards and soft salt dots.",
        "yard": "The yard was bright, with a splashy little plot.",
        "hall": "The hall was calm, with a shiny floor and a quiet lot.",
    }[next(k for k, v in SETTINGS.items() if v is setting)]


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "distraught": 0.0, "joy": 0.0, "teamwork": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="helper",
        label=params.helper,
        meters={"steps": 0.0},
        memes={"helpfulness": 1.0, "joy": 0.0},
    ))
    prize_cfg = PRIZES[params.prize]
    prize = world.add(Entity(
        id=prize_cfg.id,
        kind="thing",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        portable=prize_cfg.portable,
        meters={"mud": 0.0, "carried": 0.0},
        memes={"shine": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, prize=prize, prize_cfg=prize_cfg)
    return world


def simulate(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    prize: Entity = world.facts["prize"]
    setting = world.setting

    world.say(hero_intro(hero))
    world.say(f"{hero.id} spied {prize.phrase} and gave it a curious little spin.")
    world.say(setting_line(setting))
    world.para()

    hero.meters["steps"] += 1
    prize.carried_by = hero.id
    prize.meters["carried"] += 1
    world.say(
        f"{hero.id} started to skip and grin, like a tune with a twirl, "
        f"while {prize.label} went bobbing along in the whirl."
    )

    if setting.mud or setting.puddle:
        world.para()
        prize.meters["mud"] += 1
        hero.memes["distraught"] += 1
        hero.memes["curiosity"] = 0.0
        world.say(
            f"Then the path turned slick, and a muddy splash flew fast; "
            f"{prize.label} got stuck, and {hero.id}'s happy breath did not last."
        )
        world.say(
            f"{hero.id} looked down and felt distraught, with a wobble in the chest; "
            f"the pretty portable prize was no longer at its best."
        )

    world.para()
    world.say(helper_line(helper))
    hero.memes["teamwork"] += 1
    helper.memes["joy"] += 1
    prize.carried_by = None
    prize.meters["mud"] = max(0.0, prize.meters["mud"] - 1.0)
    prize.meters["carried"] += 1
    world.say(
        f"{helper.label.capitalize()} said, \"Let's do this together, with a lift and a cheer.\" "
        f"So they counted to three and moved in near."
    )
    world.say(
        f"One took the left and one took the right, "
        f"and the portable prize rose up light."
    )

    world.para()
    hero.memes["distraught"] = 0.0
    hero.memes["joy"] += 1
    prize.meters["mud"] = 0.0
    prize.carried_by = hero.id
    world.say(
        f"At last, the prize was clean and snug, and the worry was through; "
        f"{hero.id} felt bright, and {helper.label} did too."
    )
    world.say(
        f"They walked back home side by side, in a happy little line, "
        f"with teamwork in their steps and a finish that did rhyme."
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize_cfg"]
    return [
        f'Write a short rhyming story for a child named {hero.id} who finds {prize.phrase} and learns teamwork.',
        f'Tell a gentle story where {hero.id} feels curious, then distraught, then happy again with help from {helper.label}.',
        f'Create a tiny rhyming tale about a portable prize, a muddy mishap, and a friendly team fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize = f["hero"], f["helper"], f["prize"]
    return [
        QAItem(
            question=f"What did {hero.id} first feel when {hero.id} saw the portable {prize.label}?",
            answer=f"{hero.id} felt curious and wanted to look closer at the portable {prize.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} become distraught later in the story?",
            answer=f"{hero.id} became distraught because the portable {prize.label} got stuck in the muddy path.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.label} fix the problem?",
            answer=f"They used teamwork, lifted together, and carried the portable {prize.label} back to safety.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does portable mean?",
            answer="Portable means something is easy to carry from one place to another.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do a job.",
        ),
    ]
    if world.setting.mud:
        out.append(
            QAItem(
                question="Why can mud make things messy?",
                answer="Mud sticks to things and can make them dirty and slippery.",
            )
        )
    return out


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
# CLI helpers
# ---------------------------------------------------------------------------
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
        if e.portable:
            bits.append("portable=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming teamwork storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.prize:
        combos = [c for c in combos if c[1] == args.prize]
    if args.helper:
        combos = [c for c in combos if c[2] == args.helper]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, prize, helper = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, prize=prize, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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


def asp_program_full(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program_full("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, prize, helper) combos "
              f"({len(stories)} with gender):\n")
        for setting, prize, helper in triples:
            genders = sorted(g for (s, p, h, g) in stories if (s, p, h) == (setting, prize, helper))
            print(f"  {setting:6} {prize:8} {helper:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for sid in SETTINGS:
            for pid in PRIZES:
                for hid in HELPERS:
                    if (sid, pid, hid) in valid_combos():
                        params = StoryParams(setting=sid, prize=pid, name="Mia", gender="girl", helper=hid)
                        samples.append(generate(params))
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
