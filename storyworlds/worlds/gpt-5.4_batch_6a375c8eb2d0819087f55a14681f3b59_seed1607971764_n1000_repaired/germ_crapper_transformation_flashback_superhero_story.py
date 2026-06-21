#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py
===================================================================================

A standalone storyworld for a tiny superhero tale about bathroom germs, a flashback,
and a child-sized transformation into a cleaner kind of hero.

Premise
-------
A child dashes out of the crapper in the middle of a pretend superhero mission.
Their hands carry real germs. A helper reminds them of an earlier germ disaster,
which triggers a flashback. The child must decide whether to use a real hand-wash
or a weak shortcut. In the happy branch, soap, water, and a towel-cape turn the
hero into a safer kind of superhero.

Run it
------
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py --mission cookies
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py --method quick_rinse
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py --qa --trace
    python storyworlds/worlds/gpt-5.4/germ_crapper_transformation_flashback_superhero_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Mission:
    id: str
    call: str
    object_label: str
    object_phrase: str
    place: str
    touch_verb: str
    ending_image: str
    object_type: str
    risk: str
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
class Flashback:
    id: str
    cue: str
    recall: str
    lesson: str
    consequence: str
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
class Soap:
    id: str
    label: str
    sparkle: str
    smell: str
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
class Costume:
    id: str
    label: str
    wear_text: str
    ending_pose: str
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
class Method:
    id: str
    sense: int
    power: int
    wash_text: str
    qa_text: str
    fail_text: str
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
        self.history: list[str] = []
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

    def note(self, item: str) -> None:
        self.history.append(item)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
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


def _r_germs_threaten(world: World) -> list[str]:
    out: list[str] = []
    hands = world.get("hands")
    mission_object = world.get("mission_object")
    hero = world.get("hero")
    if hands.meters["germs"] >= THRESHOLD and mission_object.meters["touched"] >= THRESHOLD:
        sig = ("contaminate", mission_object.id)
        if sig not in world.fired:
            world.fired.add(sig)
            mission_object.meters["germs"] += 1
            hero.memes["alarm"] += 1
            out.append("__contamination__")
    return out


def _r_wash_clears_germs(world: World) -> list[str]:
    out: list[str] = []
    hands = world.get("hands")
    hero = world.get("hero")
    if hands.meters["soap"] >= THRESHOLD and hands.meters["rinse"] >= THRESHOLD:
        sig = ("cleaned", hands.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hands.meters["germs"] = 0.0
            hands.meters["clean"] += 1
            hero.memes["relief"] += 1
            out.append("__clean__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    hands = world.get("hands")
    hero = world.get("hero")
    costume = world.get("costume")
    if hands.meters["clean"] >= THRESHOLD and costume.meters["worn"] >= THRESHOLD:
        sig = ("transform", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["heroic"] += 1
            hero.memes["pride"] += 1
            hero.attrs["title"] = "Captain Clean"
            out.append("__transform__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="germs_threaten", tag="physical", apply=_r_germs_threaten),
    Rule(name="wash_clears_germs", tag="physical", apply=_r_wash_clears_germs),
    Rule(name="transform", tag="social", apply=_r_transform),
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
    return produced if narrate else produced


MISSIONS = {
    "cookies": Mission(
        id="cookies",
        call="The Cookie Tower was in danger.",
        object_label="cookie tray",
        object_phrase="a tray of star cookies for the family",
        place="the kitchen table",
        touch_verb="grab the cookie tray and carry it to safety",
        ending_image="The cookies stayed neat on the bright plate, ready for everyone.",
        object_type="food",
        risk="food",
        tags={"cookies", "food", "kitchen"},
    ),
    "blocks": Mission(
        id="blocks",
        call="The Block Bridge was wobbling.",
        object_label="block bridge",
        object_phrase="a tall block bridge for the baby",
        place="the rug by the sofa",
        touch_verb="steady the block bridge before it toppled",
        ending_image="The bridge stood tall, and the baby clapped at the safe rescue.",
        object_type="toy",
        risk="baby",
        tags={"blocks", "toy", "baby"},
    ),
    "books": Mission(
        id="books",
        call="The Library Fort needed a guard.",
        object_label="library books",
        object_phrase="a stack of picture books from the library",
        place="the reading fort under the blanket",
        touch_verb="stack the books into their hero fort",
        ending_image="The books rested in a neat fort, with clean corners and smooth pages.",
        object_type="book",
        risk="shared",
        tags={"books", "library", "reading"},
    ),
}

FLASHBACKS = {
    "tummy_ache": Flashback(
        id="tummy_ache",
        cue="last week's long couch day",
        recall="Last week, after a rushed bathroom break and a snack with unwashed hands, the hero had a sore tummy and missed all the backyard fun.",
        lesson="Germs are tiny, but they can make a big day feel small.",
        consequence="That memory made the danger feel real again.",
        tags={"germ", "tummy"},
    ),
    "sticky_controller": Flashback(
        id="sticky_controller",
        cue="the game-pad cleanup",
        recall="A few days ago, grubby hands left smudges all over the game controller, and everyone had to stop play while it was wiped and dried.",
        lesson="Even pretend speed is not worth making shared things grimy.",
        consequence="The hero remembered the disappointed faces around the couch.",
        tags={"germ", "shared"},
    ),
    "baby_sneeze": Flashback(
        id="baby_sneeze",
        cue="the nursery reminder",
        recall="Not long ago, the baby had sneezed after touching a toy someone had handled with dirty hands, and the whole family spent the evening washing toys instead of playing.",
        lesson="Little hands and little germs travel fast together.",
        consequence="The memory made the hero slow down.",
        tags={"germ", "baby"},
    ),
}

SOAPS = {
    "bubble": Soap(
        id="bubble",
        label="bubble soap",
        sparkle="silver bubbles climbed up the wrists like tiny moon balloons",
        smell="smelled like clean pears",
        tags={"soap", "sink"},
    ),
    "foamy": Soap(
        id="foamy",
        label="foamy soap",
        sparkle="soft white foam puffed up like superhero clouds",
        smell="smelled bright and fresh",
        tags={"soap", "sink"},
    ),
    "lemon": Soap(
        id="lemon",
        label="lemon soap",
        sparkle="sunny suds slid between every finger",
        smell="smelled lemony and brave",
        tags={"soap", "sink"},
    ),
}

COSTUMES = {
    "towel_cape": Costume(
        id="towel_cape",
        label="towel cape",
        wear_text="snapped a little towel around the shoulders like a fluttering cape",
        ending_pose="The towel cape shone in the light from the sink.",
        tags={"cape", "superhero"},
    ),
    "washcloth_cuffs": Costume(
        id="washcloth_cuffs",
        label="washcloth cuffs",
        wear_text="slid two washcloths over the wrists like mighty hero cuffs",
        ending_pose="The washcloth cuffs looked ready for another clean rescue.",
        tags={"costume", "superhero"},
    ),
    "colander_helmet": Costume(
        id="colander_helmet",
        label="colander helmet",
        wear_text="balanced a shiny colander on the head like a starry helmet",
        ending_pose="The colander helmet glittered with tiny kitchen stars.",
        tags={"helmet", "superhero"},
    ),
}

METHODS = {
    "soap_and_water": Method(
        id="soap_and_water",
        sense=3,
        power=3,
        wash_text="pumped soap, scrubbed between every finger, counted slowly to twenty, and rinsed until the water carried the suds away",
        qa_text="washed carefully with soap and water",
        fail_text="would have needed soap and water, not a rushed shortcut",
        tags={"soap", "handwashing"},
    ),
    "quick_rinse": Method(
        id="quick_rinse",
        sense=1,
        power=1,
        wash_text="splashed the fingertips for one second and shook them dry",
        qa_text="gave a quick rinse",
        fail_text="only splashed the fingertips, leaving bathroom germs behind",
        tags={"water", "shortcut"},
    ),
    "sanitizer": Method(
        id="sanitizer",
        sense=1,
        power=1,
        wash_text="rubbed a little sanitizer on the palms and dashed off",
        qa_text="used sanitizer only",
        fail_text="used sanitizer alone after the crapper, which was not the right clean-up for that job",
        tags={"shortcut", "sanitizer"},
    ),
}

GIRL_NAMES = ["Luna", "Ava", "Mia", "Zoe", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Leo", "Max", "Ben", "Finn", "Theo", "Eli", "Sam", "Noah"]
HELPERS = [
    ("Maya", "girl"),
    ("Tess", "girl"),
    ("Owen", "boy"),
    ("Jack", "boy"),
]
TRAITS = ["swift", "bold", "bouncy", "earnest", "dramatic", "kind"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission_id in MISSIONS:
        for flashback_id in FLASHBACKS:
            for soap_id in SOAPS:
                for costume_id in COSTUMES:
                    combos.append((mission_id, flashback_id, soap_id, costume_id))
    return combos


def method_is_reasonable(method: Method) -> bool:
    return method.sense >= SENSE_MIN and method.power >= 2


@dataclass
class StoryParams:
    mission: str
    flashback: str
    soap: str
    costume: str
    method: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    trait: str
    helper_relation: str = "sibling"
    memory_strength: int = 2
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


def predict_contamination(world: World, method_id: str) -> dict:
    sim = world.copy()
    hands = sim.get("hands")
    mission_object = sim.get("mission_object")
    if method_id == "soap_and_water":
        hands.meters["soap"] += 1
        hands.meters["rinse"] += 1
        propagate(sim, narrate=False)
    elif method_id == "quick_rinse":
        hands.meters["rinse"] += 0.5
    elif method_id == "sanitizer":
        hands.meters["sanitizer"] += 1
    mission_object.meters["touched"] += 1
    propagate(sim, narrate=False)
    return {
        "hands_clean": sim.get("hands").meters["germs"] < THRESHOLD,
        "contaminated": sim.get("mission_object").meters["germs"] >= THRESHOLD,
    }


def explain_method_rejection(method_id: str) -> str:
    method = METHODS[method_id]
    return (
        f"(No story: '{method_id}' is not a sensible bathroom clean-up after the crapper. "
        f"It {method.fail_text}. Choose soap_and_water for a reasonable superhero rescue.)"
    )


def _pick_name(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    if gender == "girl":
        return rng.choice(GIRL_NAMES), gender
    return rng.choice(BOY_NAMES), gender


def introduce(world: World, mission: Mission) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(
        f"{hero.id} was a little {hero.attrs['style_name']} who believed every room in the house held a secret city."
    )
    world.say(
        f"That afternoon, {mission.place} had become Hero Headquarters, and {helper.id} was the lookout."
    )


def bathroom_exit(world: World, mission: Mission) -> None:
    hero = world.get("hero")
    hands = world.get("hands")
    hero.memes["urgency"] += 1
    hands.meters["germs"] += 2
    world.note("bathroom_exit")
    world.say(
        f"Then came the emergency. {mission.call} {hero.id} blasted out of the crapper so fast that {hero.pronoun()} almost forgot the sink."
    )
    world.say(
        f'"Quick! I have to {mission.touch_verb}!" {hero.id} cried.'
    )


def helper_warns(world: World, mission: Mission, parent: Entity) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    pred = predict_contamination(world, "quick_rinse")
    world.facts["predicted_contaminated"] = pred["contaminated"]
    helper.memes["concern"] += 1
    world.note("warning")
    world.say(
        f'{helper.id} held out a hand. "Heroes still wash first," {helper.pronoun()} said. '
        f'"There could be a germ from the crapper on your hands, and it could reach the {mission.object_label}."'
    )
    if pred["contaminated"]:
        world.say(
            f'{parent.label_word.capitalize()} looked over from the doorway and nodded. "A real hero protects people before prizes," {parent.pronoun()} said.'
        )


def flashback(world: World, flash: Flashback) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["memory"] += world.facts["memory_strength"]
    world.note("flashback")
    world.say(
        f"At those words, {hero.id} stopped. In a quick flashback, {hero.pronoun()} remembered {flash.cue}: {flash.recall}"
    )
    world.say(
        f"{flash.lesson} {flash.consequence}"
    )
    if helper.memes["concern"] >= THRESHOLD:
        world.say(
            f"{helper.id}'s serious face made the memory feel even closer."
        )


def decide_to_wash(world: World, method: Method, soap: Soap, costume: Costume) -> None:
    hero = world.get("hero")
    hands = world.get("hands")
    costume_ent = world.get("costume")
    hero.memes["decision"] += 1
    world.note("wash")
    world.say(
        f"{hero.id} spun back to the sink, grabbed the {soap.label}, and {method.wash_text}. {soap.sparkle}, and the air {soap.smell}."
    )
    if method.id == "soap_and_water":
        hands.meters["soap"] += 1
        hands.meters["rinse"] += 1
        propagate(world, narrate=False)
    costume_ent.meters["worn"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {hero.pronoun()} {costume.wear_text}."
    )
    if hero.attrs.get("title") == "Captain Clean":
        world.note("transformation")
        world.say(
            f"In that moment, {hero.id} did not feel like a rushed blur anymore. {hero.pronoun().capitalize()} had transformed into Captain Clean, the hand-washing hero of the house."
        )


def rescue_clean(world: World, mission: Mission) -> None:
    hero = world.get("hero")
    mission_object = world.get("mission_object")
    mission_object.meters["touched"] += 1
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.note("clean_rescue")
    world.say(
        f"Now {hero.id} hurried back and {mission.touch_verb}. This time the rescue was safe as well as fast."
    )
    world.say(
        f"{mission.ending_image} {world.get('costume').attrs['ending_pose']}"
    )


def rescue_dirty(world: World, mission: Mission, method: Method) -> None:
    hero = world.get("hero")
    mission_object = world.get("mission_object")
    mission_object.meters["touched"] += 1
    propagate(world, narrate=False)
    hero.memes["shame"] += 1
    world.note("dirty_rescue")
    world.say(
        f"{hero.id} chose speed instead, {method.wash_text}, and dashed to {mission.touch_verb}."
    )
    if mission_object.meters["germs"] >= THRESHOLD:
        world.say(
            f"But the win did not feel bright. The mission was touched by a germ risk, and everyone had to stop and clean up before the game could go on."
        )
    world.say(
        f"{hero.id} looked at {hero.pronoun('possessive')} hands and wished {hero.pronoun()} had been a wiser hero."
        )


def ending_lesson(world: World, mission: Mission) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    parent = world.get("parent")
    outcome = world.facts["outcome"]
    if outcome == "clean":
        world.say(
            f'"That is real superhero work," {parent.label_word} said. {helper.id} grinned, and {hero.id} grinned back.'
        )
        world.say(
            f"After that, whenever an alarm rang in Hero Headquarters, {hero.id} checked the sink before the skyline."
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} brought soap and a clean towel. "{mission.object_label.capitalize()} can wait," {parent.pronoun()} said. "People come first, and clean hands help keep them safe."'
        )
        world.say(
            f"After that, {hero.id} still loved pretending, but the first step of every mission was a real wash at the sink."
        )


def tell(
    mission: Mission,
    flashback_cfg: Flashback,
    soap: Soap,
    costume: Costume,
    method: Method,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: str,
    trait: str,
    helper_relation: str,
    memory_strength: int,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"style_name": trait, "title": "Comet Kid"},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            label=helper_name,
            role="helper",
            attrs={"relation": helper_relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    hands = world.add(
        Entity(
            id="hands",
            type="hands",
            label="hands",
            role="hands",
            attrs={"owner": hero_name},
        )
    )
    mission_object = world.add(
        Entity(
            id="mission_object",
            type=mission.object_type,
            label=mission.object_label,
            role="mission_object",
            attrs={"risk": mission.risk},
            tags=set(mission.tags),
        )
    )
    costume_ent = world.add(
        Entity(
            id="costume",
            type="costume",
            label=costume.label,
            role="costume",
            attrs={"ending_pose": costume.ending_pose},
            tags=set(costume.tags),
        )
    )

    world.facts["memory_strength"] = memory_strength
    world.facts["method"] = method
    world.facts["mission"] = mission
    world.facts["flashback"] = flashback_cfg
    world.facts["soap"] = soap
    world.facts["costume_cfg"] = costume

    introduce(world, mission)
    bathroom_exit(world, mission)

    world.para()
    helper_warns(world, mission, parent)
    flashback(world, flashback_cfg)

    world.para()
    if method_is_reasonable(method):
        decide_to_wash(world, method, soap, costume)
        rescue_clean(world, mission)
        outcome = "clean"
    else:
        rescue_dirty(world, mission, method)
        outcome = "dirty"

    world.para()
    ending_lesson(world, mission)
    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        hands=hands,
        mission_object=mission_object,
        outcome=outcome,
        transformed=hero.attrs.get("title") == "Captain Clean",
        contaminated=mission_object.meters["germs"] >= THRESHOLD,
        washed=hands.meters["clean"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "germ": [
        (
            "What is a germ?",
            "A germ is a tiny living thing so small you cannot see it without special tools. Some germs can make people sick, so clean hands help stop them from spreading.",
        )
    ],
    "crapper": [
        (
            "What does crapper mean?",
            "Crapper is a silly word for the toilet or bathroom. It is not a fancy word, but children sometimes say it when joking around.",
        )
    ],
    "soap": [
        (
            "Why do people use soap when they wash their hands?",
            "Soap helps loosen dirt and germs from your skin so water can rinse them away. That is why soap and water clean better than a quick splash.",
        )
    ],
    "handwashing": [
        (
            "Why is washing after the bathroom important?",
            "After the bathroom, germs can stay on your hands even if they look clean. Washing with soap and water helps keep those germs off food, toys, and other people.",
        )
    ],
    "superhero": [
        (
            "Can a superhero story teach a real safety rule?",
            "Yes. Pretend stories can still show real choices, like being brave enough to stop and wash your hands before helping someone.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick look at something that happened earlier. It helps explain why a character makes a choice now.",
        )
    ],
    "cookies": [
        (
            "Why should clean hands touch food?",
            "Food goes into your mouth, so dirty hands can carry germs onto it. Clean hands help keep snacks safer to eat.",
        )
    ],
    "blocks": [
        (
            "Why should toys for a baby be kept clean?",
            "Babies touch toys and often put their hands near their mouths. Clean toys and clean hands help protect them from germs.",
        )
    ],
    "books": [
        (
            "Why is it nice to keep library books clean?",
            "Library books are shared by many families. Clean hands help keep the pages nice and safer for the next reader.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    mission = world.facts["mission"]
    flashback_cfg = world.facts["flashback"]
    outcome = world.facts["outcome"]
    if outcome == "clean":
        return [
            f'Write a superhero story for a 3-to-5-year-old that includes the words "germ" and "crapper", uses a flashback, and ends with a transformation into a cleaner hero.',
            f"Tell a child-friendly superhero story where {hero.id} rushes out of the crapper to save the {mission.object_label}, remembers {flashback_cfg.cue} in a flashback, and chooses soap and water first.",
            f"Write a simple story with a fast beginning, a flashback in the middle, and an ending where the hero changes from a rushed rescuer into a wiser superhero.",
        ]
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "germ" and "crapper" and uses a flashback to warn the hero after a rushed choice.',
        f"Tell a gentle cautionary story where {hero.id} tries a weak shortcut after the crapper and learns that even superheroes have to wash properly.",
        f"Write a story where a flashback reminds a child hero that clean hands matter more than speed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    parent = world.facts["parent"]
    mission = world.facts["mission"]
    flashback_cfg = world.facts["flashback"]
    method = world.facts["method"]
    costume = world.facts["costume_cfg"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child pretending to be a superhero, with {helper.id} helping and {parent.label_word} nearby. The story follows one fast bathroom-to-rescue moment that turns into a lesson.",
        ),
        (
            "What problem started the story?",
            f"{hero.id} rushed out of the crapper because {mission.call.lower()} {hero.pronoun().capitalize()} wanted to {mission.touch_verb} right away. The problem was that bathroom germs could still be on {hero.pronoun('possessive')} hands.",
        ),
        (
            f"Why did {helper.id} stop {hero.id}?",
            f"{helper.id} warned that a germ from the crapper could reach the {mission.object_label}. That warning mattered because the mission needed touching something other people would use or enjoy.",
        ),
        (
            "What happened in the flashback?",
            f"The flashback showed {flashback_cfg.recall} It helped {hero.id} remember why clean hands matter before a rescue.",
        ),
    ]
    if outcome == "clean":
        qa.append(
            (
                f"How did {hero.id} solve the problem?",
                f"{hero.id} {method.qa_text} before touching the {mission.object_label}. That choice removed the danger first, so the rescue could stay safe and heroic.",
            )
        )
        qa.append(
            (
                "What was the transformation in the story?",
                f"After washing well and putting on the {costume.label}, {hero.id} transformed from a rushed blur into Captain Clean. The change was not magic only on the outside; it showed a wiser way of being a hero.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a safe rescue and a new habit. {hero.id} learned to check the sink before the skyline, which proves the hero changed inside as well as in costume.",
            )
        )
    else:
        qa.append(
            (
                f"Why was {method.id} not enough?",
                f"{method.id} was not enough because it was only a shortcut after the crapper. The mission had to pause for cleanup, which showed that speed without proper washing can spread risk.",
            )
        )
        qa.append(
            (
                "How did the ending show a change?",
                f"The rescue did not feel proud, and then {parent.label_word} brought soap and a towel. After that, {hero.id} made real hand-washing the first step of every mission.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mission = world.facts["mission"]
    tags = {"germ", "crapper", "soap", "handwashing", "superhero", "flashback"}
    tags |= set(mission.tags)
    out: list[tuple[str, str]] = []
    order = ["germ", "crapper", "soap", "handwashing", "flashback", "superhero", "cookies", "blocks", "books"]
    for tag in order:
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:14} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    if world.history:
        lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        mission="cookies",
        flashback="tummy_ache",
        soap="bubble",
        costume="towel_cape",
        method="soap_and_water",
        hero_name="Luna",
        hero_gender="girl",
        helper_name="Owen",
        helper_gender="boy",
        parent="mother",
        trait="swift",
        helper_relation="friend",
        memory_strength=3,
    ),
    StoryParams(
        mission="blocks",
        flashback="baby_sneeze",
        soap="foamy",
        costume="washcloth_cuffs",
        method="soap_and_water",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="father",
        trait="bold",
        helper_relation="sibling",
        memory_strength=3,
    ),
    StoryParams(
        mission="books",
        flashback="sticky_controller",
        soap="lemon",
        costume="colander_helmet",
        method="soap_and_water",
        hero_name="Nora",
        hero_gender="girl",
        helper_name="Jack",
        helper_gender="boy",
        parent="mother",
        trait="earnest",
        helper_relation="friend",
        memory_strength=2,
    ),
    StoryParams(
        mission="cookies",
        flashback="tummy_ache",
        soap="bubble",
        costume="towel_cape",
        method="quick_rinse",
        hero_name="Max",
        hero_gender="boy",
        helper_name="Tess",
        helper_gender="girl",
        parent="father",
        trait="dramatic",
        helper_relation="sibling",
        memory_strength=1,
    ),
]


ASP_RULES = r"""
valid(M,F,S,C) :- mission(M), flashback(F), soap(S), costume(C).

reasonable_method(soap_and_water) :- method(soap_and_water), sense(soap_and_water, S), sense_min(M), S >= M.
unreasonable_method(Mt) :- method(Mt), not reasonable_method(Mt).

outcome(clean) :- chosen_method(Mt), reasonable_method(Mt).
outcome(dirty) :- chosen_method(Mt), unreasonable_method(Mt).

#show valid/4.
#show reasonable_method/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mission_id in MISSIONS:
        lines.append(asp.fact("mission", mission_id))
    for flashback_id in FLASHBACKS:
        lines.append(asp.fact("flashback", flashback_id))
    for soap_id in SOAPS:
        lines.append(asp.fact("soap", soap_id))
    for costume_id in COSTUMES:
        lines.append(asp.fact("costume", costume_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_reasonable_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(m for (m,) in asp.atoms(model, "reasonable_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_method", params.method)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "clean" if method_is_reasonable(METHODS[params.method]) else "dirty"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero rushes from the crapper, remembers a germ lesson, and learns what real hero work looks like."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--soap", choices=SOAPS)
    ap.add_argument("--costume", choices=COSTUMES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method is not None and not method_is_reasonable(METHODS[args.method]):
        raise StoryError(explain_method_rejection(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.flashback is None or combo[1] == args.flashback)
        and (args.soap is None or combo[2] == args.soap)
        and (args.costume is None or combo[3] == args.costume)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, flashback_id, soap_id, costume_id = rng.choice(sorted(combos))
    method_id = args.method or "soap_and_water"
    hero_name, hero_gender = _pick_name(rng)
    helper_name, helper_gender = rng.choice(HELPERS)
    if helper_name == hero_name:
        helper_name, helper_gender = rng.choice([x for x in HELPERS if x[0] != hero_name])
    if args.hero_name:
        hero_name = args.hero_name
    if args.helper_name:
        helper_name = args.helper_name
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    helper_relation = rng.choice(["sibling", "friend"])
    memory_strength = rng.randint(2, 3)
    return StoryParams(
        mission=mission_id,
        flashback=flashback_id,
        soap=soap_id,
        costume=costume_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        trait=trait,
        helper_relation=helper_relation,
        memory_strength=memory_strength,
    )


def generate(params: StoryParams) -> StorySample:
    for key, table in [
        (params.mission, MISSIONS),
        (params.flashback, FLASHBACKS),
        (params.soap, SOAPS),
        (params.costume, COSTUMES),
        (params.method, METHODS),
    ]:
        if key not in table:
            raise StoryError(f"(No story: unknown option '{key}'.)")
    mission = MISSIONS[params.mission]
    flashback_cfg = FLASHBACKS[params.flashback]
    soap = SOAPS[params.soap]
    costume = COSTUMES[params.costume]
    method = METHODS[params.method]

    world = tell(
        mission=mission,
        flashback_cfg=flashback_cfg,
        soap=soap,
        costume=costume,
        method=method,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        helper_relation=params.helper_relation,
        memory_strength=params.memory_strength,
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    python_methods = sorted(mid for mid, method in METHODS.items() if method_is_reasonable(method))
    clingo_methods = asp_reasonable_methods()
    if python_methods == clingo_methods:
        print(f"OK: reasonable methods match ({clingo_methods}).")
    else:
        rc = 1
        print(f"MISMATCH in reasonable methods: python={python_methods} clingo={clingo_methods}")

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"reasonable methods: {', '.join(asp_reasonable_methods())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, flashback, soap, costume) combos:\n")
        for mission_id, flashback_id, soap_id, costume_id in combos:
            print(f"  {mission_id:8} {flashback_id:17} {soap_id:7} {costume_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.mission}, {p.flashback}, {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
