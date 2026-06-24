#!/usr/bin/env python3
"""
A small Storyweavers world about a prairie whodunit shaped by a misunderstanding,
a kind act, and a lesson learned.

Seed tale sketch:
---
On a wide prairie, a small fox named Miri found a broken locket beside a red
barn. She thought the barn cat had taken it, and she hurried to tell the others.
But the cat had only been trying to protect the locket from a sudden windstorm.
When Miri followed the muddy prints, she learned the truth: the locket had been
lost by accident, and kindness solved the mystery better than blame.

World model:
---
A prairie mystery starts with a missing object, a mistaken clue, and a character
who jumps to the wrong conclusion.
A helpful search reveals the truth.
The ending proves the lesson learned: asking gently and helping first can solve
a mystery without hurt.
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
    handled_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "fox", "cat", "mouse"}
        male = {"boy", "father", "dad", "man", "dog", "raccoon"}
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
    description: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    kind: str
    label: str
    location: str
    owned_by: Optional[str] = None
    clue_word: str = ""


@dataclass
class StoryParams:
    place: str
    mystery: str
    missing: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    suspect: str
    suspect_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.clues: list[Clue] = []
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


MYSTERIES = {
    "locket": {
        "missing": "a silver locket",
        "label": "locket",
        "clue_word": "shine",
        "at_risk": "lost",
    },
    "pie": {
        "missing": "a berry pie",
        "label": "pie",
        "clue_word": "crumbs",
        "at_risk": "ruined",
    },
    "lantern": {
        "missing": "a tin lantern",
        "label": "lantern",
        "clue_word": "squeak",
        "at_risk": "gone dark",
    },
    "ribbon": {
        "missing": "a blue ribbon",
        "label": "ribbon",
        "clue_word": "flutter",
        "at_risk": "blown away",
    },
}

SETTINGS = {
    "prairie": Setting(
        place="the prairie",
        description="The prairie was wide and bright, with tall grass and a lonely red barn.",
        affords={"search", "listen", "follow"},
    )
}

NAMES = {
    "fox": ["Miri", "Pip", "Nora"],
    "cat": ["Tansy", "Moss", "Lulu"],
    "dog": ["Rex", "Bram", "Otis"],
    "mouse": ["Bean", "Mina", "Tilly"],
    "raccoon": ["Juno", "Patch", "Wren"],
    "girl": ["Maya", "Lena", "Ivy"],
    "boy": ["Eli", "Noah", "Owen"],
}
TYPES = ["fox", "cat", "dog", "mouse", "raccoon"]
TRAITS = ["curious", "gentle", "brave", "careful", "spry"]


def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"Unknown place: {params.place}")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")


def pronoun_label(ent: Entity) -> str:
    return ent.pronoun("possessive")


def make_world(params: StoryParams) -> World:
    validate_params(params)
    setting = SETTINGS[params.place]
    world = World(setting)
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper))
    suspect = world.add(Entity(id="suspect", kind="character", type=params.suspect_type, label=params.suspect))

    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=params.mystery,
        label=mystery["label"],
        phrase=mystery["missing"],
        owner=suspect.id,
        caretaker=hero.id,
        location="shed",
    ))

    world.facts.update(hero=hero, helper=helper, suspect=suspect, missing=missing, mystery=mystery)
    return world


def story_text(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]
    mystery = f["mystery"]

    world.say(
        f"{hero.label} lived near {world.setting.place}, where the grass swayed like whispers in the wind."
    )
    world.say(
        f"One afternoon, {hero.label} noticed that {missing.phrase} was missing from the old shed."
    )
    world.say(
        f"{hero.label} saw {mystery['clue_word']} marks near the barn and thought {suspect.label} must have taken {missing.it()}."
    )
    world.say(
        f"That guess made {hero.label} frown, because the clue looked neat enough to seem like a secret on purpose."
    )

    world.para()
    world.say(
        f"{hero.label} hurried to {helper.label} and told {helper.label} about the strange clue."
    )
    world.say(
        f"But {helper.label} listened closely and asked {hero.label} to look again before blaming anyone."
    )
    world.say(
        f"So {hero.label} followed the tiny tracks through the grass, past a thistle patch, and down to a wind-bent fence."
    )
    world.say(
        f"There, tucked under a burlap sack, was {missing.phrase}."
    )
    world.say(
        f"The sack had blown over it during the storm, and the marks came from {suspect.label} trying to keep it safe."
    )

    world.para()
    world.say(
        f"{hero.label} felt heat rise in {hero.label}'s cheeks, because the mystery had been solved and the first guess had been wrong."
    )
    world.say(
        f"{hero.label} thanked {suspect.label} for the kindness, then thanked {helper.label} for the gentle reminder."
    )
    world.say(
        f"By sunset, the locket was back where it belonged, and {hero.label} knew that on the prairie, kindness could be the best clue of all."
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    suspect: Entity = f["suspect"]
    missing: Entity = f["missing"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{missing.phrase} went missing from the shed.",
        ),
        QAItem(
            question=f"Who did {hero.label} first think was responsible?",
            answer=f"{hero.label} first thought {suspect.label} had taken {missing.it()}.",
        ),
        QAItem(
            question=f"Who helped {hero.label} slow down and look again?",
            answer=f"{helper.label} helped by asking {hero.label} to look again before blaming anyone.",
        ),
        QAItem(
            question=f"What really happened to the missing {mystery['label']}?",
            answer=f"It had been covered by a burlap sack blown over it in the storm, and {suspect.label} was trying to protect it.",
        ),
        QAItem(
            question=f"What lesson did {hero.label} learn?",
            answer=f"{hero.label} learned that kindness and careful looking can solve a misunderstanding better than blame.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prairie?",
            answer="A prairie is a wide, open grassland with lots of sky and few trees.",
        ),
        QAItem(
            question="Why is kindness important in a mystery?",
            answer="Kindness helps people share clues and stay calm, which makes it easier to find the truth.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing is true.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means you understand something important that changes how you act next time.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    missing: Entity = f["missing"]
    mystery = f["mystery"]
    return [
        f"Write a child-friendly prairie whodunit about {hero.label} and a missing {missing.label}.",
        f"Tell a short story where a misunderstanding on the prairie is fixed by kindness and ends with a lesson learned.",
        f"Write a gentle mystery that uses the word prairie and shows how the clue {mystery['clue_word']} led to the truth.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:8} ({e.kind:8} {e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("label", mid, m["label"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid_setting(S) :- setting(S).
valid_mystery(M) :- mystery(M).
story_ok(S, M) :- valid_setting(S), valid_mystery(M).
#show story_ok/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_ok/2."))
    return sorted(set(asp.atoms(model, "story_ok")))


def asp_verify() -> int:
    py = {(p, m) for p in SETTINGS for m in MYSTERIES}
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: clingo gate matches Python registry ({len(py)} pairs).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Prairie whodunit story world with kindness and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=TYPES)
    ap.add_argument("--suspect")
    ap.add_argument("--suspect-type", choices=TYPES)
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
    place = args.place or "prairie"
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    hero_type = args.hero_type or rng.choice(TYPES)
    helper_type = args.helper_type or rng.choice([t for t in TYPES if t != hero_type])
    suspect_type = args.suspect_type or rng.choice([t for t in TYPES if t not in {hero_type, helper_type}])

    hero = args.hero or rng.choice(NAMES.get(hero_type, ["Miri"]))
    helper = args.helper or rng.choice(NAMES.get(helper_type, ["Tansy"]))
    suspect = args.suspect or rng.choice(NAMES.get(suspect_type, ["Patch"]))

    if hero == suspect:
        raise StoryError("The hero and suspect must be different characters.")
    if helper == suspect:
        raise StoryError("The helper and suspect must be different characters.")
    return StoryParams(
        place=place,
        mystery=mystery,
        missing=MYSTERIES[mystery]["missing"],
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
        suspect=suspect,
        suspect_type=suspect_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_text(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
    StoryParams(
        place="prairie",
        mystery="locket",
        missing=MYSTERIES["locket"]["missing"],
        hero="Miri",
        hero_type="fox",
        helper="Tansy",
        helper_type="cat",
        suspect="Patch",
        suspect_type="raccoon",
    ),
    StoryParams(
        place="prairie",
        mystery="pie",
        missing=MYSTERIES["pie"]["missing"],
        hero="Lena",
        hero_type="girl",
        helper="Bean",
        helper_type="mouse",
        suspect="Rex",
        suspect_type="dog",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_ok/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        pairs = asp_valid_pairs()
        for p, m in pairs:
            print(p, m)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
