#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py
=================================================================================

A standalone story world about a grand fair in the town centre, where children
face a bragging-sized problem: something tall must be topped, one child wants to
climb it the foolish way, another warns that the whole giant thing is already
muttering trouble, and a grown-up helps them choose a safer way.

This world is shaped as a cautionary tall tale:
- the setting and objects are exaggerated in a child-friendly way,
- the conflict comes from a risky choice versus a careful warning,
- the foreshadowing comes from visible wobble before the mishap,
- the ending proves that safe help beats proud scrambling.

Run it
------
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py --display apple_crates --method ladder
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py --method stilts
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/centre_cautionary_conflict_foreshadowing_tall_tale.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Display:
    id: str
    label: str
    phrase: str
    material: str
    surface: str
    height: int
    wobble: int
    skyline: str
    groan: str
    tumble_text: str
    stable_text: str
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
class Topper:
    id: str
    label: str
    phrase: str
    shine: str
    final_image: str
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
    label: str
    phrase: str
    reach: int
    support: int
    sense: int
    surfaces: set[str]
    use_text: str
    fail_text: str
    qa_text: str
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
class StoryParams:
    display: str
    topper: str
    method: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    trust: int = 6
    pet: str = ""
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


def _r_sway(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    climber = world.get("climber")
    if display.meters["climbed"] < THRESHOLD:
        return out
    sig = ("sway", display.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["sway"] += float(world.facts["display_cfg"].wobble)
    world.get("centre").meters["danger"] += 1
    climber.memes["fear"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__sway__")
    return out


def _r_drop(world: World) -> list[str]:
    out: list[str] = []
    display = world.get("display")
    if display.meters["sway"] < 2.0:
        return out
    sig = ("drop", display.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    display.meters["dropped_topper"] += 1
    world.get("centre").meters["mess"] += 1
    out.append("__drop__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="sway", tag="physical", apply=_r_sway),
    Rule(name="drop", tag="physical", apply=_r_drop),
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


DISPLAYS = {
    "apple_crates": Display(
        id="apple_crates",
        label="apple-crate tower",
        phrase="a tower of apple crates stacked so high it seemed to tickle the weather",
        material="wood",
        surface="rungs",
        height=3,
        wobble=2,
        skyline="Its top leaned over the town centre like it was trying to hear its own name shouted back.",
        groan="The wooden corners gave a dry little creak, as if the stack had knees and disliked surprises.",
        tumble_text="The crates sprang apart like a flock of startled geese, and apples rolled in every direction.",
        stable_text="The crates stayed put at last, neat and square again.",
        tags={"apples", "crates", "centre"},
    ),
    "haystack": Display(
        id="haystack",
        label="hay hill",
        phrase="a hay hill piled so high it looked fit for giants to nap on",
        material="hay",
        surface="soft",
        height=2,
        wobble=1,
        skyline="A few wisps of straw kept sliding down, as if the hill were quietly combing its own hair.",
        groan="The hay gave a whispery shush under every touch.",
        tumble_text="The hay slumped in a golden sigh and slid into a fluffy hill at the children's feet.",
        stable_text="The hay settled into a tidy hill with the top smoothed flat.",
        tags={"hay", "farm", "centre"},
    ),
    "cheese_wheels": Display(
        id="cheese_wheels",
        label="cheese-wheel stack",
        phrase="a stack of cheese wheels broad as wagon wheels and round as harvest moons",
        material="cheese",
        surface="round",
        height=3,
        wobble=3,
        skyline="The top wheel looked so round and shiny that even the crows watched it the way sailors watch a storm cloud.",
        groan="The whole stack gave a soft rolling grumble.",
        tumble_text="The cheese wheels broke ranks and waddled away in every direction like yellow moons set loose.",
        stable_text="The cheese wheels were chocked and quiet, not rolling an inch.",
        tags={"cheese", "wheels", "centre"},
    ),
}

TOPPERS = {
    "star": Topper(
        id="star",
        label="brass star",
        phrase="a brass star",
        shine="It flashed whenever the sun found it.",
        final_image="At the end, the brass star winked above the town centre like a tiny captured dawn.",
        tags={"star"},
    ),
    "pennant": Topper(
        id="pennant",
        label="red pennant",
        phrase="a red pennant",
        shine="It fluttered and snapped like a little flame that had learned good manners.",
        final_image="At the end, the red pennant danced over the town centre and showed everyone the wind had turned friendly.",
        tags={"pennant"},
    ),
    "bell": Topper(
        id="bell",
        label="silver bell",
        phrase="a silver bell",
        shine="It gave one bright ding whenever it swung.",
        final_image="At the end, the silver bell chimed over the town centre, clear as a teaspoon tapping a moonbeam.",
        tags={"bell"},
    ),
}

METHODS = {
    "ladder": Method(
        id="ladder",
        label="orchard ladder",
        phrase="an orchard ladder",
        reach=3,
        support=3,
        sense=3,
        surfaces={"rungs", "soft"},
        use_text="set up the orchard ladder on firm boards, climbed only a little way, and fixed the {topper} neatly on top",
        fail_text="tried the orchard ladder, but there was nowhere firm to set it and the job still sat too high and wild",
        qa_text="used the orchard ladder to reach the top safely",
        tags={"ladder"},
    ),
    "hook_pole": Method(
        id="hook_pole",
        label="hooked fair pole",
        phrase="a hooked fair pole",
        reach=3,
        support=2,
        sense=3,
        surfaces={"rungs", "round", "soft"},
        use_text="used the hooked fair pole from the ground and lifted the {topper} into place without letting anyone climb",
        fail_text="raised the hooked fair pole, but the top swayed too much for such a careful job",
        qa_text="used a hooked pole from the ground so nobody had to climb",
        tags={"pole"},
    ),
    "wagon": Method(
        id="wagon",
        label="wagon platform",
        phrase="a wagon platform",
        reach=2,
        support=2,
        sense=2,
        surfaces={"soft"},
        use_text="rolled over the wagon platform and stood on it just high enough to settle the {topper} onto the smoothed top",
        fail_text="brought the wagon platform, but it was too short for that towering job",
        qa_text="used the wagon platform to raise the topper safely",
        tags={"wagon"},
    ),
    "stilts": Method(
        id="stilts",
        label="festival stilts",
        phrase="festival stilts",
        reach=2,
        support=1,
        sense=1,
        surfaces={"rungs", "round", "soft"},
        use_text="strapped on the festival stilts and tottered toward the top",
        fail_text="strapped on the festival stilts, which only made a silly danger look sillier",
        qa_text="tried festival stilts",
        tags={"stilts"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Tess", "Ruby", "Lila", "June", "Poppy", "Ada", "Molly", "Wren"]
BOY_NAMES = ["Bo", "Finn", "Jory", "Cal", "Ned", "Otis", "Rory", "Eli", "Milo", "Tate"]
TRAITS = ["careful", "steady", "curious", "sensible", "thoughtful", "bold"]
PETS = ["the goat", "the little dog", "the old mule", "the cat"]


def method_fits(method: Method, display: Display) -> bool:
    return (
        method.sense >= SENSE_MIN
        and display.surface in method.surfaces
        and method.reach >= display.height
        and method.support >= display.wobble
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for display_id, display in DISPLAYS.items():
        for topper_id in TOPPERS:
            for method_id, method in METHODS.items():
                if method_fits(method, display):
                    combos.append((display_id, topper_id, method_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def method_succeeds(method: Method, display: Display) -> bool:
    return (
        display.surface in method.surfaces
        and method.reach >= display.height
        and method.support >= display.wobble
    )


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("display").meters["climbed"] += 1
    propagate(sim, narrate=False)
    return {
        "sway": sim.get("display").meters["sway"],
        "drop": sim.get("display").meters["dropped_topper"] >= THRESHOLD,
        "danger": sim.get("centre").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, display: Display, topper: Topper) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On fair morning, {a.id} and {b.id} hurried into the town centre, where {display.phrase} waited for the parade."
    )
    world.say(
        f"The children had been chosen to help place {topper.phrase} at the very top. {topper.shine}"
    )
    world.say(display.skyline)


def foreshadow(world: World, display: Display) -> None:
    world.say(
        f"Even before anybody touched it, {display.groan} That was the sort of small sound that should have made a sensible child stop and think."
    )


def boast(world: World, a: Entity, display: Display, topper: Topper) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"No need to fetch a grown-up," {a.id} said. "I can scamper up that {display.label} quicker than a squirrel can blink and set {topper.phrase} there myself."'
    )


def warn(world: World, b: Entity, a: Entity, display: Display, parent: Entity) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_sway"] = pred["sway"]
    world.facts["predicted_drop"] = pred["drop"]
    b.memes["caution"] += 1
    extra = ""
    if pred["drop"]:
        extra = " If you climb it, the top will shake and the prize may come flying down."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, don\'t. {parent.label_word.capitalize()} said the town centre is busy today, and that stack is already talking in creaks.{extra}"'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} puffed up for one more second, then let the proud idea slide out of {a.pronoun('possessive')} head. Together the children went to find {parent.label_word} instead of testing their luck."
    )


def climb(world: World, a: Entity, display: Display, topper: Topper) -> None:
    world.get("display").meters["climbed"] += 1
    a.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {a.id} snatched up {topper.phrase} and started up the {display.label} anyway, climbing as if bragging could make a shaky thing sturdy."
    )
    if world.get("display").meters["sway"] >= THRESHOLD:
        world.say(
            f"At once the whole {display.label} swayed under {a.pronoun('possessive')} feet. The town centre seemed to hold its breath."
        )
    if world.get("display").meters["dropped_topper"] >= THRESHOLD:
        world.say(
            f"{topper.phrase.capitalize()} slipped from {a.pronoun('possessive')} hand and came flashing down through the air."
        )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    b.memes["fear"] += 1
    world.say(f'"{a.id}!" {b.id} cried. "{parent.label_word.capitalize()}! Quick!"')


def rescue_success(world: World, parent: Entity, display: Display, topper: Topper, method: Method) -> None:
    world.get("display").meters["climbed"] = 0.0
    world.get("display").meters["sway"] = 0.0
    world.get("centre").meters["danger"] = 0.0
    world.get("display").meters["safe_fix"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came at a run, took one look, and {method.use_text.format(topper=topper.label)}."
    )
    world.say(
        f"{display.stable_text} Soon {topper.final_image}"
    )


def rescue_fail(world: World, parent: Entity, display: Display, topper: Topper, method: Method) -> None:
    world.get("display").meters["fallen"] += 1
    world.get("centre").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {method.fail_text}."
    )
    world.say(
        f"Then {display.tumble_text} {topper.phrase.capitalize()} landed in the straw and dust with a clink that sounded much smaller than all the boasting before it."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, method: Method) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{parent.label_word.capitalize()} pulled the children close and spoke in a voice calmer than the church clock. "Height is not the same as skill," {parent.pronoun()} said. "When a job stands over your head, you ask for the right help instead of climbing your pride."'
    )
    world.say(
        f'{a.id} nodded hard. {b.id} nodded too. After that, the children remembered that {method.label} was for reaching, and children\'s feet were for staying on steady ground.'
    )


def gentle_end(world: World, a: Entity, b: Entity, topper: Topper) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"By parade time, {a.id} and {b.id} stood shoulder to shoulder in the town centre and looked up without trying to climb a thing. {topper.final_image}"
    )


def cautionary_end(world: World, a: Entity, b: Entity, display: Display) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    pet = world.facts.get("pet", "")
    pet_line = f" Even {pet} stopped nosing about and stared at the heap." if pet else ""
    world.say(
        f"No one was hurt, and that mattered most. But the parade workers spent the morning gathering up the mess where the {display.label} had stood.{pet_line}"
    )
    world.say(
        f"{a.id} did not brag again that day. In the quiet after the tumble, the lesson sounded bigger than any tall tale."
    )


def safe_setup(world: World, parent: Entity, display: Display, topper: Topper, method: Method) -> None:
    world.say(
        f"{parent.label_word.capitalize()} listened, looked at the {display.label}, and chose {method.phrase} at once. The careful plan looked almost boring beside a wild climb, which is one reason it worked so well."
    )
    world.say(
        f"{parent.pronoun().capitalize()} {method.use_text.format(topper=topper.label)}."
    )
    world.say(display.stable_text)


def tell(
    display: Display,
    topper: Topper,
    method: Method,
    instigator: str = "Bo",
    instigator_gender: str = "boy",
    cautioner: str = "Mira",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    relation: str = "siblings",
    instigator_age: int = 6,
    cautioner_age: int = 4,
    trust: int = 6,
    pet: str = "",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            attrs={"relation": relation},
            traits=["bold"],
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    world.add(Entity(id="centre", type="place", label="the town centre"))
    world.add(Entity(id="display", type="display", label=display.label))
    world.add(Entity(id="climber", type=instigator_gender, label=instigator))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    world.facts.update(
        display_cfg=display,
        topper_cfg=topper,
        method_cfg=method,
        pet=pet,
        relation=relation,
    )

    introduce(world, a, b, display, topper)
    foreshadow(world, display)

    world.para()
    boast(world, a, display, topper)
    warn(world, b, a, display, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    succeeded = method_succeeds(method, display)

    if averted:
        back_down(world, a, b, parent)
        world.para()
        safe_setup(world, parent, display, topper, method)
        lesson(world, parent, a, b, method)
        world.para()
        gentle_end(world, a, b, topper)
        outcome = "averted"
    else:
        world.para()
        climb(world, a, display, topper)
        alarm(world, b, a, parent)
        world.para()
        if succeeded:
            rescue_success(world, parent, display, topper, method)
            lesson(world, parent, a, b, method)
            world.para()
            gentle_end(world, a, b, topper)
            outcome = "saved"
        else:
            rescue_fail(world, parent, display, topper, method)
            lesson(world, parent, a, b, method)
            world.para()
            cautionary_end(world, a, b, display)
            outcome = "tumbled"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        display=world.get("display"),
        topper=topper,
        method=method,
        outcome=outcome,
        averted=averted,
        succeeded=succeeded,
        toppled=world.get("display").meters["fallen"] >= THRESHOLD,
        dropped=world.get("display").meters["dropped_topper"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    display = f["display_cfg"]
    topper = f["topper_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a child-friendly tall tale set in a town centre where two children must place {topper.phrase} on {display.phrase}. '
        f'Include foreshadowing, a warning, and the word "centre".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a cautionary story where {a.id} boasts about climbing the {display.label}, but {b.id} stops that bad idea before anyone gets hurt.",
            f"Write a conflict story in a tall-tale voice where a careful child warns that a towering display in the centre is already wobbling, and the children choose safe help instead.",
        ]
    if outcome == "tumbled":
        return [
            base,
            f"Tell a cautionary tall tale where {a.id} ignores {b.id}'s warning, the {display.label} gives way, and the parade display is lost even though everyone stays safe.",
            f"Write a story with foreshadowing and conflict in which pride leads to a tumble in the town centre, and the ending teaches children not to climb shaky things.",
        ]
    return [
        base,
        f"Tell a tall tale where {a.id} ignores {b.id}'s warning and starts climbing, but a grown-up uses the right tool to save the day in the centre.",
        f"Write a cautionary story with a close call, a calm lesson, and an ending image above the town centre that proves the children learned safer habits.",
    ]


KNOWLEDGE = {
    "centre": [
        (
            "What is a town centre?",
            "A town centre is the middle part of a town where many people gather, shop, and hold events. It is often a busy place, so children need to be extra careful there.",
        )
    ],
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps someone reach a high place step by step. It must stand on firm ground and be used carefully.",
        )
    ],
    "pole": [
        (
            "Why might a long pole be safer than climbing?",
            "A long pole can reach something high while your feet stay on the ground. Staying on the ground is often safer than climbing a shaky object.",
        )
    ],
    "wagon": [
        (
            "What is a wagon platform?",
            "A wagon platform is a flat raised surface on a wagon. It can make a person a little taller, but it still cannot safely reach every high job.",
        )
    ],
    "stilts": [
        (
            "Why are stilts a bad idea for careful work?",
            "Stilts make a person taller, but they also make balancing much harder. That is why they are poor tools for a delicate, high job.",
        )
    ],
    "crates": [
        (
            "Why can stacked crates be dangerous?",
            "Stacked crates can slide or tip if they are climbed or bumped. A tall stack may look strong, but each box depends on the others staying still.",
        )
    ],
    "hay": [
        (
            "Why is a haystack slippery for climbing?",
            "Hay slides and shifts under feet, so it does not make firm steps. A person can sink, slip, or knock the shape loose.",
        )
    ],
    "cheese": [
        (
            "Why do round things roll?",
            "Round things roll because their shape keeps turning along the ground. That is why stacked wheels can move in a hurry if they are not held still.",
        )
    ],
    "star": [
        (
            "Why do brass stars shine?",
            "Brass can reflect light, so a brass star flashes when the sun hits it. That is why it looks bright even from far away.",
        )
    ],
    "bell": [
        (
            "How does a bell make a sound?",
            "A bell rings when something inside it or against it strikes the metal. The metal vibrates and sends the sound into the air.",
        )
    ],
    "pennant": [
        (
            "Why does a pennant flap in the wind?",
            "A pennant is a light piece of cloth, so moving air pushes it easily. The cloth bends and flutters as the wind passes by.",
        )
    ],
}
KNOWLEDGE_ORDER = ["centre", "crates", "hay", "cheese", "ladder", "pole", "wagon", "stilts", "star", "bell", "pennant"]


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
    display_cfg = f["display_cfg"]
    topper = f["topper_cfg"]
    method = f["method"]
    relation = f["relation"]
    outcome = f["outcome"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, helping at the town centre fair. Their proud idea and careful warning make the trouble in the story.",
        ),
        (
            "What were the children trying to do?",
            f"They were trying to place {topper.phrase} on top of the huge {display_cfg.label} for the parade. The job seemed exciting because the display was so high and showy.",
        ),
        (
            f"What warning sign came before the real trouble?",
            f"The {display_cfg.label} was already making small uneasy sounds and looking unsteady before anyone climbed it. That foreshadowed that the boastful plan was unsafe.",
        ),
        (
            f"Why did {b.id} tell {a.id} not to climb?",
            f"{b.id} could see that the {display_cfg.label} was already shaky in the busy centre. {b.pronoun().capitalize()} warned that climbing would make it sway and might knock the topper loose.",
        ),
    ]
    if outcome == "averted":
        qa.extend(
            [
                (
                    f"What did {a.id} do after the warning?",
                    f"{a.id} gave up the climbing idea and went to get a grown-up. That choice ended the conflict before the dangerous part could begin.",
                ),
                (
                    "How was the problem solved?",
                    f"The grown-up used {method.phrase} instead of letting a child climb. That safer method reached the top without turning the job into a wobbling contest.",
                ),
                (
                    "How did the story end?",
                    f"It ended peacefully, with the topper shining above the town centre and the children looking up from the ground. The ending shows they learned that asking for the right help is wiser than showing off.",
                ),
            ]
        )
    elif outcome == "saved":
        qa.extend(
            [
                (
                    f"What happened when {a.id} climbed?",
                    f"The {display_cfg.label} swayed and the whole centre seemed to gasp. The trouble happened because bragging did not make the tall stack any steadier.",
                ),
                (
                    f"How did {parent.label_word} fix the problem?",
                    f"{parent.label_word.capitalize()} {method.qa_text}. That worked because the tool matched the height and shape of the display better than a child's feet ever could.",
                ),
                (
                    "What lesson did the children learn?",
                    f"They learned that a high job needs the right help, not a proud climb. The close call made the warning feel true instead of just bossy.",
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"Could {parent.label_word} save the display in time?",
                    f"No. {parent.label_word.capitalize()} tried, but the method was not enough for that tall, unstable stack. The display tumbled, even though everyone stayed safe.",
                ),
                (
                    "Why is this a cautionary ending?",
                    f"It shows that ignoring a warning can spoil something big and public in a moment. No one was hurt, but the loss in the centre proves that reckless pride has a cost.",
                ),
                (
                    "What changed by the end?",
                    f"{a.id} stopped boasting and understood why the warning mattered. The quiet heap where the display had stood was a stronger lesson than any scolding could have been.",
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"centre"}
    display_cfg = world.facts["display_cfg"]
    method = world.facts["method"]
    topper = world.facts["topper_cfg"]
    tags |= set(display_cfg.tags)
    tags |= set(method.tags)
    tags |= set(topper.tags)
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        display="haystack",
        topper="pennant",
        method="wagon",
        instigator="Bo",
        instigator_gender="boy",
        cautioner="Mira",
        cautioner_gender="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=5,
        pet="the little dog",
    ),
    StoryParams(
        display="apple_crates",
        topper="star",
        method="ladder",
        instigator="Finn",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=4,
        pet="the goat",
    ),
    StoryParams(
        display="cheese_wheels",
        topper="bell",
        method="hook_pole",
        instigator="Tess",
        instigator_gender="girl",
        cautioner="Rory",
        cautioner_gender="boy",
        parent="mother",
        trait="sensible",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
        trust=6,
        pet="the cat",
    ),
    StoryParams(
        display="cheese_wheels",
        topper="star",
        method="wagon",
        instigator="Nell",
        instigator_gender="girl",
        cautioner="Bo",
        cautioner_gender="boy",
        parent="father",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
        trust=7,
        pet="the old mule",
    ),
]


def explain_display_method(display: Display, method: Method) -> str:
    reasons: list[str] = []
    if method.sense < SENSE_MIN:
        reasons.append(f"{method.label} is a low-common-sense choice")
    if display.surface not in method.surfaces:
        reasons.append(f"{method.label} does not suit a {display.surface} surface")
    if method.reach < display.height:
        reasons.append(f"{method.label} is too short for that display")
    if method.support < display.wobble:
        reasons.append(f"{method.label} is not steady enough for a wobble score of {display.wobble}")
    if not reasons:
        reasons.append("that method does not make a reasonable story here")
    return "(No story: " + "; ".join(reasons) + ".)"


def explain_combo_filter() -> str:
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    display = DISPLAYS[params.display]
    method = METHODS[params.method]
    return "saved" if method_succeeds(method, display) else "tumbled"


ASP_RULES = r"""
valid(D, T, M) :- display(D), topper(T), method(M),
                  sense(M, S), sense_min(Min), S >= Min,
                  surface(D, Surf), suited(M, Surf),
                  height(D, H), reach(M, R), R >= H,
                  wobble(D, W), support(M, P), P >= W.

cautious_now(T)  :- trait(T), is_cautious(T).
init_caution(5)  :- trait(T), cautious_now(T).
init_caution(3)  :- trait(T), not cautious_now(T).
cautioner_older  :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4)         :- cautioner_older.
bonus(0)         :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted          :- cautioner_older, authority(A), bravery_init(BR), A > BR.

method_ok        :- chosen_method(M), chosen_display(D),
                    surface(D, Surf), suited(M, Surf),
                    height(D, H), reach(M, R), R >= H,
                    wobble(D, W), support(M, P), P >= W.

outcome(averted) :- averted.
outcome(saved)   :- not averted, method_ok.
outcome(tumbled) :- not averted, not method_ok.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did, d in DISPLAYS.items():
        lines.append(asp.fact("display", did))
        lines.append(asp.fact("surface", did, d.surface))
        lines.append(asp.fact("height", did, d.height))
        lines.append(asp.fact("wobble", did, d.wobble))
    for tid in TOPPERS:
        lines.append(asp.fact("topper", tid))
    for mid, m in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("reach", mid, m.reach))
        lines.append(asp.fact("support", mid, m.support))
        lines.append(asp.fact("sense", mid, m.sense))
        for surf in sorted(m.surfaces):
            lines.append(asp.fact("suited", mid, surf))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_display", params.display),
            asp.fact("chosen_method", params.method),
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
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tall fair in the town centre, a risky climb, and a safer way."
    )
    ap.add_argument("--display", choices=DISPLAYS)
    ap.add_argument("--topper", choices=TOPPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.display and args.method:
        if not method_fits(METHODS[args.method], DISPLAYS[args.display]):
            raise StoryError(explain_display_method(DISPLAYS[args.display], METHODS[args.method]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        display = DISPLAYS[args.display] if args.display else next(iter(DISPLAYS.values()))
        raise StoryError(explain_display_method(display, METHODS[args.method]))

    combos = [
        c
        for c in valid_combos()
        if (args.display is None or c[0] == args.display)
        and (args.topper is None or c[1] == args.topper)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError(explain_combo_filter())

    display_id, topper_id, method_id = rng.choice(sorted(combos))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    trait = rng.choice(TRAITS)
    parent = args.parent or rng.choice(["mother", "father"])
    pet = rng.choice(PETS + ["", ""])
    return StoryParams(
        display=display_id,
        topper=topper_id,
        method=method_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        trust=trust,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    if params.display not in DISPLAYS:
        raise StoryError(f"(Unknown display: {params.display})")
    if params.topper not in TOPPERS:
        raise StoryError(f"(Unknown topper: {params.topper})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    display = DISPLAYS[params.display]
    topper = TOPPERS[params.topper]
    method = METHODS[params.method]

    world = tell(
        display=display,
        topper=topper,
        method=method,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
        pet=params.pet,
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
        print(f"{len(combos)} compatible (display, topper, method) combos:\n")
        for display, topper, method in combos:
            print(f"  {display:14} {topper:8} {method}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.instigator} & {p.cautioner}: {p.display} / {p.topper} / {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
