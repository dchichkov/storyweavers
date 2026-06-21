#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py
==============================================================================

A standalone story world for a rhyming, happy tale set at a grandparent's
house. A child wants something lovely from a high shelf, is tempted to reach it
the wrong way, a wobble begins, and a grandparent helps them choose the proper
way to proceed.

The prose is state-driven: room, target object, risky perch, safe helper, and
whether the wobble starts before the grown-up intervenes all come from the world
model. The ending is always warm and happy, but the middle turn changes with the
simulated risk.

Run it
------
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py --room kitchen --target cookie_tin
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py --unsafe books
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py --aid reacher
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py --all
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/proceed_gerund_grandparent_s_house_happy_ending.py --verify
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
    portable: bool = True
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
        return {"grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
class Room:
    id: str
    label: str
    shelf_word: str
    detail: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    plural: bool = False
    height: int = 2
    weight: int = 1
    fragile: bool = False
    shine: str = ""
    purpose: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class UnsafePerch:
    id: str
    label: str
    phrase: str
    base_stability: int
    slips: bool = False
    rolls: bool = False
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
class SafeAid:
    id: str
    label: str
    phrase: str
    reach: int
    support: int
    handles_fragile: bool = True
    two_person: bool = False
    action: str = ""
    ending_line: str = ""
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
    def __init__(self, room: Room) -> None:
        self.room = room
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
        clone = World(self.room)
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


def hazard_score(target: Target, unsafe: UnsafePerch) -> int:
    score = target.height + target.weight
    if target.fragile:
        score += 1
    if unsafe.slips:
        score += 1
    if unsafe.rolls:
        score += 1
    return score


def wobble_begins(target: Target, unsafe: UnsafePerch) -> bool:
    return hazard_score(target, unsafe) > unsafe.base_stability


def safe_solution(target: Target, aid: SafeAid) -> bool:
    if aid.reach < target.height:
        return False
    if aid.support < target.weight:
        return False
    if target.fragile and not aid.handles_fragile:
        return False
    return True


def _r_wobble(world: World) -> list[str]:
    child = world.get("child")
    perch = world.get("perch")
    if child.meters["climbing"] < THRESHOLD:
        return []
    if not world.facts.get("predicted_wobble", False):
        return []
    sig = ("wobble", perch.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    perch.meters["wobble"] += 1
    child.memes["fear"] += 1
    child.memes["surprise"] += 1
    return ["__wobble__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
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


ROOMS = {
    "kitchen": Room(
        id="kitchen",
        label="the kitchen",
        shelf_word="pantry shelf",
        detail="Copper pans gave a gentle gleam, and cinnamon made the whole room seem like a dream.",
        affords={"cookie_tin", "jam_jar", "teacups"},
    ),
    "hall": Room(
        id="hall",
        label="the front hall",
        shelf_word="coat shelf",
        detail="Umbrellas stood in a row so neat, and old floorboards hummed beneath small feet.",
        affords={"kite_box", "photo_album"},
    ),
    "sewing_room": Room(
        id="sewing_room",
        label="the sewing room",
        shelf_word="button shelf",
        detail="Soft quilts rested fold by fold, and bright thread spools shone red and gold.",
        affords={"button_tin", "photo_album"},
    ),
}

TARGETS = {
    "cookie_tin": Target(
        id="cookie_tin",
        label="cookie tin",
        phrase="a round blue cookie tin",
        plural=False,
        height=2,
        weight=1,
        fragile=False,
        shine="blue as the noon-day sky",
        purpose="share sweet biscuits with tea",
        tags={"cookies", "high_shelf"},
    ),
    "jam_jar": Target(
        id="jam_jar",
        label="jam jar",
        phrase="a ruby jam jar",
        plural=False,
        height=2,
        weight=1,
        fragile=True,
        shine="red as a berry bright",
        purpose="spread jam on warm bread tonight",
        tags={"jam", "glass", "high_shelf"},
    ),
    "teacups": Target(
        id="teacups",
        label="teacups",
        phrase="a pair of flowered teacups",
        plural=True,
        height=3,
        weight=1,
        fragile=True,
        shine="white with roses curled just right",
        purpose="set a tiny table for a game",
        tags={"cups", "glass", "high_shelf"},
    ),
    "kite_box": Target(
        id="kite_box",
        label="kite box",
        phrase="a bright kite box",
        plural=False,
        height=3,
        weight=2,
        fragile=False,
        shine="striped with green and yellow bands",
        purpose="find a kite for breezy hands",
        tags={"kite", "high_shelf"},
    ),
    "button_tin": Target(
        id="button_tin",
        label="button tin",
        phrase="a shiny button tin",
        plural=False,
        height=2,
        weight=1,
        fragile=False,
        shine="silver with a moonlike grin",
        purpose="pick buttons for a patchwork bear",
        tags={"buttons", "high_shelf"},
    ),
    "photo_album": Target(
        id="photo_album",
        label="photo album",
        phrase="a thick photo album",
        plural=False,
        height=3,
        weight=2,
        fragile=False,
        shine="brown with corners worn and kind",
        purpose="look at baby pictures they might find",
        tags={"photos", "memories", "high_shelf"},
    ),
}

UNSAFE_PERCHES = {
    "wheely_chair": UnsafePerch(
        id="wheely_chair",
        label="wheeled chair",
        phrase="a wheeled chair",
        base_stability=2,
        slips=False,
        rolls=True,
        tags={"chair", "rolling"},
    ),
    "books": UnsafePerch(
        id="books",
        label="stack of books",
        phrase="a stack of books",
        base_stability=1,
        slips=True,
        rolls=False,
        tags={"books", "stack"},
    ),
    "toy_crate": UnsafePerch(
        id="toy_crate",
        label="toy crate",
        phrase="an old toy crate",
        base_stability=2,
        slips=True,
        rolls=False,
        tags={"crate"},
    ),
}

SAFE_AIDS = {
    "step_stool": SafeAid(
        id="step_stool",
        label="step stool",
        phrase="a striped step stool",
        reach=2,
        support=2,
        handles_fragile=True,
        two_person=False,
        action="set the striped step stool flat on the floor and held one steady hand nearby",
        ending_line="Soon they were proceeding with care, and the treat came down without a scare.",
        tags={"stool", "reach"},
    ),
    "reacher": SafeAid(
        id="reacher",
        label="grabber reacher",
        phrase="a long grabber reacher",
        reach=3,
        support=1,
        handles_fragile=False,
        two_person=False,
        action="brought a long grabber reacher and showed how to pinch just right",
        ending_line="Soon they were proceeding with a careful squeeze, and down it came with cozy ease.",
        tags={"reacher", "tool"},
    ),
    "ladder": SafeAid(
        id="ladder",
        label="little ladder",
        phrase="a little folding ladder",
        reach=3,
        support=2,
        handles_fragile=True,
        two_person=False,
        action="opened a little folding ladder and checked each foot before they climbed",
        ending_line="Soon they were proceeding rung by rung, with a happy hum on every tongue.",
        tags={"ladder", "reach"},
    ),
    "grandparent_help": SafeAid(
        id="grandparent_help",
        label="grandparent's helping arms",
        phrase="grandparent's helping arms",
        reach=3,
        support=2,
        handles_fragile=True,
        two_person=True,
        action="lifted the child just enough while keeping both feet and both hearts safe",
        ending_line="Soon they were proceeding side by side, with safe strong help and family pride.",
        tags={"help", "adult"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Daisy", "Poppy", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Ben", "Eli", "Leo", "Finn", "Jude"]
TRAITS = ["eager", "curious", "bouncy", "bright", "gentle", "cheery"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for room_id, room in ROOMS.items():
        for target_id in sorted(room.affords):
            target = TARGETS[target_id]
            for unsafe_id, unsafe in UNSAFE_PERCHES.items():
                if not wobble_begins(target, unsafe):
                    continue
                for aid_id, aid in SAFE_AIDS.items():
                    if safe_solution(target, aid):
                        combos.append((room_id, target_id, unsafe_id, aid_id))
    return combos


def explain_invalid_target(room: Room, target: Target) -> str:
    return (
        f"(No story: {target.the} does not belong in {room.label} here, so the shelf problem "
        f"would not feel natural. Try one that fits {room.label}.)"
    )


def explain_invalid_aid(target: Target, aid: SafeAid) -> str:
    bits = []
    if aid.reach < target.height:
        bits.append("it cannot reach that shelf")
    if aid.support < target.weight:
        bits.append("it cannot handle that weight")
    if target.fragile and not aid.handles_fragile:
        bits.append("it is too clumsy for something breakable")
    why = ", and ".join(bits) if bits else "it is not a safe fit"
    return f"(No story: {aid.phrase} will not work for {target.the} because {why}.)"


ASP_RULES = r"""
risky(Target, Unsafe) :-
    target(Target), unsafe(Unsafe),
    height(Target, H), weight(Target, W), stability(Unsafe, S),
    H + W > S.

risky(Target, Unsafe) :-
    target(Target), unsafe(Unsafe),
    height(Target, H), weight(Target, W), stability(Unsafe, S),
    fragile(Target), H + W + 1 > S.

usable_aid(Target, Aid) :-
    target(Target), aid(Aid),
    height(Target, H), reach(Aid, R),
    weight(Target, W), support(Aid, S),
    R >= H, S >= W, not blocked_fragile(Target, Aid).

blocked_fragile(Target, Aid) :-
    target(Target), aid(Aid), fragile(Target), not handles_fragile(Aid).

valid(Room, Target, Unsafe, Aid) :-
    in_room(Room, Target),
    risky(Target, Unsafe),
    usable_aid(Target, Aid).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for target_id in sorted(room.affords):
            lines.append(asp.fact("in_room", room_id, target_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("height", target_id, target.height))
        lines.append(asp.fact("weight", target_id, target.weight))
        if target.fragile:
            lines.append(asp.fact("fragile", target_id))
    for unsafe_id, unsafe in UNSAFE_PERCHES.items():
        lines.append(asp.fact("unsafe", unsafe_id))
        lines.append(asp.fact("stability", unsafe_id, unsafe.base_stability))
    for aid_id, aid in SAFE_AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("reach", aid_id, aid.reach))
        lines.append(asp.fact("support", aid_id, aid.support))
        if aid.handles_fragile:
            lines.append(asp.fact("handles_fragile", aid_id))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    room: str
    target: str
    unsafe: str
    aid: str
    child_name: str
    child_gender: str
    grandparent: str
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


def predict(world: World, target: Target, unsafe: UnsafePerch) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["climbing"] += 1
    sim.facts["predicted_wobble"] = wobble_begins(target, unsafe)
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("perch").meters["wobble"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def opening(world: World, child: Entity, grandparent: Entity, room: Room, target: Target) -> None:
    world.say(
        f"At {grandparent.label_word}'s house in {room.label}, the afternoon kept gentle time; "
        f"{room.detail}"
    )
    world.say(
        f"{child.id}, a {next((t for t in child.traits if t), 'bright')} little {child.type}, "
        f"spied {target.phrase} on the {room.shelf_word}, {target.shine} in the light sublime."
    )
    world.say(
        f"{child.pronoun().capitalize()} hoped to fetch {target.the} so they could {target.purpose}; "
        f"the wish rose quick, the way small wishes often do."
    )


def temptation(world: World, child: Entity, unsafe: UnsafePerch) -> None:
    child.memes["want"] += 1
    world.say(
        f'"I can reach it if I stand on {unsafe.phrase}," {child.id} said with a grin. '
        f"The idea looked easy from the floor below, and very hard not to begin."
    )


def warning(world: World, child: Entity, grandparent: Entity, target: Target, unsafe: UnsafePerch) -> None:
    pred = predict(world, target, unsafe)
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["trust"] += 1
    world.say(
        f'{grandparent.label_word.capitalize()} looked at {unsafe.phrase}, then up at {target.the}, '
        f'and softly said, "Let us think before our climbing starts. Some ways wobble feet and flutter hearts."'
    )


def climb(world: World, child: Entity, unsafe: UnsafePerch) -> None:
    child.meters["climbing"] += 1
    child.memes["defiance"] += 1
    world.say(
        f"But wish went skipping before wisdom, so {child.id} put one foot up high "
        f"and began proceeding, trying the risky way with a hopeful little sigh."
    )
    propagate(world, narrate=False)
    if world.get("perch").meters["wobble"] >= THRESHOLD:
        world.say(
            f"Then {unsafe.the if hasattr(unsafe, 'the') else 'the perch'} gave a wobble, small but clear; "
            f"it made the brave idea suddenly feel near to fear."
        )


def catch_turn(world: World, child: Entity, grandparent: Entity, unsafe: UnsafePerch) -> None:
    child.memes["fear"] = max(child.memes["fear"], 1.0)
    grandparent.memes["care"] += 1
    world.say(
        f"{grandparent.label_word.capitalize()} was there at once with steady hands and steady tone: "
        f'"Down you come, my dear," {grandparent.pronoun()} said. "We never have to do hard things alone."'
    )
    world.say(
        f"{child.id} climbed down from {unsafe.phrase}, cheeks pink and eyes wide. "
        f"The room grew calm again as the hurry slipped aside."
    )


def choose_safe_way(world: World, child: Entity, grandparent: Entity, aid: SafeAid) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    grandparent.memes["care"] += 1
    world.say(
        f"Then {grandparent.label_word.capitalize()} {aid.action}. "
        f'"This is how we proceed," {grandparent.pronoun()} smiled, "with care, with help, and with a plan."'
    )


def retrieve(world: World, child: Entity, grandparent: Entity, target: Target, aid: SafeAid) -> None:
    child.meters["safe_reach"] += 1
    target_ent = world.get("target")
    target_ent.meters["retrieved"] += 1
    child.memes["joy"] += 1
    grandparent.memes["joy"] += 1
    world.say(
        f"{aid.ending_line} {child.id} held {target.the} close, and nothing tipped or tore. "
        f"Safe hands had brought the happy thing from shelf to floor."
    )


def ending(world: World, child: Entity, grandparent: Entity, target: Target) -> None:
    share = {
        "cookie_tin": "They shared sweet biscuits, crumb by crumb, while rain tapped out a tiny drum.",
        "jam_jar": "They spread bright jam on warm soft bread, and laughed at ruby mustaches red.",
        "teacups": "They poured pretend tea light and slow, and made the flowered table glow.",
        "kite_box": "They opened the kite box by the door, dreaming of windy games in store.",
        "button_tin": "They chose round buttons, bright and small, and stitched a smiling bear for all.",
        "photo_album": "They turned old pages, cheek to cheek, and found young faces rosy-sweet.",
    }[target.id]
    world.say(
        f'Soon {child.id} was smiling again. "{target.label.title()} first, but safety before all," '
        f'{child.pronoun()} said, remembering the wobble small.'
    )
    world.say(
        f"{share} And in {grandparent.label_word}'s house the lesson stayed bright as evening light: "
        f"kind help and careful steps can make a tricky reach come right."
    )


def tell(
    room: Room,
    target: Target,
    unsafe: UnsafePerch,
    aid: SafeAid,
    child_name: str = "Lila",
    child_gender: str = "girl",
    grandparent_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World(room)
    child = world.add(
        Entity(
            id="child",
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
            attrs={"name": child_name},
        )
    )
    grandparent = world.add(
        Entity(
            id="grandparent",
            kind="character",
            type=grandparent_type,
            label="the grandparent",
            role="grandparent",
            attrs={},
        )
    )
    perch = world.add(
        Entity(
            id="perch",
            kind="thing",
            type="perch",
            label=unsafe.label,
            role="unsafe",
            attrs={"rolls": unsafe.rolls, "slips": unsafe.slips},
        )
    )
    target_ent = world.add(
        Entity(
            id="target",
            kind="thing",
            type="target",
            label=target.label,
            role="target",
            attrs={"fragile": target.fragile},
        )
    )

    world.facts.update(
        room=room,
        target_cfg=target,
        unsafe_cfg=unsafe,
        aid_cfg=aid,
        child=child,
        grandparent=grandparent,
        predicted_wobble=wobble_begins(target, unsafe),
    )

    opening(world, child, grandparent, room, target)
    world.para()
    temptation(world, child, unsafe)
    warning(world, child, grandparent, target, unsafe)
    climb(world, child, unsafe)
    world.para()
    catch_turn(world, child, grandparent, unsafe)
    choose_safe_way(world, child, grandparent, aid)
    retrieve(world, child, grandparent, target, aid)
    world.para()
    ending(world, child, grandparent, target)

    world.facts.update(
        wobble_started=perch.meters["wobble"] >= THRESHOLD,
        retrieved=target_ent.meters["retrieved"] >= THRESHOLD,
        happy=True,
    )
    return world


KNOWLEDGE = {
    "high_shelf": [
        (
            "Why can reaching for things on a high shelf be unsafe?",
            "High shelves can make children stretch, climb, or stand on wobbly things. That is risky because balance can slip before a hand is ready."
        )
    ],
    "glass": [
        (
            "Why do grown-ups carry glass things carefully?",
            "Glass can break if it falls or bumps hard. Sharp pieces can hurt hands and feet, so careful carrying matters."
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool is a small sturdy step that helps you reach a little higher. It is meant to stand flat on the floor so your feet stay steadier."
        )
    ],
    "ladder": [
        (
            "What makes a little ladder safer than standing on random objects?",
            "A ladder is built for climbing and has stable steps. Random objects can slide or tip because they are not made for standing."
        )
    ],
    "reacher": [
        (
            "What is a grabber reacher?",
            "A grabber reacher is a long tool that helps pick up light things from far away. It works best for objects that are not too heavy or delicate."
        )
    ],
    "adult": [
        (
            "Why is it smart to ask a grown-up for help?",
            "Grown-ups can hold things steady, reach higher, and choose safer tools. Asking for help can stop a problem before someone gets hurt."
        )
    ],
    "cookies": [
        (
            "What is a cookie tin?",
            "A cookie tin is a metal container that keeps cookies fresh and crumbly. It is often round and can sit on a pantry shelf."
        )
    ],
    "jam": [
        (
            "What is jam made from?",
            "Jam is made by cooking fruit with sugar until it turns thick and sweet. People spread it on bread or toast."
        )
    ],
    "cups": [
        (
            "What are teacups for?",
            "Teacups are small cups used for tea or pretend tea. Because they can be delicate, people carry them gently."
        )
    ],
    "kite": [
        (
            "What does a kite need to fly?",
            "A kite needs wind and a string held by someone below. The moving air lifts the kite and helps it dance."
        )
    ],
    "buttons": [
        (
            "What can buttons be used for?",
            "Buttons can fasten clothes, decorate crafts, or help mend a torn thing. They come in many shapes, sizes, and colors."
        )
    ],
    "memories": [
        (
            "Why do people keep photo albums?",
            "Photo albums hold pictures from the past so families can remember times they loved. Looking through one can bring back stories and smiles."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room = f["room"]
    target = f["target_cfg"]
    unsafe = f["unsafe_cfg"]
    aid = f["aid_cfg"]
    child = f["child"]
    grandparent = f["grandparent"]
    name = child.attrs["name"]
    gp = grandparent.label_word
    return [
        f'Write a short rhyming story for a 3-to-5-year-old set in {gp}\'s house, and include the word "proceeding".',
        f"Tell a happy story where {name} wants {target.the} from a high shelf in {room.label}, tries {unsafe.phrase}, and then learns to proceed safely with {aid.phrase}.",
        f"Write a gentle poem-story about a child and {gp} choosing a safer plan before reaching too high for {target.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    room = f["room"]
    target = f["target_cfg"]
    unsafe = f["unsafe_cfg"]
    aid = f["aid_cfg"]
    child = f["child"]
    grandparent = f["grandparent"]
    name = child.attrs["name"]
    gp = grandparent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {name} and {gp} in {room.label} at grandparent's house. {name} wanted {target.the} from the high {room.shelf_word}."
        ),
        (
            f"Why did {child.attrs['name']} want {target.the}?",
            f"{name} wanted {target.the} so they could {target.purpose}. The wish to use or share it is what started the reaching problem."
        ),
        (
            f"Why was standing on {unsafe.phrase} a bad idea?",
            f"It was risky because {unsafe.phrase} was not steady enough for that reach. In the world model, that perch could wobble before {name} got safely down."
        ),
    ]
    if f.get("wobble_started"):
        qa.append(
            (
                "What happened when the child tried the risky way?",
                f"A wobble started, and the brave idea suddenly felt scary. That small wobble is why {gp} stepped in right away with calm help."
            )
        )
    qa.append(
        (
            f"How did {gp} solve the problem?",
            f"{gp.capitalize()} used {aid.phrase} to make the reach safe. That worked because it fit the shelf height and the kind of object they were trying to get."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily with {name} getting {target.the} safely and sharing a cozy moment with {gp}. The ending shows that careful help changed a near-mistake into a warm success."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["target_cfg"].tags)
    aid = f["aid_cfg"]
    if aid.id == "step_stool":
        tags.add("stool")
    if aid.id == "ladder":
        tags.add("ladder")
    if aid.id == "reacher":
        tags.add("reacher")
    if aid.id == "grandparent_help":
        tags.add("adult")
    if "glass" in tags:
        tags.add("adult")
    ordered = [
        "high_shelf",
        "glass",
        "stool",
        "ladder",
        "reacher",
        "adult",
        "cookies",
        "jam",
        "cups",
        "kite",
        "buttons",
        "memories",
    ]
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:11} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: predicted_wobble={world.facts.get('predicted_wobble')} retrieved={world.facts.get('retrieved')}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="kitchen",
        target="cookie_tin",
        unsafe="books",
        aid="step_stool",
        child_name="Lila",
        child_gender="girl",
        grandparent="grandmother",
        trait="eager",
        seed=None,
    ),
    StoryParams(
        room="kitchen",
        target="teacups",
        unsafe="wheely_chair",
        aid="ladder",
        child_name="Theo",
        child_gender="boy",
        grandparent="grandmother",
        trait="curious",
        seed=None,
    ),
    StoryParams(
        room="hall",
        target="kite_box",
        unsafe="toy_crate",
        aid="grandparent_help",
        child_name="Mina",
        child_gender="girl",
        grandparent="grandfather",
        trait="bouncy",
        seed=None,
    ),
    StoryParams(
        room="sewing_room",
        target="button_tin",
        unsafe="books",
        aid="reacher",
        child_name="Owen",
        child_gender="boy",
        grandparent="grandmother",
        trait="bright",
        seed=None,
    ),
    StoryParams(
        room="sewing_room",
        target="photo_album",
        unsafe="wheely_chair",
        aid="ladder",
        child_name="Ruby",
        child_gender="girl",
        grandparent="grandfather",
        trait="gentle",
        seed=None,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a child at grandparent's house reaches too high, wobbles, and learns to proceed safely."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--unsafe", choices=UNSAFE_PERCHES)
    ap.add_argument("--aid", choices=SAFE_AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grandparent", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.target and args.target not in ROOMS[args.room].affords:
        raise StoryError(explain_invalid_target(ROOMS[args.room], TARGETS[args.target]))
    if args.target and args.aid:
        if not safe_solution(TARGETS[args.target], SAFE_AIDS[args.aid]):
            raise StoryError(explain_invalid_aid(TARGETS[args.target], SAFE_AIDS[args.aid]))

    combos = [
        c for c in valid_combos()
        if (args.room is None or c[0] == args.room)
        and (args.target is None or c[1] == args.target)
        and (args.unsafe is None or c[2] == args.unsafe)
        and (args.aid is None or c[3] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, target_id, unsafe_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grandparent = args.grandparent or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        room=room_id,
        target=target_id,
        unsafe=unsafe_id,
        aid=aid_id,
        child_name=name,
        child_gender=gender,
        grandparent=grandparent,
        trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.unsafe not in UNSAFE_PERCHES:
        raise StoryError(f"(Unknown unsafe perch: {params.unsafe})")
    if params.aid not in SAFE_AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    room = ROOMS[params.room]
    target = TARGETS[params.target]
    unsafe = UNSAFE_PERCHES[params.unsafe]
    aid = SAFE_AIDS[params.aid]

    if params.target not in room.affords:
        raise StoryError(explain_invalid_target(room, target))
    if not wobble_begins(target, unsafe):
        raise StoryError(
            f"(No story: {unsafe.phrase} is not risky enough for {target.the} here, so the middle turn never honestly starts.)"
        )
    if not safe_solution(target, aid):
        raise StoryError(explain_invalid_aid(target, aid))

    world = tell(
        room=room,
        target=target,
        unsafe=unsafe,
        aid=aid,
        child_name=params.child_name,
        child_gender=params.child_gender,
        grandparent_type=params.grandparent,
        trait=params.trait,
    )

    story = world.render().replace("child", params.child_name).replace("grandparent", world.get("grandparent").label_word.capitalize())
    story = story.replace("At grandma's house", "At grandma's house").replace("At grandpa's house", "At grandpa's house")
    story = story.replace(" child ", f" {params.child_name} ").replace(" child,", f" {params.child_name},")
    story = story.replace(" child.", f" {params.child_name}.")
    story = story.replace(" child's ", f" {params.child_name}'s ")
    story = story.replace(" grandparent ", f" {world.get('grandparent').label_word} ")

    for wrong in ("child", "grandparent"):
        if wrong in story:
            pass

    return StorySample(
        params=params,
        story=story.replace("  ", " "),
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
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("(Generated empty story.)")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random resolve/generate smoke test passed for 20 seeds.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (room, target, unsafe, aid) combos:\n")
        for room, target, unsafe, aid in combos:
            print(f"  {room:12} {target:12} {unsafe:12} {aid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.target} in {p.room} ({p.unsafe} -> {p.aid})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
