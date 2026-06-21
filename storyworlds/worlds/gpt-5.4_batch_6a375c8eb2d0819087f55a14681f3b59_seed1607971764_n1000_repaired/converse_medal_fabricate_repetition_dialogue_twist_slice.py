#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py
=======================================================================================

A standalone story world for a small slice-of-life tale about a missing medal,
a tempted child, a careful conversation, and a gentle twist.

Premise
-------
A child earned a medal and wants to take it to a school sharing moment. On the
morning of the event, the medal is missing. The child and a calm helper search
the home, repeating the same worried refrain: "Not here. Not there. Where is my
medal?" The child is tempted to fabricate a replacement from craft supplies.
Instead of scolding, the helper sits down to converse and asks what happened
last. That conversation changes the search. Sometimes it leads to a happy twist:
the real medal is found in the very place the child finally remembers. If there
is too little time, the child tells the truth and goes without the medal.

Run it
------
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py --award reading --place book
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py --place shoe_rack
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py --all
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/converse_medal_fabricate_repetition_dialogue_twist_slice.py --verify
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
CRAFT_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "sister", "grandmother", "woman"}
        male = {"boy", "father", "brother", "grandfather", "man"}
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
            "sister": "sister",
            "brother": "brother",
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
    cozy: str
    spots: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
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


@dataclass
class Award:
    id: str
    medal_name: str
    earned_for: str
    ribbon: str
    true_place: str
    memory_line: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    room: str
    found_line: str
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
class Material:
    id: str
    label: str
    phrase: str
    craft_score: int
    result: str
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
class HelperType:
    id: str
    type: str
    patience: int
    opening: str
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
    medal = world.get("medal")
    child = world.get("child")
    if medal.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["urgency"] += 1
    return []


def _r_converse_calm(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["talked"] < THRESHOLD:
        return []
    sig = ("converse_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["honesty"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    helper.memes["care"] += 1
    return []


def _r_memory_unlock(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["honesty"] < THRESHOLD or child.memes["recalled"] >= THRESHOLD:
        return []
    sig = ("memory_unlock",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["recalled"] += 1
    return []


def _r_search_find(world: World) -> list[str]:
    medal = world.get("medal")
    child = world.get("child")
    helper = world.get("helper")
    correct = world.facts["correct_place"]
    for place_id in world.facts.get("searched_places", []):
        if place_id != correct:
            continue
        if child.memes["recalled"] < THRESHOLD:
            continue
        sig = ("search_find", place_id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        medal.meters["missing"] = 0.0
        medal.meters["found"] += 1
        child.memes["relief"] += 1
        child.memes["pride"] += 1
        helper.memes["relief"] += 1
        return []
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="converse_calm", tag="emotion", apply=_r_converse_calm),
    Rule(name="memory_unlock", tag="memory", apply=_r_memory_unlock),
    Rule(name="search_find", tag="physical", apply=_r_search_find),
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


def place_compatible(setting: Setting, award: Award) -> bool:
    return award.true_place in setting.spots


def material_sensible(material: Material) -> bool:
    return material.craft_score >= CRAFT_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for aid, award in AWARDS.items():
            if not place_compatible(setting, award):
                continue
            for mid, material in MATERIALS.items():
                if material_sensible(material) and mid in setting.materials:
                    combos.append((sid, aid, mid))
    return combos


def would_find(helper: HelperType, minutes_left: int) -> bool:
    return helper.patience + minutes_left >= 5


def outcome_of(params: "StoryParams") -> str:
    helper = HELPERS[params.helper]
    return "found" if would_find(helper, params.minutes_left) else "honest_without_medal"


def explain_place(setting: Setting, award: Award) -> str:
    return (
        f"(No story: {setting.place} does not have the right place for this medal's last stop. "
        f"The {award.medal_name} was last put in {PLACES[award.true_place].phrase}, so pick a "
        f"setting that includes that spot.)"
    )


def explain_material(material: Material) -> str:
    return (
        f"(Refusing material '{material.id}': it is too flimsy for a believable medal "
        f"(craft_score={material.craft_score} < {CRAFT_MIN}). The storyworld knows about it, "
        f"but prefers sturdier craft choices like foil_cardboard or clay_paint.)"
    )


def predict_after_talk(world: World, helper: HelperType, minutes_left: int) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["talked"] += 1
    propagate(sim, narrate=False)
    if would_find(helper, minutes_left):
        sim.facts["searched_places"] = list(sim.facts["search_order"]) + [sim.facts["correct_place"]]
        propagate(sim, narrate=False)
    return {
        "recalled": child.memes["recalled"] >= THRESHOLD,
        "found": sim.get("medal").meters["found"] >= THRESHOLD,
    }


def opening(world: World, child: Entity, helper: Entity, award: Award) -> None:
    child.memes["love"] += 1
    world.say(
        f"{child.id} had earned a {award.medal_name} for {award.earned_for} the day before. "
        f"The medal had a {award.ribbon} ribbon, and {child.pronoun()} kept touching it just to make "
        f"sure it was real."
    )
    world.say(
        f"In the morning light, {world.setting.cozy}. {helper.id}'s {helper.label_word} was packing snacks "
        f"while {child.id} got ready for school."
    )
    world.say(
        f'"I want to show my medal today," {child.id} said. Then {child.pronoun()} looked at the hook by the door, '
        f"the small table, and the chair seat. The medal was not there."
    )
    world.get("medal").meters["missing"] += 1
    propagate(world)


def repeat_search(world: World, child: Entity, helper: Entity, search_ids: list[str]) -> None:
    world.facts["searched_places"] = []
    refrain = "Not here. Not there. Where is my medal?"
    for index, pid in enumerate(search_ids[:3], 1):
        place = PLACES[pid]
        world.facts["searched_places"].append(pid)
        child.memes["worry"] += 0.5
        world.say(
            f'They looked in {place.phrase}. "{refrain}" {child.id} said for the {["first", "second", "third"][index - 1]} time.'
        )
        if index == 1:
            world.say(f'"Let\'s keep looking," said {helper.id}.')
        elif index == 2:
            world.say(f'"Not here. Not there," echoed {helper.id}, trying to make the words gentle.')
        propagate(world)


def tempted(world: World, child: Entity, material: Material) -> None:
    child.memes["tempted"] += 1
    world.say(
        f'{child.id} stared at the craft drawer. "{child.pronoun("possessive").capitalize()} ribbon could be gone forever," '
        f'{child.pronoun()} whispered. "Maybe I could fabricate a medal from {material.label}."'
    )
    world.say(
        f"The idea felt bright for one second and heavy the next."
    )


def converse(world: World, child: Entity, helper: Entity, award: Award, helper_cfg: HelperType,
             minutes_left: int) -> None:
    pred = predict_after_talk(world, helper_cfg, minutes_left)
    child.memes["talked"] += 1
    propagate(world)
    world.say(
        f'{helper.id} sat on the rug beside {child.id}. "{helper_cfg.opening}"'
    )
    world.say(
        f'"Before we fabricate anything, let\'s converse and think," {helper.id} said. '
        f'"What was the very last thing you did with the medal?"'
    )
    if pred["recalled"]:
        world.say(
            f'{child.id} blinked, then sat very still. "{award.memory_line}"'
        )


def search_correct_place(world: World, child: Entity, helper: Entity, award: Award) -> None:
    correct = award.true_place
    place = PLACES[correct]
    world.facts["searched_places"].append(correct)
    propagate(world)
    if world.get("medal").meters["found"] >= THRESHOLD:
        world.say(
            f'Together they hurried to {place.phrase}. {place.found_line} "{child.id} found it!" cried {helper.id}.'
        )


def found_ending(world: World, child: Entity, helper: Entity, award: Award, material: Material) -> None:
    child.memes["tempted"] = 0.0
    world.say(
        f'{child.id} held the real medal against {child.pronoun("possessive")} shirt and laughed. '
        f'"So I didn\'t need to fabricate one at all," {child.pronoun()} said.'
    )
    world.say(
        f'"Nope," said {helper.id}. "You needed to slow down and remember."'
    )
    world.say(
        f"They went out the door together. The medal swung once, warm in the sun, and the morning felt settled again."
    )
    world.facts["outcome"] = "found"


def honest_ending(world: World, child: Entity, helper: Entity, material: Material) -> None:
    fake = world.add(Entity(id="fake_medal", type="craft", label="practice medal"))
    fake.meters["made"] += 1
    child.memes["honesty"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 0.5)
    world.say(
        f'{helper.id} opened the drawer and set out {material.label}, but did not tie the craft around {child.pronoun("possessive")} neck.'
    )
    world.say(
        f'"We can make a practice medal for fun," said {helper.id}, "but we will not pretend it is the real one."'
    )
    world.say(
        f'{child.id} nodded. "I\'ll tell my teacher the truth," {child.pronoun()} said. '
        f'They made {material.result} and tucked it into the backpack instead.'
    )
    world.say(
        f"At school, {child.id} did not have the medal to hold up, but {child.pronoun()} had a brave voice. "
        f"That turned out to shine even more."
    )
    world.facts["outcome"] = "honest_without_medal"


def tell(setting: Setting, award: Award, material: Material, helper_cfg: HelperType,
         child_name: str = "Mina", child_type: str = "girl", helper_name: str = "Parent",
         minutes_left: int = 2, search_order: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        attrs={"school_event": "sharing circle"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label="the helper",
    ))
    medal = world.add(Entity(
        id="medal",
        type="medal",
        label=award.medal_name,
        owner=child.id,
        attrs={"award": award.id, "ribbon": award.ribbon},
    ))
    child.memes["worry"] = 0.0
    child.memes["honesty"] = 0.0
    child.memes["recalled"] = 0.0
    child.memes["talked"] = 0.0
    medal.meters["missing"] = 0.0
    medal.meters["found"] = 0.0

    default_wrong = [pid for pid in sorted(setting.spots) if pid != award.true_place]
    chosen_search = list(search_order or default_wrong[:3])
    if award.true_place in chosen_search:
        chosen_search = [pid for pid in chosen_search if pid != award.true_place]
    while len(chosen_search) < min(3, max(1, len(default_wrong))):
        for pid in default_wrong:
            if pid not in chosen_search:
                chosen_search.append(pid)
            if len(chosen_search) >= min(3, max(1, len(default_wrong))):
                break

    world.facts.update(
        award=award,
        material=material,
        helper_cfg=helper_cfg,
        minutes_left=minutes_left,
        correct_place=award.true_place,
        search_order=chosen_search,
        searched_places=[],
        setting=setting,
    )

    opening(world, child, helper, award)
    world.para()
    repeat_search(world, child, helper, chosen_search)
    tempted(world, child, material)
    world.para()
    converse(world, child, helper, award, helper_cfg, minutes_left)

    if would_find(helper_cfg, minutes_left):
        search_correct_place(world, child, helper, award)
        world.para()
        found_ending(world, child, helper, award, material)
    else:
        world.para()
        honest_ending(world, child, helper, material)

    world.facts.update(
        child=child,
        helper=helper,
        medal=medal,
        found=medal.meters["found"] >= THRESHOLD,
        fabricated=fake_exists(world),
    )
    return world


def fake_exists(world: World) -> bool:
    item = world.entities.get("fake_medal")
    return bool(item and item.meters["made"] >= THRESHOLD)


SETTINGS = {
    "apartment": Setting(
        id="apartment",
        place="the apartment",
        cozy="the kitchen smelled like toast and the hallway was full of soft morning steps",
        spots={"book", "backpack", "drawer", "coat_pocket"},
        materials={"foil_cardboard", "paper_crayon", "clay_paint"},
    ),
    "house": Setting(
        id="house",
        place="the house",
        cozy="the kettle hummed and a stripe of light lay across the floor",
        spots={"book", "backpack", "coat_pocket", "apron_pocket", "drawer"},
        materials={"foil_cardboard", "paper_crayon", "clay_paint"},
    ),
    "cottage": Setting(
        id="cottage",
        place="the cottage",
        cozy="the window over the sink was bright and the breakfast plates still clinked softly",
        spots={"backpack", "apron_pocket", "drawer"},
        materials={"foil_cardboard", "paper_crayon"},
    ),
}

PLACES = {
    "book": HidingPlace(
        id="book",
        label="library book",
        phrase="the thick library book on the sofa",
        room="living room",
        found_line="The medal slid out from between two pages and landed on the cushion.",
        tags={"book", "reading"},
    ),
    "backpack": HidingPlace(
        id="backpack",
        label="backpack pocket",
        phrase="the front pocket of the backpack",
        room="hallway",
        found_line="The zipper rasped, and there it was, tucked beside a blunt pencil.",
        tags={"backpack", "school"},
    ),
    "coat_pocket": HidingPlace(
        id="coat_pocket",
        label="coat pocket",
        phrase="the coat hanging by the door",
        room="hallway",
        found_line="A small clink came from the pocket before the ribbon even showed.",
        tags={"coat", "race"},
    ),
    "apron_pocket": HidingPlace(
        id="apron_pocket",
        label="apron pocket",
        phrase="the striped apron on the kitchen hook",
        room="kitchen",
        found_line="The ribbon peeked out from the pocket like a tiny bright tongue.",
        tags={"apron", "garden"},
    ),
    "drawer": HidingPlace(
        id="drawer",
        label="craft drawer",
        phrase="the shallow craft drawer",
        room="kitchen",
        found_line="Under a stack of stickers, the medal shone back at them.",
        tags={"drawer", "craft"},
    ),
    "shoe_rack": HidingPlace(
        id="shoe_rack",
        label="shoe rack",
        phrase="the shoe rack by the door",
        room="hallway",
        found_line="The medal was nowhere near the shoes.",
        tags={"shoes"},
    ),
}

AWARDS = {
    "reading": Award(
        id="reading",
        medal_name="reading medal",
        earned_for="finishing a stack of library books",
        ribbon="blue",
        true_place="book",
        memory_line='"I used it as a bookmark while I read one more page after dinner!"',
        tags={"reading", "book"},
    ),
    "running": Award(
        id="running",
        medal_name="running medal",
        earned_for="finishing the little school race",
        ribbon="red",
        true_place="coat_pocket",
        memory_line='"I took it off when I came inside and stuffed it into my coat pocket because my hands were cold!"',
        tags={"running", "coat"},
    ),
    "garden": Award(
        id="garden",
        medal_name="garden medal",
        earned_for="helping plant beans in the school bed",
        ribbon="green",
        true_place="apron_pocket",
        memory_line='"I showed it while I was wearing the striped apron and then I forgot it there!"',
        tags={"garden", "apron"},
    ),
    "music": Award(
        id="music",
        medal_name="music medal",
        earned_for="singing clearly at assembly",
        ribbon="gold",
        true_place="backpack",
        memory_line='"I tucked it into my backpack pocket so it would come to school again today!"',
        tags={"music", "backpack"},
    ),
}

MATERIALS = {
    "foil_cardboard": Material(
        id="foil_cardboard",
        label="cardboard and silver foil",
        phrase="cardboard and silver foil",
        craft_score=3,
        result="a round silver craft medal with a neat ribbon loop",
        tags={"foil", "craft"},
    ),
    "clay_paint": Material(
        id="clay_paint",
        label="air-dry clay and yellow paint",
        phrase="air-dry clay and yellow paint",
        craft_score=2,
        result="a lumpy little painted medal that still looked cheerful",
        tags={"clay", "craft"},
    ),
    "paper_crayon": Material(
        id="paper_crayon",
        label="paper and crayons",
        phrase="paper and crayons",
        craft_score=2,
        result="a paper medal colored with careful yellow rings",
        tags={"paper", "craft"},
    ),
    "string_leaf": Material(
        id="string_leaf",
        label="string and a leaf",
        phrase="string and a leaf",
        craft_score=1,
        result="a leaf necklace",
        tags={"leaf", "craft"},
    ),
}

HELPERS = {
    "mother": HelperType(
        id="mother",
        type="mother",
        patience=3,
        opening="Come close, little one. Fast feet make mixed-up thoughts.",
        tags={"family"},
    ),
    "father": HelperType(
        id="father",
        type="father",
        patience=2,
        opening="Take one breath with me. We think better when we are quiet first.",
        tags={"family"},
    ),
    "grandmother": HelperType(
        id="grandmother",
        type="grandmother",
        patience=4,
        opening="Sit by me and tell it from the beginning.",
        tags={"family"},
    ),
    "brother": HelperType(
        id="brother",
        type="brother",
        patience=1,
        opening="Hold on. Let me hear the whole story before we rush.",
        tags={"family"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Maya", "Rose", "Ella", "Zoe"]
BOY_NAMES = ["Owen", "Leo", "Max", "Eli", "Finn", "Theo", "Noah", "Sam"]


@dataclass
class StoryParams:
    setting: str
    award: str
    material: str
    helper: str
    child_name: str
    child_type: str
    helper_name: str
    minutes_left: int = 2
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
    "medal": [
        (
            "What is a medal?",
            "A medal is a special prize you can wear or hold to remember something you did well. It often hangs from a ribbon."
        )
    ],
    "converse": [
        (
            "What does converse mean?",
            "To converse means to talk together and listen to each other. A calm conversation can help people remember and decide what to do."
        )
    ],
    "fabricate": [
        (
            "What does fabricate mean?",
            "Fabricate can mean to make something, especially with your hands from other materials. It can also mean making up something untrue, which is why honesty matters."
        )
    ],
    "reading": [
        (
            "Why might a medal end up inside a book?",
            "A child might tuck a ribbon into a book as a bookmark and forget. Later, the book can look ordinary even though something important is inside."
        )
    ],
    "backpack": [
        (
            "Why do people keep things in a backpack pocket?",
            "A backpack pocket keeps school things together in one place. Small things can hide there if they slip under papers or pencils."
        )
    ],
    "craft": [
        (
            "What can craft supplies be used for?",
            "Craft supplies can be used to make pretend things, decorations, and gifts. They are good for creating, but they do not change what is true."
        )
    ],
    "honesty": [
        (
            "Why is it good to tell the truth when something is missing?",
            "Telling the truth helps other people trust you and help you. Even if the problem is not fixed right away, honesty makes the next step clearer."
        )
    ],
}

KNOWLEDGE_ORDER = ["medal", "converse", "fabricate", "reading", "backpack", "craft", "honesty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    award = f["award"]
    child = f["child"]
    helper = f["helper"]
    material = f["material"]
    if f["outcome"] == "found":
        return [
            f'Write a short slice-of-life story for ages 3 to 5 that uses the words "converse", "medal", and "fabricate".',
            f"Tell a story where {child.id} cannot find a {award.medal_name}, wants to fabricate one from {material.label}, but a calm talk leads to a twist ending where the real medal is found.",
            f'Write a gentle home story with repetition and dialogue, where the line "Not here. Not there. Where is my medal?" appears before a warm twist.'
        ]
    return [
        f'Write a short slice-of-life story for ages 3 to 5 that uses the words "converse", "medal", and "fabricate".',
        f"Tell a story where {child.id} wants to fabricate a missing medal, but {helper.id} helps {child.pronoun('object')} tell the truth instead.",
        f'Write a gentle dialogue story with repetition where a child learns that honesty can shine even without the missing prize.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    award = f["award"]
    material = f["material"]
    correct_place = PLACES[f["correct_place"]]
    out = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who earned a {award.medal_name}, and {helper.id}, who stayed close and helped. The story happens during a small morning rush before school."
        ),
        (
            "Why was the child upset?",
            f"{child.id} wanted to bring the medal to school, but it was missing when it was time to leave. That made the morning feel tight and worried."
        ),
        (
            "What words did they keep saying while they searched?",
            'They repeated, "Not here. Not there. Where is my medal?" The repeated line shows how the worry kept circling in the child\'s head.'
        ),
        (
            f"Why did {child.id} think about trying to fabricate a medal?",
            f"{child.pronoun('subject').capitalize()} was afraid of arriving at school without the prize {child.pronoun()} had earned. The craft drawer looked like a quick answer, even though it would not be the real medal."
        ),
        (
            f"How did talking help in the story?",
            f"{helper.id} asked {child.id} to slow down and converse about the very last moment with the medal. That calm talk lowered the rush and helped memory do its work."
        ),
    ]
    if f["outcome"] == "found":
        out.append(
            (
                "What was the twist at the end?",
                f"The real medal was in {correct_place.phrase} all along. Once {child.id} remembered the last thing {child.pronoun()} had done, the search changed and the medal appeared."
            )
        )
        out.append(
            (
                f"Why didn't {child.id} need the craft supplies in the end?",
                f"{child.pronoun('subject').capitalize()} nearly used {material.label} to make a stand-in, but the real medal was found first. The ending shows that remembering and telling the truth solved the problem better than pretending."
            )
        )
    else:
        out.append(
            (
                "Did they use the fake medal as if it were real?",
                f"No. They made a practice craft, but they did not pretend it was the real prize. That mattered because {helper.id} wanted honesty to come before show-and-tell."
            )
        )
        out.append(
            (
                "How did the story end if the medal was still missing?",
                f"{child.id} went to school without the real medal but with a brave, truthful voice. The change at the end is that {child.pronoun()} felt steadier and chose honesty over hiding the problem."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"medal", "converse", "fabricate", "craft", "honesty"}
    tags |= set(f["award"].tags)
    if f["award"].true_place == "backpack":
        tags.add("backpack")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE.get(tag, []))
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
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  searched_places: {world.facts.get('searched_places', [])}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment",
        award="reading",
        material="foil_cardboard",
        helper="grandmother",
        child_name="Mina",
        child_type="girl",
        helper_name="Grandma",
        minutes_left=2,
    ),
    StoryParams(
        setting="house",
        award="music",
        material="paper_crayon",
        helper="mother",
        child_name="Owen",
        child_type="boy",
        helper_name="Mom",
        minutes_left=1,
    ),
    StoryParams(
        setting="house",
        award="garden",
        material="clay_paint",
        helper="father",
        child_name="Lila",
        child_type="girl",
        helper_name="Dad",
        minutes_left=3,
    ),
    StoryParams(
        setting="cottage",
        award="running",
        material="foil_cardboard",
        helper="brother",
        child_name="Max",
        child_type="boy",
        helper_name="Ben",
        minutes_left=2,
    ),
]


ASP_RULES = r"""
valid(S, A, M) :- setting(S), award(A), material(M),
                  true_place(A, P), has_spot(S, P),
                  available(S, M), sensible_material(M).

sensible_material(M) :- material(M), craft_score(M, C), craft_min(K), C >= K.

found :- helper(H), patience(H, P), minutes_left(T), P + T >= 5.
outcome(found) :- found.
outcome(honest_without_medal) :- not found.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.spots):
            lines.append(asp.fact("has_spot", sid, spot))
        for material in sorted(setting.materials):
            lines.append(asp.fact("available", sid, material))
    for aid, award in AWARDS.items():
        lines.append(asp.fact("award", aid))
        lines.append(asp.fact("true_place", aid, award.true_place))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        lines.append(asp.fact("craft_score", mid, material.craft_score))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper_kind", hid))
        lines.append(asp.fact("patience", hid, helper.patience))
    lines.append(asp.fact("craft_min", CRAFT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    program = "\n".join(
        [
            asp.fact("helper", params.helper),
            asp.fact("minutes_left", params.minutes_left),
        ]
    )
    model = asp.one_model(asp_program(program, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("  clingo only:", sorted(set(asp_valid_combos()) - set(valid_combos())))
        print("  python only:", sorted(set(valid_combos()) - set(asp_valid_combos())))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: random resolution failed for seed {seed}.")
            break

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
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a missing medal, a tempted craft fix, and a remembering conversation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--award", choices=AWARDS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES, help="explicit true place; must match the chosen award")
    ap.add_argument("--minutes-left", type=int, choices=[0, 1, 2, 3], dest="minutes_left")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.award and args.place:
        if AWARDS[args.award].true_place != args.place:
            raise StoryError(
                f"(No story: the {AWARDS[args.award].medal_name} was not last left in {PLACES[args.place].phrase}. "
                f"It belongs with {PLACES[AWARDS[args.award].true_place].phrase} instead.)"
            )
    if args.material and not material_sensible(MATERIALS[args.material]):
        raise StoryError(explain_material(MATERIALS[args.material]))
    if args.setting and args.award and not place_compatible(SETTINGS[args.setting], AWARDS[args.award]):
        raise StoryError(explain_place(SETTINGS[args.setting], AWARDS[args.award]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.award is None or combo[1] == args.award)
        and (args.material is None or combo[2] == args.material)
        and (args.place is None or AWARDS[combo[1]].true_place == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, award_id, material_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or {
        "mother": "Mom",
        "father": "Dad",
        "grandmother": "Grandma",
        "brother": rng.choice(BOY_NAMES),
    }[helper_id]
    minutes_left = args.minutes_left if args.minutes_left is not None else rng.choice([0, 1, 2, 3])

    return StoryParams(
        setting=setting_id,
        award=award_id,
        material=material_id,
        helper=helper_id,
        child_name=child_name,
        child_type=gender,
        helper_name=helper_name,
        minutes_left=minutes_left,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting: {params.setting}")
    if params.award not in AWARDS:
        raise StoryError(f"Unknown award: {params.award}")
    if params.material not in MATERIALS:
        raise StoryError(f"Unknown material: {params.material}")
    if params.helper not in HELPERS:
        raise StoryError(f"Unknown helper: {params.helper}")

    setting = SETTINGS[params.setting]
    award = AWARDS[params.award]
    material = MATERIALS[params.material]
    helper_cfg = HELPERS[params.helper]

    if not place_compatible(setting, award):
        raise StoryError(explain_place(setting, award))
    if not material_sensible(material):
        raise StoryError(explain_material(material))

    wrong_places = [pid for pid in sorted(setting.spots) if pid != award.true_place]
    search_order = wrong_places[:3] if wrong_places else []
    world = tell(
        setting=setting,
        award=award,
        material=material,
        helper_cfg=helper_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        minutes_left=params.minutes_left,
        search_order=search_order,
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
        print(f"{len(combos)} compatible (setting, award, material) combos:\n")
        for setting, award, material in combos:
            print(f"  {setting:10} {award:8} {material}")
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
            header = f"### {p.child_name}: {p.award} medal in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
