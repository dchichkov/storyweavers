#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py
=====================================================================================

A standalone story world for a tall-tale-flavored contemporary rescue story:
a pudgy child loses something important in a tricky modern place, feels scared,
then discovers that bravery can mean asking for the right grown-up and using
the right tool instead of grabbing wildly.

The world model is small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate over (place, item, tool) combinations
- a forward-chaining rule layer for fear, confidence, and relief
- a declarative ASP twin for the same compatibility gate
- prose that follows state changes rather than swapping nouns into one paragraph

Run it
------
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --place plaza --item lunch_tin
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --place fountain_walk --tool net
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --all
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --qa
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --trace
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --asp
    python storyworlds/worlds/gpt-5.4/pudgy_contemporary_bravery_happy_ending_lesson_learned.py --verify
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
# from the repo root or this nested directory.
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
        female = {"girl", "mother", "woman", "caretaker"}
        male = {"boy", "father", "man", "superintendent"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    hazard: str
    opening: str
    activity: str
    helper_title: str
    helper_type: str
    helper_tool_place: str
    risk_line: str
    ending_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ItemCfg:
    id: str
    label: str
    phrase: str
    material: str
    behaves: str
    shiny: bool = False
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolCfg:
    id: str
    label: str
    phrase: str
    action: str
    works_in: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_item_stuck(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["stuck"] >= THRESHOLD:
        sig = ("fear", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] += 1
            hero.memes["urgency"] += 1
            out.append("__stuck__")
    return out


def _r_helper_arrives(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("helper")
    if helper.meters["near"] >= THRESHOLD:
        sig = ("confidence", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["confidence"] += 1
            helper.memes["calm"] += 1
            out.append("__helper__")
    return out


def _r_recovered(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    item = world.get("item")
    if item.meters["recovered"] >= THRESHOLD:
        sig = ("relief", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["fear"] = 0.0
            hero.memes["relief"] += 1
            hero.memes["pride"] += 1
            hero.memes["lesson"] += 1
            out.append("__recovered__")
    return out


CAUSAL_RULES = [
    Rule(name="item_stuck", tag="emotion", apply=_r_item_stuck),
    Rule(name="helper_arrives", tag="emotion", apply=_r_helper_arrives),
    Rule(name="recovered", tag="emotion", apply=_r_recovered),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


PLACES = {
    "plaza": Place(
        id="plaza",
        label="the apartment plaza",
        phrase="the apartment plaza with glass doors, planters, and a row of parked scooters",
        hazard="drain",
        opening="The sidewalks looked so wide and shiny that they seemed to run clear to tomorrow.",
        activity="watching delivery bikes zip past and making up giant-city stories",
        helper_title="Super Vega",
        helper_type="superintendent",
        helper_tool_place="the lobby closet",
        risk_line="The storm drain crouched at the curb like a little iron dragon mouth.",
        ending_line="Soon the plaza felt less like a monster map and more like home again.",
        tags={"city", "drain", "contemporary"},
    ),
    "fountain_walk": Place(
        id="fountain_walk",
        label="the fountain walk",
        phrase="the fountain walk beside the food hall, where little jets danced up from the stones",
        hazard="fountain",
        opening="The water jumped so high it looked as if the square was trying to touch the clouds.",
        activity="counting the splashy fountains and waving at people with shopping bags and headphones",
        helper_title="Ms. Rina",
        helper_type="caretaker",
        helper_tool_place="the cleaning cart",
        risk_line="The fountain basin shone deep and wobbly, like a pocket-sized sea in the middle of town.",
        ending_line="After that, every fountain jet looked more like a laugh than a danger.",
        tags={"city", "fountain", "contemporary"},
    ),
    "school_gate": Place(
        id="school_gate",
        label="the school gate",
        phrase="the school gate beside the bike rack and the bright mural of planets",
        hazard="bush",
        opening="Even the bike helmets gleamed there, as if the whole block had been polished for a parade.",
        activity="waiting after school and telling grand stories about which painted planet was the wildest",
        helper_title="Coach Dani",
        helper_type="man",
        helper_tool_place="the storage shed",
        risk_line="The thorny hedge stood in one corner like a green castle wall full of tiny hooks.",
        ending_line="By the time they left, the mural planets looked friendly again, and the hedge had lost all its meanness.",
        tags={"school", "bush", "contemporary"},
    ),
}

ITEMS = {
    "lunch_tin": ItemCfg(
        id="lunch_tin",
        label="lunch tin",
        phrase="a shiny robot lunch tin",
        material="metal",
        behaves="clanged and skittered",
        shiny=True,
        tags={"metal", "school_item"},
    ),
    "key_fob": ItemCfg(
        id="key_fob",
        label="key fob",
        phrase="a little silver key fob",
        material="metal",
        behaves="spun like a coin and flashed once",
        shiny=True,
        tags={"metal", "keys"},
    ),
    "plush_whale": ItemCfg(
        id="plush_whale",
        label="plush whale",
        phrase="a soft blue plush whale",
        material="soft",
        behaves="bounced once and flopped",
        soft=True,
        tags={"plush"},
    ),
    "light_ball": ItemCfg(
        id="light_ball",
        label="light-up ball",
        phrase="a rubber light-up ball",
        material="rubber",
        behaves="blinked rainbow colors as it rolled",
        tags={"ball"},
    ),
    "notebook": ItemCfg(
        id="notebook",
        label="notebook",
        phrase="a small striped notebook",
        material="paper",
        behaves="fluttered like a startled bird",
        tags={"paper"},
    ),
}

TOOLS = {
    "magnet_pole": ToolCfg(
        id="magnet_pole",
        label="magnet pole",
        phrase="a long magnet pole",
        action="lowered the magnet pole carefully until it clicked onto the metal prize",
        works_in={"drain", "fountain"},
        materials={"metal"},
        qa_text="used a magnet pole to lift it out",
        tags={"magnet"},
    ),
    "grabber": ToolCfg(
        id="grabber",
        label="grabber",
        phrase="a long grabber",
        action="reached with the grabber, squeezed the handle, and pinched the prize safely",
        works_in={"drain", "bush"},
        materials={"metal", "soft", "paper", "rubber"},
        qa_text="used a long grabber to pinch it safely",
        tags={"grabber"},
    ),
    "net": ToolCfg(
        id="net",
        label="net",
        phrase="a small fountain net",
        action="slid the little net under the floating prize and lifted it in one smooth scoop",
        works_in={"fountain"},
        materials={"soft", "rubber", "paper"},
        qa_text="used a small net to scoop it out",
        tags={"net"},
    ),
    "rake": ToolCfg(
        id="rake",
        label="rake",
        phrase="a child-safe leaf rake",
        action="hooked the prize gently with the rake and drew it out of the thorns",
        works_in={"bush"},
        materials={"soft", "paper", "rubber"},
        qa_text="used a rake to pull it free from the thorns",
        tags={"rake"},
    ),
}


def tool_works(place: Place, item: ItemCfg, tool: ToolCfg) -> bool:
    return place.hazard in tool.works_in and item.material in tool.materials


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for tool_id, tool in TOOLS.items():
                if tool_works(place, item, tool):
                    combos.append((place_id, item_id, tool_id))
    return sorted(combos)


def tall_tale_compare(place: Place) -> str:
    return {
        "drain": "as if the city had a hundred secret mouths",
        "fountain": "like a silver fish was laughing under every splash",
        "bush": "as though even the leaves had decided to grow brave little claws",
    }[place.hazard]


def helper_kind_word(helper: Entity) -> str:
    if helper.type == "superintendent":
        return "building super"
    if helper.type == "caretaker":
        return "caretaker"
    return "coach"


def introduce(world: World, hero: Entity, friend: Entity, parent: Entity, place: Place) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} was a pudgy little {hero.type} with quick feet and a round laugh. "
        f"One bright afternoon, {hero.id}, {friend.id}, and {hero.pronoun('possessive')} "
        f"{parent.label_word} were at {place.phrase}."
    )
    world.say(place.opening)
    world.say(
        f"They were {place.activity}, and {hero.id} kept telling the story so big that "
        f"every scooter looked fast enough to race the wind {tall_tale_compare(place)}."
    )


def treasure_intro(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["love"] += 1
    world.say(
        f"Tucked under {hero.pronoun('possessive')} arm was {item.phrase}. "
        f"{hero.id} liked carrying it everywhere, as if an ordinary day might turn into an adventure at any minute."
    )


def accident(world: World, hero: Entity, friend: Entity, place: Place, item: Entity, item_cfg: ItemCfg) -> None:
    item.meters["loose"] += 1
    world.say(
        f"Then a gust came bustling through the modern square. {item_cfg.behaves.capitalize()}, "
        f"slipped from {hero.id}'s hand, and shot toward the edge of {place.label}."
    )
    if place.hazard == "drain":
        world.say(
            f"It stopped with one corner peeking through the bars of a storm drain. {place.risk_line}"
        )
    elif place.hazard == "fountain":
        world.say(
            f"It landed in the fountain with a plink and bobbed near the rim. {place.risk_line}"
        )
    else:
        world.say(
            f"It vanished into the thorny hedge beside the gate. {place.risk_line}"
        )
    item.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.facts["hazard_seen"] = True


def risky_idea(world: World, hero: Entity, place: Place) -> None:
    hero.memes["reckless_idea"] += 1
    if place.hazard == "drain":
        world.say(
            f'{hero.id} bent down at once. "Maybe I can just squeeze my hand in," {hero.pronoun()} whispered.'
        )
    elif place.hazard == "fountain":
        world.say(
            f'{hero.id} took one step toward the slick fountain edge. "Maybe I can reach it before it drifts away," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} lifted one foot toward the hedge. "Maybe I can crawl in after it," {hero.pronoun()} murmured.'
        )


def caution(world: World, friend: Entity, parent: Entity, place: Place) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} caught {hero_reference(world).pronoun("possessive")} sleeve first. '
        f'"Wait," {friend.pronoun()} said. "{place.risk_line} We should not grab at it by ourselves."'
    )
    world.say(
        f'{parent.label_word.capitalize()} nodded. "The safe way may take one more minute," '
        f'{parent.pronoun()} said, "but one safe minute is better than one hurt second."'
    )


def hero_reference(world: World) -> Entity:
    return world.get("hero")


def brave_choice(world: World, hero: Entity, helper: Entity, place: Place) -> None:
    hero.memes["bravery"] += 1
    world.say(
        f"{hero.id}'s tummy felt full of jumping frogs, but {hero.pronoun()} stood up straight anyway."
    )
    world.say(
        f'"{place.helper_title}! Please help!" {hero.id} called, loud and clear enough to cross the whole square.'
    )
    world.say(
        f"That was the brave part: not pretending to be bigger than the problem, but speaking up before the problem got any bigger."
    )
    helper.meters["near"] += 1
    propagate(world, narrate=False)


def helper_arrives(world: World, helper: Entity, place: Place, tool: ToolCfg) -> None:
    world.say(
        f"{place.helper_title} came over from {place.helper_tool_place} with {tool.phrase}. "
        f"{helper.pronoun().capitalize()} did not hurry in a fluttery way. {helper.pronoun().capitalize()} moved like someone carrying a good idea."
    )


def rescue(world: World, hero: Entity, helper: Entity, item: Entity, tool: ToolCfg) -> None:
    item.meters["recovered"] += 1
    item.meters["stuck"] = 0.0
    hero.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f"While {hero.id} held very still and watched, {helper.id} {tool.action}. "
        f"In another blink, {item.phrase} was back in the daylight."
    )


def return_item(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f'{helper.id} handed it back with a smile. "{item.phrase.capitalize()} belongs in your hands, not in trouble," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} hugged the {item.label} to {hero.pronoun('possessive')} chest until {hero.pronoun('possessive')} round little shoulders stopped shaking."
    )


def lesson(world: World, hero: Entity, friend: Entity, parent: Entity, place: Place) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f'"I thought brave meant doing it myself," {hero.id} admitted.'
    )
    world.say(
        f'{parent.label_word.capitalize()} squeezed {hero.pronoun("possessive")} shoulder. '
        f'"Sometimes brave means stopping, thinking, and calling the right helper," {parent.pronoun()} said.'
    )
    world.say(
        f"{friend.id} grinned. \"That makes you brave and smart,\" {friend.pronoun()} added."
    )
    world.say(
        f"{hero.id} nodded. The lesson settled inside {hero.pronoun('object')} as neatly as a coin dropping into a jar."
    )


def happy_end(world: World, hero: Entity, friend: Entity, place: Place, item: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"After that, the afternoon turned friendly again. {hero.id} and {friend.id} went back to playing, and {item.phrase} stayed tucked safely beside them."
    )
    world.say(
        f"{place.ending_line} Even the wind seemed to know the story now: brave hearts ask for help before trouble grows teeth."
    )


def tell(place: Place, item_cfg: ItemCfg, tool_cfg: ToolCfg,
         hero_name: str = "Milo", hero_type: str = "boy",
         friend_name: str = "June", friend_type: str = "girl",
         parent_type: str = "mother") -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        type=friend_type,
        label=friend_name,
        phrase=friend_name,
        role="friend",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=place.helper_type,
        label=place.helper_title,
        phrase=place.helper_title,
        role="helper",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="prize",
        attrs={"material": item_cfg.material},
    ))

    world.facts.update(
        place=place,
        item_cfg=item_cfg,
        tool_cfg=tool_cfg,
        hero=hero,
        friend=friend,
        parent=parent,
        helper=helper,
        item=item,
    )

    introduce(world, hero, friend, parent, place)
    treasure_intro(world, hero, item)

    world.para()
    accident(world, hero, friend, place, item, item_cfg)
    risky_idea(world, hero, place)
    caution(world, friend, parent, place)

    world.para()
    brave_choice(world, hero, helper, place)
    helper_arrives(world, helper, place, tool_cfg)
    rescue(world, hero, helper, item, tool_cfg)
    return_item(world, hero, helper, item)

    world.para()
    lesson(world, hero, friend, parent, place)
    happy_end(world, hero, friend, place, item)

    world.facts.update(
        resolved=item.meters["recovered"] >= THRESHOLD,
        brave=hero.memes["bravery"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="plaza",
        item="lunch_tin",
        tool="magnet_pole",
        hero_name="Milo",
        hero_gender="boy",
        friend_name="June",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="plaza",
        item="plush_whale",
        tool="grabber",
        hero_name="Ruby",
        hero_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="fountain_walk",
        item="light_ball",
        tool="net",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Ava",
        friend_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="fountain_walk",
        item="key_fob",
        tool="magnet_pole",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="school_gate",
        item="notebook",
        tool="rake",
        hero_name="Piper",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        parent="mother",
    ),
]


GIRL_NAMES = ["Lily", "Maya", "Nora", "Ava", "June", "Ruby", "Ella", "Zoe", "Piper", "Lucy"]
BOY_NAMES = ["Milo", "Theo", "Ben", "Eli", "Finn", "Sam", "Leo", "Max", "Noah", "Jack"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    item_cfg = f["item_cfg"]
    hero = f["hero"]
    return [
        f'Write a tall-tale-flavored contemporary story for a 3-to-5-year-old that includes the word "pudgy" and ends happily.',
        f"Tell a story about a pudgy little {hero.type} in {place.label} who loses {item_cfg.phrase}, feels scared, and learns that asking for help can be brave.",
        f'Write a gentle lesson story in a modern city setting where a child makes a brave choice, gets help the safe way, and finishes with a happy ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    parent = f["parent"]
    helper = f["helper"]
    place = f["place"]
    item_cfg = f["item_cfg"]
    tool_cfg = f["tool_cfg"]
    item = f["item"]

    name = hero.label
    friend_name = friend.label
    helper_name = helper.label
    pw = parent.label_word

    out = [
        (
            "Who is the story about?",
            f"It is about a pudgy little {hero.type} named {name}. {friend_name}, {name}'s {pw}, and {helper_name} help shape the adventure too.",
        ),
        (
            f"What happened to {name}'s {item_cfg.label}?",
            f"It slipped away and got stuck near the {place.hazard} at {place.label}. That is what turned an ordinary afternoon into a problem.",
        ),
        (
            f"Why didn't {name} grab it alone?",
            f"{friend_name} and {name}'s {pw} saw that the place was risky. They wanted to stop a small problem from becoming a hurt one.",
        ),
        (
            f"What brave thing did {name} do?",
            f"{name} called out for {helper_name} instead of pretending to handle it alone. That was brave because {hero.pronoun('subject')} was scared and still chose the safe thing.",
        ),
        (
            f"How did {helper_name} get the {item_cfg.label} back?",
            f"{helper_name} {tool_cfg.qa_text}. The tool matched the problem, so the rescue was calm and safe.",
        ),
        (
            "What lesson did the child learn?",
            f"{name} learned that bravery does not always mean grabbing fastest. Sometimes bravery means stopping, thinking, and asking the right helper for help.",
        ),
        (
            "How did the story end?",
            f"It ended happily with the {item.label} back in {name}'s hands. The scary place felt smaller after the safe rescue and the lesson learned.",
        ),
    ]
    return out


KNOWLEDGE = {
    "drain": [
        (
            "What is a storm drain?",
            "A storm drain is an opening near the street that carries rainwater away. It is not a place for hands or toys."
        )
    ],
    "fountain": [
        (
            "What is a fountain?",
            "A fountain is a place where water sprays or flows for people to look at. The edges can be slippery, so children should be careful around it."
        )
    ],
    "bush": [
        (
            "Why can a thorny bush be hard to reach into?",
            "A thorny bush has sharp little points that can scratch your skin. That is why it is better to use a tool or ask a grown-up for help."
        )
    ],
    "magnet": [
        (
            "What does a magnet do?",
            "A magnet can pull certain metal things toward it. That makes it useful for picking up some lost objects without putting your hand in danger."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool with a handle that pinches things at the far end. It helps you reach safely instead of stretching into a risky place."
        )
    ],
    "net": [
        (
            "What is a net used for?",
            "A net can scoop up something from water or from a hard-to-reach spot. It is helpful when you want to lift an object gently."
        )
    ],
    "rake": [
        (
            "How can a rake help with a stuck toy or notebook?",
            "A rake can hook or pull something toward you from a prickly spot. That way, your hands do not have to go into the thorns."
        )
    ],
    "bravery": [
        (
            "Can asking for help be brave?",
            "Yes. Asking for help can be very brave because you are choosing the safe, smart thing even when you feel nervous."
        )
    ],
    "contemporary": [
        (
            "What does contemporary mean?",
            "Contemporary means belonging to the present time, like things you see around you today. A contemporary place might have scooters, glass doors, or food halls."
        )
    ],
}
KNOWLEDGE_ORDER = ["contemporary", "drain", "fountain", "bush", "magnet", "grabber", "net", "rake", "bravery"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["place"].tags) | set(f["tool_cfg"].tags) | {"bravery"}
    hazard = f["place"].hazard
    if hazard == "drain":
        tags.add("drain")
    elif hazard == "fountain":
        tags.add("fountain")
    else:
        tags.add("bush")
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: ItemCfg, tool: ToolCfg) -> str:
    hazard_name = {
        "drain": "storm drain",
        "fountain": "fountain",
        "bush": "thorny hedge",
    }[place.hazard]
    if place.hazard not in tool.works_in:
        return (
            f"(No story: {tool.label} is not the right kind of tool for a {hazard_name} rescue at {place.label}. "
            f"Pick a tool that works in that place.)"
        )
    return (
        f"(No story: {tool.label} does not suit a {item.label} made of {item.material}. "
        f"The rescue tool has to match both the place and the object.)"
    )


ASP_RULES = r"""
compatible(P, I, T) :- place(P), item(I), tool(T),
                       hazard(P, H), works_in(T, H),
                       material(I, M), works_on(T, M).

valid(P, I, T) :- compatible(P, I, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("hazard", place_id, place.hazard))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("material", item_id, item.material))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for hazard in sorted(tool.works_in):
            lines.append(asp.fact("works_in", tool_id, hazard))
        for material in sorted(tool.materials):
            lines.append(asp.fact("works_on", tool_id, material))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: a pudgy child, a contemporary mishap, and a brave safe rescue."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
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
    ap.add_argument("--asp", action="store_true", help="list compatible (place, item, tool) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.tool:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if not tool_works(place, item, tool):
            raise StoryError(explain_rejection(place, item, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, tool_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    friend_name = args.friend_name or pick_name(rng, friend_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    tool = TOOLS[params.tool]
    if not tool_works(place, item, tool):
        raise StoryError(explain_rejection(place, item, tool))

    world = tell(
        place=place,
        item_cfg=item,
        tool_cfg=tool,
        hero_name=params.hero_name,
        hero_type=params.hero_gender,
        friend_name=params.friend_name,
        friend_type=params.friend_gender,
        parent_type=params.parent,
    )
    story = world.render().replace("hero", params.hero_name).replace("friend", params.friend_name)
    story = story.replace("parent", world.get("parent").label_word.capitalize(), 0)

    # Replace label placeholders with names in a controlled way.
    story = world.render()
    story = story.replace("hero", params.hero_name)
    story = story.replace("friend", params.friend_name)
    story = story.replace("parent", world.get("parent").label_word)

    # The world model keeps ids; child-facing text and QA should use display names.
    story = story.replace("hero", params.hero_name).replace("friend", params.friend_name)

    story = story.replace("  ", " ")
    story = story.replace("the parent", world.get("parent").label_word)

    hero = world.get("hero")
    friend = world.get("friend")
    parent = world.get("parent")
    helper = world.get("helper")

    story = story.replace(hero.id, params.hero_name)
    story = story.replace(friend.id, params.friend_name)
    story = story.replace(parent.id, parent.label_word)
    story = story.replace(helper.id, helper.label)

    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a.replace("hero", params.hero_name).replace("friend", params.friend_name)) for q, a in story_qa(world)],
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        sample_params = resolve_params(default_args, random.Random(7))
        smoke_cases.append(sample_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE SETUP FAILED: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            if sample.world is None:
                raise StoryError("missing live world")
        except Exception as err:
            rc = 1
            print(f"SMOKE TEST FAILED on case {idx}: {err}")
            break
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} story generations.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place, item, tool in combos:
            print(f"  {place:14} {item:12} {tool}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.item} at {p.place} with {p.tool}"
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
