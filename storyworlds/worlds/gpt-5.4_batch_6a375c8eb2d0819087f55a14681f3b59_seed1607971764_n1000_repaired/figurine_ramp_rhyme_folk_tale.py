#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py
===========================================================

A standalone story world for a tiny folk-tale domain about a child, a fragile
figurine, and a ramp built to reach a high family perch before a festival
evening. The story uses state, not slot-swaps: a figurine may glide safely up
the ramp, wobble and chip, or be carried so carefully that the old rhyme
becomes the heart of the tale.

The world models a practical question in child-scale terms:
when is a ramp and a helper sensible for moving a delicate thing upward?

Run it
------
    python storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py
    python storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py --figurine moon_cat --ramp satin_ramp
    python storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/figurine_ramp_rhyme_folk_tale.py --verify
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
        female = {"girl", "woman", "grandmother", "mother", "aunt"}
        male = {"boy", "man", "grandfather", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.type)
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
class Figurine:
    id: str
    label: str
    phrase: str
    material: str
    weight: int
    fragility: int
    blessing: str
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
class Ramp:
    id: str
    label: str
    phrase: str
    surface: str
    sturdiness: int
    grip: int
    image: str
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
class Helper:
    id: str
    label: str
    phrase: str
    sense: int
    power: int
    prep: str
    success: str
    catch_fail: str
    mend: str
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
class Slope:
    id: str
    label: str
    steepness: int
    opening: str
    climb: str
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


def _r_slide_or_arrive(world: World) -> list[str]:
    figurine = world.get("figurine")
    if figurine.meters["moving"] < THRESHOLD:
        return []
    sig = ("travel",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    support = figurine.meters["support"]
    demand = figurine.meters["demand"]
    if support >= demand:
        figurine.meters["placed"] += 1
        world.get("child").memes["hope"] += 1
        world.get("elder").memes["pride"] += 1
        return ["__placed__"]
    figurine.meters["slipping"] += 1
    world.get("child").memes["fear"] += 1
    return ["__slipping__"]


def _r_chip(world: World) -> list[str]:
    figurine = world.get("figurine")
    if figurine.meters["slipping"] < THRESHOLD:
        return []
    sig = ("chip",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    figurine.meters["chipped"] += 1
    world.get("child").memes["sorrow"] += 1
    world.get("elder").memes["calm"] += 1
    return ["__chipped__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="slide_or_arrive", tag="physical", apply=_r_slide_or_arrive),
    Rule(name="chip", tag="physical", apply=_r_chip),
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
        for sent in produced:
            if not sent.startswith("__"):
                world.say(sent)
    return produced


def sturdy_enough(figurine: Figurine, ramp: Ramp) -> bool:
    return ramp.sturdiness >= figurine.weight


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def support_score(ramp: Ramp, helper: Helper) -> int:
    return ramp.grip + helper.power


def demand_score(figurine: Figurine, slope: Slope) -> int:
    return figurine.fragility + slope.steepness


def outcome_of(params: "StoryParams") -> str:
    if params.figurine not in FIGURINES:
        raise StoryError(f"(Unknown figurine: {params.figurine})")
    if params.ramp not in RAMPS:
        raise StoryError(f"(Unknown ramp: {params.ramp})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.slope not in SLOPES:
        raise StoryError(f"(Unknown slope: {params.slope})")
    figurine = FIGURINES[params.figurine]
    ramp = RAMPS[params.ramp]
    helper = HELPERS[params.helper]
    slope = SLOPES[params.slope]
    if not sturdy_enough(figurine, ramp):
        raise StoryError(explain_rejection(figurine, ramp, helper))
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))
    return "placed" if support_score(ramp, helper) >= demand_score(figurine, slope) else "mended"


def predict_trip(world: World) -> dict:
    sim = world.copy()
    figurine = sim.get("figurine")
    figurine.meters["moving"] += 1
    propagate(sim, narrate=False)
    return {
        "placed": figurine.meters["placed"] >= THRESHOLD,
        "slipping": figurine.meters["slipping"] >= THRESHOLD,
        "chipped": figurine.meters["chipped"] >= THRESHOLD,
    }


def folk_rhyme() -> str:
    return '"Slow and low, and safe we go; steady and slight through the lantern light."'  # noqa: E501


def opening(world: World, child: Entity, elder: Entity, figurine: Entity,
            figurine_cfg: Figurine, slope: Slope) -> None:
    child.memes["duty"] += 1
    world.say(
        f"In the years when evening bells were small and clear, there lived a child "
        f"named {child.id} in a cottage under the hill. On the night of the lantern feast, "
        f"{elder.label_word} brought out {figurine_cfg.phrase}, a {figurine_cfg.material} figurine "
        f"kept all year on a folded blue cloth."
    )
    world.say(
        f'"Set it on the high window ledge before moonrise," said {elder.label_word}, '
        f'"for our house remembers {figurine_cfg.blessing} when that little keeper watches the road."'
    )
    world.say(
        f"The ledge was above {child.id}'s reach, and {slope.opening}."
    )


def build_ramp(world: World, child: Entity, ramp_cfg: Ramp, slope: Slope) -> None:
    child.memes["cleverness"] += 1
    world.say(
        f"So {child.id} fetched {ramp_cfg.phrase} and made a ramp from the chest to the ledge. "
        f"It was {slope.label}, and the {ramp_cfg.label} {slope.climb}."
    )
    world.say(ramp_cfg.image)


def warning(world: World, child: Entity, elder: Entity,
            figurine_cfg: Figurine, ramp_cfg: Ramp, helper_cfg: Helper) -> None:
    pred = predict_trip(world)
    world.facts["predicted_slip"] = pred["slipping"]
    world.facts["predicted_chip"] = pred["chipped"]
    elder.memes["care"] += 1
    if pred["slipping"]:
        world.say(
            f"{elder.label_word.capitalize()} watched the small road of wood and said, "
            f'{folk_rhyme()}'
        )
        world.say(
            f'"A {figurine_cfg.label} does not like hurry on a {ramp_cfg.surface} path," '
            f"{elder.pronoun()} added. "
            f'"Take {helper_cfg.phrase}, and let care walk beside courage."'
        )
    else:
        world.say(
            f"{elder.label_word.capitalize()} nodded at the careful little roadway and said, "
            f'{folk_rhyme()}'
        )


def prepare(world: World, child: Entity, helper_cfg: Helper) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{child.id} listened, {helper_cfg.prep}, and took one long breath before touching the treasure."
    )


def send_up(world: World, child: Entity, figurine: Entity, ramp_cfg: Ramp, slope: Slope) -> None:
    child.memes["bravery"] += 1
    figurine.meters["moving"] += 1
    world.say(
        f"Then {child.id} set the figurine at the foot of the ramp. Up it went, "
        f"{slope.label} and slow, while the lamp flame trembled on the wall."
    )
    world.say(
        f"For a blink it looked as though the little image were climbing a moon-road all by itself."
    )


def narrate_success(world: World, child: Entity, elder: Entity,
                    helper_cfg: Helper, figurine_cfg: Figurine) -> None:
    world.say(helper_cfg.success)
    world.say(
        f"The figurine reached the ledge and stood facing the lane, quiet as a promise. "
        f"{elder.label_word.capitalize()} smiled, and {child.id}'s heart grew light again."
    )
    world.say(
        f'Together they whispered, {folk_rhyme()}'
    )
    world.say(
        f"All that night the cottage windows shone, and anyone passing by said the house looked blessed by {figurine_cfg.blessing}."
    )


def narrate_mended(world: World, child: Entity, elder: Entity,
                   helper_cfg: Helper, figurine_cfg: Figurine) -> None:
    world.say(helper_cfg.catch_fail)
    world.say(
        f"The figurine did not shatter, but a small chip showed white along one edge, "
        f"and tears sprang into {child.id}'s eyes."
    )
    world.say(
        f'Yet {elder.label_word} only gathered {child.pronoun("object")} close and said, '
        f'"A wise heart does not hide a crack. It mends it."'
    )
    world.say(helper_cfg.mend)
    world.say(
        f"When the paste had set, they lifted the little figure together and placed it on the ledge by hand. "
        f"The mark stayed faintly there, like a silver seed of memory."
    )
    world.say(
        f'Together they whispered, {folk_rhyme()}'
    )
    world.say(
        f"After that, people who saw the figurine said it guarded not only {figurine_cfg.blessing}, "
        f"but patience too."
    )


def tell(figurine_cfg: Figurine, ramp_cfg: Ramp, helper_cfg: Helper, slope: Slope,
         child_name: str = "Mira", child_type: str = "girl",
         elder_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder"))
    figurine = world.add(Entity(id="figurine", type="figurine", label=figurine_cfg.label))
    ramp = world.add(Entity(id="ramp", type="ramp", label=ramp_cfg.label))
    helper = world.add(Entity(id="helper", type="helper", label=helper_cfg.label))
    ledge = world.add(Entity(id="ledge", type="place", label="window ledge"))

    figurine.meters["support"] = float(support_score(ramp_cfg, helper_cfg))
    figurine.meters["demand"] = float(demand_score(figurine_cfg, slope))
    figurine.meters["placed"] = 0.0
    figurine.meters["slipping"] = 0.0
    figurine.meters["chipped"] = 0.0
    figurine.meters["moving"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["hope"] = 0.0
    child.memes["sorrow"] = 0.0
    elder.memes["care"] = 0.0
    elder.memes["pride"] = 0.0
    elder.memes["calm"] = 0.0
    world.facts["predicted_slip"] = False
    world.facts["predicted_chip"] = False

    opening(world, child, elder, figurine, figurine_cfg, slope)
    build_ramp(world, child, ramp_cfg, slope)

    world.para()
    warning(world, child, elder, figurine_cfg, ramp_cfg, helper_cfg)
    prepare(world, child, helper_cfg)

    world.para()
    send_up(world, child, figurine, ramp_cfg, slope)
    propagate(world, narrate=False)

    if figurine.meters["placed"] >= THRESHOLD:
        world.para()
        narrate_success(world, child, elder, helper_cfg, figurine_cfg)
        outcome = "placed"
    else:
        world.para()
        narrate_mended(world, child, elder, helper_cfg, figurine_cfg)
        outcome = "mended"

    world.facts.update(
        child=child,
        elder=elder,
        figurine=figurine,
        ramp=ramp,
        helper=helper,
        ledge=ledge,
        figurine_cfg=figurine_cfg,
        ramp_cfg=ramp_cfg,
        helper_cfg=helper_cfg,
        slope=slope,
        outcome=outcome,
        rhyme=folk_rhyme(),
        support=int(figurine.meters["support"]),
        demand=int(figurine.meters["demand"]),
    )
    return world


FIGURINES = {
    "swallow_clay": Figurine(
        id="swallow_clay",
        label="swallow",
        phrase="a clay swallow with painted wings",
        material="clay",
        weight=1,
        fragility=3,
        blessing="safe returns",
        tags={"figurine", "clay", "bird"},
    ),
    "fox_wood": Figurine(
        id="fox_wood",
        label="fox",
        phrase="a carved wooden fox with a bright tail",
        material="wood",
        weight=2,
        fragility=1,
        blessing="quick wits",
        tags={"figurine", "wood", "fox"},
    ),
    "moon_cat": Figurine(
        id="moon_cat",
        label="moon-cat",
        phrase="a porcelain moon-cat with a blue collar",
        material="porcelain",
        weight=1,
        fragility=4,
        blessing="peaceful sleep",
        tags={"figurine", "porcelain", "cat"},
    ),
}

RAMPS = {
    "pine_board": Ramp(
        id="pine_board",
        label="pine board",
        phrase="a pine board from the bread bench",
        surface="grained",
        sturdiness=2,
        grip=2,
        image="The board smelled of sap, and its grain gave the tiny feet of the journey something to trust.",
        tags={"ramp", "wood"},
    ),
    "bark_plank": Ramp(
        id="bark_plank",
        label="bark plank",
        phrase="a bark-edged plank from the shed",
        surface="rough",
        sturdiness=1,
        grip=2,
        image="Its bark held a little bite, so nothing slid quickly unless it was pushed by foolish hands.",
        tags={"ramp", "bark"},
    ),
    "reed_board": Ramp(
        id="reed_board",
        label="reed board",
        phrase="a reed-woven board used for drying herbs",
        surface="springy",
        sturdiness=2,
        grip=1,
        image="The woven reeds bowed a little in the middle, as if the ramp itself were thinking hard.",
        tags={"ramp", "reed"},
    ),
    "satin_ramp": Ramp(
        id="satin_ramp",
        label="satin ramp",
        phrase="a satin-covered tray",
        surface="slick",
        sturdiness=1,
        grip=0,
        image="It shone beautifully, but beauty is not always the same thing as footing.",
        tags={"ramp", "slick"},
    ),
}

HELPERS = {
    "felt_nest": Helper(
        id="felt_nest",
        label="felt nest",
        phrase="a round felt nest at the bottom",
        sense=3,
        power=2,
        prep="set a round felt nest below the ledge",
        success="The felt nest kept the little traveler from skidding, and the climb finished with hardly a whisper.",
        catch_fail="The figurine wobbled, slid, and dropped into the felt nest with a soft little thup.",
        mend="Grandmother mixed paste with a pinch of white clay and smoothed the tiny wound until it looked like dawn on a shell.",
        tags={"felt", "catcher", "mending"},
    ),
    "side_rails": Helper(
        id="side_rails",
        label="side rails",
        phrase="two spoon-thin side rails",
        sense=3,
        power=3,
        prep="tied on two spoon-thin side rails with kitchen string",
        success="The side rails held the path true, and the figurine glided between them as neatly as a boat in a narrow canal.",
        catch_fail="Even with the rails, the figurine knocked once against the edge and came down with a sad little click.",
        mend="Grandfather warmed a little beeswax, pressed it into the nick, and rubbed the place until it only glimmered when the lamp caught it.",
        tags={"rails", "support", "mending"},
    ),
    "steady_hands": Helper(
        id="steady_hands",
        label="steady hands",
        phrase="two steady guiding hands",
        sense=2,
        power=2,
        prep="asked the elder to guide the climb with two steady hands nearby",
        success="The elder's hands never touched the figurine, but they shadowed it like careful wings, and that was enough.",
        catch_fail="The little figure slipped against one careful hand and was caught before it struck the floor, though one edge was still nicked.",
        mend="Together they polished the nick with chalk and paste until the line looked gentler than before.",
        tags={"hands", "help", "mending"},
    ),
    "broom_hook": Helper(
        id="broom_hook",
        label="broom hook",
        phrase="a broom hook held from below",
        sense=1,
        power=1,
        prep="held a broom hook under the ramp",
        success="The broom hook somehow held long enough, though no wise elder would praise such a plan.",
        catch_fail="The hook jerked, the ramp quivered, and the figurine bounced badly.",
        mend="They did what they could, but it was the wrong tool from the start.",
        tags={"broom", "bad_idea"},
    ),
}

SLOPES = {
    "low": Slope(
        id="low",
        label="low",
        steepness=0,
        opening="the chest could be drawn close beneath it",
        climb="rose in a gentle line",
        tags={"gentle"},
    ),
    "middle": Slope(
        id="middle",
        label="middle",
        steepness=1,
        opening="the chest stood a little way off, so the way upward needed care",
        climb="rose at a listening slant",
        tags={"middle"},
    ),
    "steep": Slope(
        id="steep",
        label="steep",
        steepness=2,
        opening="the chest sat far below, so the climb had to be steep",
        climb="rose sharp as a goat path",
        tags={"steep"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Anya", "Tala", "Nessa", "Orla"]
BOY_NAMES = ["Ivo", "Niko", "Pavel", "Tarin", "Oren", "Milan"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for fig_id, fig in FIGURINES.items():
        for ramp_id, ramp in RAMPS.items():
            for helper_id, helper in HELPERS.items():
                if sturdy_enough(fig, ramp) and helper.sense >= SENSE_MIN:
                    combos.append((fig_id, ramp_id, helper_id))
    return combos


@dataclass
class StoryParams:
    figurine: str
    ramp: str
    helper: str
    slope: str
    child_name: str
    child_type: str
    elder_type: str
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
    "figurine": [
        (
            "What is a figurine?",
            "A figurine is a small figure made to look like a person or animal. People often keep one as a decoration or a special keepsake.",
        )
    ],
    "ramp": [
        (
            "What is a ramp?",
            "A ramp is a sloping path that goes up or down. It helps something move gradually instead of being lifted straight up.",
        )
    ],
    "clay": [
        (
            "Why can clay break easily?",
            "Clay can feel hard, but once it is dry it can chip or crack if it falls or knocks against something. That is why clay things must be handled gently.",
        )
    ],
    "porcelain": [
        (
            "Why is porcelain fragile?",
            "Porcelain is smooth and pretty, but it can break if it is dropped or bumped. A fragile thing needs slow, careful hands.",
        )
    ],
    "wood": [
        (
            "Why is wood often sturdier than clay?",
            "Wood can still be damaged, but it usually does not chip as easily as clay or porcelain. That makes a wooden toy or figure a little tougher.",
        )
    ],
    "mending": [
        (
            "What does it mean to mend something?",
            "To mend something is to fix it after it is torn, cracked, or chipped. Mending shows care because you do not throw the thing away at once.",
        )
    ],
    "patience": [
        (
            "Why does moving slowly sometimes help?",
            "Going slowly gives you time to notice wobbles and trouble before they grow worse. Patience often keeps fragile things safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["figurine", "ramp", "clay", "porcelain", "wood", "mending", "patience"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    figurine_cfg = f["figurine_cfg"]
    ramp_cfg = f["ramp_cfg"]
    slope = f["slope"]
    if f["outcome"] == "placed":
        return [
            f'Write a short folk tale for a young child that includes the words "figurine" and "ramp" and uses a gentle rhyme as advice.',
            f"Tell a folk-style story where {child.id} must guide a {figurine_cfg.label} figurine up a {slope.label} ramp to a high ledge before evening.",
            f"Write a story with a repeated rhyme about moving carefully, where a child uses a {ramp_cfg.label} and succeeds through patience.",
        ]
    return [
        f'Write a short folk tale for a young child that includes the words "figurine" and "ramp" and uses a gentle rhyme after a small mishap.',
        f"Tell a folk-style story where {child.id} tries to send a fragile {figurine_cfg.label} figurine up a {slope.label} ramp, and it chips but is lovingly mended.",
        f"Write a rhyming cautionary tale where a child learns that care matters more than hurry when moving something delicate.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    figurine_cfg = f["figurine_cfg"]
    ramp_cfg = f["ramp_cfg"]
    helper_cfg = f["helper_cfg"]
    slope = f["slope"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in a cottage under the hill, and {elder.label_word} who trusted {child.pronoun('object')} with a special figurine. The little figure mattered because the family believed it watched over the house.",
        ),
        (
            "Why did the child build a ramp?",
            f"{child.id} needed a way to get the figurine to a high window ledge that was out of reach. The ramp turned a hard lift into a careful climb.",
        ),
        (
            f"What warning did {elder.label_word} give?",
            f"{elder.label_word.capitalize()} reminded {child.id} to move slowly and carefully, using the rhyme about going slow and low. The warning came because a fragile {figurine_cfg.label} on a {ramp_cfg.surface} path could slip if anyone hurried.",
        ),
        (
            "What helper did they use, and why?",
            f"They used {helper_cfg.phrase}. That helper was meant to give the climb more support, so the figurine would have a safer journey up the ramp.",
        ),
    ]
    if outcome == "placed":
        qa.append(
            (
                "How did the problem get solved?",
                f"The figurine reached the ledge safely and stood watching the road. It worked because the support from the {ramp_cfg.label} and {helper_cfg.label} was enough for that climb.",
            )
        )
        qa.append(
            (
                f"How did {child.id} feel at the end?",
                f"{child.id} felt relieved and proud. The safe ending showed that patience had carried the little treasure where it needed to go.",
            )
        )
    else:
        qa.append(
            (
                "What happened on the ramp?",
                f"The figurine slipped and took a small chip, though it was caught before it shattered. The climb demanded more care than the ramp and helper could fully give on that steep path.",
            )
        )
        qa.append(
            (
                "How was the problem resolved after the chip?",
                f"{elder.label_word.capitalize()} stayed calm and mended the little figure instead of scolding. Then they placed it on the ledge together, so the story ended with repair and patience instead of loss.",
            )
        )
        qa.append(
            (
                f"What did {child.id} learn?",
                f"{child.id} learned that a delicate thing should not be rushed. The rhyme became a memory of how care can prevent cracks, and how love can mend a mistake when one appears.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"figurine", "ramp", "patience"}
    figurine_cfg = world.facts["figurine_cfg"]
    helper_cfg = world.facts["helper_cfg"]
    if figurine_cfg.material == "clay":
        tags.add("clay")
    elif figurine_cfg.material == "porcelain":
        tags.add("porcelain")
    elif figurine_cfg.material == "wood":
        tags.add("wood")
    if world.facts["outcome"] == "mended" or "mending" in helper_cfg.tags:
        tags.add("mending")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        figurine="swallow_clay",
        ramp="pine_board",
        helper="side_rails",
        slope="middle",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        figurine="fox_wood",
        ramp="reed_board",
        helper="steady_hands",
        slope="steep",
        child_name="Oren",
        child_type="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        figurine="moon_cat",
        ramp="pine_board",
        helper="felt_nest",
        slope="steep",
        child_name="Lina",
        child_type="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        figurine="swallow_clay",
        ramp="bark_plank",
        helper="steady_hands",
        slope="middle",
        child_name="Pavel",
        child_type="boy",
        elder_type="grandfather",
    ),
    StoryParams(
        figurine="moon_cat",
        ramp="reed_board",
        helper="side_rails",
        slope="middle",
        child_name="Nessa",
        child_type="girl",
        elder_type="grandmother",
    ),
]


def explain_rejection(figurine: Figurine, ramp: Ramp, helper: Helper) -> str:
    if not sturdy_enough(figurine, ramp):
        return (
            f"(No story: the {ramp.label} is not sturdy enough for the {figurine.label} figurine. "
            f"A weak ramp would buckle before the tale could become a careful climb.)"
        )
    if helper.sense < SENSE_MIN:
        return explain_helper(helper.id)
    return "(No story: that combination does not make practical sense in this world.)"


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper.id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of these instead: {better}.)"
    )


ASP_RULES = r"""
sturdy(F, R) :- figurine(F), ramp(R), weight(F, W), sturdiness(R, S), S >= W.
sensible(H) :- helper(H), sense(H, X), sense_min(M), X >= M.
valid(F, R, H) :- figurine(F), ramp(R), helper(H), sturdy(F, R), sensible(H).

support(F, R, H, G + P) :- figurine(F), ramp(R), helper(H), grip(R, G), power(H, P).
demand(F, S, Fr + St) :- figurine(F), slope(S), fragility(F, Fr), steepness(S, St).
safe(F, R, H, S) :- support(F, R, H, Sup), demand(F, S, Dem), Sup >= Dem.

outcome(placed) :- chosen_figurine(F), chosen_ramp(R), chosen_helper(H), chosen_slope(S), safe(F, R, H, S).
outcome(mended) :- chosen_figurine(F), chosen_ramp(R), chosen_helper(H), chosen_slope(S), not safe(F, R, H, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for fid, fig in FIGURINES.items():
        lines.append(asp.fact("figurine", fid))
        lines.append(asp.fact("weight", fid, fig.weight))
        lines.append(asp.fact("fragility", fid, fig.fragility))
    for rid, ramp in RAMPS.items():
        lines.append(asp.fact("ramp", rid))
        lines.append(asp.fact("sturdiness", rid, ramp.sturdiness))
        lines.append(asp.fact("grip", rid, ramp.grip))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("power", hid, helper.power))
    for sid, slope in SLOPES.items():
        lines.append(asp.fact("slope", sid))
        lines.append(asp.fact("steepness", sid, slope.steepness))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_figurine", params.figurine),
            asp.fact("chosen_ramp", params.ramp),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_slope", params.slope),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    parser = build_parser()
    cases: list[StoryParams] = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed at seed {seed}")
            break

    mismatches = 0
    for params in cases:
        try:
            py_out = outcome_of(params)
            asp_out = asp_outcome(params)
            if py_out != asp_out:
                mismatches += 1
        except StoryError as err:
            rc = 1
            print(f"Outcome check crashed for {params}: {err}")
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a figurine, a ramp, a rhyme, and a careful folk-tale ending."
    )
    ap.add_argument("--figurine", choices=FIGURINES)
    ap.add_argument("--ramp", choices=RAMPS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--slope", choices=SLOPES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.figurine and args.figurine not in FIGURINES:
        raise StoryError(f"(Unknown figurine: {args.figurine})")
    if args.ramp and args.ramp not in RAMPS:
        raise StoryError(f"(Unknown ramp: {args.ramp})")
    if args.helper and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")
    if args.slope and args.slope not in SLOPES:
        raise StoryError(f"(Unknown slope: {args.slope})")

    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))
    if args.figurine and args.ramp:
        fig = FIGURINES[args.figurine]
        ramp = RAMPS[args.ramp]
        helper = HELPERS[args.helper] if args.helper else sensible_helpers()[0]
        if not sturdy_enough(fig, ramp):
            raise StoryError(explain_rejection(fig, ramp, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.figurine is None or combo[0] == args.figurine)
        and (args.ramp is None or combo[1] == args.ramp)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    figurine_id, ramp_id, helper_id = rng.choice(sorted(combos))
    slope = args.slope or rng.choice(sorted(SLOPES))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])

    return StoryParams(
        figurine=figurine_id,
        ramp=ramp_id,
        helper=helper_id,
        slope=slope,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.figurine not in FIGURINES:
        raise StoryError(f"(Unknown figurine: {params.figurine})")
    if params.ramp not in RAMPS:
        raise StoryError(f"(Unknown ramp: {params.ramp})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.slope not in SLOPES:
        raise StoryError(f"(Unknown slope: {params.slope})")
    figurine_cfg = FIGURINES[params.figurine]
    ramp_cfg = RAMPS[params.ramp]
    helper_cfg = HELPERS[params.helper]
    slope = SLOPES[params.slope]
    if helper_cfg.sense < SENSE_MIN or not sturdy_enough(figurine_cfg, ramp_cfg):
        raise StoryError(explain_rejection(figurine_cfg, ramp_cfg, helper_cfg))

    world = tell(
        figurine_cfg=figurine_cfg,
        ramp_cfg=ramp_cfg,
        helper_cfg=helper_cfg,
        slope=slope,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (figurine, ramp, helper) combos:\n")
        for figurine_id, ramp_id, helper_id in combos:
            print(f"  {figurine_id:13} {ramp_id:11} {helper_id}")
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
            header = f"### {p.child_name}: {p.figurine} on {p.ramp} with {p.helper} ({p.slope}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
