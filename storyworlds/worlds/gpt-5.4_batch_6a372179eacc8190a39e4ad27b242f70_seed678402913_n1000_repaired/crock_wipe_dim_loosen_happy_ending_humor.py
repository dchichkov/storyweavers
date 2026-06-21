#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/crock_wipe_dim_loosen_happy_ending_humor.py
======================================================================

A standalone story world about two children playing pirates, a dim pantry, and a
heavy crock of "treasure" on a high shelf. One child is tempted to use a silly,
unsafe shortcut to reach it. A cautious child warns them, a grown-up helps the
sensible way, and the ending proves what they learned.

Seed words rebuilt into world state:
- crock: the treasure sits in a heavy ceramic crock
- wipe-dim: the family jokingly says "wipe-dim" when a dusty flashlight lens
  needs a quick wipe to shine properly again
- loosen: the tempting shortcut usually tries to loosen or hook something the
  wrong way instead of asking for help

The style stays close to a playful pirate tale: pretend roles, a dark "cave,"
a risky idea, a turn, and a bright safe ending with a small laugh.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "sensible", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    heavy: bool = False
    fragile: bool = False
    dusty: bool = False
    movable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
class Theme:
    id: str
    scene: str
    rig: str
    title_a: str
    title_b: str
    goal: str
    dark_spot: str
    cave_word: str
    role_solo: str
    role_plural: str
    send_off: str


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    lid_word: str
    treasure: str
    shelf: str
    height: int
    wobble: int
    heavy: bool = True
    fragile: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"


@dataclass
class UnsafeMethod:
    id: str
    label: str
    action: str
    setup: str
    risk: int
    power: int
    sense: int
    fail_text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeAid:
    id: str
    label: str
    action: str
    ending_line: str
    sense: int
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
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_wobble(world: World) -> list[str]:
    vessel = world.get("vessel")
    if vessel.meters["wobbling"] < THRESHOLD:
        return []
    sig = ("wobble", "vessel")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["fear"] += 1
    world.get("room").meters["danger"] += 1
    return ["__wobble__"]


def _r_spill(world: World) -> list[str]:
    vessel = world.get("vessel")
    if vessel.meters["tilted"] < THRESHOLD:
        return []
    sig = ("spill", "vessel")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vessel.meters["spilled"] += 1
    room = world.get("room")
    room.meters["mess"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def sensible_aids() -> list[SafeAid]:
    return [aid for aid in SAFE_AIDS.values() if aid.sense >= SENSE_MIN]


def hazard_at_risk(vessel: Vessel, method: UnsafeMethod) -> bool:
    return vessel.height > 0 and vessel.heavy and method.risk >= 2


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    base = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    authority = base + 1.0 + (4.0 if older else 0.0)
    return older and authority > BRAVERY_INIT


def spill_happens(vessel: Vessel, method: UnsafeMethod) -> bool:
    return method.power < vessel.wobble


def predict_trouble(world: World, method_id: str) -> dict:
    sim = world.copy()
    method = METHODS[method_id]
    vessel = VESSELS[sim.facts["vessel_cfg"].id]
    _do_unsafe(sim, vessel=vessel, method=method, narrate=False)
    return {
        "wobble": sim.get("vessel").meters["wobbling"] >= THRESHOLD,
        "spill": sim.get("vessel").meters["spilled"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def _do_unsafe(world: World, vessel: Vessel, method: UnsafeMethod, narrate: bool = True) -> None:
    vessel_ent = world.get("vessel")
    vessel_ent.meters["wobbling"] += 1
    vessel_ent.meters["tilted"] += 1 if spill_happens(vessel, method) else 0
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"On a rainy afternoon, {a.id} and {b.id} turned the kitchen into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.title_a} {a.id} and {theme.title_b} {b.id}!" {a.id} said. '
        f'"Let\'s find {theme.goal}!"'
    )


def find_dark_spot(world: World, b: Entity, theme: Theme, vessel: Vessel) -> None:
    world.say(
        f"But the {theme.cave_word} -- {theme.dark_spot}, with {vessel.the} waiting {vessel.shelf} -- "
        f"looked dim and secret."
    )
    world.say(
        f'{b.id} squinted. "Our light looks sleepy," {b.pronoun()} said.'
    )


def wipe_dim_light(world: World, a: Entity, b: Entity) -> None:
    lantern = world.get("light")
    if lantern.dusty:
        lantern.dusty = False
        lantern.meters["bright"] += 1
        world.say(
            f'{b.id} rubbed the dusty flashlight window on a dish towel. '
            f'"There," {b.pronoun()} said. "A little wipe-dim, and now it shines again."'
        )
        a.memes["amusement"] += 1
        b.memes["amusement"] += 1
        world.facts["wiped_dim"] = True


def tempt(world: World, a: Entity, method: UnsafeMethod, vessel: Vessel) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id} pointed at {vessel.the}. "{vessel.treasure.capitalize()}!" '
        f'{a.pronoun().capitalize()} whispered. "I can get it if I {method.action}."'
    )
    world.say(method.setup)


def warn(world: World, a: Entity, b: Entity, parent: Entity, vessel: Vessel, method: UnsafeMethod) -> None:
    pred = predict_trouble(world, method.id)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    spill = "and spill the treasure all over the floor" if pred["spill"] else "and make it wobble"
    world.say(
        f'{b.id} grabbed {a.pronoun("possessive")} sleeve. "{a.id}, don\'t. '
        f'{parent.label_word.capitalize()} said we must ask for help with high shelves. '
        f'You could bump {vessel.the} {spill}."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} made a face, then puffed out one dramatic pirate sigh. '
        f'"A captain can wait for a harbor helper," {a.pronoun()} said.'
    )
    world.say(
        f"They went to find {parent.label_word}, still carrying the flashlight and their paper map."
    )
    world.facts["attempted"] = False
    world.facts["outcome"] = "averted"


def defy(world: World, a: Entity, b: Entity, method: UnsafeMethod) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"It will only take one tiny pirate reach," {a.id} said, and {a.pronoun()} tried to {method.action}.'
    )
    if b.attrs.get("trust", 0) >= 7:
        world.say(
            f"For half a breath, {b.id} trusted {a.pronoun('object')}. Then the whole plan looked wobblier than a jellyfish on skates."
        )


def trouble(world: World, a: Entity, b: Entity, vessel: Vessel, method: UnsafeMethod) -> None:
    _do_unsafe(world, vessel=vessel, method=method, narrate=False)
    world.facts["attempted"] = True
    vessel_ent = world.get("vessel")
    if vessel_ent.meters["spilled"] >= THRESHOLD:
        world.say(method.fail_text.format(vessel=vessel.label, treasure=vessel.treasure))
        world.say(
            f"The lid jumped, {vessel.treasure} flew out, and both little pirates stared as if a snack storm had attacked the ship."
        )
        world.facts["outcome"] = "spill"
    else:
        world.say(method.fail_text.format(vessel=vessel.label, treasure=vessel.treasure))
        world.say(
            f"{vessel.the.capitalize()} rocked once, then twice, and stopped with a scary clunk that made both children freeze."
        )
        world.facts["outcome"] = "wobble"


def alarm(world: World, b: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {b.id} yelped. "We need harbor help!"')


def rescue(world: World, parent: Entity, aid: SafeAid, vessel: Vessel) -> None:
    world.get("room").meters["danger"] = 0.0
    world.get("vessel").meters["wobbling"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in fast, took one look, and did not laugh until the danger was gone. "
        f"{parent.pronoun().capitalize()} {aid.action}."
    )
    if world.get("vessel").meters["spilled"] >= THRESHOLD:
        world.say(
            f'Soon {vessel.treasure} was back where it belonged, and the floor no longer looked like a seagull picnic.'
        )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, vessel: Vessel, aid: SafeAid) -> None:
    for kid in (a, b):
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, nobody spoke except the refrigerator, which hummed like a sleepy sea monster.")
    world.say(
        f'Then {parent.label_word.capitalize()} knelt beside them. '
        f'"I am glad you called me," {parent.pronoun()} said. '
        f'"Heavy things on high shelves are not for guessing games. '
        f'When something is too high or too tight, ask a grown-up instead of trying to loosen it the risky way."'
    )
    world.say(
        f'{a.id} nodded. "{vessel.the.capitalize()} is heavier than pirate stories make it look," {a.pronoun()} admitted.'
    )
    world.say(
        f'{b.id} sniffed, then smiled a little. "And {aid.label} beats a jellyfish-on-skates plan," {b.pronoun()} said.'
    )


def safe_ending(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, vessel: Vessel, aid: SafeAid) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f'{parent.label_word.capitalize()} opened {vessel.the} properly and shared out {vessel.treasure}. '
        f'"Now," {parent.pronoun()} smiled, "what does {theme.role_solo} use when treasure sits too high?"'
    )
    world.say(
        f'"A grown-up and {aid.label}!" {a.id} and {b.id} shouted together.'
    )
    world.say(aid.ending_line)
    world.say(
        f"When they sailed back into their game, the map was still crinkly, the flashlight was bright from its wipe-dim, and the pirates were laughing instead of wobbling."
    )


def tell(
    theme: Theme,
    vessel: Vessel,
    method: UnsafeMethod,
    aid: SafeAid,
    *,
    instigator: str,
    instigator_gender: str,
    cautioner: str,
    cautioner_gender: str,
    trait: str,
    parent_type: str,
    relation: str,
    instigator_age: int,
    cautioner_age: int,
    trust: int,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation, "trust": trust},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="kitchen", label="the kitchen"))
    world.add(Entity(
        id="vessel",
        type="crock",
        label=vessel.label,
        phrase=vessel.phrase,
        heavy=vessel.heavy,
        fragile=vessel.fragile,
        tags=set(vessel.tags),
    ))
    world.add(Entity(
        id="light",
        type="flashlight",
        label="flashlight",
        phrase="a little flashlight",
        dusty=True,
        tags={"flashlight", "wipe-dim"},
    ))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    b.memes["trust"] = float(trust)

    world.facts.update(
        theme=theme,
        vessel_cfg=vessel,
        method=method,
        aid=aid,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
        wiped_dim=False,
    )

    play_setup(world, a, b, theme)
    find_dark_spot(world, b, theme, vessel)
    wipe_dim_light(world, a, b)

    world.para()
    tempt(world, a, method, vessel)
    warn(world, a, b, parent, vessel, method)

    if would_avert(relation, instigator_age, cautioner_age, trait):
        back_down(world, a, b, parent, theme)
    else:
        defy(world, a, b, method)
        world.para()
        trouble(world, a, b, vessel, method)
        alarm(world, b, parent)

    world.para()
    rescue(world, parent, aid, vessel)
    lesson(world, parent, a, b, vessel, aid)

    world.para()
    safe_ending(world, parent, a, b, theme, vessel, aid)

    world.facts["spilled"] = world.get("vessel").meters["spilled"] >= THRESHOLD
    world.facts["promised"] = a.memes["lesson"] >= THRESHOLD
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a tiny pirate galley",
        rig="The table was their ship, a dish towel became a sail, a wooden spoon served as a cutlass, and a crayon map showed where the biscuit treasure was hidden.",
        title_a="Captain",
        title_b="Lookout",
        goal="the pantry cave",
        dark_spot="the pantry door beside the fridge",
        cave_word="cave",
        role_solo="a pirate",
        role_plural="pirates",
        send_off="sailed back toward the pantry cave",
    ),
    "buccaneers": Theme(
        id="buccaneers",
        scene="a stormy pirate deck",
        rig="The kitchen chairs became masts, a colander was a captain's helmet, and a floury map pointed to the secret biscuit hoard.",
        title_a="Captain",
        title_b="Scout",
        goal="the biscuit hoard",
        dark_spot="the pantry nook under the high shelf",
        cave_word="nook",
        role_solo="a buccaneer",
        role_plural="buccaneers",
        send_off="marched back to their deck with brave stomps",
    ),
}

VESSELS = {
    "cookie_crock": Vessel(
        id="cookie_crock",
        label="crock",
        phrase="a blue cookie crock",
        lid_word="lid",
        treasure="ginger snaps",
        shelf="on the highest pantry shelf",
        height=2,
        wobble=3,
        heavy=True,
        fragile=True,
        tags={"crock", "cookies"},
    ),
    "pretzel_crock": Vessel(
        id="pretzel_crock",
        label="crock",
        phrase="a speckled pretzel crock",
        lid_word="lid",
        treasure="pretzel twists",
        shelf="on the top shelf by the cereal",
        height=2,
        wobble=2,
        heavy=True,
        fragile=True,
        tags={"crock", "pretzels"},
    ),
    "cracker_crock": Vessel(
        id="cracker_crock",
        label="crock",
        phrase="a fat cracker crock",
        lid_word="lid",
        treasure="cheese crackers",
        shelf="above the mixing bowls",
        height=2,
        wobble=2,
        heavy=True,
        fragile=True,
        tags={"crock", "crackers"},
    ),
    "floor_basket": Vessel(
        id="floor_basket",
        label="basket",
        phrase="a wicker snack basket",
        lid_word="top",
        treasure="apple slices",
        shelf="right on the floor",
        height=0,
        wobble=0,
        heavy=False,
        fragile=False,
        tags={"basket"},
    ),
}

METHODS = {
    "broom_hook": UnsafeMethod(
        id="broom_hook",
        label="broom hook",
        action="hook the crock with the broom handle",
        setup="The plan sounded clever for exactly one second.",
        risk=3,
        power=1,
        sense=2,
        fail_text="The broom slipped with a wooden clack against the {vessel}.",
        qa_text="tried to hook the crock with a broom handle",
        tags={"broom", "reach_high"},
    ),
    "wheeled_chair": UnsafeMethod(
        id="wheeled_chair",
        label="wheeled chair",
        action="climb onto the wheeled chair and reach for the crock",
        setup="The chair gave a tiny squeak, which was not a brave pirate sound at all.",
        risk=3,
        power=1,
        sense=2,
        fail_text="The wheeled chair skittered, and the captain's reach bumped the {vessel}.",
        qa_text="climbed on a wheeled chair to reach the crock",
        tags={"chair", "reach_high"},
    ),
    "loosen_lid": UnsafeMethod(
        id="loosen_lid",
        label="loosen lid with spoon",
        action="stand on tiptoes and poke the lid to loosen it with a spoon",
        setup='"{0}" was what {1} called the plan: brave in pirate words, not so brave in a real kitchen.',
        risk=2,
        power=1,
        sense=2,
        fail_text="The spoon rang on the {vessel}, and the lid jumped crooked.",
        qa_text="poked the lid with a spoon to loosen it",
        tags={"loosen", "spoon"},
    ),
    "table_pull": UnsafeMethod(
        id="table_pull",
        label="tablecloth yank",
        action="yank the little towel sail and hope the crock slid closer",
        setup="It was a plan with more imagination than sense.",
        risk=3,
        power=0,
        sense=1,
        fail_text="The towel flapped, nothing good came of it, and the {vessel} lurched.",
        qa_text="yanked the towel under the crock",
        tags={"cloth", "too_silly"},
    ),
}

SAFE_AIDS = {
    "step_stool": SafeAid(
        id="step_stool",
        label="the step stool",
        action="set the step stool in place, held the crock with two careful hands, and opened it the slow safe way",
        ending_line="Then the pirates climbed down from the step stool one at a time and marched off with crumbs on their cheeks and no broken crock at all.",
        sense=3,
        tags={"step_stool", "ask_adult"},
    ),
    "counter_help": SafeAid(
        id="counter_help",
        label="a grown-up reach",
        action="lifted the crock down to the counter first, then loosened the lid with a rubber grip",
        ending_line="Soon the pirate game sailed on, and nobody had to pretend the floor was an ocean of spilled crackers anymore.",
        sense=3,
        tags={"adult_help", "ask_adult"},
    ),
    "dish_towel": SafeAid(
        id="dish_towel",
        label="a folded dish towel",
        action="wrapped a folded dish towel around the crock, steadied it on the counter, and opened the lid properly",
        ending_line="After that, the whole crew crunched treasure and laughed at how badly Captain Wobble had steered.",
        sense=2,
        tags={"dish_towel", "ask_adult"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Theo"]
TRAITS = ["careful", "cautious", "steady", "clever", "thoughtful", "sensible"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_aids():
        return combos
    for theme_id in THEMES:
        for vessel_id, vessel in VESSELS.items():
            for method_id, method in METHODS.items():
                if method.sense >= SENSE_MIN and hazard_at_risk(vessel, method):
                    combos.append((theme_id, vessel_id, method_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    vessel: str
    method: str
    aid: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    relation: str = "siblings"
    instigator_age: int = 6
    cautioner_age: int = 4
    trust: int = 6
    seed: Optional[int] = None


KNOWLEDGE = {
    "crock": [(
        "What is a crock?",
        "A crock is a heavy pot or jar, often made of thick clay or ceramic. Because it can be heavy and breakable, a grown-up should help if it is on a high shelf."
    )],
    "wipe-dim": [(
        "What does wipe-dim mean in this story?",
        "It is a silly family way to say, 'wipe the dusty light so it is not dim anymore.' A quick wipe can help a flashlight shine better if the outside is smudged."
    )],
    "loosen": [(
        "What does loosen mean?",
        "Loosen means make something less tight. If a lid is too tight, it is safer to ask a grown-up than to poke or yank at it."
    )],
    "ask_adult": [(
        "What should you do if something heavy is too high to reach?",
        "Ask a grown-up for help right away. Heavy things can fall and break if you try a risky shortcut."
    )],
    "step_stool": [(
        "Why is a step stool safer than climbing on a wheeled chair?",
        "A step stool is made to stand on and does not roll away as easily. A wheeled chair can slide, which makes reaching high places unsafe."
    )],
    "adult_help": [(
        "Why do grown-ups use two hands with breakable things?",
        "Two hands give better control and help hold a heavy object steady. That makes dropping or tipping it less likely."
    )],
    "dish_towel": [(
        "Why can a towel help with a tight lid?",
        "A towel can help your hand grip a slippery lid better. But a grown-up should still do it if the jar or crock is heavy."
    )],
}
KNOWLEDGE_ORDER = ["crock", "wipe-dim", "loosen", "ask_adult", "step_stool", "adult_help", "dish_towel"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    vessel = f["vessel_cfg"]
    method = f["method"]
    aid = f["aid"]
    theme = f["theme"]
    if f["outcome"] == "averted":
        return [
            f'Write a pirate-style kitchen story for a 3-to-5-year-old where two children want snack treasure from a high {vessel.label}, but one child stops the other before anything falls. Include the word "crock".',
            f"Tell a gentle near-miss story where {a.id} wants to {method.action}, but {b.id} warns {a.pronoun('object')} and they ask a grown-up instead.",
            'Write a funny story with the exact word "wipe-dim" and a happy ending where the lesson is to ask for help with heavy things on high shelves.',
        ]
    return [
        f'Write a pirate-style cautionary story for a 3-to-5-year-old where two children chase treasure in a pantry cave, a high crock wobbles, and a grown-up helps the safe way. Include the words "crock", "wipe-dim", and "loosen".',
        f"Tell a humorous story where {a.id} tries to {method.action}, but the plan goes wrong and a grown-up uses {aid.label} to fix the problem.",
        f"Write a warm story with a lesson learned: do not use silly shortcuts with heavy things, and end with the children laughing and eating {vessel.treasure}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    vessel = f["vessel_cfg"]
    method = f["method"]
    aid = f["aid"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who were playing pirates in the kitchen, and their {parent.label_word} who helped them."
        ),
        (
            "What treasure were they looking for?",
            f"They were trying to reach {vessel.treasure} inside {vessel.the} on a high shelf. The high shelf is what made the problem begin."
        ),
        (
            'Why did the story use the funny word "wipe-dim"?',
            "The flashlight looked dusty and dull, so one child wiped it to make it shine better. They joked that a quick 'wipe-dim' could wake the light up."
        ),
        (
            f"What risky idea did {a.id} have?",
            f"{a.id} wanted to {method.action}. That was risky because {vessel.the} was heavy and high up."
        ),
    ]
    if outcome == "averted":
        qa.append((
            f"How was the problem solved before anything fell?",
            f"{b.id} warned {a.id}, and {a.id} listened instead of trying the shortcut. Then they got their {parent.label_word}, who used {aid.label} and opened the crock safely."
        ))
    elif outcome == "wobble":
        qa.append((
            f"What happened when {a.id} tried the shortcut?",
            f"{vessel.the.capitalize()} wobbled and scared both children, but it did not spill. They called for help fast, which kept the moment from getting worse."
        ))
        qa.append((
            f"How did their {parent.label_word} fix it?",
            f"Their {parent.label_word} used {aid.label} and handled the crock carefully with both hands. That worked because a steady, sensible method is better than guessing with something heavy."
        ))
    else:
        qa.append((
            f"What happened when {a.id} tried the shortcut?",
            f"The crock tipped and spilled {vessel.treasure} onto the floor. The trouble started because {a.id} used a risky shortcut instead of asking for help."
        ))
        qa.append((
            f"Why is the ending still happy if there was a spill?",
            f"Everyone stayed safe, and their {parent.label_word} cleaned up and opened the crock the right way. The children learned the lesson and were laughing again by the end."
        ))
    qa.append((
        "What lesson did the children learn?",
        "They learned to ask a grown-up for help with heavy things on high shelves. They also learned that a funny pirate plan is not always a safe real-life plan."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"crock", "wipe-dim", "ask_adult"}
    if "loosen" in f["method"].tags:
        tags.add("loosen")
    tags |= set(f["aid"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        flags = [name for name, on in (
            ("heavy", ent.heavy),
            ("fragile", ent.fragile),
            ("dusty", ent.dusty),
            ("movable", ent.movable),
        ) if on]
        if flags:
            bits.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        vessel="cookie_crock",
        method="broom_hook",
        aid="step_stool",
        instigator="Tom",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        instigator_age=6,
        cautioner_age=4,
        trust=7,
    ),
    StoryParams(
        theme="buccaneers",
        vessel="pretzel_crock",
        method="wheeled_chair",
        aid="counter_help",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="steady",
        relation="friends",
        instigator_age=5,
        cautioner_age=5,
        trust=3,
    ),
    StoryParams(
        theme="pirates",
        vessel="cracker_crock",
        method="loosen_lid",
        aid="dish_towel",
        instigator="Sam",
        instigator_gender="boy",
        cautioner="Theo",
        cautioner_gender="boy",
        parent="mother",
        trait="cautious",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
        trust=4,
    ),
]


def explain_rejection(vessel: Vessel, method: UnsafeMethod) -> str:
    if vessel.height <= 0:
        return (
            f"(No story: {vessel.phrase} is not on a high shelf, so {method.action} would not create a real reaching problem. "
            f"Pick a vessel on a shelf so the warning and lesson make sense.)"
        )
    if not vessel.heavy:
        return (
            f"(No story: {vessel.phrase} is too light for this world's 'ask for help with heavy things' lesson.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too silly even for a pirate game "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {', '.join(sorted(m.id for m in METHODS.values() if m.sense >= SENSE_MIN))}.)"
        )
    return "(No story: this combination does not create the right kind of pantry hazard.)"


def explain_aid(aid_id: str) -> str:
    aid = SAFE_AIDS[aid_id]
    return (
        f"(Refusing aid '{aid_id}': it scores too low on common sense "
        f"(sense={aid.sense} < {SENSE_MIN}).)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "spill" if spill_happens(VESSELS[params.vessel], METHODS[params.method]) else "wobble"


ASP_RULES = r"""
hazard(V, M) :- high(V), heavy(V), method(M), risk(M, R), R >= 2.
sensible_method(M) :- method(M), method_sense(M, S), sense_min(N), S >= N.
sensible_aid(A) :- aid(A), aid_sense(A, S), sense_min(N), S >= N.
valid(T, V, M) :- theme(T), vessel(V), method(M), hazard(V, M), sensible_method(M).

cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
cautious_trait(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_trait(T).
init_caution(3) :- trait(T), not cautious_trait(T).
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

spill :- chosen_vessel(V), chosen_method(M), wobble_need(V, W), method_power(M, P), P < W.

outcome(averted) :- averted.
outcome(spill) :- not averted, spill.
outcome(wobble) :- not averted, not spill.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        if vessel.height > 0:
            lines.append(asp.fact("high", vessel_id))
        if vessel.heavy:
            lines.append(asp.fact("heavy", vessel_id))
        lines.append(asp.fact("wobble_need", vessel_id, vessel.wobble))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("risk", method_id, method.risk))
        lines.append(asp.fact("method_power", method_id, method.power))
        lines.append(asp.fact("method_sense", method_id, method.sense))
    for aid_id, aid in SAFE_AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("aid_sense", aid_id, aid.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_vessel", params.vessel),
        asp.fact("chosen_method", params.method),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate pantry treasure, a high crock, a silly shortcut, and a safe happy ending."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--aid", choices=SAFE_AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.vessel and args.method:
        vessel = VESSELS[args.vessel]
        method = METHODS[args.method]
        if not (hazard_at_risk(vessel, method) and method.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(vessel, method))
    if args.vessel and VESSELS[args.vessel].height <= 0:
        method = METHODS[args.method] if args.method else METHODS[next(iter(METHODS))]
        raise StoryError(explain_rejection(VESSELS[args.vessel], method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        vessel = VESSELS[args.vessel] if args.vessel else VESSELS["cookie_crock"]
        raise StoryError(explain_rejection(vessel, METHODS[args.method]))
    if args.aid and SAFE_AIDS[args.aid].sense < SENSE_MIN:
        raise StoryError(explain_aid(args.aid))

    combos = [
        combo for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, vessel_id, method_id = rng.choice(sorted(combos))
    aid_id = args.aid or rng.choice(sorted(aid.id for aid in sensible_aids()))
    instigator, instigator_gender = _pick_kid(rng)
    cautioner, cautioner_gender = _pick_kid(rng, avoid=instigator)
    relation = rng.choice(["siblings", "friends"])
    ages = rng.sample([3, 4, 5, 6, 7], 2)
    trait = rng.choice(TRAITS)
    trust = rng.randint(0, 10)
    return StoryParams(
        theme=theme_id,
        vessel=vessel_id,
        method=method_id,
        aid=aid_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        parent=args.parent or rng.choice(["mother", "father"]),
        trait=trait,
        relation=relation,
        instigator_age=ages[0],
        cautioner_age=ages[1],
        trust=trust,
    )


def _method_setup(params: StoryParams) -> UnsafeMethod:
    method = METHODS[params.method]
    if method.id == "loosen_lid":
        text = method.setup.format("Loosen and snatch", params.instigator)
        return UnsafeMethod(
            id=method.id,
            label=method.label,
            action=method.action,
            setup=text,
            risk=method.risk,
            power=method.power,
            sense=method.sense,
            fail_text=method.fail_text,
            qa_text=method.qa_text,
            tags=set(method.tags),
        )
    return method


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        vessel = VESSELS[params.vessel]
        aid = SAFE_AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None
    method = _method_setup(params)
    if not hazard_at_risk(vessel, method) or method.sense < SENSE_MIN:
        raise StoryError(explain_rejection(vessel, method))
    if aid.sense < SENSE_MIN:
        raise StoryError(explain_aid(params.aid))

    world = tell(
        theme=theme,
        vessel=vessel,
        method=method,
        aid=aid,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        parent_type=params.parent,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        trust=params.trust,
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
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
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
        print(f"{len(combos)} compatible (theme, vessel, method) combos:\n")
        for theme_id, vessel_id, method_id in combos:
            print(f"  {theme_id:11} {vessel_id:13} {method_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.method} with {p.vessel} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
