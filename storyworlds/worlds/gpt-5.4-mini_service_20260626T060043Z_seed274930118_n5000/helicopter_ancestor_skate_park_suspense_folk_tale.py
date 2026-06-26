#!/usr/bin/env python3
"""
storyworlds/worlds/helicopter_ancestor_skate_park_suspense_folk_tale.py
========================================================================

A small, self-contained story world in a folk-tale style.

Premise:
- A child in a skate park wants to do a daring trick.
- An ancestor's warning and a little helicopter shape the suspense.
- The story turns on a practical choice: wait for help, or rush and tumble.

This world is intentionally narrow: it generates a few strong, complete
stories rather than many weak ones.
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
# Domain model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    wears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def say(self, text: str) -> str:
        return text


@dataclass
class Setting:
    place: str = "the skate park"
    affords: set[str] = field(default_factory=lambda: {"jump", "ramp"})


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    hazard: str
    meter: str
    threshold: float = 1.0


@dataclass
class Talisman:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    action: str
    talisman: str
    name: str
    gender: str
    ancestor: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

ACTIONS = {
    "ramp": Action(
        id="ramp",
        verb="ride the steep ramp",
        gerund="riding the steep ramp",
        risk="a hard fall",
        hazard="tumble",
        meter="shake",
    ),
    "jump": Action(
        id="jump",
        verb="jump the gap",
        gerund="jumping the gap",
        risk="a bad spill",
        hazard="spill",
        meter="wobble",
    ),
}

TALISMANS = {
    "helicopter": Talisman(
        id="helicopter",
        label="a little helicopter charm",
        phrase="a little helicopter charm on a string",
        helps={"calm", "guide"},
    ),
    "bell": Talisman(
        id="bell",
        label="an old silver bell",
        phrase="an old silver bell tied with blue thread",
        helps={"calm"},
    ),
}

NAMES_GIRL = ["Mina", "Lena", "Nora", "Ivy", "Tess", "Maya"]
NAMES_BOY = ["Eli", "Noah", "Finn", "Theo", "Levi", "Owen"]
TRAITS = ["brave", "curious", "small", "quick", "cheerful"]


# ---------------------------------------------------------------------------
# Folk-tale simulation
# ---------------------------------------------------------------------------
def _meter(entity: Entity, key: str) -> float:
    return entity.meters.get(key, 0.0)


def _mem(entity: Entity, key: str) -> float:
    return entity.memes.get(key, 0.0)


def _set_meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = value


def _add_meter(entity: Entity, key: str, value: float) -> None:
    entity.meters[key] = _meter(entity, key) + value


def _add_mem(entity: Entity, key: str, value: float) -> None:
    entity.memes[key] = _mem(entity, key) + value


def predict(world: World, child: Entity, action: Action, talisman: Talisman) -> dict[str, object]:
    sim = world.copy()
    c = sim.get(child.id)
    _add_meter(c, action.meter, 1.0)
    if talisman.id not in c.owner and talisman.id in talisman.helps:
        pass
    tumble = _meter(c, "balance") < 0.5
    return {"tumble": tumble}


def enforce_suspense(world: World, child: Entity, ancestor: Entity, action: Action) -> None:
    _add_mem(child, "doubt", 1.0)
    _add_mem(child, "longing", 1.0)
    world.say(
        f"{child.id} wanted to {action.verb}, but the boards whispered of {action.risk}."
    )
    world.say(
        f"{ancestor.label} lifted a hand and said, "
        f'"Haste makes the wheel slip, and the stone remembers every fall."'
    )


def apply_action(world: World, child: Entity, action: Action, talisman: Talisman) -> None:
    _add_meter(child, action.meter, 1.0)
    _add_meter(child, "balance", 0.4)
    if talisman.id == "helicopter":
        _add_mem(child, "calm", 1.0)


def resolve(world: World, child: Entity, ancestor: Entity, action: Action, talisman: Talisman) -> None:
    _add_mem(child, "hope", 1.0)
    _add_mem(child, "trust", 1.0)
    _set_meter(child, "balance", 1.0)
    world.say(
        f"Then {ancestor.label} showed {child.id} the {talisman.label}, and the little helicopter charm "
        f"spun in the breeze like a bright eye."
    )
    world.say(
        f"{child.id} breathed slow, took the board again, and {action.gerund} with careful feet."
    )


def tell(setting: Setting, action: Action, talisman: Talisman, name: str, gender: str, ancestor_role: str) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        label=name,
        meters={"balance": 1.0},
        memes={"curiosity": 1.0},
    ))
    ancestor = world.add(Entity(
        id="Ancestor",
        kind="character",
        type=ancestor_role,
        label=f"the {ancestor_role}",
        memes={"worry": 1.0, "care": 1.0},
    ))
    charm = world.add(Entity(
        id=talisman.id,
        type="thing",
        label=talisman.label,
        phrase=talisman.phrase,
        owner=child.id,
    ))
    child.owner = child.id
    world.facts = {
        "child": child,
        "ancestor": ancestor,
        "charm": charm,
        "action": action,
        "talisman": talisman,
        "setting": setting,
    }

    world.say(
        f"At {setting.place}, there lived a little {gender} named {name}, who loved the sound of wheels on stone."
    )
    world.say(
        f"{name} kept {talisman.phrase} close, for it had once belonged to {ancestor.label}, "
        f"who had known many winds and many roads."
    )
    world.para()
    world.say(
        f"One bright day, {name} looked at the ramp and the gap beyond it, and wished to {action.verb}."
    )
    enforce_suspense(world, child, ancestor, action)
    world.para()

    if predict(world, child, action, talisman)["tumble"]:
        world.say(f"For a moment, the skate park grew still, as if it waited to see whether {name} would fall.")
        resolve(world, child, ancestor, action, talisman)
        world.say(
            f"So {name} tried again, and this time the board sang true; the little helicopter charm turned once more, "
            f"and the stone kept the secret of a safe landing."
        )
        _add_mem(child, "joy", 1.0)
        world.facts["resolved"] = True
    else:
        world.say(f"But the path looked steady, and {name} listened, so the wheel rolled on without fear.")
        world.say(f"In the end, {name} still {action.gerund}, and {ancestor.label} smiled at the careful choice.")
        world.facts["resolved"] = True

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    action = f["action"]
    talisman = f["talisman"]
    return [
        f'Write a short folk tale set at {SETTING.place} about a child named {child.id} who wants to {action.verb}.',
        f"Tell a suspenseful story where {child.id} and {f['ancestor'].label} use {talisman.label} to make a safe choice.",
        f'Write a gentle story with a helicopter charm, an ancestor, and a careful ending at the skate park.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    ancestor = f["ancestor"]
    action = f["action"]
    talisman = f["talisman"]
    return [
        QAItem(
            question=f"Who wanted to {action.verb} at {SETTING.place}?",
            answer=f"{child.id} wanted to {action.verb} at {SETTING.place}, even though the move looked risky.",
        ),
        QAItem(
            question=f"Why did {ancestor.label} warn {child.id}?",
            answer=f"{ancestor.label} warned {child.id} because the ramp could lead to {action.risk}, and the day felt suspenseful.",
        ),
        QAItem(
            question=f"What helped {child.id} stay calm and try again?",
            answer=f"{talisman.label} helped {child.id} stay calm, and the little helicopter charm gave the story its hopeful turn.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended with {child.id} making a careful try at {action.gerund}, while {ancestor.label} watched with relief."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a helicopter?",
            answer="A helicopter is an aircraft that can rise and hover in one place because its top blades spin fast.",
        ),
        QAItem(
            question="What is an ancestor?",
            answer="An ancestor is a family member from an earlier generation, like a grandparent or great-grandparent.",
        ),
        QAItem(
            question="What is a skate park?",
            answer="A skate park is a place with ramps, rails, and smooth ground where people ride skateboards and scooters.",
        ),
        QAItem(
            question="Why can suspense make a story exciting?",
            answer="Suspense makes a story exciting because the reader wonders what will happen next and worries a little before the ending.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old-style story that is often simple, wise, and a little magical or mysterious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_risk(A) :- action(A), hazard(A, H), H = "tumble".
safe_fix(T) :- talisman(T), helps(T, calm).
valid_story(A, T) :- child_risk(A), safe_fix(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = [asp.fact("setting", "skate_park")]
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("hazard", aid, a.hazard))
    for tid, t in TALISMANS.items():
        lines.append(asp.fact("talisman", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def python_valid() -> list[tuple]:
    out = []
    for a in ACTIONS:
        for t in TALISMANS:
            if True:
                out.append((a, t))
    return sorted(out)


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    py_set = set(python_valid())
    if clingo_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python gates.")
    if clingo_set - py_set:
        print("Only in ASP:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("Only in Python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful folk tale at a skate park.")
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--talisman", choices=sorted(TALISMANS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--ancestor", choices=["grandmother", "grandfather", "ancestor"])
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
    action = args.action or rng.choice(list(ACTIONS))
    talisman = args.talisman or rng.choice(list(TALISMANS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    ancestor = args.ancestor or rng.choice(["grandmother", "grandfather"])
    return StoryParams(action=action, talisman=talisman, name=name, gender=gender, ancestor=ancestor)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, ACTIONS[params.action], TALISMANS[params.talisman], params.name, params.gender, params.ancestor)
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


CURATED = [
    StoryParams(action="ramp", talisman="helicopter", name="Mina", gender="girl", ancestor="grandmother"),
    StoryParams(action="jump", talisman="helicopter", name="Eli", gender="boy", ancestor="grandfather"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
