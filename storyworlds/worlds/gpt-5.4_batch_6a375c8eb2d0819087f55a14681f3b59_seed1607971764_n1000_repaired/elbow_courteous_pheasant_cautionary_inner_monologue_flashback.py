#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py
=============================================================================================

A small mystery-flavoured storyworld about a child, a missing shiny object, and
the dangerous temptation to push an arm into a hidden place.

The seed asked for these words and devices:
- elbow
- courteous
- pheasant
- cautionary
- inner monologue
- flashback
- mystery style

This world turns them into a state-driven simulation:

A child notices that a small prized object has gone missing in a quiet garden-like
place. Clues point toward a hiding spot where a pheasant has nested. The child
feels the pull of mystery, thinks privately about what the clues mean, and gets a
flashback warning about never shoving an arm into dark, hidden places. If the
child listens, a helpful grown-up uses a sensible tool and the mystery is solved
safely. If not, the child reaches in up to the elbow, gets scratched, and learns
the lesson the hard way. With a weak-but-still-sensible tool, the object is only
recovered after a patient wait and a courteous pheasant steps out and drops it
back.

Run it
------
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py --hideout rose_hedge
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py --tool bare_hand
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py --all
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py --qa --json
    python storyworlds/worlds/gpt-5.4/elbow_courteous_pheasant_cautionary_inner_monologue_flashback.py --verify
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
CAREFUL_TRAITS = {"careful", "patient", "thoughtful", "courteous"}


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
        female = {"girl", "mother", "woman", "librarian"}
        male = {"boy", "father", "man", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Setting:
    id: str
    place: str
    atmosphere: str
    path: str
    helper_type: str
    helper_label: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    shine: str
    size: int
    sentimental: str
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
class Hideout:
    id: str
    label: str
    phrase: str
    opening: str
    clue: str
    hazard: int
    reach_need: int
    capacity: int
    can_hide: bool = True
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
    sense: int
    power: int
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


def _r_scrape(world: World) -> list[str]:
    hero = world.get("hero")
    hideout = world.get("hideout")
    if hero.meters["arm_inside"] < THRESHOLD:
        return []
    sig = ("scrape",)
    if sig in world.fired:
        return []
    if hideout.attrs.get("hazard", 0) <= 0:
        return []
    world.fired.add(sig)
    hero.meters["scratched"] += 1
    hero.memes["fear"] += 1
    hero.memes["embarrassment"] += 1
    return ["__scrape__"]


def _r_startle_bird(world: World) -> list[str]:
    hero = world.get("hero")
    bird = world.get("pheasant")
    item = world.get("item")
    if hero.meters["arm_inside"] < THRESHOLD:
        return []
    sig = ("startle_bird",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    bird.memes["startled"] += 1
    item.meters["deeper"] += 1
    return ["__bird__"]


def _r_relief(world: World) -> list[str]:
    item = world.get("item")
    hero = world.get("hero")
    if item.meters["recovered"] < THRESHOLD:
        return []
    sig = ("relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["curiosity"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="scrape", tag="physical", apply=_r_scrape),
    Rule(name="startle_bird", tag="social", apply=_r_startle_bird),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def thing_fits(item: MissingThing, hideout: Hideout) -> bool:
    return hideout.can_hide and item.size <= hideout.capacity


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def tool_can_reach(tool: Tool, hideout: Hideout, disturbed: bool = False) -> bool:
    need = hideout.reach_need + (1 if disturbed else 0)
    return tool.power >= need


def would_pause(trait: str, bravery: int) -> bool:
    caution = 6 if trait in CAREFUL_TRAITS else 3
    return caution > bravery


def predict_reach(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["arm_inside"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "scratched": hero.meters["scratched"] >= THRESHOLD,
        "bird_startled": sim.get("pheasant").memes["startled"] >= THRESHOLD,
        "deeper": item.meters["deeper"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} liked small puzzles, especially the kind that seemed to whisper instead of shout. "
        f"On that quiet afternoon in {world.setting.place}, {hero.pronoun()} noticed at once that "
        f"{item.attrs['owner_name']}'s {item.label} was gone."
    )
    world.say(
        f"It was {item.attrs['shine']} and easy to miss in daylight, yet somehow its absence made the whole place feel different."
    )
    hero.memes["curiosity"] += 1


def set_scene(world: World, hideout: Hideout) -> None:
    world.say(world.setting.atmosphere)
    world.say(
        f"Near {world.setting.path}, a few bent leaves and {hideout.clue} pointed toward {hideout.phrase}."
    )


def inner_monologue(world: World, hero: Entity, item_cfg: MissingThing, hideout: Hideout) -> None:
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} thought, "A mystery. Did someone tuck the {item_cfg.label} away on purpose?"'
    )
    world.say(
        f'{hero.pronoun().capitalize()} stared at {hideout.opening} and wondered, "What if the dark place is hiding more than one secret?"'
    )


def spot_pheasant(world: World, bird: Entity) -> None:
    bird.memes["calm"] += 1
    world.say(
        f"Then a pheasant stepped from the shade with a soft rustle. It was so courteous in its slow little bow that it looked less like a thief and more like a keeper of clues."
    )


def flashback_warning(world: World, hero: Entity, helper: Entity, hideout: Hideout) -> None:
    pred = predict_reach(world)
    world.facts["predicted_scratched"] = pred["scratched"]
    world.facts["predicted_bird_startled"] = pred["bird_startled"]
    hero.memes["caution"] += 1
    world.say(
        f"A quick flashback came to {hero.id}: once, {helper.label_word} had said, "
        f'"Never push your arm into a hidden place up to the elbow. A dark opening may hold thorns, splinters, or a frightened animal."'
    )
    if pred["scratched"] or pred["bird_startled"]:
        world.say(
            f"Remembering that warning made the mystery feel sharper, not smaller."
        )


def reach_anyway(world: World, hero: Entity, hideout: Hideout) -> None:
    hero.meters["arm_inside"] += 1
    hero.meters["elbow_deep"] += 1
    hero.memes["defiance"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But curiosity tugged harder. {hero.id} knelt beside {hideout.phrase} and slid one arm in until the sleeve reached the elbow."
    )
    if hero.meters["scratched"] >= THRESHOLD:
        world.say(
            f"At once, something rough scraped {hero.pronoun('possessive')} skin, and {hero.pronoun()} jerked back with a gasp."
        )
    if world.get("pheasant").memes["startled"] >= THRESHOLD:
        world.say(
            f"Inside, wings thumped once, and the hidden little world became noisy and upset."
        )


def stop_in_time(world: World, hero: Entity, hideout: Hideout) -> None:
    hero.memes["self_control"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"{hero.id} crouched near {hideout.phrase}, then pulled {hero.pronoun('possessive')} hand back before it went in."
    )
    world.say(
        f'"No," {hero.pronoun()} whispered to {hero.pronoun("object")}self. "A mystery is not permission to be careless."'
    )


def call_helper(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} called for {helper.label_word}, who came quickly but quietly, as if even the answer should not scare the clues away."
    )


def helper_retrieve(world: World, helper: Entity, tool: Tool, hideout: Hideout, item_cfg: MissingThing, disturbed: bool) -> None:
    item = world.get("item")
    item.meters["recovered"] += 1
    item.meters["hidden"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{helper.label_word.capitalize()} used {tool.phrase} and {tool.use_text.format(hideout=hideout.label, item=item_cfg.label)}."
    )
    world.say(
        f"In a moment, the missing {item_cfg.label} glinted in the light again."
    )
    if not disturbed:
        world.say(
            f"The pheasant gave another courteous sidestep, as if it approved of solving a puzzle without grabbing at it."
        )


def helper_fail_then_wait(world: World, helper: Entity, tool: Tool, hideout: Hideout, item_cfg: MissingThing) -> None:
    hero = world.get("hero")
    hero.memes["patience"] += 1
    world.say(
        f"{helper.label_word.capitalize()} tried {tool.phrase}, but {tool.fail_text.format(hideout=hideout.label, item=item_cfg.label)}."
    )
    world.say(
        f'"We know where the mystery lives now," {helper.label_word} said. "So we can let patience do part of the work."'
    )


def pheasant_returns_item(world: World, item_cfg: MissingThing) -> None:
    item = world.get("item")
    bird = world.get("pheasant")
    item.meters["recovered"] += 1
    item.meters["hidden"] = 0.0
    bird.memes["calm"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They waited very still. At last the pheasant stepped out, head high and oddly solemn, with the {item_cfg.label} caught in its beak."
    )
    world.say(
        f"It set the little object down on the path as neatly as a courteous host laying a spoon beside a teacup."
    )


def clean_and_lesson(world: World, helper: Entity, hero: Entity) -> None:
    if hero.meters["scratched"] >= THRESHOLD:
        hero.memes["comfort"] += 1
        world.say(
            f"{helper.label_word.capitalize()} dabbed the scratch clean and checked the sore elbow before saying anything else."
        )
    world.say(
        f'"Clues are for looking at first," {helper.label_word} said softly. "Hands come second, and only when the place is safe."'
    )
    world.say(
        f"{hero.id} nodded. The warning from the flashback no longer felt like a rule floating in the air. It felt true."
    )


def ending_safe(world: World, hero: Entity, item_cfg: MissingThing) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"By the time the shadows lengthened, the mystery had become a story {hero.id} would remember for the right reason: the {item_cfg.label} was back, and no one had been hurt."
    )


def ending_oopsie(world: World, hero: Entity, item_cfg: MissingThing) -> None:
    hero.memes["wisdom"] += 1
    world.say(
        f"That evening, {hero.id} tucked the recovered {item_cfg.label} safely away and glanced once more at the dark opening."
    )
    world.say(
        f"{hero.pronoun().capitalize()} could still feel the sting near {hero.pronoun('possessive')} elbow, and that tiny sting was enough to keep the lesson bright."
    )


def tell(
    setting: Setting,
    thing: MissingThing,
    hideout: Hideout,
    tool: Tool,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    hero_trait: str = "careful",
    helper_type: str = "gardener",
    owner_name: str = "Grandma",
    bravery: int = 4,
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            traits=[hero_trait],
            attrs={"display_name": hero_name},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label=setting.helper_label,
            role="helper",
        )
    )
    bird = world.add(
        Entity(
            id="pheasant",
            kind="thing",
            type="pheasant",
            label="the pheasant",
            role="bird",
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=thing.label,
            role="missing",
            attrs={"owner_name": owner_name},
        )
    )
    hide_ent = world.add(
        Entity(
            id="hideout",
            kind="thing",
            type="hideout",
            label=hideout.label,
            role="hideout",
            attrs={"hazard": hideout.hazard, "reach_need": hideout.reach_need},
        )
    )
    tool_ent = world.add(
        Entity(
            id="tool",
            kind="thing",
            type="tool",
            label=tool.label,
            role="tool",
            attrs={"sense": tool.sense, "power": tool.power},
        )
    )

    hero.attrs["display_name"] = hero_name
    hero.memes["curiosity"] = 1.0
    hero.memes["caution"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["defiance"] = 0.0
    hero.meters["arm_inside"] = 0.0
    hero.meters["scratched"] = 0.0
    hero.meters["elbow_deep"] = 0.0
    bird.memes["startled"] = 0.0
    bird.memes["calm"] = 0.0
    item.meters["hidden"] = 1.0
    item.meters["recovered"] = 0.0
    item.meters["deeper"] = 0.0

    introduce(world, hero, item)
    set_scene(world, hideout)
    world.para()
    inner_monologue(world, hero, thing, hideout)
    spot_pheasant(world, bird)
    flashback_warning(world, hero, helper, hideout)

    paused = would_pause(hero_trait, bravery)
    disturbed = False
    retrieved = False
    patient_return = False

    world.para()
    if paused:
        stop_in_time(world, hero, hideout)
        call_helper(world, hero, helper)
        helper_retrieve(world, helper, tool, hideout, thing, disturbed=False)
        retrieved = True
    else:
        reach_anyway(world, hero, hideout)
        disturbed = True
        call_helper(world, hero, helper)
        if tool_can_reach(tool, hideout, disturbed=True):
            helper_retrieve(world, helper, tool, hideout, thing, disturbed=True)
            retrieved = True
        else:
            helper_fail_then_wait(world, helper, tool, hideout, thing)
            world.para()
            pheasant_returns_item(world, thing)
            patient_return = True
            retrieved = True

    world.para()
    clean_and_lesson(world, helper, hero)
    if paused or (retrieved and hero.meters["scratched"] < THRESHOLD):
        ending_safe(world, hero, thing)
    else:
        ending_oopsie(world, hero, thing)

    outcome = "averted" if paused else ("waited" if patient_return else "scraped")
    world.facts.update(
        hero=hero,
        helper=helper,
        pheasant=bird,
        item=item,
        thing_cfg=thing,
        hideout_cfg=hideout,
        tool_cfg=tool,
        bravery=bravery,
        paused=paused,
        disturbed=disturbed,
        retrieved=retrieved,
        patient_return=patient_return,
        outcome=outcome,
        setting=setting,
        owner_name=owner_name,
    )
    return world


SETTINGS = {
    "manor_garden": Setting(
        id="manor_garden",
        place="the old manor garden",
        atmosphere="The hedges held their shadows close, and every pebble on the path looked like part of a secret.",
        path="the yew path",
        helper_type="gardener",
        helper_label="the gardener",
        tags={"garden", "mystery"},
    ),
    "museum_court": Setting(
        id="museum_court",
        place="the museum courtyard",
        atmosphere="The stone walls kept the air cool, and the fountain made a quiet sound like someone whispering behind a door.",
        path="the fig pots",
        helper_type="librarian",
        helper_label="the curator",
        tags={"courtyard", "mystery"},
    ),
    "orchard_walk": Setting(
        id="orchard_walk",
        place="the orchard walk",
        atmosphere="The rows of trees made long green rooms, and the wind kept slipping from one room to the next with a hush-hush sound.",
        path="the apple crates",
        helper_type="gardener",
        helper_label="the orchard keeper",
        tags={"orchard", "mystery"},
    ),
}

THINGS = {
    "key": MissingThing(
        id="key",
        label="brass key",
        phrase="a little brass key",
        shine="warm and yellow as honey",
        size=1,
        sentimental="It opened a painted music box.",
        tags={"key", "metal"},
    ),
    "thimble": MissingThing(
        id="thimble",
        label="silver thimble",
        phrase="a tiny silver thimble",
        shine="bright as a fish scale",
        size=1,
        sentimental="It belonged to a sewing basket that had been in the family for years.",
        tags={"thimble", "metal"},
    ),
    "bell": MissingThing(
        id="bell",
        label="little bell",
        phrase="a little bell on a blue ribbon",
        shine="small and golden",
        size=2,
        sentimental="It used to jingle from a favorite satchel.",
        tags={"bell", "metal"},
    ),
    "spoon": MissingThing(
        id="spoon",
        label="silver spoon",
        phrase="a silver spoon with a swirled handle",
        shine="cool and bright",
        size=2,
        sentimental="It had been saved for special tea days.",
        tags={"spoon", "metal"},
    ),
}

HIDEOUTS = {
    "rose_hedge": Hideout(
        id="rose_hedge",
        label="rose hedge",
        phrase="the thick rose hedge",
        opening="a thorny pocket under the hedge",
        clue="a bright feather caught on a stem",
        hazard=2,
        reach_need=2,
        capacity=2,
        can_hide=True,
        tags={"hedge", "thorns"},
    ),
    "hollow_stump": Hideout(
        id="hollow_stump",
        label="hollow stump",
        phrase="the hollow stump",
        opening="the dark round hollow",
        clue="a line of small claw marks in the dust",
        hazard=1,
        reach_need=3,
        capacity=2,
        can_hide=True,
        tags={"stump", "dark"},
    ),
    "stone_drain": Hideout(
        id="stone_drain",
        label="stone drain",
        phrase="the narrow stone drain",
        opening="the slit between two flat stones",
        clue="a trail of pressed grass leading to the grate",
        hazard=1,
        reach_need=4,
        capacity=1,
        can_hide=True,
        tags={"drain", "narrow"},
    ),
    "bench_slat": Hideout(
        id="bench_slat",
        label="bench slat",
        phrase="the gap beneath an old bench",
        opening="a shallow gap under the wooden seat",
        clue="one feather resting on the board",
        hazard=0,
        reach_need=1,
        capacity=1,
        can_hide=False,
        tags={"bench"},
    ),
}

TOOLS = {
    "tongs": Tool(
        id="tongs",
        label="kitchen tongs",
        phrase="a pair of kitchen tongs",
        sense=3,
        power=3,
        use_text="reached carefully into the {hideout} and lifted out the {item}",
        fail_text="the {item} lay just beyond the safe reach of the tongs inside the {hideout}",
        qa_text="used kitchen tongs to lift the object out safely",
        tags={"tongs", "tool"},
    ),
    "grabber": Tool(
        id="grabber",
        label="garden grabber",
        phrase="the long garden grabber",
        sense=3,
        power=5,
        use_text="slid the long grip into the {hideout} and drew the {item} out without poking or pulling wildly",
        fail_text="even the grabber could not catch the {item} in the first try",
        qa_text="used the long garden grabber to pull the object out safely",
        tags={"grabber", "tool"},
    ),
    "walking_stick": Tool(
        id="walking_stick",
        label="walking stick",
        phrase="a walking stick",
        sense=2,
        power=2,
        use_text="nudged the {item} toward the edge of the {hideout} until it could be taken safely",
        fail_text="the walking stick could only tap near the opening, not bring the {item} all the way out of the {hideout}",
        qa_text="used a walking stick to nudge the object toward safety",
        tags={"stick", "tool"},
    ),
    "bare_hand": Tool(
        id="bare_hand",
        label="bare hand",
        phrase="a bare hand",
        sense=1,
        power=1,
        use_text="reached straight into the {hideout} for the {item}",
        fail_text="a bare hand was the wrong way to reach into the {hideout}",
        qa_text="reached in with a bare hand",
        tags={"hand"},
    ),
}

GIRL_NAMES = ["Mira", "Nora", "Lucy", "Ivy", "Ada", "Tess", "Ruby", "Wren"]
BOY_NAMES = ["Owen", "Theo", "Ben", "Miles", "Eli", "Noah", "Finn", "Jude"]
TRAITS = ["careful", "patient", "thoughtful", "courteous", "curious", "bold"]
OWNERS = ["Grandma", "Uncle Ren", "Aunt May"]


@dataclass
class StoryParams:
    setting: str
    thing: str
    hideout: str
    tool: str
    hero_name: str
    hero_gender: str
    hero_trait: str
    owner_name: str
    bravery: int = 4
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
    "pheasant": [
        (
            "What is a pheasant?",
            "A pheasant is a ground bird with strong legs and a long tail. It often hides in grass or under bushes and can burst out with a sudden flap."
        )
    ],
    "thorns": [
        (
            "Why can a thorny hedge be dangerous?",
            "A thorny hedge has sharp points that can scratch skin and snag sleeves. That is why hands should stay out unless a grown-up says it is safe."
        )
    ],
    "hidden_place": [
        (
            "Why should children not reach into dark hidden places?",
            "A dark hidden place can have thorns, splinters, or a frightened animal inside. Looking first and asking a grown-up for help is safer than grabbing."
        )
    ],
    "tool": [
        (
            "Why is a tool safer than a bare hand for pulling something out?",
            "A long tool lets you reach from farther away, so your fingers do not have to go into the risky spot. It also keeps you from poking around blindly."
        )
    ],
    "key": [
        (
            "What does a key do?",
            "A key opens a lock. Even a small key can be important if it belongs to a box, a gate, or a special drawer."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is something puzzling that you have to figure out from clues. You look carefully, think calmly, and solve it step by step."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick memory from earlier that helps explain what a character does now. It can remind the character of a warning, a promise, or a lesson."
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "pheasant", "hidden_place", "thorns", "tool", "key", "flashback"]


def pair_article(label: str) -> str:
    if label[0].lower() in "aeiou":
        return f"an {label}"
    return f"a {label}"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting_id in SETTINGS:
        for thing_id, thing in THINGS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if thing_fits(thing, hideout):
                    out.append((setting_id, thing_id, hideout_id))
    return out


def explain_rejection(thing: MissingThing, hideout: Hideout) -> str:
    if not hideout.can_hide:
        return (
            f"(No story: {hideout.phrase} is too open and shallow to hold a hidden clue worth investigating. "
            f"A mystery needs a real hiding place.)"
        )
    if thing.size > hideout.capacity:
        return (
            f"(No story: the {thing.label} is too large to fit inside {hideout.phrase}. "
            f"Pick a smaller object or a roomier hiding place.)"
        )
    return "(No story: that combination does not make a plausible little mystery.)"


def explain_tool(tool_id: str) -> str:
    tool = TOOLS[tool_id]
    better = ", ".join(sorted(t.id for t in sensible_tools()))
    return (
        f"(Refusing tool '{tool_id}': it scores too low on common sense (sense={tool.sense} < {SENSE_MIN}). "
        f"A child in a mystery should not be guided toward an unsafe reach. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    paused = would_pause(params.hero_trait, params.bravery)
    if paused:
        return "averted"
    tool = TOOLS[params.tool]
    hideout = HIDEOUTS[params.hideout]
    return "scraped" if tool_can_reach(tool, hideout, disturbed=True) else "waited"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    thing = f["thing_cfg"]
    hideout = f["hideout_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short mystery for a 3-to-5-year-old that includes the words "elbow", "courteous", and "pheasant", '
        f"uses inner monologue and a flashback, and centers on a missing {thing.label}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle cautionary mystery where {hero.attrs['display_name']} stops before pushing an arm into {hideout.phrase}, remembers a warning, and solves the puzzle safely with help.",
            f"Write a child-facing mystery in which a courteous pheasant seems suspicious at first, but the real lesson is to pause and ask for help before reaching into hidden places.",
        ]
    if outcome == "waited":
        return [
            base,
            f"Tell a mystery where the child reaches in up to the elbow, gets a scratch, and then must wait quietly until the courteous pheasant returns the missing object.",
            f"Write a cautionary mystery with a small injury, a patient grown-up, and an ending that proves patience can solve what grabbing cannot.",
        ]
    return [
        base,
        f"Tell a mystery where the child ignores a flashback warning, reaches into {hideout.phrase}, scrapes an elbow, and then a grown-up solves the puzzle with a safe tool.",
        f"Write a cautionary story with inner monologue and a flashback, where the child learns that clues should be studied before hands go into dangerous places.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    thing = f["thing_cfg"]
    hideout = f["hideout_cfg"]
    tool = f["tool_cfg"]
    owner_name = f["owner_name"]
    hero_name = hero.attrs["display_name"]
    out: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {owner_name}'s {thing.label} had gone missing. Bent leaves, a feather, and the dark opening near {hideout.phrase} made {hero_name} suspect the answer was hiding there."
        ),
        (
            "What did the child think privately when the clues appeared?",
            f"{hero_name} had an inner monologue and wondered whether someone had tucked the {thing.label} away on purpose. Those private thoughts made the place feel more mysterious before the truth was known."
        ),
        (
            "What was the flashback about?",
            f"The flashback was a remembered warning not to push an arm into hidden places up to the elbow. It mattered because the opening could hold thorns or a frightened animal, not just the missing object."
        ),
        (
            "Why did the pheasant seem important?",
            f"The pheasant appeared right beside the clues, so it looked like part of the mystery. Later it turned out to be a calm, courteous keeper of the hiding place rather than a scary threat."
        ),
    ]
    if f["outcome"] == "averted":
        out.append(
            (
                f"How was the mystery solved without anyone getting hurt?",
                f"{hero_name} stopped before reaching in and called {helper.label_word} for help. {helper.label_word.capitalize()} {tool.qa_text}, so the {thing.label} came back safely and the warning proved useful."
            )
        )
    elif f["outcome"] == "scraped":
        out.append(
            (
                f"What happened when {hero_name} reached in?",
                f"{hero_name} pushed an arm in until the sleeve reached the elbow and got scratched. That also startled the pheasant, so the safe answer was to let {helper.label_word} handle the hiding place with {tool.phrase}."
            )
        )
        out.append(
            (
                "What lesson did the child learn?",
                f"{hero_name} learned that clues should be looked at first and touched only when the place is safe. The scratch made the warning feel real, and the grown-up's careful method solved the mystery better than grabbing."
            )
        )
    else:
        out.append(
            (
                f"Why did they have to wait instead of solving it right away?",
                f"The child had already startled the bird and pushed the {thing.label} deeper, and the tool could not reach it safely. Waiting quietly worked better because the courteous pheasant finally stepped out and returned the object itself."
            )
        )
        out.append(
            (
                "How did the ending prove what changed?",
                f"At the end, {hero_name} had the {thing.label} back but also remembered the sting near the elbow. The object was recovered, and the child had become more patient and careful than before."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery", "pheasant", "hidden_place", "tool", "flashback"}
    if "thorns" in f["hideout_cfg"].tags:
        tags.add("thorns")
    if f["thing_cfg"].id == "key":
        tags.add("key")
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
            shown = {k: v for k, v in ent.attrs.items() if v != 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="manor_garden",
        thing="key",
        hideout="rose_hedge",
        tool="grabber",
        hero_name="Mira",
        hero_gender="girl",
        hero_trait="careful",
        owner_name="Grandma",
        bravery=4,
    ),
    StoryParams(
        setting="museum_court",
        thing="thimble",
        hideout="hollow_stump",
        tool="tongs",
        hero_name="Owen",
        hero_gender="boy",
        hero_trait="bold",
        owner_name="Aunt May",
        bravery=5,
    ),
    StoryParams(
        setting="orchard_walk",
        thing="key",
        hideout="stone_drain",
        tool="walking_stick",
        hero_name="Nora",
        hero_gender="girl",
        hero_trait="curious",
        owner_name="Uncle Ren",
        bravery=5,
    ),
    StoryParams(
        setting="manor_garden",
        thing="bell",
        hideout="rose_hedge",
        tool="grabber",
        hero_name="Theo",
        hero_gender="boy",
        hero_trait="patient",
        owner_name="Grandma",
        bravery=3,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
fits(Thing, Hideout) :- thing(Thing), hideout(Hideout), can_hide(Hideout),
                        size(Thing, S), capacity(Hideout, C), S <= C.
valid(Setting, Thing, Hideout) :- setting(Setting), fits(Thing, Hideout).

sensible_tool(T) :- tool(T), sense(T, S), sense_min(M), S >= M.

% --- outcome model ---------------------------------------------------------
careful_trait(T) :- trait(T), is_careful(T).
caution(6) :- trait(T), careful_trait(T).
caution(3) :- trait(T), not careful_trait(T).
paused :- caution(C), bravery(B), C > B.

need(R + 1) :- chosen_hideout(H), reach_need(H, R).
scraped_path :- not paused.
reachable :- chosen_tool(T), power(T, P), need(N), P >= N.

outcome(averted) :- paused.
outcome(scraped) :- scraped_path, reachable.
outcome(waited)  :- scraped_path, not reachable.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("size", tid, thing.size))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("capacity", hid, hideout.capacity))
        lines.append(asp.fact("reach_need", hid, hideout.reach_need))
        if hideout.can_hide:
            lines.append(asp.fact("can_hide", hid))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        lines.append(asp.fact("power", tool_id, tool.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_tools() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_tool/1."))
    return sorted(t for (t,) in asp.atoms(model, "sensible_tool"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("chosen_tool", params.tool),
            asp.fact("trait", params.hero_trait),
            asp.fact("bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_tools = {tool.id for tool in sensible_tools()}
    asp_tools = set(asp_sensible_tools())
    if py_tools == asp_tools:
        print(f"OK: sensible tools match ({sorted(py_tools)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible tools: python={sorted(py_tools)} clingo={sorted(asp_tools)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
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
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves a little mystery near a pheasant's hiding place."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--owner", choices=OWNERS)
    ap.add_argument("--bravery", type=int, choices=[3, 4, 5, 6])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.hideout:
        thing = THINGS[args.thing]
        hideout = HIDEOUTS[args.hideout]
        if not thing_fits(thing, hideout):
            raise StoryError(explain_rejection(thing, hideout))
    if args.tool and TOOLS[args.tool].sense < SENSE_MIN:
        raise StoryError(explain_tool(args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.thing is None or combo[1] == args.thing)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, thing_id, hideout_id = rng.choice(sorted(combos))
    tool_id = args.tool or rng.choice(sorted(tool.id for tool in sensible_tools()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    owner_name = args.owner or rng.choice(OWNERS)
    bravery = args.bravery if args.bravery is not None else rng.choice([3, 4, 5, 6])

    return StoryParams(
        setting=setting_id,
        thing=thing_id,
        hideout=hideout_id,
        tool=tool_id,
        hero_name=name,
        hero_gender=gender,
        hero_trait=trait,
        owner_name=owner_name,
        bravery=bravery,
    )


def _require_key(registry: dict, key: str, field: str):
    if key not in registry:
        raise StoryError(f"(Invalid {field}: {key})")
    return registry[key]


def generate(params: StoryParams) -> StorySample:
    setting = _require_key(SETTINGS, params.setting, "setting")
    thing = _require_key(THINGS, params.thing, "thing")
    hideout = _require_key(HIDEOUTS, params.hideout, "hideout")
    tool = _require_key(TOOLS, params.tool, "tool")

    if not thing_fits(thing, hideout):
        raise StoryError(explain_rejection(thing, hideout))
    if tool.sense < SENSE_MIN:
        raise StoryError(explain_tool(tool.id))

    world = tell(
        setting=setting,
        thing=thing,
        hideout=hideout,
        tool=tool,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        hero_trait=params.hero_trait,
        helper_type=setting.helper_type,
        owner_name=params.owner_name,
        bravery=params.bravery,
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
        print(asp_program("", "#show valid/3.\n#show sensible_tool/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible tools: {', '.join(asp_sensible_tools())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, thing, hideout) combos:\n")
        for setting_id, thing_id, hideout_id in combos:
            print(f"  {setting_id:13} {thing_id:8} {hideout_id}")
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
            header = (
                f"### {p.hero_name}: {p.thing} in {p.hideout} "
                f"({p.setting}, {p.tool}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
