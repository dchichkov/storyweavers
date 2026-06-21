#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py
=================================================================================

A standalone story world for a heartwarming tale about a child, a rainy garden,
and a chrysalis that changes into a butterfly. The world model centers on a
simple, concrete problem: rainwater gathers around a butterfly shelter, and the
child wants to help without hurting the fragile chrysalis. A calm grown-up
chooses a gentle fix, the child remembers the caterpillar from earlier days
(a small flashback beat), and the story ends with a visible transformation.

The seed requested the words "satisfy" and "bail", plus the narrative features
Transformation and Flashback, in a heartwarming style. This world uses:
- "bail" as the child and grown-up bailing rainwater from the tray/saucer,
- "satisfy" in the child's wish to satisfy the butterfly's need for a safe,
  dry place,
- Transformation as chrysalis -> butterfly,
- Flashback as the child remembering the earlier caterpillar stage.

Run it
------
    python storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py
    python storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py --shelter mesh_hamper --response spoon_bail
    python storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py --response shake
    python storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/satisfy_bail_transformation_flashback_heartwarming.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    delicate: bool = False
    can_hold_water: bool = False
    is_stage: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    rain_sound: str
    release_spot: str
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
class Shelter:
    id: str
    label: str
    phrase: str
    tray: str
    hangs_from: str
    delicate: bool = True
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
    gentle: bool
    power: int
    text: str
    qa_text: str
    fail: str
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
class Memory:
    id: str
    past_image: str
    lesson: str
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
class ButterflyKind:
    id: str
    caterpillar: str
    butterfly: str
    wing_color: str
    likes: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    shelter = world.get("shelter")
    stage = world.get("stage")
    if shelter.meters["water_near"] < THRESHOLD:
        return out
    sig = ("risk", shelter.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage.meters["risk"] += 1
    for eid in ("child", "helper"):
        if eid in world.entities:
            world.get(eid).memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    stage = world.get("stage")
    if stage.meters["ready"] < THRESHOLD:
        return out
    if stage.meters["risk"] >= THRESHOLD:
        return out
    sig = ("transform", stage.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stage.meters["opened"] += 1
    butterfly = world.get("butterfly")
    butterfly.meters["present"] += 1
    out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="transform", tag="physical", apply=_r_transform),
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def hazard_at_risk(shelter: Shelter) -> bool:
    return shelter.delicate


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN and r.gentle]


def response_works(response: Response, rain_level: int) -> bool:
    return response.gentle and response.power >= rain_level


def best_response() -> Response:
    return max(sensible_responses(), key=lambda r: (r.power, r.sense))


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for shelter_id, shelter in SHELTERS.items():
            if not hazard_at_risk(shelter):
                continue
            for memory_id in MEMORIES:
                for butterfly_id in BUTTERFLIES:
                    combos.append((setting_id, shelter_id, memory_id, butterfly_id))
    return combos


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_outcome(world: World, response: Response, rain_level: int) -> dict:
    sim = world.copy()
    stage = sim.get("stage")
    shelter = sim.get("shelter")
    shelter.meters["water_near"] = float(rain_level)
    propagate(sim, narrate=False)
    if response.gentle and response.power >= rain_level:
        shelter.meters["water_near"] = 0.0
        stage.meters["risk"] = 0.0
    else:
        if not response.gentle:
            stage.meters["risk"] += 1
            stage.meters["jostled"] += 1
    propagate(sim, narrate=False)
    return {
        "safe": stage.meters["risk"] < THRESHOLD,
        "transforms": sim.get("butterfly").meters["present"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, helper: Entity, shelter: Shelter,
              butterfly: ButterflyKind) -> None:
    child.memes["care"] += 1
    world.say(
        f"After a soft rain, {child.id} and {child.pronoun('possessive')} "
        f"{helper.label_word} stepped onto the porch beside {world.setting.place}."
    )
    world.say(
        f"Under {shelter.hangs_from} hung {shelter.phrase}, and inside it a "
        f"quiet {butterfly.caterpillar} had become a still green chrysalis."
    )
    world.say(
        f"{child.id} pressed close and whispered that {child.pronoun()} wanted to "
        f"satisfy the tiny creature's need for a calm, dry morning."
    )


def notice_problem(world: World, child: Entity, shelter: Shelter, rain_level: int) -> None:
    shelter_ent = world.get("shelter")
    shelter_ent.meters["water_near"] = float(rain_level)
    world.say(
        f"Rain had splashed into {shelter.tray}, and little beads of water shone all around it."
    )
    if rain_level >= 2:
        world.say(
            f'"Oh no," {child.id} said. "The water is getting too close."'
        )
    else:
        world.say(
            f'{child.id} noticed the damp ring first and frowned.'
        )
    propagate(world, narrate=False)


def flashback(world: World, child: Entity, helper: Entity, memory: Memory,
              butterfly: ButterflyKind) -> None:
    child.memes["memory"] += 1
    world.say(
        f"{child.id} remembered another day, not long before."
    )
    world.say(
        f"{memory.past_image} That was when {helper.label_word} had taught "
        f"{child.pronoun('object')} {memory.lesson}."
    )
    world.facts["flashback_used"] = True


def worry_and_wish(world: World, child: Entity, helper: Entity, response: Response) -> None:
    pred = predict_outcome(world, response, int(world.get("shelter").meters["water_near"]))
    world.facts["predicted_safe"] = pred["safe"]
    if pred["safe"]:
        world.say(
            f'"Can we {response.id.replace("_", " ")}?" {child.id} asked. '
            f'"Maybe that will help."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} saw the same worry in {child.id}\'s face and knelt beside '
            f"{child.pronoun('object')}."
        )


def choose_gentle_fix(world: World, child: Entity, helper: Entity, response: Response,
                      shelter: Shelter, rain_level: int) -> None:
    stage = world.get("stage")
    shelter_ent = world.get("shelter")
    if response.gentle and response.power >= rain_level:
        shelter_ent.meters["water_near"] = 0.0
        stage.meters["risk"] = 0.0
        child.memes["hope"] += 1
        helper.memes["care"] += 1
        world.say(
            f'{helper.label_word.capitalize()} smiled gently. "{response.text}"'
        )
        world.say(
            f"Together they began to bail the rainwater away, slow spoonful by slow spoonful, "
            f"until only damp circles were left in {shelter.tray}."
        )
        world.facts["rescued"] = True
    else:
        stage.meters["risk"] += 1
        stage.meters["jostled"] += 1
        child.memes["regret"] += 1
        world.say(
            f'{helper.label_word.capitalize()} tried to help, but {response.fail}.'
        )
        world.facts["rescued"] = False
    propagate(world, narrate=False)


def calm_wait(world: World, child: Entity, helper: Entity, butterfly: ButterflyKind) -> None:
    child.memes["patience"] += 1
    helper.memes["patience"] += 1
    world.say(
        f"Then they waited together, listening to {world.setting.rain_sound} and watching for any tiny change."
    )
    world.say(
        f'{helper.label_word.capitalize()} reminded {child.id} that growing can look quiet even when something '
        f"wonderful is happening."
    )
    world.get("stage").meters["ready"] = 1.0
    propagate(world, narrate=False)


def transform(world: World, child: Entity, butterfly: ButterflyKind) -> None:
    if world.get("butterfly").meters["present"] < THRESHOLD:
        return
    child.memes["joy"] += 1
    world.say(
        f"At last the chrysalis split with a tiny seam, and out came a {butterfly.butterfly} "
        f"with {butterfly.wing_color} wings folded close."
    )
    world.say(
        f"{child.id} forgot to blink. The whole porch seemed to brighten as the new butterfly "
        f"rested, opened, and slowly tested its wings."
    )


def release(world: World, child: Entity, helper: Entity, butterfly: ButterflyKind) -> None:
    if world.get("butterfly").meters["present"] < THRESHOLD:
        return
    child.memes["love"] += 1
    helper.memes["love"] += 1
    world.say(
        f"When the wings were strong, {child.id} and {helper.label_word} carried the shelter to "
        f"{world.setting.release_spot}."
    )
    world.say(
        f"The {butterfly.butterfly} lifted into the air, circled once above them, and drifted toward "
        f"{butterfly.likes}."
    )
    world.say(
        f'{child.id} squeezed {helper.label_word}\'s hand. "{helper.label_word.capitalize()}, we kept it safe," '
        f'{child.pronoun()} said.'
    )


def gentle_ending(world: World, child: Entity, helper: Entity) -> None:
    world.say(
        f'{helper.label_word.capitalize()} hugged {child.pronoun("object")} close and said that a small kind choice '
        f"can make room for a big change."
    )
    world.say(
        f"On the wet porch, with the rain almost done, {child.id} felt warmer than the sunshine that was beginning to return."
    )


def sad_ending(world: World, child: Entity, helper: Entity, butterfly: ButterflyKind) -> None:
    child.memes["sadness"] += 1
    helper.memes["care"] += 1
    world.say(
        f"They moved the shelter back under the porch roof and kept watch, but that day no {butterfly.butterfly} appeared."
    )
    world.say(
        f'{helper.label_word.capitalize()} put an arm around {child.id}. "{child.id}," {helper.pronoun()} said softly, '
        f'"sometimes helping means learning to be gentler next time."'
    )
    world.say(
        f"{child.id} nodded. Even in disappointment, {child.pronoun()} understood that careful hands matter to small living things."
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(setting: Setting, shelter: Shelter, memory: Memory, butterfly: ButterflyKind,
         response: Response, child_name: str = "Mira", child_gender: str = "girl",
         helper_type: str = "grandfather", rain_level: int = 1) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["gentle"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label="the helper",
        role="helper",
        traits=["patient"],
    ))
    world.add(Entity(
        id="shelter",
        kind="thing",
        type="shelter",
        label=shelter.label,
        phrase=shelter.phrase,
        delicate=shelter.delicate,
        can_hold_water=True,
        attrs={"tray": shelter.tray},
    ))
    world.add(Entity(
        id="stage",
        kind="thing",
        type="chrysalis",
        label="chrysalis",
        phrase="the chrysalis",
        delicate=True,
        is_stage=True,
    ))
    world.add(Entity(
        id="butterfly",
        kind="thing",
        type="butterfly",
        label=butterfly.butterfly,
        phrase=f"the {butterfly.butterfly}",
    ))

    # initialize meters read by rules
    world.get("shelter").meters["water_near"] = 0.0
    world.get("stage").meters["risk"] = 0.0
    world.get("stage").meters["ready"] = 0.0
    world.get("stage").meters["jostled"] = 0.0
    world.get("stage").meters["opened"] = 0.0
    world.get("butterfly").meters["present"] = 0.0
    child.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0

    world.facts.update(
        child=child,
        helper=helper,
        setting=setting,
        shelter_cfg=shelter,
        memory=memory,
        butterfly_cfg=butterfly,
        response=response,
        rain_level=rain_level,
        flashback_used=False,
        rescued=False,
    )

    introduce(world, child, helper, shelter, butterfly)
    notice_problem(world, child, shelter, rain_level)

    world.para()
    flashback(world, child, helper, memory, butterfly)
    worry_and_wish(world, child, helper, response)

    world.para()
    choose_gentle_fix(world, child, helper, response, shelter, rain_level)
    calm_wait(world, child, helper, butterfly)

    if world.get("butterfly").meters["present"] >= THRESHOLD:
        world.para()
        transform(world, child, butterfly)
        release(world, child, helper, butterfly)
        gentle_ending(world, child, helper)
        outcome = "transformed"
    else:
        world.para()
        sad_ending(world, child, helper, butterfly)
        outcome = "delayed"

    world.facts.update(
        outcome=outcome,
        transformed=world.get("butterfly").meters["present"] >= THRESHOLD,
        jostled=world.get("stage").meters["jostled"] >= THRESHOLD,
        safe=world.get("stage").meters["risk"] < THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
SETTINGS = {
    "porch_garden": Setting(
        id="porch_garden",
        place="the little garden",
        rain_sound="soft drops tapping from the porch roof",
        release_spot="the zinnias by the fence",
        tags={"garden", "rain"},
    ),
    "kitchen_window": Setting(
        id="kitchen_window",
        place="the herb boxes outside the kitchen window",
        rain_sound="drips ticking on the window ledge",
        release_spot="the mint and marigolds below",
        tags={"garden", "window"},
    ),
    "shed_corner": Setting(
        id="shed_corner",
        place="the bright corner beside the shed",
        rain_sound="rain sliding off the old metal roof",
        release_spot="the sunny milkweed patch",
        tags={"garden", "shed"},
    ),
}

SHELTERS = {
    "mesh_hamper": Shelter(
        id="mesh_hamper",
        label="mesh butterfly hamper",
        phrase="a white mesh butterfly hamper",
        tray="the shallow blue tray",
        hangs_from="the porch hook",
        delicate=True,
        tags={"mesh", "tray"},
    ),
    "screen_cage": Shelter(
        id="screen_cage",
        label="screen butterfly cage",
        phrase="a tall screen butterfly cage",
        tray="the black saucer underneath",
        hangs_from="a nail by the railing",
        delicate=True,
        tags={"screen", "saucer"},
    ),
    "jar_topper": Shelter(
        id="jar_topper",
        label="jar with a net top",
        phrase="a clean jar with a net top",
        tray="the little flowerpot saucer",
        hangs_from="the low shelf edge",
        delicate=True,
        tags={"jar", "saucer"},
    ),
}

RESPONSES = {
    "spoon_bail": Response(
        id="spoon_bail",
        sense=3,
        gentle=True,
        power=2,
        text="Let's use a spoon and a cup to bail the water away, and we will not touch the chrysalis at all.",
        qa_text="They used a spoon and a cup to bail the water away without touching the chrysalis.",
        fail="the rain kept pouring in faster than they could manage",
        tags={"bail", "gentle_help"},
    ),
    "cloth_wick": Response(
        id="cloth_wick",
        sense=2,
        gentle=True,
        power=1,
        text="Let's lay a folded cloth at the edge so it drinks the water out, and then we can bail the rest.",
        qa_text="They used a folded cloth to wick water out and then bailed the rest away.",
        fail="the cloth helped only a little, and the water stayed too close",
        tags={"cloth", "bail"},
    ),
    "move_shelter": Response(
        id="move_shelter",
        sense=3,
        gentle=True,
        power=3,
        text="Let's slide the whole tray to the dry table first, then bail what is left very carefully.",
        qa_text="They slid the tray to a dry place and carefully bailed the remaining water away.",
        fail="the footing was too slippery for a safe move",
        tags={"move", "bail"},
    ),
    "shake": Response(
        id="shake",
        sense=1,
        gentle=False,
        power=2,
        text="Let's shake the water off quickly.",
        qa_text="They shook the shelter.",
        fail="shaking the shelter was too rough for something so delicate",
        tags={"rough"},
    ),
}

MEMORIES = {
    "leaf_nibbling": Memory(
        id="leaf_nibbling",
        past_image="In the flashback in her mind, the caterpillar had once been no bigger than a little finger, nibbling a leaf in neat half-moons.",
        lesson="small creatures can do brave changing when grown-ups and children make a quiet place for them",
        tags={"flashback", "caterpillar"},
    ),
    "milkweed_walk": Memory(
        id="milkweed_walk",
        past_image="In the flashback in his mind, the caterpillar had inched along a milkweed stem, stopping every so often as if it were thinking hard about the sky.",
        lesson="care does not have to be loud to be real",
        tags={"flashback", "milkweed"},
    ),
    "button_body": Memory(
        id="button_body",
        past_image="In the flashback that returned, the caterpillar had looked like a tiny striped button with legs, lifting itself leaf to leaf.",
        lesson="gentle waiting can satisfy what a growing creature needs",
        tags={"flashback", "waiting"},
    ),
}

BUTTERFLIES = {
    "monarch": ButterflyKind(
        id="monarch",
        caterpillar="striped caterpillar",
        butterfly="monarch butterfly",
        wing_color="orange-and-black",
        likes="the milkweed and zinnias",
        tags={"butterfly", "monarch"},
    ),
    "painted_lady": ButterflyKind(
        id="painted_lady",
        caterpillar="spiky caterpillar",
        butterfly="painted lady butterfly",
        wing_color="sunny orange-and-brown",
        likes="the marigolds and herbs",
        tags={"butterfly", "painted_lady"},
    ),
    "swallowtail": ButterflyKind(
        id="swallowtail",
        caterpillar="green swallowtail caterpillar",
        butterfly="swallowtail butterfly",
        wing_color="yellow-and-black",
        likes="the fennel and bright flowers",
        tags={"butterfly", "swallowtail"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Ava", "Nora", "Ivy", "Ella", "Ruby", "June"]
BOY_NAMES = ["Owen", "Eli", "Theo", "Noah", "Ben", "Finn", "Milo", "Sam"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    shelter: str
    memory: str
    butterfly: str
    response: str
    child_name: str
    child_gender: str
    helper_type: str
    rain_level: int = 1
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short memory scene from an earlier time. It helps readers understand why a character feels or chooses something now."
        )
    ],
    "transformation": [
        (
            "What does transformation mean?",
            "Transformation means changing from one form into another. A caterpillar turning into a butterfly is a real kind of transformation in nature."
        )
    ],
    "bail": [
        (
            "What does it mean to bail water out?",
            "To bail water out means to scoop or lift water away from a place where it should not stay. People do it gently with a cup, spoon, or small bucket."
        )
    ],
    "chrysalis": [
        (
            "What is a chrysalis?",
            "A chrysalis is the hard outer case a butterfly caterpillar makes around itself while it changes. The animal inside is still alive and growing."
        )
    ],
    "butterfly": [
        (
            "Why should people be gentle with a chrysalis?",
            "A chrysalis is delicate because a butterfly is changing inside it. Rough handling can hurt the insect before it is ready to emerge."
        )
    ],
    "garden": [
        (
            "Why do butterflies like flowers?",
            "Butterflies visit flowers for nectar, a sweet liquid they drink. Flowers also give them safe places to land and rest."
        )
    ],
}

KNOWLEDGE_ORDER = ["flashback", "transformation", "bail", "chrysalis", "butterfly", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    butterfly = f["butterfly_cfg"]
    shelter = f["shelter_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "satisfy" and "bail", plus a flashback and a transformation.',
        f"Tell a gentle story where {child.id} and {child.pronoun('possessive')} {helper.label_word} protect a chrysalis in {shelter.phrase} after rain.",
        f"Write a story in which a {butterfly.butterfly} appears at the end, proving that careful help and patient waiting mattered.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    shelter = f["shelter_cfg"]
    response = f["response"]
    butterfly = f["butterfly_cfg"]
    rain_level = f["rain_level"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {child.pronoun('possessive')} {helper.label_word}, who were caring for a chrysalis after the rain. They wanted to help without hurting something small and delicate."
        ),
        (
            "What problem did they notice?",
            f"They saw rainwater gathering around {shelter.tray} near the shelter. That made {child.id} worry because too much water too close to the chrysalis did not feel safe."
        ),
        (
            "Why is there a flashback in the story?",
            f"The flashback shows that {child.id} remembered the creature when it was still a caterpillar. That memory explains why {child.pronoun()} cared so much and wanted to protect the change still happening inside the chrysalis."
        ),
    ]
    if f["outcome"] == "transformed":
        qa.append(
            (
                "How did they solve the problem?",
                f"{response.qa_text} They chose a gentle method because the chrysalis was delicate, and that careful choice kept the space safe while they waited."
            )
        )
        qa.append(
            (
                "How did the story show transformation?",
                f"The transformation happened when the chrysalis opened and a {butterfly.butterfly} came out. The ending image of the butterfly lifting toward {butterfly.likes} proves that the quiet creature had truly changed."
            )
        )
    else:
        qa.append(
            (
                "Why did the ending feel sad but loving?",
                f"The butterfly did not come out that day, so {child.id} felt disappointed. Still, {helper.label_word} stayed close and turned the moment into a lesson about being gentler with small living things."
            )
        )
    if rain_level >= 2:
        qa.append(
            (
                "Why did they need to act quickly?",
                f"The rain had left a lot of water near the shelter, not just a tiny damp ring. That extra water made the worry feel more urgent, so they had to help carefully right away."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"flashback", "transformation", "bail", "chrysalis", "butterfly", "garden"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.delicate:
            bits.append("delicate=True")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="porch_garden",
        shelter="mesh_hamper",
        memory="leaf_nibbling",
        butterfly="monarch",
        response="spoon_bail",
        child_name="Mira",
        child_gender="girl",
        helper_type="grandfather",
        rain_level=1,
    ),
    StoryParams(
        setting="kitchen_window",
        shelter="screen_cage",
        memory="milkweed_walk",
        butterfly="painted_lady",
        response="move_shelter",
        child_name="Theo",
        child_gender="boy",
        helper_type="grandmother",
        rain_level=2,
    ),
    StoryParams(
        setting="shed_corner",
        shelter="jar_topper",
        memory="button_body",
        butterfly="swallowtail",
        response="cloth_wick",
        child_name="Ruby",
        child_gender="girl",
        helper_type="father",
        rain_level=1,
    ),
    StoryParams(
        setting="porch_garden",
        shelter="mesh_hamper",
        memory="leaf_nibbling",
        butterfly="monarch",
        response="shake",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandfather",
        rain_level=2,
    ),
]


def explain_rejection(response_id: str) -> str:
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response_id}': it is too rough or not sensible enough for a fragile chrysalis. "
            f"Choose a gentler fix such as {', '.join(sorted(r.id for r in sensible_responses()))}.)"
        )
    if not response.gentle:
        return (
            f"(Refusing response '{response_id}': this world requires gentle help around a chrysalis, not shaking or jolting.)"
        )
    return "(No valid response.)"


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    return "transformed" if response_works(response, params.rain_level) else "delayed"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% --- compatible scenarios --------------------------------------------------
valid(S, Sh, M, B) :- setting(S), shelter(Sh), delicate_shelter(Sh), memory(M), butterfly_kind(B).

% --- gentle/common-sense gate ---------------------------------------------
sensible(R) :- response(R), sense(R, V), sense_min(Min), V >= Min, gentle(R).

% --- outcome model ---------------------------------------------------------
works :- chosen_response(R), gentle(R), power(R, P), rain_level(L), P >= L.
outcome(transformed) :- works.
outcome(delayed) :- not works.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for shid, sh in SHELTERS.items():
        lines.append(asp.fact("shelter", shid))
        if sh.delicate:
            lines.append(asp.fact("delicate_shelter", shid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    for bid in BUTTERFLIES:
        lines.append(asp.fact("butterfly_kind", bid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
        if r.gentle:
            lines.append(asp.fact("gentle", rid))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("rain_level", params.rain_level),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_valid = set(asp_valid_combos())
    python_valid = set(valid_combos())
    if clingo_valid == python_valid:
        print(f"OK: gate matches valid_combos() ({len(clingo_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
        print("  clingo:", sorted(clingo_sensible))
        print("  python:", sorted(python_sensible))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated empty story.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: a child protects a chrysalis after rain."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--shelter", choices=SHELTERS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--butterfly", choices=BUTTERFLIES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--rain-level", type=int, choices=[1, 2], help="how much water gathers near the shelter")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.response))
    if args.response and not RESPONSES[args.response].gentle:
        raise StoryError(explain_rejection(args.response))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.shelter is None or c[1] == args.shelter)
        and (args.memory is None or c[2] == args.memory)
        and (args.butterfly is None or c[3] == args.butterfly)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, shelter_id, memory_id, butterfly_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "grandmother", "grandfather"])
    rain_level = args.rain_level if args.rain_level is not None else rng.choice([1, 2])

    return StoryParams(
        setting=setting_id,
        shelter=shelter_id,
        memory=memory_id,
        butterfly=butterfly_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_type=helper_type,
        rain_level=rain_level,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.shelter not in SHELTERS:
        raise StoryError(f"(Unknown shelter: {params.shelter})")
    if params.memory not in MEMORIES:
        raise StoryError(f"(Unknown memory: {params.memory})")
    if params.butterfly not in BUTTERFLIES:
        raise StoryError(f"(Unknown butterfly: {params.butterfly})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN or not RESPONSES[params.response].gentle:
        raise StoryError(explain_rejection(params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        shelter=SHELTERS[params.shelter],
        memory=MEMORIES[params.memory],
        butterfly=BUTTERFLIES[params.butterfly],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_type=params.helper_type,
        rain_level=params.rain_level,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, shelter, memory, butterfly) combos:\n")
        for setting_id, shelter_id, memory_id, butterfly_id in combos:
            print(f"  {setting_id:14} {shelter_id:12} {memory_id:14} {butterfly_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            try:
                samples.append(generate(p))
            except StoryError as err:
                print(err)
                return
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.response} at {p.setting} "
                f"({p.butterfly}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
