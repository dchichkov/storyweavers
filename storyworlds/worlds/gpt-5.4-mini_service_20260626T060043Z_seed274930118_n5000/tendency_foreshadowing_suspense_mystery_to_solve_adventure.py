#!/usr/bin/env python3
"""
storyworlds/worlds/tendency_foreshadowing_suspense_mystery_to_solve_adventure.py
=================================================================================

A standalone storyworld for a small adventure mystery.

Premise:
- A child explorer notices a pattern of little signs in an old orchard trail.
- Something important goes missing just before a lantern-lit map walk.
- The guide and child follow foreshadowed clues, feel suspense, solve the mystery,
  and continue the adventure safely.

The world is intentionally small and state-driven:
- characters have physical meters and emotional memes
- objects can be carried, hidden, found, or revealed
- clues are foreshadowed before the solution
- the ending proves what changed in the world

Seed instrument:
- tendency

Narrative instruments:
- foreshadowing
- suspense
- mystery to solve
- adventure
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    found: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guide"}
        male = {"boy", "father", "man", "guide"}
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
    trail: str


@dataclass
class MysteryItem:
    id: str
    label: str
    phrase: str
    hiding_places: list[str]
    clue_word: str
    reveal_word: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    hero_name: str
    hero_type: str
    guide_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orchard": Setting(place="the old orchard", mood="golden and still", trail="the winding trail"),
    "cliffside": Setting(place="the cliffside path", mood="windy and bright", trail="the narrow path"),
    "harbor": Setting(place="the little harbor", mood="misty and busy", trail="the dock walk"),
}

MYSTERIES = {
    "lantern": MysteryItem(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        hiding_places=["under a crate", "behind a barrel", "inside a basket"],
        clue_word="gleam",
        reveal_word="lantern",
    ),
    "map": MysteryItem(
        id="map",
        label="map",
        phrase="a folded treasure map",
        hiding_places=["under a leaf pile", "inside a tin box", "beneath a stool"],
        clue_word="corner",
        reveal_word="map",
    ),
    "compass": MysteryItem(
        id="compass",
        label="compass",
        phrase="a round silver compass",
        hiding_places=["under a hat", "inside a pocket", "behind a sign"],
        clue_word="needle",
        reveal_word="compass",
    ),
}

TRAITS = ["curious", "brave", "gentle", "lively", "thoughtful", "spunky"]
GIRL_NAMES = ["Maya", "Lina", "Zoe", "Nora", "Ella", "Rina"]
BOY_NAMES = ["Finn", "Theo", "Leo", "Max", "Noah", "Eli"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    mystery = MYSTERIES[params.mystery]

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"steps": 0, "distance": 0},
        memes={"curiosity": 1, "suspense": 0, "joy": 0, "relief": 0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=params.guide_type,
        label="the guide",
        meters={"steps": 0},
        memes={"calm": 1, "suspense": 0},
    ))
    item = world.add(Entity(
        id=mystery.id,
        type=mystery.label,
        label=mystery.label,
        phrase=mystery.phrase,
        hidden_in=random.choice(mystery.hiding_places),
        found=False,
    ))
    marker = world.add(Entity(
        id="marker",
        type="stone",
        label="painted stone",
        phrase="a painted stone with a little arrow",
    ))
    world.facts["mystery"] = mystery
    world.facts["hero"] = hero
    world.facts["guide"] = guide
    world.facts["item"] = item
    world.facts["marker"] = marker
    return world


def foreshadow(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guide: Entity = world.facts["guide"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]

    world.say(
        f"{hero.id} loved walking the {world.setting.trail} at {world.setting.place}, "
        f"because every turn felt like the start of a small adventure."
    )
    world.say(
        f"Before they started, {guide.label} pointed out a tiny {mystery.clue_word} on a stone, "
        f"as if the trail was already trying to whisper a secret."
    )
    hero.memes["curiosity"] += 1
    hero.memes["suspense"] += 1
    guide.memes["suspense"] += 1
    world.say(
        f"That made {hero.id} look again and again at the path, wondering what the sign could mean."
    )
    world.say(
        f"Somewhere ahead, {item.label} had vanished, and the day had turned into a mystery to solve."
    )


def suspense_step(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guide: Entity = world.facts["guide"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]

    hero.meters["steps"] += 3
    guide.meters["steps"] += 3
    hero.meters["distance"] += 1

    world.say(
        f"They followed the arrow past a basket, then past a barrel, and the trail felt quiet enough to hear a pin drop."
    )
    world.say(
        f"{hero.id} held {guide.label}'s hand tighter, because each hiding place looked a little too good for a missing {item.label}."
    )
    hero.memes["suspense"] += 2
    guide.memes["suspense"] += 1


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guide: Entity = world.facts["guide"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]

    # The clue points to the actual hiding place.
    world.say(
        f"At last, {hero.id} noticed a {mystery.clue_word} by a basket, and there, tucked safely away, was the missing {item.label}."
    )
    item.found = True
    item.hidden_in = None
    item.carried_by = hero.id
    hero.memes["suspense"] = max(0, hero.memes["suspense"] - 2)
    hero.memes["joy"] += 1
    guide.memes["calm"] += 1
    world.say(
        f"{hero.id} lifted {item.it()} with a grin, and {guide.label} laughed softly, because the strange clues had finally made sense."
    )
    world.say(
        f"It turned out the wind had nudged the {item.label} behind the basket, which was why the trail had seemed to lead them in circles."
    )


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guide: Entity = world.facts["guide"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]

    hero.memes["relief"] += 2
    guide.memes["calm"] += 1
    world.para()
    world.say(
        f"With the {mystery.label} back where it belonged, they kept walking the {world.setting.trail} in the warm light."
    )
    world.say(
        f"{hero.id} did not feel afraid anymore; {hero.pronoun().capitalize()} felt ready for the next bend in the road."
    )
    world.say(
        f"By the end, the little mystery had been solved, and the adventure felt bigger because {item.label} was safe again."
    )


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    foreshadow(world)
    world.para()
    suspense_step(world)
    world.para()
    solve_mystery(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]
    return [
        f"Write a short adventure story for a child where {hero.id} follows clues to find the missing {item.label}.",
        f"Tell a suspenseful but gentle mystery where a hidden {mystery.label} is found after a foreshadowed clue on the trail.",
        f"Write a child-friendly story about a brave walk, a strange sign, and a solved mystery to solve.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = world.facts["hero"]  # type: ignore[assignment]
    guide: Entity = world.facts["guide"]  # type: ignore[assignment]
    item: Entity = world.facts["item"]  # type: ignore[assignment]
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What kind of day was it for {hero.id}'s walk?",
            answer=f"It was a small adventure on {world.setting.place}, along {world.setting.trail}, where the day felt {world.setting.mood}.",
        ),
        QAItem(
            question=f"What clue foreshadowed the missing {item.label}?",
            answer=f"A tiny {mystery.clue_word} on a stone foreshadowed the answer and hinted that the trail was hiding a secret.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{guide.label} helped by pointing out clues and staying calm while they searched.",
        ),
        QAItem(
            question=f"How did the story end after the mystery was solved?",
            answer=f"The missing {item.label} was found, {hero.id} felt relief, and they kept going on the adventure together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "lantern": QAItem(
        question="What is a lantern for?",
        answer="A lantern gives off light so people can see in dark places or after the sun goes down.",
    ),
    "map": QAItem(
        question="What does a map do?",
        answer="A map shows where things are and can help someone find a path or a place.",
    ),
    "compass": QAItem(
        question="What is a compass used for?",
        answer="A compass helps people know which way is north so they can travel in the right direction.",
    ),
    "orchard": QAItem(
        question="What is an orchard?",
        answer="An orchard is a place where many fruit trees grow together.",
    ),
    "suspense": QAItem(
        question="What is suspense in a story?",
        answer="Suspense is the feeling of wondering what will happen next, especially when something important is not known yet.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    mystery: MysteryItem = world.facts["mystery"]  # type: ignore[assignment]
    out = []
    for key in ("suspense", mystery.id):
        if key in WORLD_KNOWLEDGE:
            out.append(WORLD_KNOWLEDGE[key])
    # add an extra setting-related item
    if world.setting.place == "the old orchard":
        out.append(WORLD_KNOWLEDGE["orchard"])
    return out


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(orchard). place(cliffside). place(harbor).

setting_place(orchard, "the old orchard").
setting_place(cliffside, "the cliffside path").
setting_place(harbor, "the little harbor").

mystery(lantern). mystery(map). mystery(compass).

clue_word(lantern, gleam).
clue_word(map, corner).
clue_word(compass, needle).

reveal_word(lantern, lantern).
reveal_word(map, map).
reveal_word(compass, compass).

valid_story(P, M) :- place(P), mystery(M).
#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue_word", mid, MYSTERIES[mid].clue_word))
        lines.append(asp.fact("reveal_word", mid, MYSTERIES[mid].reveal_word))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = sorted(set(asp.atoms(model, "valid_story")))
    py_set = sorted((place, mystery) for place in SETTINGS for mystery in MYSTERIES)
    if set(asp_set) == set(py_set):
        print(f"OK: clingo gate matches Python registry combos ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python registry combos:")
    print("clingo:", asp_set)
    print("python:", py_set)
    return 1


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Adventure mystery storyworld with foreshadowing and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide_type = args.guide or rng.choice(["woman", "man"])
    trait = args.trait or rng.choice(TRAITS)
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.mystery and args.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    return StoryParams(
        place=place,
        mystery=mystery,
        hero_name=hero_name,
        hero_type=gender,
        guide_type=guide_type,
        trait=trait,
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.found:
            bits.append("found=True")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for place, mystery in combos:
            print(f"  {place:10} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in SETTINGS:
            for mystery in MYSTERIES:
                p = StoryParams(
                    place=place,
                    mystery=mystery,
                    hero_name="Maya",
                    hero_type="girl",
                    guide_type="woman",
                    trait="curious",
                )
                samples.append(generate(p))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not args.all else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
