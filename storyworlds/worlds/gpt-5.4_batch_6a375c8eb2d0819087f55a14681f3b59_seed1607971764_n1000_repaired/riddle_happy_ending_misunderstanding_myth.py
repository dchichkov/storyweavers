#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/riddle_happy_ending_misunderstanding_myth.py
========================================================================

A standalone story world for a tiny myth-shaped tale about a village, a spirit's
riddle, a misunderstanding, and a happy ending.

Premise
-------
Each spring, a village walks to a sacred place and waits for a guardian spirit's
blessing. The spirit speaks in a riddle. The grown-ups misunderstand the riddle
and bring the wrong sort of gift. Nothing terrible happens, but the blessing
does not come, fear begins to grow, and the people think the spirit has become
cold or angry. Then one child, helped by someone who listens closely, realizes
the riddle was asking for a living gift rather than a treasure. The villagers
correct the misunderstanding, and the blessing arrives.

Run it
------
    python storyworlds/worlds/gpt-5.4/riddle_happy_ending_misunderstanding_myth.py
    python storyworlds/worlds/gpt-5.4/riddle_happy_ending_misunderstanding_myth.py --qa
    python storyworlds/worlds/gpt-5.4/riddle_happy_ending_misunderstanding_myth.py --all
    python storyworlds/worlds/gpt-5.4/riddle_happy_ending_misunderstanding_myth.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
NOTICE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt", "priestess"}
        male = {"boy", "man", "father", "uncle", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "priestess": "priestess",
            "priest": "priest",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Spirit:
    id: str
    label: str
    title: str
    domain: str
    blessing: str
    reveal: str
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
class Place:
    id: str
    label: str
    path: str
    shrine: str
    ending_image: str
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
class Riddle:
    id: str
    question: str
    answer_kind: str
    asks_for: str
    hint: str
    misunderstanding: str
    explanation: str
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
class MistakenOffering:
    id: str
    label: str
    phrase: str
    kind: str
    reason: str
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


@dataclass
class TrueGift:
    id: str
    label: str
    phrase: str
    kind: str
    action: str
    spirit_reply: str
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


@dataclass
class Helper:
    id: str
    label: str
    type: str
    notice: int
    method: str
    opening: str
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
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def crowd(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "elder", "helper"}]


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


def _r_misunderstanding(world: World) -> list[str]:
    shrine = world.get("shrine")
    if shrine.meters["wrong_offering"] < THRESHOLD or shrine.meters["blessing"] >= THRESHOLD:
        return []
    sig = ("misunderstood",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["closed"] += 1
    village = world.get("village")
    village.meters["silence"] += 1
    for person in world.crowd():
        person.memes["fear"] += 1
    return ["__silence__"]


def _r_blessing(world: World) -> list[str]:
    shrine = world.get("shrine")
    if shrine.meters["true_gift"] < THRESHOLD:
        return []
    sig = ("blessing",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shrine.meters["blessing"] += 1
    shrine.meters["closed"] = 0.0
    village = world.get("village")
    village.meters["silence"] = 0.0
    village.meters["prosperity"] += 1
    for person in world.crowd():
        person.memes["fear"] = 0.0
        person.memes["relief"] += 1
        person.memes["joy"] += 1
    spirit = world.get("spirit")
    spirit.memes["pleased"] += 1
    return ["__blessing__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="misunderstanding", tag="social", apply=_r_misunderstanding),
    Rule(name="blessing", tag="mythic", apply=_r_blessing),
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
        for sent in produced:
            world.say(sent)
    return produced


def true_gift_matches(riddle: Riddle, gift: TrueGift) -> bool:
    return riddle.answer_kind == gift.kind


def plausible_mistake(riddle: Riddle, mistaken: MistakenOffering) -> bool:
    return mistaken.kind in PLAUSIBLE_MISTAKES.get(riddle.id, set())


def helper_can_resolve(helper: Helper) -> bool:
    return helper.notice >= NOTICE_MIN


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for spirit_id in SPIRITS:
        for place_id in PLACES:
            for riddle_id, riddle in RIDDLES.items():
                for mistaken_id, mistaken in MISTAKEN_OFFERINGS.items():
                    if not plausible_mistake(riddle, mistaken):
                        continue
                    for gift_id, gift in TRUE_GIFTS.items():
                        if not true_gift_matches(riddle, gift):
                            continue
                        for helper_id, helper in HELPERS.items():
                            if helper_can_resolve(helper):
                                combos.append(
                                    (spirit_id, place_id, riddle_id, mistaken_id, gift_id, helper_id)
                                )
    return combos


def outcome_of(params: "StoryParams") -> str:
    if not helper_can_resolve(HELPERS[params.helper]):
        return "unresolved"
    if not plausible_mistake(RIDDLES[params.riddle], MISTAKEN_OFFERINGS[params.mistaken]):
        return "invalid"
    if not true_gift_matches(RIDDLES[params.riddle], TRUE_GIFTS[params.true_gift]):
        return "invalid"
    return "blessed"


def explain_bad_mistake(riddle: Riddle, mistaken: MistakenOffering) -> str:
    return (
        f"(No story: {mistaken.phrase} does not naturally fit this riddle's first misunderstanding. "
        f"The villagers must be able to make a believable mistake from the spirit's words.)"
    )


def explain_bad_gift(riddle: Riddle, gift: TrueGift) -> str:
    return (
        f"(No story: {gift.phrase} does not answer the riddle. "
        f"This world only tells tales where the final gift truly matches the guardian's meaning.)"
    )


def explain_bad_helper(helper: Helper) -> str:
    return (
        f"(No story: {helper.label} is not attentive enough to untangle the misunderstanding. "
        f"Pick a helper who listens more closely.)"
    )


def predict_shrine(world: World, gift_kind: str) -> dict:
    sim = world.copy()
    shrine = sim.get("shrine")
    if gift_kind == "wrong":
        shrine.meters["wrong_offering"] += 1
    elif gift_kind == "true":
        shrine.meters["true_gift"] += 1
    propagate(sim, narrate=False)
    return {
        "closed": sim.get("shrine").meters["closed"] >= THRESHOLD,
        "blessing": sim.get("shrine").meters["blessing"] >= THRESHOLD,
        "fear": sum(person.memes["fear"] for person in sim.crowd()),
    }


def procession(world: World, hero: Entity, elder: Entity, spirit: Spirit, place: Place) -> None:
    hero.memes["wonder"] += 1
    elder.memes["duty"] += 1
    world.say(
        f"Each spring, when the first swallows bent through the sky, {hero.id} climbed "
        f"{place.path} with the rest of the village. At {place.shrine}, they waited for "
        f"{spirit.title}, the {spirit.domain}, whose blessing always touched the valley."
    )


def speak_riddle(world: World, spirit_cfg: Spirit, riddle: Riddle) -> None:
    world.get("spirit").memes["mystery"] += 1
    world.say(
        f"A soft voice rose from the shrine stones, and everyone fell still. "
        f'"{riddle.question}" asked {spirit_cfg.label}.'
    )
    world.facts["riddle_question"] = riddle.question


def elder_interprets(
    world: World,
    elder: Entity,
    mistaken: MistakenOffering,
    riddle: Riddle,
) -> None:
    elder.memes["certainty"] += 1
    world.say(
        f'{elder.id}, who kept the old customs, lifted {elder.pronoun("possessive")} chin. '
        f'"It must mean {mistaken.reason}," {elder.pronoun()} said. '
        f'Soon the villagers gathered {mistaken.phrase}.'
    )
    world.facts["misunderstanding_text"] = riddle.misunderstanding


def offer_wrong(world: World, spirit_cfg: Spirit, place: Place, mistaken: MistakenOffering) -> None:
    shrine = world.get("shrine")
    shrine.meters["wrong_offering"] += 1
    prediction = predict_shrine(world, "wrong")
    world.facts["wrong_prediction_fear"] = prediction["fear"]
    propagate(world, narrate=False)
    world.say(
        f"They laid {mistaken.phrase} before the shrine of {spirit_cfg.label}. "
        f"But the stones stayed dim, and the wind only curled around the offering."
    )
    if shrine.meters["closed"] >= THRESHOLD:
        world.say(
            f"A hush spread over {place.label}. Some villagers whispered that the guardian had turned away."
        )


def helper_listens(world: World, hero: Entity, helper: Helper, riddle: Riddle) -> None:
    hero.memes["thought"] += 1
    guide = world.get("helper")
    guide.memes["attention"] += 1
    world.say(
        f"{helper.opening} {guide.label.capitalize()} {helper.method}, and {hero.id} listened too. "
        f"Together they noticed the riddle's hidden turn: {riddle.hint}."
    )


def rethink(world: World, hero: Entity, elder: Entity, riddle: Riddle, gift: TrueGift) -> None:
    hero.memes["courage"] += 1
    elder.memes["doubt"] += 1
    world.say(
        f'"Maybe the spirit did not ask for treasure at all," {hero.id} said softly. '
        f'"Maybe the answer is {gift.label}."'
    )
    world.say(
        f"At first the grown-ups stared, because {riddle.misunderstanding}. Then the elder heard the words again in silence."
    )


def offer_true(world: World, spirit_cfg: Spirit, gift: TrueGift) -> None:
    shrine = world.get("shrine")
    shrine.meters["true_gift"] += 1
    prediction = predict_shrine(world, "true")
    world.facts["true_prediction_blessing"] = prediction["blessing"]
    propagate(world, narrate=False)
    world.say(
        f"So the villagers {gift.action}. {gift.spirit_reply}"
    )


def reveal(world: World, spirit_cfg: Spirit, place: Place, riddle: Riddle) -> None:
    world.say(
        f"Then {spirit_cfg.reveal}. The people understood that no anger had ever lived in the shrine; "
        f"only a misunderstanding had stood there."
    )
    world.say(
        f"Soon {spirit_cfg.blessing}, and {place.ending_image}."
    )
    world.facts["lesson"] = riddle.explanation


def tell(
    spirit_cfg: Spirit,
    place: Place,
    riddle: Riddle,
    mistaken: MistakenOffering,
    true_gift: TrueGift,
    helper_cfg: Helper,
    hero_name: str = "Nila",
    hero_gender: str = "girl",
    elder_type: str = "priestess",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=["curious", "gentle"],
            attrs={"age_band": "child"},
        )
    )
    elder_name = "Mother Sere" if elder_type in {"priestess", "aunt", "mother"} else "Old Teren"
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            label=elder_name,
            role="elder",
            traits=["revered"],
            attrs={"keeps_customs": True},
        )
    )
    helper_name = helper_cfg.label.capitalize()
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_cfg.type,
            label=helper_cfg.label,
            role="helper",
            traits=["attentive"],
            attrs={"notice": helper_cfg.notice},
        )
    )
    spirit = world.add(
        Entity(
            id="spirit",
            kind="character",
            type="spirit",
            label=spirit_cfg.label,
            role="spirit",
            traits=["ancient"],
            attrs={"domain": spirit_cfg.domain},
        )
    )
    shrine = world.add(
        Entity(
            id="shrine",
            kind="thing",
            type="shrine",
            label=place.shrine,
            role="shrine",
            attrs={"place": place.label},
        )
    )
    village = world.add(
        Entity(
            id="village",
            kind="thing",
            type="village",
            label="the village",
            role="village",
            attrs={"place": place.label},
        )
    )

    world.facts.update(
        spirit_cfg=spirit_cfg,
        place=place,
        riddle=riddle,
        mistaken=mistaken,
        true_gift=true_gift,
        helper_cfg=helper_cfg,
        hero=hero,
        elder=elder,
        helper=helper,
        outcome="blessed",
        misunderstanding=False,
        blessing=False,
    )

    procession(world, hero, elder, spirit_cfg, place)
    speak_riddle(world, spirit_cfg, riddle)

    world.para()
    elder_interprets(world, elder, mistaken, riddle)
    offer_wrong(world, spirit_cfg, place, mistaken)
    world.facts["misunderstanding"] = shrine.meters["closed"] >= THRESHOLD

    world.para()
    helper_listens(world, hero, helper_cfg, riddle)
    rethink(world, hero, elder, riddle, true_gift)

    world.para()
    offer_true(world, spirit_cfg, true_gift)
    reveal(world, spirit_cfg, place, riddle)
    world.facts["blessing"] = shrine.meters["blessing"] >= THRESHOLD
    return world


@dataclass
class StoryParams:
    spirit: str
    place: str
    riddle: str
    mistaken: str
    true_gift: str
    helper: str
    hero_name: str
    hero_gender: str
    elder_type: str
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


SPIRITS = {
    "river_mother": Spirit(
        id="river_mother",
        label="the River Mother",
        title="the River Mother",
        domain="keeper of the green river",
        blessing="water ran clear through every furrow",
        reveal="the River Mother's face shone in the water like a moon made of rain",
        tags={"river", "spirit"},
    ),
    "mist_stag": Spirit(
        id="mist_stag",
        label="the Mist Stag",
        title="the Mist Stag",
        domain="horned guardian of the dawn meadows",
        blessing="silver dew settled on the barley and did not spoil",
        reveal="the Mist Stag stepped from the white air with dew hanging from his antlers",
        tags={"mist", "spirit"},
    ),
    "laurel_lady": Spirit(
        id="laurel_lady",
        label="the Laurel Lady",
        title="the Laurel Lady",
        domain="quiet watcher of the hill groves",
        blessing="the fig trees lifted sweet leaves toward the sun",
        reveal="the Laurel Lady rose from the laurel shade with leaves woven in her hair",
        tags={"grove", "spirit"},
    ),
}

PLACES = {
    "ford": Place(
        id="ford",
        label="the old ford",
        path="the reed-bright path to the ford",
        shrine="the stone arch at the ford",
        ending_image="children splashed in the shallow edges while their parents laughed",
        tags={"water"},
    ),
    "spring_cave": Place(
        id="spring_cave",
        label="the spring cave",
        path="the ferny path to the spring cave",
        shrine="the cave mouth ringed with white stone",
        ending_image="the cave pool shone so brightly that even the swallows dipped to look",
        tags={"cave"},
    ),
    "laurel_steps": Place(
        id="laurel_steps",
        label="the laurel steps",
        path="the long steps under the laurel trees",
        shrine="the mossy altar at the top of the steps",
        ending_image="laurel leaves trembled above the village like little green hands clapping",
        tags={"grove"},
    ),
}

RIDDLES = {
    "mouth_bright": Riddle(
        id="mouth_bright",
        question="What is carried by every mouth, brightens the dark bank, and leaves no ash?",
        answer_kind="song",
        asks_for="song",
        hint="something borne by mouths is made by voices",
        misunderstanding="the words about brightness had made them think of flame",
        explanation="The riddle spoke of voices, not fire. A song can brighten hearts without burning anything.",
        tags={"riddle", "song"},
    ),
    "grows_when_shared": Riddle(
        id="grows_when_shared",
        question="What fills many hands, grows when given away, and is never lighter for being split?",
        answer_kind="story",
        asks_for="story",
        hint="only a tale can be handed on without becoming smaller",
        misunderstanding="the words about many hands had made them think of silver or grain",
        explanation="The spirit wanted a shared tale, because stories grow by being passed from person to person.",
        tags={"riddle", "story"},
    ),
    "warms_without_coals": Riddle(
        id="warms_without_coals",
        question="What warms the lonely and mends the day, though no brazier glows?",
        answer_kind="kindness",
        asks_for="kindness",
        hint="the warmth in the riddle belonged to hearts, not coals",
        misunderstanding="the word warms had made them think of cloth and firepots",
        explanation="The spirit asked for kindness, the warmth people make for one another without any flame.",
        tags={"riddle", "kindness"},
    ),
}

MISTAKEN_OFFERINGS = {
    "torches": MistakenOffering(
        id="torches",
        label="torches",
        phrase="three new torches bound with red thread",
        kind="fire",
        reason="the spirit wanted bright flame",
        tags={"fire"},
    ),
    "silver_bowl": MistakenOffering(
        id="silver_bowl",
        label="silver bowl",
        phrase="a silver bowl full of coins",
        kind="silver",
        reason="the spirit wanted something that filled many hands",
        tags={"silver"},
    ),
    "grain_basket": MistakenOffering(
        id="grain_basket",
        label="grain basket",
        phrase="a willow basket piled with shining grain",
        kind="grain",
        reason="the spirit wanted food to heap into open hands",
        tags={"grain"},
    ),
    "braziers": MistakenOffering(
        id="braziers",
        label="braziers",
        phrase="two little braziers of cedar coal",
        kind="fire",
        reason="the spirit wanted warmth from coals",
        tags={"fire"},
    ),
    "wool_cloak": MistakenOffering(
        id="wool_cloak",
        label="wool cloak",
        phrase="a soft wool cloak stitched with sun-colored thread",
        kind="cloth",
        reason="the spirit wanted to warm the lonely",
        tags={"cloth"},
    ),
}

TRUE_GIFTS = {
    "chorus_song": TrueGift(
        id="chorus_song",
        label="a song",
        phrase="a song sung together",
        kind="song",
        action="joined hands and sang the old river hymn until the notes crossed the water",
        spirit_reply="At once the air answered with a clear note of its own.",
        tags={"song"},
    ),
    "shared_story": TrueGift(
        id="shared_story",
        label="a story",
        phrase="a story told aloud",
        kind="story",
        action="sat on the shrine steps and each added a piece to the village's oldest story",
        spirit_reply="The stones gave back every line as if they had been waiting to hear it finished.",
        tags={"story"},
    ),
    "open_table": TrueGift(
        id="open_table",
        label="kindness",
        phrase="an act of kindness",
        kind="kindness",
        action="set their offerings aside, shared bread with the poorest families, and wrapped the coldest child in a warm shawl",
        spirit_reply="A warm wind moved through the shrine like a grateful breath.",
        tags={"kindness", "sharing"},
    ),
}

HELPERS = {
    "echo_heron": Helper(
        id="echo_heron",
        label="the heron-keeper",
        type="woman",
        notice=3,
        method="tilted her head and listened to how the last words echoed back from the stones",
        opening="Just then,",
        tags={"listening"},
    ),
    "goat_boy": Helper(
        id="goat_boy",
        label="the goat boy",
        type="boy",
        notice=2,
        method="repeated the riddle under his breath until the strangest words sounded plain",
        opening="Nearby,",
        tags={"listening"},
    ),
    "reed_aunt": Helper(
        id="reed_aunt",
        label="the reed aunt",
        type="aunt",
        notice=3,
        method="closed her eyes and listened to the spaces between the lines",
        opening="At the edge of the crowd,",
        tags={"listening"},
    ),
    "drummer": Helper(
        id="drummer",
        label="the festival drummer",
        type="man",
        notice=1,
        method="kept tapping the same loud beat and never quite heard the words clearly",
        opening="Beside the steps,",
        tags={"noise"},
    ),
}

PLAUSIBLE_MISTAKES = {
    "mouth_bright": {"torches"},
    "grows_when_shared": {"silver_bowl", "grain_basket"},
    "warms_without_coals": {"braziers", "wool_cloak"},
}

GIRL_NAMES = ["Nila", "Sera", "Mira", "Tali", "Ione", "Dara", "Luma", "Rhea"]
BOY_NAMES = ["Tarin", "Eran", "Milo", "Corin", "Lio", "Pavel", "Soren", "Niko"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    spirit = f["spirit_cfg"]
    riddle = f["riddle"]
    gift = f["true_gift"]
    place = f["place"]
    return [
        f'Write a short mythic story for a 3-to-5-year-old that includes the word "riddle" and a happy ending.',
        f"Tell a gentle myth where a child named {hero.id} hears a spirit's riddle at {place.label}, the grown-ups misunderstand it, and the right answer turns out to be {gift.label}.",
        f"Write a story in a myth style about {spirit.label}, a misunderstanding about a riddle, and a joyful blessing at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    helper = f["helper"]
    spirit = f["spirit_cfg"]
    place = f["place"]
    riddle = f["riddle"]
    mistaken = f["mistaken"]
    gift = f["true_gift"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, the villagers, {elder.id}, and {spirit.label} at {place.label}. "
            f"The story follows how they moved from confusion to understanding.",
        ),
        (
            "What did the spirit say?",
            f"{spirit.label} spoke a riddle at the shrine. The riddle was: \"{riddle.question}\"",
        ),
        (
            "What was the misunderstanding?",
            f"The villagers thought the riddle meant {mistaken.reason}, so they brought {mistaken.phrase}. "
            f"They misunderstood the spirit because {f['misunderstanding_text']}.",
        ),
        (
            f"How did {hero.id} begin to solve the problem?",
            f"{hero.id} listened again with help from {helper.label}. Together they noticed that {riddle.hint}. "
            f"That changed the riddle from something literal into something living.",
        ),
        (
            "How was the riddle answered in the end?",
            f"The villagers answered it with {gift.label}: they {gift.action}. "
            f"That worked because {riddle.explanation}",
        ),
        (
            "Why did the ending become happy?",
            f"The spirit had never wanted treasure at all. Once the misunderstanding was cleared up, the blessing came and the people were relieved and joyful.",
        ),
    ]
    return qa


KNOWLEDGE = {
    "riddle": [
        (
            "What is a riddle?",
            "A riddle is a puzzling question with a hidden answer. You have to think about what the words really mean, not just the first thing they sound like.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old kind of story about gods, spirits, or magical beings. It often explains why people do certain rituals or how a place became special.",
        )
    ],
    "song": [
        (
            "How can a song be a gift?",
            "A song can be a gift because it brings beauty and feeling to other people. When people sing together, they share something living that cannot be held in a box.",
        )
    ],
    "story": [
        (
            "Why do stories grow when they are shared?",
            "Stories grow when they are shared because each new listener carries them onward. Sometimes people remember new details or tell them with fresh warmth.",
        )
    ],
    "kindness": [
        (
            "How can kindness feel warm?",
            "Kindness can feel warm because being cared for makes people feel safe and comforted. That warmth comes from hearts and actions, not from fire.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or sees something the wrong way. The problem can be fixed when people slow down, listen, and understand each other better.",
        )
    ],
    "spirit": [
        (
            "What is a guardian spirit in a story?",
            "A guardian spirit is a magical being that watches over a place, such as a river or grove. In stories, people often show respect to such a being with songs, gifts, or careful words.",
        )
    ],
}

KNOWLEDGE_ORDER = ["riddle", "myth", "misunderstanding", "spirit", "song", "story", "kindness"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"riddle", "myth", "misunderstanding", "spirit", f["true_gift"].kind}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        spirit="river_mother",
        place="ford",
        riddle="mouth_bright",
        mistaken="torches",
        true_gift="chorus_song",
        helper="echo_heron",
        hero_name="Nila",
        hero_gender="girl",
        elder_type="priestess",
    ),
    StoryParams(
        spirit="mist_stag",
        place="spring_cave",
        riddle="grows_when_shared",
        mistaken="silver_bowl",
        true_gift="shared_story",
        helper="goat_boy",
        hero_name="Tarin",
        hero_gender="boy",
        elder_type="priest",
    ),
    StoryParams(
        spirit="laurel_lady",
        place="laurel_steps",
        riddle="warms_without_coals",
        mistaken="wool_cloak",
        true_gift="open_table",
        helper="reed_aunt",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="aunt",
    ),
    StoryParams(
        spirit="river_mother",
        place="spring_cave",
        riddle="grows_when_shared",
        mistaken="grain_basket",
        true_gift="shared_story",
        helper="echo_heron",
        hero_name="Corin",
        hero_gender="boy",
        elder_type="priest",
    ),
]


ASP_RULES = r"""
plausible_mistake(R, M) :- riddle(R), mistaken(M), mistake_for(R, M).
matches(R, G) :- riddle(R), gift(G), answer_kind(R, K), gift_kind(G, K).
resolving_helper(H) :- helper(H), notice(H, N), notice_min(M), N >= M.

valid(S, P, R, M, G, H) :-
    spirit(S), place(P), riddle(R), mistaken(M), gift(G), helper(H),
    plausible_mistake(R, M), matches(R, G), resolving_helper(H).

outcome(blessed) :- chosen_helper(H), resolving_helper(H),
                    chosen_riddle(R), chosen_mistaken(M), plausible_mistake(R, M),
                    chosen_gift(G), matches(R, G).
outcome(unresolved) :- chosen_helper(H), not resolving_helper(H).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SPIRITS:
        lines.append(asp.fact("spirit", sid))
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for rid, riddle in RIDDLES.items():
        lines.append(asp.fact("riddle", rid))
        lines.append(asp.fact("answer_kind", rid, riddle.answer_kind))
        for mid in sorted(PLAUSIBLE_MISTAKES.get(rid, set())):
            lines.append(asp.fact("mistake_for", rid, mid))
    for mid in MISTAKEN_OFFERINGS:
        lines.append(asp.fact("mistaken", mid))
    for gid, gift in TRUE_GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_kind", gid, gift.kind))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("notice", hid, helper.notice))
    lines.append(asp.fact("notice_min", NOTICE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_riddle", params.riddle),
            asp.fact("chosen_mistaken", params.mistaken),
            asp.fact("chosen_gift", params.true_gift),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _validate_params(params: StoryParams) -> None:
    if params.spirit not in SPIRITS:
        raise StoryError(f"(Unknown spirit: {params.spirit})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.riddle not in RIDDLES:
        raise StoryError(f"(Unknown riddle: {params.riddle})")
    if params.mistaken not in MISTAKEN_OFFERINGS:
        raise StoryError(f"(Unknown mistaken offering: {params.mistaken})")
    if params.true_gift not in TRUE_GIFTS:
        raise StoryError(f"(Unknown true gift: {params.true_gift})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown hero gender: {params.hero_gender})")
    if params.elder_type not in {"priestess", "priest", "aunt", "uncle", "mother", "father"}:
        raise StoryError(f"(Unknown elder type: {params.elder_type})")

    riddle = RIDDLES[params.riddle]
    mistaken = MISTAKEN_OFFERINGS[params.mistaken]
    gift = TRUE_GIFTS[params.true_gift]
    helper = HELPERS[params.helper]
    if not plausible_mistake(riddle, mistaken):
        raise StoryError(explain_bad_mistake(riddle, mistaken))
    if not true_gift_matches(riddle, gift):
        raise StoryError(explain_bad_gift(riddle, gift))
    if not helper_can_resolve(helper):
        raise StoryError(explain_bad_helper(helper))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A myth-shaped story world about a spirit's riddle, a misunderstanding, and a happy ending."
    )
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--riddle", choices=RIDDLES)
    ap.add_argument("--mistaken", choices=MISTAKEN_OFFERINGS)
    ap.add_argument("--true-gift", dest="true_gift", choices=TRUE_GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["priestess", "priest", "aunt", "uncle", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and question sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.riddle and args.mistaken:
        riddle = RIDDLES[args.riddle]
        mistaken = MISTAKEN_OFFERINGS[args.mistaken]
        if not plausible_mistake(riddle, mistaken):
            raise StoryError(explain_bad_mistake(riddle, mistaken))
    if args.riddle and args.true_gift:
        riddle = RIDDLES[args.riddle]
        gift = TRUE_GIFTS[args.true_gift]
        if not true_gift_matches(riddle, gift):
            raise StoryError(explain_bad_gift(riddle, gift))
    if args.helper:
        helper = HELPERS[args.helper]
        if not helper_can_resolve(helper):
            raise StoryError(explain_bad_helper(helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.spirit is None or combo[0] == args.spirit)
        and (args.place is None or combo[1] == args.place)
        and (args.riddle is None or combo[2] == args.riddle)
        and (args.mistaken is None or combo[3] == args.mistaken)
        and (args.true_gift is None or combo[4] == args.true_gift)
        and (args.helper is None or combo[5] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    spirit, place, riddle, mistaken, true_gift, helper = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["priestess", "priest", "aunt", "uncle"])
    return StoryParams(
        spirit=spirit,
        place=place,
        riddle=riddle,
        mistaken=mistaken,
        true_gift=true_gift,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        spirit_cfg=SPIRITS[params.spirit],
        place=PLACES[params.place],
        riddle=RIDDLES[params.riddle],
        mistaken=MISTAKEN_OFFERINGS[params.mistaken],
        true_gift=TRUE_GIFTS[params.true_gift],
        helper_cfg=HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: ASP outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (spirit, place, riddle, mistaken, true_gift, helper) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
                f"### {p.hero_name}: {p.riddle} at {p.place} "
                f"({p.spirit}, mistaken {p.mistaken}, true {p.true_gift})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
