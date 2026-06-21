#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py
=============================================================================

A standalone story world for a tiny superhero tale: a child takes on a quiet
quest to find a sleepy toddler's missing comfort item without making enough
noise to waken the napper. The world is driven by a small physical/emotional
simulation: search tools fit some hiding places and not others, rushing creates
noise, noise can wake the toddler, and the ending image proves what lesson the
hero learned.

Features from the seed:
- includes the words "look" and "waken"
- superhero style
- a quest
- a rhyme used inside the story world
- a clear lesson learned

Run it
------
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py --spot closet_shelf --tool flashlight_stool
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py --spot under_couch --tool step_stool
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py --all
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/look_waken_lesson_learned_quest_rhyme_superhero.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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


@dataclass
class Setting:
    id: str
    home: str
    hero_view: str
    nap_place: str
    affords: set[str] = field(default_factory=set)
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
class LostItem:
    id: str
    label: str
    phrase: str
    soothe_text: str
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
class Spot:
    id: str
    label: str
    phrase: str
    room_text: str
    clue: str
    needs: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    abilities: set[str] = field(default_factory=set)
    bulky: bool = False
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
class HeroMode:
    id: str
    title: str
    boast: str
    ending_pose: str
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
class StoryParams:
    setting: str
    item: str
    spot: str
    tool: str
    mode: str
    hero_name: str
    hero_gender: str
    toddler_name: str
    toddler_gender: str
    parent: str
    pace: str = "careful"
    sleep_depth: int = 2
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


def _r_noise_wakens(world: World) -> list[str]:
    toddler = world.get("toddler")
    room = world.get("room")
    if toddler.meters["asleep"] < THRESHOLD:
        return []
    if room.meters["noise"] <= world.facts["sleep_depth"]:
        return []
    sig = ("wakens", toddler.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toddler.meters["asleep"] = 0.0
    toddler.meters["awake"] = 1.0
    toddler.memes["startled"] += 1
    world.get("hero").memes["worry"] += 1
    world.get("parent").memes["hurry"] += 1
    return ["__wakened__"]


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["relief"] += 1
    world.get("hero").memes["hope"] += 1
    return []


def _r_returned_comfort(world: World) -> list[str]:
    item = world.get("item")
    toddler = world.get("toddler")
    if item.meters["returned"] < THRESHOLD:
        return []
    sig = ("comfort", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    toddler.memes["comfort"] += 1
    world.get("hero").memes["pride"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="noise_wakens", tag="physical", apply=_r_noise_wakens),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="returned_comfort", tag="social", apply=_r_returned_comfort),
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


SETTINGS = {
    "apartment": Setting(
        id="apartment",
        home="a bright little apartment",
        hero_view="Every hallway looked like a secret base corridor.",
        nap_place="the tiny bedroom at the end of the hall",
        affords={"under_couch", "closet_shelf", "laundry_basket"},
    ),
    "house": Setting(
        id="house",
        home="a cozy little house",
        hero_view="Every doorway looked like an archway to a mission room.",
        nap_place="the sunny room beside the stairs",
        affords={"under_couch", "closet_shelf", "porch_bench"},
    ),
    "duplex": Setting(
        id="duplex",
        home="a snug upstairs duplex",
        hero_view="Every room felt like one more corner of Hero Headquarters.",
        nap_place="the quiet room with the moon curtains",
        affords={"closet_shelf", "laundry_basket", "porch_bench"},
    ),
}

ITEMS = {
    "bunny": LostItem(
        id="bunny",
        label="bunny",
        phrase="a floppy bedtime bunny",
        soothe_text="nestled the bunny under one small arm",
        tags={"comfort", "bedtime"},
    ),
    "blanket": LostItem(
        id="blanket",
        label="blanket",
        phrase="a starry blue blanket",
        soothe_text="pulled the blanket up to a sleepy chin",
        tags={"comfort", "bedtime"},
    ),
    "dino": LostItem(
        id="dino",
        label="dino",
        phrase="a soft green dino",
        soothe_text="hugged the dino to a warm pajama shirt",
        tags={"comfort", "bedtime"},
    ),
}

SPOTS = {
    "under_couch": Spot(
        id="under_couch",
        label="under the couch",
        phrase="under the couch where the shadows gathered",
        room_text="the living room rug",
        clue="Only a narrow, dark gap showed beneath the couch.",
        needs={"low", "dark"},
        tags={"couch", "dark"},
    ),
    "closet_shelf": Spot(
        id="closet_shelf",
        label="on the closet shelf",
        phrase="on the high closet shelf behind a box of winter hats",
        room_text="the hall closet",
        clue="The shelf was high, and the back corner was dim.",
        needs={"high", "dark"},
        tags={"closet", "high", "dark"},
    ),
    "laundry_basket": Spot(
        id="laundry_basket",
        label="in the laundry basket",
        phrase="in the tall laundry basket under the folded towels",
        room_text="the laundry nook",
        clue="The basket was deep, but it was right at hand.",
        needs={"deep"},
        tags={"laundry"},
    ),
    "porch_bench": Spot(
        id="porch_bench",
        label="under the porch bench",
        phrase="under the porch bench beside one lonely rain boot",
        room_text="the front porch",
        clue="A small crack of daylight shone under the bench.",
        needs={"low"},
        tags={"porch"},
    ),
}

TOOLS = {
    "flashlight_hand": Tool(
        id="flashlight_hand",
        label="flashlight",
        phrase="a small flashlight",
        abilities={"dark", "low"},
        bulky=False,
        tags={"flashlight", "light"},
    ),
    "flashlight_stool": Tool(
        id="flashlight_stool",
        label="flashlight and step stool",
        phrase="a flashlight and a fold-out step stool",
        abilities={"dark", "high"},
        bulky=True,
        tags={"flashlight", "stool", "light"},
    ),
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="a fold-out step stool",
        abilities={"high"},
        bulky=True,
        tags={"stool"},
    ),
    "grabber": Tool(
        id="grabber",
        label="grabber claw",
        phrase="a long grabber claw",
        abilities={"low", "deep"},
        bulky=False,
        tags={"grabber"},
    ),
    "careful_hands": Tool(
        id="careful_hands",
        label="careful hands",
        phrase="nothing but careful hands and a quiet tiptoe",
        abilities={"deep", "low"},
        bulky=False,
        tags={"hands", "quiet"},
    ),
}

MODES = {
    "comet": HeroMode(
        id="comet",
        title="Comet Kid",
        boast="fast feet and a bright brave grin",
        ending_pose="with one hand on the cape and one finger at the lips",
    ),
    "moon": HeroMode(
        id="moon",
        title="Moon Mask",
        boast="a silver whisper-cape and sharp superhero eyes",
        ending_pose="like a moonlit guard at the bedroom door",
    ),
    "thunder": HeroMode(
        id="thunder",
        title="Captain Thunder-Soft",
        boast="a big brave heart and a promise to help",
        ending_pose="standing tall, but soft as a cloud",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Ruby"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TODDLER_GIRL_NAMES = ["Pip", "June", "Nina", "Tess", "Lulu"]
TODDLER_BOY_NAMES = ["Pip", "Oli", "Nico", "Toby", "Milo"]


def tool_fits(spot: Spot, tool: Tool) -> bool:
    return spot.needs.issubset(tool.abilities)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for spot_id in sorted(setting.affords):
            spot = SPOTS[spot_id]
            for tool_id, tool in TOOLS.items():
                if tool_fits(spot, tool):
                    combos.append((setting_id, spot_id, tool_id))
    return combos


def search_noise(tool: Tool, pace: str) -> int:
    if pace == "careful":
        return 0
    return 2 if tool.bulky else 1


def outcome_of(params: StoryParams) -> str:
    if params.setting not in SETTINGS or params.spot not in SPOTS or params.tool not in TOOLS:
        return "invalid"
    tool = TOOLS[params.tool]
    noise = search_noise(tool, params.pace)
    return "wakened" if noise > params.sleep_depth else "quiet"


def rhyme_for(mode: HeroMode) -> str:
    if mode.id == "moon":
        return "Look left, look right, look low, look high; a hero helps with a watchful eye."
    if mode.id == "thunder":
        return "Look slow, look near, look far, look through; a gentle hero knows what to do."
    return "Look low, look high, superhero eye; move soft, move smart, and bravely try."


def explain_rejection(setting_id: str, spot_id: str, tool_id: str) -> str:
    setting = SETTINGS[setting_id]
    spot = SPOTS[spot_id]
    tool = TOOLS[tool_id]
    if spot_id not in setting.affords:
        return (
            f"(No story: {spot.label} is not a place this home setup includes. "
            f"Pick a spot that belongs in {setting.home}.)"
        )
    missing = sorted(spot.needs - tool.abilities)
    return (
        f"(No story: {tool.label} cannot search {spot.label}. "
        f"The spot needs {missing}, so the hero would not honestly be able to finish the quest.)"
    )


def predict_search(setting: Setting, spot: Spot, tool: Tool, pace: str, sleep_depth: int) -> dict:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label="hero"))
    toddler = world.add(Entity(id="toddler", kind="character", type="girl", label="toddler"))
    parent = world.add(Entity(id="parent", kind="character", type="mother", label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the home"))
    item = world.add(Entity(id="item", type="toy", label="item"))
    toddler.meters["asleep"] = 1.0
    toddler.meters["awake"] = 0.0
    world.facts["sleep_depth"] = sleep_depth
    world.facts["pace"] = pace
    world.facts["predicted"] = True
    room.meters["noise"] = float(search_noise(tool, pace))
    if tool_fits(spot, tool):
        item.meters["found"] = 1.0
    propagate(world, narrate=False)
    return {
        "found": item.meters["found"] >= THRESHOLD,
        "wakened": toddler.meters["awake"] >= THRESHOLD,
        "noise": int(room.meters["noise"]),
    }


def introduce(world: World, hero: Entity, toddler: Entity, parent: Entity, mode: HeroMode) -> None:
    world.say(
        f"In {world.setting.home}, {hero.id} had tied a towel around {hero.pronoun('possessive')} shoulders "
        f"and declared that for the afternoon {hero.pronoun()} was {mode.title}, with {mode.boast}."
    )
    world.say(world.setting.hero_view)
    world.say(
        f"But in {world.setting.nap_place}, little {toddler.id} had finally fallen asleep while "
        f"{parent.label_word} rubbed a tired back."
    )


def missing_item(world: World, hero: Entity, toddler: Entity, parent: Entity, item_cfg: LostItem) -> None:
    hero.memes["care"] += 1
    toddler.memes["needs_item"] += 1
    world.say(
        f"There was one problem. {toddler.id}'s {item_cfg.label} was missing, and without {item_cfg.label} "
        f"{toddler.pronoun()} often popped awake again before the nap was settled."
    )
    world.say(
        f'"Can you help me find {toddler.id}\'s {item_cfg.label} without making enough noise to waken '
        f'{toddler.pronoun("object")}?" {hero.pronoun("possessive")} {parent.label_word} whispered.'
    )
    world.say(f'"A quest!" {hero.id} breathed, suddenly very still.')


def clue_and_rhyme(world: World, hero: Entity, parent: Entity, spot: Spot, mode: HeroMode) -> None:
    world.say(
        f"{parent.label_word.capitalize()} pointed toward {spot.room_text}. "
        f'"I had my last good look there," {parent.pronoun()} said. "{spot.clue}"'
    )
    line = rhyme_for(mode)
    world.facts["rhyme"] = line
    world.say(
        f'Then {parent.pronoun()} added a helper-rhyme in the softest voice: "{line}"'
    )
    hero.memes["focus"] += 1


def choose_tool(world: World, hero: Entity, tool: Tool) -> None:
    world.say(f"{hero.id} chose {tool.phrase} for the mission.")
    hero.attrs["tool"] = tool.id


def vow(world: World, hero: Entity, mode: HeroMode, pace: str) -> None:
    if pace == "hurried":
        hero.memes["rush"] += 1
        world.say(
            f'"{mode.title} will be back in a flash," {hero.id} whispered, and for one moment '
            f'{hero.pronoun("possessive")} knees wanted to race faster than {hero.pronoun("possessive")} thoughts.'
        )
    else:
        hero.memes["patience"] += 1
        world.say(
            f'{hero.id} pressed one hand to {hero.pronoun("possessive")} towel-cape and whispered, '
            f'"Slow feet, sharp eyes, quiet skies."'
        )


def search(world: World, hero: Entity, toddler: Entity, spot: Spot, tool: Tool, pace: str) -> None:
    room = world.get("room")
    item = world.get("item")
    room.meters["noise"] += float(search_noise(tool, pace))
    if pace == "hurried":
        if tool.bulky:
            world.say(
                f"{hero.id} hurried to {spot.room_text} with the {tool.label}, and the stool gave a little clack on the floor."
            )
        else:
            world.say(
                f"{hero.id} hurried to {spot.room_text}, breathing hard through a superhero grin."
            )
    else:
        world.say(
            f"{hero.id} tiptoed to {spot.room_text} and let the rhyme lead the way."
        )

    if tool_fits(spot, tool):
        world.say(
            f"{hero.pronoun().capitalize()} looked {spot.label} and soon found the missing {item.label} {spot.phrase}."
        )
        item.meters["found"] = 1.0
    else:
        world.say(
            f"{hero.pronoun().capitalize()} looked {spot.label}, but the tool could not reach where the {item.label} was hidden."
        )
    propagate(world, narrate=False)

    if toddler.meters["awake"] >= THRESHOLD:
        world.say(
            f"From {world.setting.nap_place} came a small rustle, then two blinking eyes. The noise had begun to waken {toddler.id}."
        )


def return_item(world: World, hero: Entity, toddler: Entity, parent: Entity, item_cfg: LostItem) -> None:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return
    if toddler.meters["awake"] >= THRESHOLD:
        world.say(
            f"{hero.id} hurried back with the {item_cfg.label}, and {parent.label_word} scooped {toddler.id} close."
        )
        world.say(
            f"The missing {item_cfg.label} still helped: {toddler.id} {item_cfg.soothe_text} and the crying shrank to a sleepy sniffle."
        )
    else:
        world.say(
            f"{hero.id} carried the {item_cfg.label} back as gently as if it were a glowing secret crystal."
        )
        world.say(
            f"{parent.label_word.capitalize()} tucked it beside {toddler.id}, who only sighed, {item_cfg.soothe_text}, and slept on."
        )
    item.meters["returned"] = 1.0
    propagate(world, narrate=False)


def lesson(world: World, hero: Entity, parent: Entity, toddler: Entity, mode: HeroMode) -> None:
    if toddler.meters["awake"] >= THRESHOLD:
        hero.memes["lesson"] += 1
        world.say(
            f"Later, when the room was calm again, {hero.id} looked at the cape puddled around {hero.pronoun('possessive')} feet."
        )
        world.say(
            f'"I thought heroes had to be fast," {hero.pronoun()} said. "{parent.label_word.capitalize()}, I should have looked more carefully first."'
        )
        world.say(
            f'{parent.label_word.capitalize()} kissed the top of {hero.pronoun("possessive")} head. '
            f'"Sometimes fast helps," {parent.pronoun()} said, "but today the brave part was being gentle enough not to waken someone who needed sleep."'
        )
    else:
        hero.memes["lesson"] += 1
        world.say(
            f"{parent.label_word.capitalize()} smiled at the quiet doorway. "
            f'"That was real superhero work," {parent.pronoun()} whispered. "You did not just run. You looked, listened, and helped."'
        )
        world.say(
            f'{hero.id} stood a little taller. "{mode.title} has learned something," {hero.pronoun()} said. '
            f'"The best heroes do not only move fast. They move wisely."'
        )


def ending(world: World, hero: Entity, toddler: Entity, mode: HeroMode) -> None:
    if toddler.meters["awake"] >= THRESHOLD:
        world.say(
            f"That evening, {hero.id} made a new superhero rule and sang it under {hero.pronoun('possessive')} breath: "
            f'"{world.facts["rhyme"]}"'
        )
        world.say(
            f"Next time {hero.pronoun()} would begin the quest with patient feet. Even {mode.title} could grow wiser."
        )
    else:
        world.say(
            f"When the hall was still again, {hero.id} took {mode.ending_pose}, guarding the nap like the smallest, kindest superhero in the city."
        )
        world.say(
            f"The towel-cape barely swished at all, and that was exactly how {hero.pronoun()} knew the quest was won."
        )


def tell(
    setting: Setting,
    item_cfg: LostItem,
    spot: Spot,
    tool: Tool,
    mode: HeroMode,
    hero_name: str,
    hero_gender: str,
    toddler_name: str,
    toddler_gender: str,
    parent_type: str,
    pace: str,
    sleep_depth: int,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name))
    toddler = world.add(Entity(id="toddler", kind="character", type=toddler_gender, label=toddler_name))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent"))
    room = world.add(Entity(id="room", type="room", label="the home"))
    item = world.add(Entity(id="item", type="comfort_item", label=item_cfg.label))
    hero.attrs["name"] = hero_name
    toddler.attrs["name"] = toddler_name
    parent.attrs["name"] = "Parent"
    toddler.meters["asleep"] = 1.0
    toddler.meters["awake"] = 0.0
    room.meters["noise"] = 0.0
    item.meters["found"] = 0.0
    item.meters["returned"] = 0.0
    world.facts["sleep_depth"] = sleep_depth
    world.facts["pace"] = pace
    world.facts["predicted"] = False

    introduce(world, hero, toddler, parent, mode)
    missing_item(world, hero, toddler, parent, item_cfg)

    world.para()
    clue_and_rhyme(world, hero, parent, spot, mode)
    choose_tool(world, hero, tool)
    vow(world, hero, mode, pace)

    world.para()
    pred = predict_search(setting, spot, tool, pace, sleep_depth)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_waken"] = pred["wakened"]
    search(world, hero, toddler, spot, tool, pace)
    return_item(world, hero, toddler, parent, item_cfg)

    world.para()
    lesson(world, hero, parent, toddler, mode)
    ending(world, hero, toddler, mode)

    world.facts.update(
        hero=hero,
        toddler=toddler,
        parent=parent,
        item_cfg=item_cfg,
        spot=spot,
        tool=tool,
        mode=mode,
        found=item.meters["found"] >= THRESHOLD,
        returned=item.meters["returned"] >= THRESHOLD,
        outcome="wakened" if toddler.meters["awake"] >= THRESHOLD else "quiet",
        setting_cfg=setting,
    )
    return world


KNOWLEDGE = {
    "comfort": [
        (
            "Why do some little children like to sleep with a special toy or blanket?",
            "A special toy or blanket can feel familiar and safe at bedtime. That steady feeling helps some children relax and settle down."
        )
    ],
    "bedtime": [
        (
            "Why do people try to keep things quiet during nap time?",
            "Quiet helps a sleepy body stay calm enough to rest. Loud sounds can break that calm and make someone wake too soon."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight for?",
            "A flashlight helps you see in dark places. It gives light without making a big, bright room light shine everywhere."
        )
    ],
    "stool": [
        (
            "What is a step stool used for?",
            "A step stool helps a person reach something up high. It should be used carefully so nobody trips or falls."
        )
    ],
    "grabber": [
        (
            "What does a grabber claw do?",
            "A grabber claw helps you reach or pull something without crawling all the way in. It is useful when an object is low or deep in a tight place."
        )
    ],
    "quiet": [
        (
            "Why can moving slowly help on a careful job?",
            "Moving slowly gives your eyes and hands more time to notice things. It can also keep you from making extra noise or mistakes."
        )
    ],
    "dark": [
        (
            "Why is it harder to find things in dark places?",
            "Dark places hide edges, colors, and corners from your eyes. That makes careful looking more important."
        )
    ],
}
KNOWLEDGE_ORDER = ["comfort", "bedtime", "dark", "flashlight", "stool", "grabber", "quiet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    toddler = f["toddler"]
    mode = f["mode"]
    item_cfg = f["item_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old that includes the words '
        f'"look" and "waken". The hero must go on a quiet quest to find a missing {item_cfg.label}.'
    )
    if outcome == "wakened":
        return [
            base,
            f"Tell a gentle cautionary story where {hero.attrs['name']} plays {mode.title} and tries to help {toddler.attrs['name']}, "
            f"but rushing makes enough noise to waken the toddler before the comfort item is returned.",
            'Write a superhero bedtime story with a rhyme and a lesson learned: real heroes do not only move fast; they also move wisely.',
        ]
    return [
        base,
        f"Tell a warm superhero story where {hero.attrs['name']} quietly helps sleeping {toddler.attrs['name']} by following a rhyme and searching carefully.",
        'Write a simple quest story with a soft superhero voice, a bedtime rhyme, and a lesson learned about careful helping.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    toddler = f["toddler"]
    parent = f["parent"]
    item_cfg = f["item_cfg"]
    spot = f["spot"]
    tool = f["tool"]
    mode = f["mode"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.attrs['name']}, who pretended to be {mode.title}, and little {toddler.attrs['name']}, who was trying to stay asleep for a nap."
        ),
        (
            "What was the quest?",
            f"The quest was to find {toddler.attrs['name']}'s missing {item_cfg.label} and bring it back without enough noise to waken {toddler.pronoun('object')}. "
            f"The whole problem mattered because the missing comfort item helped at nap time."
        ),
        (
            "What rhyme helped the hero?",
            f'The helper-rhyme was "{world.facts["rhyme"]}" It reminded {hero.attrs["name"]} to look carefully instead of only hurrying.'
        ),
        (
            f"Where was the {item_cfg.label} found?",
            f"It was found {spot.phrase}. That hiding place is why {tool.label} mattered on the quest."
        ),
    ]
    if outcome == "wakened":
        qa.append(
            (
                f"Why did {toddler.attrs['name']} wake up?",
                f"{toddler.attrs['name']} woke because {hero.attrs['name']} rushed during the search and made too much noise. "
                f"The world state shows the search noise rose higher than the nap's quiet limit, so the toddler began to waken."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.attrs['name']} learned that a real hero should not only be fast. "
                f"{hero.pronoun('subject').capitalize()} needed to look carefully and move gently when someone else needed rest."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.attrs['name']} keep the quest quiet?",
                f"{hero.pronoun('subject').capitalize()} used {tool.phrase} and moved carefully instead of rushing. "
                f"Because the search stayed quiet, {toddler.attrs['name']} kept sleeping while the missing {item_cfg.label} was returned."
            )
        )
        qa.append(
            (
                "What lesson did the hero learn?",
                f"{hero.attrs['name']} learned that wise helping is part of being brave. "
                f"Looking, listening, and moving gently solved the problem better than simply trying to be the fastest hero."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item_cfg"].tags) | set(world.facts["spot"].tags) | set(world.facts["tool"].tags)
    if world.facts["pace"] == "careful":
        tags.add("quiet")
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
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: pace={world.facts.get('pace')} sleep_depth={world.facts.get('sleep_depth')} outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="apartment",
        item="bunny",
        spot="under_couch",
        tool="flashlight_hand",
        mode="comet",
        hero_name="Lily",
        hero_gender="girl",
        toddler_name="Pip",
        toddler_gender="boy",
        parent="mother",
        pace="careful",
        sleep_depth=1,
    ),
    StoryParams(
        setting="house",
        item="blanket",
        spot="closet_shelf",
        tool="flashlight_stool",
        mode="moon",
        hero_name="Max",
        hero_gender="boy",
        toddler_name="June",
        toddler_gender="girl",
        parent="father",
        pace="hurried",
        sleep_depth=1,
    ),
    StoryParams(
        setting="duplex",
        item="dino",
        spot="laundry_basket",
        tool="careful_hands",
        mode="thunder",
        hero_name="Ava",
        hero_gender="girl",
        toddler_name="Milo",
        toddler_gender="boy",
        parent="mother",
        pace="careful",
        sleep_depth=2,
    ),
    StoryParams(
        setting="house",
        item="bunny",
        spot="porch_bench",
        tool="grabber",
        mode="moon",
        hero_name="Theo",
        hero_gender="boy",
        toddler_name="Lulu",
        toddler_gender="girl",
        parent="father",
        pace="careful",
        sleep_depth=1,
    ),
    StoryParams(
        setting="apartment",
        item="blanket",
        spot="closet_shelf",
        tool="flashlight_stool",
        mode="comet",
        hero_name="Ruby",
        hero_gender="girl",
        toddler_name="Oli",
        toddler_gender="boy",
        parent="mother",
        pace="hurried",
        sleep_depth=0,
    ),
]

ASP_RULES = r"""
% --- world compatibility gate ----------------------------------------------
valid(Setting, Spot, Tool) :- affords(Setting, Spot), tool(Tool),
                              need(Spot, Need) : need(Spot, Need), ability(Tool, Need).

% --- outcome model ----------------------------------------------------------
noise(Tool, careful, 0) :- tool(Tool).
noise(Tool, hurried, 2) :- bulky(Tool).
noise(Tool, hurried, 1) :- tool(Tool), not bulky(Tool).

wakened :- chosen_tool(Tool), chosen_pace(Pace), chosen_sleep_depth(Depth),
           noise(Tool, Pace, N), N > Depth.

outcome(quiet) :- not wakened.
outcome(wakened) :- wakened.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot_id in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, spot_id))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for need in sorted(spot.needs):
            lines.append(asp.fact("need", spot_id, need))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for ability in sorted(tool.abilities):
            lines.append(asp.fact("ability", tool_id, ability))
        if tool.bulky:
            lines.append(asp.fact("bulky", tool_id))
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
            asp.fact("chosen_tool", params.tool),
            asp.fact("chosen_pace", params.pace),
            asp.fact("chosen_sleep_depth", params.sleep_depth),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(60):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome cases differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a quiet superhero quest to find a missing bedtime comfort item."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mode", choices=MODES)
    ap.add_argument("--pace", choices=["careful", "hurried"])
    ap.add_argument("--sleep-depth", type=int, choices=[0, 1, 2], dest="sleep_depth")
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--toddler-name")
    ap.add_argument("--toddler-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, spot, tool) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, toddler: bool = False, avoid: str = "") -> str:
    if toddler:
        pool = TODDLER_GIRL_NAMES if gender == "girl" else TODDLER_BOY_NAMES
    else:
        pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.spot and args.tool:
        if (args.setting, args.spot, args.tool) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.setting, args.spot, args.tool))
    if args.setting and args.spot and args.spot not in SETTINGS[args.setting].affords:
        chosen_tool = args.tool or next(iter(TOOLS))
        raise StoryError(explain_rejection(args.setting, args.spot, chosen_tool))
    if args.spot and args.tool and not tool_fits(SPOTS[args.spot], TOOLS[args.tool]):
        setting_id = args.setting or next(sid for sid, s in SETTINGS.items() if args.spot in s.affords)
        raise StoryError(explain_rejection(setting_id, args.spot, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.spot is None or combo[1] == args.spot)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, spot_id, tool_id = rng.choice(sorted(combos))
    item_id = args.item or rng.choice(sorted(ITEMS))
    mode_id = args.mode or rng.choice(sorted(MODES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    toddler_gender = args.toddler_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    toddler_name = args.toddler_name or _pick_name(rng, toddler_gender, toddler=True, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    pace = args.pace or rng.choice(["careful", "hurried"])
    sleep_depth = args.sleep_depth if args.sleep_depth is not None else rng.choice([0, 1, 2])
    return StoryParams(
        setting=setting_id,
        item=item_id,
        spot=spot_id,
        tool=tool_id,
        mode=mode_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        toddler_name=toddler_name,
        toddler_gender=toddler_gender,
        parent=parent,
        pace=pace,
        sleep_depth=sleep_depth,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.mode not in MODES:
        raise StoryError(f"(Unknown mode: {params.mode})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.pace not in {"careful", "hurried"}:
        raise StoryError(f"(Unknown pace: {params.pace})")
    if params.sleep_depth not in {0, 1, 2}:
        raise StoryError("(sleep_depth must be 0, 1, or 2)")
    if (params.setting, params.spot, params.tool) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.setting, params.spot, params.tool))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=ITEMS[params.item],
        spot=SPOTS[params.spot],
        tool=TOOLS[params.tool],
        mode=MODES[params.mode],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        toddler_name=params.toddler_name,
        toddler_gender=params.toddler_gender,
        parent_type=params.parent,
        pace=params.pace,
        sleep_depth=params.sleep_depth,
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
        print(f"{len(combos)} compatible (setting, spot, tool) combos:\n")
        for setting_id, spot_id, tool_id in combos:
            print(f"  {setting_id:10} {spot_id:14} {tool_id}")
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
                f"### {p.hero_name} as {MODES[p.mode].title}: {p.item} at {p.spot} "
                f"with {p.tool} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
