#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py
==================================================================================

A standalone story world about a child growing a tiny seed into something big
and beloved, then meeting an unexpected garden problem with bravery.

The seed request asked for:
- the word "whopper"
- Transformation
- Surprise
- Bravery
- a Heartwarming tone

This world turns that into a small classical simulation:
a child tends a plant from seed to sprout to a great big garden treasure; an
unexpected threat arrives; the child bravely helps protect the plant with the
right garden fix; and the ending shows the child sharing what grew.

Run it
------
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --plant pumpkin --surprise frost --response blanket_cover
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --plant sunflower --surprise rabbits
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --trace --seed 9
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --json
    python storyworlds/worlds/gpt-5.4/whopper_transformation_surprise_bravery_heartwarming.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "grandmother", "woman", "neighbor_woman"}
        male = {"boy", "father", "uncle", "grandfather", "man", "neighbor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Patch:
    id: str
    place: str
    detail: str
    ending_place: str
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
class Plant:
    id: str
    seed_phrase: str
    sprout_phrase: str
    mature_phrase: str
    whopper_phrase: str
    share_text: str
    height: str
    vulnerabilities: set[str]
    reward: str
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
class Surprise:
    id: str
    arrival: str
    warning: str
    effect: str
    risk: int
    affects: set[str]
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
    label: str
    sense: int
    power: int
    handles: set[str]
    suited_heights: set[str]
    action: str
    partial: str
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
    def __init__(self, patch: Patch) -> None:
        self.patch = patch
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {"patch": patch}

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
        clone = World(self.patch)
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


def _r_transform(world: World) -> list[str]:
    plant = world.get("plant")
    out: list[str] = []
    if plant.meters["growth"] >= 1.0 and ("stage", "sprout") not in world.fired:
        world.fired.add(("stage", "sprout"))
        plant.attrs["stage"] = "sprout"
        out.append("__sprout__")
    if plant.meters["growth"] >= 3.0 and ("stage", "whopper") not in world.fired:
        world.fired.add(("stage", "whopper"))
        plant.attrs["stage"] = "whopper"
        out.append("__whopper__")
    return out


def _r_danger(world: World) -> list[str]:
    patch = world.get("patch")
    plant = world.get("plant")
    child = world.get("child")
    if plant.meters["threat"] >= THRESHOLD and ("danger", plant.id) not in world.fired:
        world.fired.add(("danger", plant.id))
        patch.meters["danger"] += 1
        child.memes["worry"] += 1
        return ["__danger__"]
    return []


def _r_damage(world: World) -> list[str]:
    plant = world.get("plant")
    if plant.meters["threat"] >= THRESHOLD and plant.meters["protection"] < THRESHOLD:
        if ("damage", plant.id) not in world.fired:
            world.fired.add(("damage", plant.id))
            plant.meters["damage"] += 1
            return ["__damage__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="damage", tag="physical", apply=_r_damage),
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
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


def plant_at_risk(plant: Plant, surprise: Surprise) -> bool:
    return surprise.id in plant.vulnerabilities and plant.height in surprise.affects


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def response_fits(plant: Plant, surprise: Surprise, response: Response) -> bool:
    return (
        response.sense >= SENSE_MIN
        and surprise.id in response.handles
        and plant.height in response.suited_heights
    )


def threat_severity(surprise: Surprise, delay: int) -> int:
    return surprise.risk + delay


def fully_saved(plant: Plant, surprise: Surprise, response: Response, delay: int) -> bool:
    if not response_fits(plant, surprise, response):
        return False
    return response.power >= threat_severity(surprise, delay)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for patch_id in PATCHES:
        for plant_id, plant in PLANTS.items():
            for surprise_id, surprise in SURPRISES.items():
                if not plant_at_risk(plant, surprise):
                    continue
                for response_id, response in RESPONSES.items():
                    if response_fits(plant, surprise, response):
                        combos.append((patch_id, plant_id, surprise_id, response_id))
    return combos


def predict_outcome(plant: Plant, surprise: Surprise, response: Response, delay: int) -> dict:
    return {
        "valid": response_fits(plant, surprise, response),
        "fully_saved": fully_saved(plant, surprise, response, delay),
        "severity": threat_severity(surprise, delay),
    }


def introduce(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    world.say(
        f"{child.id} loved small growing things and the quiet promises tucked inside seeds. "
        f"One soft morning in {world.patch.place}, {child.pronoun()} planted {plant_cfg.seed_phrase} "
        f"with {child.pronoun('possessive')} {helper.label_word} beside {child.pronoun('object')}."
    )
    world.say(world.patch.detail)


def tend_days(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    plant = world.get("plant")
    child.memes["care"] += 1
    for _ in range(3):
        plant.meters["growth"] += 1
        plant.meters["watered"] += 1
        propagate(world, narrate=False)
    world.say(
        f"Every day, {child.id} carried a little watering can, patted the soil, and looked for change."
    )
    world.say(
        f"Soon the seed was not only a seed anymore. It became {plant_cfg.sprout_phrase}, "
        f"and after more sunny mornings it turned into {plant_cfg.whopper_phrase}."
    )
    child.memes["pride"] += 1
    helper.memes["love"] += 1
    plant.attrs["mature_name"] = plant_cfg.mature_phrase
    world.facts["transformed"] = True


def plan_special_day(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    world.say(
        f'"If it keeps growing like this," {helper.label_word} said, smiling, '
        f'"we can take it to {world.patch.ending_place}."'
    )
    world.say(
        f"{child.id} could already picture {plant_cfg.reward} and felt warm all the way down to "
        f"{child.pronoun('possessive')} toes."
    )


def surprise_arrives(world: World, child: Entity, surprise: Surprise) -> None:
    plant = world.get("plant")
    plant.meters["threat"] = 1.0
    propagate(world, narrate=False)
    world.say(surprise.arrival)
    world.say(
        f"{child.id} looked out and saw that the {plant.label} was in trouble. {surprise.warning}"
    )
    child.memes["fear"] += 1
    world.facts["threat_started"] = True


def brave_choice(world: World, child: Entity, helper: Entity, response: Response) -> None:
    child.memes["courage"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 0.5)
    world.say(
        f"{child.id}'s tummy fluttered. The garden felt bigger in the dim light than it had in the afternoon."
    )
    world.say(
        f'But {child.pronoun()} took a breath and said, "I want to help." {helper.label_word.capitalize()} '
        f"squeezed {child.pronoun('possessive')} shoulder, and together they hurried out with {response.label}."
    )


def protect(world: World, child: Entity, helper: Entity, plant_cfg: Plant,
            surprise: Surprise, response: Response, delay: int) -> None:
    plant = world.get("plant")
    world.facts["severity"] = threat_severity(surprise, delay)
    if fully_saved(plant_cfg, surprise, response, delay):
        plant.meters["protection"] = 1.0
        plant.meters["threat"] = 0.0
        world.get("patch").meters["danger"] = 0.0
        world.say(response.action.format(plant=plant.label))
        world.say(
            f"The danger passed before it could bite into the growing {plant.label}."
        )
        plant.meters["saved"] += 1
        world.facts["outcome"] = "thriving"
    else:
        plant.meters["protection"] = 1.0
        plant.meters["threat"] = 0.0
        plant.meters["damage"] += 1
        world.get("patch").meters["danger"] = 0.0
        world.say(response.partial.format(plant=plant.label))
        world.say(
            f"A few leaves showed the scare, but the plant was still standing. It had made it through the surprise."
        )
        plant.meters["saved"] += 1
        world.facts["outcome"] = "nicked"
    child.memes["relief"] += 1
    helper.memes["relief"] += 1


def morning_after(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    plant = world.get("plant")
    if world.facts.get("outcome") == "thriving":
        world.say(
            f"In the morning, the garden seemed to smile back. {plant_cfg.mature_phrase.capitalize()} stood there, "
            f"fresh and proud, as if it knew who had cared for it."
        )
    else:
        world.say(
            f"In the morning, {child.id} found a few bent leaves, but {plant_cfg.mature_phrase} was still there, "
            f"brave in its own quiet way."
        )
    child.memes["joy"] += 1
    child.memes["bravery_known"] += 1
    helper.memes["pride"] += 1


def ending(world: World, child: Entity, helper: Entity, plant_cfg: Plant) -> None:
    world.say(
        f"At {world.patch.ending_place}, everyone noticed what had grown. {plant_cfg.share_text}"
    )
    world.say(
        f'{helper.label_word.capitalize()} leaned down and whispered, "The plant changed, and so did you."'
    )
    world.say(
        f"{child.id} touched the whopper {world.get('plant').label} very gently and smiled. "
        f"{child.pronoun().capitalize()} knew bravery did not always sound loud; sometimes it sounded like a small voice saying, "
        f'"I want to help."'
    )


def tell(patch: Patch, plant_cfg: Plant, surprise: Surprise, response: Response,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_type: str = "grandmother", trait: str = "gentle",
         delay: int = 0) -> World:
    world = World(patch)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=["little", trait],
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
    ))
    patch_ent = world.add(Entity(
        id="patch",
        type="garden_patch",
        label=patch.place,
        phrase=patch.place,
    ))
    plant = world.add(Entity(
        id="plant",
        type="plant",
        label=plant_cfg.id,
        phrase=plant_cfg.seed_phrase,
        attrs={"stage": "seed"},
    ))
    child.memes["fear"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["love"] = 0.0
    helper.memes["pride"] = 0.0
    patch_ent.meters["danger"] = 0.0
    plant.meters["growth"] = 0.0
    plant.meters["threat"] = 0.0
    plant.meters["protection"] = 0.0
    plant.meters["damage"] = 0.0
    plant.meters["saved"] = 0.0
    world.facts.update(
        child=child,
        helper=helper,
        plant_cfg=plant_cfg,
        plant=plant,
        surprise=surprise,
        response=response,
        delay=delay,
        outcome="?",
        transformed=False,
        threat_started=False,
        patch=patch,
    )

    introduce(world, child, helper, plant_cfg)
    tend_days(world, child, helper, plant_cfg)
    plan_special_day(world, child, helper, plant_cfg)

    world.para()
    surprise_arrives(world, child, surprise)
    brave_choice(world, child, helper, response)

    world.para()
    protect(world, child, helper, plant_cfg, surprise, response, delay)
    morning_after(world, child, helper, plant_cfg)
    ending(world, child, helper, plant_cfg)
    return world


PATCHES = {
    "backyard": Patch(
        id="backyard",
        place="the backyard garden",
        detail="There was a crooked fence, a warm patch of dirt, and one robin that always seemed to be watching.",
        ending_place="the neighborhood harvest table",
        tags={"garden"},
    ),
    "schoolyard": Patch(
        id="schoolyard",
        place="the little school garden",
        detail="Beside the play fence sat a row of wooden boxes where children grew small green hopes.",
        ending_place="the school sharing table",
        tags={"garden", "school"},
    ),
    "courtyard": Patch(
        id="courtyard",
        place="the apartment courtyard planter",
        detail="Pots lined the bricks, and even the windows above seemed to lean down to see what was growing.",
        ending_place="the courtyard picnic",
        tags={"garden", "neighborhood"},
    ),
}

PLANTS = {
    "pumpkin": Plant(
        id="pumpkin",
        seed_phrase="a round pumpkin seed",
        sprout_phrase="a shy green sprout with soft leaves",
        mature_phrase="a plump orange pumpkin",
        whopper_phrase="a whopper pumpkin resting under broad leaves",
        share_text="Slices of pumpkin bread were passed from hand to hand, and the warm smell made everyone smile.",
        height="low",
        vulnerabilities={"frost", "rabbits", "heat"},
        reward="a cheerful table with something everyone could share",
        tags={"pumpkin", "seed", "garden_food"},
    ),
    "sunflower": Plant(
        id="sunflower",
        seed_phrase="a striped sunflower seed",
        sprout_phrase="a bright little stem that kept turning toward the sun",
        mature_phrase="a tall sunflower with a golden face",
        whopper_phrase="a whopper sunflower nodding over the fence",
        share_text="Children counted the seeds in its big center and tucked a few away to plant next spring.",
        height="tall",
        vulnerabilities={"wind", "heat"},
        reward="a sunny corner that made people stop and grin",
        tags={"sunflower", "seed", "flower"},
    ),
    "bean": Plant(
        id="bean",
        seed_phrase="a smooth bean seed",
        sprout_phrase="a curled green shoot reaching for something to climb",
        mature_phrase="a twisting bean vine with crisp pods",
        whopper_phrase="a whopper bean vine climbing higher than the watering can",
        share_text="A bowl of beans was snapped and shared, and a few pods were saved for planting again.",
        height="climbing",
        vulnerabilities={"wind", "frost", "heat"},
        reward="a basket that could be filled together",
        tags={"bean", "seed", "garden_food"},
    ),
}

SURPRISES = {
    "frost": Surprise(
        id="frost",
        arrival="That evening, a surprise cold crept in and silvered the grass.",
        warning="A thin frost would sting anything tender before sunrise.",
        effect="cold nips the leaves",
        risk=2,
        affects={"low", "climbing"},
        tags={"frost", "weather"},
    ),
    "wind": Surprise(
        id="wind",
        arrival="Just before supper, a sudden gusty wind came tumbling through the garden.",
        warning="The stronger stems might lean, but the tallest growing things could snap if no one helped them.",
        effect="wind bends the stems",
        risk=2,
        affects={"tall", "climbing"},
        tags={"wind", "weather"},
    ),
    "heat": Surprise(
        id="heat",
        arrival="The next day turned into a surprise hot spell, and the dirt lost its cool smell by noon.",
        warning="If the roots stayed thirsty too long, the plant would droop and stop growing happily.",
        effect="heat dries the roots",
        risk=1,
        affects={"low", "tall", "climbing"},
        tags={"heat", "weather"},
    ),
    "rabbits": Surprise(
        id="rabbits",
        arrival="At dusk, two rabbits slipped under the fence with twitching noses.",
        warning="Tender leaves low to the ground looked like supper to them.",
        effect="rabbits nibble the leaves",
        risk=2,
        affects={"low"},
        tags={"rabbits", "garden_animals"},
    ),
}

RESPONSES = {
    "blanket_cover": Response(
        id="blanket_cover",
        label="a soft garden blanket",
        sense=3,
        power=2,
        handles={"frost"},
        suited_heights={"low", "climbing"},
        action="Together they draped a soft garden blanket over the {plant} and tucked the edges down so the cold could not bite through.",
        partial="Together they covered the {plant}, but the cold had already brushed past once before the blanket settled.",
        qa_text="They covered the plant with a soft blanket to keep the frost off.",
        tags={"blanket", "frost"},
    ),
    "stake_ties": Response(
        id="stake_ties",
        label="stakes and cloth ties",
        sense=3,
        power=2,
        handles={"wind"},
        suited_heights={"tall", "climbing"},
        action="Together they pressed in sturdy stakes and tied the {plant} gently, so it could sway without falling.",
        partial="They tied the {plant} as fast as they could, though one hard gust had already bent it a little.",
        qa_text="They used stakes and soft ties so the wind could not knock the plant down.",
        tags={"stakes", "wind"},
    ),
    "deep_water": Response(
        id="deep_water",
        label="two full watering cans",
        sense=3,
        power=2,
        handles={"heat"},
        suited_heights={"low", "tall", "climbing"},
        action="Together they poured slow, deep water around the roots of the {plant} until the thirsty soil turned dark again.",
        partial="They watered the {plant} deeply, though the heat had already curled a few edges dry.",
        qa_text="They gave the roots a deep drink of water so the hot day would not wilt the plant.",
        tags={"water", "heat"},
    ),
    "garden_fence": Response(
        id="garden_fence",
        label="a little folding fence",
        sense=3,
        power=2,
        handles={"rabbits"},
        suited_heights={"low"},
        action="Together they opened a little folding fence and set it around the {plant} before the rabbits could reach the leaves.",
        partial="They set the little fence around the {plant}, though the rabbits had already nibbled a few leaves.",
        qa_text="They put a little fence around the plant so the rabbits could not eat it.",
        tags={"fence", "rabbits"},
    ),
    "paper_sign": Response(
        id="paper_sign",
        label="a paper sign",
        sense=1,
        power=0,
        handles={"rabbits", "wind", "frost", "heat"},
        suited_heights={"low", "tall", "climbing"},
        action="They stuck up a paper sign beside the {plant}.",
        partial="They stuck up a paper sign, but it did not help the {plant} at all.",
        qa_text="They put up a paper sign.",
        tags={"weak_fix"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Ella", "Zoe", "Anna", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["gentle", "hopeful", "patient", "careful", "cheerful", "kind"]


@dataclass
class StoryParams:
    patch: str
    plant: str
    surprise: str
    response: str
    child_name: str
    child_gender: str
    helper_type: str
    trait: str
    delay: int = 0
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
    "seed": [
        (
            "What does a seed do in the ground?",
            "A seed can wake up in warm, wet soil and start growing roots and a stem. That is how a new plant begins."
        )
    ],
    "pumpkin": [
        (
            "What is a pumpkin plant like?",
            "A pumpkin plant grows on a vine close to the ground. Its big leaves help shade the soil, and later it can grow round orange pumpkins."
        )
    ],
    "sunflower": [
        (
            "Why do sunflowers look tall and bright?",
            "Sunflowers grow on long stems so their big flower heads can reach the sun. Their faces look bright because they are made of many tiny yellow petals."
        )
    ],
    "bean": [
        (
            "Why do bean vines climb?",
            "Bean vines like to curl around poles or strings as they grow. Climbing helps them reach light and make room for their pods."
        )
    ],
    "frost": [
        (
            "What is frost?",
            "Frost is a thin icy layer that forms when the air gets very cold. Tender leaves can be hurt by it."
        )
    ],
    "wind": [
        (
            "Why can strong wind bother a plant?",
            "Strong wind can bend stems and tug at roots. Tall or climbing plants sometimes need support to stay steady."
        )
    ],
    "heat": [
        (
            "Why do plants need water on a very hot day?",
            "Hot weather can dry the soil quickly. Plants need water in their roots so their leaves stay full and strong."
        )
    ],
    "rabbits": [
        (
            "Why do rabbits nibble garden leaves?",
            "Rabbits eat tender green plants because the leaves are soft and easy to chew. A small fence helps keep the garden safe."
        )
    ],
    "blanket": [
        (
            "How can a blanket help a plant on a cold night?",
            "A garden blanket holds in a little warmth and keeps frost off tender leaves. It works like a cozy cover for the plant."
        )
    ],
    "stakes": [
        (
            "What do plant stakes do?",
            "Plant stakes help hold a stem upright. Soft ties let the plant move a little without falling over."
        )
    ],
    "water": [
        (
            "What does deep watering mean?",
            "Deep watering means giving enough water for the soil under the surface to get wet. That helps the roots drink for longer."
        )
    ],
    "fence": [
        (
            "What is a garden fence for?",
            "A small garden fence makes a clear little wall around a plant. It helps keep nibbling animals away."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "seed",
    "pumpkin",
    "sunflower",
    "bean",
    "frost",
    "wind",
    "heat",
    "rabbits",
    "blanket",
    "stakes",
    "water",
    "fence",
]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    plant_cfg = world.facts["plant_cfg"]
    surprise = world.facts["surprise"]
    patch = world.facts["patch"]
    response = world.facts["response"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "whopper" and shows a plant transforming from a seed into something wonderful.',
        f"Tell a gentle story where a {child.type} named {child.id} grows a {plant_cfg.id} in {patch.place}, faces a surprise {surprise.id}, and shows bravery by helping with {response.label}.",
        f"Write a cozy story about transformation, surprise, and bravery in a garden, ending with people sharing what grew.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    plant_cfg = world.facts["plant_cfg"]
    surprise = world.facts["surprise"]
    response = world.facts["response"]
    patch = world.facts["patch"]
    outcome = world.facts.get("outcome")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child who cared for a growing {plant_cfg.id}, and {child.pronoun('possessive')} {helper.label_word} who helped. Together they looked after the garden in {patch.place}."
        ),
        (
            f"What changed in the story?",
            f"The little seed changed into {plant_cfg.whopper_phrase}. The story also shows {child.id} changing from simply hoping into someone brave enough to help when a surprise came."
        ),
        (
            f"What was the surprise problem?",
            f"The surprise was {surprise.id}. {surprise.warning} That is why the plant suddenly needed help."
        ),
        (
            f"Why was {child.id} brave?",
            f"{child.id} felt scared because the garden seemed bigger and more uncertain when the trouble came. Even so, {child.pronoun()} chose to go help the plant instead of hiding inside."
        ),
        (
            f"How did they help the plant?",
            f"{response.qa_text} They acted quickly because that was the right fix for the kind of trouble the plant was facing."
        ),
    ]
    if outcome == "thriving":
        qa.append(
            (
                "How did the story end?",
                f"It ended happily, with the plant still strong and beautiful the next morning. At {patch.ending_place}, people shared what had grown, and {child.id} understood that small brave choices can protect precious things."
            )
        )
    else:
        qa.append(
            (
                "Did the plant get ruined?",
                f"No. A few leaves showed the scare, but the plant survived and was still worth sharing. That makes the ending heartwarming because care mattered even though the surprise left a tiny mark."
            )
        )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    plant_cfg = world.facts["plant_cfg"]
    surprise = world.facts["surprise"]
    response = world.facts["response"]
    tags: set[str] = {"seed"} | set(plant_cfg.tags) | set(surprise.tags) | set(response.tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != "" and v is not None}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        patch="backyard",
        plant="pumpkin",
        surprise="frost",
        response="blanket_cover",
        child_name="Mia",
        child_gender="girl",
        helper_type="grandmother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        patch="schoolyard",
        plant="sunflower",
        surprise="wind",
        response="stake_ties",
        child_name="Leo",
        child_gender="boy",
        helper_type="father",
        trait="hopeful",
        delay=0,
    ),
    StoryParams(
        patch="courtyard",
        plant="bean",
        surprise="heat",
        response="deep_water",
        child_name="Anna",
        child_gender="girl",
        helper_type="uncle",
        trait="patient",
        delay=0,
    ),
    StoryParams(
        patch="backyard",
        plant="pumpkin",
        surprise="rabbits",
        response="garden_fence",
        child_name="Ben",
        child_gender="boy",
        helper_type="grandfather",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        patch="schoolyard",
        plant="bean",
        surprise="wind",
        response="stake_ties",
        child_name="Ruby",
        child_gender="girl",
        helper_type="mother",
        trait="kind",
        delay=1,
    ),
]


def explain_rejection(plant: Plant, surprise: Surprise, response: Optional[Response] = None) -> str:
    if not plant_at_risk(plant, surprise):
        return (
            f"(No story: a {plant.id} in this world is not the sort of plant that would reasonably need help from {surprise.id}. "
            f"The surprise has to fit the plant's real risk.)"
        )
    if response is not None and response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Pick a more helpful garden fix.)"
        )
    if response is not None and not response_fits(plant, surprise, response):
        return (
            f"(No story: {response.label} is not the right fix for a {plant.id} facing {surprise.id}. "
            f"The brave action has to match the actual problem.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    plant = PLANTS[params.plant]
    surprise = SURPRISES[params.surprise]
    response = RESPONSES[params.response]
    return "thriving" if fully_saved(plant, surprise, response, params.delay) else "nicked"


ASP_RULES = r"""
plant_at_risk(P, S) :- vulnerable(P, S), plant_height(P, H), surprise_affects(S, H).
sensible(R) :- response(R), sense(R, N), sense_min(M), N >= M.
response_fits(P, S, R) :- plant_at_risk(P, S), sensible(R),
                          handles(R, S), plant_height(P, H), suited_height(R, H).
valid(Patch, P, S, R) :- patch(Patch), plant(P), surprise(S), response(R), response_fits(P, S, R).

severity(V + D) :- chosen_surprise(S), risk(S, V), delay(D).
resp_power(Pw) :- chosen_response(R), power(R, Pw).
outcome(thriving) :- chosen_plant(P), chosen_surprise(S), chosen_response(R),
                     response_fits(P, S, R), resp_power(Pw), severity(Sev), Pw >= Sev.
outcome(nicked) :- chosen_plant(P), chosen_surprise(S), chosen_response(R),
                   response_fits(P, S, R), resp_power(Pw), severity(Sev), Pw < Sev.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for patch_id in PATCHES:
        lines.append(asp.fact("patch", patch_id))
    for plant_id, plant in PLANTS.items():
        lines.append(asp.fact("plant", plant_id))
        lines.append(asp.fact("plant_height", plant_id, plant.height))
        for s in sorted(plant.vulnerabilities):
            lines.append(asp.fact("vulnerable", plant_id, s))
    for surprise_id, surprise in SURPRISES.items():
        lines.append(asp.fact("surprise", surprise_id))
        lines.append(asp.fact("risk", surprise_id, surprise.risk))
        for h in sorted(surprise.affects):
            lines.append(asp.fact("surprise_affects", surprise_id, h))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
        for s in sorted(response.handles):
            lines.append(asp.fact("handles", response_id, s))
        for h in sorted(response.suited_heights):
            lines.append(asp.fact("suited_height", response_id, h))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_plant", params.plant),
            asp.fact("chosen_surprise", params.surprise),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    cl_valid = set(asp_valid_combos())
    if py_valid == cl_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl_valid - py_valid:
            print("  only in asp:", sorted(cl_valid - py_valid))
        if py_valid - cl_valid:
            print("  only in python:", sorted(py_valid - cl_valid))

    py_sens = {r.id for r in sensible_responses()}
    cl_sens = set(asp_sensible())
    if py_sens == cl_sens:
        print(f"OK: sensible responses match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: asp={sorted(cl_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

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
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="### smoke")
        if not sample.story.strip():
            raise StoryError("Generated smoke-test story was empty.")
        print("OK: smoke-test story generation and emit() succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a tiny seed becomes a whopper garden wonder, and a child meets a surprise with bravery."
    )
    ap.add_argument("--patch", choices=PATCHES)
    ap.add_argument("--plant", choices=PLANTS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra head start for the surprise")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plant and args.surprise:
        plant = PLANTS[args.plant]
        surprise = SURPRISES[args.surprise]
        if not plant_at_risk(plant, surprise):
            raise StoryError(explain_rejection(plant, surprise))
    if args.response:
        response = RESPONSES[args.response]
        if response.sense < SENSE_MIN:
            plant = PLANTS[args.plant] if args.plant else next(iter(PLANTS.values()))
            surprise = SURPRISES[args.surprise] if args.surprise else next(iter(SURPRISES.values()))
            raise StoryError(explain_rejection(plant, surprise, response))
    if args.plant and args.surprise and args.response:
        plant = PLANTS[args.plant]
        surprise = SURPRISES[args.surprise]
        response = RESPONSES[args.response]
        if not response_fits(plant, surprise, response):
            raise StoryError(explain_rejection(plant, surprise, response))

    combos = [
        combo for combo in valid_combos()
        if (args.patch is None or combo[0] == args.patch)
        and (args.plant is None or combo[1] == args.plant)
        and (args.surprise is None or combo[2] == args.surprise)
        and (args.response is None or combo[3] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    patch, plant, surprise, response = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    helper_type = args.helper or rng.choice(["mother", "father", "grandmother", "grandfather", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 0, 1])

    return StoryParams(
        patch=patch,
        plant=plant,
        surprise=surprise,
        response=response,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.patch not in PATCHES:
        raise StoryError(f"Unknown patch '{params.patch}'.")
    if params.plant not in PLANTS:
        raise StoryError(f"Unknown plant '{params.plant}'.")
    if params.surprise not in SURPRISES:
        raise StoryError(f"Unknown surprise '{params.surprise}'.")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response '{params.response}'.")

    patch = PATCHES[params.patch]
    plant_cfg = PLANTS[params.plant]
    surprise = SURPRISES[params.surprise]
    response = RESPONSES[params.response]

    if not plant_at_risk(plant_cfg, surprise):
        raise StoryError(explain_rejection(plant_cfg, surprise))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_rejection(plant_cfg, surprise, response))
    if not response_fits(plant_cfg, surprise, response):
        raise StoryError(explain_rejection(plant_cfg, surprise, response))

    world = tell(
        patch=patch,
        plant_cfg=plant_cfg,
        surprise=surprise,
        response=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        trait=params.trait,
        delay=params.delay,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("", "#show sensible/1.\n#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (patch, plant, surprise, response) combos:\n")
        for patch, plant, surprise, response in combos:
            print(f"  {patch:10} {plant:10} {surprise:9} {response}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.plant} in {p.patch} "
                f"({p.surprise}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
