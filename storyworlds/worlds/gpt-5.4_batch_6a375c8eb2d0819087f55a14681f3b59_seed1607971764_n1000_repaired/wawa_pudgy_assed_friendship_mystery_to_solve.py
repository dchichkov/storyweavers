#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py
============================================================================

A standalone storyworld about two friends in a folk-tale village who must solve
a small mystery: something needed for a celebration has gone missing. The world
models why the thing vanished, what clues were left behind, whether the friends
keep trusting each other while they search, and whether they solve the mystery
themselves or need a gentle hint from old Assed.

Run it
------
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --setting willow_pond --item lantern
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --helper mouse --hideout cart
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --json
    python storyworlds/worlds/gpt-5.4/wawa_pudgy_assed_friendship_mystery_to_solve.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose", "duck"}
        male = {"boy", "father", "man", "donkey"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    place: str
    festival: str
    weather: str
    path_text: str
    hideouts: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    size: int
    risk: str
    use_text: str
    open_spot: str
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
    carry: int
    clue: str
    trail: str
    reason: str
    hideouts: set[str] = field(default_factory=set)
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
class Hideout:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    trace: str = ""
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


def _r_item_safe(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    helper = world.get("helper")
    if item.meters["moved"] < THRESHOLD:
        return out
    sig = ("safe",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["hidden"] += 1
    item.meters["safe"] += 1
    helper.memes["care"] += 1
    out.append("__moved__")
    return out


def _r_search_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    for eid in ("wawa", "pudgy"):
        friend = world.get(eid)
        if item.meters["missing"] >= THRESHOLD and friend.memes["searching"] >= THRESHOLD:
            sig = ("worry", eid)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            friend.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [
    Rule(name="item_safe", tag="physical", apply=_r_item_safe),
    Rule(name="search_worry", tag="emotional", apply=_r_search_worry),
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


def valid_combo(setting: Setting, item: LostItem, helper: Helper, hideout: Hideout) -> bool:
    return (
        helper.carry >= item.size
        and item.risk in hideout.protects
        and hideout.id in setting.hideouts
        and hideout.id in helper.hideouts
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for helper_id, helper in HELPERS.items():
                for hideout_id, hideout in HIDEOUTS.items():
                    if valid_combo(setting, item, helper, hideout):
                        combos.append((setting_id, item_id, helper_id, hideout_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "self_solved" if params.trust + params.patience >= 12 else "hint_solved"


def explain_rejection(setting: Optional[Setting], item: Optional[LostItem],
                      helper: Optional[Helper], hideout: Optional[Hideout]) -> str:
    if setting and hideout and hideout.id not in setting.hideouts:
        return (
            f"(No story: {hideout.phrase} is not part of {setting.place}, so the clue trail "
            f"could not honestly lead there.)"
        )
    if helper and hideout and hideout.id not in helper.hideouts:
        return (
            f"(No story: {helper.label.capitalize()} would not tuck something into {hideout.phrase}. "
            f"The hiding place does not fit that helper's habits.)"
        )
    if item and helper and helper.carry < item.size:
        return (
            f"(No story: {helper.label.capitalize()} is too small to carry {item.phrase}. "
            f"Pick a lighter item or a stronger helper.)"
        )
    if item and hideout and item.risk not in hideout.protects:
        return (
            f"(No story: {hideout.phrase} would not protect {item.phrase} from {item.risk}. "
            f"The hiding place must solve the real problem.)"
        )
    return "(No story: this combination does not form a reasonable mystery.)"


def predict_move(world: World) -> dict:
    sim = world.copy()
    item = sim.get("item")
    item.meters["moved"] += 1
    item.meters["missing"] += 1
    propagate(sim, narrate=False)
    return {
        "missing": item.meters["missing"] >= THRESHOLD,
        "safe": item.meters["safe"] >= THRESHOLD,
    }


def clue_round(world: World, place_text: str, clue_text: str, trail_text: str) -> None:
    wawa = world.get("wawa")
    pudgy = world.get("pudgy")
    item = world.get("item")
    wawa.memes["searching"] += 1
    pudgy.memes["searching"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They searched {place_text}. There Wawa found {clue_text}, and Pudgy found {trail_text}."
    )
    world.facts["clues"].append(clue_text)
    world.facts["clues"].append(trail_text)
    item.meters["clues_found"] += 2
    wawa.memes["hope"] += 1
    pudgy.memes["hope"] += 1


def introduce(world: World, wawa: Entity, pudgy: Entity, assed: Entity,
              item: LostItem) -> None:
    wawa.memes["friendship"] += 1
    pudgy.memes["friendship"] += 1
    world.say(
        f"In the days when reeds whispered and mill wheels answered them, Wawa the duck "
        f"and Pudgy the hedgehog lived beside {world.setting.place}."
    )
    world.say(
        f"Wawa was quick of eye, and Pudgy was a little pudgy and slow of step, but his "
        f"heart stayed steady. Old Assed the donkey watched the lane from his shady post "
        f"and said the two friends were as good together as a lamp and its flame."
    )
    world.say(
        f"On the morning of {world.setting.festival}, the village needed {item.phrase}, "
        f"for {item.use_text}."
    )


def disappearance(world: World, item: LostItem, helper: Helper, hideout: Hideout) -> None:
    world.get("item").meters["moved"] += 1
    world.get("item").meters["missing"] += 1
    propagate(world, narrate=False)
    pred = predict_move(world)
    world.facts["predicted_missing"] = pred["missing"]
    world.facts["predicted_safe"] = pred["safe"]
    world.say(
        f"But when Wawa went to {item.open_spot}, the place was empty. Only the morning air "
        f"stirred there, and the little village drew one long breath."
    )
    world.say(
        f'"Where has it gone?" asked Wawa. Pudgy looked at the bare spot and felt his small '
        f"spines prickle. Even Assed lifted his long ears, for it was a true mystery to solve."
    )
    world.facts["motive_text"] = (
        f"{helper.label.capitalize()} had carried it away to {hideout.phrase} because {helper.reason}."
    )


def promise_search(world: World) -> None:
    wawa = world.get("wawa")
    pudgy = world.get("pudgy")
    wawa.memes["loyalty"] += 1
    pudgy.memes["loyalty"] += 1
    world.say(
        '"We will not let the day grow sad," said Wawa. "We will follow what the world tells us."'
    )
    world.say(
        '"And we will follow it together," said Pudgy, brushing dust from his round little paws.'
    )


def mild_doubt(world: World) -> None:
    wawa = world.get("wawa")
    pudgy = world.get("pudgy")
    wawa.memes["friction"] += 1
    pudgy.memes["friction"] += 1
    world.say(
        "As they searched, Wawa hurried ahead and Pudgy lagged behind. For a blink they almost "
        "grew cross with one another, because worry can make even kind friends speak too fast."
    )
    world.say(
        'Then Pudgy said, "Let us not lose each other while we look for the lost thing," and '
        "Wawa's feathers settled at once."
    )
    wawa.memes["trust"] += 1
    pudgy.memes["trust"] += 1


def assed_hint(world: World, helper: Helper, hideout: Hideout) -> None:
    assed = world.get("assed")
    assed.memes["wisdom"] += 1
    world.say(
        f'Old Assed stamped once and said, "A thing does not walk away by itself. Ask who would '
        f'carry it, and ask who wished it no harm."'
    )
    world.say(
        f"Then he pointed his nose toward {hideout.phrase}, where the ground held {hideout.trace}."
    )
    world.facts["hint_text"] = (
        f'Assed told them to think about who could carry the item kindly, then pointed toward {hideout.phrase}.'
    )
    world.facts["helper_guess"] = helper.label


def self_realization(world: World, helper: Helper, hideout: Hideout) -> None:
    world.say(
        f"Wawa stopped beside the path and looked again. {helper.clue.capitalize()} lay there, "
        f"and beside it ran {helper.trail}."
    )
    world.say(
        f'"This was no thief\'s work," said Pudgy. "Someone careful carried it toward {hideout.phrase}."'
    )
    world.facts["helper_guess"] = helper.label


def discovery(world: World, item: LostItem, helper: Helper, hideout: Hideout) -> None:
    item_ent = world.get("item")
    helper_ent = world.get("helper")
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    item_ent.meters["safe"] += 1
    helper_ent.memes["shy"] += 1
    world.say(
        f"They came at last to {hideout.phrase}. There, tucked safe inside, rested {item.phrase}."
    )
    world.say(
        f"Beside it stood {helper.label}, not wicked at all, only bright-eyed and bashful."
    )
    world.say(
        f'"I moved it because {helper.reason}," {helper.pronoun()} seemed to say with {helper.pronoun("possessive")} '
        f"small, honest face."
    )
    world.facts["found_place"] = hideout.phrase
    world.facts["reason_text"] = helper.reason


def resolution(world: World, item: LostItem) -> None:
    wawa = world.get("wawa")
    pudgy = world.get("pudgy")
    helper = world.get("helper")
    assed = world.get("assed")
    wawa.memes["relief"] += 1
    pudgy.memes["relief"] += 1
    wawa.memes["friendship"] += 1
    pudgy.memes["friendship"] += 1
    helper.memes["relief"] += 1
    assed.memes["pride"] += 1
    world.say(
        f"Wawa laughed first, and then Pudgy laughed too, until the worry fell away like chaff in wind."
    )
    world.say(
        f"They thanked {helper.label} for meaning well, carried {item.label} back together, and told the village "
        f"the whole truth."
    )
    world.say(
        f"So {world.setting.festival} began with bright faces after all, and from that day on Wawa and Pudgy "
        f"trusted each other even when the world looked puzzling. Old Assed blinked in the sun, and the tale "
        f"said that friendship is the best lantern for any mystery road."
    )


@dataclass
class StoryParams:
    setting: str
    item: str
    helper: str
    hideout: str
    trust: int = 7
    patience: int = 7
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


def tell(setting: Setting, item: LostItem, helper: Helper, hideout: Hideout,
         trust: int = 7, patience: int = 7) -> World:
    world = World(setting)
    wawa = world.add(Entity(id="wawa", kind="character", type="duck", label="Wawa", role="friend"))
    pudgy = world.add(Entity(id="pudgy", kind="character", type="hedgehog", label="Pudgy", role="friend"))
    assed = world.add(Entity(id="assed", kind="character", type="donkey", label="Assed", role="elder"))
    item_ent = world.add(Entity(id="item", kind="thing", type=item.id, label=item.label, role="lost_item"))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.id, label=helper.label, role="helper"))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", label=setting.place, role="setting"))

    wawa.memes["trust"] = float(trust)
    pudgy.memes["trust"] = float(trust)
    wawa.memes["patience"] = float(patience)
    pudgy.memes["patience"] = float(patience)
    item_ent.meters["missing"] = 0.0
    item_ent.meters["moved"] = 0.0
    item_ent.meters["safe"] = 0.0
    item_ent.meters["clues_found"] = 0.0

    world.facts.update(
        setting=setting,
        item_cfg=item,
        helper_cfg=helper,
        hideout_cfg=hideout,
        clues=[],
        hint_text="",
        helper_guess="",
        found_place="",
        reason_text="",
        motive_text="",
    )

    introduce(world, wawa, pudgy, assed, item)
    world.para()
    disappearance(world, item, helper, hideout)
    promise_search(world)
    world.para()

    clue_round(
        world,
        place_text=item.open_spot,
        clue_text=helper.clue,
        trail_text=helper.trail,
    )

    if outcome_of(StoryParams(
        setting=setting.id,
        item=item.id,
        helper=helper.id,
        hideout=hideout.id,
        trust=trust,
        patience=patience,
        seed=None,
    )) == "hint_solved":
        mild_doubt(world)
        world.para()
        assed_hint(world, helper, hideout)
    else:
        world.para()
        self_realization(world, helper, hideout)

    world.para()
    discovery(world, item, helper, hideout)
    resolution(world, item)

    world.facts.update(
        wawa=wawa,
        pudgy=pudgy,
        assed=assed,
        helper=helper_ent,
        item=item_ent,
        place=place_ent,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            item=item.id,
            helper=helper.id,
            hideout=hideout.id,
            trust=trust,
            patience=patience,
            seed=None,
        )),
        trust=trust,
        patience=patience,
    )
    return world


SETTINGS = {
    "willow_pond": Setting(
        id="willow_pond",
        place="the willow pond",
        festival="the Lantern Waking",
        weather="misty",
        path_text="a silver path between reeds",
        hideouts={"reed_nest", "cart"},
        tags={"pond", "festival"},
    ),
    "fern_glen": Setting(
        id="fern_glen",
        place="the fern glen",
        festival="the Bell Circle",
        weather="drizzly",
        path_text="a soft path under ferns",
        hideouts={"stump", "reed_nest"},
        tags={"glen", "festival"},
    ),
    "mill_yard": Setting(
        id="mill_yard",
        place="the mill yard",
        festival="the First Bread Dance",
        weather="windy",
        path_text="a dusty path by the wheel",
        hideouts={"cart", "stump"},
        tags={"mill", "festival"},
    ),
}

ITEMS = {
    "lantern": LostItem(
        id="lantern",
        label="lantern",
        phrase="the blue festival lantern",
        size=2,
        risk="rain",
        use_text="its soft light was to be hung above the singers",
        open_spot="the hook beside the water gate",
        tags={"lantern", "rain"},
    ),
    "bell_ribbon": LostItem(
        id="bell_ribbon",
        label="bell ribbon",
        phrase="the red bell ribbon",
        size=1,
        risk="wind",
        use_text="it was to be tied on the old bell rope",
        open_spot="the flat stone near the bell post",
        tags={"ribbon", "wind"},
    ),
    "seed_cake": LostItem(
        id="seed_cake",
        label="seed cake",
        phrase="the round seed cake",
        size=1,
        risk="rain",
        use_text="it was to be set on the sharing table",
        open_spot="the cool sill by the kitchen door",
        tags={"cake", "rain"},
    ),
}

HELPERS = {
    "magpie": Helper(
        id="magpie",
        label="the magpie",
        carry=2,
        clue="a shining black feather",
        trail="small hopping prints in the dust",
        reason="the weather smelled wet, and it wished to keep the pretty thing dry",
        hideouts={"cart", "stump"},
        tags={"bird", "feather"},
    ),
    "mouse": Helper(
        id="mouse",
        label="the field mouse",
        carry=1,
        clue="a neat little nibble in a fallen oat",
        trail="tiny quick tracks like stitched thread",
        reason="the drizzle was coming on, and it wished to keep the food from spoiling",
        hideouts={"stump", "cart"},
        tags={"mouse", "tracks"},
    ),
    "otter": Helper(
        id="otter",
        label="the otter",
        carry=2,
        clue="a smooth wet paw mark",
        trail="dragged reed tips leading off the bank",
        reason="it thought the wind and rain would trouble the thing where it lay",
        hideouts={"reed_nest"},
        tags={"otter", "paw"},
    ),
}

HIDEOUTS = {
    "reed_nest": Hideout(
        id="reed_nest",
        label="reed nest",
        phrase="a dry reed nest under the bank",
        protects={"rain"},
        trace="bent reeds and a soft hollow",
        tags={"reeds", "shelter"},
    ),
    "stump": Hideout(
        id="stump",
        label="stump",
        phrase="the hollow stump under the fern hill",
        protects={"rain", "wind"},
        trace="crumbs and little scratches by the root",
        tags={"stump", "shelter"},
    ),
    "cart": Hideout(
        id="cart",
        label="cart",
        phrase="the old cart with one wheel sunk in moss",
        protects={"rain", "wind"},
        trace="a line of dust brushed under the axle",
        tags={"cart", "shelter"},
    ),
}

TRUST_VALUES = [3, 4, 5, 6, 7, 8]
PATIENCE_VALUES = [3, 4, 5, 6, 7, 8]


KNOWLEDGE = {
    "lantern": [
        (
            "What is a lantern?",
            "A lantern is a lamp with a cover around its light. People use it to carry or hang light safely.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a long strip of cloth used for tying or decorating things. Wind can whip a ribbon away if it is left loose.",
        )
    ],
    "cake": [
        (
            "Why should food be kept dry?",
            "Food should be kept dry because rain can make it soggy and spoil it. Dry food stays nicer to share and eat.",
        )
    ],
    "rain": [
        (
            "Why do animals hide things from rain?",
            "Rain can soak light things, food, and cloth. A dry hiding place protects them from getting spoiled or ruined.",
        )
    ],
    "wind": [
        (
            "Why can wind make small things disappear?",
            "Wind can lift, roll, or blow away small light things. That is why people tuck them into safe places.",
        )
    ],
    "tracks": [
        (
            "What can tracks tell you?",
            "Tracks can show who passed by and which way they went. Careful eyes can use them like a quiet kind of map.",
        )
    ],
    "friendship": [
        (
            "How can friendship help solve a problem?",
            "Friends notice different clues and help each other stay brave. When they listen to one another, they can solve harder problems together.",
        )
    ],
    "donkey": [
        (
            "Why do folk tales often have a wise old animal?",
            "A wise old animal can help younger characters slow down and think. The hint is small, but it helps the heroes see the answer for themselves.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lantern", "ribbon", "cake", "rain", "wind", "tracks", "friendship", "donkey"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    item = f["item_cfg"]
    outcome = f["outcome"]
    if outcome == "self_solved":
        return [
            f'Write a folk-tale story for a 3-to-5-year-old that includes the words "wawa", "pudgy", and "assed", and centers on friendship and a mystery to solve.',
            f"Tell a gentle village mystery where Wawa and Pudgy notice that {item.phrase} is missing at {setting.place}, follow clues, and solve it together.",
            f"Write a child-friendly folk tale in which two friends keep trusting each other while they search for a missing festival object and discover a kind reason for its disappearance.",
        ]
    return [
        f'Write a folk-tale story for a 3-to-5-year-old that includes the words "wawa", "pudgy", and "assed", and centers on friendship and a mystery to solve.',
        f"Tell a gentle village mystery where Wawa and Pudgy nearly lose heart while looking for {item.phrase}, but old Assed gives them a wise hint.",
        f"Write a simple folk tale about two friends solving a mystery with clues, kindness, and help from an elder who teaches them to think before they blame.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    setting = f["setting"]
    item = f["item_cfg"]
    helper_cfg = f["helper_cfg"]
    hideout = f["hideout_cfg"]
    outcome = f["outcome"]
    clues = f["clues"]

    qa: list[tuple[str, str]] = [
        (
            "Who are the main friends in the story?",
            "The main friends are Wawa and Pudgy. Wawa is quick and Pudgy is slow and round, but they stay loyal to each other.",
        ),
        (
            f"What mystery did they have to solve at {setting.place}?",
            f"They had to find out what happened to {item.phrase}. The village needed it for {item.use_text}.",
        ),
        (
            "What clues did they follow?",
            f"They followed clues from the world around them: {clues[0]} and {clues[1]}. Those clues showed that a small animal had carried the missing thing away instead of a thief stealing it.",
        ),
        (
            f"Why was {item.phrase} missing?",
            f"It was missing because {helper_cfg.label} moved it to {hideout.phrase}. {helper_cfg.label.capitalize()} was trying to keep it safe because {helper_cfg.reason}.",
        ),
    ]
    if outcome == "hint_solved":
        qa.append(
            (
                "How did Assed help them solve the mystery?",
                f'Assed did not give the whole answer away. He reminded them to ask who could carry the item kindly, and that hint helped them look toward {hideout.phrase}.',
            )
        )
    else:
        qa.append(
            (
                "How did Wawa and Pudgy solve the mystery themselves?",
                f"They slowed down and looked carefully at the clues instead of blaming anyone. Because they trusted each other, they understood that the trail led toward {hideout.phrase}.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The friends found {item.phrase} safe in {hideout.phrase} and brought it back together. The festival could begin, and their friendship felt stronger because they had solved the mystery kindly.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["item_cfg"].tags) | set(f["helper_cfg"].tags) | {"friendship", "donkey", "tracks"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="willow_pond",
        item="lantern",
        helper="otter",
        hideout="reed_nest",
        trust=8,
        patience=7,
        seed=101,
    ),
    StoryParams(
        setting="fern_glen",
        item="bell_ribbon",
        helper="magpie",
        hideout="stump",
        trust=6,
        patience=6,
        seed=102,
    ),
    StoryParams(
        setting="mill_yard",
        item="seed_cake",
        helper="mouse",
        hideout="cart",
        trust=4,
        patience=4,
        seed=103,
    ),
    StoryParams(
        setting="mill_yard",
        item="bell_ribbon",
        helper="magpie",
        hideout="cart",
        trust=3,
        patience=5,
        seed=104,
    ),
]


ASP_RULES = r"""
valid(S, I, H, D) :- setting(S), item(I), helper(H), hideout(D),
                     carry(H, C), size(I, Z), C >= Z,
                     risk(I, R), protects(D, R),
                     setting_has(S, D),
                     helper_uses(H, D).

total(T) :- trust(V), patience(P), T = V + P.
outcome(self_solved) :- total(T), T >= 12.
outcome(hint_solved) :- total(T), T < 12.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hid in sorted(setting.hideouts):
            lines.append(asp.fact("setting_has", sid, hid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("size", iid, item.size))
        lines.append(asp.fact("risk", iid, item.risk))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("carry", hid, helper.carry))
        for place in sorted(helper.hideouts):
            lines.append(asp.fact("helper_uses", hid, place))
    for did, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", did))
        for risk in sorted(hideout.protects):
            lines.append(asp.fact("protects", did, risk))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("trust", params.trust),
        asp.fact("patience", params.patience),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Wawa, Pudgy, Assed, friendship, and a small mystery to solve."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--trust", type=int, choices=TRUST_VALUES)
    ap.add_argument("--patience", type=int, choices=PATIENCE_VALUES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = SETTINGS.get(args.setting) if args.setting else None
    item = ITEMS.get(args.item) if args.item else None
    helper = HELPERS.get(args.helper) if args.helper else None
    hideout = HIDEOUTS.get(args.hideout) if args.hideout else None

    if setting and item and helper and hideout and not valid_combo(setting, item, helper, hideout):
        raise StoryError(explain_rejection(setting, item, helper, hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.helper is None or combo[2] == args.helper)
        and (args.hideout is None or combo[3] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, helper_id, hideout_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=setting_id,
        item=item_id,
        helper=helper_id,
        hideout=hideout_id,
        trust=args.trust if args.trust is not None else rng.choice(TRUST_VALUES),
        patience=args.patience if args.patience is not None else rng.choice(PATIENCE_VALUES),
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")

    setting = SETTINGS[params.setting]
    item = ITEMS[params.item]
    helper = HELPERS[params.helper]
    hideout = HIDEOUTS[params.hideout]
    if not valid_combo(setting, item, helper, hideout):
        raise StoryError(explain_rejection(setting, item, helper, hideout))

    world = tell(
        setting=setting,
        item=item,
        helper=helper,
        hideout=hideout,
        trust=params.trust,
        patience=params.patience,
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
        print(f"{len(combos)} compatible (setting, item, helper, hideout) combos:\n")
        for setting, item, helper, hideout in combos:
            print(f"  {setting:12} {item:11} {helper:7} {hideout}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.setting}: {p.item} moved by {p.helper} to {p.hideout} "
                f"({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
