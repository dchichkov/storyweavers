#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/enthuse_bad_ending_moral_value_sound_effects.py
===============================================================================

A standalone storyworld for a tiny pirate-tale domain with a moral lesson,
sound effects, and a deliberately bad ending branch when the wrong choice is
made too long. The core seed is a short pirate-style tale about children who are
enthused by a lantern, a warning about theft and fire, and a consequence that
teaches a moral value.

This world generates small, state-driven stories rather than frozen templates:
- typed entities with meters and memes
- a causal rule engine
- a reasonableness gate
- an ASP twin for parity checks
- grounded QA from simulated world state

The story world centers on a young pirate play-crew, a forbidden lantern, a
safe lamp substitute, and a bad ending where the ship's sail gets singed when
nobody listens in time. The moral value is simple: don't take what isn't yours,
and do not play with fire.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/enthuse_bad_ending_moral_value_sound_effects.py
    python storyworlds/worlds/gpt-5.4-mini/enthuse_bad_ending_moral_value_sound_effects.py --all
    python storyworlds/worlds/gpt-5.4-mini/enthuse_bad_ending_moral_value_sound_effects.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/enthuse_bad_ending_moral_value_sound_effects.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    flammable: bool = False
    makes_flame: bool = False
    safe_light: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
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
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    captain: str
    mate: str
    goal: str
    hideout: str
    role_solo: str
    role_plural: str
    send_off: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Forbidden:
    id: str
    label: str
    phrase: str
    where: str
    sound: str
    not_toy: str
    makes_flame: bool = True
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Target:
    id: str
    label: str
    the: str
    near: str
    drape: str
    flammable: bool = True
    spread: int = 2
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[:1].upper() + self.the[1:]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SafeLight:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["burning"] < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "ship" in world.entities:
            world.get("ship").meters["danger"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["fear"] += 1
        out.append("__fire__")
    return out


CAUSAL_RULES = [Rule("spread", "physical", _r_spread)]


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


def hazard_at_risk(forbidden: Forbidden, target: Target) -> bool:
    return forbidden.makes_flame and target.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fire_severity(target: Target, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: Target, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def would_avert(relation: str, warning_strength: int) -> bool:
    return relation == "siblings" and warning_strength >= 7


def _do_forbidden(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["burning"] += 1
    target.meters["scorched"] += 1
    propagate(world, narrate=narrate)


def predict_fire(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_forbidden(sim, sim.get(target_id), narrate=False)
    return {
        "ignites": sim.get(target_id).meters["burning"] >= THRESHOLD,
        "danger": sim.get("ship").meters["danger"],
    }


def play_setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} turned the deck into {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.captain} {a.id} and {theme.mate} {b.id}!" {a.id} shouted. '
        f'"Let\'s find {theme.goal}!"'
    )


def need_light(world: World, target: Target, theme: Theme, b: Entity) -> None:
    world.say(
        f"But {theme.hideout} was dark -- {target.drape} made the shadows hang low."
    )
    world.say(f'"We need a light," {b.id} said, peering in.')


def tempt(world: World, a: Entity, forbidden: Forbidden) -> None:
    a.memes["enthuse"] += 1
    world.say(
        f'{a.id} was so enthused that {a.pronoun("subject")} nearly bounced in place. '
        f'"I know! {forbidden.label}!" {a.id} cried. '
        f'"{forbidden.sound} will light the way!"'
    )
    world.say("The idea felt shiny and exciting for one breath.")


def warn(world: World, b: Entity, a: Entity, forbidden: Forbidden, target: Target, parent: Entity) -> None:
    pred = predict_fire(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.say(
        f'{b.id} bit {b.pronoun("possessive")} lip. "{a.id}, we\'re not allowed '
        f'to touch {forbidden.label}. {parent.label_word.capitalize()} said it was not a toy, '
        f'and a spark can reach {target.the}."'
    )


def back_down(world: World, a: Entity, b: Entity, forbidden: Forbidden, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"{a.id}," {b.id} said gently, "we should leave {forbidden.label} alone." '
        f'{a.id} looked at {b.id}, thought better of it, and put the idea aside.'
    )
    world.say(
        f'They went to tell {parent.label_word.capitalize()} about the dark hideout instead.'
    )


def defy(world: World, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    a.memes["defiance"] += 1
    world.say(f'"Don\'t be such a scaredy-cat," {a.id} said, and reached for {forbidden.label}.')
    world.say(f'The deck went {forbidden.sound.lower()} as the dangerous little light flared.')


def ignite(world: World, target_ent: Entity, forbidden: Forbidden, target: Target) -> None:
    _do_forbidden(world, target_ent)
    world.say(
        f'{forbidden.sound} {forbidden.label} flashed for a second. Then it leaned, touched {target.near}, '
        f'and a tiny orange line began to creep.'
    )


def alarm(world: World, b: Entity, a: Entity, target: Target, parent: Entity) -> None:
    world.say(f'"{a.id}! Fire! {target.The}!" {b.id} screamed.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    target_ent.meters["burning"] = 0.0
    world.get("ship").meters["danger"] = 0.0
    body = response.text.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came running and {body}.")
    world.say("The flame hissed out, leaving only smoke and frightened faces.")


def lesson(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and said, "
        f'"I am glad you called for help. But remember: {forbidden.not_toy}. '
        f'Things can be replaced, but safety cannot."'
    )
    world.say(f'"We promise," whispered {b.id} and {a.id} together.')


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, l1: SafeLight, l2: SafeLight) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} had a surprise: "
        f"{l1.phrase} that {l1.glow}, and {l2.phrase} that {l2.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does {theme.role_solo} need to explore a dark {theme.goal}?"'
    )
    world.say(f'{a.id} held up the {l2.label}. {b.id} clicked on the {l1.label}.')
    world.say('"Safe light!" they cheered.')
    world.say(f'This time the {theme.role_plural} {theme.send_off} -- bright, brave, and safe.')


def rescue_fail(world: World, parent: Entity, response: Response, target_ent: Entity, target: Target) -> None:
    if "ship" in world.entities:
        world.get("ship").meters["burning"] += 1
    target_ent.meters["burning"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{target}", target.label)
    world.say(f"{parent.label_word.capitalize()} came running, but {body}.")
    world.say("The fire leapt to the sail and snapped along the rope.")


def escape_and_loss(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"{parent.label_word.capitalize()} grabbed both children and rushed them off the deck. "
        f'From the shore they watched the ship glow orange in the dark.'
    )
    world.say("By the time the last crackle went quiet, the sail was ruined.")
    world.say("The game ended with smoke, tears, and a lesson none of them forgot.")


def moral_value(world: World, parent: Entity, a: Entity, b: Entity, forbidden: Forbidden) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} hugged them tight and said, '
        f'"{forbidden.not_toy}. We do not take what is not ours, and we do not play with fire."'
    )
    world.say(
        "After that, the children kept their hands to themselves and remembered the rule."
    )


def tell(theme: Theme, forbidden: Forbidden, target: Target, lights: tuple[SafeLight, SafeLight],
         response: Response, instigator: str = "Finn", cautioner: str = "Mira",
         parent_type: str = "mother", delay: int = 0, relation: str = "siblings",
         warning_strength: int = 5) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type="boy", role="instigator"))
    b = world.add(Entity(id=cautioner, kind="character", type="girl", role="cautioner"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="ship", type="ship", label="the ship"))
    tgt = world.add(Entity(id="target", type="target", label=target.label, flammable=target.flammable))
    a.memes["enthuse"] = 1.0
    b.memes["caution"] = 1.0
    world.facts["relation"] = relation

    play_setup(world, a, b, theme)
    need_light(world, target, theme, b)
    world.para()
    tempt(world, a, forbidden)
    warn(world, b, a, forbidden, target, parent)

    averted = would_avert(relation, warning_strength)
    contained = True
    severity = 0
    if averted:
        back_down(world, a, b, forbidden, parent)
        world.para()
        safe_gift(world, parent, a, b, theme, lights[0], lights[1])
        outcome = "averted"
    else:
        defy(world, a, b, forbidden)
        world.para()
        ignite(world, tgt, forbidden, target)
        alarm(world, b, a, target, parent)
        severity = fire_severity(target, delay)
        tgt.meters["severity"] = float(severity)
        contained = is_contained(response, target, delay)
        world.para()
        if contained:
            rescue(world, parent, response, tgt, target)
            lesson(world, parent, a, b, forbidden)
            world.para()
            safe_gift(world, parent, a, b, theme, lights[0], lights[1])
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, tgt, target)
            escape_and_loss(world, parent, a, b)
            moral_value(world, parent, a, b, forbidden)
            outcome = "burned"

    world.facts.update(
        instigator=a, cautioner=b, parent=parent, theme=theme, forbidden=forbidden,
        target_cfg=target, target=tgt, lights=lights, response=response,
        outcome=outcome, rescued=contained, severity=severity, delay=delay,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme("pirates", "a busy pirate deck", "The sofa became a ship's rail, a broom became a mast, and an old hat held the treasure map.", "Captain", "Mate", "the hidden cove", "the captain's cabin", "a pirate", "pirates", "sailed out to sea"),
    "buccaneers": Theme("buccaneers", "a moonlit quarterdeck", "The barrels were stacked like towers, a rope became a ladder, and a wooden spoon pointed to the gold.", "Captain", "Scout", "the secret cave", "the shadowy hold", "a buccaneer", "buccaneers", "set sail into the night"),
}

FORBIDDEN = {
    "lantern": Forbidden("lantern", "the lantern", "a brass lantern", "on the chart table", "Fssst!", "lanterns are not toys", True, False, {"fire", "light"}),
    "matchbox": Forbidden("matchbox", "the matchbox", "a little box of matches", "in the galley drawer", "Scratch!", "matches are not toys", True, False, {"fire", "light"}),
}

TARGETS = {
    "sail": Target("sail", "sail", "the sail", "the canvas edge", "hung with a big white sail", True, 3, {"cloth", "ship"}),
    "rope": Target("rope", "rope", "the rope", "the frayed rope", "looped around the mast", True, 2, {"rope", "ship"}),
    "flag": Target("flag", "flag", "the flag", "the red flag", "fluttering by the rail", True, 2, {"cloth", "ship"}),
}

SAFE_LIGHTS = {
    "lamp": SafeLight("lamp", "lamp", "a small cabin lamp", "glowed warm and steady", {"light"}),
    "torchlight": SafeLight("torchlight", "torchlight", "a battery torchlight", "shone bright and safe", {"light"}),
}

RESPONSES = {
    "extinguisher": Response("extinguisher", 3, 4, "grabbed the fire extinguisher and sprayed until the sparks were gone", "was too late to stop the flames", "put the flames out with the fire extinguisher", {"fire"}),
    "smother": Response("smother", 3, 3, "pulled the {target} down and smothered the flames under a heavy blanket", "could not smother the fire fast enough", "pulled the {target} down and smothered the flames", {"fire"}),
    "stomp": Response("stomp", 2, 2, "stamped the flames hard until they went out", "stamped at the flames, but they only leapt higher", "stamped the flames out", {"fire"}),
    "water_bucket": Response("water_bucket", 1, 1, "threw a bucket of water over the {target}", "threw water, but it was not enough", "threw a bucket of water over the {target}", {"fire"}),
}

GIRL_NAMES = ["Mira", "Nina", "Lia", "Nora", "Zoe", "Ava"]
BOY_NAMES = ["Finn", "Owen", "Leo", "Max", "Toby", "Eli"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    forbidden: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    cautioner: str
    parent: str
    relation: str = "siblings"
    warning_strength: int = 5
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


KNOWLEDGE = {
    "fire": [("Why is fire dangerous?", "Fire is dangerous because it is hot and can spread fast. It can burn cloth, wood, and skin.")],
    "lantern": [("What is a lantern?", "A lantern is a light that can be carried around. It can be safe only when it is used the right way.")],
    "matches": [("What are matches?", "Matches are tiny sticks that make fire when they are struck. They are not toys.")],
    "moral": [("What is a moral lesson?", "A moral lesson is the important thing a story teaches about how to act.")],
    "safe_light": [("Why are battery lights safer than flames?", "Battery lights give light without a flame, so they are safer around cloth and wood.")],
    "ship": [("What is a ship's sail for?", "A sail catches the wind and helps a ship move across the water.")],
}
KNOWLEDGE_ORDER = ["matches", "lantern", "fire", "safe_light", "ship", "moral"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in THEMES:
        for f_id, f in FORBIDDEN.items():
            for tg_id, tg in TARGETS.items():
                if hazard_at_risk(f, tg):
                    combos.append((t, f_id, tg_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    th, fb, tg, resp = f["theme"], f["forbidden"], f["target_cfg"], f["response"]
    if f["outcome"] == "burned":
        return [
            f'Write a pirate tale for a little child that includes the word "enthuse" and shows a bad ending after someone uses {fb.label} near {tg.the}.',
            f"Tell a moral story where {f['instigator'].id} is enthused by {fb.label}, ignores a warning, and the ship is damaged by fire.",
            f'Write a short pirate story with sound effects like "{fb.sound}" and a clear lesson about not touching {fb.label}.',
        ]
    return [
        f'Write a pirate tale for a little child that includes the word "enthuse" and ends with safe light instead of {fb.label}.',
        f"Tell a moral story where {f['instigator'].id} is enthused by {fb.label}, but listens and the danger is avoided.",
        f'Write a short pirate story with sound effects like "{fb.sound}" and a clear lesson about not touching {fb.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a, b, parent = f["instigator"], f["cautioner"], f["parent"]
    fb, tg, resp = f["forbidden"], f["target_cfg"], f["response"]
    qa = [
        ("What kind of story is this?",
         f"It is a pirate tale about {a.id} and {b.id} on {f['theme'].scene}. It uses a moral lesson and sound effects to keep the scene lively."),
        ("What did {0} want to use?".format(a.id),
         f"{a.id} wanted to use {fb.label} for light, even though {fb.not_toy} and it was not safe near {tg.the}."),
        ("What sound effect was important?",
         f'The story used "{fb.sound}" when the dangerous light appeared. That sound marks the moment when the choice became risky.'),
    ]
    if f["outcome"] == "burned":
        qa.append((
            "How did the story end?",
            f"It ended badly: the fire reached the sail and the ship was damaged. The children got out safely, but they lost the game and learned a hard lesson."
        ))
        qa.append((
            f"What moral value did {parent.label_word} teach?",
            f"{parent.label_word.capitalize()} taught that {fb.not_toy} and that taking what is not yours is wrong. The lesson also said that fire is not a toy."
        ))
    elif f["outcome"] == "contained":
        body = resp.qa_text.replace("{target}", tg.label)
        qa.append((
            f"How was the fire stopped?",
            f"{parent.label_word.capitalize()} came running and {body}. That stopped the fire before it ruined the whole ship."
        ))
        qa.append((
            f"What did the children learn?",
            f"They learned that {fb.not_toy} and that it is better to ask a grown-up. They kept the game going with safe light instead."
        ))
    else:
        qa.append((
            "What happened after the warning?",
            f"{a.id} listened, left {fb.label} alone, and the children used safe light. No fire started, and the ship stayed calm."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["forbidden"].tags) | set(world.facts["target_cfg"].tags)
    if world.facts["outcome"] != "averted":
        tags |= {"fire", "moral"}
    else:
        tags |= {"safe_light", "moral"}
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
        if e.flammable:
            bits.append("flammable")
        if e.safe_light:
            bits.append("safe_light")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("pirates", "lantern", "sail", "lamp", "torchlight", "extinguisher", "Finn", "Mira", "mother", "siblings", 5, 0),
    StoryParams("buccaneers", "matchbox", "flag", "torchlight", "lamp", "stomp", "Leo", "Nora", "father", "siblings", 3, 1),
]


def explain_rejection(forbidden: Forbidden, target: Target) -> str:
    if not target.flammable:
        return f"(No story: {target.the} will not catch fire, so there is no real hazard to tell.)"
    return "(No story: this combination has no fire hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}). Try: {better}.)"


ASP_RULES = r"""
hazard(F, T) :- makes_flame(F), flammable(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Theme, F, T) :- theme(Theme), forbidden(F), target(T), hazard(F, T).
severity(T, D, V) :- target(T), spread(T, S), delay(D), V = S + D.
contained(R, T, D) :- response(R), severity(T, D, V), power(R, P), P >= V.
outcome(averted) :- relation(siblings), warning_strength(W), W >= 7.
outcome(contained) :- not outcome(averted), chosen_response(R), chosen_target(T), delay(D), contained(R, T, D).
outcome(burned) :- not outcome(averted), chosen_response(R), chosen_target(T), delay(D), not contained(R, T, D).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for fid, f in FORBIDDEN.items():
        lines.append(asp.fact("forbidden", fid))
        if f.makes_flame:
            lines.append(asp.fact("makes_flame", fid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.flammable:
            lines.append(asp.fact("flammable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("warning_strength", params.warning_strength),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in the gate.")
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    else:
        print("OK: sensible responses match.")
    cases = list(CURATED)
    for s in range(10):
        try:
            cases.append(resolve_params(build_parser().parse_args([]), random.Random(s)))
        except StoryError:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    else:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.warning_strength):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "burned"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale world: enthuse, moral value, sound effects, and a bad ending.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--forbidden", choices=FORBIDDEN)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.forbidden and args.target:
        if not hazard_at_risk(FORBIDDEN[args.forbidden], TARGETS[args.target]):
            raise StoryError(explain_rejection(FORBIDDEN[args.forbidden], TARGETS[args.target]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.forbidden is None or c[1] == args.forbidden)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, forbidden, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    l1, l2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator = rng.choice(BOY_NAMES)
    cautioner = rng.choice([n for n in GIRL_NAMES if n != instigator])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    warning_strength = rng.randint(4, 9)
    return StoryParams(theme, forbidden, target, l1, l2, response, instigator, cautioner, parent, relation, warning_strength, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], FORBIDDEN[params.forbidden], TARGETS[params.target],
                 (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]), RESPONSES[params.response],
                 params.instigator, params.cautioner, params.parent, params.delay, params.relation, params.warning_strength)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t, f, tg in asp_valid_combos():
            print(f"{t:10} {f:12} {tg}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
            header = f"### {p.instigator} & {p.cautioner}: {p.forbidden} near {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
