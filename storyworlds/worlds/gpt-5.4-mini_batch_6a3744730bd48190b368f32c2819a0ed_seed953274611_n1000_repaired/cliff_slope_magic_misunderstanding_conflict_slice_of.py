#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/cliff_slope_magic_misunderstanding_conflict_slice_of.py
=======================================================================================

A standalone storyworld for a small slice-of-life scene about a child, a little
bit of magic, a misunderstanding, and a soft conflict by a cliff-side slope.

Premise
-------
A child brings a small charm to a neighborhood walk near a cliff and a grassy
slope. The charm seems to move things in a surprising way, another child thinks
it is being used for something sneaky, and a grown-up helps them sort out what
really happened. The story ends with the children sharing a safer use for the
magic and the scene settling back into ordinary calm.

This script follows the Storyweavers contract:
- self-contained stdlib script
- uses typed entities with meters and memes
- state-driven story generation
- Python reasonableness gate and inline ASP twin
- prompts, story QA, and world-knowledge QA grounded in world state
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
class Place:
    id: str
    label: str
    near_cliff: bool = False
    has_slope: bool = False
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
class Charm:
    id: str
    label: str
    phrase: str
    magic_kind: str
    effect: str
    safe_use: str
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
class Misunderstanding:
    id: str
    label: str
    belief: str
    correction: str
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
class Response:
    id: str
    sense: int
    text: str
    repair: str
    qa_text: str
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
class StoryParams:
    place: str
    charm: str
    misunderstanding: str
    response: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    parent: str
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


def _r_balance(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["tilt"] < THRESHOLD:
            continue
        sig = ("balance", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("cliff").meters["worry"] += 1
        out.append("__worry__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.get("friend").memes["fear"] >= THRESHOLD:
        sig = ("fear", "friend")
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("child").memes["hurt"] += 1
            out.append("__hurt__")
    return out


CAUSAL_RULES = [
    Rule("balance", "physical", _r_balance),
    Rule("fear", "social", _r_fear),
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
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def safe_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(place: Place, charm: Charm, misunderstanding: Misunderstanding) -> bool:
    return place.near_cliff and place.has_slope and "magic" in charm.tags and "conflict" in misunderstanding.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for cid, charm in CHARMS.items():
            for mid, mis in MISUNDERSTANDINGS.items():
                if valid_combo(place, charm, mis):
                    combos.append((pid, cid, mid))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_chase(world: World, charm: Charm) -> dict:
    sim = world.copy()
    sim.get("child").meters["tilt"] += 1
    sim.get("friend").memes["fear"] += 1
    propagate(sim, narrate=False)
    return {"worry": sim.get("cliff").meters["worry"], "hurt": sim.get("child").memes["hurt"]}


def story_setup(world: World, child: Entity, friend: Entity, place: Place, charm: Charm) -> None:
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"After breakfast, {child.id} and {friend.id} walked along {place.label}. "
        f"The path curved beside a cliff, and a gentle slope of grass led down to a patch of wildflowers."
    )
    world.say(
        f"{child.id} carried {charm.phrase}, a little bit of magic that could nudge a pebble or make a leaf spin."
    )


def misunderstanding_scene(world: World, child: Entity, friend: Entity, charm: Charm, mis: Misunderstanding) -> None:
    child.meters["tilt"] += 1
    friend.memes["fear"] += 1
    world.say(
        f"{friend.id} saw the charm move a pebble on the slope and frowned. "
        f'"{child.id}, don\'t shove anything toward the cliff," {friend.id} said. '
        f'"{I saw {mis.belief}."'
    )
    world.say(
        f"{child.id} blinked. {charm.safe_use.capitalize()}, not anything dangerous, was all the charm had done."
    )


def explain(world: World, parent: Entity, child: Entity, friend: Entity, charm: Charm, mis: Misunderstanding) -> None:
    child.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.say(
        f"{parent.label_word.capitalize()} knelt beside them and listened. "
        f'"{mis.correction}," {parent.pronoun()} said gently. '
        f'"{That charm is for small, careful tricks, not for making trouble near a cliff."'
    )
    world.say(
        f"{friend.id}'s shoulders dropped. {child.id} showed {friend.pronoun('object')} how the charm could spin a dandelion seed instead."
    )


def repair(world: World, parent: Entity, child: Entity, friend: Entity, response: Response, place: Place) -> None:
    child.memes["peace"] += 1
    friend.memes["peace"] += 1
    world.say(
        f"{parent.label_word.capitalize()} {response.text}."
    )
    world.say(
        f"The little worry settled down at once, and the two children moved a few steps away from the cliff edge to sit on the slope together."
    )
    world.say(
        f"There, {child.id} used the charm to make a soft ring of light drift over the wildflowers, and {friend.id} laughed at how pretty it looked."
    )


def close(world: World, child: Entity, friend: Entity, place: Place, charm: Charm) -> None:
    world.say(
        f"By the time they headed home, the cliff was only part of the view again. "
        f"{child.id} tucked {charm.phrase} into a pocket, and {friend.id} walked beside {child.id} without any more worries."
    )
    world.say(
        f"The slope stayed green, the flowers stayed still, and the ordinary afternoon felt warm and calm."
    )


def tell(place: Place, charm: Charm, mis: Misunderstanding, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         friend_name: str = "Owen", friend_gender: str = "boy",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child", traits=["careful"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["watchful"]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))

    story_setup(world, child, friend, place, charm)
    world.para()
    misunderstanding_scene(world, child, friend, charm, mis)
    world.para()
    explain(world, parent, child, friend, charm, mis)
    world.para()
    repair(world, parent, child, friend, response, place)
    world.para()
    close(world, child, friend, place, charm)

    world.facts.update(
        child=child,
        friend=friend,
        parent=parent,
        place=place,
        charm=charm,
        misunderstanding=mis,
        response=response,
        outcome="repaired",
    )
    return world


PLACES = {
    "harbor_path": Place(id="harbor_path", label="the harbor path", near_cliff=True, has_slope=True, tags={"cliff", "slope"}),
    "headland_walk": Place(id="headland_walk", label="the headland walk", near_cliff=True, has_slope=True, tags={"cliff", "slope"}),
    "garden_hill": Place(id="garden_hill", label="the garden hill", near_cliff=False, has_slope=True, tags={"slope"}),
}

CHARMS = {
    "pebble_song": Charm(
        id="pebble_song",
        label="pebble-song charm",
        phrase="a pebble-song charm",
        magic_kind="magic",
        effect="tapped pebbles into a tiny song",
        safe_use="it made a tiny tune for nearby stones",
        tags={"magic"},
    ),
    "leaf_glow": Charm(
        id="leaf_glow",
        label="leaf-glow charm",
        phrase="a leaf-glow charm",
        magic_kind="magic",
        effect="lit leaves with a soft shimmer",
        safe_use="it only gave leaves a friendly glow",
        tags={"magic"},
    ),
}

MISUNDERSTANDINGS = {
    "thought_push": Misunderstanding(
        id="thought_push",
        label="a misunderstanding",
        belief="you were trying to push things downhill",
        correction="The charm only nudges little things, and only when someone is careful",
        tags={"misunderstanding", "conflict"},
    ),
    "thought_trick": Misunderstanding(
        id="thought_trick",
        label="a misunderstanding",
        belief="you were playing a trick near the edge",
        correction="The charm is for calm, playful magic, not tricks that scare people",
        tags={"misunderstanding", "conflict"},
    ),
}

RESPONSES = {
    "show_pocket": Response(
        id="show_pocket",
        sense=3,
        text="showed how the charm could make a seed spin in the palm of a hand instead of near the edge",
        repair="showed a safer use for the charm",
        qa_text="showed how the charm could make a seed spin in a palm instead of near the edge",
        tags={"magic"},
    ),
    "step_back": Response(
        id="step_back",
        sense=3,
        text="asked them to step back from the cliff and sit where the grass was wider",
        repair="moved them to a safer spot",
        qa_text="asked them to step back from the cliff and sit where the grass was wider",
        tags={"safety"},
    ),
}

GIRL_NAMES = ["Mina", "Sara", "Leah", "Ruby", "Nina", "Tessa"]
BOY_NAMES = ["Owen", "Caleb", "Theo", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "curious", "gentle", "watchful", "thoughtful"]


@dataclass
class StoryRule:
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.near_cliff:
            lines.append(asp.fact("near_cliff", pid))
        if place.has_slope:
            lines.append(asp.fact("has_slope", pid))
    for cid, charm in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("magic_kind", cid, charm.magic_kind))
    for mid, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("conflict", mid))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,C,M) :- place(P), charm(C), misunderstanding(M), near_cliff(P), has_slope(P), magic_kind(C, magic), conflict(M).
safe(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_safe_responses() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show safe/1."))
    return sorted(r for (r,) in asp.atoms(model, "safe"))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story that includes the words "cliff" and "slope" and a small bit of magic.',
        f"Tell a gentle story where {f['child'].id} and {f['friend'].id} misunderstand one another near a cliff and then clear it up.",
        f'Write a child-friendly story about calm magic, a misunderstanding, and a quiet conflict that ends safely on a slope.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    parent = f["parent"]
    place = f["place"]
    charm = f["charm"]
    mis = f["misunderstanding"]
    resp = f["response"]
    return [
        QAItem(
            question="Where did the children go?",
            answer=f"They walked along {place.label}, where a cliff stood beside a grassy slope. It was an ordinary walk, just with a view that made everyone a little careful.",
        ),
        QAItem(
            question=f"What did {child.id} bring?",
            answer=f"{child.id} brought {charm.phrase}, a little bit of magic. It was meant for small, safe tricks, not for anything dangerous.",
        ),
        QAItem(
            question=f"Why did {friend.id} get upset?",
            answer=f"{friend.id} thought {mis.belief}. That made the moment tense, because the wrong idea can sound scary when people are standing near a cliff.",
        ),
        QAItem(
            question="How did the grown-up help?",
            answer=f"{parent.label_word.capitalize()} listened, explained the misunderstanding, and {resp.qa_text}. That turned the worry into a safer idea and helped everyone relax.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the children sitting safely on the slope, sharing a gentle magic trick and feeling calm again. The cliff stayed in the background, but the conflict was gone.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["charm"].tags) | set(world.facts["misunderstanding"].tags) | {"cliff", "slope"}
    out: list[QAItem] = []
    if "magic" in tags:
        out.append(QAItem("What is a charm?", "A charm is a small object people may treat as lucky or magical. In stories, it can do tiny special things."))

    if "conflict" in tags:
        out.append(QAItem("What is a conflict?", "A conflict is when characters want different things or think differently. In a gentle story, they can talk it through and feel better."))

    if "misunderstanding" in tags:
        out.append(QAItem("What is a misunderstanding?", "A misunderstanding happens when someone gets the wrong idea. Once people explain themselves, the confusion can go away."))

    out.append(QAItem("What is a cliff?", "A cliff is a very steep edge of rock or land. People stay careful near one because the ground drops quickly."))

    out.append(QAItem("What is a slope?", "A slope is ground that rises or falls gradually. It is not as steep as a cliff, so it is easier to walk on."))

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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor_path", charm="pebble_song", misunderstanding="thought_push", response="show_pocket", child="Mina", child_gender="girl", friend="Owen", friend_gender="boy", parent="mother"),
    StoryParams(place="headland_walk", charm="leaf_glow", misunderstanding="thought_trick", response="step_back", child="Theo", child_gender="boy", friend="Leah", friend_gender="girl", parent="father"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    if args.misunderstanding and args.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError("Unknown misunderstanding.")
    if args.response and args.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("Response is too weak for this storyworld.")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.charm is None or c[1] == args.charm)
              and (args.misunderstanding is None or c[2] == args.misunderstanding)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, charm, mis = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    friend_gender = "boy" if child_gender == "girl" else "girl"
    friend_pool = BOY_NAMES if friend_gender == "boy" else GIRL_NAMES
    friend = args.friend or rng.choice([n for n in friend_pool if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, charm=charm, misunderstanding=mis, response=response,
                       child=child, child_gender=child_gender, friend=friend, friend_gender=friend_gender,
                       parent=parent)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.charm not in CHARMS or params.misunderstanding not in MISUNDERSTANDINGS or params.response not in RESPONSES:
        raise StoryError("Invalid story parameters.")
    world = tell(PLACES[params.place], CHARMS[params.charm], MISUNDERSTANDINGS[params.misunderstanding], RESPONSES[params.response], params.child, params.child_gender, params.friend, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life storyworld with a cliff, a slope, magic, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def asp_verify() -> int:
    import storyworlds.asp as asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo sets.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
    # smoke test ordinary generation
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1 if rc == 0 else rc
    print("OK: generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show safe/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"safe responses: {', '.join(asp_safe_responses())}")
        print()
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.child} and {p.friend} near the cliff ({p.place}, {p.charm}, {p.misunderstanding})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
