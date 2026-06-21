#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py
===================================================================================

A standalone storyworld about two children turning a living room into a pirate
deck and using an exercycle as a pretend engine. The world model keeps track of
physical state (spin, wobble, solved need) and emotional state (pride, fear,
trust, left-out feelings), so the prose changes with the simulation.

Reference seed re-imagined into a tiny story domain:
----------------------------------------------------
Two children are playing pirates. They need something the ship does not yet
have: wind for a paper sail, light for a cave, or a bell-call for a foggy
harbor. In the corner stands an exercycle, which the children call an
imaginative, power-ful machine.

One child wants to pedal it alone and show off. The other remembers a flashback:
earlier, a parent had said the bike was for one rider at a time and for sharing,
not showing off. If the warning lands, the children take turns right away. If
not, the first child pedals too hard, the bike wobbles, and a parent comes to
steady the play. In both branches, the ending proves the moral value: the ship
moves forward only when the children share the power.

Run it
------
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py --need wind --attachment fan
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py --need wind --attachment lamp
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py --all
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/imaginative_power_ful_exercycle_moral_value_flashback.py --verify
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
STEADY_TRAITS = {"careful", "steady", "thoughtful", "patient"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
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
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    mission: str
    ending: str
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
class Need:
    id: str
    problem: str
    ask: str
    solved_text: str
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
class Attachment:
    id: str
    label: str
    phrase: str
    need: str
    effect: str
    click: str
    qa_text: str
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
class Value:
    id: str
    name: str
    flashback_line: str
    lesson_line: str
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
            "need_id": "",
            "attachment_id": "",
            "value_id": "",
            "shared": False,
            "mission_done": False,
            "wobble": False,
            "flashback_happened": False,
            "outcome": "",
        }

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"hero", "mate"}]

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


def _r_power_matches_need(world: World) -> list[str]:
    cycle = world.get("cycle")
    tool = world.get("attachment")
    need = world.get("need")
    if cycle.meters["spin"] < THRESHOLD:
        return []
    if tool.attrs.get("need") != world.facts["need_id"]:
        return []
    sig = ("solved", tool.id, need.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    need.meters["solved"] += 1
    world.facts["mission_done"] = True
    return ["__mission__"]


def _r_showing_off_hurts(world: World) -> list[str]:
    hero = world.get("hero")
    mate = world.get("mate")
    cycle = world.get("cycle")
    if cycle.meters["spin"] < THRESHOLD or hero.memes["hogging"] < THRESHOLD:
        return []
    sig = ("left_out", hero.id, mate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    mate.memes["left_out"] += 1
    mate.memes["sad"] += 1
    return ["__left_out__"]


def _r_strain_causes_wobble(world: World) -> list[str]:
    cycle = world.get("cycle")
    if cycle.meters["strain"] < THRESHOLD:
        return []
    sig = ("wobble", cycle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cycle.meters["wobble"] += 1
    world.facts["wobble"] = True
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__wobble__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="power_matches_need", tag="physical", apply=_r_power_matches_need),
    Rule(name="showing_off_hurts", tag="social", apply=_r_showing_off_hurts),
    Rule(name="strain_causes_wobble", tag="physical", apply=_r_strain_causes_wobble),
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


def supports(attachment: Attachment, need: Need) -> bool:
    return attachment.need == need.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for need_id, need in NEEDS.items():
            for attachment_id, attachment in ATTACHMENTS.items():
                if supports(attachment, need):
                    combos.append((theme_id, need_id, attachment_id))
    return combos


def initial_steadiness(trait: str) -> float:
    return 5.0 if trait in STEADY_TRAITS else 3.0


def would_share_early(relation: str, hero_age: int, mate_age: int, trait: str) -> bool:
    mate_older_sibling = relation == "siblings" and mate_age > hero_age
    authority = initial_steadiness(trait) + (3.0 if mate_older_sibling else 0.0)
    return mate_older_sibling and authority >= 8.0


def explain_rejection(need: Need, attachment: Attachment) -> str:
    return (
        f"(No story: {attachment.phrase} can make {attachment.effect}, but this mission needs "
        f"{need.solved_text.lower()}. The exercycle only helps when the attachment honestly "
        f"matches the ship's problem.)"
    )


def predict_success(world: World) -> dict:
    sim = world.copy()
    sim.get("cycle").meters["spin"] += 1
    propagate(sim, narrate=False)
    return {
        "mission_done": bool(sim.facts["mission_done"]),
        "wobble": bool(sim.facts["wobble"]),
    }


def play_setup(world: World, hero: Entity, mate: Entity, theme: Theme) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {hero.id} and {mate.id} turned the living room into "
        f"{theme.scene}. {theme.rig}"
    )
    world.say(
        f'"{theme.captain} {hero.id} and {theme.mate} {mate.id}!" {hero.id} cried. '
        f'"Today we sail for {theme.mission}!"'
    )


def introduce_exercycle(world: World, hero: Entity) -> None:
    cycle = world.get("cycle")
    hero.memes["wonder"] += 1
    world.say(
        f"In the corner stood an exercycle. To {hero.id}, it looked like an imaginative, "
        f"power-ful engine waiting for a pirate crew."
    )
    world.say(
        f'{hero.id} touched the handlebar as if it were the wheel of a ship. '
        f'"If we pedal this, maybe our voyage will wake up," {hero.pronoun()} said.'
    )


def need_arises(world: World, mate: Entity, need: Need) -> None:
    world.say(need.problem)
    world.say(f'{mate.id} looked around and whispered, "{need.ask}"')


def flashback_warning(
    world: World,
    mate: Entity,
    hero: Entity,
    parent: Entity,
    value: Value,
    need: Need,
    attachment: Attachment,
) -> None:
    pred = predict_success(world)
    world.facts["predicted_success"] = pred["mission_done"]
    world.facts["predicted_wobble"] = pred["wobble"]
    world.facts["flashback_happened"] = True
    mate.memes["caution"] += 1
    world.say(
        f"{mate.id} reached for {hero.id}'s sleeve, and a flashback came to {mate.pronoun('object')}: "
        f"that morning, {parent.label_word} had tapped the seat and said, "
        f'"{value.flashback_line}"'
    )
    world.say(
        f'{mate.id} remembered every word. "{attachment.label.capitalize()} can help with '
        f'{need.solved_text.lower()}, but only if we are gentle and take turns," '
        f'{mate.pronoun()} said.'
    )


def boast(world: World, hero: Entity, mate: Entity) -> None:
    hero.memes["pride"] += 1
    hero.memes["hogging"] += 1
    world.say(
        f'"I can do it myself," {hero.id} said, already climbing onto the seat. '
        f'"Watch how fast a captain can make a ship go."'
    )
    if mate.attrs.get("relation") == "siblings" and hero.age > mate.age:
        world.say(
            f"Because {hero.id} was the older child, {mate.id} hesitated for one breath, "
            f"not wanting to spoil the game."
        )


def back_down(world: World, hero: Entity, mate: Entity, value: Value) -> None:
    hero.memes["pride"] = 0.0
    hero.memes["hogging"] = 0.0
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.say(
        f"{hero.id} looked at the seat, then at {mate.id}, and the brave-showing-off feeling "
        f"slipped away."
    )
    world.say(
        f'"You are right," {hero.pronoun()} said. "A real captain keeps {value.name.lower()}." '
        f"{hero.id} stepped down and made room."
    )


def pedal_alone(world: World, hero: Entity, attachment: Attachment) -> None:
    cycle = world.get("cycle")
    cycle.meters["spin"] += 1
    cycle.meters["strain"] += 1
    hero.memes["effort"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} pushed the pedals hard. {attachment.click} The {attachment.label} answered, "
        f"and for one exciting second it really did seem as if pirate power had leapt into the room."
    )
    if world.get("mate").memes["left_out"] >= THRESHOLD:
        world.say(
            f"But {mate_name(world)} was left holding the map alone, and the game stopped feeling shared."
        )
    if world.facts["wobble"]:
        world.say(
            "Then the exercycle gave a shaky rattle. The handlebars twitched, the pretend ship lurched, "
            "and both children forgot to grin."
        )


def mate_name(world: World) -> str:
    return world.get("mate").id


def call_parent(world: World, parent: Entity, hero: Entity, mate: Entity) -> None:
    world.say(f'"{parent.label_word.upper()}!" {mate.id} yelped.')
    world.say(
        f"{parent.label_word.capitalize()} came quickly from the kitchen and put steady hands on the "
        "handlebars before the wobble could grow."
    )
    hero.memes["fear"] = 0.0
    mate.memes["fear"] = 0.0
    world.get("cycle").meters["strain"] = 0.0


def lesson(world: World, parent: Entity, hero: Entity, mate: Entity, value: Value) -> None:
    hero.memes["lesson"] += 1
    mate.memes["lesson"] += 1
    hero.memes["trust"] += 1
    mate.memes["trust"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "This bike is strong," '
        f'{parent.pronoun()} said softly, "but strength is not for showing off. '
        f'{value.lesson_line}"'
    )
    world.say(
        f"{hero.id} looked at {mate.id}'s face and finally noticed the part that mattered: "
        f"{mate.id} had been trying to sail too."
    )


def share_turns(world: World, hero: Entity, mate: Entity, attachment: Attachment, value: Value) -> None:
    cycle = world.get("cycle")
    cycle.meters["spin"] += 1
    cycle.meters["strain"] = 0.0
    hero.memes["hogging"] = 0.0
    mate.memes["left_out"] = 0.0
    world.facts["shared"] = True
    propagate(world, narrate=False)
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    hero.memes["trust"] += 1
    mate.memes["trust"] += 1
    world.say(
        f"So {hero.id} pedaled for ten slow counts, then {mate.id} pedaled for ten more. "
        f"Each child kept one hand on the story and one on {value.name.lower()}."
    )
    world.say(
        f"The exercycle no longer sounded wild. It sounded busy and happy, and the {attachment.label} "
        f"worked just the way it should."
    )


def finish_mission(world: World, theme: Theme, need: Need) -> None:
    world.say(need.solved_text)
    world.say(
        f"And because the power was shared instead of grabbed, {theme.ending}."
    )


def tell(
    theme: Theme,
    need: Need,
    attachment: Attachment,
    value: Value,
    hero_name: str = "Tom",
    hero_gender: str = "boy",
    mate_name_value: str = "Lily",
    mate_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    hero_age: int = 6,
    mate_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    world.facts["need_id"] = need.id
    world.facts["attachment_id"] = attachment.id
    world.facts["value_id"] = value.id

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["bold"],
            age=hero_age,
            attrs={"relation": relation},
        )
    )
    mate = world.add(
        Entity(
            id=mate_name_value,
            kind="character",
            type=mate_gender,
            role="mate",
            traits=[trait],
            age=mate_age,
            attrs={"relation": relation},
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            role="parent",
            label="the parent",
        )
    )
    cycle = world.add(
        Entity(
            id="cycle",
            type="exercycle",
            label="the exercycle",
            attrs={"one_rider": True},
        )
    )
    world.add(
        Entity(
            id="attachment",
            type="attachment",
            label=attachment.label,
            attrs={"need": attachment.need},
        )
    )
    world.add(
        Entity(
            id="need",
            type="need",
            label=need.id,
            attrs={"problem": need.problem},
        )
    )

    hero.memes["pride"] = 0.0
    hero.memes["hogging"] = 0.0
    hero.memes["fear"] = 0.0
    mate.memes["left_out"] = 0.0
    mate.memes["fear"] = 0.0
    mate.memes["caution"] = initial_steadiness(trait)
    cycle.meters["spin"] = 0.0
    cycle.meters["strain"] = 0.0
    cycle.meters["wobble"] = 0.0
    world.get("need").meters["solved"] = 0.0

    play_setup(world, hero, mate, theme)
    introduce_exercycle(world, hero)
    need_arises(world, mate, need)

    world.para()
    flashback_warning(world, mate, hero, parent, value, need, attachment)

    if would_share_early(relation, hero_age, mate_age, trait):
        back_down(world, hero, mate, value)
        world.para()
        share_turns(world, hero, mate, attachment, value)
        finish_mission(world, theme, need)
        world.facts["outcome"] = "shared_early"
    else:
        boast(world, hero, mate)
        world.para()
        pedal_alone(world, hero, attachment)
        world.para()
        call_parent(world, parent, hero, mate)
        lesson(world, parent, hero, mate, value)
        world.para()
        share_turns(world, hero, mate, attachment, value)
        finish_mission(world, theme, need)
        world.facts["outcome"] = "guided_share"

    world.facts.update(
        hero=hero,
        mate=mate,
        parent=parent,
        cycle=cycle,
        theme=theme,
        need_cfg=need,
        attachment_cfg=attachment,
        value=value,
        relation=relation,
        mission_done=bool(world.facts["mission_done"]),
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a bright little pirate bay",
        rig="The couch was their ship, a blanket was the sea, a cardboard box became the treasure chest, and a spoon in a flowerpot marked the harbor bell.",
        captain="Captain",
        mate="First Mate",
        mission="Treasure Cove",
        ending="the little ship reached Treasure Cove with both pirates laughing",
    ),
    "storm_sailors": Theme(
        id="storm_sailors",
        scene="a stormy sea made from rugs and cushions",
        rig="Two chairs became the stern, a laundry basket became the captain's cabin, and a blue towel rolled across the floor like a wavy sea.",
        captain="Captain",
        mate="Deckhand",
        mission="the brave blue island",
        ending="their brave little vessel glided to the blue island in good order",
    ),
    "lantern_crew": Theme(
        id="lantern_crew",
        scene="a moonlit pirate deck",
        rig="The coffee table was the map table, the couch arm was the mast, and a striped scarf trailed behind like a sea flag.",
        captain="Captain",
        mate="Lamp Keeper",
        mission="the hidden harbor",
        ending="their tiny pirate deck felt warm and safe all the way to the hidden harbor",
    ),
}

NEEDS = {
    "wind": Need(
        id="wind",
        problem="Their paper sail drooped sadly, and the ship would not seem to move at all.",
        ask="We need wind, or this ship will stay stuck in the rug-sea.",
        solved_text="Soon a cheerful breeze fluttered the paper sail, and the ship looked ready to skim across the room.",
        tags={"wind", "sail"},
    ),
    "light": Need(
        id="light",
        problem="Under the table, Treasure Cove had gone dark as a cave, and the map's X was hard to find.",
        ask="We need light, or we will miss the treasure and bump our noses in the dark.",
        solved_text="A safe glow shone under the table, and the treasure mark on the map stopped hiding.",
        tags={"light", "cave"},
    ),
    "signal": Need(
        id="signal",
        problem="The harbor was hidden by pillows and blankets, and no one on shore could hear their pretend ship arriving.",
        ask="We need a signal, or the harbor will never know we are coming home.",
        solved_text="A bright ding-ding rang out across the room, and suddenly the harbor seemed to hear them.",
        tags={"signal", "harbor"},
    ),
}

ATTACHMENTS = {
    "fan": Attachment(
        id="fan",
        label="fan",
        phrase="the fan",
        need="wind",
        effect="a breeze",
        click="Whirr",
        qa_text="made a breeze for the sail",
        tags={"fan", "wind"},
    ),
    "lamp": Attachment(
        id="lamp",
        label="lamp",
        phrase="the lamp",
        need="light",
        effect="a safe glow",
        click="Click",
        qa_text="made a safe glow for the cave",
        tags={"lamp", "light"},
    ),
    "bell": Attachment(
        id="bell",
        label="bell",
        phrase="the bell",
        need="signal",
        effect="a harbor signal",
        click="Ding",
        qa_text="rang a harbor signal",
        tags={"bell", "signal"},
    ),
    "streamers": Attachment(
        id="streamers",
        label="paper streamers",
        phrase="the paper streamers",
        need="decor",
        effect="pretty fluttering",
        click="Flap",
        qa_text="only made decorations flutter",
        tags={"decor"},
    ),
}

VALUES = {
    "sharing": Value(
        id="sharing",
        name="sharing",
        flashback_line="One rider at a time, and the best power is shared power.",
        lesson_line="When you share strength, everyone gets to belong in the story.",
        tags={"sharing", "moral"},
    ),
    "kindness": Value(
        id="kindness",
        name="kindness",
        flashback_line="One rider at a time, and remember to notice who is waiting beside you.",
        lesson_line="Kind power notices another person's face before it notices itself.",
        tags={"kindness", "moral"},
    ),
    "patience": Value(
        id="patience",
        name="patience",
        flashback_line="One rider at a time, and strong feet can still wait for a safe turn.",
        lesson_line="Patient power is often the strongest power of all.",
        tags={"patience", "moral"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]
TRAITS = ["careful", "steady", "thoughtful", "patient", "curious", "bold"]


@dataclass
class StoryParams:
    theme: str
    need: str
    attachment: str
    value: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    trait: str
    hero_age: int = 6
    mate_age: int = 4
    relation: str = "siblings"
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
    "exercycle": [
        (
            "What is an exercycle?",
            "An exercycle is a bike that stays in one place while you pedal it. People use it to exercise their legs indoors."
        )
    ],
    "sharing": [
        (
            "Why is sharing important in a game?",
            "Sharing helps everyone get a turn and feel included. When children share, the game usually stays happier and kinder."
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means noticing how another person feels and choosing to help instead of only thinking about yourself."
        )
    ],
    "patience": [
        (
            "What is patience?",
            "Patience means waiting calmly for the right moment instead of grabbing right away. It helps people make safer and wiser choices."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a quick memory from earlier that helps a character understand what to do now. It lets the past guide the present."
        )
    ],
    "wind": [
        (
            "What makes a sail move?",
            "A sail moves when air pushes against it. Even a small breeze can make a light paper sail flutter."
        )
    ],
    "light": [
        (
            "Why do people need light in the dark?",
            "Light helps people see where they are going and what is around them. It makes dark places easier and safer to explore."
        )
    ],
    "signal": [
        (
            "What is a signal?",
            "A signal is a sound or sign that tells someone something important. Bells, lights, and flags can all be signals."
        )
    ],
    "fan": [
        (
            "What does a fan do?",
            "A fan moves air. That moving air feels like a breeze."
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp gives light so people can see. A safe lamp helps brighten a dark place without a flame."
        )
    ],
    "bell": [
        (
            "What does a bell do?",
            "A bell makes a clear ringing sound. People can use it to call attention or send a signal."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "exercycle",
    "flashback",
    "sharing",
    "kindness",
    "patience",
    "wind",
    "light",
    "signal",
    "fan",
    "lamp",
    "bell",
]


def pair_noun(hero: Entity, mate: Entity, relation: str) -> str:
    if relation == "siblings":
        if hero.type == "boy" and mate.type == "boy":
            return "two brothers"
        if hero.type == "girl" and mate.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    theme = f["theme"]
    need = f["need_cfg"]
    attachment = f["attachment_cfg"]
    value = f["value"]
    if f["outcome"] == "shared_early":
        return [
            f'Write a pirate-style story for a 3-to-5-year-old that includes the words "imaginative", "power-ful", and "exercycle", and uses a flashback to teach {value.name}.',
            f"Tell a gentle pirate tale where {hero.id} and {mate.id} need {need.id} for their pretend voyage, and a remembered warning helps them take turns before anything goes wrong.",
            f'Write a complete story where an exercycle feels like a pirate engine, but the real treasure is {value.name} and shared power.'
        ]
    return [
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "imaginative", "power-ful", and "exercycle", and uses a flashback to teach {value.name}.',
        f"Tell a story where {hero.id} tries to use the exercycle alone to make {attachment.effect}, the bike wobbles, and a calm parent turns the moment into a lesson about {value.name}.",
        f"Write a child-facing pirate tale where a pretend ship needs {need.id}, a flashback warning is ignored at first, and the ending image proves that shared power works better than showing off."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    need = f["need_cfg"]
    attachment = f["attachment_cfg"]
    value = f["value"]
    relation = f["relation"]
    pair = pair_noun(hero, mate, relation)
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {mate.id}, who turned their living room into a pirate adventure. Their {pw} also mattered because {pw} helped guide the turning point."
        ),
        (
            "What problem did the pirate game have?",
            f"Their pretend voyage was missing something important: it needed {need.id}. That missing piece is what made the exercycle seem like such a tempting pirate machine."
        ),
        (
            f"What was the flashback about?",
            f"{mate.id} remembered {pw} saying that the bike was for one rider at a time and that power should be used with {value.name}. The memory mattered because it warned them before the wobble happened."
        ),
    ]
    if f["outcome"] == "shared_early":
        qa.extend(
            [
                (
                    f"Why did {hero.id} step down from the exercycle at first?",
                    f"{hero.id} listened to {mate.id}'s remembered warning and realized the game should be shared, not grabbed. That choice changed the story before anyone got frightened."
                ),
                (
                    "How did they solve the pirate problem?",
                    f"They took turns pedaling, and the exercycle helped the {attachment.label} do its job. Because they shared the work, the mission was solved calmly and happily."
                ),
                (
                    "What moral value did the ending show?",
                    f"It showed {value.name}. The ship only felt truly alive once both children had a place in the adventure."
                ),
            ]
        )
    else:
        qa.extend(
            [
                (
                    f"What happened when {hero.id} tried to do it alone?",
                    f"{hero.id} pedaled hard to show off, and for one second the machine felt exciting. Then the exercycle wobbled, and the children stopped feeling brave because the game no longer felt safe or shared."
                ),
                (
                    f"How did {pw} help?",
                    f"{pw.capitalize()} came quickly, steadied the exercycle, and spoke in a calm voice instead of shouting. That helped turn the scary moment into a lesson about {value.name} and taking turns."
                ),
                (
                    "How did the story end?",
                    f"It ended with the children sharing the power and finishing their pretend voyage together. The final image proves the lesson because the mission works only after the power stops belonging to just one child."
                ),
            ]
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"exercycle", "flashback", f["value"].id, f["need_cfg"].id, f["attachment_cfg"].id}
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
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts={{{k: v for k, v in world.facts.items() if k not in {'hero', 'mate', 'parent', 'cycle', 'theme', 'need_cfg', 'attachment_cfg', 'value'}}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        need="wind",
        attachment="fan",
        value="sharing",
        hero="Tom",
        hero_gender="boy",
        mate="Lily",
        mate_gender="girl",
        parent="mother",
        trait="careful",
        hero_age=5,
        mate_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="storm_sailors",
        need="light",
        attachment="lamp",
        value="patience",
        hero="Max",
        hero_gender="boy",
        mate="Mia",
        mate_gender="girl",
        parent="father",
        trait="steady",
        hero_age=6,
        mate_age=4,
        relation="friends",
    ),
    StoryParams(
        theme="lantern_crew",
        need="signal",
        attachment="bell",
        value="kindness",
        hero="Ella",
        hero_gender="girl",
        mate="Nora",
        mate_gender="girl",
        parent="mother",
        trait="thoughtful",
        hero_age=7,
        mate_age=5,
        relation="siblings",
    ),
    StoryParams(
        theme="pirates",
        need="light",
        attachment="lamp",
        value="sharing",
        hero="Ben",
        hero_gender="boy",
        mate="Theo",
        mate_gender="boy",
        parent="father",
        trait="patient",
        hero_age=4,
        mate_age=6,
        relation="siblings",
    ),
    StoryParams(
        theme="storm_sailors",
        need="wind",
        attachment="fan",
        value="kindness",
        hero="Ava",
        hero_gender="girl",
        mate="Leo",
        mate_gender="boy",
        parent="mother",
        trait="curious",
        hero_age=6,
        mate_age=5,
        relation="friends",
    ),
]


ASP_RULES = r"""
supports(A, N) :- attachment(A), powers(A, N).
valid(T, N, A) :- theme(T), need(N), attachment(A), supports(A, N).

steady_now(T) :- trait(T), steady_trait(T).
init_steadiness(5) :- trait(T), steady_now(T).
init_steadiness(3) :- trait(T), not steady_now(T).

mate_older_sibling :- relation(siblings), hero_age(H), mate_age(M), M > H.
authority(S + B) :- init_steadiness(S), bonus(B).
bonus(3) :- mate_older_sibling.
bonus(0) :- not mate_older_sibling.

shared_early :- mate_older_sibling, authority(A), A >= 8.

outcome(shared_early) :- shared_early.
outcome(guided_share) :- not shared_early.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for need_id in NEEDS:
        lines.append(asp.fact("need", need_id))
    for attachment_id, attachment in ATTACHMENTS.items():
        lines.append(asp.fact("attachment", attachment_id))
        lines.append(asp.fact("powers", attachment_id, attachment.need))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait_name", trait))
    for trait in sorted(STEADY_TRAITS):
        lines.append(asp.fact("steady_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("hero_age", params.hero_age),
            asp.fact("mate_age", params.mate_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    return "shared_early" if would_share_early(params.relation, params.hero_age, params.mate_age, params.trait) else "guided_share"


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
    for s in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke-test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: pirate play, an exercycle, a flashback, and a moral about shared power."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--attachment", choices=ATTACHMENTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.need and args.attachment:
        need = NEEDS[args.need]
        attachment = ATTACHMENTS[args.attachment]
        if not supports(attachment, need):
            raise StoryError(explain_rejection(need, attachment))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.need is None or combo[1] == args.need)
        and (args.attachment is None or combo[2] == args.attachment)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, need, attachment = rng.choice(sorted(combos))
    value = args.value or rng.choice(sorted(VALUES))
    hero, hero_gender = _pick_child(rng)
    mate, mate_gender = _pick_child(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    hero_age, mate_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        need=need,
        attachment=attachment,
        value=value,
        hero=hero,
        hero_gender=hero_gender,
        mate=mate,
        mate_gender=mate_gender,
        parent=parent,
        trait=trait,
        hero_age=hero_age,
        mate_age=mate_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.need not in NEEDS:
        raise StoryError(f"(Unknown need: {params.need})")
    if params.attachment not in ATTACHMENTS:
        raise StoryError(f"(Unknown attachment: {params.attachment})")
    if params.value not in VALUES:
        raise StoryError(f"(Unknown value: {params.value})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")

    need = NEEDS[params.need]
    attachment = ATTACHMENTS[params.attachment]
    if not supports(attachment, need):
        raise StoryError(explain_rejection(need, attachment))

    world = tell(
        theme=THEMES[params.theme],
        need=need,
        attachment=attachment,
        value=VALUES[params.value],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        mate_name_value=params.mate,
        mate_gender=params.mate_gender,
        parent_type=params.parent,
        trait=params.trait,
        hero_age=params.hero_age,
        mate_age=params.mate_age,
        relation=params.relation,
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
        print(f"{len(combos)} compatible (theme, need, attachment) combos:\n")
        for theme, need, attachment in combos:
            print(f"  {theme:13} {need:8} {attachment}")
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
                f"### {p.hero} & {p.mate}: {p.need} with {p.attachment} "
                f"({p.theme}, {p.value}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
