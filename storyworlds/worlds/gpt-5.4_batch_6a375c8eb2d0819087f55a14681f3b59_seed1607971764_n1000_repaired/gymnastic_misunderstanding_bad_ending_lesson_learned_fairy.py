#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py
=========================================================================================

A standalone story world for a small fairy-tale domain:

A young fairy is preparing a gymnastic performance for a moonlit celebration.
A messenger delivers instructions about where to practice, but the fairy
misunderstands the message and rehearses in a dangerous place instead. The bad
choice leads to a sad ending for that night's performance, followed by a clear
lesson: when words are uncertain, ask again before acting.

The model is state-driven. A risky surface can crack or slip, a fall can ruin a
special prop, and the missed celebration follows from the simulated world state.
The reasonableness gate constrains stories to combinations where the mistaken
place really is confusable with the intended place and really is dangerous for
gymnastic practice.

Run it
------
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py --message glade_bridge --prop ribbon
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py --message glade_nest
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py --all
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gymnastic_misunderstanding_bad_ending_lesson_learned_fairy.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy_girl", "sprite_girl"}
        male = {"boy", "father", "king", "fairy_boy", "sprite_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "queen": "queen",
            "king": "king",
            "mentor": "aunt",
            "owl": "owl",
            "cricket": "cricket",
        }.get(self.type, self.label or self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SafePlace:
    id: str
    label: str
    phrase: str
    footing: str
    shine: str
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
class RiskyPlace:
    id: str
    label: str
    phrase: str
    hazard: str
    surface: str
    reason: str
    damage: str
    end_image: str
    over: str
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
class Message:
    id: str
    safe_place: str
    risky_place: str
    wording: str
    misheard_as: str
    cause: str
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
class Prop:
    id: str
    label: str
    phrase: str
    ruined: str
    final_loss: str
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
class Messenger:
    id: str
    type: str
    phrase: str
    sound: str
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


def _r_surface_fails(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    place = world.get("risky_place")
    if hero.meters["rehearsing"] < THRESHOLD:
        return out
    if place.attrs.get("stunt_safe", 1) >= 1:
        return out
    sig = ("surface_fails", place.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if place.attrs["hazard"] == "fragile":
        place.meters["cracked"] += 1
    else:
        place.meters["slick"] += 1
    hero.memes["alarm"] += 1
    out.append("__surface__")
    return out


def _r_fall(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    place = world.get("risky_place")
    if place.meters["cracked"] < THRESHOLD and place.meters["slick"] < THRESHOLD:
        return out
    sig = ("fall", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["fell"] += 1
    hero.meters["sore"] += 1
    hero.memes["fear"] += 1
    prop = world.get("prop")
    prop.meters["ruined"] += 1
    if place.attrs["damage"] == "water":
        prop.meters["soaked"] += 1
    else:
        prop.meters["torn"] += 1
    out.append("__fall__")
    return out


def _r_miss_festival(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    if hero.meters["fell"] < THRESHOLD:
        return out
    sig = ("miss_festival", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["regret"] += 1
    hero.memes["lesson"] += 1
    world.get("festival").meters["missed_performance"] += 1
    out.append("__missed__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="surface_fails", tag="physical", apply=_r_surface_fails),
    Rule(name="fall", tag="physical", apply=_r_fall),
    Rule(name="miss_festival", tag="social", apply=_r_miss_festival),
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


def valid_message(message: Message) -> bool:
    return (
        message.safe_place in SAFE_PLACES
        and message.risky_place in RISKY_PLACES
        and message.safe_place != message.risky_place
    )


def valid_combo(message_id: str, prop_id: str, messenger_id: str) -> bool:
    return (
        message_id in MESSAGES
        and prop_id in PROPS
        and messenger_id in MESSENGERS
        and valid_message(MESSAGES[message_id])
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for message_id in sorted(MESSAGES):
        for prop_id in sorted(PROPS):
            for messenger_id in sorted(MESSENGERS):
                if valid_combo(message_id, prop_id, messenger_id):
                    combos.append((message_id, prop_id, messenger_id))
    return combos


def explain_rejection(message_id: str) -> str:
    if message_id not in MESSAGES:
        return "(No story: that message id is unknown.)"
    msg = MESSAGES[message_id]
    if msg.safe_place not in SAFE_PLACES:
        return "(No story: the intended practice place does not exist in this world.)"
    if msg.risky_place not in RISKY_PLACES:
        return "(No story: the misunderstood place does not exist in this world.)"
    if msg.safe_place == msg.risky_place:
        return "(No story: the words do not create a real misunderstanding, because the safe and risky places are the same.)"
    return "(No story: this message does not support a reasonable misunderstanding.)"


def predict_misunderstood_rehearsal(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["rehearsing"] += 1
    propagate(sim, narrate=False)
    place = sim.get("risky_place")
    prop = sim.get("prop")
    return {
        "fell": hero.meters["fell"] >= THRESHOLD,
        "surface_failed": place.meters["cracked"] >= THRESHOLD or place.meters["slick"] >= THRESHOLD,
        "prop_ruined": prop.meters["ruined"] >= THRESHOLD,
        "missed": sim.get("festival").meters["missed_performance"] >= THRESHOLD,
    }


def opening(world: World, hero: Entity, guardian: Entity, prop: Prop) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In the silver age of dew and moonbeams, there lived a little fairy named {hero.id}. "
        f"{hero.pronoun().capitalize()} longed to dance a gymnastic ribbon-turn before the Moon Lantern Feast."
    )
    world.say(
        f"{guardian.label.capitalize()} had given {hero.pronoun('object')} {prop.phrase}, "
        f"and {hero.pronoun()} loved how it caught the light like a piece of morning."
    )


def promise(world: World, guardian: Entity, hero: Entity, safe_place: SafePlace) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'"If you practice with patient feet at {safe_place.phrase}," '
        f"{guardian.label} said, \"you may dance before the whole court tonight.\""
    )


def deliver_message(world: World, messenger: Messenger, message: Message) -> None:
    world.say(
        f"By and by, {messenger.phrase} came with a message from the palace. "
        f"It {messenger.sound} through the clover: \"{message.wording}\""
    )


def misunderstand(
    world: World,
    hero: Entity,
    message: Message,
    safe_place: SafePlace,
    risky_place: RiskyPlace,
) -> None:
    pred = predict_misunderstood_rehearsal(world)
    world.facts["predicted_fall"] = pred["fell"]
    world.facts["predicted_prop_ruined"] = pred["prop_ruined"]
    hero.memes["confusion"] += 1
    world.say(
        f"But the words brushed past too quickly. {hero.id} heard "
        f'"{message.misheard_as}" and thought the message meant {risky_place.phrase}.'
    )
    world.say(
        f"{message.cause.capitalize()}, {hero.pronoun()} never stopped to ask whether "
        f"the palace truly meant {safe_place.phrase} instead."
    )


def choose_wrong_place(world: World, hero: Entity, risky_place: RiskyPlace) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"So {hero.id} flew to {risky_place.phrase}, where {risky_place.reason}. "
        f"The place looked splendid from far away, and that made it easier to trust a mistake."
    )


def rehearse(world: World, hero: Entity, risky_place: RiskyPlace) -> None:
    hero.meters["rehearsing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} chin, spun once, and began a brave gymnastic leap upon {risky_place.surface}."
    )


def surface_turn(world: World, risky_place: RiskyPlace) -> None:
    place = world.get("risky_place")
    if place.meters["cracked"] >= THRESHOLD:
        world.say(
            f"At once there came a soft snap. {risky_place.label.capitalize()} shivered under the landing."
        )
    elif place.meters["slick"] >= THRESHOLD:
        world.say(
            f"At once the silver damp betrayed the step. {risky_place.label.capitalize()} turned slippery as glass."
        )


def fall(world: World, hero: Entity, risky_place: RiskyPlace, prop: Prop) -> None:
    place = world.get("risky_place")
    if hero.meters["fell"] < THRESHOLD:
        return
    if place.attrs["damage"] == "water":
        world.say(
            f"Down {hero.pronoun()} slipped, not into the deep dark, but into the cold shine of {risky_place.over}. "
            f"When {hero.pronoun()} rose again, {prop.ruined}."
        )
    else:
        world.say(
            f"Down {hero.pronoun()} tumbled into {risky_place.over}. When {hero.pronoun()} scrambled free, {prop.ruined}."
        )


def bad_ending(world: World, hero: Entity, guardian: Entity, prop: Prop) -> None:
    festival = world.get("festival")
    if festival.meters["missed_performance"] < THRESHOLD:
        return
    hero.memes["sadness"] += 1
    world.say(
        f"That evening the Moon Lantern Feast still began, but {hero.id} could not dance. "
        f"{hero.pronoun().capitalize()} was too sore, and {prop.final_loss}."
    )
    world.say(
        f"While music rang across the hall, {hero.id} sat beside {guardian.label} with tears bright in {hero.pronoun('possessive')} eyes. "
        f"It was a sad ending for the night {hero.pronoun()} had dreamed about."
    )


def lesson(world: World, hero: Entity, guardian: Entity, safe_place: SafePlace) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f"Then {guardian.label} wrapped a soft wing around {hero.pronoun('object')} and said, "
        f'"Little one, a hurried ear can lead quick feet into trouble. When words sound misty, ask again before you leap."'
    )
    world.say(
        f"{hero.id} nodded and whispered that {hero.pronoun()} understood at last. "
        f"Next time, {hero.pronoun()} would ask once more and practice only at {safe_place.phrase}."
    )


def ending_image(world: World, hero: Entity, safe_place: SafePlace) -> None:
    world.say(
        f"And so, when the next pale moon rose, {hero.id} carried the lesson more carefully than any ribbon, "
        f"and stepped toward {safe_place.phrase} with questions on {hero.pronoun('possessive')} lips and wiser feet below."
    )


def tell(
    message: Message,
    prop_cfg: Prop,
    messenger_cfg: Messenger,
    hero_name: str = "Liora",
    hero_type: str = "fairy_girl",
    guardian_type: str = "queen",
) -> World:
    if message.safe_place not in SAFE_PLACES or message.risky_place not in RISKY_PLACES:
        raise StoryError(explain_rejection(message.id))

    safe_place = SAFE_PLACES[message.safe_place]
    risky_place = RISKY_PLACES[message.risky_place]

    world = World()
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["eager", "young"],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=guardian_type,
        label="the queen",
        role="guardian",
    ))
    world.add(Entity(
        id="safe_place",
        type="place",
        label=safe_place.label,
        phrase=safe_place.phrase,
        attrs={"stunt_safe": 1, "shine": safe_place.shine},
    ))
    world.add(Entity(
        id="risky_place",
        type="place",
        label=risky_place.label,
        phrase=risky_place.phrase,
        attrs={
            "stunt_safe": 0,
            "hazard": risky_place.hazard,
            "damage": risky_place.damage,
            "over": risky_place.over,
        },
    ))
    world.add(Entity(
        id="prop",
        type="prop",
        label=prop_cfg.label,
        phrase=prop_cfg.phrase,
    ))
    world.add(Entity(
        id="festival",
        type="festival",
        label="the Moon Lantern Feast",
    ))

    world.facts.update(
        message=message,
        safe_place=safe_place,
        risky_place_cfg=risky_place,
        prop_cfg=prop_cfg,
        messenger_cfg=messenger_cfg,
        hero_name=hero_name,
        hero_type=hero_type,
    )

    opening(world, hero, guardian, prop_cfg)
    promise(world, guardian, hero, safe_place)

    world.para()
    deliver_message(world, messenger_cfg, message)
    misunderstand(world, hero, message, safe_place, risky_place)
    choose_wrong_place(world, hero, risky_place)

    world.para()
    rehearse(world, hero, risky_place)
    surface_turn(world, risky_place)
    fall(world, hero, risky_place, prop_cfg)

    world.para()
    bad_ending(world, hero, guardian, prop_cfg)
    lesson(world, hero, guardian, safe_place)
    ending_image(world, hero, safe_place)

    world.facts.update(
        hero=hero,
        guardian=guardian,
        fell=hero.meters["fell"] >= THRESHOLD,
        prop_ruined=world.get("prop").meters["ruined"] >= THRESHOLD,
        missed=world.get("festival").meters["missed_performance"] >= THRESHOLD,
    )
    return world


SAFE_PLACES = {
    "moon_glade": SafePlace(
        id="moon_glade",
        label="the moonlit glade",
        phrase="the moonlit glade",
        footing="soft moss",
        shine="pearled with moonlight",
        tags={"glade", "safe_place"},
    ),
    "silver_lawn": SafePlace(
        id="silver_lawn",
        label="the silver lawn",
        phrase="the silver lawn by the palace gate",
        footing="trim springy grass",
        shine="bright with firefly lamps",
        tags={"lawn", "safe_place"},
    ),
    "daisy_ring": SafePlace(
        id="daisy_ring",
        label="the daisy ring",
        phrase="the daisy ring beside the brook",
        footing="flat flower-soft earth",
        shine="circled in tiny stars of dew",
        tags={"flowers", "safe_place"},
    ),
}

RISKY_PLACES = {
    "mushroom_bridge": RiskyPlace(
        id="mushroom_bridge",
        label="the mushroom bridge",
        phrase="the mushroom bridge over the stream",
        hazard="fragile",
        surface="the springy mushroom caps",
        reason="the caps were pretty but thin underneath",
        damage="water",
        end_image="cold water clinging to her wings",
        over="the stream",
        tags={"bridge", "water", "fragile"},
    ),
    "crystal_steps": RiskyPlace(
        id="crystal_steps",
        label="the crystal steps",
        phrase="the crystal stepping stones in the pond",
        hazard="slippery",
        surface="the bright crystal tops",
        reason="dew lay on every stone like glass",
        damage="water",
        end_image="pond water dripping from her hem",
        over="the lily pond",
        tags={"crystal", "water", "slippery"},
    ),
    "thistle_wall": RiskyPlace(
        id="thistle_wall",
        label="the thistle wall",
        phrase="the old thistle wall by the hedge",
        hazard="slippery",
        surface="the narrow wall-top",
        reason="the stones were loose and dusted with pollen",
        damage="thorns",
        end_image="thistle fluff caught in her skirt",
        over="a bed of sharp thistles",
        tags={"wall", "thorns", "slippery"},
    ),
}

MESSAGES = {
    "glade_bridge": Message(
        id="glade_bridge",
        safe_place="moon_glade",
        risky_place="mushroom_bridge",
        wording="Practice in the moonlit glade before dusk.",
        misheard_as="Practice on the mushroom bridge before dusk",
        cause="the brook below was chattering and the message blurred in the air",
        tags={"mishearing", "ask_again"},
    ),
    "lawn_steps": Message(
        id="lawn_steps",
        safe_place="silver_lawn",
        risky_place="crystal_steps",
        wording="Practice on the silver lawn by the palace gate.",
        misheard_as="Practice on the glittering stones by the palace gate",
        cause="the messenger's quick tune made silver sound like glitter",
        tags={"mishearing", "ask_again"},
    ),
    "ring_wall": Message(
        id="ring_wall",
        safe_place="daisy_ring",
        risky_place="thistle_wall",
        wording="Practice at the daisy ring beside the brook.",
        misheard_as="Practice at the high wall beside the brook",
        cause="a gust shook the reeds and swallowed the middle of the sentence",
        tags={"mishearing", "ask_again"},
    ),
    "glade_nest": Message(
        id="glade_nest",
        safe_place="moon_glade",
        risky_place="moon_glade",
        wording="Practice in the moonlit glade before dusk.",
        misheard_as="Practice in the moonlit glade before dusk",
        cause="nothing was actually misunderstood",
        tags={"invalid"},
    ),
}

PROPS = {
    "ribbon": Prop(
        id="ribbon",
        label="ribbon",
        phrase="a moon-silk ribbon",
        ruined="the moon-silk ribbon dragged dim and heavy behind her",
        final_loss="the ribbon had lost its silver float",
        tags={"ribbon"},
    ),
    "crown": Prop(
        id="crown",
        label="flower crown",
        phrase="a flower crown woven with glow-seeds",
        ruined="the flower crown sagged apart and the glow-seeds fell out",
        final_loss="the flower crown was broken beyond wearing",
        tags={"crown", "flowers"},
    ),
    "bells": Prop(
        id="bells",
        label="bell sash",
        phrase="a bell sash tied with blue thread",
        ruined="the little bells were bent and one sweet note was gone",
        final_loss="the bell sash no longer sang clearly enough for the dance",
        tags={"bells"},
    ),
}

MESSENGERS = {
    "owl": Messenger(
        id="owl",
        type="owl",
        phrase="a white owl",
        sound="hooted softly",
        tags={"owl"},
    ),
    "cricket": Messenger(
        id="cricket",
        type="cricket",
        phrase="a green cricket page",
        sound="chirped brightly",
        tags={"cricket"},
    ),
    "swallow": Messenger(
        id="swallow",
        type="swallow",
        phrase="a swift blue swallow",
        sound="sang",
        tags={"bird"},
    ),
}

FAIRY_GIRL_NAMES = ["Liora", "Nessa", "Mira", "Aveline", "Poppy", "Elowen", "Tansy", "Bria"]
FAIRY_BOY_NAMES = ["Rowan", "Ivo", "Pip", "Aster", "Lark", "Nico", "Bram", "Tobin"]
GUARDIANS = ["queen", "mentor"]


@dataclass
class StoryParams:
    message: str
    prop: str
    messenger: str
    hero_name: str
    hero_type: str
    guardian_type: str
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
    "mishearing": [
        (
            "What should you do if you do not understand a message?",
            "You should stop and ask again in a calm voice. Clear words can keep you from making a risky mistake."
        )
    ],
    "ask_again": [
        (
            "Why is asking again a brave thing to do?",
            "Asking again is brave because it means you care more about being right than about rushing. Careful questions can protect you and other people."
        )
    ],
    "bridge": [
        (
            "Why can a mushroom bridge be unsafe for jumping?",
            "A mushroom bridge may look soft and magical, but it can bend or break under a hard landing. Pretty things are not always strong things."
        )
    ],
    "crystal": [
        (
            "Why are wet stones slippery?",
            "Wet stones are slippery because water makes their tops smooth and slick. Feet can slide before you are ready."
        )
    ],
    "thorns": [
        (
            "Why are thistles a bad place to fall?",
            "Thistles are prickly plants with sharp points. Falling into them can hurt and tear clothes."
        )
    ],
    "water": [
        (
            "What can happen if cloth falls into water?",
            "Cloth can get heavy, soggy, and hard to move gracefully. A wet costume or ribbon may no longer work the way it should."
        )
    ],
    "ribbon": [
        (
            "What is a ribbon dance prop?",
            "A ribbon dance prop is a long ribbon that trails through the air when a dancer moves. It needs space and care to look beautiful."
        )
    ],
    "crown": [
        (
            "Why might a flower crown fall apart?",
            "A flower crown is delicate, so rough weather or a tumble can break it apart. Petals and stems are lovely, but they are not sturdy."
        )
    ],
    "bells": [
        (
            "Why do bent bells sound different?",
            "A bell rings well when its shape is even. If it gets bent, the sound can turn dull or crooked."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "mishearing",
    "ask_again",
    "bridge",
    "crystal",
    "thorns",
    "water",
    "ribbon",
    "crown",
    "bells",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    msg = f["message"]
    prop = f["prop_cfg"]
    risky = f["risky_place_cfg"]
    return [
        (
            f'Write a short fairy-tale story for a 3-to-5-year-old that includes the word "gymnastic", '
            f'a misunderstood message, and a sad ending that teaches a lesson.'
        ),
        (
            f"Tell a fairy tale where {hero.label} prepares for a moon feast, misunderstands a message, "
            f"and practices at {risky.phrase} instead of the right place."
        ),
        (
            f"Write a gentle cautionary story in which a young fairy ruins {prop.phrase} after hearing "
            f'"{msg.misheard_as}" and learns to ask again when words sound unclear.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    msg = f["message"]
    safe = f["safe_place"]
    risky = f["risky_place_cfg"]
    prop = f["prop_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young fairy who wanted to dance at the Moon Lantern Feast. "
            f"{guardian.label.capitalize()} and the messenger also mattered because their words set the trouble in motion."
        ),
        (
            "What did the fairy hope to do?",
            f"{hero.label} hoped to perform a gymnastic dance at the feast that night. "
            f"That wish is why the message about practice mattered so much."
        ),
        (
            "What was the misunderstanding?",
            f"The palace meant {safe.phrase}, but {hero.label} thought the message meant {risky.phrase}. "
            f"{msg.cause.capitalize()}, so the mistake felt real until it was too late."
        ),
        (
            f"Why was {risky.label} a bad place to practice?",
            f"It was unsafe because {risky.reason}. "
            f"A hard landing there could make the surface fail under a dancer's feet."
        ),
    ]
    if f.get("fell"):
        qa.append(
            (
                f"What happened when {hero.label} practiced there?",
                f"The surface gave way or turned slick, and {hero.label} fell. "
                f"That tumble also ruined the {prop.label}, so the trouble spread from one misunderstanding into a bigger loss."
            )
        )
    if f.get("missed"):
        qa.append(
            (
                "Why was the ending sad?",
                f"The ending was sad because {hero.label} missed the dance {hero.pronoun()} had dreamed about, and {prop.final_loss}. "
                f"The feast still went on, but the fairy had to sit and watch instead."
            )
        )
    qa.append(
        (
            "What lesson did the fairy learn?",
            f"{hero.label} learned to ask again when words sound uncertain. "
            f"Instead of hurrying to prove {hero.pronoun('object')}self, {hero.pronoun()} would check the message first next time."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["message"].tags) | set(f["risky_place_cfg"].tags) | set(f["prop_cfg"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            out.extend(KNOWLEDGE[key])
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:11} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        message="glade_bridge",
        prop="ribbon",
        messenger="owl",
        hero_name="Liora",
        hero_type="fairy_girl",
        guardian_type="queen",
    ),
    StoryParams(
        message="lawn_steps",
        prop="bells",
        messenger="swallow",
        hero_name="Aster",
        hero_type="fairy_boy",
        guardian_type="mentor",
    ),
    StoryParams(
        message="ring_wall",
        prop="crown",
        messenger="cricket",
        hero_name="Poppy",
        hero_type="fairy_girl",
        guardian_type="queen",
    ),
]


ASP_RULES = r"""
valid_message(M) :- message(M), has_safe(M,S), safe_place(S), has_risky(M,R), risky_place(R), S != R.
valid_combo(M,P,Ms) :- valid_message(M), prop(P), messenger(Ms).

surface_fail(M) :- valid_message(M), has_risky(M,R), risky_hazard(R,fragile).
surface_fail(M) :- valid_message(M), has_risky(M,R), risky_hazard(R,slippery).
fall(M) :- surface_fail(M).
prop_ruined(M,P) :- fall(M), valid_message(M), prop(P).
missed(M) :- fall(M).

#show valid_combo/3.
#show valid_message/1.
#show fall/1.
#show prop_ruined/2.
#show missed/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in sorted(SAFE_PLACES):
        lines.append(asp.fact("safe_place", sid))
    for rid, rp in sorted(RISKY_PLACES.items()):
        lines.append(asp.fact("risky_place", rid))
        lines.append(asp.fact("risky_hazard", rid, rp.hazard))
    for mid, msg in sorted(MESSAGES.items()):
        lines.append(asp.fact("message", mid))
        lines.append(asp.fact("has_safe", mid, msg.safe_place))
        lines.append(asp.fact("has_risky", mid, msg.risky_place))
    for pid in sorted(PROPS):
        lines.append(asp.fact("prop", pid))
    for msid in sorted(MESSENGERS):
        lines.append(asp.fact("messenger", msid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_fall_messages() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show fall/1."))
    return sorted(m for (m,) in asp.atoms(model, "fall"))


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in ASP:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in Python:", sorted(py_valid - asp_valid))

    py_fall = {mid for mid in MESSAGES if valid_message(MESSAGES[mid])}
    asp_fall = set(asp_fall_messages())
    if py_fall == asp_fall:
        print(f"OK: every valid misunderstanding leads to a fall in both models ({len(py_fall)} messages).")
    else:
        rc = 1
        print("MISMATCH in fall messages:")
        if asp_fall - py_fall:
            print("  only in ASP:", sorted(asp_fall - py_fall))
        if py_fall - asp_fall:
            print("  only in Python:", sorted(py_fall - asp_fall))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(17))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("default resolve/generate produced an empty story")
        print("OK: default resolve_params() + generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fairy misunderstands where to practice, a sad ending follows, and a lesson is learned."
    )
    ap.add_argument("--message", choices=sorted(MESSAGES))
    ap.add_argument("--prop", choices=sorted(PROPS))
    ap.add_argument("--messenger", choices=sorted(MESSENGERS))
    ap.add_argument("--guardian", choices=sorted(GUARDIANS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.message is not None and not valid_message(MESSAGES[args.message]):
        raise StoryError(explain_rejection(args.message))

    combos = [
        combo for combo in valid_combos()
        if (args.message is None or combo[0] == args.message)
        and (args.prop is None or combo[1] == args.prop)
        and (args.messenger is None or combo[2] == args.messenger)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    message_id, prop_id, messenger_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        hero_name = args.name
    else:
        hero_name = rng.choice(FAIRY_GIRL_NAMES if gender == "girl" else FAIRY_BOY_NAMES)
    hero_type = "fairy_girl" if gender == "girl" else "fairy_boy"
    guardian_type = args.guardian or rng.choice(GUARDIANS)
    return StoryParams(
        message=message_id,
        prop=prop_id,
        messenger=messenger_id,
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_type=guardian_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.message not in MESSAGES:
        raise StoryError(f"(No story: unknown message '{params.message}'.)")
    if params.prop not in PROPS:
        raise StoryError(f"(No story: unknown prop '{params.prop}'.)")
    if params.messenger not in MESSENGERS:
        raise StoryError(f"(No story: unknown messenger '{params.messenger}'.)")
    if params.guardian_type not in GUARDIANS:
        raise StoryError(f"(No story: unknown guardian type '{params.guardian_type}'.)")
    if not valid_message(MESSAGES[params.message]):
        raise StoryError(explain_rejection(params.message))

    world = tell(
        message=MESSAGES[params.message],
        prop_cfg=PROPS[params.prop],
        messenger_cfg=MESSENGERS[params.messenger],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        guardian_type=params.guardian_type,
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
        print(asp_program("", "#show valid_combo/3.\n#show fall/1.\n#show missed/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (message, prop, messenger) combos:\n")
        for message_id, prop_id, messenger_id in combos:
            print(f"  {message_id:13} {prop_id:8} {messenger_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.message}, {p.prop}, {p.messenger}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
