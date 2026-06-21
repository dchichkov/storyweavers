#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py
==============================================================================

A standalone story world for a superhero-style misunderstanding tale.

Premise
-------
A child in a superhero game hears a grown-up say, "The spare tyre is important."
The child misunderstands what "important" means and tries to help in a heroic
but mistaken way by moving the spare tyre. Later the family needs it, the mix-up
is explained, and the child learns to ask when words are unclear.

This world models:
- typed entities with physical meters and emotional memes
- a misunderstanding that changes the world state
- a clear turn when the missing tyre matters
- a resolution driven by explanation and return of the tyre
- a small ASP twin for reasonableness and outcome parity

Run it
------
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py --all
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py --qa --seed 7
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py --trace
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py --asp
python storyworlds/worlds/gpt-5.4/important_tyre_misunderstanding_superhero_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = False
    visible: bool = True
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class Mission:
    id: str
    destination: str
    reason: str
    vehicle: str
    flat_where: str
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
class MisreadAction:
    id: str
    verb: str
    thought: str
    move_text: str
    clue_text: str
    visible_score: int
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
class Hideout:
    id: str
    label: str
    phrase: str
    reachable: bool = True
    enclosed: bool = False
    big_enough: bool = True
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


MISSIONS = {
    "parade": Mission(
        id="parade",
        destination="the town parade",
        reason="the whole street was waiting for capes, music, and waving flags",
        vehicle="family car",
        flat_where="at the end of the driveway",
        ending_image="the car rolled off with two paper masks on the back seat and sunshine on the windscreen",
        tags={"car", "parade"},
    ),
    "picnic": Mission(
        id="picnic",
        destination="Grandma's picnic by the river",
        reason="Grandma had packed strawberry biscuits and a red blanket",
        vehicle="little blue car",
        flat_where="beside the front gate",
        ending_image="the little blue car hummed toward the river while a picnic basket bumped softly on the seat",
        tags={"car", "picnic"},
    ),
    "library": Mission(
        id="library",
        destination="the library hero day",
        reason="children were coming in costume to hear a rescue story",
        vehicle="family car",
        flat_where="by the curb",
        ending_image="the family car purred toward the library with a cape peeking out of the back window",
        tags={"car", "library"},
    ),
}

ACTIONS = {
    "guard": MisreadAction(
        id="guard",
        verb="guard",
        thought="important things should be hidden from villains",
        move_text="rolled the spare tyre away to a secret base where no villain would ever think to look",
        clue_text="a dark rubber line on the path led toward the hiding place",
        visible_score=0,
        tags={"misunderstanding", "guard"},
    ),
    "decorate": MisreadAction(
        id="decorate",
        verb="decorate",
        thought="important things should look extra heroic",
        move_text="rolled the spare tyre away and tied a tiny cape around it with bright ribbon",
        clue_text="a scrap of shiny ribbon trailed behind the tyre like a clue",
        visible_score=2,
        tags={"misunderstanding", "decorate"},
    ),
}

HIDEOUTS = {
    "porch_fort": Hideout(
        id="porch_fort",
        label="porch fort",
        phrase="behind the blanket fort on the porch",
        reachable=True,
        enclosed=False,
        big_enough=True,
        tags={"fort"},
    ),
    "shed_nook": Hideout(
        id="shed_nook",
        label="shed nook",
        phrase="in the cool nook beside the garden shed",
        reachable=True,
        enclosed=True,
        big_enough=True,
        tags={"shed"},
    ),
    "hedge_base": Hideout(
        id="hedge_base",
        label="hedge base",
        phrase="under the tall hedge by the fence",
        reachable=True,
        enclosed=False,
        big_enough=True,
        tags={"garden"},
    ),
    "toy_box": Hideout(
        id="toy_box",
        label="toy box",
        phrase="inside the toy box",
        reachable=True,
        enclosed=True,
        big_enough=False,
        tags={"toy"},
    ),
    "roof": Hideout(
        id="roof",
        label="roof",
        phrase="on the garage roof",
        reachable=False,
        enclosed=False,
        big_enough=True,
        tags={"danger"},
    ),
}

GIRL_NAMES = ["Lily", "Maya", "Ruby", "Ava", "Zoe", "Nora", "Ella", "Mina"]
BOY_NAMES = ["Max", "Leo", "Sam", "Ben", "Theo", "Eli", "Jack", "Finn"]
HELPER_TRAITS = ["sharp", "careful", "kind", "quick-eyed", "steady"]


# ---------------------------------------------------------------------------
# World and rules
# ---------------------------------------------------------------------------
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


def _r_missing_spare(world: World) -> list[str]:
    spare = world.get("spare")
    parent = world.get("Parent")
    if spare.attrs.get("location") == "vehicle_side":
        return []
    sig = ("missing_spare", spare.attrs.get("location", ""))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    parent.memes["worry"] += 1
    world.get("vehicle").meters["delay"] += 1
    return ["__missing__"]


def _r_clarified(world: World) -> list[str]:
    hero = world.get("hero")
    parent = world.get("Parent")
    if hero.memes["understands"] < THRESHOLD:
        return []
    sig = ("clarified",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["confusion"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["shame"] += 1
    parent.memes["worry"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_spare", tag="practical", apply=_r_missing_spare),
    Rule(name="clarified", tag="social", apply=_r_clarified),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def action_fits_hideout(action: MisreadAction, hideout: Hideout) -> bool:
    if not hideout.reachable:
        return False
    if not hideout.big_enough:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for mission_id in MISSIONS:
        for action_id, action in ACTIONS.items():
            for hideout_id, hideout in HIDEOUTS.items():
                if action_fits_hideout(action, hideout):
                    combos.append((mission_id, action_id, hideout_id))
    return combos


def explain_rejection(action: MisreadAction, hideout: Hideout) -> str:
    if not hideout.reachable:
        return (
            f"(No story: a child cannot reasonably move a spare tyre to {hideout.phrase}. "
            f"That hiding place is not safely reachable.)"
        )
    if not hideout.big_enough:
        return (
            f"(No story: {hideout.label} is too small for a spare tyre. "
            f"The misunderstanding must still fit the physical world.)"
        )
    return "(No story: that misunderstanding move does not fit this world.)"


def outcome_of(params: "StoryParams") -> str:
    hideout = HIDEOUTS[params.hideout]
    action = ACTIONS[params.action]
    if hideout.enclosed and action.visible_score == 0:
        return "late"
    return "quick"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_problem(world: World, new_location: str) -> dict:
    sim = world.copy()
    sim.get("spare").attrs["location"] = new_location
    propagate(sim, narrate=False)
    return {
        "missing": sim.get("Parent").memes["worry"] >= THRESHOLD,
        "delay": sim.get("vehicle").meters["delay"],
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} tied on a towel cape and became Star Sprint, defender of front yards everywhere. "
        f"{helper.id} was the sidekick for the morning mission."
    )
    world.say(
        f"They were getting ready to ride in the {mission.vehicle} to {mission.destination}, "
        f"and {mission.reason}."
    )


def setup_vehicle(world: World, parent: Entity) -> None:
    world.say(
        f"By the car, {parent.label_word} checked the boot, the snacks, and the shiny spare tyre."
    )


def important_line(world: World, parent: Entity) -> None:
    world.say(
        f'"This spare tyre is important," {parent.label_word} said. '
        f'"Leave it right here by the car."'
    )


def misunderstand(world: World, hero: Entity, action: MisreadAction, hideout: Hideout) -> None:
    hero.memes["confusion"] += 1
    hero.memes["heroic"] += 1
    world.facts["predicted_problem"] = predict_problem(world, hideout.id)
    world.say(
        f"But {hero.id} heard that in superhero language. "
        f"{hero.pronoun().capitalize()} decided that {action.thought}."
    )
    world.say(
        f"While the grown-ups packed juice and napkins, {hero.id} {action.move_text}, {hideout.phrase}."
    )
    world.get("spare").attrs["location"] = hideout.id


def helper_reacts(world: World, helper: Entity, hero: Entity, action: MisreadAction) -> None:
    helper.memes["curiosity"] += 1
    line = (
        f'{helper.id} blinked. "Is that part of the mission?"'
        if action.id == "decorate"
        else f'{helper.id} noticed {hero.id} straining and whispered, "Why are you taking the tyre away?"'
    )
    world.say(line)


def trouble(world: World, parent: Entity, mission: Mission) -> None:
    vehicle = world.get("vehicle")
    vehicle.meters["flat"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Just then, {parent.label_word} crouched beside the car and found a soft, sleepy wheel {mission.flat_where}."
    )
    world.say(
        f'"Oh dear," {parent.label_word} said. "We need the spare tyre now."'
    )


def search(world: World, parent: Entity, action: MisreadAction) -> None:
    spare = world.get("spare")
    location = spare.attrs.get("location", "")
    if location == "vehicle_side":
        return
    if world.get("vehicle").meters["delay"] >= THRESHOLD:
        world.say(
            f"{parent.label_word.capitalize()} looked around the driveway, then under the bench, growing quieter and more worried."
        )
    if action.id == "decorate":
        world.say(f"Then {parent.pronoun('subject')} spotted {action.clue_text}.")
    else:
        world.say(f"Then {parent.pronoun('subject')} noticed {action.clue_text}.")


def explain(world: World, helper: Entity, hero: Entity, parent: Entity, mission: Mission) -> None:
    helper.memes["helpfulness"] += 1
    hero.memes["understands"] += 1
    world.say(
        f'{helper.id} tugged {hero.id}\'s cape. "I think {parent.label_word} meant important for the car," '
        f'{helper.pronoun()} said. "Not important like secret treasure."'
    )
    world.say(
        f"{hero.id} looked from the flat wheel to the empty spot by the car and understood all at once."
    )
    propagate(world, narrate=False)


def return_tyre(world: World, hero: Entity, hideout: Hideout, parent: Entity) -> None:
    spare = world.get("spare")
    spare.attrs["location"] = "vehicle_side"
    spare.visible = True
    hero.meters["carried"] += 1
    world.say(
        f'"I was trying to help," {hero.id} said, and hurried to fetch the tyre from {hideout.phrase}.'
    )
    world.say(
        f"{hero.pronoun().capitalize()} rolled it back with both hands, cheeks hot under the mask."
    )


def repair_and_lesson(world: World, parent: Entity, hero: Entity, mission: Mission) -> None:
    world.get("vehicle").meters["ready"] += 1
    world.say(
        f"{parent.label_word.capitalize()} fitted the spare tyre and tightened the nuts until the wheel sat straight and strong."
    )
    world.say(
        f'Then {parent.pronoun()} knelt beside {hero.id}. "You have a kind heart," {parent.pronoun()} said softly. '
        f'"Next time, if a word sounds important but puzzling, ask me what I mean."'
    )
    hero.memes["lesson"] += 1
    hero.memes["love"] += 1


def ending(world: World, hero: Entity, helper: Entity, mission: Mission, outcome: str) -> None:
    if outcome == "late":
        world.say(
            f"They reached {mission.destination} a little late, but still in time for the best part."
        )
    else:
        world.say(
            f"They still reached {mission.destination} right on time."
        )
    world.say(
        f"{hero.id} made a new superhero promise: before making a rescue plan, {hero.pronoun()} would ask one clear question first."
    )
    world.say(
        f"Soon {mission.ending_image}, and the sidekicks decided that asking carefully could be a superpower too."
    )
def tell(
    action: Action,
    hideout: Hideout,
    hero_name: str,
    hero_gender: str,
    helper_name: str,
    helper_gender: str,
    parent_type: ParentType,
    helper_trait: HelperTrait,
    mission=None,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper", traits=[helper_trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    vehicle = world.add(Entity(id="vehicle", kind="thing", type="car", label=mission.vehicle))
    spare = world.add(
        Entity(
            id="spare",
            kind="thing",
            type="spare_tyre",
            label="spare tyre",
            movable=True,
            visible=True,
            attrs={"location": "vehicle_side"},
        )
    )

    world.facts.update(
        mission=mission,
        action=action,
        hideout=hideout,
        hero=hero,
        helper=helper,
        parent=parent,
        vehicle=vehicle,
        spare=spare,
        predicted_problem={"missing": False, "delay": 0},
    )

    introduce(world, hero, helper, mission)
    setup_vehicle(world, parent)
    important_line(world, parent)

    world.para()
    misunderstand(world, hero, action, hideout)
    helper_reacts(world, helper, hero, action)

    world.para()
    trouble(world, parent, mission)
    search(world, parent, action)
    explain(world, helper, hero, parent, mission)
    return_tyre(world, hero, hideout, parent)

    world.para()
    repair_and_lesson(world, parent, hero, mission)
    out = outcome_of(
        StoryParams(
            mission=mission.id,
            action=action.id,
            hideout=hideout.id,
            hero_name=hero_name,
            hero_gender=hero_gender,
            helper_name=helper_name,
            helper_gender=helper_gender,
            parent=parent_type,
            helper_trait=helper_trait,
        )
    )
    ending(world, hero, helper, mission, out)

    world.facts.update(
        outcome=out,
        clarified=hero.memes["understands"] >= THRESHOLD,
        returned=spare.attrs.get("location") == "vehicle_side",
        lesson=hero.memes["lesson"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
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
    "tyre": [
        (
            "What is a tyre?",
            "A tyre is the thick rubber ring around a wheel. It helps a car roll smoothly and safely on the road.",
        )
    ],
    "spare": [
        (
            "What is a spare tyre for?",
            "A spare tyre is an extra tyre kept in case one wheel goes flat. It helps a grown-up get the car moving again.",
        )
    ],
    "flat": [
        (
            "What is a flat tyre?",
            "A flat tyre is a tyre that has lost its air, so it turns soft and squishy. A car should not be driven far on it.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. Asking a question can help fix it.",
        )
    ],
    "ask": [
        (
            "Why is it good to ask what someone means?",
            "It helps you understand the real message instead of guessing. That can stop mix-ups before they grow into problems.",
        )
    ],
    "hero": [
        (
            "Can asking for help be brave?",
            "Yes. Brave people do not have to guess alone; they can ask questions and listen carefully when something matters.",
        )
    ],
}

KNOWLEDGE_ORDER = ["tyre", "spare", "flat", "misunderstanding", "ask", "hero"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    action = f["action"]
    hero = f["hero"]
    return [
        'Write a short Superhero Story for a 3-to-5-year-old that includes the words "important" and "tyre" and turns on a misunderstanding.',
        f"Tell a gentle superhero tale where {hero.label} hears that a spare tyre is important and misunderstands what that means.",
        f"Write a story in which a child tries to help like a hero by choosing to {action.verb} something important, but learns to ask questions before acting.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    mission: Mission = f["mission"]
    action: MisreadAction = f["action"]
    hideout: Hideout = f["hideout"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    parent: Entity = f["parent"]
    predicted = f["predicted_problem"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a child playing superhero, {helper.label}, the sidekick, and {hero.pronoun('possessive')} {parent.label_word}. They were getting ready to go to {mission.destination}.",
        ),
        (
            "What was the misunderstanding?",
            f"{hero.label} heard that the spare tyre was important, but thought that meant it needed a secret superhero rescue. {hero.pronoun().capitalize()} did not understand that it was important because the car might need it.",
        ),
        (
            f"Why did moving the tyre cause a problem?",
            f"It caused a problem because the car soon had a soft wheel and the family needed the spare tyre right away. Since {hero.label} had moved it to {hideout.phrase}, {parent.label_word} could not use it at first.",
        ),
    ]
    if predicted.get("missing"):
        qa.append(
            (
                "Could the problem have been predicted?",
                f"Yes. In the world of the story, moving the tyre away meant the grown-up would worry and the trip could be delayed. The misunderstanding looked helpful to {hero.label}, but it was already creating trouble.",
            )
        )
    if f.get("clarified"):
        qa.append(
            (
                f"How was the misunderstanding fixed?",
                f"{helper.label} explained that 'important' meant important for the car, not secret treasure. Then {hero.label} understood, brought the tyre back, and the grown-up could use it.",
            )
        )
    if f.get("lesson"):
        qa.append(
            (
                f"What did {hero.label} learn?",
                f"{hero.label} learned that asking one clear question can be better than guessing. That lesson mattered because {hero.pronoun()} had wanted to help, but misunderstood the word instead.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tyre", "spare", "flat", "misunderstanding", "ask", "hero"}
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.movable:
            bits.append("movable=True")
        if not ent.visible:
            bits.append("visible=False")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    mission: str
    action: str
    hideout: str
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_gender: str
    parent: str
    helper_trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        mission="parade",
        action="guard",
        hideout="shed_nook",
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Max",
        helper_gender="boy",
        parent="mother",
        helper_trait="sharp",
    ),
    StoryParams(
        mission="picnic",
        action="decorate",
        hideout="porch_fort",
        hero_name="Leo",
        hero_gender="boy",
        helper_name="Maya",
        helper_gender="girl",
        parent="father",
        helper_trait="kind",
    ),
    StoryParams(
        mission="library",
        action="guard",
        hideout="hedge_base",
        hero_name="Ava",
        hero_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="mother",
        helper_trait="quick-eyed",
    ),
    StoryParams(
        mission="parade",
        action="decorate",
        hideout="porch_fort",
        hero_name="Finn",
        hero_gender="boy",
        helper_name="Zoe",
        helper_gender="girl",
        parent="father",
        helper_trait="steady",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(M,A,H) :- mission(M), action(A), hideout(H), reachable(H), big_enough(H).

late :- chosen_action(guard), chosen_hideout(H), enclosed(H).
quick :- not late.

outcome(late) :- late.
outcome(quick) :- quick.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for hid, h in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if h.reachable:
            lines.append(asp.fact("reachable", hid))
        if h.big_enough:
            lines.append(asp.fact("big_enough", hid))
        if h.enclosed:
            lines.append(asp.fact("enclosed", hid))
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
            asp.fact("chosen_action", params.action),
            asp.fact("chosen_hideout", params.hideout),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero-style misunderstanding story about an important spare tyre."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.action and args.hideout:
        action = ACTIONS[args.action]
        hideout = HIDEOUTS[args.hideout]
        if not action_fits_hideout(action, hideout):
            raise StoryError(explain_rejection(action, hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.mission is None or combo[0] == args.mission)
        and (args.action is None or combo[1] == args.action)
        and (args.hideout is None or combo[2] == args.hideout)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission_id, action_id, hideout_id = rng.choice(sorted(combos))
    hero_gender = rng.choice(["girl", "boy"])
    helper_gender = "boy" if hero_gender == "girl" else "girl" if rng.random() < 0.6 else hero_gender
    hero_name = pick_name(rng, hero_gender)
    helper_name = pick_name(rng, helper_gender, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    helper_trait = rng.choice(HELPER_TRAITS)
    return StoryParams(
        mission=mission_id,
        action=action_id,
        hideout=hideout_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
        helper_trait=helper_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.action not in ACTIONS:
        raise StoryError(f"(Unknown action: {params.action})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.hero_gender not in {"girl", "boy"} or params.helper_gender not in {"girl", "boy"}:
        raise StoryError("(Gender must be 'girl' or 'boy'.)")

    mission = MISSIONS[params.mission]
    action = ACTIONS[params.action]
    hideout = HIDEOUTS[params.hideout]
    if not action_fits_hideout(action, hideout):
        raise StoryError(explain_rejection(action, hideout))

    world = tell(
        mission=mission,
        action=action,
        hideout=hideout,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        helper_trait=params.helper_trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("hero", world.facts["hero"].label).replace("helper", world.facts["helper"].label),
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
        print(f"{len(combos)} compatible (mission, action, hideout) combos:\n")
        for mission, action, hideout in combos:
            print(f"  {mission:8} {action:9} {hideout}")
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
            header = f"### {p.hero_name}: {p.action} the tyre for {p.mission} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
