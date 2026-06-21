#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py
=================================================================================

A standalone story world for a small, spooky-at-first swimming-pool tale.

Seed premise rebuilt as simulation
----------------------------------
A child at an indoor swimming pool wants praise for helping after swim class.
But one toy is left near a dim, echoing part of the pool. A harmless pool sound
or shadow makes that place seem haunted. Another child presses the hero to go
alone. Inside the hero's head, wanting praise pulls one way and fear pulls the
other. The problem is solved only when the hero chooses a safe method that truly
fits the depth and the kind of spooky mistake.

This world keeps a gentle "ghost story" feeling without making the world
actually supernatural. The turn comes from a mistaken ghost guess, and the
resolution proves what changed: the child learns that asking for help can be
brave, and that careful choices earn better praise than risky ones do.

Run it
------
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py --cause drain_bubbles --item silver_ring
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py --solution sneak_alone
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py --all
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py -n 5 --seed 777 --qa
    python storyworlds/worlds/gpt-5.4/praise_burst_swimming_pool_inner_monologue_conflict.py --verify
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
SENSE_MIN = 2
DEPTH_ORDER = {"steps": 1, "middle": 2, "deep": 3}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach_woman"}
        male = {"boy", "father", "man", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"mother", "father"}:
            return {"mother": "mom", "father": "dad"}[self.type]
        if self.type in {"coach_woman", "coach_man"}:
            return "coach"
        return self.label or self.type
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
class Cause:
    id: str
    label: str
    zone: str
    mode: str
    sign: str
    sign_burst: str
    ghost_guess: str
    reveal: str
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
class PoolItem:
    id: str
    label: str
    phrase: str
    zone: str
    kind: str
    scene: str
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
class Solution:
    id: str
    label: str
    sense: int
    max_depth: int
    modes: set[str]
    retrieves: set[str]
    adult_needed: bool
    action: str
    reveal_text: str
    praise_text: str
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


def _r_spook(world: World) -> list[str]:
    cause = world.get("cause")
    hero = world.get("hero")
    if cause.meters["active"] < THRESHOLD:
        return []
    sig = ("spook", cause.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["ghost_guess"] += 1
    world.get("pool").memes["unease"] += 1
    return []


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    peer = world.get("peer")
    if hero.memes["desire"] < THRESHOLD or hero.memes["fear"] < THRESHOLD:
        return []
    if peer.memes["tease"] < THRESHOLD:
        return []
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    cause = world.get("cause")
    hero = world.get("hero")
    if cause.meters["explained"] < THRESHOLD:
        return []
    sig = ("relief", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["trust"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="spook", tag="emotional", apply=_r_spook),
    Rule(name="conflict", tag="emotional", apply=_r_conflict),
    Rule(name="relief", tag="emotional", apply=_r_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        current_count = len(world.fired)
        for rule in CAUSAL_RULES:
            if len(world.fired) != current_count:
                changed = True
                break
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


CAUSES = {
    "drain_bubbles": Cause(
        id="drain_bubbles",
        label="drain bubbles",
        zone="middle",
        mode="underwater",
        sign="a necklace of silver bubbles rising from the round drain",
        sign_burst="A burst of bubbles slipped up through the blue water",
        ghost_guess="a ghost blowing secret pool-breath from under the floor",
        reveal="the filter was just pushing out clean air bubbles from the drain",
        tags={"drain", "bubbles", "pool_safety"},
    ),
    "flag_shadow": Cause(
        id="flag_shadow",
        label="lane-flag shadow",
        zone="deep",
        mode="reflection",
        sign="a long black ribbon of shadow shaking under the backstroke flags",
        sign_burst="The shadow burst and stitched itself together again when the water wrinkled",
        ghost_guess="a long ghost tail waving in the deep end",
        reveal="the dangling lane flags were making a dancing shadow on the pool floor",
        tags={"reflection", "flags", "pool_safety"},
    ),
    "vacuum_hose": Cause(
        id="vacuum_hose",
        label="vacuum hose",
        zone="deep",
        mode="object",
        sign="a pale hose swaying beside the wall like something alive",
        sign_burst="The hose gave a slow burst-like wobble when the water pump hummed",
        ghost_guess="a pool ghost curling and uncurling by the wall",
        reveal="the pool-cleaning hose was only bobbing in the moving water",
        tags={"pool_cleaner", "pool_safety"},
    ),
    "vent_echo": Cause(
        id="vent_echo",
        label="vent echo",
        zone="steps",
        mode="sound",
        sign="a soft hoo-oo sound coming from the vent near the shallow steps",
        sign_burst='A burst of echo bounced off the tiles and came back sounding bigger',
        ghost_guess="a whispering ghost hiding in the wall",
        reveal="the air vent was echoing in the empty room and making the pool sound spooky",
        tags={"echo", "sound", "pool_safety"},
    ),
}

ITEMS = {
    "silver_ring": PoolItem(
        id="silver_ring",
        label="silver ring",
        phrase="the little silver dive ring",
        zone="middle",
        kind="sink",
        scene="resting on the blue line halfway down the lane",
        tags={"dive_ring"},
    ),
    "foam_ball": PoolItem(
        id="foam_ball",
        label="foam ball",
        phrase="the foam practice ball",
        zone="steps",
        kind="float",
        scene="bobbing near the shallow steps",
        tags={"float_toy"},
    ),
    "red_kickboard": PoolItem(
        id="red_kickboard",
        label="red kickboard",
        phrase="the red kickboard",
        zone="deep",
        kind="float",
        scene="drifting near the rope at the deep end",
        tags={"kickboard"},
    ),
    "shell_toy": PoolItem(
        id="shell_toy",
        label="shell toy",
        phrase="the little shell dive toy",
        zone="middle",
        kind="sink",
        scene="lying on the tiles where the water turned darker",
        tags={"dive_toy"},
    ),
}

SOLUTIONS = {
    "buddy_goggles": Solution(
        id="buddy_goggles",
        label="goggles with coach",
        sense=3,
        max_depth=2,
        modes={"underwater", "reflection", "sound"},
        retrieves={"sink", "float"},
        adult_needed=True,
        action="asked Coach to come with a pair of goggles and a steady hand on the rail",
        reveal_text="With clear goggles and Coach right there, the scary shape looked ordinary at once.",
        praise_text="That was brave and careful.",
        tags={"goggles", "ask_for_help"},
    ),
    "lifeguard_net": Solution(
        id="lifeguard_net",
        label="lifeguard net",
        sense=3,
        max_depth=3,
        modes={"underwater", "reflection", "sound", "object"},
        retrieves={"sink", "float"},
        adult_needed=True,
        action="called the lifeguard, who came with the long pool net",
        reveal_text="From the deck, the lifeguard reached in safely and showed the trick of the shadow and the water.",
        praise_text="Good thinking to ask before doing something risky.",
        tags={"lifeguard", "pool_net", "ask_for_help"},
    ),
    "sneak_alone": Solution(
        id="sneak_alone",
        label="sneak alone",
        sense=1,
        max_depth=3,
        modes={"underwater", "reflection", "sound", "object"},
        retrieves={"sink", "float"},
        adult_needed=False,
        action="slipped toward the water alone without telling a grown-up",
        reveal_text="The plan was unsafe even if it might have worked.",
        praise_text="",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Ava", "Zoe", "Nora", "Ivy", "Tessa", "Lucy"]
BOY_NAMES = ["Owen", "Finn", "Max", "Leo", "Eli", "Sam", "Theo", "Ben"]
TRAITS = ["careful", "quiet", "curious", "thoughtful", "steady", "gentle"]


def compatible(cause: Cause, item: PoolItem, solution: Solution) -> bool:
    depth = DEPTH_ORDER[cause.zone]
    return (
        cause.zone == item.zone
        and solution.sense >= SENSE_MIN
        and cause.mode in solution.modes
        and item.kind in solution.retrieves
        and depth <= solution.max_depth
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for cause_id, cause in CAUSES.items():
        for item_id, item in ITEMS.items():
            for solution_id, solution in SOLUTIONS.items():
                if compatible(cause, item, solution):
                    out.append((cause_id, item_id, solution_id))
    return sorted(out)


def sensible_solutions() -> list[Solution]:
    return [s for s in SOLUTIONS.values() if s.sense >= SENSE_MIN]


def explain_combo_rejection(cause: Cause, item: PoolItem, solution: Optional[Solution] = None) -> str:
    if cause.zone != item.zone:
        return (
            f"(No story: {cause.label} belongs in the {cause.zone} part of the pool, "
            f"but {item.phrase} is in the {item.zone} part. The spooky mistake and "
            f"the lost item need to happen in the same place.)"
        )
    if solution is not None:
        if solution.sense < SENSE_MIN:
            return (
                f"(Refusing solution '{solution.id}': it is too unsafe for this world. "
                f"Children at a pool should ask a grown-up for help instead of sneaking off alone.)"
            )
        if cause.mode not in solution.modes:
            return (
                f"(No story: {solution.label} does not honestly explain a {cause.mode} problem.)"
            )
        if item.kind not in solution.retrieves:
            return (
                f"(No story: {solution.label} cannot retrieve a {item.kind} item.)"
            )
        if DEPTH_ORDER[cause.zone] > solution.max_depth:
            return (
                f"(No story: {solution.label} is not reasonable for the {cause.zone} part of the pool.)"
            )
    return "(No valid combination matches the given options.)"


def resolution_kind(solution_id: str) -> str:
    if solution_id == "buddy_goggles":
        return "paired"
    if solution_id == "lifeguard_net":
        return "reached"
    return "unsafe"


def pool_mood(cause: Cause) -> str:
    if cause.zone == "deep":
        return "The deep end looked almost black under the high windows."
    if cause.zone == "middle":
        return "The middle lane gleamed dark blue where the light thinned out."
    return "The shallow steps shone pale, but the tiled wall still held odd little echoes."


def setup_scene(world: World, hero: Entity, peer: Entity, coach: Entity, item: PoolItem, cause: Cause) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"After swim class, the indoor swimming pool felt huge and hushy. Water tapped the lane ropes, "
        f"and the rafters threw every sound back in a thin, ghost-story whisper."
    )
    world.say(
        f'Coach smiled at the children stacking noodles and boards. "Whoever helps me gather the last toy gets my praise for being helpful," '
        f'{coach.pronoun()} said.'
    )
    world.say(
        f"{hero.id} looked across the water and spotted {item.phrase}, {item.scene}. {pool_mood(cause)}"
    )


def activate_spook(world: World, cause: Cause) -> None:
    world.get("cause").meters["active"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near it was {cause.sign}. {cause.sign_burst}"
    )


def peer_push(world: World, hero: Entity, peer: Entity, cause: Cause) -> None:
    peer.memes["tease"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Go on," {peer.id} said. "It is only the pool. Unless you think that thing is a ghost."'
    )
    fear = world.get("hero").memes["fear"]
    desire = world.get("hero").memes["desire"]
    if fear >= THRESHOLD and desire >= THRESHOLD:
        world.say(
            f"{hero.id} felt two hard pulls inside at once: wanting the praise, and wanting to stay far away from that corner."
        )


def inner_monologue(world: World, hero: Entity, cause: Cause, item: PoolItem) -> None:
    conflict = hero.memes["conflict"] >= THRESHOLD
    if conflict:
        world.say(
            f'"If I bring back {item.phrase}, Coach will smile at me," {hero.id} thought. '
            f'"But what if that is {cause.ghost_guess}? What if I reach in and it reaches back?"'
        )
    else:
        world.say(
            f'"I want the praise," {hero.id} thought, "but that place does not look right at all."'
        )


def edge_forward(world: World, hero: Entity, cause: Cause) -> None:
    hero.meters["near_edge"] += 1
    hero.memes["startle"] += 1
    world.say(
        f"{hero.id} crept to the edge and wrapped small toes over the wet tile lip. Then {cause.sign_burst.lower()}, and {hero.pronoun()} jumped back so fast that water slapped the wall."
    )


def solve_with_adult(world: World, hero: Entity, coach: Entity, cause: Cause, item: PoolItem, solution: Solution) -> None:
    item_ent = world.get("item")
    cause_ent = world.get("cause")
    hero.memes["choice_care"] += 1
    world.say(
        f"Instead of sneaking any closer, {hero.id} {solution.action}."
    )
    if solution.id == "buddy_goggles":
        item_ent.meters["retrieved"] += 1
        cause_ent.meters["explained"] += 1
        propagate(world, narrate=False)
        world.say(
            f'Coach came beside {hero.pronoun("object")} and said, "We look carefully first, together." '
            f'{solution.reveal_text}'
        )
        world.say(
            f"Under the water, they could see the truth: {cause.reveal} Coach picked up {item.phrase} and passed it to {hero.id}."
        )
    else:
        item_ent.meters["retrieved"] += 1
        cause_ent.meters["explained"] += 1
        propagate(world, narrate=False)
        world.say(
            f"{solution.reveal_text} In another second everyone could see that {cause.reveal}"
        )
        world.say(
            f"The lifeguard lifted out {item.phrase} and laid it dripping on the deck."
        )


def ending(world: World, hero: Entity, coach: Entity, solution: Solution) -> None:
    hero.memes["praised"] += 1
    world.say(
        f'Coach gave {hero.id} the warm kind of praise that made {hero.pronoun("possessive")} shoulders loosen. "{solution.praise_text}"'
    )
    world.say(
        f"{hero.id} carried the toy back to the basket. The pool still echoed, but now it sounded like ordinary splashes in an ordinary room, and not like a ghost at all."
    )


def tell(
    *,
    cause: Cause,
    item: PoolItem,
    solution: Solution,
    hero_name: str,
    hero_gender: str,
    peer_name: str,
    peer_gender: str,
    coach_gender: str,
    hero_trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[hero_trait],
            attrs={"trait": hero_trait},
        )
    )
    peer = world.add(
        Entity(
            id=peer_name,
            kind="character",
            type=peer_gender,
            role="peer",
            traits=["bold"],
            attrs={},
        )
    )
    coach_type = "coach_woman" if coach_gender == "woman" else "coach_man"
    coach = world.add(
        Entity(
            id="Coach",
            kind="character",
            type=coach_type,
            role="coach",
            label="the coach",
            attrs={},
        )
    )
    world.add(Entity(id="pool", type="pool", label="pool", attrs={}))
    world.add(
        Entity(
            id="cause",
            type="cause",
            label=cause.label,
            attrs={"mode": cause.mode, "zone": cause.zone},
        )
    )
    world.add(
        Entity(
            id="item",
            type="item",
            label=item.label,
            attrs={"kind": item.kind, "zone": item.zone},
        )
    )

    setup_scene(world, hero, peer, coach, item, cause)
    world.para()

    activate_spook(world, cause)
    peer_push(world, hero, peer, cause)
    inner_monologue(world, hero, cause, item)
    edge_forward(world, hero, cause)
    world.para()

    solve_with_adult(world, hero, coach, cause, item, solution)
    ending(world, hero, coach, solution)

    world.facts.update(
        hero=hero,
        peer=peer,
        coach=coach,
        cause_cfg=cause,
        item_cfg=item,
        solution=solution,
        retrieved=world.get("item").meters["retrieved"] >= THRESHOLD,
        explained=world.get("cause").meters["explained"] >= THRESHOLD,
        resolution=resolution_kind(solution.id),
        ghost_guess=hero.memes["ghost_guess"] >= THRESHOLD,
        conflict=hero.memes["conflict"] >= THRESHOLD,
        praised=hero.memes["praised"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    cause: str
    item: str
    solution: str
    hero_name: str
    hero_gender: str
    peer_name: str
    peer_gender: str
    coach_gender: str
    hero_trait: str
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
    "drain": [
        (
            "Why do bubbles come up from a pool drain?",
            "A pool filter moves water and air through the system, so small bubbles can rise from a drain. They can look strange, but they are usually just part of the pool equipment working.",
        )
    ],
    "bubbles": [
        (
            "What is a burst of bubbles?",
            "A burst of bubbles is a bunch of bubbles coming up all at once. In water, they can pop and shimmer very quickly.",
        )
    ],
    "reflection": [
        (
            "What is a reflection in water?",
            "A reflection is light bouncing so you see a shape or shadow in a new place. Wavy water can stretch and wiggle a reflection until it looks very different from the real thing.",
        )
    ],
    "echo": [
        (
            "What is an echo?",
            "An echo is a sound that bounces off walls and comes back to your ears. Big tiled rooms, like a pool, can make quiet sounds seem spooky and much bigger.",
        )
    ],
    "lifeguard": [
        (
            "What does a lifeguard do?",
            "A lifeguard watches the water to keep people safe. If something is too far away or looks risky, a lifeguard is the right grown-up to call.",
        )
    ],
    "pool_net": [
        (
            "What is a pool net for?",
            "A pool net is a long tool for reaching things in the water without leaning in too far. It helps grown-ups pick up toys and leaves safely.",
        )
    ],
    "goggles": [
        (
            "Why do swimmers use goggles?",
            "Goggles help swimmers see clearly underwater. Seeing clearly can turn a scary guess into the real answer.",
        )
    ],
    "ask_for_help": [
        (
            "Is asking for help brave?",
            "Yes. Asking for help is brave when something feels unsafe or confusing, because careful choices protect your body and help you solve the problem.",
        )
    ],
    "pool_safety": [
        (
            "Why should children not lean into the pool alone to reach far things?",
            "Pool edges are slippery, and deep water can be dangerous if you are not ready for it. It is safer to call a grown-up or use the right tool.",
        )
    ],
}


KNOWLEDGE_ORDER = [
    "drain",
    "bubbles",
    "reflection",
    "echo",
    "lifeguard",
    "pool_net",
    "goggles",
    "ask_for_help",
    "pool_safety",
]


CURATED = [
    StoryParams(
        cause="drain_bubbles",
        item="silver_ring",
        solution="buddy_goggles",
        hero_name="Mira",
        hero_gender="girl",
        peer_name="Finn",
        peer_gender="boy",
        coach_gender="woman",
        hero_trait="careful",
        seed=101,
    ),
    StoryParams(
        cause="flag_shadow",
        item="red_kickboard",
        solution="lifeguard_net",
        hero_name="Owen",
        hero_gender="boy",
        peer_name="Zoe",
        peer_gender="girl",
        coach_gender="man",
        hero_trait="steady",
        seed=102,
    ),
    StoryParams(
        cause="vent_echo",
        item="foam_ball",
        solution="buddy_goggles",
        hero_name="Lina",
        hero_gender="girl",
        peer_name="Max",
        peer_gender="boy",
        coach_gender="woman",
        hero_trait="quiet",
        seed=103,
    ),
    StoryParams(
        cause="vacuum_hose",
        item="red_kickboard",
        solution="lifeguard_net",
        hero_name="Theo",
        hero_gender="boy",
        peer_name="Ivy",
        peer_gender="girl",
        coach_gender="man",
        hero_trait="thoughtful",
        seed=104,
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cause = f["cause_cfg"]
    item = f["item_cfg"]
    solution = f["solution"]
    return [
        'Write a gentle ghost-story-style story for a 3-to-5-year-old set at a swimming pool that includes the words "praise" and "burst".',
        f"Tell a spooky-but-safe swimming pool story where {hero.id} wants praise for helping after class, sees {item.phrase}, and mistakes {cause.label} for a ghost before choosing a careful solution.",
        f"Write a story with inner monologue, conflict, and problem solving in which a child at a pool feels afraid of a haunted-looking corner and finally asks for help using {solution.label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    peer = f["peer"]
    coach = f["coach"]
    cause = f["cause_cfg"]
    item = f["item_cfg"]
    solution = f["solution"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} at the swimming pool, another child named {peer.id}, and Coach. {hero.id} wants to help after class and hopes for praise.",
        ),
        (
            f"Why did {hero.id} feel scared?",
            f"{hero.id} saw {cause.sign} near {item.phrase} and guessed it might be a ghost. The echoing pool and dim water made the harmless thing look much scarier than it really was.",
        ),
        (
            f"What was the conflict inside {hero.id}?",
            f"{hero.id} wanted the praise for helping, but also wanted to stay away from the spooky corner. {peer.id}'s teasing made that tug inside feel even stronger.",
        ),
        (
            f"How did {hero.id} solve the problem?",
            f"{hero.id} did not sneak into the water alone. Instead, {hero.pronoun()} {solution.action}, which let a grown-up reveal the truth safely.",
        ),
    ]
    if f["explained"]:
        qa.append(
            (
                "What was the 'ghost' really?",
                f"It was not a ghost at all: {cause.reveal} Once they looked carefully, the scary guess melted away.",
            )
        )
    if f["praised"]:
        qa.append(
            (
                f"Why did Coach praise {hero.id} at the end?",
                f'Coach praised {hero.id} for choosing the careful way instead of the risky way. The story shows that asking for help can be brave and smart at the same time.',
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["cause_cfg"].tags) | set(f["solution"].tags) | {"pool_safety"}
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
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
aligned(C, I) :- cause(C), item(I), cause_zone(C, Z), item_zone(I, Z).

sensible(S) :- solution(S), sense(S, N), sense_min(M), N >= M.

compatible(C, I, S) :-
    aligned(C, I),
    sensible(S),
    cause_mode(C, M),
    handles(S, M),
    item_kind(I, K),
    retrieves(S, K),
    cause_zone(C, Z),
    depth(Z, D),
    max_depth(S, MD),
    D <= MD.

resolution(C, I, S, paired) :- compatible(C, I, S), chosen_solution(S), S = buddy_goggles.
resolution(C, I, S, reached) :- compatible(C, I, S), chosen_solution(S), S = lifeguard_net.

valid(C, I, S) :- compatible(C, I, S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for zone, depth in DEPTH_ORDER.items():
        lines.append(asp.fact("depth", zone, depth))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_zone", cid, cause.zone))
        lines.append(asp.fact("cause_mode", cid, cause.mode))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_zone", iid, item.zone))
        lines.append(asp.fact("item_kind", iid, item.kind))
    for sid, solution in SOLUTIONS.items():
        lines.append(asp.fact("solution", sid))
        lines.append(asp.fact("sense", sid, solution.sense))
        lines.append(asp.fact("max_depth", sid, solution.max_depth))
        for mode in sorted(solution.modes):
            lines.append(asp.fact("handles", sid, mode))
        for kind in sorted(solution.retrieves):
            lines.append(asp.fact("retrieves", sid, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_resolution(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_solution", params.solution),
            asp.fact("query_cause", params.cause),
            asp.fact("query_item", params.item),
        ]
    )
    show = "#show resolution/4."
    model = asp.one_model(asp_program(extra, show))
    atoms = asp.atoms(model, "resolution")
    for cause, item, solution, kind in atoms:
        if cause == params.cause and item == params.item and solution == params.solution:
            return kind
    return "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a spooky swimming pool misunderstanding solved the careful way."
    )
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--peer-gender", choices=["girl", "boy"])
    ap.add_argument("--coach-gender", choices=["woman", "man"])
    ap.add_argument("--hero-name")
    ap.add_argument("--peer-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.item:
        cause = CAUSES[args.cause]
        item = ITEMS[args.item]
        if cause.zone != item.zone:
            raise StoryError(explain_combo_rejection(cause, item))
    if args.solution:
        solution = SOLUTIONS[args.solution]
        if solution.sense < SENSE_MIN:
            raise StoryError(explain_combo_rejection(CAUSES[args.cause] if args.cause else next(iter(CAUSES.values())), ITEMS[args.item] if args.item else next(iter(ITEMS.values())), solution))
    combos = [
        combo
        for combo in valid_combos()
        if (args.cause is None or combo[0] == args.cause)
        and (args.item is None or combo[1] == args.item)
        and (args.solution is None or combo[2] == args.solution)
    ]
    if not combos:
        if args.cause and args.item and args.solution:
            raise StoryError(explain_combo_rejection(CAUSES[args.cause], ITEMS[args.item], SOLUTIONS[args.solution]))
        raise StoryError("(No valid combination matches the given options.)")

    cause_id, item_id, solution_id = rng.choice(combos)
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    peer_gender = args.peer_gender or rng.choice(["girl", "boy"])
    coach_gender = args.coach_gender or rng.choice(["woman", "man"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    peer_name = args.peer_name or pick_name(rng, peer_gender, avoid=hero_name)
    hero_trait = rng.choice(TRAITS)
    return StoryParams(
        cause=cause_id,
        item=item_id,
        solution=solution_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        peer_name=peer_name,
        peer_gender=peer_gender,
        coach_gender=coach_gender,
        hero_trait=hero_trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.solution not in SOLUTIONS:
        raise StoryError(f"(Unknown solution: {params.solution})")
    cause = CAUSES[params.cause]
    item = ITEMS[params.item]
    solution = SOLUTIONS[params.solution]
    if not compatible(cause, item, solution):
        raise StoryError(explain_combo_rejection(cause, item, solution))
    world = tell(
        cause=cause,
        item=item,
        solution=solution,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        peer_name=params.peer_name,
        peer_gender=params.peer_gender,
        coach_gender=params.coach_gender,
        hero_trait=params.hero_trait,
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

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_sensible = {s.id for s in sensible_solutions()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible solutions match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible solutions: python={sorted(py_sensible)} clingo={sorted(asp_sens)}")

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if params.solution in {"buddy_goggles", "lifeguard_net"}:
            if asp_resolution(params) != resolution_kind(params.solution):
                bad += 1
    if bad == 0:
        print(f"OK: resolution model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} resolution results differ.")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(777))
        smoke_params.seed = 777
        sample = generate(smoke_params)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True)
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show resolution/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible solutions: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (cause, item, solution) combos:\n")
        for cause, item, solution in combos:
            print(f"  {cause:14} {item:12} {solution}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.cause} + {p.item} ({p.solution})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
