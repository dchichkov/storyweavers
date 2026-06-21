#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py
=====================================================

A standalone storyworld about Ole, a pretend pirate, and the kind of bravery
that grows when a scary problem is met with a careful plan.

Reference seed
--------------
Words: ole
Features: Bravery
Style: Pirate Tale

World idea
----------
Ole and a friend turn a shore-side place into a pirate deck. A gust or wobble
carries their tiny treasure into a spot that feels scary: a dark cave mouth, a
high beam, or a gap over splashing water. Ole wants the treasure back, but fear
arrives first. The world only permits stories where the chosen tool is the
right tool for the obstacle. Bravery here is not wild daring. It is the moment
Ole admits he is scared, listens to good advice, uses sensible gear, and then
takes the careful step.

Run it
------
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py --place cove --obstacle cave_mouth --gear lantern
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py --obstacle mast_beam --gear lantern
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py --all
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/ole_bravery_pirate_tale.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root. This file lives one level deeper than most worlds:
# storyworlds/worlds/gpt-5.4/<file>.py -> add storyworlds/ to sys.path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother", "aunt"}
        male = {"boy", "man", "grandfather", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    scene: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    place_text: str
    threat_text: str
    need: str
    fear_text: str
    success_text: str
    image_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    satisfies: set[str] = field(default_factory=set)
    offer_text: str = ""
    use_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    shine_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    obstacle: str
    treasure: str
    gear: str
    companion_name: str
    companion_gender: str
    ole_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lost_treasure(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.entities.get("treasure")
    ole = world.entities.get("Ole")
    if treasure is None or ole is None:
        return out
    if treasure.meters["lost"] < THRESHOLD:
        return out
    sig = ("lost_treasure",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ole.memes["worry"] += 1
    ole.memes["fear"] += float(world.facts["obstacle_cfg"].attrs["fear"])
    out.append("__lost__")
    return out


def _r_prepared(world: World) -> list[str]:
    out: list[str] = []
    gear_ent = world.entities.get("gear")
    ole = world.entities.get("Ole")
    if gear_ent is None or ole is None:
        return out
    if gear_ent.meters["equipped"] < THRESHOLD:
        return out
    sig = ("prepared",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ole.meters["prepared"] += 1
    ole.memes["bravery"] += 2
    ole.memes["fear"] = max(0.0, ole.memes["fear"] - 1.0)
    out.append("__prepared__")
    return out


def _r_recovered(world: World) -> list[str]:
    out: list[str] = []
    treasure = world.entities.get("treasure")
    ole = world.entities.get("Ole")
    if treasure is None or ole is None:
        return out
    if treasure.meters["lost"] < THRESHOLD or ole.meters["prepared"] < THRESHOLD:
        return out
    sig = ("recovered",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    treasure.meters["recovered"] += 1
    treasure.meters["lost"] = 0.0
    ole.memes["relief"] += 1
    ole.memes["pride"] += 1
    out.append("__recovered__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="lost_treasure", tag="emotion", apply=_r_lost_treasure),
    Rule(name="prepared", tag="emotion", apply=_r_prepared),
    Rule(name="recovered", tag="physical", apply=_r_recovered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def gear_fits(obstacle: Obstacle, gear: Gear) -> bool:
    return obstacle.need in gear.satisfies


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for obstacle_id in sorted(setting.affords):
            obstacle = OBSTACLES[obstacle_id]
            for treasure_id in TREASURES:
                for gear_id, gear in GEARS.items():
                    if gear_fits(obstacle, gear):
                        combos.append((place_id, obstacle_id, treasure_id, gear_id))
    return combos


def explain_rejection(setting: Setting, obstacle: Obstacle, gear: Gear) -> str:
    if obstacle.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not have {obstacle.place_text}. "
            f"Pick an obstacle that fits the place.)"
        )
    return (
        f"(No story: {gear.label} does not solve {obstacle.label}. "
        f"This tale only allows brave plans that use the right tool for the danger.)"
    )


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_success(world: World, obstacle_id: str, gear_id: str) -> dict:
    sim = world.copy()
    obstacle = OBSTACLES[obstacle_id]
    gear = GEARS[gear_id]
    gear_ent = sim.get("gear")
    gear_ent.label = gear.label
    gear_ent.phrase = gear.phrase
    gear_ent.attrs["satisfies"] = set(gear.satisfies)
    if gear_fits(obstacle, gear):
        gear_ent.meters["equipped"] += 1
        propagate(sim, narrate=False)
    treasure = sim.get("treasure")
    ole = sim.get("Ole")
    return {
        "safe": treasure.meters["recovered"] >= THRESHOLD,
        "prepared": ole.meters["prepared"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, ole: Entity, friend: Entity, treasure: Treasure) -> None:
    world.say(
        f"On a bright afternoon, Ole and {friend.id} made {world.setting.place} feel like {world.setting.scene}."
    )
    world.say(
        f"Ole tied a towel around his shoulders like a captain's coat, and {friend.id} tucked {treasure.phrase} into a biscuit tin for pirate treasure."
    )


def play_goal(world: World, ole: Entity, friend: Entity, treasure: Treasure) -> None:
    ole.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f'"Captain Ole!" {friend.id} cried. "If we keep sailing, we will find the place where {treasure.label} belongs."'
    )
    world.say(
        f"Ole grinned. For a while, every rock was a sea beast and every gull cry sounded like a sailor's song."
    )


def mishap(world: World, ole: Entity, friend: Entity, obstacle: Obstacle, treasure_ent: Entity, treasure: Treasure) -> None:
    treasure_ent.meters["lost"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a sudden gust skipped over the shore and snatched the biscuit tin lid. Out tumbled {treasure.phrase}, and it slid straight to {obstacle.place_text}."
    )
    world.say(
        f"{treasure.shine_text} now it looked terribly far away."
    )
    world.say(
        f"Ole took one step after it, then stopped. {obstacle.fear_text}"
    )


def admit_fear(world: World, ole: Entity, obstacle: Obstacle) -> None:
    world.say(
        f'"I want it back," Ole whispered, "but {obstacle.threat_text}."'
    )


def companion_warns(world: World, friend: Entity, ole: Entity, obstacle: Obstacle, gear: Gear) -> None:
    world.say(
        f'{friend.id} did not laugh. "{obstacle.threat_text.capitalize()},"
        f" {friend.pronoun()} said. "Real captains do not charge at trouble with empty hands."'
    )
    pred = predict_success(world, obstacle.id, gear.id)
    world.facts["predicted_safe"] = pred["safe"]
    if pred["safe"]:
        world.say(
            f'"But if we bring {gear.phrase}, we can make a careful plan," {friend.id} said.'
        )


def fetch_gear(world: World, ole: Entity, friend: Entity, gear_ent: Entity, gear: Gear) -> None:
    gear_ent.label = gear.label
    gear_ent.phrase = gear.phrase
    gear_ent.attrs["satisfies"] = set(gear.satisfies)
    world.say(
        f"So they ran to their play pile and found {gear.phrase}. {gear.offer_text}"
    )


def equip_and_try(world: World, ole: Entity, friend: Entity, obstacle: Obstacle, gear_ent: Entity, gear: Gear, treasure: Treasure) -> None:
    gear_ent.meters["equipped"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Ole held {gear.label} so tightly that his knuckles turned pale. His heart still thumped, but now the thump felt useful instead of wild."
    )
    world.say(
        f'{friend.id} stood close beside him. "Slow and steady, Captain Ole," {friend.pronoun()} said.'
    )
    world.say(
        f"{gear.use_text} {obstacle.success_text}"
    )
    propagate(world, narrate=False)
    world.say(
        f"In one careful moment, Ole reached {treasure.phrase} and pulled it back to his chest."
    )


def brave_lesson(world: World, ole: Entity, friend: Entity, obstacle: Obstacle, treasure: Treasure) -> None:
    ole.memes["lesson"] += 1
    friend.memes["love"] += 1
    world.say(
        f"Ole let out a long breath that sounded almost like a laugh. The scary place was still {obstacle.label}, but it no longer felt bigger than he was."
    )
    world.say(
        f'"I was scared," Ole said, "and I still did the careful thing."'
    )
    world.say(
        f'"That is bravery," {friend.id} answered. "Not pretending the fear is gone. Just choosing the good step anyway."'
    )
    world.say(
        f"Then Captain Ole lifted {treasure.phrase} high above his head, and the little pirates sailed on with straighter backs and brighter eyes."
    )


# ---------------------------------------------------------------------------
# Story driver
# ---------------------------------------------------------------------------
def tell(setting: Setting, obstacle: Obstacle, treasure: Treasure, gear: Gear,
         companion_name: str = "Mira", companion_gender: str = "girl",
         ole_trait: str = "careful") -> World:
    world = World(setting)
    ole = world.add(Entity(
        id="Ole",
        kind="character",
        type="boy",
        role="hero",
        label="Ole",
        attrs={"trait": ole_trait},
    ))
    friend = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_gender,
        role="companion",
        label=companion_name,
    ))
    treasure_ent = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        tags=set(treasure.tags),
    ))
    gear_ent = world.add(Entity(
        id="gear",
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.phrase,
        attrs={"satisfies": set(gear.satisfies)},
        tags=set(gear.tags),
    ))

    fear_base = TRAIT_FEAR[ole_trait]
    obstacle_view = copy.deepcopy(obstacle)
    obstacle_view.attrs = {"fear": fear_base + OBSTACLE_FEAR[obstacle.id]}

    world.facts.update(
        ole=ole,
        companion=friend,
        treasure_cfg=treasure,
        obstacle_cfg=obstacle_view,
        gear_cfg=gear,
        setting=setting,
    )

    introduce(world, ole, friend, treasure)
    play_goal(world, ole, friend, treasure)

    world.para()
    mishap(world, ole, friend, obstacle_view, treasure_ent, treasure)
    admit_fear(world, ole, obstacle_view)
    companion_warns(world, friend, ole, obstacle_view, gear)

    world.para()
    fetch_gear(world, ole, friend, gear_ent, gear)
    equip_and_try(world, ole, friend, obstacle_view, gear_ent, gear, treasure)

    world.para()
    brave_lesson(world, ole, friend, obstacle_view, treasure)

    world.facts.update(
        recovered=treasure_ent.meters["recovered"] >= THRESHOLD,
        bravery=ole.memes["bravery"],
        fear=ole.memes["fear"],
        prepared=ole.meters["prepared"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cove": Setting(
        id="cove",
        place="the little cove",
        scene="a pirate cove with hidden routes between the stones",
        affords={"cave_mouth", "tide_gap"},
    ),
    "harbor": Setting(
        id="harbor",
        place="the old harbor wall",
        scene="a bustling pirate dock with planks and lookout posts",
        affords={"mast_beam", "tide_gap"},
    ),
    "beach": Setting(
        id="beach",
        place="the windy beach",
        scene="a broad pirate shore where the waves kept trying to steal secrets",
        affords={"cave_mouth", "mast_beam"},
    ),
}

OBSTACLES = {
    "cave_mouth": Obstacle(
        id="cave_mouth",
        label="the dark cave mouth",
        place_text="the dark cave mouth under the cliff",
        threat_text="it is dark in there",
        need="light",
        fear_text="The black opening looked like a giant pirate's yawn, and Ole could not see where to place his feet.",
        success_text="The small circle of light slid over the stone and showed a dry, safe path between the puddles.",
        image_text="the cave mouth glowed softly instead of glaring black",
        tags={"cave", "light"},
    ),
    "mast_beam": Obstacle(
        id="mast_beam",
        label="the high beam",
        place_text="a high beam on the harbor frame",
        threat_text="it is too high to reach safely",
        need="reach",
        fear_text="The beam sat high overhead, and the treasure looked smaller and smaller the longer Ole stared at it.",
        success_text="The careful reach brought the treasure close without any climbing at all.",
        image_text="the high beam no longer seemed to sneer down at him",
        tags={"high", "reach"},
    ),
    "tide_gap": Obstacle(
        id="tide_gap",
        label="the splashing gap",
        place_text="a narrow gap where sea water slapped between two rocks",
        threat_text="the stones there are slippery",
        need="steady",
        fear_text="Water snapped and splashed between the rocks, and Ole did not trust the shiny stones to hold him.",
        success_text="With a steady line in hand, each step had somewhere safe to lean.",
        image_text="the splashing gap looked like a path, not a trap",
        tags={"water", "steady"},
    ),
}

GEARS = {
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a little brass lantern",
        satisfies={"light"},
        offer_text="Mira rubbed the glass with her sleeve until it shone like a warm star.",
        use_text="Ole lifted the lantern first and peered where the light reached.",
        tags={"lantern", "light"},
    ),
    "hook_pole": Gear(
        id="hook_pole",
        label="hook pole",
        phrase="a long hook pole made from a driftwood stick",
        satisfies={"reach"},
        offer_text="They had made it that morning by tying a bent spoon to the end with string.",
        use_text="Ole planted his feet, stretched out the hook pole, and nudged the treasure gently toward himself.",
        tags={"hook", "reach"},
    ),
    "rope_line": Gear(
        id="rope_line",
        label="rope line",
        phrase="a thick rope line",
        satisfies={"steady"},
        offer_text="Ole looped it over the rock the way he had seen boat hands do.",
        use_text="Ole held the rope line with both hands and moved one foot, then the next.",
        tags={"rope", "water"},
    ),
}

TREASURES = {
    "ruby_button": Treasure(
        id="ruby_button",
        label="the ruby button",
        phrase="a red button they called the ruby of the sea",
        shine_text="It flashed once in the sun, and then",
        tags={"treasure"},
    ),
    "shell_coin": Treasure(
        id="shell_coin",
        label="the shell coin",
        phrase="a pale shell coin with a hole through the middle",
        shine_text="It twinkled like a drop of moonlight, but",
        tags={"treasure", "shell"},
    ),
    "brass_key": Treasure(
        id="brass_key",
        label="the brass key",
        phrase="a tiny brass key from their toy chest",
        shine_text="It gave one brave little gleam, and then",
        tags={"treasure", "key"},
    ),
}

COMPANION_NAMES = {
    "girl": ["Mira", "Nora", "Ava", "Lena", "Lucy"],
    "boy": ["Finn", "Toby", "Max", "Eli", "Sam"],
}

OLE_TRAITS = ["careful", "shaky", "thoughtful", "steady"]
TRAIT_FEAR = {
    "careful": 2,
    "shaky": 3,
    "thoughtful": 2,
    "steady": 1,
}
OBSTACLE_FEAR = {
    "cave_mouth": 1,
    "mast_beam": 1,
    "tide_gap": 2,
}

CURATED = [
    StoryParams(
        place="cove",
        obstacle="cave_mouth",
        treasure="shell_coin",
        gear="lantern",
        companion_name="Mira",
        companion_gender="girl",
        ole_trait="careful",
    ),
    StoryParams(
        place="harbor",
        obstacle="mast_beam",
        treasure="brass_key",
        gear="hook_pole",
        companion_name="Finn",
        companion_gender="boy",
        ole_trait="thoughtful",
    ),
    StoryParams(
        place="cove",
        obstacle="tide_gap",
        treasure="ruby_button",
        gear="rope_line",
        companion_name="Nora",
        companion_gender="girl",
        ole_trait="shaky",
    ),
    StoryParams(
        place="beach",
        obstacle="mast_beam",
        treasure="shell_coin",
        gear="hook_pole",
        companion_name="Sam",
        companion_gender="boy",
        ole_trait="steady",
    ),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cave": [
        (
            "Why is a dark cave hard to explore safely?",
            "A dark cave is hard to explore because you cannot see where your feet should go. When you cannot see well, it is easier to trip or step somewhere unsafe.",
        )
    ],
    "light": [
        (
            "Why does a lantern help in dark places?",
            "A lantern makes light, so you can see the ground and the walls around you. Seeing clearly helps you choose careful steps.",
        )
    ],
    "high": [
        (
            "Why is climbing for something high up sometimes unsafe?",
            "Something high up can tempt you to stretch or climb too much. If you cannot reach it safely from the ground, it is better to use the right tool or ask for help.",
        )
    ],
    "reach": [
        (
            "What is a hook pole for?",
            "A hook pole helps you pull something closer without climbing. It lets you reach from a safer place.",
        )
    ],
    "water": [
        (
            "Why are wet rocks slippery?",
            "Wet rocks can be slippery because water makes their surface slick. Feet can slide on slick stone more easily.",
        )
    ],
    "steady": [
        (
            "How can a rope help someone cross carefully?",
            "A rope gives your hands something steady to hold. That extra support can help your balance while you move slowly.",
        )
    ],
    "bravery": [
        (
            "What does bravery mean?",
            "Bravery does not mean you never feel scared. It means you choose a careful, good step even while your heart is beating fast.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cave", "light", "high", "reach", "water", "steady", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    setting = f["setting"]
    companion = f["companion"]
    return [
        f'Write a pirate tale for a 3-to-5-year-old about Ole being brave at {setting.place}. Include the word "Ole".',
        f"Tell a gentle story where Ole and {companion.id} lose {treasure.label} at {obstacle.place_text}, and Ole learns that bravery can be careful.",
        f"Write a small pirate adventure with a scary middle, the right tool for the problem, and an ending image that shows Captain Ole standing taller than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    ole = f["ole"]
    companion = f["companion"]
    obstacle = f["obstacle_cfg"]
    treasure = f["treasure_cfg"]
    gear = f["gear_cfg"]
    setting = f["setting"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Ole and {companion.id}, two children pretending to be pirates at {setting.place}. The story follows Ole most closely because he has to face the scary part.",
        ),
        (
            "What problem started the adventure?",
            f"Their treasure slipped away and landed at {obstacle.place_text}. Ole wanted it back, but the place felt scary because {obstacle.threat_text}.",
        ),
        (
            "How did Ole feel when he saw where the treasure had gone?",
            f"Ole felt scared and stopped instead of rushing in. That pause matters because it showed he understood the danger before he tried to be brave.",
        ),
        (
            f"How did {companion.id} help Ole?",
            f"{companion.id} did not tease Ole for being afraid. {companion.pronoun('subject').capitalize()} helped him choose {gear.phrase}, because that tool matched the problem and made a careful plan possible.",
        ),
    ]
    if f.get("recovered"):
        qa.append(
            (
                "How did Ole get the treasure back?",
                f"Ole used {gear.phrase} and moved carefully instead of charging ahead. The right tool changed the scary place into something he could handle one safe step at a time.",
            )
        )
        qa.append(
            (
                "What did Ole learn about bravery?",
                "Ole learned that bravery is not acting as if nothing is scary. It is admitting the fear, making a sensible plan, and then doing the careful thing anyway.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with Captain Ole holding {treasure.phrase} high again. That final image shows he did not shrink from the adventure anymore after solving the problem the safe way.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"bravery"}
    tags |= set(world.facts["obstacle_cfg"].tags)
    tags |= set(world.facts["gear_cfg"].tags)
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
fits(O, G) :- obstacle(O), gear(G), needs(O, N), satisfies(G, N).
valid(P, O, T, G) :- setting(P), obstacle(O), treasure(T), gear(G), affords(P, O), fits(O, G).
safe_plan(O, G) :- fits(O, G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for oid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, obstacle.need))
    for gid, gear in GEARS.items():
        lines.append(asp.fact("gear", gid))
        for need in sorted(gear.satisfies):
            lines.append(asp.fact("satisfies", gid, need))
    for tid in TREASURES:
        lines.append(asp.fact("treasure", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_plan(obstacle: str, gear: str) -> bool:
    import asp
    extra = "\n".join([asp.fact("chosen_obstacle", obstacle), asp.fact("chosen_gear", gear), "query_safe :- chosen_obstacle(O), chosen_gear(G), safe_plan(O, G)."])
    model = asp.one_model(asp_program(extra, "#show query_safe/0."))
    atoms = asp.atoms(model, "query_safe")
    return bool(atoms)


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

    for obstacle_id, obstacle in OBSTACLES.items():
        for gear_id, gear in GEARS.items():
            py = gear_fits(obstacle, gear)
            asp_ok = asp_safe_plan(obstacle_id, gear_id)
            if py != asp_ok:
                rc = 1
                print(f"MISMATCH in safe_plan({obstacle_id}, {gear_id}): python={py} asp={asp_ok}")

    smoke_cases = list(CURATED)
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE resolve failed: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE generation failed for {params}: {err}")

    if rc == 0:
        print(f"OK: smoke-generated {len(smoke_cases)} stories.")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Ole learns careful bravery in a pirate tale."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--companion-name")
    ap.add_argument("--ole-trait", choices=OLE_TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.gear:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        gear = GEARS[args.gear]
        if obstacle.id not in setting.affords or not gear_fits(obstacle, gear):
            raise StoryError(explain_rejection(setting, obstacle, gear))
    elif args.obstacle and args.gear:
        obstacle = OBSTACLES[args.obstacle]
        gear = GEARS[args.gear]
        if not gear_fits(obstacle, gear):
            setting = SETTINGS[args.place] if args.place else next(iter(SETTINGS.values()))
            raise StoryError(explain_rejection(setting, obstacle, gear))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.treasure is None or combo[2] == args.treasure)
        and (args.gear is None or combo[3] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, obstacle, treasure, gear = rng.choice(sorted(combos))
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    if args.companion_name:
        companion_name = args.companion_name
    else:
        companion_name = rng.choice(COMPANION_NAMES[companion_gender])
    ole_trait = args.ole_trait or rng.choice(OLE_TRAITS)

    return StoryParams(
        place=place,
        obstacle=obstacle,
        treasure=treasure,
        gear=gear,
        companion_name=companion_name,
        companion_gender=companion_gender,
        ole_trait=ole_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.treasure not in TREASURES:
        raise StoryError(f"(Unknown treasure: {params.treasure})")
    if params.gear not in GEARS:
        raise StoryError(f"(Unknown gear: {params.gear})")
    if params.companion_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown companion gender: {params.companion_gender})")
    if params.ole_trait not in OLE_TRAITS:
        raise StoryError(f"(Unknown Ole trait: {params.ole_trait})")

    setting = SETTINGS[params.place]
    obstacle = OBSTACLES[params.obstacle]
    gear = GEARS[params.gear]
    if obstacle.id not in setting.affords or not gear_fits(obstacle, gear):
        raise StoryError(explain_rejection(setting, obstacle, gear))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        treasure=TREASURES[params.treasure],
        gear=gear,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        ole_trait=params.ole_trait,
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
        print(asp_program("", "#show valid/4.\n#show safe_plan/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, obstacle, treasure, gear) combos:\n")
        for place, obstacle, treasure, gear in combos:
            print(f"  {place:7} {obstacle:11} {treasure:11} {gear}")
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
            header = f"### Ole at {p.place}: {p.obstacle} with {p.gear}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
