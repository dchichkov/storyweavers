#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py
================================================================

A standalone story world for a tiny Animal Story domain built around a quest:
a young animal is sent to fetch something important, faces one concrete obstacle,
and either rushes into a small, harmless setback or listens early and solves the
problem with the right tool. The world model controls the turn: the obstacle has
a challenge type, tools only work when they truly fit that challenge, and a
hasty hero triggers a brief stumble before the fix.

Required seed words are woven naturally into the prose:
- "buckaroo" appears as a fond nickname from the helper
- "angled" appears in the journey imagery

Run it
------
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py --site brook --tool board
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py --site stump --tool board
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/buckaroo_angled_quest_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
HASTY_TRAITS = {"hasty", "bouncy", "daring"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "animal"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Site:
    id: str
    label: str
    challenge: str
    path_text: str
    obstacle_text: str
    fail_text: str
    success_text: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Quest:
    id: str
    item: str
    recipient: str
    need_text: str
    ending_text: str
    tags: set[str] = field(default_factory=set)
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    solves: str
    offer_text: str
    use_text: str
    qa_text: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "challenge": "",
            "stumbled": False,
            "resolved": False,
            "quest_done": False,
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


def has_right_tool(world: World, hero: Entity) -> bool:
    tool_id = hero.attrs.get("tool", "")
    if not tool_id:
        return False
    if tool_id not in TOOLS:
        return False
    return TOOLS[tool_id].solves == world.facts.get("challenge")


def _r_stuck(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["raw_attempt"] < THRESHOLD:
        return []
    if has_right_tool(world, hero):
        return []
    sig = ("stuck", world.facts.get("challenge", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["stuck"] += 1
    hero.memes["fear"] += 1
    hero.memes["humility"] += 1
    return ["__stuck__"]


def _r_reach(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["tool_attempt"] < THRESHOLD:
        return []
    if not has_right_tool(world, hero):
        return []
    sig = ("reached", world.facts.get("challenge", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["reached"] += 1
    hero.memes["confidence"] += 1
    return ["__reached__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="stuck", tag="physical", apply=_r_stuck),
    Rule(name="reach", tag="physical", apply=_r_reach),
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
        for sent in produced:
            world.say(sent)
    return produced


SITES = {
    "stump": Site(
        id="stump",
        label="the old stump hill",
        challenge="high",
        path_text="They followed an angled deer trail up the hill until the old stump rose above the grass like a little tower.",
        obstacle_text="The quest item waited at the top, much too high for small paws to reach from the ground.",
        fail_text="Hero scrambled up the bark, but slid back down with a soft thump and a surprised squeak.",
        success_text="With the ladder braced against the bark, Hero climbed carefully and reached the quest item at the top.",
        tags={"stump", "high"},
    ),
    "brambles": Site(
        id="brambles",
        label="the berry bramble ring",
        challenge="prickly",
        path_text="They padded beneath fern shadows until an angled branch pointed them toward a ring of berry brambles.",
        obstacle_text="The quest item gleamed inside, but the thorns were packed too closely for bare paws.",
        fail_text="Hero pushed in too fast and jerked back when the thorns snagged at fur and made the leaves shiver.",
        success_text="Wearing the gloves, Hero parted the thorny stems little by little and slipped inside to take the quest item gently.",
        tags={"brambles", "thorn"},
    ),
    "brook": Site(
        id="brook",
        label="the singing brook",
        challenge="slippery",
        path_text="They followed the mossy bank until the path bent at an angled root beside the singing brook.",
        obstacle_text="The quest item rested on the far side, beyond wet stones that shone like soap.",
        fail_text="Hero hopped onto a stone, wobbled at once, and sat down with a splash before the current could tug at their toes.",
        success_text="Hero laid the cork board across the slick stones, crossed step by step, and reached the quest item on the far bank.",
        tags={"brook", "water", "slippery"},
    ),
}

QUESTS = {
    "bell": Quest(
        id="bell",
        item="the silver bell",
        recipient="Mama Goat",
        need_text="Mama Goat's little wagon sounded lonely without the silver bell tied to its handle.",
        ending_text="Mama Goat tied the silver bell onto the wagon, and the lane rang with bright, happy chimes again.",
        tags={"bell"},
    ),
    "mint": Quest(
        id="mint",
        item="the cool mint sprig",
        recipient="Grandma Wren",
        need_text="Grandma Wren wanted the cool mint sprig for her evening tea, because her throat felt scratchy.",
        ending_text="Grandma Wren tucked the cool mint sprig into her steaming tea, and the whole burrow smelled fresh and calm.",
        tags={"mint", "tea"},
    ),
    "ribbon": Quest(
        id="ribbon",
        item="the golden ribbon",
        recipient="the Mole twins",
        need_text="The Mole twins needed the golden ribbon to finish the welcome arch at the garden gate before dusk.",
        ending_text="The Mole twins tied the golden ribbon to the welcome arch, and it fluttered over the path like a sunny smile.",
        tags={"ribbon"},
    ),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="vine ladder",
        phrase="a little vine ladder",
        solves="high",
        offer_text="Climbing is easier when the path goes up in steps. Let's carry a little vine ladder.",
        use_text="Helper steadied the vine ladder while Hero climbed one careful rung after another.",
        qa_text="used a vine ladder to climb safely",
        tags={"ladder", "climb"},
    ),
    "gloves": Tool(
        id="gloves",
        label="berry gloves",
        phrase="a pair of berry gloves",
        solves="prickly",
        offer_text="Thorns only feel brave when paws are bare. Let's use the berry gloves.",
        use_text="Hero pulled on the berry gloves and touched the thorny stems without getting poked.",
        qa_text="put on berry gloves to handle the thorns",
        tags={"gloves", "thorn"},
    ),
    "board": Tool(
        id="board",
        label="cork board",
        phrase="a light cork board",
        solves="slippery",
        offer_text="Wet stones like to wiggle under little feet. Let's lay down the cork board.",
        use_text="Together they set the cork board over the wet stones so the crossing stayed steady.",
        qa_text="laid down a cork board to cross the slick stones",
        tags={"board", "water"},
    ),
    "song": Tool(
        id="song",
        label="humming song",
        phrase="a brave little humming song",
        solves="none",
        offer_text="A song can cheer a traveler, but it does not solve a real obstacle.",
        use_text="The song was lovely, but it could not make the obstacle smaller.",
        qa_text="sang a song",
        tags={"song"},
    ),
}

HERO_NAMES = ["Pip", "Moss", "Nibbles", "Tumble", "Clover", "Pebble", "Sunny", "Bramble"]
HELPER_NAMES = ["Dot", "Fern", "Juniper", "Skipper", "Poppy", "Mallow", "Reed", "Wisp"]
ELDER_NAMES = ["Aunt Sable", "Grandpa Thimble", "Mama Goat", "Grandma Wren", "Uncle Toad"]

SPECIES = ["rabbit", "mouse", "squirrel", "hedgehog", "otter", "fox"]
TRAITS = ["careful", "patient", "steady", "hasty", "bouncy", "daring"]


def valid_combo(site_id: str, tool_id: str) -> bool:
    if site_id not in SITES or tool_id not in TOOLS:
        return False
    return TOOLS[tool_id].solves == SITES[site_id].challenge


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for site_id in SITES:
        for quest_id in QUESTS:
            for tool_id in TOOLS:
                if valid_combo(site_id, tool_id):
                    combos.append((site_id, quest_id, tool_id))
    return combos


@dataclass
class StoryParams:
    site: str
    quest: str
    tool: str
    hero_name: str
    hero_species: str
    helper_name: str
    helper_species: str
    elder_name: str
    elder_species: str
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


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["raw_attempt"] += 1
    propagate(sim, narrate=False)
    return {
        "stuck": hero.meters["stuck"] >= THRESHOLD,
        "fear": hero.memes["fear"],
    }


def introduce(world: World, hero: Entity, helper: Entity, elder: Entity, quest: Quest) -> None:
    world.say(
        f"In Clover Hollow, {hero.id} the {hero.attrs['species']} liked being useful even more than being first."
    )
    world.say(
        f"That morning, {elder.id} the {elder.attrs['species']} had a small worry. {quest.need_text}"
    )
    world.say(
        f'"Will you go on a quest for it?" {elder.id} asked. {helper.id} the {helper.attrs["species"]} came trotting over at once, ready to help.'
    )


def depart(world: World, hero: Entity, helper: Entity, quest: Quest, site: Site) -> None:
    hero.memes["purpose"] += 1
    helper.memes["care"] += 1
    world.say(
        f'{hero.id} nodded. "We will bring back {quest.item}," {hero.pronoun()} promised.'
    )
    world.say(site.path_text)


def arrive(world: World, quest: Quest, site: Site) -> None:
    world.say(
        f"There, near {site.label}, they saw {quest.item}. {site.obstacle_text}"
    )


def rush_without_plan(world: World, hero: Entity, site: Site) -> None:
    hero.meters["raw_attempt"] += 1
    propagate(world, narrate=False)
    world.facts["stumbled"] = hero.meters["stuck"] >= THRESHOLD
    world.say(
        f"{hero.id} was feeling very {hero.attrs['trait']}, so {hero.pronoun()} darted forward before making a plan."
    )
    if hero.meters["stuck"] >= THRESHOLD:
        world.say(site.fail_text)


def helper_warns(world: World, helper: Entity, tool: Tool, site: Site) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_stuck"] = pred["stuck"]
    world.say(
        f'"Easy, little buckaroo," said {helper.id}. "{tool.offer_text}"'
    )
    if pred["stuck"]:
        world.say(
            f"{helper.id} had seen right away that the {site.challenge} obstacle would be hard to manage without the right help."
        )


def equip_tool(world: World, hero: Entity, tool: Tool) -> None:
    hero.attrs["tool"] = tool.id
    hero.meters["equipped"] += 1
    world.say(f"They unpacked {tool.phrase} from the satchel they had brought along.")


def try_with_tool(world: World, hero: Entity, helper: Entity, site: Site, tool: Tool) -> None:
    hero.meters["tool_attempt"] += 1
    propagate(world, narrate=False)
    if hero.meters["reached"] < THRESHOLD:
        raise StoryError("(Internal story error: the equipped tool did not solve the obstacle.)")
    world.say(tool.use_text.replace("Helper", helper.id).replace("Hero", hero.id))
    world.say(site.success_text.replace("Hero", hero.id))


def claim_item(world: World, hero: Entity, quest: Quest) -> None:
    hero.meters["holding_item"] += 1
    hero.memes["joy"] += 1
    world.facts["quest_done"] = True
    world.say(
        f"{hero.id} lifted {quest.item} with both paws and grinned. The hardest part of the quest was over."
    )


def return_home(world: World, hero: Entity, helper: Entity, elder: Entity, quest: Quest) -> None:
    hero.memes["pride"] += 1
    helper.memes["joy"] += 1
    elder.memes["relief"] += 1
    world.facts["resolved"] = True
    world.say(
        f"By the time the sky turned honey-gold, {hero.id} and {helper.id} were back in Clover Hollow with {quest.item} safe between them."
    )
    world.say(
        f'"You did it," said {elder.id}, smiling so wide that even {hero.id} stood a little taller.'
    )
    world.say(quest.ending_text)


def closing_image(world: World, hero: Entity, helper: Entity) -> None:
    if world.facts.get("stumbled"):
        world.say(
            f"After that, {hero.id} still loved quick adventures, but now {hero.pronoun()} paused to listen before leaping. Beside {helper.id}, even a tricky path felt possible."
        )
    else:
        world.say(
            f"After that, {hero.id} felt ready for bigger quests too, because planning first had made the whole day shine. {helper.id} gave a pleased little nod, and the path home felt easy."
        )


def tell(
    site: Site,
    quest: Quest,
    tool: Tool,
    hero_name: str = "Pip",
    hero_species: str = "rabbit",
    helper_name: str = "Dot",
    helper_species: str = "mouse",
    elder_name: str = "Grandma Wren",
    elder_species: str = "wren",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="animal",
            label=hero_name,
            traits=[trait],
            attrs={"name": hero_name, "species": hero_species, "trait": trait, "tool": ""},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            type="animal",
            label=helper_name,
            attrs={"name": helper_name, "species": helper_species},
        )
    )
    elder = world.add(
        Entity(
            id="elder",
            kind="character",
            type="animal",
            label=elder_name,
            attrs={"name": elder_name, "species": elder_species},
        )
    )

    world.facts.update(
        {
            "site": site,
            "quest": quest,
            "tool": tool,
            "challenge": site.challenge,
            "trait": trait,
            "predicted_stuck": False,
        }
    )

    introduce(world, hero, helper, elder, quest)
    depart(world, hero, helper, quest, site)

    world.para()
    arrive(world, quest, site)

    if trait in HASTY_TRAITS:
        rush_without_plan(world, hero, site)
        helper_warns(world, helper, tool, site)
    else:
        helper_warns(world, helper, tool, site)

    equip_tool(world, hero, tool)
    try_with_tool(world, hero, helper, site, tool)

    world.para()
    claim_item(world, hero, quest)
    return_home(world, hero, helper, elder, quest)
    closing_image(world, hero, helper)

    world.facts.update(
        {
            "hero": hero,
            "helper": helper,
            "elder": elder,
            "outcome": "stumble_then_fix" if world.facts.get("stumbled") else "smooth",
        }
    )
    return world


KNOWLEDGE = {
    "ladder": [
        (
            "What is a ladder for?",
            "A ladder helps you go up safely by giving your feet small steps to climb. It is useful when something is too high to reach from the ground.",
        )
    ],
    "gloves": [
        (
            "Why do gloves help with thorns?",
            "Gloves cover your paws or hands so sharp thorns do not poke you so easily. They make careful touching much safer.",
        )
    ],
    "board": [
        (
            "Why is a board helpful on slippery stones?",
            "A board can make a flatter path over wet, slick places. That gives little feet a steadier way to cross.",
        )
    ],
    "thorn": [
        (
            "Why are brambles hard to walk through?",
            "Brambles are thick, thorny plants. Their sharp points can scratch fur or skin and make it hard to reach inside safely.",
        )
    ],
    "water": [
        (
            "Why are wet stones slippery?",
            "Wet stones can be slippery because the water makes their surface slick. Feet can slide on them more easily.",
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a ringing sound when it moves or is tapped. People and animals often use bells so something can be heard clearly.",
        )
    ],
    "mint": [
        (
            "What is mint?",
            "Mint is a green plant with a cool, fresh smell. People sometimes put mint in tea because it tastes and smells soothing.",
        )
    ],
    "ribbon": [
        (
            "What is a ribbon?",
            "A ribbon is a soft strip of cloth used for tying, decorating, or wrapping. It can make something plain look special.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ladder", "gloves", "board", "thorn", "water", "bell", "mint", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    quest = world.facts["quest"]
    site = world.facts["site"]
    outcome = world.facts["outcome"]
    if outcome == "stumble_then_fix":
        middle = (
            f"Include a moment where {hero.label} rushes at the obstacle first, then learns to slow down and use the right tool."
        )
    else:
        middle = (
            f"Include a calm planning moment where {helper.label} helps {hero.label} choose the right tool before crossing the obstacle."
        )
    return [
        f'Write a gentle Animal Story about a quest to fetch {quest.item} from {site.label}. Include the words "buckaroo" and "angled".',
        f"Tell a cozy quest story where a young {hero.attrs['species']} named {hero.label} and a helper named {helper.label} bring something important back to {quest.recipient}. {middle}",
        f'Write a short child-facing story with a clear beginning, a tricky obstacle, and a happy return home. Use the exact words "buckaroo" and "angled".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    elder = world.facts["elder"]
    quest = world.facts["quest"]
    site = world.facts["site"]
    tool = world.facts["tool"]
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "What was the quest in the story?",
            f"{hero.label} and {helper.label} went to fetch {quest.item} for {quest.recipient}. They did it because {quest.need_text}",
        ),
        (
            "Where did they go to find the quest item?",
            f"They went to {site.label}. The path there felt like a real journey because {site.path_text.lower()}",
        ),
        (
            f"Why was the obstacle hard?",
            f"It was hard because the place was {site.challenge}. {site.obstacle_text}",
        ),
    ]

    if outcome == "stumble_then_fix":
        qa.append(
            (
                f"What went wrong before the problem was solved?",
                f"{hero.label} rushed ahead before making a plan and got into a small bit of trouble. {site.fail_text} That moment showed why the obstacle needed the right tool, not just bravery.",
            )
        )
    else:
        qa.append(
            (
                f"How did {helper.label} help before anything went wrong?",
                f"{helper.label} looked at the obstacle and warned {hero.label} in time. {helper.label} could tell the {site.challenge} place needed {tool.phrase}, so the quest stayed calm instead of turning into a muddle.",
            )
        )

    qa.append(
        (
            "How did they solve the problem?",
            f"They used {tool.phrase}. {tool.qa_text.capitalize()}, which matched the obstacle and let {hero.label} reach {quest.item} safely.",
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"They brought {quest.item} home to {quest.recipient}, and the whole quest ended happily. {quest.ending_text}",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["tool"].tags) | set(world.facts["site"].tags) | set(world.facts["quest"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
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
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = [f"name={ent.label}"]
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:7} ({ent.type:7}) {' '.join(bits)}")
    lines.append(
        f"  facts: outcome={world.facts.get('outcome')} challenge={world.facts.get('challenge')} "
        f"stumbled={world.facts.get('stumbled')} resolved={world.facts.get('resolved')}"
    )
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="stump",
        quest="bell",
        tool="ladder",
        hero_name="Pip",
        hero_species="rabbit",
        helper_name="Fern",
        helper_species="mouse",
        elder_name="Mama Goat",
        elder_species="goat",
        trait="hasty",
    ),
    StoryParams(
        site="brambles",
        quest="mint",
        tool="gloves",
        hero_name="Moss",
        hero_species="hedgehog",
        helper_name="Juniper",
        helper_species="otter",
        elder_name="Grandma Wren",
        elder_species="wren",
        trait="careful",
    ),
    StoryParams(
        site="brook",
        quest="ribbon",
        tool="board",
        hero_name="Clover",
        hero_species="squirrel",
        helper_name="Reed",
        helper_species="fox",
        elder_name="Uncle Toad",
        elder_species="toad",
        trait="bouncy",
    ),
]


def explain_tool(site_id: str, tool_id: str) -> str:
    if site_id not in SITES or tool_id not in TOOLS:
        return "(No story: unknown site or tool.)"
    site = SITES[site_id]
    tool = TOOLS[tool_id]
    if tool.solves == "none":
        return (
            f"(No story: {tool.label} is pleasant, but it does not solve a real obstacle. "
            f"The quest at {site.label} needs a tool for something {site.challenge}.)"
        )
    return (
        f"(No story: {tool.label} solves something {tool.solves}, but {site.label} is {site.challenge}. "
        f"The tool must match the obstacle.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "stumble_then_fix" if params.trait in HASTY_TRAITS else "smooth"


ASP_RULES = r"""
valid(S, Q, T) :- site(S), quest(Q), tool(T), challenge(S, C), solves(T, C).

hasty_trait(T) :- trait_name(T), hasty(T).
outcome(stumble_then_fix) :- chosen_trait(T), hasty_trait(T).
outcome(smooth) :- chosen_trait(T), not hasty_trait(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        lines.append(asp.fact("challenge", site_id, site.challenge))
    for quest_id in QUESTS:
        lines.append(asp.fact("quest", quest_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        if tool.solves != "none":
            lines.append(asp.fact("solves", tool_id, tool.solves))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(HASTY_TRAITS):
        lines.append(asp.fact("hasty", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_trait", params.trait)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    rows = asp.atoms(model, "outcome")
    return rows[0][0] if rows else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story quest world. Unspecified choices are picked at random from valid combinations."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--quest", choices=sorted(QUESTS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.tool and not valid_combo(args.site, args.tool):
        raise StoryError(explain_tool(args.site, args.tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.quest is None or combo[1] == args.quest)
        and (args.tool is None or combo[2] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, quest_id, tool_id = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(sorted(TRAITS))
    hero_name = rng.choice(HERO_NAMES)
    helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    elder_name = rng.choice(ELDER_NAMES)
    hero_species = rng.choice(SPECIES)
    helper_species = rng.choice([s for s in SPECIES if s != hero_species] or SPECIES)
    elder_species = rng.choice(["goat", "wren", "toad", "badger", "mole"])

    return StoryParams(
        site=site_id,
        quest=quest_id,
        tool=tool_id,
        hero_name=hero_name,
        hero_species=hero_species,
        helper_name=helper_name,
        helper_species=helper_species,
        elder_name=elder_name,
        elder_species=elder_species,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(No story: unknown site '{params.site}'.)")
    if params.quest not in QUESTS:
        raise StoryError(f"(No story: unknown quest '{params.quest}'.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool '{params.tool}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if not valid_combo(params.site, params.tool):
        raise StoryError(explain_tool(params.site, params.tool))

    world = tell(
        site=SITES[params.site],
        quest=QUESTS[params.quest],
        tool=TOOLS[params.tool],
        hero_name=params.hero_name,
        hero_species=params.hero_species,
        helper_name=params.helper_name,
        helper_species=params.helper_species,
        elder_name=params.elder_name,
        elder_species=params.elder_species,
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
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=False)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (site, quest, tool) combinations:\n")
        for site_id, quest_id, tool_id in combos:
            print(f"  {site_id:10} {quest_id:8} {tool_id}")
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
            header = f"### {p.hero_name}: {p.quest} at {p.site} with {p.tool} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
