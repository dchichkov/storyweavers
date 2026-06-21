#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/manner_ism_psycho_radish_misunderstanding_twist_dialogue.py
=======================================================================================

A tiny bedtime-story world about a child, a moonlit radish patch, a frightened
misunderstanding, and a gentle twist that makes everything make sense.

Seed ingredients rebuilt as world state:
- words: "manner-ism", "psycho", "radish"
- features: Misunderstanding, Twist, Dialogue
- style: Bedtime Story

Premise
-------
A child goes out to say good night to the family radishes. A torn paper tag near
the patch shows the word "psycho", and the radish leaves rustle in the dark.
Earlier, a grown-up had jokingly called the plant's little habit a "manner-ism".
The child puts those clues together the wrong way and imagines a "psycho radish".

Turn
----
The helper stays calm, listens, looks closely, and discovers the harmless source
of the rustling.

Twist / resolution
------------------
The scary idea is wrong: the paper is only a torn corner from a grown-up note,
and the rustle comes from something ordinary like wind, a snail, or a kitten.
The radish is only a radish, and bedtime can be peaceful again.
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(
            self.type, self.type
        )
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
    bedtime_image: str
    afford_sources: set[str] = field(default_factory=set)
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
class Source:
    id: str
    label: str
    sound: str
    motion: str
    reveal: str
    comfort: str
    works_in: set[str] = field(default_factory=set)
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
class HelperStyle:
    id: str
    opener: str
    check: str
    lesson: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "misunderstanding": False,
            "rustle_happened": False,
            "source_revealed": False,
            "note_clarified": False,
        }

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


def _r_rustle_scares(world: World) -> list[str]:
    child = world.get("child")
    bed = world.get("bed")
    note = world.get("note")
    if bed.meters["rustle"] < THRESHOLD:
        return []
    sig = ("rustle_scares",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["rustle_happened"] = True
    if child.memes["belief_scary"] >= THRESHOLD and note.meters["visible"] >= THRESHOLD:
        child.memes["fear"] += 1
        return ["__fear__"]
    child.memes["wonder"] += 1
    return []


def _r_reveal_calms(world: World) -> list[str]:
    child = world.get("child")
    source = world.get("source")
    if source.meters["revealed"] < THRESHOLD:
        return []
    sig = ("reveal_calms",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    world.facts["source_revealed"] = True
    return ["__relief__"]


def _r_note_clarified(world: World) -> list[str]:
    child = world.get("child")
    note = world.get("note")
    if note.meters["clarified"] < THRESHOLD:
        return []
    sig = ("note_clarified",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["belief_scary"] = 0.0
    child.memes["understanding"] += 1
    world.facts["note_clarified"] = True
    return []


CAUSAL_RULES = [
    Rule(name="rustle_scares", tag="emotional", apply=_r_rustle_scares),
    Rule(name="reveal_calms", tag="emotional", apply=_r_reveal_calms),
    Rule(name="note_clarified", tag="cognitive", apply=_r_note_clarified),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "moon_garden": Place(
        id="moon_garden",
        label="the little moon garden",
        bedtime_image="The moon laid a pale square of light over the soil.",
        afford_sources={"wind", "snail", "kitten"},
        tags={"garden", "bedtime"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="the glass greenhouse",
        bedtime_image="Soft lantern light shone in the warm glass walls.",
        afford_sources={"wind", "snail"},
        tags={"garden", "bedtime"},
    ),
    "window_box": Place(
        id="window_box",
        label="the window box by the stairs",
        bedtime_image="A sleepy lamp made the leaves gleam by the window.",
        afford_sources={"wind", "kitten"},
        tags={"garden", "bedtime"},
    ),
}

SOURCES = {
    "wind": Source(
        id="wind",
        label="the night breeze",
        sound="a hush-hush whisper",
        motion="made the radish leaves nod and tap the wooden edge",
        reveal="showed that the leaves were only bowing to the breeze",
        comfort="Even the funny sound was just the air saying good night.",
        works_in={"moon_garden", "greenhouse", "window_box"},
        tags={"wind"},
    ),
    "snail": Source(
        id="snail",
        label="a shiny snail",
        sound="a soft scrape-scrape",
        motion="dragged the torn paper tag along the soil",
        reveal="found a shiny snail pulling the paper corner with its shell",
        comfort="The tiny traveler had only been going slowly past the radish.",
        works_in={"moon_garden", "greenhouse"},
        tags={"snail"},
    ),
    "kitten": Source(
        id="kitten",
        label="the striped kitten",
        sound="a tickly rustle and a tiny mew",
        motion="poked its tail through the leaves and bumped the planter",
        reveal="saw the striped kitten batting at a leaf with one careful paw",
        comfort="The little kitten had mistaken the leaves for a toy.",
        works_in={"moon_garden", "window_box"},
        tags={"kitten"},
    ),
}

HELPER_STYLES = {
    "mother": HelperStyle(
        id="mother",
        opener=' "Let us look slowly before we decide anything scary," ',
        check="knelt beside the bed and held the lantern low",
        lesson="Sometimes a half-seen clue and a half-read word can make a whole wrong idea.",
        tags={"family"},
    ),
    "father": HelperStyle(
        id="father",
        opener=' "Easy now. We can listen first and guess later," ',
        check="bent close, listened once, and then lifted the broad leaves",
        lesson="A calm look can untangle a big misunderstanding.",
        tags={"family"},
    ),
    "aunt": HelperStyle(
        id="aunt",
        opener=' "Stories grow in the dark, but so do mistakes," ',
        check="smiled softly and tipped the lamp toward the planter",
        lesson="Words can look odd when a page is torn, and sounds can seem stranger at bedtime.",
        tags={"family"},
    ),
    "uncle": HelperStyle(
        id="uncle",
        opener=' "Let us not make the radish guilty before the facts arrive," ',
        check="crouched beside the leaves and peeped under them",
        lesson="When we check gently, the world is often simpler than our fear.",
        tags={"family"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Zoe", "Maya", "Ella", "Ivy"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Leo", "Noah", "Sam", "Finn", "Eli"]
TRAITS = ["careful", "dreamy", "curious", "gentle", "thoughtful", "sleepy"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if source_id in place.afford_sources and place_id in source.works_in:
                combos.append((place_id, source_id))
    return sorted(combos)


def source_fits_place(place_id: str, source_id: str) -> bool:
    place = PLACES[place_id]
    source = SOURCES[source_id]
    return source_id in place.afford_sources and place_id in source.works_in


def predict_fear(world: World) -> dict:
    sim = world.copy()
    sim.get("bed").meters["rustle"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("child").memes["fear"],
        "rustle": sim.get("bed").meters["rustle"],
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"Each night before bed, {child.id} liked to visit {place.label} with "
        f"{child.pronoun('possessive')} {helper.label_word}."
    )
    world.say(
        f"There was one plump radish there, round as a little moon under the leaves, "
        f"and {child.id} always whispered good night to it."
    )


def name_mannerism(world: World, child: Entity, helper: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f'That evening the radish tops leaned to one side, and {helper.label_word} laughed softly. '
        f'"Look at that tiny manner-ism," {helper.pronoun()} said. '
        f'"Our radish always bows as if it knows the bedtime song."'
    )


def find_note(world: World, child: Entity) -> None:
    note = world.get("note")
    note.meters["visible"] += 1
    child.memes["curiosity"] += 1
    world.say(
        f"Near the stem, a damp paper corner stuck out of the soil. On it was one strange word: "
        f'"psycho."'
    )


def misunderstand(world: World, child: Entity, helper: Entity) -> None:
    child.memes["belief_scary"] += 1
    world.facts["misunderstanding"] = True
    pred = predict_fear(world)
    world.facts["predicted_fear"] = pred["fear"]
    world.say(
        f'{child.id} looked from the odd word to the bowing leaves. "{child.pronoun("possessive").capitalize()} '
        f'manner-ism and that note... is it a psycho radish?" {child.pronoun()} whispered.'
    )
    world.say(
        f"{helper.label_word.capitalize()}{HELPER_STYLES[helper.type].opener.strip()}"
    )


def rustle(world: World, source_cfg: Source) -> None:
    bed = world.get("bed")
    source = world.get("source")
    bed.meters["rustle"] += 1
    source.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then came {source_cfg.sound}, and something in the patch "
        f"{source_cfg.motion}."
    )


def fear_dialogue(world: World, child: Entity, helper: Entity) -> None:
    if child.memes["fear"] >= THRESHOLD:
        world.say(
            f'"It heard me," {child.id} breathed, edging behind {helper.pronoun("object")}. '
            f'"Please do not let the radish be mad."'
        )
    else:
        world.say(
            f'{child.id} squeezed {helper.pronoun("possessive")} hand anyway and waited very still.'
        )


def investigate(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} {HELPER_STYLES[helper.type].check}."
    )


def reveal_source(world: World, source_cfg: Source) -> None:
    source = world.get("source")
    note = world.get("note")
    source.meters["revealed"] += 1
    note.meters["clarified"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the next moment, {HELPER_STYLES[world.get('helper').type].check.split()[0].lower()} "
        f"{source_cfg.reveal}."
    )
    world.say(
        f'The torn paper was not a plant label at all. It had blown from a grown-up note, and only the bit '
        f'with "psycho" had been left behind.'
    )


def twist(world: World, child: Entity, helper: Entity, source_cfg: Source) -> None:
    child.memes["joy"] += 1
    world.say(
        f'"So it was never a psycho radish?" {child.id} asked.'
    )
    world.say(
        f'"No," {helper.label_word} said, kissing the top of {child.pronoun("possessive")} head. '
        f'"It is only a radish with a funny manner-ism, and {source_cfg.comfort}"'
    )


def bedtime_end(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"{helper.label_word.capitalize()} added, "
        f'"{HELPER_STYLES[helper.type].lesson}"'
    )
    world.say(
        f'{child.id} laughed at last and bent close to the leaves. '
        f'"Good night, ordinary radish," {child.pronoun()} said.'
    )
    world.say(place.bedtime_image)
    world.say(
        f"Then {child.id} went inside feeling light again, while the small green tops nodded in the quiet."
    )


def tell(
    *,
    place: Place,
    source_cfg: Source,
    child_name: str,
    child_gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World(place)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label="the helper",
            attrs={},
        )
    )
    bed = world.add(
        Entity(
            id="bed",
            type="garden_bed",
            label="the radish patch",
            attrs={},
        )
    )
    note = world.add(
        Entity(
            id="note",
            type="paper",
            label="the torn note",
            attrs={},
        )
    )
    source = world.add(
        Entity(
            id="source",
            type=source_cfg.id,
            label=source_cfg.label,
            attrs={},
        )
    )

    child.memes["fear"] = 0.0
    child.memes["belief_scary"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["understanding"] = 0.0
    bed.meters["rustle"] = 0.0
    note.meters["visible"] = 0.0
    note.meters["clarified"] = 0.0
    source.meters["active"] = 0.0
    source.meters["revealed"] = 0.0

    introduce(world, child, helper, place)
    name_mannerism(world, child, helper)

    world.para()
    find_note(world, child)
    misunderstand(world, child, helper)
    rustle(world, source_cfg)
    fear_dialogue(world, child, helper)

    world.para()
    investigate(world, helper)
    reveal_source(world, source_cfg)
    twist(world, child, helper, source_cfg)

    world.para()
    bedtime_end(world, child, helper, place)

    world.facts.update(
        child=child,
        helper=helper,
        place=place,
        source_cfg=source_cfg,
        source=source,
        note=note,
        outcome="calmed",
        trait=trait,
    )
    return world


@dataclass
class StoryParams:
    place: str
    source: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
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
    "garden": [
        (
            "What is a radish?",
            "A radish is a root vegetable that grows partly under the soil with green leaves on top. Some are red and round, and they can be crunchy to eat."
        )
    ],
    "wind": [
        (
            "Why do leaves make sounds in the wind?",
            "When wind moves leaves, the leaves can brush each other or tap wood and soil. That makes soft rustling sounds."
        )
    ],
    "snail": [
        (
            "What does a snail do?",
            "A snail moves very slowly and carries its shell on its back. It can leave a shiny trail as it crawls."
        )
    ],
    "kitten": [
        (
            "Why do kittens pounce on moving things?",
            "Kittens love to practice chasing and batting at little moving things. They are playing and learning with their paws."
        )
    ],
    "bedtime": [
        (
            "Why can things seem scarier at bedtime?",
            "At bedtime the light is dimmer and the world is quieter, so small sounds can feel bigger. A calm look often makes the scary idea shrink."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone gets the wrong idea about what they saw or heard. When people check carefully and talk, they can fix it."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    helper = f["helper"]
    return [
        'Write a gentle bedtime story that includes the words "manner-ism", "psycho", and "radish", and ends with a child feeling safe again.',
        f"Tell a bedtime story set in {place.label} where {child.id} misunderstands a clue and thinks a radish is scary, but {child.pronoun('possessive')} {helper.label_word} calmly reveals the truth.",
        f"Write a story with dialogue, a misunderstanding, and a twist where the strange sound near a radish turns out to be {source_cfg.label}."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {helper.label_word} visiting {place.label} before bed. They go out to say good night to the radish there."
        ),
        (
            "Why did the child think the radish was scary?",
            f"{child.id} saw a torn paper with the word 'psycho' and remembered the grown-up joking about the radish's little manner-ism. Then the leaves rustled in the dark, so {child.pronoun()} put the clues together the wrong way and imagined a psycho radish."
        ),
        (
            "What was the misunderstanding?",
            f"The misunderstanding was that {child.id} thought the note belonged to the radish and proved something was wrong with it. Really, the paper was only a torn corner from a grown-up note, so the word did not describe the plant at all."
        ),
        (
            "What was making the sound in the patch?",
            f"The sound came from {source_cfg.label}. It moved the leaves in a harmless way, which is why the patch seemed spooky only until the helper looked closely."
        ),
        (
            "How did the helper solve the problem?",
            f"{helper.label_word.capitalize()} stayed calm, checked the patch slowly, and revealed the real source instead of guessing. That careful look also explained the torn note, so the fear had nothing left to hold on to."
        ),
        (
            "How did the story end?",
            f"It ended with {child.id} laughing and saying good night to an ordinary radish. The final quiet garden image shows that the scary misunderstanding has been replaced by peace."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"garden", "bedtime", "misunderstanding"}
    tags |= set(world.facts["source_cfg"].tags)
    out: list[tuple[str, str]] = []
    order = ["garden", "wind", "snail", "kitten", "bedtime", "misunderstanding"]
    for tag in order:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts | {'child': world.facts['child'].id, 'helper': world.facts['helper'].type, 'place': world.facts['place'].id, 'source_cfg': world.facts['source_cfg'].id, 'source': world.facts['source'].id, 'note': world.facts['note'].id}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="moon_garden",
        source="snail",
        child_name="Mina",
        child_gender="girl",
        helper_type="mother",
        trait="dreamy",
    ),
    StoryParams(
        place="window_box",
        source="kitten",
        child_name="Theo",
        child_gender="boy",
        helper_type="father",
        trait="careful",
    ),
    StoryParams(
        place="greenhouse",
        source="wind",
        child_name="Nora",
        child_gender="girl",
        helper_type="aunt",
        trait="curious",
    ),
]


def explain_rejection(place_id: str, source_id: str) -> str:
    place = PLACES[place_id]
    source = SOURCES[source_id]
    return (
        f"(No story: {source.label} is not a good fit for {place.label}. "
        f"That place supports {', '.join(sorted(place.afford_sources))}, so the twist would not feel honest.)"
    )


ASP_RULES = r"""
valid(P, S) :- place(P), source(S), affords(P, S), works_in(S, P).
chosen_valid :- chosen_place(P), chosen_source(S), valid(P, S).
outcome(calmed) :- chosen_valid.
#show valid/2.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for sid in sorted(place.afford_sources):
            lines.append(asp.fact("affords", pid, sid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        for pid in sorted(source.works_in):
            lines.append(asp.fact("works_in", sid, pid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_source", params.source),
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "invalid"


def outcome_of(params: StoryParams) -> str:
    return "calmed" if source_fits_place(params.place, params.source) else "invalid"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for {params}")
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Empty story during smoke test.")
        print("OK: normal generation smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a misunderstood radish, a calm helper, and a gentle twist."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--helper", dest="helper_type", choices=HELPER_STYLES)
    ap.add_argument("--gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and not source_fits_place(args.place, args.source):
        raise StoryError(explain_rejection(args.place, args.source))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id = rng.choice(combos)
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    helper_type = args.helper_type or rng.choice(sorted(HELPER_STYLES))
    trait = rng.choice(TRAITS)

    return StoryParams(
        place=place_id,
        source=source_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.helper_type not in HELPER_STYLES:
        raise StoryError(f"(Unknown helper: {params.helper_type})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if not source_fits_place(params.place, params.source):
        raise StoryError(explain_rejection(params.place, params.source))

    world = tell(
        place=PLACES[params.place],
        source_cfg=SOURCES[params.source],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source) combos:\n")
        for place_id, source_id in combos:
            print(f"  {place_id:12} {source_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.source} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
