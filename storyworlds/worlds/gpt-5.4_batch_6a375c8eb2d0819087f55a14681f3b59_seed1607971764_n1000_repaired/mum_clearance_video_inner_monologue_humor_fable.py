#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py
=============================================================================

A standalone story world about a child, a clearance bargain, and a homemade
video. The tone is gently comic and a little fable-like: a youngster rushes
toward showy glory, a sensible mum notices the real problem, and a small,
practical fix turns silliness into success.

Core premise
------------
A child finds a clearance costume piece that seems perfect for a grand little
video. Inside the child's head, the plan already looks splendid. In the real
world, the bargain item is a poor fit: boots slosh, a cape drags, or a crown
slides. Mum tests the setup, sees the risk, and uses the right humble helper.
Then the child makes the video properly, and the ending image proves the lesson:
before you show off, make sure the thing actually works.

Run it
------
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --plan parade --item boots
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --fix ribbon
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --all
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --trace
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --json
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --asp
    python storyworlds/worlds/gpt-5.4/mum_clearance_video_inner_monologue_humor_fable.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mum", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class Plan:
    id: str
    title: str
    act: str
    motion: str
    boast: str
    ending: str
    needs: str
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
class ClearanceItem:
    id: str
    label: str
    phrase: str
    issue: str
    problem_text: str
    comedy: str
    solved_by: str
    supports: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    phrase: str
    solves: set[str] = field(default_factory=set)
    action: str = ""
    qa_text: str = ""
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


def _r_misfit(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    if child.meters["testing"] < THRESHOLD:
        return out
    if item.meters["secure"] >= THRESHOLD:
        return out
    issue = item.attrs.get("issue", "")
    sig = ("misfit", issue)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["wobble"] += 1
    child.meters["balance"] -= 1
    child.memes["alarm"] += 1
    child.memes["embarrassment"] += 1
    out.append("__misfit__")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    helper = world.get("fix")
    if helper.meters["used"] < THRESHOLD:
        return out
    issue = item.attrs.get("issue", "")
    if issue not in helper.attrs.get("solves", set()):
        return out
    sig = ("fix", helper.id, issue)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["secure"] += 1
    item.meters["wobble"] = 0.0
    child = world.get("child")
    child.meters["balance"] = max(child.meters["balance"], 0.0) + 1
    child.memes["confidence"] += 1
    child.memes["relief"] += 1
    out.append("__fixed__")
    return out


def _r_record(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    item = world.get("item")
    camera = world.get("camera")
    if child.meters["performing"] < THRESHOLD:
        return out
    if item.meters["secure"] < THRESHOLD:
        return out
    sig = ("recorded",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    camera.meters["recorded"] += 1
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    out.append("__recorded__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="misfit", tag="physical", apply=_r_misfit),
    Rule(name="fix", tag="physical", apply=_r_fix),
    Rule(name="record", tag="social", apply=_r_record),
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


def item_supports_plan(item: ClearanceItem, plan: Plan) -> bool:
    return plan.id in item.supports


def fix_works(item: ClearanceItem, fix: Fix) -> bool:
    return item.issue in fix.solves


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for plan_id, plan in PLANS.items():
        for item_id, item in CLEARANCE_ITEMS.items():
            if not item_supports_plan(item, plan):
                continue
            for fix_id, fx in FIXES.items():
                if fix_works(item, fx):
                    combos.append((plan_id, item_id, fix_id))
    return combos


def explain_combo(plan: Plan, item: ClearanceItem) -> str:
    return (
        f"(No story: {item.label} do not honestly fit the {plan.title} plan. "
        f"The little video needs something suited to {plan.needs}, not a bargain "
        f"chosen only because it was on clearance.)"
    )


def explain_fix(item: ClearanceItem, fix: Fix) -> str:
    return (
        f"(No story: {fix.label} would not solve the real problem. "
        f"The {item.label} are wrong because they are {item.problem_text}, so the fix "
        f"must actually make them steady.)"
    )


def predict_problem(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["testing"] += 1
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "wobble": item.meters["wobble"] >= THRESHOLD,
        "balance": child.meters["balance"],
    }


def introduce(world: World, child: Entity, plan: Plan) -> None:
    world.say(
        f"In a small brick house at the edge of the lane lived {child.id}, a young "
        f"{child.type} with more ideas than patience. That afternoon {child.pronoun()} "
        f"decided to make {plan.title}, and in {child.pronoun('possessive')} head it was "
        f"already famous."
    )
    world.say(
        f'"This will be the grandest video in the whole lane," {child.pronoun()} '
        f"thought. {plan.boast}"
    )


def find_clearance(world: World, child: Entity, item_cfg: ClearanceItem) -> None:
    child.memes["greed"] += 1
    world.say(
        f"At the jumble shop, a cardboard sign shouted CLEARANCE in red letters. "
        f"Under it lay {item_cfg.phrase}, waiting like a cheap temptation with a dusty grin."
    )
    world.say(
        f'"A bargain and a masterpiece at once," {child.pronoun()} thought. '
        f'"What clever creature could resist?"'
    )


def bring_home(world: World, child: Entity, mum: Entity, item_cfg: ClearanceItem) -> None:
    world.say(
        f"{child.id} hurried home with the bargain tucked under one arm and found "
        f"{mum.label} folding tea towels by the window."
    )
    world.say(
        f'"Mum, please hold the phone for my video," said {child.id}. '
        f'"Just wait until you see me in these {item_cfg.label}."'
    )


def dress_and_brag(world: World, child: Entity, item_cfg: ClearanceItem, plan: Plan) -> None:
    child.meters["dressed"] += 1
    child.memes["hope"] += 1
    world.say(
        f"{child.id} put on the {item_cfg.label} and struck a pose for {plan.act}. "
        f"{item_cfg.comedy}"
    )
    world.say(
        f'"Steady now," {child.pronoun()} thought. "Soon everyone will gasp, then applaud, '
        f'then ask how I became so splendid by teatime."'
    )


def mum_warns(world: World, child: Entity, mum: Entity, item_cfg: ClearanceItem) -> None:
    pred = predict_problem(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    if pred["wobble"]:
        mum.memes["care"] += 1
        child.memes["stubborn"] += 1
        world.say(
            f"{mum.label.capitalize()} looked once at the costume and once at the child's feet, hem, "
            f"or brow, depending on where the trouble lived. "
            f'"A clearance price is not the same as a clearance for nonsense," {mum.pronoun()} said.'
        )
        world.say(
            f'"Test it first. If you start {world.facts["plan"].motion}, those {item_cfg.label} may go '
            f'wrong in a hurry."'
        )


def test_attempt(world: World, child: Entity, item_cfg: ClearanceItem, plan: Plan) -> None:
    child.meters["testing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But excitement had cotton in its ears. {child.id} tried one sample move for {plan.act}."
    )
    world.say(
        f"At once, the trouble showed itself: {item_cfg.problem_text}. "
        f"{item_cfg.comedy}"
    )
    world.say(
        f'"Oh crumbs," {child.pronoun()} thought. "My masterpiece has the manners of a turnip."'
    )


def mum_helps(world: World, child: Entity, mum: Entity, fix_cfg: Fix) -> None:
    helper = world.get("fix")
    helper.meters["used"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{mum.label.capitalize()} did not laugh for long, though {mum.pronoun()} did have to bite "
        f"{mum.pronoun('possessive')} lip once. Then {mum.pronoun()} fetched {fix_cfg.phrase} and "
        f"{fix_cfg.action}."
    )
    world.say(
        f'"There," said {mum.label}. "Now the joke may stay in the video instead of on the floor."'
    )


def record_success(world: World, child: Entity, mum: Entity, plan: Plan, item_cfg: ClearanceItem) -> None:
    child.meters["performing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Once the {item_cfg.label} were secure, {mum.label} held up the phone and began the video."
    )
    world.say(
        f"{child.id} {plan.motion} and finished with {plan.ending}. This time the funny part was chosen, "
        f"not accidental."
    )
    world.say(
        f'"Much better," {child.pronoun()} thought. "Even glory looks wiser after a small repair."'
    )


def ending(world: World, child: Entity, mum: Entity, plan: Plan, item_cfg: ClearanceItem, fix_cfg: Fix) -> None:
    child.memes["gratitude"] += 1
    mum.memes["warmth"] += 1
    world.say(
        f"That evening they watched the little video together. In it, {child.id} looked merry, "
        f"the {item_cfg.label} stayed where they belonged, and even {mum.label}'s chuckle at the end "
        f"made the whole thing brighter."
    )
    world.say(
        f"So the child learned that a thing on clearance may still need care, and a proud plan walks "
        f"best when it listens to sense. For the market loves a bargain, but wisdom checks the fit."
    )
    world.facts["moral"] = (
        "A cheap prize is not a good plan until it is made fit for use."
    )


def tell(
    plan: Plan,
    item_cfg: ClearanceItem,
    fix_cfg: Fix,
    child_name: str = "Pip",
    child_type: str = "mouse",
    mum_name: str = "mum",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    mum = world.add(Entity(id="mum", kind="character", type="mother", label=mum_name, role="mum"))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="costume",
        label=item_cfg.label,
        attrs={"issue": item_cfg.issue},
    ))
    helper = world.add(Entity(
        id="fix",
        kind="thing",
        type="helper",
        label=fix_cfg.label,
        attrs={"solves": set(fix_cfg.solves)},
    ))
    camera = world.add(Entity(id="camera", kind="thing", type="phone", label="phone"))

    child.meters["balance"] = 1.0
    child.meters["testing"] = 0.0
    child.meters["performing"] = 0.0
    item.meters["secure"] = 0.0
    item.meters["wobble"] = 0.0
    helper.meters["used"] = 0.0
    camera.meters["recorded"] = 0.0

    child.memes["alarm"] = 0.0
    child.memes["confidence"] = 0.0
    child.memes["embarrassment"] = 0.0
    child.memes["joy"] = 0.0
    child.memes["pride"] = 0.0
    mum.memes["care"] = 0.0

    world.facts["plan"] = plan
    world.facts["item_cfg"] = item_cfg
    world.facts["fix_cfg"] = fix_cfg
    world.facts["child_name"] = child_name
    world.facts["mum_name"] = mum_name

    introduce(world, child, plan)
    find_clearance(world, child, item_cfg)
    world.para()
    bring_home(world, child, mum, item_cfg)
    dress_and_brag(world, child, item_cfg, plan)
    mum_warns(world, child, mum, item_cfg)
    world.para()
    test_attempt(world, child, item_cfg, plan)
    mum_helps(world, child, mum, fix_cfg)
    world.para()
    record_success(world, child, mum, plan, item_cfg)
    ending(world, child, mum, plan, item_cfg, fix_cfg)

    world.facts.update(
        child=child,
        mum=mum,
        item=item,
        fix=helper,
        camera=camera,
        success=camera.meters["recorded"] >= THRESHOLD,
        fixed=item.meters["secure"] >= THRESHOLD,
        issue=item_cfg.issue,
    )
    return world


PLANS = {
    "parade": Plan(
        id="parade",
        title="a parade video",
        act="a tiny parade",
        motion="marched across the rug with comic dignity",
        boast="I shall swing my arms like a mayor and bow like a duke.",
        ending="a solemn bow so grand that even the lamp seemed impressed",
        needs="marching and bowing",
        tags={"video", "parade"},
    ),
    "hero": Plan(
        id="hero",
        title="a hero video",
        act="a heroic twirl",
        motion="twirled by the umbrella stand and pointed at the ceiling",
        boast="I shall whirl like a champion and rescue the ottoman from boredom.",
        ending="a brave point at the ceiling as if a dragon lived there",
        needs="twirling and sweeping turns",
        tags={"video", "hero"},
    ),
    "royal": Plan(
        id="royal",
        title="a royal video",
        act="a royal speech",
        motion="walked three proud steps and bowed to an imaginary crowd",
        boast="I shall look so royal that the teapot may begin taking orders.",
        ending="a small wave so majestic it nearly forgave the curtains",
        needs="a bow and a steady head",
        tags={"video", "royal"},
    ),
}

CLEARANCE_ITEMS = {
    "boots": ClearanceItem(
        id="boots",
        label="boots",
        phrase="a pair of shiny parade boots that were plainly two sizes too large",
        issue="loose",
        problem_text="the boots were loose and slapped about with every step",
        comedy="They made a clop-clop sound like two stubborn pudding bowls arguing.",
        solved_by="socks",
        supports={"parade"},
        tags={"boots", "clearance"},
    ),
    "cape": ClearanceItem(
        id="cape",
        label="cape",
        phrase="a velvet cape with a hem so long it looked eager to sweep the moon",
        issue="dragging",
        problem_text="the cape dragged behind like a sleepy red mop",
        comedy="Its tail kept trying to become part rug and part weather.",
        solved_by="pin",
        supports={"hero"},
        tags={"cape", "clearance"},
    ),
    "crown": ClearanceItem(
        id="crown",
        label="crown",
        phrase="a glittering crown with more sparkle than sense and a band too wide",
        issue="slipping",
        problem_text="the crown slid over one eye whenever its owner tried to bow",
        comedy="It behaved less like a crown and more like a polite metal pancake.",
        solved_by="ribbon",
        supports={"royal"},
        tags={"crown", "clearance"},
    ),
    "feather_hat": ClearanceItem(
        id="feather_hat",
        label="hat",
        phrase="a feather hat so floppy that it could not decide which century to visit",
        issue="slipping",
        problem_text="the hat tipped over the ears whenever its owner tried to bow",
        comedy="The feather nodded before the child did, which seemed terribly rude.",
        solved_by="ribbon",
        supports={"parade", "royal"},
        tags={"hat", "clearance"},
    ),
}

FIXES = {
    "socks": Fix(
        id="socks",
        label="thick socks",
        phrase="a pair of thick wool socks",
        solves={"loose"},
        action="stuffed the extra room snugly with the socks",
        qa_text="used thick socks to make the boots fit snugly",
        tags={"socks", "fit"},
    ),
    "pin": Fix(
        id="pin",
        label="a safety pin",
        phrase="a bright safety pin",
        solves={"dragging"},
        action="pinned the cape up so the hem sat clear of the floor",
        qa_text="pinned the cape up so it would not drag",
        tags={"pin", "fit"},
    ),
    "ribbon": Fix(
        id="ribbon",
        label="a ribbon",
        phrase="a narrow blue ribbon",
        solves={"slipping"},
        action="tied the ribbon under the crown so it stayed in place",
        qa_text="tied the crown with a ribbon so it would stay put",
        tags={"ribbon", "fit"},
    ),
    "spoon": Fix(
        id="spoon",
        label="a wooden spoon",
        phrase="a wooden spoon from the crock",
        solves=set(),
        action="waved it helpfully in the air, which solved nothing at all",
        qa_text="waved a spoon, which would not fix a costume",
        tags={"kitchen"},
    ),
}

ANIMAL_TYPES = ["mouse", "rabbit", "fox"]
NAMES = ["Pip", "Mabel", "Ned", "Tess", "Jun", "Bram"]


@dataclass
class StoryParams:
    plan: str
    item: str
    fix: str
    child_name: str = "Pip"
    child_type: str = "mouse"
    mum_name: str = "mum"
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
    "clearance": [
        (
            "What does clearance mean in a shop?",
            "Clearance means a shop is trying to sell things quickly, often for a lower price. A low price can be useful, but you still have to check whether the thing works for you."
        )
    ],
    "video": [
        (
            "What is a video?",
            "A video is a moving recording made with a camera or phone. It can show actions, sounds, and funny little moments."
        )
    ],
    "boots": [
        (
            "Why can boots that are too big be hard to walk in?",
            "Boots that are too big can slide around your feet. That makes your steps wobbly and can make you trip."
        )
    ],
    "cape": [
        (
            "Why is a long cape tricky to wear?",
            "A cape that drags can catch under your feet or on the floor. When cloth trails too low, it can pull and tangle."
        )
    ],
    "crown": [
        (
            "Why does a loose crown slip?",
            "If a crown is wider than your head, it cannot stay steady by itself. When you bow or turn, it slides."
        )
    ],
    "hat": [
        (
            "Why does a floppy hat fall over the eyes?",
            "A floppy hat that is too loose does not grip the head well. It tips forward when the wearer moves."
        )
    ],
    "socks": [
        (
            "How can thick socks help with big boots?",
            "Thick socks fill some of the empty space inside the boots. That helps the boots fit more snugly and move less."
        )
    ],
    "pin": [
        (
            "What can a safety pin do to clothes?",
            "A safety pin can hold a fold of cloth in place. Grown-ups use it to shorten or secure fabric for a while."
        )
    ],
    "ribbon": [
        (
            "How can a ribbon help a loose crown or hat?",
            "A ribbon can be tied so the headpiece stays in place instead of sliding. It is a simple way to make something steadier."
        )
    ],
}
KNOWLEDGE_ORDER = ["clearance", "video", "boots", "cape", "crown", "hat", "socks", "pin", "ribbon"]


def generation_prompts(world: World) -> list[str]:
    plan = world.facts["plan"]
    item_cfg = world.facts["item_cfg"]
    child = world.facts["child"]
    return [
        f'Write a short fable-like story for a young child that includes the words "mum", "clearance", and "video".',
        f"Tell a humorous story with inner monologue where {world.facts['child_name']} finds {item_cfg.phrase}, imagines greatness, and learns to test things before making a {plan.title}.",
        f"Write a gentle comic fable about a child, a clearance bargain, and a mum who uses practical wisdom to save a homemade video."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    mum = world.facts["mum"]
    item_cfg = world.facts["item_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    plan = world.facts["plan"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {world.facts['child_name']}, a young {child.type}, and {mum.label} who helps with the plan. The story follows a proud little idea that becomes wiser before the video is made."
        ),
        (
            "What did the child find on clearance?",
            f"The child found {item_cfg.phrase}. It looked perfect for {plan.title}, at least inside the child's excited thoughts."
        ),
        (
            "Why did mum tell the child to test the costume first?",
            f"{mum.label.capitalize()} could see that the bargain item did not fit properly. She wanted to stop a silly accident before it spoiled the video."
        ),
        (
            "What went wrong when the child tried a sample move?",
            f"The trouble showed itself right away: {item_cfg.problem_text}. The child's proud idea turned funny because the costume would not behave."
        ),
        (
            f"How did {mum.label} fix the problem?",
            f"{mum.label.capitalize()} {fix_cfg.qa_text}. That practical little repair changed the costume from a hazard into something usable."
        ),
        (
            "How did the story end?",
            f"In the end, the child made the video successfully and the funny part stayed playful instead of disastrous. The ending shows that good sense can rescue even a grand, goofy plan."
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    item_cfg = world.facts["item_cfg"]
    fix_cfg = world.facts["fix_cfg"]
    tags = {"clearance", "video"} | set(item_cfg.tags) | set(fix_cfg.tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: sorted(v) if isinstance(v, set) else v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        plan="parade",
        item="boots",
        fix="socks",
        child_name="Pip",
        child_type="mouse",
        mum_name="mum",
    ),
    StoryParams(
        plan="hero",
        item="cape",
        fix="pin",
        child_name="Tess",
        child_type="rabbit",
        mum_name="mum",
    ),
    StoryParams(
        plan="royal",
        item="crown",
        fix="ribbon",
        child_name="Bram",
        child_type="fox",
        mum_name="mum",
    ),
    StoryParams(
        plan="royal",
        item="feather_hat",
        fix="ribbon",
        child_name="Mabel",
        child_type="mouse",
        mum_name="mum",
    ),
]


ASP_RULES = r"""
supports(Item, Plan) :- item(Item), plan(Plan), item_support(Item, Plan).
solves(Fix, Issue) :- fix(Fix), issue(Issue), fix_solves(Fix, Issue).

valid(Plan, Item, Fix) :- plan(Plan), item(Item), fix(Fix),
                          supports(Item, Plan),
                          item_issue(Item, Issue),
                          solves(Fix, Issue).

chosen_valid :- chosen_plan(P), chosen_item(I), chosen_fix(F), valid(P, I, F).
outcome(success) :- chosen_valid.
outcome(invalid) :- chosen_plan(_), chosen_item(_), chosen_fix(_), not chosen_valid.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for plan_id in PLANS:
        lines.append(asp.fact("plan", plan_id))
    for item_id, item in CLEARANCE_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("issue", item.issue))
        lines.append(asp.fact("item_issue", item_id, item.issue))
        for plan_id in sorted(item.supports):
            lines.append(asp.fact("item_support", item_id, plan_id))
    for fix_id, fx in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for issue in sorted(fx.solves):
            lines.append(asp.fact("fix_solves", fix_id, issue))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_plan", params.plan),
        asp.fact("chosen_item", params.item),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    if params.plan not in PLANS or params.item not in CLEARANCE_ITEMS or params.fix not in FIXES:
        return "invalid"
    if (params.plan, params.item, params.fix) in set(valid_combos()):
        return "success"
    return "invalid"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated an ordinary story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child, a clearance costume piece, and a homemade video. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--item", choices=CLEARANCE_ITEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=ANIMAL_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.plan and args.item:
        plan = PLANS[args.plan]
        item = CLEARANCE_ITEMS[args.item]
        if not item_supports_plan(item, plan):
            raise StoryError(explain_combo(plan, item))
    if args.item and args.fix:
        item = CLEARANCE_ITEMS[args.item]
        fix = FIXES[args.fix]
        if not fix_works(item, fix):
            raise StoryError(explain_fix(item, fix))

    combos = [
        combo for combo in valid_combos()
        if (args.plan is None or combo[0] == args.plan)
        and (args.item is None or combo[1] == args.item)
        and (args.fix is None or combo[2] == args.fix)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    plan_id, item_id, fix_id = rng.choice(sorted(combos))
    child_name = args.child_name or rng.choice(NAMES)
    child_type = args.child_type or rng.choice(ANIMAL_TYPES)
    return StoryParams(
        plan=plan_id,
        item=item_id,
        fix=fix_id,
        child_name=child_name,
        child_type=child_type,
        mum_name="mum",
    )


def generate(params: StoryParams) -> StorySample:
    if params.plan not in PLANS:
        raise StoryError(f"(Unknown plan: {params.plan})")
    if params.item not in CLEARANCE_ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")

    plan = PLANS[params.plan]
    item_cfg = CLEARANCE_ITEMS[params.item]
    fix_cfg = FIXES[params.fix]

    if not item_supports_plan(item_cfg, plan):
        raise StoryError(explain_combo(plan, item_cfg))
    if not fix_works(item_cfg, fix_cfg):
        raise StoryError(explain_fix(item_cfg, fix_cfg))

    world = tell(
        plan=plan,
        item_cfg=item_cfg,
        fix_cfg=fix_cfg,
        child_name=params.child_name,
        child_type=params.child_type,
        mum_name=params.mum_name,
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
        print(f"{len(combos)} valid (plan, item, fix) combos:\n")
        for plan_id, item_id, fix_id in combos:
            print(f"  {plan_id:8} {item_id:12} {fix_id}")
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
            header = f"### {p.child_name}: {p.plan} with {p.item} ({p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
