#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py
====================================================================================

A standalone story world about a child group trying to do something kind together.
The domain centers on a simple moral notion: **some jobs are too big for one child,
but small caring actions can fit together into teamwork**.

Reference seed shape
--------------------
A heartwarming TinyStories-style tale where children want to help, one child first
tries to do everything alone, the plan wobbles, friends join in, and the shared work
creates a happy ending. The word "notion" appears naturally in the story.

Run it
------
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py --task garden_bed --helper sora
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py --task stage_banner --tool wagon
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py --tool spoon
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/notion_moral_value_teamwork_happy_ending_heartwarming.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    heavy: bool = False
    carrying: bool = False
    # typed world axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Task:
    id: str
    place: str
    goal_label: str
    scene: str
    object_label: str
    object_phrase: str
    item_kind: str
    heavy_need: int
    needs_wheels: bool
    result_image: str
    helper_action: str
    child_benefit: str
    moral_line: str
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
    support: int
    wheels: bool = False
    sense: int = 2
    carrying: bool = False
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
class HelperProfile:
    id: str
    name: str
    gender: str
    trait: str
    encouragement: str
    ending_line: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "helper"}]

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


def _r_strain(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("phase") != "solo_try":
        return out
    lead = world.get("lead")
    item = world.get("item")
    if lead.meters["effort"] < THRESHOLD:
        return out
    if item.meters["moved"] >= THRESHOLD:
        return out
    sig = ("strain", lead.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lead.memes["frustration"] += 1
    lead.meters["wobble_seen"] += 1
    out.append("__strain__")
    return out


def _r_team_move(world: World) -> list[str]:
    out: list[str] = []
    lead = world.get("lead")
    helper = world.get("helper")
    item = world.get("item")
    total_support = (
        int(lead.meters["push_power"]) +
        int(helper.meters["push_power"]) +
        int(world.facts.get("tool_support", 0))
    )
    if world.facts.get("phase") != "team_try":
        return out
    sig = ("team_move", item.id, total_support)
    if sig in world.fired:
        return out
    if total_support >= int(world.facts["heavy_need"]) and (
        (not world.facts["needs_wheels"]) or world.facts["tool_wheels"]
    ):
        world.fired.add(sig)
        item.meters["moved"] += 1
        lead.memes["hope"] += 1
        helper.memes["hope"] += 1
        out.append("__moved__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if item.meters["moved"] < THRESHOLD:
        return out
    sig = ("kindness_done", item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["care"] += 1
        kid.memes["joy"] += 1
    world.get("adult").memes["gratitude"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="strain", tag="social", apply=_r_strain),
    Rule(name="team_move", tag="physical", apply=_r_team_move),
    Rule(name="kindness", tag="moral", apply=_r_kindness),
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


def valid_combo(task: Task, tool: Tool) -> bool:
    if tool.sense < SENSE_MIN:
        return False
    if task.needs_wheels and not tool.wheels:
        return False
    if tool.support <= 0:
        return False
    return task.heavy_need <= 2 + tool.support


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for task_id, task in TASKS.items():
        for tool_id, tool in TOOLS.items():
            if valid_combo(task, tool):
                combos.append((task_id, tool_id))
    return combos


def explain_rejection(task: Task, tool: Tool) -> str:
    if tool.sense < SENSE_MIN:
        return (f"(No story: {tool.phrase} is not a sensible teamwork tool here. "
                f"Pick something sturdier, like a wagon, rolling cart, or wide strap.)")
    if task.needs_wheels and not tool.wheels:
        return (f"(No story: moving {task.object_phrase} to {task.goal_label} needs "
                f"wheels, but {tool.phrase} has none. The children need a rolling tool.)")
    if task.heavy_need > 2 + tool.support:
        return (f"(No story: even with two children, {tool.phrase} does not give enough "
                f"help to move {task.object_phrase}. The fix must actually work.)")
    return "(No story: that combination is not reasonable.)"


def predict_success(world: World) -> dict:
    sim = world.copy()
    sim.facts["phase"] = "team_try"
    sim.get("lead").meters["push_power"] = 1
    sim.get("helper").meters["push_power"] = 1
    propagate(sim, narrate=False)
    return {
        "moved": sim.get("item").meters["moved"] >= THRESHOLD,
        "need": sim.facts["heavy_need"],
        "support": sim.facts["tool_support"],
    }


def introduce(world: World, lead: Entity, adult: Entity, task: Task) -> None:
    lead.memes["care"] += 1
    world.say(
        f"One bright afternoon, {lead.id} was in {task.place} when {lead.pronoun()} noticed "
        f"{task.scene}."
    )
    world.say(
        f"{lead.pronoun().capitalize()} had a kind notion that the children in the neighborhood "
        f"would smile if someone helped make it ready."
    )
    world.say(
        f"{adult.label_word.capitalize()} was nearby, setting out little things for the day, "
        f"and {lead.id} wanted to do something useful."
    )


def explain_task(world: World, lead: Entity, adult: Entity, task: Task) -> None:
    world.say(
        f'"If we can get {task.object_phrase} to {task.goal_label}," {lead.id} said, '
        f'"then {task.child_benefit}."'
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled and said, "{task.moral_line}"'
    )


def solo_attempt(world: World, lead: Entity, item: Entity, task: Task) -> None:
    world.facts["phase"] = "solo_try"
    lead.meters["effort"] += 1
    lead.meters["push_power"] = 1
    world.say(
        f"{lead.id} put both hands on {task.object_phrase} and tried to move it alone."
    )
    propagate(world, narrate=False)
    if lead.memes["frustration"] >= THRESHOLD:
        world.say(
            f"It scraped only a tiny bit. {lead.id} felt {lead.pronoun('possessive')} cheeks grow warm, "
            f"because good wishes were not enough by themselves."
        )


def helper_arrives(world: World, lead: Entity, helper: Entity, task: Task) -> None:
    helper.memes["care"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"Just then, {helper.id} came by and saw {lead.id} trying so hard."
    )
    world.say(
        f'"What if we do it together?" {helper.id} asked. "{HELPERS[world.facts["helper_profile"]].encouragement}"'
    )
    world.say(
        f"The notion of sharing the work made the hard job feel smaller already."
    )


def choose_tool(world: World, adult: Entity, tool: Tool) -> None:
    world.say(
        f'{adult.label_word.capitalize()} looked around and brought over {tool.phrase}. '
        f'"Two caring hands are even better with the right help," {adult.pronoun()} said.'
    )


def team_attempt(world: World, lead: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    world.facts["phase"] = "team_try"
    lead.meters["push_power"] = 1
    helper.meters["push_power"] = 1
    if tool.carrying:
        world.get("tool").carrying = True
    world.say(
        f"{lead.id} and {helper.id} {task.helper_action} with {tool.phrase}."
    )
    propagate(world, narrate=False)
    if world.get("item").meters["moved"] >= THRESHOLD:
        world.say(
            f"This time {task.object_phrase} rolled along steadily, and the two friends laughed with relief."
        )


def finish_scene(world: World, lead: Entity, helper: Entity, adult: Entity,
                 task: Task, helper_profile: HelperProfile) -> None:
    world.say(
        f"When the work was done, {task.result_image}."
    )
    world.say(
        f'{adult.label_word.capitalize()} clapped softly. "You finished it by helping each other," '
        f'{adult.pronoun()} said.'
    )
    world.say(
        f'{helper_profile.ending_line} {lead.id} nodded, and both children felt proud in the warm, calm way '
        f"that comes after kindness."
    )


def tell(task: Task, tool: Tool, helper_profile: HelperProfile,
         lead_name: str = "Nia", lead_gender: str = "girl",
         adult_type: str = "mother") -> World:
    world = World()
    lead = world.add(Entity(
        id=lead_name, kind="character", type=lead_gender, role="lead",
        traits=["kind", "eager"], attrs={}
    ))
    helper = world.add(Entity(
        id=helper_profile.name, kind="character", type=helper_profile.gender,
        role="helper", traits=[helper_profile.trait], attrs={}
    ))
    adult = world.add(Entity(
        id="Adult", kind="character", type=adult_type, role="adult",
        label="the grown-up", attrs={}
    ))
    item = world.add(Entity(
        id="item", kind="thing", type=task.item_kind, label=task.object_label,
        movable=True, heavy=True, attrs={}
    ))
    tool_ent = world.add(Entity(
        id="tool", kind="thing", type="tool", label=tool.label,
        movable=True, carrying=tool.carrying, attrs={}
    ))

    world.facts["task"] = task
    world.facts["tool_cfg"] = tool
    world.facts["helper_cfg"] = helper_profile
    world.facts["helper_profile"] = helper_profile.id
    world.facts["heavy_need"] = task.heavy_need
    world.facts["needs_wheels"] = task.needs_wheels
    world.facts["tool_support"] = tool.support
    world.facts["tool_wheels"] = tool.wheels
    world.facts["phase"] = "setup"

    introduce(world, lead, adult, task)
    explain_task(world, lead, adult, task)

    world.para()
    solo_attempt(world, lead, item, task)
    helper_arrives(world, lead, helper, task)
    choose_tool(world, adult, tool)

    pred = predict_success(world)
    world.facts["predicted_success"] = pred["moved"]
    world.facts["predicted_need"] = pred["need"]
    world.facts["predicted_support"] = pred["support"]

    world.para()
    team_attempt(world, lead, helper, task, tool)
    finish_scene(world, lead, helper, adult, task, helper_profile)

    world.facts.update(
        lead=lead,
        helper=helper,
        adult=adult,
        item=item,
        tool=tool_ent,
        task_done=item.meters["moved"] >= THRESHOLD,
        teamwork_used=True,
        moral_learned=lead.memes["care"] >= THRESHOLD and helper.memes["care"] >= THRESHOLD,
    )
    return world


TASKS = {
    "garden_bed": Task(
        id="garden_bed",
        place="the community yard",
        goal_label="the sunny corner by the fence",
        scene="a bare patch of dirt waiting for flowers",
        object_label="planter box",
        object_phrase="the wooden planter box full of soil",
        item_kind="planter",
        heavy_need=3,
        needs_wheels=True,
        result_image="soon the planter sat in the sunlight, ready for seeds and tiny watering cans",
        helper_action="pulled and guided the heavy box",
        child_benefit="everyone can plant bright flowers there after school",
        moral_line="Kind ideas grow best when people share the work.",
        tags={"garden", "teamwork", "kindness"},
    ),
    "book_corner": Task(
        id="book_corner",
        place="the library hall",
        goal_label="the reading rug under the paper stars",
        scene="a stack of books waiting beside a low shelf",
        object_label="book basket",
        object_phrase="the big book basket packed with picture books",
        item_kind="basket",
        heavy_need=2,
        needs_wheels=False,
        result_image="the reading rug looked cozy, with books close enough for every small hand to reach",
        helper_action="lifted and steadied the basket",
        child_benefit="the littler children can choose stories more easily",
        moral_line="A caring job feels lighter when friends carry it together.",
        tags={"books", "teamwork", "sharing"},
    ),
    "stage_banner": Task(
        id="stage_banner",
        place="the school hall",
        goal_label="the front of the little stage",
        scene="a painted banner and a box of decorations waiting for the music night",
        object_label="decoration cart",
        object_phrase="the tall cart stacked with banner poles and bright paper stars",
        item_kind="cartload",
        heavy_need=3,
        needs_wheels=True,
        result_image="the stage glowed with color, and the banner hung straight above the chairs",
        helper_action="pushed and steered the load",
        child_benefit="families can see the welcome banner when they come in",
        moral_line="When work is shared, joy has room to arrive too.",
        tags={"stage", "teamwork", "welcome"},
    ),
}

TOOLS = {
    "wagon": Tool(
        id="wagon",
        label="wagon",
        phrase="a red wagon",
        support=2,
        wheels=True,
        sense=3,
        carrying=True,
        tags={"wagon", "wheels"},
    ),
    "rolling_cart": Tool(
        id="rolling_cart",
        label="rolling cart",
        phrase="a sturdy rolling cart",
        support=2,
        wheels=True,
        sense=3,
        carrying=True,
        tags={"cart", "wheels"},
    ),
    "wide_strap": Tool(
        id="wide_strap",
        label="wide strap",
        phrase="a wide cloth lifting strap",
        support=1,
        wheels=False,
        sense=2,
        carrying=False,
        tags={"strap", "lifting"},
    ),
    "spoon": Tool(
        id="spoon",
        label="spoon",
        phrase="a kitchen spoon",
        support=0,
        wheels=False,
        sense=1,
        carrying=False,
        tags={"silly"},
    ),
}

HELPERS = {
    "sora": HelperProfile(
        id="sora",
        name="Sora",
        gender="girl",
        trait="steady",
        encouragement="You pull one side, and I will take the other.",
        ending_line='"We did not just finish a job," Sora said. "We made the place kinder."',
        tags={"friend"},
    ),
    "milo": HelperProfile(
        id="milo",
        name="Milo",
        gender="boy",
        trait="cheerful",
        encouragement="If we count together, our arms can work together too.",
        ending_line='"It feels good when nobody is left to do the hard part alone," Milo said.',
        tags={"friend"},
    ),
    "ruth": HelperProfile(
        id="ruth",
        name="Ruth",
        gender="girl",
        trait="thoughtful",
        encouragement="Let us slow down and make a real plan first.",
        ending_line='"A shared plan can be gentle and strong at the same time," Ruth said.',
        tags={"friend"},
    ),
}

LEAD_NAMES = {
    "girl": ["Nia", "Lina", "Ava", "Maya", "Ella", "June"],
    "boy": ["Owen", "Leo", "Ben", "Noah", "Eli", "Finn"],
}
LEAD_TRAITS = ["kind", "helpful", "eager", "gentle"]


@dataclass
class StoryParams:
    task: str
    tool: str
    helper: str
    lead_name: str
    lead_gender: str
    adult: str
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


KNOWLEDGE = {
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people share a job and help one another do it. A hard task can become easier when everyone does a part."
    )],
    "kindness": [(
        "What is kindness?",
        "Kindness means choosing to help, comfort, or care for someone. Small kind actions can change how a whole place feels."
    )],
    "wagon": [(
        "What is a wagon good for?",
        "A wagon helps people move heavy things because it rolls on wheels. Wheels can do part of the hard work."
    )],
    "cart": [(
        "Why is a rolling cart useful?",
        "A rolling cart lets you push a load instead of carrying it all in your arms. That makes heavy things easier to move safely."
    )],
    "strap": [(
        "What does a lifting strap do?",
        "A lifting strap helps two people hold the same heavy thing together. It spreads the pull so the load feels steadier."
    )],
    "books": [(
        "Why is it nice to share books?",
        "Sharing books helps more children enjoy stories together. A cozy reading place can make everyone feel welcome."
    )],
    "garden": [(
        "Why do flowers need a sunny place?",
        "Flowers grow best when they have light and care. A sunny spot helps many plants grow strong."
    )],
    "welcome": [(
        "What does a welcome banner do?",
        "A welcome banner shows guests that they are meant to come in and feel included. It can make a room feel friendly before anyone speaks."
    )],
}
KNOWLEDGE_ORDER = ["teamwork", "kindness", "wagon", "cart", "strap", "books", "garden", "welcome"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    task = f["task"]
    tool = f["tool_cfg"]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old that includes the word "notion" and shows teamwork.',
        f"Tell a gentle story where {lead.id} has a kind idea in {task.place}, cannot finish the job alone, and then works with {helper.id} using {tool.phrase}.",
        f"Write a story with a moral about sharing hard work so other children can enjoy something nice at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    adult = f["adult"]
    task = f["task"]
    tool = f["tool_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {helper.id}, two children who worked together, and {adult.label_word} who encouraged them. They wanted to do something kind for other people."
        ),
        (
            f"What was {lead.id}'s kind notion?",
            f"{lead.id} had the idea to move {task.object_phrase} to {task.goal_label}. {task.child_benefit.capitalize()}, so the notion was about helping others, not just about having fun."
        ),
        (
            f"Why could {lead.id} not finish the job alone?",
            f"{lead.id} tried first, but the job was too hard for one child. The story shows that caring is important, yet some kind plans still need teamwork and the right help."
        ),
        (
            f"How did {helper.id} and the grown-up help?",
            f"{helper.id} joined the work instead of walking past, and the grown-up brought {tool.phrase}. With two children and a useful tool, the hard job became possible."
        ),
    ]
    if f.get("task_done"):
        qa.append((
            "How did the story end?",
            f"It ended happily: {task.result_image}. The ending proves that their teamwork changed the place in a warm, useful way."
        ))
        qa.append((
            "What is the moral of the story?",
            f"The moral is that a kind idea grows stronger when people help one another. Good hearts matter, and shared work can turn a hopeful plan into something real."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "kindness"} | set(world.facts["task"].tags) | set(world.facts["tool_cfg"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        flags = [name for name, on in (
            ("movable", e.movable),
            ("heavy", e.heavy),
            ("carrying", e.carrying),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: phase={world.facts.get('phase')} heavy_need={world.facts.get('heavy_need')} "
                 f"tool_support={world.facts.get('tool_support')} tool_wheels={world.facts.get('tool_wheels')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        task="garden_bed",
        tool="wagon",
        helper="sora",
        lead_name="Nia",
        lead_gender="girl",
        adult="mother",
        seed=101,
    ),
    StoryParams(
        task="book_corner",
        tool="wide_strap",
        helper="milo",
        lead_name="Owen",
        lead_gender="boy",
        adult="father",
        seed=102,
    ),
    StoryParams(
        task="stage_banner",
        tool="rolling_cart",
        helper="ruth",
        lead_name="Maya",
        lead_gender="girl",
        adult="mother",
        seed=103,
    ),
]


ASP_RULES = r"""
valid(Task, Tool) :- task(Task), tool(Tool), sense(Tool, S), sense_min(M), S >= M,
                     heavy_need(Task, Need), support(Tool, Sup), Need <= 2 + Sup,
                     not needs_wheels(Task).
valid(Task, Tool) :- task(Task), tool(Tool), sense(Tool, S), sense_min(M), S >= M,
                     heavy_need(Task, Need), support(Tool, Sup), Need <= 2 + Sup,
                     needs_wheels(Task), wheels(Tool).

team_strength(Task, Tool, 2 + Sup) :- valid(Task, Tool), support(Tool, Sup).
successful(Task, Tool) :- valid(Task, Tool), team_strength(Task, Tool, Total),
                          heavy_need(Task, Need), Total >= Need.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("heavy_need", task_id, task.heavy_need))
        if task.needs_wheels:
            lines.append(asp.fact("needs_wheels", task_id))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("support", tool_id, tool.support))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.wheels:
            lines.append(asp.fact("wheels", tool_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_successful_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show successful/2."))
    return sorted(set(asp.atoms(model, "successful")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - py_set:
            print("  only in clingo:", sorted(clingo_set - py_set))
        if py_set - clingo_set:
            print("  only in python:", sorted(py_set - clingo_set))

    if set(asp_successful_combos()) == py_set:
        print("OK: every valid combo is also successful in the ASP model.")
    else:
        rc = 1
        print("MISMATCH: some valid combos are not successful in ASP.")

    # Smoke test: ordinary generation must not crash.
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"VERIFY GENERATION FAILURE: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming teamwork storyworld. Unspecified choices are chosen at random (seeded)."
    )
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--lead-name")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.task and args.tool:
        task = TASKS[args.task]
        tool = TOOLS[args.tool]
        if not valid_combo(task, tool):
            raise StoryError(explain_rejection(task, tool))

    combos = [
        combo for combo in valid_combos()
        if (args.task is None or combo[0] == args.task)
        and (args.tool is None or combo[1] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    task_id, tool_id = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead_name or rng.choice(LEAD_NAMES[lead_gender])
    helper_choices = sorted(HELPERS)
    if args.helper is not None:
        helper_id = args.helper
    else:
        helper_id = rng.choice(helper_choices)
    if HELPERS[helper_id].name == lead_name:
        other = [hid for hid in helper_choices if HELPERS[hid].name != lead_name]
        if not other:
            raise StoryError("(No valid helper remains after avoiding duplicate names.)")
        helper_id = rng.choice(other)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        task=task_id,
        tool=tool_id,
        helper=helper_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        adult=adult,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.task not in TASKS:
        raise StoryError(f"(Unknown task: {params.task})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.adult not in {"mother", "father"}:
        raise StoryError(f"(Unknown adult type: {params.adult})")
    task = TASKS[params.task]
    tool = TOOLS[params.tool]
    if not valid_combo(task, tool):
        raise StoryError(explain_rejection(task, tool))

    helper = HELPERS[params.helper]
    if helper.name == params.lead_name:
        raise StoryError("(Lead and helper must not have the same name.)")

    world = tell(
        task=task,
        tool=tool,
        helper_profile=helper,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/2.\n#show successful/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (task, tool) combos:\n")
        for task_id, tool_id in combos:
            print(f"  {task_id:12} {tool_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.lead_name}: {p.task} with {p.tool} and {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
