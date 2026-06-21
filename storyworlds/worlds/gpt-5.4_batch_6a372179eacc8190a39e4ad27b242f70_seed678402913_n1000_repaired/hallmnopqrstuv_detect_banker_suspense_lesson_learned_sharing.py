#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hallmnopqrstuv_detect_banker_suspense_lesson_learned_sharing.py
==========================================================================================

A standalone story world for a tiny detective-style tale about a missing shared
treat at Hallmnopqrstuv Hall. A child tries to detect clues, a banker helps
calm the search, and the ending teaches a lesson about asking, sharing, and not
blaming too quickly.

Run it
------
    python storyworlds/worlds/gpt-5.4/hallmnopqrstuv_detect_banker_suspense_lesson_learned_sharing.py
    python storyworlds/worlds/gpt-5.4/hallmnopqrstuv_detect_banker_suspense_lesson_learned_sharing.py --item muffins --hider shy_child
    python storyworlds/worlds/gpt-5.4/hallmnopqrstuv_detect_banker_suspense_lesson_learned_sharing.py --all
    python storyworlds/worlds/gpt-5.4/hallmnopqrstuv_detect_banker_suspense_lesson_learned_sharing.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so the package directory is
# three levels up from here: storyworlds/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    owner: str = ""
    location: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "banker_woman"}
        male = {"boy", "father", "man", "banker_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "banker_woman" or self.type == "banker_man":
            return "banker"
        return self.label or self.type


@dataclass
class Hall:
    id: str
    place: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    plural_label: str
    container: str
    crumb: str
    sharing_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Hider:
    id: str
    label: str
    type: str
    reason: str
    confession: str
    sharing_fix: str
    courage_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    trail: str
    place: str
    detect_line: str
    proof: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    text: str
    calming: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    hero = world.get("hero")
    banker = world.get("banker")
    if item.meters["missing"] < THRESHOLD:
        return out
    sig = ("missing_worry", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] += 1
    banker.memes["worry"] += 1
    out.append("__suspense__")
    return out


def _r_hidden_clue(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    clue = world.get("clue")
    if item.location != clue.location:
        return out
    sig = ("clue_visible", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.meters["visible"] += 1
    out.append("__clue__")
    return out


def _r_found_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return out
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for eid in ("hero", "friend", "banker", "hider"):
        if eid in world.entities:
            world.get(eid).memes["relief"] += 1
            world.get(eid).memes["worry"] = 0.0
    out.append("__relief__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotion", apply=_r_missing_worry),
    Rule(name="hidden_clue", tag="physical", apply=_r_hidden_clue),
    Rule(name="found_relief", tag="emotion", apply=_r_found_relief),
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


HALLS = {
    "clock": Hall(
        id="clock",
        place="Hallmnopqrstuv Hall",
        detail="a long room with a creaky clock, shiny floorboards, and a little side closet",
        tags={"hallmnopqrstuv", "hall"},
    ),
    "garden": Hall(
        id="garden",
        place="Hallmnopqrstuv Garden Hall",
        detail="a cheerful room with paper flowers, tall windows, and a side cupboard",
        tags={"hallmnopqrstuv", "hall"},
    ),
    "river": Hall(
        id="river",
        place="Hallmnopqrstuv River Hall",
        detail="a bright room with blue bunting, echoing steps, and a coat nook",
        tags={"hallmnopqrstuv", "hall"},
    ),
}

ITEMS = {
    "muffins": ShareItem(
        id="muffins",
        label="muffins",
        phrase="a tray of blueberry muffins",
        plural_label="the muffins",
        container="tray",
        crumb="blueberry crumbs",
        sharing_line="There should be enough for everyone if we share them carefully.",
        tags={"food", "sharing", "muffins"},
    ),
    "oranges": ShareItem(
        id="oranges",
        label="orange slices",
        phrase="a bowl of orange slices",
        plural_label="the orange slices",
        container="bowl",
        crumb="tiny drops of juice",
        sharing_line="There should be enough for everyone if we pass them around.",
        tags={"food", "sharing", "oranges"},
    ),
    "cookies": ShareItem(
        id="cookies",
        label="star cookies",
        phrase="a tin of star cookies",
        plural_label="the star cookies",
        container="tin",
        crumb="sweet sugar crumbs",
        sharing_line="There should be enough for everyone if we put them on a sharing plate.",
        tags={"food", "sharing", "cookies"},
    ),
}

HIDERS = {
    "shy_child": Hider(
        id="shy_child",
        label="a shy little child named Poppy",
        type="girl",
        reason="thought there would not be any left for her if she waited",
        confession="I hid them because I was scared everyone else would get one first.",
        sharing_fix="The children promised to save the first plate for the smallest guests.",
        courage_line="Next time I can ask instead of hiding things.",
        tags={"child", "sharing", "ask_first"},
    ),
    "janitor": Hider(
        id="janitor",
        label="Mr. Bell the hall helper",
        type="man",
        reason="moved them away from a wobbly table and forgot to tell anyone",
        confession="I tucked them somewhere safe when the table rocked, and then I rushed off for tape.",
        sharing_fix="Everyone laughed softly, and Mr. Bell helped carry the food back so it could be shared fairly.",
        courage_line="Next time I will say where I put things.",
        tags={"helper", "communication"},
    ),
    "younger_brother": Hider(
        id="younger_brother",
        label="a little boy named Niko",
        type="boy",
        reason="wanted to bring the treats closer so he could guard them",
        confession="I was trying to help, but I moved them without asking.",
        sharing_fix="The others thanked him for caring and showed him how to help by passing plates instead.",
        courage_line="Next time I can help with words, not secret moving.",
        tags={"child", "sharing", "helping"},
    ),
}

CLUES = {
    "crumbs_closet": Clue(
        id="crumbs_closet",
        trail="a line of crumbs",
        place="the side closet",
        detect_line="a line of tiny crumbs led toward the side closet",
        proof="The crumbs matched the missing treat exactly.",
        tags={"clue", "crumbs"},
    ),
    "juice_cupboard": Clue(
        id="juice_cupboard",
        trail="small orange drops",
        place="the cupboard by the sink",
        detect_line="small orange drops shone by the cupboard near the sink",
        proof="The little drops smelled just like the oranges.",
        tags={"clue", "juice"},
    ),
    "sugar_stage": Clue(
        id="sugar_stage",
        trail="sparkly sugar dust",
        place="the low stage curtain",
        detect_line="a sparkle of sugar dust drifted beside the low stage curtain",
        proof="The sugar glitter came from the cookies.",
        tags={"clue", "sugar"},
    ),
}

RESPONSES = {
    "calm_search": Response(
        id="calm_search",
        sense=3,
        text="The banker lowered her voice and suggested a calm clue-by-clue search instead of a noisy rush.",
        calming="A calm search helps us detect what is true.",
        tags={"detect", "calm"},
    ),
    "check_list": Response(
        id="check_list",
        sense=2,
        text="The banker took a pencil from her pocket and made a tiny list of where to look first.",
        calming="If we slow down, our eyes can detect more.",
        tags={"detect", "calm"},
    ),
    "accuse_first": Response(
        id="accuse_first",
        sense=1,
        text="The banker pointed at the nearest child and guessed before checking anything.",
        calming="Guessing loudly can make the truth hide longer.",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Mira", "Lily", "Nora", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Max", "Finn"]
TRAITS = ["careful", "curious", "patient", "bright", "gentle"]


def hiding_possible(item: ShareItem, hider: Hider, clue: Clue) -> bool:
    if item.id == "oranges":
        return clue.id == "juice_cupboard"
    if item.id == "cookies":
        return clue.id in {"crumbs_closet", "sugar_stage"}
    if item.id == "muffins":
        return clue.id == "crumbs_closet"
    return False


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for hider_id, hider in HIDERS.items():
            for clue_id, clue in CLUES.items():
                if hiding_possible(item, hider, clue):
                    combos.append((item_id, hider_id, clue_id))
    return combos


def explain_rejection(item: ShareItem, hider: Hider, clue: Clue) -> str:
    return (
        f"(No story: {item.label} would not leave the right kind of clue for {clue.place}, "
        f"so the detective turn would feel weak. Pick a clue that honestly fits the missing item.)"
    )


def explain_response(rid: str) -> str:
    response = RESPONSES[rid]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it is too hasty for this world "
        f"(sense={response.sense} < {SENSE_MIN}). Try a calmer detective move like {better}.)"
    )


@dataclass
class StoryParams:
    hall: str
    item: str
    hider: str
    clue: str
    response: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    banker_name: str
    trait: str
    seed: Optional[int] = None


def _do_hide(world: World, place: str, narrate: bool = True) -> None:
    item = world.get("item")
    item.meters["missing"] += 1
    item.location = place
    world.facts["hidden_place"] = place
    propagate(world, narrate=narrate)


def predict_find(world: World, place: str) -> dict:
    sim = world.copy()
    _do_hide(sim, place, narrate=False)
    clue = sim.get("clue")
    return {
        "clue_visible": clue.meters["visible"] >= THRESHOLD,
        "clue_place": clue.location,
    }


def setup_scene(world: World, hall: Hall, hero: Entity, friend: Entity, banker: Entity, item: ShareItem) -> None:
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(
        f"On the morning of the sharing party at {hall.place}, {hero.id} and {friend.id} helped set tables in {hall.detail}."
    )
    world.say(
        f"On the middle table sat {item.phrase}, meant for the whole room."
    )
    world.say(
        f'{banker.id}, the kind banker from the little corner bank, brought a jar of coins for the party game and smiled. "{item.sharing_line}"'
    )


def detective_pride(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} liked to pretend to be a detective and to detect tiny clues before anyone else could."
    )


def vanish(world: World, item: ShareItem, hider: Hider, clue: Clue) -> None:
    world.para()
    _do_hide(world, clue.place)
    world.say(
        f"But when the children turned back to the table, {item.plural_label} were gone."
    )
    world.say(
        "The hall suddenly felt much quieter. Even the clock seemed to tick more slowly."
    )
    world.facts["hider_reason"] = hider.reason


def panic_start(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["suspense"] += 1
    friend.memes["suspense"] += 1
    world.say(
        f'"Did somebody take them?" {friend.id} whispered. {hero.id} felt a small shiver of suspense run down {hero.pronoun("possessive")} back.'
    )


def banker_guides(world: World, banker: Entity, response: Response) -> None:
    banker.memes["calm"] += 1
    world.say(response.text)
    world.say(f'"{response.calming}" {banker.id} said.')


def detect_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["confidence"] += 1
    prediction = predict_find(world, clue.place)
    world.facts["predicted_clue_visible"] = prediction["clue_visible"]
    world.say(
        f"{hero.id} knelt, narrowed {hero.pronoun('possessive')} eyes, and tried to detect what the busy room had missed."
    )
    world.say(
        f"Soon {clue.detect_line}."
    )


def follow_clue(world: World, hero: Entity, friend: Entity, clue: Clue) -> None:
    hero.meters["steps"] += 1
    friend.meters["steps"] += 1
    world.say(
        f"{hero.id} and {friend.id} followed the clue to {clue.place}, trying not to run."
    )


def reveal(world: World, item: ShareItem, hider_cfg: Hider, clue: Clue) -> None:
    item_ent = world.get("item")
    hider = world.get("hider")
    item_ent.meters["found"] += 1
    item_ent.meters["missing"] = 0.0
    item_ent.location = clue.place
    propagate(world, narrate=False)
    world.say(
        f"There, tucked beside a stack of boxes, sat {item.phrase}."
    )
    world.say(
        f"{clue.proof}"
    )
    world.say(
        f"Then out stepped {hider.label}."
    )
    world.say(
        f'"{hider_cfg.confession}"'
    )


def accusation_check(world: World, hero: Entity, banker: Entity, hider_cfg: Hider) -> None:
    hero.memes["lesson"] += 1
    banker.memes["lesson"] += 1
    world.say(
        f"{hero.id} had been ready to blame a thief, but the truth was softer and sadder than that."
    )
    world.say(
        f'{banker.id} crouched down. "Thank you for telling the truth," {banker.pronoun()} said. "Being worried is real, but hiding things makes other people worry too."'
    )
    world.say(
        hider_cfg.courage_line
    )


def sharing_end(world: World, hero: Entity, friend: Entity, banker: Entity, item: ShareItem, hider_cfg: Hider) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    banker.memes["joy"] += 1
    world.say(
        hider_cfg.sharing_fix
    )
    world.say(
        f"Soon {hero.id} helped carry {item.plural_label} back to the middle table, and {friend.id} counted plates so every child would get some."
    )
    world.say(
        f'{banker.id} added, "The best treasure in a hall is not what we keep to ourselves, but what we share."'
    )
    world.say(
        f"By the time the party began, the hall no longer felt full of suspense. It smelled warm and sweet, and nobody was left out."
    )


def tell(
    hall: Hall,
    item: ShareItem,
    hider_cfg: Hider,
    clue: Clue,
    response: Response,
    hero_name: str,
    hero_gender: str,
    friend_name: str,
    friend_gender: str,
    banker_name: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        role="hero",
        label=hero_name,
        attrs={"trait": trait},
        tags={"detective"},
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        label=friend_name,
    ))
    banker_type = "banker_woman"
    banker = world.add(Entity(
        id=banker_name,
        kind="character",
        type=banker_type,
        role="banker",
        label=banker_name,
        tags={"banker"},
    ))
    hider = world.add(Entity(
        id="hider",
        kind="character",
        type=hider_cfg.type,
        role="hider",
        label=hider_cfg.label,
        tags=set(hider_cfg.tags),
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="food",
        label=item.label,
        phrase=item.phrase,
        role="shared_item",
        location="middle table",
        tags=set(item.tags),
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue.trail,
        phrase=clue.trail,
        role="clue",
        location=clue.place,
        tags=set(clue.tags),
    ))

    setup_scene(world, hall, hero, friend, banker, item)
    detective_pride(world, hero)
    vanish(world, item, hider_cfg, clue)
    panic_start(world, hero, friend)

    world.para()
    banker_guides(world, banker, response)
    detect_clue(world, hero, clue)
    follow_clue(world, hero, friend, clue)

    world.para()
    reveal(world, item, hider_cfg, clue)
    accusation_check(world, hero, banker, hider_cfg)
    sharing_end(world, hero, friend, banker, item, hider_cfg)

    world.facts.update(
        hall=hall,
        item_cfg=item,
        hider_cfg=hider_cfg,
        clue_cfg=clue,
        response=response,
        hero=hero,
        friend=friend,
        banker=banker,
        item=item_ent,
        clue=clue_ent,
        hider=hider,
        found=item_ent.meters["found"] >= THRESHOLD,
        lesson=hero.memes["lesson"] >= THRESHOLD,
        shared=hero.memes["joy"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "detect": [
        (
            "What does detect mean?",
            "To detect something means to notice it by looking, listening, or thinking carefully. Detectives try to detect clues that other people miss."
        )
    ],
    "banker": [
        (
            "What does a banker do?",
            "A banker helps people keep money safe and count it carefully. A banker can also help people stay calm and organized."
        )
    ],
    "sharing": [
        (
            "Why is sharing important at a party?",
            "Sharing helps make sure everyone gets a turn and nobody feels left out. It can also stop people from grabbing or hiding things because they feel worried."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A crumb, a footprint, or a drop of juice can all be clues."
        )
    ],
    "ask_first": [
        (
            "What should you do if you are afraid there will not be enough?",
            "You should ask a grown-up or another helper instead of hiding things. Asking gives other people a chance to solve the problem kindly."
        )
    ],
    "communication": [
        (
            "Why is it important to tell people when you move something?",
            "If you move something quietly, other people may think it is lost or stolen. Telling the truth early keeps a small problem from growing bigger."
        )
    ],
}
KNOWLEDGE_ORDER = ["detect", "banker", "clue", "sharing", "ask_first", "communication"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    banker = f["banker"]
    item = f["item_cfg"]
    hall = f["hall"]
    return [
        f'Write a detective-style story for a 3-to-5-year-old that includes the words "hallmnopqrstuv", "detect", and "banker".',
        f"Tell a gentle suspense story where {hero.id} searches for missing {item.label} at {hall.place} and a calm banker helps solve the mystery.",
        "Write a story with suspense, a lesson learned, and sharing, where the mystery turns out to be a misunderstanding instead of a mean theft.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    banker = f["banker"]
    item = f["item_cfg"]
    hider = f["hider_cfg"]
    hall = f["hall"]
    clue = f["clue_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id} at {hall.place}, and about {banker.id}, the banker who helped them search calmly."
        ),
        (
            f"What went missing at {hall.place}?",
            f"{item.phrase.capitalize()} went missing from the middle table. That is why the room suddenly felt tense and full of suspense."
        ),
        (
            f"How did {hero.id} try to detect the truth?",
            f"{hero.id} slowed down and looked for a real clue instead of guessing. Soon {clue.detect_line}, which showed where to search next."
        ),
        (
            f"Why had {hider.label} hidden the food?",
            f"{hider.label.capitalize()} had hidden it because {hider.reason}. The mystery was caused by worry, not by a cruel plan."
        ),
        (
            "What lesson did the children learn?",
            f"They learned not to blame people before checking the facts, and they learned that it is better to ask than to hide things. The calm search helped everyone understand each other."
        ),
        (
            "How did the story end?",
            f"They brought the food back and shared it so everyone had a turn. The ending proves the problem changed from fearful secrecy into open sharing."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detect", "banker", "sharing", "clue"} | set(f["hider_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.location:
            bits.append(f"location={e.location}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        hall="clock",
        item="muffins",
        hider="shy_child",
        clue="crumbs_closet",
        response="calm_search",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        banker_name="Mrs. Vale",
        trait="careful",
    ),
    StoryParams(
        hall="garden",
        item="oranges",
        hider="janitor",
        clue="juice_cupboard",
        response="check_list",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Nora",
        friend_gender="girl",
        banker_name="Mrs. Vale",
        trait="patient",
    ),
    StoryParams(
        hall="river",
        item="cookies",
        hider="younger_brother",
        clue="sugar_stage",
        response="calm_search",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        banker_name="Mrs. Vale",
        trait="curious",
    ),
]


ASP_RULES = r"""
clue_fits(Item, crumbs_closet) :- item(Item), Item = muffins.
clue_fits(Item, crumbs_closet) :- item(Item), Item = cookies.
clue_fits(Item, sugar_stage)   :- item(Item), Item = cookies.
clue_fits(Item, juice_cupboard) :- item(Item), Item = oranges.

valid(Item, Hider, Clue) :- item(Item), hider(Hider), clue(Clue), clue_fits(Item, Clue).

sensible(Response) :- response(Response), sense(Response, S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hall_id in HALLS:
        lines.append(asp.fact("hall", hall_id))
    for item_id in ITEMS:
        lines.append(asp.fact("item", item_id))
    for hider_id in HIDERS:
        lines.append(asp.fact("hider", hider_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


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

    py_sensible = {r.id for r in sensible_responses()}
    asp_sense = set(asp_sensible())
    if py_sensible == asp_sense:
        print(f"OK: sensible responses match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: python={sorted(py_sensible)} clingo={sorted(asp_sense)}")

    # Smoke test normal generation so verify fails if ordinary runs crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Detective-style story world: a missing shared treat, a calm banker, and a lesson about sharing."
    )
    ap.add_argument("--hall", choices=HALLS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hider", choices=HIDERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.hider and args.clue:
        item = ITEMS[args.item]
        hider = HIDERS[args.hider]
        clue = CLUES[args.clue]
        if not hiding_possible(item, hider, clue):
            raise StoryError(explain_rejection(item, hider, clue))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.hider is None or combo[1] == args.hider)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, hider_id, clue_id = rng.choice(sorted(combos))
    hall_id = args.hall or rng.choice(sorted(HALLS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    trait = rng.choice(TRAITS)
    return StoryParams(
        hall=hall_id,
        item=item_id,
        hider=hider_id,
        clue=clue_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        banker_name="Mrs. Vale",
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hall not in HALLS:
        raise StoryError(f"(Unknown hall: {params.hall})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.hider not in HIDERS:
        raise StoryError(f"(Unknown hider: {params.hider})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not hiding_possible(ITEMS[params.item], HIDERS[params.hider], CLUES[params.clue]):
        raise StoryError(explain_rejection(ITEMS[params.item], HIDERS[params.hider], CLUES[params.clue]))

    world = tell(
        hall=HALLS[params.hall],
        item=ITEMS[params.item],
        hider_cfg=HIDERS[params.hider],
        clue=CLUES[params.clue],
        response=RESPONSES[params.response],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        banker_name=params.banker_name,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (item, hider, clue) combos:\n")
        for item, hider, clue in combos:
            print(f"  {item:8} {hider:15} {clue}")
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
            header = f"### {p.hero_name}: {p.item} mystery at {p.hall} ({p.hider}, {p.clue})"
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
