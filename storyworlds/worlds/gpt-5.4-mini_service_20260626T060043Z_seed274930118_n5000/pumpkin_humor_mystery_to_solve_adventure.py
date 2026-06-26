#!/usr/bin/env python3
"""
Pumpkin-humor mystery adventure storyworld.

A small, self-contained classical simulation about a child, a pumpkin, a mystery,
and a funny adventure that ends in a clear solved image.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    keeper: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affordance: str
    weather: str


@dataclass
class Mystery:
    label: str
    clue_word: str
    solution_word: str
    culprit: str
    humor_word: str
    risk_word: str
    ending_image: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    hero_name: str
    hero_type: str
    helper_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.clues_found: list[str] = []
        self.suspects: list[str] = []
        self.solution_found: bool = False
        self.humor_level: float = 0.0

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

SETTINGS = {
    "pumpkin_patch": Setting(place="the pumpkin patch", affordance="search", weather="windy"),
    "barn_path": Setting(place="the barn path", affordance="search", weather="breezy"),
    "lantern_square": Setting(place="the lantern square", affordance="search", weather="cool"),
}

MYSTERIES = {
    "missing_pumpkin": Mystery(
        label="the missing pumpkin",
        clue_word="muddy",
        solution_word="wheelbarrow",
        culprit="goat",
        humor_word="goat",
        risk_word="stolen",
        ending_image="the pumpkin sitting safely in a wheelbarrow full of straw",
    ),
    "silly_carving": Mystery(
        label="the silly pumpkin face",
        clue_word="grinning",
        solution_word="carving knife",
        culprit="squirrel",
        humor_word="squirrel",
        risk_word="smeared",
        ending_image="the pumpkin wearing its lopsided grin and a tiny leaf on top",
    ),
    "lost_pumpkin_seed": Mystery(
        label="the lost pumpkin seed packet",
        clue_word="rustling",
        solution_word="seed pouch",
        culprit="pocket",
        humor_word="pocket",
        risk_word="missing",
        ending_image="the seed packet tucked into a coat pocket beside a snack crumb",
    ),
}

GIRL_NAMES = ["Maya", "Lila", "Nora", "Pia", "Zoe", "Ava", "Mina"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Milo", "Noah", "Ben", "Eli"]


# ---------------------------------------------------------------------------
# Contracted params / parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pumpkin mystery adventure storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", dest="hero_type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", dest="helper_type", choices=["mother", "father", "grandma", "grandpa"])
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery:
        if (args.setting, args.mystery) not in set(valid_combos()):
            raise StoryError("That setting and mystery do not make a workable pumpkin adventure.")

    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    setting, mystery = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandma", "grandpa"])
    name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    return StoryParams(setting=setting, mystery=mystery, hero_name=name, hero_type=hero_type, helper_type=helper_type)


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------

def _hero_pronoun(hero: Entity, case: str = "subject") -> str:
    return hero.pronoun(case)


def _build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)

    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_type))
    pumpkin = world.add(Entity(id="pumpkin", kind="thing", type="pumpkin", label="pumpkin", phrase="a round orange pumpkin"))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label="clue", phrase=f"a {mystery.clue_word} clue"))
    suspect = world.add(Entity(id="suspect", kind="thing", type=mystery.culprit, label=mystery.culprit, phrase=f"a funny-looking {mystery.culprit}"))

    pumpkin.location = setting.place
    clue.location = setting.place
    suspect.location = setting.place

    world.facts.update(hero=hero, helper=helper, pumpkin=pumpkin, clue=clue, suspect=suspect)
    return world


def _introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    pumpkin: Entity = world.facts["pumpkin"]  # type: ignore[assignment]
    world.say(
        f"{hero.label} loved adventure stories, especially ones with a pumpkin in them."
    )
    world.say(
        f"One day, {hero.label} and {helper.type} went to {world.setting.place} to help with {pumpkin.phrase}."
    )


def _raise_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    world.para()
    world.say(
        f"But something funny had happened: {mystery.label} was {mystery.risk_word}."
    )
    world.say(
        f"{hero.label} spotted a {mystery.clue_word} mark near the dirt and said, "
        f"\"That looks like a clue, not a lunch snack.\""
    )
    world.humor_level += 1


def _search(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    suspect: Entity = world.facts["suspect"]  # type: ignore[assignment]
    clue: Entity = world.facts["clue"]  # type: ignore[assignment]

    world.para()
    world.say(
        f"{hero.label} and {helper.type} followed the clue along the path."
    )
    world.say(
        f"They checked behind a crate, under a hay bale, and beside a boot that looked far too proud of itself."
    )
    world.say(
        f"At last, they found {suspect.phrase} near {mystery.solution_word}."
    )
    world.clues_found.extend([mystery.clue_word, mystery.solution_word])
    world.suspects.append(suspect.type)
    clue.meters["found"] = 1
    world.humor_level += 1
    world.say(
        f"{hero.label} laughed and said, \"I knew the {mystery.humor_word} was trying to act mysterious.\""
    )


def _solve(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    pumpkin: Entity = world.facts["pumpkin"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery

    world.para()
    world.say(
        f"Then the last clue made sense: the pumpkin had rolled into the {mystery.solution_word} by accident."
    )
    world.say(
        f"{helper.type} pulled it out while {hero.label} kept watch like a tiny detective."
    )
    world.solution_found = True
    pumpkin.location = "safe"
    pumpkin.memes["relief"] = 1
    pumpkin.meters["scratches"] = 0
    world.say(
        f"In the end, {mystery.ending_image}."
    )
    world.say(
        f"{hero.label} grinned, {helper.type} chuckled, and the whole patch felt cheerful again."
    )


def tell(world: World) -> None:
    _introduce(world)
    _raise_mystery(world)
    _search(world)
    _solve(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    return [
        f"Write a short adventure story about {hero.label} and a pumpkin mystery that gets solved with a funny clue.",
        f"Tell a child-friendly story set at {world.setting.place} where a pumpkin is missing and the answer is a little silly.",
        f"Write a playful mystery story with a pumpkin, a clue, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    mystery: Mystery = world.mystery
    pumpkin: Entity = world.facts["pumpkin"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who went to {world.setting.place} to help with the pumpkin?",
            answer=f"{hero.label} went with the {helper.type} to help with the pumpkin.",
        ),
        QAItem(
            question="What was the mystery in the story?",
            answer=f"The mystery was {mystery.label}, which looked {mystery.risk_word} at first.",
        ),
        QAItem(
            question="How did they solve the mystery?",
            answer=f"They followed a clue, found the pumpkin near {mystery.solution_word}, and pulled it out safely.",
        ),
        QAItem(
            question="What was the ending image?",
            answer=f"The ending showed {mystery.ending_image}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery: Mystery = world.mystery
    return [
        QAItem(
            question="What is a pumpkin?",
            answer="A pumpkin is a round orange squash. People often use it for cooking, decorating, or carving.",
        ),
        QAItem(
            question="Why can a mystery story be fun?",
            answer="A mystery story is fun because there are clues to follow, and the answer comes as a surprise.",
        ),
        QAItem(
            question="Why do people laugh in a funny adventure?",
            answer="People laugh when something silly happens, like a goat acting important or a clue looking like a snack.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).
valid(S,M) :- setting(S), mystery(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_fact", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    if cl - py:
        print("only in clingo:", sorted(cl - py))
    if py - cl:
        print("only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.location:
            parts.append(f"location={e.location}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  clues found: {world.clues_found}")
    lines.append(f"  solution found: {world.solution_found}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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


def explain_rejection() -> str:
    return "That combination would not make a clear pumpkin mystery adventure."


CURATED = [
    StoryParams(setting="pumpkin_patch", mystery="missing_pumpkin", hero_name="Maya", hero_type="girl", helper_type="grandpa"),
    StoryParams(setting="barn_path", mystery="silly_carving", hero_name="Theo", hero_type="boy", helper_type="mother"),
    StoryParams(setting="lantern_square", mystery="lost_pumpkin_seed", hero_name="Nora", hero_type="girl", helper_type="father"),
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
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.setting} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
