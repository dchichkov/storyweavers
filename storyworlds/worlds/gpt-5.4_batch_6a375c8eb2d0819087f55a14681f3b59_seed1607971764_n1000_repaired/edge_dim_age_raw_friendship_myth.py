#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py
==============================================================

A standalone storyworld in a small mythic domain: two children set out as
friends to return a sacred object, face one fitting obstacle on the way, and
learn that friendship is stronger than pride.

The story is driven by simulated state rather than frozen templates. Physical
meters track danger, progress, and whether the sacred task is completed;
emotional memes track trust, fear, pride, gratitude, and friendship. A helper's
offer only counts as a valid story when it actually fits the obstacle.

Run it
------
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py --realm cliff_path --hazard wind_gap --aid rope
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py --hazard dark_cave --aid raft
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py --all
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/edge_dim_age_raw_friendship_myth.py --verify
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
        female = {"girl", "woman", "goddess"}
        male = {"boy", "man", "god"}
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
class Realm:
    id: str
    opening: str
    path_name: str
    shrine_name: str
    atmosphere: str
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
class Hazard:
    id: str
    label: str
    scene: str
    threat: str
    overcome_by: set[str] = field(default_factory=set)
    severity: int = 1
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
class Aid:
    id: str
    label: str
    phrase: str
    works_on: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
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
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
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


def _r_danger_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("hazard_active") and world.get("path").meters["danger"] >= THRESHOLD:
        sig = ("danger_fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            for eid in ("hero", "friend"):
                world.get(eid).memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_help_deepens_friendship(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["accepted_help"] >= THRESHOLD:
        sig = ("friendship",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["gratitude"] += 1
            hero.memes["friendship"] += 1
            friend.memes["friendship"] += 1
            out.append("__friendship__")
    return out


def _r_relic_restored(world: World) -> list[str]:
    out: list[str] = []
    if world.get("path").meters["crossed"] >= THRESHOLD and world.get("relic").meters["carried"] >= THRESHOLD:
        sig = ("restored",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("relic").meters["restored"] += 1
            out.append("__restored__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="danger_fear", tag="emotional", apply=_r_danger_fear),
    Rule(name="help_deepens_friendship", tag="social", apply=_r_help_deepens_friendship),
    Rule(name="relic_restored", tag="physical", apply=_r_relic_restored),
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


REALMS = {
    "cliff_path": Realm(
        id="cliff_path",
        opening="In the old age when hills still listened, two young friends lived below the high red cliffs.",
        path_name="the edge-dim cliff path",
        shrine_name="the little shrine of dawn",
        atmosphere="Below them the valley slept, and a raw wind moved through the grass.",
        tags={"myth", "cliff"},
    ),
    "reed_marsh": Realm(
        id="reed_marsh",
        opening="In the old age when cranes carried prayers between earth and sky, two young friends lived beside the reed marsh.",
        path_name="the moon-water trail",
        shrine_name="the stone pool of dawn",
        atmosphere="Mist lay low on the water, and the marsh smelled green and raw.",
        tags={"myth", "marsh"},
    ),
    "cedar_hollow": Realm(
        id="cedar_hollow",
        opening="In the old age when cedar trees were said to remember names, two young friends lived near a hollow in the hills.",
        path_name="the path under the cedars",
        shrine_name="the spring-house of dawn",
        atmosphere="The branches made an edge-dim roof above them, and raw sap shone on the bark.",
        tags={"myth", "forest"},
    ),
}

HAZARDS = {
    "wind_gap": Hazard(
        id="wind_gap",
        label="wind gap",
        scene="a broken step where the path opened over empty air",
        threat="the raw wind rushed up from the rocks and made the narrow way tremble",
        overcome_by={"rope", "staff"},
        severity=2,
        tags={"wind", "cliff"},
    ),
    "flooded_ford": Hazard(
        id="flooded_ford",
        label="flooded ford",
        scene="a ford gone wide and cold with mountain water",
        threat="the current tugged hard at ankles and would sweep small feet sideways",
        overcome_by={"raft", "rope"},
        severity=2,
        tags={"water", "river"},
    ),
    "dark_cave": Hazard(
        id="dark_cave",
        label="dark cave",
        scene="a cave-mouth dark as a closed eye",
        threat="inside, the stones drank the light and turned every step unsure",
        overcome_by={"lantern", "song"},
        severity=1,
        tags={"dark", "cave"},
    ),
    "thorn_gate": Hazard(
        id="thorn_gate",
        label="thorn gate",
        scene="a wall of thorn vines knotted across the old way",
        threat="the hooked branches caught sleeves and skin and would not easily let go",
        overcome_by={"staff", "song"},
        severity=1,
        tags={"thorn", "forest"},
    ),
}

AIDS = {
    "rope": Aid(
        id="rope",
        label="rope",
        phrase="a coil of rope woven from river grass",
        works_on={"wind_gap", "flooded_ford"},
        action_text="unwound the rope, tied one end fast, and let the other friend cross while holding the line",
        qa_text="used a rope so one child could hold fast while the other crossed",
        tags={"rope"},
    ),
    "raft": Aid(
        id="raft",
        label="raft",
        phrase="a little reed raft",
        works_on={"flooded_ford"},
        action_text="pushed the reed raft into the water and steadied it until both children reached the far bank",
        qa_text="used a little reed raft to float across the water together",
        tags={"raft"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a shell lantern with a patient flame",
        works_on={"dark_cave"},
        action_text="lifted the shell lantern high, and its small flame showed each safe stone and bend",
        qa_text="held up a lantern so the safe stones could be seen",
        tags={"lantern"},
    ),
    "song": Aid(
        id="song",
        label="song",
        phrase="the old bridge-song their grandmothers knew",
        works_on={"dark_cave", "thorn_gate"},
        action_text="began the old bridge-song, and the frightened place seemed to loosen as their two voices moved together",
        qa_text="used an old song that helped them stay steady and brave together",
        tags={"song"},
    ),
    "staff": Aid(
        id="staff",
        label="staff",
        phrase="a smooth ash staff",
        works_on={"wind_gap", "thorn_gate"},
        action_text="set the ash staff before each careful step and pressed the thorny branches or loose earth away from their legs",
        qa_text="used a sturdy staff to test the way and keep the danger back",
        tags={"staff"},
    ),
}

RELICS = {
    "sun_drop": Relic(
        id="sun_drop",
        label="sun-drop",
        phrase="a sun-drop seed",
        glow="It held a warm gold light as if morning had curled up inside it.",
        tags={"light", "seed"},
    ),
    "rain_bell": Relic(
        id="rain_bell",
        label="rain bell",
        phrase="a rain bell of pale silver",
        glow="When it moved, it gave one soft note, like a tiny cloud singing.",
        tags={"bell", "rain"},
    ),
    "star_shell": Relic(
        id="star_shell",
        label="star shell",
        phrase="a star shell no bigger than a plum",
        glow="Its inside shone blue-white, like moonlight hidden in milk.",
        tags={"shell", "star"},
    ),
}


def aid_fits(hazard: Hazard, aid: Aid) -> bool:
    return hazard.id in aid.works_on and aid.id in hazard.overcome_by


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id in REALMS:
        for hazard_id, hazard in HAZARDS.items():
            for aid_id, aid in AIDS.items():
                if aid_fits(hazard, aid):
                    for relic_id in RELICS:
                        combos.append((realm_id, hazard_id, aid_id, relic_id))
    return combos


@dataclass
class StoryParams:
    realm: str
    hazard: str
    aid: str
    relic: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    parent_style: str
    pride: int = 2
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


GIRL_NAMES = ["Lila", "Mira", "Nara", "Suri", "Tama", "Asha", "Ira", "Daya"]
BOY_NAMES = ["Tarin", "Milo", "Rin", "Kavi", "Solen", "Aren", "Pavi", "Niko"]
TRAITS = ["gentle", "bright", "careful", "quick", "steady", "kind"]

KNOWLEDGE = {
    "rope": [
        (
            "What is a rope for?",
            "A rope helps people hold on, pull, or tie things safely together. It is useful when a path is steep or water is strong.",
        )
    ],
    "raft": [
        (
            "What is a raft?",
            "A raft is a small floating platform that can carry people across water. It stays on top of the water instead of walking through it.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see in the dark. A safe light helps you choose each step carefully.",
        )
    ],
    "song": [
        (
            "How can a song help someone?",
            "A song can help people keep time, stay calm, and feel less alone. Singing together can make two people braver than one.",
        )
    ],
    "staff": [
        (
            "What is a walking staff for?",
            "A walking staff helps test the ground and steady your body. It can make a narrow or rough path safer.",
        )
    ],
    "friendship": [
        (
            "Why does friendship matter on a hard journey?",
            "A friend can share courage, tools, and good ideas. When people trust each other, they can solve problems together instead of facing them alone.",
        )
    ],
    "myth": [
        (
            "What is a myth?",
            "A myth is a story told in an old, wonder-filled way. It often explains why people remember a place, a promise, or a custom.",
        )
    ],
}
KNOWLEDGE_ORDER = ["myth", "friendship", "rope", "raft", "lantern", "song", "staff"]


def predict_crossing(world: World, hazard_id: str, aid_id: str, accept_help: bool) -> dict:
    sim = world.copy()
    sim.facts["hazard_active"] = True
    sim.get("path").meters["danger"] = float(HAZARDS[hazard_id].severity)
    propagate(sim, narrate=False)
    if accept_help:
        sim.get("hero").memes["accepted_help"] += 1
        sim.get("path").meters["crossed"] += 1
    else:
        sim.get("hero").meters["stuck"] += 1
    propagate(sim, narrate=False)
    return {
        "crossed": sim.get("path").meters["crossed"] >= THRESHOLD,
        "fear": sim.get("hero").memes["fear"],
        "restored": sim.get("relic").meters["restored"] >= THRESHOLD,
    }


def introduce(world: World, realm: Realm, hero: Entity, friend: Entity, relic: Relic) -> None:
    world.say(realm.opening)
    world.say(
        f"Their names were {hero.id} and {friend.id}, and in those days people said their friendship was as even as two hands carrying one bowl."
    )
    world.say(
        f"One dusk they found {relic.phrase} beside a field altar, where it did not belong. {relic.glow}"
    )
    world.say(
        f"An elder had once taught them that any sacred thing found on common ground must be returned before sunrise to {realm.shrine_name}."
    )
    world.say(realm.atmosphere)


def vow(world: World, hero: Entity, friend: Entity, realm: Realm, relic: Relic) -> None:
    world.get("relic").meters["carried"] = 1.0
    hero.memes["duty"] += 1
    friend.memes["duty"] += 1
    world.say(
        f'"We will carry the {relic.label} there together," said {hero.id}. "{realm.path_name.capitalize()} is the shortest way."'
    )
    world.say(
        f'{friend.id} nodded and walked beside {hero.pronoun("object")}.'
    )


def meet_hazard(world: World, hazard: Hazard, realm: Realm) -> None:
    world.facts["hazard_active"] = True
    world.get("path").meters["danger"] = float(hazard.severity)
    propagate(world, narrate=False)
    world.say(
        f"But when they reached {realm.path_name}, they found {hazard.scene}. {hazard.threat}."
    )


def hero_pushes_on(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'{hero.id} drew in a breath and said, "I am not small. I can do this alone."'
    )


def offer_help(world: World, friend: Entity, aid: Aid, hazard: Hazard) -> None:
    friend.memes["care"] += 1
    world.say(
        f'Yet {friend.id} touched {friend.pronoun("possessive")} friend\'s sleeve and showed {aid.phrase}. '
        f'"Then do not do it alone," {friend.pronoun()} said. "This {aid.label} was made for a {hazard.label}."'
    )


def refuse_help(world: World, hero: Entity, friend: Entity, hazard: Hazard) -> None:
    hero.meters["stuck"] += 1
    world.say(
        f'{hero.id} stepped forward without waiting. At once the {hazard.label} answered back, and {hero.pronoun()} froze.'
    )
    world.say(
        f"{hero.pronoun().capitalize()} was not hurt, but the way before {hero.pronoun('object')} felt too uncertain to trust."
    )


def accept_help(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    hero.memes["accepted_help"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} looked at {friend.id}, and pride loosened inside {hero.pronoun('object')}."
    )
    world.say(
        f'"Forgive me," {hero.pronoun()} said. "A hard road is not made lighter by pretending to walk it alone."'
    )
    world.say(
        f"{friend.id} smiled and came close beside {hero.pronoun('object')}."
    )


def use_aid(world: World, hero: Entity, friend: Entity, aid: Aid) -> None:
    world.get("path").meters["crossed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {friend.id} {aid.action_text}."
    )
    world.say(
        f"Step by step, with shoulders nearly touching, the two friends passed the danger together."
    )


def restore_relic(world: World, hero: Entity, friend: Entity, realm: Realm, relic: Relic) -> None:
    propagate(world, narrate=False)
    world.say(
        f"Beyond the hard place stood {realm.shrine_name}, quiet under the paling sky."
    )
    world.say(
        f"{hero.id} and {friend.id} laid the {relic.label} on the altar stone together."
    )
    world.say(
        "At once the morning light widened, as if the world itself had taken a calm breath."
    )


def closing_lesson(world: World, hero: Entity, friend: Entity, realm: Realm) -> None:
    world.say(
        f"From that day on, people of that valley said that the surest road through fear was not pride, but friendship."
    )
    world.say(
        f"And when children walked {realm.path_name} in later years, they walked it in pairs and remembered {hero.id} and {friend.id}."
    )


def tell(
    realm: Realm,
    hazard: Hazard,
    aid: Aid,
    relic: Relic,
    hero_name: str = "Lila",
    hero_gender: str = "girl",
    friend_name: str = "Tarin",
    friend_gender: str = "boy",
    parent_style: str = "elder",
    pride: int = 2,
    trust: int = 6,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=["young", "dutiful"],
            attrs={"parent_style": parent_style},
        )
    )
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=friend_gender,
            role="friend",
            traits=["steady", "kind"],
            attrs={"parent_style": parent_style},
        )
    )
    path = world.add(
        Entity(
            id="path",
            type="path",
            label=realm.path_name,
            attrs={},
        )
    )
    relic_ent = world.add(
        Entity(
            id="relic",
            type="relic",
            label=relic.label,
            attrs={},
        )
    )
    hero.memes["trust"] = float(trust)
    hero.memes["pride"] = float(max(pride - 1, 0))
    hero.memes["fear"] = 0.0
    hero.memes["accepted_help"] = 0.0
    hero.memes["friendship"] = 1.0
    friend.memes["friendship"] = 1.0
    friend.memes["care"] = 0.0
    path.meters["danger"] = 0.0
    path.meters["crossed"] = 0.0
    hero.meters["stuck"] = 0.0
    relic_ent.meters["carried"] = 0.0
    relic_ent.meters["restored"] = 0.0
    world.facts["hazard_active"] = False

    introduce(world, realm, hero, friend, relic)
    vow(world, hero, friend, realm, relic)

    world.para()
    meet_hazard(world, hazard, realm)
    hero_pushes_on(world, hero)
    offer_help(world, friend, aid, hazard)

    should_accept = trust >= pride + hazard.severity
    prediction = predict_crossing(world, hazard.id, aid.id, should_accept)
    world.facts["predicted_crossed"] = prediction["crossed"]
    world.facts["predicted_fear"] = prediction["fear"]

    if not should_accept:
        refuse_help(world, hero, friend, hazard)
        world.say(
            f"{friend.id} did not shame {hero.pronoun('object')}. {friend.pronoun().capitalize()} only waited, holding out the {aid.label}."
        )

    world.para()
    accept_help(world, hero, friend, aid)
    use_aid(world, hero, friend, aid)
    restore_relic(world, hero, friend, realm, relic)
    closing_lesson(world, hero, friend, realm)

    world.facts.update(
        hero=hero,
        friend=friend,
        realm=realm,
        hazard=hazard,
        aid=aid,
        relic_cfg=relic,
        relic=relic_ent,
        accepted_initially=should_accept,
        resolved=True,
        friendship_grew=hero.memes["friendship"] > 1.0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    realm = f["realm"]
    hazard = f["hazard"]
    aid = f["aid"]
    relic = f["relic_cfg"]
    return [
        f'Write a short myth for young children that includes the words "edge-dim", "age", and "raw", and is about friendship.',
        f"Tell a mythic story where two young friends, {hero.id} and {friend.id}, must return a sacred {relic.label} by crossing {hazard.label} with the help of {aid.label}.",
        f"Write a gentle old-style tale set on {realm.path_name} where pride gives way to friendship and the children finish a sacred task together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    realm = f["realm"]
    hazard = f["hazard"]
    aid = f["aid"]
    relic = f["relic_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young friends, {hero.id} and {friend.id}. Together they tried to carry a sacred {relic.label} back to {realm.shrine_name}.",
        ),
        (
            f"Why were {hero.id} and {friend.id} traveling before sunrise?",
            f"They had found the {relic.label} in the wrong place and believed it must be returned before sunrise. That duty is what sent them onto the hard road.",
        ),
        (
            f"What problem did they meet on the way?",
            f"They came to {hazard.scene}. It was dangerous because {hazard.threat}.",
        ),
        (
            f"How did {friend.id} help {hero.id}?",
            f"{friend.id} offered {aid.phrase} and {aid.qa_text}. The help fit the danger, so the crossing became possible when they worked together.",
        ),
    ]
    if f["accepted_initially"]:
        qa.append(
            (
                f"Did {hero.id} accept help right away?",
                f"Yes. {hero.id} still felt the danger, but trusted {friend.id} enough to listen at once. That let them cross before fear could trap them in place.",
            )
        )
    else:
        qa.append(
            (
                f"Did {hero.id} accept help right away?",
                f"No. {hero.id} first tried to face the danger alone and got stuck. Then {hero.pronoun().capitalize()} let pride go and accepted {friend.id}'s help, which is what changed the journey.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"They crossed the danger together, returned the {relic.label} to {realm.shrine_name}, and the morning light opened over them. The ending shows that their friendship grew stronger because they trusted one another.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"myth", "friendship"} | set(f["aid"].tags)
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="cliff_path",
        hazard="wind_gap",
        aid="rope",
        relic="sun_drop",
        hero_name="Lila",
        hero_gender="girl",
        friend_name="Tarin",
        friend_gender="boy",
        parent_style="elder",
        pride=3,
        trust=7,
    ),
    StoryParams(
        realm="reed_marsh",
        hazard="flooded_ford",
        aid="raft",
        relic="rain_bell",
        hero_name="Mira",
        hero_gender="girl",
        friend_name="Rin",
        friend_gender="boy",
        parent_style="elder",
        pride=7,
        trust=4,
    ),
    StoryParams(
        realm="cedar_hollow",
        hazard="dark_cave",
        aid="song",
        relic="star_shell",
        hero_name="Asha",
        hero_gender="girl",
        friend_name="Niko",
        friend_gender="boy",
        parent_style="keeper",
        pride=4,
        trust=7,
    ),
    StoryParams(
        realm="cedar_hollow",
        hazard="thorn_gate",
        aid="staff",
        relic="sun_drop",
        hero_name="Kavi",
        hero_gender="boy",
        friend_name="Daya",
        friend_gender="girl",
        parent_style="keeper",
        pride=6,
        trust=5,
    ),
]


def explain_rejection(hazard: Hazard, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not honestly solve the {hazard.label}. "
        f"In this world, help must fit the obstacle, so pick an aid such as "
        f"{', '.join(sorted(hazard.overcome_by))}.)"
    )


ASP_RULES = r"""
fits(H, A) :- hazard(H), aid(A), works_on(A, H), overcome_by(H, A).
valid(R, H, A, Rel) :- realm(R), hazard(H), aid(A), relic(Rel), fits(H, A).

accepts(P, T, H) :- pride(P), trust(T), severity(Hs), T >= P + Hs.
initial_stuck(P, T, H) :- pride(P), trust(T), severity(Hs), T < P + Hs.
resolved :- fits(chosen_hazard, chosen_aid).
friendship_grows :- resolved.
#show valid/4.
#show accepts/3.
#show initial_stuck/3.
#show friendship_grows/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hazard.severity))
        for aid_id in sorted(hazard.overcome_by):
            lines.append(asp.fact("overcome_by", hid, aid_id))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for hid in sorted(aid.works_on):
            lines.append(asp.fact("works_on", aid_id, hid))
    for relic_id in RELICS:
        lines.append(asp.fact("relic", relic_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_accepts(pride: int, trust: int, hazard: str) -> bool:
    import asp

    scenario = "\n".join(
        [
            asp.fact("pride", pride),
            asp.fact("trust", trust),
            asp.fact("chosen_hazard", hazard),
            asp.fact("chosen_aid", next(iter(sorted(HAZARDS[hazard].overcome_by)))),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show accepts/3.\n#show initial_stuck/3."))
    return bool(asp.atoms(model, "accepts"))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = [
        ("wind_gap", 3, 7),
        ("wind_gap", 7, 4),
        ("dark_cave", 4, 5),
        ("thorn_gate", 6, 5),
    ]
    mismatches = 0
    for hazard, pride, trust in cases:
        py = trust >= pride + HAZARDS[hazard].severity
        cl = asp_accepts(pride, trust, hazard)
        if py != cl:
            mismatches += 1
    if mismatches == 0:
        print("OK: ASP acceptance logic matches Python checks.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches} acceptance cases differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated empty story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic friendship storyworld. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--pride", type=int, choices=list(range(1, 9)))
    ap.add_argument("--trust", type=int, choices=list(range(1, 9)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hazard and args.aid:
        hazard = HAZARDS[args.hazard]
        aid = AIDS[args.aid]
        if not aid_fits(hazard, aid):
            raise StoryError(explain_rejection(hazard, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.aid is None or combo[2] == args.aid)
        and (args.relic is None or combo[3] == args.relic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, hazard, aid, relic = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    pride = args.pride if args.pride is not None else rng.randint(2, 7)
    trust = args.trust if args.trust is not None else rng.randint(3, 8)
    return StoryParams(
        realm=realm,
        hazard=hazard,
        aid=aid,
        relic=relic,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        parent_style=rng.choice(["elder", "keeper", "grandmother"]),
        pride=pride,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")

    hazard = HAZARDS[params.hazard]
    aid = AIDS[params.aid]
    if not aid_fits(hazard, aid):
        raise StoryError(explain_rejection(hazard, aid))

    world = tell(
        realm=REALMS[params.realm],
        hazard=hazard,
        aid=aid,
        relic=RELICS[params.relic],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        parent_style=params.parent_style,
        pride=params.pride,
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
        print(asp_program("", "#show valid/4.\n#show accepts/3.\n#show initial_stuck/3.\n#show friendship_grows/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, hazard, aid, relic) combos:\n")
        for realm, hazard, aid, relic in combos:
            print(f"  {realm:12} {hazard:13} {aid:8} {relic}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.hazard} with {p.aid} ({p.realm})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
