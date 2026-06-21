#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py
========================================================================================

A standalone story world about two friends on a seaside esplanade whose curiosity
pulls them toward a stuck object, while friendship helps them choose a safer way
to solve the problem.

The world is built for gentle, child-facing stories with:
- the required words "mauve" and "esplanade"
- a happy ending
- curiosity as the spark
- friendship as the steadying force
- a lightly rhyming, sing-song style

The small simulation models:
- typed entities with physical meters and emotional memes
- a near-risky reach or an averted reach
- a sensible helper/tool choice constrained by the world
- recovery of the lost item
- return of the item to its owner

Run it
------
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py --item key --snag drain --helper bandleader
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py --item scarf --helper bandleader
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py --all
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mauve_esplanade_happy_ending_curiosity_friendship_rhyming.py --verify
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
CAUTIOUS_TRAITS = {"careful", "steady", "thoughtful"}


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
        female = {"girl", "woman"}
        male = {"boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Snag:
    id: str
    label: str
    place_text: str
    risk: int
    reach_text: str
    danger_text: str
    rescue_text: str
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
class Item:
    id: str
    label: str
    phrase: str
    material: str
    clue: str
    owner_name: str
    owner_role: str
    owner_line: str
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
class Tool:
    id: str
    label: str
    verb: str
    works_on_materials: set[str] = field(default_factory=set)
    works_on_snags: set[str] = field(default_factory=set)
    qa_text: str = ""
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
class Helper:
    id: str
    label: str
    type: str
    tool: str
    intro: str
    kind_line: str
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


def _r_reach_risk(world: World) -> list[str]:
    out: list[str] = []
    snag = world.facts["snag_cfg"]
    finder = world.facts["finder"]
    friend = world.facts["friend"]
    if finder.meters["reaching"] < THRESHOLD:
        return out
    sig = ("reach_risk", snag.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    finder.meters["risk"] += float(snag.risk)
    friend.memes["worry"] += 1
    world.facts["predicted_risk"] = snag.risk
    out.append("__risk__")
    return out


def _r_recovered(world: World) -> list[str]:
    out: list[str] = []
    item = world.facts["item_ent"]
    finder = world.facts["finder"]
    friend = world.facts["friend"]
    if item.meters["recovered"] < THRESHOLD:
        return out
    sig = ("recovered", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["stuck"] = 0.0
    finder.memes["relief"] += 1
    friend.memes["relief"] += 1
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    out.append("__recovered__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="reach_risk", tag="physical", apply=_r_reach_risk),
    Rule(name="recovered", tag="physical", apply=_r_recovered),
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


SNAGS = {
    "drain": Snag(
        id="drain",
        label="storm drain",
        place_text="in the narrow bars of a storm drain by the esplanade bench",
        risk=1,
        reach_text="knelt and slipped curious fingers toward the narrow bars",
        danger_text="A finger could wedge where iron stayed, and small surprises can turn sharp in a blink.",
        rescue_text="under the drain's thin bars",
        tags={"drain", "esplanade"},
    ),
    "fountain": Snag(
        id="fountain",
        label="fountain rim",
        place_text="inside the shallow fountain where silver water made rings",
        risk=2,
        reach_text="leaned over the fountain lip, stretching farther than was wise",
        danger_text="Wet stone can turn slick in a beat, and a curious reach can end with a slip of the feet.",
        rescue_text="from the fountain's bright basin",
        tags={"fountain", "water", "esplanade"},
    ),
    "railing": Snag(
        id="railing",
        label="curled railing",
        place_text="high in the curls of an iron railing above a flower bed",
        risk=2,
        reach_text="rose on tiptoe and started to climb the lower rail",
        danger_text="A wobble from that height could bring a tumble, however light.",
        rescue_text="from the railing's windy curl",
        tags={"railing", "height", "esplanade"},
    ),
}

ITEMS = {
    "key": Item(
        id="key",
        label="key",
        phrase="a small brass key",
        material="metal",
        clue="a blue tag that said 'Boat Shed B'",
        owner_name="Mr. Vale",
        owner_role="boatman",
        owner_line='"My key!" cried Mr. Vale. "Now the little skiffs can glide away."',
        tags={"metal", "key"},
    ),
    "whistle": Item(
        id="whistle",
        label="whistle",
        phrase="a bright tin whistle",
        material="metal",
        clue="tiny letters that read 'Mara Band'",
        owner_name="Mara",
        owner_role="band child",
        owner_line='"My whistle!" said Mara. "Now our seaside tune can play."',
        tags={"metal", "music"},
    ),
    "scarf": Item(
        id="scarf",
        label="scarf",
        phrase="a soft mauve scarf",
        material="fabric",
        clue="a stitched corner that said 'Aunt June'",
        owner_name="Aunt June",
        owner_role="visitor",
        owner_line='"My mauve scarf!" laughed Aunt June. "You saved my breezy day."',
        tags={"fabric", "mauve"},
    ),
    "boat": Item(
        id="boat",
        label="toy boat",
        phrase="a little painted toy boat",
        material="wood",
        clue="the name 'Pip' on its tiny side",
        owner_name="Pip",
        owner_role="small child",
        owner_line='"My boat!" cheered Pip. "Now it can bob and play."',
        tags={"wood", "toy"},
    ),
}

TOOLS = {
    "magnet": Tool(
        id="magnet",
        label="magnet wand",
        verb="lowered a magnet wand with a slow, patient sway",
        works_on_materials={"metal"},
        works_on_snags={"drain", "railing", "fountain"},
        qa_text="used a magnet wand to pull the item free",
        tags={"magnet"},
    ),
    "grabber": Tool(
        id="grabber",
        label="long litter-grabber",
        verb="opened a long litter-grabber and pinched with careful play",
        works_on_materials={"fabric", "wood", "metal"},
        works_on_snags={"drain", "railing"},
        qa_text="used a long litter-grabber to pinch the item free",
        tags={"grabber"},
    ),
    "net": Tool(
        id="net",
        label="ringed net",
        verb="dipped a ringed net through the water in a neat, soft way",
        works_on_materials={"fabric", "wood", "metal"},
        works_on_snags={"fountain"},
        qa_text="used a ringed net to lift the item out",
        tags={"net"},
    ),
}

HELPERS = {
    "bandleader": Helper(
        id="bandleader",
        label="the bandleader",
        type="woman",
        tool="magnet",
        intro="near the bandstand stood the bandleader, tuning for the afternoon air",
        kind_line='"Let us try the calm way first," she said, "and see what answers there."',
        tags={"music_helper"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="the caretaker",
        type="man",
        tool="grabber",
        intro="by the flower tubs worked the caretaker, brushing sand from every square",
        kind_line='"Hands stay safe and feet stay low," he said. "Good plans are best to share."',
        tags={"caretaker"},
    ),
    "fountain_keeper": Helper(
        id="fountain_keeper",
        label="the fountain keeper",
        type="woman",
        tool="net",
        intro="beside the fountain hummed the fountain keeper, checking every sparkling flare",
        kind_line='"Water likes to trick quick feet," she said. "A patient net is fair."',
        tags={"water_helper"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Tess", "Lila", "Ruby", "Ivy", "Clara", "Poppy"]
BOY_NAMES = ["Kit", "Owen", "Jules", "Milo", "Ned", "Theo", "Finn", "Arlo"]
TRAITS = ["careful", "steady", "thoughtful", "quick", "brave", "bouncy"]

KNOWLEDGE = {
    "esplanade": [(
        "What is an esplanade?",
        "An esplanade is a wide walkway, often by the sea, where people can stroll and look at the view. It is made for walking, so climbing and reaching in tricky places is not the safe game there."
    )],
    "drain": [(
        "Why should children keep their hands out of a storm drain?",
        "Storm drains have hard bars and narrow spaces where fingers can get stuck. It is safer to ask a grown-up with the right tool to help."
    )],
    "fountain": [(
        "Why can a fountain edge be slippery?",
        "Water can splash onto stone and make it slick. That is why leaning far over a fountain can lead to a slip."
    )],
    "railing": [(
        "Why is climbing a railing risky?",
        "A railing can be high and wobbly for small feet. A little climb can turn into a tumble very quickly."
    )],
    "magnet": [(
        "How can a magnet help pick up a metal thing?",
        "A magnet can pull on some metals without fingers needing to squeeze into a tight place. That makes it useful for lifting a metal object more safely."
    )],
    "grabber": [(
        "What is a litter-grabber for?",
        "A litter-grabber is a long tool that lets a person pinch and lift something from far away. It helps keep hands out of hard-to-reach spots."
    )],
    "net": [(
        "Why is a net useful in water?",
        "A net can scoop something up while keeping hands and feet steadier on dry ground. It is helpful when an object is sitting in shallow water."
    )],
    "friendship": [(
        "How can friendship help when someone feels too curious?",
        "A good friend can slow the moment down and help with a better idea. Friendship is not only playing together; it is also keeping each other safe."
    )],
    "curiosity": [(
        "Is curiosity good?",
        "Curiosity is good because it helps us notice and learn new things. It needs a safe path, though, so asking for help can be part of being curious and wise."
    )],
    "mauve": [(
        "What color is mauve?",
        "Mauve is a soft purple-pink color. People often use it to describe something gentle or dreamy."
    )],
    "music": [(
        "What does a whistle do in music?",
        "A whistle can make a clear, bright sound that helps make a tune. Musicians use small instruments carefully so they do not get lost."
    )],
}

KNOWLEDGE_ORDER = [
    "esplanade",
    "curiosity",
    "friendship",
    "drain",
    "fountain",
    "railing",
    "magnet",
    "grabber",
    "net",
    "mauve",
    "music",
]


def helper_tool(helper_id: str) -> Tool:
    return TOOLS[HELPERS[helper_id].tool]


def compatible(item: Item, snag: Snag, helper: Helper) -> bool:
    tool = TOOLS[helper.tool]
    return item.material in tool.works_on_materials and snag.id in tool.works_on_snags


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for snag_id, snag in SNAGS.items():
            for helper_id, helper in HELPERS.items():
                if compatible(item, snag, helper):
                    out.append((item_id, snag_id, helper_id))
    return sorted(out)


def reach_outcome(snag: Snag, friend_trait: str) -> str:
    if snag.risk >= 2 and friend_trait in CAUTIOUS_TRAITS:
        return "averted"
    return "wobble"


def predict_reach(world: World) -> dict:
    sim = world.copy()
    finder = sim.get("finder")
    finder.meters["reaching"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": finder.meters["risk"],
        "danger": sim.facts["snag_cfg"].danger_text,
    }


def introduce(world: World, finder: Entity, friend: Entity) -> None:
    world.say(
        f"On the mauve esplanade by the foam-flecked bay, {finder.id} and {friend.id} skipped in a sing-song way."
    )
    world.say(
        f"They were friends who liked to wonder and wander side by side, with curiosity bright as the turning tide."
    )
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    finder.memes["trust"] += 1
    friend.memes["trust"] += 1


def discover(world: World, finder: Entity, friend: Entity, item: Item, snag: Snag) -> None:
    item_ent = world.facts["item_ent"]
    item_ent.meters["stuck"] = 1.0
    finder.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"Then {finder.id} spied {item.phrase} {snag.place_text}, and both friends stopped with a soft surprise."
    )
    world.say(
        f'"Whose could it be?" whispered {friend.id}. "What tiny tale is tucked inside?"'
    )


def impulse(world: World, finder: Entity, snag: Snag) -> None:
    finder.memes["impulse"] += 1
    world.say(
        f"{finder.id} took one step, then two, then {snag.reach_text}."
    )


def warn(world: World, finder: Entity, friend: Entity, snag: Snag) -> None:
    pred = predict_reach(world)
    world.facts["predicted_risk"] = pred["risk"]
    friend.memes["care"] += 1
    extra = " " + pred["danger"]
    world.say(
        f'"Wait," said {friend.id}, gentle but quick. "Let us think before we pick."{extra}'
    )


def stop_in_time(world: World, finder: Entity, friend: Entity) -> None:
    finder.memes["restraint"] += 1
    finder.memes["respect"] += 1
    friend.memes["pride"] += 1
    world.say(
        f"{finder.id} paused at once and lowered {finder.pronoun('possessive')} hand. Friendship, not hurry, made the safer stand."
    )


def wobble(world: World, finder: Entity, friend: Entity, snag: Snag) -> None:
    finder.meters["reaching"] += 1
    propagate(world, narrate=False)
    finder.memes["startle"] += 1
    world.say(
        f"But before {friend.id} could tug {finder.pronoun('object')} back, there came a tiny wobble and a nervous lack of knack."
    )
    if snag.id == "drain":
        world.say(
            f"{finder.id} felt the cold iron nip at one knuckle and quickly pulled away."
        )
    elif snag.id == "fountain":
        world.say(
            f"{finder.id}'s shoe slid on one wet stone, and {friend.id} caught {finder.pronoun('possessive')} sleeve before the sway."
        )
    else:
        world.say(
            f"The rail gave a little creak beneath {finder.pronoun('possessive')} shoe, and that small sound was warning enough to do."
        )


def meet_helper(world: World, helper: Entity, helper_cfg: Helper) -> None:
    world.say(
        f"Just then, {helper_cfg.intro}."
    )
    world.say(helper_cfg.kind_line)


def recover(world: World, helper: Entity, helper_cfg: Helper, item: Item, snag: Snag) -> None:
    item_ent = world.facts["item_ent"]
    tool = helper_tool(helper_cfg.id)
    item_ent.meters["recovered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label.capitalize()} {tool.verb}, and soon {item.phrase} came free {snag.rescue_text}."
    )
    world.say(
        f"It landed safe in {helper.pronoun('possessive')} palm, not bent or torn or gray."
    )


def trace_owner(world: World, finder: Entity, friend: Entity, item: Item) -> None:
    item_ent = world.facts["item_ent"]
    item_ent.meters["clue_read"] += 1
    finder.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"On it they found {item.clue}, and now the mystery had a way."
    )
    world.say(
        f'"Let us look with open eyes," said {finder.id}. "The owner may be near today."'
    )


def return_item(world: World, finder: Entity, friend: Entity, item: Item) -> None:
    item_ent = world.facts["item_ent"]
    owner = world.facts["owner"]
    item_ent.meters["returned"] += 1
    owner.memes["gratitude"] += 1
    finder.memes["joy"] += 1
    friend.memes["joy"] += 1
    finder.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"Soon they found {owner.label}, who turned at once when {friend.id} called {owner.pronoun('object')} by name."
    )
    world.say(item.owner_line)
    world.say(
        f"{finder.id} and {friend.id} grinned at each other, glad their care and curiosity had done a kindly thing."
    )


def ending(world: World, finder: Entity, friend: Entity, item: Item) -> None:
    world.say(
        f"Then off they went along the esplanade, still full of questions, still full of cheer."
    )
    if item.id == "scarf":
        world.say(
            "The mauve scarf fluttered like a little flag behind Aunt June, and the two friends laughed in the sunny air."
        )
    else:
        world.say(
            "The sea hummed low, the gulls wheeled high, and side by side they walked without a fear."
        )
    world.say(
        f"For curiosity had found a friendly guide, and friendship kept it safe beside the tide."
    )


def tell(
    *,
    item_cfg: Item,
    snag_cfg: Snag,
    helper_cfg: Helper,
    finder_name: str,
    finder_gender: str,
    friend_name: str,
    friend_gender: str,
    friend_trait: str,
) -> World:
    world = World()
    finder = world.add(Entity(
        id="finder",
        kind="character",
        type=finder_gender,
        label=finder_name,
        role="finder",
        traits=["curious"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_gender,
        label=friend_name,
        role="friend",
        traits=[friend_trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type="person",
        label=item_cfg.owner_name,
        role="owner",
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        role="item",
        tags=set(item_cfg.tags),
    ))

    world.facts.update(
        finder=finder,
        friend=friend,
        helper=helper,
        owner=owner,
        item_ent=item_ent,
        item_cfg=item_cfg,
        snag_cfg=snag_cfg,
        helper_cfg=helper_cfg,
        friend_trait=friend_trait,
    )

    introduce(world, finder, friend)
    discover(world, finder, friend, item_cfg, snag_cfg)

    world.para()
    impulse(world, finder, snag_cfg)
    warn(world, finder, friend, snag_cfg)

    outcome = reach_outcome(snag_cfg, friend_trait)
    world.facts["outcome"] = outcome

    if outcome == "averted":
        stop_in_time(world, finder, friend)
    else:
        wobble(world, finder, friend, snag_cfg)

    world.para()
    meet_helper(world, helper, helper_cfg)
    recover(world, helper, helper_cfg, item_cfg, snag_cfg)

    world.para()
    trace_owner(world, finder, friend, item_cfg)
    return_item(world, finder, friend, item_cfg)
    ending(world, finder, friend, item_cfg)

    world.facts["happy"] = item_ent.meters["returned"] >= THRESHOLD
    return world


@dataclass
class StoryParams:
    item: str
    snag: str
    helper: str
    finder_name: str
    finder_gender: str
    friend_name: str
    friend_gender: str
    friend_trait: str
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


CURATED = [
    StoryParams(
        item="scarf",
        snag="railing",
        helper="caretaker",
        finder_name="Nia",
        finder_gender="girl",
        friend_name="Kit",
        friend_gender="boy",
        friend_trait="careful",
        seed=1,
    ),
    StoryParams(
        item="key",
        snag="drain",
        helper="bandleader",
        finder_name="Milo",
        finder_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        friend_trait="quick",
        seed=2,
    ),
    StoryParams(
        item="boat",
        snag="fountain",
        helper="fountain_keeper",
        finder_name="Ruby",
        finder_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        friend_trait="steady",
        seed=3,
    ),
    StoryParams(
        item="whistle",
        snag="railing",
        helper="bandleader",
        finder_name="Finn",
        finder_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        friend_trait="thoughtful",
        seed=4,
    ),
    StoryParams(
        item="boat",
        snag="drain",
        helper="caretaker",
        finder_name="Clara",
        finder_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        friend_trait="bouncy",
        seed=5,
    ),
]


def generation_prompts(world: World) -> list[str]:
    item = world.facts["item_cfg"]
    snag = world.facts["snag_cfg"]
    helper = world.facts["helper_cfg"]
    finder = world.facts["finder"]
    friend = world.facts["friend"]
    outcome = world.facts["outcome"]
    middle = (
        "where a careful friend stops a risky reach before it happens"
        if outcome == "averted"
        else "where a child gets a small scare from reaching too quickly, then accepts help"
    )
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the words "mauve" and "esplanade", featuring curiosity, friendship, and a happy ending.',
        f"Tell a gentle rhyming story where {finder.label} and {friend.label} find {item.phrase} {snag.place_text}, and {helper.label} helps retrieve it safely.",
        f"Write a sing-song seaside story {middle}, and the friends return the lost object to its owner.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    friend = f["friend"]
    helper = f["helper"]
    helper_cfg = f["helper_cfg"]
    item = f["item_cfg"]
    snag = f["snag_cfg"]
    outcome = f["outcome"]
    tool = helper_tool(helper_cfg.id)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {finder.label} and {friend.label}, walking on the mauve esplanade. Their friendship matters because they stay together and solve the problem as a team."
        ),
        (
            f"What made the children curious?",
            f"They saw {item.phrase} stuck {snag.place_text}, and they wanted to know whose it was. The mystery of the lost object pulled their attention and started the whole adventure."
        ),
        (
            f"Why was reaching for the {item.label} risky?",
            f"It was risky because it was stuck at {snag.label}, where a quick reach could go wrong. {snag.danger_text}"
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How did {friend.label} help before anything bad happened?",
            f"{friend.label} warned {finder.label} and helped {finder.pronoun('object')} stop in time. That caring pause turned curiosity into a safer plan before there was any wobble or slip."
        ))
    else:
        qa.append((
            f"What happened when {finder.label} reached too quickly?",
            f"{finder.label} had a little scare and pulled back fast. The moment showed why {friend.label}'s warning mattered and why asking for help was smarter."
        ))
    qa.append((
        f"How did {helper.label} get the {item.label} out?",
        f"{helper.label.capitalize()} {tool.qa_text}. The right tool matched both the object and the place where it was stuck, so nobody had to keep reaching dangerously."
    ))
    qa.append((
        f"How did they find the owner?",
        f"They noticed {item.clue} on the object and used that clue to look nearby. Their curiosity did not end with getting the object out; it helped them return it kindly."
    ))
    qa.append((
        "How did the story end?",
        f"It ended happily because the lost {item.label} was returned, and the two friends walked on together by the sea. The ending image shows that friendship and curiosity worked best when they stayed gentle and careful."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"esplanade", "curiosity", "friendship"} | set(f["snag_cfg"].tags) | set(f["item_cfg"].tags)
    tool = helper_tool(f["helper_cfg"].id)
    tags |= set(tool.tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted_risk={world.facts.get('predicted_risk')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(item: Item, snag: Snag, helper: Helper) -> str:
    tool = TOOLS[helper.tool]
    if item.material not in tool.works_on_materials:
        return (
            f"(No story: {helper.label} carries a {tool.label}, but that tool does not suit a {item.material} object like the {item.label}. "
            f"Pick a helper with a better-matched tool.)"
        )
    return (
        f"(No story: a {tool.label} is not a good way to recover the {item.label} from the {snag.label}. "
        f"Pick a helper whose tool fits that place.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.snag not in SNAGS or params.friend_trait not in TRAITS:
        raise StoryError("(No story: the requested snag or friend trait is unknown.)")
    return reach_outcome(SNAGS[params.snag], params.friend_trait)


ASP_RULES = r"""
valid(I,S,H) :- item(I), snag(S), helper(H), helper_tool(H,T),
                works_material(T,M), item_material(I,M),
                works_snag(T,S).

cautious(careful).
cautious(steady).
cautious(thoughtful).

averted :- chosen_snag(S), snag_risk(S,R), R >= 2, chosen_trait(T), cautious(T).
wobble  :- not averted.

outcome(averted) :- averted.
outcome(wobble)  :- wobble.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("item_material", item_id, item.material))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("snag_risk", snag_id, snag.risk))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for material in sorted(tool.works_on_materials):
            lines.append(asp.fact("works_material", tool_id, material))
        for snag_id in sorted(tool.works_on_snags):
            lines.append(asp.fact("works_snag", tool_id, snag_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helper_tool", helper_id, helper.tool))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_snag", params.snag),
        asp.fact("chosen_trait", params.friend_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
            if py != cl:
                mismatches.append((params, py, cl))
        except StoryError as err:
            rc = 1
            print(f"Unexpected StoryError during outcome check: {err}")
            break

    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} outcome differences.")
        for params, py, cl in mismatches[:5]:
            print(f"  {params} -> python={py} clingo={cl}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming seaside storyworld: curiosity, friendship, a stuck object, and a safe happy ending."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--friend-trait", choices=TRAITS, dest="friend_trait")
    ap.add_argument("--finder-name")
    ap.add_argument("--finder-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (item, snag, helper) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.snag and args.helper:
        if not compatible(ITEMS[args.item], SNAGS[args.snag], HELPERS[args.helper]):
            raise StoryError(explain_rejection(ITEMS[args.item], SNAGS[args.snag], HELPERS[args.helper]))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.snag is None or combo[1] == args.snag)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, snag_id, helper_id = rng.choice(combos)
    finder_gender = args.finder_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    finder_name = args.finder_name or _pick_name(rng, finder_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=finder_name)
    friend_trait = args.friend_trait or rng.choice(TRAITS)

    return StoryParams(
        item=item_id,
        snag=snag_id,
        helper=helper_id,
        finder_name=finder_name,
        finder_gender=finder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        friend_trait=friend_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(No story: unknown item '{params.item}'.)")
    if params.snag not in SNAGS:
        raise StoryError(f"(No story: unknown snag '{params.snag}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if params.friend_trait not in TRAITS:
        raise StoryError(f"(No story: unknown friend trait '{params.friend_trait}'.)")
    if not compatible(ITEMS[params.item], SNAGS[params.snag], HELPERS[params.helper]):
        raise StoryError(explain_rejection(ITEMS[params.item], SNAGS[params.snag], HELPERS[params.helper]))

    world = tell(
        item_cfg=ITEMS[params.item],
        snag_cfg=SNAGS[params.snag],
        helper_cfg=HELPERS[params.helper],
        finder_name=params.finder_name,
        finder_gender=params.finder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        friend_trait=params.friend_trait,
    )
    finder = world.facts["finder"]
    friend = world.facts["friend"]
    finder.label = params.finder_name
    friend.label = params.friend_name

    story_text = world.render().replace("finder", params.finder_name).replace("friend", params.friend_name)

    story_text = story_text.replace("finder", params.finder_name)
    story_text = story_text.replace("friend", params.friend_name)
    story_text = story_text.replace("Finder", params.finder_name)
    story_text = story_text.replace("Friend", params.friend_name)

    story_text = story_text.replace(world.facts["finder"].id, params.finder_name)
    story_text = story_text.replace(world.facts["friend"].id, params.friend_name)

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (item, snag, helper) combos:\n")
        for item_id, snag_id, helper_id in combos:
            print(f"  {item_id:8} {snag_id:9} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = f"### {p.finder_name} & {p.friend_name}: {p.item} at {p.snag} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
