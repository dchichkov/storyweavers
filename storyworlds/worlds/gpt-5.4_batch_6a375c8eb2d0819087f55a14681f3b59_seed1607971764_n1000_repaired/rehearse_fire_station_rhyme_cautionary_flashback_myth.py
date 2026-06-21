#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py
===================================================================================

A standalone storyworld for a myth-tinged fire-station safety tale.

Small domain:
    A child visits a fire station to rehearse a safety rhyme before a practice
    drill. A firefighter tells a cautionary flashback in the shape of an old
    station myth, warning what happens when someone breaks the rhyme. Then the
    child either heeds the lesson at once or makes one unsafe move in the drill,
    gets frightened, and learns the rhyme the right way.

The world model drives the prose:
    - physical meters: smoke, danger, cough, confusion, found_exit
    - emotional memes: wonder, trust, bravado, caution, fear, relief, pride
    - a forward-chaining rule engine turns a wrong move in the chosen drill risk
      into a concrete scare
    - the ending image proves the change: the child can rehearse and teach the
      rhyme back safely inside the fire station

Run it:
    python storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py
    python storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py --risk smoke_hall --cue crawl_low
    python storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py --cue leave_it
    python storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/rehearse_fire_station_rhyme_cautionary_flashback_myth.py --verify
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
BRAVERY_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "thoughtful", "steady", "gentle"}


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
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
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
class Risk:
    id: str
    label: str
    room: str
    temptation: str
    unsafe_action: str
    danger_text: str
    harm: str
    safe_cue: str
    rhyme_need: str
    rhyme_line: str
    ending_image: str
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
class Cue:
    id: str
    label: str
    instruction: str
    benefit: str
    drill_action: str
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
class Myth:
    id: str
    title: str
    creature: str
    opening: str
    mistake_line: str
    warning_line: str
    rescue_line: str
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
        self.facts: dict = {
            "risk_id": "",
            "mistake_done": False,
            "predicted_danger": "",
        }

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


def _r_smoke_hall(world: World) -> list[str]:
    out: list[str] = []
    if world.facts["risk_id"] != "smoke_hall":
        return out
    kid = world.get("kid")
    room = world.get("room")
    if kid.meters["standing_in_smoke"] >= THRESHOLD:
        sig = ("smoke_hall", "standing")
        if sig not in world.fired:
            world.fired.add(sig)
            kid.meters["cough"] += 1
            kid.memes["fear"] += 1
            room.meters["danger"] += 1
            out.append("__scare__")
    return out


def _r_wrong_door(world: World) -> list[str]:
    out: list[str] = []
    if world.facts["risk_id"] != "wrong_door":
        return out
    kid = world.get("kid")
    room = world.get("room")
    if kid.meters["wandering"] >= THRESHOLD:
        sig = ("wrong_door", "wandering")
        if sig not in world.fired:
            world.fired.add(sig)
            kid.meters["confused"] += 1
            kid.memes["fear"] += 1
            room.meters["danger"] += 1
            out.append("__scare__")
    return out


def _r_lost_toy(world: World) -> list[str]:
    out: list[str] = []
    if world.facts["risk_id"] != "lost_toy":
        return out
    kid = world.get("kid")
    room = world.get("room")
    if kid.meters["turned_back"] >= THRESHOLD:
        sig = ("lost_toy", "turn_back")
        if sig not in world.fired:
            world.fired.add(sig)
            kid.meters["delay"] += 1
            kid.memes["fear"] += 1
            room.meters["danger"] += 1
            out.append("__scare__")
    return out


CAUSAL_RULES = [
    Rule(name="smoke_hall", tag="physical", apply=_r_smoke_hall),
    Rule(name="wrong_door", tag="physical", apply=_r_wrong_door),
    Rule(name="lost_toy", tag="physical", apply=_r_lost_toy),
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


RISKS = {
    "smoke_hall": Risk(
        id="smoke_hall",
        label="smoke in the practice hall",
        room="the training hall",
        temptation="walk tall like a hero",
        unsafe_action="kept walking upright through the gray practice smoke",
        danger_text="the higher smoke scratched at little throats and hid the ceiling lights",
        harm="The smoke sat higher in the room, so standing up put the child right in the thickest part.",
        safe_cue="crawl_low",
        rhyme_need="when smoke rolls high",
        rhyme_line="When smoke rides high, stay low and go.",
        ending_image="one small helmet bobbing low and sure beneath the silver smoke",
        tags={"smoke", "crawl", "fire_station"},
    ),
    "wrong_door": Risk(
        id="wrong_door",
        label="confusing doors in the drill maze",
        room="the old bunk-room corridor",
        temptation="dash toward any bright-looking doorway",
        unsafe_action="raced toward a shiny side door instead of the marked exit",
        danger_text="the corridor twisted with lockers and shadows until every doorway looked almost right",
        harm="The child could have wandered deeper inside, because not every door leads out.",
        safe_cue="follow_bell",
        rhyme_need="when bells sing out",
        rhyme_line="When bells sing clear, follow and steer.",
        ending_image="small boots turning straight toward the bright red exit lamp",
        tags={"alarm", "exit", "fire_station"},
    ),
    "lost_toy": Risk(
        id="lost_toy",
        label="wanting to go back for a dropped toy",
        room="the gear room by the engines",
        temptation="run back for a fallen toy badge",
        unsafe_action="turned back for the toy badge after the drill horn sounded",
        danger_text="the shining engines and hanging coats made the room feel bigger and slower than it had a moment before",
        harm="Going back for a toy costs time, and leaving fast matters more than keeping a little thing.",
        safe_cue="leave_it",
        rhyme_need="when treasures fall",
        rhyme_line="When treasures fall, leave them and call.",
        ending_image="a toy badge left behind on the floor while the child reached safety first",
        tags={"evacuate", "leave_it", "fire_station"},
    ),
}

CUES = {
    "crawl_low": Cue(
        id="crawl_low",
        label="crawl low",
        instruction="drop low, use knees and hands, and keep moving toward the door",
        benefit="The cleanest air is lower, so the child can breathe and see better there.",
        drill_action="crawled low beneath the worst of the smoke",
        tags={"crawl", "smoke"},
    ),
    "follow_bell": Cue(
        id="follow_bell",
        label="follow the bell light",
        instruction="look for the blinking bell light and go only where it leads",
        benefit="A marked signal guides the child toward the practiced safe exit instead of a confusing side path.",
        drill_action="followed the blinking bell light to the right door",
        tags={"alarm", "exit"},
    ),
    "leave_it": Cue(
        id="leave_it",
        label="leave it and tell",
        instruction="leave the dropped thing behind and tell a grown-up once outside",
        benefit="Leaving a toy behind saves time, and grown-ups can help later after everyone is safe.",
        drill_action="left the toy where it lay and headed out at once",
        tags={"evacuate", "leave_it"},
    ),
}

MYTHS = {
    "ash_dragon": Myth(
        id="ash_dragon",
        title="the Ash Dragon",
        creature="Ash Dragon",
        opening="Old firefighters said an Ash Dragon once curled in the rafters and fed on foolish steps.",
        mistake_line="A proud child in the tale forgot the station rhyme and rose too high for the dragon's breath.",
        warning_line="The old bell kept singing, but pride made the room feel longer than it was.",
        rescue_line="Only when the child remembered the right line did the path grow plain and safe again.",
        tags={"myth", "dragon"},
    ),
    "cinder_crow": Myth(
        id="cinder_crow",
        title="the Cinder Crow",
        creature="Cinder Crow",
        opening="On stormy nights, people whispered that the Cinder Crow perched above the engine doors and watched for careless hearts.",
        mistake_line="In the old story, a child broke the rhyme and chased the wrong glitter instead of the true way out.",
        warning_line="The crow loved confusion more than flame, and it pecked at every bad hurry.",
        rescue_line="When the child listened at last, even the crow had to flap away from the bright safe path.",
        tags={"myth", "crow"},
    ),
    "smoke_ogre": Myth(
        id="smoke_ogre",
        title="the Smoke Ogre",
        creature="Smoke Ogre",
        opening="Grandparents used to tell of a Smoke Ogre who grew only where children forgot the lesson of the bell.",
        mistake_line="The tale says one child reached back for a shiny treasure and almost fed the ogre with delay.",
        warning_line="The ogre was never strongest in fire; it was strongest in one more foolish moment.",
        rescue_line="A calm firefighter called the rhyme, and the child's feet found the safe road again.",
        tags={"myth", "ogre"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Ivy", "Tessa", "Ruby", "Mila"]
BOY_NAMES = ["Theo", "Eli", "Jonah", "Sam", "Noah", "Milo", "Ben", "Leo"]
TRAITS = ["careful", "curious", "steady", "bold", "eager", "thoughtful", "gentle"]
MENTOR_NAMES = ["Captain Mara", "Captain Ivo", "Firefighter June", "Firefighter Tomas"]


def valid_combo(risk_id: str, cue_id: str) -> bool:
    risk = RISKS[risk_id]
    return risk.safe_cue == cue_id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for myth_id in MYTHS:
        for risk_id, risk in RISKS.items():
            for cue_id in CUES:
                if risk.safe_cue == cue_id:
                    combos.append((myth_id, risk_id, cue_id))
    return combos


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_heed(trust: int, trait: str, bravery: float = BRAVERY_INIT) -> bool:
    return float(trust) + initial_caution(trait) > bravery + 4.0


def predict_scare(world: World, risk_id: str) -> dict:
    sim = world.copy()
    sim.facts["risk_id"] = risk_id
    if risk_id == "smoke_hall":
        sim.get("kid").meters["standing_in_smoke"] += 1
    elif risk_id == "wrong_door":
        sim.get("kid").meters["wandering"] += 1
    elif risk_id == "lost_toy":
        sim.get("kid").meters["turned_back"] += 1
    propagate(sim, narrate=False)
    kid = sim.get("kid")
    room = sim.get("room")
    return {
        "fear": kid.memes["fear"],
        "danger": room.meters["danger"],
    }


def introduce(world: World, kid: Entity, mentor: Entity) -> None:
    world.say(
        f"In the red-brick fire station, where boots stood in rows like sleeping giants, "
        f"{kid.id} came to meet {mentor.id} and rehearse the station safety rhyme."
    )
    world.say(
        f"The brass bell above the engine bay gleamed as if it remembered a hundred old stories."
    )
    kid.memes["wonder"] += 1


def station_detail(world: World, risk: Risk) -> None:
    world.say(
        f"Today the practice would happen in {risk.room}, and everyone said the lesson mattered {risk.rhyme_need}."
    )
    world.say(
        f"In that place, {risk.danger_text}."
    )


def teach_rhyme(world: World, mentor: Entity, risk: Risk, cue: Cue) -> None:
    kid = world.get("kid")
    kid.memes["trust"] += 1
    world.say(
        f'{mentor.id} tapped the floor once with two fingers and said, '
        f'"Here is the line we rehearse before drills: {risk.rhyme_line}"'
    )
    world.say(
        f'"And what does it mean?" asked {mentor.pronoun("subject")} gently. '
        f'"It means {cue.instruction}."'
    )


def temptation(world: World, kid: Entity, risk: Risk) -> None:
    kid.memes["bravado"] += 1
    world.say(
        f"But {kid.id} wanted to {risk.temptation}. The engines were shining, the helmets were bright, "
        f"and bravery felt easy while everything was still quiet."
    )


def flashback_warning(world: World, mentor: Entity, myth: Myth, risk: Risk) -> None:
    pred = predict_scare(world, risk.id)
    world.facts["predicted_danger"] = risk.harm
    world.facts["predicted_fear"] = pred["fear"]
    mentor.memes["care"] += 1
    world.para()
    world.say(
        f"{mentor.id} saw that proud look and grew still. Then {mentor.pronoun('subject')} told a flashback the old station loved to keep."
    )
    world.say(
        f"{myth.opening} {myth.mistake_line} {myth.warning_line} {myth.rescue_line}"
    )
    world.say(
        f'"That story sounds like a myth," {kid.id} whispered.'
    )
    world.say(
        f'"Maybe," said {mentor.id}. "But the danger in it is plain and true. {risk.harm}"'
    )


def decide(world: World, kid: Entity, mentor: Entity, trust: int, trait: str) -> bool:
    heed = would_heed(trust=trust, trait=trait)
    if heed:
        kid.memes["caution"] += 1
        world.say(
            f"{kid.id} took a breath, looked at {mentor.id}, and nodded. The rhyme settled inside {kid.pronoun('object')} like a small bright nail holding a door steady."
        )
    else:
        kid.memes["defiance"] += 1
        world.say(
            f"{kid.id} nodded, but the wish to look brave was still louder than the lesson."
        )
    return heed


def start_drill(world: World, mentor: Entity) -> None:
    world.para()
    world.say(
        f"Then the practice horn sounded through the station: one clear call, then another."
    )
    world.say(
        f'{mentor.id} raised a hand. "Now we do only what we rehearsed."'
    )


def perform_safe(world: World, kid: Entity, cue: Cue, risk: Risk) -> None:
    kid.meters["found_exit"] += 1
    kid.memes["relief"] += 1
    kid.memes["pride"] += 1
    world.say(
        f"{kid.id} remembered the line and {cue.drill_action}. {cue.benefit}"
    )
    world.say(
        f"Soon the child was outside in the yard, safe beneath the open sky."
    )
    world.say(
        f"The last thing seen in the doorway was {risk.ending_image}."
    )


def perform_mistake(world: World, kid: Entity, risk: Risk) -> None:
    world.facts["mistake_done"] = True
    if risk.id == "smoke_hall":
        kid.meters["standing_in_smoke"] += 1
    elif risk.id == "wrong_door":
        kid.meters["wandering"] += 1
    elif risk.id == "lost_toy":
        kid.meters["turned_back"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But instead {kid.id} {risk.unsafe_action}."
    )
    if risk.id == "smoke_hall":
        world.say(
            f"{kid.pronoun('possessive').capitalize()} throat prickled at once, and the room seemed meaner than it had a heartbeat before."
        )
    elif risk.id == "wrong_door":
        world.say(
            f"For one scary blink, every handle looked strange, and the sure way out was not sure at all."
        )
    else:
        world.say(
            f"The single step back made the room feel wide and wrong, and fear came in fast."
        )


def rescue_and_correct(world: World, kid: Entity, mentor: Entity, cue: Cue, risk: Risk) -> None:
    room = world.get("room")
    room.meters["danger"] = 0.0
    kid.memes["fear"] = max(0.0, kid.memes["fear"])
    kid.memes["relief"] += 1
    kid.memes["caution"] += 1
    kid.meters["found_exit"] += 1
    world.say(
        f'{mentor.id} was beside {kid.pronoun("object")} in two quick steps. "{risk.rhyme_line}" {mentor.pronoun("subject")} called.'
    )
    world.say(
        f"This time {kid.id} listened and {cue.drill_action}. {cue.benefit}"
    )
    world.say(
        f"When they reached the yard, {kid.id} leaned against {mentor.id}'s coat and let the fear leave little by little."
    )


def close_lesson(world: World, kid: Entity, mentor: Entity, cue: Cue, risk: Risk) -> None:
    world.para()
    kid.memes["trust"] += 1
    kid.memes["pride"] += 1
    world.say(
        f'{mentor.id} knelt so their faces were even. "A drill is where we learn before a true hard moment comes," {mentor.pronoun("subject")} said.'
    )
    world.say(
        f'"So we rehearse the rhyme now," said {kid.id}, "so our feet can remember it later."'
    )
    world.say(
        f'"Yes," said {mentor.id}. "And the rhyme is not magic by itself. It is a little rope for the mind."'
    )
    world.say(
        f"Once more, under the old bell, {kid.id} spoke the line aloud: {risk.rhyme_line}"
    )
    world.say(
        f"Then {kid.pronoun('subject')} showed the younger visitors how to {cue.instruction}, and the fire station seemed less like a hall of giants and more like a house of helpers."
    )


def tell(
    *,
    myth: Myth,
    risk: Risk,
    cue: Cue,
    kid_name: str = "Nora",
    kid_type: str = "girl",
    mentor_name: str = "Captain Mara",
    mentor_type: str = "woman",
    trait: str = "careful",
    trust: int = 5,
) -> World:
    world = World()
    kid = world.add(Entity(
        id=kid_name,
        kind="character",
        type=kid_type,
        label=kid_name,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    mentor = world.add(Entity(
        id=mentor_name,
        kind="character",
        type=mentor_type,
        label="the firefighter",
        role="mentor",
        attrs={"rank": mentor_name.split()[0]},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="fire_station_room",
        label=risk.room,
    ))

    kid.memes["trust"] = float(trust)
    kid.memes["caution"] = initial_caution(trait)
    kid.memes["bravery"] = BRAVERY_INIT
    world.facts["risk_id"] = risk.id
    world.facts["cue_id"] = cue.id
    world.facts["myth_id"] = myth.id

    introduce(world, kid, mentor)
    station_detail(world, risk)

    world.para()
    teach_rhyme(world, mentor, risk, cue)
    temptation(world, kid, risk)
    flashback_warning(world, mentor, myth, risk)
    heed = decide(world, kid, mentor, trust, trait)

    start_drill(world, mentor)
    if heed:
        perform_safe(world, kid, cue, risk)
        outcome = "heeded"
    else:
        perform_mistake(world, kid, risk)
        rescue_and_correct(world, kid, mentor, cue, risk)
        outcome = "corrected"

    close_lesson(world, kid, mentor, cue, risk)

    world.facts.update(
        kid=kid,
        mentor=mentor,
        room=room,
        risk=risk,
        cue=cue,
        myth=myth,
        outcome=outcome,
        trust=trust,
        trait=trait,
        heeded=(outcome == "heeded"),
        scared=world.facts["mistake_done"],
    )
    return world


@dataclass
class StoryParams:
    myth: str
    risk: str
    cue: str
    name: str
    gender: str
    mentor: str
    mentor_gender: str
    trait: str
    trust: int = 5
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "fire_station": [
        (
            "What happens in a fire station?",
            "A fire station is where firefighters keep their engines, tools, and safety gear. It is also a place where people can practice drills and learn how to stay safe."
        )
    ],
    "smoke": [
        (
            "Why is smoke dangerous?",
            "Smoke can make it hard to see and hard to breathe. In a fire, cleaner air is often lower than the thick smoke above."
        )
    ],
    "crawl": [
        (
            "Why do people crawl low in smoke?",
            "People crawl low because the thicker smoke rises higher. Staying low can help you breathe better and find the way out."
        )
    ],
    "alarm": [
        (
            "What is a fire alarm for?",
            "A fire alarm warns people that they need to leave quickly and safely. It helps everyone start moving before danger gets worse."
        )
    ],
    "exit": [
        (
            "Why should you follow the marked exit in a drill?",
            "The marked exit shows the safe path out. Picking a random door can lead you the wrong way."
        )
    ],
    "evacuate": [
        (
            "Why should you leave toys behind during an emergency?",
            "You should leave toys behind because getting out safely matters more than keeping an object. A grown-up can help with things later, but people need to be safe first."
        )
    ],
    "leave_it": [
        (
            "What does 'leave it and tell' mean?",
            "It means do not go back for the dropped thing. Get to safety first, then tell a grown-up what was left behind."
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is an old story people tell to carry an idea or warning. Even when the creature in the story is pretend, the lesson can still be true."
        )
    ],
}

KNOWLEDGE_ORDER = ["fire_station", "myth", "smoke", "crawl", "alarm", "exit", "evacuate", "leave_it"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = f["kid"]
    risk = f["risk"]
    cue = f["cue"]
    myth = f["myth"]
    if f["outcome"] == "heeded":
        return [
            f'Write a child-facing myth-like story set in a fire station that uses the word "rehearse" and includes a rhyme, a cautionary flashback, and a safe drill.',
            f"Tell a story where {kid.id} learns the old station line '{risk.rhyme_line}' after hearing a flashback about {myth.title}, then follows the rule to stay safe.",
            f"Write a gentle cautionary tale in a fire station where a firefighter teaches a rhyme and a child remembers to {cue.instruction}.",
        ]
    return [
        f'Write a child-facing myth-like story set in a fire station that uses the word "rehearse" and includes a rhyme, a cautionary flashback, and one scary mistake in a drill.',
        f"Tell a story where {kid.id} wants to be brave, ignores a warning for one moment, then learns the line '{risk.rhyme_line}' the hard way in a fire-station practice.",
        f"Write a cautionary myth for young children where an old station tale about {myth.creature} helps a child finally choose the safe rule: {cue.instruction}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    kid = f["kid"]
    mentor = f["mentor"]
    risk = f["risk"]
    cue = f["cue"]
    myth = f["myth"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {kid.id}, a child visiting a fire station, and {mentor.id}, the firefighter who teaches the drill. Together they practice a safety rhyme before the horn sounds."
        ),
        (
            f"Why did {kid.id} come to the fire station?",
            f"{kid.id} came to rehearse a safety rhyme before a practice drill. The station was using the rhyme to help children remember what to do in a frightening moment."
        ),
        (
            "What was the rhyme for?",
            f'The rhyme was for {risk.label}. It turned the rule "{risk.rhyme_line}" into words small enough to remember fast.'
        ),
        (
            f"Why did {mentor.id} tell a flashback about {myth.title}?",
            f"{mentor.id} used the old story as a warning, not just as entertainment. The flashback matched the real risk in the drill, so the child could feel why the rule mattered."
        ),
    ]
    if f["outcome"] == "heeded":
        qa.append(
            (
                f"How did {kid.id} stay safe in the drill?",
                f"{kid.id} remembered the rhyme and {cue.drill_action}. {cue.benefit}"
            )
        )
        qa.append(
            (
                f"What changed by the end of the story?",
                f"At first {kid.id} wanted to look brave in the wrong way. By the end, {kid.pronoun('subject')} understood that real bravery means following the practiced safety rule and even teaching it to younger visitors."
            )
        )
    else:
        qa.append(
            (
                f"What unsafe thing did {kid.id} do, and why was it dangerous?",
                f"{kid.id} {risk.unsafe_action}. {risk.harm}"
            )
        )
        qa.append(
            (
                f"How did {mentor.id} help after the mistake?",
                f'{mentor.id} called out the rhyme again and guided {kid.id} back to the safe action. The correction worked because the child finally connected the old warning story to the real drill.'
            )
        )
        qa.append(
            (
                f"What changed by the end of the story?",
                f"{kid.id} began by chasing a proud or hurried impulse, but the scare made the lesson real. By the end, {kid.pronoun('subject')} could say the rhyme, do the safe move, and teach it with respect instead of showing off."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["risk"].tags) | set(f["cue"].tags) | {"myth"}
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:14} ({ent.type:16}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        myth="ash_dragon",
        risk="smoke_hall",
        cue="crawl_low",
        name="Nora",
        gender="girl",
        mentor="Captain Mara",
        mentor_gender="woman",
        trait="careful",
        trust=7,
    ),
    StoryParams(
        myth="cinder_crow",
        risk="wrong_door",
        cue="follow_bell",
        name="Theo",
        gender="boy",
        mentor="Firefighter June",
        mentor_gender="woman",
        trait="bold",
        trust=3,
    ),
    StoryParams(
        myth="smoke_ogre",
        risk="lost_toy",
        cue="leave_it",
        name="Mila",
        gender="girl",
        mentor="Captain Ivo",
        mentor_gender="man",
        trait="thoughtful",
        trust=6,
    ),
    StoryParams(
        myth="ash_dragon",
        risk="wrong_door",
        cue="follow_bell",
        name="Eli",
        gender="boy",
        mentor="Firefighter Tomas",
        mentor_gender="man",
        trait="eager",
        trust=2,
    ),
]


def explain_rejection(risk_id: str, cue_id: str) -> str:
    risk = RISKS[risk_id]
    cue = CUES[cue_id]
    return (
        f"(No story: '{cue.label}' does not solve the risk '{risk.label}'. "
        f"This drill needs the rule '{RISKS[risk_id].safe_cue}', because {risk.harm})"
    )


ASP_RULES = r"""
valid(M, R, C) :- myth(M), risk(R), cue(C), safe_cue(R, C).

init_caution(5) :- trait(T), cautious_trait(T).
init_caution(3) :- trait(T), not cautious_trait(T).
authority(TS + C) :- trust(TS), init_caution(C).
heeded :- authority(A), bravery_init(B), A > B + 4.
outcome(heeded) :- heeded.
outcome(corrected) :- not heeded.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for myth_id in MYTHS:
        lines.append(asp.fact("myth", myth_id))
    for risk_id, risk in RISKS.items():
        lines.append(asp.fact("risk", risk_id))
        lines.append(asp.fact("safe_cue", risk_id, risk.safe_cue))
    for cue_id in CUES:
        lines.append(asp.fact("cue", cue_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("cautious_trait", trait))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("trust", params.trust),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "heeded" if would_heed(trust=params.trust, trait=params.trait) else "corrected"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0] if cases else CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-tinged fire-station drill stories with rhyme, flashback, and caution."
    )
    ap.add_argument("--myth", choices=sorted(MYTHS))
    ap.add_argument("--risk", choices=sorted(RISKS))
    ap.add_argument("--cue", choices=sorted(CUES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor", choices=sorted(MENTOR_NAMES))
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=sorted(TRAITS))
    ap.add_argument("--trust", type=int, choices=list(range(0, 11)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.risk and args.cue and not valid_combo(args.risk, args.cue):
        raise StoryError(explain_rejection(args.risk, args.cue))

    combos = [
        combo for combo in valid_combos()
        if (args.myth is None or combo[0] == args.myth)
        and (args.risk is None or combo[1] == args.risk)
        and (args.cue is None or combo[2] == args.cue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    myth_id, risk_id, cue_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    mentor = args.mentor or rng.choice(sorted(MENTOR_NAMES))
    mentor_gender = args.mentor_gender or ("woman" if mentor in {"Captain Mara", "Firefighter June"} else "man")
    trait = args.trait or rng.choice(sorted(TRAITS))
    trust = args.trust if args.trust is not None else rng.randint(0, 10)

    return StoryParams(
        myth=myth_id,
        risk=risk_id,
        cue=cue_id,
        name=name,
        gender=gender,
        mentor=mentor,
        mentor_gender=mentor_gender,
        trait=trait,
        trust=trust,
    )


def _checked_lookup(table: dict, key: str, field_name: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {field_name} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    myth = _checked_lookup(MYTHS, params.myth, "myth")
    risk = _checked_lookup(RISKS, params.risk, "risk")
    cue = _checked_lookup(CUES, params.cue, "cue")
    if not valid_combo(params.risk, params.cue):
        raise StoryError(explain_rejection(params.risk, params.cue))

    world = tell(
        myth=myth,
        risk=risk,
        cue=cue,
        kid_name=params.name,
        kid_type=params.gender,
        mentor_name=params.mentor,
        mentor_type=params.mentor_gender,
        trait=params.trait,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (myth, risk, cue) combos:\n")
        for myth_id, risk_id, cue_id in combos:
            print(f"  {myth_id:12} {risk_id:12} {cue_id}")
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
            header = f"### {p.name}: {p.risk} with {p.cue} ({p.myth}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
