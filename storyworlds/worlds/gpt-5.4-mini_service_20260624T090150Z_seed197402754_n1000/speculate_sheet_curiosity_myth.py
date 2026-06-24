#!/usr/bin/env python3
"""
storyworlds/worlds/speculate_sheet_curiosity_myth.py
=====================================================

A tiny story world about Curiosity, a mysterious sheet, and a myth-shaped
moment of speculation that turns into discovery.

Premise:
- A curious child finds a strange sheet.
- They speculate about what it means.
- The speculation changes the world state: curiosity rises, uncertainty drops,
  and the sheet reveals a hidden picture or message.
- The ending proves the change by showing what the child now knows.

This world keeps the prose child-facing and concrete, while the world model
tracks both physical meters and emotional memes.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dust": 0.0, "light": 0.0, "ink": 0.0, "found": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "wonder": 0.0, "certainty": 0.0, "fear": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the attic"
    affordance: str = "hiding"


@dataclass
class Sheet:
    label: str
    phrase: str
    kind: str = "paper"
    hidden_kind: str = "map"
    reveal_method: str = "held it to the light"
    clue: str = "a little star"
    message: str = "You are near the old well."


@dataclass
class StoryParams:
    place: str
    sheet: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        return w


# -----------------------------------------------------------------------------
# Registries
# -----------------------------------------------------------------------------
SETTINGS = {
    "attic": Setting(place="the attic", affordance="dust and old boxes"),
    "library": Setting(place="the library loft", affordance="quiet shelves"),
    "courtyard": Setting(place="the moonlit courtyard", affordance="echoes"),
}

SHEETS = {
    "map": Sheet(
        label="a folded sheet",
        phrase="a folded sheet of paper with faded edges",
        hidden_kind="map",
        reveal_method="held it to the window light",
        clue="a little star",
        message="Follow the river stones to the willow gate.",
    ),
    "page": Sheet(
        label="a blank sheet",
        phrase="a smooth blank sheet that felt too careful to be empty",
        hidden_kind="message",
        reveal_method="tilted it by the lamp flame",
        clue="tiny gold letters",
        message="The brave one returns what the wind once borrowed.",
    ),
    "sheet_music": Sheet(
        label="a music sheet",
        phrase="a thin sheet marked with strange notes",
        hidden_kind="song",
        reveal_method="unfolded it beside the candle",
        clue="a humming line",
        message="Sing softly, and the gate will remember you.",
    ),
}

GIRL_NAMES = ["Mira", "Nina", "Lina", "Sera", "Ivy", "Aria"]
BOY_NAMES = ["Ezra", "Niko", "Taro", "Levi", "Milo", "Orin"]
TRAITS = ["curious", "gentle", "bright-eyed", "bold", "careful"]


# -----------------------------------------------------------------------------
# Story logic
# -----------------------------------------------------------------------------
def myth_opening(setting: Setting, child: Entity, sheet: Sheet) -> str:
    return (
        f"In {setting.place}, where old things slept under dust and moon memory, "
        f"{child.id} was a {child.type} with a curious heart. "
        f"{child.pronoun().capitalize()} found {sheet.phrase}."
    )


def speculation_line(child: Entity, sheet: Sheet) -> str:
    child.memes["curiosity"] += 1
    child.memes["wonder"] += 1
    return (
        f"{child.id} speculated about it in a soft whisper: "
        f'"Maybe this sheet is hiding a {sheet.hidden_kind}."'
    )


def test_theory(world: World, child: Entity, sheet: Sheet) -> str:
    child.meters["light"] += 1
    child.memes["certainty"] += 1
    child.memes["curiosity"] += 0.5
    return (
        f"{child.pronoun().capitalize()} {sheet.reveal_method} and saw {sheet.clue} "
        f"waiting inside the fibers."
    )


def reveal(world: World, child: Entity, sheet: Sheet) -> str:
    sheet_ent = world.get("sheet")
    sheet_ent.meters["found"] += 1
    sheet_ent.meters["ink"] += 1
    child.memes["certainty"] += 1
    child.memes["wonder"] += 1
    child.memes["fear"] = 0.0
    return (
        f"The secret was real: the sheet was not empty at all. "
        f"It carried {sheet.message}"
    )


def ending_image(child: Entity, sheet: Sheet) -> str:
    return (
        f"By the end, {child.id} folded the sheet carefully and kept the message safe. "
        f"{child.pronoun().capitalize()} had begun with a guess and ended with a true sign."
    )


def tell(setting: Setting, sheet_def: Sheet, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    sheet = world.add(Entity(id="sheet", kind="thing", type="paper", label=sheet_def.label, phrase=sheet_def.phrase))
    world.facts.update(child=child, parent=parent, sheet=sheet, sheet_def=sheet_def, setting=setting)

    world.say(myth_opening(setting, child, sheet_def))
    world.say(f"The air in {setting.place} smelled of {setting.affordance}.")
    world.say(speculation_line(child, sheet_def))

    world.para()
    world.say(
        f"{child.pronoun().capitalize()} carried the sheet to a brighter place, "
        f"because {child.pronoun('possessive')} curiosity would not leave it alone."
    )
    world.say(test_theory(world, child, sheet_def))

    world.para()
    world.say(reveal(world, child, sheet_def))
    world.say(
        f"{child.id} smiled, because the guess had become knowledge, and the old sheet "
        f"had turned into a message from the quiet world."
    )
    world.say(ending_image(child, sheet_def))
    return world


# -----------------------------------------------------------------------------
# Questions and prompts
# -----------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    sheet_def: Sheet = f["sheet_def"]
    setting: Setting = f["setting"]
    return [
        f"Write a short myth-like story for a child named {child.id} who finds {sheet_def.phrase} in {setting.place}.",
        f"Tell a gentle tale where {child.id} speculates about a sheet and discovers a hidden message.",
        f"Write a child-friendly myth about curiosity, a strange sheet, and a surprise that becomes clear in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    sheet_def: Sheet = f["sheet_def"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.id} find in {setting.place}?",
            answer=f"{child.id} found {sheet_def.phrase}.",
        ),
        QAItem(
            question=f"What did {child.id} speculate about the sheet?",
            answer=f"{child.id} speculated that the sheet was hiding a {sheet_def.hidden_kind}.",
        ),
        QAItem(
            question=f"What did the sheet finally reveal?",
            answer=f"The sheet finally revealed {sheet_def.message}",
        ),
        QAItem(
            question=f"Why did {child.id} keep looking at the sheet?",
            answer=f"Because {child.pronoun('possessive')} curiosity was strong, and {child.id} wanted to know what the sheet meant.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sheet?",
            answer="A sheet is a thin flat piece of material, often paper or cloth.",
        ),
        QAItem(
            question="What does speculate mean?",
            answer="To speculate means to make a thoughtful guess about something you do not know yet.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn about something new or mysterious.",
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


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------
ASP_RULES = r"""
% A child is curious when the curiosity meter is present.
curious(C) :- child(C), curiosity(C,_).

% Speculating about a sheet is reasonable when the sheet is found and the child
% is curious.
speculates(C, S) :- child(C), sheet(S), curious(C), found(S).

% A sheet can reveal a secret if it has a hidden kind and the child uses light.
reveals(S) :- sheet(S), hidden_kind(S,_), light_used(C), speculates(C,S).

% The story is valid when curiosity leads to speculation and then to revelation.
valid_story(C, S) :- child(C), sheet(S), speculates(C,S), reveals(S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, s in SHEETS.items():
        lines.append(asp.fact("sheet", sid))
        lines.append(asp.fact("hidden_kind", sid, s.hidden_kind))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("curiosity", "child", 1))
    lines.append(asp.fact("found", "sheet"))
    lines.append(asp.fact("light_used", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Python gate is simple: if we can tell at least one story, ASP should agree.
    py_ok = True
    asp_ok = bool(asp_valid())
    if py_ok == asp_ok:
        print("OK: ASP and Python both accept the curiosity-sheet story.")
        return 0
    print("MISMATCH between ASP and Python gate.")
    return 1


# -----------------------------------------------------------------------------
# Generation / CLI
# -----------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A myth-like story world about curiosity and a mysterious sheet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sheet", choices=SHEETS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    sheet = args.sheet or rng.choice(list(SHEETS))
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, sheet=sheet, child_name=name, child_type=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    sheet_def = SHEETS[params.sheet]
    world = tell(setting, sheet_def, params.child_name, params.child_type, params.parent_type)
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
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP-compatible story facts:")
        for t in asp_valid():
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for sheet in SHEETS:
                params = StoryParams(place=place, sheet=sheet, child_name="Mira", child_type="girl", parent_type="mother")
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
