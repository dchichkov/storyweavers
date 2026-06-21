#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py
============================================================================

A standalone story world for a small adventure mystery: two children help a
ranger solve a missing-item puzzle by noticing the same clue again and again.
The repeated clue is not decorative; it changes the children's confidence and
guides them to the right hiding place. The ending folds the adventure back into
a gentle lesson, because the ranger wanted to educate young explorers about
reading signs in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py --setting forest --mystery feather_trail
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py --mystery thorn_snags --helper hook_stick
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py --all
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/educate_mystery_to_solve_repetition_adventure.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "ranger_woman", "woman"}
        male = {"boy", "father", "ranger_man", "man"}
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
            "ranger_woman": "ranger",
            "ranger_man": "ranger",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parameter knobs
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
    affords: set[str] = field(default_factory=set)
    path_text: str = ""
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
class Mystery:
    id: str
    item_label: str
    item_phrase: str
    purpose: str
    exclaim: str
    repeated_sign: str
    repeated_line: str
    culprit: str
    hide_place: str
    hide_phrase: str
    access: str
    trail_start: str
    retrieval: str
    lesson: str
    danger_feel: str
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
    label: str
    phrase: str
    access: str
    use_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"leader", "partner"}]

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
# Causal rules
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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    guide = world.get("guide")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    guide.memes["worry"] += 1
    return []


def _r_first_clue_curiosity(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["seen"] < 1:
        return []
    sig = ("curiosity",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["curiosity"] += 1
    return []


def _r_repetition_certainty(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["seen"] < 2:
        return []
    sig = ("certainty",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["certainty"] += 1
    return []


def _r_deep_place_caution(world: World) -> list[str]:
    place = world.get("hide_place")
    if place.meters["reached"] < THRESHOLD:
        return []
    sig = ("caution",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts.get("mystery_access") in {"under_bridge", "thorn_bush"}:
        for kid in world.kids():
            kid.memes["caution"] += 1
    return []


def _r_retrieved_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["retrieved"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for ent in [world.get("guide")] + world.kids():
        ent.memes["relief"] += 1
        ent.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="first_clue_curiosity", tag="emotional", apply=_r_first_clue_curiosity),
    Rule(name="repetition_certainty", tag="emotional", apply=_r_repetition_certainty),
    Rule(name="deep_place_caution", tag="emotional", apply=_r_deep_place_caution),
    Rule(name="retrieved_relief", tag="emotional", apply=_r_retrieved_relief),
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
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def helper_fits(mystery: Mystery, helper: Helper) -> bool:
    return mystery.access == helper.access


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id in sorted(setting.affords):
            mystery = MYSTERIES[mystery_id]
            for helper_id, helper in HELPERS.items():
                if helper_fits(mystery, helper):
                    combos.append((setting_id, mystery_id, helper_id))
    return sorted(combos)


def explain_rejection(mystery: Mystery, helper: Helper) -> str:
    need = {
        "high_branch": "something that can reach up to a low branch",
        "thorn_bush": "something that protects small hands from thorns",
        "under_bridge": "something that can reach under the bridge without climbing in",
    }[mystery.access]
    return (
        f"(No story: {helper.label} is not a sensible way to recover {mystery.item_phrase} "
        f"from {mystery.hide_phrase}. This mystery needs {need}.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_path(world: World) -> dict:
    sim = world.copy()
    clue = sim.get("clue")
    clue.meters["seen"] += 3
    propagate(sim, narrate=False)
    return {
        "curiosity": sum(k.memes["curiosity"] for k in sim.kids()),
        "certainty": sum(k.memes["certainty"] for k in sim.kids()),
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def open_adventure(world: World, a: Entity, b: Entity, guide: Entity,
                   mystery: Mystery, helper: Helper) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["bravery"] += 1
    world.say(
        f"Early that morning, {guide.id} led {a.id} and {b.id} along {world.setting.place}. "
        f"{world.setting.path_text}"
    )
    world.say(
        f"In {guide.pronoun('possessive')} satchel was {mystery.item_phrase}, "
        f"which {guide.pronoun()} used to educate young explorers about {mystery.purpose}."
    )
    world.say(
        f'{guide.id} even tucked {helper.phrase} into a side pocket, because real adventures '
        f'were easier when everyone carried the right tool.'
    )


def discover_loss(world: World, guide: Entity, mystery: Mystery) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the first bend, {guide.id} stopped short. "
        f'"{mystery.exclaim}" {guide.pronoun()} said.'
    )
    world.say(
        f"The path suddenly felt like the beginning of a mystery instead of an ordinary walk."
    )


def invite_search(world: World, a: Entity, b: Entity, guide: Entity) -> None:
    pred = predict_path(world)
    world.facts["predicted_curiosity"] = pred["curiosity"]
    world.facts["predicted_certainty"] = pred["certainty"]
    world.say(
        f'"Then we will solve it like explorers," said {a.id}. '
        f'{b.id} nodded so hard that {b.pronoun("possessive")} backpack bounced.'
    )
    world.say(
        f'{guide.id} smiled a little, even though {guide.pronoun()} was worried. '
        f'"Good clue-hunters look twice, and then look again," {guide.pronoun()} said.'
    )


def see_clue(world: World, speaker: Entity, mystery: Mystery, number: int) -> None:
    clue = world.get("clue")
    clue.meters["seen"] += 1
    propagate(world, narrate=False)
    if number == 1:
        world.say(
            f"A few steps later, {speaker.id} pointed down. "
            f'"Look!" {speaker.pronoun().capitalize()} whispered. {mystery.repeated_line}.'
        )
    elif number == 2:
        world.say(
            f"They hurried on and found {mystery.repeated_sign} again. "
            f'"Again!" said {speaker.id}. "{mystery.repeated_sign.capitalize()} do not land in two places by accident."'
        )
    else:
        world.say(
            f"Past one more turn, there it was a third time: {mystery.repeated_sign}. "
            f"Now the pattern felt too strong to ignore."
        )


def interpret_pattern(world: World, a: Entity, b: Entity, mystery: Mystery) -> None:
    certainty = a.memes["certainty"] + b.memes["certainty"]
    if certainty >= 2:
        world.say(
            f'"It is the same clue over and over," said {b.id}. '
            f'"Something is leading us toward {mystery.hide_phrase}."'
        )
    else:
        world.say(
            f'"I think the clues are trying to show us a direction," said {a.id}.'
        )


def reach_hiding_place(world: World, a: Entity, b: Entity, mystery: Mystery) -> None:
    place = world.get("hide_place")
    place.meters["reached"] += 1
    propagate(world, narrate=False)
    mood = mystery.danger_feel
    world.say(
        f"The trail ended at {mystery.hide_phrase}. "
        f"It was {mood}, and both children went quiet for one small second."
    )
    if a.memes["caution"] >= THRESHOLD or b.memes["caution"] >= THRESHOLD:
        world.say(
            f"Then {a.id} took a careful breath. Adventure was easier when brave feet listened to careful thoughts."
        )


def solve_mystery(world: World, guide: Entity, helper: Helper, mystery: Mystery) -> None:
    item = world.get("item")
    item.meters["retrieved"] += 1
    item.meters["missing"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} pulled out {helper.phrase}, and {helper.use_text}."
    )
    world.say(
        f"There was {mystery.item_phrase}, right where the clues had promised."
    )


def reveal(world: World, guide: Entity, mystery: Mystery, a: Entity, b: Entity) -> None:
    world.say(
        f'"So that was the answer," said {guide.id}. '
        f'"A {mystery.culprit} carried it away and left {mystery.repeated_sign} behind."'
    )
    world.say(
        f"{a.id} and {b.id} looked at each other with wide, shining eyes. "
        f"The mystery was solved because they had trusted the repeated clue."
    )


def educate_ending(world: World, guide: Entity, a: Entity, b: Entity, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["learned"] += 1
    world.say(
        f'{guide.id} tucked {world.get("item").label} safely back into the satchel. '
        f'"Today did more than find a lost thing," {guide.pronoun()} said. '
        f'"It helped educate us all. {mystery.lesson}"'
    )
    world.say(
        f"Then the three explorers walked on together, a little slower and a lot wiser, "
        f"still watching the path for whatever pattern might appear next."
    )


def tell(setting: Setting, mystery: Mystery, helper: Helper,
         leader_name: str = "Nora", leader_gender: str = "girl",
         partner_name: str = "Finn", partner_gender: str = "boy",
         guide_name: str = "Ranger May", guide_type: str = "ranger_woman") -> World:
    world = World(setting)
    world.facts["mystery_access"] = mystery.access
    world.facts["repetition_target"] = 3

    a = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=["eager"],
        attrs={"job": "clue_hunter"},
    ))
    b = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=["careful"],
        attrs={"job": "pattern_spotter"},
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type=guide_type,
        role="guide",
        label="the ranger",
        traits=["patient", "wise"],
        attrs={"teaches": mystery.purpose},
    ))
    item = world.add(Entity(
        id="item",
        type="lesson_item",
        label=mystery.item_label,
        phrase=mystery.item_phrase,
        attrs={"purpose": mystery.purpose},
    ))
    clue = world.add(Entity(
        id="clue",
        type="clue",
        label=mystery.repeated_sign,
        phrase=mystery.repeated_sign,
    ))
    hide_place = world.add(Entity(
        id="hide_place",
        type="place",
        label=mystery.hide_place,
        phrase=mystery.hide_phrase,
        attrs={"access": mystery.access},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        type="tool",
        label=helper.label,
        phrase=helper.phrase,
        attrs={"access": helper.access},
    ))

    for ent in world.kids() + [guide, item, clue, hide_place, helper_ent]:
        ent.meters["seen"] += 0.0
        ent.meters["retrieved"] += 0.0
        ent.meters["missing"] += 0.0
        ent.meters["reached"] += 0.0
        ent.memes["curiosity"] += 0.0
        ent.memes["certainty"] += 0.0
        ent.memes["caution"] += 0.0
        ent.memes["relief"] += 0.0
        ent.memes["joy"] += 0.0
        ent.memes["worry"] += 0.0
        ent.memes["learned"] += 0.0

    open_adventure(world, a, b, guide, mystery, helper)
    world.para()
    discover_loss(world, guide, mystery)
    invite_search(world, a, b, guide)
    see_clue(world, a, mystery, 1)
    see_clue(world, b, mystery, 2)
    see_clue(world, a, mystery, 3)
    interpret_pattern(world, a, b, mystery)

    world.para()
    reach_hiding_place(world, a, b, mystery)
    solve_mystery(world, guide, helper, mystery)
    reveal(world, guide, mystery, a, b)

    world.para()
    educate_ending(world, guide, a, b, mystery)

    world.facts.update(
        setting=setting,
        mystery=mystery,
        helper=helper,
        leader=a,
        partner=b,
        guide=guide,
        item=item,
        clue=clue,
        hide_place=hide_place,
        clue_count=int(clue.meters["seen"]),
        solved=item.meters["retrieved"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(
        id="forest",
        place="the pine-needle path in the forest",
        affords={"feather_trail", "thorn_snags"},
        path_text="Sunlight slipped between tall trunks, and every turn looked like a secret doorway.",
        tags={"forest", "trail"},
    ),
    "creek": Setting(
        id="creek",
        place="the creek trail beside the old wooden bridge",
        affords={"pawprint_bridge"},
        path_text="The water flashed silver below, and the bridge boards knocked softly under small shoes.",
        tags={"creek", "bridge"},
    ),
    "meadow": Setting(
        id="meadow",
        place="the meadow path that curved toward the trees",
        affords={"feather_trail", "thorn_snags"},
        path_text="Long grass swayed on both sides, making the narrow path feel like a road into the unknown.",
        tags={"meadow", "trail"},
    ),
}

MYSTERIES = {
    "feather_trail": Mystery(
        id="feather_trail",
        item_label="silver compass",
        item_phrase="the small silver compass",
        purpose="finding north and noticing where a path turns",
        exclaim="My compass is gone",
        repeated_sign="three blue feathers",
        repeated_line="Three blue feathers lay on the ground",
        culprit="magpie",
        hide_place="low pine branch",
        hide_phrase="a low pine branch bent over the path",
        access="high_branch",
        trail_start="upward",
        retrieval="used it to lift the compass down from the branch",
        lesson="When the same clue appears again and again, it is probably not random at all.",
        danger_feel="high enough to feel tricky, but close enough to study",
        tags={"compass", "bird", "pattern"},
    ),
    "thorn_snags": Mystery(
        id="thorn_snags",
        item_label="leaf-card pouch",
        item_phrase="the little pouch of leaf cards",
        purpose="matching leaves to trees by shape and edge",
        exclaim="The leaf cards are missing",
        repeated_sign="the same green ribbon thread caught on thorns",
        repeated_line="The same green ribbon thread was caught on a thorn",
        culprit="goat",
        hide_place="blackberry bush",
        hide_phrase="a blackberry bush with hooked thorns",
        access="thorn_bush",
        trail_start="sideways",
        retrieval="used them to reach in safely and free the pouch from the thorns",
        lesson="Patterns can whisper the truth even before you see the whole answer.",
        danger_feel="scratchy and crowded with hooks",
        tags={"leaves", "bush", "pattern"},
    ),
    "pawprint_bridge": Mystery(
        id="pawprint_bridge",
        item_label="shell whistle",
        item_phrase="the shell whistle",
        purpose="how sound travels across water and wood",
        exclaim="The whistle has disappeared",
        repeated_sign="muddy puppy pawprints",
        repeated_line="Muddy puppy pawprints dotted the boards",
        culprit="camp puppy",
        hide_place="the dark space under the bridge",
        hide_phrase="the dark space under the bridge",
        access="under_bridge",
        trail_start="downward",
        retrieval="slid it under the bridge and hooked the whistle back without anyone crawling into the mud",
        lesson="Repeated signs can turn a worried guess into a smart answer.",
        danger_feel="shadowy and damp",
        tags={"sound", "bridge", "pattern"},
    ),
}

HELPERS = {
    "step_stool": Helper(
        id="step_stool",
        label="step stool",
        phrase="a folding step stool",
        access="high_branch",
        use_text="opened the stool, climbed one careful step, and used it to lift the compass down from the branch",
        qa_text="used a folding step stool to reach the branch safely",
        tags={"tool", "reach"},
    ),
    "garden_gloves": Helper(
        id="garden_gloves",
        label="garden gloves",
        phrase="a pair of garden gloves",
        access="thorn_bush",
        use_text="pulled on the gloves and used them to reach in safely and free the pouch from the thorns",
        qa_text="put on garden gloves and pulled the pouch out without getting scratched",
        tags={"tool", "gloves"},
    ),
    "hook_stick": Helper(
        id="hook_stick",
        label="hook stick",
        phrase="a long hook stick",
        access="under_bridge",
        use_text="slid it under the bridge and hooked the whistle back without anyone crawling into the mud",
        qa_text="used a long hook stick to pull the whistle back from under the bridge",
        tags={"tool", "bridge"},
    ),
}


GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna"]
BOY_NAMES = ["Finn", "Leo", "Max", "Sam", "Theo", "Ben", "Noah", "Eli"]
GUIDE_NAMES = ["Ranger May", "Ranger June", "Ranger Oak", "Ranger Tess"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    mystery: str
    helper: str
    leader_name: str
    leader_gender: str
    partner_name: str
    partner_gender: str
    guide_name: str
    guide_type: str
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
    "compass": [(
        "What does a compass do?",
        "A compass helps you find direction. Its needle points north, which helps explorers know which way they are going.",
    )],
    "leaves": [(
        "Why do people compare leaves when they study trees?",
        "Leaves have different shapes, edges, and sizes. Looking closely at those patterns helps people tell one kind of tree from another.",
    )],
    "sound": [(
        "How can sound travel across water and wood?",
        "Sound is made of tiny vibrations that move through air and solid things. Water and wood can help carry those vibrations to your ears.",
    )],
    "bird": [(
        "Why might a bird pick up something shiny?",
        "Some birds notice bright or shiny things very quickly. They may carry one away because it catches their eye.",
    )],
    "bridge": [(
        "Why is it safer to use a tool instead of crawling under a bridge?",
        "A tool can reach into a muddy or dark place while you stay on safe ground. That keeps your clothes cleaner and your body safer.",
    )],
    "gloves": [(
        "What are garden gloves for?",
        "Garden gloves protect your hands from scratches and prickly plants. They also help you hold rough things more safely.",
    )],
    "pattern": [(
        "What is a pattern?",
        "A pattern is something that repeats in a way you can notice. When the same clue appears again and again, it can help you solve a problem.",
    )],
}
KNOWLEDGE_ORDER = ["pattern", "compass", "leaves", "sound", "bird", "bridge", "gloves"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery = f["mystery"]
    leader = f["leader"]
    partner = f["partner"]
    guide = f["guide"]
    return [
        f'Write an adventure story for a 3-to-5-year-old that includes the word "educate" and a mystery solved by repeated clues.',
        f"Tell a gentle adventure where {leader.id} and {partner.id} help {guide.id} find {mystery.item_phrase} by noticing {mystery.repeated_sign} again and again.",
        f"Write a story about young explorers who solve a mystery because a pattern keeps repeating on the trail, and end with a calm lesson about paying attention.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partner = f["partner"]
    guide = f["guide"]
    mystery = f["mystery"]
    helper = f["helper"]
    clue_count = f["clue_count"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {partner.id}, two young explorers, and {guide.id}, the ranger leading their walk.",
        ),
        (
            f"Why did {guide.id} care about {mystery.item_phrase}?",
            f"{guide.id} used it to educate young explorers about {mystery.purpose}. That is why losing it turned the walk into an important mystery.",
        ),
        (
            "What clue kept repeating?",
            f"The repeated clue was {mystery.repeated_sign}. The children saw it {clue_count} times, so they knew it was a pattern and not an accident.",
        ),
        (
            "How did the children solve the mystery?",
            f"They followed the same clue again and again until it led them to {mystery.hide_phrase}. The repetition gave them confidence because each new clue pointed in the same direction.",
        ),
        (
            f"How did {guide.id} get the lost item back?",
            f"{guide.id} {helper.qa_text}. That worked because the tool matched the place where the item was hidden.",
        ),
        (
            "What changed by the end of the story?",
            f"At first the group felt worried and puzzled because the lesson item was missing. By the end they felt relieved and proud, because the mystery was solved and the adventure had taught them to trust repeating clues.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["mystery"].tags) | set(world.facts["helper"].tags)
    tags.add("pattern")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(S, M, H) :- setting(S), mystery(M), helper(H), affords(S, M), needs(M, A), supports(H, A).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for mystery_id in sorted(setting.affords):
            lines.append(asp.fact("affords", setting_id, mystery_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("needs", mystery_id, mystery.access))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("supports", helper_id, helper.access))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        setting="forest",
        mystery="feather_trail",
        helper="step_stool",
        leader_name="Nora",
        leader_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        guide_name="Ranger May",
        guide_type="ranger_woman",
    ),
    StoryParams(
        setting="forest",
        mystery="thorn_snags",
        helper="garden_gloves",
        leader_name="Lucy",
        leader_gender="girl",
        partner_name="Theo",
        partner_gender="boy",
        guide_name="Ranger Oak",
        guide_type="ranger_man",
    ),
    StoryParams(
        setting="creek",
        mystery="pawprint_bridge",
        helper="hook_stick",
        leader_name="Mia",
        leader_gender="girl",
        partner_name="Leo",
        partner_gender="boy",
        guide_name="Ranger June",
        guide_type="ranger_woman",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an adventure mystery solved by repeated clues."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.helper:
        mystery = MYSTERIES[args.mystery]
        helper = HELPERS[args.helper]
        if not helper_fits(mystery, helper):
            raise StoryError(explain_rejection(mystery, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, helper_id = rng.choice(combos)
    leader_gender = rng.choice(["girl", "boy"])
    partner_gender = rng.choice(["girl", "boy"])
    leader_name = _pick_name(rng, leader_gender)
    partner_name = _pick_name(rng, partner_gender, avoid=leader_name)
    guide_name = rng.choice(GUIDE_NAMES)
    guide_type = rng.choice(["ranger_woman", "ranger_man"])
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        helper=helper_id,
        leader_name=leader_name,
        leader_gender=leader_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        guide_name=guide_name,
        guide_type=guide_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Unknown mystery: {params.mystery})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    helper = HELPERS[params.helper]

    if params.mystery not in setting.affords:
        raise StoryError(
            f"(No story: {setting.place} does not support the {params.mystery} mystery.)"
        )
    if not helper_fits(mystery, helper):
        raise StoryError(explain_rejection(mystery, helper))

    world = tell(
        setting=setting,
        mystery=mystery,
        helper=helper,
        leader_name=params.leader_name,
        leader_gender=params.leader_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
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
        print(f"{len(combos)} compatible (setting, mystery, helper) combos:\n")
        for setting_id, mystery_id, helper_id in combos:
            print(f"  {setting_id:8} {mystery_id:16} {helper_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.setting}: {p.mystery} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
