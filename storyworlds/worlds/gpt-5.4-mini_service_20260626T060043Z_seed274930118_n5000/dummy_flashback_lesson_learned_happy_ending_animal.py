#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dummy_flashback_lesson_learned_happy_ending_animal.py
=================================================================================================

A small animal-story world with a flashback, a lesson learned, and a happy ending.

Premise:
- A little animal wants to play with a dummy toy.
- The dummy is special to someone else, so the first choice causes trouble.
- A flashback reveals why the dummy matters.
- The animal learns a lesson, repairs the problem, and ends happy.

This world is intentionally tiny and classical:
- typed entities with meters and memes
- a state-driven narrative
- a reasonableness gate for valid combinations
- an inline ASP twin for parity checks

The seed word is "dummy", and the style is kept close to an Animal Story.
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
# World content
# ---------------------------------------------------------------------------

ANIMAL_TRAITS = ["curious", "playful", "brave", "gentle", "bouncy", "tiny"]
ANIMAL_TYPES = ["rabbit", "fox", "bear", "mouse", "puppy", "kitten"]
HUMAN_TYPES = ["girl", "boy", "child"]
NAMES = {
    "rabbit": ["Ruby", "Nibbles", "Pip"],
    "fox": ["Fiona", "Toby", "Milo"],
    "bear": ["Benny", "Mara", "Ollie"],
    "mouse": ["Mimi", "Nori", "Tess"],
    "puppy": ["Buddy", "Luna", "Scout"],
    "kitten": ["Kiki", "Poppy", "Sage"],
    "girl": ["Ava", "Mia", "Lily"],
    "boy": ["Leo", "Max", "Finn"],
    "child": ["Sam", "Robin", "Ellis"],
}
CARETAKER_TYPES = ["mother", "father", "grandma", "grandpa"]

LOCATIONS = {
    "meadow": "the meadow",
    "den": "the cozy den",
    "yard": "the sunny yard",
    "barn": "the barn",
    "porch": "the porch",
}

# The story is built around one special toy that is "dummy" by seed word.
DUMMY_KIND = "dummy"

# ---------------------------------------------------------------------------
# Shared containers and world model
# ---------------------------------------------------------------------------


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "animal" | "caretaker" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"broken": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "regret": 0.0, "love": 0.0, "lesson": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandma"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandpa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    allows: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    animal: str
    name: str
    trait: str
    caretaker: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.flashback_seen = False

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
        clone.flashback_seen = self.flashback_seen
        return clone


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------


@dataclass
class Scene:
    place: str
    danger: str
    lesson: str
    fix: str
    memory: str
    allows_dummy: bool = True


SCENES = {
    "meadow": Scene(
        place="the meadow",
        danger="the dummy could get muddy in the grass",
        lesson="it's kinder to ask before taking something special",
        fix="wash the dummy and return it carefully",
        memory="the dummy had once been a brave toy for a tiny puppy",
    ),
    "den": Scene(
        place="the cozy den",
        danger="the dummy could get scratched on the floor",
        lesson="a shared toy stays happier when everyone takes turns",
        fix="polish the dummy and give it back gently",
        memory="the dummy had once helped a nervous kitten feel safe",
    ),
    "yard": Scene(
        place="the sunny yard",
        danger="the dummy could get dirty near the flower bed",
        lesson="a borrowed thing should be treated like a treasure",
        fix="wipe the dummy clean and say sorry",
        memory="the dummy had once cheered up a lonely rabbit",
    ),
    "barn": Scene(
        place="the barn",
        danger="the dummy could get dusty among the hay",
        lesson="if a toy matters to someone, that feeling matters too",
        fix="brush the dummy off and bring it back",
        memory="the dummy had once been loved by a small foal",
    ),
    "porch": Scene(
        place="the porch",
        danger="the dummy could get scuffed by rough boards",
        lesson="kindness is better than winning the game",
        fix="smooth the dummy’s edges and hand it over",
        memory="the dummy had once comforted a shy mouse",
    ),
}


def valid_places() -> list[str]:
    return sorted(SCENES)


def select_scene(place: str) -> Scene:
    if place not in SCENES:
        raise StoryError(f"(No story: unknown place {place!r}.)")
    return SCENES[place]


def explain_rejection(place: str) -> str:
    return (
        f"(No story: {place} does not fit the gentle dummy lesson story. "
        f"Try one of: {', '.join(valid_places())}.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A valid story is one where the place is one of the registered safe scenes.
valid_place(P) :- scene(P).

% A story is valid when the chosen place is valid and the dummy is allowed there.
valid_story(P) :- valid_place(P), dummy_ok(P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p, scene in SCENES.items():
        lines.append(asp.fact("scene", p))
        lines.append(asp.fact("dummy_ok", p))
        if scene.place:
            lines.append(asp.fact("place_name", p, scene.place))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    python_set = {(p,) for p in valid_places()}
    clingo_set = set(asp_valid_places())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_places() ({len(python_set)} places).")
        return 0
    print("MISMATCH between clingo and valid_places():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Narrative model
# ---------------------------------------------------------------------------


def build_world(params: StoryParams) -> World:
    setting = Setting(place=SCENES[params.place].place, indoors=params.place in {"den", "porch"}, allows={"dummy"})
    world = World(setting)

    animal = world.add(Entity(
        id=params.name,
        kind="animal",
        type=params.animal,
        label=params.name,
    ))
    caretaker = world.add(Entity(
        id="caretaker",
        kind="caretaker",
        type=params.caretaker,
        label=f"the {params.caretaker}",
    ))
    dummy = world.add(Entity(
        id="dummy",
        kind="thing",
        type="toy",
        label="dummy",
        phrase="a soft little dummy",
        owner=caretaker.id,
        caretaker=caretaker.id,
    ))

    world.facts.update(
        animal=animal,
        caretaker=caretaker,
        dummy=dummy,
        scene=SCENES[params.place],
        params=params,
    )

    # Act 1: setup
    world.say(
        f"Little {params.name} was a {params.trait} {params.animal} who loved to explore {world.setting.place}."
    )
    world.say(
        f"One day, {params.name} noticed {dummy.phrase} tucked near the door, and the toy looked like perfect play."
    )

    # Act 2: conflict
    world.para()
    world.say(
        f"{params.name} hurried to carry the dummy outside, but {caretaker.label} called softly, "
        f'"Please be careful. That dummy belongs to someone who loves it."'
    )
    world.say(
        f"{params.name} kept going anyway, and soon the toy got a little dirty."
    )
    dummy.meters["dirty"] += 1.0
    animal.memes["worry"] += 1.0
    caretaker.memes["worry"] += 1.0

    # Flashback
    world.para()
    world.flashback_seen = True
    scene = SCENES[params.place]
    world.say(
        f"Then {params.name} remembered something from earlier: {scene.memory}."
    )
    world.say(
        f"In that memory, the dummy was held gently and everyone smiled, because the toy had helped before."
    )

    # Lesson learned and fix
    world.para()
    animal.memes["regret"] += 1.0
    animal.memes["lesson"] += 1.0
    animal.memes["love"] += 1.0
    world.say(
        f"{params.name} felt sorry and learned a simple lesson: {scene.lesson}."
    )
    world.say(
        f"So {params.name} wiped the dummy clean, carried it back inside, and gave it back with a kind apology."
    )
    dummy.meters["dirty"] = 0.0
    animal.memes["worry"] = 0.0
    caretaker.memes["worry"] = 0.0

    # Happy ending
    world.para()
    animal.memes["joy"] += 1.0
    caretaker.memes["joy"] += 1.0
    world.say(
        f"After that, {caretaker.label} smiled and let {params.name} play a new game nearby."
    )
    world.say(
        f"{params.name} felt warm and happy, and the dummy stayed safe and clean where it belonged."
    )

    return world


# ---------------------------------------------------------------------------
# Registries and Q&A
# ---------------------------------------------------------------------------


@dataclass
class StoryChoice:
    place: str
    animal: str
    name: str
    trait: str
    caretaker: str


CURATED = [
    StoryParams(place="meadow", animal="rabbit", name="Ruby", trait="curious", caretaker="mother"),
    StoryParams(place="den", animal="kitten", name="Kiki", trait="gentle", caretaker="grandma"),
    StoryParams(place="yard", animal="fox", name="Toby", trait="playful", caretaker="father"),
    StoryParams(place="barn", animal="puppy", name="Buddy", trait="bouncy", caretaker="grandpa"),
    StoryParams(place="porch", animal="mouse", name="Mimi", trait="tiny", caretaker="mother"),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    return [
        f'Write a short animal story for a young child that includes the word "dummy" and a flashback.',
        f"Tell a gentle story about a {params.trait} {params.animal} named {params.name} who borrows a dummy and learns a lesson.",
        f"Write a happy-ending animal story set at {scene.place} where an animal makes a mistake, remembers something kind, and puts things right.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = f["params"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    animal: Entity = f["animal"]  # type: ignore[assignment]
    caretaker: Entity = f["caretaker"]  # type: ignore[assignment]
    dummy: Entity = f["dummy"]  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {params.name}, a {params.trait} {params.animal} who learns to be careful with a dummy.",
        ),
        QAItem(
            question=f"What did {params.name} do wrong at first?",
            answer=f"{params.name} tried to carry the dummy away, and the toy got dirty.",
        ),
        QAItem(
            question=f"What did {params.name} remember in the flashback?",
            answer=f"{params.name} remembered {scene.memory}, which showed why the dummy mattered.",
        ),
        QAItem(
            question=f"What lesson did {params.name} learn?",
            answer=f"{params.name} learned that {scene.lesson}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{params.name} cleaned the dummy, returned it kindly, and ended up happy with {caretaker.label} smiling nearby.",
        ),
        QAItem(
            question=f"Was the dummy still dirty at the end?",
            answer=f"No. The dummy was cleaned and put back safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dummy in this story?",
            answer="A dummy is a small toy that an animal can carry and that should be treated gently.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory scene that shows something from earlier.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means understanding a better way to act after making a mistake.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets fixed and the characters feel better.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  flashback_seen={world.flashback_seen}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world with dummy, flashback, lesson learned, and happy ending."
    )
    ap.add_argument("--place", choices=valid_places())
    ap.add_argument("--animal", choices=ANIMAL_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=ANIMAL_TRAITS)
    ap.add_argument("--caretaker", choices=CARETAKER_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid places derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SCENES:
        raise StoryError(explain_rejection(args.place))

    place = args.place or rng.choice(valid_places())
    animal = args.animal or rng.choice(ANIMAL_TYPES)
    trait = args.trait or rng.choice(ANIMAL_TRAITS)
    caretaker = args.caretaker or rng.choice(CARETAKER_TYPES)
    name = args.name or rng.choice(NAMES[animal])
    return StoryParams(place=place, animal=animal, name=name, trait=trait, caretaker=caretaker)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_place/1."))
        places = sorted(set(asp.atoms(model, "valid_place")))
        print(f"{len(places)} valid places:\n")
        for (place,) in places:
            print(f"  {place}")
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
            header = f"### {p.name}: {p.animal} at {p.place} (dummy story)"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
