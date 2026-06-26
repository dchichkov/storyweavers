#!/usr/bin/env python3
"""
A fairy-tale storyworld about someone arriving at a small place and solving a
gentle mystery.

Premise:
- A child or young traveler arrives at a cozy fairy-tale setting.
- Something important is missing or strange.
- The hero looks closely, follows clues, and solves the mystery.
- The ending proves the change with a clear, small celebration.

This file is a standalone Storyweavers world script.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman"}
        male = {"boy", "prince", "king", "father", "man", "knight"}
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
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_label: str
    phrase: str
    clue_type: str
    clue_place: str
    solved_by: str
    reveal_line: str
    ending_image: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


SETTINGS = {
    "castle_gate": Setting("the castle gate", "bright", {"arrive", "mystery"}),
    "forest_lane": Setting("the forest lane", "misty", {"arrive", "mystery"}),
    "village_square": Setting("the village square", "cheery", {"arrive", "mystery"}),
    "moon_bridge": Setting("the moon bridge", "quiet", {"arrive", "mystery"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing_label="silver bell",
        phrase="a silver bell with a ribbon",
        clue_type="footprints",
        clue_place="the rosemary path",
        solved_by="the baker had borrowed it for a feast",
        reveal_line="The baker smiled and returned the silver bell with a bow.",
        ending_image="Soon the silver bell rang from the tower again.",
    ),
    "lantern": Mystery(
        id="lantern",
        missing_label="golden lantern",
        phrase="a golden lantern with star-shaped glass",
        clue_type="sparkles",
        clue_place="the mossy steps",
        solved_by="the fireflies had gathered in it to rest",
        reveal_line="The fireflies fluttered out, and the golden lantern glowed softly once more.",
        ending_image="Soon the golden lantern shone like a small moon.",
    ),
    "key": Mystery(
        id="key",
        missing_label="little brass key",
        phrase="a little brass key on a blue string",
        clue_type="marks",
        clue_place="the well stones",
        solved_by="the key had fallen into the wishing well and been lifted by a bucket",
        reveal_line="The key came up wet but safe, glittering in the sun.",
        ending_image="Soon the little brass key opened the garden gate again.",
    ),
}

GENTLE_NAMES = ["Ava", "Mia", "Lily", "Nora", "Theo", "Eli", "Finn", "Owen", "Maya", "Rose"]
HELPERS = {
    "girl": "old woman",
    "boy": "old man",
    "knight": "kind knight",
    "princess": "gentle princess",
}

HERO_TYPES = ["girl", "boy", "knight", "princess"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale mystery storyworld about arriving and solving a small puzzle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=["old woman", "old man", "kind knight", "gentle princess"])
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    helper_type = args.helper_type or HELPERS.get(hero_type, "kind knight")
    name = args.name or rng.choice(GENTLE_NAMES)
    return StoryParams(place=place, mystery=mystery, hero_name=name, hero_type=hero_type, helper_type=helper_type)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, m) for p in SETTINGS for m in MYSTERIES]


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mystery = MYSTERIES[params.mystery]
    world = World(setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, meters={}, memes={"wonder": 1.0}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=params.helper_type))
    missing = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="treasure",
        label=mystery.missing_label,
        phrase=mystery.phrase,
        owner=hero.id,
        caretaker=helper.id,
        location=mystery.clue_place,
        hidden=True,
        found=False,
    ))

    world.say(f"One evening, {hero.id} arrived at {setting.place}.")
    world.say(f"The place was {setting.mood}, but something was wrong: {hero.pronoun('possessive')} {missing.label} was gone.")
    world.para()
    world.say(f"{hero.id} looked at the ground and found {mystery.clue_type} near {mystery.clue_place}.")
    world.say(f"At once, {hero.id} followed the clue with careful steps, and {hero.pronoun()} met a {helper.type} by the path.")
    world.say(f'The {helper.type} said, "A mystery is a story that asks for kind eyes and patient feet."')
    world.para()
    world.say(f"{hero.id} searched under leaves, beside stones, and behind a little wall.")
    world.say(f"Then the answer came clear: {mystery.solved_by}.")
    missing.hidden = False
    missing.found = True
    world.facts.update(hero=hero, helper=helper, mystery=mystery, setting=setting, missing=missing)
    world.para()
    world.say(mystery.reveal_line)
    world.say(f"{hero.id} smiled, because the mystery was solved without any fuss.")
    world.say(mystery.ending_image)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, mystery, setting = f["hero"], f["mystery"], f["setting"]
    return [
        f'Write a short fairy tale for a young child about a traveler who arrives at {setting.place} and solves a small mystery.',
        f"Tell a gentle story where {hero.id} arrives at {setting.place}, notices that a {mystery.missing_label} is missing, and finds out what happened.",
        f'Write a simple fairy-tale mystery using the word "arrive" and ending with the missing treasure back in its place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, mystery, setting = f["hero"], f["helper"], f["mystery"], f["setting"]
    return [
        QAItem(
            question=f"Where did {hero.id} arrive at the beginning of the story?",
            answer=f"{hero.id} arrived at {setting.place}, where the air felt {setting.mood} and the mystery was waiting to be solved.",
        ),
        QAItem(
            question=f"What was missing when {hero.id} arrived?",
            answer=f"The missing thing was {mystery.missing_label}. It belonged to {hero.id} and made the little mystery worth solving.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the mystery?",
            answer=f"{hero.id} followed the clue, searched carefully, and learned that {mystery.solved_by}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think about the mystery?",
            answer=f"A {helper.type} helped by speaking gently and reminding {hero.id} to look with patient eyes.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The {mystery.missing_label} was found and returned, so the place felt complete again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to arrive?",
            answer="To arrive means to come to a place after traveling there.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to understand or solve.",
        ),
        QAItem(
            question="Why do clues matter in a mystery?",
            answer="Clues matter because they help someone figure out what happened.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.found:
            bits.append("found=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(P) :- place(P).
mystery(M) :- mystery_kind(M).
compatible(P,M) :- place(P), mystery_kind(M).
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_kind", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="castle_gate", mystery="bell", hero_name="Ava", hero_type="girl", helper_type="old woman"),
    StoryParams(place="forest_lane", mystery="lantern", hero_name="Theo", hero_type="boy", helper_type="kind knight"),
    StoryParams(place="village_square", mystery="key", hero_name="Mia", hero_type="princess", helper_type="gentle princess"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/mystery combos:")
        for p, m in combos:
            print(f"  {p:14} {m}")
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
