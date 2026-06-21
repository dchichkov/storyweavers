#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py
============================================================================

A standalone storyworld for a small slice-of-life quest: a child notices that a
friend's school word cards have blown away, then kindly helps gather them so the
friend can still finish a class project before the afternoon meeting.

This world is built from the seed words "smootch" and "deport". They appear as
literal vocabulary cards inside the story world, which keeps the story gentle
and child-facing while still grounding those words in simulated state. The core
shape is:

    setup -> windy mishap -> small neighborhood search quest -> kind repair ->
    finished goodbye board / calm ending image

Reasonableness gate
-------------------
Not every combination makes a sensible story. Cards only scatter when the chosen
container can actually fail in the chosen weather. A repair only works when it
would realistically keep the cards together afterward. The Python gate and the
inline ASP twin both enforce that.

Run it
------
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py --weather windy --container envelope
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py --container box
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py --all
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/smootch_deport_quest_kindness_slice_of_life.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    route: str
    end_place: str
    bench: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    breeze: int
    line: str
    sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ContainerCfg:
    id: str
    label: str
    phrase: str
    secure: int
    fragile: bool
    spill_verb: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RepairCfg:
    id: str
    label: str
    sense: int
    holds: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GoalCfg:
    id: str
    board: str
    audience: str
    closing: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    if friend.meters["missing_cards"] >= THRESHOLD:
        sig = ("worry", "friend")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["helping"] >= THRESHOLD and friend.memes["worry"] >= THRESHOLD:
        sig = ("kindness", "friend")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["comfort"] += 1
            hero.memes["kindness"] += 1
            out.append("__kindness__")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    friend = world.get("friend")
    board = world.get("board")
    if board.meters["ready"] >= THRESHOLD:
        sig = ("relief", "board_ready")
        if sig not in world.fired:
            world.fired.add(sig)
            friend.memes["relief"] += 1
            hero = world.get("hero")
            hero.memes["joy"] += 1
            out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="kindness", tag="emotion", apply=_r_kindness),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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
    "courtyard": Setting(
        id="courtyard",
        place="the sunny courtyard outside the apartment building",
        route="the brick path, the little bench, and the flower boxes",
        end_place="the front stoop",
        bench="the little bench by the mailboxes",
        tags={"neighborhood"},
    ),
    "library_walk": Setting(
        id="library_walk",
        place="the walk to the library",
        route="the sidewalk, the bus-stop bench, and the hedge by the corner",
        end_place="the library steps",
        bench="the bus-stop bench",
        tags={"library"},
    ),
    "market_lane": Setting(
        id="market_lane",
        place="the lane beside the small market",
        route="the chalky sidewalk, the milk-crate bench, and the row of planters",
        end_place="the market door",
        bench="the milk-crate bench",
        tags={"market"},
    ),
}

WEATHERS = {
    "breezy": Weather(
        id="breezy",
        breeze=1,
        line="A soft breeze kept lifting the edges of leaves and paper.",
        sound="The air made little shh-shh sounds along the path.",
        tags={"wind"},
    ),
    "windy": Weather(
        id="windy",
        breeze=2,
        line="The wind skipped between the buildings and tugged at anything light.",
        sound="Paper whispered and shoes scuffed faster to keep up.",
        tags={"wind"},
    ),
    "still": Weather(
        id="still",
        breeze=0,
        line="The air was calm, and even the hanging fern hardly moved.",
        sound="Everything felt steady and easy to hold.",
        tags={"calm"},
    ),
}

CONTAINERS = {
    "envelope": ContainerCfg(
        id="envelope",
        label="envelope",
        phrase="a thin paper envelope",
        secure=0,
        fragile=True,
        spill_verb="split at the side",
        tags={"paper"},
    ),
    "folder": ContainerCfg(
        id="folder",
        label="folder",
        phrase="a blue homework folder",
        secure=1,
        fragile=False,
        spill_verb="slipped open",
        tags={"school"},
    ),
    "box": ContainerCfg(
        id="box",
        label="box",
        phrase="a small lidded card box",
        secure=3,
        fragile=False,
        spill_verb="popped open",
        tags={"box"},
    ),
}

REPAIRS = {
    "rubber_band": RepairCfg(
        id="rubber_band",
        label="a rubber band",
        sense=3,
        holds=1,
        text="looped a rubber band around the stack so the cards hugged each other tightly",
        qa_text="used a rubber band to hold the cards together",
        tags={"repair"},
    ),
    "clip": RepairCfg(
        id="clip",
        label="a bright paper clip",
        sense=3,
        holds=1,
        text="slid a bright paper clip over the cards and tucked them into the folder",
        qa_text="used a paper clip to keep the cards together",
        tags={"repair"},
    ),
    "ribbon": RepairCfg(
        id="ribbon",
        label="a ribbon",
        sense=2,
        holds=1,
        text="tied a ribbon around the stack in a careful bow",
        qa_text="tied a ribbon around the stack",
        tags={"repair"},
    ),
    "pocket": RepairCfg(
        id="pocket",
        label="a pocket",
        sense=1,
        holds=0,
        text="stuffed the cards into a loose pocket",
        qa_text="stuffed the cards into a pocket",
        tags={"repair"},
    ),
}

GOALS = {
    "farewell_board": GoalCfg(
        id="farewell_board",
        board="a goodbye word board",
        audience="the afternoon class circle",
        closing="propped the finished board against the wall where everyone could see it",
        tags={"goodbye"},
    ),
    "window_board": GoalCfg(
        id="window_board",
        board="a window display of favorite words",
        audience="the people coming in from the street",
        closing="set the finished board in the window where the letters glowed in the light",
        tags={"display"},
    ),
    "club_board": GoalCfg(
        id="club_board",
        board="the reading-club board",
        audience="the little reading club",
        closing="leaned the finished board on the low table for the club to discover",
        tags={"club"},
    ),
}


WORD_POOL = [
    "smootch",
    "deport",
    "pocket",
    "lantern",
    "meadow",
    "button",
    "cobble",
    "feather",
    "murmur",
]


GIRL_NAMES = ["Lina", "Maya", "Nora", "Zoe", "Ava", "Ella", "Mina", "Lucy"]
BOY_NAMES = ["Ben", "Omar", "Leo", "Sam", "Noah", "Eli", "Finn", "Theo"]
TRAITS = ["gentle", "careful", "helpful", "cheerful", "patient", "thoughtful"]


def scatter_possible(weather: Weather, container: ContainerCfg) -> bool:
    return weather.breeze > container.secure


def sensible_repairs() -> list[RepairCfg]:
    return [repair for repair in REPAIRS.values() if repair.sense >= SENSE_MIN]


def repair_works(container: ContainerCfg, repair: RepairCfg) -> bool:
    return repair.holds + container.secure >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for weather_id, weather in WEATHERS.items():
            for container_id, container in CONTAINERS.items():
                if not scatter_possible(weather, container):
                    continue
                for goal_id in GOALS:
                    combos.append((setting_id, weather_id, container_id, goal_id))
    return combos


def search_spots(setting: Setting) -> list[str]:
    if setting.id == "courtyard":
        return ["under the bench", "beside the flower boxes", "against the step"]
    if setting.id == "library_walk":
        return ["by the bus-stop bench", "under the hedge", "near the library rail"]
    return ["under the milk-crate bench", "beside the planters", "against the market step"]


def predict_scatter(container: ContainerCfg, weather: Weather) -> int:
    return max(0, weather.breeze - container.secure + 1)


def _word_cards(world: World) -> list[Entity]:
    return [e for e in world.entities.values() if e.type == "card"]


def spill_cards(world: World, weather: Weather, container: ContainerCfg, setting: Setting) -> None:
    n_missing = predict_scatter(container, weather)
    spots = search_spots(setting)
    cards = _word_cards(world)
    world.facts["search_order"] = []
    for i, card in enumerate(cards):
        if i < n_missing:
            card.meters["lost"] = 1
            card.attrs["spot"] = spots[i % len(spots)]
            world.facts["search_order"].append(card.id)
        else:
            card.meters["kept"] = 1
    world.get("friend").meters["missing_cards"] = float(n_missing)
    propagate(world, narrate=False)


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting, weather: Weather, goal: GoalCfg) -> None:
    world.say(
        f"After lunch, {hero.id} and {friend.id} walked through {setting.place}. "
        f"{weather.line}"
    )
    world.say(
        f"{friend.id} was carrying {goal.board} for {goal.audience}, along with a stack of word cards."
    )
    world.say(weather.sound)


def show_words(world: World, friend: Entity, goal: GoalCfg) -> None:
    words = [card.label for card in _word_cards(world)]
    featured = ", ".join(f'"{w}"' for w in words[:4])
    friend.memes["pride"] += 1
    world.say(
        f'"I picked my favorite funny and tricky words," {friend.id} said, fanning the cards a little. '
        f'{featured} were right on top.'
    )
    world.say(
        f"{friend.id} wanted to tape the cards around {goal.board} before anybody else arrived."
    )


def accident(world: World, friend: Entity, container: ContainerCfg) -> None:
    friend.memes["worry"] += 0.5
    world.say(
        f"But then {container.phrase} {container.spill_verb}, and a few cards skittered away."
    )


def notice_and_offer(world: World, hero: Entity, friend: Entity, setting: Setting) -> None:
    hero.memes["helping"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{hero.id} saw {friend.id} stop short and stare at the path. "{friend.id}, I can help," '
        f'{hero.pronoun()} said at once.'
    )
    world.say(
        f"Together they looked over {setting.route} and made a tiny search plan."
    )


def search(world: World, hero: Entity, friend: Entity) -> None:
    found: list[str] = []
    for word in world.facts.get("search_order", []):
        card = world.get(word)
        if card.meters["lost"] < THRESHOLD:
            continue
        found.append(word)
        card.meters["found"] = 1
        card.meters["lost"] = 0
        friend.meters["missing_cards"] -= 1
        spot = card.attrs.get("spot", "by the path")
        if len(found) == 1:
            world.say(
                f"They hurried first to {spot}, where {hero.id} spotted the card for '{word}' fluttering like a white leaf."
            )
        else:
            world.say(
                f"Next they checked {spot}, and {friend.id} found '{word}' waiting there."
            )
    propagate(world, narrate=False)
    world.facts["found_words"] = found


def explain_words(world: World, friend: Entity) -> None:
    words = world.facts.get("found_words", [])
    if "smootch" in words and "deport" in words:
        world.say(
            f'"There they are!" {friend.id} said. "I liked "smootch" because it sounds silly, '
            f'and "deport" because it looks serious and different."'
        )
    elif "smootch" in words:
        world.say(
            f'"I was really hoping to keep "smootch"," {friend.id} said, smiling a little at the funny sound of it.'
        )
    elif "deport" in words:
        world.say(
            f'"I was worried about "deport"," {friend.id} admitted. "It was one of the hardest words on my board."'
        )


def repair_stack(world: World, helper: Entity, container: ContainerCfg, repair: RepairCfg) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Before the wind could play the same trick again, {helper.id} {repair.text}."
    )
    kept = repair_works(container, repair)
    world.facts["repair_success"] = kept
    if kept:
        world.say("This time the stack stayed neat and still in their hands.")
    else:
        world.say("The stack still felt loose, and they had to hold it carefully all the way.")
    if kept:
        world.get("board").meters["ready"] = 1
        propagate(world, narrate=False)


def finish_board(world: World, hero: Entity, friend: Entity, goal: GoalCfg) -> None:
    board = world.get("board")
    board.meters["ready"] = 1
    propagate(world, narrate=False)
    words = [card.label for card in _word_cards(world)]
    highlighted = ", ".join(f'"{w}"' for w in words[:2])
    world.say(
        f"At {world.facts['setting'].end_place}, they taped the cards around the board, including {highlighted}."
    )
    world.say(
        f"When the last corner lay flat, {friend.id}'s shoulders dropped in relief."
    )
    world.say(
        f"Then they {goal.closing}."
    )
    world.say(
        f"{hero.id} felt glad in the quiet, everyday way that comes from making someone else's afternoon easier."
    )


def tell(
    setting: Setting,
    weather: Weather,
    container: ContainerCfg,
    repair: RepairCfg,
    goal: GoalCfg,
    hero_name: str = "Mina",
    hero_gender: str = "girl",
    friend_name: str = "Omar",
    friend_gender: str = "boy",
    grownup_type: str = "grandmother",
    trait: str = "helpful",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero", traits=[trait]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend", traits=["busy"]))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up", phrase="the grown-up", role="grownup"))
    board = world.add(Entity(id="board", kind="thing", type="board", label="board", phrase=goal.board))
    container_ent = world.add(Entity(id="container", kind="thing", type="container", label=container.label, phrase=container.phrase))
    words = random.sample(WORD_POOL[2:], 2)
    picked = ["smootch", "deport"] + words
    for word in picked:
        world.add(Entity(id=word, kind="thing", type="card", label=word, phrase=f"the card for {word!r}"))
    world.facts.update(
        setting=setting,
        weather=weather,
        container_cfg=container,
        repair_cfg=repair,
        goal_cfg=goal,
        hero=hero,
        friend=friend,
        grownup=grownup,
        board=board,
    )

    introduce(world, hero, friend, setting, weather, goal)
    show_words(world, friend, goal)

    world.para()
    accident(world, friend, container)
    spill_cards(world, weather, container, setting)
    notice_and_offer(world, hero, friend, setting)

    world.para()
    search(world, hero, friend)
    explain_words(world, friend)

    world.para()
    repair_stack(world, hero, container, repair)
    finish_board(world, hero, friend, goal)

    world.facts.update(
        missing_count=int(predict_scatter(container, weather)),
        found_all=all(card.meters["lost"] < THRESHOLD for card in _word_cards(world)),
        featured_words=[card.label for card in _word_cards(world)],
    )
    return world


@dataclass
class StoryParams:
    setting: str
    weather: str
    container: str
    repair: str
    goal: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="courtyard",
        weather="windy",
        container="envelope",
        repair="rubber_band",
        goal="farewell_board",
        hero_name="Mina",
        hero_gender="girl",
        friend_name="Omar",
        friend_gender="boy",
        grownup="grandmother",
        trait="helpful",
    ),
    StoryParams(
        setting="library_walk",
        weather="breezy",
        container="folder",
        repair="clip",
        goal="club_board",
        hero_name="Ben",
        hero_gender="boy",
        friend_name="Lucy",
        friend_gender="girl",
        grownup="father",
        trait="careful",
    ),
    StoryParams(
        setting="market_lane",
        weather="windy",
        container="envelope",
        repair="ribbon",
        goal="window_board",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Leo",
        friend_gender="boy",
        grownup="mother",
        trait="gentle",
    ),
]


KNOWLEDGE = {
    "wind": [
        (
            "Why can wind blow papers away?",
            "Paper is light, so moving air can push it along the ground or lift its corners. That is why loose papers need clips, boxes, or careful hands."
        )
    ],
    "repair": [
        (
            "Why does a rubber band or clip help keep cards together?",
            "It squeezes or holds the stack so the cards act like one thicker bundle instead of many loose pieces. That makes them harder to scatter."
        )
    ],
    "goodbye": [
        (
            "Why do people make goodbye boards or cards?",
            "People make them to show care, share memories, and help someone feel remembered. A kind display can make parting feel warmer."
        )
    ],
    "library": [
        (
            "What is a library for?",
            "A library is a place where people borrow books, read quietly, and learn new things together."
        )
    ],
    "market": [
        (
            "What is a market?",
            "A market is a place where people buy food and small household things. It is often busy and full of little sights and sounds."
        )
    ],
    "paper": [
        (
            "Why does paper tear more easily than a box?",
            "Paper is thin and bends and rips quickly, especially at the edge. A box has stiffer sides, so it protects what is inside better."
        )
    ],
}
KNOWLEDGE_ORDER = ["wind", "repair", "goodbye", "library", "market", "paper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    goal = f["goal_cfg"]
    setting = f["setting"]
    return [
        'Write a gentle slice-of-life story for a 3-to-5-year-old that includes the words "smootch" and "deport" as part of a small neighborhood quest.',
        f"Tell a kindness story where {hero.label} helps {friend.label} recover lost word cards before they can finish {goal.board}.",
        f"Write a simple everyday story set in {setting.place} where a windy problem turns into a caring little quest."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    setting = f["setting"]
    container = f["container_cfg"]
    repair = f["repair_cfg"]
    goal = f["goal_cfg"]
    found_words = f.get("found_words", [])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label} walking together through {setting.place}. The story follows how {hero.label} notices a problem and chooses to help."
        ),
        (
            f"What problem started the quest?",
            f"{container.phrase.capitalize()} {container.spill_verb}, and some of {friend.label}'s word cards blew away. That mattered because {friend.label} needed them for {goal.board}."
        ),
        (
            f"Why did {hero.label} help {friend.label}?",
            f"{hero.label} saw that {friend.label} was worried and offered help right away. The kindness changed the moment from a lonely mistake into something they could solve together."
        ),
    ]
    if found_words:
        listed = ", ".join(f'"{w}"' for w in found_words)
        qa.append(
            (
                "Which cards did they find?",
                f"They found {listed}. The search mattered because those missing cards were part of the board they wanted to finish before the afternoon gathering."
            )
        )
    qa.append(
        (
            f"How did they keep the cards from blowing away again?",
            f"{hero.label} {repair.qa_text}. That made the stack safer to carry, so they could finish the board without losing the cards a second time."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They taped the cards onto the board and left it ready for {goal.audience}. The ending shows the change clearly: what began as scattered paper ended as a calm, finished display."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["weather"].tags) | set(world.facts["repair_cfg"].tags) | set(world.facts["goal_cfg"].tags) | set(world.facts["container_cfg"].tags) | set(world.facts["setting"].tags)
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
    for ent in world.entities.values():
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(weather: Weather, container: ContainerCfg) -> str:
    return (
        f"(No story: {container.phrase} is secure enough for {weather.id} weather here, "
        f"so no cards scatter and there is no quest to solve. Pick a less secure container or stronger wind.)"
    )


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it scores too low on common sense "
        f"(sense={repair.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
scatter(Weather, Container) :- weather(Weather), container(Container),
                               breeze(Weather, B), secure(Container, S), B > S.

sensible_repair(R) :- repair(R), sense(R, S), sense_min(M), S >= M.
repair_works(C, R) :- container(C), repair(R), secure(C, S), holds(R, H), S + H >= 2.

valid(Setting, Weather, Container, Goal) :- setting(Setting), goal(Goal),
                                            scatter(Weather, Container).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for weather_id, weather in WEATHERS.items():
        lines.append(asp.fact("weather", weather_id))
        lines.append(asp.fact("breeze", weather_id, weather.breeze))
    for container_id, container in CONTAINERS.items():
        lines.append(asp.fact("container", container_id))
        lines.append(asp.fact("secure", container_id, container.secure))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("sense", repair_id, repair.sense))
        lines.append(asp.fact("holds", repair_id, repair.holds))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_repairs() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_repair/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible_repair"))


def asp_repair_works(container_id: str, repair_id: str) -> bool:
    import asp
    extra = "\n".join([asp.fact("chosen_container", container_id), asp.fact("chosen_repair", repair_id),
                       "ok :- chosen_container(C), chosen_repair(R), repair_works(C, R)."])
    model = asp.one_model(asp_program(extra, "#show ok/0."))
    return bool(asp.atoms(model, "ok"))


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

    c_repairs = set(asp_sensible_repairs())
    p_repairs = {r.id for r in sensible_repairs()}
    if c_repairs == p_repairs:
        print(f"OK: sensible repairs match ({sorted(c_repairs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(c_repairs)} python={sorted(p_repairs)}")

    for container_id in CONTAINERS:
        for repair_id in REPAIRS:
            if asp_repair_works(container_id, repair_id) != repair_works(CONTAINERS[container_id], REPAIRS[repair_id]):
                rc = 1
                print(f"MISMATCH in repair_works for {container_id} + {repair_id}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        if sample.world is None:
            raise StoryError("Missing world during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a windy neighborhood quest of kindness with lost word cards."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.weather and args.container:
        if not scatter_possible(WEATHERS[args.weather], CONTAINERS[args.container]):
            raise StoryError(explain_rejection(WEATHERS[args.weather], CONTAINERS[args.container]))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.weather is None or combo[1] == args.weather)
        and (args.container is None or combo[2] == args.container)
        and (args.goal is None or combo[3] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, weather_id, container_id, goal_id = rng.choice(sorted(combos))
    repair_id = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        weather=weather_id,
        container=container_id,
        repair=repair_id,
        goal=goal_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        grownup=grownup,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        weather = WEATHERS[params.weather]
        container = CONTAINERS[params.container]
        repair = REPAIRS[params.repair]
        goal = GOALS[params.goal]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not scatter_possible(weather, container):
        raise StoryError(explain_rejection(weather, container))
    if repair.sense < SENSE_MIN:
        raise StoryError(explain_repair(params.repair))
    if not repair_works(container, repair):
        raise StoryError(
            f"(No story: {repair.label} would not keep cards safe enough after the spill. Pick a sturdier repair.)"
        )

    world = tell(
        setting=setting,
        weather=weather,
        container=container,
        repair=repair,
        goal=goal,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        grownup_type=params.grownup,
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
        print(asp_program("", "#show valid/4.\n#show sensible_repair/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible_repairs())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, weather, container, goal) combos:\n")
        for setting_id, weather_id, container_id, goal_id in combos:
            print(f"  {setting_id:12} {weather_id:7} {container_id:9} {goal_id}")
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
            header = (
                f"### {p.hero_name} helps {p.friend_name}: {p.container} in {p.weather} "
                f"at {p.setting} ({p.goal})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
