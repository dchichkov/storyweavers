#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py
=========================================================================

A standalone story world about a warm flask, a gate, and a very funny
misunderstanding. The child hears an adult's instruction the wrong way, tries
to help in a silly way, and then a reversal reveals what the flask was really
for. The stories stay small, concrete, and child-facing, with a clear beginning,
a mistaken middle, and an ending image that proves the child learned something.

Run it
------
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --setting community_garden --misreading oil
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --setting town_library --misreading oil
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --all
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --json
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --asp
    python storyworlds/worlds/gpt-5.4/flask_reversal_gate_misunderstanding_comedy.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian", "gardener", "farmer"}
        male = {"boy", "father", "man", "groundskeeper", "coach"}
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
class Setting:
    id: str
    place: str
    gate_name: str
    gate_kind: str
    opens: str
    squeaky: bool
    staffed: bool
    recipient_name: str
    recipient_type: str
    recipient_role: str
    intro: str
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
class FlaskFill:
    id: str
    label: str
    steam: str
    sip_line: str
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
class Misreading:
    id: str
    thought: str
    whisper: str
    act_line: str
    risky: bool
    needs_squeak: bool = False
    needs_staff: bool = False
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
        self.facts: dict = {
            "clarified": False,
            "outcome": "",
            "reversal": "",
            "spill": False,
            "sign_helped": False,
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


def _r_wrong_push(world: World) -> list[str]:
    gate = world.get("gate")
    hero = world.get("hero")
    if gate.attrs["opens"] != "pull":
        return []
    if gate.meters["pushed"] < THRESHOLD:
        return []
    sig = ("wrong_push",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confusion"] += 1
    return ["__wrong_push__"]


def _r_tilt_spill(world: World) -> list[str]:
    flask = world.get("flask")
    gate = world.get("gate")
    hero = world.get("hero")
    helper = world.get("helper")
    if flask.meters["tilted"] < THRESHOLD or flask.meters["full"] < THRESHOLD:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    flask.meters["full"] = 0.0
    flask.meters["spilled"] += 1
    gate.meters["sticky"] += 1
    hero.memes["embarrassment"] += 1
    helper.memes["surprise"] += 1
    return ["__spill__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wrong_push", tag="physical", apply=_r_wrong_push),
    Rule(name="tilt_spill", tag="physical", apply=_r_tilt_spill),
]


def propagate(world: World, narrate: bool = False) -> list[str]:
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


SETTINGS = {
    "community_garden": Setting(
        id="community_garden",
        place="the community garden",
        gate_name="green gate",
        gate_kind="hinged gate",
        opens="pull",
        squeaky=True,
        staffed=True,
        recipient_name="Mrs. Pru",
        recipient_type="gardener",
        recipient_role="gardener",
        intro="Rows of carrots stood like tiny soldiers, and the seed beds waited behind the green gate.",
        tags={"garden", "gate", "plants"},
    ),
    "duck_pond": Setting(
        id="duck_pond",
        place="the duck pond",
        gate_name="painted pond gate",
        gate_kind="swing gate",
        opens="pull",
        squeaky=False,
        staffed=True,
        recipient_name="Mr. Bell",
        recipient_type="groundskeeper",
        recipient_role="groundskeeper",
        intro="The ducks were already making bossy little quacks behind the painted pond gate.",
        tags={"pond", "gate", "ducks"},
    ),
    "town_library": Setting(
        id="town_library",
        place="the library garden",
        gate_name="iron reading gate",
        gate_kind="sliding gate",
        opens="slide",
        squeaky=False,
        staffed=True,
        recipient_name="Ms. Hale",
        recipient_type="librarian",
        recipient_role="librarian",
        intro="A tiny story garden sat behind the iron reading gate, with bright cushions under a tree.",
        tags={"library", "gate", "books"},
    ),
    "petting_farm": Setting(
        id="petting_farm",
        place="the petting farm",
        gate_name="red farm gate",
        gate_kind="hinged gate",
        opens="pull",
        squeaky=True,
        staffed=True,
        recipient_name="Farmer June",
        recipient_type="farmer",
        recipient_role="farmer",
        intro="Beyond the red farm gate, two goats were standing on a barrel as if they owned the whole place.",
        tags={"farm", "gate", "animals"},
    ),
}

FILLS = {
    "cocoa": FlaskFill(
        id="cocoa",
        label="hot cocoa",
        steam="little curls of chocolate steam",
        sip_line="The cocoa smelled sweet and warm.",
        smell="chocolate",
        tags={"flask", "cocoa"},
    ),
    "tea": FlaskFill(
        id="tea",
        label="warm mint tea",
        steam="thin minty steam",
        sip_line="The tea smelled fresh and gentle.",
        smell="mint",
        tags={"flask", "tea"},
    ),
    "soup": FlaskFill(
        id="soup",
        label="tomato soup",
        steam="fat red steam that fogged the lid",
        sip_line="The soup smelled cozy and a little bit like lunch.",
        smell="tomato",
        tags={"flask", "soup"},
    ),
}

MISREADINGS = {
    "key": Misreading(
        id="key",
        thought="thought the flask must be the special thing that made the gate open",
        whisper='So the flask is the gate key?',
        act_line="held the flask near the latch as if the gate might sniff it and unlock itself",
        risky=True,
        needs_squeak=False,
        needs_staff=False,
        tags={"misunderstanding", "reversal"},
    ),
    "oil": Misreading(
        id="oil",
        thought="decided the drink inside must be medicine for a grumpy squeaky gate",
        whisper='Oh! The gate needs a sip from the flask.',
        act_line="carefully tipped the flask toward the hinge, trying to feed the squeak away",
        risky=True,
        needs_squeak=True,
        needs_staff=False,
        tags={"misunderstanding", "reversal"},
    ),
    "trade": Misreading(
        id="trade",
        thought="decided the gate would only let nice children through after it had been politely offered the flask",
        whisper='Maybe we have to show the flask some manners first.',
        act_line="stood very straight and offered the flask to the gate with a small, serious bow",
        risky=False,
        needs_squeak=False,
        needs_staff=True,
        tags={"misunderstanding", "reversal"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "curious", "cheerful", "thoughtful", "sensible"]


def valid_combo(setting: Setting, misreading: Misreading) -> bool:
    if misreading.needs_squeak and not setting.squeaky:
        return False
    if misreading.needs_staff and not setting.staffed:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for fill_id in FILLS:
            for misreading_id, misreading in MISREADINGS.items():
                if valid_combo(setting, misreading):
                    combos.append((setting_id, fill_id, misreading_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    fill: str
    misreading: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    helper_trait: str
    relation: str = "siblings"
    hero_age: int = 5
    helper_age: int = 6
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


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_correct_early(relation: str, hero_age: int, helper_age: int, helper_trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > hero_age
    authority = initial_caution(helper_trait) + 1.0 + (4.0 if helper_older else 0.0)
    return authority > BRAVERY_INIT


def outcome_of(params: StoryParams) -> str:
    if would_correct_early(params.relation, params.hero_age, params.helper_age, params.helper_trait):
        return "clean"
    misreading = MISREADINGS[params.misreading]
    return "spill" if misreading.risky else "clean"


def explain_rejection(setting: Setting, misreading: Misreading) -> str:
    if misreading.needs_squeak and not setting.squeaky:
        return (
            f"(No story: the {setting.gate_name} at {setting.place} is not squeaky, "
            f"so the '{misreading.id}' misunderstanding has no honest trigger. "
            f"Pick a squeaky gate like the one at the community garden or petting farm.)"
        )
    if misreading.needs_staff and not setting.staffed:
        return (
            f"(No story: the '{misreading.id}' misunderstanding needs someone waiting at the gate, "
            f"but {setting.place} has no gate helper in this world.)"
        )
    return "(No story: that setting and misunderstanding do not fit together.)"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


@dataclass
class Plan:
    early_fix: bool
    spill: bool
    wrong_push: bool
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


def plan_for(setting: Setting, misreading: Misreading, params: StoryParams) -> Plan:
    early_fix = would_correct_early(
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
        helper_trait=params.helper_trait,
    )
    spill = misreading.risky and not early_fix
    wrong_push = setting.opens == "pull" and misreading.id == "key" and not early_fix
    return Plan(early_fix=early_fix, spill=spill, wrong_push=wrong_push)


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity, setting: Setting, fill: FlaskFill) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a chilly morning, {hero.id} and {helper.id} walked with {hero.pronoun('possessive')} "
        f"{parent.label_word} toward {setting.place}. {setting.intro}"
    )
    world.say(
        f"In {parent.label_word.capitalize()}'s hand was a shiny flask with {fill.steam}. "
        f"{fill.sip_line}"
    )


def hand_off(world: World, hero: Entity, helper: Entity, parent: Entity, recipient: Entity, fill: FlaskFill, setting: Setting) -> None:
    world.say(
        f'"Please carry this flask to {recipient.id} at the gate," {parent.label_word} said. '
        f'"{recipient.pronoun().capitalize()} has been outside all morning."'
    )
    hero.memes["responsibility"] += 1
    helper.memes["responsibility"] += 1
    world.say(
        f"{hero.id} took the flask with both hands. It felt important, and that was exactly when the misunderstanding began."
    )


def mishear(world: World, hero: Entity, helper: Entity, misreading: Misreading) -> None:
    hero.memes["confusion"] += 1
    world.say(
        f"{hero.id} {misreading.thought}. "
        f'{hero.pronoun().capitalize()} whispered, "{misreading.whisper}"'
    )
    if helper.memes["caution"] >= 6:
        world.say(
            f"{helper.id} blinked at the flask, not quite sure that was right."
        )
    else:
        world.say(
            f"{helper.id} looked at the gate, then at the flask, and looked almost as puzzled."
        )


def helper_corrects(world: World, hero: Entity, helper: Entity, recipient: Entity, setting: Setting, misreading: Misreading) -> None:
    hero.memes["confusion"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["confidence"] += 1
    world.say(
        f'"Wait," said {helper.id}. "{recipient.id} is at the gate. The flask is for {recipient.pronoun("object")}, '
        f'not for the {setting.gate_name}."'
    )
    world.say(
        f"{hero.id} stopped in the middle of a very serious plan and stared at the flask. "
        f'Then {hero.pronoun()} gave a small gasp. "Ohhh. I gave the gate a whole job in my head."'
    )


def action_attempt(world: World, hero: Entity, helper: Entity, gate: Entity, flask: Entity, misreading: Misreading, setting: Setting) -> None:
    world.say(
        f"So {hero.id} marched up to the {setting.gate_name} and {misreading.act_line}."
    )
    if misreading.id == "key":
        gate.meters["pushed"] += 1
        propagate(world, narrate=False)
        if hero.memes["confusion"] >= THRESHOLD:
            world.say(
                f"{hero.pronoun().capitalize()} gave the gate a mighty push. The gate did not move at all, "
                f"which only made the flask seem even more mysterious."
            )
    elif misreading.id == "oil":
        flask.meters["tilted"] += 1
        propagate(world, narrate=False)
        if flask.meters["spilled"] >= THRESHOLD:
            world.say(
                f"A warm splash slid down the hinge and made the metal smell very much like {flask.attrs['smell']}. "
                f"The gate looked no happier, but much more like lunch."
            )
    elif misreading.id == "trade":
        world.say(
            f"The gate stayed exactly as gate-like as before."
        )
    if helper.memes["surprise"] >= THRESHOLD:
        world.say(f'"{hero.id}!" {helper.id} squeaked, a beat too late.')


def reversal(world: World, hero: Entity, helper: Entity, recipient: Entity, gate: Entity, flask: Entity, setting: Setting, fill: FlaskFill) -> None:
    hero.memes["amusement"] += 1
    helper.memes["amusement"] += 1
    recipient.memes["amusement"] += 1
    world.say(
        f"Just then, {recipient.id} appeared on the other side. "
        f"{recipient.pronoun().capitalize()} reached out, "
        f"{'pulled' if setting.opens == 'pull' else 'slid'} the {setting.gate_name} open in one easy motion, "
        f"and the whole mystery fell apart at once."
    )
    world.facts["reversal"] = (
        f"{recipient.id} simply {'pulled' if setting.opens == 'pull' else 'slid'} the gate open"
    )
    if flask.meters["spilled"] >= THRESHOLD:
        world.say(
            f'"Oh dear," {recipient.pronoun()} said, smiling instead of scolding. '
            f'"The flask was for me to drink, not for the gate to wear."'
        )
        world.say(
            f"{hero.id} looked at the shiny drip on the hinge and then at {helper.id}, and both children burst into surprised giggles."
        )
    else:
        world.say(
            f'"The flask was for me," {recipient.pronoun()} said, laughing kindly. '
            f'"The gate only needed the right direction."'
        )
        world.say(
            f"{hero.id}'s cheeks turned pink, but only for a second, because the idea of a thirsty gate was too funny to keep a straight face."
        )
    world.facts["clarified"] = True


def tidy_or_share(world: World, hero: Entity, helper: Entity, parent: Entity, recipient: Entity, flask: Entity, fill: FlaskFill, setting: Setting) -> None:
    if flask.meters["spilled"] >= THRESHOLD:
        hero.memes["embarrassment"] = 0.0
        hero.memes["relief"] += 1
        gate = world.get("gate")
        gate.meters["sticky"] = 0.0
        world.say(
            f"{recipient.id} fetched a rag, and {parent.label_word} helped wipe the hinge clean. "
            f"Luckily, a little of the {fill.label} was still inside the flask."
        )
        world.say(
            f'{recipient.pronoun().capitalize()} took a careful sip and said, "Much better in a cup than on a gate." '
            f"That made {hero.id} laugh so hard {hero.pronoun()} had to hold the flask with both hands again."
        )
        world.facts["spill"] = True
        world.facts["outcome"] = "spill"
    else:
        hero.memes["relief"] += 1
        world.say(
            f"{recipient.id} took the flask, opened the cup-lid, and let the warm smell drift out into the cold air."
        )
        world.say(
            f"{helper.id} held the gate while {hero.id} followed the sign this time. "
            f"{hero.pronoun().capitalize()} grinned as {hero.pronoun()} {'pulled' if setting.opens == 'pull' else 'slid'} it the right way."
        )
        world.facts["spill"] = False
        world.facts["outcome"] = "clean"
    world.facts["sign_helped"] = True


def ending_image(world: World, hero: Entity, helper: Entity, recipient: Entity, setting: Setting) -> None:
    world.say(
        f"A minute later, the children went through the gate properly at last. "
        f"{hero.id} touched the latch, looked first, and then "
        f"{'pulled' if setting.opens == 'pull' else 'slid'} with a proud little nod."
    )
    world.say(
        f'After that, whenever anyone mentioned a flask and a gate in the same sentence, '
        f"{helper.id} and {hero.id} had to bite their lips to stop laughing."
    )


def tell(
    setting: Setting,
    fill: FlaskFill,
    misreading: Misreading,
    hero_name: str = "Lily",
    hero_gender: str = "girl",
    helper_name: str = "Tom",
    helper_gender: str = "boy",
    helper_trait: str = "careful",
    parent_type: str = "mother",
    relation: str = "siblings",
    hero_age: int = 5,
    helper_age: int = 6,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        traits=["earnest"],
        age=hero_age,
        attrs={"relation": relation},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=[helper_trait],
        age=helper_age,
        attrs={"relation": relation},
        tags={"child"},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        tags={"adult"},
    ))
    recipient = world.add(Entity(
        id=setting.recipient_name,
        kind="character",
        type=setting.recipient_type,
        role="recipient",
        label=setting.recipient_role,
        tags={setting.recipient_role},
    ))
    gate = world.add(Entity(
        id="gate",
        kind="thing",
        type="gate",
        label=setting.gate_name,
        attrs={"opens": setting.opens, "squeaky": setting.squeaky, "kind": setting.gate_kind},
        tags={"gate"},
    ))
    flask = world.add(Entity(
        id="flask",
        kind="thing",
        type="flask",
        label="flask",
        attrs={"fill": fill.label, "smell": fill.smell},
        tags={"flask"},
    ))

    gate.meters["pushed"] = 0.0
    gate.meters["sticky"] = 0.0
    flask.meters["tilted"] = 0.0
    flask.meters["full"] = 1.0
    flask.meters["spilled"] = 0.0
    hero.memes["confusion"] = 0.0
    hero.memes["embarrassment"] = 0.0
    hero.memes["relief"] = 0.0
    hero.memes["amusement"] = 0.0
    helper.memes["caution"] = initial_caution(helper_trait)
    helper.memes["surprise"] = 0.0
    recipient.memes["amusement"] = 0.0

    plan = plan_for(setting, misreading, StoryParams(
        setting=setting.id,
        fill=fill.id,
        misreading=misreading.id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent_type,
        helper_trait=helper_trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
    ))

    introduce(world, hero, helper, parent, setting, fill)
    hand_off(world, hero, helper, parent, recipient, fill, setting)

    world.para()
    mishear(world, hero, helper, misreading)

    if plan.early_fix:
        helper_corrects(world, hero, helper, recipient, setting, misreading)
    else:
        action_attempt(world, hero, helper, gate, flask, misreading, setting)

    world.para()
    reversal(world, hero, helper, recipient, gate, flask, setting, fill)
    tidy_or_share(world, hero, helper, parent, recipient, flask, fill, setting)

    world.para()
    ending_image(world, hero, helper, recipient, setting)

    world.facts.update(
        setting=setting,
        fill=fill,
        misreading=misreading,
        hero=hero,
        helper=helper,
        parent=parent,
        recipient=recipient,
        gate=gate,
        flask=flask,
        relation=relation,
        early_fix=plan.early_fix,
        wrong_push=plan.wrong_push,
    )
    return world


KNOWLEDGE = {
    "flask": [
        (
            "What is a flask?",
            "A flask is a strong little container that keeps a drink warm or cold for a long time. People carry soup, tea, or cocoa in it."
        )
    ],
    "gate": [
        (
            "What is a gate?",
            "A gate is a door in a fence. You open it to go in or out of a yard, garden, or farm."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or thinks the wrong thing. People can fix it by asking, checking, and listening again."
        )
    ],
    "reversal": [
        (
            "What is a reversal in a story?",
            "A reversal is when the story suddenly turns and the truth is different from what a character expected. It can feel funny because everything has to be understood in a new way."
        )
    ],
    "cocoa": [
        (
            "Why does hot cocoa make steam?",
            "Hot cocoa makes steam because it is warm, and some of the water in it turns into tiny bits that rise into the air. That is why warm drinks can look misty."
        )
    ],
    "tea": [
        (
            "Why do people drink warm tea on a chilly day?",
            "Warm tea can make your hands and throat feel cozy. A warm drink is comforting when the air feels cold."
        )
    ],
    "soup": [
        (
            "Why might someone carry soup in a flask?",
            "Soup stays warm in a flask, so a person can take it outside without it getting cold fast. That is useful on a chilly morning."
        )
    ],
    "garden": [
        (
            "Why might a gardener stand near a gate?",
            "A gardener may be working outside and greeting visitors. The gate is a handy place to meet people before they come in."
        )
    ],
    "library": [
        (
            "Why would a library have a story garden?",
            "A story garden is a quiet outdoor place where children can listen, read, and sit together. It makes books feel connected to the world outside."
        )
    ],
    "farm": [
        (
            "Why do farms use gates?",
            "Farms use gates to keep animals safe and to guide where people walk. A good gate helps everyone know where to go."
        )
    ],
    "ducks": [
        (
            "Why shouldn't you leave a gate open near ducks or farm animals?",
            "A closed gate helps keep animals where they are meant to be. If a gate stays open, the animals might wander somewhere unsafe."
        )
    ],
}
KNOWLEDGE_ORDER = ["flask", "gate", "misunderstanding", "reversal", "cocoa", "tea", "soup", "garden", "library", "farm", "ducks"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting"]
    misreading = f["misreading"]
    fill = f["fill"]
    return [
        f'Write a short comedy for a 3-to-5-year-old that uses the words "flask", "reversal", and "gate".',
        f"Tell a funny misunderstanding story where {hero.id} carries a flask to {setting.place} and gets the idea wrong before a kind adult explains it.",
        f"Write a gentle comic story in which {helper.id} and {hero.id} bring {fill.label} to {setting.recipient_name}, and the misunderstanding about the gate leads to a reversal.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    recipient = f["recipient"]
    setting = f["setting"]
    fill = f["fill"]
    misreading = f["misreading"]
    flask = f["flask"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {helper.id}, who were carrying a flask for {recipient.id}, and {hero.id}'s {parent.label_word} who sent them to the gate."
        ),
        (
            "Why were they carrying the flask?",
            f"They were carrying it to {recipient.id} at {setting.place}. The flask was meant to be a warm drink for {recipient.pronoun('object')} while {recipient.pronoun()} worked outside."
        ),
        (
            f"What misunderstanding did {hero.id} have?",
            f"{hero.id} misunderstood the job of the flask and {misreading.thought}. The mistake happened because {parent.label_word} said to take the flask to the gate, and {hero.id} mixed up who it was really for."
        ),
    ]
    if f["early_fix"]:
        qa.append(
            (
                f"How was the misunderstanding fixed before anything messy happened?",
                f"{helper.id} stopped {hero.id} and explained that the flask was for {recipient.id}, not for the gate. That helped {hero.id} change plans before the funny mistake went any further."
            )
        )
    elif f["spill"]:
        qa.append(
            (
                "What happened when the misunderstanding was acted out?",
                f"{hero.id} tilted the flask and some of the {fill.label} spilled on the gate. That made the middle of the story funnier, because the gate ended up wearing the drink that was supposed to be inside the flask."
            )
        )
    else:
        qa.append(
            (
                "What did the children do because of the misunderstanding?",
                f"{hero.id} offered the flask to the gate itself in a very serious way. Nothing broke, but the gate stayed just a gate until the grown-up laughed and explained the mix-up."
            )
        )
    qa.append(
        (
            "What was the reversal?",
            f"The reversal came when {recipient.id} simply {'pulled' if setting.opens == 'pull' else 'slid'} the gate open and showed there had never been a gate mystery at all. The flask was for drinking, and the gate only needed the right direction."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children going through the gate the right way and laughing about the mistake. The ending image shows that {hero.id} now checks first and uses the flask like a flask, not like gate magic."
        )
    )
    if flask.meters["spilled"] >= THRESHOLD:
        qa.append(
            (
                "Was anyone angry after the spill?",
                f"No. {recipient.id} and {parent.label_word} helped clean up, and everyone treated the mistake as something to fix and laugh about. That kindness turned embarrassment into relief."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"flask", "gate", "misunderstanding", "reversal"}
    setting = world.facts["setting"]
    fill = world.facts["fill"]
    misreading = world.facts["misreading"]
    tags |= set(setting.tags)
    tags |= set(fill.tags)
    tags |= set(misreading.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v is False}
            bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="community_garden",
        fill="cocoa",
        misreading="oil",
        hero="Lily",
        hero_gender="girl",
        helper="Tom",
        helper_gender="boy",
        parent="mother",
        helper_trait="cheerful",
        relation="siblings",
        hero_age=6,
        helper_age=4,
    ),
    StoryParams(
        setting="duck_pond",
        fill="tea",
        misreading="key",
        hero="Ben",
        hero_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        helper_trait="curious",
        relation="friends",
        hero_age=5,
        helper_age=5,
    ),
    StoryParams(
        setting="town_library",
        fill="soup",
        misreading="trade",
        hero="Ava",
        hero_gender="girl",
        helper="Noah",
        helper_gender="boy",
        parent="mother",
        helper_trait="thoughtful",
        relation="friends",
        hero_age=5,
        helper_age=6,
    ),
    StoryParams(
        setting="petting_farm",
        fill="cocoa",
        misreading="key",
        hero="Sam",
        hero_gender="boy",
        helper="Rose",
        helper_gender="girl",
        parent="father",
        helper_trait="careful",
        relation="siblings",
        hero_age=4,
        helper_age=7,
    ),
    StoryParams(
        setting="community_garden",
        fill="tea",
        misreading="trade",
        hero="Zoe",
        hero_gender="girl",
        helper="Max",
        helper_gender="boy",
        parent="mother",
        helper_trait="sensible",
        relation="siblings",
        hero_age=5,
        helper_age=7,
    ),
]


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
supports(S, oil)   :- setting(S), squeaky_gate(S).
supports(S, trade) :- setting(S), staffed_gate(S).
supports(S, key)   :- setting(S).

valid(S, F, M) :- setting(S), fill(F), misreading(M), supports(S, M).

% --- early correction / outcome -------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

helper_older :- relation(siblings), helper_age(H), hero_age(A), H > A.
bonus(4) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).

early_fix :- authority(A), bravery_init(BR), A > BR.

risky(key).
risky(oil).

spill :- chosen_mode(M), risky(M), not early_fix.
outcome(spill) :- spill.
outcome(clean) :- not spill.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        if setting.squeaky:
            lines.append(asp.fact("squeaky_gate", setting_id))
        if setting.staffed:
            lines.append(asp.fact("staffed_gate", setting_id))
    for fill_id in FILLS:
        lines.append(asp.fact("fill", fill_id))
    for misreading_id in MISREADINGS:
        lines.append(asp.fact("misreading", misreading_id))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_mode", params.misreading),
            asp.fact("trait", params.helper_trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("helper_age", params.helper_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test story came out empty")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a flask, a gate, and a comic misunderstanding. "
        "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--fill", choices=FILLS)
    ap.add_argument("--misreading", choices=MISREADINGS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.misreading:
        setting = SETTINGS[args.setting]
        misreading = MISREADINGS[args.misreading]
        if not valid_combo(setting, misreading):
            raise StoryError(explain_rejection(setting, misreading))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.fill is None or combo[1] == args.fill)
        and (args.misreading is None or combo[2] == args.misreading)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, fill_id, misreading_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([4, 5, 6, 7], 2)
    hero_age, helper_age = ages[0], ages[1]
    return StoryParams(
        setting=setting_id,
        fill=fill_id,
        misreading=misreading_id,
        hero=hero_name,
        hero_gender=hero_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        helper_trait=helper_trait,
        relation=relation,
        hero_age=hero_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.fill not in FILLS:
        raise StoryError(f"(Unknown fill: {params.fill})")
    if params.misreading not in MISREADINGS:
        raise StoryError(f"(Unknown misreading: {params.misreading})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    setting = SETTINGS[params.setting]
    fill = FILLS[params.fill]
    misreading = MISREADINGS[params.misreading]
    if not valid_combo(setting, misreading):
        raise StoryError(explain_rejection(setting, misreading))

    world = tell(
        setting=setting,
        fill=fill,
        misreading=misreading,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        parent_type=params.parent,
        relation=params.relation,
        hero_age=params.hero_age,
        helper_age=params.helper_age,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, fill, misreading) combos:\n")
        for setting, fill, misreading in combos:
            print(f"  {setting:17} {fill:6} {misreading}")
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
            header = f"### {p.hero} & {p.helper}: {p.misreading} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
