#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py
=====================================================================================

A standalone story world about two children playing pirates in a venetian-style
boat game, a risky cod snack, a tummy sickness, and a reconciliation.

The world model prefers plausible combinations: a fish snack only causes the
story's trouble when it has been left somewhere warm long enough to spoil.
A cautious child can sometimes stop the risky bite before anything happens.
Otherwise a grown-up helps sensibly, the children make up, and the ending image
proves that trust has been repaired.

Run it
------
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py --theme lagoon --food fritter --storage sun_basket
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py --storage ice_box
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py --response more_snack
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cod_venetian_gastroenteritis_reconciliation_pirate_tale.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    fish_food: bool = False
    spoiled: bool = False
    safe_light: bool = False
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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    water_line: str
    send_off: str
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
class Food:
    id: str
    label: str
    phrase: str
    plural: bool = False
    fish_food: bool = True
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
class Storage:
    id: str
    label: str
    place: str
    detail: str
    spoiled: bool
    severity: int
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
    power: int
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_sicken(world: World) -> list[str]:
    out: list[str] = []
    eater_id = world.facts.get("eater_id", "")
    if not eater_id:
        return out
    eater = world.get(eater_id)
    food = world.get("food")
    if eater.meters["ate_risky_food"] < THRESHOLD or not food.spoiled:
        return out
    sig = ("sicken", eater.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    eater.meters["nausea"] += 1
    eater.meters["cramps"] += 1
    eater.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__sicken__")
    return out


def _r_hurt_feelings(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("instigator")
    b = world.get("cautioner")
    if a.memes["snapped"] < THRESHOLD:
        return out
    sig = ("hurt", a.id, b.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    b.memes["hurt"] += 1
    b.memes["distance"] += 1
    out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule(name="sicken", tag="physical", apply=_r_sicken),
    Rule(name="hurt_feelings", tag="social", apply=_r_hurt_feelings),
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


def hazard_at_risk(food: Food, storage: Storage) -> bool:
    return food.fish_food and storage.spoiled


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(storage: Storage, delay: int) -> int:
    return storage.severity + delay


def is_managed(response: Response, storage: Storage, delay: int) -> bool:
    return response.power >= severity_of(storage, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_sickness(world: World) -> dict:
    sim = world.copy()
    sim.get(sim.facts["eater_id"]).meters["ate_risky_food"] += 1
    propagate(sim, narrate=False)
    eater = sim.get(sim.facts["eater_id"])
    return {
        "sick": eater.meters["nausea"] >= THRESHOLD,
        "worry": sum(k.memes["worry"] for k in sim.kids()),
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the sitting room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} cried. '
        f'"Let\'s sail toward {theme.goal}!"'
    )
    world.say(theme.water_line)


def spot_snack(world: World, a: Entity, food: Food, storage: Storage) -> None:
    world.say(
        f"Near the pretend deck sat {food.phrase}, {storage.detail}. "
        f"{a.id} stopped and stared at it as if it were treasure."
    )


def tempt(world: World, a: Entity, food: Food) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"Ship snack!" {a.id} said. "Pirates need strength. Let\'s eat the {food.label} now."'
    )


def warn(world: World, b: Entity, a: Entity, parent: Entity, food: Food, storage: Storage) -> None:
    pred = predict_sickness(world)
    world.facts["predicted_sick"] = pred["sick"]
    world.facts["predicted_worry"] = pred["worry"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.pronoun().capitalize()} sounded very sure."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, no. That {food.label} was '
        f'{storage.place}. {parent.label_word.capitalize()} said fish should not sit there too long. '
        f'It could make our tummies sick with gastroenteritis."{extra}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    a.memes["snapped"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"You always stop the fun," {a.id} snapped. {b.id} went quiet and held the rope-map a little tighter.'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    b.memes["distance"] = 0.0
    world.say(
        f'{a.id} reached for the snack, then looked at {b.id} again. Because {b.id} was the older one and '
        f'sounded so certain, {a.id} let out a long breath and pulled {a.pronoun("possessive")} hand back.'
    )
    world.say(
        f'"All right," {a.pronoun()} muttered. "No cod treasure today." They went to tell '
        f'{parent.label_word.capitalize()} about the snack instead and kept steering toward {theme.goal}.'
    )


def eat_risky_food(world: World, a: Entity, food: Food) -> None:
    a.meters["ate_risky_food"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before anyone could stop {a.pronoun('object')}, {a.id} took a big bite of the cod. "
        f"For one blink it tasted salty and grand, like pirate food from a storybook."
    )


def stomach_turn(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f"Then the game tipped sideways. {a.id} pressed both hands to {a.pronoun('possessive')} middle, "
        f"and the brave pirate face crumpled."
    )
    world.say(
        f'"My tummy hurts," {a.pronoun()} whispered. {b.id} dropped the rope-map and hurried close at once.'
    )


def home_care(world: World, parent: Entity, response: Response, a: Entity) -> None:
    a.meters["nausea"] = 0.0
    a.meters["cramps"] = 0.0
    a.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {response.text}."
    )
    world.say(
        f"Soon the room felt less stormy. {a.id}'s breathing slowed, and the pirate ship stopped feeling like it was rocking."
    )


def clinic_care(world: World, parent: Entity, response: Response, a: Entity) -> None:
    a.meters["nausea"] = 0.0
    a.meters["cramps"] = 0.0
    a.memes["fear"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} tried to help and {response.fail}."
    )
    world.say(
        f"So {parent.pronoun()} took {a.id} to the evening clinic, where a kind doctor said it looked like gastroenteritis and showed them how to help {a.pronoun('object')} sip fluids slowly."
    )


def apology(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["hurt"] = 0.0
    world.say(
        f"When the sharp part had passed, {a.id} looked at {b.id} with wet eyes. "
        f'"I am sorry I snapped at you," {a.pronoun()} said. "You were trying to help me."'
    )
    world.say(
        f'{b.id} scooted closer. "{parent.label_word.capitalize()} says crews stay kind, even after mistakes," '
        f'{b.pronoun()} answered.'
    )


def reconcile(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    a.memes["love"] += 1
    b.memes["love"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"They bumped their shoulders together and shared the blanket like two sailors under one small sail. "
        f"The hurt feeling melted away, and the pirate crew felt whole again."
    )
    world.say(
        f"The next day they sailed their pretend boat once more, but this time they asked before tasting anything, "
        f"and their {theme.send_off} sounded warmer than before."
    )


def safe_feast(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    world.say(
        f"Later, {parent.label_word.capitalize()} brought out fresh bread, cool apple slices, and lemon water. "
        f'"Here is proper captain food," {parent.pronoun()} said.'
    )
    world.say(
        f"{a.id} handed the first cup to {b.id}, and {b.id} tore the bread in half to share. "
        f"They ate carefully and watched the late light make small venetian stripes across the floor."
    )
    world.say(
        f"Under those quiet stripes, the two pirates knew what had changed: treasure tasted best when the whole crew felt safe."
    )


def tell(
    theme: Theme,
    food: Food,
    storage: Storage,
    response: Response,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    cautioner: str = "Lily",
    cautioner_gender: str = "girl",
    trait: str = "careful",
    parent_type: str = "mother",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id="instigator",
            kind="character",
            type=instigator_gender,
            label=instigator,
            role="instigator",
            traits=["bold"],
            age=instigator_age,
            attrs={"relation": relation},
        )
    )
    b = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner,
            role="cautioner",
            traits=[trait],
            age=cautioner_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    food_ent = world.add(
        Entity(
            id="food",
            type="food",
            label=food.label,
            fish_food=food.fish_food,
            spoiled=storage.spoiled,
        )
    )

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    a.memes["trust"] = 5.0
    b.memes["trust"] = 5.0
    world.facts["eater_id"] = "instigator"

    play_setup(world, a, b, theme)
    spot_snack(world, a, food, storage)

    world.para()
    tempt(world, a, food)
    warn(world, b, a, parent, food, storage)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, theme)
        world.para()
        apology(world, a, b, parent)
        reconcile(world, a, b, theme)
        world.para()
        safe_feast(world, parent, a, b, theme)
        outcome = "averted"
    else:
        defy(world, a, b)
        world.para()
        eat_risky_food(world, a, food)
        stomach_turn(world, a, b)
        managed = is_managed(response, storage, delay)
        world.para()
        if managed:
            home_care(world, parent, response, a)
            outcome = "home_recovery"
        else:
            clinic_care(world, parent, response, a)
            outcome = "clinic"
        apology(world, a, b, parent)
        reconcile(world, a, b, theme)
        world.para()
        safe_feast(world, parent, a, b, theme)

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        theme=theme,
        food_cfg=food,
        storage=storage,
        response=response,
        ignited_sickness=not averted,
        outcome=outcome,
        delay=delay,
        severity=severity_of(storage, delay),
        relation=relation,
    )
    return world


THEMES = {
    "lagoon": Theme(
        id="lagoon",
        scene="a little venetian lagoon full of cushions and blue scarves",
        rig="A chair became the stern, the footstool became the prow, and two striped towels hung like bright sails.",
        captain="Captain",
        mate="Navigator",
        goal="the silver bell at the end of the canal",
        water_line="Outside the window, the afternoon light slipped through the blinds in narrow bars, like reflections from canal water.",
        send_off="cheers for the crew",
        tags={"venetian", "pirates"},
    ),
    "regatta": Theme(
        id="regatta",
        scene="a venetian regatta with a sofa for a grand black boat",
        rig="A wooden spoon became a captain's oar, a blanket became a night-dark lagoon, and a paper mask watched from the wall like parade treasure.",
        captain="Captain",
        mate="First Mate",
        goal="the lantern bridge",
        water_line="The room gleamed in long gold stripes, and the children said the stripes were sunlight dancing on canal water.",
        send_off="songs over the pretend water",
        tags={"venetian", "pirates"},
    ),
    "market": Theme(
        id="market",
        scene="a tiny pirate raid through a venetian market",
        rig="Pillows became fish crates, a laundry basket became their boat, and a blue scarf wound across the rug like a canal.",
        captain="Captain",
        mate="Lookout",
        goal="the striped bridge of spices",
        water_line="Every time the scarf rippled under their toes, they pretended the canal was tugging at the hull.",
        send_off="captain calls across the room",
        tags={"venetian", "pirates"},
    ),
}

FOODS = {
    "fritter": Food(
        id="fritter",
        label="cod fritter",
        phrase="a little cod fritter",
        tags={"cod", "fish_food"},
    ),
    "sandwich": Food(
        id="sandwich",
        label="cod sandwich",
        phrase="half a cod sandwich",
        tags={"cod", "fish_food"},
    ),
    "salad": Food(
        id="salad",
        label="cod salad",
        phrase="a small bowl of cod salad",
        tags={"cod", "fish_food"},
    ),
}

STORAGES = {
    "sun_basket": Storage(
        id="sun_basket",
        label="sun-warm basket",
        place="in a basket by the sunny window all morning",
        detail="forgotten in a basket by the sunny window all morning",
        spoiled=True,
        severity=2,
        tags={"warm_food", "window"},
    ),
    "radiator_plate": Storage(
        id="radiator_plate",
        label="warm plate",
        place="on a plate near the radiator",
        detail="left on a plate near the radiator while the room grew toasty",
        spoiled=True,
        severity=3,
        tags={"warm_food", "radiator"},
    ),
    "boat_step": Storage(
        id="boat_step",
        label="doorstep napkin",
        place="on the back step in the warm air",
        detail="wrapped in a napkin on the back step in the warm air",
        spoiled=True,
        severity=2,
        tags={"warm_food", "step"},
    ),
    "ice_box": Storage(
        id="ice_box",
        label="ice box",
        place="in the cool ice box",
        detail="kept safely cool in the ice box",
        spoiled=False,
        severity=0,
        tags={"cold_food"},
    ),
}

RESPONSES = {
    "sips_and_rest": Response(
        id="sips_and_rest",
        sense=3,
        power=3,
        text="sat beside the little pirate, called the nurse line, and brought tiny sips of water and a cool cloth",
        fail="sat beside the little pirate, called the nurse line, and offered tiny sips of water, but the tummy pain kept coming back",
        qa_text="gave tiny sips of water, a cool cloth, and careful rest after calling for advice",
        tags={"fluids", "doctor"},
    ),
    "oral_rehydration": Response(
        id="oral_rehydration",
        sense=3,
        power=4,
        text="mixed an oral rehydration drink, phoned the doctor for advice, and kept the room quiet and calm",
        fail="mixed an oral rehydration drink and phoned the doctor, but the pain was still too strong to stay home",
        qa_text="used an oral rehydration drink and called the doctor for advice",
        tags={"fluids", "doctor", "oral_rehydration"},
    ),
    "cuddle_only": Response(
        id="cuddle_only",
        sense=2,
        power=1,
        text="held the little pirate close and offered a warm cuddle while bringing a few careful sips of water",
        fail="held the little pirate close and offered a warm cuddle, but a cuddle alone was not enough help for that strong tummy sickness",
        qa_text="gave a cuddle and a few sips of water",
        tags={"fluids"},
    ),
    "more_snack": Response(
        id="more_snack",
        sense=1,
        power=0,
        text="offered another bite of snack, which made no sense at all here",
        fail="offered more snack, which only made the bad idea worse",
        qa_text="offered more snack",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "brave"]


@dataclass
class StoryParams:
    theme: str = "lagoon"
    food: str = "fritter"
    storage: str = "sun_basket"
    response: str = "oral_rehydration"
    instigator: str = "Tom"
    instigator_gender: str = "boy"
    cautioner: str = "Lily"
    cautioner_gender: str = "girl"
    parent: str = "mother"
    trait: str = "careful"
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
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
    "cod": [
        (
            "What is cod?",
            "Cod is a kind of fish that people sometimes cook for meals. Like other fish, it should be kept cold so it stays safe to eat.",
        )
    ],
    "gastroenteritis": [
        (
            "What is gastroenteritis?",
            "Gastroenteritis is a tummy sickness that can cause pain, vomiting, or diarrhea. A grown-up helps by giving fluids, rest, and calling a doctor when needed.",
        )
    ],
    "venetian": [
        (
            "What does venetian mean in this story?",
            "Venetian means it reminds us of Venice, a city with canals and boats. The children use that idea to make their pirate game feel special.",
        )
    ],
    "doctor": [
        (
            "Why should a grown-up call a doctor or nurse line for a bad tummy sickness?",
            "A doctor or nurse can tell you how to stay safe and when you need more help. That matters because tummy sickness can make your body lose water.",
        )
    ],
    "fluids": [
        (
            "Why do tiny sips of water help when someone has a tummy bug?",
            "Tiny sips can help replace water the body has lost. Small sips are often easier for a sore tummy to keep down.",
        )
    ],
    "oral_rehydration": [
        (
            "What is an oral rehydration drink?",
            "It is a special drink with water, salts, and sugar to help the body recover from losing fluids. Grown-ups use it carefully when a doctor or nurse says it will help.",
        )
    ],
    "warm_food": [
        (
            "Why can fish left in a warm place become unsafe to eat?",
            "Warm places can let germs grow on food. That is why fish should be kept cold until it is time to eat.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "cod",
    "venetian",
    "gastroenteritis",
    "warm_food",
    "fluids",
    "doctor",
    "oral_rehydration",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for theme in THEMES:
        for food_id, food in FOODS.items():
            for storage_id, storage in STORAGES.items():
                if hazard_at_risk(food, storage):
                    combos.append((theme, food_id, storage_id))
    return combos


def explain_rejection(food: Food, storage: Storage) -> str:
    if not storage.spoiled:
        return (
            f"(No story: the {food.label} was {storage.place}, so it stayed safe. "
            "Without a real risk, there is no honest warning, sickness, or repair of trust. "
            "Pick a warm storage place instead.)"
        )
    return "(No story: this combination does not create the tummy-sickness risk the world needs.)"


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    managed = is_managed(RESPONSES[params.response], STORAGES[params.storage], params.delay)
    return "home_recovery" if managed else "clinic"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    food = f["food_cfg"]
    storage = f["storage"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old where two children turn a room into a venetian canal and one child wisely stops the other from eating risky cod.',
            f"Tell a gentle reconciliation story where {a.label} wants the {food.label}, but {b.label} warns that it was {storage.place}, and they make up after the danger is avoided.",
            f'Write a simple story that includes the words "cod", "venetian", and "gastroenteritis", but ends safely because the children ask a grown-up before eating.',
        ]
    if outcome == "clinic":
        return [
            f'Write a child-facing pirate tale where a risky cod snack in a venetian pretend game leads to gastroenteritis and a doctor visit, but the children reconcile at the end.',
            f"Tell a story where {a.label} hurts {b.label}'s feelings, gets sick after ignoring a warning, and then apologizes and repairs the friendship.",
            f"Write a cautionary pirate-style story with a tummy-sickness turn, sensible grown-up help, and a warm ending image that shows the crew is together again.",
        ]
    return [
        f'Write a short pirate-style story where children play on a venetian pretend boat, one eats unsafe cod, and a calm grown-up helps with a tummy sickness.',
        f"Tell a reconciliation story where {a.label} ignores {b.label}'s warning, gets gastroenteritis, then apologizes and makes up.",
        f'Write a simple story that includes "cod", "venetian", and "gastroenteritis" and ends with the children sharing safe food after the scare.',
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    theme = f["theme"]
    food = f["food_cfg"]
    storage = f["storage"]
    response = f["response"]
    outcome = f["outcome"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, who were playing pirates together. Their {pw} also mattered because {pw} helped when the problem grew real.",
        ),
        (
            "What were the children pretending?",
            f"They turned the room into {theme.scene} and imagined they were sailing toward {theme.goal}. The venetian boat game made the snack feel like pirate treasure.",
        ),
        (
            f"Why did {b.label} warn {a.label} not to eat the {food.label}?",
            f"{b.label} knew the {food.label} had been {storage.place}. That made {b.pronoun('object')} worry it could cause gastroenteritis, a real tummy sickness.",
        ),
    ]
    if outcome == "averted":
        qa.append(
            (
                f"What changed after {b.label} spoke up?",
                f"{a.label} stopped reaching for the cod and chose to tell a grown-up instead. The danger passed before anyone got sick, which made it easier for the crew to calm down and stay kind.",
            )
        )
    else:
        qa.append(
            (
                f"What happened after {a.label} ate the {food.label}?",
                f"{a.label}'s tummy began to hurt and the pirate game suddenly stopped feeling fun. The sickness came after eating fish that had been left in a warm place.",
            )
        )
        if outcome == "home_recovery":
            qa.append(
                (
                    f"How did {a.label}'s {pw} help?",
                    f"{pw.capitalize()} {response.qa_text}. That calm help eased the sickness and made the room feel safe again.",
                )
            )
        else:
            qa.append(
                (
                    f"Why did they go to the clinic?",
                    f"The tummy pain stayed too strong for home care alone. So the grown-up took {a.label} for extra help, and the doctor explained that it looked like gastroenteritis.",
                )
            )
    qa.append(
        (
            "How did the children reconcile?",
            f"{a.label} apologized for snapping, and {b.label} moved close again instead of staying hurt and far away. Sharing safe food afterward showed that trust had been repaired, not just talked about.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["food_cfg"].tags) | set(f["theme"].tags) | set(f["storage"].tags)
    tags |= {"gastroenteritis"}
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.fish_food:
            bits.append("fish_food=True")
        if e.spoiled:
            bits.append("spoiled=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="lagoon",
        food="fritter",
        storage="sun_basket",
        response="oral_rehydration",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="regatta",
        food="sandwich",
        storage="radiator_plate",
        response="sips_and_rest",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=1,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="market",
        food="salad",
        storage="boat_step",
        response="cuddle_only",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="mother",
        trait="curious",
        delay=1,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
    ),
    StoryParams(
        theme="lagoon",
        food="sandwich",
        storage="radiator_plate",
        response="cuddle_only",
        instigator="Eli",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="father",
        trait="cautious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
    ),
    StoryParams(
        theme="market",
        food="fritter",
        storage="sun_basket",
        response="oral_rehydration",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Lucy",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        delay=0,
        instigator_age=4,
        cautioner_age=7,
        relation="siblings",
    ),
]


ASP_RULES = r"""
hazard(F,S) :- fish_food(F), spoiled(S).
sensible(R) :- response(R), sense(R, X), sense_min(M), X >= M.
valid(T,F,S) :- theme(T), food(F), storage(S), hazard(F,S).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(SV + D) :- chosen_storage(S), storage_severity(S, SV), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
managed :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(home_recovery) :- not averted, managed.
outcome(clinic) :- not averted, not managed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.fish_food:
            lines.append(asp.fact("fish_food", fid))
    for sid, storage in STORAGES.items():
        lines.append(asp.fact("storage", sid))
        lines.append(asp.fact("storage_severity", sid, storage.severity))
        if storage.spoiled:
            lines.append(asp.fact("spoiled", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
            asp.fact("chosen_storage", params.storage),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample, trace=False, qa=True, header="### smoke")


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    python_sensible = {r.id for r in sensible_responses()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(seed)))
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome classifications differ.")

    try:
        _smoke_generation()
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a venetian pirate game, risky cod, tummy sickness, and reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.storage and args.food:
        food = FOODS[args.food]
        storage = STORAGES[args.storage]
        if not hazard_at_risk(food, storage):
            raise StoryError(explain_rejection(food, storage))
    if args.storage and not STORAGES[args.storage].spoiled:
        food = FOODS[args.food] if args.food else next(iter(FOODS.values()))
        raise StoryError(explain_rejection(food, STORAGES[args.storage]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.food is None or combo[1] == args.food)
        and (args.storage is None or combo[2] == args.storage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, food, storage = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        theme=theme,
        food=food,
        storage=storage,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.food not in FOODS:
        raise StoryError(f"(Unknown food: {params.food})")
    if params.storage not in STORAGES:
        raise StoryError(f"(Unknown storage: {params.storage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hazard_at_risk(FOODS[params.food], STORAGES[params.storage]):
        raise StoryError(explain_rejection(FOODS[params.food], STORAGES[params.storage]))

    world = tell(
        theme=THEMES[params.theme],
        food=FOODS[params.food],
        storage=STORAGES[params.storage],
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
    )

    world.facts["instigator"].label = params.instigator
    world.facts["cautioner"].label = params.cautioner

    story_text = world.render().replace("instigator", params.instigator).replace("cautioner", params.cautioner)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, food, storage) combos:\n")
        for theme, food, storage in combos:
            print(f"  {theme:8} {food:10} {storage}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.food} from {p.storage} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
