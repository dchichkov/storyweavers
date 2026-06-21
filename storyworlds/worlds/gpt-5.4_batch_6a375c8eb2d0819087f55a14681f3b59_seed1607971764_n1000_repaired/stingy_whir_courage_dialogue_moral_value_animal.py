#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py
==============================================================================

A standalone story world for a small Animal Story about a stingy woodland animal,
a machine that goes whir, and a helper whose courage turns a selfish problem into
a shared solution.

Premise
-------
In a little woodland, the animals use a whirring seed lift to send winter food
up to a dry loft. One animal becomes stingy and refuses to share the lift.
Then the animal's own overstuffed food sack snags in the spinning wheel.
Another small animal must decide whether to act with courage, using a sensible
safe method, before the food spills away.

The model is state-driven:
- characters and objects are typed entities with physical meters and emotional memes
- a small forward-chaining rule system turns snagged spinning into danger and fear
- the helper's courage determines whether there is a delay
- the chosen rescue method determines whether the food is fully saved or partly lost
- the ending teaches sharing as the new rule of the place

Run it
------
python storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py
python storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py --all
python storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py --response paws
python storyworlds/worlds/gpt-5.4/stingy_whir_courage_dialogue_moral_value_animal.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "duck", "goose"}
        male = {"boy", "rooster"}
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
class Setting:
    id: str
    place: str
    opening: str
    machine: str
    loft: str
    air: str
    noise: int
    elder: str
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
class Hoard:
    id: str
    label: str
    phrase: str
    plural: bool
    weight: int
    spill_text: str
    share_text: str
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
class Snag:
    id: str
    label: str
    phrase: str
    severity: int
    shape: str
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
class Response:
    id: str
    sense: int
    power: int
    works_on: set[str]
    text: str
    fail: str
    qa_text: str
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


def _r_spinning_danger(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    load = world.get("load")
    if wheel.meters["spinning"] >= THRESHOLD and load.meters["snagged"] >= THRESHOLD:
        sig = ("danger",)
        if sig not in world.fired:
            world.fired.add(sig)
            wheel.meters["danger"] += 1
            for ent in list(world.entities.values()):
                if ent.role in {"keeper", "helper"}:
                    ent.memes["fear"] += 1
            out.append("__danger__")
    return out


def _r_torn_load(world: World) -> list[str]:
    out: list[str] = []
    wheel = world.get("wheel")
    load = world.get("load")
    if wheel.meters["danger"] >= THRESHOLD and wheel.meters["spinning"] >= THRESHOLD:
        sig = ("tear",)
        if sig not in world.fired:
            world.fired.add(sig)
            load.meters["torn"] += 1
            out.append("__tear__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="spinning_danger", tag="physical", apply=_r_spinning_danger),
    Rule(name="torn_load", tag="physical", apply=_r_torn_load),
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
    "oak_hollow": Setting(
        id="oak_hollow",
        place="an old oak hollow above a brook",
        opening="In Oak Hollow, the little animals kept their winter food high and dry.",
        machine="a seed lift with a round wooden wheel",
        loft="the loft above the hollow door",
        air="The morning air smelled of bark and cool water.",
        noise=1,
        elder="Badger",
        tags={"machine", "sharing"},
    ),
    "pine_bank": Setting(
        id="pine_bank",
        place="a pine-bank shed beside the stream",
        opening="On Pine Bank, the small animals stored their food in a snug shed by the stream.",
        machine="a nut lift with a willow wheel",
        loft="the shelf under the pine roof",
        air="The stream flashed under the roots, and the damp wind stirred the needles.",
        noise=2,
        elder="Badger",
        tags={"machine", "stream"},
    ),
    "mill_stump": Setting(
        id="mill_stump",
        place="a dry stump-house near the windy ridge",
        opening="Near Windy Ridge, the little animals used a stump-house to keep food safe from rain.",
        machine="a berry lift with a reed wheel",
        loft="the round shelf inside the stump-house",
        air="A fresh gust hurried over the ridge and rustled every leaf.",
        noise=2,
        elder="Badger",
        tags={"machine", "wind"},
    ),
}

HOARDS = {
    "acorns": Hoard(
        id="acorns",
        label="acorn sack",
        phrase="a bulging acorn sack",
        plural=False,
        weight=1,
        spill_text="acorns began pattering toward the brook",
        share_text="acorns for everyone to sort",
        tags={"acorn", "food"},
    ),
    "berries": Hoard(
        id="berries",
        label="berry basket",
        phrase="a berry basket tied with grass string",
        plural=False,
        weight=1,
        spill_text="berries began bouncing and rolling over the floorboards",
        share_text="berries for everyone to dry",
        tags={"berry", "food"},
    ),
    "chestnuts": Hoard(
        id="chestnuts",
        label="chestnut bundle",
        phrase="a heavy chestnut bundle",
        plural=False,
        weight=2,
        spill_text="chestnuts thumped against the boards and toward the edge",
        share_text="chestnuts for everyone to stack",
        tags={"chestnut", "food"},
    ),
}

SNAGS = {
    "twig": Snag(
        id="twig",
        label="twig",
        phrase="a crooked twig",
        severity=1,
        shape="loose",
        tags={"twig"},
    ),
    "vine": Snag(
        id="vine",
        label="vine",
        phrase="a bramble vine",
        severity=2,
        shape="wrapped",
        tags={"vine"},
    ),
    "ribbon_grass": Snag(
        id="ribbon_grass",
        label="grass ribbon",
        phrase="a long ribbon of marsh grass",
        severity=1,
        shape="loose",
        tags={"grass"},
    ),
}

RESPONSES = {
    "brake_rope": Response(
        id="brake_rope",
        sense=3,
        power=3,
        works_on={"loose", "wrapped"},
        text="leaped to the side post, seized the brake rope, and pulled until the wheel slowed to a stop",
        fail="pulled the brake rope, but the wheel had spun too wildly and food had already spilled away",
        qa_text="pulled the brake rope and stopped the wheel",
        tags={"brake", "machine"},
    ),
    "hook_pole": Response(
        id="hook_pole",
        sense=3,
        power=2,
        works_on={"loose"},
        text="caught the snag with a long hook-pole and tugged the load free while the wheel slowed",
        fail="reached with the hook-pole, but the snag held too tightly and food spilled before the load came free",
        qa_text="used a hook-pole to free the snag",
        tags={"pole", "machine"},
    ),
    "paws": Response(
        id="paws",
        sense=1,
        power=1,
        works_on={"loose"},
        text="grabbed at the spinning load with bare paws",
        fail="grabbed at the spinning load with bare paws and only made the tearing worse",
        qa_text="grabbed at the spinning load with bare paws",
        tags={"unsafe"},
    ),
}

ANIMALS = [
    ("Pip", "mouse"),
    ("Moss", "mouse"),
    ("Nim", "squirrel"),
    ("Hazel", "squirrel"),
    ("Brindle", "rabbit"),
    ("Fern", "rabbit"),
    ("Tansy", "hedgehog"),
    ("Bram", "hedgehog"),
]

HELPER_TRAITS = {
    "brave": 3,
    "steady": 2,
    "shy": 1,
    "gentle": 2,
}
HELPER_TRAIT_ORDER = ["brave", "steady", "shy", "gentle"]


def method_compatible(response: Response, snag: Snag) -> bool:
    return snag.shape in response.works_on


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(hoard: Hoard, snag: Snag) -> int:
    return hoard.weight + snag.severity


def courage_delay(setting: Setting, helper_trait: str) -> int:
    courage = HELPER_TRAITS[helper_trait]
    return 0 if courage >= setting.noise else 1


def contained(setting: Setting, hoard: Hoard, snag: Snag, helper_trait: str, response: Response) -> bool:
    if not method_compatible(response, snag):
        return False
    return response.power >= severity_of(hoard, snag) + courage_delay(setting, helper_trait)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for hoard_id in HOARDS:
            for snag_id in SNAGS:
                if any(method_compatible(r, SNAGS[snag_id]) for r in sensible_responses()):
                    combos.append((setting_id, hoard_id, snag_id))
    return combos


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    load = sim.get("load")
    wheel = sim.get("wheel")
    load.meters["snagged"] += 1
    wheel.meters["spinning"] += 1
    propagate(sim, narrate=False)
    return {
        "danger": wheel.meters["danger"],
        "torn": load.meters["torn"],
    }


def introduce(world: World, keeper: Entity, helper: Entity, hoard: Hoard) -> None:
    world.say(world.setting.opening)
    world.say(
        f"{keeper.id} the {keeper.type} had filled {hoard.phrase}, and {helper.id} the "
        f"{helper.type} had come carrying a much smaller bundle."
    )
    world.say(world.setting.air)
    world.say(
        f"In the middle stood {world.setting.machine}. Whenever the wind caught it, "
        f"it made a soft whir, whir, whir."
    )


def refuse_share(world: World, keeper: Entity, helper: Entity, hoard: Hoard) -> None:
    keeper.memes["stinginess"] += 1
    helper.memes["hope"] += 1
    world.say(
        f'"May I send my little bundle up after you?" asked {helper.id}.'
    )
    world.say(
        f'{keeper.id} hugged the {hoard.label} to {keeper.pronoun("possessive")} chest. '
        f'"No," {keeper.pronoun()} said. "The lift is mine this morning. I worked early, '
        f"and I do not want anyone touching my {hoard.share_text}."
    )
    world.say(
        f"{helper.id} lowered {helper.pronoun('possessive')} ears but stayed nearby."
    )


def start_trouble(world: World, keeper: Entity, hoard: Hoard, snag: Snag) -> None:
    wheel = world.get("wheel")
    load = world.get("load")
    load.meters["snagged"] += 1
    wheel.meters["spinning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a gust puffed through {world.setting.place}, and the wheel spun faster. "
        f"The load bumped the side beam, and {snag.phrase} caught in the turning spokes."
    )
    world.say(
        f'The wheel sang louder -- whirrr! -- and the {hoard.label} jerked in the air.'
    )


def danger_beat(world: World, keeper: Entity, helper: Entity, hoard: Hoard) -> None:
    if world.get("wheel").meters["danger"] >= THRESHOLD:
        keeper.memes["fear"] += 0
        helper.memes["fear"] += 0
    world.say(
        f'"Oh no!" cried {keeper.id}. "My {hoard.label}!"'
    )
    world.say(
        f"{helper.id} saw the knot stretching wider and wider, and {hoard.spill_text}."
    )


def hesitate_or_act(world: World, helper: Entity, helper_trait: str) -> int:
    delay = courage_delay(world.setting, helper_trait)
    if delay == 0:
        helper.memes["courage"] += 1
        world.say(
            f"{helper.id} felt a flutter of fear at the noisy wheel, but courage held "
            f"{helper.pronoun('possessive')} feet steady."
        )
    else:
        helper.memes["fear"] += 1
        helper.memes["courage"] += 1
        world.say(
            f"{helper.id} jumped back at the sharp whir and called, "
            f'"{world.setting.elder}! The lift is tearing!"'
        )
        world.say(
            f"No grown-up was close enough to reach the post in time. {helper.id} took one "
            f"deep breath, found some courage, and ran forward anyway."
        )
    return delay


def rescue_success(world: World, helper: Entity, keeper: Entity, response: Response, hoard: Hoard) -> None:
    wheel = world.get("wheel")
    load = world.get("load")
    wheel.meters["spinning"] = 0.0
    wheel.meters["danger"] = 0.0
    load.meters["saved"] += 1
    world.say(
        f"{helper.id} {response.text}."
    )
    world.say(
        f"The awful shaking stopped. Only a few crumbs fell, and the {hoard.label} swung gently again."
    )
    keeper.memes["relief"] += 1
    helper.memes["relief"] += 1


def rescue_fail(world: World, helper: Entity, keeper: Entity, response: Response, hoard: Hoard) -> None:
    wheel = world.get("wheel")
    load = world.get("load")
    wheel.meters["spinning"] = 0.0
    load.meters["spilled"] += 1
    load.meters["saved"] += 0
    world.say(
        f"{helper.id} {response.fail}."
    )
    world.say(
        f"When the wheel finally stopped, part of the {hoard.label} was safe, but much of it had spilled away."
    )
    keeper.memes["sadness"] += 1
    helper.memes["sadness"] += 1


def lesson(world: World, keeper: Entity, helper: Entity, hoard: Hoard, outcome: str) -> None:
    keeper.memes["regret"] += 1
    keeper.memes["sharing"] += 1
    helper.memes["trust"] += 1
    if outcome == "saved":
        world.say(
            f"{keeper.id} climbed down slowly and looked at {helper.id}. "
            f'"You helped me even after I was stingy," {keeper.pronoun()} said.'
        )
    else:
        world.say(
            f"{keeper.id} stared at the scattered food, then at {helper.id}. "
            f'"You still tried to help me, even after I was stingy," {keeper.pronoun()} said.'
        )
    world.say(
        f'"I was afraid too," said {helper.id}, "but courage is not keeping everything for yourself. '
        f'It is doing the right thing when someone needs help."'
    )
    world.say(
        f'{keeper.id} nodded. "Then I will do the right thing now. From today on, the lift will be shared."'
    )
    if outcome == "saved":
        world.say(
            f"Together they carried the {hoard.label} to {world.setting.loft}, and then {keeper.id} waved the next animals forward."
        )
    else:
        world.say(
            f"Together they gathered what was left, and {keeper.id} waved the next animals forward to use the lift before any more could be lost."
        )


def ending(world: World, keeper: Entity, helper: Entity, hoard: Hoard, outcome: str) -> None:
    keeper.memes["joy"] += 1
    helper.memes["joy"] += 1
    if outcome == "saved":
        world.say(
            f"Soon the loft held not only {keeper.id}'s food, but everyone's little bundles too. "
            f"The wheel still went whir in the wind, but now it sounded like a friendly song."
        )
    else:
        world.say(
            f"By sunset the shelf was lighter than it should have been, yet the hollow felt warmer than before, "
            f"because the animals worked side by side and shared what remained."
        )
    world.say(
        f"And whenever the wheel went whir after that, {keeper.id} remembered that sharing makes a winter store stronger, "
        f"and {helper.id} remembered the day courage turned fear into help."
    )
@dataclass
class StoryParams:
    setting: str
    hoard: str
    snag: str
    response: str
    keeper_name: str
    keeper_type: str
    helper_name: str
    helper_type: str
    helper_trait: str
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
    "whir": [
        (
            "What does whir mean?",
            "Whir is the soft fast sound something makes when it spins around, like a wheel or fan. It often means the thing is moving quickly."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in a group?",
            "Sharing helps everyone use what they need, and it keeps one animal from having too much while another has too little. It also makes friends trust one another."
        )
    ],
    "courage": [
        (
            "What is courage?",
            "Courage means doing the right thing even when you feel afraid. It does not mean you have no fear; it means you do not let fear stop your kind choice."
        )
    ],
    "machine": [
        (
            "Why should you be careful around a spinning wheel?",
            "A spinning wheel moves quickly, so loose things can get caught in it. That is why it is safer to stop it with the proper handle or rope than to grab it with your paws."
        )
    ],
    "brake": [
        (
            "What does a brake do?",
            "A brake slows something down or stops it. On a wheel, a brake helps make the moving parts safe again."
        )
    ],
    "pole": [
        (
            "Why might a long pole be safer than bare paws?",
            "A long pole lets you reach from farther away, so you do not have to put your body right next to the moving part. Distance can make a rescue safer."
        )
    ],
    "food": [
        (
            "Why do animals save food for winter?",
            "Many animals store food because winter can be cold and hard, with less fresh food to find. Saving food early helps them stay fed later."
        )
    ],
}

KNOWLEDGE_ORDER = ["whir", "sharing", "courage", "machine", "brake", "pole", "food"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    keeper = f["keeper"]
    helper = f["helper"]
    hoard = f["hoard"]
    return [
        'Write an Animal Story for a 3-to-5-year-old that includes the words "stingy", "whir", and "courage".',
        f"Tell a woodland story where {keeper.id} is stingy about {hoard.label}, but {helper.id} shows courage when trouble starts at a whirring lift.",
        "Write a gentle moral story with dialogue where a selfish choice causes a problem, a brave helper acts kindly, and the ending teaches sharing.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    keeper = f["keeper"]
    helper = f["helper"]
    hoard = f["hoard"]
    response = f["response"]
    snag = f["snag"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {keeper.id} the {keeper.type} and {helper.id} the {helper.type}. They were together at {setting.place} where the animals kept winter food."
        ),
        (
            f"Why did {keeper.id} seem stingy at the beginning?",
            f"{keeper.id} would not let {helper.id} use the lift after the big load went up. {keeper.pronoun('subject').capitalize()} wanted the machine and the food to be only for {keeper.pronoun('object')}."
        ),
        (
            "What made the problem start?",
            f"A gust made the wheel spin faster, and {snag.phrase} caught in the spokes. Because the wheel kept going whir, the {hoard.label} began to jerk and tear."
        ),
        (
            f"How did {helper.id} show courage?",
            f"{helper.id} was frightened by the loud wheel, but still moved in to help. {helper.pronoun('subject').capitalize()} chose a careful way to act instead of running away."
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How was the food saved?",
                f"{helper.id} {response.qa_text}. That stopped the danger before more than a few bits fell, so the winter food stayed safe."
            )
        )
    else:
        qa.append(
            (
                "Did all the food stay safe?",
                f"No. {helper.id} tried to help, but part of the {hoard.label} spilled before the wheel stopped. Even so, the rescue still mattered because it kept the whole load from being lost."
            )
        )
    qa.append(
        (
            "What lesson did the characters learn at the end?",
            f"{keeper.id} learned that being stingy leaves others out and can leave you alone when trouble comes. {helper.id} showed that courage and kindness make a group stronger, so the lift became something everyone shared."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"whir", "sharing", "courage", "machine", "food"}
    response = world.facts["response"]
    if response.id == "brake_rope":
        tags.add("brake")
    if response.id == "hook_pole":
        tags.add("pole")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is below the common-sense floor "
        f"(sense={r.sense} < {SENSE_MIN}). A child-facing story should prefer a safer method. "
        f"Try: {better}.)"
    )


def explain_rejection_combo(snag: Snag) -> str:
    return (
        f"(No story: none of the sensible rescue methods can handle a snag shaped like {snag.label}. "
        f"This world only tells problems that have a reasonable fix.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.setting not in SETTINGS or params.hoard not in HOARDS or params.snag not in SNAGS or params.response not in RESPONSES:
        raise StoryError("(Invalid params for outcome.)")
    return "saved" if contained(
        SETTINGS[params.setting],
        HOARDS[params.hoard],
        SNAGS[params.snag],
        params.helper_trait,
        RESPONSES[params.response],
    ) else "spilled"


ASP_RULES = r"""
% --- gate ------------------------------------------------------------------
works_on_shape(R,S) :- response(R), shape(S), method_works_on(R,S).
sensible(R)         :- response(R), sense(R, N), sense_min(M), N >= M.
fix_exists(Sg)      :- snag(Sg), snag_shape(Sg, S), works_on_shape(R, S), sensible(R).
valid(St,H,Sg)      :- setting(St), hoard(H), snag(Sg), fix_exists(Sg).

% --- outcome ---------------------------------------------------------------
courage_delay(0) :- chosen_setting(St), helper_trait(T), noise(St, N), courage(T, C), C >= N.
courage_delay(1) :- chosen_setting(St), helper_trait(T), noise(St, N), courage(T, C), C < N.

severity(W + S) :- chosen_hoard(H), chosen_snag(Sg), weight(H, W), snag_severity(Sg, S).
compatible      :- chosen_response(R), chosen_snag(Sg), snag_shape(Sg, Sh), method_works_on(R, Sh).
contained       :- compatible, chosen_response(R), power(R, P), severity(V), courage_delay(D), P >= V + D.

outcome(saved)   :- contained.
outcome(spilled) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("noise", setting_id, setting.noise))
    for hoard_id, hoard in HOARDS.items():
        lines.append(asp.fact("hoard", hoard_id))
        lines.append(asp.fact("weight", hoard_id, hoard.weight))
    lines.append(asp.fact("shape", "loose"))
    lines.append(asp.fact("shape", "wrapped"))
    for snag_id, snag in SNAGS.items():
        lines.append(asp.fact("snag", snag_id))
        lines.append(asp.fact("snag_severity", snag_id, snag.severity))
        lines.append(asp.fact("snag_shape", snag_id, snag.shape))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for shape in sorted(response.works_on):
            lines.append(asp.fact("method_works_on", response_id, shape))
    for trait, value in HELPER_TRAITS.items():
        lines.append(asp.fact("helper_trait_name", trait))
        lines.append(asp.fact("courage", trait, value))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_hoard", params.hoard),
            asp.fact("chosen_snag", params.snag),
            asp.fact("chosen_response", params.response),
            asp.fact("helper_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="oak_hollow",
        hoard="acorns",
        snag="twig",
        response="hook_pole",
        keeper_name="Nim",
        keeper_type="squirrel",
        helper_name="Fern",
        helper_type="rabbit",
        helper_trait="brave",
        seed=1,
    ),
    StoryParams(
        setting="pine_bank",
        hoard="chestnuts",
        snag="vine",
        response="brake_rope",
        keeper_name="Hazel",
        keeper_type="squirrel",
        helper_name="Tansy",
        helper_type="hedgehog",
        helper_trait="steady",
        seed=2,
    ),
    StoryParams(
        setting="mill_stump",
        hoard="berries",
        snag="vine",
        response="hook_pole",
        keeper_name="Nim",
        keeper_type="squirrel",
        helper_name="Pip",
        helper_type="mouse",
        helper_trait="shy",
        seed=3,
    ),
    StoryParams(
        setting="pine_bank",
        hoard="berries",
        snag="ribbon_grass",
        response="hook_pole",
        keeper_name="Hazel",
        keeper_type="squirrel",
        helper_name="Brindle",
        helper_type="rabbit",
        helper_trait="gentle",
        seed=4,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a stingy animal, a whirring lift, and courage that leads to sharing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hoard", choices=HOARDS)
    ap.add_argument("--snag", choices=SNAGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--keeper-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--keeper-type", choices=["squirrel", "rabbit", "hedgehog", "mouse"])
    ap.add_argument("--helper-type", choices=["squirrel", "rabbit", "hedgehog", "mouse"])
    ap.add_argument("--helper-trait", choices=HELPER_TRAIT_ORDER)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (setting, hoard, snag) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_animal(rng: random.Random, avoid_name: str = "") -> tuple[str, str]:
    pool = [pair for pair in ANIMALS if pair[0] != avoid_name]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection_response(args.response))
    if args.snag and not any(method_compatible(r, SNAGS[args.snag]) for r in sensible_responses()):
        raise StoryError(explain_rejection_combo(SNAGS[args.snag]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hoard is None or combo[1] == args.hoard)
        and (args.snag is None or combo[2] == args.snag)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hoard_id, snag_id = rng.choice(sorted(combos))
    snag = SNAGS[snag_id]

    response_choices = [
        response_id
        for response_id, response in RESPONSES.items()
        if response.sense >= SENSE_MIN and method_compatible(response, snag)
        and (args.response is None or response_id == args.response)
    ]
    if not response_choices:
        raise StoryError("(No sensible response matches the chosen snag.)")

    keeper_name, keeper_type = (args.keeper_name, args.keeper_type) if args.keeper_name and args.keeper_type else pick_animal(rng)
    if args.keeper_name and not args.keeper_type:
        keeper_type = rng.choice(["squirrel", "rabbit", "hedgehog", "mouse"])
    if args.keeper_type and not args.keeper_name:
        keeper_name, _ = pick_animal(rng)
        keeper_type = args.keeper_type

    helper_name, helper_type = pick_animal(rng, avoid_name=keeper_name or "")
    if args.helper_name:
        helper_name = args.helper_name
    if args.helper_type:
        helper_type = args.helper_type
    if helper_name == keeper_name:
        helper_name, helper_type = pick_animal(rng, avoid_name=keeper_name)

    return StoryParams(
        setting=setting_id,
        hoard=hoard_id,
        snag=snag_id,
        response=args.response or rng.choice(sorted(response_choices)),
        keeper_name=keeper_name,
        keeper_type=keeper_type,
        helper_name=helper_name,
        helper_type=helper_type,
        helper_trait=args.helper_trait or rng.choice(HELPER_TRAIT_ORDER),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.hoard not in HOARDS:
        raise StoryError(f"(Unknown hoard: {params.hoard})")
    if params.snag not in SNAGS:
        raise StoryError(f"(Unknown snag: {params.snag})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.helper_trait not in HELPER_TRAITS:
        raise StoryError(f"(Unknown helper trait: {params.helper_trait})")

    response = RESPONSES[params.response]
    snag = SNAGS[params.snag]
    if response.sense < SENSE_MIN:
        raise StoryError(explain_rejection_response(params.response))
    if not method_compatible(response, snag):
        raise StoryError(
            f"(No story: the response '{params.response}' does not fit a {snag.label} snag. Pick a method that matches the kind of snag.)"
        )

    world = tell(
        setting=SETTINGS[params.setting],
        hoard=HOARDS[params.hoard],
        snag=snag,
        response=response,
        keeper_name=params.keeper_name,
        keeper_type=params.keeper_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        helper_trait=params.helper_trait,
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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, hoard, snag) combos:\n")
        for setting_id, hoard_id, snag_id in combos:
            print(f"  {setting_id:11} {hoard_id:10} {snag_id}")
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
            header = f"### {p.keeper_name} & {p.helper_name}: {p.hoard} at {p.setting} ({p.snag}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    hoard: Hoard,
    snag: Snag,
    response: Response,
    keeper_name: str = "Nim",
    keeper_type: str = "squirrel",
    helper_name: str = "Fern",
    helper_type: str = "rabbit",
    helper_trait: str = "brave",
) -> World:
    world = World(setting)
    keeper = world.add(
        Entity(
            id=keeper_name,
            kind="character",
            type=keeper_type,
            role="keeper",
            traits=["stingy"],
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            traits=[helper_trait],
            attrs={},
        )
    )
    world.add(
        Entity(
            id="wheel",
            kind="thing",
            type="machine",
            label=setting.machine,
            attrs={},
        )
    )
    world.add(
        Entity(
            id="load",
            kind="thing",
            type="food",
            label=hoard.label,
            attrs={},
        )
    )

    world.facts["predicted_danger"] = 0
    world.facts["predicted_torn"] = 0

    introduce(world, keeper, helper, hoard)
    world.para()
    refuse_share(world, keeper, helper, hoard)

    world.para()
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_torn"] = pred["torn"]
    start_trouble(world, keeper, hoard, snag)
    danger_beat(world, keeper, helper, hoard)

    world.para()
    delay = hesitate_or_act(world, helper, helper_trait)
    if contained(setting, hoard, snag, helper_trait, response):
        rescue_success(world, helper, keeper, response, hoard)
        outcome = "saved"
    else:
        rescue_fail(world, helper, keeper, response, hoard)
        outcome = "spilled"

    world.para()
    lesson(world, keeper, helper, hoard, outcome)
    ending(world, keeper, helper, hoard, outcome)

    world.facts.update(
        setting=setting,
        hoard=hoard,
        snag=snag,
        response=response,
        keeper=keeper,
        helper=helper,
        helper_trait=helper_trait,
        delay=delay,
        outcome=outcome,
        predicted=pred,
        shared=True,
    )
    return world

if __name__ == "__main__":
    main()
