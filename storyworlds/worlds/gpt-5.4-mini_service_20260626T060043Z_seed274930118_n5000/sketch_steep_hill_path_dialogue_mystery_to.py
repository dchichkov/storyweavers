#!/usr/bin/env python3
"""
A small comedy storyworld set on a steep hill path.

Premise:
- A child takes a sketch on a hill walk.
- A mystery appears: odd marks, a missing thing, or a strange sound.
- Through dialogue, the characters solve it in a funny but grounded way.

The world model uses physical meters and emotional memes, and the prose is
state-driven rather than a template swap.
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

HILL_TERRAIN = "steep hill path"
MYSTERY_TAG = "mystery"
COMEDY_TAG = "comedy"
SKETCH_TAG = "sketch"


@dataclass
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Item:
    id: str
    kind: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    place: str
    slope: str = "steep"
    weather: str = "clear"
    characters: dict[str, Character] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add_character(self, c: Character) -> Character:
        self.characters[c.id] = c
        return c

    def add_item(self, it: Item) -> Item:
        self.items[it.id] = it
        return it

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
        return _copy.deepcopy(self)


@dataclass
class StoryParams:
    hero_name: str
    hero_type: str
    companion_name: str
    companion_type: str
    mystery: str
    seed: Optional[int] = None


SETTINGS = {
    "steep hill path": {"tag": HILL_TERRAIN, "safe_spots": {"flat spot", "bench", "path bend"}},
}

MYSTERIES = {
    "missing pencil": {
        "label": "missing pencil",
        "cause": "it had rolled into a shoe",
        "solve_by": "looking inside the big boot",
        "found_in": "a muddy boot",
    },
    "funny marks": {
        "label": "funny marks",
        "cause": "a gust of wind flipped the sketch page over",
        "solve_by": "turning the sketchbook around",
        "found_in": "the back of the sketchbook",
    },
    "mystery whistle": {
        "label": "mystery whistle",
        "cause": "a kettle at the hill tea cart was singing",
        "solve_by": "following the whistling sound",
        "found_in": "the tea cart",
    },
}

GIRL_NAMES = ["Mia", "Zoe", "Lily", "Ava", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Max", "Finn", "Theo", "Ben", "Jack"]
COMPANION_TYPES = ["parent", "friend", "uncle", "aunt"]


class WorldModel:
    def __init__(self, world: World) -> None:
        self.world = world
        self.fired: set[str] = set()

    def climb_strain(self, name: str) -> None:
        c = self.world.characters[name]
        c.meters["strain"] = c.meters.get("strain", 0) + 1

    def curiosity(self, name: str) -> None:
        c = self.world.characters[name]
        c.memes["curious"] = c.memes.get("curious", 0) + 1

    def amusement(self, name: str) -> None:
        c = self.world.characters[name]
        c.memes["amused"] = c.memes.get("amused", 0) + 1

    def worry(self, name: str) -> None:
        c = self.world.characters[name]
        c.memes["worry"] = c.memes.get("worry", 0) + 1

    def relieve(self, name: str) -> None:
        c = self.world.characters[name]
        c.memes["worry"] = max(0, c.memes.get("worry", 0) - 1)
        c.memes["joy"] = c.memes.get("joy", 0) + 1


def reasonableness(params: StoryParams) -> None:
    if params.hero_name == params.companion_name:
        raise StoryError("The hero and companion must be different characters.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.hero_type not in {"girl", "boy"}:
        raise StoryError("Hero type must be girl or boy.")
    if params.companion_type not in COMPANION_TYPES:
        raise StoryError("Unknown companion type.")


def build_world(params: StoryParams) -> World:
    world = World(place=HILL_TERRAIN)
    hero = world.add_character(Character(id=params.hero_name, type=params.hero_type))
    companion = world.add_character(Character(id=params.companion_name, type=params.companion_type))
    sketchbook = world.add_item(Item(id="sketchbook", label="sketchbook", owner=hero.id, carried_by=hero.id))
    pencil = world.add_item(Item(id="pencil", label="pencil", owner=hero.id, carried_by=hero.id))
    mystery = world.add_item(Item(id="mystery", label=MYSTERIES[params.mystery]["label"], hidden=True))

    hero.memes["curious"] = 1
    hero.meters["footsteps"] = 0
    companion.memes["patient"] = 1
    world.facts.update(params=params, hero=hero, companion=companion, sketchbook=sketchbook, pencil=pencil, mystery=mystery)
    return world


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    model = WorldModel(world)
    hero = world.characters[params.hero_name]
    companion = world.characters[params.companion_name]
    mystery = world.items["mystery"]
    sketchbook = world.items["sketchbook"]
    pencil = world.items["pencil"]
    mystery_def = MYSTERIES[params.mystery]

    world.say(f"{hero.id} went up the {HILL_TERRAIN} with a sketchbook tucked under one arm.")
    world.say(f"{hero.id} loved to sketch silly things, especially on days when the hill felt big and dramatic.")
    world.say(f"{companion.id} walked beside {hero.pronoun('object')} and said, \"Careful on the steep bits.\"")
    world.say(f"{hero.id} grinned. \"I am being careful. My knees are just doing their funny little climbing dance.\"")

    world.para()
    model.climb_strain(hero.id)
    model.climb_strain(companion.id)
    world.say(f"Halfway up, {hero.id} stopped so fast that {companion.id} almost turned into a wobble.")
    world.say(f"\"Wait,\" {hero.id} said. \"Where did my pencil go?\"")
    world.say(f"\"It was in your hand a moment ago,\" {companion.id} said. \"Did the hill eat it?\"")
    model.curiosity(hero.id)
    model.worry(companion.id)

    world.para()
    world.say(f"They looked at the path, the grass, and the little flat stones by the side.")
    if params.mystery == "missing pencil":
        world.say(f"\"Maybe it rolled,\" {companion.id} said. \"This path is so steep it could send a potato on vacation.\"")
        world.say(f"\"My pencil is not a potato,\" {hero.id} said, then laughed anyway.")
        world.say(f"They followed the tiny trail of worry and found it inside a muddy boot by the path.")
        pencil.found = True
        pencil.hidden = False
        pencil.carried_by = hero.id
        mystery.hidden = False
        world.say(f"\"A boot?\" {hero.id} said. \"That pencil is sneaky.\"")
        world.say(f"\"It probably wanted a better view,\" {companion.id} said.")
    elif params.mystery == "funny marks":
        world.say(f"\"Maybe a monster drew them,\" {hero.id} whispered.")
        world.say(f"\"A very tidy monster,\" {companion.id} said, squinting at the page.")
        world.say(f"{companion.id} turned the sketchbook around, and the marks made sense at once.")
        sketchbook.found = True
        mystery.hidden = False
        world.say(f"\"Oh!\" said {hero.id}. \"The page was upside down. The hill did not make nonsense. I did.\"")
    else:
        world.say(f"\"Do you hear that whistle?\" {hero.id} asked.")
        world.say(f"\"Yes,\" said {companion.id}. \"That sound is either a bird, a kettle, or a very proud shoe.\"")
        world.say(f"They followed the whistle to the tea cart near the bend.")
        mystery.hidden = False
        world.say(f"A kettle there was singing away like it wanted applause, and the mystery was solved.")
        world.say(f"\"I blame the kettle's stage career,\" {hero.id} said.")
    model.amusement(hero.id)
    model.amusement(companion.id)

    world.para()
    world.say(f"{hero.id} sat on a flat stone, opened the sketchbook, and drew the funniest hill they had ever seen.")
    world.say(f"This hill had a heroic slope, a dramatic boot, and a pencil that looked far too pleased with itself.")
    world.say(f"{companion.id} peeked over and laughed. \"Now that is a proper mystery picture.\"")
    world.say(f"{hero.id} smiled. \"And the best part is, we solved it without the hill eating anyone.\"")
    model.relieve(companion.id)
    model.relieve(hero.id)

    world.facts["resolved"] = True
    world.facts["ending"] = "The sketchbook stayed safe, and the hill got turned into a joke on paper."
    return world


def prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    mystery = MYSTERIES[params.mystery]["label"]
    return [
        f'Write a funny story for young children set on a "{HILL_TERRAIN}" with a sketchbook and a small mystery.',
        f"Tell a comedy where {params.hero_name} and {params.companion_name} climb a steep hill path, talk a lot, and solve the {mystery}.",
        f'Write a gentle dialogue story that begins with a sketch and ends with the mystery on the hill being explained.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    m = MYSTERIES[p.mystery]
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    qa = [
        QAItem(
            question=f"Who went up the {HILL_TERRAIN} with a sketchbook?",
            answer=f"{hero.id} went up the {HILL_TERRAIN} with {companion.id} beside {hero.pronoun('object')}.",
        ),
        QAItem(
            question=f"What was the mystery in the story?",
            answer=f"The mystery was the {m['label']}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} solve it?",
            answer=f"They solved it by talking, looking carefully, and using the clue that led them to {m['found_in']}.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} sat down and made a funny sketch of the hill after the mystery was solved.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a sketchbook for?",
            answer="A sketchbook is a book for drawings and quick pictures.",
        ),
        QAItem(
            question="Why do people walk carefully on a steep hill path?",
            answer="People walk carefully on a steep hill path because the ground can be hard to climb and easy to slip on.",
        ),
        QAItem(
            question="Why are questions and answers helpful in a mystery?",
            answer="Questions and answers help people compare clues until the confusing part makes sense.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    reasonableness(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for c in world.characters.values():
        meters = {k: v for k, v in c.meters.items() if v}
        memes = {k: v for k, v in c.memes.items() if v}
        lines.append(f"  {c.id} ({c.type}) meters={meters} memes={memes}")
    for i in world.items.values():
        bits = []
        if i.owner:
            bits.append(f"owner={i.owner}")
        if i.carried_by:
            bits.append(f"carried_by={i.carried_by}")
        if i.hidden:
            bits.append("hidden=True")
        if i.found:
            bits.append("found=True")
        lines.append(f"  {i.id} ({i.label}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy mystery storyworld on a steep hill path.")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--companion-type", choices=COMPANION_TYPES)
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
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
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    companion_type = args.companion_type or rng.choice(COMPANION_TYPES)
    companion_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != hero_name]
    companion_name = args.companion_name or rng.choice(companion_pool)
    mystery = args.mystery or rng.choice(sorted(MYSTERIES))
    params = StoryParams(
        hero_name=hero_name,
        hero_type=hero_type,
        companion_name=companion_name,
        companion_type=companion_type,
        mystery=mystery,
    )
    reasonableness(params)
    return params


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
hero(H) :- hero_name(H).
companion(C) :- companion_name(C).
mystery(M) :- mystery_name(M).

good_story(H,C,M) :- hero(H), companion(C), H != C, mystery(M).

#show good_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("hero_name", n))
    for n in GIRL_NAMES + BOY_NAMES:
        lines.append(asp.fact("companion_name", n))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_name", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid())
    py_set = set((h, c, m) for h in GIRL_NAMES + BOY_NAMES for c in GIRL_NAMES + BOY_NAMES for m in MYSTERIES if h != c)
    if clingo_set == py_set:
        print(f"OK: clingo gate matches python gate ({len(clingo_set)} combinations).")
        return 0
    print("MISMATCH between clingo and python gates.")
    if clingo_set - py_set:
        print(" only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print(" only in python:", sorted(py_set - clingo_set))
    return 1


CURATED = [
    StoryParams("Mia", "girl", "Dad", "father", "missing pencil"),
    StoryParams("Leo", "boy", "Aunt June", "aunt", "funny marks"),
    StoryParams("Nora", "girl", "Uncle Ben", "uncle", "mystery whistle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show good_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
