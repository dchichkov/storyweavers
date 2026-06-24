#!/usr/bin/env python3
"""
A tiny mystery storyworld: a hesitant child, a surprising clue, a mystery to
solve, and a twist that changes what the clue means.

The world is small and classical: one child, one grown helper, one hidden
object, one place, and one surprising reveal. The story begins with hesitation,
moves through clues and a mystery to solve, then ends with a twist that makes
the final answer satisfying.
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
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    hiding_spot: str


@dataclass
class Clue:
    label: str
    phrase: str
    surprise: str
    wrong_guess: str
    twist: str
    solves: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(place="the attic", detail="Dusty boxes leaned against the slanted walls, and a single window let in a pale stripe of light.", hiding_spot="under an old blanket"),
    "garden": Setting(place="the garden", detail="The garden was quiet, with bean poles, cool dirt, and a little path between the plants.", hiding_spot="inside a watering can"),
    "library": Setting(place="the library", detail="Tall shelves stood like sleepy trees, and the air smelled like paper and glue.", hiding_spot="behind a stack of picture books"),
}

CLUES = {
    "bell": Clue(
        label="little bell",
        phrase="a tiny silver bell",
        surprise="It gave a sudden jingle from somewhere it should not have been",
        wrong_guess="the sound might be from a mouse or a toy",
        twist="the bell was tied to the lost kitten's collar",
        solves="the kitten was hiding safely in the room all along",
    ),
    "map": Clue(
        label="folded map",
        phrase="a folded paper map with a blue dot",
        surprise="It fluttered out of a crack like a secret trying to be found",
        wrong_guess="the blue dot might point to treasure",
        twist="the blue dot marked where the helper had tucked the missing snack",
        solves="the mystery was not about treasure at all, but about lunch",
    ),
    "ribbon": Clue(
        label="red ribbon",
        phrase="a soft red ribbon with a knot",
        surprise="It peeked out from under a box as if it wanted to be noticed",
        wrong_guess="it might belong to a present waiting to be opened",
        twist="the ribbon was tied around the lost key the child needed",
        solves="the key opened the little door everyone had been searching for",
    ),
}

NAMES_GIRL = ["Mina", "Tia", "Lina", "Nora", "Pia", "Maya"]
NAMES_BOY = ["Owen", "Theo", "Ben", "Ezra", "Leo", "Noah"]
HELPERS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["careful", "curious", "brave", "gentle", "shy"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with hesitation, surprise, and a twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in SETTINGS for c in CLUES]


def explain_rejection() -> str:
    return "(No story: the chosen mystery parts do not make a believable clue-and-twist chain.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError(explain_rejection())
    place, clue = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue, name=name, gender=gender, helper=helper)


def _hero_title(gender: str) -> str:
    return "girl" if gender == "girl" else "boy"


def tell(setting: Setting, clue: Clue, name: str, gender: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    grown = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}"))
    clue_ent = world.add(Entity(id="Clue", type="thing", label=clue.label, phrase=clue.phrase, caretaker=grown.id))

    hero.memes["hesitant"] = 1
    world.say(f"{hero.id} was a {_hero_title(gender)} who felt hesitant whenever something strange happened.")
    world.say(f"One day, {hero.id} and {grown.label} went to {setting.place}. {setting.detail}")
    world.say(f"Then they noticed {clue.phrase}. {clue.surprise}.")
    world.para()
    hero.memes["mystery"] = 1
    world.say(f"{hero.id} stared at it and whispered, \"{clue.wrong_guess}.\"")
    world.say(f"But {grown.label} said, \"Let's solve the mystery carefully.\"")
    world.say(f"They looked under boxes, behind jars, and near the floor, following the small clue.")
    world.para()
    hero.memes["surprise"] = 1
    world.say(f"At last, the twist came clear: {clue.twist}.")
    world.say(f"That meant {clue.solves}.")
    world.say(f"{hero.id} smiled, no longer hesitant, because the mystery had an answer after all.")
    world.say(f"By the end, {hero.id} was happy to keep {clue.label} safe beside {grown.label}.")

    world.facts.update(
        hero=hero,
        helper=grown,
        clue=clue_ent,
        clue_cfg=clue,
        setting=setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    helper = f["helper"]
    return [
        f'Write a short mystery story for a child named {hero.id} that includes the word "hesitant" and ends with a twist.',
        f"Tell a gentle story set in {setting.place} where {hero.id} and {helper.label} find {clue.phrase} and solve a mystery.",
        f"Write a simple surprise mystery story for a young child about a clue, a wrong guess, and a twist reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue_cfg"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who was hesitant when the strange clue appeared in {setting.place}?",
            answer=f"{hero.id} was hesitant at first, because the clue looked surprising and mysterious.",
        ),
        QAItem(
            question=f"What did {hero.id} and {helper.label} find in {setting.place}?",
            answer=f"They found {clue.phrase}, which started the mystery to solve.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {clue.twist}, so the clue meant something different from the first guess.",
        ),
        QAItem(
            question=f"How did the mystery end?",
            answer=f"It ended when {clue.solves}, and {hero.id} felt happy instead of hesitant.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a surprising change that makes the story mean something new.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a problem or mystery.",
        ),
        QAItem(
            question="What does hesitant mean?",
            answer="Hesitant means unsure or slow to act because someone is not ready yet.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
mystery(P,C) :- place(P), clue(C).
twist(C) :- clue(C).
hesitant_story(P,C) :- mystery(P,C), twist(C).
#show mystery/2.
#show twist/1.
#show hesitant_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CLUES:
        lines.append(asp.fact("clue", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show hesitant_story/2."))
    atoms = set(asp.atoms(model, "hesitant_story"))
    py = set((p, c) for p in SETTINGS for c in CLUES)
    if atoms == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(py))
    return 1


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show hesitant_story/2."))
    return sorted(set(asp.atoms(model, "hesitant_story")))


def asp_valid_stories() -> list[tuple[str, str]]:
    return asp_valid_combos()


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CLUES[params.clue], params.name, params.gender, params.helper)
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
    StoryParams(place="attic", clue="bell", name="Mina", gender="girl", helper="mother"),
    StoryParams(place="garden", clue="map", name="Owen", gender="boy", helper="father"),
    StoryParams(place="library", clue="ribbon", name="Tia", gender="girl", helper="grandma"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show hesitant_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:\n")
        for place, clue in combos:
            print(f"  {place:8} {clue:8}")
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
            header = f"### {p.name}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
