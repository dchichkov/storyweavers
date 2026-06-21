#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py
==============================================================

A standalone storyworld about a child carrying a sacred rod through a mythic
night. A proud companion pushes for force, a small guide teaches the wiser way,
and the child must calm a living obstacle before dawn. The stories are built
from simulated state: darkness deepens, fear rises, conflict sharpens, then the
right rhythm or rhyme changes the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py
    python storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py --realm sky_hill
    python storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py --method strike
    python storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py --all --qa
    python storyworlds/worlds/gpt-5.4/rod_rhyme_suspense_conflict_myth.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "queen"}
        male = {"boy", "man", "priest", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return self.label or self.type
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Realm:
    id: str
    place: str
    path: str
    shrine: str
    sky: str
    goal: str
    affords: set[str] = field(default_factory=set)
    ending: str = ""
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
class Threat:
    id: str
    label: str
    intro: str
    block: str
    requires: str
    fear: str
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
class Helper:
    id: str
    label: str
    kind: str
    teaches: str
    entrance: str
    counsel: str
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
class Method:
    id: str
    label: str
    skill: str
    sense: int
    action: str
    chant_a: str
    chant_b: str
    success: str
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
    def __init__(self, realm: Realm) -> None:
        self.realm = realm
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
        clone = World(self.realm)
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


def _r_dread(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    rod = world.get("rod")
    if threat.meters["blocking"] >= THRESHOLD and rod.meters["glow"] < THRESHOLD:
        sig = ("dread",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("path").meters["danger"] += 1
            world.get("hero").memes["fear"] += 1
            world.get("companion").memes["fear"] += 1
            out.append("__dread__")
    return out


def _r_quarrel(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    companion = world.get("companion")
    if companion.memes["push"] >= THRESHOLD and hero.memes["resist"] >= THRESHOLD:
        sig = ("quarrel",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
            companion.memes["conflict"] += 1
            out.append("__quarrel__")
    return out


def _r_open(world: World) -> list[str]:
    out: list[str] = []
    threat = world.get("threat")
    rod = world.get("rod")
    if threat.meters["soothed"] >= THRESHOLD and rod.meters["blessing"] >= THRESHOLD:
        sig = ("open",)
        if sig not in world.fired:
            world.fired.add(sig)
            threat.meters["blocking"] = 0.0
            world.get("path").meters["danger"] = 0.0
            world.get("path").meters["open"] += 1
            world.get("hero").memes["fear"] = 0.0
            world.get("companion").memes["fear"] = 0.0
            world.get("hero").memes["hope"] += 1
            world.get("companion").memes["awe"] += 1
            rod.meters["glow"] += 1
            out.append("__open__")
    return out


CAUSAL_RULES = [
    Rule(name="dread", tag="emotional", apply=_r_dread),
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="open", tag="mythic", apply=_r_open),
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


def valid_combo(realm_id: str, threat_id: str, helper_id: str, method_id: str) -> bool:
    if realm_id not in REALMS or threat_id not in THREATS or helper_id not in HELPERS or method_id not in METHODS:
        return False
    realm = REALMS[realm_id]
    threat = THREATS[threat_id]
    helper = HELPERS[helper_id]
    method = METHODS[method_id]
    return (
        threat.id in realm.affords
        and helper.teaches == threat.requires
        and method.skill == threat.requires
        and method.sense >= SENSE_MIN
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for threat_id in sorted(realm.affords):
            for helper_id, helper in HELPERS.items():
                for method_id, method in METHODS.items():
                    if (
                        helper.teaches == THREATS[threat_id].requires
                        and method.skill == THREATS[threat_id].requires
                        and method.sense >= SENSE_MIN
                    ):
                        combos.append((realm_id, threat_id, helper_id, method_id))
    return sorted(combos)


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def explain_rejection(realm_id: str, threat_id: str, helper_id: str, method_id: str) -> str:
    if realm_id not in REALMS:
        return f"(No story: unknown realm '{realm_id}'.)"
    if threat_id not in THREATS:
        return f"(No story: unknown threat '{threat_id}'.)"
    if helper_id not in HELPERS:
        return f"(No story: unknown helper '{helper_id}'.)"
    if method_id not in METHODS:
        return f"(No story: unknown method '{method_id}'.)"
    realm = REALMS[realm_id]
    threat = THREATS[threat_id]
    helper = HELPERS[helper_id]
    method = METHODS[method_id]
    if threat.id not in realm.affords:
        return (
            f"(No story: {threat.label} does not belong on the path through {realm.place}. "
            f"Pick a threat the realm actually holds.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it treats the sacred rod like a weapon. "
            f"This world prefers wiser mythic solutions such as calm speech, song, or rhythm.)"
        )
    if helper.teaches != threat.requires:
        return (
            f"(No story: {helper.label} does not know how to calm {threat.label}. "
            f"That threat yields only to {threat.requires}.)"
        )
    if method.skill != threat.requires:
        return (
            f"(No story: {threat.label} yields to {threat.requires}, but '{method.label}' "
            f"uses {method.skill}. The answer must match the mythic rule.)"
        )
    return "(No story: that combination breaks the world rule.)"


def predict_opening(world: World, method: Method) -> dict:
    sim = world.copy()
    do_rite(sim, method, narrate=False)
    return {
        "opened": sim.get("path").meters["open"] >= THRESHOLD,
        "danger": sim.get("path").meters["danger"],
        "rod_glow": sim.get("rod").meters["glow"],
    }


def mission_setup(world: World, hero: Entity, companion: Entity, elder: Entity, realm: Realm) -> None:
    hero.memes["duty"] += 1
    companion.memes["pride"] += 1
    world.say(
        f"In the age when hills still listened and rivers still answered, {hero.id} was chosen "
        f"to carry the dawn rod along {realm.path} to {realm.shrine}. {realm.sky}"
    )
    world.say(
        f"{elder.label.capitalize()} placed the slim gold rod in {hero.id}'s hands and said, "
        f'"Take it to {realm.goal} before the last star fades, and morning will rise in peace."'
    )
    world.say(
        f"{companion.id} went too, walking close at {hero.pronoun('possessive')} side. "
        f"{companion.pronoun().capitalize()} wanted to be brave first and loudest."
    )


def enter_path(world: World, hero: Entity, realm: Realm) -> None:
    world.get("path").meters["distance"] += 1
    world.say(
        f"They climbed into {realm.place}. The stones were cold, the wind was thin, "
        f"and every step made the dark seem to lean a little nearer."
    )
    world.say(
        f"{hero.id} held the rod high, but its small light trembled like a candle trapped in a shell."
    )


def awaken_threat(world: World, threat: Threat) -> None:
    ent = world.get("threat")
    ent.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(threat.intro)
    world.say(threat.block)


def argue(world: World, hero: Entity, companion: Entity, method: Method) -> None:
    companion.memes["push"] += 1
    hero.memes["resist"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Stand aside," {companion.id} said. "I will make it obey. We should {method.action}."'
    )
    world.say(
        f'But {hero.id} drew the rod back against {hero.pronoun("possessive")} chest. '
        f'"The rod was given to wake the day, not to start a fight," {hero.pronoun()} said.'
    )


def helper_arrives(world: World, helper: Helper) -> None:
    world.say(helper.entrance)
    world.say(helper.counsel)


def choose_wisdom(world: World, hero: Entity, helper: Helper, method: Method) -> None:
    pred = predict_opening(world, method)
    world.facts["predicted_open"] = pred["opened"]
    world.say(
        f"{hero.id} listened. The dark still pressed close, but {hero.pronoun('possessive')} hands grew steady on the rod."
    )
    if pred["opened"]:
        world.say(
            f"{hero.pronoun().capitalize()} understood that the path would open only if the rod was used with {helper.teaches}, not anger."
        )


def do_rite(world: World, method: Method, narrate: bool = True) -> None:
    rod = world.get("rod")
    threat = world.get("threat")
    rod.meters["blessing"] += 1
    threat.meters["soothed"] += 1
    propagate(world, narrate=False)
    if narrate:
        world.say(
            f"{world.get('hero').id} {method.action}."
        )
        world.say(f'"{method.chant_a}"')
        world.say(f'"{method.chant_b}"')


def resolution(world: World, hero: Entity, companion: Entity, threat: Threat, realm: Realm, method: Method) -> None:
    world.say(method.success.format(threat=threat.label))
    companion.memes["pride"] = 0.0
    companion.memes["respect"] += 1
    world.say(
        f"{companion.id} lowered {companion.pronoun('possessive')} eyes. The quarrel went out of {companion.pronoun('object')} as quickly as a spark in rain."
    )
    world.say(
        f"Together they carried the shining rod to {realm.shrine}, and {realm.ending}"
    )
    world.say(
        f"From then on, people told how {hero.id} won a road through fear not by striking, but by choosing the true sound for the sacred rod."
    )


def tell(
    realm: Realm,
    threat: Threat,
    helper: Helper,
    method: Method,
    hero_name: str = "Iria",
    hero_gender: str = "girl",
    companion_name: str = "Doro",
    companion_gender: str = "boy",
    elder_title: str = "priestess",
) -> World:
    world = World(realm=realm)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    companion = world.add(
        Entity(
            id=companion_name,
            kind="character",
            type=companion_gender,
            role="companion",
            label=companion_name,
            traits=["proud"],
        )
    )
    elder = world.add(Entity(id="Elder", kind="character", type=elder_title, role="elder", label=f"the {elder_title}"))
    world.add(Entity(id="rod", type="artifact", label="rod"))
    world.add(Entity(id="threat", type="threat", label=threat.label))
    world.add(Entity(id="path", type="path", label=realm.path))
    world.add(Entity(id="helper", type=helper.kind, label=helper.label))
    world.facts["predicted_open"] = False

    mission_setup(world, hero, companion, elder, realm)
    world.para()
    enter_path(world, hero, realm)
    awaken_threat(world, threat)
    world.say(threat.fear)
    world.para()
    argue(world, hero, companion, method)
    helper_arrives(world, helper)
    choose_wisdom(world, hero, helper, method)
    world.para()
    do_rite(world, method, narrate=True)
    resolution(world, hero, companion, threat, realm, method)

    world.facts.update(
        hero=hero,
        companion=companion,
        elder=elder,
        rod=world.get("rod"),
        threat_cfg=threat,
        helper_cfg=helper,
        method_cfg=method,
        realm_cfg=realm,
        path_open=world.get("path").meters["open"] >= THRESHOLD,
        conflict=hero.memes["conflict"] >= THRESHOLD or companion.memes["conflict"] >= THRESHOLD,
    )
    return world


REALMS = {
    "sky_hill": Realm(
        id="sky_hill",
        place="Sky Hill, where the slope faced the east",
        path="the stair of blue stones",
        shrine="the Bowl of First Light",
        sky="Above the valley, dawn was waiting behind a shut gate of cloud.",
        goal="the hilltop bowl",
        affords={"echo_gate", "stone_lion"},
        ending="the first red rim of the sun climbed up and painted the sheepfolds gold.",
    ),
    "reed_ford": Realm(
        id="reed_ford",
        place="Reed Ford, where moonlit water braided around black reeds",
        path="the whispering ford",
        shrine="the River Niche of Morning",
        sky="Beyond the marsh, dawn stood hidden under a silver mist.",
        goal="the river niche",
        affords={"river_serpent"},
        ending="the reeds flashed green, and the river gave back the color of morning.",
    ),
    "cavern_pass": Realm(
        id="cavern_pass",
        place="Cavern Pass, where cliffs held the night's breath",
        path="the cave-mouth road",
        shrine="the Stone Cup above the pass",
        sky="Far beyond the dark arch, day waited like a bird inside an egg.",
        goal="the stone cup",
        affords={"echo_gate", "river_serpent"},
        ending="light spilled through the pass in long bright bands, and even the bats tucked themselves away.",
    ),
}

THREATS = {
    "echo_gate": Threat(
        id="echo_gate",
        label="the Echo Gate",
        intro="Ahead of them rose the Echo Gate, a wall of black stone with no hinge and no seam.",
        block="It drank every footstep and gave back a deeper one, as if a giant heart were beating inside the hill.",
        requires="rhyme",
        fear="The waiting made the air feel full of secrets, and neither child could tell whether the next sound would be wind or something waking.",
        tags={"gate", "rhyme"},
    ),
    "river_serpent": Threat(
        id="river_serpent",
        label="the River Serpent",
        intro="At the ford, the water heaved once, twice, and the River Serpent lifted its moon-bright coils.",
        block="Its long back lay across the stepping stones, and each slow breath made the dark water ring.",
        requires="lullaby",
        fear="The serpent did not strike. It only watched, which was worse, because the children had to wait and wonder what it would do.",
        tags={"serpent", "river"},
    ),
    "stone_lion": Threat(
        id="stone_lion",
        label="the Stone Lion",
        intro="On the stair above them crouched the Stone Lion, carved from the hill itself, its eyes shut but not asleep.",
        block="When the rod-light touched its paws, its tail thudded once against the rock, and the whole stair shivered.",
        requires="rhythm",
        fear="For a moment, nobody moved. If the lion opened its eyes, the path might close forever.",
        tags={"lion", "stone"},
    ),
}

HELPERS = {
    "swallow": Helper(
        id="swallow",
        label="a dawn swallow",
        kind="bird",
        teaches="rhyme",
        entrance="Then a dawn swallow skimmed through the dark and settled on the rod, light as a leaf.",
        counsel='"Not blows, little walker," it chirped. "This gate remembers song. Give it a true rhyme, and it will remember morning."',
        tags={"bird", "rhyme"},
    ),
    "turtle": Helper(
        id="turtle",
        label="an old river turtle",
        kind="turtle",
        teaches="lullaby",
        entrance="Out of the reeds came an old river turtle, slow as thought and steady as a drum in the earth.",
        counsel='"Do not challenge the deep one," it murmured. "Water listens best to gentle sleep-words."',
        tags={"turtle", "river"},
    ),
    "cricket": Helper(
        id="cricket",
        label="a cave cricket",
        kind="cricket",
        teaches="rhythm",
        entrance="A cave cricket sprang onto a stone and tapped its bright legs together in a tiny, certain beat.",
        counsel='"The lion hears patterns," it sang. "Match the hill\'s own pulse, and stone will move for you."',
        tags={"cricket", "rhythm"},
    ),
}

METHODS = {
    "chant": Method(
        id="chant",
        label="chant the gate-rhyme",
        skill="rhyme",
        sense=3,
        action="lifted the rod and spoke in a ringing rhyme",
        chant_a="Rod of dawn, show the way.",
        chant_b="Stone, unclose and welcome day.",
        success="At once the sacred rod burned bright, and {threat} softened. A seam of gold ran through the dark, and the way opened.",
        qa_text="used a ringing rhyme with the rod to open the way",
        tags={"rhyme", "chant"},
    ),
    "lullaby": Method(
        id="lullaby",
        label="sing the river-lullaby",
        skill="lullaby",
        sense=3,
        action="lowered the rod toward the water and sang softly",
        chant_a="River, shimmer, coil and sleep.",
        chant_b="Let the road of sunrise keep.",
        success="The sacred rod glowed like warm honey, and {threat} lowered its head. Its coils loosened from the stones, leaving a shining path.",
        qa_text="sang a gentle lullaby over the rod until the water creature grew calm",
        tags={"song", "river"},
    ),
    "tap": Method(
        id="tap",
        label="tap the lion-beat",
        skill="rhythm",
        sense=3,
        action="tapped the rod three times against the stair in a slow brave rhythm",
        chant_a="Hill-heart, hear this steady beat.",
        chant_b="Lion, fold your mighty feet.",
        success="The rod flashed, and {threat} bowed its head. The shivering stair grew still, and a safe line of steps appeared.",
        qa_text="tapped out the right rhythm with the rod until the stone guardian yielded",
        tags={"rhythm", "beat"},
    ),
    "strike": Method(
        id="strike",
        label="strike at the dark",
        skill="force",
        sense=1,
        action="swung the rod like a spear",
        chant_a="",
        chant_b="",
        success="",
        qa_text="tried to hit the danger with the rod",
        tags={"force"},
    ),
}

GIRL_NAMES = ["Iria", "Nera", "Tala", "Mira", "Sela", "Runa"]
BOY_NAMES = ["Doro", "Pelin", "Aren", "Timo", "Leron", "Sami"]


@dataclass
class StoryParams:
    realm: str
    threat: str
    helper: str
    method: str
    hero: str
    hero_gender: str
    companion: str
    companion_gender: str
    elder_title: str
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
    "rod": [
        (
            "What is a rod?",
            "A rod is a straight stick or staff. In myths, a special rod can be a sign of duty or power."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme uses words with matching sounds, like day and way. Rhymes are easy to remember, so stories and songs often use them."
        )
    ],
    "lullaby": [
        (
            "What is a lullaby?",
            "A lullaby is a soft song meant to calm someone and help them rest. Gentle music can make a scary moment feel safer."
        )
    ],
    "rhythm": [
        (
            "What is rhythm?",
            "Rhythm is a steady pattern of sounds or beats. It helps people move, sing, and remember a pattern together."
        )
    ],
    "gate": [
        (
            "Why is a closed gate suspenseful in a story?",
            "A closed gate makes characters stop and wonder what is behind it or how to get through. That waiting feeling builds suspense."
        )
    ],
    "serpent": [
        (
            "What is a serpent?",
            "A serpent is a snake, and in myths it is often very large and magical. Serpents can guard rivers, treasures, or secret places."
        )
    ],
    "lion": [
        (
            "Why do myths use lions as guardians?",
            "Lions feel strong and watchful, so they make good guardian figures in stories. A stone lion can show that even a quiet gate has power."
        )
    ],
}

KNOWLEDGE_ORDER = ["rod", "rhyme", "lullaby", "rhythm", "gate", "serpent", "lion"]


CURATED = [
    StoryParams(
        realm="sky_hill",
        threat="echo_gate",
        helper="swallow",
        method="chant",
        hero="Iria",
        hero_gender="girl",
        companion="Doro",
        companion_gender="boy",
        elder_title="priestess",
    ),
    StoryParams(
        realm="reed_ford",
        threat="river_serpent",
        helper="turtle",
        method="lullaby",
        hero="Mira",
        hero_gender="girl",
        companion="Aren",
        companion_gender="boy",
        elder_title="priest",
    ),
    StoryParams(
        realm="sky_hill",
        threat="stone_lion",
        helper="cricket",
        method="tap",
        hero="Timo",
        hero_gender="boy",
        companion="Nera",
        companion_gender="girl",
        elder_title="priestess",
    ),
    StoryParams(
        realm="cavern_pass",
        threat="echo_gate",
        helper="swallow",
        method="chant",
        hero="Sela",
        hero_gender="girl",
        companion="Leron",
        companion_gender="boy",
        elder_title="priest",
    ),
    StoryParams(
        realm="cavern_pass",
        threat="river_serpent",
        helper="turtle",
        method="lullaby",
        hero="Sami",
        hero_gender="boy",
        companion="Runa",
        companion_gender="girl",
        elder_title="priestess",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    threat = f["threat_cfg"]
    method = f["method_cfg"]
    realm = f["realm_cfg"]
    return [
        f'Write a short myth for a 3-to-5-year-old that includes the word "rod" and a suspenseful conflict on a dark path.',
        f"Tell a mythic story where {hero.id} carries a sacred rod through {realm.place}, argues with {companion.id}, and faces {threat.label}.",
        f"Write a child-facing myth where fear rises, a helper teaches a wiser answer, and the hero uses {method.label} instead of force.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    elder = f["elder"]
    threat = f["threat_cfg"]
    helper = f["helper_cfg"]
    method = f["method_cfg"]
    realm = f["realm_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was chosen to carry a sacred rod, and {companion.id}, who came along on the journey. The {elder.title_word} trusted {hero.id} with a task that mattered to the whole valley."
        ),
        (
            "What was {0} supposed to do with the rod?".format(hero.id),
            f"{hero.id} had to carry the rod to {realm.shrine} before dawn. If the rod arrived there in time, morning would rise in peace."
        ),
        (
            f"Why did the path feel scary?",
            f"The dark path held {threat.label}, which blocked the way and made both children wait and wonder. That uncertainty made the journey feel dangerous before anything even touched them."
        ),
    ]
    if f.get("conflict"):
        qa.append(
            (
                f"What was the conflict between {hero.id} and {companion.id}?",
                f"{companion.id} wanted to force the danger aside, but {hero.id} would not use the sacred rod like a weapon. Their quarrel mattered because the right answer had to fit the old rule of the path, not just their fear."
            )
        )
    qa.append(
        (
            f"How did {hero.id} get past {threat.label}?",
            f"{hero.id} listened to {helper.label} and {method.qa_text}. Because the method matched the guardian's ancient rule, the danger calmed and the way opened."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"The children reached {realm.shrine}, and light returned across the land. The ending shows that wisdom changed more than their feelings: it changed the whole morning sky."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"rod"} | set(f["threat_cfg"].tags) | set(f["method_cfg"].tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, T, H, M) :- realm(R), threat(T), helper(H), method(M),
                     affords(R, T),
                     requires(T, S),
                     teaches(H, S),
                     performs(M, S),
                     sense(M, N), sense_min(K), N >= K.

opened :- chosen_realm(R), chosen_threat(T), chosen_helper(H), chosen_method(M),
          valid(R, T, H, M).
outcome(opened) :- opened.
outcome(blocked) :- not opened.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for threat_id in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, threat_id))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("requires", threat_id, threat.requires))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("teaches", helper_id, helper.teaches))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("performs", method_id, method.skill))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_realm", params.realm),
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_method", params.method),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    outcome_bad = 0
    for params in CURATED:
        if asp_outcome(params) != "opened":
            outcome_bad += 1
    if outcome_bad == 0:
        print(f"OK: ASP outcome says all {len(CURATED)} curated stories open the path.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_bad} curated scenarios were not opened in ASP.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a sacred rod, a dark obstacle, and the wiser mythic answer."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion")
    ap.add_argument("--companion-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-title", choices=["priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and smoke-test story generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and args.method in METHODS and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_rejection(args.realm or "sky_hill", args.threat or "echo_gate", args.helper or "swallow", args.method))
    if args.realm and args.threat and args.helper and args.method:
        if not valid_combo(args.realm, args.threat, args.helper, args.method):
            raise StoryError(explain_rejection(args.realm, args.threat, args.helper, args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.threat is None or combo[1] == args.threat)
        and (args.helper is None or combo[2] == args.helper)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        if args.realm and args.threat and args.helper and args.method:
            raise StoryError(explain_rejection(args.realm, args.threat, args.helper, args.method))
        raise StoryError("(No valid combination matches the given options.)")

    realm_id, threat_id, helper_id, method_id = rng.choice(sorted(combos))
    hero_gender = args.gender or rng.choice(["girl", "boy"])
    companion_gender = args.companion_gender or rng.choice(["girl", "boy"])
    hero = args.hero or _pick_name(rng, hero_gender)
    companion = args.companion or _pick_name(rng, companion_gender, avoid=hero)
    elder_title = args.elder_title or rng.choice(["priestess", "priest"])
    return StoryParams(
        realm=realm_id,
        threat=threat_id,
        helper=helper_id,
        method=method_id,
        hero=hero,
        hero_gender=hero_gender,
        companion=companion,
        companion_gender=companion_gender,
        elder_title=elder_title,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS or params.threat not in THREATS or params.helper not in HELPERS or params.method not in METHODS:
        raise StoryError("(No story: one or more parameters are unknown.)")
    if not valid_combo(params.realm, params.threat, params.helper, params.method):
        raise StoryError(explain_rejection(params.realm, params.threat, params.helper, params.method))

    world = tell(
        realm=REALMS[params.realm],
        threat=THREATS[params.threat],
        helper=HELPERS[params.helper],
        method=METHODS[params.method],
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        companion_name=params.companion,
        companion_gender=params.companion_gender,
        elder_title=params.elder_title,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, threat, helper, method) combos:\n")
        for realm_id, threat_id, helper_id, method_id in combos:
            print(f"  {realm_id:11} {threat_id:14} {helper_id:8} {method_id}")
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
            header = f"### {p.hero} & {p.companion}: {p.realm} / {p.threat} / {p.method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
