#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py
====================================================================

A small storyworld for a gentle mystery at the planetarium.

Seed ingredients rebuilt as world state:
- the child carries a sippy cup
- the cold day leaves the child's lips chapped
- the setting is a planetarium
- a hidden rhyme clue helps solve the mystery

The core causal turn is physical, not just decorative: a sip from the sippy cup
leaves a damp ring on a star pamphlet, and that damp ring reveals a faded rhyme.
The rhyme points to a plausible hiding place, and the missing keepsake is found.

Run it
------
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py --item moon_card --spot brochure_rack
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py --item comet_coin --spot brochure_rack
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py --all
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/sippy_chapped_planetarium_rhyme_mystery.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman", "sister", "guide_f"}
        male = {"boy", "father", "uncle", "man", "brother", "guide_m"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    size: str
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
class SpotCfg:
    id: str
    label: str
    place: str
    fits: set[str]
    rhyme_a: str
    rhyme_b: str
    clue: str
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
class HelperCfg:
    id: str
    label: str
    type: str
    intro: str
    notice: str
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
class StoryParams:
    item: str
    spot: str
    helper: str
    child_name: str
    child_gender: str
    caregiver: str
    trait: str
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
        self.facts: dict = {
            "search_target": "",
            "rhyme_lines": (),
            "predicted_fit": False,
        }

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


def _r_soothe(world: World) -> list[str]:
    child = world.get("child")
    if child.meters["sipped"] < THRESHOLD or child.meters["chapped"] < THRESHOLD:
        return []
    sig = ("soothe", "child")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["chapped"] = 0.0
    child.memes["comfort"] += 1
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    return []


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    child = world.get("child")
    helper = world.get("helper")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("missing", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    child.memes["curiosity"] += 1
    helper.memes["alert"] += 1
    return []


def _r_reveal_rhyme(world: World) -> list[str]:
    pamphlet = world.get("pamphlet")
    child = world.get("child")
    helper = world.get("helper")
    if pamphlet.meters["damp"] < THRESHOLD or pamphlet.meters["hidden_ink"] < THRESHOLD:
        return []
    sig = ("reveal", "pamphlet")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pamphlet.meters["revealed"] += 1
    child.memes["hope"] += 1
    helper.memes["focus"] += 1
    return []


def _r_find_item(world: World) -> list[str]:
    pamphlet = world.get("pamphlet")
    item = world.get("item")
    child = world.get("child")
    helper = world.get("helper")
    target = world.facts.get("search_target", "")
    if pamphlet.meters["revealed"] < THRESHOLD or not target:
        return []
    if item.attrs.get("spot") != target:
        return []
    sig = ("find", item.id, target)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["hidden"] = 0.0
    item.meters["found"] += 1
    child.memes["relief"] += 1
    child.memes["pride"] += 1
    helper.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="soothe", tag="physical", apply=_r_soothe),
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="reveal_rhyme", tag="physical", apply=_r_reveal_rhyme),
    Rule(name="find_item", tag="physical", apply=_r_find_item),
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
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ITEMS = {
    "star_badge": ItemCfg(
        id="star_badge",
        label="star badge",
        phrase="a shiny star badge",
        size="small",
        tags={"badge", "star"},
    ),
    "moon_card": ItemCfg(
        id="moon_card",
        label="moon card",
        phrase="a silver moon card",
        size="flat",
        tags={"card", "moon"},
    ),
    "comet_coin": ItemCfg(
        id="comet_coin",
        label="comet coin",
        phrase="a little comet coin",
        size="small",
        tags={"coin", "comet"},
    ),
}

SPOTS = {
    "bench_nook": SpotCfg(
        id="bench_nook",
        label="the nook under the dome bench",
        place="the star dome",
        fits={"small", "flat"},
        rhyme_a="Look where tired stargazers sit,",
        rhyme_b="low and quiet, tucked a bit.",
        clue="something can slip beneath the dome bench",
        ending="The mystery ended under the curved bench, where shadows were soft and the lost thing waited patiently.",
        tags={"bench", "dome"},
    ),
    "brochure_rack": SpotCfg(
        id="brochure_rack",
        label="the brochure rack in the lobby",
        place="the lobby",
        fits={"flat"},
        rhyme_a="If paper moons have drifted away,",
        rhyme_b="check the rack by maps on display.",
        clue="a flat thing might have slid into the brochure rack",
        ending="The mystery ended in the bright lobby, with the lost thing peeking from a row of star maps.",
        tags={"brochure", "lobby"},
    ),
    "mitten_bin": SpotCfg(
        id="mitten_bin",
        label="the mitten bin by the coat hooks",
        place="the coat nook",
        fits={"small"},
        rhyme_a="For tiny things that tumble and spin,",
        rhyme_b="peek by the hooks in the mitten bin.",
        clue="a tiny keepsake could have dropped into the mitten bin",
        ending="The mystery ended by the coat hooks, where mittens and scarves had been keeping the little treasure company.",
        tags={"mittens", "coatroom"},
    ),
}

HELPERS = {
    "guide": HelperCfg(
        id="guide",
        label="the guide",
        type="guide_f",
        intro="A guide with a star-shaped pin welcomed them at the door.",
        notice="The guide bent close and noticed the pale words waking up under the damp ring.",
        tags={"guide"},
    ),
    "usher": HelperCfg(
        id="usher",
        label="the usher",
        type="guide_m",
        intro="An usher with a soft flashlight showed them where to sit.",
        notice="The usher tilted the pamphlet and noticed the pale words waking up under the damp ring.",
        tags={"usher"},
    ),
    "aunt": HelperCfg(
        id="aunt",
        label="Aunt June",
        type="aunt",
        intro="Aunt June came too and whispered that mysteries were even better under stars.",
        notice="Aunt June smiled and noticed the pale words waking up under the damp ring.",
        tags={"family_helper"},
    ),
}

TRAITS = ["careful", "curious", "thoughtful", "bright", "patient", "gentle"]
GIRL_NAMES = ["Lina", "Maya", "Zoe", "Nora", "Ella", "Ivy", "Rose", "Anna"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Sam", "Finn", "Leo", "Eli", "Ben"]

KNOWLEDGE = {
    "sippy": [
        (
            "What is a sippy cup?",
            "A sippy cup is a cup with a lid that helps young children drink without spilling too much. It is handy when they want little sips while walking around.",
        )
    ],
    "chapped": [
        (
            "What does chapped mean?",
            "Chapped skin is dry and sore, often because of cold air or wind. Lips can feel rough and sting a little when they are chapped.",
        )
    ],
    "planetarium": [
        (
            "What is a planetarium?",
            "A planetarium is a place where people look at stars, planets, and space shows indoors. The ceiling can turn into a dark dome that looks like the night sky.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme clue?",
            "A rhyme clue is a hint written with words that sound alike. It can make a mystery feel playful while still pointing to something real.",
        )
    ],
    "brochure": [
        (
            "What is a brochure rack for?",
            "A brochure rack holds folded papers, maps, or little guides. Flat things can slip into it if nobody notices.",
        )
    ],
    "mittens": [
        (
            "Why do little things get lost near coat hooks?",
            "Mittens, scarves, and sleeves all move around together there. Small objects can tumble into a bin or pocket while people are taking coats on and off.",
        )
    ],
    "bench": [
        (
            "Why do objects slide under benches?",
            "When something small is dropped, it can skid or roll into the dark space underneath. Benches hide things because the floor under them is hard to see.",
        )
    ],
}

KNOWLEDGE_ORDER = ["sippy", "chapped", "planetarium", "rhyme", "bench", "brochure", "mittens"]


def item_fits_spot(item: ItemCfg, spot: SpotCfg) -> bool:
    return item.size in spot.fits


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for item_id, item in ITEMS.items():
        for spot_id, spot in SPOTS.items():
            if item_fits_spot(item, spot):
                out.append((item_id, spot_id))
    return out


def explain_rejection(item: ItemCfg, spot: SpotCfg) -> str:
    return (
        f"(No story: {item.phrase} is {item.size}, but {spot.label} is not a plausible place for that kind of object. "
        f"The mystery clue must point to a spot where the missing thing could honestly fit.)"
    )


def predict_search(world: World, spot_id: str) -> bool:
    sim = world.copy()
    sim.facts["search_target"] = spot_id
    propagate(sim, narrate=False)
    return sim.get("item").meters["found"] >= THRESHOLD


def introduce(world: World, child: Entity, caregiver: Entity, helper: Entity) -> None:
    world.say(
        f"On a cold afternoon, {child.id} went to the planetarium with {child.pronoun('possessive')} "
        f"{caregiver.label_word}. {child.pronoun('possessive').capitalize()} lips were chapped from the wind, "
        f"so {child.pronoun()} kept a blue sippy cup tucked in one hand."
    )
    world.say(helper.attrs["intro"])


def settle_in(world: World, child: Entity, item: Entity) -> None:
    world.say(
        f"In the lobby, {child.id} received {item.phrase} as part of the night's little star game, "
        f"and a folded pamphlet dusted with silver dots."
    )
    world.say(
        "The dome beyond the curtains was dim and whispery, the sort of place where even a tiny mystery could feel enormous."
    )


def sip_and_soothe(world: World, child: Entity) -> None:
    child.meters["sipped"] += 1
    propagate(world, narrate=False)
    if child.memes["comfort"] >= THRESHOLD:
        world.say(
            f"{child.id} took a careful sip from the sippy cup, and the cool drink made {child.pronoun('possessive')} mouth feel better."
        )


def lose_item(world: World, child: Entity, item: Entity, spot: SpotCfg) -> None:
    item.meters["hidden"] += 1
    item.attrs["spot"] = spot.id
    propagate(world, narrate=False)
    world.say(
        f"But when the lights brightened after the first star show, {child.id} patted {child.pronoun('possessive')} coat and went still."
    )
    world.say(
        f'"My {item.label} is gone," {child.pronoun()} whispered. For a moment, it felt as if the whole planetarium had swallowed it.'
    )


def inspect_pamphlet(world: World, child: Entity, helper: Entity, spot: SpotCfg) -> None:
    pamphlet = world.get("pamphlet")
    pamphlet.meters["damp"] += 1
    propagate(world, narrate=False)
    world.facts["rhyme_lines"] = (spot.rhyme_a, spot.rhyme_b)
    world.facts["predicted_fit"] = predict_search(world, spot.id)
    world.say(
        f"{child.id} set the pamphlet on a bench beside the sippy cup. A round damp mark bloomed on the paper, and faint gray words slowly appeared."
    )
    world.say(helper.attrs["notice"])
    world.say(
        f"{helper.label.capitalize()} read the hidden lines aloud: "
        f'"{spot.rhyme_a} {spot.rhyme_b}"'
    )


def search(world: World, child: Entity, caregiver: Entity, helper: Entity, item: Entity, spot: SpotCfg) -> None:
    world.facts["search_target"] = spot.id
    propagate(world, narrate=False)
    found = item.meters["found"] >= THRESHOLD
    world.say(
        f"{child.id}, {caregiver.label_word}, and {helper.label} hurried toward {spot.place}, following the rhyme as if it were a string through the dark."
    )
    if found:
        world.say(
            f"There, exactly where the clue promised, lay {item.phrase}. {child.id} let out a happy breath that sounded almost like a laugh."
        )
    else:
        world.say(
            f"They searched carefully, but the rhyme pointed nowhere useful. That would make no sense for this world."
        )


def ending(world: World, child: Entity, item: Entity, spot: SpotCfg) -> None:
    world.say(
        f"{spot.ending} {child.id} tucked {item.label} safely away and held the sippy cup close."
    )
    world.say(
        f"When the stars blossomed across the dome again, the mystery was solved, {child.pronoun('possessive')} lips no longer chapped, and the rhyme still twinkled in {child.pronoun('possessive')} head."
    )


def tell(
    item_cfg: ItemCfg,
    spot_cfg: SpotCfg,
    helper_cfg: HelperCfg,
    child_name: str = "Lina",
    child_gender: str = "girl",
    caregiver_type: str = "mother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            traits=[trait],
        )
    )
    caregiver = world.add(
        Entity(
            id="Caregiver",
            kind="character",
            type=caregiver_type,
            role="caregiver",
            label="the caregiver",
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label,
            kind="character",
            type=helper_cfg.type,
            role="helper",
            label=helper_cfg.label,
            attrs={"intro": helper_cfg.intro},
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="keepsake",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            attrs={"size": item_cfg.size, "spot": ""},
        )
    )
    pamphlet = world.add(
        Entity(
            id="pamphlet",
            type="paper",
            label="pamphlet",
        )
    )
    cup = world.add(
        Entity(
            id="cup",
            type="cup",
            label="sippy cup",
        )
    )

    child.meters["chapped"] = 1.0
    child.meters["sipped"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["relief"] = 0.0
    child.memes["comfort"] = 0.0
    helper.memes["alert"] = 0.0
    helper.memes["focus"] = 0.0
    helper.memes["relief"] = 0.0
    pamphlet.meters["hidden_ink"] = 1.0
    pamphlet.meters["damp"] = 0.0
    pamphlet.meters["revealed"] = 0.0
    item.meters["hidden"] = 0.0
    item.meters["found"] = 0.0
    cup.meters["full"] = 1.0

    introduce(world, child, caregiver, helper)
    settle_in(world, child, item)

    world.para()
    sip_and_soothe(world, child)
    lose_item(world, child, item, spot_cfg)

    world.para()
    inspect_pamphlet(world, child, helper, spot_cfg)
    search(world, child, caregiver, helper, item, spot_cfg)

    world.para()
    ending(world, child, item, spot_cfg)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        helper=helper,
        item=item,
        item_cfg=item_cfg,
        spot_cfg=spot_cfg,
        helper_cfg=helper_cfg,
        pamphlet=pamphlet,
        solved=item.meters["found"] >= THRESHOLD,
        soothed=child.memes["comfort"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    item = world.facts["item_cfg"]
    helper = world.facts["helper_cfg"]
    return [
        'Write a short mystery for a 3-to-5-year-old that includes the words "sippy", "chapped", and "planetarium", and use a rhyme as the clue.',
        f"Tell a gentle planetarium mystery where a {child.type} loses {item.phrase}, and {helper.label} helps solve it after a damp mark reveals a hidden rhyme.",
        "Write a child-facing mystery with a clear beginning, a worried middle, and an ending image under starry lights after the clue is solved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    caregiver = world.facts["caregiver"]
    helper = world.facts["helper"]
    item = world.facts["item_cfg"]
    spot = world.facts["spot_cfg"]
    rhyme_a, rhyme_b = world.facts.get("rhyme_lines", ("", ""))
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who went to the planetarium with {child.pronoun('possessive')} {caregiver.label_word}, and {helper.label}, who helped with the mystery.",
        ),
        (
            f"Why was {child.id} carrying a sippy cup?",
            f"{child.id} had chapped lips from the cold, so the sippy cup helped {child.pronoun('object')} take small drinks. The sip made {child.pronoun('possessive')} mouth feel better before the mystery was solved.",
        ),
        (
            f"What was missing?",
            f"The missing thing was {item.phrase}. Losing it is what turned the quiet visit into a mystery.",
        ),
        (
            "How did the clue appear?",
            f"A damp ring from the sippy cup landed on the pamphlet and revealed hidden words. That mattered because the rhyme pointed them toward {spot.label}.",
        ),
        (
            "What was the rhyme clue?",
            f'The hidden rhyme said, "{rhyme_a} {rhyme_b}" It was a playful hint that led the search to the right place.',
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            (
                f"How was the mystery solved?",
                f"They followed the rhyme to {spot.label} and found {item.phrase} there. The clue worked because that spot was a plausible place for the missing item to slip into.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the mystery solved and the stars shining over them again. {child.id} felt relieved, and the calm ending showed that the planetarium was magical instead of scary.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"sippy", "chapped", "planetarium", "rhyme"}
    tags |= set(world.facts["spot_cfg"].tags)
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(Item, Spot) :- item(Item), spot(Spot), size(Item, S), accepts(Spot, S).
valid(Item, Spot) :- fits(Item, Spot).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("size", item_id, item.size))
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for size in sorted(spot.fits):
            lines.append(asp.fact("accepts", spot_id, size))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("curated story was empty")
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
            break
    else:
        print(f"OK: generated {len(CURATED)} curated stories.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a planetarium mystery solved by a rhyme clue."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (item, spot) pairs from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.spot:
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        if not item_fits_spot(item, spot):
            raise StoryError(explain_rejection(item, spot))

    combos = [
        c
        for c in valid_combos()
        if (args.item is None or c[0] == args.item)
        and (args.spot is None or c[1] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, spot_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        item=item_id,
        spot=spot_id,
        helper=helper_id,
        child_name=name,
        child_gender=gender,
        caregiver=caregiver,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown gender: {params.child_gender})")
    if params.caregiver not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown caregiver: {params.caregiver})")

    item = ITEMS[params.item]
    spot = SPOTS[params.spot]
    helper = HELPERS[params.helper]
    if not item_fits_spot(item, spot):
        raise StoryError(explain_rejection(item, spot))

    world = tell(
        item_cfg=item,
        spot_cfg=spot,
        helper_cfg=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        caregiver_type=params.caregiver,
        trait=params.trait,
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


CURATED = [
    StoryParams(
        item="star_badge",
        spot="bench_nook",
        helper="guide",
        child_name="Lina",
        child_gender="girl",
        caregiver="mother",
        trait="curious",
    ),
    StoryParams(
        item="moon_card",
        spot="brochure_rack",
        helper="usher",
        child_name="Theo",
        child_gender="boy",
        caregiver="father",
        trait="thoughtful",
    ),
    StoryParams(
        item="comet_coin",
        spot="mitten_bin",
        helper="aunt",
        child_name="Maya",
        child_gender="girl",
        caregiver="aunt",
        trait="careful",
    ),
    StoryParams(
        item="moon_card",
        spot="bench_nook",
        helper="guide",
        child_name="Owen",
        child_gender="boy",
        caregiver="mother",
        trait="bright",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, spot) combos:\n")
        for item_id, spot_id in combos:
            print(f"  {item_id:12} {spot_id}")
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
            header = f"### {p.child_name}: {p.item} at {p.spot} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
