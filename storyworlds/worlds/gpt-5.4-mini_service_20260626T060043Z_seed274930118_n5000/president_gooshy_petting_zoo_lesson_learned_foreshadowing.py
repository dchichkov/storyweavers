#!/usr/bin/env python3
"""
A standalone storyworld for a tiny whodunit at a petting zoo.

Premise:
- A careful president visits a petting zoo.
- Something gooshy goes missing or gets smudged.
- Clues are planted as foreshadowing.
- The story resolves with a Lesson Learned and a clean reveal.

The simulation tracks physical mess, clues, and a small emotional arc.
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
# Core world model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"president"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the petting zoo"
    clues: list[str] = field(default_factory=list)


@dataclass
class Suspect:
    id: str
    label: str
    species: str
    reason: str
    clue: str


@dataclass
class StoryParams:
    suspect: str
    object: str
    hero_name: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
OBJECTS = {
    "gooshy_pie": {
        "label": "gooshy pie",
        "phrase": "a gooshy pie in a paper tray",
        "mess": "gooshy",
        "color": "yellow",
        "smell": "sweet and sticky",
    },
    "gooshy_berry": {
        "label": "gooshy berry cup",
        "phrase": "a little cup of gooshy berries",
        "mess": "gooshy",
        "color": "purple",
        "smell": "dark and fruity",
    },
}

SUSPECTS = {
    "goat": Suspect(
        id="goat",
        label="a hungry goat",
        species="goat",
        reason="it liked to nibble anything left on a low table",
        clue="tiny tooth marks near the tray",
    ),
    "duck": Suspect(
        id="duck",
        label="a waddling duck",
        species="duck",
        reason="it followed shiny lids and splashed in puddles",
        clue="wet footprints beside the path",
    ),
    "pony": Suspect(
        id="pony",
        label="a small pony",
        species="pony",
        reason="it brushed past visitors with a fluffy tail",
        clue="a strand of straw caught in the fence",
    ),
}

HERO_NAMES = ["Avery", "Mina", "Noah", "Lena", "Theo", "Iris", "Maya"]
TRAITS = ["careful", "curious", "brave", "serious", "gentle"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    world = World(Setting())
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type="president",
        label="the president",
        meters={"attention": 1.0},
        memes={"curiosity": 1.0, "resolve": 1.0},
    ))
    obj_def = OBJECTS[params.object]
    obj = world.add(Entity(
        id="gooshy",
        type="thing",
        label=obj_def["label"],
        phrase=obj_def["phrase"],
        owner=hero.id,
        meters={"gooshy": 1.0, "mess": 1.0},
    ))
    suspect = SUSPECTS[params.suspect]

    world.facts.update(
        hero=hero,
        object=obj,
        suspect=suspect,
        obj_def=obj_def,
        setting=world.setting,
    )

    # Act 1: setup and foreshadowing
    world.say(
        f"{hero.id} was the president, and {hero.pronoun('subject')} came to {world.setting.place} to be polite, listen closely, and keep notes."
    )
    world.say(
        f"Near the barn path, {hero.pronoun('subject')} noticed {obj.phrase}; it looked {obj_def['color']} and smelled {obj_def['smell']}."
    )
    world.say(
        f"Before anything went wrong, {suspect.label} had already left a small clue: {suspect.clue}. That was the first bit of foreshadowing."
    )

    # Act 2: mystery and suspicion
    world.para()
    world.say(
        f"Soon after, the {obj.label} was missing from the table. {hero.id} frowned and asked who had touched it."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} followed the clues one by one, because at a petting zoo every detail mattered."
    )
    world.say(
        f"The {suspect.species} looked suspicious at first, but the clue matched {suspect.reason}."
    )

    # Act 3: reveal
    world.para()
    world.say(
        f"At last, {hero.id} found the answer: {suspect.label} had not stolen anything at all."
    )
    world.say(
        f"It had only nudged the tray while looking for food, and the real mess came from an overturned cup nearby."
    )
    world.say(
        f"{hero.id} cleaned the spot, thanked the keeper, and learned a Lesson Learned: in a mystery, the loudest suspect is not always the guilty one."
    )
    world.say(
        f"By the end, the petting zoo was calm again, and {hero.id} was smiling with {obj.label} safely put away."
    )

    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(suspect: str, obj: str) -> bool:
    return suspect in SUSPECTS and obj in OBJECTS


def explain_rejection(suspect: str, obj: str) -> str:
    return f"(No story: suspect={suspect!r} and object={obj!r} do not match this whodunit zoo domain.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
suspect(goat).
suspect(duck).
suspect(pony).

object(gooshy_pie).
object(gooshy_berry).

valid(S, O) :- suspect(S), object(O), can_pair(S, O).

can_pair(goat, gooshy_pie).
can_pair(goat, gooshy_berry).
can_pair(duck, gooshy_pie).
can_pair(duck, gooshy_berry).
can_pair(pony, gooshy_pie).
can_pair(pony, gooshy_berry).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SUSPECTS:
        lines.append(asp.fact("suspect", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
        lines.append(asp.fact("can_pair", "goat", o))
        lines.append(asp.fact("can_pair", "duck", o))
        lines.append(asp.fact("can_pair", "pony", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {(s, o) for s in SUSPECTS for o in OBJECTS if valid_combo(s, o)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combo() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# QA and prompts
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child at {world.setting.place} that includes the word "gooshy".',
        f"Tell a mystery story where {f['hero'].id} the president notices {f['obj_def']['label']} and follows clues at a petting zoo.",
        f"Write a gentle detective story with foreshadowing, a false suspicion, and a Lesson Learned ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    suspect: Suspect = f["suspect"]
    obj_def = f["obj_def"]
    return [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to the petting zoo to pay close attention and solve the mystery.",
        ),
        QAItem(
            question=f"What gooshy thing was involved?",
            answer=f"It was {obj_def['phrase']}.",
        ),
        QAItem(
            question=f"Why did {suspect.label} seem suspicious at first?",
            answer=f"{suspect.label} seemed suspicious because {suspect.reason}.",
        ),
        QAItem(
            question="What kind of clue helped the story foreshadow the answer?",
            answer=f"The story used {suspect.clue}, which hinted at what would matter later.",
        ),
        QAItem(
            question="What lesson was learned at the end?",
            answer="The lesson was that the loudest or first suspect is not always the one who caused the problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a petting zoo?",
            answer="A petting zoo is a place where people can gently visit and sometimes pet friendly animals.",
        ),
        QAItem(
            question="What does foreshadowing mean in a story?",
            answer="Foreshadowing is a clue early in a story that hints about what may matter later.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="To learn a lesson means to understand something important that changes how you act next time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    obj = args.object or rng.choice(list(OBJECTS))
    if not valid_combo(suspect, obj):
        raise StoryError(explain_rejection(suspect, obj))
    name = args.name or rng.choice(HERO_NAMES)
    return StoryParams(suspect=suspect, object=obj, hero_name=name)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
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
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit petting-zoo storyworld with foreshadowing and a lesson learned.")
    ap.add_argument("--suspect", choices=list(SUSPECTS))
    ap.add_argument("--object", choices=list(OBJECTS))
    ap.add_argument("--name")
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


CURATED = [
    StoryParams(suspect="goat", object="gooshy_pie", hero_name="Avery"),
    StoryParams(suspect="duck", object="gooshy_berry", hero_name="Mina"),
    StoryParams(suspect="pony", object="gooshy_pie", hero_name="Theo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for s, o in combos:
            print(f"  {s:5} {o}")
        return

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = build_params(args, rng)
            except StoryError as e:
                print(e)
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.suspect} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
