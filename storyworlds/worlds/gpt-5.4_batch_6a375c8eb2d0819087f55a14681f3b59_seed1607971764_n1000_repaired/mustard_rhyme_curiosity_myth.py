#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py
==========================================================

A standalone storyworld about a curious child who goes to an old sacred place to
ask a wonder-question, carrying mustard seeds and learning that the place
answers only to patient rhyme.

The world models a tiny mythic domain:

- a child is stirred by curiosity about some natural wonder
- an elder knows the old custom: scatter mustard seeds, use the right ritual
  object gently, and ask in rhyme
- if the child is too hasty, the place falls silent first
- after guidance, the child asks again in rhyme and receives an answer-sign
- the ending image shows what changed in the child and in the place

Run it
------
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py --place river_steps --wonder river_song
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py --place mustard_field --item bronze_bell
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py --all
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mustard_rhyme_curiosity_myth.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman", "grandmother", "aunt", "priestess", "shepherdess"}
        male = {"boy", "man", "grandfather", "uncle", "boatman", "keeper"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    intro: str
    path: str
    sign: str
    affords: set[str] = field(default_factory=set)
    calls_for: str = ""
    omen_line: str = ""
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
class Wonder:
    id: str
    question: str
    child_line: str
    answer_line: str
    proof: str
    omen: str
    topic: str
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
class RitualItem:
    id: str
    label: str
    phrase: str
    action: str
    gentle: str
    harsh: str
    place_ids: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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


GUIDE_TYPES = {
    "grandmother": {"type": "grandmother", "label": "grandmother"},
    "boatman": {"type": "boatman", "label": "boatman"},
    "shepherdess": {"type": "shepherdess", "label": "shepherdess"},
}


class World:
    def __init__(self, place_cfg: Place) -> None:
        self.place_cfg = place_cfg
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


def _r_listening(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    out: list[str] = []
    if hero.meters["mustard_ring"] >= THRESHOLD and hero.meters["gentle_call"] >= THRESHOLD:
        sig = ("listening",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["listening"] += 1
            out.append("__listening__")
    return out


def _r_silence(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    out: list[str] = []
    if hero.meters["harsh_call"] >= THRESHOLD:
        sig = ("silence",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["silence"] += 1
            hero.memes["disappointment"] += 1
            out.append("__silence__")
    return out


def _r_answer(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    out: list[str] = []
    if place.meters["listening"] >= THRESHOLD and hero.memes["rhyme"] >= THRESHOLD:
        sig = ("answer",)
        if sig not in world.fired:
            world.fired.add(sig)
            place.meters["answered"] += 1
            hero.memes["awe"] += 1
            hero.memes["calm"] += 1
            out.append("__answer__")
    return out


CAUSAL_RULES = [
    Rule(name="listening", tag="ritual", apply=_r_listening),
    Rule(name="silence", tag="ritual", apply=_r_silence),
    Rule(name="answer", tag="ritual", apply=_r_answer),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


PLACES = {
    "sun_hill": Place(
        id="sun_hill",
        label="Sun Hill",
        intro="where a round white gate of stone watched the east",
        path="a path of pale dust climbed between thyme and small rocks",
        sign="the first light always touched the stones there before it touched the village roofs",
        affords={"dawn", "stars"},
        calls_for="bronze_bell",
        omen_line="The bell-note ran over the hill like a bright thread.",
        tags={"hill", "dawn", "stars"},
    ),
    "river_steps": Place(
        id="river_steps",
        label="the River Steps",
        intro="where old stairs sank into green water",
        path="flat reeds bowed along the bank, and the stones were cool under bare feet",
        sign="the water never seemed to stop whispering against the steps",
        affords={"river_song", "moon_reflection"},
        calls_for="reed_flute",
        omen_line="A thin note slipped out over the water, and the ripples held it.",
        tags={"river", "water", "moon"},
    ),
    "mustard_field": Place(
        id="mustard_field",
        label="the Mustard Field",
        intro="where yellow flowers nodded under the sky like a little gold sea",
        path="a narrow footpath wound between the stems, sweet and peppery in the air",
        sign="bees moved there with the steady hum of tiny spinning wheels",
        affords={"bees", "wind_name"},
        calls_for="clay_whistle",
        omen_line="The whistle answered softly, and the flowers all leaned one way together.",
        tags={"mustard", "field", "bees", "wind"},
    ),
}

WONDERS = {
    "dawn": Wonder(
        id="dawn",
        question="why morning comes",
        child_line="Why does morning always find the village?",
        answer_line='A voice seemed to say, "Dawn follows songs that wake before fear."',
        proof="When the child looked east, even the little stones were shining.",
        omen="a warm stripe of light crossed the gate",
        topic="dawn",
        tags={"dawn", "sun"},
    ),
    "stars": Wonder(
        id="stars",
        question="where the stars go by day",
        child_line="Where do the stars hide when the blue day opens?",
        answer_line='The old hill answered, "They sleep in the bright bowl of heaven until evening calls them back."',
        proof="One silver star still trembled above the hill as if nodding yes.",
        omen="a late star flickered in the paling sky",
        topic="stars",
        tags={"stars", "sky"},
    ),
    "river_song": Wonder(
        id="river_song",
        question="why the river sings",
        child_line="Why does the river keep singing, even when nobody is near?",
        answer_line='The water answered, "It remembers the mountain, and memory hums as it runs."',
        proof="After that, every ripple sounded less lonely and more like a lullaby.",
        omen="the ripples gathered into one bright braid",
        topic="river",
        tags={"river", "water", "song"},
    ),
    "moon_reflection": Wonder(
        id="moon_reflection",
        question="why the moon follows water",
        child_line="Why does the moon climb into every dark pool?",
        answer_line='The river answered, "The moon loves any place that can carry a silver story."',
        proof="The moonlight on the steps looked almost close enough to hold.",
        omen="the water made a silver ladder",
        topic="moon",
        tags={"moon", "water"},
    ),
    "bees": Wonder(
        id="bees",
        question="why bees love mustard flowers",
        child_line="Why do the bees love mustard flowers so much?",
        answer_line='The field replied, "Because gold calls to gold, and sweet work calls to winged workers."',
        proof="The bees circled the yellow heads as if the flowers had begun to sing.",
        omen="three bees hovered in one shining ring",
        topic="bees",
        tags={"bees", "mustard", "flowers"},
    ),
    "wind_name": Wonder(
        id="wind_name",
        question="what the wind is called before dawn",
        child_line="What is the wind called before the sun wakes?",
        answer_line='The flowers whispered, "Before dawn it is called the Gatherer, for it collects every small scent."',
        proof="The child could smell thyme, dust, and mustard all at once.",
        omen="the stems bent together and then stood straight again",
        topic="wind",
        tags={"wind", "mustard", "field"},
    ),
}

ITEMS = {
    "bronze_bell": RitualItem(
        id="bronze_bell",
        label="bronze bell",
        phrase="a little bronze bell",
        action="rang the bronze bell once",
        gentle="tapped the bronze bell with one careful finger",
        harsh="clanged the bronze bell too hard",
        place_ids={"sun_hill"},
        tags={"bell", "sound"},
    ),
    "reed_flute": RitualItem(
        id="reed_flute",
        label="reed flute",
        phrase="a reed flute cut from the river bank",
        action="blew one low note through the reed flute",
        gentle="blew one low note through the reed flute",
        harsh="blew a sharp, grabbing blast through the reed flute",
        place_ids={"river_steps"},
        tags={"flute", "sound", "river"},
    ),
    "clay_whistle": RitualItem(
        id="clay_whistle",
        label="clay whistle",
        phrase="a thumb-sized clay whistle",
        action="blew the clay whistle softly",
        gentle="blew the clay whistle softly",
        harsh="shrilled the clay whistle again and again",
        place_ids={"mustard_field"},
        tags={"whistle", "sound", "mustard"},
    ),
}


@dataclass
class StoryParams:
    place: str
    wonder: str
    item: str
    hero_name: str
    hero_gender: str
    guide_type: str
    temperament: str
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


def place_fits_wonder(place: Place, wonder: Wonder) -> bool:
    return wonder.id in place.affords


def item_fits_place(item: RitualItem, place: Place) -> bool:
    return place.id in item.place_ids and item.id == place.calls_for


def valid_combo(place_id: str, wonder_id: str, item_id: str) -> bool:
    if place_id not in PLACES or wonder_id not in WONDERS or item_id not in ITEMS:
        return False
    return place_fits_wonder(PLACES[place_id], WONDERS[wonder_id]) and item_fits_place(ITEMS[item_id], PLACES[place_id])


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for wonder_id, wonder in WONDERS.items():
            for item_id, item in ITEMS.items():
                if place_fits_wonder(place, wonder) and item_fits_place(item, place):
                    combos.append((place_id, wonder_id, item_id))
    return combos


GIRL_NAMES = ["Nila", "Tala", "Mira", "Suri", "Ila", "Rina", "Luma", "Asha"]
BOY_NAMES = ["Aren", "Tavi", "Milo", "Kiran", "Solen", "Ivo", "Darin", "Neri"]
TEMPERAMENTS = ["hasty", "patient"]


def outcome_of(params: StoryParams) -> str:
    return "guided" if params.temperament == "hasty" else "smooth"


def mustard_rhyme_lines(place: Place, wonder: Wonder) -> tuple[str, str]:
    if place.id == "sun_hill":
        return (
            "Mustard bright, mustard gold,",
            "teach my small heart what dawn has told.",
        )
    if place.id == "river_steps":
        return (
            "Mustard bright on stone and stream,",
            "carry my question in your gleam.",
        )
    return (
        "Mustard bright in bloom and breeze,",
        "tell me softly what secrets please.",
    )


def introduce(world: World, hero: Entity, guide: Entity, wonder: Wonder, place: Place) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"In the days when hills were said to remember footsteps and rivers were said to remember names, "
        f"{hero.id} was a curious little {hero.type} who could not keep a wonder-question shut inside."
    )
    world.say(
        f"All morning {hero.pronoun()} asked about {wonder.question}. At last {hero.pronoun('possessive')} "
        f"{guide.label_word} smiled and said that {place.label} still listened to respectful questions."
    )


def prepare(world: World, hero: Entity, guide: Entity, item: RitualItem, place: Place) -> None:
    hero.attrs["item"] = item.id
    hero.attrs["mustard_pouch"] = True
    world.say(
        f"So the two of them walked toward {place.label}, {place.intro}. "
        f"{place.path}, and {place.sign}."
    )
    world.say(
        f"{guide.label_word.capitalize()} tucked a tiny cloth pouch of mustard seeds into {hero.pronoun('possessive')} hand "
        f"and gave {hero.pronoun('object')} {item.phrase}. "
        f'"Old places do not answer grabbing voices," {guide.pronoun()} said. "They answer patient rhyme."'
    )


def first_attempt(world: World, hero: Entity, guide: Entity, item: RitualItem, wonder: Wonder) -> None:
    if hero.attrs.get("temperament") == "hasty":
        hero.meters["harsh_call"] += 1
        hero.memes["impatience"] += 1
        propagate(world, narrate=False)
        world.say(
            f"But {hero.id}'s curiosity was hopping faster than good sense. {hero.pronoun().capitalize()} "
            f'''{item.harsh} and cried, "{wonder.child_line}"'''
        )
        world.say(
            "Nothing answered. Even the little sounds nearby seemed to tuck themselves away."
        )
    else:
        world.say(
            f"{hero.id} wanted to rush, yet {hero.pronoun()} remembered the warning and held still with the mustard pouch closed in "
            f"{hero.pronoun('possessive')} fist."
        )


def guide_teaches(world: World, hero: Entity, guide: Entity, place: Place, wonder: Wonder) -> None:
    line1, line2 = mustard_rhyme_lines(place, wonder)
    guide.attrs["rhyme_1"] = line1
    guide.attrs["rhyme_2"] = line2
    hero.memes["calm"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{guide.label_word.capitalize()} knelt beside {hero.id} and opened the little pouch. "
        f'"Questions climb higher when they walk in rhyme," {guide.pronoun()} whispered.'
    )
    world.say(
        f'{guide.pronoun().capitalize()} taught {hero.pronoun("object")} two small lines: "{line1}" '
        f'and "{line2}"'
    )


def true_ritual(world: World, hero: Entity, item: RitualItem, wonder: Wonder) -> None:
    hero.meters["mustard_ring"] += 1
    hero.meters["gentle_call"] += 1
    hero.memes["rhyme"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} scattered the mustard seeds in a tiny gold ring and then {item.gentle}. "
        f'This time {hero.pronoun()} spoke the rhyme softly and ended with the true question: "{wonder.child_line}"'
    )


def answer(world: World, hero: Entity, place: Place, wonder: Wonder) -> None:
    if world.get("place").meters["answered"] < THRESHOLD:
        raise StoryError("The ritual did not produce an answer; the story would not resolve.")
    world.say(
        f"{place.omen_line} {wonder.omen.capitalize()}, and {wonder.answer_line}"
    )
    world.say(
        f"{wonder.proof} {hero.id} no longer felt as if {hero.pronoun()} had to grab an answer. "
        f"{hero.pronoun().capitalize()} felt big enough to carry mystery gently."
    )


def ending(world: World, hero: Entity, guide: Entity, place: Place, wonder: Wonder) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"On the walk home, {hero.id} kept the empty mustard pouch in {hero.pronoun('possessive')} pocket as if it were a treasure. "
        f"{guide.label_word.capitalize()} laughed softly and told {hero.pronoun('object')} that not every answer comes quickly, "
        f"but gentle questions are the ones the world remembers."
    )
    if place.id == "mustard_field":
        world.say(
            "Behind them, the field nodded in one golden wave, and the bees went on with their shining work."
        )
    elif place.id == "river_steps":
        world.say(
            "Behind them, the river kept singing on the steps, and now the song sounded like a friend instead of a puzzle."
        )
    else:
        world.say(
            "Behind them, the hill held the first light like a bowl, and the child felt that dawn had spoken kindly."
        )


def tell(
    place: Place,
    wonder: Wonder,
    item: RitualItem,
    hero_name: str = "Nila",
    hero_gender: str = "girl",
    guide_type: str = "grandmother",
    temperament: str = "hasty",
) -> World:
    if not place_fits_wonder(place, wonder):
        raise StoryError(explain_rejection(place, wonder, item))
    if not item_fits_place(item, place):
        raise StoryError(explain_rejection(place, wonder, item))
    if guide_type not in GUIDE_TYPES:
        raise StoryError(f"(No story: unknown guide type '{guide_type}'.)")

    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero", attrs={"temperament": temperament}))
    guide_cfg = GUIDE_TYPES[guide_type]
    guide = world.add(Entity(id="guide", kind="character", type=guide_cfg["type"], label=guide_cfg["label"], role="guide"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.add(Entity(id="pouch", kind="thing", type="mustard_pouch", label="mustard seed pouch"))
    world.add(Entity(id="ritual_item", kind="thing", type=item.id, label=item.label))

    hero.meters["mustard_ring"] = 0.0
    hero.meters["gentle_call"] = 0.0
    hero.meters["harsh_call"] = 0.0
    hero.memes["rhyme"] = 0.0
    hero.memes["calm"] = 0.0
    hero.memes["awe"] = 0.0
    hero.memes["curiosity"] = 0.0
    place_ent.meters["listening"] = 0.0
    place_ent.meters["silence"] = 0.0
    place_ent.meters["answered"] = 0.0

    introduce(world, hero, guide, wonder, place)
    world.para()
    prepare(world, hero, guide, item, place)
    first_attempt(world, hero, guide, item, wonder)
    world.para()
    guide_teaches(world, hero, guide, place, wonder)
    true_ritual(world, hero, item, wonder)
    answer(world, hero, place, wonder)
    world.para()
    ending(world, hero, guide, place, wonder)

    world.facts.update(
        hero=hero,
        guide=guide,
        place=place,
        wonder=wonder,
        item=item,
        outcome=outcome_of(
            StoryParams(
                place=place.id,
                wonder=wonder.id,
                item=item.id,
                hero_name=hero_name,
                hero_gender=hero_gender,
                guide_type=guide_type,
                temperament=temperament,
            )
        ),
        had_silence=hero.meters["harsh_call"] >= THRESHOLD,
        answered=place_ent.meters["answered"] >= THRESHOLD,
        rhyme_lines=(guide.attrs.get("rhyme_1", ""), guide.attrs.get("rhyme_2", "")),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    wonder = world.facts["wonder"]
    place = world.facts["place"]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old about a curious child who carries mustard seeds to {place.label} and asks about {wonder.question} in rhyme.',
        f"Tell a gentle myth where a {hero.type} named {hero.label} goes with {guide.label_word} to {place.label}, learns patient rhyme, and receives an answer-sign from the old world.",
        'Write a child-facing myth that includes the word "mustard" and shows curiosity turning from grabbing to listening.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    guide = world.facts["guide"]
    place = world.facts["place"]
    wonder = world.facts["wonder"]
    item = world.facts["item"]
    had_silence = world.facts["had_silence"]
    outcome = world.facts["outcome"]
    lines = world.facts["rhyme_lines"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a curious little {hero.type}, and {hero.pronoun('possessive')} {guide.label_word}. They go to {place.label} to ask about {wonder.question}.",
        ),
        (
            f"Why did {hero.label} go to {place.label}?",
            f"{hero.label} was full of curiosity and wanted to know {wonder.question}. {guide.label_word.capitalize()} believed that old place still listened to respectful questions.",
        ),
        (
            "What did they bring?",
            f"They brought a little pouch of mustard seeds and {item.phrase}. The mustard seeds helped make a careful ritual, and the right object matched the place they were visiting.",
        ),
    ]
    if had_silence:
        qa.append(
            (
                f"Why did nothing answer at first?",
                f"At first {hero.label} acted too fast and used {item.label} too harshly. In this world, grabbing sounds make the sacred place go silent before it will listen.",
            )
        )
    else:
        qa.append(
            (
                f"Why did {hero.label} pause before asking the question?",
                f"{hero.label} remembered the warning that old places answer patient rhyme, not grabbing voices. That pause helped {hero.pronoun('object')} become calm enough to ask gently.",
            )
        )
    qa.append(
        (
            "How did the child finally receive an answer?",
            f"{hero.label} scattered the mustard seeds in a small ring, used {item.label} gently, and spoke in rhyme. The careful ritual changed the place from silence to listening, so the answer-sign could appear.",
        )
    )
    qa.append(
        (
            "What were the rhyme lines for?",
            f'The rhyme lines were "{lines[0]}" and "{lines[1]}" They taught {hero.label} to ask with patience instead of grabbing for an answer.',
        )
    )
    if outcome == "guided":
        qa.append(
            (
                "What changed by the end of the story?",
                f"{hero.label} began with rushing curiosity, but ended with calm wonder. The ending shows that {hero.pronoun()} learned mystery can be met gently and still be answered.",
            )
        )
    else:
        qa.append(
            (
                "What changed by the end of the story?",
                f"{hero.label} kept being curious, but now that curiosity had shape and patience. The ending shows that listening made the answer feel like a gift instead of a prize to snatch.",
            )
        )
    return qa


KNOWLEDGE = {
    "mustard": [
        (
            "What is mustard?",
            "Mustard is a plant with tiny seeds and bright yellow flowers. People can use the seeds for food, and the flowers make a field look golden.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words sound alike at the end, like song and long. Rhymes can make words easier to remember and nicer to say aloud.",
        )
    ],
    "echo": [
        (
            "Why do quiet places seem to answer sounds?",
            "Some places send sound back to you as an echo. A hill, a wall, or water can make your voice seem to answer itself.",
        )
    ],
    "river": [
        (
            "Why does a river make sounds?",
            "A river makes sounds when water moves around stones, plants, and bends in the bank. That is why it can seem to hum or sing.",
        )
    ],
    "bees": [
        (
            "Why do bees visit flowers?",
            "Bees visit flowers to gather nectar and pollen. While they move from flower to flower, they also help many plants make seeds.",
        )
    ],
    "stars": [
        (
            "Why can stars be hard to see in the daytime?",
            "Stars are still in the sky in the daytime, but the bright sunlight makes them hard for our eyes to see. At night the sky grows dark enough for the stars to show again.",
        )
    ],
    "dawn": [
        (
            "What is dawn?",
            "Dawn is the early time when night begins to turn into morning. The sky brightens before the sun is fully up.",
        )
    ],
    "wind": [
        (
            "What is wind?",
            "Wind is moving air. You cannot see it directly, but you can see leaves, grass, or flowers bend when it passes.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mustard", "rhyme", "dawn", "stars", "river", "bees", "wind", "echo"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    wonder = world.facts["wonder"]
    place = world.facts["place"]
    tags = {"mustard", "rhyme", "echo"} | set(wonder.tags) | set(place.tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:11} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, wonder: Wonder, item: RitualItem) -> str:
    if not place_fits_wonder(place, wonder):
        return (
            f"(No story: {place.label} is not a place in this world that answers questions about {wonder.question}. "
            f"Pick a wonder the place is known to hold.)"
        )
    if not item_fits_place(item, place):
        needed = ITEMS[place.calls_for].label
        return (
            f"(No story: {place.label} does not answer to {item.label}. In this world it calls for {needed}, so the ritual would not feel reasonable.)"
        )
    return "(No story: that combination does not belong together in this myth.)"


ASP_RULES = r"""
fits_wonder(P,W) :- place(P), wonder(W), affords(P,W).
fits_item(P,I) :- place(P), item(I), calls_for(P,I), used_item(I).

valid(P,W,I) :- place(P), wonder(W), item(I), affords(P,W), calls_for(P,I).

guided :- temperament(hasty).
smooth :- temperament(patient).

outcome(guided) :- guided.
outcome(smooth) :- smooth.

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for wonder_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, wonder_id))
        lines.append(asp.fact("calls_for", place_id, place.calls_for))
    for wonder_id in WONDERS:
        lines.append(asp.fact("wonder", wonder_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("used_item", params.item),
            asp.fact("temperament", params.temperament),
        ]
    )
    model = asp.one_model(asp_program(scenario))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        place="sun_hill",
        wonder="dawn",
        item="bronze_bell",
        hero_name="Nila",
        hero_gender="girl",
        guide_type="grandmother",
        temperament="hasty",
    ),
    StoryParams(
        place="river_steps",
        wonder="river_song",
        item="reed_flute",
        hero_name="Aren",
        hero_gender="boy",
        guide_type="boatman",
        temperament="patient",
    ),
    StoryParams(
        place="mustard_field",
        wonder="bees",
        item="clay_whistle",
        hero_name="Mira",
        hero_gender="girl",
        guide_type="shepherdess",
        temperament="hasty",
    ),
    StoryParams(
        place="sun_hill",
        wonder="stars",
        item="bronze_bell",
        hero_name="Tavi",
        hero_gender="boy",
        guide_type="grandmother",
        temperament="patient",
    ),
    StoryParams(
        place="mustard_field",
        wonder="wind_name",
        item="clay_whistle",
        hero_name="Ila",
        hero_gender="girl",
        guide_type="shepherdess",
        temperament="patient",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child, mustard seeds, rhyme, and a mythic answer."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--guide-type", choices=sorted(GUIDE_TYPES))
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.wonder and args.item:
        if not valid_combo(args.place, args.wonder, args.item):
            raise StoryError(explain_rejection(PLACES[args.place], WONDERS[args.wonder], ITEMS[args.item]))
    if args.place and args.item and args.place in PLACES and args.item in ITEMS:
        if not item_fits_place(ITEMS[args.item], PLACES[args.place]):
            wonder_id = args.wonder or sorted(PLACES[args.place].affords)[0]
            raise StoryError(explain_rejection(PLACES[args.place], WONDERS[wonder_id], ITEMS[args.item]))
    if args.place and args.wonder and args.place in PLACES and args.wonder in WONDERS:
        if not place_fits_wonder(PLACES[args.place], WONDERS[args.wonder]):
            item_id = args.item or PLACES[args.place].calls_for
            raise StoryError(explain_rejection(PLACES[args.place], WONDERS[args.wonder], ITEMS[item_id]))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.wonder is None or c[1] == args.wonder)
        and (args.item is None or c[2] == args.item)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, wonder_id, item_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    guide_type = args.guide_type or rng.choice(sorted(GUIDE_TYPES))
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    return StoryParams(
        place=place_id,
        wonder=wonder_id,
        item=item_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        guide_type=guide_type,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.wonder not in WONDERS:
        raise StoryError(f"(No story: unknown wonder '{params.wonder}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown hero gender '{params.hero_gender}'.)")
    if params.guide_type not in GUIDE_TYPES:
        raise StoryError(f"(No story: unknown guide type '{params.guide_type}'.)")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(No story: unknown temperament '{params.temperament}'.)")

    place = PLACES[params.place]
    wonder = WONDERS[params.wonder]
    item = ITEMS[params.item]
    if not valid_combo(params.place, params.wonder, params.item):
        raise StoryError(explain_rejection(place, wonder, item))

    world = tell(
        place=place,
        wonder=wonder,
        item=item,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        guide_type=params.guide_type,
        temperament=params.temperament,
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


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatch = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcome labels differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, wonder, item) combos:\n")
        for place_id, wonder_id, item_id in combos:
            print(f"  {place_id:13} {wonder_id:15} {item_id}")
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
            header = f"### {p.hero_name}: {p.wonder} at {p.place} ({p.item}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
