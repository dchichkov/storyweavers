#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py
============================================================================

A small storyworld about a child who finds something meant for a home to the
north, struggles to carry it there, and learns that honesty grows easier when
you ask for help the right way.

The world stays close to slice-of-life: sidewalks, porches, neighbors, weather,
and one ordinary choice. The moral value is honesty and helpfulness; the happy
ending comes from a sensible fix; the twist is that the person at the north
house is kinder and more connected to the child than first expected.

Run it
------
python storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py
python storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py --route north_hill --item soup_jar --method boots_tray
python storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py --route north_lane --item library_book --method crate_scarf
python storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py --all --qa
python storyworlds/worlds/gpt-5.4/struggle_north_moral_value_happy_ending_twist.py --verify
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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Route:
    id: str
    destination: str
    opening: str
    feel: str
    challenge_text: str
    requires: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class FoundItem:
    id: str
    label: str
    phrase: str
    drop_text: str
    carry_text: str
    needs: set[str] = field(default_factory=set)
    owner_name: str = ""
    owner_role: str = ""
    owner_type: str = "woman"
    owner_phrase: str = ""
    twist_text: str = ""
    gift_text: str = ""
    knowledge_tags: set[str] = field(default_factory=set)

    @property
    def owner_label(self) -> str:
        return self.owner_name


@dataclass
class Method:
    id: str
    phrase: str
    offer_text: str
    travel_text: str
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[str] = []
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
        clone.history = list(self.history)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def uncovered_requirements(world: World) -> set[str]:
    route = world.facts["route_cfg"]
    item = world.facts["item_cfg"]
    method_id = world.facts.get("method_id", "")
    covers = set()
    if method_id:
        covers = set(METHODS[method_id].covers)
    needed = set(route.requires) | set(item.needs)
    return needed - covers


def _r_struggle(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters["walking_north"] < THRESHOLD:
        return []
    missing = uncovered_requirements(world)
    if not missing:
        return []
    sig = ("struggle", tuple(sorted(missing)))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["strain"] += float(len(missing))
    hero.memes["worry"] += 1
    item.meters["risk"] += float(len(missing))
    world.history.append("struggle")
    return ["__struggle__"]


def _r_ready(world: World) -> list[str]:
    hero = world.get("hero")
    item = world.get("item")
    if hero.meters["walking_north"] < THRESHOLD:
        return []
    missing = uncovered_requirements(world)
    if missing:
        return []
    sig = ("ready", world.facts.get("method_id", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confidence"] += 1
    item.meters["safe"] += 1
    world.history.append("ready")
    return []


def _r_delivered(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["delivered"] < THRESHOLD:
        return []
    sig = ("delivered",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    hero.memes["pride"] += 1
    world.get("owner").memes["gratitude"] += 1
    world.history.append("delivered")
    return []


CAUSAL_RULES = [
    Rule(name="struggle", tag="physical", apply=_r_struggle),
    Rule(name="ready", tag="physical", apply=_r_ready),
    Rule(name="delivered", tag="social", apply=_r_delivered),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(route: Route, item: FoundItem, method: Method) -> bool:
    needed = set(route.requires) | set(item.needs)
    return needed.issubset(method.covers)


def predict_without_method(route: Route, item: FoundItem) -> set[str]:
    return set(route.requires) | set(item.needs)


def start_story(world: World, hero: Entity, parent: Entity, item: Entity, route: Route, cfg: FoundItem) -> None:
    hero.memes["honesty"] += 1
    world.say(
        f"{hero.id} was walking home with {hero.pronoun('possessive')} {parent.label_word} when {hero.pronoun()} spotted {cfg.drop_text}."
    )
    world.say(
        f"There was a paper tag tucked against it with an address for {route.destination}. "
        f"{hero.id} read the word north, looked up the street, and knew it belonged to somebody else."
    )
    world.say(
        f"{hero.pronoun().capitalize()} picked up {cfg.phrase} carefully. For a moment, returning it looked simple."
    )
    world.facts["moral_choice"] = "return"


def first_attempt(world: World, hero: Entity, route: Route, item_cfg: FoundItem) -> None:
    hero.meters["walking_north"] += 1
    propagate(world, narrate=False)
    miss = sorted(uncovered_requirements(world))
    world.facts["missing_before_help"] = miss
    world.say(
        f"But {route.opening}. {route.feel} {hero.id} started north with {item_cfg.carry_text}, and the walk turned into a struggle."
    )
    world.say(route.challenge_text)
    if "wet" in miss or "dry" in miss:
        world.say(f"{hero.pronoun().capitalize()} tucked {item_cfg.label} close, worried it might get damp.")
    if "grip" in miss or "steady" in miss:
        world.say(f"{hero.pronoun().capitalize()} slowed down so nothing would slip or slosh.")
    if "gust" in miss or "shelter" in miss:
        world.say(f"Each gust made {hero.pronoun('object')} angle {hero.pronoun('possessive')} shoulders around it like a little wall.")


def adult_offer(world: World, hero: Entity, parent: Entity, method: Method) -> None:
    hero.memes["trust"] += 1
    parent.memes["care"] += 1
    world.say(
        f'{parent.label_word.capitalize()} watched for one more step, then said, "{method.offer_text}"'
    )
    world.say(
        f"{hero.id} nodded. Returning the thing was still the right idea, but doing it alone was not the smartest way."
    )
    world.facts["asked_help"] = True


def equip_method(world: World, hero: Entity, method_id: str) -> None:
    world.facts["method_id"] = method_id
    helper = METHODS[method_id]
    tool = world.add(
        Entity(
            id="method",
            type="tool",
            label=helper.phrase,
            phrase=helper.phrase,
            role="helper",
            tags=set(helper.tags),
        )
    )
    tool.meters["ready"] += 1
    hero.memes["hope"] += 1
    world.history.append("equipped")
    propagate(world, narrate=False)


def second_attempt(world: World, hero: Entity, route: Route, method: Method) -> None:
    world.say(
        f"Soon they started again. {method.travel_text} this time, {route.destination} did not seem nearly so far away."
    )
    hero.meters["walking_north"] += 1
    propagate(world, narrate=False)


def deliver(world: World, hero: Entity, owner: Entity, item_cfg: FoundItem, route: Route) -> None:
    hero.meters["delivered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {route.destination}. {hero.id} held out {item_cfg.phrase} and said, "
        f'"I found this on the way and wanted to bring it back."'
    )
    world.say(
        f"The door opened, and there stood {owner.label}."
    )
    world.say(item_cfg.twist_text)
    world.say(
        f"{owner.label} smiled and {item_cfg.gift_text}"
    )
    world.say(
        f"On the walk home, the north wind no longer felt bossy at all. {hero.id} had learned that an honest heart and a little help could carry good things all the way to the right door."
    )
    world.facts["twist_revealed"] = True


ROUTES = {
    "north_lane": Route(
        id="north_lane",
        destination="the yellow house on North Lane",
        opening="a fine drizzle began to whisper over the sidewalk",
        feel="The stones looked dark and shiny.",
        challenge_text="Small drops tapped at the air and the ground, so every paper edge felt one mistake away from trouble.",
        requires={"wet", "dry"},
        tags={"rain", "north"},
    ),
    "north_hill": Route(
        id="north_hill",
        destination="the brick house at the top of North Hill",
        opening="the hill ahead still held a thin skin of ice in the shady places",
        feel="The path climbed higher than it had looked from below.",
        challenge_text="Each careful step asked for balance, and the cold path wanted slippery feet.",
        requires={"grip"},
        tags={"ice", "north"},
    ),
    "north_steps": Route(
        id="north_steps",
        destination="the upstairs flat above the bakery on North Street",
        opening="the afternoon wind came hurrying between the buildings",
        feel="It tugged at sleeves and nipped at corners.",
        challenge_text="The gusts kept reaching for anything light or leafy, as if they wanted to carry it away first.",
        requires={"gust"},
        tags={"wind", "north"},
    ),
}

ITEMS = {
    "library_book": FoundItem(
        id="library_book",
        label="library book",
        phrase="the library book",
        drop_text="a library book resting on a low wall",
        carry_text="both hands under the book",
        needs={"dry"},
        owner_name="Ms. Vale",
        owner_role="librarian",
        owner_type="woman",
        owner_phrase="the librarian from the little library room at school",
        twist_text="It was not a stern stranger at all. It was Ms. Vale, the librarian from school, still wearing her soft green cardigan. She blinked in surprise and laughed because she had been worrying about that very book.",
        gift_text="slipped a bright bookmark shaped like a fox into the front cover for him to keep",
        knowledge_tags={"book", "honesty"},
    ),
    "soup_jar": FoundItem(
        id="soup_jar",
        label="soup jar",
        phrase="the warm soup jar",
        drop_text="a glass jar of soup in a cloth bag beside a bench",
        carry_text="careful arms around the warm jar",
        needs={"steady"},
        owner_name="Mr. Han",
        owner_role="baker",
        owner_type="man",
        owner_phrase="the baker who waved from the corner shop every morning",
        twist_text="The person at the door turned out to be Mr. Han from the bakery. He had left in a hurry to help his sister and had not even noticed the bag was gone. His worried face softened the instant he saw the jar safe in Leo's hands.",
        gift_text="pressed two tiny sesame buns into his hand, still warm from the oven",
        knowledge_tags={"soup", "honesty"},
    ),
    "seedling": FoundItem(
        id="seedling",
        label="seedling tray",
        phrase="the little seedling tray",
        drop_text="a little seedling tray tucked near the fence",
        carry_text="the tray flat in front of her",
        needs={"shelter"},
        owner_name="Mrs. Rina",
        owner_role="gardener",
        owner_type="woman",
        owner_phrase="the gardener who kept pots along the front steps",
        twist_text="The upstairs door opened, and there was Mrs. Rina, who always let children smell the mint by her steps. She clapped one hand to her cheek because she had thought the baby plants were lost for good.",
        gift_text="tore open a tiny packet of sunflower seeds and gave it to her with a wink",
        knowledge_tags={"plant", "honesty"},
    ),
}

METHODS = {
    "raincoat_backpack": Method(
        id="raincoat_backpack",
        phrase="a raincoat and a zipped backpack",
        offer_text="Let's put this inside the zipped backpack and button your raincoat before we go north again.",
        travel_text="With the book dry inside the backpack",
        covers={"wet", "dry"},
        tags={"raincoat", "backpack"},
    ),
    "boots_tray": Method(
        id="boots_tray",
        phrase="grippy boots and a tray with a folded towel",
        offer_text="Let's give your feet more grip and set the jar on a tray with a folded towel so it stays steady.",
        travel_text="With grippy boots underfoot and the tray steady between them",
        covers={"grip", "steady"},
        tags={"boots", "tray"},
    ),
    "crate_scarf": Method(
        id="crate_scarf",
        phrase="a lidded crate wrapped with a scarf",
        offer_text="Let's tuck the plants into this little crate and wrap the scarf around it so the wind cannot bother them.",
        travel_text="With the seedlings tucked inside the crate",
        covers={"gust", "shelter"},
        tags={"crate", "scarf"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Noah", "Eli", "Theo", "Jack", "Owen"]
TRAITS = ["kind", "careful", "thoughtful", "patient", "bright", "gentle"]


@dataclass
class StoryParams:
    route: str
    item: str
    method: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        route="north_lane",
        item="library_book",
        method="raincoat_backpack",
        name="Leo",
        gender="boy",
        parent="mother",
        trait="thoughtful",
    ),
    StoryParams(
        route="north_hill",
        item="soup_jar",
        method="boots_tray",
        name="Mia",
        gender="girl",
        parent="father",
        trait="kind",
    ),
    StoryParams(
        route="north_steps",
        item="seedling",
        method="crate_scarf",
        name="Nora",
        gender="girl",
        parent="mother",
        trait="careful",
    ),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for route_id, route in ROUTES.items():
        for item_id, item in ITEMS.items():
            for method_id, method in METHODS.items():
                if valid_combo(route, item, method):
                    out.append((route_id, item_id, method_id))
    return sorted(out)


def explain_rejection(route: Route, item: FoundItem, method: Method) -> str:
    needed = sorted((set(route.requires) | set(item.needs)) - set(method.covers))
    return (
        f"(No story: {method.phrase} does not honestly solve this trip. "
        f"The route and item still need {needed}, so the north walk would stay unreasonable.)"
    )


def ending_of(params: StoryParams) -> str:
    return ITEMS[params.item].owner_role


KNOWLEDGE = {
    "book": [
        (
            "Why should you keep a library book dry?",
            "Books are made of paper, and paper wrinkles and tears when it gets wet. Keeping a library book dry helps the next reader enjoy it too.",
        )
    ],
    "soup": [
        (
            "Why do you carry a jar of soup carefully?",
            "A jar can tip or slip if you hurry. Carrying it steadily keeps the soup inside and keeps the glass from dropping.",
        )
    ],
    "plant": [
        (
            "Why can wind bother little plants?",
            "Little plants bend easily because their stems are soft. A hard gust can shake the soil loose or snap tender leaves.",
        )
    ],
    "honesty": [
        (
            "What does honesty mean?",
            "Honesty means telling the truth and doing the right thing even when nobody is making you do it. Returning something that belongs to another person is one honest choice.",
        )
    ],
    "raincoat": [
        (
            "What does a raincoat do?",
            "A raincoat helps keep rain off your clothes. It makes a wet walk easier and more comfortable.",
        )
    ],
    "boots": [
        (
            "Why do boots help on a slippery path?",
            "Boots with good grip help your feet hold the ground better. That makes slips less likely on wet or icy places.",
        )
    ],
    "north": [
        (
            "What does north mean?",
            "North is one direction, like south, east, and west. People use directions to explain where a place is.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    route = f["route_cfg"]
    item = f["item_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the words "struggle" and "north".',
        f"Tell a gentle story where a {hero.type} named {hero.id} finds {item.phrase} meant for {route.destination}, struggles on the way north, and learns to ask for help without giving up on doing the right thing.",
        f"Write a moral story with a happy ending and a small twist: the person at the north address turns out to be someone kind and familiar.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    route = f["route_cfg"]
    item = f["item_cfg"]
    method = f["method_cfg"]
    owner = f["owner"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.traits[0]} little {hero.type}, and {hero.pronoun('possessive')} {parent.label_word} on an ordinary walk home.",
        ),
        (
            f"What did {hero.id} find?",
            f"{hero.id} found {item.phrase} with an address for {route.destination}. That is why {hero.pronoun()} decided it should be returned instead of left behind.",
        ),
        (
            f"Why was the trip north a struggle at first?",
            f"The route itself was hard, and {hero.id} did not yet have the right way to carry the item. The walk north became a struggle because {route.challenge_text[0].lower() + route.challenge_text[1:]}",
        ),
        (
            f"Why did {hero.id} keep going instead of giving up?",
            f"{hero.pronoun().capitalize()} wanted to do the honest thing and bring the item back to its owner. That good choice mattered more than taking the easy way home.",
        ),
        (
            f"How did {hero.id}'s {parent.label_word} help?",
            f"{parent.label_word.capitalize()} noticed the problem and suggested {method.phrase}. That solved the real risk on the trip, so helping did not replace honesty; it helped honesty succeed.",
        ),
        (
            "What was the twist at the door?",
            f"The owner was not an upset stranger after all. It was {owner.label}, {item.owner_phrase}, which made the ending feel warm instead of scary.",
        ),
        (
            "How did the story end?",
            f"It ended happily: the item got home safely, the owner was grateful, and {hero.id} went home proud. The ending image shows that doing the right thing became lighter once it was shared.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"north", "honesty"} | set(world.facts["item_cfg"].knowledge_tags) | set(world.facts["method_cfg"].tags)
    order = ["north", "honesty", "book", "soup", "plant", "raincoat", "boots"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def tell(
    route: Route,
    item_cfg: FoundItem,
    method_cfg: Method,
    name: str,
    gender: str,
    parent_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="hero",
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    item = world.add(
        Entity(
            id="item",
            type="item",
            label=item_cfg.label,
            phrase=item_cfg.phrase,
            role="found_item",
        )
    )
    owner = world.add(
        Entity(
            id="owner",
            kind="character",
            type=item_cfg.owner_type,
            label=item_cfg.owner_label,
            phrase=item_cfg.owner_phrase,
            role="owner",
        )
    )
    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        owner=owner,
        route_cfg=route,
        item_cfg=item_cfg,
        method_cfg=method_cfg,
        method_id="",
    )

    start_story(world, hero, parent, item, route, item_cfg)
    world.para()
    first_attempt(world, hero, route, item_cfg)
    world.para()
    adult_offer(world, hero, parent, method_cfg)
    equip_method(world, hero, method_cfg.id)
    second_attempt(world, hero, route, method_cfg)
    world.para()
    deliver(world, hero, owner, item_cfg, route)

    return world


ASP_RULES = r"""
needs(Route, Need) :- route_req(Route, Need).
needs(Item, Need)  :- item_need(Item, Need).

covers_all(Route, Item, Method) :-
    method(Method),
    not missing_need(Route, Item, Method).

missing_need(Route, Item, Method) :-
    route(Route), item(Item), method(Method),
    route_req(Route, Need), not method_cover(Method, Need).

missing_need(Route, Item, Method) :-
    route(Route), item(Item), method(Method),
    item_need(Item, Need), not method_cover(Method, Need).

valid(Route, Item, Method) :-
    route(Route), item(Item), method(Method),
    covers_all(Route, Item, Method).

ending(Role) :- chosen_item(Item), item_owner_role(Item, Role).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        for need in sorted(route.requires):
            lines.append(asp.fact("route_req", route_id, need))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for need in sorted(item.needs):
            lines.append(asp.fact("item_need", item_id, need))
        lines.append(asp.fact("item_owner_role", item_id, item.owner_role))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for cover in sorted(method.covers):
            lines.append(asp.fact("method_cover", method_id, cover))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_ending(item_id: str) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            extra=asp.fact("chosen_item", item_id),
            show="#show ending/1.",
        )
    )
    atoms = asp.atoms(model, "ending")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: an honest child struggles north to return a lost item, then gets help the sensible way."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible route/item/method triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.item and args.method:
        route = ROUTES[args.route]
        item = ITEMS[args.item]
        method = METHODS[args.method]
        if not valid_combo(route, item, method):
            raise StoryError(explain_rejection(route, item, method))

    combos = [
        c
        for c in valid_combos()
        if (args.route is None or c[0] == args.route)
        and (args.item is None or c[1] == args.item)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, item_id, method_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        route=route_id,
        item=item_id,
        method=method_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    route = ROUTES[params.route]
    item = ITEMS[params.item]
    method = METHODS[params.method]
    if not valid_combo(route, item, method):
        raise StoryError(explain_rejection(route, item, method))

    world = tell(
        route=route,
        item_cfg=item,
        method_cfg=method,
        name=params.name,
        gender=params.gender,
        parent_type=params.parent,
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


def asp_verify() -> int:
    rc = 0

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    ending_bad = []
    for item_id in ITEMS:
        if asp_ending(item_id) != ITEMS[item_id].owner_role:
            ending_bad.append((item_id, asp_ending(item_id), ITEMS[item_id].owner_role))
    if not ending_bad:
        print("OK: ASP ending role matches Python ending_of().")
    else:
        rc = 1
        print("MISMATCH in ending roles:", ending_bad)

    try:
        sample = generate(CURATED[0])
        if not sample.story or "north" not in sample.story.lower() or "struggle" not in sample.story.lower():
            raise StoryError("(Smoke test failed: story missing required seed words or empty story.)")
        print("OK: smoke test story generated.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    try:
        args = build_parser().parse_args([])
        params = resolve_params(args, random.Random(123))
        sample = generate(params)
        _ = sample.to_json()
        print("OK: default resolve/generate/json smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"DEFAULT SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show ending/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, item, method) combos:\n")
        for route_id, item_id, method_id in combos:
            print(f"  {route_id:12} {item_id:12} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = f"### {p.name}: {p.item} via {p.route} with {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
