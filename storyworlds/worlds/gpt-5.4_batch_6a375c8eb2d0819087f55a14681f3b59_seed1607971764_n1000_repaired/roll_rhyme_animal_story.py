#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py
=====================================================

A standalone story world for a small animal tale built around a tempting idea:
a child animal wants to let a round treat roll down a path, a rhyme warns that
rolling things can run away, and the turn of the story comes from whether the
helper can stop it in time.

This world aims for a gentle "animal story" feel: woodland children, a simple
problem, a memorable rhyme, and an ending image that proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py --setting brook_path --item acorn
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py --response kick_after_it
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/roll_rhyme_animal_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def species(self) -> str:
        return str(self.attrs.get("species", "animal"))

    @property
    def title(self) -> str:
        return str(self.attrs.get("title", self.id))
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    path: str
    steepness: int
    hazard: str
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
class RollingItem:
    id: str
    label: str
    phrase: str
    rolliness: int
    round_item: bool = True
    color: str = ""
    rhyme_warning: str = ""
    rhyme_end: str = ""
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
    label: str
    sense: int
    power: int
    success: str
    failure: str
    qa_text: str
    rhyme: str
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
class AnimalSpec:
    id: str
    species: str
    feature: str
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
class StoryParams:
    setting: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    hero_species: str
    helper_name: str
    helper_gender: str
    helper_species: str
    trait: str
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
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_rolling_danger(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["rolling"] < THRESHOLD:
        return out
    sig = ("rolling_danger", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("path").meters["danger"] += 1
    for actor in world.characters():
        if actor.role in {"hero", "helper"}:
            actor.memes["fear"] += 1
    out.append("__rolling__")
    return out


def _r_lost_sadness(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["lost"] < THRESHOLD:
        return out
    sig = ("lost_sadness", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["sadness"] += 1
    helper.memes["concern"] += 1
    out.append("__lost__")
    return out


def _r_secured_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["secured"] < THRESHOLD:
        return out
    sig = ("secured_relief", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    out.append("__secured__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="rolling_danger", tag="physical", apply=_r_rolling_danger),
    Rule(name="lost_sadness", tag="emotional", apply=_r_lost_sadness),
    Rule(name="secured_relief", tag="emotional", apply=_r_secured_relief),
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
    "brook_path": Setting(
        id="brook_path",
        place="the ferny brook path",
        path="a smooth little slope beside the brook",
        steepness=2,
        hazard="the cold brook",
        ending_image="with the brook whispering nearby and the basket swinging gently",
        tags={"brook", "path"},
    ),
    "garden_bank": Setting(
        id="garden_bank",
        place="the bean garden",
        path="a soft garden bank that slanted toward the tulips",
        steepness=1,
        hazard="the tulip bed",
        ending_image="between the bean rows, under the warm afternoon sun",
        tags={"garden", "flowers"},
    ),
    "moss_ramp": Setting(
        id="moss_ramp",
        place="the mossy hill near the hollow tree",
        path="a springy green ramp of moss above the bramble patch",
        steepness=2,
        hazard="the prickly brambles",
        ending_image="under the hollow tree, where the moss glowed soft and green",
        tags={"hill", "brambles"},
    ),
}

ITEMS = {
    "acorn": RollingItem(
        id="acorn",
        label="acorn",
        phrase="a shiny brown acorn",
        rolliness=2,
        round_item=True,
        color="brown",
        rhyme_warning="Round and brown can tumble down.",
        rhyme_end="Round and brown should travel sound.",
        tags={"acorn", "roll"},
    ),
    "berry": RollingItem(
        id="berry",
        label="berry",
        phrase="a plump red berry",
        rolliness=1,
        round_item=True,
        color="red",
        rhyme_warning="Round and red can race ahead.",
        rhyme_end="Round and red rides safe instead.",
        tags={"berry", "roll"},
    ),
    "chestnut": RollingItem(
        id="chestnut",
        label="chestnut",
        phrase="a glossy chestnut",
        rolliness=2,
        round_item=True,
        color="glossy brown",
        rhyme_warning="Shiny and round can bound from the ground.",
        rhyme_end="Shiny and round stays safe when it's found.",
        tags={"chestnut", "roll"},
    ),
    "leaf": RollingItem(
        id="leaf",
        label="leaf",
        phrase="a bright maple leaf",
        rolliness=0,
        round_item=False,
        color="golden",
        rhyme_warning="A leaf will drift, not roll away.",
        rhyme_end="A leaf can flutter all the day.",
        tags={"leaf"},
    ),
}

RESPONSES = {
    "leaf_cup": Response(
        id="leaf_cup",
        label="leaf cup",
        sense=2,
        power=2,
        success="sprang ahead, flipped a curled leaf in front of the {item}, and scooped it up before it could slip any farther",
        failure="flipped a curled leaf toward the {item}, but it skipped right past and kept rolling",
        qa_text="used a curled leaf to scoop the {item} up",
        rhyme="If it can roll, cup it whole.",
        tags={"leaf_cup", "carry"},
    ),
    "basket": Response(
        id="basket",
        label="bark basket",
        sense=3,
        power=3,
        success="darted after it, caught it at the very edge, and popped the {item} into a tiny bark basket",
        failure="reached with the bark basket, but the {item} was already bouncing too fast to catch",
        qa_text="caught the {item} and tucked it into a bark basket",
        rhyme="If it can roll, use a basket-bowl.",
        tags={"basket", "carry"},
    ),
    "paws": Response(
        id="paws",
        label="two careful paws",
        sense=2,
        power=1,
        success="pressed both paws around the {item} and held it still",
        failure="clapped both paws down, but the {item} slid between them and rushed on",
        qa_text="stopped the {item} with two careful paws",
        rhyme="If it can roll, hold it whole.",
        tags={"paws", "carry"},
    ),
    "kick_after_it": Response(
        id="kick_after_it",
        label="a little kick",
        sense=1,
        power=1,
        success="gave the {item} a tiny kick and somehow knocked it into a safe tuft of grass",
        failure="kicked after the {item}, which only made it bounce farther away",
        qa_text="kicked after the {item}",
        rhyme="Kicks and flicks make trouble quick.",
        tags={"kick", "carry"},
    ),
}

ANIMALS = {
    "squirrel": AnimalSpec(id="squirrel", species="squirrel", feature="a tail like a feather duster", tags={"tree"}),
    "rabbit": AnimalSpec(id="rabbit", species="rabbit", feature="long listening ears", tags={"meadow"}),
    "mouse": AnimalSpec(id="mouse", species="mouse", feature="tiny velvet paws", tags={"burrow"}),
    "hedgehog": AnimalSpec(id="hedgehog", species="hedgehog", feature="a round prickly back", tags={"hedge"}),
    "otter": AnimalSpec(id="otter", species="otter", feature="bright whiskers", tags={"water"}),
}

GIRL_NAMES = ["Pip", "Mimi", "Tansy", "Lulu", "Nell", "Daisy"]
BOY_NAMES = ["Moss", "Toby", "Pico", "Bram", "Nico", "Ollie"]
TRAITS = ["eager", "bouncy", "curious", "playful", "cheerful", "quick"]


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def hazard_at_risk(item: RollingItem) -> bool:
    return item.round_item


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in ITEMS.items():
            if not hazard_at_risk(item):
                continue
            for response_id, response in RESPONSES.items():
                if response.sense >= SENSE_MIN:
                    combos.append((setting_id, item_id, response_id))
    return combos


def danger_score(setting: Setting, item: RollingItem) -> int:
    return setting.steepness + item.rolliness


def is_caught(setting: Setting, item: RollingItem, response: Response) -> bool:
    return response.power >= danger_score(setting, item)


def explain_item(item: RollingItem) -> str:
    if not item.round_item:
        return (
            f"(No story: {item.phrase} is not the kind of thing that can honestly "
            f"roll away down a path. Pick a round item like an acorn, berry, or chestnut.)"
        )
    return "(No story: this item does not create a rolling problem.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names)


def predict_roll(world: World, response: Response) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["rolling"] += 1
    propagate(sim, narrate=False)
    caught = is_caught(SETTINGS[sim.facts["setting"].id], ITEMS[sim.facts["item_cfg"].id], response)
    if caught:
        item.meters["secured"] += 1
    else:
        item.meters["lost"] += 1
    propagate(sim, narrate=False)
    return {
        "caught": caught,
        "danger": sim.get("path").meters["danger"],
        "sadness": sim.get("hero").memes["sadness"],
    }


def opening(world: World, hero: Entity, helper: Entity, setting: Setting, item: RollingItem) -> None:
    world.say(
        f"{hero.id} the little {hero.species} and {helper.id} the little {helper.species} "
        f"were on their way through {setting.place} when {hero.id} found {item.phrase}."
    )
    world.say(
        f"It looked perfect for sharing at snack time, and {hero.id} held it up as proudly "
        f"as if it were a lantern made of autumn."
    )
    world.say(
        f"The path ahead was {setting.path}, and that made the {item.label} feel even rounder in "
        f"{hero.pronoun('possessive')} paw."
    )


def temptation(world: World, hero: Entity, helper: Entity, setting: Setting, item: RollingItem) -> None:
    hero.memes["joy"] += 1
    hero.memes["temptation"] += 1
    world.say(
        f'"Look," said {hero.id}, "{setting.path} is so smooth. I could let the {item.label} roll '
        f"and meet it at the bottom."
    )
    world.say(
        f"{helper.id}, who loved making up little rhymes, stopped so fast {helper.pronoun('possessive')} "
        f"whiskers twitched."
    )


def warning(world: World, helper: Entity, hero: Entity, item: RollingItem, response: Response) -> None:
    helper.memes["care"] += 1
    pred = predict_roll(world, response)
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'"{item.rhyme_warning}" {helper.id} sang softly. '
        f'"{response.rhyme}"'
    )
    world.say(
        f'"If you start it rolling, it may not stop where you want," {helper.pronoun()} added.'
    )


def defy(world: World, hero: Entity, item: RollingItem) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But the {item.label} looked so round and ready that {hero.id} gave it one tiny push anyway."
    )


def roll_away(world: World, hero: Entity, helper: Entity, setting: Setting, item: Entity) -> None:
    item.meters["rolling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At once the {item.label} began to roll. It hopped over one root, spun over two stones, "
        f"and hurried down toward {setting.hazard}."
    )
    world.say(
        f'"Oh no!" cried {hero.id}, and both little animals raced after it.'
    )


def rescue_success(world: World, helper: Entity, hero: Entity, response: Response, item_cfg: RollingItem) -> None:
    item = world.get("item")
    item.meters["rolling"] = 0.0
    item.meters["secured"] += 1
    propagate(world, narrate=False)
    body = response.success.format(item=item_cfg.label)
    world.say(f"{helper.id} {body}.")
    world.say(
        f"{hero.id} skidded to a stop beside {helper.id} and let out the breath {hero.pronoun()} had been holding."
    )


def rescue_fail(world: World, helper: Entity, hero: Entity, setting: Setting, response: Response, item_cfg: RollingItem) -> None:
    item = world.get("item")
    item.meters["rolling"] = 0.0
    item.meters["lost"] += 1
    propagate(world, narrate=False)
    body = response.failure.format(item=item_cfg.label)
    world.say(f"{helper.id} {body}.")
    world.say(
        f"The {item_cfg.label} gave one last bright twirl and disappeared into {setting.hazard}."
    )
    world.say(
        f"{hero.id} stood very still. The game had felt funny for one second and sad the next."
    )


def elder_arrives(world: World, elder: Entity, hero: Entity, helper: Entity, item_cfg: RollingItem, response: Response, caught: bool) -> None:
    if caught:
        world.say(
            f"Just then {elder.title} came along with a bundle of clover string and smiled at the sight."
        )
        world.say(
            f'"A round treasure needs a cozy ride," {elder.pronoun()} said. '
            f'"That was quick thinking, {helper.id}."'
        )
    else:
        world.say(
            f"Just then {elder.title} came along with a bundle of clover string and saw the two drooping faces."
        )
        world.say(
            f'"Oh, my dears," {elder.pronoun()} said. "Round things can trick fast paws."'
        )
        world.say(
            f"{elder.pronoun().capitalize()} reached into {elder.pronoun('possessive')} satchel and brought out another "
            f"{item_cfg.label}, saved from earlier in the day."
        )
    world.say(
        f'{elder.pronoun().capitalize()} tied up a little carrying basket and said, "{response.rhyme}"'
    )


def lesson_end(world: World, hero: Entity, helper: Entity, elder: Entity, setting: Setting, item_cfg: RollingItem, caught: bool) -> None:
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    if not caught:
        hero.memes["sadness"] = 0.0
        hero.memes["relief"] += 1
    world.say(
        f"{hero.id} tried the rhyme back in a whisper, then louder with {helper.id}, until both of them were smiling."
    )
    world.say(
        f'"{item_cfg.rhyme_end}" they chanted, carrying the {item_cfg.label} carefully between them.'
    )
    world.say(
        f"And they went on {setting.ending_image}, a little slower than before and much wiser about what could roll."
    )


def tell(
    setting: Setting,
    item_cfg: RollingItem,
    response: Response,
    hero_name: str,
    hero_gender: str,
    hero_species: AnimalSpec,
    helper_name: str,
    helper_gender: str,
    helper_species: AnimalSpec,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            attrs={"species": hero_species.species, "feature": hero_species.feature},
            traits=[trait],
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_gender,
            role="helper",
            attrs={"species": helper_species.species, "feature": helper_species.feature},
            traits=["rhyming", "careful"],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type="grandmother",
            role="elder",
            label="the elder",
            attrs={"species": "badger", "title": "Grandma Bramble"},
            traits=["calm", "kind"],
        )
    )
    world.add(
        Entity(
            id="path",
            kind="thing",
            type="path",
            label=setting.path,
            role="path",
            attrs={"hazard": setting.hazard, "steepness": setting.steepness},
        )
    )
    item_ent = world.add(
        Entity(
            id="item",
            kind="thing",
            type="snack",
            label=item_cfg.label,
            role="item",
            attrs={"round": item_cfg.round_item, "color": item_cfg.color},
        )
    )

    world.facts["setting"] = setting
    world.facts["item_cfg"] = item_cfg
    world.facts["response"] = response
    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["elder"] = elder
    world.facts["outcome"] = ""
    world.facts["caught"] = False

    opening(world, hero, helper, setting, item_cfg)
    world.para()
    temptation(world, hero, helper, setting, item_cfg)
    warning(world, helper, hero, item_cfg, response)
    defy(world, hero, item_cfg)
    world.para()
    roll_away(world, hero, helper, setting, item_ent)

    caught = is_caught(setting, item_cfg, response)
    world.para()
    if caught:
        rescue_success(world, helper, hero, response, item_cfg)
    else:
        rescue_fail(world, helper, hero, setting, response, item_cfg)

    world.para()
    elder_arrives(world, elder, hero, helper, item_cfg, response, caught)
    lesson_end(world, hero, helper, elder, setting, item_cfg, caught)

    world.facts["outcome"] = "caught" if caught else "lost"
    world.facts["caught"] = caught
    world.facts["severity"] = danger_score(setting, item_cfg)
    world.facts["used_response"] = response.qa_text.format(item=item_cfg.label)
    return world


KNOWLEDGE = {
    "roll": [
        (
            "Why do round things roll?",
            "Round things roll because their curved sides keep turning when you push them. On a slope, gravity helps them move even faster."
        )
    ],
    "acorn": [
        (
            "What is an acorn?",
            "An acorn is the nut of an oak tree. Squirrels and other animals often gather them for food."
        )
    ],
    "berry": [
        (
            "What is a berry?",
            "A berry is a small juicy fruit. Many birds and woodland animals like to eat them."
        )
    ],
    "chestnut": [
        (
            "What is a chestnut?",
            "A chestnut is a shiny brown nut with a smooth shell. Its round shape can make it easy to roll."
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of moving water. It can carry light things away if they fall in."
        )
    ],
    "basket": [
        (
            "Why is a basket good for carrying round things?",
            "A basket holds round things inside its sides, so they cannot easily roll away. That makes carrying safer and steadier."
        )
    ],
    "leaf_cup": [
        (
            "How can a curled leaf help carry something small?",
            "A curled leaf can make a little cup shape. That shape can help scoop up a tiny thing instead of letting it keep rolling."
        )
    ],
    "paws": [
        (
            "When can careful paws stop a rolling thing?",
            "Careful paws can stop a rolling thing when it is still moving slowly enough to catch. If it is already too fast, paws may not be enough."
        )
    ],
    "rhyme": [
        (
            "Why do rhymes help children remember things?",
            "Rhymes are easy to say and easy to hear. That makes safety ideas stick in your mind."
        )
    ],
}
KNOWLEDGE_ORDER = ["roll", "acorn", "berry", "chestnut", "brook", "basket", "leaf_cup", "paws", "rhyme"]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting"]
    item_cfg = world.facts["item_cfg"]
    response = world.facts["response"]
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    outcome = world.facts["outcome"]
    base = (
        f'Write a gentle animal story for a 3-to-5-year-old that includes the word "roll", '
        f'a warning rhyme, and a round {item_cfg.label} on {setting.place}.'
    )
    if outcome == "caught":
        return [
            base,
            f"Tell a woodland story where {hero.id} wants to let a {item_cfg.label} roll, "
            f"but {helper.id}'s rhyme comes true and the {item_cfg.label} is caught with {response.label}.",
            f'Write a child-facing animal story that repeats the rhyme "{response.rhyme}" '
            f"and ends with the friends carrying the {item_cfg.label} carefully."
        ]
    return [
        base,
        f"Tell a woodland story where {hero.id} ignores a rhyme, lets a {item_cfg.label} roll, "
        f"and loses it in {setting.hazard}, but an elder still helps the children learn a safer way.",
        f'Write an animal story with a small sad turn and a comforting ending, using the rhyme "{response.rhyme}".'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    elder = world.facts["elder"]
    setting = world.facts["setting"]
    item_cfg = world.facts["item_cfg"]
    response = world.facts["response"]
    outcome = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the little {hero.species} and {helper.id} the little {helper.species}. "
            f"They are joined by {elder.title}, who helps at the end."
        ),
        (
            f"Why did {helper.id} make up a rhyme before the {item_cfg.label} moved?",
            f"{helper.id} could see that the path was smooth and sloped toward {setting.hazard}. "
            f"The rhyme was a quick way to warn that once a round thing starts to roll, it may run away."
        ),
        (
            f"What made the {item_cfg.label} start to roll?",
            f"{hero.id} gave the {item_cfg.label} a tiny push because letting it roll looked fun. "
            f"That small choice turned the smooth slope into a problem."
        ),
    ]
    if outcome == "caught":
        qa.append(
            (
                f"How was the {item_cfg.label} saved?",
                f"{helper.id} {world.facts['used_response']}. "
                f"That worked because the helper reached it before the slope could carry it into {setting.hazard}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the children carrying the {item_cfg.label} instead of letting it roll. "
                f"The ending image shows they learned to move slowly and keep round things tucked in."
            )
        )
    else:
        qa.append(
            (
                f"What happened to the {item_cfg.label} after it rolled away?",
                f"It was lost in {setting.hazard}. "
                f"The children could not stop it in time once it got too fast."
            )
        )
        qa.append(
            (
                f"How did {elder.title} help after the loss?",
                f"{elder.title} comforted the children, brought out another {item_cfg.label}, and tied up a little carrying basket. "
                f"That turned the sad moment into a lesson about safer carrying."
            )
        )
    qa.append(
        (
            "What lesson did the children remember at the end?",
            f"They remembered the rhyme and stopped treating the {item_cfg.label} like a toy to roll. "
            f"By the ending, they were carrying it carefully together."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    response = world.facts["response"]
    setting = world.facts["setting"]
    tags = {"roll", "rhyme"} | set(item_cfg.tags) | set(response.tags)
    if "brook" in setting.tags:
        tags.add("brook")
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
    for entity in list(world.entities.values()):
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        bits = []
        if entity.role:
            bits.append(f"role={entity.role}")
        if entity.attrs:
            shown = {k: v for k, v in entity.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {entity.id:8} ({entity.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden_bank",
        item="berry",
        response="leaf_cup",
        hero_name="Pip",
        hero_gender="girl",
        hero_species="mouse",
        helper_name="Moss",
        helper_gender="boy",
        helper_species="rabbit",
        trait="eager",
        seed=101,
    ),
    StoryParams(
        setting="brook_path",
        item="acorn",
        response="basket",
        hero_name="Toby",
        hero_gender="boy",
        hero_species="squirrel",
        helper_name="Nell",
        helper_gender="girl",
        helper_species="hedgehog",
        trait="playful",
        seed=102,
    ),
    StoryParams(
        setting="moss_ramp",
        item="chestnut",
        response="paws",
        hero_name="Mimi",
        hero_gender="girl",
        hero_species="rabbit",
        helper_name="Bram",
        helper_gender="boy",
        helper_species="mouse",
        trait="curious",
        seed=103,
    ),
]


def outcome_of(params: StoryParams) -> str:
    return (
        "caught"
        if is_caught(SETTINGS[params.setting], ITEMS[params.item], RESPONSES[params.response])
        else "lost"
    )


ASP_RULES = r"""
hazard(I) :- item(I), round(I).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,I,R) :- setting(S), item(I), response(R), hazard(I), sensible(R).

severity(V) :- chosen_setting(S), chosen_item(I), steepness(S,St), rolliness(I,R), V = St + R.
caught :- chosen_response(R), power(R,P), severity(V), P >= V.

outcome(caught) :- caught.
outcome(lost) :- not caught.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("steepness", setting_id, setting.steepness))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("rolliness", item_id, item.rolliness))
        if item.round_item:
            lines.append(asp.fact("round", item_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
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

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [params for params in cases if asp_outcome(params) != outcome_of(params)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld: a round thing may roll away, a rhyme warns, and the ending teaches safer carrying."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item is not None:
        item_cfg = ITEMS[args.item]
        if not hazard_at_risk(item_cfg):
            raise StoryError(explain_item(item_cfg))
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.response is None or combo[2] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, response_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    hero_name = _pick_name(rng, hero_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=hero_name)
    hero_species = rng.choice(sorted(ANIMALS))
    helper_species_pool = [species for species in sorted(ANIMALS) if species != hero_species]
    helper_species = rng.choice(helper_species_pool)
    trait = rng.choice(TRAITS)

    return StoryParams(
        setting=setting_id,
        item=item_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_gender=helper_gender,
        helper_species=helper_species,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.hero_species not in ANIMALS:
        raise StoryError(f"(Unknown hero species: {params.hero_species})")
    if params.helper_species not in ANIMALS:
        raise StoryError(f"(Unknown helper species: {params.helper_species})")
    if params.response and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not ITEMS[params.item].round_item:
        raise StoryError(explain_item(ITEMS[params.item]))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        response=RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_species=ANIMALS[params.hero_species],
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        helper_species=ANIMALS[params.helper_species],
        trait=params.trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, response) combos:\n")
        for setting_id, item_id, response_id in combos:
            print(f"  {setting_id:12} {item_id:9} {response_id}")
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
            params = sample.params
            header = (
                f"### {params.hero_name} and {params.helper_name}: "
                f"{params.item} at {params.setting} ({params.response}, {outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
