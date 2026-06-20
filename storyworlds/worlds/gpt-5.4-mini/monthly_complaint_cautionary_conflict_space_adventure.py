#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/monthly_complaint_cautionary_conflict_space_adventure.py
=======================================================================================

A standalone story world for a small Space Adventure tale with a cautionary
conflict: a child wants to use a noisy, risky space gadget during a monthly
station chore, another child complains and warns, an adult steps in, and the
ending proves they choose a safer cosmic way to play.

Seed words: monthly, complaint
Features: Cautionary, Conflict
Style: Space Adventure
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
CAUTIOUS_TRAITS = {"careful", "cautious", "thoughtful", "steady"}
LOUD_MIN = 2.0


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
    setup: str
    mission: str
    dark_spot: str
    role_solo: str
    role_plural: str
    send_off: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class HazardGadget:
    id: str
    label: str
    phrase: str
    noise: str
    risk: str
    makes_noise: bool = True
    makes_sparks: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class RiskTarget:
    id: str
    label: str
    phrase: str
    vulnerable: bool = True
    spread: int = 2
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def kids(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.role in {"instigator", "cautioner"}]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "station" in world.entities:
            world.get("station").meters["stress"] += 1
        for kid in world.kids():
            kid.memes["annoyed"] += 1
        out.append("__noise__")
    return out


def _r_conflict(world: World) -> list[str]:
    for kid in world.kids():
        if kid.memes["complaint"] < THRESHOLD or kid.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [Rule("noise", "physical", _r_noise), Rule("conflict", "social", _r_conflict)]


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


def caution_strength(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    if relation != "siblings" or cautioner_age <= instigator_age:
        return False
    return caution_strength(trait) + 1.0 + 4.0 > 6.0


def hazard_risk(gadget: HazardGadget, target: RiskTarget) -> bool:
    return gadget.makes_noise and target.vulnerable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def fire_severity(target: RiskTarget, delay: int) -> int:
    return target.spread + delay


def is_contained(response: Response, target: RiskTarget, delay: int) -> bool:
    return response.power >= fire_severity(target, delay)


def _do_gadget(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["noise"] += 1
    target.meters["risk"] += 1
    propagate(world, narrate=narrate)


def predict_hazard(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_gadget(sim, sim.get(target_id), narrate=False)
    return {
        "noisy": sim.get(target_id).meters["noise"] >= THRESHOLD,
        "stress": sim.get("station").meters["stress"],
    }


def setup(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright day aboard the space station, {a.id} and {b.id} turned a quiet corner into {theme.scene}. "
        f"{theme.setup}"
    )
    world.say(
        f'"{theme.mission}!" {a.id} shouted. "Let\'s explore {theme.dark_spot}!"'
    )


def need_plan(world: World, b: Entity, theme: Theme, target: RiskTarget) -> None:
    world.say(
        f"But {theme.dark_spot} was dim, and the station hummed around them like a sleepy giant. "
        f'{b.id} peered at the shadows. "We need a light," {b.pronoun()} said.'
    )


def tempt(world: World, a: Entity, gadget: HazardGadget) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'{a.id}\'s eyes lit up. "I know! {gadget.phrase} {gadget.noise} {gadget.risk}."'
    )
    world.say("For one breath, it sounded like a clever space adventure trick.")


def warn(world: World, b: Entity, a: Entity, gadget: HazardGadget, target: RiskTarget, parent: Entity) -> None:
    pred = predict_hazard(world, "target")
    b.memes["complaint"] += 1
    world.facts["predicted_stress"] = pred["stress"]
    world.say(
        f'{b.id} wrinkled {b.pronoun("possessive")} nose and made a small complaint. '
        f'"{a.id}, we are not allowed to use {gadget.label} here. {parent.label_word.capitalize()} said so. '
        f"It could make noise, and noise can bother the station."
    )
    if pred["noisy"]:
        world.say(
            f'"And {target.label} is right there," {b.id} added. "That would be a bad mix."'
        )


def defy(world: World, a: Entity, b: Entity, gadget: HazardGadget) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said, and {a.id} reached for {gadget.label} anyway.'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity, theme: Theme) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'"Don\'t be such a scaredy-cat," {a.id} said. But {b.id} was {a.pronoun("possessive")} older sibling, '
        f"so {a.id} looked at {b.pronoun('object')}, thought better of it, and gave up the idea."
    )
    world.say(
        f"They left the gadget alone and went to tell {parent.label_word.capitalize()} how dark {theme.dark_spot} had been."
    )


def ignite(world: World, target_ent: Entity, gadget: HazardGadget, target: RiskTarget) -> None:
    _do_gadget(world, target_ent)
    world.say(
        f"{gadget.noise} {gadget.label} flashed on in a bright blink. For one second it was wonderful, like a tiny star. "
        f"Then it buzzed too loudly near {target.phrase}, and the little adventure turned tense."
    )


def alarm(world: World, b: Entity, a: Entity, target: RiskTarget, parent: Entity) -> None:
    world.say(f'"{a.id}! Complaint! {target.label}!" {b.id} yelled.')
    world.say(f'"{parent.label_word.upper()}!"')


def rescue(world: World, parent: Entity, response: Response, target_ent: Entity, target: RiskTarget, theme: Theme) -> None:
    target_ent.meters["noise"] = 0.0
    world.get("station").meters["stress"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came running. In a calm voice {parent.pronoun()} {response.text.replace('{target}', target.label)}."
    )
    world.say(
        f"The commotion faded, and the corridor was quiet again, with two very startled {theme.role_plural} standing still."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, gadget: HazardGadget) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
    world.say("For a moment, nobody spoke.")
    world.say(
        f"Then {parent.label_word.capitalize()} knelt down and hugged them both. "
        f'"I am not mad that you spoke up," {parent.pronoun()} said softly. '
        f'"I am glad you complained before the noise got worse. But remember: {gadget.label} is not a toy."'
    )
    world.say(f'"We promise," whispered {b.id} and {a.id} together.')


def safe_gift(world: World, parent: Entity, a: Entity, b: Entity, theme: Theme, l1: SafeTool, l2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"The next day, {parent.label_word.capitalize()} had a surprise. {parent.pronoun().capitalize()} handed them {l1.phrase} that {l1.glow}, "
        f"and {l2.phrase} that {l2.glow}."
    )
    world.say(
        f'"Now," {parent.pronoun()} smiled, "what does {theme.role_solo} need to explore a dark place?"'
    )
    world.say(f"{a.id} held up the {l2.label}. {b.id} clicked on the {l1.label}.")
    world.say('"Safe light!" they cheered.')
    world.say(f"This time, the {theme.role_plural} {theme.send_off} -- bright, brave, and safe.")


def tell(theme: Theme, gadget: HazardGadget, target: RiskTarget, lights: tuple[SafeTool, SafeTool], response: Response,
         instigator: str = "Nova", instigator_gender: str = "girl", cautioner: str = "Milo", cautioner_gender: str = "boy",
         trait: str = "careful", parent_type: str = "mother", delay: int = 0, instigator_age: int = 6,
         cautioner_age: int = 4, relation: str = "siblings", trust: int = 7) -> World:
    world = World()
    a = world.add(Entity(id=instigator, kind="character", type=instigator_gender, role="instigator", attrs={"relation": relation}))
    b = world.add(Entity(id=cautioner, kind="character", type=cautioner_gender, role="cautioner", traits=[trait], attrs={"relation": relation}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    station = world.add(Entity(id="station", type="station", label="the station"))
    tgt = world.add(Entity(id="target", type="target", label=target.label))
    a.memes["bravado"] = 6.0
    b.memes["complaint"] = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    b.memes["trust"] = float(trust)
    world.facts["theme"] = theme
    world.facts["gadget"] = gadget
    world.facts["target_cfg"] = target
    world.facts["lights"] = lights
    world.facts["response"] = response
    world.facts["relation"] = relation

    setup(world, a, b, theme)
    need_plan(world, b, theme, target)
    world.para()
    tempt(world, a, gadget)
    warn(world, b, a, gadget, target, parent)
    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent, theme)
        world.para()
        safe_gift(world, parent, a, b, theme, *lights)
        contained = True
        severity = 0
        ignited = False
    else:
        defy(world, a, b, gadget)
        world.para()
        ignite(world, tgt, gadget, target)
        alarm(world, b, a, target, parent)
        severity = fire_severity(target, delay)
        contained = is_contained(response, target, delay)
        ignited = True
        world.para()
        if contained:
            rescue(world, parent, response, tgt, target, theme)
            lesson(world, parent, a, b, gadget)
            world.para()
            safe_gift(world, parent, a, b, theme, *lights)
        else:
            world.say(
                f"{parent.label_word.capitalize()} came running, but {response.fail.replace('{target}', target.label)}."
            )
            world.say(
                "The noise kept climbing until the corridor had to be evacuated, and the adventure ended with everyone safe outside."
            )
            for kid in (a, b):
                kid.memes["fear"] += 1
                kid.memes["lesson"] += 1
    outcome = "averted" if averted else ("contained" if contained else "evacuated")
    world.facts.update(instigator=a, cautioner=b, parent=parent, target=tgt, ignited=ignited, outcome=outcome, severity=severity, delay=delay)
    return world


THEMES = {
    "orbit": Theme("orbit", "a shining orbit corner", "They arranged paper stars and a foam moon around a crate table.", "We need to check the moon gate", "the storage nook behind the comet curtain", "an explorer", "explorers", "set off to explore the station"),
    "lunar": Theme("lunar", "a tiny lunar camp", "A sleeping bag became a moon rock bed, and a cardboard rover waited by the wall.", "Let's map the crater path", "the locker room by the airlock", "a moon scout", "moon scouts", "glided off to chart the crater"),
    "rocket": Theme("rocket", "a pretend rocket bay", "A blanket turned into a launch pad, and a box of crayons became mission controls.", "Let's open the rocket tunnel", "the dark corner behind the cargo crate", "a rocket pilot", "rocket pilots", "zoomed off to test the rocket"),
}

GADGETS = {
    "flashlamp": HazardGadget("flashlamp", "flashlamp", "a flashlamp", "beep-beep", "could startle the ship", True, False, {"light"}),
    "blaster": HazardGadget("blaster", "toy blaster", "a toy blaster", "pew-pew", "could make a loud complaint from the walls", True, False, {"noise"}),
    "sparkler": HazardGadget("sparkler", "mini spark wand", "a mini spark wand", "fizz-fizz", "could spray bright sparks", True, True, {"spark"}),
}

TARGETS = {
    "panel": RiskTarget("panel", "control panel", "the control panel", True, 3, {"panel"}),
    "airlock": RiskTarget("airlock", "airlock door", "the airlock door", True, 2, {"airlock"}),
    "comet": RiskTarget("comet", "paper comet", "the paper comet", True, 2, {"paper"}),
    "moonrock": RiskTarget("moonrock", "moon rock model", "the moon rock model", True, 2, {"rock"}),
}

SAFE_LIGHTS = {
    "lamp": SafeTool("lamp", "lamp", "a little lamp", "glowed softly", {"lamp"}),
    "glowstick": SafeTool("glowstick", "glow stick", "a glow stick", "shone green in the dark", {"glow"}),
    "headlamp": SafeTool("headlamp", "headlamp", "a headlamp", "lit up the whole nook", {"headlamp"}),
}

RESPONSES = {
    "shield": Response("shield", 3, 4, "put a shield over the source and calmed the station down", "tried to shield the source, but the noise had already spread", "put a shield over the source"),
    "mute": Response("mute", 3, 3, "switched the station to quiet mode and shut the noisy gadget off", "switched to quiet mode, but the gadget was too loud already", "switched the station to quiet mode"),
    "stow": Response("stow", 2, 2, "grabbed the gadget and stowed it in a padded box", "stowed it, but it was already too late", "grabbed the gadget and stowed it"),
    "water": Response("water", 1, 1, "splashed water on the gadget", "splashed water on it, but that did not fix the problem", "splashed water on it"),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ivy", "Zara", "Cleo"]
BOY_NAMES = ["Milo", "Kai", "Arlo", "Finn", "Leo", "Jett"]
TRAITS = ["careful", "cautious", "thoughtful", "steady", "curious"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for tid in THEMES:
        for gid, g in GADGETS.items():
            for xid, x in TARGETS.items():
                if hazard_risk(g, x):
                    combos.append((tid, gid, xid))
    return combos


@dataclass
@dataclass
class StoryParams:
    theme: str
    gadget: str
    target: str
    light1: str
    light2: str
    response: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    parent: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    cautioner_age: int = 4
    relation: str = "siblings"
    trust: int = 7
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    "light": [("What is a light?", "A light helps people see in the dark. Some lights are safe and use batteries instead of fire.")],
    "noise": [("Why can loud noise be a problem on a space station?", "Loud noise can bother people who are trying to work or sleep, so astronauts try to keep things calm.")],
    "station": [("What is a space station?", "A space station is a home in space where people live and work for a while.")],
    "airlock": [("What is an airlock door?", "An airlock door is a special door on a space station that helps keep air inside.")],
    "panel": [("What is a control panel?", "A control panel has buttons and switches that help people run machines.")],
    "glow": [("What is a glow stick?", "A glow stick makes a soft light without a flame, so it is good for dark places.")],
    "spark": [("Why are sparks risky near important equipment?", "Sparks can surprise people and may damage things, so grown-ups keep them away from machines.")],
    "shield": [("What does it mean to shield something?", "To shield something means to cover or protect it so it is safer.")],
    "mute": [("What does it mean to mute something?", "To mute something means to make it quiet or turn the sound down.")],
    "stow": [("What does stow mean?", "To stow something means to put it away carefully where it will not get in the way.")],
}
KNOWLEDGE_ORDER = ["light", "noise", "station", "airlock", "panel", "glow", "spark", "shield", "mute", "stow"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b, g, t = f["instigator"], f["cautioner"], f["gadget"], f["theme"]
    return [
        f'Write a Space Adventure story for a 3-to-5-year-old that includes the words "monthly" and "complaint".',
        f"Tell a cautionary conflict story where {a.id} wants to use {g.label} during a monthly job, but {b.id} complains and warns them.",
        f"Write a gentle spaceship story where siblings solve a noisy problem with a safer choice and end up ready for their next monthly task.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, parent, gadget, target, resp = f["instigator"], f["cautioner"], f["parent"], f["gadget"], f["target_cfg"], f["response"]
    qa = [
        QAItem("Who is the story about?", f"It is about {a.id} and {b.id}, two children on a space station, and the grown-up who helps them."),
        QAItem("What monthly job were they doing?", f"They were taking part in a monthly station chore while they explored a dark place for their pretend adventure."),
        QAItem(f"What did {a.id} want to use?", f"{a.id} wanted to use {gadget.label}, which sounded exciting but was not a good choice in that place."),
    ]
    if f.get("outcome") == "averted":
        qa.append(QAItem(f"What did {b.id} do after the warning?", f"{b.id} complained and warned {a.id}, and {a.id} backed down before anything bad happened. That stopped the conflict before it could grow."))
        qa.append(QAItem("How did the story end?", f"It ended safely with the children choosing a quiet, safe light instead of the risky gadget. The space adventure could continue without trouble."))
    elif f.get("outcome") == "contained":
        qa.append(QAItem("What happened after the risky gadget was used?", f"The gadget made too much noise near {target.label}, so the station became tense and the children called for help. {parent.label_word.capitalize()} then used {resp.qa_text.replace('{target}', target.label)}."))
        qa.append(QAItem("How did the adults help?", f"{parent.label_word.capitalize()} came running, fixed the problem, and then taught the children that {gadget.label} was not a toy. The quick help kept the station safe."))
        qa.append(QAItem("What changed at the end?", f"At the end the children were calmer and had safe lights to use for their dark-space game. They learned to ask for help before a complaint turned into a bigger problem."))
    else:
        qa.append(QAItem("Could the grown-up stop the problem quickly?", f"No. {parent.label_word.capitalize()} tried, but the noise had already spread too far and everyone had to evacuate safely."))
        qa.append(QAItem("How did the story end?", f"It ended with everyone safe outside the noisy area, but the adventure had to stop for the day. The children learned to choose safer tools next time."))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["gadget"].tags) | set(world.facts["target_cfg"].tags)
    if world.facts.get("outcome") == "contained":
        tags |= set(world.facts["response"].tags)
    for light in world.facts["lights"]:
        tags |= set(light.tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(q, a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orbit", "blaster", "panel", "lamp", "glowstick", "shield", "Nova", "girl", "Milo", "boy", "mother", "careful", 0, 6, 4, "siblings", 8),
    StoryParams("lunar", "flashlamp", "moonrock", "headlamp", "glowstick", "mute", "Kai", "boy", "Luna", "girl", "father", "thoughtful", 0, 5, 7, "siblings", 5),
    StoryParams("rocket", "sparkler", "comet", "lamp", "headlamp", "stow", "Mira", "girl", "Jett", "boy", "mother", "cautious", 1, 6, 4, "siblings", 4),
]


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < 2). Try a safer choice.)"


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], TARGETS[params.target], params.delay) else "evacuated"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        if g.makes_noise:
            lines.append(asp.fact("makes_noise", gid))
        if g.makes_sparks:
            lines.append(asp.fact("makes_sparks", gid))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        if t.vulnerable:
            lines.append(asp.fact("vulnerable", tid))
        lines.append(asp.fact("spread", tid, t.spread))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    for lid in SAFE_LIGHTS:
        lines.append(asp.fact("light", lid))
    lines.append(asp.fact("sense_min", 2))
    lines.append(asp.fact("bravery_init", 6))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(G,T) :- makes_noise(G), vulnerable(T).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,G,X) :- theme(T), gadget(G), target(X), hazard(G,X).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_sibling :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- older_sibling.
bonus(0) :- not older_sibling.
authority(A) :- init_caution(C), bonus(B), A = C + 1 + B.
averted :- older_sibling, authority(A), bravery_init(B), A > B.

severity(V) :- chosen_target(T), spread(T,S), delay(D), V = S + D.
contained :- chosen_response(R), power(R,P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(evacuated) :- not averted, not contained.
"""


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
    extra = "\n".join([
        asp.fact("chosen_target", params.target),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    cases = list(CURATED)
    for s in range(20):
        try:
            cases.append(resolve_params(argparse.Namespace(theme=None, gadget=None, target=None, response=None, parent=None, seed=None), random.Random(s)))
        except Exception:
            pass
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure cautionary conflict storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError(explain_response(args.response))
    combos = [c for c in valid_combos()
              if (args.theme is None or c[0] == args.theme)
              and (args.gadget is None or c[1] == args.gadget)
              and (args.target is None or c[2] == args.target)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, gadget, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    instigator = rng.choice(GIRL_NAMES + BOY_NAMES)
    instigator_gender = "girl" if instigator in GIRL_NAMES else "boy"
    cautioner = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != instigator])
    cautioner_gender = "girl" if cautioner in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    ia, ca = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(theme, gadget, target, light1, light2, response, instigator, instigator_gender,
                       cautioner, cautioner_gender, parent, trait, delay, ia, ca, relation, trust)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], GADGETS[params.gadget], TARGETS[params.target],
                 (SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]), RESPONSES[params.response],
                 params.instigator, params.instigator_gender, params.cautioner, params.cautioner_gender,
                 params.trait, params.parent, params.delay, params.instigator_age, params.cautioner_age,
                 params.relation, params.trust)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        for t, g, x in asp_valid_combos():
            print(f"  {t:10} {g:10} {x}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
            header = f"### {p.instigator} & {p.cautioner}: {p.gadget} near {p.target} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
