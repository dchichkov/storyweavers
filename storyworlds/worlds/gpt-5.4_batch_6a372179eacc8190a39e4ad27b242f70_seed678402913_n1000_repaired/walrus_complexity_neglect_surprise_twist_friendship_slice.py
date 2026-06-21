#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py
=======================================================================================

A standalone storyworld about two friends making a walrus craft for a small
everyday event. The domain is "slice of life": a classroom or library project,
too much complexity, one neglected step, a drooping middle, and a friendship-led
repair that turns into a surprise twist.

The seed words are built into the world model itself:

- walrus: every story centers on a walrus craft
- complexity: one child pushes the design toward more complexity
- neglect: the turning problem comes from neglecting a basic step

The story engine keeps typed entities with physical meters and emotional memes,
checks combinations for reasonableness, and includes an inline ASP twin for the
same gate and outcome logic.

Run it
------
    python storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py
    python storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py --material clay --neglect rush_drying
    python storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py --pose storybook_stack --fix wait_and_patch
    python storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py --all
    python storyworlds/worlds/gpt-5.4/walrus_complexity_neglect_surprise_twist_friendship_slice.py --verify
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
# This file lives under storyworlds/worlds/gpt-5.4/, so we need the package dir
# (storyworlds/) on sys.path.
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
        female = {"girl", "mother", "mom", "woman", "teacher"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    event: str
    detail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    texture: str
    needs_dry: bool = False
    needs_brace: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Pose:
    id: str
    label: str
    line: str
    complexity: int
    support_need: int
    surprise_ready: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Neglect:
    id: str
    label: str
    line: str
    kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    line: str
    handles: set[str]
    preserves_pose: bool
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"maker", "friend"}]

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


def _r_soft_slump(world: World) -> list[str]:
    craft = world.get("craft")
    if craft.meters["soft"] < THRESHOLD:
        return []
    sig = ("soft_slump",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["wobble"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__slump__"]


def _r_unsupported_slump(world: World) -> list[str]:
    craft = world.get("craft")
    if craft.meters["unsupported"] < THRESHOLD:
        return []
    sig = ("unsupported_slump",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["wobble"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__slump__"]


def _r_overloaded_slump(world: World) -> list[str]:
    craft = world.get("craft")
    if craft.meters["overloaded"] < THRESHOLD:
        return []
    sig = ("overloaded_slump",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    craft.meters["wobble"] += 1
    craft.meters["crooked"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return ["__slump__"]


CAUSAL_RULES = [
    Rule(name="soft_slump", tag="physical", apply=_r_soft_slump),
    Rule(name="unsupported_slump", tag="physical", apply=_r_unsupported_slump),
    Rule(name="overloaded_slump", tag="physical", apply=_r_overloaded_slump),
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


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the classroom art table",
        event="the hallway display",
        detail="Sunlight made pale squares on the table, and the glue bottle leaned beside a cup of brushes.",
        tags={"school"},
    ),
    "library": Setting(
        id="library",
        place="the library craft corner",
        event="the reading nook shelf",
        detail="A rolling cart of books stood nearby, and the room smelled like paper and dust and crayons.",
        tags={"library"},
    ),
    "clubroom": Setting(
        id="clubroom",
        place="the after-school clubroom",
        event="family open house",
        detail="Someone had left a tray of markers uncapped, and the window showed a soft gray afternoon.",
        tags={"school"},
    ),
}

MATERIALS = {
    "clay": Material(
        id="clay",
        label="clay",
        phrase="a lump of gray clay",
        texture="cool and a little squishy",
        needs_dry=True,
        needs_brace=False,
        tags={"clay"},
    ),
    "papier_mache": Material(
        id="papier_mache",
        label="papier-mâché",
        phrase="a bowl of papier-mâché paste and strips",
        texture="sticky and floppy until it dried",
        needs_dry=True,
        needs_brace=False,
        tags={"papier_mache"},
    ),
    "cardboard": Material(
        id="cardboard",
        label="cardboard",
        phrase="cut cardboard, tape, and brown paper",
        texture="light and easy to bend",
        needs_dry=False,
        needs_brace=True,
        tags={"cardboard"},
    ),
}

POSES = {
    "sleepy": Pose(
        id="sleepy",
        label="a sleepy walrus",
        line="its chin resting low, as if it had curled up after a long swim",
        complexity=1,
        support_need=0,
        surprise_ready=True,
        tags={"sleepy"},
    ),
    "wave": Pose(
        id="wave",
        label="a waving walrus",
        line="one flipper lifted as if it were saying hello to everyone who passed",
        complexity=2,
        support_need=1,
        surprise_ready=True,
        tags={"wave"},
    ),
    "parade": Pose(
        id="parade",
        label="a parade walrus",
        line="head high, tusks forward, and both flippers posed grandly",
        complexity=3,
        support_need=1,
        surprise_ready=True,
        tags={"parade"},
    ),
    "storybook_stack": Pose(
        id="storybook_stack",
        label="a walrus balancing on a stack of books",
        line="perched on three pretend books with its nose tipped proudly upward",
        complexity=4,
        support_need=2,
        surprise_ready=False,
        tags={"books"},
    ),
}

NEGLECTS = {
    "rush_drying": Neglect(
        id="rush_drying",
        label="rushing the drying time",
        line="They were so eager to finish that they neglected the drying time and kept touching the soft shape.",
        kind="soft",
        tags={"drying", "neglect"},
    ),
    "skip_braces": Neglect(
        id="skip_braces",
        label="skipping the little braces",
        line="The tiny paper braces looked boring, so they neglected that plain step and hurried on.",
        kind="unsupported",
        tags={"support", "neglect"},
    ),
    "ignore_simple_shape": Neglect(
        id="ignore_simple_shape",
        label="neglecting the simple shape underneath",
        line="The design gained more and more complexity, and they neglected the plain body shape underneath all the extra pieces.",
        kind="overloaded",
        tags={"complexity", "neglect"},
    ),
}

FIXES = {
    "wait_and_patch": Fix(
        id="wait_and_patch",
        label="wait and patch",
        line="slow down, let the shape rest, and patch the soft places after a little wait",
        handles={"soft"},
        preserves_pose=True,
        tags={"patience"},
    ),
    "add_braces": Fix(
        id="add_braces",
        label="add braces",
        line="tape in two little braces and a wider base under the body",
        handles={"unsupported"},
        preserves_pose=True,
        tags={"support"},
    ),
    "simplify_to_sleepy": Fix(
        id="simplify_to_sleepy",
        label="simplify it into a sleepy walrus",
        line="smooth the lopsided parts down and turn the whole thing into a sleepy walrus with low whiskers",
        handles={"soft", "unsupported", "overloaded"},
        preserves_pose=False,
        tags={"twist"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Tess", "Ruby", "Nina", "Ava", "Mila", "Ivy"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Sam", "Leo", "Milo", "Ben", "Finn"]
TRAITS = ["patient", "practical", "steady", "gentle", "cheerful", "careful"]


def problem_kind(material: Material, pose: Pose, neglect: Neglect) -> Optional[str]:
    if neglect.kind == "soft" and material.needs_dry:
        return "soft"
    if neglect.kind == "unsupported" and (material.needs_brace or pose.support_need > 0):
        return "unsupported"
    if neglect.kind == "overloaded" and pose.complexity >= 3:
        return "overloaded"
    return None


def fix_works(problem: str, fix: Fix, pose: Pose) -> bool:
    if problem not in fix.handles:
        return False
    if fix.id == "add_braces" and pose.support_need > 1:
        return False
    if fix.id == "wait_and_patch" and pose.support_need > 1:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for material_id, material in MATERIALS.items():
            for pose_id, pose in POSES.items():
                for neglect_id, neglect in NEGLECTS.items():
                    problem = problem_kind(material, pose, neglect)
                    if not problem:
                        continue
                    if any(fix_works(problem, fix, pose) for fix in FIXES.values()):
                        combos.append((setting_id, material_id, pose_id, neglect_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    material: str
    pose: str
    neglect: str
    fix: str
    maker_name: str
    maker_gender: str
    friend_name: str
    friend_gender: str
    helper_trait: str
    grownup_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="classroom",
        material="clay",
        pose="parade",
        neglect="rush_drying",
        fix="wait_and_patch",
        maker_name="Maya",
        maker_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        helper_trait="patient",
        grownup_type="teacher",
    ),
    StoryParams(
        setting="library",
        material="cardboard",
        pose="wave",
        neglect="skip_braces",
        fix="add_braces",
        maker_name="Eli",
        maker_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        helper_trait="practical",
        grownup_type="teacher",
    ),
    StoryParams(
        setting="clubroom",
        material="papier_mache",
        pose="storybook_stack",
        neglect="ignore_simple_shape",
        fix="simplify_to_sleepy",
        maker_name="Lina",
        maker_gender="girl",
        friend_name="Milo",
        friend_gender="boy",
        helper_trait="gentle",
        grownup_type="teacher",
    ),
    StoryParams(
        setting="classroom",
        material="clay",
        pose="wave",
        neglect="rush_drying",
        fix="simplify_to_sleepy",
        maker_name="Sam",
        maker_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        helper_trait="steady",
        grownup_type="teacher",
    ),
    StoryParams(
        setting="library",
        material="cardboard",
        pose="parade",
        neglect="skip_braces",
        fix="simplify_to_sleepy",
        maker_name="Nina",
        maker_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        helper_trait="careful",
        grownup_type="teacher",
    ),
]


def explain_invalid(material: Material, pose: Pose, neglect: Neglect) -> str:
    if neglect.kind == "soft" and not material.needs_dry:
        return (
            f"(No story: {material.label} does not depend on drying time here, so "
            f"{neglect.label} would not honestly make the walrus droop.)"
        )
    if neglect.kind == "unsupported" and not (material.needs_brace or pose.support_need > 0):
        return (
            f"(No story: {pose.label} sits low enough that skipping braces would not "
            f"create a real problem.)"
        )
    if neglect.kind == "overloaded" and pose.complexity < 3:
        return (
            f"(No story: {pose.label} is simple enough that the added complexity "
            f"never becomes the central problem.)"
        )
    return "(No story: this combination does not create a sensible middle problem.)"


def explain_fix(fix: Fix, material: Material, pose: Pose, neglect: Neglect) -> str:
    problem = problem_kind(material, pose, neglect)
    if not problem:
        return explain_invalid(material, pose, neglect)
    if problem not in fix.handles:
        handled = ", ".join(sorted(fix.handles))
        return (
            f"(Refusing fix '{fix.id}': it handles {handled}, but this problem is "
            f"{problem}.)"
        )
    if fix.id == "add_braces" and pose.support_need > 1:
        return (
            "(Refusing fix 'add_braces': this pose is too top-heavy for a tiny brace "
            "repair; a bigger simplification is the sensible answer.)"
        )
    if fix.id == "wait_and_patch" and pose.support_need > 1:
        return (
            "(Refusing fix 'wait_and_patch': waiting helps soft material, but it does "
            "not solve a very top-heavy shape.)"
        )
    return "(Refusing fix: it is not a sensible repair for this scenario.)"


def final_pose_id(params: StoryParams) -> str:
    return "sleepy" if params.fix == "simplify_to_sleepy" else params.pose


def outcome_of(params: StoryParams) -> str:
    return "twist" if params.fix == "simplify_to_sleepy" else "rescued"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def _apply_neglect(world: World, material: Material, pose: Pose, neglect: Neglect) -> None:
    craft = world.get("craft")
    if neglect.kind == "soft" and material.needs_dry:
        craft.meters["soft"] += 1
    elif neglect.kind == "unsupported" and (material.needs_brace or pose.support_need > 0):
        craft.meters["unsupported"] += 1
    elif neglect.kind == "overloaded" and pose.complexity >= 3:
        craft.meters["overloaded"] += 1
    propagate(world, narrate=False)


def predict_problem(world: World, material: Material, pose: Pose, neglect: Neglect) -> dict:
    sim = world.copy()
    _apply_neglect(sim, material, pose, neglect)
    craft = sim.get("craft")
    return {
        "wobble": craft.meters["wobble"],
        "problem": problem_kind(material, pose, neglect),
    }


def introduce(world: World, maker: Entity, friend: Entity, grownup: Entity, setting: Setting) -> None:
    maker.memes["hope"] += 1
    friend.memes["hope"] += 1
    world.say(
        f"After lunch, {maker.id} and {friend.id} sat together at {setting.place} to make "
        f"a walrus for {setting.event}."
    )
    world.say(setting.detail)
    world.say(
        f"{maker.id} liked big ideas, and {friend.id} was the kind of friend who stayed close when a plan got messy."
    )
    world.say(
        f'Their {grownup.label_word}, smiling as she sorted paper scraps, said, "Make something you can be proud of."'
    )


def choose_plan(world: World, maker: Entity, friend: Entity, material: Material, pose: Pose) -> None:
    maker.memes["pride"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"They pulled over {material.phrase}. The material felt {material.texture} in their hands."
    )
    world.say(
        f'"Let\'s make {pose.label}," {maker.id} said, imagining {pose.line}.'
    )
    if pose.complexity >= 3:
        world.say(
            f"The idea had real complexity, and that made {maker.id} grin even wider."
        )
    else:
        world.say(
            f"It was a clear, friendly idea, easy to picture from nose to flippers."
        )


def build_up(world: World, maker: Entity, friend: Entity, pose: Pose) -> None:
    craft = world.get("craft")
    craft.meters["shape"] += 1
    maker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Together they pressed, folded, and pinched until the walrus body began to appear."
    )
    if pose.support_need > 0:
        world.say(
            f"The raised flippers and long tusks made the pose look lively, but they also asked the little model to hold itself very carefully."
        )
    else:
        world.say(
            f"The low, rounded body made the little walrus look calm already."
        )


def neglect_step(world: World, maker: Entity, material: Material, pose: Pose, neglect: Neglect) -> None:
    pred = predict_problem(world, material, pose, neglect)
    world.facts["predicted_problem"] = pred["problem"]
    maker.memes["eagerness"] += 1
    world.say(neglect.line)
    if pred["problem"] == "soft":
        world.say(
            f"{maker.id} wanted the walrus done before the room changed to the next activity."
        )
    elif pred["problem"] == "unsupported":
        world.say(
            f"The plain little supports did not look exciting, so they were easy to overlook."
        )
    elif pred["problem"] == "overloaded":
        world.say(
            f"By then the extra tusk curls and tiny paper books seemed more exciting than the strong shape underneath."
        )


def slump(world: World, maker: Entity, friend: Entity, pose: Pose) -> None:
    craft = world.get("craft")
    _ = pose
    if craft.meters["soft"] >= THRESHOLD:
        world.say(
            f"When {maker.id} tried to lift the walrus, one side sighed downward like warm dough."
        )
    elif craft.meters["unsupported"] >= THRESHOLD:
        world.say(
            "When they set it back on the table, the body leaned and one flipper drooped."
        )
    else:
        world.say(
            "The extra pieces pulled the middle shape off balance, and the whole walrus tilted into itself."
        )
    world.say(
        f'"Oh no," {maker.id} whispered. The surprise was not the happy kind yet.'
    )
    world.say(
        f"{friend.id} reached out with both hands to steady the little model before anything snapped off."
    )


def comfort_and_notice(world: World, maker: Entity, friend: Entity, fix: Fix) -> None:
    friend.memes["care"] += 1
    maker.memes["worry"] += 1
    friend.memes["calm"] += 1
    extra = ""
    if "patient" in friend.traits or "steady" in friend.traits:
        extra = f" {friend.id} did not laugh or blame anyone."
    world.say(
        f'"It\'s okay," {friend.id} said.{extra} "We can {fix.line}."'
    )
    world.say(
        f"For a second, the room went quiet enough for both of them to really look at what the walrus was becoming."
    )


def repair(world: World, maker: Entity, friend: Entity, pose: Pose, fix: Fix) -> None:
    craft = world.get("craft")
    if fix.id == "wait_and_patch":
        craft.meters["soft"] = 0.0
        craft.meters["wobble"] = 0.0
        craft.meters["patched"] += 1
        world.say(
            f"They set the walrus down, breathed slowly, and counted together while the soft parts rested."
        )
        world.say(
            f"Then {friend.id} held the body steady while {maker.id} patched the sagging side with careful fingers."
        )
    elif fix.id == "add_braces":
        craft.meters["unsupported"] = 0.0
        craft.meters["wobble"] = 0.0
        craft.meters["braced"] += 1
        world.say(
            f"{friend.id} cut two small braces from scrap card, and {maker.id} taped them under the body."
        )
        world.say(
            "A wider base under the belly stopped the lean and gave the flipper somewhere safe to rest."
        )
    else:
        craft.meters["soft"] = 0.0
        craft.meters["unsupported"] = 0.0
        craft.meters["overloaded"] = 0.0
        craft.meters["wobble"] = 0.0
        craft.meters["crooked"] = 0.0
        craft.meters["reshaped"] += 1
        world.say(
            f"Instead of fighting the droop, they followed it. {friend.id} smoothed the back low while {maker.id} turned the tilted nose into a sleepy chin."
        )
        world.say(
            "The twist surprised them both: the mistake was beginning to look exactly right for a resting walrus."
        )
    maker.memes["relief"] += 1
    friend.memes["relief"] += 1
    friend.memes["joy"] += 1
    if fix.preserves_pose:
        world.say(
            f"Little by little, {pose.label} came back into shape."
        )


def ending(world: World, maker: Entity, friend: Entity, grownup: Entity, pose: Pose, fix: Fix) -> None:
    final_pose = POSES["sleepy"] if fix.id == "simplify_to_sleepy" else pose
    maker.memes["gratitude"] += 1
    friend.memes["love"] += 1
    maker.memes["love"] += 1
    world.say(
        f"When their {grownup.label_word} came by, she bent down and smiled at the finished walrus."
    )
    if fix.id == "simplify_to_sleepy":
        world.say(
            f'"What a dear sleepy fellow," she said. "It looks as if he fell asleep while reading."'
        )
        world.say(
            f"{maker.id} blinked, then laughed. {friend.id} laughed too, and suddenly the surprise felt warm instead of awful."
        )
        world.say(
            f"They set the walrus on {world.setting.event}, and its low whiskers and tucked shape made everyone want to stop and look twice."
        )
    else:
        world.say(
            f'"You two kept going kindly," she said. "Now {final_pose.label} looks ready to greet the whole room."'
        )
        world.say(
            f"{maker.id} felt the worry leave {maker.pronoun('object')}. {friend.id} gave the base one last gentle tap, just to be sure."
        )
        world.say(
            f"They placed the walrus on {world.setting.event}, and it stood there as if it had always meant to make it through the hard part."
        )
    world.say(
        f"On the way to wash their hands, {maker.id} bumped shoulders with {friend.id}. The walrus was lovely, but the best part was how their friendship had held steady when the plan did not."
    )
    world.facts["final_pose"] = final_pose


def tell(
    setting: Setting,
    material: Material,
    pose: Pose,
    neglect: Neglect,
    fix: Fix,
    maker_name: str,
    maker_gender: str,
    friend_name: str,
    friend_gender: str,
    helper_trait: str,
    grownup_type: str,
) -> World:
    world = World(setting)
    maker = world.add(
        Entity(
            id=maker_name,
            kind="character",
            type=maker_gender,
            role="maker",
            traits=["imaginative"],
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=[helper_trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    craft = world.add(
        Entity(
            id="craft",
            kind="thing",
            type="walrus_craft",
            label="the walrus",
            phrase="their little walrus",
            attrs={"pose": pose.id, "material": material.id},
        )
    )

    introduce(world, maker, friend, grownup, setting)
    choose_plan(world, maker, friend, material, pose)
    world.para()
    build_up(world, maker, friend, pose)
    neglect_step(world, maker, material, pose, neglect)
    _apply_neglect(world, material, pose, neglect)
    slump(world, maker, friend, pose)
    world.para()
    comfort_and_notice(world, maker, friend, fix)
    repair(world, maker, friend, pose, fix)
    ending(world, maker, friend, grownup, pose, fix)

    world.facts.update(
        setting=setting,
        material=material,
        pose=pose,
        neglect=neglect,
        fix=fix,
        maker=maker,
        friend=friend,
        grownup=grownup,
        craft=craft,
        outcome="twist" if fix.id == "simplify_to_sleepy" else "rescued",
        problem=problem_kind(material, pose, neglect),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    material = f["material"]
    pose = f["pose"]
    neglect = f["neglect"]
    outcome = f["outcome"]
    if outcome == "twist":
        return [
            'Write a slice-of-life story for a 3-to-5-year-old that includes the words "walrus", "complexity", and "neglect".',
            f"Tell a gentle friendship story where {maker.id} and {friend.id} make a walrus from {material.label}, a neglected step makes it droop, and the mistake turns into a happy surprise.",
            f"Write a classroom craft story where {pose.label} becomes something different after {neglect.label}, and the twist leaves the friends closer than before.",
        ]
    return [
        'Write a slice-of-life story for a 3-to-5-year-old that includes the words "walrus", "complexity", and "neglect".',
        f"Tell a gentle story where two friends make {pose.label} from {material.label}, hit a small craft problem, and solve it kindly together.",
        f"Write a friendship story set around a school craft table where neglecting one plain step causes trouble, but patience and teamwork save the walrus.",
    ]


def pair_noun(maker: Entity, friend: Entity) -> str:
    if maker.type == "girl" and friend.type == "girl":
        return "two friends"
    if maker.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    friend = f["friend"]
    material = f["material"]
    pose = f["pose"]
    neglect = f["neglect"]
    fix = f["fix"]
    final_pose = f["final_pose"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(maker, friend)}, {maker.id} and {friend.id}, making a walrus together. Their friendship matters because they stay kind when the craft goes wrong.",
        ),
        (
            "What were they making?",
            f"They were making {pose.label} for {world.setting.event}. They used {material.label}, so the walrus had to be shaped with care.",
        ),
        (
            "What does the word complexity mean in this story?",
            f"Here, complexity means the plan had many parts and was harder to hold together. The walrus idea became more complicated than a plain simple shape.",
        ),
        (
            "What did neglect mean in this story?",
            f"Neglect meant they skipped or forgot a basic step that mattered. The problem came from {neglect.label}, not from being mean to each other.",
        ),
    ]
    if f["problem"] == "soft":
        qa.append(
            (
                "Why did the walrus droop?",
                f"It drooped because the material was still soft, and they had neglected the drying time. Touching and moving it too soon made the shape sag.",
            )
        )
    elif f["problem"] == "unsupported":
        qa.append(
            (
                "Why did the walrus lean over?",
                f"It leaned because the pose needed support and they skipped the braces underneath. Without that plain step, the raised parts made the body wobble.",
            )
        )
    else:
        qa.append(
            (
                "Why did the walrus tilt into itself?",
                f"It tilted because the design gained too much complexity and they neglected the simple shape underneath. The extra pieces pulled attention away from the strong body the craft needed.",
            )
        )
    if outcome == "twist":
        qa.append(
            (
                "What was the surprise twist?",
                f"The surprise twist was that the mistake helped them find a better ending. When they simplified the craft, the droop turned into {final_pose.label}, and everyone liked that version.",
            )
        )
    else:
        qa.append(
            (
                "How did they solve the problem?",
                f"They solved it by deciding to {fix.line}. That repair matched the real problem, so the walrus could keep its original pose.",
            )
        )
    qa.append(
        (
            "How did friendship help?",
            f"{friend.id} stayed calm and helped instead of blaming {maker.id}. Because they worked together, the hard middle became a warm ending instead of a ruined afternoon.",
        )
    )
    return qa


KNOWLEDGE = {
    "clay": [
        (
            "Why can clay droop before it dries?",
            "Soft clay can bend and sag if you move it too soon. It needs time to hold its shape.",
        )
    ],
    "papier_mache": [
        (
            "Why does papier-mâché need time to dry?",
            "Papier-mâché starts out wet and floppy. As it dries, it gets much firmer and stronger.",
        )
    ],
    "cardboard": [
        (
            "Why do some cardboard crafts need braces?",
            "Braces are little support pieces that help a shape stand up. They stop tall or bendy parts from tipping over.",
        )
    ],
    "support": [
        (
            "What does support mean in a craft?",
            "Support means the parts underneath that help a craft stay strong. Good support keeps it from wobbling or falling.",
        )
    ],
    "complexity": [
        (
            "Can too much complexity make a project harder?",
            "Yes. More parts can make something interesting, but they also make it easier to forget the simple strong shape underneath.",
        )
    ],
    "neglect": [
        (
            "What does neglect mean?",
            "Neglect means not paying attention to something important that needs care. In a small craft, it can mean skipping a basic step.",
        )
    ],
    "friendship": [
        (
            "What can a good friend do when a plan goes wrong?",
            "A good friend can stay kind, help fix the problem, and keep you from feeling alone. Friendship often matters most in the tricky part.",
        )
    ],
    "surprise": [
        (
            "What is a surprise twist in a story?",
            "A surprise twist is when something unexpected changes the story's direction. Sometimes a mistake leads to a better ending than anyone planned.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "clay",
    "papier_mache",
    "cardboard",
    "support",
    "complexity",
    "neglect",
    "friendship",
    "surprise",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    tags |= set(world.facts["material"].tags)
    tags |= set(world.facts["neglect"].tags)
    tags |= {"friendship", "complexity"}
    if world.facts["outcome"] == "twist":
        tags |= {"surprise"}
    if world.facts["problem"] == "unsupported":
        tags |= {"support"}
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:13}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Problem kinds from material / pose / neglect.
problem(M, P, N, soft) :- material(M), pose(P), neglect(N), neglect_kind(N, soft), needs_dry(M).
problem(M, P, N, unsupported) :- material(M), pose(P), neglect(N), neglect_kind(N, unsupported), needs_brace(M).
problem(M, P, N, unsupported) :- material(M), pose(P), neglect(N), neglect_kind(N, unsupported), support_need(P, S), S > 0.
problem(M, P, N, overloaded) :- material(M), pose(P), neglect(N), neglect_kind(N, overloaded), complexity(P, C), C >= 3.

works(F, Problem, P) :- fix(F), handles(F, Problem), not bad_fix(F, P).
bad_fix(add_braces, P) :- support_need(P, S), S > 1.
bad_fix(wait_and_patch, P) :- support_need(P, S), S > 1.

valid(Setting, M, P, N) :- setting(Setting), problem(M, P, N, Problem), works(_, Problem, P).

chosen_problem(Problem) :- chosen_material(M), chosen_pose(P), chosen_neglect(N), problem(M, P, N, Problem).
sensible_fix :- chosen_fix(F), chosen_problem(Problem), works(F, Problem, P), chosen_pose(P).
outcome(twist) :- chosen_fix(simplify_to_sleepy), sensible_fix.
outcome(rescued) :- sensible_fix, not chosen_fix(simplify_to_sleepy).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, material in MATERIALS.items():
        lines.append(asp.fact("material", mid))
        if material.needs_dry:
            lines.append(asp.fact("needs_dry", mid))
        if material.needs_brace:
            lines.append(asp.fact("needs_brace", mid))
    for pid, pose in POSES.items():
        lines.append(asp.fact("pose", pid))
        lines.append(asp.fact("complexity", pid, pose.complexity))
        lines.append(asp.fact("support_need", pid, pose.support_need))
    for nid, neglect in NEGLECTS.items():
        lines.append(asp.fact("neglect", nid))
        lines.append(asp.fact("neglect_kind", nid, neglect.kind))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for problem in sorted(fix.handles):
            lines.append(asp.fact("handles", fid, problem))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_material", params.material),
            asp.fact("chosen_pose", params.pose),
            asp.fact("chosen_neglect", params.neglect),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: empty story.")
    _ = format_qa(sample)
    _ = sample.to_json()


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
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test story generation passed.")
    except Exception as err:  # pragma: no cover - defensive verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: two friends make a walrus craft, neglect a simple step, and find a kind ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--pose", choices=POSES)
    ap.add_argument("--neglect", choices=NEGLECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--maker-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["teacher"])
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
    if args.material and args.pose and args.neglect:
        material = MATERIALS[args.material]
        pose = POSES[args.pose]
        neglect = NEGLECTS[args.neglect]
        if not problem_kind(material, pose, neglect):
            raise StoryError(explain_invalid(material, pose, neglect))
        if args.fix:
            fix = FIXES[args.fix]
            if not fix_works(problem_kind(material, pose, neglect), fix, pose):
                raise StoryError(explain_fix(fix, material, pose, neglect))
    elif args.fix and args.material and args.pose and args.neglect:
        pass

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.material is None or combo[1] == args.material)
        and (args.pose is None or combo[2] == args.pose)
        and (args.neglect is None or combo[3] == args.neglect)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, material_id, pose_id, neglect_id = rng.choice(sorted(combos))
    material = MATERIALS[material_id]
    pose = POSES[pose_id]
    neglect = NEGLECTS[neglect_id]
    problem = problem_kind(material, pose, neglect)
    sensible_fixes = [
        fid for fid, fix in FIXES.items()
        if fix_works(problem, fix, pose)
        and (args.fix is None or fid == args.fix)
    ]
    if not sensible_fixes:
        if args.fix is not None:
            raise StoryError(explain_fix(FIXES[args.fix], material, pose, neglect))
        raise StoryError("(No sensible fix matches the given options.)")
    fix_id = rng.choice(sorted(sensible_fixes))

    maker_gender = args.maker_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    maker_name = _pick_name(rng, maker_gender)
    friend_name = _pick_name(rng, friend_gender, avoid=maker_name)
    helper_trait = rng.choice(TRAITS)
    grownup_type = args.grownup or "teacher"

    return StoryParams(
        setting=setting_id,
        material=material_id,
        pose=pose_id,
        neglect=neglect_id,
        fix=fix_id,
        maker_name=maker_name,
        maker_gender=maker_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        helper_trait=helper_trait,
        grownup_type=grownup_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        material = MATERIALS[params.material]
        pose = POSES[params.pose]
        neglect = NEGLECTS[params.neglect]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid story parameter: {err.args[0]})") from None

    problem = problem_kind(material, pose, neglect)
    if not problem:
        raise StoryError(explain_invalid(material, pose, neglect))
    if not fix_works(problem, fix, pose):
        raise StoryError(explain_fix(fix, material, pose, neglect))

    world = tell(
        setting=setting,
        material=material,
        pose=pose,
        neglect=neglect,
        fix=fix,
        maker_name=params.maker_name,
        maker_gender=params.maker_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        helper_trait=params.helper_trait,
        grownup_type=params.grownup_type,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, material, pose, neglect) combos:\n")
        for setting, material, pose, neglect in combos:
            print(f"  {setting:10} {material:13} {pose:16} {neglect}")
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
                f"### {p.maker_name} & {p.friend_name}: {p.material} / {p.pose} / "
                f"{p.neglect} -> {p.fix} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
