#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py
==================================================================================

A standalone story world about two children walking a jungle path with a foil-
wrapped gift. One child is tempted to unfold the shiny foil and show off. A
monkey notices, a quarrel begins, and the children must solve the problem
sensibly.

This world is shaped as a small folk-tale domain:
- a true path through the jungle
- a warning that can be obeyed or ignored
- a concrete mistake with consequences
- a calm problem-solving turn
- an ending image that proves what changed

Run it
------
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --animal capuchin
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --animal deer
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --solution decoy
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --all
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --qa --json
    python storyworlds/worlds/gpt-5.4/jungle_foil_true_cautionary_problem_solving_conflict.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "wise", "steady"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
class Errand:
    id: str
    start: str
    destination: str
    elder_title: str
    purpose: str
    closing: str
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
class Gift:
    id: str
    label: str
    phrase: str
    smell: str
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
class Animal:
    id: str
    label: str
    movement: str
    cry: str
    curious_to_shine: bool
    snatches_food: bool
    quickness: int
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
class Solution:
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


def _r_notice_shine(world: World) -> list[str]:
    foil = world.get("foil")
    animal = world.get("animal")
    if foil.meters["waved"] < THRESHOLD:
        return []
    if not animal.attrs.get("curious_to_shine", False):
        return []
    sig = ("notice_shine", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    animal.meters["alert"] += 1
    return ["__notice__"]


def _r_snatch(world: World) -> list[str]:
    animal = world.get("animal")
    bundle = world.get("bundle")
    if animal.meters["alert"] < THRESHOLD:
        return []
    if bundle.meters["open"] < THRESHOLD:
        return []
    if not animal.attrs.get("snatches_food", False):
        return []
    sig = ("snatch", animal.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bundle.meters["stolen"] += 1
    bundle.meters["held"] = 0.0
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__snatch__"]


def _r_quarrel(world: World) -> list[str]:
    bundle = world.get("bundle")
    if bundle.meters["stolen"] < THRESHOLD:
        return []
    sig = ("quarrel", "kids")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["conflict"] += 1
    return ["__quarrel__"]


CAUSAL_RULES = [
    Rule(name="notice_shine", tag="physical", apply=_r_notice_shine),
    Rule(name="snatch", tag="physical", apply=_r_snatch),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
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


def hazard_at_risk(gift: Gift, animal: Animal) -> bool:
    return animal.curious_to_shine and animal.snatches_food and "food" in gift.tags


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def trouble_severity(animal: Animal, delay: int) -> int:
    return animal.quickness + delay


def is_recovered(solution: Solution, animal: Animal, delay: int) -> bool:
    return solution.power >= trouble_severity(animal, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_snatch(world: World) -> dict:
    sim = world.copy()
    _do_wave(sim, narrate=False)
    return {
        "alert": sim.get("animal").meters["alert"],
        "stolen": sim.get("bundle").meters["stolen"],
    }


def _do_wave(world: World, narrate: bool = True) -> None:
    foil = world.get("foil")
    bundle = world.get("bundle")
    foil.meters["waved"] += 1
    bundle.meters["open"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, elder: Entity, errand: Errand, gift: Gift) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In a village where the trees stood close as a green wall, {a.id} and {b.id} "
        f"were sent from {errand.start} to {errand.destination}."
    )
    world.say(
        f"They carried {gift.phrase} for their {elder.label_word}, and the warm bundle "
        f"smelled of {gift.smell}."
    )
    world.say(
        f"Everyone in that place said the jungle had many paths, but only one true path "
        f"that stayed kind to small feet."
    )


def send_on_errand(world: World, elder: Entity, errand: Errand) -> None:
    world.say(
        f'Before they left, their {elder.label_word} had said, "{errand.purpose} Keep the bundle folded, '
        f'keep your eyes open, and stay on the true path."'
    )


def tempt(world: World, a: Entity) -> None:
    a.memes["pride"] += 1
    world.say(
        f"But as the shade grew deeper, {a.id} pinched up one bright corner of the foil. "
        f'"Look," {a.pronoun()} said, "it flashes like a little sun."'
    )


def warn(world: World, b: Entity, a: Entity, animal: Animal) -> None:
    pred = predict_snatch(world)
    b.memes["caution"] += 1
    world.facts["predicted_stolen"] = pred["stolen"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} spoke as if repeating an old jungle saying."
    world.say(
        f'"Fold it shut," {b.id} told {a.id}. "Shiny things wake quick eyes in the jungle, '
        f'and a {animal.label} can leap before we can blink."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked at {b.id}, heard the steadiness in {b.pronoun('possessive')} voice, "
        f"and folded the foil smooth again."
    )
    world.say(
        "So the bright foolish thought passed like a dragonfly, and no creature came out of the leaves."
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'But {a.id} only laughed. "I will wave it once and no more," {a.pronoun()} said.'
    )
    if a.attrs.get("relation") == "siblings" and a.age > b.age:
        world.say(
            f"Because {a.id} was the older one, {b.id} could not stop {a.pronoun('object')} in time."
        )


def wave_foil(world: World, animal: Animal) -> None:
    _do_wave(world, narrate=False)
    world.say(
        f"The foil flashed between the vines. At once a branch shook, leaves hissed, "
        f"and a {animal.label} came {animal.movement} with a sharp {animal.cry}."
    )
    world.say(
        "Before either child could tuck the bundle closed, the nimble paws snatched it and fled to a low branch."
    )


def quarrel(world: World, a: Entity, b: Entity) -> None:
    world.say(
        f'"I warned you!" cried {b.id}. "{a.id}, you have spoiled the errand."'
    )
    world.say(
        f'"Do not scold me now," {a.id} answered, though {a.pronoun()} had gone pale. '
        f"Their words bumped against each other like stones in a stream."
    )


def choose_solution(world: World, a: Entity, b: Entity, solution: Solution) -> None:
    a.memes["shame"] += 1
    b.memes["care"] += 1
    world.say(
        f"Then {b.id} drew one long breath. \"Quarrelling will not bring it down,\" {b.pronoun()} said."
    )
    world.say(
        f"Together they chose a true idea: {solution.text}."
    )


def recover_success(world: World, a: Entity, b: Entity, animal: Animal, solution: Solution, gift: Gift) -> None:
    bundle = world.get("bundle")
    bundle.meters["stolen"] = 0.0
    bundle.meters["held"] = 1.0
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["conflict"] = 0.0
    world.say(
        f"The {animal.label} tipped its head, sprang toward the glitter, and let the bundle slip."
    )
    world.say(
        f"{a.id} caught {gift.label} against {a.pronoun('possessive')} chest, and {b.id} folded the foil tight without a sound."
    )
    world.say(
        f"From then on they walked more softly, as if the jungle were listening to whether their lesson was true."
    )


def recover_fail(world: World, a: Entity, b: Entity, animal: Animal, solution: Solution) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["conflict"] = 0.0
    world.say(
        f"But the {animal.label} was quicker than their plan. {solution.fail}."
    )
    world.say(
        f"After that there was nothing to do but follow the true path onward with empty hands and heavy hearts."
    )


def arrival_averted(world: World, a: Entity, b: Entity, elder: Entity, errand: Errand, gift: Gift) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"When they reached {errand.destination}, their {elder.label_word} smiled to see the neat silver bundle still safe."
    )
    world.say(
        f'"You carried both the gift and your good sense," {elder.pronoun()} said. '
        f'"That is how one walks a jungle road."'
    )
    world.say(
        errand.closing
    )


def arrival_recovered(world: World, a: Entity, b: Entity, elder: Entity, errand: Errand, gift: Gift) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"At last they came to {errand.destination} and laid {gift.label} before their {elder.label_word}."
    )
    world.say(
        f'"We nearly lost it," {a.id} admitted, "because I loved the shine more than the warning."'
    )
    world.say(
        f'Their {elder.label_word} nodded. "{elder.pronoun().capitalize()} who ignores a true warning feeds trouble. '
        f'But {elder.pronoun()} who stops quarrelling and thinks clearly can still mend a foolish step."'
    )
    world.say(
        errand.closing
    )


def arrival_lost(world: World, a: Entity, b: Entity, elder: Entity, errand: Errand, gift: Gift) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f"When they reached {errand.destination}, their hands were empty, and they bowed their heads before their {elder.label_word}."
    )
    world.say(
        f'"The jungle has taken its price for pride," their {elder.label_word} said, not unkindly. '
        f'"Let this be your true lesson: never wave what should be carried with care, and never waste your breath in quarrelling when thought is needed."'
    )
    world.say(
        "That evening they wrapped the next gift in plain leaves, and when they stepped beneath the trees again, they kept it quiet and close."
    )


def tell(
    errand: Errand,
    gift: Gift,
    animal_cfg: Animal,
    solution: Solution,
    *,
    instigator: str = "Kito",
    instigator_gender: str = "boy",
    cautioner: str = "Nia",
    cautioner_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 5,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
    ))
    bundle = world.add(Entity(
        id="bundle",
        type="bundle",
        label=gift.label,
        attrs={"gift": gift.id},
    ))
    foil = world.add(Entity(
        id="foil",
        type="foil",
        label="foil",
    ))
    animal = world.add(Entity(
        id="animal",
        type="animal",
        label=animal_cfg.label,
        attrs={
            "curious_to_shine": animal_cfg.curious_to_shine,
            "snatches_food": animal_cfg.snatches_food,
            "quickness": animal_cfg.quickness,
        },
    ))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    bundle.meters["held"] = 1.0
    bundle.meters["open"] = 0.0
    bundle.meters["stolen"] = 0.0
    foil.meters["waved"] = 0.0
    animal.meters["alert"] = 0.0
    world.facts["predicted_stolen"] = 0.0

    introduce(world, a, b, elder, errand, gift)
    send_on_errand(world, elder, errand)

    world.para()
    tempt(world, a)
    warn(world, b, a, animal_cfg)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b)
        world.para()
        arrival_averted(world, a, b, elder, errand, gift)
        recovered = True
        severity = 0
        outcome = "averted"
    else:
        defy(world, a, b)
        world.para()
        wave_foil(world, animal_cfg)
        quarrel(world, a, b)
        severity = trouble_severity(animal_cfg, delay)
        recovered = is_recovered(solution, animal_cfg, delay)
        world.para()
        choose_solution(world, a, b, solution)
        if recovered:
            recover_success(world, a, b, animal_cfg, solution, gift)
            world.para()
            arrival_recovered(world, a, b, elder, errand, gift)
            outcome = "recovered"
        else:
            recover_fail(world, a, b, animal_cfg, solution)
            world.para()
            arrival_lost(world, a, b, elder, errand, gift)
            outcome = "lost"

    world.facts.update(
        errand=errand,
        gift_cfg=gift,
        animal_cfg=animal_cfg,
        solution=solution,
        instigator=a,
        cautioner=b,
        elder=elder,
        bundle=bundle,
        foil=foil,
        animal=animal,
        relation=relation,
        ignited_problem=not averted,
        outcome=outcome,
        recovered=recovered,
        severity=severity,
        delay=delay,
        promised=True,
    )
    return world


ERRANDS = {
    "grandmother_soup": Errand(
        id="grandmother_soup",
        start="the cooking fire",
        destination="their grandmother's little house by the fig roots",
        elder_title="grandmother",
        purpose="Take this hot meal before the steam grows thin.",
        closing="So they ate beneath the fig tree, and the true path home looked wider than before.",
        tags={"elder", "meal"},
    ),
    "healer_buns": Errand(
        id="healer_buns",
        start="the village square",
        destination="the healer's round hut near the river reeds",
        elder_title="grandfather",
        purpose="Carry these buns while they are soft, and do not play with what must be delivered.",
        closing="The healer shared a sweet sip of tea, and the children sat close together without quarrelling.",
        tags={"elder", "meal"},
    ),
    "weaver_cakes": Errand(
        id="weaver_cakes",
        start="the shade of the bread oven",
        destination="the basket-weaver's porch at the edge of the jungle",
        elder_title="grandmother",
        purpose="Bring these cakes with both hands and a quiet mind.",
        closing="When the sun slipped low, they returned along the true path with calmer feet and wiser eyes.",
        tags={"elder", "meal"},
    ),
}

GIFTS = {
    "honey_cakes": Gift(
        id="honey_cakes",
        label="the honey cakes",
        phrase="foil-wrapped honey cakes",
        smell="warm honey and woodsmoke",
        tags={"food", "sweet"},
    ),
    "mango_buns": Gift(
        id="mango_buns",
        label="the mango buns",
        phrase="foil-wrapped mango buns",
        smell="ripe mango and sweet bread",
        tags={"food", "sweet"},
    ),
    "sesame_rice": Gift(
        id="sesame_rice",
        label="the sesame rice balls",
        phrase="foil-wrapped sesame rice balls",
        smell="toasted sesame and steamed rice",
        tags={"food", "meal"},
    ),
}

ANIMALS = {
    "capuchin": Animal(
        id="capuchin",
        label="capuchin monkey",
        movement="swinging down vine by vine",
        cry="ki-ki-ki",
        curious_to_shine=True,
        snatches_food=True,
        quickness=2,
        tags={"monkey", "jungle"},
    ),
    "macaque": Animal(
        id="macaque",
        label="macaque",
        movement="scrambling over the branch tips",
        cry="chak-chak",
        curious_to_shine=True,
        snatches_food=True,
        quickness=3,
        tags={"monkey", "jungle"},
    ),
    "squirrel_monkey": Animal(
        id="squirrel_monkey",
        label="squirrel monkey",
        movement="darting like a strip of sunlight",
        cry="tsee-tsee",
        curious_to_shine=True,
        snatches_food=True,
        quickness=2,
        tags={"monkey", "jungle"},
    ),
    "deer": Animal(
        id="deer",
        label="jungle deer",
        movement="stepping lightly from fern to fern",
        cry="soft snorts",
        curious_to_shine=False,
        snatches_food=False,
        quickness=1,
        tags={"deer", "jungle"},
    ),
}

SOLUTIONS = {
    "decoy": Solution(
        id="decoy",
        sense=3,
        power=3,
        text="they crinkled a loose scrap of foil, laid it shining on a stump, and hid behind a broad root",
        fail="The monkey only clutched the bundle tighter and sprang to a higher branch",
        qa_text="They used a shiny decoy on a stump so the monkey would look away from the bundle",
        tags={"decoy", "problem_solving"},
    ),
    "leaf_trade": Solution(
        id="leaf_trade",
        sense=2,
        power=2,
        text="they set out a broad banana leaf with a few crumbs and stood very still",
        fail="The monkey snatched the crumbs and vanished with the bundle before they could move",
        qa_text="They stayed calm, offered crumbs on a leaf, and waited for a chance to take the bundle back",
        tags={"leaf", "problem_solving"},
    ),
    "chase": Solution(
        id="chase",
        sense=1,
        power=1,
        text="they ran after the monkey, shouting and slapping at the vines",
        fail="The noise only drove it deeper into the branches",
        qa_text="They chased the monkey noisily through the vines",
        tags={"chase"},
    ),
}

GIRL_NAMES = ["Nia", "Ama", "Lela", "Suri", "Tala", "Mira", "Zuri", "Ayo"]
BOY_NAMES = ["Kito", "Timo", "Bako", "Jabari", "Luan", "Pili", "Sefu", "Daro"]
TRAITS = ["careful", "patient", "wise", "steady", "curious", "quick-thinking"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_solutions():
        return combos
    for errand_id in ERRANDS:
        for gift_id, gift in GIFTS.items():
            for animal_id, animal in ANIMALS.items():
                if hazard_at_risk(gift, animal):
                    combos.append((errand_id, gift_id, animal_id))
    return combos


@dataclass
class StoryParams:
    errand: str
    gift: str
    animal: str
    solution: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    elder: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 5
    relation: str = "siblings"
    trust: int = 6
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
    "monkey": [
        (
            "Why do monkeys grab food so fast?",
            "Many monkeys have quick hands and sharp eyes, so they can snatch food in a blink. That is why people should keep food folded away and carry it carefully.",
        )
    ],
    "jungle": [
        (
            "What is a jungle?",
            "A jungle is a thick, warm place full of trees, vines, insects, and animals. Paths can be hard to see there, so people watch where they step.",
        )
    ],
    "foil": [
        (
            "What is foil?",
            "Foil is a thin, shiny sheet of metal often used to wrap food. It keeps food covered, but its bright shine can catch the eye.",
        )
    ],
    "decoy": [
        (
            "What is a decoy?",
            "A decoy is something used to draw attention away from the thing you want to protect. A good decoy helps solve a problem without a fight.",
        )
    ],
    "leaf": [
        (
            "Why can staying still help around animals?",
            "Staying still can keep an animal from feeling chased or excited. Calm bodies often make room for calmer choices.",
        )
    ],
    "problem_solving": [
        (
            "What does problem solving mean?",
            "Problem solving means stopping to think about what is wrong and choosing a plan that fits the problem. It is often wiser than arguing or rushing.",
        )
    ],
    "true_path": [
        (
            "What does a true path mean in a folk tale?",
            "A true path is the safe and honest way forward. In many folk tales, leaving it brings trouble and returning to it shows wisdom.",
        )
    ],
}
KNOWLEDGE_ORDER = ["jungle", "foil", "monkey", "decoy", "leaf", "problem_solving", "true_path"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    errand = f["errand"]
    gift = f["gift_cfg"]
    animal = f["animal_cfg"]
    outcome = f["outcome"]
    if outcome == "averted":
        return [
            'Write a short folk-tale style story for a 3-to-5-year-old that includes the words "jungle", "foil", and "true".',
            f"Tell a cautionary jungle tale where {a.id} wants to wave shiny foil, but {b.id} stops {a.pronoun('object')} before trouble begins, and they keep to the true path.",
            f"Write a gentle story about children carrying {gift.label} to {errand.destination} and learning that true caution can prevent a mistake.",
        ]
    if outcome == "lost":
        return [
            'Write a folk-tale cautionary story using the words "jungle", "foil", and "true", with a conflict between two children and a problem they do not fully fix.',
            f"Tell a jungle story where a {animal.label} steals {gift.label} after a child waves shiny foil, and the children learn a true lesson after making things worse by rushing.",
            f"Write a child-facing cautionary tale where quarrelling wastes time and the ending is sad but safe.",
        ]
    return [
        'Write a short folk-tale style story for a 3-to-5-year-old that includes the words "jungle", "foil", and "true".',
        f"Tell a cautionary problem-solving story where a {animal.label} grabs {gift.label} after shiny foil is waved on a jungle path, and the children must stop quarrelling and think.",
        f"Write a gentle folk tale with conflict, a true warning, and a clever recovery plan that fits the problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    elder = f["elder"]
    errand = f["errand"]
    gift = f["gift_cfg"]
    animal = f["animal_cfg"]
    solution = f["solution"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, walking through the jungle with {gift.label} for their {elder.label_word}. The errand matters because they were trusted to carry something carefully.",
        ),
        (
            "What were they carrying, and where were they going?",
            f"They were carrying {gift.phrase} to {errand.destination}. The bundle had to stay safe because it was meant for someone waiting for them.",
        ),
        (
            f"Why did {b.id} warn {a.id} about the foil?",
            f"{b.id} warned that shiny foil could attract quick jungle eyes. In this story, that warning was true because the monkey noticed the flash and rushed in.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What changed when {a.id} listened?",
                f"{a.id} folded the foil shut and gave up the boastful idea. Because the warning was obeyed, no animal came and the gift reached their {elder.label_word} safely.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with the children arriving safely and being praised for their care. The ending proves the lesson because the bundle stayed neat and the true path stayed free of trouble.",
            )
        )
    elif f["outcome"] == "recovered":
        qa.append(
            (
                f"What happened when {a.id} waved the foil?",
                f"A {animal.label} saw the flash, leapt in, and stole the bundle. The trouble began because the foil was opened and waved instead of being carried quietly.",
            )
        )
        qa.append(
            (
                "How did they solve the problem?",
                f"{solution.qa_text}. They solved it only after they stopped quarrelling, because calm thinking gave them a better chance than angry shouting.",
            )
        )
        qa.append(
            (
                "What did they learn?",
                f"They learned that a true warning should be heeded before trouble starts. They also learned that when a mistake has already happened, clear thinking is better than blame.",
            )
        )
    else:
        qa.append(
            (
                "Why could they not get the bundle back?",
                f"The monkey was too quick for their noisy plan, so the bundle was lost. Their rushing made the problem worse because it scared the animal deeper into the branches.",
            )
        )
        qa.append(
            (
                "What was the true lesson at the end?",
                f"The true lesson was not to show off with something that should be carried with care. They also learned that quarrelling steals time when a problem needs thought.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"jungle", "foil", "true_path", "problem_solving"}
    animal = f["animal_cfg"]
    if "monkey" in animal.tags:
        tags.add("monkey")
    solution = f["solution"]
    tags |= set(solution.tags)
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", 0, False)}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        errand="grandmother_soup",
        gift="honey_cakes",
        animal="capuchin",
        solution="decoy",
        instigator="Kito",
        instigator_gender="boy",
        cautioner="Nia",
        cautioner_gender="girl",
        elder="grandmother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        errand="healer_buns",
        gift="mango_buns",
        animal="squirrel_monkey",
        solution="leaf_trade",
        instigator="Ama",
        instigator_gender="girl",
        cautioner="Bako",
        cautioner_gender="boy",
        elder="grandfather",
        trait="patient",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        errand="weaver_cakes",
        gift="sesame_rice",
        animal="macaque",
        solution="leaf_trade",
        instigator="Timo",
        instigator_gender="boy",
        cautioner="Lela",
        cautioner_gender="girl",
        elder="grandmother",
        trait="wise",
        delay=1,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(gift: Gift, animal: Animal) -> str:
    if not animal.curious_to_shine:
        return (
            f"(No story: a {animal.label} is not modeled as caring about shiny foil, so the warning would not be true. "
            f"Pick an animal like a monkey that notices flashes.)"
        )
    if not animal.snatches_food:
        return (
            f"(No story: a {animal.label} is not modeled as snatching food, so the foil mistake would not create this problem.)"
        )
    return "(No story: this combination does not create a plausible foil-and-food jungle problem.)"


def explain_solution(solution_id: str) -> str:
    sol = SOLUTIONS[solution_id]
    better = ", ".join(sorted(s.id for s in sensible_solutions()))
    return (
        f"(Refusing solution '{solution_id}': it scores too low on common sense "
        f"(sense={sol.sense} < {SENSE_MIN}). Try a calmer fix such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    animal = ANIMALS[params.animal]
    solution = SOLUTIONS[params.solution]
    return "recovered" if is_recovered(solution, animal, params.delay) else "lost"


ASP_RULES = r"""
hazard(G, A) :- gift(G), animal(A), food(G), curious_to_shine(A), snatches_food(A).
valid(E, G, A) :- errand(E), hazard(G, A).

sensible(S) :- solution(S), sense(S, V), sense_min(M), V >= M.

careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).

older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(B), A > B.

severity(Q + D) :- chosen_animal(A), quickness(A, Q), delay(D).
sol_power(P) :- chosen_solution(S), power(S, P).
recovered :- sol_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for errand_id in ERRANDS:
        lines.append(asp.fact("errand", errand_id))
    for gift_id, gift in GIFTS.items():
        lines.append(asp.fact("gift", gift_id))
        if "food" in gift.tags:
            lines.append(asp.fact("food", gift_id))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        if animal.curious_to_shine:
            lines.append(asp.fact("curious_to_shine", animal_id))
        if animal.snatches_food:
            lines.append(asp.fact("snatches_food", animal_id))
        lines.append(asp.fact("quickness", animal_id, animal.quickness))
    for solution_id, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", solution_id))
        lines.append(asp.fact("sense", solution_id, solution.sense))
        lines.append(asp.fact("power", solution_id, solution.power))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
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
    return sorted(s for (s,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_animal", params.animal),
            asp.fact("chosen_solution", params.solution),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_gate = set(asp_valid_combos())
    p_gate = set(valid_combos())
    if c_gate == p_gate:
        print(f"OK: gate matches valid_combos() ({len(c_gate)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_gate - p_gate:
            print("  only in clingo:", sorted(c_gate - p_gate))
        if p_gate - c_gate:
            print("  only in python:", sorted(p_gate - c_gate))

    c_sense = set(asp_sensible())
    p_sense = {s.id for s in sensible_solutions()}
    if c_sense == p_sense:
        print(f"OK: sensible solutions match ({sorted(c_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: clingo={sorted(c_sense)} python={sorted(p_sense)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a jungle errand, shiny foil, a warning, and a true lesson."
    )
    ap.add_argument("--errand", choices=ERRANDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra head start for the animal")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.gift:
        animal = ANIMALS[args.animal]
        gift = GIFTS[args.gift]
        if not hazard_at_risk(gift, animal):
            raise StoryError(explain_rejection(gift, animal))
    if args.animal and not hazard_at_risk(next(iter(GIFTS.values())), ANIMALS[args.animal]):
        if not ANIMALS[args.animal].curious_to_shine or not ANIMALS[args.animal].snatches_food:
            raise StoryError(explain_rejection(next(iter(GIFTS.values())), ANIMALS[args.animal]))
    if args.solution and SOLUTIONS[args.solution].sense < SENSE_MIN:
        raise StoryError(explain_solution(args.solution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.errand is None or combo[0] == args.errand)
        and (args.gift is None or combo[1] == args.gift)
        and (args.animal is None or combo[2] == args.animal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    errand_id, gift_id, animal_id = rng.choice(sorted(combos))
    solution_id = args.solution or rng.choice(sorted(s.id for s in sensible_solutions()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    elder = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        errand=errand_id,
        gift=gift_id,
        animal=animal_id,
        solution=solution_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        elder=elder,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.errand not in ERRANDS:
        raise StoryError(f"(Unknown errand: {params.errand})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    if params.elder not in {"grandmother", "grandfather"}:
        raise StoryError(f"(Unknown elder type: {params.elder})")

    gift = GIFTS[params.gift]
    animal = ANIMALS[params.animal]
    solution = SOLUTIONS[params.solution]
    if not hazard_at_risk(gift, animal):
        raise StoryError(explain_rejection(gift, animal))
    if solution.sense < SENSE_MIN:
        raise StoryError(explain_solution(solution.id))

    world = tell(
        ERRANDS[params.errand],
        gift,
        animal,
        solution,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (errand, gift, animal) combos:\n")
        for errand_id, gift_id, animal_id in combos:
            print(f"  {errand_id:18} {gift_id:13} {animal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.gift} with {p.animal} "
                f"({p.errand}, {p.solution}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
