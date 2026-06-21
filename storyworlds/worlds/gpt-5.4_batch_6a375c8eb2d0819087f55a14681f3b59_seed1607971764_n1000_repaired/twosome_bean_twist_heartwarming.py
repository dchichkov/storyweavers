#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py
=============================================================

A standalone storyworld about a child-sized twosome who plant a bean together,
worry when it seems to disappear, and discover a heartwarming twist: a caring
grown-up moved it to a better home so it could live.

The world model tracks physical state (soil wetness, root risk, transplanting,
sprouting) and emotional state (hope, worry, relief, trust). The prose is
rendered from those states, not from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --starter teacup
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --starter nursery_pot
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --trace
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --asp
    python storyworlds/worlds/gpt-5.4/twosome_bean_twist_heartwarming.py --verify
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
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
class Setting:
    id: str
    label: str
    light_line: str
    morning_line: str
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
class Starter:
    id: str
    label: str
    phrase: str
    drainage: int
    room: int
    texture: str
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
class NewHome:
    id: str
    label: str
    phrase: str
    drainage: int
    room: int
    place_line: str
    reveal_line: str
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
class HelperAction:
    id: str
    sense: int
    power: int
    text: str
    qa_text: str
    fail_text: str
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


def root_risk(starter: Starter, extra_water: int) -> int:
    return max(0, (3 - starter.drainage) + (2 - starter.room) + extra_water)


def can_help(starter: Starter, new_home: NewHome, action: HelperAction) -> bool:
    return new_home.drainage > starter.drainage and new_home.room > starter.room and action.sense >= SENSE_MIN


def rescue_strength(new_home: NewHome, action: HelperAction) -> int:
    return new_home.drainage + new_home.room + action.power


def saved_bean(starter: Starter, new_home: NewHome, action: HelperAction, extra_water: int) -> bool:
    return rescue_strength(new_home, action) > root_risk(starter, extra_water)


def sensible_actions() -> list[HelperAction]:
    return [a for a in ACTIONS.values() if a.sense >= SENSE_MIN]


def _r_soggy_risk(world: World) -> list[str]:
    bean = world.get("bean")
    starter = world.get("starter")
    if starter.meters["wet"] < THRESHOLD or bean.attrs.get("home") != "starter":
        return []
    sig = ("soggy_risk",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bean.meters["root_risk"] += world.facts["risk"]
    return []


def _r_empty_cup_worry(world: World) -> list[str]:
    starter = world.get("starter")
    bean = world.get("bean")
    if starter.meters["empty"] < THRESHOLD or bean.attrs.get("home") != "new_home":
        return []
    sig = ("empty_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for role in ("child1", "child2"):
        world.get(role).memes["worry"] += 1
    return ["__empty__"]


def _r_good_home_sprout(world: World) -> list[str]:
    bean = world.get("bean")
    new_home = world.get("new_home")
    if bean.attrs.get("home") != "new_home":
        return []
    if new_home.meters["ready"] < THRESHOLD:
        return []
    if bean.meters["root_risk"] >= world.facts["rescue_strength"]:
        return []
    sig = ("sprout",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bean.meters["sprouted"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soggy_risk", tag="physical", apply=_r_soggy_risk),
    Rule(name="empty_cup_worry", tag="emotional", apply=_r_empty_cup_worry),
    Rule(name="good_home_sprout", tag="physical", apply=_r_good_home_sprout),
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


def predict_risk(world: World) -> dict:
    sim = world.copy()
    sim.get("starter").meters["wet"] = 1.0
    propagate(sim, narrate=False)
    return {
        "risk": int(sim.get("bean").meters["root_risk"]),
        "needs_help": sim.get("bean").meters["root_risk"] > 0,
    }


def introduce(world: World, c1: Entity, c2: Entity, setting: Setting, starter: Starter) -> None:
    for kid in (c1, c2):
        kid.memes["joy"] += 1
        kid.memes["hope"] += 1
    world.say(
        f"{c1.id} and {c2.id} were a cheerful twosome who liked making small plans together. "
        f"One afternoon, they filled {starter.phrase} with soft soil and tucked a bean inside."
    )
    world.say(
        f"They pressed the soil with careful fingertips and set it on {setting.label}. "
        f"{setting.light_line}"
    )


def vow_to_watch(world: World, c1: Entity, c2: Entity, starter: Starter) -> None:
    world.say(
        f'"Let\'s look every morning," {c1.id} said. '
        f'"And every night," {c2.id} added, patting {starter.label} as if the bean could hear.'
    )
    world.say("To them, the little seed already felt like a tiny promise.")


def water_too_much(world: World, c1: Entity, c2: Entity, starter: Starter) -> None:
    starter.meters["wet"] = 1.0
    c1.memes["care"] += 1
    c2.memes["care"] += 1
    amount = world.facts["extra_water"]
    if amount == 0:
        world.say(
            f"That evening, the children gave the soil a sip of water and whispered good night to the bean."
        )
    else:
        world.say(
            f"That evening, each child wanted to be extra helpful, so the soil in the {starter.label} got watered twice."
        )
        world.say("The top looked shiny and dark, and a little puddle clung near the edge.")
    propagate(world, narrate=False)


def night_notice(world: World, helper: Entity, starter: Starter, bean: Entity) -> None:
    pred = predict_risk(world)
    world.facts["predicted_risk"] = pred["risk"]
    helper.memes["care"] += 1
    if pred["needs_help"]:
        world.say(
            f"Later, when the house was quiet, {helper.label_word.capitalize()} passed by and noticed how soggy the soil looked in the {starter.label}."
        )
        world.say(
            f'{helper.pronoun().capitalize()} touched the rim, thought about the bean\'s tender roots, and whispered, '
            f'"This little one needs a safer place."'
        )
    else:
        world.say(
            f"Later, {helper.label_word} checked the {starter.label} and smiled at the neat little mound of soil."
        )


def transplant(world: World, helper: Entity, action: HelperAction, new_home: NewHome) -> None:
    bean = world.get("bean")
    starter = world.get("starter")
    starter.meters["empty"] = 1.0
    starter.meters["wet"] = 0.0
    bean.attrs["home"] = "new_home"
    bean.meters["moved"] = 1.0
    world.get("new_home").meters["ready"] = 1.0
    helper.memes["care"] += 1
    world.say(
        f"{helper.label_word.capitalize()} {action.text.format(new_home=new_home.phrase)}"
    )
    propagate(world, narrate=False)


def morning_panic(world: World, c1: Entity, c2: Entity, starter: Starter) -> None:
    propagate(world, narrate=False)
    if c1.memes["worry"] >= THRESHOLD or c2.memes["worry"] >= THRESHOLD:
        world.say(
            f"In the morning, the twosome hurried back to the {starter.label}. "
            f"The soil was gone, and the little cup sat empty."
        )
        world.say(
            f'"Our bean!" {c2.id} gasped. {c1.id} stared at the bare {starter.label} and felt a lump rise in {c1.pronoun("possessive")} throat.'
        )


def reveal_saved(world: World, helper: Entity, c1: Entity, c2: Entity, new_home: NewHome) -> None:
    bean = world.get("bean")
    for kid in (c1, c2):
        kid.memes["relief"] += 1
        kid.memes["trust"] += 1
        kid.memes["joy"] += 1
        kid.memes["worry"] = 0.0
    helper.memes["love"] += 1
    sprout_line = "A pale green loop was lifting out of the soil like a tiny hello." if bean.meters["sprouted"] >= THRESHOLD else "The soil looked calm and crumbly, ready to help the bean begin again."
    world.say(
        f'Then {helper.label_word} called from nearby. "{bean.label.capitalize()} is not gone," {helper.pronoun()} said. '
        f'"Come and see."'
    )
    world.say(
        f"On {new_home.place_line} stood {new_home.phrase}. {sprout_line} {new_home.reveal_line}"
    )
    world.say(
        f"{c1.id} and {c2.id} looked at each other, and the worry in their faces melted into shining relief."
    )


def explain_and_end(world: World, helper: Entity, c1: Entity, c2: Entity, starter: Starter, new_home: NewHome) -> None:
    bean = world.get("bean")
    if bean.meters["sprouted"] >= THRESHOLD:
        world.say(
            f'"The {starter.label} was holding too much water," {helper.label_word} explained gently. '
            f'"So I moved your bean into {new_home.phrase}, where its roots could breathe and grow."'
        )
        world.say(
            f"The children touched the rim of the new pot together. Side by side, the twosome watched the small green sprout and felt as if the morning had opened just for them."
        )
    else:
        world.say(
            f'"The {starter.label} was much too soggy," {helper.label_word} explained softly. '
            f'"I moved your bean into {new_home.phrase} so it still has a chance."'
        )
        world.say(
            f"{c2.id} leaned against {helper.label_word}, and {c1.id} nodded. Together they promised to give the bean sunshine, patience, and only the water it needed."
        )
        world.say(
            f"By the window, the new pot looked steadier than the old one, and that steadiness made everyone feel hopeful again."
        )


def tell(
    setting: Setting,
    starter_cfg: Starter,
    new_home_cfg: NewHome,
    action_cfg: HelperAction,
    child1_name: str = "Lina",
    child1_type: str = "girl",
    child2_name: str = "Owen",
    child2_type: str = "boy",
    helper_type: str = "grandmother",
    extra_water: int = 1,
) -> World:
    world = World()
    world.facts["extra_water"] = extra_water
    world.facts["risk"] = root_risk(starter_cfg, extra_water)
    world.facts["rescue_strength"] = rescue_strength(new_home_cfg, action_cfg)

    c1 = world.add(Entity(id=child1_name, kind="character", type=child1_type, role="child1"))
    c2 = world.add(Entity(id=child2_name, kind="character", type=child2_type, role="child2"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper", label="the helper"))
    starter = world.add(Entity(id="starter", type="starter", label=starter_cfg.label))
    new_home = world.add(Entity(id="new_home", type="pot", label=new_home_cfg.label))
    bean = world.add(Entity(id="bean", type="bean", label="bean", attrs={"home": "starter"}))

    bean.meters["root_risk"] = 0.0
    bean.meters["sprouted"] = 0.0
    bean.meters["moved"] = 0.0
    starter.meters["wet"] = 0.0
    starter.meters["empty"] = 0.0
    new_home.meters["ready"] = 0.0

    introduce(world, c1, c2, setting, starter_cfg)
    vow_to_watch(world, c1, c2, starter_cfg)

    world.para()
    water_too_much(world, c1, c2, starter_cfg)
    night_notice(world, helper, starter_cfg, bean)
    transplant(world, helper, action_cfg, new_home_cfg)

    world.para()
    morning_panic(world, c1, c2, starter_cfg)
    reveal_saved(world, helper, c1, c2, new_home_cfg)
    explain_and_end(world, helper, c1, c2, starter_cfg, new_home_cfg)

    outcome = "sprouted" if bean.meters["sprouted"] >= THRESHOLD else "saved"
    world.facts.update(
        child1=c1,
        child2=c2,
        helper=helper,
        setting=setting,
        starter_cfg=starter_cfg,
        new_home_cfg=new_home_cfg,
        action=action_cfg,
        bean=bean,
        outcome=outcome,
        twist_happened=starter.meters["empty"] >= THRESHOLD and bean.meters["moved"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "windowsill": Setting(
        id="windowsill",
        label="the sunny kitchen windowsill",
        light_line="The light there was warm and square, the kind that made dust look like gold.",
        morning_line="The morning sun laid a bright stripe across the sill.",
        tags={"sunlight", "window"},
    ),
    "porch": Setting(
        id="porch",
        label="the back porch shelf",
        light_line="A soft breeze came through the screen and made the day feel gentle.",
        morning_line="Morning light slipped across the porch boards.",
        tags={"sunlight", "porch"},
    ),
    "table": Setting(
        id="table",
        label="the breakfast table beside the window",
        light_line="The nearby window filled the room with a pale, cozy glow.",
        morning_line="The tablecloth shone softly in the morning light.",
        tags={"sunlight", "window"},
    ),
}

STARTERS = {
    "teacup": Starter(
        id="teacup",
        label="teacup",
        phrase="a little teacup",
        drainage=0,
        room=0,
        texture="smooth and pretty",
        tags={"cup", "drainage"},
    ),
    "jam_jar": Starter(
        id="jam_jar",
        label="jar",
        phrase="an old jam jar",
        drainage=0,
        room=1,
        texture="clear and shiny",
        tags={"jar", "drainage"},
    ),
    "paper_cup": Starter(
        id="paper_cup",
        label="paper cup",
        phrase="a paper cup with crayon hearts on it",
        drainage=1,
        room=1,
        texture="light and cheerful",
        tags={"cup", "drainage"},
    ),
    "nursery_pot": Starter(
        id="nursery_pot",
        label="nursery pot",
        phrase="a small nursery pot with holes underneath",
        drainage=3,
        room=2,
        texture="plain but sensible",
        tags={"pot"},
    ),
}

NEW_HOMES = {
    "blue_pot": NewHome(
        id="blue_pot",
        label="blue flowerpot",
        phrase="a blue flowerpot with good dark soil",
        drainage=3,
        room=3,
        place_line="the brightest part of the windowsill",
        reveal_line="The pot looked roomy and safe, as if someone had made a proper bed for the little seed.",
        tags={"pot", "transplant"},
    ),
    "window_box": NewHome(
        id="window_box",
        label="window box",
        phrase="a wooden window box with crumbly soil",
        drainage=3,
        room=4,
        place_line="the porch shelf where the morning sun lingered",
        reveal_line="There was enough space for roots to stretch without bumping into glass or china.",
        tags={"box", "transplant"},
    ),
    "clay_pot": NewHome(
        id="clay_pot",
        label="clay pot",
        phrase="a warm clay pot with a little saucer",
        drainage=4,
        room=3,
        place_line="the corner by the window where the light stayed longest",
        reveal_line="The clay pot smelled like clean earth after rain.",
        tags={"pot", "transplant"},
    ),
    "tiny_jar": NewHome(
        id="tiny_jar",
        label="tiny jar",
        phrase="a tiny jar with heavy wet soil",
        drainage=0,
        room=1,
        place_line="the same old spot by the window",
        reveal_line="It did not look much safer than before.",
        tags={"jar"},
    ),
}

ACTIONS = {
    "transplant": HelperAction(
        id="transplant",
        sense=3,
        power=3,
        text='carefully lifted the bean with a spoon, tucked it into {new_home}, and turned it toward the morning light.',
        qa_text="moved the bean into a bigger pot with better soil and drainage",
        fail_text="moved the bean, but the roots had already spent too long in soggy soil",
        tags={"transplant", "roots"},
    ),
    "rehome_gently": HelperAction(
        id="rehome_gently",
        sense=2,
        power=2,
        text='gently loosened the soil, moved the bean into {new_home}, and patted the top smooth with loving hands.',
        qa_text="replanted the bean in a safer pot so its roots could breathe",
        fail_text="replanted the bean, but it still struggled after sitting in too much water",
        tags={"transplant", "roots"},
    ),
    "do_nothing": HelperAction(
        id="do_nothing",
        sense=1,
        power=0,
        text='only looked at the soggy cup and hoped for the best.',
        qa_text="left the bean where it was",
        fail_text="left the bean in the soggy starter, which did not solve the problem",
        tags={"neglect"},
    ),
}

GIRL_NAMES = ["Lina", "Mia", "Ava", "Nora", "Zoe", "Ella", "Ruby", "Ivy"]
BOY_NAMES = ["Owen", "Ben", "Leo", "Milo", "Finn", "Eli", "Theo", "Noah"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]

TRAITS = ["gentle", "careful", "hopeful", "patient"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for starter_id, starter in STARTERS.items():
            for home_id, home in NEW_HOMES.items():
                for action_id, action in ACTIONS.items():
                    if root_risk(starter, 1) > 0 and can_help(starter, home, action):
                        combos.append((setting_id, starter_id, home_id, action_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    starter: str
    new_home: str
    action: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
    extra_water: int = 1
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    starter = f["starter_cfg"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "twosome" and "bean" and contains a gentle twist.',
        f"Tell a warm story where a child twosome, {c1.id} and {c2.id}, plant a bean in {starter.phrase}, think it is gone the next morning, and then discover a loving surprise.",
        "Write a short story with a worried middle and a comforting reveal, where a grown-up quietly helps a seed and the ending image shows what changed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1 = f["child1"]
    c2 = f["child2"]
    helper = f["helper"]
    starter = f["starter_cfg"]
    new_home = f["new_home_cfg"]
    action = f["action"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a twosome of children, {c1.id} and {c2.id}, and {helper.label_word} who quietly watched over their bean. The whole story grows out of how much all three cared for that little seed."
        ),
        (
            "Why did the children feel worried in the morning?",
            f"They hurried back to the {starter.label} and found it empty, so they thought their bean was gone. That empty starter made the loss feel sudden and real."
        ),
        (
            f"Why did {helper.label_word} move the bean?",
            f"{helper.label_word.capitalize()} saw that the {starter.label} was too soggy for a tiny bean. {helper.pronoun().capitalize()} moved it because better drainage and more room would help the roots stay safe."
        ),
        (
            "What was the twist in the story?",
            f"The twist was that the bean had not been lost at all. It had been quietly moved into {new_home.phrase} so it could grow better."
        ),
    ]
    if outcome == "sprouted":
        qa.append(
            (
                "What did the children discover when the grown-up showed them the new pot?",
                f"They found their bean alive in {new_home.phrase}, already lifting a small green sprout from the soil. The surprise turned their worry into relief because the empty cup had really been the sign of help, not loss."
            )
        )
    else:
        qa.append(
            (
                "How did the story still end hopefully?",
                f"The bean had been moved into a safer pot, even if it had not sprouted yet. The family ended by giving it sunshine, patience, and gentler care together."
            )
        )
    return qa


KNOWLEDGE = {
    "bean": [
        (
            "What does a bean seed need to grow?",
            "A bean seed needs soil, water, air, and light. Too little water can dry it out, but too much water can make it hard for the roots to breathe."
        )
    ],
    "roots": [
        (
            "Why do plant roots need space and air?",
            "Roots drink water and help hold a plant steady. They also need little spaces in the soil for air, so packed or soggy soil can make growing harder."
        )
    ],
    "drainage": [
        (
            "What does drainage mean for a plant pot?",
            "Drainage means extra water can leave the pot instead of staying trapped around the roots. Pots with drainage holes help soil stay damp without turning swampy."
        )
    ],
    "transplant": [
        (
            "What does it mean to transplant a seed or plant?",
            "To transplant means to move it from one place to another so it can grow better. People do that when a plant needs more space, better soil, or a sunnier spot."
        )
    ],
    "sunlight": [
        (
            "Why do many plants like a sunny window?",
            "Sunlight gives plants energy to grow. A bright window can help a small seedling start strong when the weather is gentle."
        )
    ],
}
KNOWLEDGE_ORDER = ["bean", "roots", "drainage", "transplant", "sunlight"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bean"} | set(world.facts["starter_cfg"].tags) | set(world.facts["new_home_cfg"].tags) | set(world.facts["action"].tags) | set(world.facts["setting"].tags)
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
        lines.append(f"  {e.id:9} ({e.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="windowsill",
        starter="teacup",
        new_home="blue_pot",
        action="transplant",
        child1="Lina",
        child1_gender="girl",
        child2="Owen",
        child2_gender="boy",
        helper="grandmother",
        extra_water=1,
    ),
    StoryParams(
        setting="porch",
        starter="jam_jar",
        new_home="window_box",
        action="rehome_gently",
        child1="Mia",
        child1_gender="girl",
        child2="Leo",
        child2_gender="boy",
        helper="grandfather",
        extra_water=1,
    ),
    StoryParams(
        setting="table",
        starter="paper_cup",
        new_home="clay_pot",
        action="transplant",
        child1="Ruby",
        child1_gender="girl",
        child2="Finn",
        child2_gender="boy",
        helper="mother",
        extra_water=1,
    ),
]


def explain_rejection(starter: Starter, new_home: NewHome, action: HelperAction) -> str:
    if root_risk(starter, 1) <= 0:
        return (
            f"(No story: {starter.phrase} is already roomy and drains well enough, so the bean does not honestly need a secret rescue. "
            f"Pick a riskier starter like a teacup, jam jar, or paper cup.)"
        )
    if action.sense < SENSE_MIN:
        return (
            f"(No story: the action '{action.id}' is too unhelpful for this heartwarming world. "
            f"Choose a caring action like transplant or rehome_gently.)"
        )
    if not (new_home.drainage > starter.drainage and new_home.room > starter.room):
        return (
            f"(No story: {new_home.phrase} is not clearly better than {starter.phrase}. "
            f"The twist only works if the bean is moved to a safer, roomier home.)"
        )
    return "(No story: this combination does not describe a sensible rescue.)"


def outcome_of(params: StoryParams) -> str:
    starter = STARTERS[params.starter]
    new_home = NEW_HOMES[params.new_home]
    action = ACTIONS[params.action]
    return "sprouted" if saved_bean(starter, new_home, action, params.extra_water) else "saved"


ASP_RULES = r"""
risky_starter(S) :- starter(S), starter_risk(S, R), R > 0.
better_home(S, H) :- starter(S), new_home(H), starter_drainage(S, SD), starter_room(S, SR),
                     home_drainage(H, HD), home_room(H, HR), HD > SD, HR > SR.
sensible_action(A) :- action(A), sense(A, S), sense_min(M), S >= M.

valid(Place, S, H, A) :- setting(Place), risky_starter(S), better_home(S, H), sensible_action(A).

rescue_strength(H, A, V) :- home_drainage(H, HD), home_room(H, HR), power(A, P), V = HD + HR + P.
saved(S, H, A, W) :- starter_risk(S, R0), extra_water(W), R = R0 + W, rescue_strength(H, A, V), V > R.
outcome(sprouted) :- chosen_starter(S), chosen_home(H), chosen_action(A), chosen_water(W), saved(S, H, A, W).
outcome(saved) :- chosen_starter(S), chosen_home(H), chosen_action(A), chosen_water(W), not saved(S, H, A, W).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for starter_id, starter in STARTERS.items():
        lines.append(asp.fact("starter", starter_id))
        lines.append(asp.fact("starter_drainage", starter_id, starter.drainage))
        lines.append(asp.fact("starter_room", starter_id, starter.room))
        lines.append(asp.fact("starter_risk", starter_id, max(0, (3 - starter.drainage) + (2 - starter.room))))
    for home_id, home in NEW_HOMES.items():
        lines.append(asp.fact("new_home", home_id))
        lines.append(asp.fact("home_drainage", home_id, home.drainage))
        lines.append(asp.fact("home_room", home_id, home.room))
    for action_id, action in ACTIONS.items():
        lines.append(asp.fact("action", action_id))
        lines.append(asp.fact("sense", action_id, action.sense))
        lines.append(asp.fact("power", action_id, action.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for water in [0, 1]:
        lines.append(asp.fact("extra_water", water))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_starter", params.starter),
            asp.fact("chosen_home", params.new_home),
            asp.fact("chosen_action", params.action),
            asp.fact("chosen_water", params.extra_water),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        _ = smoke.to_json()
        print("OK: smoke test passed for generate()/emit()/json.")
    except Exception as err:  # pragma: no cover - verify surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a twosome, a bean, and a heartwarming twist. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--starter", choices=STARTERS)
    ap.add_argument("--new-home", dest="new_home", choices=NEW_HOMES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--extra-water", dest="extra_water", type=int, choices=[0, 1])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.starter and args.new_home and args.action:
        starter = STARTERS[args.starter]
        home = NEW_HOMES[args.new_home]
        action = ACTIONS[args.action]
        if not can_help(starter, home, action) or root_risk(starter, 1) <= 0:
            raise StoryError(explain_rejection(starter, home, action))
    if args.starter and root_risk(STARTERS[args.starter], 1) <= 0:
        starter = STARTERS[args.starter]
        home = NEW_HOMES[args.new_home] if args.new_home else next(iter(NEW_HOMES.values()))
        action = ACTIONS[args.action] if args.action else next(iter(ACTIONS.values()))
        raise StoryError(explain_rejection(starter, home, action))
    if args.action and ACTIONS[args.action].sense < SENSE_MIN:
        starter = STARTERS[args.starter] if args.starter else next(iter(STARTERS.values()))
        home = NEW_HOMES[args.new_home] if args.new_home else next(iter(NEW_HOMES.values()))
        raise StoryError(explain_rejection(starter, home, ACTIONS[args.action]))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.starter is None or c[1] == args.starter)
        and (args.new_home is None or c[2] == args.new_home)
        and (args.action is None or c[3] == args.action)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, starter_id, home_id, action_id = rng.choice(sorted(combos))
    child1, g1 = _pick_name(rng)
    child2, g2 = _pick_name(rng, avoid=child1)
    helper = args.helper or rng.choice(HELPERS)
    extra_water = args.extra_water if args.extra_water is not None else 1

    return StoryParams(
        setting=setting_id,
        starter=starter_id,
        new_home=home_id,
        action=action_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        helper=helper,
        extra_water=extra_water,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.starter not in STARTERS:
        raise StoryError(f"(Unknown starter: {params.starter})")
    if params.new_home not in NEW_HOMES:
        raise StoryError(f"(Unknown new home: {params.new_home})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    starter = STARTERS[params.starter]
    home = NEW_HOMES[params.new_home]
    action = ACTIONS[params.action]
    if root_risk(starter, 1) <= 0 or not can_help(starter, home, action):
        raise StoryError(explain_rejection(starter, home, action))

    world = tell(
        setting=SETTINGS[params.setting],
        starter_cfg=starter,
        new_home_cfg=home,
        action_cfg=action,
        child1_name=params.child1,
        child1_type=params.child1_gender,
        child2_name=params.child2,
        child2_type=params.child2_gender,
        helper_type=params.helper,
        extra_water=params.extra_water,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, starter, new_home, action) combos:\n")
        for setting_id, starter_id, home_id, action_id in combos:
            print(f"  {setting_id:10} {starter_id:11} {home_id:10} {action_id}")
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
            header = f"### {p.child1} & {p.child2}: {p.starter} -> {p.new_home} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
