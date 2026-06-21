#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py
===========================================================================

A standalone storyworld for a gentle child-facing mystery: a child hears the
same strange sound again and again, makes a careful copy of a clue, and learns
to solve a mystery by checking clues instead of feeding a scary guess.

Seed requirements carried through the world:
- includes the words "copy" and "bull"
- uses repetition in the middle beats
- ends with a clear lesson learned
- keeps a mild mystery tone suitable for TinyStories-style prose

Run it
------
    python storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py
    python storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py --place farm --case door
    python storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py --all
    python storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/copy_bull_lesson_learned_repetition_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "bull"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Place:
    id: str
    label: str
    opening: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Case:
    id: str
    object_label: str
    object_phrase: str
    sound_word: str
    repeated_line: str
    clue_label: str
    clue_phrase: str
    copy_action: str
    reveal_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sound_causes_worry(world: World) -> list[str]:
    out: list[str] = []
    sound = world.get("mystery")
    hero = world.get("hero")
    helper = world.get("helper")
    if sound.meters["noise"] >= THRESHOLD:
        sig = ("worry", int(sound.meters["noise"]))
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            helper.memes["alert"] += 1
            out.append("__worry__")
    return out


def _r_copy_builds_clarity(world: World) -> list[str]:
    out: list[str] = []
    copy_ent = world.get("copy")
    hero = world.get("hero")
    if copy_ent.meters["made"] >= THRESHOLD:
        sig = ("clarity", "copy")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["curiosity"] += 1
            hero.memes["confidence"] += 1
            out.append("__clarity__")
    return out


def _r_match_solves(world: World) -> list[str]:
    out: list[str] = []
    copy_ent = world.get("copy")
    bull = world.get("bull")
    hero = world.get("hero")
    helper = world.get("helper")
    if copy_ent.meters["matches_bull"] >= THRESHOLD:
        sig = ("solved", "bull")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            helper.memes["relief"] += 1
            bull.memes["calm"] += 1
            out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="sound_causes_worry", tag="emotional", apply=_r_sound_causes_worry),
    Rule(name="copy_builds_clarity", tag="cognitive", apply=_r_copy_builds_clarity),
    Rule(name="match_solves", tag="cognitive", apply=_r_match_solves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(s for s in bits if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def case_supported(place: Place, case: Case) -> bool:
    return case.id in place.affords


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for case_id, case in CASES.items():
            if case_supported(place, case):
                out.append((place_id, case_id))
    return out


def explain_rejection(place: Place, case: Case) -> str:
    return (
        f"(No story: {place.label} does not fit the '{case.id}' mystery here. "
        f"That case needs a place that reasonably has {case.object_phrase}.)"
    )


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{place.opening} {hero.id} and {helper.id} were helping near {place.label}. "
        f"{place.mood}"
    )


def begin_mystery(world: World, hero: Entity, case: Case) -> None:
    mystery = world.get("mystery")
    mystery.meters["noise"] += 1
    propagate(world, narrate=False)
    hero.memes["curiosity"] += 1
    world.say(
        f"Just then they heard a strange sound from the shadows: "
        f'"{case.sound_word}... {case.sound_word}... {case.sound_word}."'
    )
    world.say(
        f"It came again. {case.repeated_line}"
    )


def guess_scary(world: World, hero: Entity, helper: Entity) -> None:
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f'"Maybe it is a monster," {hero.id} whispered. '
            f'{helper.id} listened hard and did not laugh, but {helper.pronoun()} did not run either.'
        )


def spot_clue(world: World, hero: Entity, case: Case) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    hero.memes["notice"] += 1
    world.say(
        f"Near the ground, {hero.id} found {case.clue_phrase}. "
        f"It looked important, but it did not explain everything yet."
    )


def make_copy(world: World, hero: Entity, case: Case) -> None:
    copy_ent = world.get("copy")
    copy_ent.meters["made"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} made a careful copy of the clue {case.copy_action}. "
        f'Then {hero.pronoun()} looked from the copy to the dark yard and back again.'
    )


def repeat_sound(world: World, case: Case) -> None:
    mystery = world.get("mystery")
    mystery.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Again came the sound: "{case.sound_word}... {case.sound_word}... {case.sound_word}." '
        f'The same sound, the same pause, the same sound.'
    )


def compare_with_bull(world: World, hero: Entity, helper: Entity, case: Case) -> None:
    copy_ent = world.get("copy")
    bull = world.get("bull")
    copy_ent.meters["matches_bull"] += 1
    bull.meters["nearby"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the moon slid out from a cloud, and they saw the old bull standing by "
        f"{case.object_phrase}. {hero.id} held up the copy and gasped. "
        f'The copied clue matched the bull exactly.'
    )
    world.say(case.reveal_text)


def lesson(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.say(
        f'{helper.id} smiled and squeezed {hero.id}\'s hand. '
        f'"A mystery feels bigger when we guess before we look," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} nodded. {hero.pronoun().capitalize()} had learned to follow the clues, "
        f"make a copy when needed, and ask what fits best before choosing a scary answer."
    )


def ending(world: World, case: Case) -> None:
    world.say(case.ending_image)


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(place: Place, case: Case, *, hero_name: str, hero_gender: str,
         helper_name: str, helper_gender: str, grownup_type: str,
         bull_name: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["careful", "curious"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=grownup_type,
        role="helper",
        traits=["calm"],
    ))
    bull = world.add(Entity(
        id=bull_name,
        kind="character",
        type="bull",
        role="bull",
        label="the bull",
        phrase=f"the old bull named {bull_name}",
        tags={"bull"},
    ))
    world.add(Entity(
        id="mystery",
        type="sound",
        label="mystery sound",
        phrase="the strange sound",
        tags={"mystery"},
    ))
    world.add(Entity(
        id="clue",
        type="clue",
        label=case.clue_label,
        phrase=case.clue_phrase,
        tags=set(case.tags),
    ))
    world.add(Entity(
        id="copy",
        type="copy",
        label="copy",
        phrase="a careful copy of the clue",
        tags={"copy"},
    ))
    world.add(Entity(
        id="object",
        type="object",
        label=case.object_label,
        phrase=case.object_phrase,
        tags=set(case.tags),
    ))

    introduce(world, hero, helper, place)
    world.para()
    begin_mystery(world, hero, case)
    guess_scary(world, hero, helper)
    spot_clue(world, hero, case)
    make_copy(world, hero, case)
    repeat_sound(world, case)
    world.para()
    compare_with_bull(world, hero, helper, case)
    lesson(world, hero, helper)
    ending(world, case)

    world.facts.update(
        place=place,
        case=case,
        hero=hero,
        helper=helper,
        bull=bull,
        mystery=world.get("mystery"),
        clue=world.get("clue"),
        copy=world.get("copy"),
        object=world.get("object"),
        repeated=world.get("mystery").meters["noise"] >= 2,
        solved=world.get("copy").meters["matches_bull"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "farm": Place(
        id="farm",
        label="the little farm barn",
        opening="On a cool evening",
        mood="The lantern by the door glowed softly, but the far corners still looked full of secrets.",
        affords={"door", "bell", "bucket"},
    ),
    "orchard": Place(
        id="orchard",
        label="the shed beside the orchard",
        opening="At sunset",
        mood="Apple leaves whispered over the path, and every shadow seemed to hide a question.",
        affords={"door", "bell"},
    ),
    "fairground": Place(
        id="fairground",
        label="the quiet animal pen behind the fair tents",
        opening="After the fair had closed",
        mood="The bright ribbons had stopped fluttering, and the empty path felt hushed and mysterious.",
        affords={"bell", "bucket"},
    ),
}

CASES = {
    "door": Case(
        id="door",
        object_label="feed-room door",
        object_phrase="the loose feed-room door",
        sound_word="thump",
        repeated_line="Thump by thump, it seemed to tap the same wooden board.",
        clue_label="hoofprint",
        clue_phrase="a split hoofprint in the dust by the step",
        copy_action="in a notebook with two neat curved halves",
        reveal_text="The bull had been nudging the loose door with his broad head because he smelled sweet hay inside. Each bump made the same thump, so the mystery had sounded larger than it really was.",
        ending_image="Soon the door was tied shut, the yard felt ordinary again, and the bull stood chewing hay as if no mystery had ever happened.",
        tags={"hoofprint", "door", "hay"},
    ),
    "bell": Case(
        id="bell",
        object_label="hanging bell rope",
        object_phrase="the hanging bell rope",
        sound_word="clang",
        repeated_line="Clang by clang, it rang in the same slow rhythm.",
        clue_label="pale hairs",
        clue_phrase="a few pale hairs twisted on the rope",
        copy_action="by drawing the twist and every little hair",
        reveal_text="The bull had been scratching his neck against the rope. Each rub pulled the bell once, then once again, and the repeated clang had turned a simple habit into a spooky puzzle.",
        ending_image="After that, the bell hung still, the rope swayed only in the wind, and the bull blinked in the moonlight with a sleepy face.",
        tags={"bell", "rope", "hair"},
    ),
    "bucket": Case(
        id="bucket",
        object_label="tin bucket",
        object_phrase="the hanging tin bucket",
        sound_word="bonk",
        repeated_line="Bonk by bonk, it hit the fence in the same little beat.",
        clue_label="mud smear",
        clue_phrase="a fresh mud smear beside the bucket chain",
        copy_action="on a scrap of paper, line by line",
        reveal_text="The bull had been pushing the bucket to reach the last cold drops inside. Every nudge made the bucket swing back and bonk the fence, so the mystery was only a thirsty animal making the same move again and again.",
        ending_image="When the bucket was filled properly, the bonking stopped, the night grew peaceful, and the bull drank with a slow happy snort.",
        tags={"bucket", "mud", "water"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ruby", "Tess", "Anna", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Eli", "Theo", "Max", "Jack"]
BULL_NAMES = ["Maple", "Bruno", "Oak", "Rusty", "Bramble"]
HELPER_NAMES = {
    "mother": ["Mom", "Mama"],
    "father": ["Dad", "Papa"],
}

# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    case: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    bull_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "bull": [
        (
            "What is a bull?",
            "A bull is a grown male cow. Bulls are big animals, but they are not mysteries by themselves; what matters is how they are acting."
        )
    ],
    "hoofprint": [
        (
            "What is a hoofprint?",
            "A hoofprint is the mark an animal with hooves leaves on the ground. It can help people tell which animal walked by."
        )
    ],
    "copy": [
        (
            "Why can making a copy of a clue help?",
            "A copy lets you look carefully at a clue even after you move away from it. That helps you compare it with other things and notice patterns."
        )
    ],
    "mystery": [
        (
            "How do you solve a mystery?",
            "You look for clues, compare what you find, and test your idea against the facts. Good clues are better than a scary guess."
        )
    ],
    "bell": [
        (
            "Why does a bell make a sound?",
            "A bell makes a sound when it is moved and the metal inside or around it shakes. That shaking makes the ringing you hear."
        )
    ],
    "bucket": [
        (
            "Why would a metal bucket make a loud noise?",
            "Metal makes a sharp sound when it bumps something hard. Even a small swing can sound big in a quiet place."
        )
    ],
    "door": [
        (
            "Why can a loose door sound spooky at night?",
            "A loose door can bang in the same way over and over, and quiet nighttime makes the sound feel bigger. Repetition can make an ordinary noise seem mysterious."
        )
    ],
}

KNOWLEDGE_ORDER = ["bull", "hoofprint", "copy", "mystery", "bell", "bucket", "door"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    case = f["case"]
    place = f["place"]
    bull = f["bull"]
    return [
        f'Write a gentle mystery story for a 3-to-5-year-old that includes the words "copy" and "bull".',
        f"Tell a story where {hero.id} hears the same strange sound again and again at {place.label}, makes a copy of a clue, and solves the mystery.",
        f"Write a child-friendly mystery with repetition in the middle, a lesson about checking clues, and a reveal that the bull named {bull.id} was causing the {case.sound_word} sound.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    bull = f["bull"]
    place = f["place"]
    case = f["case"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {helper.id}, and a bull named {bull.id}. They are together near {place.label} when a mystery begins."
        ),
        (
            "What made the story feel like a mystery at first?",
            f"The same strange {case.sound_word} sound kept happening again and again in the dark. That repetition made the ordinary night feel full of questions."
        ),
        (
            f"What clue did {hero.id} find?",
            f"{hero.id} found {case.clue_phrase}. The clue mattered because it pointed to something real instead of only a guess."
        ),
        (
            f"Why did {hero.id} make a copy of the clue?",
            f"{hero.id} wanted to study the clue carefully and compare it with what was nearby. The copy helped {hero.pronoun('object')} test the mystery instead of only feeling scared."
        ),
    ]
    if f["solved"]:
        qa.append(
            (
                f"How was the mystery solved?",
                f"When the moon brightened the yard, {hero.id} compared the copy with the bull and saw they matched. Then it became clear that {bull.id} was making the repeated {case.sound_word} sound in an ordinary way."
            )
        )
        qa.append(
            (
                "What lesson did the story teach?",
                f"The story taught that clues should come before scary guesses. {hero.id} learned that repetition can reveal a pattern, and careful looking can turn a mystery into an answer."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"bull", "copy", "mystery"} | set(world.facts["case"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="farm",
        case="door",
        hero_name="Lila",
        hero_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        bull_name="Bramble",
    ),
    StoryParams(
        place="orchard",
        case="bell",
        hero_name="Ben",
        hero_gender="boy",
        helper_name="Dad",
        helper_type="father",
        bull_name="Oak",
    ),
    StoryParams(
        place="fairground",
        case="bucket",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Mom",
        helper_type="mother",
        bull_name="Rusty",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
supported(P, C) :- place(P), case(C), affords(P, C).
valid(P, C) :- supported(P, C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for case_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, case_id))
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "bull" not in sample.story.lower() or "copy" not in sample.story.lower():
            raise StoryError("Smoke test story missing required seed words or empty story.")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle mystery with a copied clue and a bull."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--bull-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, case) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.case:
        place = PLACES[args.place]
        case = CASES[args.case]
        if not case_supported(place, case):
            raise StoryError(explain_rejection(place, case))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.case is None or combo[1] == args.case)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, case_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(["mother", "father"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES[helper_type])
    bull_name = args.bull_name or rng.choice(BULL_NAMES)

    return StoryParams(
        place=place_id,
        case=case_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        bull_name=bull_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.case not in CASES:
        raise StoryError(f"(Invalid case: {params.case})")
    place = PLACES[params.place]
    case = CASES[params.case]
    if not case_supported(place, case):
        raise StoryError(explain_rejection(place, case))

    world = tell(
        place=place,
        case=case,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_type,
        grownup_type=params.helper_type,
        bull_name=params.bull_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, case) pairs:\n")
        for place, case in combos:
            print(f"  {place:10} {case}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
