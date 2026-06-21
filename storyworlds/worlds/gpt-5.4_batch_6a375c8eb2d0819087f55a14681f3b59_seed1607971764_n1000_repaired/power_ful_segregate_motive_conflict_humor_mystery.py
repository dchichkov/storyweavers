#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py
================================================================================

A standalone storyworld for a small fable domain:
a proud leader uses a weak guess to segregate the town after something goes
missing, a funny helper follows clues, and the true motive turns out to be more
human than the accusation. The conflict is repaired when the mystery is solved
from world state rather than from a frozen template.

Run it
------
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py --accused-group winged
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py --culprit crow --motive hungry_family
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py --all
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/power_ful_segregate_motive_conflict_humor_mystery.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"hen", "goose", "sheep", "girl", "woman"}
        male = {"lion", "ram", "crow", "fox", "boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Leader:
    id: str
    type: str
    title: str
    style: str
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
class Helper:
    id: str
    type: str
    clue_skill: str
    comic_habit: str
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
class CulpritCfg:
    id: str
    type: str
    group: str
    manner: str
    can_take: set[str] = field(default_factory=set)
    can_motive: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    clue: str
    evidence: str
    use_tags: set[str] = field(default_factory=set)
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
class Motive:
    id: str
    need: str
    because: str
    confession: str
    repair: str
    ending: str
    requires: set[str] = field(default_factory=set)
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
class GroupRule:
    id: str
    label: str
    sign_text: str
    crowd_name: str
    members_phrase: str
    opposite_phrase: str
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


def _r_segregation_stings(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("segregated"):
        return out
    accused = world.get("accused_group")
    other = world.get("other_group")
    for ent in (accused, other):
        sig = ("stung", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["hurt"] += 1
        ent.memes["cross"] += 1
    helper = world.get("helper")
    helper.memes["curiosity"] += 1
    out.append("__segregated__")
    return out


def _r_clue_changes_suspicion(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_found") and not world.facts.get("mystery_solved"):
        helper = world.get("helper")
        culprit = world.get("culprit")
        sig = ("suspect", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["certainty"] += 1
            culprit.memes["worry"] += 1
            out.append("__suspect__")
    return out


def _r_truth_softens_crowd(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("mystery_solved"):
        return out
    leader = world.get("leader")
    accused = world.get("accused_group")
    other = world.get("other_group")
    culprit = world.get("culprit")
    sig = ("truth", culprit.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.memes["shame"] += 1
    leader.memes["pride"] = 0.0
    accused.memes["relief"] += 1
    accused.memes["cross"] = 0.0
    other.memes["relief"] += 1
    culprit.memes["relief"] += 1
    out.append("__truth__")
    return out


def _r_repair_restores(world: World) -> list[str]:
    out: list[str] = []
    if not world.facts.get("repair_done"):
        return out
    accused = world.get("accused_group")
    other = world.get("other_group")
    for ent in (accused, other):
        sig = ("restored", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["friendship"] += 1
        ent.memes["hurt"] = 0.0
    out.append("__repaired__")
    return out


CAUSAL_RULES = [
    Rule(name="segregation_stings", tag="social", apply=_r_segregation_stings),
    Rule(name="clue_changes_suspicion", tag="mystery", apply=_r_clue_changes_suspicion),
    Rule(name="truth_softens_crowd", tag="social", apply=_r_truth_softens_crowd),
    Rule(name="repair_restores", tag="social", apply=_r_repair_restores),
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


LEADERS = {
    "lion": Leader(
        id="lion",
        type="lion",
        title="Mayor Lion",
        style="liked to stand on an apple crate and speak as if every whisker were a trumpet",
        tags={"leader", "power"},
    ),
    "ram": Leader(
        id="ram",
        type="ram",
        title="Bailiff Ram",
        style="kept his bell polished and his rules even more polished",
        tags={"leader", "power"},
    ),
    "peacock": Leader(
        id="peacock",
        type="peacock",
        title="Steward Peacock",
        style="spread his tail whenever he wanted his ideas to look bigger than they were",
        tags={"leader", "power"},
    ),
}

HELPERS = {
    "goose": Helper(
        id="goose",
        type="goose",
        clue_skill="noticed tiny messes that everyone else stepped over",
        comic_habit="kept asking solemn questions while crumbs stuck to her beak",
        tags={"helper", "humor"},
    ),
    "tortoise": Helper(
        id="tortoise",
        type="tortoise",
        clue_skill="studied the ground so patiently that footprints seemed to tell him their secrets",
        comic_habit="cleared his throat before every clever thought as if it were a speech",
        tags={"helper", "mystery"},
    ),
    "mouse": Helper(
        id="mouse",
        type="mouse",
        clue_skill="slipped into corners where clues hid from bigger eyes",
        comic_habit="stood on a spoon to look taller when making a point",
        tags={"helper", "humor", "mystery"},
    ),
}

CULPRITS = {
    "crow": CulpritCfg(
        id="crow",
        type="crow",
        group="winged",
        manner="quick and bright-eyed",
        can_take={"figs", "reeds", "bell"},
        can_motive={"hungry_family", "patch_nest", "make_gift"},
        tags={"crow", "winged"},
    ),
    "squirrel": CulpritCfg(
        id="squirrel",
        type="squirrel",
        group="whiskered",
        manner="busy as a broom in a windstorm",
        can_take={"figs", "reeds", "ribbon"},
        can_motive={"hungry_family", "patch_nest", "make_gift"},
        tags={"squirrel", "whiskered"},
    ),
    "goat": CulpritCfg(
        id="goat",
        type="goat",
        group="horned",
        manner="gentle but forever nibbling at the edge of some plan",
        can_take={"figs", "reeds", "ribbon"},
        can_motive={"hungry_family", "patch_nest"},
        tags={"goat", "horned"},
    ),
}

ITEMS = {
    "figs": MissingItem(
        id="figs",
        label="figs",
        phrase="a basket of purple figs",
        clue="purple juice dotted the cobbles in polite little blots",
        evidence="a purple stain",
        use_tags={"food"},
        tags={"food", "figs"},
    ),
    "reeds": MissingItem(
        id="reeds",
        label="reeds",
        phrase="a bundle of long river reeds",
        clue="a green stalk stuck under the grain bench like a forgotten feather",
        evidence="a bent reed",
        use_tags={"building"},
        tags={"building", "reeds"},
    ),
    "bell": MissingItem(
        id="bell",
        label="bell",
        phrase="a brass handbell",
        clue="a far-off tinkle answered every gust of wind",
        evidence="a bell-chime",
        use_tags={"shiny", "gift"},
        tags={"shiny", "bell"},
    ),
    "ribbon": MissingItem(
        id="ribbon",
        label="ribbon",
        phrase="a spool of blue ribbon",
        clue="a thread of blue fluttered from a low branch and winked in the sun",
        evidence="a blue thread",
        use_tags={"gift", "building"},
        tags={"shiny", "ribbon"},
    ),
}

MOTIVES = {
    "hungry_family": Motive(
        id="hungry_family",
        need="feed a hungry family",
        because="little mouths were waiting at home and the pantry had gone thin",
        confession="I was trying to feed my hungry family",
        repair="The square shared the food fairly, and no one went hungry that evening",
        ending="shared_supper",
        requires={"food"},
        tags={"need", "food"},
    ),
    "patch_nest": Motive(
        id="patch_nest",
        need="patch a leaking home",
        because="rain had found a hole and the little house dripped right onto the bed",
        confession="I needed to patch a leaking home before the next rain",
        repair="The whole square carried reeds and ribbon together until the roof sat snug and dry",
        ending="repair_day",
        requires={"building"},
        tags={"need", "repair"},
    ),
    "make_gift": Motive(
        id="make_gift",
        need="make a surprise gift",
        because="someone kind had helped before, and a thank-you was being prepared in secret",
        confession="I wanted to make a surprise gift and keep the surprise one more hour",
        repair="The secret gift was finished in the open, and everyone laughed when the ribbon tangled round the helper's feet",
        ending="gift_day",
        requires={"gift"},
        tags={"gift", "kindness"},
    ),
}

GROUPS = {
    "winged": GroupRule(
        id="winged",
        label="winged animals",
        sign_text="WINGED THIS WAY",
        crowd_name="the winged animals",
        members_phrase="sparrows, ducks, and other winged neighbors",
        opposite_phrase="the walkers and climbers",
        tags={"group"},
    ),
    "whiskered": GroupRule(
        id="whiskered",
        label="whiskered animals",
        sign_text="WHISKERED THIS WAY",
        crowd_name="the whiskered animals",
        members_phrase="cats, mice, and other whiskered neighbors",
        opposite_phrase="the beaked and horned neighbors",
        tags={"group"},
    ),
    "horned": GroupRule(
        id="horned",
        label="horned animals",
        sign_text="HORNED THIS WAY",
        crowd_name="the horned animals",
        members_phrase="goats, deer, and other horned neighbors",
        opposite_phrase="the feathered and whiskered neighbors",
        tags={"group"},
    ),
}


def valid_combo(culprit: CulpritCfg, item: MissingItem, motive: Motive, accused_group: str) -> bool:
    if culprit.group == accused_group:
        return False
    if item.id not in culprit.can_take:
        return False
    if motive.id not in culprit.can_motive:
        return False
    if not (item.use_tags & motive.requires):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for accused_group in GROUPS:
        for culprit in CULPRITS.values():
            for item in ITEMS.values():
                for motive in MOTIVES.values():
                    if valid_combo(culprit, item, motive, accused_group):
                        combos.append((accused_group, culprit.id, item.id, motive.id))
    return sorted(combos)


def explain_rejection(culprit: CulpritCfg, item: MissingItem, motive: Motive, accused_group: str) -> str:
    if culprit.group == accused_group:
        return (
            f"(No story: the accused group is {GROUPS[accused_group].crowd_name}, "
            f"but the real culprit is a {culprit.type} from that same group. This world "
            f"needs the segregation to be a wrong guess, so the mystery can correct it.)"
        )
    if item.id not in culprit.can_take:
        return (
            f"(No story: a {culprit.type} is not a reasonable taker of {item.phrase} here. "
            f"Pick an item that this culprit could actually carry or sneak away with.)"
        )
    if motive.id not in culprit.can_motive:
        return (
            f"(No story: a {culprit.type} does not fit the motive '{motive.id}' in this small fable world.)"
        )
    if not (item.use_tags & motive.requires):
        return (
            f"(No story: {item.phrase} does not suit the motive '{motive.id}'. "
            f"The missing object must genuinely help with the culprit's motive.)"
        )
    return "(No story: this combination is unreasonable.)"


def outcome_of(params: "StoryParams") -> str:
    return MOTIVES[params.motive].ending


def other_group_phrase(accused_group: str) -> str:
    return GROUPS[accused_group].opposite_phrase


def predict_wrong_guess(world: World) -> dict:
    sim = world.copy()
    sim.facts["segregated"] = True
    propagate(sim, narrate=False)
    return {
        "hurt_accused": sim.get("accused_group").memes["hurt"] >= THRESHOLD,
        "hurt_other": sim.get("other_group").memes["hurt"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, helper: Entity, item: MissingItem) -> None:
    world.say(
        f"In the middle of Clover Square stood a common table where neighbors left "
        f"{item.phrase} for all to share."
    )
    world.say(
        f"{leader.id}, called {leader.label}, {leader.attrs['style']}. "
        f"{helper.id}, who {helper.attrs['skill']}, often watched the square with bright patience."
    )


def missing(world: World, leader: Entity, item: MissingItem) -> None:
    leader.memes["pride"] += 1
    world.say(
        f"One morning the table was bare where {item.phrase} ought to have been. "
        f'"Who has taken the {item.label}?" cried {leader.id}.'
    )


def hasty_rule(world: World, leader: Entity, helper: Entity, accused: Entity, other: Entity, group: GroupRule) -> None:
    pred = predict_wrong_guess(world)
    world.facts["predicted_hurt_accused"] = pred["hurt_accused"]
    world.facts["predicted_hurt_other"] = pred["hurt_other"]
    world.facts["segregated"] = True
    propagate(world, narrate=False)
    world.say(
        f'{leader.id} hopped onto a crate and felt very power-ful. '
        f'"Until this is solved, we shall segregate the square," {leader.pronoun()} declared.'
    )
    world.say(
        f'{leader.pronoun().capitalize()} planted a sign that read "{group.sign_text}," '
        f'and ordered {group.crowd_name} to wait on one side and {group.opposite_phrase} on the other.'
    )
    if accused.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{accused.label.capitalize()} blinked in surprise, and even {other.label} shuffled awkwardly. "
            f"The rule made everyone feel smaller, not safer."
        )
    world.say(
        f'{helper.id} tilted {helper.pronoun("possessive")} head. '
        f'"A rule is not a reason," {helper.pronoun()} murmured. "There must be a better clue, and a better motive, too."'
    )


def comic_search(world: World, helper: Entity, item: MissingItem) -> None:
    helper.memes["curiosity"] += 1
    world.say(
        f"{helper.id} began to investigate and {helper.attrs['comic_habit']}. "
        f"At first the square laughed, and then the laughing turned thoughtful."
    )
    world.say(
        f"Soon {helper.pronoun()} found this odd thing: {item.clue}"
    )


def clue_points(world: World, helper: Entity, culprit: Entity, item: MissingItem) -> None:
    world.facts["clue_found"] = True
    world.facts["suspect_id"] = culprit.id
    propagate(world, narrate=False)
    world.say(
        f'{helper.id} followed the hint from stone to step, from step to shrub, until '
        f'{helper.pronoun()} stopped under a fig tree and looked at {culprit.id}.'
    )
    world.say(
        f'"Friend {culprit.id}," said {helper.id}, "the mystery is beginning to sound like {item.evidence}, '
        f'and it sounds very close to your paws."'
    )


def confession(world: World, culprit: Entity, motive: Motive) -> None:
    world.facts["mystery_solved"] = True
    propagate(world, narrate=False)
    culprit.memes["honesty"] += 1
    world.say(
        f"{culprit.id}, who was {culprit.attrs['manner']}, lowered {culprit.pronoun('possessive')} eyes. "
        f'"It was I," {culprit.pronoun()} said. "{motive.confession}. {motive.because}."'
    )


def judgment_turns(world: World, leader: Entity, accused: Entity, group: GroupRule) -> None:
    world.say(
        f"{leader.id}'s ears drooped. {leader.pronoun().capitalize()} looked from {culprit_group_phrase(group)} "
        f"to the innocent line by the sign and understood how badly guessing had bruised the square."
    )
    world.say(
        f'"I tried to keep order," {leader.id} said, "but I used pride where I should have used proof. '
        f'I told myself I had a reason, yet I never learned the true motive."'
    )


def culprit_group_phrase(group: GroupRule) -> str:
    return group.crowd_name


def lift_rule(world: World, leader: Entity) -> None:
    world.facts["segregated"] = False
    world.say(
        f"{leader.id} pulled up the sign and snapped it across one knee. "
        f'"No more lines," {leader.pronoun()} said. "The square is one square again."'
    )


def repair(world: World, helper: Entity, motive: Motive) -> None:
    world.facts["repair_done"] = True
    propagate(world, narrate=False)
    world.say(
        f"Then the neighbors did the sensible thing that a fable always hopes for but cannot force: "
        f"they helped instead of sneering. {motive.repair}."
    )
    if motive.ending == "gift_day":
        world.say(
            f"As they worked, the blue ribbon slipped loose and looped around {helper.id}'s ankles. "
            f"{helper.id} bowed as if the knot had awarded a medal, and the whole square laughed."
        )
    elif motive.ending == "repair_day":
        world.say(
            f"When the last reed was tucked in place, even the wind sounded pleased and forgot to drip indoors."
        )
    else:
        world.say(
            f"By sunset the table held bowls on every side, and no one had to pretend not to be hungry."
        )


def moral_end(world: World, leader: Entity) -> None:
    world.say(
        f"After that, whenever {leader.id} felt like making a loud rule, "
        f"{leader.pronoun()} first asked for the facts. For no badge is so power-ful "
        f"that it can turn a guess into justice."
    )


def tell(
    leader_cfg: Leader,
    helper_cfg: Helper,
    culprit_cfg: CulpritCfg,
    item_cfg: MissingItem,
    motive_cfg: Motive,
    group_cfg: GroupRule,
) -> World:
    world = World()
    world.facts["segregated"] = False
    world.facts["clue_found"] = False
    world.facts["mystery_solved"] = False
    world.facts["repair_done"] = False
    world.facts["suspect_id"] = ""

    leader = world.add(Entity(
        id=leader_cfg.title.split()[1],
        kind="character",
        type=leader_cfg.type,
        label=leader_cfg.title,
        role="leader",
        attrs={"style": leader_cfg.style},
    ))
    helper = world.add(Entity(
        id=helper_cfg.type.capitalize(),
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.type,
        role="helper",
        attrs={"skill": helper_cfg.clue_skill, "comic_habit": helper_cfg.comic_habit},
    ))
    culprit = world.add(Entity(
        id=culprit_cfg.type.capitalize(),
        kind="character",
        type=culprit_cfg.type,
        label=culprit_cfg.type,
        role="culprit",
        attrs={"manner": culprit_cfg.manner, "group": culprit_cfg.group},
    ))
    accused = world.add(Entity(
        id="accused_group",
        kind="character",
        type="crowd",
        label=group_cfg.crowd_name,
        role="crowd",
        attrs={"group": group_cfg.id},
    ))
    other = world.add(Entity(
        id="other_group",
        kind="character",
        type="crowd",
        label=group_cfg.opposite_phrase,
        role="crowd",
        attrs={"group": "other"},
    ))

    introduce(world, leader, helper, item_cfg)
    missing(world, leader, item_cfg)

    world.para()
    hasty_rule(world, leader, helper, accused, other, group_cfg)
    comic_search(world, helper, item_cfg)
    clue_points(world, helper, culprit, item_cfg)

    world.para()
    confession(world, culprit, motive_cfg)
    judgment_turns(world, leader, accused, group_cfg)
    lift_rule(world, leader)

    world.para()
    repair(world, helper, motive_cfg)
    moral_end(world, leader)

    world.facts.update(
        leader=leader,
        helper=helper,
        culprit=culprit,
        accused_group_cfg=group_cfg,
        accused_group_ent=accused,
        other_group_ent=other,
        item_cfg=item_cfg,
        motive_cfg=motive_cfg,
        outcome=motive_cfg.ending,
        wrong_guess_hurt=accused.memes["hurt"] >= THRESHOLD,
        solved=world.facts["mystery_solved"],
        repair_done=world.facts["repair_done"],
    )
    return world


KNOWLEDGE = {
    "segregate": [(
        "What does segregate mean?",
        "To segregate means to split people into separate groups and keep them apart. That is unfair when the split is based on guessing or on a trait that has nothing to do with the problem."
    )],
    "motive": [(
        "What is a motive?",
        "A motive is the reason someone does something. Knowing the motive can help you understand an action, though it does not always make the action right."
    )],
    "power": [(
        "What should a power-ful leader do before making a rule?",
        "A power-ful leader should look for facts, listen carefully, and be fair. Strong voices are not the same as wise choices."
    )],
    "mystery": [(
        "How do you solve a mystery fairly?",
        "You solve a mystery by noticing clues and testing ideas against what really happened. Guessing about a whole group is not the same as finding proof."
    )],
    "food": [(
        "Why might hunger lead to bad choices?",
        "Hunger can make someone scared or desperate, and that can push them into poor choices. Helping with the need is often wiser than only scolding the mistake."
    )],
    "repair": [(
        "Why is it good to help repair a problem together?",
        "Helping repair a problem together fixes more than the broken thing. It also helps trust grow back."
    )],
    "gift": [(
        "Can a secret gift still cause trouble?",
        "Yes. Even a kind plan can cause trouble if it uses something that belongs to everyone or if it hides the truth too long."
    )],
}
KNOWLEDGE_ORDER = ["segregate", "motive", "power", "mystery", "food", "repair", "gift"]


@dataclass
class StoryParams:
    leader: str
    helper: str
    accused_group: str
    culprit: str
    item: str
    motive: str
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
    leader = f["leader"]
    helper = f["helper"]
    item = f["item_cfg"]
    motive = f["motive_cfg"]
    group = f["accused_group_cfg"]
    return [
        f'Write a short fable for a young child that includes the words "power-ful", "segregate", and "motive". A leader wrongly separates {group.crowd_name} after {item.label} go missing, and a funny helper solves the mystery.',
        f"Tell a gentle mystery fable where {leader.label} makes a proud rule, {helper.id} follows clues, and the true motive for taking {item.label} turns out to be {motive.need}.",
        f"Write a child-facing story with conflict, humor, and a mystery to solve, ending in fairness instead of blame."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    culprit = f["culprit"]
    item = f["item_cfg"]
    motive = f["motive_cfg"]
    group = f["accused_group_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "What was the problem at the start of the story?",
            f"The problem was that {item.phrase} disappeared from the common table in Clover Square. That loss made {leader.label} rush to make a rule before the mystery had really been solved."
        ),
        (
            f"Why did {leader.label} segregate the square?",
            f"{leader.id} thought splitting {group.crowd_name} from {group.opposite_phrase} would make the thief easier to find. But it was only a guess, and the rule hurt innocent neighbors instead of bringing the truth any closer."
        ),
        (
            f"How did {helper.id} help solve the mystery?",
            f"{helper.id} looked for small clues instead of blaming a whole group. Following {item.clue} led {helper.pronoun('object')} to {culprit.id}, which turned a loud accusation into a real answer."
        ),
        (
            f"What was {culprit.id}'s motive?",
            f"{culprit.id}'s motive was to {motive.need}. {motive.because.capitalize()}, so the taking came from a need or a secret plan, not from the group that had been blamed."
        ),
        (
            "How did the story end?",
            f"The sign came down, the neighbors helped repair the real problem, and the square became one square again. The ending shows that fairness returned only after proof, apology, and shared help."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"segregate", "motive", "power", "mystery"}
    motive = world.facts["motive_cfg"]
    if "food" in motive.requires:
        tags.add("food")
    if motive.ending == "repair_day":
        tags.add("repair")
    if motive.ending == "gift_day":
        tags.add("gift")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={{{', '.join(f'{k}={v!r}' for k, v in sorted(world.facts.items()) if k not in {'leader', 'helper', 'culprit', 'accused_group_cfg', 'accused_group_ent', 'other_group_ent', 'item_cfg', 'motive_cfg'})}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        leader="lion",
        helper="goose",
        accused_group="winged",
        culprit="squirrel",
        item="figs",
        motive="hungry_family",
    ),
    StoryParams(
        leader="ram",
        helper="tortoise",
        accused_group="horned",
        culprit="crow",
        item="reeds",
        motive="patch_nest",
    ),
    StoryParams(
        leader="peacock",
        helper="mouse",
        accused_group="whiskered",
        culprit="crow",
        item="bell",
        motive="make_gift",
    ),
    StoryParams(
        leader="lion",
        helper="mouse",
        accused_group="winged",
        culprit="goat",
        item="ribbon",
        motive="patch_nest",
    ),
    StoryParams(
        leader="ram",
        helper="goose",
        accused_group="horned",
        culprit="squirrel",
        item="ribbon",
        motive="make_gift",
    ),
]


ASP_RULES = r"""
% Basic domains
valid(Ac, Cu, It, Mo) :-
    group(Ac), culprit(Cu), item(It), motive(Mo),
    actual_group(Cu, G), G != Ac,
    can_take(Cu, It),
    can_motive(Cu, Mo),
    item_tag(It, Tag),
    motive_requires(Mo, Tag).

ending_for(Mo, End) :- motive_ending(Mo, End).

#show valid/4.
#show ending_for/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gid in GROUPS:
        lines.append(asp.fact("group", gid))
    for cid, cfg in CULPRITS.items():
        lines.append(asp.fact("culprit", cid))
        lines.append(asp.fact("actual_group", cid, cfg.group))
        for item in sorted(cfg.can_take):
            lines.append(asp.fact("can_take", cid, item))
        for motive in sorted(cfg.can_motive):
            lines.append(asp.fact("can_motive", cid, motive))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.use_tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for mid, motive in MOTIVES.items():
        lines.append(asp.fact("motive", mid))
        lines.append(asp.fact("motive_ending", mid, motive.ending))
        for tag in sorted(motive.requires):
            lines.append(asp.fact("motive_requires", mid, tag))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_endings() -> dict[str, str]:
    import asp
    model = asp.one_model(asp_program())
    return {m: e for (m, e) in asp.atoms(model, "ending_for")}


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and python valid_combos():")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    endings = asp_endings()
    for mid, motive in MOTIVES.items():
        if endings.get(mid) != motive.ending:
            rc = 1
            print(f"MISMATCH in ending for motive {mid}: clingo={endings.get(mid)!r} python={motive.ending!r}")

    smoke_cases = [CURATED[0]]
    try:
        random_case = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(random_case)
    except StoryError as err:
        rc = 1
        print(f"Smoke-test resolve_params failed: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated an empty story.")
            print(f"OK: smoke generated story for {params.culprit}/{params.item}/{params.motive}.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"Smoke generation failed for {params}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable storyworld: a proud leader segregates the square after something goes missing, and a funny helper solves the mystery."
    )
    ap.add_argument("--leader", choices=LEADERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--accused-group", choices=GROUPS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.accused_group and args.culprit and args.item and args.motive:
        culprit = CULPRITS[args.culprit]
        item = ITEMS[args.item]
        motive = MOTIVES[args.motive]
        if not valid_combo(culprit, item, motive, args.accused_group):
            raise StoryError(explain_rejection(culprit, item, motive, args.accused_group))

    combos = [
        combo for combo in valid_combos()
        if (args.accused_group is None or combo[0] == args.accused_group)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.item is None or combo[2] == args.item)
        and (args.motive is None or combo[3] == args.motive)
    ]
    if not combos:
        if args.culprit and args.item and args.motive:
            culprit = CULPRITS[args.culprit]
            item = ITEMS[args.item]
            motive = MOTIVES[args.motive]
            accused = args.accused_group or next(iter(GROUPS))
            raise StoryError(explain_rejection(culprit, item, motive, accused))
        raise StoryError("(No valid combination matches the given options.)")

    accused_group, culprit, item, motive = rng.choice(sorted(combos))
    leader = args.leader or rng.choice(sorted(LEADERS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        leader=leader,
        helper=helper,
        accused_group=accused_group,
        culprit=culprit,
        item=item,
        motive=motive,
    )


def generate(params: StoryParams) -> StorySample:
    if params.leader not in LEADERS:
        raise StoryError(f"(Unknown leader: {params.leader})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.accused_group not in GROUPS:
        raise StoryError(f"(Unknown accused group: {params.accused_group})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Unknown motive: {params.motive})")

    culprit = CULPRITS[params.culprit]
    item = ITEMS[params.item]
    motive = MOTIVES[params.motive]
    if not valid_combo(culprit, item, motive, params.accused_group):
        raise StoryError(explain_rejection(culprit, item, motive, params.accused_group))

    world = tell(
        leader_cfg=LEADERS[params.leader],
        helper_cfg=HELPERS[params.helper],
        culprit_cfg=culprit,
        item_cfg=item,
        motive_cfg=motive,
        group_cfg=GROUPS[params.accused_group],
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (accused_group, culprit, item, motive) combos:\n")
        for accused_group, culprit, item, motive in combos:
            print(f"  {accused_group:10} {culprit:9} {item:7} {motive}")
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
            header = f"### {p.leader}, {p.helper}: {p.accused_group} blamed, {p.culprit} took {p.item} for {p.motive}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
