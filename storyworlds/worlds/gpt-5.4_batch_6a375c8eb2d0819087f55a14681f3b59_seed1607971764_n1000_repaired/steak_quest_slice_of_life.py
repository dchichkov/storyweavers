#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py
======================================================

A small standalone storyworld about an everyday family "quest": dinner is nearly
ready, steak is on the stove, and one last important item is missing. A child is
sent on a small household quest to fetch it the sensible way.

The domain is deliberately narrow and constraint-checked:
- each missing item belongs in one source place
- each item has a retrieval need
- only a matching tool makes a reasonable story

The stories stay close to slice-of-life: a kitchen, a parent, a child eager to
help, a tiny obstacle, a calm correction, and a changed ending image around the
table.

Run it
------
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py --item rosemary --place herb_patch
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py --item potatoes --tool step_stool
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py --all
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py --asp
python storyworlds/worlds/gpt-5.4/steak_quest_slice_of_life.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
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
    phrase: str
    challenge: str
    detail: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class NeedItem:
    id: str
    label: str
    phrase: str
    source: str
    need: str
    use_text: str
    success_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: set[str]
    prep: str
    carry_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "attempt_need": "",
            "attempt_failed": False,
            "quest_done": False,
            "predicted_problem": "",
            "pet": "",
        }

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_fail_attempt(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.meters["attempting"] < THRESHOLD:
        return out
    need = world.facts.get("attempt_need", "")
    if not need:
        return out
    tool = world.entities.get("tool")
    solved = bool(tool and need in tool.attrs.get("solves", set()))
    sig = ("attempt", need, solved)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["attempting"] = 0.0
    if solved:
        item.meters["found"] += 1
        item.meters["carried"] += 1
        child.memes["confidence"] += 1
        child.memes["pride"] += 1
        world.facts["quest_done"] = True
        return out
    item.meters["found"] = 0.0
    child.memes["worry"] += 1
    world.get("parent").memes["worry"] += 1
    world.facts["attempt_failed"] = True
    if need == "high":
        out.append("__failed_high__")
    elif need == "heavy":
        out.append("__failed_heavy__")
    elif need == "snip":
        out.append("__failed_snip__")
    return out


def _r_dinner_ready(world: World) -> list[str]:
    item = world.get("item")
    dinner = world.get("dinner")
    if item.meters["carried"] < THRESHOLD:
        return []
    sig = ("dinner_ready", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    dinner.meters["ready"] += 1
    world.get("parent").memes["relief"] += 1
    world.get("child").memes["belonging"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="fail_attempt", tag="quest", apply=_r_fail_attempt),
    Rule(name="dinner_ready", tag="resolution", apply=_r_dinner_ready),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


PLACES = {
    "high_cupboard": Place(
        id="high_cupboard",
        label="high cupboard",
        phrase="the high cupboard by the fridge",
        challenge="high",
        detail="The good steak knives lived on the top shelf, above the cereal boxes.",
        tags={"cupboard", "home"},
    ),
    "cellar_steps": Place(
        id="cellar_steps",
        label="cellar steps",
        phrase="the cool cellar steps",
        challenge="heavy",
        detail="The potatoes waited in a paper sack on the lowest step where the air stayed cool.",
        tags={"cellar", "potato"},
    ),
    "herb_patch": Place(
        id="herb_patch",
        label="herb patch",
        phrase="the herb patch outside the back door",
        challenge="snip",
        detail="The rosemary bush leaned over the bricks, smelling sharp and green in the evening air.",
        tags={"garden", "rosemary"},
    ),
}

ITEMS = {
    "steak_knives": NeedItem(
        id="steak_knives",
        label="steak knives",
        phrase="the steak knives",
        source="high_cupboard",
        need="high",
        use_text="so everyone could cut the steak neatly",
        success_text="set the steak knives beside each plate",
        tags={"steak", "knife"},
    ),
    "potatoes": NeedItem(
        id="potatoes",
        label="potatoes",
        phrase="the potatoes for the steak dinner",
        source="cellar_steps",
        need="heavy",
        use_text="because the potatoes still needed washing and chopping for the pan",
        success_text="poured the potatoes into the sink with a soft thump",
        tags={"steak", "potato"},
    ),
    "rosemary": NeedItem(
        id="rosemary",
        label="rosemary",
        phrase="a sprig of rosemary for the steak",
        source="herb_patch",
        need="snip",
        use_text="to lay something fresh and good-smelling on top of the steak",
        success_text="laid the rosemary by the cutting board, filling the kitchen with a piney smell",
        tags={"steak", "rosemary"},
    ),
}

TOOLS = {
    "step_stool": Tool(
        id="step_stool",
        label="step stool",
        phrase="the little step stool",
        solves={"high"},
        prep="brought over the little step stool",
        carry_text="climbed up one careful step and reached the shelf safely",
        tags={"stool"},
    ),
    "basket": Tool(
        id="basket",
        label="basket",
        phrase="the wire basket with two handles",
        solves={"heavy"},
        prep="set the wire basket on the floor",
        carry_text="used both hands on the basket and carried the weight close to the body",
        tags={"basket"},
    ),
    "kitchen_scissors": Tool(
        id="kitchen_scissors",
        label="kitchen scissors",
        phrase="the small kitchen scissors",
        solves={"snip"},
        prep="handed over the small kitchen scissors",
        carry_text="pinched the rosemary stem and snipped off just enough",
        tags={"scissors"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Jack", "Finn", "Noah", "Theo", "Eli", "Owen"]
TRAITS = ["eager", "careful", "curious", "helpful", "bright", "steady"]
PETS = ["the dog", "the cat", "", ""]

KNOWLEDGE = {
    "steak": [(
        "What is steak?",
        "Steak is a piece of beef cooked in a pan or on a grill. Families often eat it for dinner with vegetables or potatoes."
    )],
    "knife": [(
        "What are steak knives for?",
        "Steak knives are table knives with sharp edges for cutting cooked meat. Grown-ups choose a safe place to keep them when they are not being used."
    )],
    "potato": [(
        "Why do people eat potatoes with dinner?",
        "Potatoes are filling and soft when cooked. They are often served beside a meal like steak because they go well together."
    )],
    "rosemary": [(
        "What is rosemary?",
        "Rosemary is an herb with thin green leaves and a strong smell. People use a little of it to give food a fresh flavor."
    )],
    "stool": [(
        "What is a step stool for?",
        "A step stool helps you reach something high without stretching dangerously. It is safer than climbing on a chair."
    )],
    "basket": [(
        "Why can a basket help carry heavy food?",
        "A basket can hold the weight and give you steady handles to grip. That makes carrying heavy things easier and safer."
    )],
    "scissors": [(
        "Why do you use scissors to cut herbs?",
        "Scissors let you snip a small piece neatly. That way you do not tug at the whole plant or tear it by mistake."
    )],
}
KNOWLEDGE_ORDER = ["steak", "knife", "potato", "rosemary", "stool", "basket", "scissors"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            if item.source != place_id:
                continue
            for tool_id, tool in TOOLS.items():
                if place.challenge in tool.solves and item.need in tool.solves:
                    combos.append((place_id, item_id, tool_id))
    return combos


@dataclass
class StoryParams:
    place: str
    item: str
    tool: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


CURATED = [
    StoryParams(
        place="high_cupboard",
        item="steak_knives",
        tool="step_stool",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        trait="eager",
        seed=101,
    ),
    StoryParams(
        place="cellar_steps",
        item="potatoes",
        tool="basket",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="helpful",
        seed=102,
    ),
    StoryParams(
        place="herb_patch",
        item="rosemary",
        tool="kitchen_scissors",
        child_name="Maya",
        child_gender="girl",
        parent="mother",
        trait="careful",
        seed=103,
    ),
]


def explain_rejection(place: Place, item: NeedItem, tool: Tool) -> str:
    if item.source != place.id:
        right = PLACES[item.source].label
        return (
            f"(No story: {item.label} do not come from the {place.label} in this world. "
            f"Try the {right} instead.)"
        )
    if place.challenge not in tool.solves or item.need not in tool.solves:
        need_map = {
            "high": "something tall enough to reach safely",
            "heavy": "something that helps carry weight steadily",
            "snip": "something that can snip herbs neatly",
        }
        return (
            f"(No story: {tool.label} does not solve this quest. Getting {item.label} from "
            f"the {place.label} needs {need_map[item.need]}.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_problem(world: World, item: NeedItem) -> dict:
    sim = world.copy()
    sim.facts["attempt_need"] = item.need
    sim.get("child").meters["attempting"] += 1
    propagate(sim, narrate=False)
    return {
        "failed": bool(sim.facts.get("attempt_failed")),
        "problem": {
            "high": "the shelf would still be too high",
            "heavy": "the load would be too awkward to carry safely",
            "snip": "pulling by hand would bend the whole plant",
        }[item.need],
    }


def dinner_setup(world: World, child: Entity, parent: Entity, item: NeedItem, place: Place) -> None:
    child.memes["eagerness"] += 1
    world.say(
        f"At the end of the day, the kitchen smelled warm and cozy. "
        f"In the pan, the steak was nearly done, and {parent.label_word} was turning it with careful tongs."
    )
    world.say(
        f"{child.id} stood nearby, wanting to help in every small way. "
        f'"Can I do something important?" {child.pronoun()} asked.'
    )
    world.say(
        f"{parent.label_word.capitalize()} looked around the kitchen, then smiled. "
        f'"Yes. We are missing {item.phrase}," {parent.pronoun()} said. '
        f'"Would you go on a little dinner quest to fetch {item.pronoun("object") if item.label == "rosemary" else item.label}?"'
    )
    world.say(place.detail)


def send_quest(world: World, child: Entity, parent: Entity, item: NeedItem, place: Place) -> None:
    pred = predict_problem(world, item)
    world.facts["predicted_problem"] = pred["problem"]
    world.say(
        f"{child.id} hurried toward {place.phrase} right away. {parent.label_word.capitalize()} "
        f"noticed and called softly, \"Slow down a moment.\""
    )
    world.say(
        f'"If you go just like that, {pred["problem"]}," {parent.pronoun()} said. '
        f'"We need {item.phrase} {item.use_text}."'
    )


def first_try(world: World, child: Entity, item: NeedItem) -> None:
    world.facts["attempt_need"] = item.need
    child.meters["attempting"] += 1
    propagate(world, narrate=False)
    if item.need == "high":
        world.say(
            f"{child.id} stretched on tiptoe anyway, but the shelf stayed high and still."
        )
    elif item.need == "heavy":
        world.say(
            f"{child.id} bent for the sack anyway, but it sagged and dragged before {child.pronoun()} had really lifted it."
        )
    else:
        world.say(
            f"{child.id} pinched at the rosemary anyway, but the whole branch only bent and sprang back."
        )


def equip_tool(world: World, child: Entity, parent: Entity, tool: Tool) -> None:
    ent = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        role="tool",
        attrs={"solves": set(tool.solves)},
        tags=set(tool.tags),
    ))
    ent.meters["ready"] = 1.0
    child.memes["trust"] += 1
    world.say(
        f"Then {parent.label_word} {tool.prep}. "
        f'"Try again with this," {parent.pronoun()} said.'
    )


def succeed(world: World, child: Entity, parent: Entity, item: NeedItem, tool: Tool) -> None:
    world.facts["attempt_need"] = item.need
    child.meters["attempting"] += 1
    propagate(world, narrate=False)
    world.say(
        f"This time, {child.id} {tool.carry_text}. "
        f"In one small moment, the quest stopped feeling hard and started feeling possible."
    )
    if item.id == "steak_knives":
        world.say(
            f"{child.pronoun().capitalize()} carried the wooden box back with both hands, walking as if it were treasure."
        )
    elif item.id == "potatoes":
        world.say(
            f"{child.pronoun().capitalize()} brought the basket upstairs one steady step at a time."
        )
    else:
        world.say(
            f"{child.pronoun().capitalize()} held the rosemary up carefully so the smell could come inside with {child.pronoun('object')}."
        )
    world.say(
        f"In the kitchen, {parent.label_word} {item.success_text}."
    )


def ending(world: World, child: Entity, parent: Entity, item: NeedItem) -> None:
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    parent.memes["love"] += 1
    pet = world.facts.get("pet", "")
    world.say(
        f'"Quest complete," {child.id} said, and {parent.label_word} laughed.'
    )
    world.say(
        f"Soon the family sat down together. The steak looked ready at the center of the table, "
        f"and {child.id} could see the one missing thing was missing no longer."
    )
    if pet:
        world.say(
            f"{pet.capitalize()} lay under the table, hoping for a good smell and maybe one tiny crumb."
        )
    world.say(
        f"{child.id} took the first bite feeling taller than before, because helping had turned dinner into part of the adventure."
    )


def tell(
    place: Place,
    item: NeedItem,
    tool: Tool,
    child_name: str = "Lily",
    child_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "eager",
    pet: str = "",
) -> World:
    world = World(place)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"name": child_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    dinner = world.add(Entity(
        id="dinner",
        kind="thing",
        type="dinner",
        label="steak dinner",
        phrase="the steak dinner",
        tags={"steak"},
    ))
    fetched = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item.label,
        phrase=item.phrase,
        role="item",
        tags=set(item.tags),
    ))
    child.memes["helpfulness"] = 1.0
    parent.memes["calm"] = 1.0
    world.facts.update(
        child=child,
        parent=parent,
        item_cfg=item,
        place_cfg=place,
        tool_cfg=tool,
        pet=pet,
    )

    dinner_setup(world, child, parent, item, place)
    world.para()
    send_quest(world, child, parent, item, place)
    first_try(world, child, item)
    equip_tool(world, child, parent, tool)
    world.para()
    succeed(world, child, parent, item, tool)
    ending(world, child, parent, item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old where a child goes on a tiny quest to fetch {item.phrase} before steak dinner.',
        f"Tell a gentle home story where {child.attrs['name']} wants to help {child.pronoun('possessive')} {parent.label_word} and must solve a small problem at {place.phrase}.",
        f'Write a simple story that includes the word "steak" and turns an everyday dinner errand into a little quest with a warm family ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item_cfg"]
    place = f["place_cfg"]
    tool = f["tool_cfg"]
    problem = f.get("predicted_problem", "")
    name = child.attrs["name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name}, who wanted to help at home, and {name}'s {pw}, who was making steak for dinner."
        ),
        (
            f"What was {name}'s quest?",
            f"{name}'s quest was to fetch {item.phrase} from {place.phrase}. It mattered because the family still needed it for the steak dinner."
        ),
        (
            f"Why did {pw} tell {name} to slow down?",
            f"{pw.capitalize()} could see that going without the right tool would not work. {problem.capitalize()}, so {pw} wanted {name} to do the quest the safe and sensible way."
        ),
        (
            f"What happened the first time {name} tried?",
            {
                "high": f"{name} stretched up, but the shelf stayed out of reach. That showed why the quest needed help, not just hurry.",
                "heavy": f"{name} tried to lift the load, but it dragged awkwardly instead. The problem was weight and steadiness, not effort.",
                "snip": f"{name} tugged at the rosemary, but the whole branch bent instead of giving a neat piece. The plant needed a clean snip, not a pull.",
            }[item.need],
        ),
        (
            f"How did {name} finish the quest?",
            f"{pw.capitalize()} gave {name} {tool.phrase}, and then the job worked. The tool matched the real problem, so {name} could bring back {item.label} safely."
        ),
        (
            "How did the story end?",
            f"The family sat down to steak dinner together, and the missing item was on the table or in the pan where it belonged. {name} felt proud because helping with one small quest changed the whole meal."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"steak"}
    item = world.facts["item_cfg"]
    tool = world.facts["tool_cfg"]
    tags |= set(item.tags)
    tags |= set(tool.tags)
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
    for eid, e in world.entities.items():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {eid:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
belongs(I, P) :- item(I), place(P), source(I, P).
fits(T, I) :- tool(T), item(I), need(I, N), solves(T, N).
valid(P, I, T) :- belongs(I, P), fits(T, I), challenge(P, N), solves(T, N).
#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("challenge", pid, place.challenge))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("source", iid, item.source))
        lines.append(asp.fact("need", iid, item.need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(tool.solves):
            lines.append(asp.fact("solves", tid, need))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tiny home quest before steak dinner."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.tool:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        tool = TOOLS[args.tool]
        if (args.place, args.item, args.tool) not in set(valid_combos()):
            raise StoryError(explain_rejection(place, item, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, tool_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        item=item_id,
        tool=tool_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if (params.place, params.item, params.tool) not in set(valid_combos()):
        raise StoryError(explain_rejection(PLACES[params.place], ITEMS[params.item], TOOLS[params.tool]))

    rng = random.Random(params.seed)
    pet = rng.choice(PETS)
    world = tell(
        place=PLACES[params.place],
        item=ITEMS[params.item],
        tool=TOOLS[params.tool],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        pet=pet,
    )
    name = params.child_name
    story_text = world.render().replace("child", name)
    story_text = story_text.replace("parent", world.get("parent").label_word)
    story_text = story_text.replace("child's", f"{name}'s")
    story_text = story_text.replace("Child", name)
    world.entities["child"].id = name
    world.facts["child"].id = name
    return StorySample(
        params=params,
        story=story_text,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, tool) combos:\n")
        for place, item, tool in combos:
            print(f"  {place:13} {item:14} {tool}")
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
            header = f"### {p.child_name}: {p.item} from {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
