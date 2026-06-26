#!/usr/bin/env python3
"""
storyworlds/worlds/principal_account_blossom_dialogue_conflict_inner_monologue.py
=================================================================================

A small adventure storyworld about a child, a principal, an account book,
and a blossom that needs saving.

Premise:
- The hero carries an important account book to the principal.
- The school garden has one fragile blossom.
- A windy mishap threatens both the account and the blossom.

Tension:
- The principal asks for the account.
- The hero worries the account may be lost.
- Dialogue and inner monologue carry the conflict forward.

Turn and resolution:
- The hero uses a simple shelter and a careful handoff.
- The account is delivered, the blossom is protected, and the day ends
  with a hopeful image in the garden.

The world is intentionally small and constraint-checked, with state-driven prose.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)

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
    place: str = "the school garden"
    indoors: bool = False


@dataclass
class StoryParams:
    name: str
    gender: str
    principal: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        return c


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: principal, account, blossom.")
    ap.add_argument("--name", choices=["Ava", "Milo", "Nia", "Leo", "Maya", "Noah"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--principal", choices=["headmistress", "principal"])
    ap.add_argument("--trait", choices=["brave", "curious", "careful", "spirited", "determined"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(["Ava", "Maya", "Nia"] if gender == "girl" else ["Leo", "Milo", "Noah"])
    principal = args.principal or rng.choice(["principal", "headmistress"])
    trait = args.trait or rng.choice(["brave", "curious", "careful", "spirited", "determined"])
    return StoryParams(name=name, gender=gender, principal=principal, trait=trait)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("role", "principal"),
            asp.fact("thing", "account"),
            asp.fact("thing", "blossom"),
            asp.fact("event", "dialogue"),
            asp.fact("event", "conflict"),
            asp.fact("event", "inner_monologue"),
            asp.fact("setting", "school_garden"),
        ]
    )


ASP_RULES = r"""
role(principal).
thing(account).
thing(blossom).
event(dialogue).
event(conflict).
event(inner_monologue).
setting(school_garden).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show role/1. #show thing/1."))
    roles = set(asp.atoms(model, "role"))
    things = set(asp.atoms(model, "thing"))
    ok = roles == {("principal",)} and things == {("account",), ("blossom",)}
    if ok:
        print("OK: ASP twin matches the Python registry.")
        return 0
    print("MISMATCH in ASP twin.")
    return 1


def _rain_pickup(world: World) -> None:
    hero = world.get("hero")
    account = world.get("account")
    blossom = world.get("blossom")
    if hero.memes.get("wind", 0) >= THRESHOLD and "protected" not in hero.meters:
        sig = ("scuff",)
        if sig in world.fired:
            return
        world.fired.add(sig)
        account.meters["near_loss"] = 1
        blossom.meters["shiver"] = 1
        world.say("The wind tugged at the account pages, and the blossom shook on its stem.")


def propagate(world: World) -> None:
    _rain_pickup(world)


def tell(hero_name: str, hero_gender: str, principal_role: str, trait: str) -> World:
    world = World(Setting())
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, traits=[trait]))
    principal = world.add(Entity(id="principal", kind="character", type="adult", label=principal_role))
    account = world.add(Entity(id="account", type="book", label="account book", phrase="a thin account book", caretaker=principal.id))
    blossom = world.add(Entity(id="blossom", type="flower", label="blossom", phrase="a bright white blossom"))

    hero.meters["protected"] = 0
    hero.memes["hope"] = 1
    principal.memes["worry"] = 0
    account.meters["safe"] = 1
    blossom.meters["safe"] = 1

    world.say(f"{hero_name} was a {trait} child who liked little adventures in {world.setting.place}.")
    world.say(f"One morning, {hero_name} carried an account book for the {principal_role} and noticed a blossom swaying near the path.")
    world.say(f"{hero_name} thought, 'If I get this account to the office, maybe the day will go smoothly.'")

    world.para()
    world.say(f"At the gate, the {principal_role} called, 'Do you have the account?'")
    hero.memes["wind"] = 1
    propagate(world)
    world.say(f"{hero_name} answered, 'I do, but the wind is chasing it!'")
    world.say(f"{hero_name} thought, 'I must not drop it, and I must not let the blossom get broken either.'")

    world.para()
    hero.meters["protected"] = 1
    account.meters["safe"] = 1
    blossom.meters["safe"] = 1
    principal.memes["worry"] = 0
    world.say(f"{hero_name} hurried under the archway, held the account close, and cupped the blossom with one careful hand.")
    world.say(f'The {principal_role} smiled and said, "That is exactly the kind of careful account I needed."')
    world.say(f"{hero_name} handed over the account, and the blossom stayed bright beside the path.")

    world.facts.update(
        hero=hero,
        principal=principal,
        account=account,
        blossom=blossom,
        principal_role=principal_role,
        trait=trait,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    principal = f["principal_role"]
    return [
        f'Write a short adventure story for a child named {hero.label} that includes a principal, an account, and a blossom.',
        f"Tell a story where {hero.label} must bring an account to the {principal} while a blossom is in danger.",
        "Write a gentle school adventure with dialogue, conflict, and a clear ending image in a garden.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    principal_role = f["principal_role"]
    return [
        QAItem(
            question=f"Who carried the account book in the story?",
            answer=f"{hero.label} carried the account book to the {principal_role}.",
        ),
        QAItem(
            question=f"What worried the child during the trip through the garden?",
            answer="The child worried that the wind would snatch the account and that the blossom might get hurt.",
        ),
        QAItem(
            question=f"What did the {principal_role} ask about at the gate?",
            answer=f"The {principal_role} asked whether the account had arrived.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.label} delivered the account, and the blossom stayed bright and safe by the path.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an account book?",
            answer="An account book is a book where someone writes down records, numbers, or important notes.",
        ),
        QAItem(
            question="What is a blossom?",
            answer="A blossom is a flower that has opened on a plant or tree.",
        ),
        QAItem(
            question="What does a principal do?",
            answer="A principal helps lead a school and makes sure students and teachers stay organized and safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.principal, params.trait)
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


CURATED = [
    StoryParams(name="Ava", gender="girl", principal="principal", trait="brave"),
    StoryParams(name="Leo", gender="boy", principal="headmistress", trait="careful"),
    StoryParams(name="Maya", gender="girl", principal="principal", trait="determined"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show role/1. #show thing/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible registry facts are built into the ASP twin.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
