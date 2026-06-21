#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py
=======================================================================

A standalone storyworld about a curious child on a little quest for a tinkling
treasure set too high to reach. The child is tempted to climb a wobbly thing,
but a wiser helper imagines the trouble ahead and offers an alternative. In the
happy endings, a grown-up and a steady tool solve the problem; in the sadder
ending, the treasure cracks before the safer plan can arrive.

The prose keeps a nursery-rhyme flavor: concrete, lilting, and child-facing.

Run it
------
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --treasure bell
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --support trunk
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --trace --seed 99
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --json
    python storyworlds/worlds/gpt-5.4/alternative_curiosity_quest_nursery_rhyme.py --verify
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
CHILD_REACH = 2
WISE_TRAITS = {"careful", "patient", "steady", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    height: int = 0
    fragile: bool = False
    steady: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mouse", "sparrow", "cat", "duck"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str
    opening: str
    ending: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    sound: str
    glow: str
    perch: str
    goal: str
    height: int
    fragile: bool
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
class Support:
    id: str
    label: str
    phrase: str
    height: int
    wobble: int
    sense: int
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
class Alternative:
    id: str
    label: str
    phrase: str
    reach: int
    power: int
    sense: int
    text: str
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


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    support = world.get("support")
    if child.meters["on_support"] < THRESHOLD:
        return []
    if support.meters["wobbling"] >= THRESHOLD:
        return []
    if support.attrs.get("wobble_score", 0) <= 0:
        return []
    support.meters["wobbling"] += 1
    child.memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    return ["__wobble__"]


def _r_reach_risk(world: World) -> list[str]:
    child = world.get("child")
    treasure = world.get("treasure")
    support = world.get("support")
    if child.meters["reaching"] < THRESHOLD:
        return []
    if support.meters["wobbling"] < THRESHOLD:
        return []
    sig = ("reach_risk", treasure.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treasure.meters["risk"] += 1
    if treasure.fragile:
        treasure.meters["risk"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="reach_risk", tag="physical", apply=_r_reach_risk),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            res = rule.apply(world)
            if res:
                changed = True
                produced.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def can_reach_with_support(treasure: Treasure, support: Support) -> bool:
    return CHILD_REACH + support.height >= treasure.height


def hazard_at_risk(treasure: Treasure, support: Support) -> bool:
    return can_reach_with_support(treasure, support) and support.wobble >= 1 and support.sense < SENSE_MIN


def sensible_alternatives() -> list[Alternative]:
    return [a for a in ALTERNATIVES.values() if a.sense >= SENSE_MIN]


def best_alternative() -> Alternative:
    return max(ALTERNATIVES.values(), key=lambda a: (a.sense, a.power, a.reach))


def can_fix(treasure: Treasure, alt: Alternative) -> bool:
    return alt.reach >= treasure.height and alt.sense >= SENSE_MIN


def danger_level(treasure: Treasure, support: Support, delay: int) -> int:
    return support.wobble + (1 if treasure.fragile else 0) + delay


def is_contained(treasure: Treasure, support: Support, alt: Alternative, delay: int) -> bool:
    return can_fix(treasure, alt) and alt.power >= danger_level(treasure, support, delay)


def would_pause(trait: str, trust: int) -> bool:
    return trait in WISE_TRAITS and trust >= 7


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("child").meters["on_support"] += 1
    sim.get("child").meters["reaching"] += 1
    propagate(sim, narrate=False)
    treasure = sim.get("treasure")
    return {
        "wobble": sim.get("support").meters["wobbling"] >= THRESHOLD,
        "risk": treasure.meters["risk"],
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, child: Entity, helper: Entity, setting: Setting, treasure: Treasure) -> None:
    child.memes["curiosity"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In {setting.place}, where small feet patter and kettle-sparrows sing, "
        f"lived {child.id}. {setting.opening}"
    )
    world.say(
        f"Near {treasure.perch} rested {treasure.phrase}, and it gave {treasure.sound} "
        f"with a little {treasure.glow}."
    )
    world.say(
        f"{child.id} tipped {child.pronoun('possessive')} head and whispered, "
        f'"What a wonder! I must begin a quest to {treasure.goal}."'
    )
    helper_name = helper.id if helper.kind == "character" else helper.label
    world.say(
        f"{helper_name.capitalize()} watched from nearby, for curiosity had come "
        f"dancing into the room."
    )


def tempt(world: World, child: Entity, support: Support) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f'"I know a quick way," said {child.id}. "I can climb {support.phrase}."'
    )
    world.say(
        f"{support.phrase.capitalize()} stood close by, but it had a light, fidgety look."
    )


def warn(world: World, helper: Entity, child: Entity, treasure: Treasure, support: Support, alt: Alternative) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_risk"] = pred["risk"]
    who = helper.id if helper.kind == "character" else helper.label.capitalize()
    extra = " It might wobble and make the treasure tumble." if pred["risk"] >= 1 else ""
    world.say(
        f'{who} said, "Hush a tick, dear {child.id}. {support.label.capitalize()} is wobbly, '
        f'and {treasure.label} is high.{extra} Let us choose an alternative."'
    )
    world.say(
        f'"We can use {alt.phrase} and ask a grown-up to help," {who.lower()} added.'
    )


def back_down(world: World, child: Entity, helper: Entity, alt: Alternative, grownup: Entity, treasure: Treasure, setting: Setting) -> None:
    child.memes["relief"] += 1
    child.memes["patience"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{child.id} looked at {support_name(world)} once, then drew back {child.pronoun('possessive')} foot."
    )
    world.say(
        f'"A quick way is not always the kind way," said {child.id}. "Let us try the alternative."'
    )
    world.para()
    safe_retrieve(world, grownup, alt, treasure)
    world.say(
        f"Soon the quest was done, and in {setting.ending}, {child.id} held {treasure.label} "
        f"without a bump or crack."
    )


def climb(world: World, child: Entity, support: Support) -> None:
    child.meters["on_support"] += 1
    child.meters["reaching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Up {support.phrase} climbed {child.id}, step by little step, reaching for the prize."
    )
    if world.get("support").meters["wobbling"] >= THRESHOLD:
        world.say(
            f"But wobble went {support.label}, bobble went {child.id}, and the room forgot its easy song."
        )


def scare(world: World, child: Entity, treasure: Treasure) -> None:
    if world.get("support").meters["wobbling"] >= THRESHOLD:
        world.say(
            f"{treasure.label.capitalize()} gave {treasure.sound} again, only now it sounded thin and frightened."
        )
        child.memes["fear"] += 1


def rescue(world: World, grownup: Entity, alt: Alternative, treasure: Treasure) -> None:
    world.get("support").meters["wobbling"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.get("child").meters["on_support"] = 0.0
    world.get("child").meters["reaching"] = 0.0
    safe_retrieve(world, grownup, alt, treasure)
    world.say(
        f"{grownup.label_word.capitalize()} set the safer plan in place, and the rattly moment settled down."
    )


def safe_retrieve(world: World, grownup: Entity, alt: Alternative, treasure: Treasure) -> None:
    treasure.meters["held"] += 1
    treasure.meters["risk"] = 0.0
    world.say(
        f"{grownup.label_word.capitalize()} {alt.text.replace('{treasure}', treasure.label)}."
    )


def break_treasure(world: World, child: Entity, treasure: Treasure, grownup: Entity) -> None:
    treasure.meters["broken"] += 1
    world.get("child").meters["on_support"] = 0.0
    world.get("child").meters["reaching"] = 0.0
    child.meters["bump"] += 1
    child.memes["sadness"] += 1
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"Then slip went a shoe, tip went the treasure, and down it came with a sorry little crack."
    )
    world.say(
        f"{grownup.label_word.capitalize()} hurried in and lifted {child.id} close. "
        f"{child.id} was safe, with only a small bump, but the quest had turned sad."
    )


def lesson_happy(world: World, grownup: Entity, child: Entity, helper: Entity, alt: Alternative) -> None:
    child.memes["lesson"] += 1
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f'"When wonder calls," said {grownup.label_word}, "we need not rush. '
        f'A steady hand and an alternative can carry a quest safely home."'
    )
    world.say(
        f"{child.id} nodded, and even the room seemed to nod along."
    )


def lesson_sad(world: World, grownup: Entity, child: Entity, alt: Alternative) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f'"Curiosity is bright," said {grownup.label_word} softly, "but bright things still need careful feet. '
        f'Next time we will choose {alt.phrase} first."'
    )
    world.say(
        f"{child.id} touched the little bump, looked at the cracked treasure, and understood."
    )


def ending_image(world: World, child: Entity, helper: Entity, treasure: Treasure, setting: Setting, outcome: str) -> None:
    helper_name = helper.id if helper.kind == "character" else helper.label
    if outcome in {"averted", "contained"}:
        world.say(
            f"Before long, {child.id} and {helper_name} were singing in {setting.ending}, "
            f"and {treasure.label} answered with a merry sound."
        )
    else:
        world.say(
            f"That evening, the crack in {treasure.label} stayed as quiet as a lesson, "
            f"while {child.id} sat close in {setting.place} and listened instead of climbing."
        )


def support_name(world: World) -> str:
    return world.get("support").label


def tell(
    setting: Setting,
    treasure_cfg: Treasure,
    support_cfg: Support,
    alt_cfg: Alternative,
    *,
    child_name: str = "Merry",
    child_gender: str = "girl",
    helper_name: str = "Pip",
    helper_type: str = "mouse",
    grownup_type: str = "grandmother",
    helper_trait: str = "careful",
    trust: int = 7,
    delay: int = 0,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["curious"],
        attrs={},
    ))
    helper_kind = "character" if helper_type in {"girl", "boy"} else "thing"
    helper = world.add(Entity(
        id=helper_name,
        kind=helper_kind,
        type=helper_type,
        label=helper_name.lower() if helper_kind == "thing" else helper_name,
        role="helper",
        traits=[helper_trait],
        attrs={},
    ))
    grownup = world.add(Entity(
        id="Grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        role="grownup",
        traits=["calm"],
        attrs={},
    ))
    world.add(Entity(id="room", type="room", label="the room", attrs={}))
    treasure = world.add(Entity(
        id="treasure",
        type="treasure",
        label=treasure_cfg.label,
        fragile=treasure_cfg.fragile,
        height=treasure_cfg.height,
        attrs={},
    ))
    support = world.add(Entity(
        id="support",
        type="support",
        label=support_cfg.label,
        height=support_cfg.height,
        attrs={"wobble_score": support_cfg.wobble},
    ))
    alt = world.add(Entity(
        id="alternative",
        type="tool",
        label=alt_cfg.label,
        steady=True,
        height=alt_cfg.reach,
        attrs={},
    ))

    child.memes["trust"] = float(trust)
    child.memes["curiosity"] = 0.0
    child.memes["fear"] = 0.0
    child.memes["lesson"] = 0.0
    child.meters["on_support"] = 0.0
    child.meters["reaching"] = 0.0
    child.meters["bump"] = 0.0
    treasure.meters["risk"] = 0.0
    treasure.meters["held"] = 0.0
    treasure.meters["broken"] = 0.0
    support.meters["wobbling"] = 0.0
    world.get("room").meters["danger"] = 0.0

    introduce(world, child, helper, setting, treasure_cfg)
    world.para()
    tempt(world, child, support_cfg)
    warn(world, helper, child, treasure_cfg, support_cfg, alt_cfg)

    averted = would_pause(helper_trait, trust)
    if averted:
        back_down(world, child, helper, alt_cfg, grownup, treasure_cfg, setting)
        lesson_happy(world, grownup, child, helper, alt_cfg)
        outcome = "averted"
    else:
        world.para()
        climb(world, child, support_cfg)
        scare(world, child, treasure_cfg)
        contained = is_contained(treasure_cfg, support_cfg, alt_cfg, delay)
        world.para()
        if contained:
            rescue(world, grownup, alt_cfg, treasure_cfg)
            lesson_happy(world, grownup, child, helper, alt_cfg)
            outcome = "contained"
        else:
            break_treasure(world, child, treasure_cfg, grownup)
            lesson_sad(world, grownup, child, alt_cfg)
            outcome = "broken"

    world.para()
    ending_image(world, child, helper, treasure_cfg, setting, outcome)
    world.facts.update(
        setting=setting,
        treasure_cfg=treasure_cfg,
        support_cfg=support_cfg,
        alt_cfg=alt_cfg,
        child=child,
        helper=helper,
        grownup=grownup,
        outcome=outcome,
        trust=trust,
        delay=delay,
        helper_trait=helper_trait,
        predicted_danger=world.facts.get("predicted_danger", 0),
        predicted_risk=world.facts.get("predicted_risk", 0),
        broken=treasure.meters["broken"] >= THRESHOLD,
        bumped=child.meters["bump"] >= THRESHOLD,
        held=treasure.meters["held"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a clover-bright cottage",
        opening="By the window hung a strip of blue ribbon, and the floorboards hummed a sleepy tune.",
        ending="the warm kitchen light",
        tags={"home"},
    ),
    "bakery": Setting(
        id="bakery",
        place="a flour-soft bakery",
        opening="Round buns cooled on trays, and the air smelled of butter and rhyme.",
        ending="the sugared doorway",
        tags={"bakery"},
    ),
    "mill": Setting(
        id="mill",
        place="a round old mill",
        opening="The great wheel outside whispered hup and hush, hup and hush.",
        ending="the turning doorway",
        tags={"mill"},
    ),
}

TREASURES = {
    "bell": Treasure(
        id="bell",
        label="bell",
        phrase="a silver bell",
        sound="ting-ting",
        glow="wink",
        perch="the highest shelf",
        goal="hear its song up close",
        height=5,
        fragile=False,
        tags={"bell", "sound"},
    ),
    "music_box": Treasure(
        id="music_box",
        label="music box",
        phrase="a painted music box",
        sound="plink-plink",
        glow="gleam",
        perch="the top cupboard",
        goal="see the dancers spin inside",
        height=6,
        fragile=True,
        tags={"music_box", "sound"},
    ),
    "star_jar": Treasure(
        id="star_jar",
        label="star jar",
        phrase="a glass star jar",
        sound="clink-clink",
        glow="twinkle",
        perch="the moon-high mantel",
        goal="count the shiny beads within",
        height=6,
        fragile=True,
        tags={"jar", "glass"},
    ),
}

SUPPORTS = {
    "stool": Support(
        id="stool",
        label="stool",
        phrase="the old three-legged stool",
        height=3,
        wobble=2,
        sense=1,
        tags={"stool", "wobble"},
    ),
    "trunk": Support(
        id="trunk",
        label="trunk",
        phrase="the round toy trunk",
        height=3,
        wobble=2,
        sense=1,
        tags={"trunk", "wobble"},
    ),
    "crate": Support(
        id="crate",
        label="crate",
        phrase="the upside-down apple crate",
        height=4,
        wobble=3,
        sense=1,
        tags={"crate", "wobble"},
    ),
    "rug": Support(
        id="rug",
        label="rug roll",
        phrase="the rolled-up rug",
        height=1,
        wobble=1,
        sense=0,
        tags={"rug", "wobble"},
    ),
}

ALTERNATIVES = {
    "ladder": Alternative(
        id="ladder",
        label="ladder",
        phrase="the little ladder",
        reach=6,
        power=4,
        sense=3,
        text="brought the little ladder, held it steady, and lifted down the {treasure}",
        qa_text="used the little ladder and held it steady to bring the treasure down",
        tags={"ladder", "alternative"},
    ),
    "hook": Alternative(
        id="hook",
        label="hook stick",
        phrase="the hook stick",
        reach=5,
        power=3,
        sense=2,
        text="took the hook stick, drew the {treasure} gently close, and set it in waiting hands",
        qa_text="used the hook stick to draw the treasure down gently",
        tags={"hook", "alternative"},
    ),
    "tongs": Alternative(
        id="tongs",
        label="long tongs",
        phrase="the long tongs",
        reach=4,
        power=2,
        sense=2,
        text="reached with the long tongs, but they were best for nearer things and not for this task",
        qa_text="tried the long tongs",
        tags={"tongs", "alternative"},
    ),
}

GIRL_NAMES = ["Merry", "Daisy", "Wren", "Nell", "Mabel", "Posy", "Lark", "Tansy"]
BOY_NAMES = ["Robin", "Toby", "Ned", "Pippin", "Jory", "Bram", "Kit", "Ollie"]
HELPER_NAMES = ["Pip", "Moss", "Tuppy", "Dot", "Nib", "Spar"]
HELPER_TYPES = ["mouse", "sparrow", "duck", "girl", "boy"]
TRAITS = ["careful", "patient", "steady", "thoughtful", "curious", "hasty"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting in SETTINGS:
        for tid, treasure in TREASURES.items():
            for sid, support in SUPPORTS.items():
                if not hazard_at_risk(treasure, support):
                    continue
                for aid, alt in ALTERNATIVES.items():
                    if can_fix(treasure, alt):
                        combos.append((setting, tid, sid, aid))
    return combos


@dataclass
class StoryParams:
    setting: str
    treasure: str
    support: str
    alternative: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    grownup: str
    helper_trait: str
    trust: int = 7
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
    "bell": [(
        "What does a bell do?",
        "A bell rings when it is moved, and the metal makes a clear sound. Small bells can sound bright and cheerful."
    )],
    "music_box": [(
        "What is a music box?",
        "A music box is a little box that plays a tune when it is wound or opened. Some are delicate, so they should be handled carefully."
    )],
    "jar": [(
        "Why can a glass jar break?",
        "Glass is hard but brittle, so if it falls it can crack or shatter. That is why glass things need careful hands and safe places."
    )],
    "ladder": [(
        "Why is a ladder safer than standing on a wobbly thing?",
        "A proper ladder is made for climbing, and a grown-up can hold it steady. That makes your feet less likely to slip or wobble."
    )],
    "hook": [(
        "What is a hook stick for?",
        "A hook stick helps pull something a little closer without climbing up high. It can be useful when a grown-up uses it carefully."
    )],
    "alternative": [(
        "What is an alternative?",
        "An alternative is another way to do something. A safer alternative can solve the same problem without as much risk."
    )],
    "wobble": [(
        "What does wobbly mean?",
        "Wobbly means something does not stay still and steady. If you stand on a wobbly thing, it can tip or shake."
    )],
    "sound": [(
        "Why are children curious about little sounds?",
        "Small sounds can make people wonder what is making them. Curiosity is the feeling that makes you want to look and learn."
    )],
}
KNOWLEDGE_ORDER = ["alternative", "sound", "bell", "music_box", "jar", "wobble", "ladder", "hook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    treasure = f["treasure_cfg"]
    alt = f["alt_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old about curiosity and a quest. '
        f'Include the word "alternative" and make the sought object a {treasure.label}.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a lilting story where {child.id} wants to climb for a {treasure.label}, but listens to a warning and chooses the alternative instead.",
            f"Write a gentle quest tale where wonder stays bright, no one gets hurt, and the safer plan brings the {treasure.label} down at the end.",
        ]
    if outcome == "contained":
        return [
            base,
            f"Tell a nursery-rhyme tale where {child.id} tries the quick way, something wobbles, and a grown-up uses {alt.phrase} to set things right.",
            f"Write a story with a small scare, a safe rescue, and an ending image that shows the child has learned to choose a steadier way.",
        ]
    return [
        base,
        f"Tell a cautionary nursery-rhyme story where {child.id}'s curiosity leads to a wobble and the treasure cracks before the alternative can help.",
        f"Write a sad-but-gentle quest story where the child is safe, the object is broken, and the lesson is to pick the safer plan first.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    grownup = f["grownup"]
    treasure = f["treasure_cfg"]
    support = f["support_cfg"]
    alt = f["alt_cfg"]
    helper_name = helper.id if helper.kind == "character" else helper.label
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who was full of curiosity, and {helper_name}, who watched the quest begin. They were joined by {grownup.label_word}, who helped when the high prize became a problem."
        ),
        (
            f"What did {child.id} want?",
            f"{child.id} wanted to {treasure.goal} by getting close to the {treasure.label}. The little sound from high up is what turned wonder into a quest."
        ),
        (
            f"Why did {helper_name} warn {child.id}?",
            f"{helper_name.capitalize()} warned {child.id} because {support.label} was wobbly and the {treasure.label} was high. In the world of the story, that quick plan could make the treasure tumble and turn curiosity into trouble."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append((
            f"What was the alternative?",
            f"The alternative was to use {alt.phrase} with {grownup.label_word}'s help. That solved the same problem without climbing on the wobbly {support.label}."
        ))
        qa.append((
            f"How did the story end?",
            f"It ended safely, with {child.id} holding the {treasure.label} and no one getting hurt. The ending proves that {child.id} learned a quest can stay merry when it uses a steadier plan."
        ))
    elif outcome == "contained":
        qa.append((
            f"What happened when {child.id} climbed?",
            f"The {support.label} began to wobble, and the room suddenly felt risky. That wobble is why the grown-up had to step in with the safer plan."
        ))
        qa.append((
            f"How did {grownup.label_word} help?",
            f"{grownup.label_word.capitalize()} {alt.qa_text}. Because the safer tool was steady enough, the treasure was saved before it could break."
        ))
        qa.append((
            f"What did {child.id} learn?",
            f"{child.id} learned that a quick way is not always the best way. The small scare taught {child.pronoun('object')} to choose the alternative before trouble grows."
        ))
    else:
        qa.append((
            f"Why did the treasure break?",
            f"It broke because {child.id} climbed the wobbly {support.label} and the moment tipped the wrong way. The alternative came too late, so the treasure fell before the safer method could rescue it."
        ))
        qa.append((
            f"Was {child.id} badly hurt?",
            f"No. {child.id} was safe and had only a small bump. The sadness of the ending comes from the cracked treasure and the lesson, not from a serious injury."
        ))
        qa.append((
            "What changed by the end?",
            f"By the end, {child.id} still had curiosity, but it had become more careful curiosity. The crack in the {treasure.label} showed why a safer alternative matters."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["treasure_cfg"].tags) | set(f["support_cfg"].tags) | set(f["alt_cfg"].tags)
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
        if e.height:
            bits.append(f"height={e.height}")
        if e.fragile:
            bits.append("fragile=True")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="cottage",
        treasure="bell",
        support="stool",
        alternative="hook",
        child_name="Merry",
        child_gender="girl",
        helper_name="Pip",
        helper_type="mouse",
        grownup="grandmother",
        helper_trait="careful",
        trust=8,
        delay=0,
    ),
    StoryParams(
        setting="bakery",
        treasure="music_box",
        support="crate",
        alternative="ladder",
        child_name="Robin",
        child_gender="boy",
        helper_name="Dot",
        helper_type="sparrow",
        grownup="father",
        helper_trait="curious",
        trust=4,
        delay=0,
    ),
    StoryParams(
        setting="mill",
        treasure="star_jar",
        support="crate",
        alternative="ladder",
        child_name="Nell",
        child_gender="girl",
        helper_name="Moss",
        helper_type="boy",
        grownup="grandfather",
        helper_trait="patient",
        trust=3,
        delay=2,
    ),
    StoryParams(
        setting="cottage",
        treasure="music_box",
        support="trunk",
        alternative="ladder",
        child_name="Toby",
        child_gender="boy",
        helper_name="Nib",
        helper_type="duck",
        grownup="mother",
        helper_trait="thoughtful",
        trust=7,
        delay=0,
    ),
]


def explain_rejection(treasure: Treasure, support: Support, alt: Optional[Alternative] = None) -> str:
    if not can_reach_with_support(treasure, support):
        return (
            f"(No story: {support.phrase} is too low to tempt a real climb toward the {treasure.label}. "
            f"A quest needs a risky near-solution, not something that obviously cannot reach.)"
        )
    if support.sense >= SENSE_MIN or support.wobble < 1:
        return (
            f"(No story: {support.label} is not an unwise, wobbly choice here, so the cautionary turn has no honest footing.)"
        )
    if alt is not None and not can_fix(treasure, alt):
        return (
            f"(No story: {alt.phrase} cannot safely reach the {treasure.label}. "
            f"The alternative must truly solve the problem.)"
        )
    return "(No story: this combination does not create a clear risky plan and safe alternative.)"


def explain_alternative(aid: str) -> str:
    alt = ALTERNATIVES[aid]
    better = ", ".join(sorted(a.id for a in sensible_alternatives()))
    return (
        f"(Refusing alternative '{aid}': it is known to the world but not sensible enough for this quest "
        f"(sense={alt.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_pause(params.helper_trait, params.trust):
        return "averted"
    treasure = TREASURES[params.treasure]
    support = SUPPORTS[params.support]
    alt = ALTERNATIVES[params.alternative]
    return "contained" if is_contained(treasure, support, alt, params.delay) else "broken"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
reachable_by_support(T, S) :- treasure(T), support(S), treasure_height(T, Ht), support_height(S, Hs), child_reach(CR), Hs + CR >= Ht.
hazard(T, S) :- reachable_by_support(T, S), wobble(S, W), W >= 1, support_sense(S, SS), sense_min(M), SS < M.
sensible_alt(A) :- alternative(A), alt_sense(A, S), sense_min(M), S >= M.
fixes(T, A) :- treasure(T), alternative(A), treasure_height(T, Ht), alt_reach(A, Ar), Ar >= Ht, sensible_alt(A).
valid(Set, T, S, A) :- setting(Set), hazard(T, S), fixes(T, A).

% --- outcome model ---------------------------------------------------------
wise_trait(T) :- trait(T), is_wise(T).
averted :- wise_trait(T), trust(V), V >= 7.
danger(W + F + D) :- chosen_support(S), wobble(S, W), chosen_treasure(T), fragile_bonus(T, F), delay(D).
contained :- chosen_treasure(T), chosen_alt(A), fixes(T, A), alt_power(A, P), danger(DG), P >= DG.
outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_height", tid, t.height))
        lines.append(asp.fact("fragile_bonus", tid, 1 if t.fragile else 0))
    for sid, s in SUPPORTS.items():
        lines.append(asp.fact("support", sid))
        lines.append(asp.fact("support_height", sid, s.height))
        lines.append(asp.fact("wobble", sid, s.wobble))
        lines.append(asp.fact("support_sense", sid, s.sense))
    for aid, a in ALTERNATIVES.items():
        lines.append(asp.fact("alternative", aid))
        lines.append(asp.fact("alt_reach", aid, a.reach))
        lines.append(asp.fact("alt_power", aid, a.power))
        lines.append(asp.fact("alt_sense", aid, a.sense))
    lines.append(asp.fact("child_reach", CHILD_REACH))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(WISE_TRAITS):
        lines.append(asp.fact("is_wise", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_alternatives() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_alt/1."))
    return sorted(a for (a,) in asp.atoms(model, "sensible_alt"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_treasure", params.treasure),
        asp.fact("chosen_support", params.support),
        asp.fact("chosen_alt", params.alternative),
        asp.fact("trait", params.helper_trait),
        asp.fact("trust", params.trust),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    csens = set(asp_sensible_alternatives())
    psens = {a.id for a in sensible_alternatives()}
    if csens == psens:
        print(f"OK: sensible alternatives match ({sorted(csens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible alternatives: clingo={sorted(csens)} python={sorted(psens)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            args = parser.parse_args([])
            p = resolve_params(args, random.Random(s))
            cases.append(p)
        except StoryError:
            continue
    mismatches = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced empty story")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: curiosity, a high treasure, and a safer alternative."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--alternative", choices=ALTERNATIVES)
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def _pick_helper(rng: random.Random) -> tuple[str, str]:
    htype = rng.choice(HELPER_TYPES)
    if htype == "girl":
        return rng.choice(GIRL_NAMES), htype
    if htype == "boy":
        return rng.choice(BOY_NAMES), htype
    return rng.choice(HELPER_NAMES), htype


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.support and args.treasure:
        treasure = TREASURES[args.treasure]
        support = SUPPORTS[args.support]
        alt = ALTERNATIVES[args.alternative] if args.alternative else None
        if not hazard_at_risk(treasure, support):
            raise StoryError(explain_rejection(treasure, support, alt))
    if args.alternative:
        alt = ALTERNATIVES[args.alternative]
        if alt.sense < SENSE_MIN:
            raise StoryError(explain_alternative(args.alternative))
        if args.treasure and not can_fix(TREASURES[args.treasure], alt):
            raise StoryError(explain_rejection(TREASURES[args.treasure], SUPPORTS[args.support] if args.support else next(iter(SUPPORTS.values())), alt))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.treasure is None or c[1] == args.treasure)
        and (args.support is None or c[2] == args.support)
        and (args.alternative is None or c[3] == args.alternative)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, treasure, support, alternative = rng.choice(sorted(combos))
    child_name, child_gender = _pick_child(rng)
    helper_name, helper_type = _pick_helper(rng)
    if helper_name == child_name and helper_type in {"girl", "boy"}:
        helper_name = rng.choice([n for n in (GIRL_NAMES if helper_type == "girl" else BOY_NAMES) if n != child_name])
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    helper_trait = rng.choice(TRAITS)
    trust = rng.randint(3, 9)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting,
        treasure=treasure,
        support=support,
        alternative=alternative,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        grownup=grownup,
        helper_trait=helper_trait,
        trust=trust,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        treasure = TREASURES[params.treasure]
        support = SUPPORTS[params.support]
        alternative = ALTERNATIVES[params.alternative]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]!r})") from None

    if not hazard_at_risk(treasure, support):
        raise StoryError(explain_rejection(treasure, support, alternative))
    if alternative.sense < SENSE_MIN or not can_fix(treasure, alternative):
        raise StoryError(explain_rejection(treasure, support, alternative))

    world = tell(
        setting=setting,
        treasure_cfg=treasure,
        support_cfg=support,
        alt_cfg=alternative,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        grownup_type=params.grownup,
        helper_trait=params.helper_trait,
        trust=params.trust,
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
        print(asp_program("", "#show valid/4.\n#show sensible_alt/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible alternatives: {', '.join(asp_sensible_alternatives())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, treasure, support, alternative) combos:\n")
        for setting, treasure, support, alt in combos:
            print(f"  {setting:8} {treasure:10} {support:8} {alt}")
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
            header = (
                f"### {p.child_name}: {p.treasure} in {p.setting} "
                f"({p.support} -> {p.alternative}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
