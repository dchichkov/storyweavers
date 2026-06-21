#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py
==================================================================================

A standalone story world in a folk-tale style about a child, a silent mime,
three repeated warnings, and a lesson about judging others by appearances.

The core tale rebuilt by this world is simple:

    A child travels a country path with a basket.
    A wandering mime sees danger ahead and tries three times to warn the child.
    Because the mime is silent and strange-looking, the child grows suspicious.
    If the child listens in time, the basket arrives safely.
    If the child waits too long, trouble comes first, the child begins to weep,
    and only then understands the mime's kindness.
    In every ending, the child learns the same moral:
    do not call a good heart suspicious just because it is quiet or odd.

The world model is small but genuinely simulated:
- typed entities with physical meters and emotional memes
- repeated warning attempts recorded in state
- a hazard rule that causes trouble when the hero steps into danger
- a help rule that turns trouble into relief
- prose rendered from world state rather than a frozen template

Run it
------
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py --place orchard_lane --hazard bee_branch --proof pebble_tap
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py --proof stone_drop --hazard rotten_bridge
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py --all
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mime_weep_suspicious_lesson_learned_repetition_moral.py --verify
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother"}
        male = {"boy", "man", "father", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.type)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    opening: str
    path_word: str
    safe_way: str
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Hazard:
    id: str
    label: str
    the: str
    clue: str
    pantomime: str
    proof_need: str
    trouble_text: str
    help_text: str
    damage: int
    severity: int
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Proof:
    id: str
    label: str
    matches: set[str]
    show_text: str
    convince_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_trouble(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    cargo = world.entities.get("cargo")
    hazard = world.facts.get("hazard_cfg")
    if hero is None or cargo is None or hazard is None:
        return out
    if hero.meters["near_hazard"] < THRESHOLD:
        return out
    sig = ("trouble", hazard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["trouble"] += float(hazard.severity)
    hero.memes["fear"] += 1.0
    cargo.meters["shaken"] += 1.0
    cargo.meters["spilled"] += float(hazard.damage)
    if hazard.damage > 0:
        hero.memes["sorrow"] += 1.0
    if hero.memes["sorrow"] >= THRESHOLD:
        hero.memes["weep"] += 1.0
    out.append("__trouble__")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    mime = world.entities.get("mime")
    if hero is None or mime is None:
        return out
    if hero.meters["trouble"] < THRESHOLD or mime.meters["helping"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["rescued"] += 1.0
    hero.meters["trouble"] = max(0.0, hero.meters["trouble"] - 1.0)
    hero.memes["relief"] += 1.0
    hero.memes["trust"] += 1.0
    hero.memes["suspicion"] = max(0.0, hero.memes["suspicion"] - 2.0)
    out.append("__help__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="trouble", tag="physical", apply=_r_trouble),
    Rule(name="help", tag="social", apply=_r_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for sentence in produced:
            world.say(sentence)
    return produced


def proof_fits(hazard: Hazard, proof: Proof) -> bool:
    return hazard.id in proof.matches


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for hazard_id in sorted(place.affords):
            hazard = HAZARDS[hazard_id]
            for proof_id, proof in PROOFS.items():
                if proof_fits(hazard, proof):
                    combos.append((place_id, hazard_id, proof_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "safe" if params.heed_after <= 2 else "spilled"


def explain_rejection(place_id: str, hazard_id: str, proof_id: str) -> str:
    place = PLACES.get(place_id)
    hazard = HAZARDS.get(hazard_id)
    proof = PROOFS.get(proof_id)
    if place is None or hazard is None or proof is None:
        return "(No story: one of the requested ids is unknown.)"
    if hazard_id not in place.affords:
        return (
            f"(No story: {hazard.the} does not belong on {place.label}. "
            f"Choose a hazard that fits that road.)"
        )
    if not proof_fits(hazard, proof):
        return (
            f"(No story: {proof.label} would not honestly prove {hazard.the}. "
            f"A mime's silent warning should use a fitting demonstration.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("hero").meters["near_hazard"] += 1.0
    propagate(sim, narrate=False)
    return {
        "trouble": sim.get("hero").meters["trouble"],
        "spilled": sim.get("cargo").meters["spilled"],
        "weep": sim.get("hero").memes["weep"],
    }


def introduce(world: World, hero: Entity, elder: Entity, cargo: Entity, place: Place) -> None:
    world.say(
        f"In the days when roads were narrow and every hedge had a tale, "
        f"{hero.id} set out along {place.label}. {place.opening}"
    )
    world.say(
        f"{hero.id}'s {elder.elder_word} had trusted {hero.pronoun('object')} with "
        f"{cargo.phrase}, and {hero.pronoun()} walked carefully because the basket mattered."
    )


def meet_mime(world: World, hero: Entity, mime: Entity) -> None:
    hero.memes["curiosity"] += 1.0
    world.say(
        f"By the roadside stood a traveling mime in a faded blue coat, with white dust on "
        f"{mime.pronoun('possessive')} cheeks and bright, watchful eyes. "
        f"The stranger said nothing at all."
    )


def first_warning(world: World, hero: Entity, mime: Entity, hazard: Hazard) -> None:
    world.facts["warnings"] = 1
    mime.memes["care"] += 1.0
    world.say(
        f"The mime stepped before the narrow way and {hazard.pantomime}. "
        f"It was the first warning, plain enough to a patient eye."
    )
    hero.memes["suspicion"] += 1.0
    world.say(
        f"But {hero.id} only frowned. A silent stranger can seem suspicious to a hurried child, "
        f"and {hero.pronoun()} wondered whether the mime wanted the basket."
    )


def second_warning(world: World, hero: Entity, mime: Entity, hazard: Hazard) -> None:
    world.facts["warnings"] = 2
    mime.memes["care"] += 1.0
    hero.memes["suspicion"] += 1.0
    world.say(
        f"A second time the mime tried, more urgently now. {mime.pronoun().capitalize()} pointed ahead at "
        f"{hazard.clue}, then pressed both palms to {mime.pronoun('possessive')} heart as if to say, "
        f'"Please believe me."'
    )
    world.say(
        f"Still {hero.id} shook {hero.pronoun('possessive')} head. The child mistrusted the painted face more "
        f"than the danger underfoot."
    )


def third_warning(world: World, hero: Entity, mime: Entity, hazard: Hazard, proof: Proof) -> None:
    world.facts["warnings"] = 3
    mime.memes["care"] += 1.0
    proof_ent = world.get("proof")
    proof_ent.meters["used"] += 1.0
    world.say(
        f"Then came the third warning. The mime used {proof.label}: {proof.show_text}"
    )
    world.say(
        f"{proof.convince_text} The silent lesson was clearer than speech."
    )


def listen_in_time(world: World, hero: Entity, mime: Entity, place: Place, attempt: int) -> None:
    hero.memes["trust"] += 1.0
    hero.memes["suspicion"] = max(0.0, hero.memes["suspicion"] - 1.0)
    attempt_word = {1: "first", 2: "second"}.get(attempt, "third")
    world.say(
        f"At the {attempt_word} warning, {hero.id} stopped. {hero.pronoun().capitalize()} looked again, "
        f"looked longer, and at last saw honest fear rather than mischief in the mime's face."
    )
    world.say(
        f"Together they took {place.safe_way}, and the basket stayed steady in {hero.pronoun('possessive')} hands."
    )


def step_into_danger(world: World, hero: Entity, cargo: Entity, hazard: Hazard) -> None:
    hero.meters["near_hazard"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"But before wisdom had fully reached {hero.pronoun('object')}, {hero.pronoun()} took one more step, and "
        f"{hazard.trouble_text}"
    )
    if cargo.meters["spilled"] >= THRESHOLD:
        if hero.memes["weep"] >= THRESHOLD:
            world.say(
                f"{hero.id} began to weep, not from pain alone, but because {cargo.label} had been spoiled through "
                f"{hero.pronoun('possessive')} own hard suspicion."
            )
        else:
            world.say(
                f"{hero.id}'s heart sank as the basket tipped and part of the load was lost."
            )


def help_after_trouble(world: World, hero: Entity, mime: Entity, hazard: Hazard, place: Place) -> None:
    mime.meters["helping"] += 1.0
    propagate(world, narrate=False)
    world.say(
        f"Then the mime did not laugh, nor turn away. {mime.pronoun().capitalize()} {hazard.help_text}"
    )
    world.say(
        f"After that, the mime led {hero.id} by {place.safe_way}, as gently as an older brother in an old song."
    )


def elder_ending(world: World, hero: Entity, elder: Entity, cargo: Entity, outcome: str) -> None:
    if outcome == "safe":
        world.say(
            f"When {hero.id} reached home, {elder.elder_word} listened to the tale and nodded slowly. "
            f'"A quiet mouth may still carry a true warning," {elder.pronoun()} said.'
        )
    else:
        world.say(
            f"When {hero.id} reached home with the poorer basket, {elder.elder_word} did not scold at once. "
            f"{elder.pronoun().capitalize()} wiped the tears away first and listened."
        )
        world.say(
            f'''"Now you know," said the {elder.elder_word}, "that a child may weep after mistrust, but wisdom comes "'''
            f"sooner to the one who watches deeds."
        )
    hero.memes["lesson"] += 1.0


def moral(world: World, hero: Entity, mime: Entity, cargo: Entity, outcome: str) -> None:
    hero.memes["gratitude"] += 1.0
    if outcome == "safe":
        world.say(
            f"The next market day, when the traveling mime passed through again, {hero.id} bowed low and offered "
            f"{mime.pronoun('object')} a warm roll from the basket. Since then, {hero.pronoun()} judged strangers "
            f"less by their oddness and more by their kindness."
        )
    else:
        world.say(
            f"On the next market day, {hero.id} searched for the mime, thanked {mime.pronoun('object')} with the best "
            f"piece left in the basket, and remembered the muddy edge where pride had failed. From then on, "
            f"{hero.pronoun()} paused before calling any quiet soul suspicious."
        )
    world.say(
        "And so the old people said: do not measure a heart by noise, for help may come in silence."
    )
@dataclass
class StoryParams:
    place: str
    hazard: str
    proof: str
    cargo: str
    hero_name: str
    hero_gender: str
    elder_type: str
    heed_after: int = 2
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


KNOWLEDGE = {
    "mime": [
        (
            "What is a mime?",
            "A mime is a performer who tells things with gestures and body movements instead of spoken words. People have to watch carefully to understand the message.",
        )
    ],
    "suspicious": [
        (
            "What does suspicious mean?",
            "Suspicious means you do not trust something yet, or you think it may hide trouble. Sometimes being cautious helps, but sometimes it can make you judge a kind person unfairly.",
        )
    ],
    "bridge": [
        (
            "Why can an old wooden bridge be dangerous?",
            "Old boards can rot and crack, so they may break under a person's weight. That is why people should cross slowly and look carefully first.",
        )
    ],
    "mud": [
        (
            "Why can a bog or deep mud trap your foot?",
            "Deep mud is soft and sticky, so it can pull at your boots and make walking hard. If you rush into it, you may fall or lose what you are carrying.",
        )
    ],
    "bees": [
        (
            "Why should you be careful near a hidden bee hive?",
            "Bees guard their hive when it is disturbed. If someone shakes the branch or comes too close, the bees may fly out in a buzzing swarm.",
        )
    ],
    "warning": [
        (
            "Why should we pay attention to a warning even if it sounds strange?",
            "A warning can still be true even when it comes in an odd way. Looking at the reason behind it can keep you safe.",
        )
    ],
    "moral": [
        (
            "What is the moral of this story world?",
            "The moral is that kindness and truth do not always arrive in a familiar voice. It is wise to judge by actions, not by appearances alone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mime", "suspicious", "bridge", "mud", "bees", "warning", "moral"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    hazard = f["hazard_cfg"]
    outcome = f["outcome"]
    if outcome == "spilled":
        return [
            f'Write a folk tale for a young child that includes the words "mime", "weep", and "suspicious".',
            f"Tell a folk-tale story where {hero.id} mistrusts a mime on {place.label}, ignores three warnings, and only learns the truth after trouble by {hazard.the}.",
            "Write a simple moral tale with repetition, where a child judges a strange helper too quickly and learns to watch deeds instead of appearances.",
        ]
    return [
        f'Write a folk tale for a young child that includes the words "mime", "suspicious", and a repeated warning.',
        f"Tell a gentle moral tale where {hero.id} meets a mime on {place.label}, grows suspicious, but learns in time that the silent stranger is trying to save the day.",
        "Write a simple folk-style story with three warnings and a lesson learned: do not judge a good heart by its odd look or quiet way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    mime = f["mime"]
    cargo = f["cargo"]
    place = f["place_cfg"]
    hazard = f["hazard_cfg"]
    proof = f["proof_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child carrying {cargo.attrs['phrase']}, and a traveling mime who sees danger first. The child and the silent stranger meet on {place.label}.",
        ),
        (
            "Why did the child think the mime was suspicious?",
            f"{hero.id} did not understand the mime's silence and painted face, so the stranger seemed suspicious at first. Because the warning came without ordinary speech, the child mistook kindness for trickery.",
        ),
        (
            "How many times did the mime warn the child?",
            f"The mime warned {hero.id} three times. The repeated warnings matter because the stranger stays patient and keeps trying to help.",
        ),
        (
            "How did the mime prove the danger was real?",
            f"The mime used {proof.label}. {proof.convince_text} That clear demonstration turned a puzzling gesture into a real warning.",
        ),
    ]
    if outcome == "safe":
        qa.append(
            (
                "What changed the child's mind in time?",
                f"{hero.id} finally stopped and looked carefully instead of hurrying past. The third warning and the proof together showed that the mime feared {hazard.the} for the child's sake, not for the basket.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely: {hero.id} took {place.safe_way} and kept the basket steady. Later the child thanked the mime and learned not to judge strangers only by their odd appearance.",
            )
        )
    else:
        qa.append(
            (
                "Why did the child begin to weep?",
                f"{hero.id} stepped into danger before trusting the mime, and the basket was spoiled in the confusion. The child began to weep because the loss came from mistrust as well as fright.",
            )
        )
        qa.append(
            (
                "Did the mime still help after the mistake?",
                f"Yes. The mime helped at once and guided {hero.id} to safety instead of turning away. That kindness proved the warning had been honest all along.",
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"{hero.id} learned that a quiet or unusual person is not always suspicious. The true measure is what someone does, and the mime's deeds were full of care.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            "The moral is to look at actions before judging a person. Good help may come in a silent form, and wisdom listens before it is forced to weep.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mime", "suspicious", "warning", "moral"}
    tags |= set(f["hazard_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  warnings={world.facts.get('warnings', 0)} outcome={world.facts.get('outcome', '?')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="mill_road",
        hazard="rotten_bridge",
        proof="wobble_staff",
        cargo="eggs",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
        heed_after=2,
    ),
    StoryParams(
        place="willow_lane",
        hazard="bog_hollow",
        proof="stone_drop",
        cargo="rolls",
        hero_name="Tobin",
        hero_gender="boy",
        elder_type="grandfather",
        heed_after=3,
    ),
    StoryParams(
        place="orchard_lane",
        hazard="bee_branch",
        proof="pebble_tap",
        cargo="pears",
        hero_name="Anya",
        hero_gender="girl",
        elder_type="mother",
        heed_after=1,
    ),
    StoryParams(
        place="willow_lane",
        hazard="bee_branch",
        proof="pebble_tap",
        cargo="eggs",
        hero_name="Ivo",
        hero_gender="boy",
        elder_type="father",
        heed_after=3,
    ),
]


ASP_RULES = r"""
valid(P,H,Pr) :- place(P), affords(P,H), hazard(H), proof(Pr), matches(Pr,H).

outcome(safe) :- heed_after(N), N <= 2.
outcome(spilled) :- heed_after(N), N >= 3.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, hazard_id))
    for hazard_id in HAZARDS:
        lines.append(asp.fact("hazard", hazard_id))
    for proof_id, proof in PROOFS.items():
        lines.append(asp.fact("proof", proof_id))
        for hazard_id in sorted(proof.matches):
            lines.append(asp.fact("matches", proof_id, hazard_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("heed_after", params.heed_after)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for s in range(20):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome results differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale story world: a suspicious child, a mime, three warnings, and a moral lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--proof", choices=PROOFS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--heed-after", type=int, choices=[1, 2, 3], dest="heed_after")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, hazard, proof) combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP facts and rules")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard and args.proof:
        if (args.place, args.hazard, args.proof) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.hazard, args.proof))
    elif args.place and args.hazard and args.hazard not in PLACES[args.place].affords:
        proof_id = args.proof or next(iter(PROOFS))
        raise StoryError(explain_rejection(args.place, args.hazard, proof_id))
    elif args.hazard and args.proof and not proof_fits(HAZARDS[args.hazard], PROOFS[args.proof]):
        place_id = args.place or next(iter(PLACES))
        raise StoryError(explain_rejection(place_id, args.hazard, args.proof))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.proof is None or combo[2] == args.proof)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, proof_id = rng.choice(sorted(combos))
    cargo_id = args.cargo or rng.choice(sorted(CARGOES))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    heed_after = args.heed_after if args.heed_after is not None else rng.choice([1, 2, 3])

    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        proof=proof_id,
        cargo=cargo_id,
        hero_name=hero_name,
        hero_gender=gender,
        elder_type=elder_type,
        heed_after=heed_after,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(No story: unknown hazard '{params.hazard}'.)")
    if params.proof not in PROOFS:
        raise StoryError(f"(No story: unknown proof '{params.proof}'.)")
    if params.cargo not in CARGOES:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if (params.place, params.hazard, params.proof) not in valid_combos():
        raise StoryError(explain_rejection(params.place, params.hazard, params.proof))
    if params.heed_after not in {1, 2, 3}:
        raise StoryError("(No story: heed_after must be 1, 2, or 3.)")

    world = tell(
        place=PLACES[params.place],
        hazard=HAZARDS[params.hazard],
        proof=PROOFS[params.proof],
        cargo_cfg=CARGOES[params.cargo],
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        elder_type=params.elder_type,
        heed_after=params.heed_after,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, hazard, proof) combinations:\n")
        for place, hazard, proof in combos:
            print(f"  {place:12} {hazard:14} {proof}")
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
            header = (
                f"### {p.hero_name}: {p.hazard} on {p.place} "
                f"({p.proof}, heed_after={p.heed_after}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    place: Place,
    hazard: Hazard,
    proof: Proof,
    cargo_cfg: Cargo,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    elder_type: str = "grandmother",
    heed_after: int = 2,
) -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, role="hero", label=hero_name))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, role="elder", label="the elder"))
    mime = world.add(Entity(id="mime", kind="character", type="person", role="mime", label="the mime"))
    cargo = world.add(
        Entity(
            id="cargo",
            kind="thing",
            type="cargo",
            role="cargo",
            label=cargo_cfg.label,
            attrs={"phrase": cargo_cfg.phrase, "plural": cargo_cfg.plural},
            fragile=cargo_cfg.fragile,
        )
    )
    proof_ent = world.add(Entity(id="proof", kind="thing", type="proof", role="proof", label=proof.label))
    world.facts["warnings"] = 0
    world.facts["hazard_cfg"] = hazard
    world.facts["proof_cfg"] = proof
    world.facts["cargo_cfg"] = cargo_cfg
    world.facts["place_cfg"] = place
    world.facts["heed_after"] = heed_after

    hero.id = hero_name
    elder.id = "Elder"
    mime.id = "Mime"
    cargo.id = "Basket"
    proof_ent.id = "Proof"
    world.entities = {
        hero.id: hero,
        elder.id: elder,
        mime.id: mime,
        cargo.id: cargo,
        proof_ent.id: proof_ent,
    }
    world.facts["hero"] = hero
    world.facts["elder"] = elder
    world.facts["mime"] = mime
    world.facts["cargo"] = cargo
    world.facts["proof"] = proof_ent

    hero.memes["suspicion"] = 0.0
    hero.memes["trust"] = 0.0
    hero.memes["lesson"] = 0.0
    hero.memes["weep"] = 0.0
    hero.meters["near_hazard"] = 0.0
    hero.meters["trouble"] = 0.0
    mime.meters["helping"] = 0.0
    cargo.meters["spilled"] = 0.0
    cargo.meters["shaken"] = 0.0
    proof_ent.meters["used"] = 0.0

    introduce(world, hero, elder, cargo, place)
    meet_mime(world, hero, mime)

    world.para()
    first_warning(world, hero, mime, hazard)
    if heed_after <= 1:
        listen_in_time(world, hero, mime, place, 1)
        outcome = "safe"
    else:
        second_warning(world, hero, mime, hazard)
        if heed_after <= 2:
            world.para()
            third_warning(world, hero, mime, hazard, proof)
            listen_in_time(world, hero, mime, place, 2)
            outcome = "safe"
        else:
            world.para()
            third_warning(world, hero, mime, hazard, proof)
            step_into_danger(world, hero, cargo, hazard)
            world.para()
            help_after_trouble(world, hero, mime, hazard, place)
            outcome = "spilled"

    world.para()
    elder_ending(world, hero, elder, cargo, outcome)
    moral(world, hero, mime, cargo, outcome)

    world.facts.update(
        outcome=outcome,
        hero_name=hero.id,
        cargo_label=cargo.label,
        spilled=cargo.meters["spilled"] >= THRESHOLD,
        wept=hero.memes["weep"] >= THRESHOLD,
        rescued=hero.meters["rescued"] >= THRESHOLD,
    )
    return world


PLACES = {
    "willow_lane": Place(
        id="willow_lane",
        label="the Willow Lane",
        opening="White willow leaves flickered above it, and the ditch beside it kept its own dark secrets.",
        path_word="lane",
        safe_way="the long path by the willow roots",
        affords={"bog_hollow", "bee_branch"},
    ),
    "mill_road": Place(
        id="mill_road",
        label="the Mill Road",
        opening="One side ran by the stream, and the old planks farther on had seen too many winters.",
        path_word="road",
        safe_way="the cart track around the mill pond",
        affords={"rotten_bridge", "bog_hollow"},
    ),
    "orchard_lane": Place(
        id="orchard_lane",
        label="the Orchard Lane",
        opening="Pear trees leaned over the way, and summer sounds hummed where fruit hung low.",
        path_word="lane",
        safe_way="the grass edge under the far hedge",
        affords={"bee_branch", "rotten_bridge"},
    ),
}

HAZARDS = {
    "rotten_bridge": Hazard(
        id="rotten_bridge",
        label="rotten bridge",
        the="the rotten bridge",
        clue="the gray boards ahead",
        pantomime="rocked from heel to heel and flung both arms wide, as if the earth itself had broken beneath a footstep",
        proof_need="wobble",
        trouble_text="the board before the little bridge snapped with a bitter crack, and the basket lurched sideways",
        help_text="caught the child by the sleeve and steadied the basket before both could tumble into the stream",
        damage=1,
        severity=2,
        tags={"bridge", "careful"},
    ),
    "bog_hollow": Hazard(
        id="bog_hollow",
        label="bog hollow",
        the="the bog hollow",
        clue="the dark wet patch in the ruts",
        pantomime="lifted each foot slowly and made a sinking face, as if unseen mud were swallowing boots and basket alike",
        proof_need="sink",
        trouble_text="the earth gave way like porridge, and one leg sank deep into cold mud",
        help_text="braced a fallen branch before the child and pulled the basket free of the sucking mire",
        damage=1,
        severity=1,
        tags={"mud", "careful"},
    ),
    "bee_branch": Hazard(
        id="bee_branch",
        label="bee branch",
        the="the bee-loud branch",
        clue="the low bough heavy with blossoms",
        pantomime="hunched, waved both hands around the head, and ran in a little circle as if chased by angry wings",
        proof_need="buzz",
        trouble_text="the low branch shook, the hidden hive stirred, and a hot buzz leapt into the air around the basket",
        help_text="threw a cloak over the basket and guided the child backward until the bees settled again",
        damage=1,
        severity=2,
        tags={"bees", "careful"},
    ),
}

PROOFS = {
    "wobble_staff": Proof(
        id="wobble_staff",
        label="a willow staff",
        matches={"rotten_bridge"},
        show_text="the stranger laid a willow staff on the first plank, and the plank bent and shivered under almost no weight at all.",
        convince_text="At last even a stubborn child could see that the bridge was old and false.",
        tags={"proof", "bridge"},
    ),
    "stone_drop": Proof(
        id="stone_drop",
        label="a smooth river stone",
        matches={"bog_hollow"},
        show_text="the stranger dropped a smooth river stone into the dark patch, and it sank with hardly a splash, as if the ground had opened a mouth.",
        convince_text="Then the bog looked less like a puddle and more like a trap.",
        tags={"proof", "mud"},
    ),
    "pebble_tap": Proof(
        id="pebble_tap",
        label="a pear-sized pebble",
        matches={"bee_branch"},
        show_text="the stranger tapped the blossom-heavy branch with a pear-sized pebble, and a sharp cloud of bees rose humming from within.",
        convince_text="The warning no longer seemed strange; it seemed merciful.",
        tags={"proof", "bees"},
    ),
}

CARGOES = {
    "rolls": Cargo(
        id="rolls",
        label="warm rolls",
        phrase="a basket of warm rolls for the noon table",
        plural=True,
        fragile=False,
        tags={"food"},
    ),
    "eggs": Cargo(
        id="eggs",
        label="brown eggs",
        phrase="a willow basket of brown eggs wrapped in straw",
        plural=True,
        fragile=True,
        tags={"food", "fragile"},
    ),
    "pears": Cargo(
        id="pears",
        label="summer pears",
        phrase="a basket of summer pears for market",
        plural=True,
        fragile=False,
        tags={"food", "fruit"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tessa", "Nella", "Sora"]
BOY_NAMES = ["Tobin", "Ivo", "Marek", "Pavel", "Nico", "Emil"]

if __name__ == "__main__":
    main()
