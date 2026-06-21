#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py
======================================================================

A standalone story world for a tiny child-facing detective mystery built from
the seed words "chime", "choose", and "boo", with bravery as the central
feature.

A child detective hears a strange chime, sees a spooky shape, and must choose
whether to hide or investigate. The world model tracks fear, bravery, clues,
and relief so the prose follows the simulated state instead of swapping words
into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py --place attic --source wind_bell --shadow coat_rack --tool flashlight
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py --source rafters_bell --tool flashlight
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/chime_choose_boo_bravery_detective_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    nook: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    sound: str
    reveal: str
    fix: str
    places: set[str] = field(default_factory=set)
    needs: set[str] = field(default_factory=set)
    danger: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Shadow:
    id: str
    label: str
    motion: str
    reveal: str
    places: set[str] = field(default_factory=set)
    fright: int = 2
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    provides: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Bravery:
    id: str
    label: str
    value: int
    line: str
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


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        hero = world.get("hero")
        friend = world.get("friend")
        room = world.get("room")
        if room.meters["heard_chime"] >= THRESHOLD and ("chime_fear",) not in world.fired:
            world.fired.add(("chime_fear",))
            hero.memes["fear"] += 1
            friend.memes["fear"] += 1
            hero.memes["curiosity"] += 1
            changed = True
        if room.meters["saw_shadow"] >= THRESHOLD and ("shadow_fear",) not in world.fired:
            world.fired.add(("shadow_fear",))
            hero.memes["fear"] += world.facts["shadow_cfg"].fright
            friend.memes["fear"] += world.facts["shadow_cfg"].fright
            changed = True
        if hero.memes["chooses_clue"] >= THRESHOLD and ("choice_brave",) not in world.fired:
            world.fired.add(("choice_brave",))
            hero.memes["bravery"] += 1
            changed = True
        if room.meters["case_solved"] >= THRESHOLD and ("solved_relief",) not in world.fired:
            world.fired.add(("solved_relief",))
            hero.memes["fear"] = 0.0
            friend.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            friend.memes["relief"] += 1
            hero.memes["pride"] += 1
            changed = True


PLACES = {
    "attic": Place(
        id="attic",
        label="attic playroom",
        opening="a dusty attic playroom with trunks and old blankets",
        nook="the dark window corner",
        ending="The attic did not seem haunted anymore. It felt like a solved case.",
        tags={"attic", "inside"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="backyard clubhouse",
        opening="a little backyard clubhouse made from boards and bright paint",
        nook="the back wall under the small window",
        ending="The clubhouse felt cheerful again, as if the mystery had tipped its hat and gone home.",
        tags={"clubhouse", "outside"},
    ),
    "hallway": Place(
        id="hallway",
        label="upstairs hallway nook",
        opening="a long upstairs hallway with family coats and a narrow window",
        nook="the coat hook by the window",
        ending="The hallway looked ordinary again, with light on the floor and no ghost at all.",
        tags={"hallway", "inside"},
    ),
}

SOURCES = {
    "wind_bell": Source(
        id="wind_bell",
        label="little brass bell",
        sound="a silver chime chimed twice by the window",
        reveal="a little brass bell tied near the cracked window latch",
        fix="latched the window and steadied the bell string",
        places={"attic", "hallway"},
        needs={"light"},
        danger=1,
        tags={"bell", "window", "wind"},
    ),
    "rafters_bell": Source(
        id="rafters_bell",
        label="bicycle bell",
        sound="a bright chime rang from up in the rafters",
        reveal="a bicycle bell hanging from a string above the beams",
        fix="lifted the string down and hung the bell where it would not swing",
        places={"clubhouse", "attic"},
        needs={"light", "reach"},
        danger=2,
        tags={"bell", "rafters", "bike"},
    ),
    "tin_spoon": Source(
        id="tin_spoon",
        label="tin cup and spoon",
        sound="a tiny chime clinked from a shelf with jars",
        reveal="a spoon tapping a tin cup each time the loose shelf wobbled",
        fix="set the spoon inside the cup and pushed the shelf snug against the wall",
        places={"clubhouse", "hallway"},
        needs={"light"},
        danger=1,
        tags={"tin", "shelf"},
    ),
}

SHADOWS = {
    "coat_rack": Shadow(
        id="coat_rack",
        label="coat rack",
        motion="a tall shape wobbled and stretched on the wall",
        reveal="a coat rack with one floppy hat on top",
        places={"attic", "hallway"},
        fright=2,
        tags={"coat", "shadow"},
    ),
    "mop": Shadow(
        id="mop",
        label="mop",
        motion="a thin shape nodded in the corner like it knew a secret",
        reveal="a mop leaning beside a box",
        places={"clubhouse", "hallway"},
        fright=1,
        tags={"mop", "shadow"},
    ),
    "blanket_stack": Shadow(
        id="blanket_stack",
        label="blanket stack",
        motion="a humped shape shivered when the draft slipped by",
        reveal="a pile of folded blankets with one corner hanging loose",
        places={"attic", "clubhouse"},
        fright=2,
        tags={"blanket", "shadow"},
    ),
}

TOOLS = {
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        use="clicked on the flashlight and drew a yellow circle across the dark",
        provides={"light"},
        tags={"flashlight", "light"},
    ),
    "lantern": Tool(
        id="lantern",
        label="camp lantern",
        phrase="a little camp lantern",
        use="switched on the lantern, and soft light opened the room like a curtain",
        provides={"light"},
        tags={"lantern", "light"},
    ),
    "stepstool": Tool(
        id="stepstool",
        label="stepstool and flashlight",
        phrase="a stepstool and a flashlight",
        use="set the stepstool in place, then shone the flashlight up where the sound came from",
        provides={"light", "reach"},
        tags={"stool", "flashlight", "light", "reach"},
    ),
}

BRAVERIES = {
    "shaky": Bravery(
        id="shaky",
        label="a little shaky",
        value=1,
        line="My knees feel wiggly, but I can still be a detective.",
        tags={"bravery"},
    ),
    "steady": Bravery(
        id="steady",
        label="steady",
        value=2,
        line="A steady detective looks twice before guessing.",
        tags={"bravery"},
    ),
    "bold": Bravery(
        id="bold",
        label="bold",
        value=3,
        line="A bold detective follows the clue instead of the shiver.",
        tags={"bravery"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Zoe", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Theo", "Noah", "Eli", "Finn"]
FRIEND_NAMES = ["Tess", "June", "Ollie", "Pip", "Rose", "Jack"]

KNOWLEDGE = {
    "bell": [("What makes a bell chime?",
              "A bell chimes when something makes it move and strike. Wind, a string, or a bump can start the ringing.")],
    "window": [("Why can a loose window make things rattle?",
                "If a window is loose, moving air can shake it. That little shake can make nearby things tap or ring.")],
    "shadow": [("Why can shadows look spooky in the dark?",
                "In dim light, a shadow hides the real shape of an object. Your brain may guess something scary before you can see clearly.")],
    "flashlight": [("What is a flashlight for?",
                    "A flashlight helps you see in dark places. Good light makes clues easier to notice.")],
    "lantern": [("What does a lantern do?",
                 "A lantern spreads light around a room so you can see safely. It helps dark corners look ordinary again.")],
    "stool": [("Why should a child use a sturdy stepstool carefully?",
               "A sturdy stepstool helps you reach something a little higher. A grown-up should know about it so you stay safe and balanced.")],
    "bravery": [("What is bravery?",
                 "Bravery means doing the right thing even when you feel scared. It does not mean pretending you have no fear.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues and asks what really happened. Detectives do not stop at the first spooky guess.")],
}

KNOWLEDGE_ORDER = ["detective", "bravery", "shadow", "bell", "window", "flashlight", "lantern", "stool"]


def tool_fits(source: Source, tool: Tool) -> bool:
    return source.needs.issubset(tool.provides)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for source_id, source in SOURCES.items():
            if place_id not in source.places:
                continue
            for shadow_id, shadow in SHADOWS.items():
                if place_id not in shadow.places:
                    continue
                for tool_id, tool in TOOLS.items():
                    if tool_fits(source, tool):
                        combos.append((place_id, source_id, shadow_id, tool_id))
    return combos


def fear_score(source: Source, shadow: Shadow) -> int:
    return source.danger + shadow.fright


def bravery_score(bravery: Bravery, tool: Tool) -> int:
    bonus = 1 if "light" in tool.provides else 0
    return bravery.value + bonus


def outcome_for(params: "StoryParams") -> str:
    source = SOURCES[params.source]
    shadow = SHADOWS[params.shadow]
    bravery = BRAVERIES[params.bravery]
    tool = TOOLS[params.tool]
    return "alone" if bravery_score(bravery, tool) >= fear_score(source, shadow) else "assisted"


@dataclass
class StoryParams:
    place: str
    source: str
    shadow: str
    tool: str
    bravery: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="attic",
        source="wind_bell",
        shadow="coat_rack",
        tool="flashlight",
        bravery="steady",
        hero_name="Lily",
        hero_gender="girl",
        friend_name="Ollie",
        friend_gender="boy",
        parent="mother",
        seed=101,
    ),
    StoryParams(
        place="clubhouse",
        source="rafters_bell",
        shadow="blanket_stack",
        tool="stepstool",
        bravery="bold",
        hero_name="Max",
        hero_gender="boy",
        friend_name="Tess",
        friend_gender="girl",
        parent="father",
        seed=102,
    ),
    StoryParams(
        place="hallway",
        source="tin_spoon",
        shadow="coat_rack",
        tool="lantern",
        bravery="shaky",
        hero_name="Maya",
        hero_gender="girl",
        friend_name="Jack",
        friend_gender="boy",
        parent="mother",
        seed=103,
    ),
]


def explain_rejection(place: str, source: Source, shadow: Shadow, tool: Tool) -> str:
    if place not in source.places:
        return f"(No story: {source.label} does not plausibly belong in the {PLACES[place].label}.)"
    if place not in shadow.places:
        return f"(No story: {shadow.label} would not make the right spooky shape in the {PLACES[place].label}.)"
    return (f"(No story: {tool.phrase} does not provide what this clue needs. "
            f"The source needs {sorted(source.needs)}, but the tool provides {sorted(tool.provides)}.)")


def opening(world: World, hero: Entity, friend: Entity, place: Place, bravery: Bravery) -> None:
    hero.memes["bravery"] = float(bravery.value)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} liked to play detective, and on that afternoon {hero.pronoun()} brought "
        f"{friend.id} to {place.opening}. {hero.id} called it the Case Club."
    )
    world.say(
        f"{hero.id} wore a paper badge and whispered, \"Detective {hero.id} is on duty.\" "
        f"{friend.id} giggled and followed close behind."
    )
    world.say(f"{hero.id} felt {bravery.label}. \"{bravery.line}\"")


def disturbance(world: World, hero: Entity, friend: Entity, place: Place, source: Source, shadow: Shadow) -> None:
    room = world.get("room")
    room.meters["heard_chime"] += 1
    propagate(world)
    world.say(
        f"Then, from {place.nook}, {source.sound}. At the same moment, {shadow.motion}."
    )
    room.meters["saw_shadow"] += 1
    propagate(world)
    world.say(f'"Boo," {friend.id} breathed, and grabbed {hero.id}\'s sleeve.')


def choose_line(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["chooses_clue"] += 1
    propagate(world)
    world.say(
        f'{hero.id} swallowed once. "We can choose to run," {hero.pronoun()} said, '
        f'"or we can choose to look for clues."'
    )
    world.say(f"{friend.id} looked at the dark and then back at the badge. \"Clues,\" {friend.pronoun()} said, but very softly.")


def investigate_alone(world: World, hero: Entity, friend: Entity, tool: Tool, source: Source, shadow: Shadow) -> None:
    world.say(f"{hero.id} {tool.use}.")
    world.say(
        f"The spooky shape turned out to be {shadow.reveal}, and the strange sound was {source.reveal}."
    )
    world.say(
        f"{hero.id} stepped closer, noticed how the air moved, and {source.fix}."
    )
    world.get("room").meters["case_solved"] += 1
    propagate(world)
    world.say(
        f"The chime stopped. {friend.id} blinked, then laughed at the very same corner that had seemed full of ghosts."
    )


def investigate_with_help(world: World, hero: Entity, friend: Entity, parent: Entity,
                          tool: Tool, source: Source, shadow: Shadow) -> None:
    hero.memes["asks_help"] += 1
    world.say(
        f"{hero.id} took a slow breath. \"A brave detective can ask for backup,\" {hero.pronoun()} said."
    )
    world.say(
        f"{hero.id} called for {hero.pronoun('possessive')} {parent.label_word}, who came to the doorway and stayed nearby while the children checked the clue."
    )
    world.say(f"{hero.id} {tool.use}.")
    world.say(
        f"In the better light, the shape was only {shadow.reveal}, and the sound was {source.reveal}."
    )
    world.say(f"With {parent.label_word}'s calm voice nearby, {hero.id} {source.fix}.")
    world.get("room").meters["case_solved"] += 1
    propagate(world)
    world.say(
        f'"So that was it," said {friend.id}. The room sounded quiet again, and nobody said boo this time.'
    )


def closing(world: World, hero: Entity, friend: Entity, place: Place, source: Source, outcome: str) -> None:
    if outcome == "alone":
        world.say(
            f'{hero.id} tapped the paper badge and grinned. "Case closed," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} smiled up at the doorway. "Case closed with backup," {hero.pronoun()} said.'
        )
    world.say(
        f"{friend.id} asked if detectives could have cocoa after hard work, and {hero.id} said that seemed like an excellent rule."
    )
    world.say(place.ending)
    world.facts["solved_by_fix"] = source.fix


def tell(place: Place, source: Source, shadow: Shadow, tool: Tool, bravery: Bravery,
         hero_name: str, hero_gender: str, friend_name: str, friend_gender: str,
         parent_type: str) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the parent", role="parent"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    hero.attrs["name"] = hero_name
    friend.attrs["name"] = friend_name
    parent.attrs["name"] = parent.label_word

    world.facts.update(
        place=place,
        source_cfg=source,
        shadow_cfg=shadow,
        tool_cfg=tool,
        bravery_cfg=bravery,
        hero=hero,
        friend=friend,
        parent=parent,
    )

    opening(world, hero, friend, place, bravery)
    world.para()
    disturbance(world, hero, friend, place, source, shadow)
    choose_line(world, hero, friend)
    world.para()

    outcome = "alone" if bravery_score(bravery, tool) >= fear_score(source, shadow) else "assisted"
    if outcome == "alone":
        investigate_alone(world, hero, friend, tool, source, shadow)
    else:
        investigate_with_help(world, hero, friend, parent, tool, source, shadow)

    world.para()
    closing(world, hero, friend, place, source, outcome)
    world.facts["outcome"] = outcome
    world.facts["fear_score"] = fear_score(source, shadow)
    world.facts["bravery_score"] = bravery_score(bravery, tool)
    world.facts["ghost_real"] = False
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    place = world.facts["place"]
    source = world.facts["source_cfg"]
    bravery = world.facts["bravery_cfg"]
    return [
        'Write a short detective story for a 3-to-5-year-old that includes the words "chime", "choose", and "boo".',
        f"Tell a child-friendly mystery where {hero.attrs['name']} hears a chime in a {place.label}, feels {bravery.label}, and must choose whether to hide or investigate.",
        f"Write a gentle detective story where {hero.attrs['name']} and {friend.attrs['name']} think something spooky is near {place.nook}, but the clue leads to {source.label} instead of a ghost.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    parent = world.facts["parent"]
    place = world.facts["place"]
    source = world.facts["source_cfg"]
    shadow = world.facts["shadow_cfg"]
    tool = world.facts["tool_cfg"]
    outcome = world.facts["outcome"]
    hero_name = hero.attrs["name"]
    friend_name = friend.attrs["name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, who likes to play detective, and {friend_name}, who joins the case. They are exploring the {place.label} together.",
        ),
        (
            "What started the mystery?",
            f"The mystery began when the children heard {source.sound} from {place.nook} and saw a strange shape moving there. The sound and the shadow made the room feel spooky at the same time.",
        ),
        (
            f"Why did {friend_name} say boo?",
            f"{friend_name} said boo because the dark shape and the chime made the corner seem haunted. Without enough light, an ordinary object can look much scarier than it really is.",
        ),
        (
            f"What did {hero_name} choose to do?",
            f"{hero_name} chose to look for clues instead of running away. That choice mattered because it turned fear into a real investigation.",
        ),
    ]
    if outcome == "alone":
        qa.append(
            (
                f"How did {hero_name} solve the case?",
                f"{hero_name} used {tool.phrase} to see clearly, discovered {shadow.reveal}, and found that the sound was really {source.reveal}. Then {hero.pronoun()} {source.fix}, so the chime stopped.",
            )
        )
        qa.append(
            (
                f"How was bravery shown in the story?",
                f"{hero_name} felt afraid, but still walked closer and checked the clue. The story shows that bravery is not the same as having no fear; it means doing the careful right thing anyway.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero_name} solve the mystery alone?",
                f"No. {hero_name} chose to ask {hero.pronoun('possessive')} {parent.label_word} for backup before checking the clue. Asking for help was part of being brave and careful.",
            )
        )
        qa.append(
            (
                f"How did they solve the case in the end?",
                f"With {parent.label_word}'s calm help nearby, {hero_name} used {tool.phrase}, saw that the shape was {shadow.reveal}, and learned that the sound was {source.reveal}. Then {hero_name} {source.fix}, which made the room quiet again.",
            )
        )
    qa.append(
        (
            "Was there really a ghost?",
            f"No, there was no ghost at all. The mystery came from an ordinary shadow and a real object making the chime.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "bravery", "shadow"} | set(world.facts["source_cfg"].tags) | set(world.facts["tool_cfg"].tags)
    out: list[tuple[str, str]] = []
    tag_map = {
        "bell": "bell",
        "window": "window",
        "flashlight": "flashlight",
        "lantern": "lantern",
        "stool": "stool",
        "bravery": "bravery",
        "detective": "detective",
        "shadow": "shadow",
    }
    for key in KNOWLEDGE_ORDER:
        if key in tags or key in {tag_map.get(t, "") for t in tags}:
            out.extend(KNOWLEDGE[key])
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
        shown_meters = {k: v for k, v in ent.meters.items() if v}
        shown_memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if shown_meters:
            bits.append(f"meters={dict(shown_meters)}")
        if shown_memes:
            bits.append(f"memes={dict(shown_memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    lines.append(
        f"  fear_score={world.facts.get('fear_score')} bravery_score={world.facts.get('bravery_score')} outcome={world.facts.get('outcome')}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
compatible_source(P, S) :- place(P), source(S), source_place(S, P).
compatible_shadow(P, Sh) :- place(P), shadow(Sh), shadow_place(Sh, P).
tool_fits(S, T) :- source(S), tool(T), not needs_missing(S, T).
needs_missing(S, T) :- needs(S, N), not provides(T, N).

valid(P, S, Sh, T) :- compatible_source(P, S), compatible_shadow(P, Sh), tool_fits(S, T).

fear(F) :- chosen_source(S), source_danger(S, D), chosen_shadow(Sh), shadow_fright(Sh, R), F = D + R.
bravery(B) :- chosen_bravery(Br), bravery_value(Br, V), chosen_tool(T), tool_light_bonus(T, L), B = V + L.

outcome(alone) :- fear(F), bravery(B), B >= F.
outcome(assisted) :- fear(F), bravery(B), B < F.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in sorted(PLACES):
        lines.append(asp.fact("place", place_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_danger", source_id, source.danger))
        for place_id in sorted(source.places):
            lines.append(asp.fact("source_place", source_id, place_id))
        for need in sorted(source.needs):
            lines.append(asp.fact("needs", source_id, need))
    for shadow_id, shadow in SHADOWS.items():
        lines.append(asp.fact("shadow", shadow_id))
        lines.append(asp.fact("shadow_fright", shadow_id, shadow.fright))
        for place_id in sorted(shadow.places):
            lines.append(asp.fact("shadow_place", shadow_id, place_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for prov in sorted(tool.provides):
            lines.append(asp.fact("provides", tool_id, prov))
        lines.append(asp.fact("tool_light_bonus", tool_id, 1 if "light" in tool.provides else 0))
    for bravery_id, bravery in BRAVERIES.items():
        lines.append(asp.fact("bravery_kind", bravery_id))
        lines.append(asp.fact("bravery_value", bravery_id, bravery.value))
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
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_shadow", params.shadow),
        asp.fact("chosen_tool", params.tool),
        asp.fact("chosen_bravery", params.bravery),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid_combos parity holds ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = []
    for params in cases:
        py_out = outcome_for(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            bad.append((params, py_out, asp_out))
    if not bad:
        print(f"OK: outcome parity holds on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH in outcomes: {len(bad)} cases differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "chime" not in sample.story.lower():
            raise StoryError("smoke test generated an empty or malformed story")
        print("OK: smoke test generation succeeded.")
        emit(sample, trace=False, qa=False, header="### smoke test")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective story world about a spooky chime, a choice, and bravery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--shadow", choices=SHADOWS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--bravery", choices=BRAVERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combo set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.source and args.shadow and args.tool:
        if (args.place, args.source, args.shadow, args.tool) not in set(valid_combos()):
            raise StoryError(explain_rejection(args.place, SOURCES[args.source], SHADOWS[args.shadow], TOOLS[args.tool]))
    elif args.place and args.source and args.tool and args.place not in SOURCES[args.source].places:
        raise StoryError(explain_rejection(args.place, SOURCES[args.source], next(iter(SHADOWS.values())), TOOLS[args.tool]))
    elif args.place and args.shadow and args.place not in SHADOWS[args.shadow].places:
        raise StoryError(explain_rejection(args.place, next(iter(SOURCES.values())), SHADOWS[args.shadow], next(iter(TOOLS.values()))))
    elif args.source and args.tool and not tool_fits(SOURCES[args.source], TOOLS[args.tool]):
        raise StoryError(explain_rejection(args.place or sorted(SOURCES[args.source].places)[0], SOURCES[args.source], next(iter(SHADOWS.values())), TOOLS[args.tool]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.shadow is None or combo[2] == args.shadow)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source, shadow, tool = rng.choice(sorted(combos))
    bravery = args.bravery or rng.choice(sorted(BRAVERIES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_pool = FRIEND_NAMES + GIRL_NAMES + BOY_NAMES
    friend_name = args.friend_name or rng.choice([n for n in friend_pool if n != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place,
        source=source,
        shadow=shadow,
        tool=tool,
        bravery=bravery,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.shadow not in SHADOWS:
        raise StoryError(f"(Unknown shadow: {params.shadow})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.bravery not in BRAVERIES:
        raise StoryError(f"(Unknown bravery kind: {params.bravery})")
    if (params.place, params.source, params.shadow, params.tool) not in set(valid_combos()):
        raise StoryError(explain_rejection(params.place, SOURCES[params.source], SHADOWS[params.shadow], TOOLS[params.tool]))

    world = tell(
        PLACES[params.place],
        SOURCES[params.source],
        SHADOWS[params.shadow],
        TOOLS[params.tool],
        BRAVERIES[params.bravery],
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
        params.parent,
    )
    story = world.render().replace("hero", params.hero_name).replace("friend", params.friend_name)
    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (place, source, shadow, tool) combos:\n")
        for place, source, shadow, tool in combos:
            print(f"  {place:10} {source:12} {shadow:14} {tool}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.place} / {p.source} / {p.shadow} / {p.tool} ({outcome_for(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
