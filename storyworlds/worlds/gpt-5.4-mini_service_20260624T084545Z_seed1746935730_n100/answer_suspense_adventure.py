#!/usr/bin/env python3
"""
storyworlds/worlds/answer_suspense_adventure.py
================================================

A small adventure storyworld about a child, a suspenseful quest, and the
careful discovery of an answer that opens the way forward.

The source tale behind this world:
---
A child followed a narrow trail into a quiet hill, hoping to find the answer
to a riddle carved on an old door. The lantern flickered. A stone bridge
groaned. A friend whispered that the answer had to be found before the sun
went down. After a tense search through clues, the child spotted the missing
word, spoke the answer aloud, and the hidden door opened to a bright room
full of treasure.
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
@dataclass
class Entity:
    id: str
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    wind: bool = False
    water: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    hint: str
    opens: str
    risk: str


@dataclass
class StoryParams:
    place: str
    clue: str
    hero_name: str
    hero_gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.path_darkness: float = 0.0
        self.suspense: float = 0.0
        self.answer_found: bool = False
        self.door_open: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.path_darkness = self.path_darkness
        clone.suspense = self.suspense
        clone.answer_found = self.answer_found
        clone.door_open = self.door_open
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "hill": Place(id="hill", label="the hill", dark=True, wind=True, affords={"trail", "bridge", "door"}),
    "cave": Place(id="cave", label="the cave", dark=True, wind=True, affords={"trail", "bridge", "door"}),
    "library": Place(id="library", label="the old library", dark=False, wind=False, affords={"trail", "door"}),
}

CLUES = {
    "riddle": Clue(
        id="riddle",
        label="riddle",
        phrase="a riddle carved on the stone door",
        hint="a missing word",
        opens="the hidden door",
        risk="the day would end before the answer was found",
    ),
    "map": Clue(
        id="map",
        label="map",
        phrase="a torn map with one corner missing",
        hint="a corner mark that matched the bridge",
        opens="the secret room",
        risk="the path would lead to a dead end",
    ),
    "song": Clue(
        id="song",
        label="song",
        phrase="a song written in looping letters",
        hint="the last line of the song",
        opens="the bright door",
        risk="the wind would blow the paper away",
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Lily", "Theo"]
COMPANIONS = [
    ("mouse", "a small mouse friend"),
    ("sister", "an older sister"),
    ("dog", "a brave little dog"),
    ("grandpa", "a patient grandpa"),
]
TRAITS = ["curious", "brave", "gentle", "bold", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- place(P).
risk(P,C) :- place(P), clue(C), dark(P), clue_needs_answer(C).
suspense(P,C) :- risk(P,C), winds(P).
answer_possible(P,C) :- risk(P,C), has_hints(C), place_affords(P,door).
valid_story(P,C) :- place_ok(P), clue(C), answer_possible(P,C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dark:
            lines.append(asp.fact("dark", pid))
        if p.wind:
            lines.append(asp.fact("winds", pid))
        if p.water:
            lines.append(asp.fact("water", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("place_affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_needs_answer", cid))
        lines.append(asp.fact("has_hints", cid))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    py = set(valid_combos())
    try:
        cl = set(asp_valid_stories())
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for clue_id in CLUES:
            if place.dark and place.affords & {"door"}:
                combos.append((place_id, clue_id))
    return combos

def reasonableness_gate(place: Place, clue: Clue) -> bool:
    return place.dark and "door" in place.affords

def explain_rejection(place: Place, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} only becomes suspenseful if it happens in a dark place "
        f"with a door to open, and {place.label} does not fit that setup.)"
    )

def predict(world: World, hero: Entity, clue: Clue) -> dict:
    sim = world.copy()
    run_search(sim, hero, clue, narrate=False)
    return {"answer_found": sim.answer_found, "door_open": sim.door_open}

def run_search(world: World, hero: Entity, clue: Clue, narrate: bool = True) -> None:
    if ("search", hero.id, clue.id) in world.fired:
        return
    world.fired.add(("search", hero.id, clue.id))
    world.suspense += 1
    world.path_darkness += 1
    world.say(f"{hero.id} followed the clue deeper into {world.place.label}.")

    if world.place.wind:
        world.suspense += 1
        world.say("The wind tugged at the lantern and made every step feel slower.")

    if clue.id == "riddle":
        world.say("On the door, the carved words waited like a puzzle with one missing piece.")
        world.say(f"{hero.id} looked at the stones, then at the hint: {clue.hint}.")
    elif clue.id == "map":
        world.say("The torn map shook in the breeze, and the missing corner seemed important.")
        world.say(f"{hero.id} noticed {clue.hint}.")
    else:
        world.say("The looping letters looked like a song the wind wanted to steal.")
        world.say(f"{hero.id} whispered {clue.hint} to keep it safe.")

    world.suspense += 1
    world.answer_found = True
    world.say(f"At last, {hero.id} saw the answer.")
    world.say(f"{hero.id} spoke the answer aloud, and the hidden door slid open.")

    world.door_open = True
    if narrate:
        world.say("Beyond it, a warm room glowed like sunrise after a long climb.")

def story_intro(world: World, hero: Entity, companion: Entity, clue: Clue) -> None:
    world.say(
        f"{hero.id} was a {next(t for t in hero.memes.get('traits', [])) if hero.memes.get('traits') else 'curious'} "
        f"{hero.type} who wanted to find the answer to {clue.phrase}."
    )
    world.say(
        f"{companion.label.capitalize()} stayed close, because the path was narrow and the hill looked serious."
    )

def render_story(world: World, hero: Entity, companion: Entity, clue: Clue) -> None:
    world.say(
        f"One evening, {hero.id} and {companion.label} climbed {world.place.label} with a small lantern."
    )
    world.say("The air felt quiet, but not safe in a boring way; it felt quiet like a secret.")
    world.para()
    world.say(f"{hero.id} wanted to solve {clue.label}, yet the answer would not come quickly.")
    world.say(f"The clue promised {clue.opens}, but only if {hero.id} found the right thought before dark.")
    world.para()
    run_search(world, hero, clue, narrate=True)
    world.para()
    if world.door_open:
        world.say(
            f"In the end, {hero.id} went through the open door with {companion.label}, and the treasure room shone ahead."
        )
        world.say(
            f"The answer had changed everything: the trail was no longer scary, because it led to something wonderful."
        )
    else:
        world.say("The hill stayed quiet, and the answer was still missing.")


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f'Write a suspenseful adventure story for a young child about {hero.id} finding the answer to {clue.phrase}.',
        f"Tell a short, child-friendly adventure where {hero.id} follows a clue, feels nervous, and speaks the answer aloud.",
        f'Write a story with a dark path, a helpful friend, and the word "answer" that ends with a door opening.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    clue = f["clue"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who went on the adventure in {place.label}?",
            answer=f"{hero.id} went with {companion.label} on a careful adventure in {place.label}."
        ),
        QAItem(
            question=f"What was {hero.id} trying to find?",
            answer=f"{hero.id} was trying to find the answer to {clue.phrase}."
        ),
        QAItem(
            question=f"What happened when {hero.id} spoke the answer?",
            answer="The hidden door opened, and the dark place turned into a bright room full of treasure."
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a puzzle or mystery."
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling that something important is about to happen, so you keep wondering what will come next."
        ),
        QAItem(
            question="Why do people use lanterns in dark places?",
            answer="People use lanterns in dark places so they can see the path and not bump into things."
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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place={world.place.id} suspense={world.suspense} darkness={world.path_darkness}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  answer_found={world.answer_found} door_open={world.door_open}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful adventure storyworld about finding an answer.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=[c[0] for c in COMPANIONS])
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
    if args.clue:
        combos = [c for c in combos if c[1] == args.clue]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, clue_id = rng.choice(combos)
    name = args.name or rng.choice(HERO_NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    comp = args.companion or rng.choice([c[0] for c in COMPANIONS])
    return StoryParams(place=place_id, clue=clue_id, hero_name=name, hero_gender=gender, companion=comp)

def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    clue = CLUES[params.clue]
    world = World(place)
    hero = world.add(Entity(
        id=params.hero_name, kind="character", type=params.hero_gender,
        meters={"courage": 1.0}, memes={"traits": [rng_trait(params.seed)]},
    ))
    companion_label = dict(COMPANIONS)[params.companion]
    companion = world.add(Entity(id=params.companion, kind="character", type="thing", label=companion_label))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, phrase=clue.phrase))
    world.facts.update(hero=hero, companion=companion, clue=clue_ent, place=place)

    world.say(f"{hero.id} was {rng_trait(params.seed)} and ready for a careful adventure.")
    world.say(f"{companion.label.capitalize()} came along to help watch the path.")
    world.para()
    render_story(world, hero, companion, clue)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )

def rng_trait(seed: Optional[int]) -> str:
    return random.Random(seed if seed is not None else 0).choice(TRAITS)

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))

def valid_combos_py() -> list[tuple[str, str]]:
    return valid_combos()


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:")
        for place, clue in combos:
            print(f"  {place:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place_id, clue_id in valid_combos():
            params = StoryParams(
                place=place_id,
                clue=clue_id,
                hero_name=random.choice(HERO_NAMES),
                hero_gender=random.choice(["girl", "boy"]),
                companion=random.choice([c[0] for c in COMPANIONS]),
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
