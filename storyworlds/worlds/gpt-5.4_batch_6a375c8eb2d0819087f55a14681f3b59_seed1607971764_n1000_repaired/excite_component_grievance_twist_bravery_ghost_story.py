#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py
==================================================================================

A standalone storyworld for a gentle ghost story with a brave child, a missing
component, and a final twist: the "haunting" is real, but the ghost is not mean.
It has a grievance because part of a treasured object is missing, so it cannot
finish one last familiar sound. A child chooses bravery, follows the clues, and
helps.

The domain is intentionally small and constraint-checked. A haunted object only
works with components that actually belong to it, and each setting only affords
certain haunted objects. The world state -- fear, courage, grievance, calm, and
the physical state of the keepsake -- drives the prose.

Run it
------
    python storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py
    python storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py --qa
    python storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py --trace
    python storyworlds/worlds/gpt-5.4/excite_component_grievance_twist_bravery_ghost_story.py --verify
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
BRAVE_MIN = 5


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Setting:
    id: str
    place: str
    opening: str
    shadows: str
    hiding_spot: str
    moonline: str
    affords: set[str] = field(default_factory=set)
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
class Keepsake:
    id: str
    label: str
    phrase: str
    owner_hint: str
    sound: str
    glow: str
    emotional_image: str
    fits: set[str] = field(default_factory=set)
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
class Component:
    id: str
    label: str
    phrase: str
    effect: str
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
class CourageAid:
    id: str
    label: str
    phrase: str
    gives: int
    action: str
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


def _r_missing_component(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    ghost = world.get("ghost")
    room = world.get("room")
    if keepsake.meters["complete"] >= THRESHOLD:
        return out
    sig = ("missing_component", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["grievance"] += 1
    room.meters["eerie"] += 1
    out.append("__uneasy__")
    return out


def _r_eerie_fear(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    child = world.get("child")
    if room.meters["eerie"] < THRESHOLD:
        return out
    sig = ("eerie_fear", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__fear__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes["courage"] < THRESHOLD or child.memes["care"] < THRESHOLD:
        return out
    sig = ("bravery", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery"] += 1
    out.append("__brave__")
    return out


def _r_repaired(world: World) -> list[str]:
    out: list[str] = []
    keepsake = world.get("keepsake")
    ghost = world.get("ghost")
    room = world.get("room")
    child = world.get("child")
    if keepsake.meters["complete"] < THRESHOLD:
        return out
    sig = ("repaired", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["grievance"] = 0.0
    ghost.memes["peace"] += 1
    room.meters["eerie"] = 0.0
    room.meters["calm"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    out.append("__peace__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="missing_component", tag="physical", apply=_r_missing_component),
    Rule(name="eerie_fear", tag="emotional", apply=_r_eerie_fear),
    Rule(name="bravery", tag="emotional", apply=_r_bravery),
    Rule(name="repaired", tag="physical", apply=_r_repaired),
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


def compatible(setting: Setting, keepsake: Keepsake, component: Component) -> bool:
    return keepsake.id in setting.affords and component.id in keepsake.fits


def brave_enough(aid: CourageAid, child_trait: str) -> bool:
    base = 3
    if child_trait in {"brave", "steady", "kind"}:
        base += 1
    return base + aid.gives >= BRAVE_MIN


def predict_success(setting: Setting, keepsake: Keepsake, component: Component,
                    aid: CourageAid, child_trait: str) -> dict:
    if not compatible(setting, keepsake, component):
        return {"compatible": False, "brave": False, "peace": False}
    brave = brave_enough(aid, child_trait)
    return {"compatible": True, "brave": brave, "peace": brave}


def introduce(world: World, child: Entity, grownup: Entity) -> None:
    world.say(
        f"One windy night, {child.id} and {child.pronoun('possessive')} "
        f"{grownup.label_word} were in {world.setting.place}. {world.setting.opening}"
    )
    world.say(world.setting.shadows)


def hear_haunting(world: World, child: Entity, keepsake: Keepsake) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"From {world.setting.hiding_spot} came a strange sound: {keepsake.sound}. "
        f"It was enough to excite {child.id}, but it also made "
        f"{child.pronoun('object')} hold still."
    )


def whisper_story(world: World, grownup: Entity, keepsake: Keepsake) -> None:
    world.say(
        f'"That sounds like {keepsake.phrase}," {grownup.label_word} whispered. '
        f'"It belonged to someone who loved it very much."'
    )


def haunt(world: World, ghost: Entity, keepsake: Keepsake) -> None:
    propagate(world, narrate=False)
    world.say(
        f"A pale figure drifted into the moonlight. It was no snarling monster, "
        f"only a small ghost with sad eyes. {keepsake.glow}"
    )
    world.say(
        f'"I do not want to scare anyone," the ghost said. "I only have a grievance. '
        f"My dear {keepsake.label} cannot sing the way it used to."
    )


def show_missing_piece(world: World, ghost: Entity, component: Component) -> None:
    world.say(
        f'The ghost lifted one misty hand and pointed toward an empty place. '
        f'"Its missing component is {component.phrase}," it sighed.'
    )


def choose_bravery(world: World, child: Entity, aid: CourageAid) -> None:
    child.memes["care"] += 1
    child.memes["courage"] += float(aid.gives)
    propagate(world, narrate=False)
    world.say(
        f"{child.id}'s knees trembled, but {child.pronoun()} took {aid.phrase} and "
        f"{aid.action}. That was {child.pronoun('possessive')} kind of bravery: "
        f"walking closer even while the room still felt strange."
    )


def retreat(world: World, child: Entity, grownup: Entity, aid: CourageAid) -> None:
    child.memes["courage"] += float(aid.gives)
    world.say(
        f"{child.id} tried to step forward with {aid.phrase}, but the shadows felt "
        f"too thick, and {child.pronoun()} hurried back to {child.pronoun('possessive')} "
        f"{grownup.label_word}."
    )
    world.say(
        f'Together they left a candle in the hall and promised to return in daylight. '
        f'Yet all night the soft sound kept drifting out, and the ghost still looked sad.'
    )


def search(world: World, child: Entity, component: Component, keepsake: Keepsake) -> None:
    world.say(
        f"Following the faint sound, {child.id} searched under old quilts and inside "
        f"a cracked box until {child.pronoun()} found {component.phrase} tucked beside "
        f"{keepsake.owner_hint}."
    )


def repair(world: World, child: Entity, keepsake_ent: Entity, component: Component,
           keepsake: Keepsake) -> None:
    keepsake_ent.meters["complete"] += 1
    keepsake_ent.attrs["component"] = component.id
    propagate(world, narrate=False)
    world.say(
        f"{child.id} set {component.phrase} into the waiting place. At once, "
        f"{component.effect}, and the {keepsake.label} gave its true sound."
    )


def twist_reveal(world: World, child: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"The twist was not that there had been no ghost at all. The twist was that "
        f"the ghost had only been lonely, guarding {keepsake.phrase} until someone "
        f"kind enough would listen."
    )
    world.say(
        f"The small ghost smiled, lighter than dust, and began to fade. "
        f'"Thank you for hearing my grievance," it whispered.'
    )


def ending(world: World, child: Entity, grownup: Entity, keepsake: Keepsake) -> None:
    world.say(
        f"When the last note faded, {world.setting.place} no longer felt cold and watchful. "
        f"{grownup.label_word.capitalize()} put an arm around {child.id}, and together they listened."
    )
    world.say(
        f"Now the room held only {keepsake.emotional_image}, and {child.id} felt "
        f"more quiet than scared. The brave part was not pretending the night was easy. "
        f"It was helping anyway."
    )
@dataclass
class StoryParams:
    setting: str
    keepsake: str
    component: str
    aid: str
    child_name: str
    child_type: str
    child_trait: str
    grownup_type: str
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
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky tale with strange sounds, shadows, and mystery. In gentle ghost stories, the scary feeling often hides a sad or lonely problem that can be understood."
        )
    ],
    "attic": [
        (
            "What is an attic?",
            "An attic is a room right under the roof of a house. People often keep old boxes and keepsakes there."
        )
    ],
    "music_box": [
        (
            "What does a music box do?",
            "A music box is a little box that plays a tune when its winding part works. If an important part is missing, it cannot play properly."
        )
    ],
    "train": [
        (
            "Why does a toy train need all its wheels?",
            "A toy train needs its wheels to roll smoothly. If one wheel is missing, it tips and cannot move the way it should."
        )
    ],
    "kite": [
        (
            "Why does a kite need a tail?",
            "A kite's tail helps keep it balanced. Without the tail, it can twist and wobble in the wind."
        )
    ],
    "light": [
        (
            "Why can a flashlight help when you feel scared in the dark?",
            "A flashlight lets you see what is really there. Seeing clearly can make a mysterious place feel less confusing and less frightening."
        )
    ],
    "component": [
        (
            "What is a component?",
            "A component is one part of a bigger thing. When an important component is missing, the whole thing may stop working."
        )
    ],
    "grievance": [
        (
            "What is a grievance?",
            "A grievance is a hurt feeling or complaint about something that is wrong. Someone with a grievance often wants the problem noticed and mended."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "attic", "music_box", "train", "kite", "light", "component", "grievance"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    keepsake = f["keepsake_cfg"]
    component = f["component_cfg"]
    aid = f["aid"]
    setting = f["setting"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old set in {setting.place} that includes the words "excite", "component", and "grievance".',
        f"Tell a spooky-but-kind story where {child.id} hears a strange sound, chooses bravery, and helps a ghost by finding the missing {component.label} for a {keepsake.label}.",
        f"Write a story with a twist: the ghost in {setting.place} is real, but its grievance is not anger. It only wants someone brave enough to repair {keepsake.phrase} with {aid.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    keepsake = f["keepsake_cfg"]
    component = f["component_cfg"]
    aid = f["aid"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {grownup.label_word}, and a lonely ghost in {world.setting.place}. The ghost was tied to a treasured {keepsake.label} that could not work properly."
        ),
        (
            f"What first happened in {world.setting.place}?",
            f"{child.id} heard {keepsake.sound} coming from {world.setting.hiding_spot}. The strange noise was spooky enough to excite {child.pronoun('object')} and frighten {child.pronoun('object')} at the same time."
        ),
        (
            "What was the ghost's grievance?",
            f"The ghost was sad because the {keepsake.label} was missing {component.phrase}. That missing component kept the keepsake from making its true sound, so the ghost could not rest."
        ),
    ]
    if outcome == "peace":
        qa.extend([
            (
                f"How did {child.id} show bravery?",
                f"{child.id} was scared, but still moved closer with {aid.phrase} and kept searching. That bravery mattered because it let {child.pronoun('object')} listen to the ghost instead of running away."
            ),
            (
                f"What was the twist at the end?",
                f"The twist was that the ghost really was there, but it was not mean at all. It only wanted help fixing the keepsake, and once {child.id} repaired it, the room became peaceful."
            ),
            (
                "How did the story end?",
                f"The missing part was returned, the {keepsake.label} made its proper sound, and the ghost faded away in peace. The ending image showed the room changed from eerie and watchful to quiet and calm."
            ),
        ])
    else:
        qa.extend([
            (
                f"Did {child.id} solve the ghost's problem that night?",
                f"No. {child.id} tried to be brave, but the shadows still felt too heavy, so the search stopped. Because the missing component was not returned, the ghost's grievance remained."
            ),
            (
                "How did the story end?",
                f"It ended with the haunting still lingering through the night. The family promised to come back later, but the room had not grown calm yet."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "component", "grievance"} | set(world.setting.tags) | set(f["keepsake_cfg"].tags) | set(f["aid"].tags)
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
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="attic",
        keepsake="music_box",
        component="key",
        aid="flashlight",
        child_name="Nora",
        child_type="girl",
        child_trait="brave",
        grownup_type="mother",
    ),
    StoryParams(
        setting="nursery",
        keepsake="kite",
        component="tail_ribbon",
        aid="song",
        child_name="Theo",
        child_type="boy",
        child_trait="kind",
        grownup_type="father",
    ),
    StoryParams(
        setting="hall",
        keepsake="toy_train",
        component="wheel",
        aid="hand_hold",
        child_name="Mina",
        child_type="girl",
        child_trait="timid",
        grownup_type="mother",
    ),
    StoryParams(
        setting="attic",
        keepsake="toy_train",
        component="wheel",
        aid="song",
        child_name="Finn",
        child_type="boy",
        child_trait="steady",
        grownup_type="father",
    ),
]


def explain_rejection(setting: Setting, keepsake: Keepsake, component: Component) -> str:
    if keepsake.id not in setting.affords:
        return (
            f"(No story: {setting.place} does not honestly fit a haunting centered on a {keepsake.label}. "
            f"Pick a keepsake that belongs in that place.)"
        )
    return (
        f"(No story: {component.phrase} does not belong to the {keepsake.label}. "
        f"The missing component must be a real part of the haunted keepsake.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.setting not in SETTINGS or params.keepsake not in KEEPSAKES or params.component not in COMPONENTS or params.aid not in AIDS:
        raise StoryError("(No story: unknown parameter value.)")
    if not compatible(SETTINGS[params.setting], KEEPSAKES[params.keepsake], COMPONENTS[params.component]):
        raise StoryError(explain_rejection(SETTINGS[params.setting], KEEPSAKES[params.keepsake], COMPONENTS[params.component]))
    return "peace" if brave_enough(AIDS[params.aid], params.child_trait) else "lingers"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, K, C) :- setting(S), keepsake(K), component(C), affords(S, K), fits(K, C).

% --- bravery / outcome -----------------------------------------------------
trait_bonus(1) :- chosen_trait(T), boosting_trait(T).
trait_bonus(0) :- chosen_trait(T), not boosting_trait(T).

courage_total(B + G) :- trait_bonus(B), chosen_aid(A), gives(A, G).
brave :- courage_total(V), brave_min(M), V >= M.

outcome(peace) :- brave.
outcome(lingers) :- not brave.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for kid in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, kid))
    for kid, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", kid))
        for cid in sorted(keepsake.fits):
            lines.append(asp.fact("fits", kid, cid))
    for cid in COMPONENTS:
        lines.append(asp.fact("component", cid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("gives", aid_id, aid.gives))
    lines.append(asp.fact("brave_min", BRAVE_MIN))
    for trait in ["brave", "steady", "kind"]:
        lines.append(asp.fact("boosting_trait", trait))
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
        asp.fact("chosen_trait", params.child_trait),
        asp.fact("chosen_aid", params.aid),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    rng = random.Random(17)
    parser = build_parser()
    for i in range(30):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(rng.randint(0, 10_000)))
        except StoryError:
            continue
        cases.append(params)
        if i > 12:
            break

    bad = 0
    for params in cases:
        py = outcome_of(params)
        asp = asp_outcome(params)
        if py != asp:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost story storyworld: a brave child, a missing component, and a lonely ghost's grievance."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--component", choices=COMPONENTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--child-trait", choices=TRAITS)
    ap.add_argument("--grownup-type", choices=PARENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (setting, keepsake, component) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.keepsake and args.component:
        setting = SETTINGS[args.setting]
        keepsake = KEEPSAKES[args.keepsake]
        component = COMPONENTS[args.component]
        if not compatible(setting, keepsake, component):
            raise StoryError(explain_rejection(setting, keepsake, component))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.component is None or combo[2] == args.component)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, keepsake_id, component_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    child_trait = args.child_trait or rng.choice(TRAITS)
    grownup_type = args.grownup_type or rng.choice(PARENTS)
    aid = args.aid or rng.choice(sorted(AIDS))
    return StoryParams(
        setting=setting_id,
        keepsake=keepsake_id,
        component=component_id,
        aid=aid,
        child_name=child_name,
        child_type=child_type,
        child_trait=child_trait,
        grownup_type=grownup_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(No story: unknown setting '{params.setting}'.)")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(No story: unknown keepsake '{params.keepsake}'.)")
    if params.component not in COMPONENTS:
        raise StoryError(f"(No story: unknown component '{params.component}'.)")
    if params.aid not in AIDS:
        raise StoryError(f"(No story: unknown aid '{params.aid}'.)")
    if params.child_type not in {"girl", "boy"}:
        raise StoryError("(No story: child_type must be 'girl' or 'boy'.)")
    if params.child_trait not in TRAITS:
        raise StoryError(f"(No story: unknown child trait '{params.child_trait}'.)")
    if params.grownup_type not in PARENTS:
        raise StoryError(f"(No story: unknown grownup type '{params.grownup_type}'.)")

    setting = SETTINGS[params.setting]
    keepsake = KEEPSAKES[params.keepsake]
    component = COMPONENTS[params.component]
    aid = AIDS[params.aid]

    if not compatible(setting, keepsake, component):
        raise StoryError(explain_rejection(setting, keepsake, component))

    world = tell(
        setting=setting,
        keepsake=keepsake,
        component=component,
        aid=aid,
        child_name=params.child_name,
        child_type=params.child_type,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, keepsake, component) combos:\n")
        for setting, keepsake, component in combos:
            print(f"  {setting:8} {keepsake:10} {component}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.keepsake} in {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(setting: Setting, keepsake: Keepsake, component: Component, aid: CourageAid,
         child_name: str = "Nora", child_type: str = "girl",
         child_trait: str = "brave", grownup_type: str = "mother") -> World:
    world = World(setting=setting)

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        role="child",
        traits=[child_trait],
        attrs={},
    ))
    grownup = world.add(Entity(
        id="Parent",
        kind="character",
        type=grownup_type,
        role="grownup",
        label="the parent",
        attrs={},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        role="ghost",
        label="the ghost",
        attrs={"wants": keepsake.id},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.place,
        attrs={},
    ))
    keepsake_ent = world.add(Entity(
        id="keepsake",
        kind="thing",
        type="keepsake",
        label=keepsake.label,
        attrs={"needs": component.id, "component": ""},
    ))
    clue = world.add(Entity(
        id="component",
        kind="thing",
        type="component",
        label=component.label,
        attrs={},
    ))

    child.memes["fear"] = 0.0
    child.memes["courage"] = 0.0
    child.memes["care"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["wonder"] = 0.0
    ghost.memes["grievance"] = 0.0
    ghost.memes["peace"] = 0.0
    room.meters["eerie"] = 0.0
    room.meters["calm"] = 0.0
    keepsake_ent.meters["complete"] = 0.0

    world.facts.update(
        setting=setting,
        keepsake_cfg=keepsake,
        component_cfg=component,
        aid=aid,
        child=child,
        grownup=grownup,
        ghost=ghost,
        keepsake=keepsake_ent,
        brave=False,
        success=False,
        outcome="sad",
    )

    introduce(world, child, grownup)
    hear_haunting(world, child, keepsake)
    whisper_story(world, grownup, keepsake)

    world.para()
    haunt(world, ghost, keepsake)
    show_missing_piece(world, ghost, component)

    world.para()
    choose_bravery(world, child, aid)
    brave = child.memes["courage"] + (1 if child_trait in {"brave", "steady", "kind"} else 0) >= BRAVE_MIN
    world.facts["brave"] = brave

    if brave:
        search(world, child, component, keepsake)
        repair(world, child, keepsake_ent, component, keepsake)
        world.para()
        twist_reveal(world, child, ghost, keepsake)
        ending(world, child, grownup, keepsake)
        outcome = "peace"
        success = True
    else:
        retreat(world, child, grownup, aid)
        outcome = "lingers"
        success = False

    world.facts.update(
        brave=brave,
        success=success,
        outcome=outcome,
        grievance_fixed=ghost.memes["grievance"] < THRESHOLD,
        eerie_gone=room.meters["eerie"] < THRESHOLD,
    )
    return world


SETTINGS = {
    "attic": Setting(
        id="attic",
        place="the attic",
        opening="Rain tapped the roof, and old trunks stood in rows like sleepy giants.",
        shadows="A thin strip of moonlight lay across the floorboards, and every nail seemed to know a secret.",
        hiding_spot="behind the tallest trunk",
        moonline="under the slanted roof",
        affords={"music_box", "toy_train"},
        tags={"attic", "night"},
    ),
    "nursery": Setting(
        id="nursery",
        place="the old nursery",
        opening="The curtains breathed in and out with the wind, and the wallpaper rabbits looked ready to hop away.",
        shadows="Moonbeams silvered the rocking chair and made the corners seem deeper than they were.",
        hiding_spot="near the little bed",
        moonline="by the rocking chair",
        affords={"music_box", "kite"},
        tags={"nursery", "night"},
    ),
    "hall": Setting(
        id="hall",
        place="the upstairs hall",
        opening="The grandfather clock had stopped long ago, yet the hallway still seemed to count each breath.",
        shadows="Portraits watched from the walls while the floor gave soft creaks under careful feet.",
        hiding_spot="beneath the small table by the stairs",
        moonline="beside the railing",
        affords={"toy_train", "kite"},
        tags={"hall", "night"},
    ),
}

KEEPSAKES = {
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a little music box painted with stars",
        owner_hint="an old velvet scarf",
        sound="a broken tinkle, then silence",
        glow="The ghost hovered beside a little music box painted with stars.",
        emotional_image="one clear tune drifting into the rafters",
        fits={"key"},
        tags={"music_box", "sound"},
    ),
    "toy_train": Keepsake(
        id="toy_train",
        label="toy train",
        phrase="a red toy train with brass trim",
        owner_hint="a faded conductor cap",
        sound="a tiny clack-clack and one lonely bell",
        glow="The ghost floated near a red toy train whose bell trembled all by itself.",
        emotional_image="a gentle bell and wheels clicking softly in a neat circle",
        fits={"wheel"},
        tags={"train", "sound"},
    ),
    "kite": Keepsake(
        id="kite",
        label="paper kite",
        phrase="a paper kite stitched with moons",
        owner_hint="a stack of old picture books",
        sound="a papery flutter, as if wings were trapped indoors",
        glow="The ghost leaned over a paper kite stitched with moons.",
        emotional_image="moon-bright paper rustling softly by the window",
        fits={"tail_ribbon"},
        tags={"kite", "wind"},
    ),
}

COMPONENTS = {
    "key": Component(
        id="key",
        label="key",
        phrase="the tiny silver key",
        effect="the spring caught and the little drum began to turn",
        tags={"key", "component"},
    ),
    "wheel": Component(
        id="wheel",
        label="wheel",
        phrase="the small black wheel",
        effect="the axle straightened and the train settled on all four wheels",
        tags={"wheel", "component"},
    ),
    "tail_ribbon": Component(
        id="tail_ribbon",
        label="tail ribbon",
        phrase="the long blue tail ribbon",
        effect="the kite steadied, no longer twisting in the draft",
        tags={"ribbon", "component"},
    ),
}

AIDS = {
    "flashlight": CourageAid(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        gives=2,
        action="clicked it on and took one slow step after another",
        tags={"flashlight", "light"},
    ),
    "hand_hold": CourageAid(
        id="hand_hold",
        label="grown-up hand",
        phrase="her grown-up's hand" if False else "a grown-up's hand",
        gives=1,
        action="held on tight and listened before moving",
        tags={"comfort", "grownup"},
    ),
    "song": CourageAid(
        id="song",
        label="humming song",
        phrase="a tiny humming song",
        gives=2,
        action="hummed under the breath to keep the heart steady",
        tags={"song", "comfort"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ella", "Rose", "June"]
BOY_NAMES = ["Theo", "Max", "Eli", "Finn", "Noah", "Ben"]
TRAITS = ["brave", "steady", "kind", "curious", "timid"]
PARENTS = ["mother", "father"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for kid, keepsake in KEEPSAKES.items():
            for cid, component in COMPONENTS.items():
                if compatible(setting, keepsake, component):
                    combos.append((sid, kid, cid))
    return combos

if __name__ == "__main__":
    main()
