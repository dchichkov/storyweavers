#!/usr/bin/env python3
"""
storyworlds/worlds/village_kindness_mystery_to_solve_mystery.py
==============================================================

A small child-facing story world about a village mystery that can be solved by
kindness. The story is state-driven: a puzzling loss creates tension, clues
narrow the possibilities, and a gentle act of help reveals the answer.

Seed inspiration:
- village
- Kindness
- Mystery to Solve
- Style: mystery

The world is intentionally tiny and classical:
- one village setting
- one mystery object
- one child protagonist
- one careful helper
- one honest resolution where kindness unlocks the answer
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# Core domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACE_NAMES = ["village square", "old village lane", "little village green", "stone village bridge"]
HERO_NAMES = ["Mina", "Toby", "Lina", "Noah", "Pia", "Ezra", "Ivy", "Sami"]
HELPER_NAMES = ["Mrs. Reed", "Old Bram", "Nana Jo", "Mr. Alder"]
VILLAGER_NAMES = ["Jessa", "Corin", "Milo", "Rina", "Bert", "Tessa"]
TRAITS = ["curious", "gentle", "brave", "patient", "careful"]

MYSTERY_OBJECTS = {
    "bell": {
        "label": "silver bell",
        "phrase": "a little silver bell with a blue ribbon",
        "place": "the village square",
        "clue": "a blue ribbon",
        "sound": "a tiny jingle",
        "missing_beat": "the square felt too quiet without it",
    },
    "lantern": {
        "label": "glass lantern",
        "phrase": "a round glass lantern with a brass handle",
        "place": "the village lane",
        "clue": "warm candle wax",
        "sound": "a soft clink",
        "missing_beat": "the lane looked dim without it",
    },
    "bake": {
        "label": "recipe card",
        "phrase": "a flour-dusted recipe card with neat little notes",
        "place": "the bakery porch",
        "clue": "a dusting of flour",
        "sound": "a paper flutter",
        "missing_beat": "the bakery felt puzzled without it",
    },
}

HELPFUL_ACTIONS = {
    "listen": "listen carefully",
    "share": "share a snack",
    "carry": "carry a heavy basket",
    "comfort": "comfort a worried neighbor",
}

# ---------------------------------------------------------------------------
# Story model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str = "the village square"


@dataclass
class Mystery:
    key: str
    label: str
    phrase: str
    place: str
    clue: str
    sound: str
    missing_beat: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace_notes: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Reasonable mystery gate
# ---------------------------------------------------------------------------

def mystery_requires_kindness(mystery: Mystery) -> bool:
    return mystery.key in MYSTERY_OBJECTS


def reasonableness_check(mystery: Mystery, helper_action: str) -> None:
    if mystery.key not in MYSTERY_OBJECTS:
        raise StoryError("The village mystery object is not recognized.")
    if helper_action not in HELPFUL_ACTIONS:
        raise StoryError("The helper action must be a kind, concrete action.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solvable when there is a clue and a kindness action that helps
% the worried village member speak honestly.
mystery(M).
clue_for(M, C) :- mystery(M), clue(M, C).
kind_action(A) :- help_action(A).
solves(M) :- mystery(M), clue_for(M, _), kind_action(_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key, data in MYSTERY_OBJECTS.items():
        lines.append(asp.fact("mystery", key))
        lines.append(asp.fact("clue", key, data["clue"]))
        lines.append(asp.fact("place_of", key, data["place"]))
    for act in HELPFUL_ACTIONS:
        lines.append(asp.fact("help_action", act))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solves/1."))
    asp_solutions = sorted(set(asp.atoms(model, "solves")))
    py_solutions = sorted((k,) for k in MYSTERY_OBJECTS)
    if set(asp_solutions) == set(py_solutions):
        print(f"OK: clingo gate matches Python registry ({len(py_solutions)} mysteries).")
        return 0
    print("MISMATCH between clingo and Python registry:")
    if set(asp_solutions) - set(py_solutions):
        print("  only in clingo:", sorted(set(asp_solutions) - set(py_solutions)))
    if set(py_solutions) - set(asp_solutions):
        print("  only in python:", sorted(set(py_solutions) - set(asp_solutions)))
    return 1


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    trait: str
    action: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def set_up_world(params: StoryParams) -> World:
    setting = Setting(place=params.place)
    world = World(setting)
    mystery_cfg = MYSTERY_OBJECTS[params.mystery]
    mystery = Mystery(key=params.mystery, **mystery_cfg)

    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type="girl" if params.hero in {"Mina", "Lina", "Pia", "Ivy"} else "boy",
        meters={"curiosity": 1.0},
        memes={"worry": 0.0, "hope": 0.0, "kindness": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="woman" if params.helper in {"Mrs. Reed", "Nana Jo"} else "man",
        meters={"care": 1.0},
        memes={"worry": 0.0, "kindness": 1.0},
    ))
    object_ent = world.add(Entity(
        id="mystery-object",
        type=mystery.label,
        label=mystery.label,
        phrase=mystery.phrase,
        owner=params.helper,
        caretaker=params.helper,
        location=mystery.place,
        hidden=True,
        meters={"missing": 1.0},
        memes={"mystery": 1.0},
    ))

    villager = world.add(Entity(
        id="villager",
        kind="character",
        type="woman",
        meters={"tired": 1.0},
        memes={"worry": 1.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        villager=villager,
        object_ent=object_ent,
        mystery=mystery,
        action=params.action,
    )
    return world


def _narrate_setup(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    world.say(
        f"In the village, {hero.id} was a {world.facts['trait']} child who loved quiet streets and small clues."
    )
    world.say(
        f"One morning, the villagers noticed that {mystery.phrase} was gone from {mystery.place}."
    )
    world.say(
        f"{mystery.missing_beat.capitalize()}, and everyone kept asking the same question: where could it be?"
    )


def _narrate_search(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    world.para()
    hero.memes["worry"] += 1.0
    hero.memes["hope"] += 1.0
    world.say(
        f"{hero.id} followed the first clue, a faint {mystery.clue}, down the lane."
    )
    world.say(
        f"At first, {hero.id} wondered if someone had taken it for themselves."
    )
    world.say(
        f"Then {hero.id} saw {helper.id} sitting very still beside the road, looking tired and sad."
    )


def _narrate_kindness(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    villager = world.facts["villager"]
    mystery = world.facts["mystery"]
    action = world.facts["action"]

    world.para()
    hero.memes["kindness"] += 1.0
    helper.memes["kindness"] += 1.0
    world.say(
        f"{hero.id} chose to {HELPFUL_ACTIONS[action]} instead of accusing anyone."
    )
    world.say(
        f"That small kindness made {helper.id} relax, and {helper.id} finally spoke up."
    )
    world.say(
        f"{helper.id} had borrowed the {mystery.label} to light {villager.id}'s dark room while {villager.id} was ill."
    )
    world.say(
        f"The missing object had not been stolen at all; it had been used to help someone."
    )
    mystery_ent = world.facts["object_ent"]
    mystery_ent.hidden = False
    mystery_ent.location = mystery.place
    mystery_ent.meters["missing"] = 0.0
    mystery_ent.memes["mystery"] = 0.0


def _narrate_resolution(world: World) -> None:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    villager = world.facts["villager"]
    mystery = world.facts["mystery"]
    action = world.facts["action"]
    world.para()
    world.say(
        f"Together, they carried the {mystery.label} back to {mystery.place}."
    )
    world.say(
        f"{villager.id} smiled when the village saw the {mystery.sound} again."
    )
    world.say(
        f"{hero.id} learned that a mystery can sometimes be solved by looking with a kind heart first."
    )
    world.say(
        f"By evening, the village was warm and calm, and the {mystery.label} shone where it belonged."
    )


def tell_story(params: StoryParams) -> World:
    world = set_up_world(params)
    _narrate_setup(world)
    _narrate_search(world)
    _narrate_kindness(world)
    _narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    m = world.facts["mystery"]
    hero = world.facts["hero"]
    return [
        f"Write a short mystery story set in a village where {hero.id} solves the problem with kindness.",
        f"Tell a gentle village mystery about a missing {m.label} and a child who helps before jumping to conclusions.",
        f"Create a child-friendly story with clues, a worried helper, and a kind ending in the village.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    mystery = world.facts["mystery"]
    villager = world.facts["villager"]
    action = world.facts["action"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} notice in the village?",
            answer=f"{hero.id} noticed that {mystery.phrase} was missing from {mystery.place}.",
        ),
        QAItem(
            question=f"Why did {hero.id} stop being suspicious of {helper.id}?",
            answer=(
                f"{hero.id} saw {helper.id} looking tired and chose to be kind instead of accusing {helper.id}."
            ),
        ),
        QAItem(
            question=f"How was the mystery solved?",
            answer=(
                f"It was solved when {hero.id} chose to {HELPFUL_ACTIONS[action]}, and {helper.id} explained that the {mystery.label} was borrowed to help {villager.id}."
            ),
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=(
                f"The {mystery.label} was returned to {mystery.place}, and the village felt calm and happy again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something gentle or helpful for someone else.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you need clues to understand.",
        ),
        QAItem(
            question="Why do people look for clues in a mystery?",
            answer="People look for clues because clues help them figure out what happened.",
        ),
        QAItem(
            question="What is a village?",
            answer="A village is a small place where people live close together and know one another.",
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
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:14} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Validation / params
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACE_NAMES:
        for mystery in MYSTERY_OBJECTS:
            for hero in HERO_NAMES:
                for helper in HELPER_NAMES:
                    combos.append((place, mystery, hero, helper))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero: str
    helper: str
    trait: str
    action: str
    seed: Optional[int] = None


def explain_rejection() -> str:
    return "No story fits that combination in this village mystery world."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small village mystery solved by kindness.")
    ap.add_argument("--place", choices=PLACE_NAMES)
    ap.add_argument("--mystery", choices=sorted(MYSTERY_OBJECTS))
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--action", choices=sorted(HELPFUL_ACTIONS))
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
    place = args.place or rng.choice(PLACE_NAMES)
    mystery = args.mystery or rng.choice(list(MYSTERY_OBJECTS))
    hero = args.hero or rng.choice(HERO_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    action = args.action or rng.choice(list(HELPFUL_ACTIONS))
    reasonableness_check(MYSTERY_OBJECTS[mystery] | {"key": mystery}, action)  # type: ignore[arg-type]
    return StoryParams(place=place, mystery=mystery, hero=hero, helper=helper, trait=trait, action=action)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solves/1."))
    return sorted(set(asp.atoms(model, "solves")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="village square", mystery="bell", hero="Mina", helper="Mrs. Reed", trait="curious", action="listen"),
    StoryParams(place="old village lane", mystery="lantern", hero="Toby", helper="Old Bram", trait="careful", action="share"),
    StoryParams(place="little village green", mystery="bake", hero="Lina", helper="Nana Jo", trait="gentle", action="comfort"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solves/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show solves/1."))
        sols = sorted(set(asp.atoms(model, "solves")))
        for s in sols:
            print(s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            rng = random.Random(seed)
            i += 1
            params = resolve_params(args, rng)
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
            header = f"### {p.hero}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
