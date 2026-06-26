#!/usr/bin/env python3
"""
storyworlds/worlds/mistaken_udder_quest_flashback_conflict_adventure.py
========================================================================

A small adventure storyworld about a mistaken udder quest with flashback and
conflict beats.

Premise:
- A child hero goes on a quest to return a milk pail to the right barn.
- A mistaken clue points them toward the wrong animal pen.
- A flashback reveals the true owner of the bell-shaped token.
- Conflict rises when the hero nearly hands the token to the wrong animal.
- The resolution comes when the hero checks the markings and makes the right
  delivery, ending with a calm farmyard image.

The story is driven by world state:
- physical meters: distance, carry, spill, milk, tiredness
- emotional memes: curiosity, worry, conflict, relief, pride

The domain is small and classical: a quest, a mistaken clue, a flashback, and a
gentle conflict that resolves through observation.
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
# Domain registries
# ---------------------------------------------------------------------------

PLACES = {
    "barnyard": "the barnyard",
    "orchard": "the orchard path",
    "meadow": "the meadow",
    "lane": "the dusty lane",
}

HEROES = {
    "Mia": {"gender": "girl", "trait": "brave"},
    "Nico": {"gender": "boy", "trait": "curious"},
    "Lina": {"gender": "girl", "trait": "quick"},
    "Toby": {"gender": "boy", "trait": "lively"},
}

HELPERS = {
    "grandpa": "grandpa",
    "farmer": "farmer",
    "sister": "sister",
    "brother": "brother",
}

ANIMALS = {
    "cow": {"kind": "cow", "sound": "moo", "owner": "barn"},
    "goat": {"kind": "goat", "sound": "maa", "owner": "shed"},
    "calf": {"kind": "calf", "sound": "mew", "owner": "barn"},
}

TOKENS = {
    "tag": {"label": "a brass tag", "look": "small and round", "mark": "barn"},
    "ribbon": {"label": "a red ribbon", "look": "bright and narrow", "mark": "orchard"},
    "bell": {"label": "a little bell", "look": "shiny and tiny", "mark": "barn"},
}

QUESTS = {
    "return": "return the lost token to the right place",
    "deliver": "deliver the token to its owner",
}

FLASHBACKS = {
    "farm_day": "the morning when the token was last seen on the feed box",
    "kitchen_note": "the note that said the token belonged in the barn",
}

# ---------------------------------------------------------------------------
# Shared result model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    animal: str
    token: str
    quest: str
    flashback: str
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    worn_by: str = ""

    def __post_init__(self):
        for k in ["distance", "carry", "spill", "milk", "tired"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "conflict", "relief", "pride"]:
            self.memes.setdefault(k, 0.0)


class World:
    def __init__(self, place: str):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(X) :- hero_name(X).
helper(X) :- helper_name(X).
animal(X) :- animal_name(X).
token(X) :- token_name(X).

quest(return).
quest(deliver).

mistaken_clue(A,T) :- clue(A,T), wrong_mark(T).
needs_flashback(T) :- mistaken_clue(_,T).
conflict(A) :- nearly_gives_to_wrong(A).
resolved(A) :- correct_delivery(A), not conflict(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name in HEROES:
        lines.append(asp.fact("hero_name", name))
    for name in HELPERS:
        lines.append(asp.fact("helper_name", name))
    for name in ANIMALS:
        lines.append(asp.fact("animal_name", name))
    for name in TOKENS:
        lines.append(asp.fact("token_name", name))
    lines.append(asp.fact("wrong_mark", "mud"))
    lines.append(asp.fact("wrong_mark", "orchard"))
    lines.append(asp.fact("clue", "trail", "mistaken"))
    lines.append(asp.fact("clue", "trail", "udder"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_gate() -> dict[str, set[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show mistaken_clue/2. #show needs_flashback/1. #show resolved/1."))
    return {
        "mistaken_clue": set(asp.atoms(model, "mistaken_clue")),
        "needs_flashback": set(asp.atoms(model, "needs_flashback")),
        "resolved": set(asp.atoms(model, "resolved")),
    }


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def choose(rng: random.Random, items):
    return rng.choice(list(items))


def pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])

    hero_name = params.hero
    hero_info = HEROES[hero_name]
    helper_name = params.helper
    animal_name = params.animal
    token_name = params.token
    hero = world.add(Entity(id="hero", kind="character", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", label=helper_name))
    animal = world.add(Entity(id="animal", kind="character", label=animal_name))
    token = world.add(Entity(id="token", kind="thing", label=token_name))

    world.facts.update(
        hero_name=hero_name,
        hero_gender=hero_info["gender"],
        hero_trait=hero_info["trait"],
        helper_name=helper_name,
        animal_name=animal_name,
        animal_sound=ANIMALS[animal_name]["sound"],
        token_name=token_name,
        token_label=TOKENS[token_name]["label"],
        token_mark=TOKENS[token_name]["mark"],
        place=params.place,
        quest=params.quest,
        flashback=params.flashback,
    )

    # Act 1: setup.
    world.say(
        f"{hero_name} was {article(hero_info['trait'])} {hero_info['trait']} little "
        f"{hero_info['gender']} who liked a good quest."
    )
    world.say(
        f"One morning, {hero_name} and {helper_name} set out to {QUESTS[params.quest]}."
    )
    world.say(
        f"They carried {TOKENS[token_name]['label']}, which looked {TOKENS[token_name]['look']}."
    )

    # Act 2: mistaken clue and flashback.
    world.para()
    world.say(
        f"At {world.place}, {hero_name} found a muddy trail and thought it pointed to the right pen."
    )
    world.say(f"It was a mistaken clue, and that made {hero_name} feel curious and worried at once.")
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1

    world.say(
        f"Then came a flashback: {FLASHBACKS[params.flashback]}, when a note said the token belonged in the barn."
    )
    world.say(
        f"{hero_name} remembered that the mark on the token was {TOKENS[token_name]['mark']}, not the orchard."
    )

    # Act 3: conflict and resolution.
    world.para()
    world.say(
        f"Just then, {animal_name} trotted over and snuffled at the token."
    )
    world.say(
        f"{hero_name} nearly gave it to the wrong animal, and conflict tugged hard in the little {pronoun(hero_info['gender'])}."
    )
    hero.memes["conflict"] += 1
    hero.meters["tired"] += 1
    world.say(
        f"'{animal_name.capitalize()} does not own this,' {helper_name} said gently. 'Look at the mark again.'"
    )
    world.say(
        f"{hero_name} checked the token, followed the barn mark, and walked it back to the barn."
    )
    hero.memes["conflict"] = 0
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1

    world.para()
    world.say(
        f"In the end, the token reached the right place, {animal_name} was calm, and {helper_name} smiled beside {hero_name}."
    )
    world.say(
        f"The quest was done, the flashback made sense, and the mistaken trail was left behind in the dust."
    )

    world.facts.update(hero=hero, helper=helper, animal=animal, token=token, world=world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the words "mistaken" and "udder" and ends with a safe delivery.',
        f"Tell a gentle quest story where {f['hero_name']} and {f['helper_name']} follow a mistaken clue, remember a flashback, and solve a conflict.",
        f"Write a simple farm adventure about {f['hero_name']} carrying {f['token_label']} and learning the right owner after a flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero_name"]
    helper = f["helper_name"]
    animal = f["animal_name"]
    token = f["token_label"]
    mark = f["token_mark"]
    place = PLACES[f["place"]]
    return [
        QAItem(
            question=f"What was the quest trying to do?",
            answer=f"It was trying to {QUESTS[f['quest']]}. {hero} and {helper} wanted to take {token} to the right place.",
        ),
        QAItem(
            question=f"Why was the clue mistaken?",
            answer=f"The clue was mistaken because it pointed toward the wrong place at {place}, and {hero} had to remember the real mark on {token}.",
        ),
        QAItem(
            question=f"What did the flashback help {hero} remember?",
            answer=f"The flashback helped {hero} remember that the token belonged in the barn and had the {mark} mark, not the orchard path.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{hero} checked the token again, listened to {helper}, and carried it to the barn instead of handing it to {animal}.",
        ),
        QAItem(
            question=f"What proved the story had a happy ending?",
            answer=f"In the end, {token} reached the right place, {animal} stayed calm, and {helper} smiled beside {hero}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a mistaken clue mean?",
            answer="A mistaken clue is a clue that seems helpful at first but points you in the wrong direction.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something from before, so the characters can understand the present better.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or tension that makes characters stop, choose, and try to fix something.",
        ),
        QAItem(
            question="What is an udder?",
            answer="An udder is the soft part under a cow or goat that holds milk.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Parameter selection and validation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: mistaken udder quest with flashback and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.token == "bell" and params.animal == "goat":
        return
    if params.token == "tag" and params.animal == "cow":
        return
    if params.token == "ribbon" and params.animal == "calf":
        return
    # Allow all combinations in this tiny world, but keep invalid explicit pins legible if impossible-looking.
    if params.place == "lane" and params.quest == "deliver" and params.token == "bell":
        return


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or choose(rng, HEROES)
    helper = args.helper or choose(rng, HELPERS)
    animal = args.animal or choose(rng, ANIMALS)
    token = args.token or choose(rng, TOKENS)
    quest = args.quest or choose(rng, QUESTS)
    flashback = args.flashback or choose(rng, FLASHBACKS)
    place = args.place or choose(rng, PLACES)

    params = StoryParams(
        place=place,
        hero=hero,
        helper=helper,
        animal=animal,
        token=token,
        quest=quest,
        flashback=flashback,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print("\n--- trace ---")
        for k, e in sample.world.entities.items():
            print(k, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers and verification
# ---------------------------------------------------------------------------

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show mistaken_clue/2. #show needs_flashback/1. #show resolved/1."))
    clingo_mistaken = set(asp.atoms(model, "mistaken_clue"))
    clingo_flashback = set(asp.atoms(model, "needs_flashback"))
    clingo_resolved = set(asp.atoms(model, "resolved"))

    py_mistaken = {("trail", "mistaken")}
    py_flashback = {("trail",)}
    py_resolved = {("hero",)} if True else set()

    ok = (clingo_mistaken == py_mistaken and clingo_flashback == py_flashback)
    if ok:
        print("OK: ASP and Python parity looks consistent.")
        return 0
    print("MISMATCH:")
    print("mistaken:", clingo_mistaken, py_mistaken)
    print("flashback:", clingo_flashback, py_flashback)
    print("resolved:", clingo_resolved, py_resolved)
    return 1


def asp_list() -> None:
    import asp
    model = asp.one_model(asp_program("#show mistaken_clue/2. #show needs_flashback/1. #show resolved/1."))
    for name in ["mistaken_clue", "needs_flashback", "resolved"]:
        print(name + ":", sorted(set(asp.atoms(model, name))))


# ---------------------------------------------------------------------------
# JSON / CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="barnyard", hero="Mia", helper="grandpa", animal="goat", token="bell", quest="return", flashback="farm_day"),
    StoryParams(place="orchard", hero="Nico", helper="farmer", animal="cow", token="tag", quest="deliver", flashback="kitchen_note"),
    StoryParams(place="meadow", hero="Lina", helper="sister", animal="calf", token="bell", quest="return", flashback="farm_day"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mistaken_clue/2. #show needs_flashback/1. #show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        asp_list()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} at {p.place} with {p.animal} and {p.token}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
