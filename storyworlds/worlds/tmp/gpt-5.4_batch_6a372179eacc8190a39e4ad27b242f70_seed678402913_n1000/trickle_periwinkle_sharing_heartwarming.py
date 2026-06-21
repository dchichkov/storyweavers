#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py
=====================================================================

A standalone story world about two children, a small water source, one
periwinkle-colored tool, and a choice between keeping and sharing.

The seed asked for the words "trickle" and "periwinkle", the feature
"Sharing", and a heartwarming style. This world rebuilds that premise as a
tiny simulation:

- Two children care for nearby plants.
- Water is scarce: only a gentle trickle comes from the source.
- There is one periwinkle watering tool.
- If one child keeps it, only one plant is watered and the other droops.
- If they share sensibly, both plants drink and the ending image proves the
  relationship changed.

The world model drives the prose. Plants carry physical meters like "water" and
"upright"; children carry emotional memes like "want", "envy", "care", and
"warmth". A small forward-chaining rule engine turns water into recovery and
neglect into drooping, and those state changes shape the story text.

Run it
------
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py --share keep
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py --qa --json
    python storyworlds/worlds/gpt-5.4/trickle_periwinkle_sharing_heartwarming.py --verify
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

# Make shared result containers importable when run directly from the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing" | "plant"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PlantKind:
    id: str
    label: str
    phrase: str
    thirsty: bool
    bloom: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SourceKind:
    id: str
    label: str
    trickle_text: str
    flow: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolKind:
    id: str
    label: str
    phrase: str
    color: str
    size: int
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareMode:
    id: str
    kind: str                  # "share" | "keep"
    sense: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


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
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "friend"}]

    def plants(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "plant"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

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


def _r_drink(world: World) -> list[str]:
    out: list[str] = []
    for plant in world.plants():
        if plant.meters["water"] < THRESHOLD:
            continue
        sig = ("drink", plant.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        plant.meters["upright"] += 1
        plant.meters["droop"] = 0.0
        out.append("__plant_recovers__")
    return out


def _r_droop(world: World) -> list[str]:
    out: list[str] = []
    for plant in world.plants():
        if plant.meters["water"] >= THRESHOLD:
            continue
        sig = ("droop", plant.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        plant.meters["droop"] += 1
        out.append("__plant_droops__")
    return out


def _r_warmth(world: World) -> list[str]:
    holder = world.entities.get("holder")
    friend = world.entities.get("friend")
    if holder is None or friend is None:
        return []
    if holder.memes["shared"] < THRESHOLD:
        return []
    sig = ("warmth",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    holder.memes["warmth"] += 1
    friend.memes["warmth"] += 1
    holder.memes["envy"] = 0.0
    friend.memes["sad"] = 0.0
    return ["__warmth__"]


CAUSAL_RULES = [
    Rule(name="drink", tag="physical", apply=_r_drink),
    Rule(name="droop", tag="physical", apply=_r_droop),
    Rule(name="warmth", tag="social", apply=_r_warmth),
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
        for sent in produced:
            world.say(sent)
    return produced


def enough_for_both(source: SourceKind, tool: ToolKind) -> bool:
    return source.flow >= tool.size


def sharing_works(mode: ShareMode) -> bool:
    return mode.kind == "share" and mode.sense >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for plant_left in PLANTS:
            for plant_right in PLANTS:
                if plant_left == plant_right:
                    continue
                for source_id, source in SOURCES.items():
                    for tool_id, tool in TOOLS.items():
                        if enough_for_both(source, tool):
                            combos.append((setting_id, plant_left, plant_right, source_id, tool_id))
    return combos


def predict_outcome(source: SourceKind, tool: ToolKind, share_mode: ShareMode) -> str:
    if sharing_works(share_mode) and enough_for_both(source, tool):
        return "shared"
    return "kept"


def _water(world: World, plant_id: str, amount: int) -> None:
    plant = world.get(plant_id)
    plant.meters["water"] += float(amount)
    propagate(world, narrate=False)


def introduce(world: World, holder: Entity, friend: Entity, parent: Entity,
              tool: ToolKind, source: SourceKind, left_plant: PlantKind,
              right_plant: PlantKind) -> None:
    world.say(
        f"One soft morning, {holder.id} and {friend.id} went with {holder.pronoun('possessive')} "
        f"{parent.label_word} to {world.setting.place}. {world.setting.image}"
    )
    world.say(
        f"By the path stood two little beds of plants: {left_plant.phrase} for {holder.id} "
        f"and {right_plant.phrase} for {friend.id}."
    )
    world.say(
        f"There was only one {tool.color} {tool.label} to use, and the rain barrel gave only "
        f"a {source.trickle_text} of water."
    )


def assign_care(world: World, holder: Entity, friend: Entity,
                left_plant: Entity, right_plant: Entity) -> None:
    holder.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f'Both children bent close. "{left_plant.label} looks thirsty," {holder.id} said. '
        f'"And {right_plant.label} does too," {friend.id} answered.'
    )


def desire(world: World, holder: Entity, tool: ToolKind) -> None:
    holder.memes["want"] += 1
    world.say(
        f"{holder.id} reached for the {tool.label} first. The little {tool.label} was such "
        f"a pretty shade of periwinkle that {holder.pronoun()} wanted to keep holding it."
    )


def warning(world: World, parent: Entity, holder: Entity, friend: Entity,
            source: SourceKind, tool: ToolKind) -> None:
    pred = predict_outcome(source, tool, ShareMode(
        id="turns", kind="share", sense=3,
        text="", qa_text="", tags=set()
    ))
    world.facts["predicted_outcome"] = pred
    world.say(
        f'{parent.label_word.capitalize()} listened to the small water trickle into the cup. '
        f'"The barrel is only giving a little trickle today," {parent.pronoun()} said. '
        f'"If one child keeps the cup all the time, one plant may have to wait too long."'
    )
    friend.memes["hope"] += 1
    holder.memes["hesitate"] += 1


def keep_it(world: World, holder: Entity, friend: Entity, tool: ToolKind,
            left_plant: Entity, right_plant: Entity) -> None:
    holder.memes["shared"] = 0.0
    holder.memes["envy"] += 1
    friend.memes["sad"] += 1
    world.say(
        f'"I want to do it myself," {holder.id} whispered, curling both hands around the '
        f"{tool.label}."
    )
    _water(world, left_plant.id, 1)
    world.say(
        f"{holder.id} tipped the cup over {holder.pronoun('possessive')} own plant. A shiny line "
        f"of water ran down the dark soil."
    )
    propagate(world, narrate=False)
    world.say(
        f"But there was no second turn yet, and {right_plant.label} had to wait."
    )


def share_it(world: World, holder: Entity, friend: Entity, tool: ToolKind,
             left_plant: Entity, right_plant: Entity, mode: ShareMode) -> None:
    holder.memes["shared"] += 1
    holder.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(mode.text.format(holder=holder.id, friend=friend.id, tool=tool.label))
    _water(world, left_plant.id, 1)
    _water(world, right_plant.id, 1)
    world.say(
        f"First the cup tilted over {left_plant.label}, then over {right_plant.label}, and the "
        f"small stream made two dark circles in the soil."
    )
    propagate(world, narrate=False)


def plant_turn(world: World, left_plant: Entity, right_plant: Entity,
               left_kind: PlantKind, right_kind: PlantKind) -> None:
    left_happy = left_plant.meters["upright"] >= THRESHOLD
    right_happy = right_plant.meters["upright"] >= THRESHOLD
    left_sad = left_plant.meters["droop"] >= THRESHOLD
    right_sad = right_plant.meters["droop"] >= THRESHOLD
    if left_happy and right_happy:
        world.say(
            f"Soon both plants looked taller. {left_kind.bloom} and {right_kind.bloom} seemed to "
            f"lift toward the sun."
        )
    elif left_happy and right_sad:
        world.say(
            f"{left_kind.bloom} stood a little straighter, but {right_kind.bloom} still drooped at "
            f"the edge of the bed."
        )
    elif left_sad and right_happy:
        world.say(
            f"{right_kind.bloom} stood a little straighter, but {left_kind.bloom} still drooped at "
            f"the edge of the bed."
        )


def gentle_lesson(world: World, parent: Entity, holder: Entity, friend: Entity,
                  tool: ToolKind, share_mode: ShareMode) -> None:
    if share_mode.kind == "share":
        world.say(
            f'{parent.label_word.capitalize()} smiled. "That was kind," {parent.pronoun()} said. '
            f'"Sharing the {tool.label} helped both plants drink."'
        )
        world.say(
            f"{friend.id} touched {holder.id}'s sleeve and smiled back. The hard little knot inside "
            f"the morning loosened."
        )
    else:
        world.say(
            f'{parent.label_word.capitalize()} knelt beside them. "Your plant got a drink," '
            f'{parent.pronoun()} said softly, "but {friend.id} still wants to help {friend.pronoun("possessive")} plant too."'
        )
        world.say(
            f"{holder.id} looked from the wet soil to {right_plant_name(world)} and felt less proud "
            f"than before."
        )


def right_plant_name(world: World) -> str:
    plant = world.get("right_plant")
    return plant.label


def ending(world: World, holder: Entity, friend: Entity, tool: ToolKind,
           share_mode: ShareMode, left_kind: PlantKind, right_kind: PlantKind) -> None:
    if share_mode.kind == "share":
        holder.memes["joy"] += 1
        friend.memes["joy"] += 1
        world.say(
            f"When another little trickle filled the periwinkle {tool.label}, the children held it "
            f"together by the handle and laughed when one cold drop splashed both thumbs."
        )
        world.say(
            f"At the end, {holder.id} and {friend.id} walked home side by side, already planning to "
            f"come back and look for {left_kind.bloom} and {right_kind.bloom} together."
        )
    else:
        world.say(
            f"On the way home, {friend.id} walked quietly, and even the bright periwinkle cup did not "
            f"look quite as special in {holder.id}'s hands."
        )
        world.say(
            f"{holder.id} promised to offer the first turn next time, hoping both little plants would "
            f"get their drink together."
        )


def tell(setting: Setting, left_kind: PlantKind, right_kind: PlantKind,
         source: SourceKind, tool: ToolKind, share_mode: ShareMode,
         holder_name: str = "Mia", holder_gender: str = "girl",
         friend_name: str = "Ben", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World(setting=setting)
    holder = world.add(Entity(
        id=holder_name, kind="character", type=holder_gender, role="holder",
        traits=["gentle"], tags={"child"}
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_gender, role="friend",
        traits=["patient"], tags={"child"}
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, role="parent",
        label="the parent", tags={"grownup"}
    ))
    left_plant = world.add(Entity(
        id="left_plant", kind="plant", type=left_kind.id, label=left_kind.label,
        phrase=left_kind.phrase, tags=set(left_kind.tags)
    ))
    right_plant = world.add(Entity(
        id="right_plant", kind="plant", type=right_kind.id, label=right_kind.label,
        phrase=right_kind.phrase, tags=set(right_kind.tags)
    ))
    world.add(Entity(
        id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase,
        tags=set(tool.tags)
    ))
    world.add(Entity(
        id="source", kind="thing", type="source", label=source.label,
        phrase=source.label, tags=set(source.tags)
    ))

    introduce(world, holder, friend, parent, tool, source, left_kind, right_kind)
    assign_care(world, holder, friend, left_plant, right_plant)

    world.para()
    desire(world, holder, tool)
    warning(world, parent, holder, friend, source, tool)

    world.para()
    if share_mode.kind == "share":
        share_it(world, holder, friend, tool, left_plant, right_plant, share_mode)
    else:
        keep_it(world, holder, friend, tool, left_plant, right_plant)
    plant_turn(world, left_plant, right_plant, left_kind, right_kind)

    world.para()
    gentle_lesson(world, parent, holder, friend, tool, share_mode)
    ending(world, holder, friend, tool, share_mode, left_kind, right_kind)

    world.facts.update(
        holder=holder,
        friend=friend,
        parent=parent,
        left_plant=left_plant,
        right_plant=right_plant,
        left_kind=left_kind,
        right_kind=right_kind,
        source=source,
        tool=tool,
        share_mode=share_mode,
        outcome=predict_outcome(source, tool, share_mode),
        both_watered=left_plant.meters["upright"] >= THRESHOLD and right_plant.meters["upright"] >= THRESHOLD,
        one_waited=right_plant.meters["droop"] >= THRESHOLD or left_plant.meters["droop"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the little garden behind the library",
        image="Marigolds nodded along the fence, and a robin hopped between the stepping stones.",
        tags={"garden"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the sunny courtyard at school",
        image="Warm bricks held the morning light, and mint leaves brushed the edge of the path.",
        tags={"garden"},
    ),
    "porch": Setting(
        id="porch",
        place="the back porch with its row of pots",
        image="Wind bells made a soft clink, and the leaves in the pots trembled in the shade.",
        tags={"garden"},
    ),
}

PLANTS = {
    "beans": PlantKind(
        id="beans",
        label="bean sprouts",
        phrase="a row of bean sprouts",
        thirsty=True,
        bloom="The bean leaves",
        tags={"plants", "beans"},
    ),
    "strawberry": PlantKind(
        id="strawberry",
        label="the strawberry plant",
        phrase="a little strawberry plant",
        thirsty=True,
        bloom="The tiny strawberry leaves",
        tags={"plants", "strawberry"},
    ),
    "pansy": PlantKind(
        id="pansy",
        label="the pansy patch",
        phrase="a patch of pansies",
        thirsty=True,
        bloom="The velvet pansy faces",
        tags={"plants", "flowers"},
    ),
}

SOURCES = {
    "barrel_tap": SourceKind(
        id="barrel_tap",
        label="the barrel tap",
        trickle_text="trickle",
        flow=1,
        tags={"water", "trickle"},
    ),
    "stone_spout": SourceKind(
        id="stone_spout",
        label="the stone spout",
        trickle_text="silver trickle",
        flow=1,
        tags={"water", "trickle"},
    ),
    "tiny_hose": SourceKind(
        id="tiny_hose",
        label="the tiny hose",
        trickle_text="thin trickle",
        flow=1,
        tags={"water", "trickle"},
    ),
}

TOOLS = {
    "cup": ToolKind(
        id="cup",
        label="cup",
        phrase="a small watering cup",
        color="periwinkle",
        size=1,
        tags={"periwinkle", "cup"},
    ),
    "can": ToolKind(
        id="can",
        label="watering can",
        phrase="a tiny watering can",
        color="periwinkle",
        size=1,
        tags={"periwinkle", "watering_can"},
    ),
    "dipper": ToolKind(
        id="dipper",
        label="dipper",
        phrase="a little garden dipper",
        color="periwinkle",
        size=1,
        tags={"periwinkle", "dipper"},
    ),
}

SHARE_MODES = {
    "turns": ShareMode(
        id="turns",
        kind="share",
        sense=3,
        text='"Let\'s take turns," {holder} said at last, passing the {tool} across after the first pour.',
        qa_text="They took turns with the periwinkle tool, so both plants could drink.",
        tags={"sharing"},
    ),
    "together": ShareMode(
        id="together",
        kind="share",
        sense=3,
        text='{holder} looked at {friend} and said, "We can hold the {tool} together."',
        qa_text="They held the periwinkle tool together and watered both plants.",
        tags={"sharing"},
    ),
    "keep": ShareMode(
        id="keep",
        kind="keep",
        sense=1,
        text="",
        qa_text="One child kept the tool and the other plant had to wait.",
        tags={"not_sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Ella", "Rose", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Finn", "Noah", "Jack", "Theo", "Max"]


@dataclass
class StoryParams:
    setting: str
    left_plant: str
    right_plant: str
    source: str
    tool: str
    share: str
    holder_name: str
    holder_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="garden",
        left_plant="beans",
        right_plant="pansy",
        source="barrel_tap",
        tool="cup",
        share="turns",
        holder_name="Mia",
        holder_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        parent="mother",
    ),
    StoryParams(
        setting="courtyard",
        left_plant="strawberry",
        right_plant="beans",
        source="stone_spout",
        tool="can",
        share="together",
        holder_name="Leo",
        holder_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        parent="father",
    ),
    StoryParams(
        setting="porch",
        left_plant="pansy",
        right_plant="strawberry",
        source="tiny_hose",
        tool="dipper",
        share="keep",
        holder_name="Ava",
        holder_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
    ),
]


KNOWLEDGE = {
    "trickle": [
        (
            "What is a trickle?",
            "A trickle is a very small, slow flow of water. It is only a little at a time, so you often have to wait patiently."
        )
    ],
    "periwinkle": [
        (
            "What color is periwinkle?",
            "Periwinkle is a soft bluish-purple color. It looks a little like blue sky mixed with lavender."
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful when there is only one tool?",
            "Sharing helps more than one person use the same thing fairly. Taking turns can solve a problem without anybody being left out."
        )
    ],
    "plants": [
        (
            "Why do plants need water?",
            "Plants need water to stay alive and stand upright. Without enough water, their leaves can droop and look tired."
        )
    ],
    "watering_can": [
        (
            "What does a watering can do?",
            "A watering can helps you pour water gently onto soil and roots. It lets small plants drink without being knocked over."
        )
    ],
    "cup": [
        (
            "How can a small cup help in a garden?",
            "A small cup can carry a little bit of water to a plant. When the water is scarce, even one careful cupful can matter."
        )
    ],
    "dipper": [
        (
            "What is a dipper for?",
            "A dipper is a little scoop or cup used to lift water. It is helpful when you need to move just a small amount."
        )
    ],
}
KNOWLEDGE_ORDER = ["trickle", "periwinkle", "sharing", "plants", "watering_can", "cup", "dipper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    holder = f["holder"]
    friend = f["friend"]
    tool = f["tool"]
    source = f["source"]
    return [
        'Write a heartwarming story for a 3-to-5-year-old that includes the words "trickle" and "periwinkle" and centers on sharing.',
        f"Tell a gentle story where {holder.id} and {friend.id} have only one periwinkle {tool.label} while water comes in a {source.trickle_text}, and they must decide how to use it.",
        "Write a warm story about two children caring for plants, facing a small problem, and ending with a concrete image that shows kindness changed the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    holder = f["holder"]
    friend = f["friend"]
    parent = f["parent"]
    tool = f["tool"]
    source = f["source"]
    left_plant = f["left_plant"]
    right_plant = f["right_plant"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {holder.id} and {friend.id}, two children caring for small plants with {holder.pronoun('possessive')} {parent.label_word} nearby."
        ),
        (
            "What was the problem in the story?",
            f"There was only one periwinkle {tool.label}, and the water came only in a {source.trickle_text}. That meant the children had to decide whether to keep it or share it."
        ),
        (
            f"Why did the water matter so much to the plants?",
            f"The plants were thirsty and needed water to stand up fresh again. With only a little water coming at once, each careful pour made a difference."
        ),
    ]
    if outcome == "shared":
        qa.extend([
            (
                f"How did {holder.id} and {friend.id} solve the problem?",
                f"They shared the periwinkle {tool.label} instead of letting one child keep it. Because they took turns or held it together, both plants got a drink."
            ),
            (
                "What changed after they shared?",
                f"Both plants perked up, and both children felt warmer toward each other. The kind choice changed both the garden and the mood between them."
            ),
            (
                "How did the story end?",
                f"It ended with the children close together, laughing over one more little trickle of water. Their final walk home showed that sharing had made the day feel gentle and bright."
            ),
        ])
    else:
        qa.extend([
            (
                f"What happened when {holder.id} kept the tool?",
                f"{holder.id}'s own plant got water first, but the other plant had to wait. That left one side of the garden happier than the other."
            ),
            (
                f"How did {friend.id} feel?",
                f"{friend.id} felt quiet and left out. The problem was not only the thirsty plant, but also that the work no longer felt shared."
            ),
            (
                "What did the ending suggest for next time?",
                f"It suggested that sharing sooner would have been kinder. {holder.id} understood that the pretty periwinkle tool mattered less than helping both plants together."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["source"].tags)
    tags |= set(f["tool"].tags)
    tags |= {"plants"}
    if f["share_mode"].kind == "share":
        tags |= {"sharing"}
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_combo(source: SourceKind, tool: ToolKind) -> str:
    return (
        f"(No story: {source.label} only gives a {source.trickle_text}, and that does not make sense "
        f"with a larger tool. This world only tells stories where one little fill of the tool matches the little water supply.)"
    )


def explain_share(share_id: str) -> str:
    mode = SHARE_MODES[share_id]
    return (
        f"(Refusing share mode '{share_id}': it scores too low on kindness for this heartwarming world. "
        f"Try one of: {', '.join(sorted(k for k, v in SHARE_MODES.items() if sharing_works(v)))}.)"
    )


ASP_RULES = r"""
% A water setup is workable when the source can fill the chosen small tool.
workable(Source, Tool) :- source(Source), tool(Tool), flow(Source, F), size(Tool, S), F >= S.

% Reasonable heartwarming share modes.
kind_mode(M) :- share_mode(M), mode_kind(M, share), sense(M, S), S >= 2.

valid(Setting, Left, Right, Source, Tool) :-
    setting(Setting), plant(Left), plant(Right), Left != Right,
    source(Source), tool(Tool), workable(Source, Tool).

outcome(shared) :- chosen_share(M), mode_kind(M, share), sense(M, S), S >= 2,
                   chosen_source(Source), chosen_tool(Tool), workable(Source, Tool).
outcome(kept) :- not outcome(shared).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PLANTS:
        lines.append(asp.fact("plant", pid))
    for sid, src in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("flow", sid, src.flow))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("size", tid, tool.size))
    for mid, mode in SHARE_MODES.items():
        lines.append(asp.fact("share_mode", mid))
        lines.append(asp.fact("mode_kind", mid, mode.kind))
        lines.append(asp.fact("sense", mid, mode.sense))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_kind_modes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show kind_mode/1."))
    return sorted(m for (m,) in asp.atoms(model, "kind_mode"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_share", params.share),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("smoke test failed: empty story")
    if "periwinkle" not in sample.story.lower():
        raise StoryError("smoke test failed: missing 'periwinkle'")
    if "trickle" not in sample.story.lower():
        raise StoryError("smoke test failed: missing 'trickle'")


def asp_verify() -> int:
    rc = 0
    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_modes = set(asp_kind_modes())
    p_modes = {mid for mid, mode in SHARE_MODES.items() if sharing_works(mode)}
    if c_modes == p_modes:
        print(f"OK: kind share modes match ({sorted(c_modes)}).")
    else:
        rc = 1
        print(f"MISMATCH in share modes: clingo={sorted(c_modes)} python={sorted(p_modes)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        py = predict_outcome(SOURCES[params.source], TOOLS[params.tool], SHARE_MODES[params.share])
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: one periwinkle tool, a little trickle of water, and a sharing choice."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--left-plant", dest="left_plant", choices=PLANTS)
    ap.add_argument("--right-plant", dest="right_plant", choices=PLANTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--share", choices=SHARE_MODES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.tool:
        if not enough_for_both(SOURCES[args.source], TOOLS[args.tool]):
            raise StoryError(explain_combo(SOURCES[args.source], TOOLS[args.tool]))
    if args.share and SHARE_MODES[args.share].kind == "keep":
        raise StoryError(explain_share(args.share))
    if args.left_plant and args.right_plant and args.left_plant == args.right_plant:
        raise StoryError("(No story: the two children need two different plant beds to share care for.)")

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.left_plant is None or c[1] == args.left_plant)
        and (args.right_plant is None or c[2] == args.right_plant)
        and (args.source is None or c[3] == args.source)
        and (args.tool is None or c[4] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, left_plant, right_plant, source, tool = rng.choice(sorted(combos))
    share_choices = [mid for mid, mode in SHARE_MODES.items() if sharing_works(mode)]
    share = args.share or rng.choice(sorted(share_choices))
    holder_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    holder_name = _pick_name(rng, holder_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=holder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        setting=setting,
        left_plant=left_plant,
        right_plant=right_plant,
        source=source,
        tool=tool,
        share=share,
        holder_name=holder_name,
        holder_gender=holder_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def _validate_params(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.left_plant not in PLANTS:
        raise StoryError(f"(Invalid left plant: {params.left_plant})")
    if params.right_plant not in PLANTS:
        raise StoryError(f"(Invalid right plant: {params.right_plant})")
    if params.source not in SOURCES:
        raise StoryError(f"(Invalid source: {params.source})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Invalid tool: {params.tool})")
    if params.share not in SHARE_MODES:
        raise StoryError(f"(Invalid share mode: {params.share})")
    if params.left_plant == params.right_plant:
        raise StoryError("(No story: the two children need two different plant beds.)")
    if not enough_for_both(SOURCES[params.source], TOOLS[params.tool]):
        raise StoryError(explain_combo(SOURCES[params.source], TOOLS[params.tool]))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        setting=SETTINGS[params.setting],
        left_kind=PLANTS[params.left_plant],
        right_kind=PLANTS[params.right_plant],
        source=SOURCES[params.source],
        tool=TOOLS[params.tool],
        share_mode=SHARE_MODES[params.share],
        holder_name=params.holder_name,
        holder_gender=params.holder_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/5.\n#show kind_mode/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, left_plant, right_plant, source, tool) combos:\n")
        for setting, left_plant, right_plant, source, tool in combos:
            print(f"  {setting:10} {left_plant:10} {right_plant:10} {source:12} {tool}")
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
            outcome = predict_outcome(SOURCES[p.source], TOOLS[p.tool], SHARE_MODES[p.share])
            header = (
                f"### {p.holder_name} & {p.friend_name}: {p.share} with {p.tool} "
                f"at {p.setting} ({outcome})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
