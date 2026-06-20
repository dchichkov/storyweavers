#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/anchor_fuzzy_moss_crystal_lighthouse_kitchen_twist.py
=================================================================================

A standalone storyworld built from the seed:

    Words: anchor, fuzzy moss, crystal lighthouse
    Setting: kitchen
    Features: Twist
    Style: Adventure

Internal source tale
--------------------
In a stormy kitchen that feels like a ship's cabin, two children search for a
missing kitchen treasure. A crystal lighthouse on the counter seems like the
obvious hiding place, and a fast shortcut would be to pry it open or yank aside
nearby decorations. Instead, the children study the light patiently. The beam
touches an anchor marker, which leads them to a patch of fuzzy moss hiding the
real prize. The twist is that the crystal lighthouse was never the treasure; it
was the guide.
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
CARE_MIN = 3


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: str = ""
    location: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Kitchen:
    id: str
    phrase: str
    weather: str
    counter: str
    mood: str
    routes: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class CrystalLighthouse:
    id: str
    label: str
    phrase: str
    lens: str
    beam: str
    hint: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MossPatch:
    id: str
    label: str
    phrase: str
    texture: str
    area: str
    hiding: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class AnchorMark:
    id: str
    label: str
    phrase: str
    place: str
    use: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shortcut:
    id: str
    label: str
    temptation: str
    thought: str
    target: str
    damage: str
    consequence: str
    safe_choice: str
    lure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    apparent: str
    truth: str
    reveal: str
    ending: str
    prize: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], list[str]]


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def copy(self) -> "World":
        clone = World(self.kitchen)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_read_beam(world: World) -> list[str]:
    hero = world.get("hero")
    lighthouse = world.get("lighthouse")
    sig = ("beam", lighthouse.id)
    if lighthouse.meters["turned"] < THRESHOLD:
        return []
    if lighthouse.meters["cracked"] >= THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lighthouse.meters["guiding"] += 1
    hero.memes["insight"] += 1
    return []


def _r_shortcut_stirs_hurry(world: World) -> list[str]:
    hero = world.get("hero")
    shortcut = world.get("shortcut")
    sig = ("hurry", shortcut.id)
    if shortcut.meters["noticed"] < THRESHOLD or sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["hurry"] += shortcut.meters["lure"]
    return []


def _r_care_makes_steady(world: World) -> list[str]:
    hero = world.get("hero")
    shortcut = world.get("shortcut")
    sig = ("steady", hero.id)
    if hero.memes["insight"] < THRESHOLD:
        return []
    if hero.memes["care"] < shortcut.meters["lure"]:
        return []
    if shortcut.meters["noticed"] < THRESHOLD:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["steady"] += 1
    return []


def _r_beam_marks_anchor(world: World) -> list[str]:
    lighthouse = world.get("lighthouse")
    anchor = world.get("anchor")
    hero = world.get("hero")
    sig = ("anchor_lit", anchor.id)
    if lighthouse.meters["guiding"] < THRESHOLD:
        return []
    if hero.memes["steady"] < THRESHOLD:
        return []
    if lighthouse.attrs["key"] != anchor.attrs["key"]:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    anchor.meters["lit"] += 1
    return []


def _r_find_prize(world: World) -> list[str]:
    anchor = world.get("anchor")
    moss = world.get("moss")
    prize = world.get("prize")
    hero = world.get("hero")
    sig = ("prize_found", prize.id)
    if anchor.meters["lit"] < THRESHOLD or moss.meters["lifted"] < THRESHOLD:
        return []
    if anchor.attrs["key"] != moss.attrs["key"] or moss.attrs["key"] != prize.attrs["key"]:
        return []
    if sig in world.fired:
        return []
    world.fired.add(sig)
    prize.meters["found"] += 1
    hero.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule("read_beam", _r_read_beam),
    Rule("shortcut_stirs_hurry", _r_shortcut_stirs_hurry),
    Rule("care_makes_steady", _r_care_makes_steady),
    Rule("beam_marks_anchor", _r_beam_marks_anchor),
    Rule("find_prize", _r_find_prize),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            before = len(world.fired)
            rule.apply(world)
            if len(world.fired) != before:
                changed = True


def route_matches(kitchen: Kitchen, lighthouse: CrystalLighthouse, moss: MossPatch,
                  anchor: AnchorMark, twist: Twist) -> bool:
    return (
        lighthouse.key in kitchen.routes
        and lighthouse.key == moss.key == anchor.key == twist.key
    )


def care_sufficient(shortcut: Shortcut, care: int) -> bool:
    return care >= max(CARE_MIN, shortcut.lure)


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for kitchen_id, kitchen in KITCHENS.items():
        for lighthouse_id, lighthouse in LIGHTHOUSES.items():
            for moss_id, moss in MOSS_PATCHES.items():
                for anchor_id, anchor in ANCHORS.items():
                    for twist_id, twist in TWISTS.items():
                        if route_matches(kitchen, lighthouse, moss, anchor, twist):
                            combos.append(
                                (kitchen_id, lighthouse_id, moss_id, anchor_id, twist_id)
                            )
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    kitchen = KITCHENS[params.kitchen]
    lighthouse = LIGHTHOUSES[params.lighthouse]
    moss = MOSS_PATCHES[params.moss]
    anchor = ANCHORS[params.anchor]
    twist = TWISTS[params.twist]
    shortcut = SHORTCUTS[params.shortcut]
    if not route_matches(kitchen, lighthouse, moss, anchor, twist):
        return "route_mismatch"
    if not care_sufficient(shortcut, params.care):
        return "too_rough"
    return "twist_found"


def predict_shortcut(world: World, shortcut: Shortcut) -> dict:
    sim = world.copy()
    target = sim.get(shortcut.target)
    target.meters[shortcut.damage] += 1
    if shortcut.target == "lighthouse":
        target.meters["guiding"] = 0.0
    if shortcut.target == "anchor":
        target.meters["lit"] = 0.0
    if shortcut.target == "moss":
        target.meters["lifted"] = 0.0
        target.meters["scattered"] += 1
    prize = sim.get("prize")
    blocked = shortcut.target in {"lighthouse", "anchor", "moss"}
    return {
        "blocked": blocked,
        "target_label": target.label,
        "damage": shortcut.damage,
        "consequence": shortcut.consequence,
        "prize_found": prize.meters["found"] >= THRESHOLD,
    }


def article_for(phrase: str) -> str:
    return "an" if phrase[:1].lower() in "aeiou" else "a"


def introduce(world: World, hero: Entity, helper: Entity, kitchen: Kitchen,
              lighthouse: CrystalLighthouse, anchor: AnchorMark,
              moss: MossPatch) -> None:
    hero.memes["curiosity"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Once upon a time, {hero.id} and {helper.id} stood in {kitchen.phrase}. "
        f"{kitchen.weather}. The room felt like {kitchen.mood}."
    )
    world.say(
        f"On {kitchen.counter} stood {lighthouse.phrase}. Near {anchor.place} sat "
        f"{moss.phrase}, soft as a tiny island."
    )


def announce_problem(world: World, hero: Entity, helper: Entity, twist: Twist) -> None:
    hero.memes["mission"] += 1
    world.say(
        f'"Captain Kitchen needs help," {helper.id} said. They were hunting for '
        f"{twist.apparent} before supper."
    )
    world.say(
        f"{hero.id} stared at the crystal lighthouse and felt sure the treasure "
        "must be inside."
    )


def study_lighthouse(world: World, hero: Entity, helper: Entity,
                     lighthouse: CrystalLighthouse) -> None:
    lighthouse_ent = world.get("lighthouse")
    lighthouse_ent.meters["turned"] += 1
    world.say(
        f"{hero.id} cupped the crystal lighthouse with careful hands and turned it "
        f"until {lighthouse.lens} caught the light."
    )
    propagate(world)
    if lighthouse_ent.meters["guiding"] >= THRESHOLD:
        world.say(
            f"{article_for(lighthouse.beam).capitalize()} {lighthouse.beam} slid across the room. "
            f'"Look," {helper.id} whispered. "{lighthouse.hint}"'
        )


def tempt_shortcut(world: World, hero: Entity, helper: Entity,
                   shortcut: Shortcut) -> None:
    shortcut_ent = world.get("shortcut")
    shortcut_ent.meters["noticed"] += 1
    shortcut_ent.meters["lure"] = float(shortcut.lure)
    prediction = predict_shortcut(world, shortcut)
    world.facts["prediction"] = prediction
    world.say(f"Then {hero.id} had a fast idea: {shortcut.temptation}.")
    world.say(f'{shortcut.thought} {hero.id} thought.')
    if prediction["blocked"]:
        world.say(
            f'"Wait," {helper.id} said. "If you do that, {shortcut.consequence}"'
        )
    propagate(world)


def refuse_shortcut(world: World, hero: Entity, shortcut: Shortcut) -> None:
    hero.memes["patience"] += 1
    world.say(
        f"But {hero.id} took a breath instead. {shortcut.safe_choice}"
    )
    propagate(world)


def follow_beam(world: World, hero: Entity, lighthouse: CrystalLighthouse,
                anchor: AnchorMark) -> None:
    anchor_ent = world.get("anchor")
    propagate(world)
    if anchor_ent.meters["lit"] >= THRESHOLD:
        world.say(
            f"The {lighthouse.beam} landed on {anchor.phrase} at {anchor.place}."
        )
        world.say(
            f"{hero.id} saw that the anchor was not the prize at all. It was a marker."
        )


def reveal_twist(world: World, hero: Entity, helper: Entity, moss: MossPatch,
                 twist: Twist) -> None:
    moss_ent = world.get("moss")
    moss_ent.meters["lifted"] += 1
    world.say(
        f"{hero.id} knelt beside {moss.phrase} and lifted the fuzzy moss very slowly."
    )
    propagate(world)
    prize = world.get("prize")
    if prize.meters["found"] >= THRESHOLD:
        world.say(
            f"Under the fuzzy moss lay {twist.prize}. {twist.reveal}"
        )
    world.say(f"That was the twist: {twist.truth}.")
    helper.memes["delight"] += 1


def ending(world: World, hero: Entity, helper: Entity, twist: Twist) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(twist.ending)
    world.say(
        f"In the warm kitchen light, {twist.prize} rested beside the crystal "
        "lighthouse, and even the anchor seemed to smile."
    )


def tell(kitchen: Kitchen, lighthouse: CrystalLighthouse, moss: MossPatch,
         anchor: AnchorMark, shortcut: Shortcut, twist: Twist, hero_name: str,
         hero_type: str, helper_name: str, helper_type: str, care: int) -> World:
    if not route_matches(kitchen, lighthouse, moss, anchor, twist):
        raise StoryError(explain_rejection(kitchen, lighthouse, moss, anchor, twist))
    if not care_sufficient(shortcut, care):
        raise StoryError(
            f"(No story: care={care} is too rough for {shortcut.label}; "
            f"try --care {max(CARE_MIN, shortcut.lure)} or higher.)"
        )

    world = World(kitchen)
    hero = world.add(Entity("hero", kind="character", type=hero_type, label=hero_name))
    hero.id = hero_name
    hero.memes["care"] = float(care)
    helper = world.add(Entity("helper", kind="character", type=helper_type, label=helper_name))
    helper.id = helper_name
    world.add(
        Entity(
            "lighthouse",
            type="crystal lighthouse",
            label=lighthouse.label,
            phrase=lighthouse.phrase,
            location=kitchen.counter,
            attrs={"key": lighthouse.key},
        )
    )
    world.add(
        Entity(
            "moss",
            type="fuzzy moss",
            label=moss.label,
            phrase=moss.phrase,
            location=moss.area,
            attrs={"key": moss.key},
        )
    )
    world.add(
        Entity(
            "anchor",
            type="anchor",
            label=anchor.label,
            phrase=anchor.phrase,
            location=anchor.place,
            attrs={"key": anchor.key},
        )
    )
    world.add(
        Entity(
            "shortcut",
            type="shortcut",
            label=shortcut.label,
            attrs={"lure": shortcut.lure},
        )
    )
    world.add(
        Entity(
            "prize",
            type="treasure",
            label=twist.prize,
            phrase=twist.prize,
            attrs={"key": twist.key},
        )
    )

    introduce(world, hero, helper, kitchen, lighthouse, anchor, moss)
    announce_problem(world, hero, helper, twist)

    world.para()
    study_lighthouse(world, hero, helper, lighthouse)
    tempt_shortcut(world, hero, helper, shortcut)
    refuse_shortcut(world, hero, shortcut)

    world.para()
    follow_beam(world, hero, lighthouse, anchor)
    reveal_twist(world, hero, helper, moss, twist)
    ending(world, hero, helper, twist)

    world.facts.update(
        hero=hero,
        helper=helper,
        kitchen=kitchen,
        lighthouse=lighthouse,
        moss=moss,
        anchor=anchor,
        shortcut=shortcut,
        twist=twist,
        prize=world.get("prize"),
        outcome=outcome_of(
            StoryParams(
                kitchen.id,
                lighthouse.id,
                moss.id,
                anchor.id,
                shortcut.id,
                twist.id,
                hero_name,
                hero_type,
                helper_name,
                helper_type,
                care,
            )
        ),
        care=care,
    )
    return world


KITCHENS = {
    "galley_sink": Kitchen(
        "galley_sink",
        "Grandma's kitchen by the sink",
        "Rain tapped the window in neat silver dots",
        "the flour-dusted counter",
        "a ship's bright little galley",
        {"sink_blue", "pantry_gold"},
        tags={"kitchen", "adventure", "rain"},
    ),
    "sunny_stove": Kitchen(
        "sunny_stove",
        "the sunny kitchen near the stove",
        "Golden light slid over the tiles",
        "the warm wooden counter",
        "a captain's cabin at noon",
        {"stove_amber", "sink_blue"},
        tags={"kitchen", "adventure", "sun"},
    ),
    "pantry_cove": Kitchen(
        "pantry_cove",
        "the kitchen beside the pantry door",
        "The room hummed softly with the fridge and the kettle",
        "the blue enamel table",
        "a snug harbor room",
        {"pantry_gold", "fridge_silver"},
        tags={"kitchen", "adventure", "harbor"},
    ),
}

LIGHTHOUSES = {
    "blue_lighthouse": CrystalLighthouse(
        "blue_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse no taller than a mug",
        "its blue glass roof",
        "blue beam",
        "The little beam is pointing somewhere on purpose.",
        "sink_blue",
        tags={"crystal", "lighthouse", "blue"},
    ),
    "silver_lighthouse": CrystalLighthouse(
        "silver_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with a silver window band",
        "its silver window band",
        "silver beam",
        "The light keeps skipping toward the cold end of the room.",
        "fridge_silver",
        tags={"crystal", "lighthouse", "silver"},
    ),
    "gold_lighthouse": CrystalLighthouse(
        "gold_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with a gold-tipped lantern",
        "its gold-tipped lantern",
        "gold beam",
        "The beam is sailing toward the pantry like a tiny sun.",
        "pantry_gold",
        tags={"crystal", "lighthouse", "gold"},
    ),
    "amber_lighthouse": CrystalLighthouse(
        "amber_lighthouse",
        "the crystal lighthouse",
        "a crystal lighthouse with an amber door",
        "its amber door",
        "amber beam",
        "The glow is drifting toward the warm side of the kitchen.",
        "stove_amber",
        tags={"crystal", "lighthouse", "amber"},
    ),
}

MOSS_PATCHES = {
    "sink_mint_moss": MossPatch(
        "sink_mint_moss",
        "the fuzzy moss",
        "the fuzzy moss around the mint pot",
        "soft and springy",
        "the mint pot near the sink",
        "a curled paper ribbon",
        "sink_blue",
        tags={"moss", "herbs", "sink"},
    ),
    "fridge_sprout_moss": MossPatch(
        "fridge_sprout_moss",
        "the fuzzy moss",
        "the fuzzy moss under the sprout tray",
        "cool and feathery",
        "the sprout tray by the fridge",
        "a tiny brass key",
        "fridge_silver",
        tags={"moss", "sprouts", "fridge"},
    ),
    "pantry_jar_moss": MossPatch(
        "pantry_jar_moss",
        "the fuzzy moss",
        "the fuzzy moss beside the flour jar",
        "velvet-soft and thick",
        "the flour jar near the pantry",
        "a rolled ribbon map",
        "pantry_gold",
        tags={"moss", "pantry", "flour"},
    ),
    "stove_basil_moss": MossPatch(
        "stove_basil_moss",
        "the fuzzy moss",
        "the fuzzy moss around the basil cup",
        "warm and fluffy",
        "the basil cup by the stove",
        "a tiny bell token",
        "stove_amber",
        tags={"moss", "basil", "stove"},
    ),
}

ANCHORS = {
    "sink_anchor_rest": AnchorMark(
        "sink_anchor_rest",
        "the anchor spoon rest",
        "the anchor spoon rest",
        "the sink tiles",
        "it marked the mint pot like a harbor sign",
        "sink_blue",
        tags={"anchor", "sink"},
    ),
    "fridge_anchor_magnet": AnchorMark(
        "fridge_anchor_magnet",
        "the anchor magnet",
        "the anchor magnet",
        "the side of the fridge",
        "it pointed down toward the sprout tray",
        "fridge_silver",
        tags={"anchor", "fridge"},
    ),
    "pantry_anchor_hook": AnchorMark(
        "pantry_anchor_hook",
        "the anchor hook",
        "the anchor hook",
        "the pantry frame",
        "it hung above the flour jar like a tiny harbor mark",
        "pantry_gold",
        tags={"anchor", "pantry"},
    ),
    "stove_anchor_cutter": AnchorMark(
        "stove_anchor_cutter",
        "the anchor cookie cutter",
        "the anchor cookie cutter",
        "the stove shelf",
        "it leaned toward the basil cup like a shiny arrow",
        "stove_amber",
        tags={"anchor", "stove"},
    ),
}

SHORTCUTS = {
    "pry_lens": Shortcut(
        "pry_lens",
        "prying open the crystal lighthouse lens",
        "pop the top of the crystal lighthouse and peek inside",
        '"Maybe the treasure is hiding in the lighthouse itself,"',
        "lighthouse",
        "cracked",
        "the crystal lighthouse would crack and stop guiding them.",
        "So the crystal lighthouse stayed whole, bright, and useful.",
        3,
        tags={"care", "crystal"},
    ),
    "yank_moss": Shortcut(
        "yank_moss",
        "yanking the fuzzy moss away in one grab",
        "snatch the fuzzy moss up all at once",
        '"Maybe the prize is under the moss, and I can grab it first,"',
        "moss",
        "scattered",
        "the fuzzy moss would scatter and the hidden thing could slip deeper away.",
        "So the fuzzy moss stayed soft and neat until the clue was clear.",
        4,
        tags={"care", "moss"},
    ),
    "grab_anchor": Shortcut(
        "grab_anchor",
        "grabbing the anchor and waving it around",
        "snatch the anchor marker and test every shelf with it",
        '"Maybe the anchor is the treasure, and I should grab it now,"',
        "anchor",
        "moved",
        "the anchor marker would stop showing the right place.",
        "So the anchor stayed exactly where the light needed it.",
        3,
        tags={"care", "anchor"},
    ),
}

TWISTS = {
    "mint_ribbon": Twist(
        "mint_ribbon",
        "Grandma's sail-shaped recipe ribbon",
        "the crystal lighthouse was not hiding the treasure at all; it was showing the way to it",
        "The tiny prize had been tucked there to stay dry until the light could find it.",
        "Grandma laughed, tied the ribbon around the mixing spoon, and said the kitchen had earned its captain for the day.",
        "Grandma's sail-shaped recipe ribbon",
        "sink_blue",
        tags={"twist", "recipe", "sink"},
    ),
    "sprout_key": Twist(
        "sprout_key",
        "the brass key to the biscuit tin",
        "the shining tower was a guide, and the real treasure was the key sleeping under the moss",
        "The children had been staring at the brightest thing in the room, while the real answer waited in the softest place.",
        "Soon the biscuit tin clicked open, and the whole kitchen smelled like sweet cinnamon treasure.",
        "the brass key to the biscuit tin",
        "fridge_silver",
        tags={"twist", "key", "fridge"},
    ),
    "pantry_map": Twist(
        "pantry_map",
        "the rolled map to the hidden snack shelf",
        "the lighthouse was a pointer, not a box, and the anchor showed where the moss kept the map safe",
        "The rolled map was dry and tidy, tucked where no flour puff could reach it.",
        "The children followed the map to the top pantry shelf and found the snack chest waiting like a calm little treasure cove.",
        "the rolled map to the hidden snack shelf",
        "pantry_gold",
        tags={"twist", "map", "pantry"},
    ),
    "basil_bell": Twist(
        "basil_bell",
        "the tiny supper bell token",
        "the crystal lighthouse was only the clue, and the anchor marked the quiet moss where the bell token had been resting",
        "Instead of a secret inside the lighthouse, the children found a secret the lighthouse could reveal.",
        "When the token rang against a spoon, everyone came smiling to the table as if a harbor bell had called them home.",
        "the tiny supper bell token",
        "stove_amber",
        tags={"twist", "bell", "stove"},
    ),
}

GIRL_NAMES = ["Mara", "Lina", "Nora", "Ava", "Tess", "Ruby"]
BOY_NAMES = ["Finn", "Eli", "Max", "Owen", "Jude", "Theo"]


@dataclass
class StoryParams:
    kitchen: str
    lighthouse: str
    moss: str
    anchor: str
    shortcut: str
    twist: str
    hero: str
    gender: str
    helper: str
    helper_gender: str
    care: int
    seed: Optional[int] = None


KNOWLEDGE = {
    "lighthouse": [
        (
            "What does a lighthouse do?",
            "A lighthouse helps guide people by sending out a bright signal. It does not have to hold treasure to be important.",
        )
    ],
    "crystal": [
        (
            "Why can crystal make bright little beams?",
            "Crystal can catch and bend light. That is why it can throw a sparkle or beam across a room.",
        )
    ],
    "anchor": [
        (
            "What does an anchor do?",
            "An anchor helps hold a boat in place. In stories, an anchor can also work like a sign that marks a safe spot.",
        )
    ],
    "moss": [
        (
            "Why might fuzzy moss hide something gently?",
            "Fuzzy moss is soft, so it can cushion a tiny object. It also makes a hiding place look plain instead of shiny.",
        )
    ],
    "kitchen": [
        (
            "Why do kitchens make good tiny adventure places?",
            "Kitchens are full of shelves, jars, tools, and smells. A child can imagine them turning into harbors, ships, or treasure rooms.",
        )
    ],
    "care": [
        (
            "Why is being careful part of adventure?",
            "Good adventurers do not just move fast. They pay attention so they do not break the clue that can lead them home.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lighthouse", "crystal", "anchor", "moss", "kitchen", "care"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    kitchen = f["kitchen"]
    twist = f["twist"]
    return [
        'Write an Adventure story for young children using the words "anchor", '
        '"fuzzy moss", and "crystal lighthouse" in a kitchen.',
        f"Tell a kitchen adventure where {hero.id} follows a crystal lighthouse clue instead of forcing it open.",
        f"Write a short Twist story where the seeming treasure is wrong and the real prize is {twist.prize} in {kitchen.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    kitchen = f["kitchen"]
    lighthouse = f["lighthouse"]
    moss = f["moss"]
    anchor = f["anchor"]
    shortcut = f["shortcut"]
    twist = f["twist"]
    prediction = f.get("prediction", {})
    return [
        (
            "Where does the adventure happen?",
            f"It happens in {kitchen.phrase}. The room feels adventurous because {kitchen.weather.lower()} and the children imagine the kitchen as {kitchen.mood}.",
        ),
        (
            f"What did {hero.id} first think about the crystal lighthouse?",
            f"{hero.id} first thought the prize must be inside the crystal lighthouse. That mistaken guess sets up the twist later in the story.",
        ),
        (
            "Why did the children not use the fast shortcut?",
            f"They stopped because {helper.id} warned that {shortcut.consequence} That risk would have ruined the clue instead of solving it.",
        ),
        (
            "What did the light show them?",
            f"The {lighthouse.beam} landed on {anchor.phrase} at {anchor.place}. That told them the anchor was a marker and not the treasure itself.",
        ),
        (
            f"What was hidden under the fuzzy moss?",
            f"Under the fuzzy moss they found {twist.prize}. The moss kept it tucked away until the beam and anchor showed the right place.",
        ),
        (
            "What was the twist at the end?",
            f"The twist was that {twist.truth}. The brightest object in the kitchen was only the guide, while the real prize waited in the soft moss.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = (
        {"kitchen", "care", "lighthouse"}
        | set(f["lighthouse"].tags)
        | set(f["moss"].tags)
        | set(f["anchor"].tags)
        | set(f["shortcut"].tags)
    )
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:18}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("galley_sink", "blue_lighthouse", "sink_mint_moss", "sink_anchor_rest",
                "pry_lens", "mint_ribbon", "Mara", "girl", "Finn", "boy", 3),
    StoryParams("pantry_cove", "silver_lighthouse", "fridge_sprout_moss", "fridge_anchor_magnet",
                "grab_anchor", "sprout_key", "Eli", "boy", "Ruby", "girl", 3),
    StoryParams("pantry_cove", "gold_lighthouse", "pantry_jar_moss", "pantry_anchor_hook",
                "yank_moss", "pantry_map", "Nora", "girl", "Theo", "boy", 4),
    StoryParams("sunny_stove", "amber_lighthouse", "stove_basil_moss", "stove_anchor_cutter",
                "pry_lens", "basil_bell", "Max", "boy", "Ava", "girl", 3),
    StoryParams("sunny_stove", "blue_lighthouse", "sink_mint_moss", "sink_anchor_rest",
                "grab_anchor", "mint_ribbon", "Tess", "girl", "Owen", "boy", 3),
]


def explain_rejection(kitchen: Kitchen, lighthouse: CrystalLighthouse, moss: MossPatch,
                      anchor: AnchorMark, twist: Twist) -> str:
    if lighthouse.key not in kitchen.routes:
        return (
            f"(No story: {kitchen.phrase} does not give this crystal lighthouse a clear route. "
            "Pick a lighthouse whose beam belongs in that kitchen.)"
        )
    return (
        "(No story: the crystal lighthouse, anchor, fuzzy moss, and twist do not point to the "
        "same hiding route, so the kitchen clue would not resolve honestly.)"
    )


ASP_RULES = r"""
valid(K,L,M,A,T) :-
    kitchen_route(K,R),
    lighthouse_key(L,R),
    moss_key(M,R),
    anchor_key(A,R),
    twist_key(T,R).

rough(C,S) :-
    chosen_care(C),
    chosen_shortcut(S),
    shortcut_lure(S,L),
    C < L.

outcome(route_mismatch) :-
    chosen_kitchen(K),
    chosen_lighthouse(L),
    chosen_moss(M),
    chosen_anchor(A),
    chosen_twist(T),
    not valid(K,L,M,A,T).

outcome(too_rough) :-
    chosen_kitchen(K),
    chosen_lighthouse(L),
    chosen_moss(M),
    chosen_anchor(A),
    chosen_twist(T),
    valid(K,L,M,A,T),
    rough(C,S).

outcome(twist_found) :-
    chosen_kitchen(K),
    chosen_lighthouse(L),
    chosen_moss(M),
    chosen_anchor(A),
    chosen_twist(T),
    valid(K,L,M,A,T),
    chosen_care(C),
    chosen_shortcut(S),
    not rough(C,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kitchen_id, kitchen in KITCHENS.items():
        lines.append(asp.fact("kitchen", kitchen_id))
        for route in sorted(kitchen.routes):
            lines.append(asp.fact("kitchen_route", kitchen_id, route))
    for lighthouse_id, lighthouse in LIGHTHOUSES.items():
        lines.append(asp.fact("lighthouse", lighthouse_id))
        lines.append(asp.fact("lighthouse_key", lighthouse_id, lighthouse.key))
    for moss_id, moss in MOSS_PATCHES.items():
        lines.append(asp.fact("moss", moss_id))
        lines.append(asp.fact("moss_key", moss_id, moss.key))
    for anchor_id, anchor in ANCHORS.items():
        lines.append(asp.fact("anchor", anchor_id))
        lines.append(asp.fact("anchor_key", anchor_id, anchor.key))
    for twist_id, twist in TWISTS.items():
        lines.append(asp.fact("twist", twist_id))
        lines.append(asp.fact("twist_key", twist_id, twist.key))
    for shortcut_id, shortcut in SHORTCUTS.items():
        lines.append(asp.fact("shortcut", shortcut_id))
        lines.append(asp.fact("shortcut_lure", shortcut_id, shortcut.lure))
    lines.append(asp.fact("care_min", CARE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_kitchen", params.kitchen),
            asp.fact("chosen_lighthouse", params.lighthouse),
            asp.fact("chosen_moss", params.moss),
            asp.fact("chosen_anchor", params.anchor),
            asp.fact("chosen_twist", params.twist),
            asp.fact("chosen_shortcut", params.shortcut),
            asp.fact("chosen_care", params.care),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    values = asp.atoms(model, "outcome")
    return values[0][0] if values else "?"


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
    empty = build_parser().parse_args([])
    for seed in range(60):
        params = resolve_params(empty, random.Random(seed))
        cases.append(params)
    cases.extend(
        [
            StoryParams(
                "galley_sink",
                "silver_lighthouse",
                "sink_mint_moss",
                "sink_anchor_rest",
                "pry_lens",
                "mint_ribbon",
                "Mara",
                "girl",
                "Finn",
                "boy",
                3,
            ),
            StoryParams(
                "pantry_cove",
                "gold_lighthouse",
                "pantry_jar_moss",
                "pantry_anchor_hook",
                "yank_moss",
                "pantry_map",
                "Nora",
                "girl",
                "Theo",
                "boy",
                2,
            ),
        ]
    )
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)}/{len(cases)} outcomes differ.")
        for params in bad[:5]:
            print(" ", params, asp_outcome(params), outcome_of(params))

    try:
        checked = 0
        for params in CURATED:
            sample = generate(params)
            checked += 1
            story = sample.story.lower()
            required = ["anchor", "fuzzy moss", "crystal lighthouse"]
            if any(word not in story for word in required):
                raise StoryError("(verify failed: required seed words missing from rendered story.)")
            if "{" in sample.story or "}" in sample.story:
                raise StoryError("(verify failed: unresolved template marker in story.)")
            if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
                raise StoryError("(verify failed: QA sets are too small.)")
        print(f"OK: rendered {checked} curated stories with seed words and QA.")
    except StoryError as err:
        rc = 1
        print(err)
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: anchor, fuzzy moss, crystal lighthouse, kitchen twist. "
                    "Unspecified choices are randomized from valid adventure setups."
    )
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--lighthouse", choices=LIGHTHOUSES)
    ap.add_argument("--moss", choices=MOSS_PATCHES)
    ap.add_argument("--anchor", choices=ANCHORS)
    ap.add_argument("--shortcut", choices=SHORTCUTS)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--care", type=int, choices=[3, 4, 5])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP twin against Python logic")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the ASP facts and rules")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.kitchen and args.lighthouse and args.moss and args.anchor and args.twist:
        if (args.kitchen, args.lighthouse, args.moss, args.anchor, args.twist) not in set(valid_combos()):
            raise StoryError(
                explain_rejection(
                    KITCHENS[args.kitchen],
                    LIGHTHOUSES[args.lighthouse],
                    MOSS_PATCHES[args.moss],
                    ANCHORS[args.anchor],
                    TWISTS[args.twist],
                )
            )

    combos = [
        combo for combo in valid_combos()
        if (args.kitchen is None or combo[0] == args.kitchen)
        and (args.lighthouse is None or combo[1] == args.lighthouse)
        and (args.moss is None or combo[2] == args.moss)
        and (args.anchor is None or combo[3] == args.anchor)
        and (args.twist is None or combo[4] == args.twist)
    ]
    if not combos:
        raise StoryError("(No valid kitchen route matches the given options.)")

    kitchen_id, lighthouse_id, moss_id, anchor_id, twist_id = rng.choice(combos)
    shortcut_id = args.shortcut or rng.choice(sorted(SHORTCUTS))
    shortcut = SHORTCUTS[shortcut_id]
    care = args.care if args.care is not None else rng.randint(max(CARE_MIN, shortcut.lure), 5)
    if not care_sufficient(shortcut, care):
        raise StoryError(
            f"(No story: care={care} is too low for {shortcut.label}; "
            f"pick --care {max(CARE_MIN, shortcut.lure)} or higher.)"
        )

    gender = args.gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, gender)
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    helper = args.helper or _pick_name(rng, helper_gender, avoid=hero)
    return StoryParams(
        kitchen_id,
        lighthouse_id,
        moss_id,
        anchor_id,
        shortcut_id,
        twist_id,
        hero,
        gender,
        helper,
        helper_gender,
        care,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        KITCHENS[params.kitchen],
        LIGHTHOUSES[params.lighthouse],
        MOSS_PATCHES[params.moss],
        ANCHORS[params.anchor],
        SHORTCUTS[params.shortcut],
        TWISTS[params.twist],
        params.hero,
        params.gender,
        params.helper,
        params.helper_gender,
        params.care,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("", "#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (kitchen, lighthouse, moss, anchor, twist) combos:\n")
        for kitchen, lighthouse, moss, anchor, twist in combos:
            print(f"  {kitchen:12} {lighthouse:18} {moss:18} {anchor:20} {twist}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 80, 80):
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
                f"### {p.hero}: {p.lighthouse} + {p.moss} + {p.anchor} in {p.kitchen}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
