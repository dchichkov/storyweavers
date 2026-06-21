#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py
===========================================================================================

A standalone story world for a small animal tale about **custard, a bloom, a
balloon, bravery, and a misunderstanding**.

Premise
-------
Two young animals are carrying a custard treat to admire a special garden bloom.
A loose balloon drifts near the flower. One child misunderstands what it is and
fears it will hurt the bloom. The other child shows bravery by looking closely
and helping carefully instead of running away from the scary idea. The ending
proves what changed: the misunderstanding clears, the bloom is safe, and the
animals understand that brave hearts look carefully before they decide.

Run it
------
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py --balloon round_yellow --misread bee
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py --balloon star_blue --misread bee
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py --response jump_grab
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/custard_bloom_balloon_bravery_misunderstanding_animal_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"rabbit_girl", "mouse_girl", "duck_girl", "squirrel_girl", "mother", "aunt"}
        male = {"rabbit_boy", "mouse_boy", "duck_boy", "squirrel_boy", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
    detail: str
    sound: str
    owner_spot: str
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
class Bloom:
    id: str
    label: str
    color: str
    patch: str
    fragility: int
    nectar_rich: bool
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
class Treat:
    id: str
    label: str
    phrase: str
    share_line: str
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
class Balloon:
    id: str
    label: str
    color: str
    shape: str
    ribbon: str
    drift: str
    float_height: int
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
class Misread:
    id: str
    label: str
    fear_line: str
    reveal_line: str
    need_color: str = ""
    need_shape: str = ""
    need_nectar: bool = False
    need_fragile_max: int = 99
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
class Response:
    id: str
    sense: int
    care: int
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


def _r_scare(world: World) -> list[str]:
    balloon = world.get("balloon")
    bloom = world.get("bloom")
    watcher = world.get("watcher")
    helper = world.get("helper")
    if watcher.memes["misunderstanding"] < THRESHOLD:
        return []
    sig = ("scare",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["fear"] += 1
    helper.memes["concern"] += 1
    balloon.meters["suspected_danger"] += 1
    bloom.meters["risk"] += 1
    return []


def _r_tangle(world: World) -> list[str]:
    balloon = world.get("balloon")
    bloom = world.get("bloom")
    if balloon.meters["caught"] < THRESHOLD:
        return []
    sig = ("tangle",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bloom.meters["tugged"] += 1
    bloom.meters["risk"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    watcher = world.get("watcher")
    helper = world.get("helper")
    balloon = world.get("balloon")
    if balloon.meters["caught"] >= THRESHOLD:
        return []
    if watcher.memes["understanding"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    watcher.memes["fear"] = 0.0
    watcher.memes["relief"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="scare", tag="emotional", apply=_r_scare),
    Rule(name="tangle", tag="physical", apply=_r_tangle),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def misunderstanding_plausible(balloon: Balloon, misread: Misread, bloom: Bloom) -> bool:
    if misread.need_color and balloon.color != misread.need_color:
        return False
    if misread.need_shape and balloon.shape != misread.need_shape:
        return False
    if misread.need_nectar and not bloom.nectar_rich:
        return False
    if bloom.fragility > misread.need_fragile_max:
        return False
    return True


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def strain_level(balloon: Balloon) -> int:
    return balloon.float_height


def bloom_stays_safe(response: Response, balloon: Balloon) -> bool:
    return response.care >= strain_level(balloon)


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("watcher").memes["misunderstanding"] += 1
    sim.get("balloon").meters["caught"] += 1
    propagate(sim, narrate=False)
    return {
        "risk": sim.get("bloom").meters["risk"],
        "fear": sim.get("watcher").memes["fear"],
        "caught": sim.get("balloon").meters["caught"],
    }


def introduce(world: World, watcher: Entity, helper: Entity, grownup: Entity,
              place: Place, treat: Treat, bloom: Bloom) -> None:
    watcher.memes["wonder"] += 1
    helper.memes["wonder"] += 1
    world.say(
        f"In {place.label}, where {place.detail}, {watcher.id} and {helper.id} padded along with "
        f"{treat.phrase}. They were going to sit by {bloom.patch} and watch the first {bloom.color} "
        f"{bloom.label} bloom of the morning."
    )
    world.say(
        f"The path smelled sweet, and {place.sound}. {grownup.id}'s basket still felt warm from the kitchen."
    )


def settle(world: World, watcher: Entity, helper: Entity, treat: Treat, bloom: Bloom) -> None:
    world.say(
        f'"Let us eat the {treat.label} after we greet the bloom," said {helper.id}. '
        f'{watcher.id} nodded and held the plate very carefully.'
    )


def drift_in(world: World, balloon: Balloon, bloom: Bloom) -> None:
    balloon_ent = world.get("balloon")
    balloon_ent.meters["caught"] += 1
    bloom_ent = world.get("bloom")
    bloom_ent.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, a {balloon.label} came drifting over the hedge. Its {balloon.ribbon} ribbon trailed low, "
        f"and soon it caught against the stem beside the {bloom.label} bloom."
    )


def misunderstand(world: World, watcher: Entity, helper: Entity, misread: Misread) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred["risk"]
    world.facts["predicted_fear"] = pred["fear"]
    watcher.memes["misunderstanding"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{watcher.id} stopped so fast that the little spoon on the custard plate rattled. '
        f'"Oh!" {watcher.pronoun()} whispered. "{misread.fear_line}"'
    )
    extra = ""
    if pred["risk"] >= THRESHOLD:
        extra = f" {watcher.pronoun().capitalize()} was sure the poor bloom would be tugged and torn."
    world.say(
        f"{helper.id} looked where {watcher.pronoun()} was pointing.{extra}"
    )


def brave_choice(world: World, helper: Entity, watcher: Entity) -> None:
    helper.memes["bravery"] += 1
    watcher.memes["trust"] += 1
    world.say(
        f'"Stay behind me if you like," said {helper.id}, though {helper.pronoun()} kept {helper.pronoun("possessive")} voice soft. '
        f'"Brave does not mean rushing. Brave means looking carefully first."'
    )


def approach(world: World, helper: Entity, balloon: Balloon, response: Response) -> None:
    world.say(
        f"{helper.id} stepped closer while the {balloon.label} bobbed and {balloon.drift}. "
        f"{helper.pronoun().capitalize()} {response.text}."
    )


def reveal(world: World, helper: Entity, watcher: Entity, misread: Misread, balloon: Balloon) -> None:
    watcher.memes["understanding"] += 1
    watcher.memes["misunderstanding"] = 0.0
    world.say(
        f'"Wait," called {helper.id}. "{misread.reveal_line}" It was only a {balloon.label}, shivering in the breeze.'
    )
    world.say(
        f"{watcher.id} blinked, then blinked again. The scary shape was not a danger at all, only a balloon in the wrong place."
    )


def free_balloon(world: World, helper: Entity, watcher: Entity, grownup: Entity,
                 balloon: Balloon, treat: Treat) -> None:
    balloon_ent = world.get("balloon")
    balloon_ent.meters["caught"] = 0.0
    balloon_ent.meters["freed"] += 1
    world.get("bloom").meters["risk"] = 0.0
    world.get("bloom").meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In another moment, {helper.id} loosened the ribbon and let the stem spring back straight. "
        f'The bloom gave one small nod, safe again.'
    )
    owner = world.facts.get("owner_name", "a small mole")
    world.say(
        f"From {grownup.attrs.get('owner_spot', 'the gate')} came a wobbly little voice. "
        f'"My balloon!" cried {owner}. {watcher.id} carried it over, and the worried face lit right up.'
    )
    world.say(
        f"Then the two friends sat in the grass at last and shared the {treat.label}. {treat.share_line}"
    )


def rough_fail(world: World, helper: Entity, watcher: Entity, grownup: Entity,
               balloon: Balloon, misread: Misread, treat: Treat, response: Response) -> None:
    bloom_ent = world.get("bloom")
    balloon_ent = world.get("balloon")
    balloon_ent.meters["caught"] = 0.0
    balloon_ent.meters["popped"] += 1
    bloom_ent.meters["bent"] += 1
    bloom_ent.meters["safe"] += 1
    watcher.memes["understanding"] += 1
    watcher.memes["misunderstanding"] = 0.0
    propagate(world, narrate=False)
    owner = world.facts.get("owner_name", "a small mole")
    world.say(
        f"But the first try was too hasty. {response.fail} The balloon gave a loud pop, and the bloom bent low before slowly lifting again."
    )
    world.say(
        f'"It was only a balloon," said {helper.id} sadly. "{misread.reveal_line}" {watcher.id} hurried to steady the stem with both paws.'
    )
    world.say(
        f"{grownup.id} came over and gently tied a soft leaf around the stem to help it stand. "
        f'Nearby, {owner} sniffled at the lost balloon, so {watcher.id} offered the first spoonful of {treat.label} to share.'
    )
    world.say(
        f"The bloom was not broken, only shaken, and the friends learned that brave hearts must be gentle as well as bold."
    )


def tell(place: Place, bloom: Bloom, treat: Treat, balloon: Balloon, misread: Misread,
         response: Response, watcher_name: str = "Pip", watcher_type: str = "rabbit_boy",
         helper_name: str = "Mara", helper_type: str = "mouse_girl",
         grownup_type: str = "aunt") -> World:
    world = World()
    watcher = world.add(Entity(
        id=watcher_name,
        kind="character",
        type=watcher_type,
        role="watcher",
        traits=["tender", "jumpy"],
        attrs={},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        traits=["steady", "kind"],
        attrs={},
    ))
    grownup = world.add(Entity(
        id=grownup_type.capitalize(),
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the grown-up",
        attrs={"owner_spot": place.owner_spot},
    ))
    world.add(Entity(
        id="bloom",
        kind="thing",
        type="flower",
        label=bloom.label,
        attrs={"color": bloom.color},
    ))
    world.add(Entity(
        id="balloon",
        kind="thing",
        type="balloon",
        label=balloon.label,
        attrs={"shape": balloon.shape, "color": balloon.color},
    ))
    world.add(Entity(
        id="plate",
        kind="thing",
        type="plate",
        label=treat.label,
        attrs={},
    ))

    world.facts["owner_name"] = random.choice(["a small mole", "a young hedgehog", "a duckling from the lane"])

    introduce(world, watcher, helper, grownup, place, treat, bloom)
    settle(world, watcher, helper, treat, bloom)

    world.para()
    drift_in(world, balloon, bloom)
    misunderstand(world, watcher, helper, misread)
    brave_choice(world, helper, watcher)

    world.para()
    approach(world, helper, balloon, response)
    reveal(world, helper, watcher, misread, balloon)

    safe = bloom_stays_safe(response, balloon)
    world.para()
    if safe:
        free_balloon(world, helper, watcher, grownup, balloon, treat)
        outcome = "safe"
    else:
        rough_fail(world, helper, watcher, grownup, balloon, misread, treat, response)
        outcome = "shaken"

    world.facts.update(
        place=place,
        bloom_cfg=bloom,
        treat=treat,
        balloon_cfg=balloon,
        misread=misread,
        response=response,
        watcher=watcher,
        helper=helper,
        grownup=grownup,
        outcome=outcome,
        balloon_freed=world.get("balloon").meters["freed"] >= THRESHOLD,
        balloon_popped=world.get("balloon").meters["popped"] >= THRESHOLD,
        bloom_safe=world.get("bloom").meters["safe"] >= THRESHOLD,
    )
    return world


PLACES = {
    "garden": Place(
        id="garden",
        label="the garden behind the burrow",
        detail="pea leaves climbed the fence and dew shone on the stones",
        sound="bees hummed far off in the clover",
        owner_spot="the gate by the bean poles",
        tags={"garden"},
    ),
    "orchard": Place(
        id="orchard",
        label="the orchard path",
        detail="apple shadows lay in round patches and the grass smelled green",
        sound="a blackbird sang from a branch above",
        owner_spot="the old gate under the apple tree",
        tags={"orchard"},
    ),
    "meadow": Place(
        id="meadow",
        label="the meadow edge",
        detail="soft grass leaned under bright light and seed fluff sailed slowly",
        sound="the brook made tiny silver sounds nearby",
        owner_spot="the little bridge",
        tags={"meadow"},
    ),
}

BLOOMS = {
    "daisy": Bloom(
        id="daisy",
        label="daisy",
        color="white",
        patch="the daisy patch",
        fragility=1,
        nectar_rich=True,
        tags={"flower", "daisy"},
    ),
    "tulip": Bloom(
        id="tulip",
        label="tulip",
        color="red",
        patch="the tulip bed",
        fragility=2,
        nectar_rich=False,
        tags={"flower", "tulip"},
    ),
    "lily": Bloom(
        id="lily",
        label="lily",
        color="gold",
        patch="the lily bank",
        fragility=1,
        nectar_rich=True,
        tags={"flower", "lily"},
    ),
}

TREATS = {
    "custard_tart": Treat(
        id="custard_tart",
        label="custard tart",
        phrase="a round custard tart on a blue plate",
        share_line="The custard tasted sunny and calm, and not one spoonful had to be eaten in a hurry now.",
        tags={"custard"},
    ),
    "custard_bun": Treat(
        id="custard_bun",
        label="custard bun",
        phrase="a soft custard bun wrapped in a checked cloth",
        share_line="The custard was smooth and sweet, and even the quiet bites felt cheerful again.",
        tags={"custard"},
    ),
    "custard_cup": Treat(
        id="custard_cup",
        label="custard cup",
        phrase="a little custard cup with two tiny spoons",
        share_line="The custard was cool and silky, and it made the whole morning feel gentle after all.",
        tags={"custard"},
    ),
}

BALLOONS = {
    "round_yellow": Balloon(
        id="round_yellow",
        label="round yellow balloon",
        color="yellow",
        shape="round",
        ribbon="curly",
        drift="dipped and rose like a sleepy bobber",
        float_height=1,
        tags={"balloon", "yellow", "round"},
    ),
    "star_blue": Balloon(
        id="star_blue",
        label="blue star balloon",
        color="blue",
        shape="star",
        ribbon="silver",
        drift="twirled on its points and tugged at the air",
        float_height=2,
        tags={"balloon", "star"},
    ),
    "heart_red": Balloon(
        id="heart_red",
        label="red heart balloon",
        color="red",
        shape="heart",
        ribbon="pink",
        drift="rocked from side to side like a nodding leaf",
        float_height=1,
        tags={"balloon", "heart"},
    ),
}

MISREADS = {
    "bee": Misread(
        id="bee",
        label="giant bee",
        fear_line="A giant bee is hanging over the bloom!",
        reveal_line="That is no bee. It has no wings at all, only ribbon and shiny skin.",
        need_color="yellow",
        need_shape="round",
        need_nectar=True,
        tags={"bee", "misunderstanding"},
    ),
    "thorn_seed": Misread(
        id="thorn_seed",
        label="thorny sky-seed",
        fear_line="A thorny sky-seed will poke the bloom to pieces!",
        reveal_line="Those points are only soft folds in foil. Nothing sharp is there.",
        need_shape="star",
        need_fragile_max=2,
        tags={"seed", "misunderstanding"},
    ),
    "snatching_heart": Misread(
        id="snatching_heart",
        label="snatching kite-creature",
        fear_line="That fluttering thing will snatch the bloom away!",
        reveal_line="See how it only tugs where the ribbon is caught? It cannot snatch anything by itself.",
        need_shape="heart",
        need_fragile_max=2,
        tags={"kite", "misunderstanding"},
    ),
}

RESPONSES = {
    "paw_unloop": Response(
        id="paw_unloop",
        sense=3,
        care=2,
        text="reached up with one steady paw and began to ease the ribbon away from the stem",
        fail="The ribbon slipped the wrong way under one hurried tug",
        qa_text="eased the ribbon away with a steady paw",
        tags={"gentle_help"},
    ),
    "reed_hook": Response(
        id="reed_hook",
        sense=3,
        care=3,
        text="picked up a fallen reed and used its curved tip to lift the ribbon free",
        fail="The reed snagged the ribbon, then jerked too hard",
        qa_text="used a fallen reed to lift the ribbon free",
        tags={"tool_help"},
    ),
    "jump_grab": Response(
        id="jump_grab",
        sense=1,
        care=1,
        text="crouched at once, ready to leap and grab the ribbon in mid-bob",
        fail="The jump came too fast and the ribbon whipped against the stem",
        qa_text="jumped to grab the ribbon",
        tags={"rough_help"},
    ),
}

WATCHER_OPTIONS = [
    ("Pip", "rabbit_boy"),
    ("Nell", "mouse_girl"),
    ("Tavi", "duck_boy"),
    ("Mira", "squirrel_girl"),
]
HELPER_OPTIONS = [
    ("Fern", "rabbit_girl"),
    ("Odo", "mouse_boy"),
    ("Wren", "duck_girl"),
    ("Bram", "squirrel_boy"),
]


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for place_id in PLACES:
        for bloom_id, bloom in BLOOMS.items():
            for treat_id in TREATS:
                for balloon_id, balloon in BALLOONS.items():
                    for misread_id, misread in MISREADS.items():
                        if misunderstanding_plausible(balloon, misread, bloom):
                            combos.append((place_id, bloom_id, treat_id, balloon_id, misread_id))
    return combos


@dataclass
class StoryParams:
    place: str
    bloom: str
    treat: str
    balloon: str
    misread: str
    response: str
    watcher_name: str
    watcher_type: str
    helper_name: str
    helper_type: str
    grownup_type: str
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
    "custard": [
        (
            "What is custard?",
            "Custard is a soft, sweet food made to be smooth and creamy. People often eat it in tarts, buns, or little cups.",
        )
    ],
    "balloon": [
        (
            "Why does a balloon float?",
            "A balloon can float when it is filled with a gas lighter than air. Then the air around it pushes it upward.",
        )
    ],
    "flower": [
        (
            "What does it mean when a flower starts to bloom?",
            "When a flower starts to bloom, it begins to open. The petals unfold so the flower can show its full shape and color.",
        )
    ],
    "bee": [
        (
            "Why do bees visit flowers?",
            "Bees visit flowers to gather nectar and pollen. As they move from bloom to bloom, they also help many plants grow seeds.",
        )
    ],
    "gentle_help": [
        (
            "Why can gentle hands help a flower?",
            "A flower stem can bend or tear if someone yanks it. Gentle hands move slowly, so they are less likely to hurt it.",
        )
    ],
    "tool_help": [
        (
            "Why might a long tool help you reach something carefully?",
            "A longer tool can help you reach without pulling too close or too hard. That can make a careful rescue easier.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is true, but it is not. Looking carefully and asking questions can help clear it up.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is not only doing bold things. It can also mean staying calm, looking closely, and helping kindly when something feels scary.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "custard",
    "balloon",
    "flower",
    "bee",
    "gentle_help",
    "tool_help",
    "misunderstanding",
    "bravery",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    watcher = f["watcher"]
    helper = f["helper"]
    bloom = f["bloom_cfg"]
    treat = f["treat"]
    balloon = f["balloon_cfg"]
    misread = f["misread"]
    if f["outcome"] == "shaken":
        return [
            f'Write an animal story for a 3-to-5-year-old that includes the words "custard", "bloom", and "balloon". A child animal mistakes a {balloon.label} for {misread.label} and a brave friend tries to help.',
            f"Tell a gentle cautionary animal tale where {watcher.id} misunderstands what is near the {bloom.label} bloom, and {helper.id} learns that bravery must be gentle as well as bold.",
            f"Write a small animal story about a misunderstanding by a flower, a brave rescue, and a shared {treat.label} at the end.",
        ]
    return [
        f'Write an animal story for a 3-to-5-year-old that includes the words "custard", "bloom", and "balloon". One child animal is frightened by a misunderstanding, and another shows bravery by looking carefully.',
        f"Tell a tender animal tale where {watcher.id} thinks a {balloon.label} will hurt a {bloom.label} bloom, but {helper.id} discovers the truth and saves the flower.",
        f"Write a story in which a misunderstanding makes something ordinary seem scary, and the ending shows two friends sharing {treat.label} once the bloom is safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    watcher = f["watcher"]
    helper = f["helper"]
    grownup = f["grownup"]
    bloom = f["bloom_cfg"]
    treat = f["treat"]
    balloon = f["balloon_cfg"]
    misread = f["misread"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {watcher.id} and {helper.id}, two small animal friends, and {grownup.id} nearby. They were carrying {treat.label} to look at a special {bloom.label} bloom.",
        ),
        (
            "What caused the trouble in the story?",
            f"A {balloon.label} drifted close and its ribbon caught by the bloom. {watcher.id} misunderstood what {watcher.pronoun()} saw and thought it was {misread.label}, so the moment suddenly felt frightening.",
        ),
        (
            f"Why was {watcher.id} scared?",
            f"{watcher.id} thought the thing above the flower would hurt the bloom. Because the ribbon was tugging near the stem, the misunderstanding seemed real at first.",
        ),
        (
            f"How did {helper.id} show bravery?",
            f"{helper.id} did not laugh or run away. {helper.pronoun().capitalize()} went closer carefully to find out what was really there, because brave choices can begin with calm looking.",
        ),
    ]
    if f["outcome"] == "safe":
        qa.append(
            (
                f"How did {helper.id} save the bloom?",
                f"{helper.id} {response.qa_text}. That careful method freed the balloon without hurting the flower, so the stem could spring back safely.",
            )
        )
        qa.append(
            (
                "What was the misunderstanding?",
                f"The scary thing was not {misread.label} at all. It was only a {balloon.label} tangled in the wrong place, which is why everyone felt relief once they understood.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The bloom was safe, the lost balloon went back to its owner, and the friends sat down to share {treat.label}. The calm ending shows that understanding replaced fear.",
            )
        )
    else:
        qa.append(
            (
                f"Did the bloom get badly hurt?",
                f"No. The bloom was bent and shaken, but it was not broken. The trouble came from a hasty rescue, which taught the friends to be gentle as well as brave.",
            )
        )
        qa.append(
            (
                "What did the friends learn?",
                f"They learned that brave hearts should look carefully and move gently. The misunderstanding made them scared, and the rough first try showed that kindness and care matter too.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The bloom recovered, and even after the balloon popped, the friends shared {treat.label} and comforted the upset owner. The ending feels softer because they turned a mistake into kindness.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"custard", "balloon", "flower", "misunderstanding", "bravery"}
    tags |= set(f["misread"].tags)
    tags |= set(f["response"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden",
        bloom="lily",
        treat="custard_tart",
        balloon="round_yellow",
        misread="bee",
        response="paw_unloop",
        watcher_name="Pip",
        watcher_type="rabbit_boy",
        helper_name="Fern",
        helper_type="rabbit_girl",
        grownup_type="aunt",
    ),
    StoryParams(
        place="orchard",
        bloom="tulip",
        treat="custard_bun",
        balloon="star_blue",
        misread="thorn_seed",
        response="reed_hook",
        watcher_name="Nell",
        watcher_type="mouse_girl",
        helper_name="Bram",
        helper_type="squirrel_boy",
        grownup_type="uncle",
    ),
    StoryParams(
        place="meadow",
        bloom="daisy",
        treat="custard_cup",
        balloon="heart_red",
        misread="snatching_heart",
        response="paw_unloop",
        watcher_name="Mira",
        watcher_type="squirrel_girl",
        helper_name="Odo",
        helper_type="mouse_boy",
        grownup_type="mother",
    ),
    StoryParams(
        place="garden",
        bloom="tulip",
        treat="custard_tart",
        balloon="star_blue",
        misread="thorn_seed",
        response="jump_grab",
        watcher_name="Tavi",
        watcher_type="duck_boy",
        helper_name="Wren",
        helper_type="duck_girl",
        grownup_type="father",
    ),
]


def explain_combo_rejection(balloon: Balloon, misread: Misread, bloom: Bloom) -> str:
    reasons: list[str] = []
    if misread.need_color and balloon.color != misread.need_color:
        reasons.append(f"{misread.label} only fits a {misread.need_color} balloon")
    if misread.need_shape and balloon.shape != misread.need_shape:
        reasons.append(f"{misread.label} only fits a {misread.need_shape} shape")
    if misread.need_nectar and not bloom.nectar_rich:
        reasons.append(f"{bloom.label} is not the kind of nectar-rich bloom that makes this fear feel natural")
    if bloom.fragility > misread.need_fragile_max:
        reasons.append(f"{bloom.label} is too sturdy for that specific misunderstanding")
    if not reasons:
        reasons.append("that misunderstanding does not fit this balloon and bloom")
    return "(No story: " + "; ".join(reasons) + ".)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the gentler responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.balloon not in BALLOONS or params.response not in RESPONSES:
        raise StoryError("(No story: invalid balloon or response.)")
    return "safe" if bloom_stays_safe(RESPONSES[params.response], BALLOONS[params.balloon]) else "shaken"


ASP_RULES = r"""
valid(Place,Bloom,Treat,Balloon,Misread) :-
    place(Place), bloom(Bloom), treat(Treat), balloon(Balloon), misread(Misread),
    fits_color(Balloon,Misread), fits_shape(Balloon,Misread),
    fits_nectar(Bloom,Misread), fits_fragility(Bloom,Misread).

fits_color(Balloon,Misread) :- need_color(Misread, C), color(Balloon, C).
fits_color(_, Misread)      :- no_need_color(Misread).

fits_shape(Balloon,Misread) :- need_shape(Misread, S), shape(Balloon, S).
fits_shape(_, Misread)      :- no_need_shape(Misread).

fits_nectar(Bloom,Misread)  :- need_nectar(Misread), nectar_rich(Bloom).
fits_nectar(_, Misread)     :- no_need_nectar(Misread).

fits_fragility(Bloom,Misread) :- fragility(Bloom,F), fragile_max(Misread,M), F <= M.

sensible(Response) :- response(Response), sense(Response,S), sense_min(M), S >= M.
safe               :- chosen_balloon(B), chosen_response(R), float_height(B,H), care(R,C), C >= H.
outcome(safe)      :- safe.
outcome(shaken)    :- not safe.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for bid, bloom in BLOOMS.items():
        lines.append(asp.fact("bloom", bid))
        lines.append(asp.fact("fragility", bid, bloom.fragility))
        if bloom.nectar_rich:
            lines.append(asp.fact("nectar_rich", bid))
    for tid in TREATS:
        lines.append(asp.fact("treat", tid))
    for bid, balloon in BALLOONS.items():
        lines.append(asp.fact("balloon", bid))
        lines.append(asp.fact("color", bid, balloon.color))
        lines.append(asp.fact("shape", bid, balloon.shape))
        lines.append(asp.fact("float_height", bid, balloon.float_height))
    for mid, misread in MISREADS.items():
        lines.append(asp.fact("misread", mid))
        if misread.need_color:
            lines.append(asp.fact("need_color", mid, misread.need_color))
        else:
            lines.append(asp.fact("no_need_color", mid))
        if misread.need_shape:
            lines.append(asp.fact("need_shape", mid, misread.need_shape))
        else:
            lines.append(asp.fact("no_need_shape", mid))
        if misread.need_nectar:
            lines.append(asp.fact("need_nectar", mid))
        else:
            lines.append(asp.fact("no_need_nectar", mid))
        lines.append(asp.fact("fragile_max", mid, misread.need_fragile_max))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("care", rid, response.care))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_balloon", params.balloon),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid, p_valid = set(asp_valid_combos()), set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sensible, p_sensible = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sensible == p_sensible:
        print(f"OK: sensible responses match ({sorted(c_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sensible)} python={sorted(p_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed for seed {s}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal story world: a balloon near a bloom, a misunderstanding, and brave careful help."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--bloom", choices=BLOOMS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--balloon", choices=BALLOONS)
    ap.add_argument("--misread", choices=MISREADS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_pair(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    watcher = rng.choice(WATCHER_OPTIONS)
    helper_choices = [opt for opt in HELPER_OPTIONS if opt[0] != watcher[0]]
    helper = rng.choice(helper_choices)
    return watcher, helper


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.balloon and args.misread and args.bloom:
        balloon = BALLOONS[args.balloon]
        misread = MISREADS[args.misread]
        bloom = BLOOMS[args.bloom]
        if not misunderstanding_plausible(balloon, misread, bloom):
            raise StoryError(explain_combo_rejection(balloon, misread, bloom))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.bloom is None or c[1] == args.bloom)
        and (args.treat is None or c[2] == args.treat)
        and (args.balloon is None or c[3] == args.balloon)
        and (args.misread is None or c[4] == args.misread)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, bloom, treat, balloon, misread = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    watcher, helper = _pick_pair(rng)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        place=place,
        bloom=bloom,
        treat=treat,
        balloon=balloon,
        misread=misread,
        response=response,
        watcher_name=watcher[0],
        watcher_type=watcher[1],
        helper_name=helper[0],
        helper_type=helper[1],
        grownup_type=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if params.bloom not in BLOOMS:
        raise StoryError("(No story: unknown bloom.)")
    if params.treat not in TREATS:
        raise StoryError("(No story: unknown treat.)")
    if params.balloon not in BALLOONS:
        raise StoryError("(No story: unknown balloon.)")
    if params.misread not in MISREADS:
        raise StoryError("(No story: unknown misunderstanding.)")
    if params.response not in RESPONSES:
        raise StoryError("(No story: unknown response.)")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not misunderstanding_plausible(BALLOONS[params.balloon], MISREADS[params.misread], BLOOMS[params.bloom]):
        raise StoryError(explain_combo_rejection(BALLOONS[params.balloon], MISREADS[params.misread], BLOOMS[params.bloom]))

    if params.watcher_name == params.helper_name:
        raise StoryError("(No story: watcher and helper must be different animals.)")

    owner_seed = params.seed if params.seed is not None else 0
    random.seed(owner_seed)

    world = tell(
        place=PLACES[params.place],
        bloom=BLOOMS[params.bloom],
        treat=TREATS[params.treat],
        balloon=BALLOONS[params.balloon],
        misread=MISREADS[params.misread],
        response=RESPONSES[params.response],
        watcher_name=params.watcher_name,
        watcher_type=params.watcher_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        grownup_type=params.grownup_type,
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
        print(asp_program("", "#show valid/5.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, bloom, treat, balloon, misread) combos:\n")
        for place, bloom, treat, balloon, misread in combos:
            print(f"  {place:8} {bloom:6} {treat:12} {balloon:12} {misread}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.watcher_name} and {p.helper_name}: {p.balloon} near {p.bloom} ({p.misread}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
