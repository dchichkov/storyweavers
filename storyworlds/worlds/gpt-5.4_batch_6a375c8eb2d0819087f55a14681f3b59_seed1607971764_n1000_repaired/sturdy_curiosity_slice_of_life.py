#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py
============================================================

A standalone story world about a curious child, a mysterious household container
on a shelf, and the calm grown-up who helps in a sturdy, everyday way.

The core little tale:
- a child notices a sound from a box or jar on a shelf
- curiosity makes the child want to look right away
- a grown-up notices the tempting but unsafe shortcut
- together they use a sturdy aid that actually reaches
- they open the mystery and end with a small homey activity that proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py --setting kitchen --mystery cookie_tin
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py --aid wheeled_chair
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/sturdy_curiosity_slice_of_life.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
CHILD_GRIP = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    sturdy: bool = False
    reach: int = 0
    level: int = 0
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    shelf_phrase: str
    afford_mysteries: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    label: str
    phrase: str
    sound: str
    clue: str
    inside: str
    ending_use: str
    shelf_level: int
    open_force: int
    closure: str
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
class Aid:
    id: str
    label: str
    phrase: str
    sturdy: bool
    reach: int
    sense: int
    carry_text: str
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
class StoryParams:
    setting: str
    mystery: str
    aid: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_wobble(world: World) -> list[str]:
    child = world.entities.get("child")
    support = world.entities.get("support")
    if child is None or support is None:
        return []
    if child.meters["climbed"] < THRESHOLD or support.sturdy:
        return []
    sig = ("wobble", support.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    support.meters["wobble"] += 1
    child.memes["fear"] += 1
    child.meters["risk"] += 1
    if "parent" in world.entities:
        world.get("parent").memes["alarm"] += 1
    return ["__wobble__"]


def _r_reach(world: World) -> list[str]:
    child = world.entities.get("child")
    support = world.entities.get("support")
    mystery = world.entities.get("mystery")
    if child is None or support is None or mystery is None:
        return []
    if child.meters["climbed"] < THRESHOLD:
        return []
    sig = ("reach", support.id, mystery.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if support.reach >= mystery.level:
        child.meters["can_reach"] += 1
    return []


def _r_opened_joy(world: World) -> list[str]:
    child = world.entities.get("child")
    if child is None:
        return []
    if child.meters["mystery_opened"] < THRESHOLD:
        return []
    sig = ("opened_joy", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wonder"] += 1
    child.memes["joy"] += 1
    child.memes["curiosity"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="reach", tag="physical", apply=_r_reach),
    Rule(name="opened_joy", tag="emotional", apply=_r_opened_joy),
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


SETTINGS = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        shelf_phrase="the high pantry shelf above the flour and tea",
        afford_mysteries={"cookie_tin", "button_jar"},
    ),
    "hall_closet": Setting(
        id="hall_closet",
        place="the hall closet",
        shelf_phrase="the top shelf above the scarves and board games",
        afford_mysteries={"shell_box", "button_jar"},
    ),
    "laundry_room": Setting(
        id="laundry_room",
        place="the laundry room",
        shelf_phrase="the shelf over the folded towels",
        afford_mysteries={"clothespin_tin", "button_jar"},
    ),
}

MYSTERIES = {
    "cookie_tin": Mystery(
        id="cookie_tin",
        label="cookie tin",
        phrase="a round blue cookie tin",
        sound="a soft clink-clink",
        clue="something inside slid and tapped when the house settled",
        inside="star-shaped cookie cutters",
        ending_use="Later, they pressed the little stars into dough together on the table.",
        shelf_level=2,
        open_force=1,
        closure="lifted the lid",
        tags={"cookie_tin", "baking"},
    ),
    "button_jar": Mystery(
        id="button_jar",
        label="button jar",
        phrase="a glass jar full of old buttons",
        sound="a bright little jingle",
        clue="the colors winked through the glass whenever the light moved",
        inside="red, yellow, and pearly buttons",
        ending_use="Soon the buttons were spread on a towel while they sorted them into tiny shining piles.",
        shelf_level=2,
        open_force=2,
        closure="twisted the lid",
        tags={"button_jar", "buttons"},
    ),
    "shell_box": Mystery(
        id="shell_box",
        label="shell box",
        phrase="a striped box with a tiny brass clasp",
        sound="a hushy clatter",
        clue="it smelled faintly like the beach when the closet door opened",
        inside="smooth seashells from old family trips",
        ending_use="By the window, they lined the shells in a neat curve and talked about waves.",
        shelf_level=3,
        open_force=2,
        closure="unhooked the clasp",
        tags={"shell_box", "shells"},
    ),
    "clothespin_tin": Mystery(
        id="clothespin_tin",
        label="clothespin tin",
        phrase="a square tin with painted daisies",
        sound="a wooden knock-knock",
        clue="something inside thumped gently whenever a towel brushed the shelf",
        inside="bright clothespins in blue, green, and orange",
        ending_use="After that, they used the bright clothespins to hang one small drawing on the line.",
        shelf_level=1,
        open_force=1,
        closure="popped the lid open",
        tags={"clothespin_tin", "clothespins"},
    ),
}

AIDS = {
    "sturdy_step_stool": Aid(
        id="sturdy_step_stool",
        label="sturdy step stool",
        phrase="a sturdy step stool",
        sturdy=True,
        reach=2,
        sense=3,
        carry_text="brought over the sturdy step stool from beside the counter",
        tags={"stool", "sturdy"},
    ),
    "library_stool": Aid(
        id="library_stool",
        label="sturdy library stool",
        phrase="a sturdy library stool",
        sturdy=True,
        reach=2,
        sense=3,
        carry_text="rolled over the heavy little library stool and locked its feet in place",
        tags={"stool", "sturdy"},
    ),
    "step_ladder": Aid(
        id="step_ladder",
        label="sturdy step ladder",
        phrase="a sturdy step ladder",
        sturdy=True,
        reach=3,
        sense=3,
        carry_text="opened the sturdy step ladder with a careful click",
        tags={"ladder", "sturdy"},
    ),
    "wheeled_chair": Aid(
        id="wheeled_chair",
        label="wheeled chair",
        phrase="a wheeled chair",
        sturdy=False,
        reach=2,
        sense=1,
        carry_text="pulled out the wheeled chair",
        tags={"chair"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Noah", "Eli", "Theo", "Finn"]
TRAITS = ["curious", "careful", "bright-eyed", "patient", "eager", "thoughtful"]


def sensible_aids() -> list[Aid]:
    return [a for a in AIDS.values() if a.sense >= SENSE_MIN]


def can_reach(aid: Aid, mystery: Mystery) -> bool:
    return aid.reach >= mystery.shelf_level


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid in sorted(setting.afford_mysteries):
            mystery = MYSTERIES[mid]
            for aid in sensible_aids():
                if can_reach(aid, mystery):
                    combos.append((sid, mid, aid.id))
    return combos


def opener_of(params: StoryParams) -> str:
    mystery = MYSTERIES[params.mystery]
    return "child" if mystery.open_force <= CHILD_GRIP else "parent"


def predict_wobble(world: World, support_id: str) -> dict:
    sim = world.copy()
    sim.entities["support"] = copy.deepcopy(sim.get(support_id))
    sim.get("child").meters["climbed"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("support").meters["wobble"] >= THRESHOLD,
        "risk": sim.get("child").meters["risk"],
    }


def introduce(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"One ordinary afternoon, {child.id} was helping {child.pronoun('possessive')} "
        f"{parent.label_word} in {world.setting.place}. {child.pronoun().capitalize()} was a little {trait} "
        f"{child.type}, the kind who noticed every tiny sound in a room."
    )
    world.say(
        f"From {world.setting.shelf_phrase} came {mystery.sound}. "
        f"{mystery.clue[0].upper()}{mystery.clue[1:]}, and {child.id} looked up at once."
    )


def wonder(world: World, child: Entity, mystery: Mystery) -> None:
    child.memes["curiosity"] += 2
    world.say(
        f'"What is in that {mystery.label}?" {child.id} asked. '
        f'The question sat in {child.pronoun("possessive")} mind and would not leave.'
    )


def tempt(world: World, child: Entity) -> None:
    child.memes["impatience"] += 1
    world.say(
        f"{child.id} stretched up on tiptoe, then glanced at the little wheeled chair nearby. "
        f"For one second, climbing right away looked faster than waiting."
    )


def warn(world: World, child: Entity, parent: Entity) -> None:
    pred = predict_wobble(world, "unsafe")
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_risk"] = pred["risk"]
    parent.memes["care"] += 1
    child.memes["listened"] += 1
    world.say(
        f'{parent.label_word.capitalize()} noticed the look and shook {parent.pronoun("possessive")} head. '
        f'"Not on the wheeled chair," {parent.pronoun()} said gently. '
        f'"It could roll, and then you could tumble before you even reached the shelf."'
    )


def bring_aid(world: World, child: Entity, parent: Entity, aid: Aid) -> None:
    support = world.get("support")
    support.sturdy = aid.sturdy
    support.reach = aid.reach
    support.label = aid.label
    support.phrase = aid.phrase
    world.say(
        f"Instead, {parent.label_word} {aid.carry_text}. "
        f'"If you are that curious," {parent.pronoun()} said, "let us do it the steady way."'
    )


def climb(world: World, child: Entity, parent: Entity) -> None:
    child.meters["climbed"] += 1
    propagate(world, narrate=False)
    if child.meters["can_reach"] >= THRESHOLD:
        world.say(
            f"{child.id} climbed up while {parent.label_word} kept one hand near the side. "
            f"Nothing wobbled. From up there, the shelf did not feel scary at all."
        )
    else:
        world.say(
            f"{child.id} climbed carefully, but even on the safe support the shelf stayed just out of reach."
        )


def lift_down(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    if child.meters["can_reach"] >= THRESHOLD:
        world.say(
            f"{child.id} slid {mystery.phrase} toward the edge with both hands, and "
            f"{parent.label_word} lifted it down to the table."
        )
    else:
        world.say(
            f"{parent.label_word.capitalize()} reached the last little bit and brought {mystery.phrase} down to the table."
        )


def open_mystery(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    who = world.facts["opener"]
    if who == "child":
        world.say(
            f"{child.id} {mystery.closure}, and inside were {mystery.inside}. "
            f"{child.pronoun().capitalize()} gave a soft gasp that turned into a smile."
        )
    else:
        world.say(
            f"{child.id} tried first, but the lid was snug. Then {parent.label_word} {mystery.closure}, "
            f"and inside were {mystery.inside}. {child.id}'s eyes grew round and bright."
        )
    child.meters["mystery_opened"] += 1
    propagate(world, narrate=False)


def settle_ending(world: World, child: Entity, parent: Entity, mystery: Mystery) -> None:
    child.memes["relief"] += 1
    parent.memes["relief"] += 1
    world.say(
        f'"So that was the sound," {child.id} said, touching the edge of the container as if it had told a secret.'
    )
    world.say(
        f"{mystery.ending_use} {child.id} kept glancing at the sturdy helper they had used, "
        f"as if being curious and being careful belonged together after all."
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    aid: Aid,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World(setting)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["little", trait],
    ))
    child.attrs["name"] = child_name
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    mystery_ent = world.add(Entity(
        id="mystery",
        type="container",
        label=mystery.label,
        phrase=mystery.phrase,
        level=mystery.shelf_level,
    ))
    world.add(Entity(
        id="unsafe",
        type="support",
        label=AIDS["wheeled_chair"].label,
        phrase=AIDS["wheeled_chair"].phrase,
        sturdy=AIDS["wheeled_chair"].sturdy,
        reach=AIDS["wheeled_chair"].reach,
    ))
    world.add(Entity(
        id="support",
        type="support",
        label=aid.label,
        phrase=aid.phrase,
        sturdy=aid.sturdy,
        reach=aid.reach,
    ))

    world.facts["child_name"] = child_name
    world.facts["opener"] = "child" if mystery.open_force <= CHILD_GRIP else "parent"

    introduce(world, child, parent, mystery)
    wonder(world, child, mystery)

    world.para()
    tempt(world, child)
    warn(world, child, parent)
    bring_aid(world, child, parent, aid)

    world.para()
    climb(world, child, parent)
    lift_down(world, child, parent, mystery)
    open_mystery(world, child, parent, mystery)

    world.para()
    settle_ending(world, child, parent, mystery)

    world.facts.update(
        child=child,
        parent=parent,
        setting=setting,
        mystery_cfg=mystery,
        mystery=mystery_ent,
        aid=aid,
        support=world.get("support"),
        safe_reach=world.get("support").reach,
        curiosity_satisfied=child.meters["mystery_opened"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "stool": [(
        "What is a step stool for?",
        "A step stool helps you reach something a little higher in a steady way. It is made to stand still while someone climbs carefully."
    )],
    "ladder": [(
        "What is a step ladder?",
        "A step ladder is a folding ladder for reaching higher places. A grown-up opens it flat so it stays balanced and safe."
    )],
    "sturdy": [(
        "What does sturdy mean?",
        "Sturdy means strong and steady, not shaky or floppy. A sturdy thing can hold still while you use it."
    )],
    "buttons": [(
        "What are buttons used for?",
        "Buttons can close clothes, but people also sort them, sew with them, and use them for crafts. They often come in many colors and shapes."
    )],
    "shells": [(
        "Where do seashells come from?",
        "Seashells are the hard outer homes of some sea animals. After the animal is gone, the shell can wash up on a beach."
    )],
    "baking": [(
        "What are cookie cutters for?",
        "Cookie cutters press shapes into dough. They help make stars, hearts, and other fun cookies."
    )],
    "clothespins": [(
        "What is a clothespin?",
        "A clothespin is a little clip that holds cloth on a line. It squeezes shut so the cloth does not blow away."
    )],
    "curiosity": [(
        "What is curiosity?",
        "Curiosity is the feeling of wanting to know more about something. It can help you learn when you ask and explore in a careful way."
    )],
}
KNOWLEDGE_ORDER = ["curiosity", "sturdy", "stool", "ladder", "buttons", "shells", "baking", "clothespins"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    mystery = world.facts["mystery_cfg"]
    aid = world.facts["aid"]
    parent = world.facts["parent"]
    name = child.attrs["name"]
    return [
        f'Write a short slice-of-life story for a 3-to-5-year-old that includes the word "sturdy" and centers on curiosity.',
        f"Tell a homey story where a {child.type} named {name} hears a strange sound from a {mystery.label} on a shelf and {name}'s {parent.label_word} helps {child.pronoun('object')} use {aid.phrase}.",
        f"Write a gentle story about wanting to know what is inside something, almost choosing a shaky shortcut, and then solving the mystery the careful way.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    parent = world.facts["parent"]
    mystery = world.facts["mystery_cfg"]
    aid = world.facts["aid"]
    name = child.attrs["name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, a curious little {child.type}, and {name}'s {pw}. They were together at home when a small mystery caught {name}'s attention."
        ),
        (
            f"Why did {name} want to reach the shelf?",
            f"{name} heard {mystery.sound} from the {mystery.label} and wanted to know what was inside. Curiosity kept tugging until {name} had to ask and look."
        ),
        (
            f"Why did {name}'s {pw} say no to the wheeled chair?",
            f"{pw.capitalize()} could tell the chair might roll if {name} climbed on it. That would make reaching the shelf risky before {name} even touched the container."
        ),
        (
            f"How did they solve the problem?",
            f"They used {aid.phrase} instead and brought the {mystery.label} down to the table together. The sturdy helper let them satisfy {name}'s curiosity without a wobble."
        ),
    ]
    if world.facts["opener"] == "parent":
        qa.append((
            f"Who opened the {mystery.label}?",
            f"{name} tried first, but the closure was too snug for small hands. Then {pw} opened it, so the mystery could still be solved calmly together."
        ))
    else:
        qa.append((
            f"Who opened the {mystery.label}?",
            f"{name} opened it after they brought it down safely. Being able to do that made the answer feel even more exciting."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the mystery solved and the family using what they found in a small everyday way. The final picture shows that careful curiosity can lead to joy, not trouble."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"curiosity"} | set(world.facts["aid"].tags) | set(world.facts["mystery_cfg"].tags)
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
        if ent.sturdy:
            bits.append("sturdy=True")
        if ent.reach:
            bits.append(f"reach={ent.reach}")
        if ent.level:
            bits.append(f"level={ent.level}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="kitchen",
        mystery="cookie_tin",
        aid="sturdy_step_stool",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        setting="hall_closet",
        mystery="shell_box",
        aid="step_ladder",
        name="Ben",
        gender="boy",
        parent="father",
        trait="thoughtful",
    ),
    StoryParams(
        setting="laundry_room",
        mystery="clothespin_tin",
        aid="library_stool",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="bright-eyed",
    ),
    StoryParams(
        setting="hall_closet",
        mystery="button_jar",
        aid="step_ladder",
        name="Theo",
        gender="boy",
        parent="father",
        trait="eager",
    ),
]


def explain_combo(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} does not belong in {setting.place} in this little world. "
        f"Try a mystery that this room actually holds.)"
    )


def explain_aid(aid: Aid) -> str:
    if aid.sense < SENSE_MIN:
        good = ", ".join(sorted(a.id for a in sensible_aids()))
        return (
            f"(Refusing aid '{aid.id}': it is not a safe, sturdy choice here "
            f"(sense={aid.sense} < {SENSE_MIN}). Try one of: {good}.)"
        )
    return f"(Refusing aid '{aid.id}': it does not fit this story.)"


def explain_reach(aid: Aid, mystery: Mystery) -> str:
    return (
        f"(No story: {aid.phrase} cannot reach the {mystery.label} on this shelf. "
        f"Choose something that reaches level {mystery.shelf_level} safely.)"
    )


ASP_RULES = r"""
sensible_aid(A) :- aid(A), sense(A,S), sense_min(M), S >= M.
reachable(A,M)  :- reach(A,R), shelf_level(M,L), R >= L.
valid(S,M,A)    :- setting(S), mystery(M), aid(A), affords(S,M), sensible_aid(A), reachable(A,M).

opener(child)  :- chosen_mystery(M), open_force(M,F), child_grip(G), F <= G.
opener(parent) :- chosen_mystery(M), open_force(M,F), child_grip(G), F > G.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sid, setting in SETTINGS.items():
        for mid in sorted(setting.afford_mysteries):
            lines.append(asp.fact("affords", sid, mid))
    for mid, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("shelf_level", mid, mystery.shelf_level))
        lines.append(asp.fact("open_force", mid, mystery.open_force))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("reach", aid_id, aid.reach))
        lines.append(asp.fact("sense", aid_id, aid.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("child_grip", CHILD_GRIP))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_opener(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_mystery", params.mystery)
    model = asp.one_model(asp_program(extra, "#show opener/1."))
    atoms = asp.atoms(model, "opener")
    return atoms[0][0] if atoms else "?"


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
    parser = build_parser()
    for seed in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_opener(params) != opener_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: opener model matches opener_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} opener results differ.")

    try:
        params = resolve_params(parser.parse_args([]), random.Random(123))
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("empty story")
        sink = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = sink
            emit(sample, trace=False, qa=False, header="smoke")
        finally:
            sys.stdout = old
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a curious child, a shelf mystery, and a sturdy everyday solution."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible stories from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mystery:
        if args.mystery not in SETTINGS[args.setting].afford_mysteries:
            raise StoryError(explain_combo(SETTINGS[args.setting], MYSTERIES[args.mystery]))
    if args.aid:
        aid = AIDS[args.aid]
        if aid.sense < SENSE_MIN:
            raise StoryError(explain_aid(aid))
        if args.mystery and not can_reach(aid, MYSTERIES[args.mystery]):
            raise StoryError(explain_reach(aid, MYSTERIES[args.mystery]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        aid=aid_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def _require(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(Unknown {label}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    setting = _require(SETTINGS, params.setting, "setting")
    mystery = _require(MYSTERIES, params.mystery, "mystery")
    aid = _require(AIDS, params.aid, "aid")

    if params.mystery not in setting.afford_mysteries:
        raise StoryError(explain_combo(setting, mystery))
    if aid.sense < SENSE_MIN:
        raise StoryError(explain_aid(aid))
    if not can_reach(aid, mystery):
        raise StoryError(explain_reach(aid, mystery))

    world = tell(
        setting=setting,
        mystery=mystery,
        aid=aid,
        child_name=params.name,
        child_gender=params.gender,
        parent_type=params.parent,
        trait=params.trait,
    )

    child = world.facts["child"]
    name = child.attrs["name"]
    story_text = world.render().replace("child", name).replace("parent", world.facts["parent"].label_word)

    return StorySample(
        params=params,
        story=story_text,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("child", name)) for q, a in story_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show opener/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery, aid) combos:\n")
        for setting, mystery, aid in combos:
            print(f"  {setting:12} {mystery:14} {aid}")
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
            header = f"### {p.name}: {p.mystery} in {p.setting} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
