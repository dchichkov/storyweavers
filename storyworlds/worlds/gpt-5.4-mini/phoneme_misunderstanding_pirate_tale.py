#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py
=======================================================================

A standalone storyworld for a tiny pirate-tale domain built around a
phoneme misunderstanding: a child pirate hears a word wrong, follows the
wrong sound clue, and a careful crew member helps them fix the mix-up.

The simulation keeps the story small and concrete:
- typed entities with physical meters and emotional memes
- a causal world state that drives the prose
- a reasonableness gate for only sensible story variants
- an inline ASP twin for the gate and the outcome model
- three Q&A sets grounded in simulated world state

The seed inspiration is a pirate tale with the target word "phoneme" and a
misunderstanding feature. The world is not about linguistics in the abstract;
instead, the phoneme is a treasure clue that is heard badly at first.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py
    python storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4-mini/phoneme_misunderstanding_pirate_tale.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    scene: str
    nook: str
    ship: str
    quest: str
    dark_place: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Clue:
    id: str
    hear: str
    label: str
    object_phrase: str
    clue_phrase: str
    safe_phrase: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Place:
    id: str
    label: str
    the: str
    near: str
    flammable: bool = True
    spread: int = 2
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Substitute:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    success: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("alarm", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            if kid.role in {"seeker", "helper"}:
                kid.memes["fear"] += 1
        out.append("__alarm__")
    return out


CAUSAL_RULES = [Rule("alarm", "social", _r_alarm)]


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


def hazard_at_risk(clue: Clue, place: Place) -> bool:
    return clue.label == "phoneme" and place.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(place: Place, delay: int) -> int:
    return place.spread + delay


def is_contained(response: Response, place: Place, delay: int) -> bool:
    return response.power >= fire_severity(place, delay)


def would_avert(relation: str, helper_age: int, seeker_age: int, helper_trait: str) -> bool:
    older_helper = relation == "siblings" and helper_age > seeker_age
    return older_helper and helper_trait in {"careful", "cautious", "steady"}


def _do_clue(world: World, place: Entity, narrate: bool = True) -> None:
    place.meters["burning"] += 1
    propagate(world, narrate=narrate)


def predict_hazard(world: World, place_id: str) -> dict:
    sim = world.copy()
    _do_clue(sim, sim.get(place_id), narrate=False)
    return {"burning": sim.get(place_id).meters["burning"] >= THRESHOLD}


def start(world: World, seeker: Entity, helper: Entity, setting: Setting) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright deck under a blue sky, {seeker.id} and {helper.id} turned the ship into "
        f"{setting.scene}. {setting.ship}"
    )
    world.say(
        f"They made a little map from a scrap of cloth and set their sights on {setting.quest}."
    )


def need_help(world: World, seeker: Entity, setting: Setting, place: Place) -> None:
    world.say(
        f"But the {setting.dark_place} was deep and dark, {place.drape if hasattr(place, 'drape') else place.the} "
        f"swallowing the light."
    )
    world.say(f'"We need a clue," said {seeker.id}.')


def mishear(world: World, seeker: Entity, clue: Clue) -> None:
    seeker.memes["curiosity"] += 1
    world.say(
        f'{seeker.id} pointed at {clue.object_phrase}. "{clue.hear}! I heard the captain say '
        f'{clue.label}!"'
    )
    world.say("For one excited moment, the sound seemed like a perfect guide.")


def warn(world: World, helper: Entity, seeker: Entity, clue: Clue, place: Place, parent: Entity) -> None:
    pred = predict_hazard(world, "place")
    helper.memes["caution"] += 1
    world.facts["predicted"] = pred["burning"]
    world.say(
        f'{helper.id} shook {helper.pronoun("possessive")} head. "{seeker.id}, that is not a toy.'
        f' {parent.label_word.capitalize()} said so. It could make a real flame, and {place.the} could catch."'
    )


def defy(world: World, seeker: Entity, helper: Entity, clue: Clue) -> None:
    seeker.memes["defiance"] += 1
    world.say(
        f'"No, I know what I heard," {seeker.id} said, and {seeker.id} rushed off with the clue.'
    )


def back_down(world: World, seeker: Entity, helper: Entity, clue: Clue, parent: Entity, setting: Setting) -> None:
    seeker.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'"No, I know what I heard," {seeker.id} began. But {helper.id} was {helper.pronoun("possessive")} '
        f"older shipmate, so {seeker.id} paused, thought better of it, and left the {clue.label} alone."
    )
    world.say(
        f"They went to tell {parent.label_word.capitalize()} about the dark nook in {setting.quest} instead."
    )


def ignite(world: World, place_ent: Entity, clue: Clue, place: Place) -> None:
    _do_clue(world, place_ent)
    world.say(
        f'The clue cracked with a tiny spark, and the sound of it felt like a bright little flame. '
        f'Then the flame leaned toward {place.near} and the trouble began.'
    )


def alarm(world: World, helper: Entity, seeker: Entity, place: Place, parent: Entity) -> None:
    world.say(f'"{seeker.id}! Fire! {place.The}!" {helper.id} shouted.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, place_ent: Entity, place: Place) -> None:
    place_ent.meters["burning"] = 0.0
    body = response.success.replace("{place}", place.label)
    world.say(
        f"{parent.label_word.capitalize()} came running. In a flash {parent.pronoun()} {body}."
    )
    world.say("The flame hissed out, leaving only a smoky smell and two shaken pirates.")


def lesson(world: World, parent: Entity, seeker: Entity, helper: Entity, clue: Clue) -> None:
    for kid in (seeker, helper):
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I am glad you called me," {parent.pronoun()} said softly. '
        f'"But remember: {clue.label} is not a toy. A real flame can grow faster than you can run."'
    )
    world.say(f'"We promise," whispered {seeker.id} and {helper.id} together.')


def safe_reward(world: World, parent: Entity, seeker: Entity, helper: Entity, setting: Setting, s1: Substitute, s2: Substitute) -> None:
    seeker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"The next morning, {parent.label_word.capitalize()} had a surprise. {parent.pronoun().capitalize()} handed them "
        f"{s1.phrase} that {s1.glow}, and {s2.phrase} that {s2.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does a pirate need to explore {setting.quest}?"'
    )
    world.say(
        f"{seeker.id} lifted the {s1.label}. {helper.id} held the {s2.label}. "
        f'"Safe light!" they cheered.'
    )
    world.say(f"This time, the crew sailed on {setting.ship.lower()}-steady and safe.")


def rescue_fail(world: World, parent: Entity, response: Response, place_ent: Entity, place: Place) -> None:
    if "room" in world.entities:
        world.get("room").meters["burning"] += 1
    place_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{parent.label_word.capitalize()} came running, but {response.fail.replace('{place}', place.label)}"
    )
    world.say(f"The flame leapt from {place.the} and raced across the deck.")


def escape_and_loss(world: World, parent: Entity, seeker: Entity, helper: Entity) -> None:
    world.say(
        f"There was no time to be brave heroes. {parent.label_word.capitalize()} grabbed {seeker.id} and {helper.id} by the hand and rushed them away."
    )
    world.say(
        "From the shore they watched the ship glow orange, and by the time the smoke cleared, the little game was gone."
    )


def grim_lesson(world: World, parent: Entity, seeker: Entity, helper: Entity, clue: Clue) -> None:
    for kid in (seeker, helper):
        kid.memes["love"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"{parent.label_word.capitalize()} held them tight on the sand. 'You are safe,' {parent.pronoun()} whispered."
    )
    world.say(
        f"After that, {seeker.id} and {helper.id} never forgot that {clue.label} was a grown-up thing, not a game."
    )


def tell(setting: Setting, clue: Clue, place: Place, substitutes: tuple[Substitute, Substitute], response: Response,
         seeker: str = "Pip", seeker_gender: str = "boy", helper: str = "Mara", helper_gender: str = "girl",
         parent_type: str = "father", helper_trait: str = "careful", delay: int = 0,
         seeker_age: int = 6, helper_age: int = 4, relation: str = "siblings") -> World:
    world = World()
    s = world.add(Entity(id=seeker, kind="character", type=seeker_gender, role="seeker", traits=["bold"], attrs={"relation": relation}))
    h = world.add(Entity(id=helper, kind="character", type=helper_gender, role="helper", traits=[helper_trait], attrs={"relation": relation}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the captain"))
    world.add(Entity(id="room", type="room", label="the deck"))
    place_ent = world.add(Entity(id="place", type="place", label=place.label))
    s.memes["bravery"] = 6.0
    h.memes["caution"] = 5.0
    world.facts["setting"] = setting
    world.facts["clue"] = clue
    world.facts["place_cfg"] = place
    world.facts["response"] = response
    world.facts["substitutes"] = substitutes

    start(world, s, h, setting)
    need_help(world, s, setting, place)
    world.para()
    mishear(world, s, clue)
    warn(world, h, s, clue, place, parent)

    if would_avert(relation, helper_age, seeker_age, helper_trait):
        back_down(world, s, h, clue, parent, setting)
        world.para()
        safe_reward(world, parent, s, h, setting, substitutes[0], substitutes[1])
        outcome = "averted"
        severity = 0
        contained = True
    else:
        defy(world, s, h, clue)
        world.para()
        ignite(world, place_ent, clue, place)
        alarm(world, h, s, place, parent)
        severity = fire_severity(place, delay)
        contained = is_contained(response, place, delay)
        world.facts["severity"] = severity
        world.para()
        if contained:
            rescue(world, parent, response, place_ent, place)
            lesson(world, parent, s, h, clue)
            world.para()
            safe_reward(world, parent, s, h, setting, substitutes[0], substitutes[1])
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, place_ent, place)
            escape_and_loss(world, parent, s, h)
            grim_lesson(world, parent, s, h, clue)
            outcome = "burned"

    world.facts.update(
        seeker=s, helper=h, parent=parent, outcome=outcome, severity=severity,
        contained=contained, delay=delay, promised=s.memes["lesson"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "harbor": Setting("harbor", "a busy harbor game", "the map nook", "the toy ship", "the lost lantern", "the galley"),
    "island": Setting("island", "a sandy island game", "the shell cave", "the little ship", "the pearl path", "the palm shadows"),
    "cave": Setting("cave", "a brave cave game", "the lantern corner", "the wooden ship", "the hidden coin", "the black passage"),
}

CLUES = {
    "phoneme": Clue("phoneme", "Fo-nem", "phoneme", "the phoneme card", "a phoneme clue", "a safe listening clue",
                    tags={"phoneme", "sound", "call_adult"}),
    "rhythm": Clue("rhythm", "Rith-um", "rhythm", "the rhythm map", "a rhythm clue", "a safe listening clue",
                   tags={"sound"}),
}

PLACES = {
    "candle": Place("candle", "the candle", "the candle", "the wick", flammable=True, spread=3, tags={"fire"}),
    "tinder": Place("tinder", "the tinder bundle", "the tinder bundle", "the dry twigs", flammable=True, spread=2, tags={"fire"}),
    "curtain": Place("curtain", "the curtain", "the curtain", "the bottom of the curtain", flammable=True, spread=3, tags={"fire"}),
}

SUBSTITUTES = {
    "lantern": Substitute("lantern", "lantern", "a little lantern", "glowed warm and safe", tags={"lantern"}),
    "flashlight": Substitute("flashlight", "flashlight", "a flashlight", "clicked bright as a star", tags={"flashlight"}),
    "glowsticks": Substitute("glowsticks", "glow sticks", "two glow sticks", "shone green in the dark", tags={"glowsticks"}),
}

RESPONSES = {
    "extinguisher": Response("extinguisher", 3, 4, "grabbed the fire extinguisher and sprayed the flames until every spark was gone",
                             "tried to use the fire extinguisher, but the flames were already too big",
                             "put the flames out with the fire extinguisher", tags={"fire"}),
    "smother": Response("smother", 3, 3, "pulled the {place} down, covered it with a heavy cloth, and smothered the flames",
                        "tried to smother the {place}, but the fire was climbing too fast",
                        "smothered the flames under a heavy cloth", tags={"fire"}),
    "stomp": Response("stomp", 2, 2, "pulled the {place} down and stamped the flames out, fast and hard",
                      "stamped at the flames, but they only leapt higher",
                      "stamped the flames out", tags={"fire"}),
    "bucket": Response("bucket", 1, 1, "threw a bucket of water over the {place}",
                       "threw a bucket of water over the {place}, but it was far too little",
                       "threw a bucket of water over the {place}", tags={"fire"}),
}

SENSE_MIN = 2


GIRL_NAMES = ["Mara", "Lily", "Nia", "Zoe", "Ava", "Ella", "Mia", "Nora"]
BOY_NAMES = ["Pip", "Tom", "Max", "Ben", "Leo", "Finn", "Sam", "Jack"]
TRAITS = ["careful", "cautious", "steady", "brave", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in CLUES:
            for pid, place in PLACES.items():
                if hazard_at_risk(CLUES[cid], place):
                    combos.append((sid, cid, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    clue: str
    place: str
    substitute1: str
    substitute2: str
    response: str
    seeker: str
    seeker_gender: str
    helper: str
    helper_gender: str
    parent: str
    helper_trait: str
    delay: int = 0
    seeker_age: int = 6
    helper_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "phoneme": [("What is a phoneme?",
                 "A phoneme is a tiny sound in a word. When you change one sound, the word can sound different.")],
    "sound": [("Why should you listen carefully to sounds?",
               "Listening carefully helps you hear the right clue and avoid a mix-up. A small sound can matter a lot.")],
    "fire": [("Why is fire dangerous?",
              "Fire is hot and can grow very fast. It can spread before people expect it.")],
    "lantern": [("What is a lantern?",
                 "A lantern is a light that helps you see in the dark. In stories, a safe lantern is better than a flame made by mistake.")],
    "flashlight": [("What is a flashlight?",
                    "A flashlight is a battery light you can turn on with a button. It gives light without a flame.")],
    "glowsticks": [("What are glow sticks?",
                    "Glow sticks are safe sticks that shine with a soft light when you snap them.")],
    "call_adult": [("What should you do if something catches fire?",
                    "Get away and call a grown-up right away. Calling for help is the safest choice.")],
}
KNOWLEDGE_ORDER = ["phoneme", "sound", "fire", "lantern", "flashlight", "glowsticks", "call_adult"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    s, h, clue, place, setting = f["seeker"], f["helper"], f["clue"], f["place_cfg"], f["setting"]
    if f["outcome"] == "averted":
        return [
            f'Write a pirate tale for a young child where {s.id} misunderstands a sound clue about "{clue.id}" and {h.id} helps fix the mix-up before anything happens.',
            f"Tell a gentle story with a misunderstanding about the word phoneme, where {s.id} hears it wrong and {h.id} slows them down.",
            f'Write a safe pirate story where the crew is tempted by a phoneme clue, but the older shipmate talks the younger one out of it and they use a safe light instead.',
        ]
    if f["outcome"] == "contained":
        return [
            f'Write a pirate tale for a young child where a misunderstanding about "{clue.id}" leads to a small fire, but a grown-up puts it out quickly.',
            f"Tell a story about a phoneme mix-up on a pirate ship, where {s.id} follows the wrong sound clue near {place.the} and everyone calls for help.",
            f'Write a child-friendly rescue story in pirate style that teaches "{clue.id} is not a toy" and ends with safe light.',
        ]
    return [
        f'Write a cautionary pirate tale for a young child where a misunderstanding about "{clue.id}" starts a fire that gets too big to stop.',
        f"Tell a pirate story where {s.id} ignores {h.id}'s warning and uses the phoneme clue near {place.the}, and the ship burns down but everyone escapes safely.",
        f'Write a sad-but-safe ending pirate story that teaches "{clue.id} is not a toy" after the crew loses the ship to fire.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    s, h, p, clue, place = f["seeker"], f["helper"], f["parent"], f["clue"], f["place_cfg"]
    qa = [
        ("Who is the story about?",
         f"It is about {s.id}, {h.id}, and their captain-parent who helped when the clue caused trouble."),
        ("What did {0} misunderstand?".format(s.id),
         f"{s.id} misunderstood the sound clue and thought {clue.label} meant a good way to explore. That mix-up led them toward the wrong kind of light."),
        ("Why did {0} warn {1}?".format(h.id, s.id),
         f"{h.id} warned {s.id} because {clue.label} could make a real flame near {place.the}. {p.label_word.capitalize()} had already taught them that it was not a toy."),
    ]
    if f["outcome"] == "averted":
        qa.append((
            f"What did {s.id} do after {h.id} warned {s.id}?",
            f"{s.id} stopped and listened to {h.id}. The mix-up ended before any fire started, so they chose a safe light instead."
        ))
        qa.append((
            "How did the story end?",
            f"It ended safely with no fire at all. The crew used {f['substitutes'][0].label} and {f['substitutes'][1].label} to explore the dark place."
        ))
    elif f["outcome"] == "contained":
        qa.append((
            f"What happened when {s.id} used the clue?",
            f"{place.The} caught fire, so everyone shouted for help. {p.label_word.capitalize()} put the flames out before they spread through the whole ship."
        ))
        qa.append((
            "How did the children feel at the end?",
            f"They felt scared at first, then relieved and loved. After the fire was out, they promised to use safe light and never to trust the clue alone."
        ))
    else:
        qa.append((
            "Could the grown-up stop the fire in time?",
            f"No. {p.label_word.capitalize()} tried, but the fire was already too big, so they had to run out and leave the ship behind."
        ))
        qa.append((
            "How did the story end?",
            f"Everyone escaped safely, but the ship was lost. The lesson was that a phoneme clue is not a toy and fire can grow faster than anyone can run."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["clue"].tags) | set(world.facts["place_cfg"].tags)
    if world.facts["outcome"] == "averted":
        tags |= set(world.facts["substitutes"][0].tags) | set(world.facts["substitutes"][1].tags)
    elif world.facts["outcome"] == "contained":
        tags |= set(world.facts["response"].tags)
    else:
        tags |= set(world.facts["response"].tags) | {"call_adult"}
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("harbor", "phoneme", "candle", "lantern", "flashlight", "extinguisher",
                "Pip", "boy", "Mara", "girl", "father", "careful", 0, 6, 4, "siblings"),
    StoryParams("island", "phoneme", "tinder", "flashlight", "glowsticks", "smother",
                "Lina", "girl", "Bo", "boy", "mother", "cautious", 0, 7, 5, "siblings"),
    StoryParams("cave", "phoneme", "curtain", "lantern", "glowsticks", "stomp",
                "Ned", "boy", "Ivy", "girl", "father", "steady", 1, 6, 4, "siblings"),
]


def explain_rejection(clue: Clue, place: Place) -> str:
    if not hazard_at_risk(clue, place):
        return f"(No story: this clue/place pair is not a real fire hazard.)"
    return "(No story: the requested combination is unreasonable.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.helper_age, params.seeker_age, params.helper_trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], PLACES[params.place], params.delay) else "burned"


ASP_RULES = r"""
hazard(C, P) :- clue(C), place(P), flammable(P).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

older_helper :- relation(siblings), helper_age(H), seeker_age(S), H > S.
averted :- older_helper, helper_trait(careful).
severity(V) :- place(P), spread(P, S), delay(D), V = S + D.
contained :- response(R), power(R, P), severity(V), P >= V.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(burned) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.flammable:
            lines.append(asp.fact("flammable", pid))
        lines.append(asp.fact("spread", pid, p.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show hazard/2."))
    return sorted(set(asp.atoms(model, "hazard")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("helper_age", params.helper_age),
        asp.fact("seeker_age", params.seeker_age),
        asp.fact("helper_trait", params.helper_trait),
        asp.fact("delay", params.delay),
        asp.fact("place", params.place),
        asp.fact("response", params.response),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        rc = 1
        print("MISMATCH in hazard gate:")
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    samples = [generate(p) for p in CURATED]
    try:
        samples.append(generate(resolve_params(build_parser().parse_args([]), random.Random(777))))
    except StoryError:
        pass
    if all(sample.story for sample in samples):
        print(f"OK: smoke test generated {len(samples)} stories.")
    else:
        rc = 1
        print("MISMATCH: story generation failed.")
    bad = sum(1 for p in CURATED if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print("OK: ASP outcome matches Python outcome on curated scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad} curated outcomes differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale storyworld with a phoneme misunderstanding.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.place and not hazard_at_risk(CLUES[args.clue], PLACES[args.place]):
        raise StoryError(explain_rejection(CLUES[args.clue], PLACES[args.place]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.clue is None or c[1] == args.clue)
              and (args.place is None or c[2] == args.place)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, clue, place = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    sub1, sub2 = rng.sample(sorted(SUBSTITUTES), 2)
    seeker_gender = rng.choice(["boy", "girl"])
    helper_gender = "girl" if seeker_gender == "boy" else "boy"
    seeker = rng.choice(BOY_NAMES if seeker_gender == "boy" else GIRL_NAMES)
    helper = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != seeker])
    parent = rng.choice(["father", "mother"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, clue, place, sub1, sub2, response, seeker, seeker_gender, helper, helper_gender, parent, trait, delay=rng.randint(0, 2),
                       seeker_age=rng.randint(4, 7), helper_age=rng.randint(4, 8), relation=rng.choice(["siblings", "friends"]))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting], CLUES[params.clue], PLACES[params.place],
        (SUBSTITUTES[params.substitute1], SUBSTITUTES[params.substitute2]),
        RESPONSES[params.response],
        params.seeker, params.seeker_gender, params.helper, params.helper_gender,
        params.parent, params.helper_trait, params.delay, params.seeker_age,
        params.helper_age, params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show hazard/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(r.id for r in sensible_responses())}")
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
            header = f"### {p.seeker} & {p.helper}: {p.clue} near {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
