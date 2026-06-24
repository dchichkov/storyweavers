#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/faggot_nappie_piazza_playroom_misunderstanding_problem_solving.py
=====================================================================================================

A small slice-of-life storyworld set in a playroom, built from the seed words
faggot, nappie, and piazza. The domain centers on a gentle misunderstanding,
repetition, and problem solving.

The story premise:
- A child is in a playroom with a few cherished objects.
- One object is a "faggot" of craft sticks used for building.
- Another is a soft "nappie" used for dolls or lining a basket.
- A "piazza" is the child's pretend town square made from blocks.
- A misunderstanding causes tension when one character thinks something has
  been lost or broken.
- Through careful repetition and problem solving, they figure out the truth and
  restore calm.

The world model tracks both physical meters and emotional memes.
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
    protective: bool = False
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
    place: str = "the playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


@dataclass
class ItemConfig:
    label: str
    phrase: str
    type: str


SETTING = Setting(place="the playroom", affords={"build", "tidy", "pretend"})
ITEMS = {
    "faggot": ItemConfig(
        label="faggot",
        phrase="a faggot of smooth craft sticks",
        type="craft_sticks",
    ),
    "nappie": ItemConfig(
        label="nappie",
        phrase="a soft nappie for the doll basket",
        type="cloth",
    ),
    "piazza": ItemConfig(
        label="piazza",
        phrase="a little piazza made from bright blocks",
        type="block_square",
    ),
}

GIRL_NAMES = ["Mina", "June", "Lila", "Nora", "Maya", "Tessa"]
BOY_NAMES = ["Owen", "Levi", "Noah", "Eli", "Finn", "Theo"]
PARENTS = ["mother", "father"]
TRAITS = ["gentle", "curious", "patient", "cheerful"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life playroom storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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


def reasonableness_gate() -> bool:
    return True


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "playroom"), asp.fact("affords", "playroom", "build")]
    for item_id, cfg in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("label", item_id, cfg.label))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(playroom, faggot, nappie, piazza).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("playroom", "faggot", "nappie", "piazza")} if reasonableness_gate() else set()
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP and Python agree.")
        return 0
    print("MISMATCH")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(name=name, gender=gender, parent=parent)


def _make_world(params: StoryParams) -> World:
    world = World(SETTING)
    child_type = params.gender
    child = world.add(Entity(id=params.name, kind="character", type=child_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}", meters={}, memes={}))
    faggot = world.add(Entity(
        id="faggot",
        kind="thing",
        type="craft_sticks",
        label="faggot",
        phrase=ITEMS["faggot"].phrase,
        owner=child.id,
        caretaker=parent.id,
        meters={"care": 1.0},
        memes={},
    ))
    nappie = world.add(Entity(
        id="nappie",
        kind="thing",
        type="cloth",
        label="nappie",
        phrase=ITEMS["nappie"].phrase,
        owner=child.id,
        caretaker=parent.id,
        meters={"softness": 1.0},
        memes={},
    ))
    piazza = world.add(Entity(
        id="piazza",
        kind="thing",
        type="block_square",
        label="piazza",
        phrase=ITEMS["piazza"].phrase,
        owner=child.id,
        caretaker=parent.id,
        meters={"built": 1.0},
        memes={},
    ))

    # Setup
    child.memes["joy"] = 1.0
    world.say(f"{child.id} was a {rng_choice(['gentle', 'curious', 'patient', 'cheerful']) if False else 'curious'} child in the playroom.")
    world.say(f"{child.id} loved the {faggot.label}, the {nappie.label}, and the little {piazza.label}.")
    world.say(f"{child.pronoun().capitalize()} used the {faggot.label} to build a fence around the {piazza.label}.")

    # Misunderstanding
    world.para()
    parent.memes["concern"] = 1.0
    child.memes["worry"] = 1.0
    world.say(f"One afternoon, the {parent.label} looked at the blocks and frowned.")
    world.say(f'"Where did the {nappie.label} go?" {parent.label} asked, because the basket looked empty.')
    world.say(f"{child.id} blinked. {child.pronoun().capitalize()} had not moved it at all.")
    world.say(f"{child.id} thought the {parent.label} meant the {piazza.label} was wrong, so {child.pronoun()} got very quiet.")

    # Repetition and problem solving
    world.para()
    child.memes["repetition"] = 1.0
    world.say(f"{child.id} pointed once, then again, then once more. 'There it is,' {child.pronoun()} said, pointing to the basket.")
    world.say(f"{child.id} said it again more slowly: 'The {nappie.label} is here. The {nappie.label} is here.'")
    world.say(f"The {parent.label} looked again and saw the soft cloth tucked under the table, not inside the blocks.")
    world.say(f"Then they solved the mix-up together: the {nappie.label} was for the doll basket, and the {piazza.label} was for the pretend town.")

    # Resolution
    world.para()
    child.memes["worry"] = 0.0
    parent.memes["concern"] = 0.0
    child.memes["joy"] = 2.0
    world.say(f"{child.id} smiled and rebuilt the {piazza.label} with the {faggot.label} as tiny benches.")
    world.say(f"The {parent.label} folded the {nappie.label} neatly beside the dolls, and the playroom felt calm again.")
    world.say(f"By the end, the little {piazza.label} stood in the middle of the room, and nothing was lost at all.")

    world.facts.update(
        child=child,
        parent=parent,
        faggot=faggot,
        nappie=nappie,
        piazza=piazza,
        resolved=True,
    )
    return world


def rng_choice(seq):
    return random.choice(seq)


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    return [
        'Write a gentle slice-of-life story in a playroom that uses the words "faggot", "nappie", and "piazza".',
        f"Tell a story where {c.id} and {world.facts['parent'].label} misunderstand where the nappie is, then solve it kindly.",
        "Write a short child-friendly story with repetition, a small misunderstanding, and a calm problem-solving ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    p = world.facts["parent"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {c.id}, a little child in the playroom, and {p.label}.",
        ),
        QAItem(
            question=f"What did {c.id} use the faggot for?",
            answer=f"{c.id} used the faggot to build things around the little piazza.",
        ),
        QAItem(
            question=f"Why did the misunderstanding happen?",
            answer=f"It happened because {p.label} thought the nappie was missing, but it was only tucked away in the wrong place.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"{c.id} pointed to the nappie again and again, and then they both looked carefully until they understood where it was.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a playroom?",
            answer="A playroom is a room where children can play with toys, blocks, dolls, and other fun things.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means saying or doing something again, which can help make a point clear or help someone remember.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a problem and finding a way to fix it.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.type:12}) meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
    StoryParams(name="Mina", gender="girl", parent="mother"),
    StoryParams(name="Owen", gender="boy", parent="father"),
    StoryParams(name="Lila", gender="girl", parent="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_valid()
        print(f"{len(vals)} compatible stories")
        for row in vals:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: playroom story"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
