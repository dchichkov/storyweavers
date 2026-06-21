#!/usr/bin/env python3
"""
storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py
==============================================================

A standalone story world about a child hearing a ginormous silly sound from a
high place, getting terribly curious, trying an unsafe way to peek, and ending
up with a safer family rule and a laugh.

The domain is deliberately small and constraint-checked:

- A funny sound source lives in a high spot.
- The instigator wants to investigate because curiosity is stronger than caution.
- An unsafe support can wobble under reaching.
- A calmer helper predicts the wobble and either averts the climb or calls a
  grown-up.
- A grown-up uses a sensible response, reveals the ridiculous source, and the
  ending image proves what changed: curiosity now waits for safe help.

Run it
------
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --place pantry --source frog_box
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --support laundry_basket
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --response broom_poke
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --all
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --trace --seed 777
    python storyworlds/worlds/ginormous_curiosity_sound_effects_comedy.py --verify
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
CURIOSITY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "patient", "sensible", "steady"}


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
    movable: bool = False
    unstable: bool = False
    high: bool = False
    # physical / emotional dimensions
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
    high_spot: str
    room_line: str
    supports: set[str] = field(default_factory=set)
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
class Source:
    id: str
    label: str
    container: str
    sound: str
    bounce_line: str
    reveal: str
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
class Support:
    id: str
    label: str
    phrase: str
    risk: int
    wobble: str
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    if "instigator" not in world.entities or "support" not in world.entities:
        return out
    kid = world.get("instigator")
    support = world.get("support")
    if kid.meters["reaching"] < THRESHOLD or support.meters["occupied"] < THRESHOLD:
        return out
    if not support.unstable:
        return out
    sig = ("wobble", support.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    support.meters["wobbling"] += 1
    kid.memes["fear"] += 1
    for other in world.kids():
        if other.id != kid.id:
            other.memes["fear"] += 1
    if "room" in world.entities:
        world.get("room").meters["danger"] += 1
    out.append("__wobble__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    if "source_box" not in world.entities or "instigator" not in world.entities:
        return out
    box = world.get("source_box")
    kid = world.get("instigator")
    if box.meters["jostled"] < THRESHOLD:
        return out
    sig = ("spill", box.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box.meters["open"] += 1
    box.meters["spilled"] += 1
    kid.meters["confetti"] += 1
    out.append("__spill__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="spill", tag="physical", apply=_r_spill),
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


def support_allowed(place: Place, support_id: str) -> bool:
    return support_id in place.supports


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def wobble_severity(support: Support, delay: int) -> int:
    return support.risk + delay


def is_contained(response: Response, support: Support, delay: int) -> bool:
    return response.power >= wobble_severity(support, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > CURIOSITY_INIT


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    kid = sim.get("instigator")
    support = sim.get("support")
    kid.meters["reaching"] += 1
    support.meters["occupied"] += 1
    sim.get("source_box").meters["jostled"] += 1
    propagate(sim, narrate=False)
    return {
        "wobble": support.meters["wobbling"] >= THRESHOLD,
        "spill": sim.get("source_box").meters["spilled"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def scene_setup(world: World, a: Entity, b: Entity, place: Place, source: Source) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"One afternoon, {a.id} and {b.id} were in {place.label}. {place.room_line}"
    )
    world.say(
        f"Then, from {place.high_spot}, came a sound so sudden and silly that both children froze: "
        f'"{source.sound}!"'
    )
    world.say(
        f"{a.id}'s eyes went round. It sounded ginormous, as if a rubber elephant had tried to hiccup."
    )


def curiosity(world: World, a: Entity, place: Place) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f'"What is up there?" {a.id} whispered. {a.pronoun().capitalize()} craned '
        f'{a.pronoun("possessive")} neck toward {place.high_spot} and took one small step closer.'
    )


def tempt(world: World, a: Entity, support: Support) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'"I can peek if I stand on {support.phrase}," {a.id} said. '
        f"For one breath, the idea sounded as quick as a snap."
    )


def warn(world: World, b: Entity, a: Entity, support: Support, parent: Entity) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = ""
    if pred["spill"]:
        extra = " And if the box tips, everything inside could go flying."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "No, {a.id}. '
        f'{support.label.capitalize()} wobbles. If you reach up there, it could wiggle right out from under you.{extra} '
        f'Let\'s get {parent.label_word}."'
    )


def back_down(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} made a face, then let out the breath {a.pronoun()} had been holding. "
        f'"Okay," {a.pronoun()} said. "I want to know, but not enough to wobble."'
    )
    world.say(
        f"The two children hurried to get {parent.label_word}, still listening for the next ridiculous noise."
    )


def defy(world: World, a: Entity, b: Entity, support: Support) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        rel = "big brother" if a.type == "boy" else "big sister"
        world.say(
            f'"Just one tiny peek," {a.id} said, because {a.pronoun()} was {b.pronoun("possessive")} {rel} '
            f"and felt very sure of {a.pronoun('object')}self."
        )
    else:
        world.say(f'"Just one tiny peek," {a.id} said.')
    world.say(f"{a.pronoun().capitalize()} dragged over {support.phrase} and climbed up.")


def wobble(world: World, a: Entity, support: Support, source: Source) -> None:
    world.get("support").meters["occupied"] += 1
    a.meters["reaching"] += 1
    world.get("source_box").meters["jostled"] += 1
    propagate(world, narrate=False)
    world.say(
        f"As {a.id} stretched toward the {source.container}, {support.label} went {support.wobble}."
    )


def alarm(world: World, b: Entity, a: Entity, parent: Entity) -> None:
    world.say(f'"{a.id}!" {b.id} yelped. "Get {parent.label_word}!"')


def rescue(world: World, parent: Entity, response: Response, source: Source) -> None:
    world.get("support").meters["wobbling"] = 0.0
    world.get("room").meters["danger"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came fast and {response.text.format(container=source.container)}."
    )
    world.say(
        f"A second later, the truth popped out: {source.reveal}"
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["joy"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt down until {parent.pronoun()} was eye to eye with them. '
        f'"Curiosity is fine," {parent.pronoun()} said, smiling a little. '
        f'"But if a mystery is high up, we solve it with help, not wobbling."'
    )
    world.say(
        f"{a.id} and {b.id} nodded, and then all three of them laughed so hard somebody had to hold the shelf to be safe."
    )


def safe_end(world: World, a: Entity, b: Entity, source: Source) -> None:
    for kid in (a, b):
        kid.memes["safety"] += 1
    world.say(
        f"After that, whenever they heard {source.sound} from somewhere high, "
        f"{a.id} and {b.id} called for help first and guessed second."
    )
    world.say(
        f"And every new guess grew sillier than the last until the whole room sounded like: "
        f'"boing, squeak, pffft, ha-ha-ha!"'
    )


def rescue_fail(world: World, parent: Entity, response: Response, source: Source, support: Support) -> None:
    world.get("room").meters["danger"] += 1
    world.get("support").meters["wobbling"] += 1
    world.get("source_box").meters["spilled"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried in and {response.fail.format(container=source.container)}."
    )
    world.say(
        f"The {support.label} skidded, the {source.container} tipped, and suddenly the floor was full of silly clutter."
    )


def comic_mess(world: World, a: Entity, b: Entity, source: Source) -> None:
    a.meters["confetti"] += 1
    for kid in (a, b):
        kid.memes["fear"] += 1
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"Nothing worse than surprise happened, but {a.id} landed on {a.pronoun('possessive')} bottom with a soft oomph, "
        f"while the mystery turned out to be {source.reveal}"
    )
    world.say(
        f"Paper bits, ribbons, and one very rude sound bounced everywhere. Even through the shock, {b.id} gave one helpless snort."
    )
    world.say(
        "After that, the children had a new family rule: if a funny noise comes from up high, funny guesses may stay on the floor."
    )


def tell(
    place: Place,
    source: Source,
    support: Support,
    response: Response,
    *,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    cautioner: str = "Tess",
    cautioner_gender: str = "girl",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id="instigator",
        kind="character",
        type=instigator_gender,
        label=instigator,
        role="instigator",
        age=instigator_age,
        attrs={"name": instigator, "relation": relation},
    ))
    b = world.add(Entity(
        id="cautioner",
        kind="character",
        type=cautioner_gender,
        label=cautioner,
        role="cautioner",
        age=cautioner_age,
        attrs={"name": cautioner, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    room = world.add(Entity(id="room", type="room", label=place.label))
    support_ent = world.add(Entity(
        id="support",
        type="support",
        label=support.label,
        unstable=True,
        movable=True,
    ))
    source_box = world.add(Entity(
        id="source_box",
        type="box",
        label=source.container,
        high=True,
    ))

    a.memes["curiosity"] = CURIOSITY_INIT
    b.memes["trust"] = float(trust)
    b.memes["caution"] = initial_caution(trait)
    room.meters["danger"] = 0.0
    support_ent.meters["occupied"] = 0.0
    support_ent.meters["wobbling"] = 0.0
    source_box.meters["jostled"] = 0.0
    source_box.meters["spilled"] = 0.0
    source_box.meters["open"] = 0.0
    a.meters["reaching"] = 0.0

    world.para()
    scene_setup(world, a, b, place, source)
    curiosity(world, a, place)

    world.para()
    tempt(world, a, support)
    warn(world, b, a, support, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        back_down(world, a, b, parent)
        world.para()
        rescue(world, parent, response, source)
        lesson(world, parent, a, b)
        world.para()
        safe_end(world, a, b, source)
        contained = True
        severity = 0
    else:
        defy(world, a, b, support)
        world.para()
        wobble(world, a, support, source)
        alarm(world, b, a, parent)
        severity = wobble_severity(support, delay)
        support_ent.meters["severity"] = float(severity)
        contained = is_contained(response, support, delay)

        world.para()
        if contained:
            rescue(world, parent, response, source)
            lesson(world, parent, a, b)
            world.para()
            safe_end(world, a, b, source)
        else:
            rescue_fail(world, parent, response, source, support)
            comic_mess(world, a, b, source)

    outcome = "averted" if averted else ("contained" if contained else "spilled")
    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        place=place,
        source=source,
        support_cfg=support,
        response=response,
        relation=relation,
        outcome=outcome,
        severity=severity,
        delay=delay,
        revealed=source_box.meters["open"] >= THRESHOLD or outcome in {"contained", "spilled", "averted"},
        predicted_danger=world.facts.get("predicted_danger", 0),
    )
    return world


PLACES = {
    "hall_closet": Place(
        id="hall_closet",
        label="the front hall",
        high_spot="the top closet shelf",
        room_line="Coats leaned together, one shoe lay upside down, and the closet door stood a little bit open.",
        supports={"rolling_chair", "pillow_stack"},
        tags={"closet"},
    ),
    "pantry": Place(
        id="pantry",
        label="the pantry",
        high_spot="the highest pantry shelf",
        room_line="Crinkly cereal boxes stood like tiny buildings, and a wooden stool was nowhere in sight.",
        supports={"rolling_chair", "step_bin"},
        tags={"kitchen"},
    ),
    "laundry_room": Place(
        id="laundry_room",
        label="the laundry room",
        high_spot="the high cabinet over the washer",
        room_line="Warm towels made the room smell clean, and one sock clung to the dryer like a flag.",
        supports={"laundry_basket", "step_bin"},
        tags={"laundry"},
    ),
}

SOURCES = {
    "frog_box": Source(
        id="frog_box",
        label="spring frog",
        container="a party box",
        sound="BOI-oi-oing",
        bounce_line="a frog",
        reveal="a green spring frog wearing a paper crown, bouncing every time the box lid twitched.",
        tags={"frog", "boing"},
    ),
    "chicken_bin": Source(
        id="chicken_bin",
        label="rubber chicken",
        container="a dress-up bin",
        sound="SQUEAK-honk",
        bounce_line="a chicken",
        reveal="a rubber chicken wedged under a feather boa, honking every time the boa slid.",
        tags={"chicken", "squeak"},
    ),
    "cushion_trunk": Source(
        id="cushion_trunk",
        label="whoopee cushion",
        container="a costume trunk",
        sound="PFFFT-prrbt",
        bounce_line="a cushion",
        reveal="a whoopee cushion squashed beneath a pirate hat, making rude noises whenever the lid settled.",
        tags={"whoopee", "pffft"},
    ),
}

SUPPORTS = {
    "rolling_chair": Support(
        id="rolling_chair",
        label="the rolling chair",
        phrase="the rolling chair",
        risk=3,
        wobble='"skrrrk-wiggle"',
        tags={"chair", "wobble"},
    ),
    "pillow_stack": Support(
        id="pillow_stack",
        label="the pillow stack",
        phrase="two sofa pillows stacked on a basket",
        risk=2,
        wobble='"fwump-flop"',
        tags={"pillows", "wobble"},
    ),
    "laundry_basket": Support(
        id="laundry_basket",
        label="the upside-down laundry basket",
        phrase="the upside-down laundry basket",
        risk=3,
        wobble='"clacka-clack"',
        tags={"basket", "wobble"},
    ),
    "step_bin": Support(
        id="step_bin",
        label="the tiptoe step-bin",
        phrase="the little step-bin",
        risk=2,
        wobble='"tik-tik-shift"',
        tags={"bin", "wobble"},
    ),
}

RESPONSES = {
    "step_stool": Response(
        id="step_stool",
        sense=3,
        power=4,
        text="steadied the child with one hand, fetched a real step stool, and brought down {container} the safe way",
        fail="tried to hurry over with a step stool, but the wobble had already turned the whole mystery into a tumble of clutter from {container}",
        qa_text="used a real step stool and brought the container down safely",
        tags={"stool", "help"},
    ),
    "lift_down_box": Response(
        id="lift_down_box",
        sense=3,
        power=3,
        text="caught the wobble before it grew, lifted the child down, and reached up to bring down {container}",
        fail="lifted for {container}, but arrived a beat too late and the box had already tipped open",
        qa_text="lifted the child down first and brought the container down",
        tags={"help"},
    ),
    "broom_poke": Response(
        id="broom_poke",
        sense=1,
        power=1,
        text="poked at {container} with a broom from across the room",
        fail="poked at {container} with a broom, which only made the wobble and the mess worse",
        qa_text="poked at the container with a broom",
        tags={"broom"},
    ),
}

GIRL_NAMES = ["Mia", "Tess", "Lulu", "Nora", "Zoe", "Pia", "Ivy", "Ella"]
BOY_NAMES = ["Milo", "Ben", "Owen", "Max", "Theo", "Finn", "Leo", "Kai"]
TRAITS = ["careful", "patient", "sensible", "steady", "curious", "bouncy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for place_id, place in PLACES.items():
        for source_id in SOURCES:
            for support_id in SUPPORTS:
                if support_allowed(place, support_id):
                    combos.append((place_id, source_id, support_id))
    return combos


@dataclass
class StoryParams:
    place: str
    source: str
    support: str
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
    trust: int = 6
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
    "boing": [(
        "Why do spring toys go boing?",
        "A spring toy stores push and pull in its bendy spring. When it lets go, it bounces back fast and makes a boing sound."
    )],
    "squeak": [(
        "Why does a rubber toy squeak?",
        "A squeaky toy pushes air through a tiny hole. The air makes the toy vibrate and that becomes a squeak."
    )],
    "pffft": [(
        "What is a whoopee cushion?",
        "A whoopee cushion is a joke toy that pushes air out in a rude, funny sound when someone sits on it. It is silly because the noise is surprising."
    )],
    "wobble": [(
        "Why is it unsafe to stand on something wobbly?",
        "A wobbly thing can slide or tip when your weight shifts. That makes it easy to fall before you can catch yourself."
    )],
    "stool": [(
        "What is a step stool for?",
        "A step stool is made to help people reach something a little higher in a steadier way. It is safer than balancing on furniture or baskets."
    )],
    "help": [(
        "Why should children ask a grown-up for help with high shelves?",
        "A grown-up can reach higher and use safer tools. Asking for help keeps curiosity from turning into a fall."
    )],
    "sound": [(
        "How can a sound seem bigger than the thing that made it?",
        "Sounds can bounce around a room and surprise your ears. A tiny toy can seem ginormous when the room echoes."
    )],
}
KNOWLEDGE_ORDER = ["sound", "boing", "squeak", "pffft", "wobble", "stool", "help"]


def display_name(ent: Entity) -> str:
    return ent.attrs.get("name", ent.label or ent.id)


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
    a = display_name(f["instigator"])
    b = display_name(f["cautioner"])
    source = f["source"]
    place = f["place"]
    outcome = f["outcome"]
    base = (
        f'Write a funny story for a 3-to-5-year-old about curiosity after a strange sound comes from {place.high_spot}. '
        f'Include the word "ginormous" and a silly sound effect like "{source.sound}".'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a comedy story where {a} wants to climb and peek, but {b} talks {a} into getting a grown-up instead, and the mystery turns out to be ridiculous.",
            f"Write a gentle story about curiosity, high shelves, and safe help, ending in laughter after the sound source is discovered."
        ]
    if outcome == "spilled":
        return [
            base,
            f"Tell a slapstick but safe story where {a} ignores a warning, something wobbles, and the mystery bursts into a silly mess before everyone learns a safer rule.",
            f"Write a comedy with sound effects, wobbling, and a funny reveal, where nobody is badly hurt but the children learn to ask for help."
        ]
    return [
        base,
        f"Tell a story where {a} gets curious about a noisy mystery, tries an unsafe peek, and a calm grown-up steps in safely before revealing the joke source.",
        f"Write a child-facing comedy about a strange noise, a wobble, and a safe ending where the family laughs and makes a better plan for next time."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    place = f["place"]
    source = f["source"]
    support = f["support_cfg"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b, f['relation'])}, {display_name(a)} and {display_name(b)}, plus their {parent.label_word}. They heard a strange noise and wanted to know what made it."
        ),
        (
            "What made the children curious?",
            f'They heard "{source.sound}" coming from {place.high_spot}, and it sounded ginormous. The silly mystery pulled them closer because they wanted to know what could make such a ridiculous noise.'
        ),
        (
            f"Why did {display_name(b)} warn {display_name(a)} not to climb?",
            f"{display_name(b)} knew that {support.label} could wobble if someone stood on it and reached up high. That meant curiosity could turn into a fall and a flying box instead of an answer."
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.extend([
            (
                f"What did {display_name(a)} do after the warning?",
                f"{display_name(a)} backed down and went to get {parent.label_word} instead. That choice kept the mystery funny instead of dangerous."
            ),
            (
                "How was the mystery solved?",
                f"{parent.label_word.capitalize()} {response.qa_text}. Then everyone saw that the noise came from {source.reveal}"
            ),
            (
                "How did the story end?",
                f"It ended with laughter and a new safe habit. The children learned that high-up mysteries are for asking about first, not climbing toward."
            ),
        ])
    elif outcome == "contained":
        qa.extend([
            (
                f"What happened when {display_name(a)} tried to peek?",
                f"{support.label.capitalize()} began to wobble as {display_name(a)} reached toward the high box. The danger came from mixing a high shelf with an unstable thing to stand on."
            ),
            (
                f"How did {parent.label_word} help?",
                f"{parent.label_word.capitalize()} {response.qa_text}. That stopped the wobble from becoming a crash and let the family learn the answer safely."
            ),
            (
                "What was the funny sound really?",
                f"It was {source.reveal} The big comic twist is that a tiny silly toy sounded far bigger than it really was."
            ),
            (
                "What changed by the end?",
                f"By the end, the children were still curious, but now they planned to call for help first. The ending proves it because the room fills with guesses and laughter instead of wobbling."
            ),
        ])
    else:
        qa.extend([
            (
                f"Did the grown-up stop the wobble in time?",
                f"No. {parent.label_word.capitalize()} tried, but the mystery tipped open first and made a silly mess. Even so, nobody was badly hurt, and that let the lesson stay funny instead of frightening."
            ),
            (
                "What was the sound source?",
                f"It was {source.reveal} The surprise is funny because the noise seemed huge, but the cause was small and ridiculous."
            ),
            (
                "What did the children learn?",
                f"They learned that high-up mysteries should stay high until a grown-up helps. Curiosity was not the problem by itself; the unsafe climbing was."
            ),
        ])
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"sound", "wobble", "help"}
    tags |= set(f["source"].tags)
    tags |= set(f["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [n for n, on in (("movable", ent.movable), ("unstable", ent.unstable), ("high", ent.high)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hall_closet",
        source="frog_box",
        support="rolling_chair",
        response="step_stool",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Tess",
        cautioner_gender="girl",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=5,
    ),
    StoryParams(
        place="pantry",
        source="chicken_bin",
        support="step_bin",
        response="lift_down_box",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="father",
        trait="curious",
        delay=0,
        instigator_age=6,
        cautioner_age=5,
        relation="friends",
        trust=4,
    ),
    StoryParams(
        place="laundry_room",
        source="cushion_trunk",
        support="laundry_basket",
        response="lift_down_box",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        parent="mother",
        trait="patient",
        delay=1,
        instigator_age=7,
        cautioner_age=4,
        relation="siblings",
        trust=6,
    ),
    StoryParams(
        place="hall_closet",
        source="chicken_bin",
        support="pillow_stack",
        response="step_stool",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Lulu",
        cautioner_gender="girl",
        parent="mother",
        trait="sensible",
        delay=0,
        instigator_age=4,
        cautioner_age=6,
        relation="siblings",
        trust=3,
    ),
]


def explain_rejection(place: Place, support: Support) -> str:
    return (
        f"(No story: {support.label} does not belong as a plausible reach-helper in {place.label}. "
        f"Choose one of: {', '.join(sorted(place.supports))}.)"
    )


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer response such as: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], SUPPORTS[params.support], params.delay) else "spilled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
allowed_support(P, S) :- place_support(P, S).
sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.
valid(P, Src, S) :- place(P), source(Src), support(S), allowed_support(P, S).

% --- outcome inference -----------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), curiosity_init(CU), A > CU.

severity(Risk + D) :- chosen_support(S), risk(S, Risk), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(spilled) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for support_id in sorted(place.supports):
            lines.append(asp.fact("place_support", place_id, support_id))
    for source_id in SOURCES:
        lines.append(asp.fact("source", source_id))
    for support_id, support in SUPPORTS.items():
        lines.append(asp.fact("support", support_id))
        lines.append(asp.fact("risk", support_id, support.risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curiosity_init", int(CURIOSITY_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
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
        asp.fact("chosen_support", params.support),
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
    for s in range(120):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test produced an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a ginormous silly sound, curiosity, wobbling, and a safer way to solve the mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--support", choices=SUPPORTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="how long the wobble gets before the grown-up reaches the child")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.support:
        place = PLACES[args.place]
        support = SUPPORTS[args.support]
        if not support_allowed(place, args.support):
            raise StoryError(explain_rejection(place, support))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
        and (args.support is None or combo[2] == args.support)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, source_id, support_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    return StoryParams(
        place=place_id,
        source=source_id,
        support=support_id,
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
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.source not in SOURCES:
        raise StoryError(f"Unknown source: {params.source}")
    if params.support not in SUPPORTS:
        raise StoryError(f"Unknown support: {params.support}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if not support_allowed(PLACES[params.place], params.support):
        raise StoryError(explain_rejection(PLACES[params.place], SUPPORTS[params.support]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        PLACES[params.place],
        SOURCES[params.source],
        SUPPORTS[params.support],
        RESPONSES[params.response],
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
        trust=params.trust,
    )

    story = world.render()
    story = story.replace("instigator", params.instigator).replace("cautioner", params.cautioner)
    story = story.replace("parent", PLACES[params.place].label)
    story = story.replace("Milo", params.instigator) if False else story  # never executed; keeps no-op branch explicit

    # Render names cleanly from world-state placeholders.
    story = story.replace("instigator", params.instigator)
    story = story.replace("cautioner", params.cautioner)

    # Replace label-based mentions inserted through display functions at QA time are not needed here.
    # The story itself uses labels stored on the entities, so do a final clean pass:
    story = story.replace(world.get("instigator").id, display_name(world.get("instigator")))
    story = story.replace(world.get("cautioner").id, display_name(world.get("cautioner")))

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, source, support) combos:\n")
        for place, source, support in combos:
            print(f"  {place:13} {source:14} {support}")
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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.source} in {p.place} "
                f"({p.support}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
