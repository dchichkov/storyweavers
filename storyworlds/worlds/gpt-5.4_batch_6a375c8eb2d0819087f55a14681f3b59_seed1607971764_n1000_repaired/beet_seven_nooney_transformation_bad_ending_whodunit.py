#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py
==================================================================================

A standalone story world for a tiny child-facing whodunit with a magical
transformation and a bad ending.

Premise
-------
On the night of a small clubhouse supper, a child detective discovers that the
cook has vanished just before serving seven dumplings. In the kitchen sits a
large beet where the cook should be. The detective must work out who used a
forbidden bottle of "nooney tonic" -- a silly-sounding transformation syrup kept
on the top shelf. Each suspect leaves a clue tied to a motive and a method.
The world always tells a complete mystery: setup, clues, reveal, and an ending
image that proves what changed. Because this world is explicitly "bad ending",
the cook is not restored that night.

Run it
------
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py --culprit janitor
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py --victim baker
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/beet_seven_nooney_transformation_bad_ending_whodunit.py --verify

Design notes
------------
- Typed entities carry physical meters and emotional memes.
- The detective does not parse English to solve the case; the simulated world
  stores clue and culprit facts directly.
- The reasonableness gate only allows culprit/victim/tool combinations where the
  suspect had a motive, access, and a clue-producing method.
- The ASP twin checks the same gate and outcome logic.
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id.lower()
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
class Victim:
    id: str
    label: str
    room: str
    dish: str
    count: int
    kind: str
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
class Suspect:
    id: str
    label: str
    type: str
    motive_text: str
    wanted: str
    access_rooms: set[str]
    clue_kind: str
    clue_text: str
    method_text: str
    reveal_text: str
    confession_text: str
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
    transform_into: str
    clue_kind: str
    sense: int
    shelf: str
    warning: str
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
class Scene:
    id: str
    place: str
    opening: str
    closing: str
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


def _r_alarm(world: World) -> list[str]:
    victim = world.get("victim")
    culprit = world.get("culprit")
    if victim.meters["transformed"] < THRESHOLD:
        return []
    sig = ("alarm", victim.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room = world.get("room")
    room.meters["mystery"] += 1
    room.meters["danger"] += 1
    detective = world.get("detective")
    detective.memes["worry"] += 1
    detective.memes["curiosity"] += 1
    culprit.memes["guilt"] += 1
    return ["__alarm__"]


def _r_bad_ending(world: World) -> list[str]:
    victim = world.get("victim")
    if victim.meters["transformed"] < THRESHOLD or victim.meters["restored"] >= THRESHOLD:
        return []
    sig = ("bad_end", victim.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    victim.memes["helpless"] += 1
    detective = world.get("detective")
    detective.memes["sadness"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="alarm", tag="social", apply=_r_alarm),
    Rule(name="bad_end", tag="social", apply=_r_bad_ending),
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
        for line in produced:
            world.say(line)
    return produced


SCENES = {
    "clubhouse": Scene(
        id="clubhouse",
        place="the little clubhouse kitchen",
        opening="Rain tapped the windowpanes of the little clubhouse.",
        closing="The lamp in the clubhouse window burned low over the quiet table.",
        tags={"kitchen", "mystery"},
    ),
    "manor": Scene(
        id="manor",
        place="the old manor kitchen",
        opening="The old manor groaned softly in the evening wind.",
        closing="The manor hall felt too large and too still after supper was lost.",
        tags={"kitchen", "mystery"},
    ),
    "garden_hall": Scene(
        id="garden_hall",
        place="the garden hall pantry",
        opening="Night settled over the garden hall and the herbs by the door smelled wet and green.",
        closing="Outside, the garden leaves shivered while the pantry stayed sadly quiet.",
        tags={"pantry", "mystery"},
    ),
}

VICTIMS = {
    "cook": Victim(
        id="cook",
        label="Cook Nella",
        room="kitchen",
        dish="dumplings",
        count=7,
        kind="cook",
        tags={"food", "supper"},
    ),
    "baker": Victim(
        id="baker",
        label="Baker Moss",
        room="pantry",
        dish="buns",
        count=7,
        kind="baker",
        tags={"food", "supper"},
    ),
    "gardener": Victim(
        id="gardener",
        label="Gardener Pru",
        room="shed",
        dish="turnovers",
        count=7,
        kind="gardener",
        tags={"garden", "supper"},
    ),
}

SUSPECTS = {
    "janitor": Suspect(
        id="janitor",
        label="Old Bram the janitor",
        type="man",
        motive_text="was cross because the victim had complained about muddy boot prints on the clean floor",
        wanted="to spoil the supper rush and get the victim out of the way for a while",
        access_rooms={"kitchen", "pantry", "shed"},
        clue_kind="mud",
        clue_text="a half-moon of muddy boot print under the flour shelf",
        method_text="carried the bottle in a mop bucket so no one would notice it",
        reveal_text="The muddy print matched the thick tread on Bram's boots.",
        confession_text="I only meant to stop the scolding for one evening, but I tipped in too much nooney tonic.",
        tags={"mud", "boots"},
    ),
    "cousin": Suspect(
        id="cousin",
        label="Tansy the cousin",
        type="girl",
        motive_text="wanted the first sweet from the tray and hated being told to wait",
        wanted="to steal a quiet moment alone with the supper table",
        access_rooms={"kitchen", "pantry"},
        clue_kind="sugar",
        clue_text="a scatter of pink sugar stars by the spoon jar",
        method_text="hid the bottle in a cake box tied with blue string",
        reveal_text="The sugar stars were the same ones Tansy always tucked onto her cuffs.",
        confession_text="I thought the nooney tonic would only make a silly red nose, not a whole beet.",
        tags={"sugar", "cake"},
    ),
    "messenger": Suspect(
        id="messenger",
        label="Pip the messenger",
        type="boy",
        motive_text="was jealous because the victim had promised the seventh serving to someone else",
        wanted="to snatch that last special portion",
        access_rooms={"kitchen", "shed"},
        clue_kind="twine",
        clue_text="a frayed bit of parcel twine beside the empty stool",
        method_text="slipped the bottle out of a satchel between deliveries",
        reveal_text="Only Pip used red parcel twine like that on his message bundles.",
        confession_text="I only wanted the last helping. I never thought the tonic would change anyone for real.",
        tags={"twine", "satchel"},
    ),
    "aunt": Suspect(
        id="aunt",
        label="Aunt Sable",
        type="aunt",
        motive_text="was tired of hearing everyone laugh at her old joke cupboard",
        wanted="to prove the cupboard held real wonders after all",
        access_rooms={"pantry", "shed"},
        clue_kind="lavender",
        clue_text="a soft lavender smell hanging over the shelf",
        method_text="uncorked the bottle with her silver thimble and left in a hurry",
        reveal_text="The lavender smell came from the sachets Aunt Sable kept in every pocket.",
        confession_text="I wanted one grand surprise, and instead I ruined the whole night.",
        tags={"lavender", "cupboard"},
    ),
}

TOOLS = {
    "nooney_tonic": Tool(
        id="nooney_tonic",
        label="nooney tonic",
        transform_into="beet",
        clue_kind="magic",
        sense=2,
        shelf="the top joke shelf",
        warning="Never sip it, never stir it, and never pour it into real food.",
        tags={"magic", "tonic", "beet"},
    ),
    "nooney_drops": Tool(
        id="nooney_drops",
        label="nooney drops",
        transform_into="beet",
        clue_kind="magic",
        sense=2,
        shelf="the locked blue cupboard",
        warning="Only for paper tricks and toy shows, never for people.",
        tags={"magic", "drops", "beet"},
    ),
}

DETECTIVE_NAMES = ["Mira", "Nell", "Rafi", "Toby", "June", "Iris", "Pia", "Otis"]
TRAITS = ["careful", "sharp-eyed", "patient", "quiet", "curious", "steady"]


def hazard_possible(suspect: Suspect, victim: Victim, tool: Tool) -> bool:
    return victim.room in suspect.access_rooms and tool.sense >= SENSE_MIN


def sensible_tools() -> list[Tool]:
    return [tool for tool in TOOLS.values() if tool.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id in SCENES:
        for suspect_id, suspect in SUSPECTS.items():
            for victim_id, victim in VICTIMS.items():
                for tool_id, tool in TOOLS.items():
                    if hazard_possible(suspect, victim, tool):
                        combos.append((scene_id, suspect_id, victim_id, tool_id))
    return combos


@dataclass
class StoryParams:
    scene: str
    culprit: str
    victim: str
    tool: str
    detective_name: str
    detective_gender: str
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


def introduce(world: World, scene: Scene, detective: Entity, victim_cfg: Victim) -> None:
    world.say(scene.opening)
    world.say(
        f"{detective.id} was a {detective.type} with a {world.facts['trait']} way of looking at small things."
    )
    world.say(
        f"Inside {scene.place}, {victim_cfg.label} was meant to carry out {victim_cfg.count} hot {victim_cfg.dish} for supper."
    )


def countdown(world: World, victim_cfg: Victim) -> None:
    world.say(
        f"Everyone kept saying the number out loud -- seven plates, seven spoons, seven hungry children waiting at the table."
    )
    world.say(
        f"But when the lid was lifted, the {victim_cfg.dish} were there and {victim_cfg.label} was not."
    )


def transformation(world: World, tool: Tool) -> None:
    victim = world.get("victim")
    victim.meters["transformed"] += 1
    victim.meters["missing"] += 1
    victim.attrs["form"] = tool.transform_into
    propagate(world, narrate=False)
    world.say(
        f"On the floury tiles sat a plump red {tool.transform_into}, still wearing the victim's little apron string."
    )
    world.say(
        f"Beside it lay an uncorked bottle labeled '{tool.label}'. The tiny writing underneath said, '{tool.warning}'"
    )


def gather_clues(world: World, suspect: Suspect, victim_cfg: Victim, tool: Tool) -> None:
    detective = world.get("detective")
    detective.memes["focus"] += 1
    world.say(
        f'"This is a real whodunit," {detective.id} whispered. "{victim_cfg.label} did not simply walk away."'
    )
    world.say(
        f"{detective.id} looked once at the bottle, once at the floor, and then spotted {suspect.clue_text}."
    )
    world.say(
        f"There was also a red drip on the ladle, showing that someone had used {tool.label} near the supper pot."
    )


def list_suspects(world: World, suspects_here: list[Suspect]) -> None:
    labels = ", ".join(s.label for s in suspects_here[:-1]) + f", and {suspects_here[-1].label}"
    world.say(
        f"Only {labels} had been near the room that evening, so the circle of suspects stayed small."
    )


def explain_motives(world: World, culprit: Suspect, victim_cfg: Victim) -> None:
    world.say(
        f"Each suspect had a reason to fuss with {victim_cfg.label}, but one reason pulled hardest: {culprit.label} {culprit.motive_text}."
    )


def reveal(world: World, culprit: Suspect, tool: Tool) -> None:
    culprit_ent = world.get("culprit")
    culprit_ent.meters["caught"] += 1
    culprit_ent.memes["guilt"] += 1
    detective = world.get("detective")
    detective.memes["certainty"] += 1
    world.say(
        f"At last {detective.id} pointed to {culprit.label}. \"It was you,\" {detective.pronoun()} said."
    )
    world.say(
        f"{culprit.reveal_text} And the bottle had been moved exactly the way someone would move it if they {culprit.method_text}."
    )
    world.say(
        f"{culprit.label} went pale and admitted it. \"{culprit.confession_text}\""
    )


def bad_ending(world: World, scene: Scene, victim_cfg: Victim, tool: Tool) -> None:
    victim = world.get("victim")
    victim.meters["restored"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"But a confession did not undo the magic. The nooney spell had sunk too deep, and no one in {scene.place} knew how to turn the {tool.transform_into} back before midnight."
    )
    world.say(
        f"The supper table stayed set for seven, yet one chair remained empty while the little red {tool.transform_into} rested on a folded towel by the stove."
    )
    world.say(scene.closing)


def tell(
    scene: Scene,
    culprit_cfg: Suspect,
    victim_cfg: Victim,
    tool: Tool,
    detective_name: str = "Mira",
    detective_gender: str = "girl",
    trait: str = "careful",
) -> World:
    world = World()
    detective = world.add(
        Entity(
            id=detective_name,
            kind="character",
            type=detective_gender,
            role="detective",
            label=detective_name,
            traits=[trait],
            attrs={},
        )
    )
    victim = world.add(
        Entity(
            id="victim",
            kind="character",
            type="woman" if victim_cfg.kind in {"cook", "gardener"} else "man",
            role="victim",
            label=victim_cfg.label,
            traits=["busy"],
            attrs={"form": "person"},
        )
    )
    culprit = world.add(
        Entity(
            id="culprit",
            kind="character",
            type=culprit_cfg.type,
            role="culprit",
            label=culprit_cfg.label,
            traits=["nervous"],
            attrs={},
        )
    )
    world.add(
        Entity(
            id="room",
            kind="thing",
            type="room",
            role="room",
            label=scene.place,
            attrs={},
        )
    )

    detective.memes["curiosity"] = 1.0
    detective.memes["worry"] = 0.0
    detective.memes["certainty"] = 0.0
    detective.memes["sadness"] = 0.0
    culprit.memes["guilt"] = 0.0
    victim.meters["transformed"] = 0.0
    victim.meters["restored"] = 0.0
    victim.meters["missing"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    world.get("room").meters["danger"] = 0.0

    world.facts.update(
        scene=scene,
        culprit_cfg=culprit_cfg,
        victim_cfg=victim_cfg,
        tool=tool,
        detective=detective,
        culprit=culprit,
        victim=victim,
        trait=trait,
        suspects_here=[s for s in SUSPECTS.values() if victim_cfg.room in s.access_rooms],
        transformed_into=tool.transform_into,
        outcome="bad_ending",
    )

    introduce(world, scene, detective, victim_cfg)
    countdown(world, victim_cfg)

    world.para()
    transformation(world, tool)
    gather_clues(world, culprit_cfg, victim_cfg, tool)
    list_suspects(world, world.facts["suspects_here"])
    explain_motives(world, culprit_cfg, victim_cfg)

    world.para()
    reveal(world, culprit_cfg, tool)
    bad_ending(world, scene, victim_cfg, tool)
    return world


def generation_prompts(world: World) -> list[str]:
    scene = world.facts["scene"]
    victim_cfg = world.facts["victim_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    tool = world.facts["tool"]
    detective = world.facts["detective"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old that includes the words "beet", "seven", and "nooney". Set it in {scene.place}.',
        f"Tell a gentle mystery where {detective.id} must figure out who used {tool.label} on {victim_cfg.label} before supper.",
        f"Write a transformation mystery with a bad ending where {culprit_cfg.label} is revealed, but the victim is still a beet by the last page.",
    ]


KNOWLEDGE = {
    "mystery": [
        (
            "What is a whodunit?",
            "A whodunit is a mystery story where someone asks who caused the trouble. The clues help the reader and the detective find the answer.",
        )
    ],
    "beet": [
        (
            "What is a beet?",
            "A beet is a round root vegetable that grows in the ground. It is often dark red and can stain things with its color.",
        )
    ],
    "magic": [
        (
            "Why can a magic bottle be dangerous?",
            "A magic bottle can be dangerous because you may not know what it will do before it is opened or poured. Strange changes can happen very fast.",
        )
    ],
    "kitchen": [
        (
            "Why do cooks count plates and spoons before supper?",
            "They count them to make sure everyone has what they need. Counting helps people notice quickly when something is missing.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand what happened. A footprint, smell, or dropped string can all be clues.",
        )
    ],
    "bad": [
        (
            "What makes an ending a bad ending?",
            "A bad ending means the trouble is not fully fixed by the end. Someone may learn the truth, but the harm still stays.",
        )
    ],
}
KNOWLEDGE_ORDER = ["mystery", "beet", "magic", "kitchen", "clue", "bad"]


def story_qa(world: World) -> list[tuple[str, str]]:
    scene = world.facts["scene"]
    victim_cfg = world.facts["victim_cfg"]
    culprit_cfg = world.facts["culprit_cfg"]
    tool = world.facts["tool"]
    detective = world.facts["detective"]
    suspects_here: list[Suspect] = world.facts["suspects_here"]
    suspect_names = ", ".join(s.label for s in suspects_here)
    return [
        (
            "What mystery did the detective have to solve?",
            f"{detective.id} had to find out who used {tool.label} on {victim_cfg.label}. The mystery began when supper for seven was ready but the cook was gone and a beet was left behind.",
        ),
        (
            f"What clue helped {detective.id} solve the case?",
            f"The strongest clue was {culprit_cfg.clue_text}. It matched {culprit_cfg.label} and showed that this suspect had really been at the scene.",
        ),
        (
            "Who were the suspects?",
            f"The suspects were {suspect_names}. They were the ones who had been near the room where the victim disappeared.",
        ),
        (
            f"Why did {culprit_cfg.label} do it?",
            f"{culprit_cfg.label} did it because {culprit_cfg.motive_text}. That motive gave {culprit_cfg.pronoun('object') if isinstance(culprit_cfg, Entity) else 'them'} a reason to use the bottle and spoil the meal.",
        ),
        (
            "How did the story end?",
            f"The detective solved the whodunit, but the ending was still sad. {victim_cfg.label} stayed a beet, so the table for seven had an empty chair at supper time.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"mystery", "beet", "magic", "kitchen", "clue", "bad"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:9} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        scene="clubhouse",
        culprit="janitor",
        victim="cook",
        tool="nooney_tonic",
        detective_name="Mira",
        detective_gender="girl",
        trait="careful",
    ),
    StoryParams(
        scene="manor",
        culprit="cousin",
        victim="baker",
        tool="nooney_tonic",
        detective_name="Otis",
        detective_gender="boy",
        trait="sharp-eyed",
    ),
    StoryParams(
        scene="garden_hall",
        culprit="messenger",
        victim="gardener",
        tool="nooney_drops",
        detective_name="June",
        detective_gender="girl",
        trait="patient",
    ),
    StoryParams(
        scene="manor",
        culprit="aunt",
        victim="baker",
        tool="nooney_drops",
        detective_name="Rafi",
        detective_gender="boy",
        trait="quiet",
    ),
]


def explain_rejection(suspect: Suspect, victim: Victim, tool: Tool) -> str:
    if victim.room not in suspect.access_rooms:
        return (
            f"(No story: {suspect.label} could not reasonably reach the {victim.room}, "
            f"so this suspect had no chance to use {tool.label} on {victim.label}.)"
        )
    if tool.sense < SENSE_MIN:
        return (
            f"(No story: {tool.label} is below the common-sense threshold for this world.)"
        )
    return "(No story: that culprit, victim, and tool do not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "bad_ending"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(S, V, T) :- suspect(S), victim(V), tool(T), accesses(S, R), room_of(V, R), sensible(T).
valid(Scene, S, V, T) :- scene(Scene), hazard(S, V, T).

% --- outcome ---------------------------------------------------------------
transformation(beet) :- chosen_tool(T), tool_turns_into(T, beet).
outcome(bad_ending) :- chosen_tool(T), sensible(T), chosen_victim(V), victim(V), chosen_suspect(S), suspect(S), hazard(S, V, T).

#show valid/4.
#show outcome/1.
#show transformation/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for room in sorted(suspect.access_rooms):
            lines.append(asp.fact("accesses", suspect_id, room))
    for victim_id, victim in VICTIMS.items():
        lines.append(asp.fact("victim", victim_id))
        lines.append(asp.fact("room_of", victim_id, victim.room))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("sense", tool_id, tool.sense))
        if tool.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", tool_id))
        lines.append(asp.fact("tool_turns_into", tool_id, tool.transform_into))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_suspect", params.culprit),
            asp.fact("chosen_victim", params.victim),
            asp.fact("chosen_tool", params.tool),
        ]
    )
    model = asp.one_model(asp_program(extra))
    got = asp.atoms(model, "outcome")
    return got[0][0] if got else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for s in range(40):
        rng = random.Random(s)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny whodunit story world: a nooney transformation, a beet, and a bad ending."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--victim", choices=VICTIMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.culprit and args.victim and args.tool:
        suspect = SUSPECTS[args.culprit]
        victim = VICTIMS[args.victim]
        tool = TOOLS[args.tool]
        if not hazard_possible(suspect, victim, tool):
            raise StoryError(explain_rejection(suspect, victim, tool))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.culprit is None or combo[1] == args.culprit)
        and (args.victim is None or combo[2] == args.victim)
        and (args.tool is None or combo[3] == args.tool)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene, culprit, victim, tool = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    detective_name = rng.choice(DETECTIVE_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        scene=scene,
        culprit=culprit,
        victim=victim,
        tool=tool,
        detective_name=detective_name,
        detective_gender=detective_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.culprit not in SUSPECTS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.victim not in VICTIMS:
        raise StoryError(f"(Unknown victim: {params.victim})")
    if params.tool not in TOOLS:
        raise StoryError(f"(Unknown tool: {params.tool})")

    suspect = SUSPECTS[params.culprit]
    victim = VICTIMS[params.victim]
    tool = TOOLS[params.tool]
    if not hazard_possible(suspect, victim, tool):
        raise StoryError(explain_rejection(suspect, victim, tool))

    world = tell(
        scene=SCENES[params.scene],
        culprit_cfg=suspect,
        victim_cfg=victim,
        tool=tool,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, culprit, victim, tool) combos:\n")
        for scene, culprit, victim, tool in combos:
            print(f"  {scene:12} {culprit:10} {victim:10} {tool}")
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
            header = f"### {p.scene}: {p.culprit} -> {p.victim} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
