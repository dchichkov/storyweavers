#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stench_quest_comedy.py
=================================================

A standalone storyworld about a silly little quest: two children smell a
mysterious stench, imagine a ridiculous monster, follow the clues, and discover
that the "beast" is really an ordinary smelly mess that must be cleaned up the
sensible way.

The world model favors a narrow, common-sense slice of this domain:
- a source of stink must plausibly belong in the chosen place
- the fix must actually fit the kind of mess
- the story is told as a comic quest, but the solution is practical

Run it
------
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py --all
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py --place classroom --source sandwich
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py --source bait_jar --place classroom
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py --qa --json
python storyworlds/worlds/gpt-5.4/stench_quest_comedy.py --verify
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
SENSE_MIN = 2


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
    tags: set[str] = field(default_factory=set)
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
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
            "teacher": "teacher",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    nook: str
    floor_detail: str
    helper_type: str
    helper_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestFrame:
    id: str
    team_name: str
    boast: str
    map_line: str
    call_word: str
    ending_cheer: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StinkSource:
    id: str
    label: str
    phrase: str
    kind: str
    smell_line: str
    clue_line: str
    monster_name: str
    found_in: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    handles: set[str] = field(default_factory=set)
    sense: int = 0
    action_text: str = ""
    result_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    quest: str
    source: str
    fix: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place_cfg: Place) -> None:
        self.place_cfg = place_cfg
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "partner"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place_cfg)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_stench_fills_room(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    room = world.get("room")
    if source.meters["stench"] >= THRESHOLD and room.meters["stench"] < THRESHOLD:
        sig = ("stench", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["stench"] += 1
            for kid in world.kids():
                kid.memes["disgust"] += 1
            out.append("__stench__")
    return out


def _r_quest_creates_clue(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    source = world.get("source")
    if room.meters["stench"] < THRESHOLD:
        return out
    if sum(k.memes["questing"] for k in world.kids()) < THRESHOLD:
        return out
    if source.hidden and source.meters["clue"] < THRESHOLD:
        sig = ("clue", source.id)
        if sig not in world.fired:
            world.fired.add(sig)
            source.meters["clue"] += 1
            for kid in world.kids():
                kid.memes["curiosity"] += 1
            out.append("__clue__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="stench_fills_room", tag="physical", apply=_r_stench_fills_room),
    Rule(name="quest_creates_clue", tag="social", apply=_r_quest_creates_clue),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(s for s in items if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def source_allowed(place_id: str, source_id: str) -> bool:
    return place_id in SOURCES[source_id].places


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def fix_works(source: StinkSource, fix: Fix) -> bool:
    return source.kind in fix.handles


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for source_id, source in SOURCES.items():
            if not source_allowed(place_id, source_id):
                continue
            for fix_id, fix in FIXES.items():
                if fix.sense >= SENSE_MIN and fix_works(source, fix):
                    combos.append((place_id, source_id, fix_id))
    return combos


def explain_place_source(place: Place, source: StinkSource) -> str:
    return (
        f"(No story: {source.phrase} does not belong in {place.phrase}, so the quest "
        f"would feel fake. Pick a place where that smelly thing could really be found.)"
    )


def explain_fix(source: StinkSource, fix: Fix) -> str:
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix.id}': it is too silly to count as a sensible solution. "
            f"A quest can be funny, but the cleanup must really solve the stink.)"
        )
    return (
        f"(No story: {fix.label} does not fix {source.phrase}. The remedy must fit the "
        f"kind of smell, not just make the children wave their hands around.)"
    )


def outcome_of(params: StoryParams) -> str:
    source = SOURCES[params.source]
    fix = FIXES[params.fix]
    if source_allowed(params.place, params.source) and fix.sense >= SENSE_MIN and fix_works(source, fix):
        return "solved"
    return "stinky"


def predict_clue(world: World) -> dict:
    sim = world.copy()
    for kid in sim.kids():
        kid.memes["questing"] += 1
    propagate(sim, narrate=False)
    source = sim.get("source")
    room = sim.get("room")
    return {
        "room_stinks": room.meters["stench"] >= THRESHOLD,
        "clue_found": source.meters["clue"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, partner: Entity, quest: QuestFrame, place: Place) -> None:
    for kid in (hero, partner):
        kid.memes["joy"] += 1
    world.say(
        f"{hero.id} and {partner.id} loved turning ordinary afternoons into grand quests. "
        f"In {place.phrase}, they had named themselves {quest.team_name}."
    )
    world.say(
        f'"{quest.boast}" {hero.id} said, while {partner.id} drew {quest.map_line} in the air with one finger.'
    )


def start_stench(world: World, source: Entity, source_cfg: StinkSource, place: Place) -> None:
    source.meters["stench"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But that day, before their quest had even begun, a stench drifted through {place.phrase}. "
        f"{source_cfg.smell_line}"
    )


def declare_quest(world: World, hero: Entity, partner: Entity, quest: QuestFrame, source_cfg: StinkSource) -> None:
    for kid in (hero, partner):
        kid.memes["questing"] += 1
        kid.memes["bravery"] += 1
    pred = predict_clue(world)
    world.facts["pred_room_stinks"] = pred["room_stinks"]
    world.facts["pred_clue_found"] = pred["clue_found"]
    world.say(
        f'{hero.id} lifted one hand like a captain on a windy ship. "{quest.call_word}! '
        f'A stink-beast is near."'
    )
    world.say(
        f'{partner.id} pinched {partner.pronoun("possessive")} nose. "If it is a beast, I hope it is a very small one," '
        f'{partner.pronoun()} said.'
    )
    if pred["clue_found"]:
        world.say(source_cfg.clue_line)


def false_guess(world: World, hero: Entity, partner: Entity, source_cfg: StinkSource) -> None:
    hero.memes["imagination"] += 1
    partner.memes["imagination"] += 1
    world.say(
        f"For one very dramatic moment, they were sure the smell belonged to {source_cfg.monster_name}. "
        f"{partner.id} even held up a ruler like a sword."
    )


def track_trail(world: World, hero: Entity, partner: Entity, place: Place) -> None:
    room = world.get("room")
    room.meters["searched"] += 1
    hero.memes["determination"] += 1
    partner.memes["determination"] += 1
    world.say(
        f"They marched past {place.floor_detail}, sniffing in tiny heroic snorts, until the smell grew stronger near {place.nook}."
    )


def discover(world: World, hero: Entity, partner: Entity, source: Entity, source_cfg: StinkSource) -> None:
    source.hidden = False
    source.meters["found"] += 1
    hero.memes["surprise"] += 1
    partner.memes["surprise"] += 1
    world.say(
        f"{hero.id} peeked behind {source_cfg.found_in} and then jumped back. "
        f'"Not a monster," {hero.pronoun()} said. "Just {source_cfg.phrase}!"'
    )
    world.say(
        f"{partner.id} stared for a beat and then giggled. The terrible beast had no claws at all. "
        f"It was only a smelly ordinary mess."
    )


def fetch_helper(world: World, helper: Entity, hero: Entity, partner: Entity, place: Place) -> None:
    for kid in (hero, partner):
        kid.memes["sense"] += 1
    world.say(
        f"Neither child touched it. They hurried to get {helper.label_word}, because even brave questers know when a grown-up should take the next turn."
    )


def clean_up(world: World, helper: Entity, hero: Entity, partner: Entity,
             source: Entity, source_cfg: StinkSource, fix: Fix, place: Place) -> None:
    source.meters["stench"] = 0.0
    source.meters["clean"] += 1
    world.get("room").meters["stench"] = 0.0
    for kid in (hero, partner):
        kid.memes["relief"] += 1
        kid.memes["pride"] += 1
        kid.memes["disgust"] = 0.0
    world.say(
        f"{helper.label_word.capitalize()} came over, took one sniff, and did not faint even a little. "
        f"{helper.pronoun().capitalize()} {fix.action_text}."
    )
    world.say(fix.result_text)
    world.say(
        f"Soon {place.phrase} smelled ordinary again, which was much better than smelling legendary."
    )


def ending(world: World, hero: Entity, partner: Entity, quest: QuestFrame, place: Place) -> None:
    hero.memes["joy"] += 1
    partner.memes["joy"] += 1
    world.say(
        f'{hero.id} tapped the floor with a spoon as if it were a royal trumpet. "{quest.ending_cheer}!"'
    )
    world.say(
        f"{partner.id} bowed toward {place.phrase}. The room was quiet, the air was fresh, and nobody had to battle a single dragon after all."
    )


def tell(place: Place, quest: QuestFrame, source_cfg: StinkSource, fix: Fix,
         hero_name: str = "Lily", hero_gender: str = "girl",
         partner_name: str = "Tom", partner_gender: str = "boy",
         helper_type: str = "mother") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            role="helper",
            label=place.helper_word,
        )
    )
    room = world.add(Entity(id="room", type="room", label=place.label))
    source = world.add(
        Entity(
            id="source",
            type="source",
            label=source_cfg.label,
            phrase=source_cfg.phrase,
            hidden=True,
            tags=set(source_cfg.tags),
            attrs={"kind": source_cfg.kind},
        )
    )

    introduce(world, hero, partner, quest, place)
    start_stench(world, source, source_cfg, place)

    world.para()
    declare_quest(world, hero, partner, quest, source_cfg)
    false_guess(world, hero, partner, source_cfg)
    track_trail(world, hero, partner, place)

    world.para()
    discover(world, hero, partner, source, source_cfg)
    fetch_helper(world, helper, hero, partner, place)
    clean_up(world, helper, hero, partner, source, source_cfg, fix, place)

    world.para()
    ending(world, hero, partner, quest, place)

    world.facts.update(
        place=place,
        quest=quest,
        source_cfg=source_cfg,
        fix=fix,
        hero=hero,
        partner=partner,
        helper=helper,
        source=source,
        outcome="solved",
        clue_found=source.meters["found"] >= THRESHOLD,
        room_fresh=world.get("room").meters["stench"] < THRESHOLD,
    )
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="classroom",
        phrase="the classroom",
        nook="the row of cubbies by the window",
        floor_detail="little chairs and a paper alphabet rug",
        helper_type="teacher",
        helper_word="teacher",
        tags={"school"},
    ),
    "clubhouse": Place(
        id="clubhouse",
        label="clubhouse",
        phrase="the backyard clubhouse",
        nook="the wobbly storage bench",
        floor_detail="a crate of crayons and a pirate flag made from an old towel",
        helper_type="father",
        helper_word="dad",
        tags={"clubhouse"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        phrase="the kitchen",
        nook="the bottom cupboard by the broom",
        floor_detail="chair legs and a line of sun on the tiles",
        helper_type="mother",
        helper_word="mom",
        tags={"kitchen"},
    ),
}

QUESTS = {
    "knights": QuestFrame(
        id="knights",
        team_name="the Knights of the Sniffing Table",
        boast="By my brave elbows, no smell can hide from us",
        map_line="an invisible treasure map",
        call_word="Quest time",
        ending_cheer="The kingdom is saved from stink",
        tags={"quest"},
    ),
    "rangers": QuestFrame(
        id="rangers",
        team_name="the Brave Nose Rangers",
        boast="We track clues faster than sneezes",
        map_line="a secret trail across the sky",
        call_word="Quest time",
        ending_cheer="The great sniffing mission is done",
        tags={"quest"},
    ),
    "captains": QuestFrame(
        id="captains",
        team_name="the Captains of the Fresh-Air Fleet",
        boast="We sail straight into mysterious smells",
        map_line="waves and islands no one else could see",
        call_word="Quest time",
        ending_cheer="Fresh air for every sailor",
        tags={"quest"},
    ),
}

SOURCES = {
    "sandwich": StinkSource(
        id="sandwich",
        label="sandwich",
        phrase="a forgotten egg sandwich",
        kind="food",
        smell_line="It was the sort of smell that made noses wrinkle first and questions arrive second.",
        clue_line="A faint line of smell seemed to point toward the cubbies like a rude little arrow.",
        monster_name="the Goblin of Rotten Lunches",
        found_in="a backpack pocket",
        places={"classroom", "clubhouse", "kitchen"},
        tags={"food", "stench"},
    ),
    "socks": StinkSource(
        id="socks",
        label="socks",
        phrase="a pair of sweaty socks",
        kind="laundry",
        smell_line="The air went thick and socky, as if someone had mixed feet with old thunderclouds.",
        clue_line="The smell seemed to crawl in lazy loops from one corner of the room to another.",
        monster_name="the Sock Ogre of Doom",
        found_in="the bench lid",
        places={"classroom", "clubhouse"},
        tags={"laundry", "stench"},
    ),
    "bait_jar": StinkSource(
        id="bait_jar",
        label="jar",
        phrase="an open bait jar",
        kind="trash",
        smell_line="The smell was sharp and swampy, and it seemed to slap the air with a wet little hand.",
        clue_line="Even the dust motes looked as if they wanted to run away from the storage bench.",
        monster_name="the Swamp Dragon of Yuck",
        found_in="the storage box",
        places={"clubhouse", "kitchen"},
        tags={"trash", "stench"},
    ),
    "compost_bowl": StinkSource(
        id="compost_bowl",
        label="bowl",
        phrase="a forgotten compost bowl",
        kind="trash",
        smell_line="A sour vegetable smell floated up and made the whole room feel as if it had sighed too long.",
        clue_line="The stink grew stronger near the bottom cupboard, where even the spoons seemed worried.",
        monster_name="the Broccoli Bog Beast",
        found_in="the bottom cupboard",
        places={"kitchen"},
        tags={"trash", "stench"},
    ),
}

FIXES = {
    "bin_and_wash": Fix(
        id="bin_and_wash",
        label="throw it away and wash the container",
        handles={"food", "trash"},
        sense=3,
        action_text="wrapped the smelly thing, dropped it into the outside bin, and washed the container with soap and warm water",
        result_text="That fixed the real problem instead of merely arguing with the smell.",
        qa_text="wrapped it, threw it away, and washed the container with soap and water",
        tags={"cleanup", "soap"},
    ),
    "laundry_basket": Fix(
        id="laundry_basket",
        label="carry it to the laundry and start a wash",
        handles={"laundry"},
        sense=3,
        action_text="pinched the socks by one corner, carried them straight to the laundry basket, and started a soapy wash",
        result_text="The socks were off on their own bubbling adventure, and the room stopped smelling like tired toes.",
        qa_text="put the socks in the laundry and washed them",
        tags={"laundry", "soap"},
    ),
    "window_only": Fix(
        id="window_only",
        label="open a window and hope",
        handles=set(),
        sense=1,
        action_text="opened the window and waved one hand through the air",
        result_text="The air moved around, but the real stink would still be sitting there, grinning.",
        qa_text="opened a window and hoped the smell would leave",
        tags={"window"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]


KNOWLEDGE = {
    "food": [
        (
            "Why can old food smell bad?",
            "Old food changes as it sits too long, and tiny germs help break it down. That can make a strong bad smell."
        )
    ],
    "laundry": [
        (
            "Why do sweaty socks stink?",
            "Sweaty socks trap sweat and germs in warm cloth. After a while, that can make a very strong smell."
        )
    ],
    "trash": [
        (
            "Why should smelly trash be thrown away?",
            "Smelly trash can make a room unpleasant and can attract bugs. Throwing it away and cleaning up keeps the place healthier and nicer."
        )
    ],
    "soap": [
        (
            "What does soap help with?",
            "Soap helps lift away grease, dirt, and smelly bits when you wash something. That is why soap is useful in cleaning."
        )
    ],
    "cleanup": [
        (
            "What is a good way to solve a bad smell?",
            "You solve a bad smell by finding what is causing it and cleaning or removing that thing. Waving your hands at the air does not fix the real problem."
        )
    ],
    "quest": [
        (
            "What is a quest in a story?",
            "A quest is a trip or mission to solve a problem or find something important. In a funny story, the quest can be grand even when the problem is small."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "food", "laundry", "trash", "cleanup", "soap"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    quest = f["quest"]
    source_cfg = f["source_cfg"]
    place = f["place"]
    return [
        (
            f'Write a funny quest story for a 3-to-5-year-old that includes the word "stench" '
            f'and takes place in {place.phrase}.'
        ),
        (
            f"Tell a comedy story where {hero.id} and {partner.id} treat a bad smell like a grand quest, "
            f"only to discover that the terrible beast is really {source_cfg.phrase}."
        ),
        (
            f'Write a child-facing story in a playful quest style where the heroes call themselves '
            f'"{quest.team_name}" and solve a stinky problem in a sensible way.'
        ),
    ]


def pair_noun(hero: Entity, partner: Entity) -> str:
    if hero.type == "girl" and partner.type == "girl":
        return "two girls"
    if hero.type == "boy" and partner.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    helper = f["helper"]
    quest = f["quest"]
    place = f["place"]
    source_cfg = f["source_cfg"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(hero, partner)}, {hero.id} and {partner.id}. They turned a bad smell into a comic quest, and {helper.label_word} helped at the end."
        ),
        (
            "What problem started the quest?",
            f"A stench drifted through {place.phrase}, so the children decided to hunt for the cause. The bad smell is what turned their ordinary afternoon into a mission."
        ),
        (
            "What did the children think the smell might be?",
            f"They joked that it might be {source_cfg.monster_name}. That silly guess makes the middle of the story funny before they learn the real answer."
        ),
        (
            "What was really causing the smell?",
            f"The smell came from {source_cfg.phrase}. When they looked in the right spot, they found an ordinary smelly mess instead of a monster."
        ),
        (
            f"Why did {hero.id} and {partner.id} get {helper.label_word} instead of touching it themselves?",
            f"They knew the sensible thing was to ask a grown-up to handle the smelly mess. Their quest was brave, but the cleanup still needed help from {helper.label_word}."
        ),
        (
            "How was the problem solved?",
            f"{helper.label_word.capitalize()} {fix.qa_text}. That fixed the real source of the stink, so the room could smell fresh again."
        ),
        (
            "How did the story end?",
            f"It ended with the air fresh again and the children cheering as if they had saved a whole kingdom. The last image shows that the quest changed the room from stinky to comfortable."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["quest"].tags) | set(world.facts["source_cfg"].tags) | set(world.facts["fix"].tags)
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
        if ent.hidden:
            bits.append("hidden=True")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        quest="knights",
        source="sandwich",
        fix="bin_and_wash",
        hero="Lily",
        hero_gender="girl",
        partner="Tom",
        partner_gender="boy",
        helper="teacher",
    ),
    StoryParams(
        place="clubhouse",
        quest="rangers",
        source="socks",
        fix="laundry_basket",
        hero="Max",
        hero_gender="boy",
        partner="Mia",
        partner_gender="girl",
        helper="father",
    ),
    StoryParams(
        place="kitchen",
        quest="captains",
        source="compost_bowl",
        fix="bin_and_wash",
        hero="Ava",
        hero_gender="girl",
        partner="Ben",
        partner_gender="boy",
        helper="mother",
    ),
    StoryParams(
        place="clubhouse",
        quest="knights",
        source="bait_jar",
        fix="bin_and_wash",
        hero="Theo",
        hero_gender="boy",
        partner="Nora",
        partner_gender="girl",
        helper="father",
    ),
]


ASP_RULES = r"""
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
works(Src, Fix) :- source_kind(Src, K), handles(Fix, K).
valid(Place, Src, Fix) :- source_in(Src, Place), sensible_fix(Fix), works(Src, Fix).

solved :- chosen_place(P), chosen_source(S), chosen_fix(F), valid(P, S, F).
outcome(solved) :- solved.
outcome(stinky) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("source_kind", source_id, source.kind))
        for place_id in sorted(source.places):
            lines.append(asp.fact("source_in", source_id, place_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for kind in sorted(fix.handles):
            lines.append(asp.fact("handles", fix_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[StoryParams] = list(CURATED)
    for place_id, source_id, fix_id in sorted(valid_combos()):
        cases.append(
            StoryParams(
                place=place_id,
                quest=next(iter(QUESTS)),
                source=source_id,
                fix=fix_id,
                hero="Lily",
                hero_gender="girl",
                partner="Tom",
                partner_gender="boy",
                helper=PLACES[place_id].helper_type,
            )
        )
    mismatch = 0
    for params in cases:
        if outcome_of(params) != asp_outcome(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: ASP outcome model matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Funny quest storyworld: children chase a mysterious stench and solve it sensibly."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=["mother", "father", "teacher"])
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (place, source, fix) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random, gender: Optional[str] = None, avoid: str = "") -> tuple[str, str]:
    g = gender or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if g == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), g


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place is not None and args.place not in PLACES:
        raise StoryError("(Unknown place.)")
    if args.quest is not None and args.quest not in QUESTS:
        raise StoryError("(Unknown quest frame.)")
    if args.source is not None and args.source not in SOURCES:
        raise StoryError("(Unknown source.)")
    if args.fix is not None and args.fix not in FIXES:
        raise StoryError("(Unknown fix.)")

    if args.place and args.source and not source_allowed(args.place, args.source):
        raise StoryError(explain_place_source(PLACES[args.place], SOURCES[args.source]))
    if args.source and args.fix:
        if not fix_works(SOURCES[args.source], FIXES[args.fix]) or FIXES[args.fix].sense < SENSE_MIN:
            raise StoryError(explain_fix(SOURCES[args.source], FIXES[args.fix]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, fix_id = rng.choice(sorted(combos))
    quest_id = args.quest or rng.choice(sorted(QUESTS))
    helper = args.helper or PLACES[place_id].helper_type

    hero_name, hero_gender = pick_child(rng, args.hero_gender)
    if args.hero:
        hero_name = args.hero
    partner_name, partner_gender = pick_child(rng, args.partner_gender, avoid=hero_name)
    if args.partner:
        partner_name = args.partner

    return StoryParams(
        place=place_id,
        quest=quest_id,
        source=source_id,
        fix=fix_id,
        hero=hero_name,
        hero_gender=hero_gender,
        partner=partner_name,
        partner_gender=partner_gender,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}').")
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest '{params.quest}').")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source '{params.source}').")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}').")
    if not source_allowed(params.place, params.source):
        raise StoryError(explain_place_source(PLACES[params.place], SOURCES[params.source]))
    if FIXES[params.fix].sense < SENSE_MIN or not fix_works(SOURCES[params.source], FIXES[params.fix]):
        raise StoryError(explain_fix(SOURCES[params.source], FIXES[params.fix]))

    world = tell(
        place=PLACES[params.place],
        quest=QUESTS[params.quest],
        source_cfg=SOURCES[params.source],
        fix=FIXES[params.fix],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        partner_name=params.partner,
        partner_gender=params.partner_gender,
        helper_type=params.helper,
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
        print(f"{len(combos)} valid (place, source, fix) combos:\n")
        for place_id, source_id, fix_id in combos:
            print(f"  {place_id:10} {source_id:12} {fix_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} & {p.partner}: {p.source} in {p.place} ({p.quest})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
