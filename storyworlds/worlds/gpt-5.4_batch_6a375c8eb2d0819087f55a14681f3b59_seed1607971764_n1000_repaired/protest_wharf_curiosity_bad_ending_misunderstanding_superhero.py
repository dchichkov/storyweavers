#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/protest_wharf_curiosity_bad_ending_misunderstanding_superhero.py
================================================================================================

A standalone story world for a small "superhero mistake at the wharf" domain.

Premise
-------
Two children visit a wharf while grown-ups hold a protest. One child, dressed
like a superhero, grows curious about a sound or banner near a small boat and
misunderstands it as a cry for help. If the cautious child cannot stop them,
the hero child hops onto the boat, the mooring rope slips free, and the boat
drifts from the wharf.

The world then branches:

* averted: an older, cautious sibling talks the hero child out of it
* contained: a grown-up quickly snags the drifting boat
* lost: the rescue is too weak or too late; the boat bumps the pilings and the
  child's cape is lost in the harbor

The prose is driven by simulated state, not frozen templates. The model also
includes a small ASP twin of its reasonableness gate and outcome logic.
"""

from __future__ import annotations

import argparse
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
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful", "sensible"}


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
    small_vessel: bool = False
    moored: bool = False
    rescue_tool: bool = False
    safe_viewing: bool = False
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
class ProtestTheme:
    id: str
    cause: str
    banner_text: str
    chant: str
    crowd_color: str
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
class MisreadSignal:
    id: str
    seen_as: str
    real_thing: str
    line: str
    on_boat: bool
    confusion: int
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
class Vessel:
    id: str
    label: str
    the: str
    drift: int
    tiny: bool
    rope_text: str
    bump_text: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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


@dataclass
class SafeAid:
    id: str
    label: str
    phrase: str
    use_text: str
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
class StoryParams:
    protest: str
    signal: str
    vessel: str
    response: str
    aid1: str
    aid2: str
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
    sidekick_name: str = "Comet Kid"
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


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    boat = world.entities.get("boat")
    if not boat or boat.meters["drifting"] < THRESHOLD:
        return out
    sig = ("drift", boat.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "wharf" in world.entities:
        world.get("wharf").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__drift__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(signal: MisreadSignal, vessel: Vessel) -> bool:
    return signal.confusion >= 2 and signal.on_boat and vessel.tiny


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def drift_severity(vessel: Vessel, delay: int) -> int:
    return vessel.drift + delay


def is_contained(response: Response, vessel: Vessel, delay: int) -> bool:
    return response.power >= drift_severity(vessel, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    cautioner_older = relation == "siblings" and cautioner_age > instigator_age
    authority = (initial_caution(trait) + 1.0) + (4.0 if cautioner_older else 0.0)
    return cautioner_older and authority > BRAVERY_INIT


def _do_board(world: World, boat: Entity, cape: Entity, narrate: bool = True) -> None:
    boat.meters["drifting"] += 1
    cape.meters["risk"] += 1
    propagate(world, narrate=narrate)


def predict_drift(world: World) -> dict:
    sim = world.copy()
    _do_board(sim, sim.get("boat"), sim.get("cape"), narrate=False)
    return {
        "drifts": sim.get("boat").meters["drifting"] >= THRESHOLD,
        "danger": sim.get("wharf").meters["danger"],
    }


def protest_setup(world: World, a: Entity, b: Entity, theme: ProtestTheme) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"On a bright afternoon, {a.id} and {b.id} walked with their family to the wharf, "
        f"where a protest had filled the boards with {theme.crowd_color}. "
        f"People held signs that said {theme.banner_text!r} and called, {theme.chant!r}."
    )
    world.say(
        f"{a.id} wore a flapping cape and whispered {a.pronoun('possessive')} superhero name, "
        f"{a.attrs['hero_name']}, while {b.id} stayed close like a careful sidekick."
    )


def set_scene(world: World, theme: ProtestTheme, vessel: Vessel) -> None:
    world.say(
        f"Beyond the crowd, {vessel.the} knocked softly against the pilings below the wharf, "
        f"and gulls turned in the windy air."
    )
    world.say(
        f"The whole place felt busy and important, as if even ordinary harbor noises might hide a mission."
    )


def notice_signal(world: World, a: Entity, signal: MisreadSignal, vessel: Vessel) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"Then {a.id} noticed {signal.line} near {vessel.the}. "
        f"From far away, it looked to {a.pronoun('object')} like {signal.seen_as}."
    )
    world.say(
        f"{a.pronoun().capitalize()} stopped so suddenly that {a.pronoun('possessive')} cape snapped in the wind."
    )


def tempt(world: World, a: Entity, signal: MisreadSignal, vessel: Vessel) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'"That boat needs {a.attrs["hero_name"]}!" {a.id} said. '
        f'"If I jump down to {vessel.the}, I can fix it before anyone else sees."'
    )
    world.say("For one excited moment, the mistake felt exactly like the start of a superhero rescue.")


def warn(world: World, b: Entity, a: Entity, signal: MisreadSignal, vessel: Vessel, parent: Entity) -> None:
    pred = predict_drift(world)
    b.memes["caution"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} had already read the dock sign that said visitors had to stay back from the edge."
    world.say(
        f'{b.id} grabbed {a.id}\'s sleeve. "{a.id}, wait. That is only {signal.real_thing}, not a real emergency," '
        f'{b.pronoun()} said. "If you leap onto {vessel.the}, the rope could slip and the boat could drift away. '
        f'Let\'s tell {parent.label_word} instead."{extra}'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"Superheroes do not stand still," {a.id} said, and because {a.pronoun()} was the older sibling, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(f'"Superheroes do not stand still," {a.id} said, and ran for the edge of the wharf.')


def back_down(world: World, a: Entity, b: Entity, parent: Entity, aids: tuple[SafeAid, SafeAid]) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    aid1, aid2 = aids
    world.say(
        f'{a.id} looked at the drop to the water, then at {b.id}, and the pretend rescue suddenly felt less shining and brave. '
        f'"Okay," {a.pronoun()} whispered. "We should ask first."'
    )
    world.say(
        f"{parent.label_word.capitalize()} listened, smiled, and showed them {aid1.phrase} and {aid2.phrase} instead. "
        f"{aid1.use_text.capitalize()}, and {aid2.use_text}."
    )


def launch_drift(world: World, a: Entity, signal: MisreadSignal, vessel: Vessel) -> None:
    boat = world.get("boat")
    cape = world.get("cape")
    _do_board(world, boat, cape, narrate=True)
    world.say(
        f"{a.id} sprang down toward {vessel.the}. The wet mooring rope gave one soft jerk, "
        f"slid free, and suddenly {vessel.the} drifted away from the wharf."
    )
    world.say(
        f"Only then did {a.id} understand that {signal.real_thing} had never been a cry for help at all."
    )


def alarm(world: World, b: Entity, parent: Entity, vessel: Vessel) -> None:
    world.say(f'"{parent.label_word.upper()}! The boat is drifting!" {b.id} shouted.')
    world.say(f"{vessel.The} turned sideways in the tide, and the little rescue game became a real problem.")


def rescue(world: World, parent: Entity, response: Response, vessel: Vessel) -> None:
    boat = world.get("boat")
    boat.meters["drifting"] = 0.0
    world.get("wharf").meters["danger"] = 0.0
    world.say(f"{parent.label_word.capitalize()} ran to the edge and {response.text}.")
    world.say(
        f"In another second {vessel.the} was snug against the posts again, and the whole crowd let out one long breath."
    )


def lesson(world: World, parent: Entity, a: Entity, b: Entity, signal: MisreadSignal, aids: tuple[SafeAid, SafeAid]) -> None:
    aid1, aid2 = aids
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
        kid.memes["fear"] = 0.0
    world.say("For a moment, even the protest grew quiet around them.")
    world.say(
        f'{parent.label_word.capitalize()} knelt beside the children. "I know you wanted to help," '
        f'{parent.pronoun()} said softly. "But being a real hero means checking first. '
        f'You misunderstood {signal.real_thing}, and the wharf is not a place for surprise jumps."'
    )
    world.say(
        f'{b.id} nodded first. Then {a.id} touched {a.pronoun("possessive")} cape and nodded too. '
        f'"Next time we ask first," {a.pronoun()} said.'
    )
    world.say(
        f"After that, {aid1.use_text}, and {aid2.use_text}, so the children could still watch without getting near the edge."
    )


def rescue_fail(world: World, parent: Entity, response: Response, vessel: Vessel) -> None:
    boat = world.get("boat")
    cape = world.get("cape")
    boat.meters["drifting"] += 1
    boat.meters["bumped"] += 1
    cape.meters["lost"] += 1
    cape.meters["wet"] += 1
    world.get("wharf").meters["danger"] += 1
    world.say(f"{parent.label_word.capitalize()} hurried forward and {response.fail}.")
    world.say(vessel.bump_text)
    world.say(
        f"{a_or_the(world.get('cape').label)} tumbled off the seat, flashed once like a small bright fish, and vanished into the dark harbor water."
    )


def sad_ending(world: World, parent: Entity, a: Entity, b: Entity, signal: MisreadSignal, theme: ProtestTheme) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
        kid.memes["fear"] += 1
    world.say(
        f'{parent.label_word.capitalize()} pulled both children back from the edge and held them close. '
        f'"You are safe, and that matters most," {parent.pronoun()} said. "But the cape is gone because we acted on a misunderstanding."'
    )
    world.say(
        f"{a.id}'s throat felt tight. {a.pronoun().capitalize()} had wanted to be brave, yet curiosity had carried "
        f"{a.pronoun('object')} past the safe line of the wharf."
    )
    world.say(
        f"When the protest began to move again, {a.id} walked beside {b.id} with no cape at all. "
        f"{theme.ending_image}."
    )


def safe_after_bad(world: World, parent: Entity, a: Entity, b: Entity, aids: tuple[SafeAid, SafeAid]) -> None:
    aid1, aid2 = aids
    world.say(
        f"Before they left, {parent.label_word} showed them a better way to look. "
        f"{aid1.use_text.capitalize()}, and {aid2.use_text}."
    )
    world.say(
        f"This time {a.id} stayed behind the railing with {b.id}, watching carefully instead of leaping first."
    )


def a_or_the(label: str) -> str:
    if label.startswith(("a ", "an ", "the ")):
        return label
    if label[0].lower() in "aeiou":
        return f"an {label}"
    return f"a {label}"


def tell(
    theme: ProtestTheme,
    signal: MisreadSignal,
    vessel: Vessel,
    aids: tuple[SafeAid, SafeAid],
    response: Response,
    instigator: str = "Nia",
    instigator_gender: str = "girl",
    cautioner: str = "Ben",
    cautioner_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    cautioner_age: int = 4,
    relation: str = "siblings",
    trust: int = 6,
    sidekick_name: str = "Comet Kid",
    pet: str = "",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            traits=["bold"],
            attrs={"relation": relation, "hero_name": sidekick_name},
        )
    )
    b = world.add(
        Entity(
            id=cautioner,
            kind="character",
            type=cautioner_gender,
            role="cautioner",
            age=cautioner_age,
            traits=[trait],
            attrs={"relation": relation},
        )
    )
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="wharf", type="place", label="the wharf"))
    world.add(Entity(id="boat", type="boat", label=vessel.label, small_vessel=vessel.tiny, moored=True))
    world.add(Entity(id="cape", type="cape", label="cape"))
    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)
    b.memes["trust"] = float(trust)
    world.facts["pet"] = pet

    protest_setup(world, a, b, theme)
    set_scene(world, theme, vessel)

    world.para()
    notice_signal(world, a, signal, vessel)
    tempt(world, a, signal, vessel)
    warn(world, b, a, signal, vessel, parent)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)
    if averted:
        world.para()
        back_down(world, a, b, parent, aids)
        outcome = "averted"
        severity = 0
        contained = True
    else:
        defy(world, a, b)
        world.para()
        launch_drift(world, a, signal, vessel)
        alarm(world, b, parent, vessel)
        severity = drift_severity(vessel, delay)
        world.get("boat").meters["severity"] = float(severity)
        contained = is_contained(response, vessel, delay)
        world.para()
        if contained:
            rescue(world, parent, response, vessel)
            lesson(world, parent, a, b, signal, aids)
            outcome = "contained"
        else:
            rescue_fail(world, parent, response, vessel)
            sad_ending(world, parent, a, b, signal, theme)
            safe_after_bad(world, parent, a, b, aids)
            outcome = "lost"

    world.facts.update(
        instigator=a,
        cautioner=b,
        parent=parent,
        protest=theme,
        signal_cfg=signal,
        vessel_cfg=vessel,
        response=response,
        aids=aids,
        outcome=outcome,
        severity=severity,
        delay=delay,
        relation=relation,
        drifted=world.get("boat").meters["drifting"] >= THRESHOLD or outcome in {"contained", "lost"},
        cape_lost=world.get("cape").meters["lost"] >= THRESHOLD,
    )
    return world


PROTESTS = {
    "save_lighthouse": ProtestTheme(
        id="save_lighthouse",
        cause="saving the old lighthouse",
        banner_text="SAVE OUR LIGHT",
        chant="Keep the light bright!",
        crowd_color="blue scarves and silver signs",
        ending_image="The chant still rolled over the water, but it sounded smaller without the cape",
        tags={"protest", "lighthouse"},
    ),
    "clean_harbor": ProtestTheme(
        id="clean_harbor",
        cause="cleaning the harbor",
        banner_text="CLEAN WATER FOR ALL",
        chant="Clean water, safe shore!",
        crowd_color="green posters and bright rain coats",
        ending_image="The gulls cried above the water while the protest signs bobbed like slow waves",
        tags={"protest", "harbor"},
    ),
    "protect_birds": ProtestTheme(
        id="protect_birds",
        cause="protecting the nesting birds by the docks",
        banner_text="SAFE NESTS, SAFE SKY",
        chant="Let the terns rest!",
        crowd_color="yellow flags and bird pictures",
        ending_image="The signs for the birds fluttered overhead, and the empty space behind the child's shoulders felt very plain",
        tags={"protest", "birds"},
    ),
}

SIGNALS = {
    "banner": MisreadSignal(
        id="banner",
        seen_as="a trapped person waving for help",
        real_thing="a protest banner tied to the boat",
        line="a long red protest banner whipping in the wind",
        on_boat=True,
        confusion=3,
        tags={"banner", "protest"},
    ),
    "whistle": MisreadSignal(
        id="whistle",
        seen_as="a captain's danger whistle",
        real_thing="a protest whistle shrilling from the boat deck",
        line="a shrill protest whistle peeping over and over",
        on_boat=True,
        confusion=2,
        tags={"whistle", "protest"},
    ),
    "megaphone": MisreadSignal(
        id="megaphone",
        seen_as="a sailor calling for rescue",
        real_thing="a protester speaking through a megaphone on the boat",
        line="a voice through a protest megaphone bouncing off the water",
        on_boat=True,
        confusion=2,
        tags={"megaphone", "protest"},
    ),
    "dock_sign": MisreadSignal(
        id="dock_sign",
        seen_as="a secret villain code",
        real_thing="an old warning sign on the dock",
        line="a rusty warning sign clacking against a post",
        on_boat=False,
        confusion=1,
        tags={"sign"},
    ),
}

VESSELS = {
    "dinghy": Vessel(
        id="dinghy",
        label="dinghy",
        the="the dinghy",
        drift=1,
        tiny=True,
        rope_text="the thin dinghy rope had only been looped once around the post",
        bump_text="The dinghy bumped the nearest piling with a hollow thunk",
        tags={"boat", "dinghy", "rope"},
    ),
    "skiff": Vessel(
        id="skiff",
        label="skiff",
        the="the skiff",
        drift=2,
        tiny=True,
        rope_text="the skiff's wet rope was slick with harbor spray",
        bump_text="The skiff knocked hard against the pilings, and a splash leapt up beside it",
        tags={"boat", "skiff", "rope"},
    ),
    "workboat": Vessel(
        id="workboat",
        label="workboat",
        the="the workboat",
        drift=3,
        tiny=True,
        rope_text="the heavier workboat strained against a frayed knot",
        bump_text="The workboat slammed sideways into the posts with a bang that made the gulls rise",
        tags={"boat", "workboat", "rope"},
    ),
    "ferry": Vessel(
        id="ferry",
        label="ferry",
        the="the ferry",
        drift=4,
        tiny=False,
        rope_text="the big ferry was held by thick harbor lines",
        bump_text="The ferry's side boomed against the dock",
        tags={"boat", "ferry"},
    ),
}

RESPONSES = {
    "boat_hook": Response(
        id="boat_hook",
        sense=3,
        power=3,
        text="caught the rope with a long boat hook and drew the drifting boat back in hand over hand",
        fail="reached with a boat hook, but the rope slid beyond the hook's tip",
        qa_text="used a boat hook to catch the rope and pull the boat back",
        tags={"boat_hook", "rope", "rescue"},
    ),
    "throw_line": Response(
        id="throw_line",
        sense=3,
        power=2,
        text="threw a line across the bow, caught it on the second toss, and pulled the boat close again",
        fail="threw a line, but the current spun the boat away before the rope could catch",
        qa_text="threw a line and pulled the boat back to the wharf",
        tags={"rope", "rescue"},
    ),
    "run_planks": Response(
        id="run_planks",
        sense=2,
        power=1,
        text="ran along the planks, leaned low, and grabbed the trailing rope just in time",
        fail="ran along the planks, but the rope dipped into the water before anyone could grab it",
        qa_text="ran along the wharf and grabbed the trailing rope",
        tags={"rescue", "rope"},
    ),
    "jump_in": Response(
        id="jump_in",
        sense=1,
        power=1,
        text="jumped straight into the harbor and shoved the boat back by hand",
        fail="splashed into the harbor, but the boat drifted farther away",
        qa_text="jumped into the harbor to push the boat back",
        tags={"harbor", "rescue"},
    ),
}

SAFE_AIDS = {
    "binoculars": SafeAid(
        id="binoculars",
        label="binoculars",
        phrase="a pair of harbor binoculars",
        use_text="they looked from far back with the binoculars",
        tags={"binoculars", "safe_view"},
    ),
    "visitor_badge": SafeAid(
        id="visitor_badge",
        label="visitor badge",
        phrase="a bright orange visitor badge for the safe railing area",
        use_text="the badge let them stand in the marked viewing place",
        tags={"badge", "safe_view"},
    ),
    "map": SafeAid(
        id="map",
        label="harbor map",
        phrase="a folded harbor map",
        use_text="the map showed which boats belonged to workers and where visitors had to stop",
        tags={"map", "wharf"},
    ),
    "guide": SafeAid(
        id="guide",
        label="harbor guide",
        phrase="a patient harbor guide with a striped cap",
        use_text="the guide answered questions before anyone had to guess",
        tags={"guide", "wharf"},
    ),
}

GIRL_NAMES = ["Nia", "Ava", "Maya", "Zoe", "Lina", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo", "Noah", "Eli", "Sam"]
TRAITS = ["careful", "curious", "steady", "thoughtful", "sensible", "bright"]
HERO_NAMES = ["Comet Kid", "Captain Star", "Sky Flash", "Storm Cape", "Moon Bolt"]
PETS = ["the puppy", "the little dog", "the cat", ""]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for protest_id in PROTESTS:
        for signal_id, signal in SIGNALS.items():
            for vessel_id, vessel in VESSELS.items():
                if hazard_at_risk(signal, vessel):
                    combos.append((protest_id, signal_id, vessel_id))
    return combos


KNOWLEDGE = {
    "protest": [
        (
            "What is a protest?",
            "A protest is when people gather to show that they care strongly about something and want others to listen. They might carry signs, chant, or march together.",
        )
    ],
    "wharf": [
        (
            "What is a wharf?",
            "A wharf is a strong walkway by the water where boats can tie up and people can load or watch them. It can be slippery and busy, so children need to stay back from the edge.",
        )
    ],
    "boat": [
        (
            "Why can a small boat drift away?",
            "A small boat can drift if its rope slips loose, because water and wind keep pushing it. That is why boats are tied carefully at a wharf.",
        )
    ],
    "rope": [
        (
            "What does a mooring rope do?",
            "A mooring rope keeps a boat fastened to a post or dock. If the rope slips free, the boat can move away with the tide.",
        )
    ],
    "boat_hook": [
        (
            "What is a boat hook?",
            "A boat hook is a long pole with a hook on the end. Grown-ups use it to catch a rope or pull a boat closer without climbing in.",
        )
    ],
    "binoculars": [
        (
            "What are binoculars for?",
            "Binoculars help you see faraway things without walking closer. They are useful when you want a better look from a safe place.",
        )
    ],
    "megaphone": [
        (
            "What does a megaphone do?",
            "A megaphone makes a person's voice louder so a crowd can hear. A loud voice is not always an emergency.",
        )
    ],
    "whistle": [
        (
            "Why do people use whistles?",
            "Whistles make a sharp sound that carries far. People might use them to get attention in a game, at work, or during a protest.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a big piece of cloth with words or pictures on it. People use banners to share a message so others can see it from far away.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something means one thing, but it really means another. Asking a question can stop a misunderstanding from growing into a problem.",
        )
    ],
}
KNOWLEDGE_ORDER = ["protest", "wharf", "misunderstanding", "boat", "rope", "boat_hook", "binoculars", "banner", "megaphone", "whistle"]


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
    protest = f["protest"]
    signal = f["signal_cfg"]
    vessel = f["vessel_cfg"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a short superhero story for a 3-to-5-year-old that includes the words "protest" and "wharf". A child misunderstands {signal.real_thing} as danger and jumps toward {vessel.the}.',
            f"Tell a cautionary story where curious {a.id} thinks {signal.seen_as}, but the mistake leads to a bad ending at the wharf and a lost cape.",
            f'Write a child-facing story with curiosity, misunderstanding, and a sad consequence, set during a protest about {protest.cause}.',
        ]
    if outcome == "contained":
        return [
            f'Write a superhero-flavored story for a 3-to-5-year-old using the words "protest" and "wharf". A child mistakes {signal.real_thing} for danger, and a grown-up quickly fixes the problem.',
            f"Tell a gentle cautionary story where {a.id} tries to be a hero at the wharf during a protest, but learns that real heroes ask first.",
            f"Write a story with a bright beginning, a misunderstanding in the middle, and a safe ending after a quick rescue.",
        ]
    return [
        f'Write a short superhero story for a 3-to-5-year-old using the words "protest" and "wharf". One child wants to leap into action, but another child stops the mistake.',
        f"Tell a near-miss story where {a.id} almost turns curiosity into trouble at the wharf, yet listens in time.",
        f"Write a story that teaches children to ask questions before acting brave.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    parent = f["parent"]
    protest = f["protest"]
    signal = f["signal_cfg"]
    vessel = f["vessel_cfg"]
    response = f["response"]
    aid1, aid2 = f["aids"]
    pair = pair_noun(a, b, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, who went to the wharf during a protest. {a.id} was pretending to be a superhero, and {b.id} tried to keep things safe.",
        ),
        (
            "What was happening at the wharf?",
            f"People were holding a protest about {protest.cause} and carrying signs. The crowd, noise, and wind made the place feel busy and dramatic.",
        ),
        (
            f"What did {a.id} misunderstand?",
            f"{a.id} mistook {signal.real_thing} for {signal.seen_as}. That misunderstanding made the moment feel like a superhero emergency when it was not one.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did {b.id} stop the mistake?",
                f"{b.id} warned that the rope could slip if {a.id} jumped onto {vessel.the}, and {a.id} finally listened. Then {pw} showed them {aid1.phrase} and {aid2.phrase}, so they could look safely instead.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the children staying back from the edge and watching from a proper place. The ending proves they changed, because they used questions and safe tools instead of a sudden leap.",
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                f"What happened when {a.id} jumped toward {vessel.the}?",
                f"The mooring rope slipped free and the boat drifted away from the wharf. That is when {a.id} realized the whole rescue idea had begun with a misunderstanding.",
            )
        )
        qa.append(
            (
                f"How did {pw} fix the problem?",
                f"{pw.capitalize()} {response.qa_text}. The quick rescue mattered because the boat was already drifting and the wharf had become dangerous.",
            )
        )
        qa.append(
            (
                f"What did {a.id} learn?",
                f"{a.id} learned that wanting to help is not enough by itself. Real heroes check what is really happening first, especially in a busy place like a wharf.",
            )
        )
    else:
        qa.append(
            (
                f"Why was the ending sad?",
                f"The rescue was too weak or too late, so {vessel.the} bumped the pilings and {a.id}'s cape fell into the harbor and was lost. The sad part came from acting on a misunderstanding instead of asking a grown-up first.",
            )
        )
        qa.append(
            (
                f"Was everyone safe?",
                f"Yes, everyone was safe because {pw} pulled the children back from the edge. Even so, the lost cape made the mistake feel real, and that is why the ending still felt bad.",
            )
        )
        qa.append(
            (
                f"What changed by the last scene?",
                f"By the end, {a.id} stopped trying to leap first and stayed behind the railing with {b.id}. The story proves the change by showing the children watching carefully from a safe place instead of charging ahead.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"protest", "wharf", "misunderstanding"}
    tags |= set(f["signal_cfg"].tags)
    tags |= set(f["vessel_cfg"].tags)
    tags |= set(f["response"].tags)
    for aid in f["aids"]:
        tags |= set(aid.tags)
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
        flags = []
        if e.small_vessel:
            flags.append("small_vessel")
        if e.moored:
            flags.append("moored")
        if e.rescue_tool:
            flags.append("rescue_tool")
        if e.safe_viewing:
            flags.append("safe_viewing")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        protest="save_lighthouse",
        signal="banner",
        vessel="skiff",
        response="boat_hook",
        aid1="binoculars",
        aid2="guide",
        instigator="Nia",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=6,
        sidekick_name="Captain Star",
        pet="the puppy",
    ),
    StoryParams(
        protest="clean_harbor",
        signal="whistle",
        vessel="dinghy",
        response="throw_line",
        aid1="map",
        aid2="binoculars",
        instigator="Max",
        instigator_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=0,
        instigator_age=5,
        cautioner_age=5,
        relation="friends",
        trust=4,
        sidekick_name="Sky Flash",
        pet="",
    ),
    StoryParams(
        protest="protect_birds",
        signal="megaphone",
        vessel="workboat",
        response="run_planks",
        aid1="visitor_badge",
        aid2="guide",
        instigator="Ella",
        instigator_gender="girl",
        cautioner="Leo",
        cautioner_gender="boy",
        parent="mother",
        trait="steady",
        delay=2,
        instigator_age=6,
        cautioner_age=4,
        relation="siblings",
        trust=5,
        sidekick_name="Moon Bolt",
        pet="the cat",
    ),
    StoryParams(
        protest="save_lighthouse",
        signal="banner",
        vessel="dinghy",
        response="boat_hook",
        aid1="map",
        aid2="guide",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="Ruby",
        cautioner_gender="girl",
        parent="father",
        trait="careful",
        delay=0,
        instigator_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=3,
        sidekick_name="Storm Cape",
        pet="",
    ),
]


def explain_rejection(signal: MisreadSignal, vessel: Vessel) -> str:
    if not signal.on_boat:
        return (
            f"(No story: {signal.real_thing} is not on a boat, so jumping aboard would not honestly follow from the misunderstanding. "
            f"Pick a signal tied to or coming from a vessel.)"
        )
    if not vessel.tiny:
        return (
            f"(No story: {vessel.the} is too large and securely tied for this small drift story. "
            f"Pick a dinghy, skiff, or workboat instead.)"
        )
    return "(No story: this signal and vessel do not make a believable drifting-boat problem.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the more sensible responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "contained" if is_contained(RESPONSES[params.response], VESSELS[params.vessel], params.delay) else "lost"


ASP_RULES = r"""
hazard(S, V) :- signal(S), vessel(V), on_boat(S), confusable(S, C), C >= 2, tiny(V).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(P, S, V) :- protest(P), hazard(S, V).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), bravery_init(BR), A > BR.

severity(D + DL) :- chosen_vessel(V), drift(V, D), delay(DL).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(lost) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROTESTS:
        lines.append(asp.fact("protest", pid))
    for sid, signal in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("confusable", sid, signal.confusion))
        if signal.on_boat:
            lines.append(asp.fact("on_boat", sid))
    for vid, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        lines.append(asp.fact("drift", vid, vessel.drift))
        if vessel.tiny:
            lines.append(asp.fact("tiny", vid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
    for tr in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", tr))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_vessel", params.vessel),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "wharf" not in sample.story or "protest" not in sample.story:
        raise StoryError("Smoke test failed: generated story missing required content.")
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    _ = sample.to_json()


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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(150):
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
        _smoke_test()
        print("OK: smoke test generate/emit/json passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero misunderstanding at a protest on the wharf."
    )
    ap.add_argument("--protest", choices=PROTESTS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the drifting boat gets")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.signal and args.vessel:
        signal = SIGNALS[args.signal]
        vessel = VESSELS[args.vessel]
        if not hazard_at_risk(signal, vessel):
            raise StoryError(explain_rejection(signal, vessel))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.protest is None or c[0] == args.protest)
        and (args.signal is None or c[1] == args.signal)
        and (args.vessel is None or c[2] == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    protest_id, signal_id, vessel_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    aid1, aid2 = rng.sample(sorted(SAFE_AIDS), 2)
    instigator, ig = _pick_kid(rng)
    cautioner, cg = _pick_kid(rng, avoid=instigator)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, cautioner_age = rng.sample([3, 4, 5, 6, 7], 2)
    trust = rng.randint(0, 10)
    sidekick_name = rng.choice(HERO_NAMES)
    pet = rng.choice(PETS)
    return StoryParams(
        protest=protest_id,
        signal=signal_id,
        vessel=vessel_id,
        response=response_id,
        aid1=aid1,
        aid2=aid2,
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
        sidekick_name=sidekick_name,
        pet=pet,
    )


def _lookup(mapping: dict, key: str, field_name: str):
    if key not in mapping:
        raise StoryError(f"(No story: unknown {field_name} {key!r}.)")
    return mapping[key]


def generate(params: StoryParams) -> StorySample:
    theme = _lookup(PROTESTS, params.protest, "protest")
    signal = _lookup(SIGNALS, params.signal, "signal")
    vessel = _lookup(VESSELS, params.vessel, "vessel")
    response = _lookup(RESPONSES, params.response, "response")
    aid1 = _lookup(SAFE_AIDS, params.aid1, "aid")
    aid2 = _lookup(SAFE_AIDS, params.aid2, "aid")
    if not hazard_at_risk(signal, vessel):
        raise StoryError(explain_rejection(signal, vessel))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    world = tell(
        theme=theme,
        signal=signal,
        vessel=vessel,
        aids=(aid1, aid2),
        response=response,
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
        sidekick_name=params.sidekick_name,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (protest, signal, vessel) combos:\n")
        for protest_id, signal_id, vessel_id in combos:
            print(f"  {protest_id:16} {signal_id:10} {vessel_id}")
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
            header = f"### {p.instigator} & {p.cautioner}: {p.signal} near {p.vessel} ({p.protest}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
