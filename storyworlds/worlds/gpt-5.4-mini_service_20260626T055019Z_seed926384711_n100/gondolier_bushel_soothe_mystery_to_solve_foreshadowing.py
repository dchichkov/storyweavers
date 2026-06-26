#!/usr/bin/env python3
"""
A small fable-like storyworld about a gondolier, a bushel, and a mystery to solve.

The seed premise:
- A gondolier finds a bushel.
- Something is wrong: a child is upset, a bell goes missing, and clues point to the canal.
- The gondolier uses calm words to soothe nerves, notices foreshadowing clues, and solves the mystery.

This world is intentionally compact: a single domain with a few plausible variants,
grounded in the physical and emotional state of the characters and objects.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "child"}
        male = {"boy", "father", "dad", "man", "gondolier"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str = "the quiet canal"
    water: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    location: str
    value: str
    clues: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    mystery: str
    object: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _noun_phrase(name: str, role: str) -> str:
    if role == "gondolier":
        return f"the gondolier {name}"
    if role == "child":
        return f"the child {name}"
    return f"{role} {name}"


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _capitalize_sentence(text: str) -> str:
    return text[:1].upper() + text[1:] if text else text


def setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        traits=["calm", "wise"],
        meters={"speed": 0.0},
        memes={"care": 1.0, "curiosity": 1.0, "soothe": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
        traits=["small", "frightened"],
        meters={"speed": 0.0},
        memes={"worry": 1.0, "relief": 0.0},
    ))
    obj = OBJECTS[params.object]
    mystery = MYSTERIES[params.mystery]

    target = world.add(Entity(
        id="bushel",
        kind="thing",
        type="bushel",
        label="bushel",
        phrase="a woven bushel",
        owner=hero.id,
        carried_by=hero.id,
        meters={"weight": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=mystery.clue_label,
        phrase=mystery.clue_phrase,
        meters={"notice": 1.0},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=obj.type,
        label=obj.label,
        phrase=obj.phrase,
        owner=helper.id,
        carried_by=None,
        meters={"lost": 1.0},
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        object=missing,
        bushel=target,
        clue=clue,
        mystery=mystery,
        object_spec=obj,
        setting=world.setting,
    )
    return world


def foreshadow(world: World) -> None:
    clue: Entity = world.facts["clue"]
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    mystery: MysterySpec = world.facts["mystery"]

    world.say(
        f"On the edge of {world.setting.place}, {hero.id} carried a bushel and noticed "
        f"{clue.phrase} waiting near the water."
    )
    world.say(
        f"The little sign seemed ordinary at first, but in a fable even ordinary things "
        f"can point toward a secret."
    )
    helper.memes["worry"] += 1.0
    world.say(
        f"{helper.id} looked worried, because {mystery.problem} had left a quiet shadow "
        f"over the morning."
    )


def soothe(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    hero.memes["soothe"] += 1.0
    helper.memes["worry"] = max(0.0, helper.memes["worry"] - 1.0)
    helper.memes["relief"] += 1.0
    world.say(
        f"{hero.id} spoke softly and said that a calm heart can hear what a loud heart misses."
    )
    world.say(
        f"That gentle voice helped {helper.id} breathe again, and the canal seemed less lonely."
    )


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    missing: Entity = world.facts["object"]
    clue: Entity = world.facts["clue"]
    mystery: MysterySpec = world.facts["mystery"]

    world.say(
        f"{hero.id} looked from {clue.label} to the ripples, then to the bushel, and guessed the truth."
    )
    world.say(
        f"The {mystery.solution} had been there all along: {mystery.hidden_place}."
    )
    missing.carried_by = helper.id
    missing.owner = helper.id
    helper.memes["worry"] = 0.0
    helper.memes["relief"] += 1.0
    world.say(
        f"{hero.id} fished it out, and {helper.id} laughed with relief when {missing.phrase} was returned."
    )
    world.say(
        f"In the end, the bushel was still useful, but now it held the lesson that patience sees farther than panic."
    )


@dataclass
class MysterySpec:
    problem: str
    clue_label: str
    clue_phrase: str
    solution: str
    hidden_place: str
    tag: str


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    location: str
    value: str
    clues: set[str] = field(default_factory=set)


SETTINGS = {
    "canal": Setting(place="the quiet canal", water=True, affords={"row", "watch", "listen"}),
    "harbor": Setting(place="the little harbor", water=True, affords={"row", "watch", "listen"}),
    "lagoon": Setting(place="the still lagoon", water=True, affords={"row", "watch", "listen"}),
}

MYSTERIES = {
    "bell": MysterySpec(
        problem="a small bell had gone missing from the boat",
        clue_label="a trail of wet rings",
        clue_phrase="a trail of wet rings",
        solution="the bell had slipped into the bushel",
        hidden_place="it was tucked beneath some grapes in the bushel",
        tag="bell",
    ),
    "key": MysterySpec(
        problem="the boat key had vanished just before the noon ride",
        clue_label="a line of scratch marks",
        clue_phrase="a line of scratch marks",
        solution="the key had fallen into the bushel",
        hidden_place="it was caught under a folded cloth in the bushel",
        tag="key",
    ),
    "shell": MysterySpec(
        problem="a shiny shell had been lost from the child’s pocket",
        clue_label="a silver glint near the planks",
        clue_phrase="a silver glint near the planks",
        solution="the shell had rolled into the bushel",
        hidden_place="it was resting at the bottom of the bushel",
        tag="shell",
    ),
}

OBJECTS = {
    "bell": ObjectSpec(
        label="bell",
        phrase="a tiny brass bell",
        type="bell",
        location="the boat",
        value="bright",
        clues={"bell"},
    ),
    "key": ObjectSpec(
        label="key",
        phrase="a small boat key",
        type="key",
        location="the oar bench",
        value="important",
        clues={"key"},
    ),
    "shell": ObjectSpec(
        label="shell",
        phrase="a smooth white shell",
        type="shell",
        location="the child’s pocket",
        value="pretty",
        clues={"shell"},
    ),
}

HEROES = [
    ("Nico", "gondolier"),
    ("Piero", "gondolier"),
    ("Luca", "gondolier"),
    ("Mara", "gondolier"),
]
HELPERS = [
    ("Anna", "child"),
    ("Mina", "child"),
    ("Toto", "child"),
    ("Ivo", "child"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    return sorted((place, mystery, obj) for place in SETTINGS for mystery in MYSTERIES for obj in OBJECTS)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like storyworld about a gondolier, a bushel, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if args.object:
        combos = [c for c in combos if c[2] == args.object]
    if not combos:
        raise StoryError("No valid story combination matches the given options.")
    place, mystery, obj = rng.choice(combos)
    hero_name, hero_type = (args.name, "gondolier") if args.name else rng.choice(HEROES)
    helper_name, helper_type = (args.helper, "child") if args.helper else rng.choice(HELPERS)
    return StoryParams(
        place=place,
        mystery=mystery,
        object=obj,
        hero_name=hero_name or rng.choice([h for h, _ in HEROES]),
        hero_type=hero_type,
        helper_name=helper_name or rng.choice([h for h, _ in HELPERS]),
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    obj = world.facts["object"]
    mystery = world.facts["mystery"]

    world.say(
        f"Once, {hero.id}, a gondolier with a steady hand, drifted along {world.setting.place}."
    )
    world.say(
        f"Beside the boat sat a bushel, and because the day was calm, it seemed like an ordinary thing."
    )
    world.para()
    foreshadow(world)
    world.para()
    soothe(world)
    world.say(
        f"{helper.id} finally pointed toward the water and whispered, 'Something is missing.'"
    )
    solve_mystery(world)
    world.facts["resolved"] = True
    world.facts["mystery"] = mystery
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable about {f['hero'].id}, a gondolier, who finds a bushel and must solve a small mystery.",
        f"Tell a gentle story where {f['helper'].id} is upset, {f['hero'].id} soothes them, and a clue near the canal leads to the truth.",
        f"Write a child-friendly story with foreshadowing about a bushel, a missing thing, and a wise gondolier.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["object"]
    mystery: MysterySpec = f["mystery"]
    return [
        QAItem(
            question=f"Who is the story mainly about?",
            answer=f"The story is mainly about {hero.id}, a gondolier who notices clues and solves a mystery.",
        ),
        QAItem(
            question=f"What was wrong at the beginning?",
            answer=f"{mystery.problem.capitalize()}. That made {helper.id} worry until {hero.id} found the clue.",
        ),
        QAItem(
            question=f"How did {hero.id} help {helper.id} feel better?",
            answer=f"{hero.id} spoke softly and soothed {helper.id}, which made it easier to think clearly.",
        ),
        QAItem(
            question=f"What was found in the end?",
            answer=f"The missing {obj.label} was found again, and the bushel helped hide the clue until the mystery was solved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gondolier?",
            answer="A gondolier is a person who rows and guides a gondola through water, often in canals or harbors.",
        ),
        QAItem(
            question="What is a bushel?",
            answer="A bushel is a basket or basket-sized container used to carry things like fruit or vegetables.",
        ),
        QAItem(
            question="What does it mean to soothe someone?",
            answer="To soothe someone means to make them feel calmer, safer, or less upset.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives a small clue early on that hints at something important later.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to gather clues, figure out what happened, and understand the hidden truth.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
valid_story(P, M, O) :- place(P), mystery(M), object(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combinations).")
        return 0
    print("MISMATCH:")
    print("only ASP:", sorted(asp_set - py_set))
    print("only Python:", sorted(py_set - asp_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story")))


CURATED = [
    StoryParams(place="canal", mystery="bell", object="bell", hero_name="Nico", hero_type="gondolier", helper_name="Anna", helper_type="child"),
    StoryParams(place="harbor", mystery="key", object="key", hero_name="Piero", hero_type="gondolier", helper_name="Mina", helper_type="child"),
    StoryParams(place="lagoon", mystery="shell", object="shell", hero_name="Luca", hero_type="gondolier", helper_name="Toto", helper_type="child"),
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid combinations:")
        for t in vals:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
