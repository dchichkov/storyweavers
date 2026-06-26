#!/usr/bin/env python3
"""
A tiny bedtime storyworld about diabetes, a leg-dim worry, and reconciliation.

The child starts tired and unsure at bedtime. A parent notices the leg-dim
feeling, checks sugar, and helps with a snack, a calm lamp, and a gentle
apology. The ending proves the room is peaceful again.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    child_name: str
    child_type: str
    parent_type: str
    bedtime_snack: str
    seed: Optional[int] = None


@dataclass
class Setting:
    place: str = "the soft little bedroom"
    time: str = "bedtime"


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
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting()

SNACKS = {
    "apple_slices": "apple slices and a cup of water",
    "cracker": "a few crackers and a warm drink",
    "yogurt": "a small bowl of yogurt with berries",
}

SNACK_FACTS = {
    "apple_slices": ("fruity", "gentle"),
    "cracker": ("plain", "calm"),
    "yogurt": ("cool", "soft"),
}

GENDER_NAMES = {
    "girl": ["Mia", "Nora", "Lily", "Ava", "Zoe"],
    "boy": ["Ben", "Leo", "Theo", "Max", "Finn"],
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_story(params: StoryParams) -> bool:
    return params.child_type in {"girl", "boy"} and params.parent_type in {"mother", "father"} and params.bedtime_snack in SNACKS


def explain_invalid(params: StoryParams) -> str:
    return "The bedtime story needs a child, a parent, and a gentle snack that fits the reconciliation scene."


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def child_intro(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} was a small {child.type} who loved the hush of bedtime and "
        f"the soft glow of the lamp."
    )


def diabetes_setup(world: World, child: Entity, parent: Entity) -> None:
    child.memes["worry"] = 1.0
    child.meters["diabetes"] = 1.0
    world.say(
        f"{child.id} had diabetes, so {parent.label} always kept a careful eye on "
        f"the evening routine."
    )


def leg_dim_signal(world: World, child: Entity) -> None:
    child.meters["leg_dim"] = 1.0
    child.memes["uneasy"] = 1.0
    world.say(
        f"That night, {child.id} rubbed a leg-dim spot and whispered that it felt "
        f"odd and sleepy."
    )


def tension(world: World, child: Entity, parent: Entity) -> None:
    child.memes["upset"] = 1.0
    parent.memes["concern"] = 1.0
    world.say(
        f"{parent.label} knelt beside the bed and asked to check on {child.id}, "
        f"but {child.id} frowned and turned away."
    )
    world.say(
        f"For a tiny moment, the room felt prickly, as if the bedtime moon had gone behind a cloud."
    )


def reconciliation(world: World, child: Entity, parent: Entity, snack: Entity) -> None:
    child.memes["upset"] = 0.0
    child.memes["peace"] = 1.0
    parent.memes["concern"] = 0.0
    parent.memes["tenderness"] = 1.0
    world.say(
        f"Then {parent.label} spoke softly: 'I'm not here to hurry you. I'm here to help.'"
    )
    world.say(
        f"{parent.label} brought {snack.phrase}, and {child.id} let the check happen."
    )
    world.say(
        f"After a few careful breaths, {child.id} leaned into {parent.label}'s shoulder, "
        f"and the two of them made up."
    )


def ending_image(world: World, child: Entity, parent: Entity, snack: Entity) -> None:
    world.say(
        f"Before long, {child.id} was tucked in again, the lamp glowed like warm honey, "
        f"and the {snack.label} sat finished on the little table while {parent.label} "
        f"smiled at the quiet room."
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(
        Entity(
            id=params.child_name,
            kind="character",
            type=params.child_type,
            label=params.child_name,
            meters={"diabetes": 1.0, "leg_dim": 0.0},
            memes={"worry": 0.0, "uneasy": 0.0, "upset": 0.0, "peace": 0.0},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=params.parent_type,
            label="mom" if params.parent_type == "mother" else "dad",
            memes={"concern": 0.0, "tenderness": 0.0},
        )
    )
    snack = world.add(
        Entity(
            id="Snack",
            kind="thing",
            type="snack",
            label="snack",
            phrase=SNACKS[params.bedtime_snack],
            caregiver=parent.id,
        )
    )

    child_intro(world, child)
    diabetes_setup(world, child, parent)
    world.para()
    leg_dim_signal(world, child)
    tension(world, child, parent)
    world.para()
    reconciliation(world, child, parent, snack)
    ending_image(world, child, parent, snack)

    world.facts.update(
        child=child,
        parent=parent,
        snack=snack,
        params=params,
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
parent(P) :- parent_type(P).
snack(S) :- snack_kind(S).

valid_story(C,P,S) :- child(C), parent(P), snack(S).
"""


def asp_facts() -> str:
    import asp  # lazy import
    lines: list[str] = []
    for gender in GENDER_NAMES:
        for name in GENDER_NAMES[gender]:
            lines.append(asp.fact("child_name", name))
    lines.append(asp.fact("parent_type", "mother"))
    lines.append(asp.fact("parent_type", "father"))
    for snack in SNACKS:
        lines.append(asp.fact("snack_kind", snack))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp  # lazy import

    model = asp.one_model(asp_program("#show valid_story/3."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = {
        (name, parent, snack)
        for gender in GENDER_NAMES
        for name in GENDER_NAMES[gender]
        for parent in ("mother", "father")
        for snack in SNACKS
    }
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    if asp_set - py_set:
        print("only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("only in python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    params: StoryParams = f["params"]
    return [
        f'Write a gentle bedtime story about diabetes, a leg-dim worry, and reconciliation.',
        f"Tell a short story where {child.id} feels a leg-dim discomfort at bedtime and {parent.label} helps with {SNACKS[params.bedtime_snack]}.",
        f'Write a soft child-friendly story that includes the words "diabetes" and "leg-dim" and ends peacefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    snack: Entity = f["snack"]
    params: StoryParams = f["params"]
    return [
        QAItem(
            question=f"What was special about {child.id} at bedtime?",
            answer=f"{child.id} had diabetes, so bedtime needed careful, gentle attention.",
        ),
        QAItem(
            question=f"What did {child.id} notice in the story?",
            answer=f"{child.id} noticed a leg-dim feeling and felt uneasy for a moment.",
        ),
        QAItem(
            question=f"How did {parent.label} help {child.id} feel better?",
            answer=f"{parent.label} stayed calm, listened, and brought {SNACKS[params.bedtime_snack]} so they could make up together.",
        ),
        QAItem(
            question=f"What happened after the reconciliation?",
            answer=f"{child.id} tucked back in peacefully while the snack sat finished on the table and the room grew quiet again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is diabetes?",
            answer="Diabetes is a condition that means a person's body needs careful help with sugar and energy.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset and become friendly again.",
        ),
        QAItem(
            question="Why is bedtime often calm in a story?",
            answer="Bedtime is often calm because the lights are soft, voices are gentle, and everyone is getting ready to rest.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: diabetes, leg-dim, and reconciliation.")
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
    ap.add_argument("--bedtime-snack", choices=sorted(SNACKS))
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
    child_type = args.child_type or rng.choice(["girl", "boy"])
    parent_type = args.parent_type or rng.choice(["mother", "father"])
    bedtime_snack = args.bedtime_snack or rng.choice(sorted(SNACKS))
    child_name = args.child_name or rng.choice(GENDER_NAMES[child_type])
    params = StoryParams(
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        bedtime_snack=bedtime_snack,
    )
    if not valid_story(params):
        raise StoryError(explain_invalid(params))
    return params


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.asp:
        import asp  # lazy import
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for combo in combos[:20]:
            print(" ", combo)
        return

    samples: list[StorySample] = []
    if args.all:
        for gender, names in GENDER_NAMES.items():
            for name in names[:1]:
                for parent in ("mother", "father"):
                    for snack in SNACKS:
                        params = StoryParams(name, gender, parent, snack)
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
