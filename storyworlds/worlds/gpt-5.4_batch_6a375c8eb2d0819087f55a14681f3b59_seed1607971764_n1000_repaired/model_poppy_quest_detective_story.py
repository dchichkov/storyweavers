#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py
===============================================================

A standalone storyworld for a tiny detective-style quest: a child notices that a
small model has vanished, studies clues near a poppy bed, and follows a
reasonable search method to recover it.

The world is deliberately small and constraint-checked:

- A disappearance cause can only move the model to plausible hiding spots.
- A search method must match the clue and the kind of place being searched.
- Low-sense methods are known to the world but refused by the generator.
- The ending image depends on simulated state: the model may come back clean,
  scuffed, or damp, and the closing beat proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py --scene fair_table --cause kitten
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py --spot rain_barrel
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/model_poppy_quest_detective_story.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    id: str
    place: str
    opening: str
    poppy_place: str
    afford_spots: set[str] = field(default_factory=set)
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
class ModelItem:
    id: str
    label: str
    phrase: str
    tiny_detail: str
    repair: str
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
class Cause:
    id: str
    label: str
    clue_tag: str
    clue_text: str
    movement: str
    can_hide: set[str] = field(default_factory=set)
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
class Spot:
    id: str
    label: str
    phrase: str
    found_line: str
    trait: str = ""
    wet: bool = False
    thorny: bool = False
    high: bool = False
    poppy_near: bool = False
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
class Method:
    id: str
    sense: int
    clue_tag: str
    needs_high: bool = False
    text: str = ""
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


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "cause_id": "",
            "spot_id": "",
            "method_id": "",
            "delay": 0,
            "predicted_spot": "",
            "outcome": "",
            "poppy_helped": False,
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
        clone = World(self.scene)
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


def _r_missing_worry(world: World) -> list[str]:
    model = world.get("model")
    hero = world.get("hero")
    helper = world.get("helper")
    if model.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    helper.memes["focus"] += 1
    return []


def _r_wet_damage(world: World) -> list[str]:
    model = world.get("model")
    if model.attrs.get("wet_spot") is not True:
        return []
    if world.facts["delay"] < 1:
        return []
    sig = ("wet_damage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    model.meters["damp"] += 1
    return []


def _r_thorn_scuff(world: World) -> list[str]:
    model = world.get("model")
    if model.attrs.get("thorny_spot") is not True:
        return []
    if world.facts["delay"] < 1:
        return []
    sig = ("thorn_scuff",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    model.meters["scuffed"] += 1
    return []


def _r_high_scuff(world: World) -> list[str]:
    model = world.get("model")
    if model.attrs.get("high_spot") is not True:
        return []
    if world.facts["delay"] < 2:
        return []
    sig = ("high_scuff",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    model.meters["scuffed"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    model = world.get("model")
    hero = world.get("hero")
    helper = world.get("helper")
    if model.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["worry"] = 0.0
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="wet_damage", tag="physical", apply=_r_wet_damage),
    Rule(name="thorn_scuff", tag="physical", apply=_r_thorn_scuff),
    Rule(name="high_scuff", tag="physical", apply=_r_high_scuff),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
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
            world.say(sent)
    return produced


def spot_damage_outcome(spot: Spot, delay: int) -> str:
    if spot.wet and delay >= 1:
        return "damp"
    if spot.thorny and delay >= 1:
        return "scuffed"
    if spot.high and delay >= 2:
        return "scuffed"
    return "clean"


def cause_allows(cause: Cause, spot: Spot) -> bool:
    return spot.id in cause.can_hide


def method_fits(method: Method, cause: Cause, spot: Spot) -> bool:
    if method.clue_tag != cause.clue_tag:
        return False
    if method.needs_high and not spot.high:
        return False
    if not method.needs_high and spot.high and method.id == "ground_scan":
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for cause_id, cause in CAUSES.items():
            for spot_id, spot in SPOTS.items():
                if spot_id not in scene.afford_spots:
                    continue
                if not cause_allows(cause, spot):
                    continue
                for method in sensible_methods():
                    if method_fits(method, cause, spot):
                        combos.append((scene_id, cause_id, spot_id, method.id))
    return combos


def explain_rejection(scene: Scene, cause: Cause, spot: Spot, method: Optional[Method] = None) -> str:
    if spot.id not in scene.afford_spots:
        return (
            f"(No story: {spot.phrase} is not part of {scene.place}, so the quest "
            f"would have no honest path there.)"
        )
    if not cause_allows(cause, spot):
        return (
            f"(No story: {cause.label} would not reasonably move the model to "
            f"{spot.phrase}. Pick a spot that matches the cause.)"
        )
    if method is not None and method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Choose a clue-based search.)"
        )
    if method is not None and not method_fits(method, cause, spot):
        return (
            f"(No story: {method.id} does not fit the clue left by {cause.label} "
            f"or the kind of place being searched.)"
        )
    return "(No story: this combination does not form a reasonable detective quest.)"


def predict_spot(scene: Scene, cause: Cause, spot: Spot, method: Method) -> dict:
    if spot.id not in scene.afford_spots:
        return {"reachable": False, "reason": "not_in_scene"}
    if not cause_allows(cause, spot):
        return {"reachable": False, "reason": "cause_mismatch"}
    if not method_fits(method, cause, spot):
        return {"reachable": False, "reason": "method_mismatch"}
    return {"reachable": True, "spot": spot.id}


def introduce(world: World, hero: Entity, helper: Entity, item: ModelItem) -> None:
    world.say(
        f"{hero.id} had set {item.phrase} on a small table in {world.scene.place}. "
        f"{world.scene.opening}"
    )
    world.say(
        f"The little model mattered to {hero.pronoun('object')} because {item.tiny_detail}."
    )
    world.say(
        f"Beside the path, {world.scene.poppy_place} nodded in the breeze like bright red lamps."
    )
    hero.memes["pride"] += 1


def vanish(world: World, hero: Entity, item: ModelItem, cause: Cause) -> None:
    model = world.get("model")
    model.meters["missing"] += 1
    world.facts["disappearance_line"] = cause.movement
    propagate(world, narrate=False)
    world.say(
        f"When {hero.id} turned back, the model was gone. {cause.movement}"
    )
    world.say(
        f'{hero.id} drew in a small breath. "A real case," {hero.pronoun()} whispered.'
    )


def inspect_clues(world: World, hero: Entity, helper: Entity, cause: Cause, spot: Spot, method: Method) -> None:
    pred = predict_spot(world.scene, cause, spot, method)
    if not pred["reachable"]:
        raise StoryError("(Internal prediction failure: unreachable search path.)")
    world.facts["predicted_spot"] = spot.id
    if spot.poppy_near:
        world.facts["poppy_helped"] = True
    hero.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id}, {hero.id}'s {helper.label_word}, crouched beside the table and looked slowly around. "
        f'"Look," {helper.pronoun()} said. "{cause.clue_text}"'
    )
    world.say(
        f"{hero.id} narrowed {hero.pronoun('possessive')} eyes the way story detectives do. "
        f"That clue pointed toward {spot.phrase}."
    )


def begin_quest(world: World, hero: Entity, helper: Entity, method: Method, spot: Spot) -> None:
    hero.memes["courage"] += 1
    world.say(
        f"They began their quest at once. {method.text}"
    )
    if spot.poppy_near:
        world.say(
            "Along the way, the poppy petals made the trail easier to read, because their bright color showed where something had brushed past."
        )


def discover(world: World, hero: Entity, item: ModelItem, spot: Spot) -> None:
    model = world.get("model")
    model.meters["found"] += 1
    model.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"At last {hero.id} spotted it: {spot.found_line}"
    )


def assess(world: World, hero: Entity, helper: Entity, item: ModelItem, spot: Spot) -> None:
    model = world.get("model")
    if model.meters["damp"] >= THRESHOLD:
        world.say(
            f"The model was safe, but beads of water clung to it. {helper.id} wrapped it in a cloth, and {hero.id} held it carefully until it felt dry again."
        )
        world.facts["outcome"] = "damp"
    elif model.meters["scuffed"] >= THRESHOLD:
        world.say(
            f"One side had a small scrape, nothing more. {helper.id} smiled and said they could {item.repair}, and {hero.id} felt the case growing lighter."
        )
        world.facts["outcome"] = "scuffed"
    else:
        world.say(
            f"Not even a corner was bent. {hero.id} laughed with relief, because the model looked just as brave and neat as before."
        )
        world.facts["outcome"] = "clean"


def close_case(world: World, hero: Entity, helper: Entity, item: ModelItem) -> None:
    outcome = world.facts["outcome"]
    if outcome == "damp":
        end_line = (
            f"By evening {item.phrase} was back on the table, dry and shining, while the poppy bed glowed red beside it."
        )
    elif outcome == "scuffed":
        end_line = (
            f"By evening {item.phrase} stood in its place again, with one tiny mended mark that made it look like a hero from a solved mystery."
        )
    else:
        end_line = (
            f"By evening {item.phrase} stood exactly where it belonged, and {hero.id} felt taller each time {hero.pronoun()} looked at it."
        )
    world.say(
        f'"Case closed," {hero.id} said. {helper.id} tapped the table once like a judge with a gavel.'
    )
    world.say(end_line)


def tell(
    scene: Scene,
    item: ModelItem,
    cause: Cause,
    spot: Spot,
    method: Method,
    hero_name: str = "Nora",
    hero_type: str = "girl",
    helper_type: str = "father",
    delay: int = 0,
) -> World:
    world = World(scene)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        role="hero",
        traits=["careful", "curious"],
        attrs={},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        traits=["calm"],
        attrs={},
    ))
    model = world.add(Entity(
        id="model",
        kind="thing",
        type="model",
        label=item.label,
        phrase=item.phrase,
        role="missing_item",
        attrs={
            "wet_spot": spot.wet,
            "thorny_spot": spot.thorny,
            "high_spot": spot.high,
        },
    ))
    world.add(Entity(
        id="spot",
        kind="thing",
        type="spot",
        label=spot.label,
        phrase=spot.phrase,
        attrs={},
    ))
    world.add(Entity(
        id="poppies",
        kind="thing",
        type="flower",
        label="poppies",
        phrase="the poppy bed",
        attrs={"bright": True},
    ))

    world.facts["cause_id"] = cause.id
    world.facts["spot_id"] = spot.id
    world.facts["method_id"] = method.id
    world.facts["delay"] = delay
    world.facts["item"] = item
    world.facts["scene"] = scene
    world.facts["cause"] = cause
    world.facts["spot"] = spot
    world.facts["method"] = method

    introduce(world, hero, helper, item)
    world.para()
    vanish(world, hero, item, cause)
    inspect_clues(world, hero, helper, cause, spot, method)
    world.para()
    begin_quest(world, hero, helper, method, spot)
    discover(world, hero, item, spot)
    assess(world, hero, helper, item, spot)
    world.para()
    close_case(world, hero, helper, item)

    world.facts.update(
        hero=hero,
        helper=helper,
        model=model,
        found=model.meters["found"] >= THRESHOLD,
        damp=model.meters["damp"] >= THRESHOLD,
        scuffed=model.meters["scuffed"] >= THRESHOLD,
    )
    return world


SCENES = {
    "fair_table": Scene(
        id="fair_table",
        place="the school garden",
        opening="Children were pinning paper ribbons to a fence for the spring fair.",
        poppy_place="a bed of poppy flowers",
        afford_spots={"poppy_patch", "hedge_nook", "rain_barrel"},
        tags={"garden", "fair"},
    ),
    "greenhouse_step": Scene(
        id="greenhouse_step",
        place="the greenhouse path",
        opening="Warm glass panes shone above the herb pots, and the path smelled of wet soil.",
        poppy_place="a row of poppy flowers by the door",
        afford_spots={"poppy_patch", "crate_corner", "rain_barrel"},
        tags={"greenhouse"},
    ),
    "porch_show": Scene(
        id="porch_show",
        place="the front porch",
        opening="A string of tiny flags trembled over the railing as if the porch were hosting its own parade.",
        poppy_place="a pot of poppy flowers by the steps",
        afford_spots={"poppy_patch", "crate_corner", "hedge_nook"},
        tags={"porch"},
    ),
}

MODELS = {
    "boat": ModelItem(
        id="boat",
        label="model boat",
        phrase="the little model boat",
        tiny_detail="it had a painted blue stripe and a paper sail {hero} had folded by hand".replace("{hero}", "the child"),
        repair="touch the scrape with a dab of blue paint",
        tags={"boat", "model"},
    ),
    "fox": ModelItem(
        id="fox",
        label="model fox",
        phrase="the small model fox",
        tiny_detail="its tail had been painted with a careful white tip",
        repair="smooth the scrape and brush on a little orange paint",
        tags={"fox", "model"},
    ),
    "tower": ModelItem(
        id="tower",
        label="model tower",
        phrase="the tiny model tower",
        tiny_detail="its windows were no bigger than raisins and had taken all morning to paint",
        repair="glue the tiny stone edge and color it again",
        tags={"tower", "model"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        label="a gust of wind",
        clue_tag="petal",
        clue_text="the poppy petals are scattered in one little line, as if the wind pushed something through them",
        movement="A gust of wind had rattled the tablecloth and sent something skittering away.",
        can_hide={"poppy_patch", "rain_barrel", "crate_corner"},
        tags={"wind", "petal"},
    ),
    "kitten": Cause(
        id="kitten",
        label="a curious kitten",
        clue_tag="paw",
        clue_text="there are tiny pawprints in the dust, and one red poppy petal is caught beside them",
        movement="Somewhere nearby, a kitten gave an innocent little mew.",
        can_hide={"poppy_patch", "hedge_nook", "crate_corner"},
        tags={"kitten", "paw"},
    ),
    "crow": Cause(
        id="crow",
        label="a nosy crow",
        clue_tag="feather",
        clue_text="a black feather lies by the table leg, and the petals are bent upward instead of down",
        movement="Overhead, a crow flapped from the railing and croaked as if it knew more than it meant to say.",
        can_hide={"hedge_nook", "rain_barrel"},
        tags={"crow", "feather"},
    ),
}

SPOTS = {
    "poppy_patch": Spot(
        id="poppy_patch",
        label="poppy patch",
        phrase="the soft earth under the poppy flowers",
        found_line="half-hidden under the poppy leaves, right where the red petals made a bright tent over it",
        trait="ground",
        wet=False,
        thorny=False,
        high=False,
        poppy_near=True,
        tags={"poppy", "ground"},
    ),
    "hedge_nook": Spot(
        id="hedge_nook",
        label="hedge nook",
        phrase="a dark nook in the hedge",
        found_line="caught in the hedge nook, with one leaf tucked against its side",
        trait="thorny",
        wet=False,
        thorny=True,
        high=False,
        poppy_near=False,
        tags={"hedge"},
    ),
    "rain_barrel": Spot(
        id="rain_barrel",
        label="rain barrel rim",
        phrase="the rim of the rain barrel",
        found_line="resting on the rain barrel rim, safe but shiny with water",
        trait="high_wet",
        wet=True,
        thorny=False,
        high=True,
        poppy_near=False,
        tags={"water", "high"},
    ),
    "crate_corner": Spot(
        id="crate_corner",
        label="crate corner",
        phrase="the shadowy corner behind a wooden crate",
        found_line="behind the crate corner, as if it had hidden there to hear the whole mystery being solved",
        trait="hidden",
        wet=False,
        thorny=False,
        high=False,
        poppy_near=False,
        tags={"crate"},
    ),
}

METHODS = {
    "follow_petals": Method(
        id="follow_petals",
        sense=3,
        clue_tag="petal",
        needs_high=False,
        text="They followed the bent stems and stray petals one by one, never hurrying past a clue.",
        qa_text="They followed the line of bent poppy petals to the hiding place.",
        tags={"petal", "trail"},
    ),
    "follow_pawprints": Method(
        id="follow_pawprints",
        sense=3,
        clue_tag="paw",
        needs_high=False,
        text="They searched low and slow, tracing the neat little pawprints as if each one were a word in a secret note.",
        qa_text="They traced the tiny pawprints until the trail ended at the hiding place.",
        tags={"paw", "trail"},
    ),
    "look_up_with_stool": Method(
        id="look_up_with_stool",
        sense=4,
        clue_tag="feather",
        needs_high=True,
        text="Helper fetched a steady stool, held it firm, and together they checked the high places where a bird might leave stolen treasure.",
        qa_text="They used a steady stool and searched the high places the feather clue suggested.",
        tags={"feather", "high"},
    ),
    "ground_scan": Method(
        id="ground_scan",
        sense=2,
        clue_tag="feather",
        needs_high=False,
        text="They scanned every low corner first, ruling places out like patient detectives.",
        qa_text="They ruled out the low corners before finding the clue's true path.",
        tags={"search"},
    ),
    "guess_randomly": Method(
        id="guess_randomly",
        sense=1,
        clue_tag="petal",
        needs_high=False,
        text="They pointed at places at random and hoped luck would do the thinking.",
        qa_text="They guessed instead of reading clues.",
        tags={"guess"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Maya", "Zoe", "Ella", "Poppy", "Ava", "Lucy"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Sam", "Eli", "Noah", "Finn"]


@dataclass
class StoryParams:
    scene: str
    model_item: str
    cause: str
    spot: str
    method: str
    hero_name: str
    hero_gender: str
    helper_type: str
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
    "model": [
        (
            "What is a model toy or model figure?",
            "A model is a small version of something bigger, like a boat, an animal, or a tower. People make them carefully so the tiny parts look real."
        )
    ],
    "poppy": [
        (
            "What is a poppy?",
            "A poppy is a flower with soft petals, often bright red. Its petals are light, so wind can move them easily."
        )
    ],
    "wind": [
        (
            "How can wind move small things?",
            "A strong gust of wind can push or roll very light objects. If something is tiny and loose, the wind may carry it farther than you expect."
        )
    ],
    "kitten": [
        (
            "Why might a kitten carry off a small toy?",
            "Kittens are curious and like to bat or carry little things. A tiny toy can look like an exciting game to them."
        )
    ],
    "crow": [
        (
            "Why do crows pick up shiny or interesting things?",
            "Crows are clever birds, and they often inspect unusual objects. If something looks bright or strange, a crow may grab it for a moment."
        )
    ],
    "trail": [
        (
            "What is a clue trail?",
            "A clue trail is a set of little signs that point the same way, like prints, petals, or a feather. A detective follows those signs instead of guessing."
        )
    ],
    "repair": [
        (
            "Can a small scratch on a toy model be fixed?",
            "Often it can. A grown-up can help glue a loose part or touch up the paint so the model looks better again."
        )
    ],
    "water": [
        (
            "Why should a paper part be dried quickly?",
            "Paper gets weak when it stays wet. Drying it quickly helps keep it from bending or tearing."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a journey with a clear goal. In a story, the hero keeps going step by step until the important thing is found or done."
        )
    ],
}
KNOWLEDGE_ORDER = ["model", "poppy", "quest", "trail", "wind", "kitten", "crow", "water", "repair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item"]
    cause = f["cause"]
    spot = f["spot"]
    return [
        f'Write a short detective story for a 3-to-5-year-old where a child goes on a quest to find a missing {item.label}. Include the words "model" and "poppy".',
        f"Tell a gentle mystery where {hero.id} notices a missing {item.label}, reads clues near poppy flowers, and solves the case before the day is over.",
        f"Write a child-facing detective tale in which {cause.label} sends a tiny model toward {spot.phrase}, and a careful search leads to a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item = f["item"]
    cause = f["cause"]
    spot = f["spot"]
    method = f["method"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child who treated a missing {item.label} like a detective case. {helper.id}, {hero.id}'s {helper.label_word}, helped read the clues."
        ),
        (
            f"Why did {hero.id} begin a quest?",
            f"{hero.id} turned around and saw that the {item.label} was gone. That missing model gave {hero.pronoun('object')} a real mystery to solve."
        ),
        (
            "What clue helped them know where to search?",
            f"They noticed that {cause.clue_text}. That clue matched what had happened and pointed them toward {spot.phrase}."
        ),
        (
            "How did they solve the case?",
            f"{method.qa_text} They acted like careful detectives, because they let the clue lead the search instead of guessing."
        ),
    ]
    if outcome == "damp":
        qa.append((
            f"What shape was the {item.label} in when they found it?",
            f"It was safe, but it had become damp from the wet place where it landed. They dried it quickly, which mattered because tiny paper or painted parts can bend if they stay wet."
        ))
    elif outcome == "scuffed":
        qa.append((
            f"What happened to the {item.label} on the quest?",
            f"It came back with a small scrape from the rough place where it had been stuck. The mark was tiny, and {helper.id} knew they could fix it."
        ))
    else:
        qa.append((
            f"How did the story end for the {item.label}?",
            f"They found it in time, and it was still neat and whole. The ending feels happy because the quest changed worry into relief without ruining the model."
        ))
    if f.get("poppy_helped"):
        qa.append((
            "How did the poppy flowers matter in the mystery?",
            "The poppy flowers were not just decoration. Their petals and bent stems helped show the path the missing model had taken."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"model", "quest"}
    spot = f["spot"]
    cause = f["cause"]
    method = f["method"]
    if spot.poppy_near:
        tags.add("poppy")
    if cause.id == "wind":
        tags.add("wind")
    if cause.id == "kitten":
        tags.add("kitten")
    if cause.id == "crow":
        tags.add("crow")
    if "trail" in method.tags or "paw" in method.tags or "petal" in method.tags:
        tags.add("trail")
    if spot.wet:
        tags.add("water")
    if f["outcome"] == "scuffed":
        tags.add("repair")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in ent.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in world.facts.items() if k not in {'hero', 'helper', 'model', 'item', 'scene', 'cause', 'spot', 'method'})}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="fair_table",
        model_item="boat",
        cause="wind",
        spot="poppy_patch",
        method="follow_petals",
        hero_name="Nora",
        hero_gender="girl",
        helper_type="father",
        delay=0,
    ),
    StoryParams(
        scene="porch_show",
        model_item="fox",
        cause="kitten",
        spot="hedge_nook",
        method="follow_pawprints",
        hero_name="Ben",
        hero_gender="boy",
        helper_type="mother",
        delay=1,
    ),
    StoryParams(
        scene="greenhouse_step",
        model_item="tower",
        cause="crow",
        spot="rain_barrel",
        method="look_up_with_stool",
        hero_name="Maya",
        hero_gender="girl",
        helper_type="aunt",
        delay=1,
    ),
    StoryParams(
        scene="porch_show",
        model_item="boat",
        cause="wind",
        spot="crate_corner",
        method="follow_petals",
        hero_name="Leo",
        hero_gender="boy",
        helper_type="uncle",
        delay=0,
    ),
    StoryParams(
        scene="fair_table",
        model_item="fox",
        cause="crow",
        spot="rain_barrel",
        method="look_up_with_stool",
        hero_name="Poppy",
        hero_gender="girl",
        helper_type="mother",
        delay=2,
    ),
]


def outcome_of(params: StoryParams) -> str:
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    return spot_damage_outcome(SPOTS[params.spot], params.delay)


ASP_RULES = r"""
valid(Scene, Cause, Spot, Method) :-
    scene(Scene), cause(Cause), spot(Spot), method(Method),
    affords(Scene, Spot), hides(Cause, Spot),
    clue_of(Cause, Tag), clue_of_method(Method, Tag),
    sensible(Method),
    not bad_high(Method, Spot).

bad_high(Method, Spot) :- needs_high(Method), not high(Spot).
bad_high(ground_scan, Spot) :- high(Spot).

outcome(Spot, Delay, damp) :-
    spot(Spot), wet(Spot), delay(Delay), Delay >= 1.
outcome(Spot, Delay, scuffed) :-
    spot(Spot), thorny(Spot), delay(Delay), Delay >= 1,
    not outcome(Spot, Delay, damp).
outcome(Spot, Delay, scuffed) :-
    spot(Spot), high(Spot), delay(Delay), Delay >= 2,
    not outcome(Spot, Delay, damp).
outcome(Spot, Delay, clean) :-
    spot(Spot), delay(Delay),
    not outcome(Spot, Delay, damp),
    not outcome(Spot, Delay, scuffed).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        for spot_id in sorted(scene.afford_spots):
            lines.append(asp.fact("affords", scene_id, spot_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("clue_of", cause_id, cause.clue_tag))
        for spot_id in sorted(cause.can_hide):
            lines.append(asp.fact("hides", cause_id, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        if spot.wet:
            lines.append(asp.fact("wet", spot_id))
        if spot.thorny:
            lines.append(asp.fact("thorny", spot_id))
        if spot.high:
            lines.append(asp.fact("high", spot_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("clue_of_method", method_id, method.clue_tag))
        if method.needs_high:
            lines.append(asp.fact("needs_high", method_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append("sensible(M) :- method(M), sense(M,S), sense_min(Min), S >= Min.")
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("delay", params.delay),
        asp.fact("chosen_spot", params.spot),
        "picked(O) :- chosen_spot(S), delay(D), outcome(S,D,O).",
    ])
    model = asp.one_model(asp_program(extra, "#show picked/1."))
    atoms = asp.atoms(model, "picked")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
        except Exception as err:
            rc = 1
            print(f"ERROR during outcome parity check: {err}")
            return rc
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-story quest: a child follows clues near poppy flowers to find a missing model."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--model-item", dest="model_item", choices=MODELS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the model stays missing before it is found")
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
    if args.method is not None:
        method = METHODS[args.method]
        if method.sense < SENSE_MIN:
            raise StoryError(
                f"(Refusing method '{args.method}': it scores too low on common sense "
                f"(sense={method.sense} < {SENSE_MIN}).)"
            )

    if args.scene and args.cause and args.spot:
        method = METHODS[args.method] if args.method else None
        if not cause_allows(CAUSES[args.cause], SPOTS[args.spot]) or args.spot not in SCENES[args.scene].afford_spots:
            raise StoryError(explain_rejection(SCENES[args.scene], CAUSES[args.cause], SPOTS[args.spot], method))
        if method is not None and not method_fits(method, CAUSES[args.cause], SPOTS[args.spot]):
            raise StoryError(explain_rejection(SCENES[args.scene], CAUSES[args.cause], SPOTS[args.spot], method))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.cause is None or combo[1] == args.cause)
        and (args.spot is None or combo[2] == args.spot)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, cause_id, spot_id, method_id = rng.choice(sorted(combos))
    model_item = args.model_item or rng.choice(sorted(MODELS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    if args.hero_name:
        hero_name = args.hero_name
    else:
        hero_name = rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    return StoryParams(
        scene=scene_id,
        model_item=model_item,
        cause=cause_id,
        spot=spot_id,
        method=method_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Invalid scene: {params.scene})")
    if params.model_item not in MODELS:
        raise StoryError(f"(Invalid model item: {params.model_item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Invalid cause: {params.cause})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Invalid spot: {params.spot})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if params.helper_type not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Invalid helper type: {params.helper_type})")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(Invalid hero gender: {params.hero_gender})")
    if params.delay not in {0, 1, 2}:
        raise StoryError(f"(Invalid delay: {params.delay})")

    scene = SCENES[params.scene]
    item = MODELS[params.model_item]
    cause = CAUSES[params.cause]
    spot = SPOTS[params.spot]
    method = METHODS[params.method]

    if method.sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing method '{params.method}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}).)"
        )
    if params.spot not in scene.afford_spots or not cause_allows(cause, spot) or not method_fits(method, cause, spot):
        raise StoryError(explain_rejection(scene, cause, spot, method))

    world = tell(
        scene=scene,
        item=item,
        cause=cause,
        spot=spot,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        helper_type=params.helper_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/4.\n#show picked/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, cause, spot, method) combos:\n")
        for scene, cause, spot, method in combos:
            print(f"  {scene:16} {cause:8} {spot:12} {method}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.hero_name}: {p.model_item} at {p.scene} "
                f"({p.cause}, {p.spot}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
