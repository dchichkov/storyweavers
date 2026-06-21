#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py
===========================================================================

A standalone story world for a cautionary superhero-style tale: two children
build a secret hero base, find an ancient handbook, and are tempted to read an
old emergency code into real signal gear. The world prefers sensible adult
responses, can produce a near-miss or a contained scare, and includes an ASP
twin for its reasonableness gate and ending model.

Run it
------
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py --base fort_hq --device siren_box
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py --device paper_badge
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/base_read_ancient_cautionary_superhero_story.py --verify
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
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "sensible"}


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
    powered: bool = False
    loud: bool = False
    fragile: bool = False
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
class BaseSetting:
    id: str
    scene: str
    build_line: str
    dark_corner: str
    ending_line: str
    echo: int
    fragile: bool = True
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
class AncientBook:
    id: str
    label: str
    phrase: str
    cover_line: str
    code_name: str
    warning: str
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
class Device:
    id: str
    label: str
    phrase: str
    activate_text: str
    consequence: str
    volume: int
    powered: bool = True
    loud: bool = True
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
class SafeTool:
    id: str
    label: str
    phrase: str
    use_line: str
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_noise(world: World) -> list[str]:
    out: list[str] = []
    device = world.entities.get("device")
    if device is None or device.meters["blaring"] < THRESHOLD:
        return out
    sig = ("noise", "device")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["noise"] += 1
    world.get("base").meters["shake"] += float(world.facts["echo"])
    for kid in world.kids():
        kid.memes["fear"] += 1
    if world.facts.get("pet"):
        world.get("pet").memes["alarm"] += 1
    out.append("__noise__")
    return out


def _r_collapse(world: World) -> list[str]:
    base = world.entities.get("base")
    if base is None or not base.fragile or base.meters["shake"] < world.facts["collapse_at"]:
        return []
    sig = ("collapse", "base")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    base.meters["collapsed"] += 1
    for kid in world.kids():
        kid.memes["sad"] += 1
    return ["__collapse__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise", tag="physical", apply=_r_noise),
    Rule(name="collapse", tag="physical", apply=_r_collapse),
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


def dangerous_combo(base: BaseSetting, device: Device) -> bool:
    return device.powered and device.loud and (device.volume + base.echo >= 2)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def signal_severity(base: BaseSetting, device: Device, delay: int) -> int:
    return base.echo + device.volume + delay


def is_contained(base: BaseSetting, device: Device, response: Response, delay: int) -> bool:
    return response.power >= signal_severity(base, device, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def predict_signal(world: World) -> dict:
    sim = world.copy()
    _do_activate(sim, narrate=False)
    return {
        "noise": sim.get("room").meters["noise"],
        "shake": sim.get("base").meters["shake"],
        "collapse": sim.get("base").meters["collapsed"] >= THRESHOLD,
    }


def _do_activate(world: World, narrate: bool = True) -> None:
    world.get("device").meters["blaring"] += 1
    propagate(world, narrate=narrate)


def play_setup(world: World, a: Entity, b: Entity, base: BaseSetting) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"After lunch, {a.id} and {b.id} turned a corner of the house into {base.scene}. "
        f"{base.build_line}"
    )
    world.say(
        f'Together they whispered, "Heroes to the base!" and ducked into {base.dark_corner}.'
    )


def find_book(world: World, a: Entity, b: Entity, book: AncientBook) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"Behind a stack of capes, {b.id} found {book.phrase}. {book.cover_line}"
    )
    world.say(
        f'{b.id} opened it carefully. "Look," {b.pronoun()} said. "This book is ancient."'
    )


def need_signal(world: World, a: Entity, b: Entity, device: Device) -> None:
    world.say(
        f"They decided their next mission was to warn the city about pretend trouble. "
        f'"A real hero base needs {device.phrase}," {a.id} said.'
    )


def tempt(world: World, a: Entity, book: AncientBook, device: Device) -> None:
    a.memes["bravado"] += 1
    world.say(
        f"{a.id}'s eyes grew bright. "
        f'"The ancient book has the {book.code_name}," {a.pronoun()} said. '
        f'"I can read it into {device.phrase} and make it work."'
    )


def warn(world: World, b: Entity, a: Entity, book: AncientBook, parent: Entity) -> None:
    pred = predict_signal(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_shake"] = pred["shake"]
    b.memes["caution"] += 1
    extra = ""
    if pred["collapse"]:
        extra = " The whole base could wobble and fall in."
    world.say(
        f'{b.id} hugged the book to {b.pronoun("possessive")} chest. '
        f'"Wait," {b.pronoun()} said. "{book.warning} {parent.label_word.capitalize()} says '
        f"emergency gear is for real emergencies, not for games.{extra}\""
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"It will only be for one second," {a.id} said, and because {a.pronoun()} '
            f"was the older one, {b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"It will only be for one second," {a.id} said, and reached for the switch.'
        )


def back_down(world: World, a: Entity, b: Entity, book: AncientBook, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["bravery"] = 0.0
    rel = "brother" if b.type == "boy" else "sister"
    world.say(
        f'{a.id} looked at {b.id}, at the old page, and then at the little base around them. '
        f'"No," {a.pronoun()} said at last. "You are my big {rel}. I should listen."'
    )
    world.say(
        f"They shut the ancient book, left the code unread, and went to ask "
        f"{parent.label_word} for a safer hero signal."
    )


def activate(world: World, a: Entity, book: AncientBook, device: Device) -> None:
    _do_activate(world, narrate=True)
    world.say(
        f"{a.id} cleared {a.pronoun('possessive')} throat and read the ancient words aloud. "
        f"{device.activate_text}"
    )
    world.say(device.consequence)


def alarm(world: World, b: Entity, parent: Entity) -> None:
    if world.facts.get("pet"):
        world.say(
            f'"{parent.label_word.upper()}!" {b.id} shouted. '
            f'The family pet scrambled back with wide eyes.'
        )
    else:
        world.say(f'"{parent.label_word.upper()}!" {b.id} shouted over the noise.')


def rescue(world: World, parent: Entity, response: Response) -> None:
    world.get("device").meters["blaring"] = 0.0
    world.get("room").meters["noise"] = 0.0
    body = response.text
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    world.say(
        "The terrible blare cut off at once. The air felt quiet again, and both young heroes "
        "pressed their hands over their thumping chests."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, book: AncientBook, device: Device) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["love"] += 1
        kid.memes["relief"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside the base and pulled them close. '
        f'"I am glad you called me," {parent.pronoun()} said softly. '
        f'"But {device.label} is not a toy, and old codes are not for pretending. '
        f'You must never read a warning code aloud just to see what happens."'
    )
    world.say(
        f'{a.id} nodded. {b.id} touched the shut cover of the ancient book and nodded too.'
    )
    world.say(
        f'Together they promised to read hero stories for fun and leave real emergency tools alone.'
    )


def rescue_fail(world: World, parent: Entity, response: Response) -> None:
    body = response.fail
    world.say(
        f"{parent.label_word.capitalize()} came running and {body}."
    )
    if world.get("base").meters["collapsed"] >= THRESHOLD:
        world.say(
            "The cape wall sagged, a cardboard panel flopped down, and the whole base slumped into a heap."
        )
    else:
        world.say(
            "Even after the sound stopped, everyone's ears rang and the game was ruined for the rest of the afternoon."
        )


def grim_lesson(world: World, parent: Entity, a: Entity, b: Entity, device: Device) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} sat with them on the floor until their breathing slowed. '
        f'"Real emergency gear can scare people and wreck a game in a blink," {parent.pronoun()} said.'
    )
    world.say(
        f"{a.id} and {b.id} never forgot it. After that day, if a mission needed a signal, "
        f"they chose a quiet plan instead of touching {device.label}."
    )


def safe_tools(world: World, parent: Entity, a: Entity, b: Entity, base: BaseSetting,
               tool1: SafeTool, tool2: SafeTool) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    next_day = "The next day" if world.facts["outcome"] != "averted" else "That evening"
    world.say(
        f"{next_day}, {parent.label_word} brought them {tool1.phrase} and {tool2.phrase}. "
        f'"Heroes can still send signals," {parent.pronoun()} said, "just not with a dangerous racket."'
    )
    world.say(
        f"{a.id} used {tool1.use_line}, and {b.id} used {tool2.use_line}."
    )
    world.say(
        f"Soon their base was full of brave whispers instead of blaring noise, and the mission went on. "
        f"{base.ending_line}"
    )


def tell(base: BaseSetting, book: AncientBook, device: Device, tools: tuple[SafeTool, SafeTool],
         response: Response, instigator: str = "Max", instigator_gender: str = "boy",
         cautioner: str = "Lily", cautioner_gender: str = "girl", parent_type: str = "mother",
         trait: str = "careful", delay: int = 0, instigator_age: int = 6, cautioner_age: int = 4,
         relation: str = "siblings", pet: str = "") -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        traits=[trait],
        attrs={"relation": relation},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(Entity(
        id="base",
        type="base",
        label="the base",
        fragile=base.fragile,
    ))
    world.add(Entity(
        id="device",
        type="device",
        label=device.label,
        powered=device.powered,
        loud=device.loud,
    ))
    if pet:
        world.add(Entity(id="pet", type="pet", label=pet))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    world.facts["echo"] = base.echo
    world.facts["collapse_at"] = 2.0
    world.facts["pet"] = pet

    play_setup(world, a, b, base)
    find_book(world, a, b, book)
    need_signal(world, a, b, device)

    world.para()
    tempt(world, a, book, device)
    warn(world, b, a, book, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, book, parent)
        world.para()
        safe_tools(world, parent, a, b, base, tools[0], tools[1])
        severity = 0
        contained = True
    else:
        defy(world, a, b)
        world.para()
        activate(world, a, book, device)
        alarm(world, b, parent)

        severity = signal_severity(base, device, delay)
        world.get("device").meters["severity"] = float(severity)
        contained = is_contained(base, device, response, delay)

        world.para()
        if contained:
            rescue(world, parent, response)
            lesson(world, parent, a, b, book, device)
            world.para()
            safe_tools(world, parent, a, b, base, tools[0], tools[1])
        else:
            world.get("base").meters["shake"] += float(delay)
            propagate(world, narrate=False)
            rescue_fail(world, parent, response)
            grim_lesson(world, parent, a, b, device)
            world.para()
            safe_tools(world, parent, a, b, base, tools[0], tools[1])

    outcome = "averted" if averted else ("contained" if contained else "ruined")
    world.facts.update(
        base_cfg=base,
        book=book,
        device_cfg=device,
        response=response,
        tools=tools,
        instigator=a,
        cautioner=b,
        parent=parent,
        relation=relation,
        ignited=world.get("device").meters["severity"] >= THRESHOLD if not averted else False,
        outcome=outcome,
        severity=severity,
        delay=delay,
        promised=a.memes["lesson"] >= THRESHOLD or b.memes["lesson"] >= THRESHOLD,
    )
    return world


BASES = {
    "fort_hq": BaseSetting(
        id="fort_hq",
        scene="a superhero base under blankets and couch cushions",
        build_line="A blue blanket became the roof, two chairs became the gates, and a cereal box held their mission cards.",
        dark_corner="the soft little hallway inside it",
        ending_line="Their secret base felt brighter, calmer, and more heroic than before.",
        echo=2,
        fragile=True,
        tags={"base", "fort"},
    ),
    "garage_hq": BaseSetting(
        id="garage_hq",
        scene="a cardboard hero base in the garage",
        build_line="An old appliance box became the command room, broom handles became antenna towers, and capes hung from a nail like flags.",
        dark_corner="the box-door of their command room",
        ending_line="The cardboard base stood proudly, and their mission felt clever instead of noisy.",
        echo=1,
        fragile=True,
        tags={"base", "garage"},
    ),
    "treehouse_hq": BaseSetting(
        id="treehouse_hq",
        scene="a secret superhero base in the treehouse",
        build_line="A string map covered one wall, a bucket held pebbles for pretend meteors, and the ladder felt like the way to the clouds.",
        dark_corner="the little lookout nook",
        ending_line="The treehouse swayed gently while the two heroes practiced their new quiet signal.",
        echo=1,
        fragile=False,
        tags={"base", "treehouse"},
    ),
    "attic_hq": BaseSetting(
        id="attic_hq",
        scene="a dusty superhero base in the attic",
        build_line="A trunk became the command desk, a silver scarf became a river of stars, and a lamp-less corner waited like a hidden cave.",
        dark_corner="the slant-roof corner",
        ending_line="Even the attic felt friendly once the heroes chose careful tools.",
        echo=2,
        fragile=True,
        tags={"base", "attic"},
    ),
}

BOOKS = {
    "ancient_handbook": AncientBook(
        id="ancient_handbook",
        label="ancient hero handbook",
        phrase="an ancient hero handbook with a cracked gold star on the cover",
        cover_line="Its corners were soft with age, and some pages had warning signs in red ink.",
        code_name="Thunder Call",
        warning="That page has an emergency code on it.",
        tags={"read", "ancient", "book"},
    ),
    "ancient_manual": AncientBook(
        id="ancient_manual",
        label="ancient signal manual",
        phrase="an ancient signal manual tied with faded red string",
        cover_line="Inside were old maps, little drawings of capes, and one page marked ONLY FOR TRUE DANGER.",
        code_name="Sky Siren Words",
        warning="Those words are there for trouble, not for play.",
        tags={"read", "ancient", "book"},
    ),
}

DEVICES = {
    "megaphone": Device(
        id="megaphone",
        label="the megaphone",
        phrase="a real megaphone",
        activate_text="The megaphone popped once and then roared awake.",
        consequence="The sound bounced off the walls like a hundred caped feet stomping at once.",
        volume=2,
        powered=True,
        loud=True,
        tags={"megaphone", "noise", "emergency"},
    ),
    "siren_box": Device(
        id="siren_box",
        label="the siren box",
        phrase="the old siren box by the wall",
        activate_text="The tiny red bulb flashed, and the siren box let out a sharp, rising wail.",
        consequence="The sound drilled through the base so hard that even the capes trembled.",
        volume=3,
        powered=True,
        loud=True,
        tags={"siren", "noise", "emergency"},
    ),
    "booster_speaker": Device(
        id="booster_speaker",
        label="the booster speaker",
        phrase="the booster speaker from the closet shelf",
        activate_text="The speaker crackled, hummed, and blasted the words back at them twice as big.",
        consequence="The little base shook with the heavy boom of its own echo.",
        volume=2,
        powered=True,
        loud=True,
        tags={"speaker", "noise", "emergency"},
    ),
    "paper_badge": Device(
        id="paper_badge",
        label="the paper badge",
        phrase="a paper badge with a lightning bolt drawn on it",
        activate_text="Nothing happened at all.",
        consequence="It was only cardboard and tape.",
        volume=0,
        powered=False,
        loud=False,
        tags={"badge"},
    ),
}

SAFE_TOOLS = {
    "flashlight": SafeTool(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        use_line="the flashlight to blink a quiet hero signal on the wall",
        tags={"flashlight"},
    ),
    "hand_signs": SafeTool(
        id="hand_signs",
        label="hand signs",
        phrase="a card of hand signs",
        use_line="the hand-sign card to send messages without a peep",
        tags={"hand_signs"},
    ),
    "toy_radio": SafeTool(
        id="toy_radio",
        label="toy radio",
        phrase="a soft-clicking toy radio",
        use_line="the toy radio to whisper mission news in a pretend hero voice",
        tags={"radio"},
    ),
    "signal_cards": SafeTool(
        id="signal_cards",
        label="signal cards",
        phrase="a stack of bright signal cards",
        use_line="the signal cards to flip up messages for the next mission",
        tags={"cards"},
    ),
}

RESPONSES = {
    "unplug": Response(
        id="unplug",
        sense=3,
        power=4,
        text="pulled the plug from the wall before the noise could grow any bigger",
        fail="reached for the plug, but the noise had already shaken the base into a panic",
        qa_text="pulled the plug and stopped the noise",
        tags={"electricity", "unplug"},
    ),
    "pull_batteries": Response(
        id="pull_batteries",
        sense=3,
        power=3,
        text="snapped open the battery cover and pulled the batteries free",
        fail="got the battery cover open, but not before the blaring had already wrecked the game",
        qa_text="pulled the batteries out and stopped the noise",
        tags={"batteries"},
    ),
    "power_button": Response(
        id="power_button",
        sense=2,
        power=2,
        text="pressed the power button hard and held it until the device went quiet",
        fail="pressed the power button, but the base had already been rattled too badly",
        qa_text="held the power button until the device went quiet",
        tags={"button"},
    ),
    "shout_over": Response(
        id="shout_over",
        sense=1,
        power=0,
        text="shouted for everyone to wait",
        fail="shouted over the blare, which did not help at all",
        qa_text="shouted over the noise",
        tags={"noise"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Max", "Ben", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]
TRAITS = ["careful", "curious", "cautious", "steady", "brave", "sensible"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for bid, base in BASES.items():
        for did, device in DEVICES.items():
            if dangerous_combo(base, device):
                combos.append((bid, did))
    return combos


@dataclass
class StoryParams:
    base: str
    book: str
    device: str
    tool1: str
    tool2: str
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
    pet: str = ""
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
    "ancient": [
        (
            "What does ancient mean?",
            "Ancient means very old, from a long time ago. Ancient things can be special, but they may need careful handling."
        )
    ],
    "read": [
        (
            "Why should you read warning words carefully?",
            "Warning words tell you that something could be unsafe. If you read them carefully, you can stop and ask a grown-up before doing something risky."
        )
    ],
    "noise": [
        (
            "Why can very loud noises be a problem?",
            "Very loud noises can hurt your ears and make your body feel scared. They can also startle pets and make it hard for people to think."
        )
    ],
    "emergency": [
        (
            "What is emergency equipment for?",
            "Emergency equipment is for real trouble when someone needs help fast. It should not be used in a pretend game."
        )
    ],
    "megaphone": [
        (
            "What does a megaphone do?",
            "A megaphone makes a voice much louder. That is useful in a real emergency, but it can be too noisy for indoor play."
        )
    ],
    "siren": [
        (
            "What is a siren?",
            "A siren is a loud warning sound. People use it to get attention fast when there is danger."
        )
    ],
    "speaker": [
        (
            "What does a speaker do?",
            "A speaker pushes sound out into the room. If the sound is too strong, it can boom and echo."
        )
    ],
    "batteries": [
        (
            "What do batteries do?",
            "Batteries store energy for many small devices. Taking them out can stop a noisy device from working."
        )
    ],
    "electricity": [
        (
            "Why should grown-ups unplug electrical things?",
            "Unplugging stops electricity from reaching the device. Grown-ups do it when they need to turn something off safely."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight a safe signal tool?",
            "A flashlight makes light without a blaring sound. It can help people send a signal quietly."
        )
    ],
    "hand_signs": [
        (
            "What are hand signs?",
            "Hand signs are quiet motions people use to share a message. They are useful when you do not want to make noise."
        )
    ],
    "radio": [
        (
            "What is a toy radio?",
            "A toy radio is a pretend talking tool for play. It lets children imagine a mission without using real emergency equipment."
        )
    ],
    "cards": [
        (
            "What are signal cards for?",
            "Signal cards show messages with colors or pictures. They are a calm way to share a plan during a game."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ancient",
    "read",
    "noise",
    "emergency",
    "megaphone",
    "siren",
    "speaker",
    "batteries",
    "electricity",
    "flashlight",
    "hand_signs",
    "radio",
    "cards",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    base = f["base_cfg"]
    book = f["book"]
    device = f["device_cfg"]
    t1, t2 = f["tools"]
    outcome = f["outcome"]
    base_prompt = (
        f'Write a short cautionary superhero story for a 3-to-5-year-old that includes the words '
        f'"base", "read", and "ancient". Two children find {book.label} in their secret base and '
        f'think about using {device.label}.'
    )
    if outcome == "averted":
        return [
            base_prompt,
            f"Tell a near-miss superhero story where {a.id} wants to read an old emergency code aloud, "
            f"but listens to {b.id} and asks a grown-up for a safer signal instead.",
            f"Write a gentle hero story set in {base.scene} where the children choose {t1.label} and "
            f"{t2.label} instead of real emergency gear.",
        ]
    if outcome == "ruined":
        return [
            base_prompt,
            f"Tell a cautionary superhero story where {a.id} reads the ancient code into {device.label}, "
            f"the noise is too big, and the base gets ruined before the grown-up can fully help.",
            "Write a child-facing warning story that shows why emergency equipment is not for pretend games, "
            "but still ends with everyone safe and wiser.",
        ]
    return [
        base_prompt,
        f"Tell a superhero story where {a.id} ignores {b.id}'s warning, reads the code, and a grown-up stops "
        f"{device.label} quickly.",
        f"Write a simple cautionary story that ends with safe tools like {t1.label} and {t2.label} replacing "
        f"the dangerous signal gear.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    base = f["base_cfg"]
    book = f["book"]
    device = f["device_cfg"]
    response = f["response"]
    tool1, tool2 = f["tools"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who built a superhero base together. "
            f"Their {pw} also matters because {pw} helps when the signal goes wrong."
        ),
        (
            "What did the children find in the base?",
            f"They found {book.phrase}. It felt special because it was ancient and had warning words inside."
        ),
        (
            f"Why did {a.id} want to read from the old book?",
            f"{a.id} wanted to make the mission feel real by using {device.label} like a hero signal. "
            f"The ancient code made the idea sound exciting and powerful."
        ),
        (
            f"Why did {b.id} try to stop {a.id}?",
            f"{b.id} understood that the page held a real emergency code, not a pretend one. "
            f"{b.pronoun().capitalize()} also feared the loud device could shake the base and scare everyone."
        ),
    ]
    if f["outcome"] == "averted":
        qa.extend([
            (
                f"What happened after {b.id} warned {a.id}?",
                f"{a.id} backed down and left the ancient code unread. "
                f"That choice stopped the danger before the signal gear could blare at all."
            ),
            (
                "How did the story end?",
                f"It ended quietly and happily. The children used {tool1.label} and {tool2.label} to keep playing hero in a safer way."
            ),
        ])
    elif f["outcome"] == "contained":
        qa.extend([
            (
                f"What happened when {a.id} read the ancient code aloud?",
                f"{device.label.capitalize()} blared so loudly that the whole base shook and both children got scared. "
                f"The danger came from using real emergency gear in a small play space."
            ),
            (
                f"How did the {pw} stop the problem?",
                f"The {pw} {response.qa_text}. That quick action cut off the sound before the base was ruined."
            ),
            (
                "What lesson did the children learn?",
                f"They learned that emergency tools are not toys and warning codes should not be read aloud for fun. "
                f"Afterward they still got to play, but with safer signal tools."
            ),
        ])
    else:
        ruined_detail = "the base collapsed" if world.get("base").meters["collapsed"] >= THRESHOLD else "the game was ruined"
        qa.extend([
            (
                f"Did the grown-up stop the noise in time?",
                f"Not quite. The {pw} tried to help, but {ruined_detail} before the danger felt fully under control."
            ),
            (
                "How did the story end?",
                f"Everyone was safe, but the children were sad and shaken. "
                f"Later they rebuilt their hero play with {tool1.label} and {tool2.label} instead."
            ),
            (
                f"Why is this a cautionary story?",
                f"It warns that exciting old words and real emergency tools can cause trouble when used carelessly. "
                f"The children's mistake changed the base and taught them to ask for a safer plan."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ancient", "read", "noise", "emergency"}
    device = f["device_cfg"]
    if "megaphone" in device.tags:
        tags.add("megaphone")
    if "siren" in device.tags:
        tags.add("siren")
    if "speaker" in device.tags:
        tags.add("speaker")
    response = f["response"]
    tags |= response.tags
    for tool in f["tools"]:
        tags |= tool.tags
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.age:
            parts.append(f"age={ent.age}")
        flags = [n for n, on in (("powered", ent.powered), ("loud", ent.loud), ("fragile", ent.fragile)) if on]
        if flags:
            parts.append(f"flags={flags}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(parts)}")
    lines.append(f"  facts: echo={world.facts.get('echo')} collapse_at={world.facts.get('collapse_at')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        base="fort_hq",
        book="ancient_handbook",
        device="siren_box",
        tool1="flashlight",
        tool2="hand_signs",
        response="unplug",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Lily",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        pet="the kitten",
    ),
    StoryParams(
        base="garage_hq",
        book="ancient_manual",
        device="booster_speaker",
        tool1="signal_cards",
        tool2="toy_radio",
        response="power_button",
        instigator="Mia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="sensible",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        pet="",
    ),
    StoryParams(
        base="attic_hq",
        book="ancient_handbook",
        device="megaphone",
        tool1="flashlight",
        tool2="signal_cards",
        response="power_button",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Nora",
        cautioner_gender="girl",
        parent="mother",
        trait="curious",
        delay=2,
        instigator_age=7,
        cautioner_age=5,
        relation="siblings",
        pet="the cat",
    ),
    StoryParams(
        base="treehouse_hq",
        book="ancient_manual",
        device="megaphone",
        tool1="hand_signs",
        tool2="toy_radio",
        response="pull_batteries",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Zoe",
        cautioner_gender="girl",
        parent="father",
        trait="steady",
        delay=1,
        instigator_age=6,
        cautioner_age=6,
        relation="friends",
        pet="the little dog",
    ),
]


def explain_rejection(base: BaseSetting, device: Device) -> str:
    if not device.powered or not device.loud:
        return (
            f"(No story: {device.label} is not real blaring emergency gear, so it cannot create the cautionary problem. "
            f"Pick a device like the megaphone, siren box, or booster speaker.)"
        )
    return (
        f"(No story: {device.label} does not create enough danger in {base.scene} for this world. "
        f"Pick a louder device or a more echoing base.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the sensible responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(BASES[params.base], DEVICES[params.device], RESPONSES[params.response], params.delay) else "ruined"


ASP_RULES = r"""
hazard(B, D) :- base(B), device(D), powered(D), loud(D), echo(B, E), volume(D, V), V + E >= 2.
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(B, D) :- hazard(B, D).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(E + V + D) :- chosen_base(B), echo(B, E), chosen_device(X), volume(X, V), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(ruined) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for bid, base in BASES.items():
        lines.append(asp.fact("base", bid))
        lines.append(asp.fact("echo", bid, base.echo))
        if base.fragile:
            lines.append(asp.fact("fragile", bid))
    for did, device in DEVICES.items():
        lines.append(asp.fact("device", did))
        lines.append(asp.fact("volume", did, device.volume))
        if device.powered:
            lines.append(asp.fact("powered", did))
        if device.loud:
            lines.append(asp.fact("loud", did))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_base", params.base),
        asp.fact("chosen_device", params.device),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("instigator_age", params.instigator_age),
        asp.fact("cautioner_age", params.cautioner_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(120):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        p.seed = seed
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        assert smoke.story.strip(), "empty story"
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero base, an ancient code, and a warning about real emergency gear."
    )
    ap.add_argument("--base", choices=BASES)
    ap.add_argument("--book", choices=BOOKS)
    ap.add_argument("--device", choices=DEVICES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the noise gets to grow before help fully lands")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.base and args.device:
        if not dangerous_combo(BASES[args.base], DEVICES[args.device]):
            raise StoryError(explain_rejection(BASES[args.base], DEVICES[args.device]))
    if args.device and args.device not in DEVICES:
        raise StoryError("(Unknown device.)")
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.base is None or combo[0] == args.base)
        and (args.device is None or combo[1] == args.device)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    base_id, device_id = rng.choice(sorted(combos))
    book_id = args.book or rng.choice(sorted(BOOKS))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    tool1, tool2 = rng.sample(sorted(SAFE_TOOLS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    pet = rng.choice(PETS)
    return StoryParams(
        base=base_id,
        book=book_id,
        device=device_id,
        tool1=tool1,
        tool2=tool2,
        response=response_id,
        instigator=instigator,
        instigator_gender=ig,
        cautioner=cautioner,
        cautioner_gender=cg,
        parent=parent,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
        relation=relation,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    for name, registry in {
        "base": BASES,
        "book": BOOKS,
        "device": DEVICES,
        "tool1": SAFE_TOOLS,
        "tool2": SAFE_TOOLS,
        "response": RESPONSES,
    }.items():
        if getattr(params, name) not in registry:
            raise StoryError(f"(Unknown {name}: {getattr(params, name)!r})")
    if params.response in RESPONSES and RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    if not dangerous_combo(BASES[params.base], DEVICES[params.device]):
        raise StoryError(explain_rejection(BASES[params.base], DEVICES[params.device]))
    if params.tool1 == params.tool2:
        raise StoryError("(Need two different safe tools.)")

    world = tell(
        base=BASES[params.base],
        book=BOOKS[params.book],
        device=DEVICES[params.device],
        tools=(SAFE_TOOLS[params.tool1], SAFE_TOOLS[params.tool2]),
        response=RESPONSES[params.response],
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        pet=params.pet,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (base, device) combos:\n")
        for base_id, device_id in combos:
            print(f"  {base_id:12} {device_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.base} / {p.device} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
