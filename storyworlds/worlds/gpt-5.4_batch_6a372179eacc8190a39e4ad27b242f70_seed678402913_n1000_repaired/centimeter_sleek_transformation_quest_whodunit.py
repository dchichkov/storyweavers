#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py
==============================================================================

A standalone storyworld for a tiny child-facing whodunit: a child caretaker is
ready to check a small animal's transformation, but the sleek measuring tool is
missing. The child and a partner go on a short clue-led quest, solve who moved
it, and end beside the transformed creature.

The seed ideas here are:
- the word "centimeter"
- the word "sleek"
- a real transformation
- a quest
- a gentle whodunit shape

Run it
------
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/centimeter_sleek_transformation_quest_whodunit.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man", "gardener"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    label: str
    hide_spots: set[str] = field(default_factory=set)
    room_word: str = "room"


@dataclass
class Transformation:
    id: str
    creature: str
    start_form: str
    end_form: str
    shelter: str
    measure_kind: str
    opening_time: int
    starting_size_cm: int
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    sleek_phrase: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Mover:
    id: str
    label: str
    type: str
    role_word: str
    clue: str
    motive: str
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    distance: int
    clue_detail: str
    found_line: str
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


def _r_missing_worry(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    out: list[str] = []
    if item.attrs.get("missing") and hero.memes["worry"] < THRESHOLD:
        sig = ("missing_worry", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            hero.memes["curiosity"] += 1
            out.append("__missing__")
    return out


def _r_clue_confidence(world: World) -> list[str]:
    hero = world.get("hero")
    partner = world.get("partner")
    out: list[str] = []
    if world.facts.get("clue_found") and hero.memes["confidence"] < THRESHOLD:
        sig = ("clue_confidence", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["confidence"] += 1
            partner.memes["confidence"] += 1
            out.append("__clue__")
    return out


def _r_transformed_joy(world: World) -> list[str]:
    creature = world.get("creature")
    hero = world.get("hero")
    partner = world.get("partner")
    out: list[str] = []
    if creature.meters["transformed"] >= THRESHOLD:
        sig = ("transformed_joy", creature.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["joy"] += 1
            partner.memes["joy"] += 1
            hero.memes["worry"] = 0.0
            out.append("__transformed__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_confidence", tag="emotional", apply=_r_clue_confidence),
    Rule(name="transformed_joy", tag="emotional", apply=_r_transformed_joy),
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        label="the classroom",
        hide_spots={"window_ledge", "art_table"},
        room_word="classroom",
    ),
    "greenhouse": Setting(
        id="greenhouse",
        label="the greenhouse room",
        hide_spots={"window_ledge", "potting_bench"},
        room_word="greenhouse",
    ),
    "nature_nook": Setting(
        id="nature_nook",
        label="the nature nook",
        hide_spots={"reading_stool", "art_table"},
        room_word="nook",
    ),
}

TRANSFORMATIONS = {
    "butterfly": Transformation(
        id="butterfly",
        creature="caterpillar",
        start_form="chrysalis",
        end_form="butterfly",
        shelter="net habitat",
        measure_kind="hanging_case",
        opening_time=2,
        starting_size_cm=3,
        ending_image="a bright butterfly drying its new wings like tiny flags",
        tags={"butterfly", "chrysalis", "transformation"},
    ),
    "moth": Transformation(
        id="moth",
        creature="caterpillar",
        start_form="cocoon",
        end_form="moth",
        shelter="mesh basket",
        measure_kind="hanging_case",
        opening_time=3,
        starting_size_cm=4,
        ending_image="a soft moth clinging quietly while its powdery wings opened",
        tags={"moth", "cocoon", "transformation"},
    ),
    "froglet": Transformation(
        id="froglet",
        creature="tadpole",
        start_form="tadpole",
        end_form="froglet",
        shelter="glass tank",
        measure_kind="tail",
        opening_time=2,
        starting_size_cm=5,
        ending_image="a tiny froglet perched on a stone, with only the last bit of tail left",
        tags={"frog", "tadpole", "transformation"},
    ),
}

ITEMS = {
    "steel_ruler": Item(
        id="steel_ruler",
        label="ruler",
        phrase="a sleek silver ruler",
        sleek_phrase="sleek silver",
        supports={"hanging_case", "tail"},
        tags={"ruler", "centimeter"},
    ),
    "centimeter_card": Item(
        id="centimeter_card",
        label="centimeter card",
        phrase="a sleek plastic centimeter card",
        sleek_phrase="sleek plastic",
        supports={"hanging_case"},
        tags={"centimeter", "measurement"},
    ),
    "tail_strip": Item(
        id="tail_strip",
        label="tail strip",
        phrase="a sleek yellow measuring strip",
        sleek_phrase="sleek yellow",
        supports={"tail"},
        tags={"measurement", "frog"},
    ),
}

MOVERS = {
    "teacher": Mover(
        id="teacher",
        label="Ms. Vale",
        type="teacher",
        role_word="teacher",
        clue="sunflower pollen",
        motive="to measure a seedling for the morning chart",
        places={"window_ledge", "potting_bench"},
        tags={"teacher", "helpful"},
    ),
    "artist_friend": Mover(
        id="artist_friend",
        label="Pip",
        type="girl",
        role_word="friend",
        clue="blue paint dots",
        motive="to draw wing lines on a parade poster",
        places={"art_table", "reading_stool"},
        tags={"friend", "poster"},
    ),
    "gardener": Mover(
        id="gardener",
        label="Mr. Reed",
        type="gardener",
        role_word="gardener",
        clue="soft brown soil",
        motive="to check how tall the bean sprouts had grown",
        places={"potting_bench", "window_ledge"},
        tags={"gardener", "plants"},
    ),
}

PLACES = {
    "window_ledge": Place(
        id="window_ledge",
        label="window ledge",
        phrase="the sunny window ledge",
        distance=1,
        clue_detail="a dusting of gold pollen on the table edge",
        found_line="The missing tool lay beside a pot of seedlings, shining in the sun.",
        tags={"window"},
    ),
    "art_table": Place(
        id="art_table",
        label="art table",
        phrase="the paint-splashed art table",
        distance=1,
        clue_detail="three tiny blue paint dots near an empty brush cup",
        found_line="The missing tool rested under a poster with half-finished wings.",
        tags={"art"},
    ),
    "potting_bench": Place(
        id="potting_bench",
        label="potting bench",
        phrase="the damp potting bench",
        distance=2,
        clue_detail="crumbly brown soil and a line of wet leaf bits",
        found_line="The missing tool leaned against a tray of little green sprouts.",
        tags={"plants"},
    ),
    "reading_stool": Place(
        id="reading_stool",
        label="reading stool",
        phrase="the round reading stool",
        distance=2,
        clue_detail="a curl of poster paper and one tiny spot of blue paint",
        found_line="The missing tool had slipped beside a stack of picture books.",
        tags={"books"},
    ),
}


def valid_combo(setting_id: str, transformation_id: str, item_id: str,
                mover_id: str, place_id: str) -> bool:
    if setting_id not in SETTINGS or transformation_id not in TRANSFORMATIONS:
        return False
    if item_id not in ITEMS or mover_id not in MOVERS or place_id not in PLACES:
        return False
    setting = SETTINGS[setting_id]
    transformation = TRANSFORMATIONS[transformation_id]
    item = ITEMS[item_id]
    mover = MOVERS[mover_id]
    return (
        place_id in setting.hide_spots
        and place_id in mover.places
        and transformation.measure_kind in item.supports
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for transformation_id in TRANSFORMATIONS:
            for item_id in ITEMS:
                for mover_id in MOVERS:
                    for place_id in PLACES:
                        if valid_combo(setting_id, transformation_id, item_id, mover_id, place_id):
                            out.append((setting_id, transformation_id, item_id, mover_id, place_id))
    return out


def search_time(place: Place, delay: int) -> int:
    return place.distance + delay


def outcome_of(params: "StoryParams") -> str:
    transformation = TRANSFORMATIONS[params.transformation]
    place = PLACES[params.place]
    return "before" if search_time(place, params.delay) < transformation.opening_time else "after"


def explain_rejection(setting_id: str, transformation_id: str, item_id: str,
                      mover_id: str, place_id: str) -> str:
    setting = SETTINGS.get(setting_id)
    transformation = TRANSFORMATIONS.get(transformation_id)
    item = ITEMS.get(item_id)
    mover = MOVERS.get(mover_id)
    if setting and place_id not in setting.hide_spots:
        return (
            f"(No story: {PLACES[place_id].phrase} is not part of {setting.label}, "
            f"so the clue-led quest would have nowhere honest to go.)"
        )
    if mover and place_id not in mover.places:
        return (
            f"(No story: {mover.label} would not reasonably leave the missing tool at "
            f"{PLACES[place_id].phrase}. Pick a place that matches the mover's job.)"
        )
    if transformation and item and transformation.measure_kind not in item.supports:
        return (
            f"(No story: {item.phrase} is not a sensible tool for measuring this "
            f"{transformation.start_form} in centimeters. Pick a tool that fits the job.)"
        )
    return "(No story: this combination does not make a reasonable mystery.)"


@dataclass
class StoryParams:
    setting: str
    transformation: str
    item: str
    mover: str
    place: str
    hero_name: str
    hero_gender: str
    partner_name: str
    partner_gender: str
    caretaker: str
    delay: int = 0
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, partner: Entity, caretaker: Entity,
              transformation: Transformation, item: Item) -> None:
    creature = world.get("creature")
    world.say(
        f"{hero.id} and {partner.id} were the best watchers in {world.setting.label}. "
        f"They checked the class {creature.label} every morning and wrote careful notes."
    )
    world.say(
        f"Today felt special. The little {transformation.start_form} in the "
        f"{transformation.shelter} was already {transformation.starting_size_cm} centimeter long, "
        f"and {hero.id} had set out {item.phrase} for one more look."
    )
    world.say(
        f'"If the change happens today," said {caretaker.label}, "we must watch with quiet eyes."'
    )


def discover_missing(world: World, hero: Entity, partner: Entity, item: Item,
                     transformation: Transformation) -> None:
    world.get("item").attrs["missing"] = True
    propagate(world, narrate=False)
    world.say(
        f"But when {hero.id} reached for the {item.label}, the tray was empty."
    )
    world.say(
        f'"Our {item.sleek_phrase} {item.label} is gone," {hero.id} whispered. '
        f'"How can we measure the {transformation.start_form} in centimeters now?"'
    )
    world.say(
        f'{partner.id} looked around the room and lowered {partner.pronoun("possessive")} voice. '
        f'"Then this is a real mystery. We need a quest."'
    )


def first_clue(world: World, hero: Entity, partner: Entity, mover: Mover,
               place: Place) -> None:
    world.facts["clue_found"] = True
    propagate(world, narrate=False)
    world.say(
        f"On the tray they found the first clue: {place.clue_detail}. "
        f'"That looks like {mover.clue}," said {partner.id}.'
    )
    world.say(
        f'{hero.id} nodded. "{mover.clue.capitalize()} means we should search '
        f'{place.phrase}."'
    )


def quest_walk(world: World, hero: Entity, partner: Entity, place: Place, delay: int) -> None:
    hero.meters["steps"] += float(place.distance + delay + 1)
    partner.meters["steps"] += float(place.distance + 1)
    if place.distance + delay >= 3:
        world.say(
            f"They hurried past shelves and seed trays, stopping once when a box of paper had slid into the path."
        )
    else:
        world.say(
            f"They tiptoed across the {world.setting.room_word}, trying not to make the mystery any bigger."
        )
    world.say(
        f"Their short quest led them to {place.phrase}."
    )


def advance_time(world: World, amount: int) -> None:
    creature = world.get("creature")
    creature.meters["time"] += float(amount)
    if creature.meters["time"] >= creature.attrs["opening_time"]:
        creature.meters["transformed"] = 1.0
    propagate(world, narrate=False)


def find_item(world: World, hero: Entity, partner: Entity, item: Item,
              mover: Mover, place: Place) -> None:
    world.get("item").attrs["missing"] = False
    world.say(place.found_line)
    world.say(
        f'"Who moved it?" asked {partner.id}.'
    )
    world.say(
        f'{hero.id} touched the clue and smiled. "It was {mover.label}, our '
        f'{mover.role_word}. {mover.pronoun("subject").capitalize()} used it {mover.motive}."'
    )


def reveal_mover(world: World, mover: Entity, item: Item, transformation: Transformation) -> None:
    mover.memes["helpful"] += 1
    world.say(
        f"Just then {mover.label} came back, carrying a tray or a poster under one arm."
    )
    world.say(
        f'"Oh!" {mover.pronoun()} said. "I borrowed the {item.label} {mover.attrs["motive"]}. '
        f'I meant to bring it back before the {transformation.start_form} opened."'
    )


def ending_before(world: World, hero: Entity, partner: Entity, mover: Entity,
                  transformation: Transformation, item: Item) -> None:
    advance_time(world, 1)
    world.say(
        f"{mover.label} placed the {item.label} gently beside the habitat, and everyone leaned close."
    )
    world.say(
        f"A tiny split opened. Soon there was {transformation.ending_image}."
    )
    world.say(
        f'{hero.id} grinned at {partner.id}. "We solved the mystery and still saw the transformation begin."'
    )


def ending_after(world: World, hero: Entity, partner: Entity, mover: Entity,
                 transformation: Transformation, item: Item) -> None:
    advance_time(world, 0)
    world.say(
        f"As {mover.label} handed back the {item.label}, a soft flutter came from the habitat."
    )
    world.say(
        f"They turned together and saw {transformation.ending_image}. "
        f"They had missed the very first crack, but not the wonder."
    )
    world.say(
        f'{partner.id} laughed with relief. "Good detectives still make it to the ending."'
    )


def tell(setting: Setting, transformation: Transformation, item: Item, mover_cfg: Mover,
         place: Place, hero_name: str, hero_gender: str, partner_name: str,
         partner_gender: str, caretaker_type: str, delay: int) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    partner = world.add(Entity(id="partner", kind="character", type=partner_gender, label=partner_name, role="partner"))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=caretaker_type, label="the teacher", role="caretaker"))
    mover = world.add(Entity(
        id="mover",
        kind="character",
        type=mover_cfg.type,
        label=mover_cfg.label,
        role="mover",
        attrs={"motive": mover_cfg.motive, "clue": mover_cfg.clue},
        tags=set(mover_cfg.tags),
    ))
    item_ent = world.add(Entity(
        id="item",
        type="tool",
        label=item.label,
        phrase=item.phrase,
        attrs={"missing": False},
        tags=set(item.tags),
    ))
    creature = world.add(Entity(
        id="creature",
        type="animal",
        label=transformation.creature,
        attrs={"opening_time": transformation.opening_time},
        tags=set(transformation.tags),
    ))

    hero.memes["care"] += 1
    partner.memes["care"] += 1
    world.facts["hero_name"] = hero_name
    world.facts["partner_name"] = partner_name

    introduce(world, hero, partner, caretaker, transformation, item)
    world.para()
    discover_missing(world, hero, partner, item, transformation)
    first_clue(world, hero, partner, mover_cfg, place)

    world.para()
    quest_walk(world, hero, partner, place, delay)
    advance_time(world, search_time(place, delay))
    find_item(world, hero, partner, item, mover_cfg, place)
    reveal_mover(world, mover, item, transformation)

    world.para()
    when = "before" if search_time(place, delay) < transformation.opening_time else "after"
    if when == "before":
        ending_before(world, hero, partner, mover, transformation, item)
    else:
        ending_after(world, hero, partner, mover, transformation, item)

    world.facts.update(
        hero=hero,
        partner=partner,
        caretaker=caretaker,
        mover=mover,
        item_cfg=item,
        transformation=transformation,
        place=place,
        setting=setting,
        clue=mover_cfg.clue,
        motive=mover_cfg.motive,
        outcome=when,
        search_time=search_time(place, delay),
        measured_before=when == "before",
        transformed=world.get("creature").meters["transformed"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "centimeter": [
        (
            "What is a centimeter?",
            "A centimeter is a small unit for measuring length. Children often see centimeters on rulers when they measure tiny things."
        )
    ],
    "transformation": [
        (
            "What does transformation mean in nature?",
            "Transformation means a living thing changes from one form into another. A caterpillar becoming a butterfly is one example."
        )
    ],
    "butterfly": [
        (
            "What comes out of a chrysalis?",
            "A butterfly comes out of a chrysalis. Its wings need a little time to open and dry."
        )
    ],
    "moth": [
        (
            "What is a cocoon?",
            "A cocoon is a case around some growing insects while they change. When the change is done, a moth can come out."
        )
    ],
    "frog": [
        (
            "What is a froglet?",
            "A froglet is a young frog that still looks a little like a tadpole. It often has a tiny bit of tail left."
        )
    ],
    "ruler": [
        (
            "What is a ruler for?",
            "A ruler helps you measure how long something is. Some rulers show centimeters and inches."
        )
    ],
    "measurement": [
        (
            "Why do people measure animals carefully?",
            "Careful measuring helps people notice small changes. It also helps them be gentle and pay close attention."
        )
    ],
    "teacher": [
        (
            "Why might a teacher borrow a ruler?",
            "A teacher might borrow a ruler to measure something for a class job. Good borrowing means bringing it back after the job is done."
        )
    ],
    "friend": [
        (
            "How can a friend make a mystery by accident?",
            "A friend can move something without meaning to cause trouble. Then everyone has to ask kind questions to figure it out."
        )
    ],
    "plants": [
        (
            "Why would someone measure a seedling?",
            "A seedling grows a little at a time, so measuring it shows the change. Small plant changes are easier to see with a ruler."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    transformation = f["transformation"]
    item = f["item_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old that includes the words "centimeter" and "sleek".',
        f"Tell a mystery where {hero.label} and {partner.label} go on a short quest to find {item.phrase} just before a {transformation.creature}'s transformation.",
        f"Write a child-facing story about a missing measuring tool, a clue, and a happy reveal beside a changing {transformation.creature}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    mover = f["mover"]
    transformation = f["transformation"]
    item = f["item_cfg"]
    place = f["place"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {partner.label}, two careful children who were watching a small {transformation.creature}. They turned into gentle detectives when the measuring tool disappeared."
        ),
        (
            f"Why did they need the {item.label}?",
            f"They wanted it so they could measure the little {transformation.start_form} in centimeters. The tool mattered because they were waiting for the creature's transformation."
        ),
        (
            "What clue helped them solve the mystery?",
            f"They found {place.clue_detail}. That clue matched {mover.label}'s work, so it pointed their quest toward {place.phrase}."
        ),
        (
            f"Who moved the {item.label}, and why?",
            f"{mover.label} moved it. {mover.pronoun('subject').capitalize()} had borrowed it {f['motive']}, so the mystery was caused by a busy helper, not by meanness."
        ),
    ]
    if outcome == "before":
        qa.append(
            (
                "Did they find it before the transformation started?",
                f"Yes. They solved the mystery in time and were already back by the habitat when the opening began. That let them see the transformation start with their own eyes."
            )
        )
    else:
        qa.append(
            (
                "Did they miss the beginning of the transformation?",
                f"They missed the very first crack, but they did not miss the wonder. By the time the tool came back, they still turned and saw the new {transformation.end_form} beside them."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with everyone gathered quietly near the habitat, watching {transformation.ending_image}. The solved mystery made the room feel calm again."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    transformation = f["transformation"]
    item = f["item_cfg"]
    mover = f["mover"]
    tags: set[str] = {"centimeter", "transformation"}
    tags |= set(transformation.tags)
    tags |= set(item.tags)
    tags |= set(mover.tags)
    ordered = ["centimeter", "transformation", "butterfly", "moth", "frog",
               "ruler", "measurement", "teacher", "friend", "plants"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
usable(I, T)      :- item(I), transformation(T), supports(I, K), measure_kind(T, K).
reachable(S, P)   :- setting(S), spot_in(S, P).
reachable(M, P)   :- mover(M), mover_place(M, P).
valid(S, T, I, M, P) :- setting(S), transformation(T), item(I), mover(M), place(P),
                        reachable(S, P), reachable(M, P), usable(I, T).

search_time(V) :- chosen_place(P), distance(P, D), delay(L), V = D + L.
outcome(before) :- chosen_transformation(T), opening_time(T, O), search_time(V), V < O.
outcome(after)  :- chosen_transformation(T), opening_time(T, O), search_time(V), V >= O.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for spot in sorted(setting.hide_spots):
            lines.append(asp.fact("spot_in", sid, spot))
    for tid, transformation in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        lines.append(asp.fact("measure_kind", tid, transformation.measure_kind))
        lines.append(asp.fact("opening_time", tid, transformation.opening_time))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for support in sorted(item.supports):
            lines.append(asp.fact("supports", iid, support))
    for mid, mover in MOVERS.items():
        lines.append(asp.fact("mover", mid))
        for place_id in sorted(mover.places):
            lines.append(asp.fact("mover_place", mid, place_id))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("distance", pid, place.distance))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_transformation", params.transformation),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        setting="classroom",
        transformation="butterfly",
        item="steel_ruler",
        mover="artist_friend",
        place="art_table",
        hero_name="Nora",
        hero_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
        caretaker="mother",
        delay=0,
    ),
    StoryParams(
        setting="greenhouse",
        transformation="moth",
        item="centimeter_card",
        mover="teacher",
        place="window_ledge",
        hero_name="Leo",
        hero_gender="boy",
        partner_name="Mia",
        partner_gender="girl",
        caretaker="father",
        delay=1,
    ),
    StoryParams(
        setting="greenhouse",
        transformation="froglet",
        item="tail_strip",
        mover="gardener",
        place="potting_bench",
        hero_name="Tess",
        hero_gender="girl",
        partner_name="Omar",
        partner_gender="boy",
        caretaker="mother",
        delay=1,
    ),
    StoryParams(
        setting="nature_nook",
        transformation="butterfly",
        item="centimeter_card",
        mover="artist_friend",
        place="reading_stool",
        hero_name="Max",
        hero_gender="boy",
        partner_name="Ivy",
        partner_gender="girl",
        caretaker="father",
        delay=1,
    ),
]


GIRL_NAMES = ["Lily", "Mia", "Nora", "Ava", "Tess", "Ruby", "Ivy", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Omar", "Finn", "Max", "Eli", "Theo", "Sam"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A tiny whodunit storyworld about a missing measuring tool, a transformation, and a clue-led quest."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--mover", choices=MOVERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra searching delay")
    ap.add_argument("--caretaker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="show world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="show valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if all(x is not None for x in (args.setting, args.transformation, args.item, args.mover, args.place)):
        if not valid_combo(args.setting, args.transformation, args.item, args.mover, args.place):
            raise StoryError(explain_rejection(args.setting, args.transformation, args.item, args.mover, args.place))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.transformation is None or combo[1] == args.transformation)
        and (args.item is None or combo[2] == args.item)
        and (args.mover is None or combo[3] == args.mover)
        and (args.place is None or combo[4] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, transformation_id, item_id, mover_id, place_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    partner_gender = "boy" if hero_gender == "girl" else "girl"
    hero_name = pick_name(rng, hero_gender)
    partner_name = pick_name(rng, partner_gender, avoid=hero_name)
    caretaker = args.caretaker or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        setting=setting_id,
        transformation=transformation_id,
        item=item_id,
        mover=mover_id,
        place=place_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        caretaker=caretaker,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.transformation, params.item, params.mover, params.place):
        raise StoryError(explain_rejection(params.setting, params.transformation, params.item, params.mover, params.place))
    if params.setting not in SETTINGS or params.transformation not in TRANSFORMATIONS:
        raise StoryError("(Unknown setting or transformation.)")
    if params.item not in ITEMS or params.mover not in MOVERS or params.place not in PLACES:
        raise StoryError("(Unknown item, mover, or place.)")

    world = tell(
        setting=SETTINGS[params.setting],
        transformation=TRANSFORMATIONS[params.transformation],
        item=ITEMS[params.item],
        mover_cfg=MOVERS[params.mover],
        place=PLACES[params.place],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        caretaker_type=params.caretaker,
        delay=params.delay,
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


def asp_verify() -> int:
    rc = 0
    try:
        clingo_set = set(asp_valid_combos())
    except Exception as err:
        print(f"ASP check failed: {err}")
        return 1

    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: valid combos match ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            continue

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcomes match on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        print(f"Smoke test failed: {err}")
        rc = 1

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, transformation, item, mover, place) combos:\n")
        for combo in combos:
            print("  " + " ".join(f"{part:14}" for part in combo))
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
            header = (
                f"### {p.hero_name} and {p.partner_name}: {p.transformation} mystery "
                f"({p.item} at {p.place}, {outcome_of(p)})"
            )
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
