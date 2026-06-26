#!/usr/bin/env python3
"""
A standalone storyworld for a tiny Detective Story domain with foreshadowing,
marmite, and a bra as the central clue objects.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old kitchen"
    weather: str = "rainy"
    light: str = "dim"


@dataclass
class Suspect:
    id: str
    type: str
    label: str
    alibi: str
    tells: str


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    smell: str
    origin: str
    foreshadow: str


@dataclass
class StoryParams:
    seed: Optional[int] = None
    setting: str = "kitchen"
    detective: str = "Mina"
    detective_type: str = "girl"
    suspect: str = "Aunt June"
    clue: str = "marmite"


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the old kitchen", weather="rainy", light="dim"),
    "hallway": Setting(place="the hallway", weather="", light="dim"),
    "laundry": Setting(place="the laundry room", weather="", light="bright"),
}

SUSPECTS = {
    "aunt": Suspect(
        id="Aunt June",
        type="woman",
        label="Aunt June",
        alibi="she had been baking bread in the next room",
        tells="she kept glancing at the laundry basket",
    ),
    "brother": Suspect(
        id="Tommy",
        type="boy",
        label="Tommy",
        alibi="he claimed he was outside kicking a ball",
        tells="his socks were damp at the ankles",
    ),
    "neighbor": Suspect(
        id="Mrs. Vale",
        type="woman",
        label="Mrs. Vale",
        alibi="she said she was only returning a borrowed spoon",
        tells="she spoke a little too quickly",
    ),
}

CLUES = {
    "marmite": Clue(
        id="marmite",
        label="marmite",
        phrase="a jar of marmite",
        smell="dark and salty",
        origin="the pantry shelf",
        foreshadow="there was a dark brown smear on the counter",
    ),
    "bra": Clue(
        id="bra",
        label="bra",
        phrase="a pale blue bra",
        smell="like soap and warm cotton",
        origin="the laundry basket",
        foreshadow="a corner of pale blue cloth peeked from under a towel",
    ),
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(setting: str, clue: str) -> bool:
    return setting in SETTINGS and clue in CLUES


def explain_invalid(setting: str, clue: str) -> str:
    return f"(No story: setting={setting!r} and clue={clue!r} do not form a tidy detective scene.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def tell(setting: Setting, detective_name: str, detective_type: str, suspect: Suspect, clue: Clue) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        label=detective_name,
        meters={"attention": 1.0},
        memes={"curiosity": 1.0},
    ))
    suspect_ent = world.add(Entity(
        id=suspect.id,
        kind="character",
        type=suspect.type,
        label=suspect.label,
        meters={"nervousness": 0.5},
        memes={"worry": 0.2},
    ))
    clue_ent = world.add(Entity(
        id=clue.id,
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        hidden=True,
        owner=suspect_ent.id,
    ))

    world.facts.update(
        detective=detective,
        suspect=suspect_ent,
        clue=clue_ent,
        clue_cfg=clue,
        suspect_cfg=suspect,
        setting=setting,
    )

    # Act 1: setup and foreshadowing.
    world.say(
        f"{detective_name} was a sharp little detective who liked to notice what other people missed."
    )
    world.say(
        f"That evening, {detective_name} walked into {setting.place}, where the light was dim and the air felt quiet."
    )
    world.say(
        f"{clue.foreshadow.capitalize()}, and {detective_name} stopped to look."
    )

    # Act 2: the small mystery tightens.
    world.para()
    world.say(
        f"{detective_name} found {clue.phrase} hidden where it did not belong."
    )
    world.say(
        f"It smelled {clue.smell}, and that smell was the first clue."
    )
    world.say(
        f"{suspect.label} said, \"{suspect.alibi}.\""
    )
    world.say(
        f"But {detective_name} noticed {suspect.tells}, and that was the second clue."
    )

    # Act 3: deduction and reveal.
    world.para()
    if clue.id == "marmite":
        world.say(
            f"{detective_name} remembered that marmite was dark enough to leave a mark, so the smear on the counter suddenly made sense."
        )
        world.say(
            f"The jar had been opened near the pantry, then hidden in a hurry."
        )
        world.say(
            f"{detective_name} asked one careful question, and {suspect.label} sighed."
        )
        world.say(
            f"{suspect.label} admitted the jar had slipped while she was tidying, and she had tried to hide the mess before anyone saw."
        )
        world.say(
            f"Then {detective_name} wiped the counter clean and closed the case."
        )
        world.say(
            f"By the end, the kitchen was neat again, and the dark streak that had looked suspicious at first was only a clumsy accident."
        )
    else:
        world.say(
            f"{detective_name} recognized the pale blue cloth right away."
        )
        world.say(
            f"The bra had been tucked into the laundry basket by mistake, not stolen at all."
        )
        world.say(
            f"{suspect.label} flushed red and explained that she had hurriedly gathered the wash and mixed up the items."
        )
        world.say(
            f"{detective_name} smiled, returned the missing thing, and the whole room felt lighter."
        )
        world.say(
            f"By the end, the laundry basket was in order, and the little mystery was solved without any trouble."
        )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly detective story set in {f['setting'].place} with foreshadowing and the clue {f['clue_cfg'].label}.",
        f"Tell a short mystery where {f['detective'].id} notices a clue that first looks suspicious but turns out harmless.",
        f"Write a gentle detective tale with a careful observer, a misleading clue, and a clear ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = f["detective"]
    sus = f["suspect"]
    clue = f["clue_cfg"]
    setting = f["setting"]

    if clue.id == "marmite":
        answer = (
            f"{det.id} found a dark brown smear near the counter, and that made the marmite clue seem important. "
            f"The mistake turned out to be a clumsy spill while {sus.label} was tidying."
        )
        reveal = (
            f"{sus.label} admitted that the marmite had slipped while she was cleaning, so the strange mark was not a crime."
        )
    else:
        answer = (
            f"{det.id} noticed the pale blue cloth in the laundry basket, and that detail led to the missing bra. "
            f"It turned out to be mixed into the wash by accident."
        )
        reveal = (
            f"{sus.label} explained that the bra had been gathered with the laundry and put in the wrong place by mistake."
        )

    return [
        QAItem(
            question=f"Where did {det.id} begin looking for the mystery clue?",
            answer=f"{det.id} began looking in {setting.place}, where the room was quiet and dim.",
        ),
        QAItem(
            question=f"What foreshadowed the mystery before {det.id} found the clue?",
            answer=f"{clue.foreshadow.capitalize()} before the clue was found.",
        ),
        QAItem(
            question=f"Why did {det.id} think the clue mattered?",
            answer=answer,
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=reveal,
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is foreshadowing?",
        answer="Foreshadowing is a little hint that points to something important before it happens.",
    ),
    QAItem(
        question="What does a detective do?",
        answer="A detective looks carefully for clues and uses them to figure out what really happened.",
    ),
    QAItem(
        question="What is marmite?",
        answer="Marmite is a very dark, salty spread that people often put on toast.",
    ),
    QAItem(
        question="What is laundry?",
        answer="Laundry is the clothes and cloth items that need to be washed and put away.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(kitchen).
setting(hallway).
setting(laundry).

clue(marmite).
clue(bra).

valid(S, C) :- setting(S), clue(C), S = kitchen.
valid(S, C) :- setting(S), clue(C), S = laundry.

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid_combos() -> list[tuple]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            if valid_story(s, c):
                if s in {"kitchen", "laundry"}:
                    combos.append((s, c))
    return combos


def asp_verify() -> int:
    py = set(python_valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in Python:", sorted(py - cl))
    print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for line in world.trace:
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective storyworld with foreshadowing, marmite, and bra clues.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--detective")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS.keys()))
    clue = args.clue or rng.choice(list(CLUES.keys()))
    if not valid_story(setting, clue):
        raise StoryError(explain_invalid(setting, clue))
    detective = args.detective or rng.choice(["Mina", "Ivy", "June", "Nell"])
    return StoryParams(
        seed=args.seed,
        setting=setting,
        detective=detective,
        detective_type="girl",
        suspect=rng.choice(list(SUSPECTS.keys())),
        clue=clue,
    )


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    suspect = SUSPECTS[params.suspect]
    clue = CLUES[params.clue]
    world = tell(setting, params.detective, params.detective_type, suspect, clue)
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print("Compatible story pairs:")
        for s, c in sorted(set(asp.atoms(model, "valid"))):
            print(f"{s} / {c}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="kitchen", detective="Mina", detective_type="girl", suspect="aunt", clue="marmite"),
            StoryParams(setting="laundry", detective="Ivy", detective_type="girl", suspect="aunt", clue="bra"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
