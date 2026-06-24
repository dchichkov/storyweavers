#!/usr/bin/env python3
"""
A small whodunit story world about a missing sundae, a subsidiary counter,
a brave little detective, and a transformation that solves the mystery.
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
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    culprit: str
    reveal: str
    transform_to: str
    brave_act: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "diner": Setting(place="the bright diner", affords={"sundae"}),
    "subsidiary": Setting(place="the subsidiary shop", affords={"sundae"}),
    "kitchen": Setting(place="the kitchen", affords={"sundae"}),
}

MYSTERIES = {
    "missing_sundae": Mystery(
        id="missing_sundae",
        clue="a trail of chocolate on the floor",
        culprit="the shy freezer fan",
        reveal="the freezer fan had blown the cherry off the sundae and into a corner",
        transform_to="braver",
        brave_act="look inside the cold case",
        tags={"sundae", "subsidiary", "transformation", "bravery", "whodunit"},
    ),
    "swapped_spoon": Mystery(
        id="swapped_spoon",
        clue="a tiny spoon left beside the napkins",
        culprit="the helper robot",
        reveal="the helper robot had quietly moved the spoon to the wrong tray",
        transform_to="braver",
        brave_act="ask the robot a hard question",
        tags={"sundae", "subsidiary", "transformation", "bravery", "whodunit"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ruby"]
BOY_NAMES = ["Leo", "Finn", "Ben", "Noah", "Eli", "Theo"]
HELPERS = ["mother", "father", "friend", "aunt", "uncle"]


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit story world: sundae, subsidiary, bravery, transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S, M) :- setting(S), mystery(M), affords(S, sundae), tagged(M, sundae), tagged(M, whodunit).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for s in SETTINGS:
        for m in MYSTERIES:
            out.append((s, m))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, helper=helper)


def _intro(world: StoryWorld, hero: Entity, helper: Entity, myst: Mystery) -> None:
    hero.memes["curious"] = 1
    hero.memes["bravery"] = 0
    world.say(
        f"{hero.id} was a little {hero.type} who loved clues, clean tables, and anything with a neat answer."
    )
    world.say(
        f"That afternoon, {hero.id} and {helper.label} went to {world.setting.place}, where a shiny sundae should have been waiting."
    )
    world.say(
        f"But the sundae was gone, and only {myst.clue} was left behind."
    )


def _investigate(world: StoryWorld, hero: Entity, helper: Entity, myst: Mystery) -> None:
    hero.memes["worry"] = 1
    hero.memes["bravery"] += 1
    world.para()
    world.say(
        f"{hero.id} felt a little scared, but {hero.pronoun()} took a brave breath and decided to {myst.brave_act}."
    )
    world.say(
        f"{helper.label} shined a lamp over the counter at the subsidiary shop, and {hero.id} spotted {myst.clue}."
    )
    world.say(
        f"That clue pointed toward a cold corner, where something had moved in a hurry."
    )


def _reveal(world: StoryWorld, hero: Entity, helper: Entity, myst: Mystery) -> None:
    hero.memes["bravery"] += 1
    hero.memes["understanding"] = 1
    world.para()
    world.say(
        f"At last, {hero.id} found the truth: {myst.reveal}."
    )
    world.say(
        f"{hero.id} asked one careful question, and the mystery untangled like a ribbon."
    )
    world.say(
        f"Then something changed. {hero.id} stopped feeling like a worried child and became {myst.transform_to}."
    )
    world.say(
        f"With that brave new feeling, {hero.id} helped make a fresh sundae and carried it back proudly to the table."
    )


def tell(setting: Setting, myst: Mystery, name: str, gender: str, helper_role: str) -> World:
    world = StoryWorld(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_role, label=f"the {helper_role}"))
    sundae = world.add(Entity(id="sundae", type="sundae", label="sundae", phrase="a tall sundae with whipped cream"))
    world.facts.update(hero=hero, helper=helper, sundae=sundae, mystery=myst, setting=setting)
    _intro(world, hero, helper, myst)
    _investigate(world, hero, helper, myst)
    _reveal(world, hero, helper, myst)
    return world


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    myst = f["mystery"]
    return [
        f'Write a child-friendly whodunit about a missing sundae at {world.setting.place}, with a clue, a brave question, and a surprise reveal.',
        f"Tell a small mystery story where {hero.id} and {helper.label} search the subsidiary shop for a missing sundae and learn a brave lesson.",
        f'Write a story with the words "sundae", "subsidiary", "Transformation", and "Bravery" that ends with the mystery solved.',
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    myst = f["mystery"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"What was missing at {setting.place}?",
            answer="A sundae was missing, and that made the little mystery feel serious.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} search the subsidiary shop?",
            answer=f"The clue was {myst.clue}, which pointed {hero.id} toward the cold corner.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery?",
            answer=f"{hero.id} showed bravery by taking a deep breath and choosing to {myst.brave_act}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} changed into {myst.transform_to}, because solving the mystery made {hero.id} feel stronger.",
        ),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sundae?",
            answer="A sundae is a sweet dessert, often with ice cream, sauce, and toppings like whipped cream or a cherry.",
        ),
        QAItem(
            question="What does subsidiary mean?",
            answer="A subsidiary is a smaller branch or shop that belongs to a larger business.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing something scary or difficult while trying to stay calm and keep going.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one state to another, like becoming more confident or changing shape in a story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this world is only for sundae mysteries with a subsidiary setting.)"


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], MYSTERIES[params.mystery], params.name, params.gender, params.helper)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show compatible/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return

    if args.all:
        params_list = [
            StoryParams(setting="diner", mystery="missing_sundae", name="Mia", gender="girl", helper="mother"),
            StoryParams(setting="subsidiary", mystery="swapped_spoon", name="Leo", gender="boy", helper="father"),
        ]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        params_list = []
        seen = set()
        i = 0
        while len(params_list) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            i += 1
            key = (p.setting, p.mystery, p.name, p.gender, p.helper)
            if key in seen:
                continue
            seen.add(key)
            params_list.append(p)

    samples = [generate(p) for p in params_list]

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
