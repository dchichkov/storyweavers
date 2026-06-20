#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dorsal_arcade_cautionary_twist_pirate_tale.py
===============================================================================

A standalone storyworld for a pirate-tale cautionary twist about a child who
wants to use an arcade machine in a dangerous way, learns a safer way, and ends
with a vivid change in the world.

The seed words are "dorsal" and "arcade". This world turns them into a small
simulated domain: a pirate ship has a tiny arcade cabinet with a glowing dorsal
emblem. A reckless choice can jam the machine and spill sparks; a calm helper can
stop the mistake or fix the mess with a sensible response.

The story style stays child-facing and pirate-tale flavored, with a clear setup,
a cautionary turn, and a twist at the end.
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
COURAGE_BASE = 5.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    title: str
    goal: str
    hideout: str
    ending: str

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
class ArcadeMachine:
    id: str
    label: str
    phrase: str
    glow: str
    panel: str
    twist: str
    risky: bool = True
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
class Hazard:
    id: str
    label: str
    near: str
    flammable: bool = False
    fragile: bool = False
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


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


def _r_spark(world: World) -> list[str]:
    out: list[str] = []
    machine = world.entities.get("machine")
    hazard = world.entities.get("hazard")
    if not machine or not hazard:
        return out
    if machine.meters["jammed"] < THRESHOLD:
        return out
    sig = ("spark",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if hazard.flammable:
        hazard.meters["sparking"] += 1
        world.get("deck").meters["danger"] += 1
        world.get("hero").memes["fear"] += 1
        out.append("__spark__")
    return out


CAUSAL_RULES = [Rule("spark", "physical", _r_spark)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def hazard_at_risk(machine: ArcadeMachine, hazard: Hazard) -> bool:
    return machine.risky and hazard.flammable


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= (2 + delay)


def tell(theme: Theme, machine: ArcadeMachine, hazard: Hazard, response: Response,
         hero_name: str = "Mara", hero_type: str = "girl",
         mate_name: str = "Finn", mate_type: str = "boy",
         parent_type: str = "mother", delay: int = 0,
         twist: str = "flip the coin", theme_flag: str = "pirate") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_type, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the captain-mom"))
    deck = world.add(Entity(id="deck", type="deck", label="the deck"))
    machine_ent = world.add(Entity(id="machine", type="machine", label=machine.label))
    hazard_ent = world.add(Entity(id="hazard", type="hazard", label=hazard.label))
    hero.memes["bold"] = COURAGE_BASE
    mate.memes["caution"] = 5.0
    world.facts["theme"] = theme
    world.facts["machine_cfg"] = machine
    world.facts["hazard_cfg"] = hazard
    world.facts["response"] = response
    world.say(
        f"On a windy afternoon aboard {theme.scene}, {hero.id} and {mate.id} turned "
        f"the deck into {theme.rig}"
    )
    world.say(
        f'"{theme.title}!" {hero.id} shouted. "Let\'s find {theme.goal}!"'
    )
    world.para()
    world.say(
        f"But {theme.hideout} was dark, and the little arcade cabinet there glowed "
        f"with a {machine.glow}."
    )
    world.say(f'{mate.id} peered at it. "We need a light," {mate.pronoun()} said.')
    world.para()
    hero.memes["temptation"] += 1
    world.say(
        f'{hero.id} grinned. "I know! That {machine.label} will make it fun." '
        f"At first the idea felt clever, like treasure tucked under a map."
    )
    if machine.id == "dorsal_arcade":
        world.say("The dorsal emblem on the cabinet flickered like a little shark fin in moonlight.")
    if delay == 0 and mate.memes["caution"] >= 5:
        world.say(
            f'"No," {mate.id} said softly. "That {machine.label} is not a toy. '
            f'We should ask {parent.label_word} for help."'
        )
        world.say(
            f'{hero.id} hesitated, looked at the dark corner again, and gave up the idea.'
        )
        world.para()
        world.say(
            f'{parent.label_word.capitalize()} came over with a lantern and showed them how '
            f'to play without touching the machine.'
        )
        world.say(
            f"In the end, the cave stayed calm, and the pirates sailed on by lantern light."
        )
        outcome = "averted"
    else:
        world.say(
            f'"Don\'t worry," {hero.id} said, and pressed the button anyway.'
        )
        machine_ent.meters["jammed"] += 1
        propagate(world, narrate=False)
        world.para()
        world.say(
            f"{machine.panel} clicked once, then sputtered. A bright spark jumped toward {hazard.near}."
        )
        world.say(
            f'"{hero.id}!" {mate.id} cried. "{parent.label_word.upper()}!"'
        )
        severity = 2 + delay
        contained = is_contained(response, hazard, delay)
        if contained:
            world.para()
            hazard_ent.meters["sparking"] = 0.0
            deck.meters["danger"] = 0.0
            world.say(
                f"{parent.label_word.capitalize()} rushed in and {response.text.replace('{target}', hazard.label)}."
            )
            world.say(
                f"The spark died with a tiny hiss, leaving only a salty smell and two wide-eyed pirates."
            )
            world.say(
                f"Then {parent.label_word.capitalize()} pointed at the cabinet and said, "
                f'"Twist: the dorsal light was only a decoration. The safe lantern was the real clue."'
            )
            world.say(
                f"{hero.id} and {mate.id} blinked, then laughed at the trick of it."
            )
            world.para()
            world.say(
                f"The next day, {parent.label_word.capitalize()} gave them a real lantern, "
                f"and the arcade stayed bright without any sparks."
            )
            outcome = "contained"
        else:
            world.para()
            world.say(
                f"{parent.label_word.capitalize()} rushed in and {response.fail.replace('{target}', hazard.label)}."
            )
            world.say(
                f"But the little spark had already leaped too far, and the deck went smoky."
            )
            world.say(
                f"The pirates escaped with their hats and hearts, yet the arcade cabinet was ruined."
            )
            world.say(
                f"After that, {hero.id} knew that a shiny trick can still hide a dangerous flame."
            )
            outcome = "burned"
    world.facts.update(
        hero=hero, mate=mate, parent=parent, deck=deck, machine=machine_ent,
        hazard=hazard_ent, outcome=outcome, delay=delay, response=response, theme=theme,
    )
    return world


THEMES = {
    "pirate_tale": Theme(
        "pirate_tale",
        "a moonlit pirate ship",
        "The deck was their island, a coil of rope became a snake trail, a tin cup became a telescope, and a chalk map showed the way to buried gold.",
        "Captain",
        "the hidden cove",
        "the shadowy hatch under the stairs",
        "The pirates sailed on with safe lanterns.",
    ),
    "storm_tale": Theme(
        "storm_tale",
        "a storm-tossed brig",
        "The deck was their brave camp, a mop became a mast, a crate became a drum, and a chalk map showed the way to the safe harbor.",
        "Matey",
        "the lantern room",
        "the dark corner by the rigging",
        "The pirates found the harbor by warm light.",
    ),
}

MACHINES = {
    "dorsal_arcade": ArcadeMachine(
        "dorsal_arcade", "arcade machine", "a little arcade cabinet", "blue-green glow",
        "front panel", "dorsal", risky=True, tags={"arcade", "dorsal"},
    ),
    "coin_game": ArcadeMachine(
        "coin_game", "coin game", "a coin game box", "golden glow",
        "front panel", "twist", risky=True, tags={"arcade"},
    ),
}

HAZARDS = {
    "powder_keg": Hazard("powder_keg", "powder keg", "the powder keg", flammable=True, tags={"fire"}),
    "curtain": Hazard("curtain", "curtain", "the curtain", flammable=True, tags={"fire"}),
}

RESPONSES = {
    "smother": Response("smother", 3, 3, "pulled the cover over the spark and smothered it at once",
                        "tried to cover the spark, but it leapt higher",
                        "pulled the cover over the spark and smothered it"),
    "douse": Response("douse", 2, 2, "snatched a bucket and doused the spark before it could spread",
                      "splashed water at it, but the spark was too quick",
                      "snatched a bucket and doused the spark"),
    "alarm": Response("alarm", 3, 4, "shouted for help and brought a grown-up with a lantern and blanket",
                      "shouted for help, but no one reached them in time",
                      "shouted for help and brought a grown-up"),
}

GIRL_NAMES = ["Mara", "Lily", "Nina", "Ada", "Tess", "Ivy"]
BOY_NAMES = ["Finn", "Oren", "Jude", "Ben", "Pip", "Theo"]
TRAITS = ["careful", "curious", "bold", "cautious", "swift"]


@dataclass
@dataclass
class StoryParams:
    theme: str
    machine: str
    hazard: str
    response: str
    hero: str
    hero_type: str
    mate: str
    mate_type: str
    parent: str
    trait: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(t, m, h) for t in THEMES for m in MACHINES for h in HAZARDS if hazard_at_risk(MACHINES[m], HAZARDS[h])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate-tale cautionary twist storyworld with an arcade machine.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--hazard", choices=HAZARDS)
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
    if args.machine and args.hazard and not hazard_at_risk(MACHINES[args.machine], HAZARDS[args.hazard]):
        raise StoryError("(No story: that arcade choice would not create a real pirate-tale hazard.)")
    combos = [c for c in valid_combos()
              if args.theme in (None, c[0]) and args.machine in (None, c[1]) and args.hazard in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, machine, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError(f"(Refusing response '{response}': too little common sense.)")
    hero = rng.choice(GIRL_NAMES + BOY_NAMES)
    hero_type = "girl" if hero in GIRL_NAMES else "boy"
    mate_pool = [n for n in (GIRL_NAMES + BOY_NAMES) if n != hero]
    mate = rng.choice(mate_pool)
    mate_type = "girl" if mate in GIRL_NAMES else "boy"
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(theme, machine, hazard, response, hero, hero_type, mate, mate_type, parent, trait, delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    theme = f["theme"]
    machine = f["machine_cfg"]
    hazard = f["hazard_cfg"]
    hero = f["hero"]
    mate = f["mate"]
    return [
        f"Write a pirate-tale story for a young child that includes the words dorsal and arcade.",
        f"Tell a cautionary twist story where {hero.id} wants to use the {machine.label} in {theme.scene}, but {mate.id} warns about the danger near {hazard.label}.",
        f"Write a short pirate adventure in which a shiny arcade clue turns out to be a trick, and the children learn a safer way to explore.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["mate"]
    parent = f["parent"]
    machine = f["machine_cfg"]
    hazard = f["hazard_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    items = [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {hero.id}, {mate.id}, and their {parent.label_word}. They are playing pirate games aboard a ship with a small arcade cabinet.",
        ),
        QAItem(
            question="Why did the danger start?",
            answer=f"The danger started when {hero.id} pressed the {machine.label} even though it was not a toy. That made a spark jump toward {hazard.label}.",
        ),
    ]
    if outcome == "averted":
        items.append(QAItem(
            question="What happened when the caution was heeded?",
            answer=f"{hero.id} stopped and the family used a lantern instead. No spark reached {hazard.label}, so the pirate game stayed safe.",
        ))
    elif outcome == "contained":
        items.append(QAItem(
            question="How was the spark stopped?",
            answer=f"{parent.label_word.capitalize()} {response.qa_text} The quick rescue kept the deck from turning smoky.",
        ))
        items.append(QAItem(
            question="What was the twist in the ending?",
            answer=f"The twist was that the dorsal glow on the machine was only a decoration, not the real light they needed. The safe lantern was the true answer.",
        ))
    else:
        items.append(QAItem(
            question="What happened at the end?",
            answer=f"The pirates escaped safely, but the deck was smoky and the arcade cabinet was ruined. The story ends as a caution that shiny tricks can hide danger.",
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["machine_cfg"].tags) | set(world.facts["hazard_cfg"].tags)
    if world.facts["outcome"] != "averted":
        tags.add("fire")
    out = []
    if "arcade" in tags:
        out.append(QAItem("What is an arcade machine?", "An arcade machine is a game cabinet with buttons and a screen. It is for playing games, not for making sparks or fire."))
    if "dorsal" in tags:
        out.append(QAItem("What does dorsal mean?", "Dorsal usually means the back side of something. In this story it names a glowing detail on the machine's back panel."))
    if "fire" in tags:
        out.append(QAItem("Why are sparks dangerous near flammable things?", "Sparks can start a fire if they land on something that burns. That is why people keep fire away from curtains, wood, and powder."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts ==", *[f"- {p}" for p in sample.prompts], "", "== story qa =="]
    for q in sample.story_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines += [f"Q: {q.question}", f"A: {q.answer}"]
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(THEMES[params.theme], MACHINES[params.machine], HAZARDS[params.hazard], RESPONSES[params.response],
                 params.hero, params.hero_type, params.mate, params.mate_type, params.parent, params.trait, params.delay)
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


ASP_RULES = r"""
hazard(F, H) :- machine(F), flammable(H).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T, F, H) :- theme(T), machine(F), hazard(H), hazard(F, H).
outcome(averted) :- cautioned.
outcome(contained) :- not cautioned, contained_fire.
outcome(burned) :- not cautioned, not contained_fire.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for m, mm in MACHINES.items():
        lines.append(asp.fact("machine", m))
        if mm.risky:
            lines.append(asp.fact("risky", m))
    for h, hh in HAZARDS.items():
        lines.append(asp.fact("hazard", h))
        if hh.flammable:
            lines.append(asp.fact("flammable", h))
    for r, rr in RESPONSES.items():
        lines.append(asp.fact("response", r))
        lines.append(asp.fact("sense", r, rr.sense))
        lines.append(asp.fact("power", r, rr.power))
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
    extra = "\n".join([
        asp.fact("cautioned", "1" if params.delay == 0 else "0"),
        asp.fact("contained_fire", "1" if is_contained(RESPONSES[params.response], HAZARDS[params.hazard], params.delay) else "0"),
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
        print("MISMATCH in valid_combos()")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    # smoke test
    try:
        sample = generate(resolve_params(argparse.Namespace(theme=None, machine=None, hazard=None, response=None, parent=None, delay=None), random.Random(777)))
        assert sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print("OK: generate() smoke test passed.")
    return rc


CURATED = [
    StoryParams("pirate_tale", "dorsal_arcade", "powder_keg", "smother", "Mara", "girl", "Finn", "boy", "mother", "careful", 0),
    StoryParams("storm_tale", "coin_game", "curtain", "douse", "Lily", "girl", "Jude", "boy", "father", "cautious", 1),
]


def explain_rejection(machine: ArcadeMachine, hazard: Hazard) -> str:
    if not hazard_at_risk(machine, hazard):
        return "(No story: that arcade machine would not create a real hazard near that object.)"
    return "(No story: invalid combination.)"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.machine and args.hazard and not hazard_at_risk(MACHINES[args.machine], HAZARDS[args.hazard]):
        raise StoryError(explain_rejection(MACHINES[args.machine], HAZARDS[args.hazard]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(Refusing response: too little common sense.)")
    combos = [c for c in valid_combos()
              if args.theme in (None, c[0]) and args.machine in (None, c[1]) and args.hazard in (None, c[2])]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, machine, hazard = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    parent = args.parent or rng.choice(["mother", "father"])
    hero = rng.choice(GIRL_NAMES + BOY_NAMES)
    mate = rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(theme, machine, hazard, response, hero, "girl" if hero in GIRL_NAMES else "boy",
                       mate, "girl" if mate in GIRL_NAMES else "boy", parent, rng.choice(TRAITS),
                       args.delay if args.delay is not None else rng.randint(0, 2))


def build_story(args: StoryParams) -> StorySample:
    return generate(args)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t, m, h in combos:
            print(f"  {t:12} {m:14} {h}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
if __name__ == "__main__":
    main()
