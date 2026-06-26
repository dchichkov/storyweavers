#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/knock_earthling_lingo_music_room_mystery_to.py
=====================================================================================================================

Story world sketch: "The Case of the Missing Drums" -- a small comedy in a
music room about a curious earthling who keeps hearing a knock in the
wrong place.  Built so the world *model* drives the prose (knock count,
clue count, lingo the earthling picks up, the helper who sets things
right), the moral is a child-friendly "ask first, listen twice" beat, and
the ending image proves what changed by showing the culprit caught mid-tap.

Initial story (used to build a world model):
---
Maya was a little earthling who loved a music room. She liked the tall drum,
the triangle that sang like a bell, and the maracas full of warm seeds.
One morning, Maya heard a knock in the music room. Tap tap, said the knock,
but the maracas were not shaking and the drum was not bouncing.

Maya scratched her head. "I keep hearing this knock. I do not know this
lingo, but it sounds like 'hello from under the lid.'" She opened the
drum lid and found nothing. She opened the case of the triangle, and the
knock went tick tick tick. She opened the piano lid, and the knock went
plonk plonk. Each time she said "I will solve this mystery," the knock
changed its tune.

Across the hall, Mr. Quinn the helper heard the same knock. He had the
earthling lingo pinned to his shirt, and he used it well. "Maya, little
earthling, listen with me," he said. "Knock means someone is saying hello.
Let us check the windows."

They found a tired bluebird tapping the window with its tiny beak, trying
to tell Maya that the music room window was stuck. Maya laughed, helped
open the window, and the bluebird sang a real song. From that day on,
Maya learned the first rule of the music room: when a knock keeps
knocking, ask, and then ask again, and then lend a hand.

Causal state updates:
---
    hear a knock                    -> ear.knock += 1
    ear.knock + wrong place         -> actor.confused += 1
    guess wrong                     -> mystery.open_clues += 1
    guess right                     -> mystery.open_clues -= 1   (a clue closes)
    helper arrives + actor.confused -> actor.calm += 1 ; confused -> 0
    lend a hand                     -> actor.kindness += 1 ; culprit.happy += 1
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# When a meter/meme has accumulated at least this much, it counts as a real,
# narratable beat (cf. the story.py memeplex convention).
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# A small bag of onomatopoeia, the music room's own lingo.
# ---------------------------------------------------------------------------
KNOCK_SOUNDS = ["tap tap", "tick tick", "plonk plonk", "rat-tat-tat", "knock knock"]
EARTHLING_LINGO = [
    "hello-from-under-the-lid",
    "good-morning-from-the-floor",
    "please-open-the-window",
    "shh-the-drum-is-sleeping",
    "tap-tap-is-a-good-word",
]
LINGO_TUTOR = {
    "good-morning-from-the-floor": "a little bird saying good morning",
    "hello-from-under-the-lid": "something alive saying hello from inside",
    "please-open-the-window": "a small voice asking for a window to open",
    "shh-the-drum-is-sleeping": "the room asking us to be gentle",
    "tap-tap-is-a-good-word": "the lesson that every tap is its own tiny word",
}

# Instruments the earthling might check first, and the locations they live in.
INSTRUMENTS = ["drum", "triangle", "piano", "maracas", "violin"]
LOCATIONS = ["lid", "case", "bench", "shelf", "window"]


# ---------------------------------------------------------------------------
# Entities: characters, items, and the abstract mystery the room is hiding.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "mystery"
    type: str = "thing"            # girl, boy, helper, instrument, bird, ...
    label: str = ""                # short reference, e.g. "drum"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    sound: str = ""                # for instruments: the onomatopoeia they make
    place: str = ""                # for instruments: where they sit in the room
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "helper", "teacher", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"helper": "the helper", "teacher": "the teacher"}.get(
            self.type, self.type)


# ---------------------------------------------------------------------------
# World model: entity store + the screenplay paragraphs.
# ---------------------------------------------------------------------------
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.place: str = "the music room"
        self.weather: str = ""
        # Counts and clues that drive the prose.
        self.knock_count: int = 0
        self.knock_sound: str = "tap tap"
        self.wrong_guesses: int = 0
        self.right_guesses: int = 0
        self.lingo: list[str] = []            # the earthling lingo picked up
        self.open_clues: int = 0              # the mystery is this many clues from solved
        # The mystery the world is hiding (a small object behind a known place).
        self.culprit: str = ""                # who/what is making the knock
        self.culprit_place: str = ""          # where it actually is
        # Facts recorded during the screenplay, read back by Q&A generators.
        self.facts: dict = {}

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.place = self.place
        clone.knock_count = self.knock_count
        clone.knock_sound = self.knock_sound
        clone.wrong_guesses = self.wrong_guesses
        clone.right_guesses = self.right_guesses
        clone.lingo = list(self.lingo)
        clone.open_clues = self.open_clues
        clone.culprit = self.culprit
        clone.culprit_place = self.culprit_place
        clone.paragraphs = [[]]                # predictions are silent
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confused(world: World) -> list[str]:
    """Ear knocked on, but the room is the wrong shape for an instrument there."""
    out: list[str] = []
    for char in world.characters():
        if char.meters["knock"] < THRESHOLD:
            continue
        if world.culprit_place in {"drum", "triangle", "piano", "maracas", "violin"}:
            # the culprit is not an instrument, so the noise is a mystery.
            if char.memes["confused"] >= THRESHOLD:
                continue
            sig = ("confused", char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            char.memes["confused"] += 1
            out.append("__confused__")
    return out


def _r_clue(world: World) -> list[str]:
    """A guess either opens or closes a clue; the moral beats care about both."""
    for char in world.characters():
        if char.meters["guess"] < THRESHOLD:
            continue
        if char.memes["right_guess"] >= THRESHOLD:
            sig = ("right", char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.right_guesses += 1
            world.open_clues = max(0, world.open_clues - 1)
        if char.memes["wrong_guess"] >= THRESHOLD:
            sig = ("wrong", char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            world.wrong_guesses += 1
            world.open_clues += 1
    return []


def _r_helper_calms(world: World) -> list[str]:
    """A helper arriving while the child is confused -> calm, confusion clears."""
    for char in world.characters():
        if char.memes["confused"] < THRESHOLD or char.meters["helper"] < THRESHOLD:
            continue
        if char.memes["calm"] >= THRESHOLD:
            continue
        sig = ("calm", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["calm"] += 1
        char.memes["confused"] = 0.0
    return []


def _r_kindness(world: World) -> list[str]:
    """Lending a hand lifts the actor's kindness and the culprit's happiness."""
    for char in world.characters():
        if char.meters["lend"] < THRESHOLD:
            continue
        if char.memes["kindness"] >= THRESHOLD:
            continue
        sig = ("kind", char.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        char.memes["kindness"] += 1
        if world.culprit and world.culprit in world.entities:
            world.entities[world.culprit].memes["happy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="confused", tag="cognitive", apply=_r_confused),
    Rule(name="clue", tag="narrative", apply=_r_clue),
    Rule(name="helper_calms", tag="social", apply=_r_helper_calms),
    Rule(name="kindness", tag="moral", apply=_r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* mystery and a *reasonable* fix.
# ---------------------------------------------------------------------------
def culprit_at_place(world: World, culprit_id: str, place: str) -> bool:
    """Sanity check: a culprit is some place in the music room; never the helper."""
    return bool(culprit_id) and bool(place) and culprit_id != "helper"


def lingo_for(c: str) -> str:
    """Stable description of an earthling lingo token, used in prose & QA."""
    return LINGO_TUTOR.get(c, c.replace("-", " "))


def has_solver(candidates: list[str]) -> bool:
    """Is there any reasonable culprit on the registry? Empty = invalid argument."""
    return any(c for c in candidates if c in {"bird", "mystery-clock", "stick-on-the-loose"})


def select_culprit_place(rng: random.Random) -> tuple[str, str]:
    """The active culprit + where it is, drawn from the registry."""
    culprit = rng.choice(["bird", "mystery-clock", "stick-on-the-loose"])
    place = rng.choice(LOCATIONS)
    return culprit, place


# ---------------------------------------------------------------------------
# Predicted solve: forward-simulate the world to see whether the earthling's
# guesses would close all open clues (i.e. actually solve the mystery).
# ---------------------------------------------------------------------------
def predict_solve(world: World, guesses_right: int, guesses_wrong: int) -> dict:
    sim = world.copy()
    for _ in range(guesses_right):
        for char in sim.characters():
            char.meters["guess"] += 1
            char.memes["right_guess"] += 1
        propagate(sim, narrate=False)
    for _ in range(guesses_wrong):
        for char in sim.characters():
            char.meters["guess"] += 1
            char.memes["wrong_guess"] += 1
        propagate(sim, narrate=False)
    return {"open_clues": sim.open_clues, "solved": sim.open_clues <= 0}


# ---------------------------------------------------------------------------
# The screenplay beats.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who loved {world.place}. {hero.pronoun().capitalize()} "
        f"knew the tall drum, the triangle, and the maracas full of warm seeds."
    )


def morning_knock(world: World, hero: Entity) -> None:
    hero.meters["knock"] += 1
    world.knock_count += 1
    world.knock_sound = random.choice(KNOCK_SOUNDS)
    world.say(
        f"One morning, {hero.id} heard a knock in {world.place}. "
        f"'{world.knock_sound},' said the knock, but the maracas were quiet "
        f"and the drum was not bouncing."
    )


def wrong_guess(world: World, hero: Entity, instrument: str) -> None:
    world.wrong_guesses += 1
    hero.meters["guess"] += 1
    hero.memes["wrong_guess"] += 1
    propagate(world, narrate=False)
    place = world.entities[instrument].place if instrument in world.entities else "the shelf"
    world.say(
        f"{hero.id} opened the {instrument} {place}, and the knock went "
        f"{world.knock_sound} from somewhere else."
    )


def right_guess(world: World, hero: Entity, instrument: str) -> None:
    world.right_guesses += 1
    hero.meters["guess"] += 1
    hero.memes["right_guess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} peeked inside the {instrument} and the knock sounded "
        f"closer than ever."
    )


def confused_beat(world: World, hero: Entity) -> None:
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} scratched {hero.pronoun('possessive')} head. "
        f"'I keep hearing this knock. I do not know this lingo, but it sounds "
        f"like a hello from under the lid.'"
    )


def helper_arrives(world: World, hero: Entity, helper: Entity) -> None:
    helper.meters["helper"] += 1
    hero.meters["helper"] += 1
    world.say(
        f"Across the hall, {helper.id} the {helper.type} heard the same knock. "
        f"{helper.pronoun().capitalize()} knew the earthling lingo by heart."
    )


def helper_translates(world: World, hero: Entity, helper: Entity,
                      lingo_token: str) -> None:
    world.lingo.append(lingo_token)
    world.say(
        f'"{lingo_for(lingo_token)}," {helper.id} said gently. "That is what '
        f'the knock is saying. Let us listen with two ears, not one."'
    )


def helper_redirects(world: World, hero: Entity, helper: Entity,
                     final_place: str) -> None:
    propagate(world, narrate=False)
    world.say(
        f'"{hero.id}, little earthling," {helper.id} said, "when a knock keeps '
        f'knocking, ask, and then ask again. Let us check the {final_place}."'
    )


def culprit_revealed(world: World, hero: Entity) -> None:
    """A clean reveal beat: the culprit is at its actual place, not at a guess."""
    culprit = world.entities[world.culprit]
    world.say(
        f"They walked to the {world.culprit_place}, and there was "
        f"{culprit.phrase}, tapping with all its might."
    )


def lend_a_hand(world: World, hero: Entity) -> None:
    hero.meters["lend"] += 1
    hero.memes["kindness"] += 1
    culprit = world.entities[world.culprit]
    culprit.memes["happy"] += 1
    if world.culprit == "bird":
        world.say(
            f"{hero.id} helped open the stuck window, and the bluebird sang a "
            f"real song into the {world.place}."
        )
    elif world.culprit == "mystery-clock":
        world.say(
            f"{hero.id} wound up the small clock, and it rang a happy little chime "
            f"into the {world.place}."
        )
    else:
        world.say(
            f"{hero.id} tucked the little stick back where it belonged, and the "
            f"{world.place} went quiet in the friendliest way."
        )


def moral_beat(world: World, hero: Entity) -> None:
    world.say(
        f"From that day on, {hero.id} learned the first rule of {world.place}: "
        f"when a knock keeps knocking, ask, and then ask again, and then lend a hand."
    )


# ---------------------------------------------------------------------------
# The screenplay: a three-act comedy with a clean cause-and-effect shape.
# ---------------------------------------------------------------------------
def tell(hero_name: str = "Maya", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         helper_type: str = "helper",
         helper_name: str = "Mr. Quinn",
         culprit: str = "bird",
         culprit_place: str = "window",
         lingo_token: str = "hello-from-under-the-lid") -> World:
    world = World()
    world.culprit = culprit
    world.culprit_place = culprit_place

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "playful"]),
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type,
        traits=["gentle", "patient"],
    ))
    # Instruments live in the world model; they have a sound + a place.
    for i, inst in enumerate(INSTRUMENTS):
        sound = KNOCK_SOUNDS[i % len(KNOCK_SOUNDS)]
        place = LOCATIONS[i % len(LOCATIONS)]
        world.add(Entity(
            id=inst, kind="thing", type="instrument", label=inst,
            phrase=f"the {inst}", sound=sound, place=place,
        ))
    # The culprit is a thing entity, with a stable phrase used in reveal/lend.
    if culprit == "bird":
        world.add(Entity(id="bird", kind="thing", type="bird", label="bluebird",
                         phrase="a tired bluebird"))
    elif culprit == "mystery-clock":
        world.add(Entity(id="mystery-clock", kind="thing", type="clock",
                         label="little clock", phrase="a small clock"))
    else:
        world.add(Entity(id="stick-on-the-loose", kind="thing", type="stick",
                         label="a stick", phrase="a tapping stick"))

    # Act 1 -- setup: the music room, the morning knock, a curious earthling.
    introduce(world, hero)
    morning_knock(world, hero)

    # Act 2 -- conflict: the earthling tries guesses, the knock keeps moving.
    world.para()
    confused_beat(world, hero)
    # Three wrong guesses that close the lid on the drum, case, and bench.
    wrong_order = [inst for inst in ("drum", "triangle", "piano", "maracas", "violin")
                   if inst != INSTRUMENTS[0]]  # don't start on the helper's hint
    for inst in wrong_order[:3]:
        wrong_guess(world, hero, inst)
    helper_arrives(world, hero, helper)
    helper_translates(world, hero, helper, lingo_token)
    helper_redirects(world, hero, helper, culprit_place)

    # Act 3 -- resolution: a right guess at the actual place, then lend a hand.
    world.para()
    right_guess(world, hero, _instrument_at(world, culprit_place))
    culprit_revealed(world, hero)
    lend_a_hand(world, hero)
    moral_beat(world, hero)

    world.facts.update(
        hero=hero, helper=helper, culprit=culprit, culprit_place=culprit_place,
        lingo_token=lingo_token, world=world, solved=True,
    )
    return world


def _instrument_at(world: World, place: str) -> str:
    """Find any instrument that *isn't* the culprit's location; used for the
    redirect beat's final right guess."""
    for inst in INSTRUMENTS:
        if world.entities[inst].place == place:
            return inst
    return INSTRUMENTS[0]


# ---------------------------------------------------------------------------
# Registries: a small content palette for the world.
# ---------------------------------------------------------------------------
CULPRITS = {
    "bird": "a tired bluebird",
    "mystery-clock": "a small clock",
    "stick-on-the-loose": "a tapping stick",
}
PLACES = ["lid", "case", "bench", "shelf", "window"]
LINGS = list(LINGO_TUTOR.keys())
GIRL_NAMES = ["Maya", "Lily", "Zoe", "Ava", "Mia", "Ella", "Nora", "Rose"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Sam", "Finn", "Max", "Noah", "Eli"]
HELPER_TYPES = ["helper", "teacher", "aunt", "grandpa"]
HELPER_NAMES = ["Mr. Quinn", "Ms. Rose", "Uncle Ben", "Aunt Lin", "Grandpa Theo"]
TRAITS = ["curious", "playful", "cheerful", "spirited", "stubborn", "gentle"]


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    name: str
    gender: str
    helper_name: str
    helper_type: str
    culprit: str
    culprit_place: str
    lingo: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, culprit, place, lingo_token = (
        f["hero"], f["helper"], f["culprit"], f["culprit_place"], f["lingo_token"],
    )
    return [
        'Write a short, funny story for a 3-to-5-year-old on the theme '
        '"a mystery knock in a music room" that includes the word "knock".',
        f'Tell a gentle comedy where a little {hero.type} named {hero.id} '
        f'hears a knock in the music room, tries a few wrong guesses, calls a '
        f'{helper.type} who knows the earthling lingo, and solves the case '
        f'({culprit} at the {place}).',
        f'Write a TinyStories-style tale that uses the phrase '
        f'"{lingo_token.replace("-", " ")}" and ends with a moral about '
        f'asking twice and lending a hand.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, culprit, place, lingo_token = (
        f["hero"], f["helper"], f["culprit"], f["culprit_place"], f["lingo_token"],
    )
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    culprit_phrase = CULPRITS[culprit]
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} hears a knock in the "
                f"music room on a quiet morning?"
            ),
            answer=(
                f"It is about a little {hero.type} named {hero.id} who loves "
                f"the music room. {sub.capitalize()} hears a knock that does "
                f"not come from any of the instruments, and the mystery begins."
            ),
        ),
        QAItem(
            question=(
                f"What instruments did {hero.id} open first while trying to "
                f"find the source of the knock in the music room?"
            ),
            answer=(
                f"{hero.id} opened the drum, the triangle, and the piano, but "
                f"the knock kept coming from somewhere else each time."
            ),
        ),
        QAItem(
            question=(
                f"Why did the helper say the knock was saying "
                f'"{lingo_token.replace("-", " ")}" to little {hero.id}?'
            ),
            answer=(
                f"The helper knew the earthling lingo, so {helper.pronoun()} "
                f"translated the knock as {lingo_for(lingo_token)}. That told "
                f"{hero.id} the knock was a real hello, not a broken instrument."
            ),
        ),
        QAItem(
            question=(
                f"Where did the helper tell {hero.id} to look for the source "
                f"of the knock in the music room?"
            ),
            answer=(
                f'The helper told {hero.id}, "When a knock keeps knocking, ask, '
                f'and then ask again. Let us check the {place}."'
            ),
        ),
        QAItem(
            question=(
                f"Who was the culprit making the knock at the {place} in the "
                f"music room that morning?"
            ),
            answer=(
                f"It was {culprit_phrase}, tapping away at the {place} and "
                f"trying to say hello in the only way it could."
            ),
        ),
        QAItem(
            question=(
                f"How did {hero.id} solve the case and what moral did the music "
                f"room teach {obj} at the end?"
            ),
            answer=(
                f"{hero.id} lent a hand to help {culprit_phrase} -- opening the "
                f"window, winding the clock, or tucking the stick back. The "
                f"moral of the music room was: when a knock keeps knocking, "
                f"ask, and then ask again, and then lend a hand."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    culprit, place, lingo_token = f["culprit"], f["culprit_place"], f["lingo_token"]
    qa: list[QAItem] = [
        QAItem(
            question="What is a music room?",
            answer=(
                "A music room is a quiet room where instruments live, like "
                "drums, triangles, and pianos, so children can play and "
                "practice songs together."
            ),
        ),
        QAItem(
            question="What does it mean to hear a knock?",
            answer=(
                "A knock is a small tap-tap sound, often made by a hand, a "
                "beak, or a clock, and it is usually a hello from someone or "
                "something nearby."
            ),
        ),
        QAItem(
            question="What is earthling lingo?",
            answer=(
                "Earthling lingo is the friendly little language earthlings use "
                "to translate what knocks, taps, and other small sounds are "
                "trying to say."
            ),
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer=(
                "A mystery to solve is a small puzzle, like a strange sound, "
                "where you follow the clues, ask good questions, and find the "
                "answer one clue at a time."
            ),
        ),
        QAItem(
            question="Why is repetition a useful part of a song?",
            answer=(
                "Repetition is when a tune or a word comes back the same way "
                "more than once, and it helps little ears remember the song."
            ),
        ),
        QAItem(
            question="What is a moral in a story?",
            answer=(
                "A moral is a kind little lesson, like 'ask twice and lend a "
                "hand,' that a story leaves you with at the end."
            ),
        ),
        QAItem(
            question=(
                f"What is the lingo meaning of the phrase "
                f'"{lingo_token.replace("-", " ")}" in the music room?'
            ),
            answer=(
                f"It means {lingo_for(lingo_token)}. Earthling lingo turns a "
                f"strange knock into a friendly little sentence."
            ),
        ),
        QAItem(
            question=(
                f"What kind of tapping sound would a {culprit} make at the "
                f"{place}?"
            ),
            answer=(
                f"A {culprit} at the {place} would make a small, patient "
                f"tapping sound, like a tiny hello, until someone came to "
                f"help."
            ),
        ),
    ]
    return qa


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
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.sound:
            bits.append(f"sound={e.sound}")
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:18} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  knock_count: {world.knock_count}, knock_sound: {world.knock_sound}")
    lines.append(f"  wrong_guesses: {world.wrong_guesses}, right_guesses: {world.right_guesses}")
    lines.append(f"  open_clues: {world.open_clues}, lingo: {world.lingo}")
    lines.append(f"  culprit: {world.culprit} at {world.culprit_place}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        name="Maya", gender="girl",
        helper_name="Mr. Quinn", helper_type="helper",
        culprit="bird", culprit_place="window",
        lingo="hello-from-under-the-lid", trait="curious",
    ),
    StoryParams(
        name="Theo", gender="boy",
        helper_name="Uncle Ben", helper_type="uncle",
        culprit="mystery-clock", culprit_place="bench",
        lingo="please-open-the-window", trait="playful",
    ),
    StoryParams(
        name="Lily", gender="girl",
        helper_name="Ms. Rose", helper_type="teacher",
        culprit="stick-on-the-loose", culprit_place="shelf",
        lingo="tap-tap-is-a-good-word", trait="cheerful",
    ),
    StoryParams(
        name="Leo", gender="boy",
        helper_name="Grandpa Theo", helper_type="grandpa",
        culprit="bird", culprit_place="lid",
        lingo="good-morning-from-the-floor", trait="spirited",
    ),
    StoryParams(
        name="Zoe", gender="girl",
        helper_name="Aunt Lin", helper_type="aunt",
        culprit="mystery-clock", culprit_place="case",
        lingo="shh-the-drum-is-sleeping", trait="gentle",
    ),
]


def explain_rejection(culprit: str, place: str) -> str:
    if not culprit_at_place(None, culprit, place):
        return "(No story: the culprit's location is missing; pick a place.)"
    if not has_solver([culprit]):
        return (f"(No story: the culprit '{culprit}' is not on the registry; "
                f"try bird, mystery-clock, or stick-on-the-loose.)")
    return ""


def explain_gender(name: str, gender: str) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return (f"(No story: '{name}' is not a typical {gender}'s name here; "
            f"try --name {' / '.join(pool)}.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate
# (has_solver / culprit_at_place).  Uses the shared `asp` helper, imported
# lazily so the prose engine runs without clingo.  See `--verify`.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A culprit+place is a real mystery when the culprit is on the registry
% (and the helper cannot be the culprit -- the helper is who *solves* it).
valid_culprit(C) :- culprit(C), C != helper.
valid_place(P) :- place(P).

% A story is solvable if the lingo token translates to a real meaning
% (i.e. it has a lingo_of entry) AND the culprit is on the registry.
valid_story(C, P, L) :- valid_culprit(C), valid_place(P), lingo_of(L, _).

% A guilty place is reachable from the music room (every place is reachable
% in this tiny room, so this rule is trivially true here -- but it documents
% the assumption in the world).
reachable(P) :- valid_place(P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for c in CULPRITS:
        lines.append(asp.fact("culprit", c))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for token, meaning in LINGO_TUTOR.items():
        lines.append(asp.fact("lingo_of", token, meaning.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_culprits() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show valid_culprit/1."))
    return sorted(c for (c,) in asp.atoms(model, "valid_culprit"))


def python_valid_culprits() -> list[str]:
    return sorted(c for c in CULPRITS if c != "helper")


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_culprits()), set(python_valid_culprits())
    ok = clingo_set == python_set
    if ok:
        print(f"OK: clingo gate matches valid_culprits() ({len(clingo_set)} entries).")
    else:
        print("MISMATCH between clingo and valid_culprits():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    # Exercise one generated story from each curated set so the verify mode
    # actually runs the prose engine end-to-end.
    ran = 0
    for params in CURATED:
        try:
            sample = generate(params)
            if sample.story:
                ran += 1
        except StoryError as err:
            print(f"story error for {params.name}: {err}")
            return 1
    print(f"OK: exercised {ran} curated stories end-to-end.")
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a music room mystery, a curious "
                    "earthling, a knock that keeps knocking. Unspecified "
                    "choices are picked at random (seeded).")
    ap.add_argument("--name", help="child's name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name", help="helper's name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--culprit", choices=list(CULPRITS.keys()))
    ap.add_argument("--culprit-place", choices=PLACES)
    ap.add_argument("--lingo", choices=LINGS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the clingo-derived valid_story set")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches the Python one")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit:
        reason = explain_rejection(args.culprit, args.culprit_place or "window")
        if reason:
            raise StoryError(reason)
    if args.lingo and args.lingo not in LINGO_TUTOR:
        raise StoryError(f"(No story: lingo '{args.lingo}' is not in the registry.)")

    culprit = args.culprit or rng.choice(sorted(CULPRITS.keys()))
    culprit_place = args.culprit_place or rng.choice(PLACES)
    lingo_token = args.lingo or rng.choice(LINGS)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        name=name, gender=gender, helper_name=helper_name, helper_type=helper_type,
        culprit=culprit, culprit_place=culprit_place, lingo=lingo_token, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        hero_name=params.name, hero_type=params.gender,
        hero_traits=[params.trait, "playful"],
        helper_type=params.helper_type, helper_name=params.helper_name,
        culprit=params.culprit, culprit_place=params.culprit_place,
        lingo_token=params.lingo,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        triples = asp_valid_stories()
        print(f"{len(triples)} valid (culprit, place, lingo) triples:\n")
        for c, p, l in triples:
            print(f"  culprit={c:18} place={p:8} lingo={l}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.culprit} at the {p.culprit_place} ({p.lingo})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
