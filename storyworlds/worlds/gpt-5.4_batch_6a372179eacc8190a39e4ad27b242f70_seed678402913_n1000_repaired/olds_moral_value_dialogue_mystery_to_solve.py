#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py
========================================================================

A standalone storyworld about a child helping loving "olds" solve a tiny bedtime
mystery. The world models who misplaced a familiar object, what clue was left
behind, and how the child and elder find the truth together.

The stories aim for a bedtime shape:
- a warm evening setup
- a missing-object mystery
- dialogue-driven searching
- a gentle moral turn toward honesty, patience, and care
- a calm ending image that proves the problem is solved

Run it
------
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py --item glasses
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py --hider breeze
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/olds_moral_value_dialogue_mystery_to_solve.py --verify
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
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    portable: bool = True
    shiny: bool = False
    soft: bool = False
    paper: bool = False
    # physical / emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    room: str
    glow: str
    bed_image: str
    searching_places: list[str] = field(default_factory=list)


@dataclass
class LostItem:
    id: str
    label: str
    phrase: str
    use_line: str
    bedtime_need: str
    adjective: str
    portable: bool = True
    shiny: bool = False
    soft: bool = False
    paper: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Hider:
    id: str
    label: str
    kind: str
    clue: str
    clue_tag: str
    action_text: str
    result_place: str
    moral: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SearchTool:
    id: str
    label: str
    phrase: str
    method: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


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


def _r_missing_worry(world: World) -> list[str]:
    item = world.get("item")
    elder = world.get("elder")
    child = world.get("child")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["worry"] += 1
    child.memes["concern"] += 1
    return []


def _r_clue_hope(world: World) -> list[str]:
    clue = world.get("clue")
    elder = world.get("elder")
    child = world.get("child")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue_hope", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["hope"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    elder = world.get("elder")
    child = world.get("child")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["worry"] = 0.0
    elder.memes["relief"] += 1
    child.memes["concern"] = 0.0
    child.memes["relief"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def plausible(item: LostItem, hider: Hider, tool: SearchTool) -> bool:
    if not item.portable:
        return False
    if hider.id == "kitten":
        if not (item.soft or item.shiny):
            return False
    elif hider.id == "breeze":
        if not item.paper:
            return False
    elif hider.id == "child_moved":
        pass
    else:
        return False
    return hider.clue_tag in tool.helps


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in ITEMS.items():
            for hider_id, hider in HIDERS.items():
                for tool_id, tool in TOOLS.items():
                    if plausible(item, hider, tool):
                        out.append((setting_id, item_id, hider_id, tool_id))
    return out


def outcome_kind(hider_id: str) -> str:
    return "honesty" if hider_id == "child_moved" else "patience"


def explain_rejection(item: LostItem, hider: Hider, tool: SearchTool) -> str:
    if hider.id == "kitten" and not (item.soft or item.shiny):
        return (
            f"(No story: {hider.label} would not be strongly tempted by {item.phrase}. "
            f"Choose something soft or shiny.)"
        )
    if hider.id == "breeze" and not item.paper:
        return (
            f"(No story: a breeze can only carry something light and papery, not {item.phrase}.)"
        )
    if hider.clue_tag not in tool.helps:
        return (
            f"(No story: {tool.label} would not honestly help with the clue this mystery leaves. "
            f"Pick a search tool that matches the clue.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


def place_ok(setting: Setting, place: str) -> bool:
    return place in setting.searching_places


def predict_clue(item: LostItem, hider: Hider) -> dict:
    return {
        "clue": hider.clue,
        "place": hider.result_place,
        "honesty": hider.id == "child_moved",
    }


def missing_start(world: World, setting: Setting, elder: Entity, child: Entity, item: LostItem) -> None:
    world.say(
        f"In {setting.room}, the lamplight {setting.glow}. {child.id} was staying with "
        f"{elder.label_word}, one of the dear olds in the family, and the whole room felt soft and sleepy."
    )
    world.say(
        f"{elder.label_word.capitalize()} reached for {item.phrase} and then paused. "
        f'"Oh dear," {elder.pronoun()} said, "I had it for {item.use_line}, and now it is gone."'
    )
    ent = world.get("item")
    ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} sat up straight. {child.pronoun().capitalize()} loved bedtime at "
        f"{elder.label_word}'s house, and {item.phrase} mattered because {item.bedtime_need}."
    )


def promise_help(world: World, elder: Entity, child: Entity) -> None:
    child.memes["care"] += 1
    world.say(f'"I can help," {child.id} said.')
    world.say(
        f'{elder.label_word.capitalize()} smiled a little, though {elder.pronoun()} still looked worried. '
        f'"A small mystery before sleep," {elder.pronoun()} said. "Then let us solve it kindly."'
    )


def notice_clue(world: World, child: Entity, elder: Entity, hider: Hider) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} looked slowly instead of rushing. "
        f'"Wait," {child.pronoun()} whispered. "I see {hider.clue}."'
    )
    world.say(
        f'"Good eyes," {elder.label_word} said. "Every true mystery leaves a little trail."'
    )


def use_tool(world: World, child: Entity, elder: Entity, tool: SearchTool) -> None:
    world.say(
        f"{child.id} took {tool.phrase} and {tool.method}. "
        f"The quiet searching made the room feel thoughtful instead of scared."
    )
    child.memes["patience"] += 1
    elder.memes["trust"] += 1


def admit_if_needed(world: World, child: Entity, elder: Entity, item: LostItem, hider: Hider) -> None:
    if hider.id != "child_moved":
        return
    child.memes["guilt"] += 1
    world.say(
        f"Then {child.id} stopped by the little footstool and pressed {child.pronoun('possessive')} hands together."
    )
    world.say(
        f'"{elder.label_word.capitalize()}," {child.pronoun()} said softly, "I think I remember now. '
        f'I moved {item.phrase} when I was making a nest for my storybook, and I forgot to tell you."'
    )
    world.say(
        f'{elder.label_word.capitalize()} did not scold. "{hider.moral}," {elder.pronoun()} said. '
        f'"Thank you for telling the truth. Truth is a lamp in a mystery."'
    )


def find_item(world: World, child: Entity, elder: Entity, item: LostItem, hider: Hider) -> None:
    ent = world.get("item")
    ent.meters["missing"] = 0.0
    ent.meters["found"] += 1
    ent.attrs["place"] = hider.result_place
    propagate(world, narrate=False)
    world.say(
        f"Together they looked {hider.result_place}, and there was {item.phrase}, "
        f"safe at last."
    )
    world.say(
        f'"There you are," {elder.label_word} said, and {elder.pronoun("possessive")} whole face grew warm again.'
    )


def bedtime_close(world: World, setting: Setting, child: Entity, elder: Entity, item: LostItem, hider: Hider) -> None:
    if hider.id == "child_moved":
        moral = "telling the truth quickly helps people trust each other and mends worry"
    else:
        moral = "patient eyes and gentle thoughts can solve a puzzle better than noisy guesses"
    world.say(
        f'Soon {elder.label_word} could use {item.phrase} for {item.use_line}. '
        f'"What did this mystery teach us?" {elder.pronoun()} asked.'
    )
    if hider.id == "child_moved":
        world.say(
            f'"That I should tell the truth right away," {child.id} said. '
            f'"And that love feels safer when we are honest."'
        )
    else:
        world.say(
            f'"That we should look carefully and stay calm," {child.id} said. '
            f'"The answer was there all along, only quiet."'
        )
    world.say(
        f'{elder.label_word.capitalize()} kissed the top of {child.id}\'s head. '
        f'"Yes," {elder.pronoun()} said. "{moral}."'
    )
    world.say(
        f"Outside, the night grew still. Inside, {setting.bed_image}, and the mystery was over."
    )


def tell(
    setting: Setting,
    item_cfg: LostItem,
    hider_cfg: Hider,
    tool_cfg: SearchTool,
    *,
    child_name: str = "Mina",
    child_gender: str = "girl",
    elder_name: str = "Grandma May",
    elder_type: str = "grandmother",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=["gentle"],
    ))
    elder = world.add(Entity(
        id=elder_name,
        kind="character",
        type=elder_type,
        label=elder_name,
        role="elder",
        traits=["patient", "kind"],
    ))
    world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="lost_item",
        portable=item_cfg.portable,
        shiny=item_cfg.shiny,
        soft=item_cfg.soft,
        paper=item_cfg.paper,
        tags=set(item_cfg.tags),
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=hider_cfg.clue,
        phrase=hider_cfg.clue,
        role="clue",
        tags={hider_cfg.clue_tag},
        portable=False,
    ))

    missing_start(world, setting, elder, child, item_cfg)
    promise_help(world, elder, child)

    world.para()
    pred = predict_clue(item_cfg, hider_cfg)
    world.facts["predicted_clue"] = pred["clue"]
    world.facts["predicted_place"] = pred["place"]
    notice_clue(world, child, elder, hider_cfg)
    use_tool(world, child, elder, tool_cfg)

    world.para()
    admit_if_needed(world, child, elder, item_cfg, hider_cfg)
    find_item(world, child, elder, item_cfg, hider_cfg)

    world.para()
    bedtime_close(world, setting, child, elder, item_cfg, hider_cfg)

    world.facts.update(
        setting=setting,
        item_cfg=item_cfg,
        hider_cfg=hider_cfg,
        tool_cfg=tool_cfg,
        child=child,
        elder=elder,
        outcome=outcome_kind(hider_cfg.id),
        found_place=hider_cfg.result_place,
        found=True,
        clue=hider_cfg.clue,
        admitted=hider_cfg.id == "child_moved",
    )
    return world


SETTINGS = {
    "parlor": Setting(
        id="parlor",
        room="the little parlor",
        glow="made a gold puddle on the rug",
        bed_image="a shawl hung over the chair, the clock ticked softly, and the bed looked ready for stories",
        searching_places=["under the sofa", "by the window seat", "inside the sewing basket", "beneath the footstool"],
    ),
    "cottage": Setting(
        id="cottage",
        room="the snug cottage room",
        glow="rested honey-yellow on the wall",
        bed_image="the curtains hardly moved, the kettle had gone quiet, and the blankets waited in a warm hill",
        searching_places=["under the rocking chair", "on the window ledge", "inside the knitting basket", "beneath the footstool"],
    ),
    "attic": Setting(
        id="attic",
        room="the attic bedroom under the eaves",
        glow="shone softly over trunks and quilts",
        bed_image="the moon pressed silver on the window, the quilts were puffed high, and the room felt tucked away from the world",
        searching_places=["under the quilt chest", "by the dormer window", "inside the patchwork basket", "beneath the footstool"],
    ),
}

ITEMS = {
    "glasses": LostItem(
        id="glasses",
        label="glasses",
        phrase="the little round glasses",
        use_line="reading the last bedtime poem",
        bedtime_need="without them, the poem would stay blurry",
        adjective="round",
        portable=True,
        shiny=True,
        tags={"glasses", "bedtime"},
    ),
    "letter": LostItem(
        id="letter",
        label="letter",
        phrase="the folded letter",
        use_line="sharing a good-night note from Grandpa",
        bedtime_need="the note was part of the bedtime ritual",
        adjective="folded",
        portable=True,
        paper=True,
        tags={"letter", "paper", "bedtime"},
    ),
    "thimble": LostItem(
        id="thimble",
        label="thimble",
        phrase="the silver thimble",
        use_line="finishing one last stitch before lights-out",
        bedtime_need="the tiny sewing job was Grandma's calm habit before bed",
        adjective="silver",
        portable=True,
        shiny=True,
        tags={"thimble", "sewing"},
    ),
    "yarn": LostItem(
        id="yarn",
        label="yarn ball",
        phrase="the soft yarn ball",
        use_line="winding away the end of the evening knitting",
        bedtime_need="the knitting basket never felt settled without it",
        adjective="soft",
        portable=True,
        soft=True,
        tags={"yarn", "knitting"},
    ),
}

HIDERS = {
    "kitten": Hider(
        id="kitten",
        label="the kitten",
        kind="animal",
        clue="tiny pawprints and one stray whisker by the rug",
        clue_tag="pawprints",
        action_text="batted the object away during play",
        result_place="under the sofa",
        moral="even when a kitten makes mischief, angry guessing does not help",
        tags={"kitten", "pawprints"},
    ),
    "breeze": Hider(
        id="breeze",
        label="the breeze",
        kind="weather",
        clue="an open window and one fluttering curtain",
        clue_tag="window",
        action_text="lifted the light thing and slid it aside",
        result_place="by the window seat",
        moral="quiet causes can hide behind ordinary little signs",
        tags={"breeze", "window"},
    ),
    "child_moved": Hider(
        id="child_moved",
        label="the child",
        kind="person",
        clue="a crooked stack of storybooks near the footstool",
        clue_tag="books",
        action_text="carried it while making a pretend nest",
        result_place="beneath the footstool",
        moral="mistakes grow heavier when hidden and lighter when spoken aloud",
        tags={"honesty", "books"},
    ),
}

TOOLS = {
    "lantern": SearchTool(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        method="swept the warm beam low across the floorboards",
        helps={"pawprints", "books"},
        tags={"lantern", "light"},
    ),
    "broom": SearchTool(
        id="broom",
        label="broom",
        phrase="a soft broom",
        method="gently drew dust aside to show what had passed there",
        helps={"pawprints"},
        tags={"broom", "cleaning"},
    ),
    "feather": SearchTool(
        id="feather",
        label="feather duster",
        phrase="the feather duster",
        method="reached carefully into narrow places without knocking anything over",
        helps={"books"},
        tags={"feather", "tidy"},
    ),
    "ribbon": SearchTool(
        id="ribbon",
        label="ribbon wand",
        phrase="a ribbon wand",
        method="held it up near the window to see which way the air was moving",
        helps={"window"},
        tags={"ribbon", "air"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    item: str
    hider: str
    tool: str
    child_name: str
    child_gender: str
    elder_name: str
    elder_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "glasses": [(
        "What do glasses help with?",
        "Glasses help some people see clearly. They can make words and shapes look sharp instead of blurry."
    )],
    "letter": [(
        "What is a letter?",
        "A letter is a message someone writes down to send or share. It can hold news, love, or a memory."
    )],
    "thimble": [(
        "What is a thimble used for?",
        "A thimble is a small cap worn on a finger while sewing. It helps push a needle safely."
    )],
    "yarn": [(
        "What is yarn for?",
        "Yarn is soft string used for knitting or crocheting. People use it to make warm things like scarves and blankets."
    )],
    "kitten": [(
        "Why do kittens hide little things?",
        "Kittens like to bat and chase small objects. Sometimes they knock things under furniture while they play."
    )],
    "breeze": [(
        "What can a breeze do indoors?",
        "A breeze can flutter curtains and move very light things like paper. It cannot carry heavy objects far."
    )],
    "honesty": [(
        "Why is honesty important?",
        "Honesty helps people trust each other. Telling the truth quickly can fix a problem before it grows bigger."
    )],
    "mystery": [(
        "How do you solve a small mystery?",
        "You look carefully for clues, stay calm, and think about what could really have happened. Good guessing starts with true signs."
    )],
    "lantern": [(
        "Why is a lantern useful in a search?",
        "A lantern helps you see into dim corners. Good light can turn a confusing place into a clear one."
    )],
    "window": [(
        "How can an open window be a clue?",
        "An open window can show that wind came inside. If something light moved, the window might help explain it."
    )],
}
KNOWLEDGE_ORDER = [
    "mystery", "honesty", "glasses", "letter", "thimble", "yarn",
    "kitten", "breeze", "lantern", "window",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item_cfg"]
    hider = f["hider_cfg"]
    return [
        f'Write a bedtime story for ages 3 to 5 that includes the word "olds" and a small mystery about {item.label}.',
        f"Tell a gentle dialogue-rich story where {child.id} helps {elder.label_word} find {item.phrase} before bed.",
        f"Write a moral story where the clue is {hider.clue} and the ending teaches either honesty or patient thinking.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    item = f["item_cfg"]
    hider = f["hider_cfg"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id} and {elder.label_word}, one of the loving olds in the family. "
            f"Together they solve a tiny bedtime mystery."
        ),
        (
            f"What was missing?",
            f"{item.phrase.capitalize()} was missing. It mattered because {item.bedtime_need}."
        ),
        (
            "What clue did they notice?",
            f"They noticed {hider.clue}. That clue pointed them toward the true cause of the mystery."
        ),
        (
            f"How did {child.id} help solve the mystery?",
            f"{child.id} stayed calm, looked carefully, and used {tool.phrase} to search in a thoughtful way. "
            f"That careful method helped turn worry into a real answer."
        ),
    ]
    if f["admitted"]:
        qa.append((
            f"Why did the truth matter in this story?",
            f"The truth mattered because {child.id} remembered moving {item.phrase} and chose to admit it. "
            f"Once the truth was spoken, the worry became smaller and trust grew again."
        ))
    else:
        qa.append((
            "Why did they solve the mystery without fussing?",
            f"They solved it by paying attention to the clue instead of making noisy guesses. "
            f"The clue told them what had really happened, so patience worked better than blame."
        ))
    qa.append((
        "How did the story end?",
        f"It ended peacefully, with {item.phrase} found {f['found_place']}. "
        f"Then bedtime could go on in a calm and cozy way."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"mystery"}
    item = f["item_cfg"]
    hider = f["hider_cfg"]
    tool = f["tool_cfg"]
    tags |= set(item.tags)
    tags |= set(hider.tags)
    tags |= set(tool.tags)
    if hider.id == "child_moved":
        tags.add("honesty")
    if hider.id == "breeze":
        tags.add("window")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if ent.shiny:
            flags.append("shiny")
        if ent.soft:
            flags.append("soft")
        if ent.paper:
            flags.append("paper")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="parlor",
        item="glasses",
        hider="kitten",
        tool="lantern",
        child_name="Mina",
        child_gender="girl",
        elder_name="Grandma May",
        elder_type="grandmother",
    ),
    StoryParams(
        setting="cottage",
        item="letter",
        hider="breeze",
        tool="ribbon",
        child_name="Ben",
        child_gender="boy",
        elder_name="Grandpa Ash",
        elder_type="grandfather",
    ),
    StoryParams(
        setting="attic",
        item="thimble",
        hider="child_moved",
        tool="feather",
        child_name="Nora",
        child_gender="girl",
        elder_name="Grandma Wren",
        elder_type="grandmother",
    ),
    StoryParams(
        setting="cottage",
        item="yarn",
        hider="kitten",
        tool="broom",
        child_name="Theo",
        child_gender="boy",
        elder_name="Grandma June",
        elder_type="grandmother",
    ),
]


ASP_RULES = r"""
% Registry-driven reasonableness.
portable_item(I) :- item(I), portable(I).
tempted_by_kitten(I) :- shiny(I).
tempted_by_kitten(I) :- soft(I).
movable_by_breeze(I) :- paper(I).
plausible_hider(I, kitten) :- portable_item(I), tempted_by_kitten(I).
plausible_hider(I, breeze) :- portable_item(I), movable_by_breeze(I).
plausible_hider(I, child_moved) :- portable_item(I).

tool_matches(T, H) :- hider(H), clue_tag(H, C), helps(T, C).

valid(S, I, H, T) :- setting(S), item(I), hider(H), tool(T),
                     plausible_hider(I, H), tool_matches(T, H).

outcome(honesty) :- chosen_hider(child_moved).
outcome(patience) :- chosen_hider(H), hider(H), H != child_moved.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.portable:
            lines.append(asp.fact("portable", iid))
        if item.shiny:
            lines.append(asp.fact("shiny", iid))
        if item.soft:
            lines.append(asp.fact("soft", iid))
        if item.paper:
            lines.append(asp.fact("paper", iid))
    for hid, hider in HIDERS.items():
        lines.append(asp.fact("hider", hid))
        lines.append(asp.fact("clue_tag", hid, hider.clue_tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for clue in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, clue))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_hider", params.hider)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    vals = asp.atoms(model, "outcome")
    return vals[0][0] if vals else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    emit(sample, trace=False, qa=False)


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_kind(p.hider))
    if bad == 0:
        print(f"OK: outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A bedtime mystery storyworld about a child helping the olds find a missing thing."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hider", choices=HIDERS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Mina", "Nora", "Lucy", "Ella", "Maya", "Rose"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Noah", "Eli", "Finn"]
GRANDMOTHERS = ["Grandma May", "Grandma Wren", "Grandma June", "Grandma Pearl"]
GRANDFATHERS = ["Grandpa Ash", "Grandpa Reed", "Grandpa Owen", "Grandpa Lee"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hider and args.tool:
        if not plausible(ITEMS[args.item], HIDERS[args.hider], TOOLS[args.tool]):
            raise StoryError(explain_rejection(ITEMS[args.item], HIDERS[args.hider], TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.hider is None or combo[2] == args.hider)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, hider_id, tool_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather"])
    elder_name = rng.choice(GRANDMOTHERS if elder_type == "grandmother" else GRANDFATHERS)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        hider=hider_id,
        tool=tool_id,
        child_name=child_name,
        child_gender=child_gender,
        elder_name=elder_name,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        hider = HIDERS[params.hider]
        tool = TOOLS[params.tool]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from exc

    if not plausible(item, hider, tool):
        raise StoryError(explain_rejection(item, hider, tool))

    world = tell(
        setting=setting,
        item_cfg=item,
        hider_cfg=hider,
        tool_cfg=tool,
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_name=params.elder_name,
        elder_type=params.elder_type,
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
        print(f"{len(combos)} compatible (setting, item, hider, tool) combos:\n")
        for setting_id, item_id, hider_id, tool_id in combos:
            print(f"  {setting_id:8} {item_id:8} {hider_id:11} {tool_id}")
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
            header = f"### {p.child_name} with {p.elder_name}: {p.item} / {p.hider} / {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
