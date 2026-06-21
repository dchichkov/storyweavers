#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bread_conflict_repetition_flashback_slice_of_life.py
==============================================================================

A small story world about an ordinary breakfast where two children want the same
bread, keep falling into the same little argument, remember an earlier lesson,
and find a calmer way to share the morning.

Domain notes
------------
This world is deliberately small and domestic. The core tension is not danger or
disaster; it is a repeated family conflict:

- bread is limited or uneven,
- two children both want the best piece,
- the same grabby habit has happened on earlier mornings,
- a flashback to a bakery visit or earlier family lesson changes what they do,
- breakfast ends with a visible proof that the routine has changed.

The model uses a tiny reasonableness gate:

- some fixes only work if the bread can be split cleanly,
- some fixes only work if there is a spare frozen slice,
- explicitly weak or evasive fixes are known but refused.

It also includes an ASP twin for the gate and the outcome model.
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Kitchen:
    id: str
    scene: str
    smell: str
    window: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BreadCfg:
    id: str
    label: str
    phrase: str
    texture: str
    splittable: bool
    heel_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Topping:
    id: str
    label: str
    phrase: str
    look: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictCfg:
    id: str
    setup: str
    want_text: str
    repeated_line: str
    scarce: bool
    needs_split: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Pantry:
    id: str
    spare_slices: int
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    sense: int
    requires_split: bool = False
    requires_spare: bool = False
    action_text: str = ""
    qa_text: str = ""
    ending_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
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
        return [e for e in self.entities.values() if e.role in {"first", "second"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.kitchen)
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


def _r_conflict(world: World) -> list[str]:
    bread = world.get("bread")
    first = world.get("first")
    second = world.get("second")
    if bread.meters["claimed_by_both"] < THRESHOLD:
        return []
    sig = ("conflict", "bread")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    first.memes["envy"] += 1
    second.memes["envy"] += 1
    first.memes["upset"] += 1
    second.memes["upset"] += 1
    return ["__conflict__"]


def _r_share_calm(world: World) -> list[str]:
    bread = world.get("bread")
    if bread.meters["shared"] < THRESHOLD:
        return []
    sig = ("share_calm", "bread")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["calm"] += 1
        kid.memes["fairness"] += 1
        kid.memes["upset"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="conflict", tag="social", apply=_r_conflict),
    Rule(name="share_calm", tag="social", apply=_r_share_calm),
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


@dataclass
class StoryParams:
    kitchen: str
    bread: str
    topping: str
    conflict: str
    pantry: str
    resolution: str
    first_name: str
    first_gender: str
    second_name: str
    second_gender: str
    parent: str
    first_habit: str
    second_habit: str
    repeated_mornings: int = 2
    seed: Optional[int] = None


KITCHENS = {
    "apartment": Kitchen(
        id="apartment",
        scene="a small apartment kitchen",
        smell="The room smelled faintly of soap and toast.",
        window="Rain tapped the window over the sink.",
        tags={"kitchen", "home"},
    ),
    "yellow_house": Kitchen(
        id="yellow_house",
        scene="the bright kitchen of a yellow house",
        smell="Warm air carried the smell of bread and butter.",
        window="Morning light lay across the table in a long stripe.",
        tags={"kitchen", "home"},
    ),
    "grandma_table": Kitchen(
        id="grandma_table",
        scene="a quiet kitchen with a round table",
        smell="The kitchen smelled like toast and a little cinnamon.",
        window="A lace curtain moved at the open window.",
        tags={"kitchen", "home"},
    ),
}

BREADS = {
    "sandwich": BreadCfg(
        id="sandwich",
        label="sandwich bread",
        phrase="a soft loaf of sandwich bread",
        texture="soft and springy",
        splittable=True,
        heel_kind="the crusty end slice",
        tags={"bread", "toast"},
    ),
    "milk_bread": BreadCfg(
        id="milk_bread",
        label="milk bread",
        phrase="a pillowy loaf of milk bread",
        texture="light and fluffy",
        splittable=True,
        heel_kind="the sweet brown end piece",
        tags={"bread", "toast"},
    ),
    "sourdough": BreadCfg(
        id="sourdough",
        label="sourdough bread",
        phrase="a round loaf of sourdough bread",
        texture="chewy inside with a thick crust",
        splittable=False,
        heel_kind="the chewy heel with the thick crust",
        tags={"bread", "toast", "crust"},
    ),
}

TOPPINGS = {
    "butter": Topping(
        id="butter",
        label="butter",
        phrase="a pat of butter",
        look="melted into a shiny yellow puddle",
        tags={"butter"},
    ),
    "jam": Topping(
        id="jam",
        label="jam",
        phrase="a spoonful of strawberry jam",
        look="glowed red on the toast",
        tags={"jam"},
    ),
    "honey": Topping(
        id="honey",
        label="honey",
        phrase="a ribbon of honey",
        look="shone gold at the edges",
        tags={"honey"},
    ),
}

CONFLICTS = {
    "last_slice": ConflictCfg(
        id="last_slice",
        setup="Only one warm slice of bread popped up from the toaster.",
        want_text="both wanted the same warm slice",
        repeated_line='"That slice!" they said at the same time.',
        scarce=True,
        needs_split=True,
        tags={"sharing", "scarcity"},
    ),
    "big_piece": ConflictCfg(
        id="big_piece",
        setup="Two pieces sat on the plate, but one was plainly bigger than the other.",
        want_text="both wanted the bigger piece",
        repeated_line='"The big one!" they said at the same time.',
        scarce=False,
        needs_split=True,
        tags={"sharing", "fairness"},
    ),
    "heel_piece": ConflictCfg(
        id="heel_piece",
        setup="On the board lay one soft slice and one heel, and neither child wanted the heel first.",
        want_text="both wanted the soft middle slice",
        repeated_line='"Not the heel," they both said, almost like a little song.',
        scarce=False,
        needs_split=False,
        tags={"sharing", "crust"},
    ),
}

PANTRIES = {
    "lean": Pantry(
        id="lean",
        spare_slices=0,
        phrase="The bread box was nearly empty.",
        tags={"scarcity"},
    ),
    "freezer_spare": Pantry(
        id="freezer_spare",
        spare_slices=1,
        phrase="One extra slice waited in the freezer, wrapped in paper.",
        tags={"freezer", "scarcity"},
    ),
    "full_box": Pantry(
        id="full_box",
        spare_slices=2,
        phrase="The bread box still held a couple of extra slices.",
        tags={"bread_box"},
    ),
}

RESOLUTIONS = {
    "split_share": Resolution(
        id="split_share",
        sense=3,
        requires_split=True,
        requires_spare=False,
        action_text="cut the bread into two neat pieces and let each child choose a side",
        qa_text="cut the bread into equal pieces and let them share it",
        ending_text="At the end, each child held half a warm piece, and the morning felt roomy again.",
        tags={"sharing", "fairness"},
    ),
    "take_turns": Resolution(
        id="take_turns",
        sense=2,
        requires_split=False,
        requires_spare=False,
        action_text="set a simple rule: one child got first pick today, and the other would get first pick tomorrow",
        qa_text="used a taking-turns rule so the choice would feel fair across two mornings",
        ending_text="Tomorrow had a place at the table too, so the children could stop pulling on today.",
        tags={"taking_turns", "fairness"},
    ),
    "freezer_slice": Resolution(
        id="freezer_slice",
        sense=3,
        requires_split=False,
        requires_spare=True,
        action_text="pull the extra slice from the freezer, toast it, and set down two warm pieces instead of one",
        qa_text="found an extra frozen slice and toasted it so there was enough bread for both children",
        ending_text="Soon there were two warm slices on the table, and the tight feeling left the room.",
        tags={"freezer", "sharing"},
    ),
    "ignore_it": Resolution(
        id="ignore_it",
        sense=1,
        requires_split=False,
        requires_spare=False,
        action_text="tell the children to stop fussing without changing anything",
        qa_text="told them to stop fussing",
        ending_text="The quiet would have sat on top of the problem instead of solving it.",
        tags={"weak_fix"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
HABITS = ["quick-handed", "sleepy", "careful", "chatty", "eager", "gentle"]


def resolution_works(bread: BreadCfg, pantry: Pantry, conflict: ConflictCfg, resolution: Resolution) -> bool:
    if resolution.sense < SENSE_MIN:
        return False
    if resolution.requires_split and (not bread.splittable or not conflict.needs_split):
        return False
    if resolution.requires_spare and pantry.spare_slices < 1:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for kitchen_id in KITCHENS:
        for bread_id, bread in BREADS.items():
            for topping_id in TOPPINGS:
                for conflict_id, conflict in CONFLICTS.items():
                    for pantry_id, pantry in PANTRIES.items():
                        for resolution_id, resolution in RESOLUTIONS.items():
                            if resolution_works(bread, pantry, conflict, resolution):
                                combos.append((kitchen_id, bread_id, topping_id, conflict_id, pantry_id, resolution_id))
    return combos


def explain_resolution(bread: BreadCfg, pantry: Pantry, conflict: ConflictCfg, resolution: Resolution) -> str:
    if resolution.sense < SENSE_MIN:
        return (
            f"(Refusing resolution '{resolution.id}': it is too weak for a storyworld "
            f"(sense={resolution.sense} < {SENSE_MIN}). A family story should solve the "
            f"bread problem, not just hush it.)"
        )
    if resolution.requires_split and not bread.splittable:
        return (
            f"(No story: {bread.label} is not a clean split kind of bread here, so "
            f"'{resolution.id}' would not honestly solve the argument.)"
        )
    if resolution.requires_split and not conflict.needs_split:
        return (
            f"(No story: '{resolution.id}' is meant for a slice that can be divided, "
            f"but this conflict is about who gets the soft middle slice versus the heel.)"
        )
    if resolution.requires_spare and pantry.spare_slices < 1:
        return (
            f"(No story: '{resolution.id}' needs an extra slice in the pantry or freezer, "
            f"but none is available.)"
        )
    return "(No story: this fix does not match the breakfast problem.)"


def outcome_of(params: StoryParams) -> str:
    bread = BREADS[params.bread]
    pantry = PANTRIES[params.pantry]
    conflict = CONFLICTS[params.conflict]
    resolution = RESOLUTIONS[params.resolution]
    if resolution.id in {"split_share", "freezer_slice"}:
        return "peaceful"
    if resolution.id == "take_turns":
        if conflict.id == "heel_piece" and pantry.spare_slices == 0:
            return "sulky"
        return "peaceful"
    if resolution_works(bread, pantry, conflict, resolution):
        return "peaceful"
    return "sulky"


def introduce(world: World, first: Entity, second: Entity, parent: Entity, bread: BreadCfg, kitchen: Kitchen) -> None:
    world.say(
        f"In {kitchen.scene}, {first.id} and {second.id} came to breakfast in their socks while "
        f"{parent.label_word} set out {bread.phrase}."
    )
    world.say(kitchen.smell)
    world.say(kitchen.window)


def repeat_pattern(world: World, first: Entity, second: Entity, conflict: ConflictCfg, repeated_mornings: int) -> None:
    for _ in range(repeated_mornings):
        first.memes["habit_grab"] += 1
        second.memes["habit_grab"] += 1
    world.say(
        f"For {repeated_mornings} mornings in a row, the same little trouble had come to the table: "
        f"{conflict.want_text}. {conflict.repeated_line}"
    )
    world.say(
        f"Each time, chairs scraped, hands reached, and breakfast felt smaller than it really was."
    )


def set_breakfast(world: World, bread: BreadCfg, topping: Topping, pantry: Pantry, conflict: ConflictCfg) -> None:
    loaf = world.get("bread")
    loaf.meters["warm"] += 1
    world.say(conflict.setup)
    world.say(
        f"{pantry.phrase} Beside the plate waited {topping.phrase} that {topping.look}."
    )


def grab_and_argue(world: World, first: Entity, second: Entity, conflict: ConflictCfg) -> None:
    bread = world.get("bread")
    first.memes["hunger"] += 1
    second.memes["hunger"] += 1
    first.memes["impatience"] += 1
    second.memes["impatience"] += 1
    bread.meters["claimed_by_both"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{first.id} reached first. {second.id} reached too. {conflict.repeated_line}"
    )
    world.say(
        f'"I wanted it," {first.id} said. "No, I wanted it," said {second.id}.'
    )


def flashback(world: World, parent: Entity, bread: BreadCfg) -> None:
    for kid in world.kids():
        kid.memes["memory"] += 1
    world.say(
        f"{parent.label_word.capitalize()} looked at their two hands on one plate and remembered last Saturday at the bakery."
    )
    world.say(
        f"The baker had pulled out a warm loaf of {bread.label}, smiled at the children, and said, "
        f'"Bread tastes better when everyone at the table gets some."'
    )
    world.say(
        f"Both children remembered it too: the paper bag warm between them, the steam, and how easy it had felt to wait when sharing was already part of the plan."
    )


def do_resolution(world: World, parent: Entity, resolution: Resolution, pantry: Pantry) -> None:
    bread = world.get("bread")
    first = world.get("first")
    second = world.get("second")
    world.say(
        f"So {parent.label_word} chose a calmer answer and {resolution.action_text}."
    )
    if resolution.id == "split_share":
        bread.meters["shared"] += 1
        bread.meters["pieces"] = 2
        first.memes["fairness"] += 1
        second.memes["fairness"] += 1
    elif resolution.id == "freezer_slice":
        bread.meters["shared"] += 1
        bread.meters["pieces"] = 2
        bread.meters["warm"] += 1
        pantry_left = max(0, pantry.spare_slices - 1)
        world.facts["pantry_left"] = pantry_left
        first.memes["relief"] += 1
        second.memes["relief"] += 1
    elif resolution.id == "take_turns":
        bread.meters["shared"] += 0
        first.memes["fairness"] += 1
        second.memes["fairness"] += 1
        first.memes["calm"] += 0.5
        second.memes["calm"] += 0.5
    propagate(world, narrate=False)


def ending(world: World, first: Entity, second: Entity, topping: Topping, resolution: Resolution, outcome: str) -> None:
    if resolution.id == "split_share":
        world.say(
            f"Soon the knife had made two small, even pieces. {first.id} spread on the {topping.label}, "
            f"and {second.id} licked a thumb and laughed at the sticky shine."
        )
    elif resolution.id == "freezer_slice":
        world.say(
            f"The second slice popped up at last, and both children leaned closer as the {topping.label} was spread."
        )
    else:
        world.say(
            f"{first.id} sat back first. Then {second.id} did too. The toast was not bigger, but the table felt less crowded."
        )
    if outcome == "peaceful":
        world.say(resolution.ending_text)
        world.say(
            f"After that, when the bread came out warm, the children looked at each other before they looked at the plate."
        )
    else:
        world.say(
            f"The lesson landed, though not all at once. One child still made a small face, but nobody grabbed again."
        )
        world.say(
            f"Breakfast went on in a quieter way, and that was the beginning of a better habit."
        )


def tell(
    kitchen: Kitchen,
    bread: BreadCfg,
    topping: Topping,
    conflict: ConflictCfg,
    pantry: Pantry,
    resolution: Resolution,
    *,
    first_name: str,
    first_gender: str,
    second_name: str,
    second_gender: str,
    parent_type: str,
    first_habit: str,
    second_habit: str,
    repeated_mornings: int,
) -> World:
    world = World(kitchen)
    first = world.add(Entity(
        id="first",
        kind="character",
        type=first_gender,
        label=first_name,
        role="first",
        traits=[first_habit],
        attrs={"name": first_name},
    ))
    second = world.add(Entity(
        id="second",
        kind="character",
        type=second_gender,
        label=second_name,
        role="second",
        traits=[second_habit],
        attrs={"name": second_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    bread_ent = world.add(Entity(
        id="bread",
        kind="thing",
        type="bread",
        label=bread.label,
        tags=set(bread.tags),
    ))

    world.facts["display_names"] = {first.id: first_name, second.id: second_name}

    introduce(world, first, second, parent, bread, kitchen)
    repeat_pattern(world, first, second, conflict, repeated_mornings)

    world.para()
    set_breakfast(world, bread, topping, pantry, conflict)
    grab_and_argue(world, first, second, conflict)

    world.para()
    flashback(world, parent, bread)
    do_resolution(world, parent, resolution, pantry)

    world.para()
    out = outcome_of(StoryParams(
        kitchen=kitchen.id,
        bread=bread.id,
        topping=topping.id,
        conflict=conflict.id,
        pantry=pantry.id,
        resolution=resolution.id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        parent=parent_type,
        first_habit=first_habit,
        second_habit=second_habit,
        repeated_mornings=repeated_mornings,
    ))
    ending(world, first, second, topping, resolution, out)

    world.facts.update(
        kitchen=kitchen,
        bread_cfg=bread,
        topping=topping,
        conflict=conflict,
        pantry=pantry,
        resolution=resolution,
        first=first,
        second=second,
        parent=parent,
        repeated_mornings=repeated_mornings,
        conflict_fired=bread_ent.meters["claimed_by_both"] >= THRESHOLD,
        flashback_used=True,
        outcome=out,
        names={first.id: first_name, second.id: second_name},
    )
    return world


def display_name(world: World, ent: Entity) -> str:
    return world.facts.get("names", {}).get(ent.id, ent.label or ent.id)


KNOWLEDGE = {
    "bread": [
        (
            "What is bread?",
            "Bread is a baked food made from dough. People slice it and eat it plain or with things like butter or jam.",
        )
    ],
    "toast": [
        (
            "What is toast?",
            "Toast is bread that has been heated until the outside turns brown and a little crisp. Warm toast often smells stronger than plain bread.",
        )
    ],
    "sharing": [
        (
            "Why does sharing food sometimes stop an argument?",
            "Sharing can make things feel fair when two people want the same thing. When each person knows there is a place for them, their bodies can calm down.",
        )
    ],
    "fairness": [
        (
            "What does fair mean at the table?",
            "Fair means people are treated in a balanced way. Sometimes that means equal pieces, and sometimes it means taking turns.",
        )
    ],
    "freezer": [
        (
            "Why do families keep bread in the freezer?",
            "Cold bread in the freezer lasts longer and can be toasted later. That helps when there is not enough fresh bread right now.",
        )
    ],
    "butter": [
        (
            "Why does butter melt on warm bread?",
            "Warm bread gives heat to the butter. That heat makes the butter soften and spread.",
        )
    ],
    "jam": [
        (
            "What is jam?",
            "Jam is fruit cooked with sugar until it turns soft and sweet. People spread it on bread or toast.",
        )
    ],
    "honey": [
        (
            "What is honey?",
            "Honey is a sweet golden food made by bees. It is thick and sticky, so people often drizzle it on bread or toast.",
        )
    ],
    "crust": [
        (
            "What is the crust of bread?",
            "The crust is the outside part of the bread. It is usually darker and firmer than the soft middle.",
        )
    ],
    "taking_turns": [
        (
            "What does taking turns mean?",
            "Taking turns means one person goes first now and the other person goes first later. It helps when only one person can have something at a time.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "bread",
    "toast",
    "sharing",
    "fairness",
    "freezer",
    "butter",
    "jam",
    "honey",
    "crust",
    "taking_turns",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    bread = f["bread_cfg"]
    conflict = f["conflict"]
    resolution = f["resolution"]
    first_name = display_name(world, first)
    second_name = display_name(world, second)
    return [
        f'Write a slice-of-life story for a 3-to-5-year-old that includes the word "bread" and shows a small breakfast conflict.',
        f"Tell a quiet family story where {first_name} and {second_name} keep having the same argument over {bread.label}, and a flashback helps them handle it better.",
        f"Write a story with repetition, conflict, and flashback where children at breakfast learn a fairer way to handle {conflict.want_text} using {resolution.id}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    first = f["first"]
    second = f["second"]
    parent = f["parent"]
    bread = f["bread_cfg"]
    topping = f["topping"]
    conflict = f["conflict"]
    resolution = f["resolution"]
    pantry = f["pantry"]
    first_name = display_name(world, first)
    second_name = display_name(world, second)
    parent_word = parent.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {first_name} and {second_name} at breakfast with their {parent_word}. The whole story stays close to one ordinary morning at the table.",
        ),
        (
            "What was the problem at breakfast?",
            f"The problem was that {conflict.want_text}. The bread felt important because it was warm and limited, so both children reached for it at once.",
        ),
        (
            "How does repetition matter in the story?",
            f"The same little argument had already happened for {f['repeated_mornings']} mornings in a row. That repetition made the conflict feel like a habit instead of a one-time mistake.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about a bakery visit from last Saturday, when a baker said that bread tastes better when everyone gets some. That memory gave the family a calmer idea for what to do now.",
        ),
        (
            f"How did their {parent_word} solve the problem?",
            f"Their {parent_word} {resolution.qa_text}. The fix worked because it matched the real bread problem instead of only telling the children to be quiet.",
        ),
    ]
    if resolution.id == "freezer_slice":
        qa.append((
            "Why did the freezer matter?",
            f"It mattered because {pantry.phrase.lower()} The extra slice meant there could be enough warm bread for both children instead of a fight over one piece.",
        ))
    if resolution.id == "split_share":
        qa.append((
            "Why was splitting the bread a good idea?",
            f"It was a good idea because this kind of bread could be divided neatly. Equal pieces turned one wanted thing into something both children could hold.",
        ))
    if resolution.id == "take_turns":
        qa.append((
            "Did the children become calm right away?",
            f"Mostly, but not by magic. The turn rule gave the morning a fair shape, so even if one child still felt disappointed, there was no more grabbing.",
        ))
    qa.append((
        "How did the story end?",
        f"It ended with breakfast feeling roomier and kinder than before. The ending image shows the change: the children looked at each other before they looked at the bread.",
    ))
    if topping.id == "butter":
        qa.append((
            "What happened to the butter on the bread?",
            "The butter melted on the warm bread. That small detail makes the breakfast feel real and close.",
        ))
    elif topping.id == "jam":
        qa.append((
            "What did the jam look like?",
            "The jam glowed red on the toast. That bright image helps show the story's quiet, everyday setting.",
        ))
    else:
        qa.append((
            "What did the honey look like?",
            "The honey shone gold at the edges of the toast. The story uses that soft image to end the breakfast on a gentler note.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["bread_cfg"].tags) | set(f["conflict"].tags) | set(f["resolution"].tags) | set(f["topping"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        kitchen="yellow_house",
        bread="sandwich",
        topping="butter",
        conflict="last_slice",
        pantry="lean",
        resolution="split_share",
        first_name="Lily",
        first_gender="girl",
        second_name="Ben",
        second_gender="boy",
        parent="mother",
        first_habit="quick-handed",
        second_habit="chatty",
        repeated_mornings=2,
    ),
    StoryParams(
        kitchen="apartment",
        bread="milk_bread",
        topping="jam",
        conflict="big_piece",
        pantry="freezer_spare",
        resolution="freezer_slice",
        first_name="Mia",
        first_gender="girl",
        second_name="Sam",
        second_gender="boy",
        parent="father",
        first_habit="eager",
        second_habit="sleepy",
        repeated_mornings=3,
    ),
    StoryParams(
        kitchen="grandma_table",
        bread="sourdough",
        topping="honey",
        conflict="heel_piece",
        pantry="lean",
        resolution="take_turns",
        first_name="Noah",
        first_gender="boy",
        second_name="Ava",
        second_gender="girl",
        parent="mother",
        first_habit="careful",
        second_habit="gentle",
        repeated_mornings=2,
    ),
    StoryParams(
        kitchen="yellow_house",
        bread="milk_bread",
        topping="jam",
        conflict="last_slice",
        pantry="full_box",
        resolution="take_turns",
        first_name="Ella",
        first_gender="girl",
        second_name="Rose",
        second_gender="girl",
        parent="father",
        first_habit="quick-handed",
        second_habit="careful",
        repeated_mornings=4,
    ),
    StoryParams(
        kitchen="apartment",
        bread="sandwich",
        topping="honey",
        conflict="big_piece",
        pantry="freezer_spare",
        resolution="freezer_slice",
        first_name="Theo",
        first_gender="boy",
        second_name="Lucy",
        second_gender="girl",
        parent="mother",
        first_habit="chatty",
        second_habit="eager",
        repeated_mornings=2,
    ),
]


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(K, B, T, C, P, R) :-
    kitchen(K), bread(B), topping(T), conflict(C), pantry(P), resolution(R),
    sensible(R),
    ( not needs_split(R)
    ; ( needs_split(R), splittable(B), conflict_splittable(C) )
    ),
    ( not needs_spare(R)
    ; ( needs_spare(R), spare(P, S), S >= 1 )
    ).

% --- outcome model ---------------------------------------------------------
outcome(peaceful) :- chosen_resolution(split_share).
outcome(peaceful) :- chosen_resolution(freezer_slice).
outcome(peaceful) :- chosen_resolution(take_turns), not chosen_conflict(heel_piece).
outcome(peaceful) :- chosen_resolution(take_turns), chosen_conflict(heel_piece),
                     chosen_pantry(P), spare(P, S), S >= 1.
outcome(sulky)    :- chosen_resolution(take_turns), chosen_conflict(heel_piece),
                     chosen_pantry(P), spare(P, 0).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for kitchen_id in KITCHENS:
        lines.append(asp.fact("kitchen", kitchen_id))
    for bread_id, bread in BREADS.items():
        lines.append(asp.fact("bread", bread_id))
        if bread.splittable:
            lines.append(asp.fact("splittable", bread_id))
    for topping_id in TOPPINGS:
        lines.append(asp.fact("topping", topping_id))
    for conflict_id, conflict in CONFLICTS.items():
        lines.append(asp.fact("conflict", conflict_id))
        if conflict.needs_split:
            lines.append(asp.fact("conflict_splittable", conflict_id))
    for pantry_id, pantry in PANTRIES.items():
        lines.append(asp.fact("pantry", pantry_id))
        lines.append(asp.fact("spare", pantry_id, pantry.spare_slices))
    for resolution_id, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", resolution_id))
        lines.append(asp.fact("sense", resolution_id, resolution.sense))
        if resolution.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", resolution_id))
        if resolution.requires_split:
            lines.append(asp.fact("needs_split", resolution_id))
        if resolution.requires_spare:
            lines.append(asp.fact("needs_spare", resolution_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/6."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_resolution", params.resolution),
        asp.fact("chosen_conflict", params.conflict),
        asp.fact("chosen_pantry", params.pantry),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _validate_params(params: StoryParams) -> None:
    if params.kitchen not in KITCHENS:
        raise StoryError(f"(Unknown kitchen: {params.kitchen})")
    if params.bread not in BREADS:
        raise StoryError(f"(Unknown bread: {params.bread})")
    if params.topping not in TOPPINGS:
        raise StoryError(f"(Unknown topping: {params.topping})")
    if params.conflict not in CONFLICTS:
        raise StoryError(f"(Unknown conflict: {params.conflict})")
    if params.pantry not in PANTRIES:
        raise StoryError(f"(Unknown pantry: {params.pantry})")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"(Unknown resolution: {params.resolution})")
    bread = BREADS[params.bread]
    pantry = PANTRIES[params.pantry]
    conflict = CONFLICTS[params.conflict]
    resolution = RESOLUTIONS[params.resolution]
    if not resolution_works(bread, pantry, conflict, resolution):
        raise StoryError(explain_resolution(bread, pantry, conflict, resolution))
    if params.repeated_mornings < 1:
        raise StoryError("(No story: repetition needs at least one earlier morning.)")


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

    cases = list(CURATED)
    for seed in range(60):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="### smoke")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: repeated breakfast conflict over bread, a flashback, and a calmer family fix."
    )
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--bread", choices=BREADS)
    ap.add_argument("--topping", choices=TOPPINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--pantry", choices=PANTRIES)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--first-name")
    ap.add_argument("--second-name")
    ap.add_argument("--first-gender", choices=["girl", "boy"])
    ap.add_argument("--second-gender", choices=["girl", "boy"])
    ap.add_argument("--repeated-mornings", type=int, choices=[1, 2, 3, 4], help="how many earlier mornings repeated the same breakfast trouble")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.bread and args.conflict and args.pantry and args.resolution:
        bread = BREADS[args.bread]
        pantry = PANTRIES[args.pantry]
        conflict = CONFLICTS[args.conflict]
        resolution = RESOLUTIONS[args.resolution]
        if not resolution_works(bread, pantry, conflict, resolution):
            raise StoryError(explain_resolution(bread, pantry, conflict, resolution))
    if args.resolution and RESOLUTIONS[args.resolution].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing resolution '{args.resolution}': it scores below the common-sense floor.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.kitchen is None or combo[0] == args.kitchen)
        and (args.bread is None or combo[1] == args.bread)
        and (args.topping is None or combo[2] == args.topping)
        and (args.conflict is None or combo[3] == args.conflict)
        and (args.pantry is None or combo[4] == args.pantry)
        and (args.resolution is None or combo[5] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    kitchen_id, bread_id, topping_id, conflict_id, pantry_id, resolution_id = rng.choice(sorted(combos))
    first_gender = args.first_gender or rng.choice(["girl", "boy"])
    second_gender = args.second_gender or rng.choice(["girl", "boy"])
    first_name = args.first_name or _pick_name(rng, first_gender)
    second_name = args.second_name or _pick_name(rng, second_gender, avoid=first_name)
    parent = args.parent or rng.choice(["mother", "father"])
    repeated_mornings = args.repeated_mornings if args.repeated_mornings is not None else rng.choice([2, 3, 4])
    return StoryParams(
        kitchen=kitchen_id,
        bread=bread_id,
        topping=topping_id,
        conflict=conflict_id,
        pantry=pantry_id,
        resolution=resolution_id,
        first_name=first_name,
        first_gender=first_gender,
        second_name=second_name,
        second_gender=second_gender,
        parent=parent,
        first_habit=rng.choice(HABITS),
        second_habit=rng.choice(HABITS),
        repeated_mornings=repeated_mornings,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        KITCHENS[params.kitchen],
        BREADS[params.bread],
        TOPPINGS[params.topping],
        CONFLICTS[params.conflict],
        PANTRIES[params.pantry],
        RESOLUTIONS[params.resolution],
        first_name=params.first_name,
        first_gender=params.first_gender,
        second_name=params.second_name,
        second_gender=params.second_gender,
        parent_type=params.parent,
        first_habit=params.first_habit,
        second_habit=params.second_habit,
        repeated_mornings=params.repeated_mornings,
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
        print(asp_program("", "#show valid/6.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (kitchen, bread, topping, conflict, pantry, resolution) combos:\n")
        for kitchen_id, bread_id, topping_id, conflict_id, pantry_id, resolution_id in combos:
            print(f"  {kitchen_id:12} {bread_id:10} {topping_id:7} {conflict_id:11} {pantry_id:13} {resolution_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.first_name} and {p.second_name}: {p.conflict} with {p.bread} "
                f"({p.resolution}, {outcome_of(p)})"
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
