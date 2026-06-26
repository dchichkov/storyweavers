#!/usr/bin/env python3
"""
storyworlds/worlds/cent_mace_problem_solving_detective_story.py
===============================================================

A tiny detective-story world where a child sleuth solves small mysteries with
careful thinking, clues, and a little help from a heavy mace-shaped object.

Seed words: cent, mace
Style: Detective Story
Feature: Problem Solving
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
    setting_detail: str


@dataclass
class Mystery:
    id: str
    missing: str
    object_label: str
    culprit_place: str
    clue: str
    method: str
    solution: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "office": Setting(
        place="the little detective office",
        setting_detail="A desk, a lamp, and a magnifying glass sat ready for clues.",
    ),
    "museum": Setting(
        place="the quiet museum hallway",
        setting_detail="The hallway was still, with polished floors and framed pictures on the wall.",
    ),
    "shop": Setting(
        place="the corner shop",
        setting_detail="The counter was neat, and jars and boxes waited in tidy rows.",
    ),
}

MYSTERIES = {
    "lost_cent": Mystery(
        id="lost_cent",
        missing="one cent",
        object_label="cent",
        culprit_place="under the heavy mace",
        clue="a tiny copper glint",
        method="lift the mace carefully with both hands",
        solution="the cent was hiding under the mace",
        tags={"cent", "mace", "money"},
    ),
    "sticky_cent": Mystery(
        id="sticky_cent",
        missing="a shiny cent",
        object_label="cent",
        culprit_place="inside a jam lid near the mace",
        clue="a sweet sticky ring",
        method="slide the lid aside and check the tray",
        solution="the cent had stuck near the jam lid",
        tags={"cent", "mace", "money"},
    ),
}

GIRL_NAMES = ["Mina", "June", "Ada", "Nora", "Lila"]
BOY_NAMES = ["Theo", "Eli", "Noah", "Finn", "Max"]
HELPERS = ["cat", "dog", "grandpa", "friend"]


@dataclass
class StoryState:
    detective: Entity
    helper: Entity
    missing: Entity
    mace: Entity
    clue_seen: bool = False
    solved: bool = False
    worry: float = 0.0
    relief: float = 0.0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child detective solves a small mystery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("has_tag", m.id, "cent"))
        lines.append(asp.fact("has_tag", m.id, "mace"))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", m.id, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M), has_tag(M, cent), has_tag(M, mace).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in valid_combos():
            raise StoryError("That setting and mystery do not make a valid detective case.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid detective story matches those options.")
    setting, mystery = rng.choice(sorted(combos))
    mystery_cfg = MYSTERIES[mystery]
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def build_world(params: StoryParams) -> tuple[World, StoryState]:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    detective = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper))
    missing = world.add(Entity(id="cent", type="coin", label="cent", phrase="one cent", owner=detective.id))
    mace = world.add(Entity(id="mace", type="object", label="mace", phrase="a heavy mace", plural=False))

    state = StoryState(detective=detective, helper=helper, missing=missing, mace=mace)

    detective.memes["curiosity"] = 1
    detective.memes["worry"] = 1

    world.say(f"{detective.id} was a little detective who loved puzzles.")
    world.say(f"{params.name} kept a notebook, a magnifying glass, and a sharp eye for clues.")
    world.say(f"One day, a {mystery.missing} went missing, and the case began at {setting.place}.")
    world.say(setting.setting_detail)

    world.para()
    detective.memes["determination"] = 1
    world.say(f"{detective.id} looked around and noticed {mystery.clue}.")
    state.clue_seen = True
    world.say(f'That clue said, "Look closer."')
    world.say(f'{detective.id} whispered, "The cent did not vanish. It hid somewhere near the mace."')

    world.para()
    state.worry = 1
    world.say(f"{params.name} checked the floor, the counter, and the corners.")
    world.say(f"{helper.id.lower() if helper.kind == 'character' else helper.id} stayed close, ready to help.")
    world.say(f"At last, {detective.id} solved it by choosing to {mystery.method}.")
    state.solved = True
    world.say(f"{mystery.solution.capitalize()}.")
    state.missing.meters["found"] = 1
    state.relief = 1
    detective.memes["worry"] = 0
    detective.memes["pride"] = 1
    world.say(f"{detective.id} smiled, because the missing cent was safe again.")

    world.facts.update(
        detective=detective,
        helper=helper,
        missing=missing,
        mace=mace,
        mystery=mystery,
        state=state,
        setting=setting,
    )
    return world, state


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = f["detective"]
    mystery: Mystery = f["mystery"]
    setting: Setting = f["setting"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What kind of story is this about {detective.id}?",
            answer=f"It is a detective story where {detective.id} looks for clues and solves a small mystery at {setting.place}.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.missing} was missing, and that made {detective.id} start looking carefully.",
        ),
        QAItem(
            question=f"What clue helped {detective.id} solve the case?",
            answer=f"The clue was {mystery.clue}, which helped {detective.id} realize where the cent was hidden.",
        ),
        QAItem(
            question=f"How did {detective.id} solve the mystery?",
            answer=f"{detective.id} solved it by choosing to {mystery.method}. That is how the cent was found.",
        ),
        QAItem(
            question=f"Who stayed near {detective.id} during the search?",
            answer=f"{helper.id} stayed close and helped keep the search calm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cent?",
            answer="A cent is a small coin. People use coins as money to buy little things.",
        ),
        QAItem(
            question="What is a mace?",
            answer="A mace is a heavy object with a long handle or spiked head in old stories, and it can also be used here as a big, hard thing that is hard to move.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective: Entity = f["detective"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short detective story for a child where {detective.id} follows a clue to find a missing cent.',
        f'Tell a problem-solving mystery about a cent and a mace, and make the detective think step by step.',
        f'Write a gentle detective story where the clue "{mystery.clue}" leads to the answer.',
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    lines.extend(f"  {t}" for t in world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world, _state = build_world(params)
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
    StoryParams(setting="office", mystery="lost_cent", name="Mina", gender="girl", helper="cat"),
    StoryParams(setting="museum", mystery="sticky_cent", name="Theo", gender="boy", helper="friend"),
    StoryParams(setting="shop", mystery="lost_cent", name="June", gender="girl", helper="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible detective combos:")
        for s, m in combos:
            print(f"  {s:8} {m}")
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
