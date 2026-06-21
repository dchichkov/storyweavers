#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py
================================================================

A standalone storyworld about two young helpers in a myth-like world who must
carry a sacred object across a dangerous place before the sky changes. The
world prefers wise, cooperative methods over false convenience: a quick solo
shortcut is known to the domain but rejected by the reasonableness gate.

The stories aim for:
- convenience as a tempting but unsafe idea
- teamwork as the real solution
- suspense from a dangerous crossing
- a myth-like tone with shrines, hills, moonlight, and old promises

Run it
------
    python storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py
    python storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py --all
    python storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py --qa
    python storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py --json
    python storyworlds/worlds/gpt-5.4/convenience_teamwork_suspense_myth.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "mother"}
        male = {"boy", "man", "priest", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"priestess": "priestess", "priest": "priest"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
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
class Realm:
    id: str
    village: str
    shrine: str
    sky: str
    blessing: str
    affords: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    glow: str
    weight: str
    fragile: bool
    water_harmed: bool
    gift: str
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
class Obstacle:
    id: str
    label: str
    phrase: str
    hazard: str
    suspense: str
    slip: str
    ending_image: str
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
class Method:
    id: str
    label: str
    teamwork: bool
    sense: int
    guards: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
    setup: str = ""
    rescue: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        self.facts: dict = {
            "realm": realm,
            "method_ok": False,
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
        return [e for e in self.entities.values() if e.role in {"leader", "helper"}]

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


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_alarm(world: World) -> list[str]:
    relic = world.get("relic")
    if relic.meters["tilt"] < THRESHOLD:
        return []
    sig = ("alarm", "relic")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("path").meters["danger"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__alarm__"]


def _r_team_save(world: World) -> list[str]:
    if not world.facts.get("method_ok"):
        return []
    relic = world.get("relic")
    if relic.meters["tilt"] < THRESHOLD:
        return []
    if any(k.memes["holding"] < THRESHOLD for k in world.kids()):
        return []
    sig = ("save", "relic")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    relic.meters["tilt"] = 0.0
    relic.meters["secured"] += 1
    for kid in world.kids():
        kid.memes["courage"] += 1
        if kid.memes["fear"] >= THRESHOLD:
            kid.memes["fear"] -= 1
    return ["__saved__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="alarm", tag="suspense", apply=_r_alarm),
    Rule(name="team_save", tag="teamwork", apply=_r_team_save),
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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN and m.teamwork]


def method_fits(method: Method, relic: Relic, obstacle: Obstacle) -> bool:
    if not method.teamwork or method.sense < SENSE_MIN:
        return False
    if relic.weight == "heavy" and "heavy" not in method.supports:
        return False
    if relic.fragile and "steady" not in method.supports:
        return False
    if obstacle.hazard == "gap" and "span" not in method.guards:
        return False
    if obstacle.hazard == "steep" and "balance" not in method.guards:
        return False
    if obstacle.hazard == "water" and "water_safe" not in method.guards:
        return False
    if relic.water_harmed and "dry" not in method.guards:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for realm_id, realm in REALMS.items():
        for obstacle_id in sorted(realm.affords):
            obstacle = OBSTACLES[obstacle_id]
            for relic_id, relic in RELICS.items():
                for method_id, method in METHODS.items():
                    if method_fits(method, relic, obstacle):
                        combos.append((realm_id, relic_id, obstacle_id, method_id))
    return combos


def explain_method_rejection(method: Method, relic: Relic, obstacle: Obstacle) -> str:
    if not method.teamwork:
        return (
            f"(No story: '{method.label}' offers only convenience, not teamwork. "
            f"In this world, the sacred task must be shared by two children.)"
        )
    if method.sense < SENSE_MIN:
        return (
            f"(No story: '{method.label}' is known to the world but refused as a poor idea. "
            f"The old stories favor wiser methods.)"
        )
    if relic.weight == "heavy" and "heavy" not in method.supports:
        return (
            f"(No story: the {relic.label} is too heavy for {method.label}. "
            f"Pick a method that can support a heavy burden.)"
        )
    if relic.fragile and "steady" not in method.supports:
        return (
            f"(No story: the {relic.label} is fragile, and {method.label} would not keep it steady.)"
        )
    if obstacle.hazard == "gap" and "span" not in method.guards:
        return (
            f"(No story: {method.label} cannot carry the children over the {obstacle.label}.)"
        )
    if obstacle.hazard == "steep" and "balance" not in method.guards:
        return (
            f"(No story: {method.label} does not give enough balance on the {obstacle.label}.)"
        )
    if obstacle.hazard == "water" and "water_safe" not in method.guards:
        return (
            f"(No story: {method.label} is not safe for crossing the {obstacle.label}.)"
        )
    if relic.water_harmed and "dry" not in method.guards:
        return (
            f"(No story: the {relic.label} must stay dry, and {method.label} cannot protect it from water.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_loss(world: World) -> dict:
    sim = world.copy()
    relic = sim.get("relic")
    obstacle = sim.facts["obstacle"]
    if obstacle.hazard in {"gap", "steep", "water"}:
        relic.meters["tilt"] += 1
    propagate(sim, narrate=False)
    return {
        "tilt": relic.meters["tilt"],
        "danger": sim.get("path").meters["danger"],
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay beats
# ---------------------------------------------------------------------------
def myth_opening(world: World, leader: Entity, helper: Entity, elder: Entity, relic: Relic) -> None:
    realm = world.realm
    for kid in (leader, helper):
        kid.memes["duty"] += 1
    world.say(
        f"In the old days, when {realm.sky} and the hills listened to vows, "
        f"the people of {realm.village} kept peace by honoring {realm.shrine}."
    )
    world.say(
        f"One evening the {relic.label} had to be carried there before the last light faded. "
        f"If it arrived in time, {realm.blessing}."
    )
    world.say(
        f"So {elder.label_word} placed {relic.phrase} in the hands of {leader.id} and {helper.id} "
        f"and asked them to walk with careful hearts."
    )


def receive_charge(world: World, elder: Entity, leader: Entity, helper: Entity, relic: Relic) -> None:
    world.say(
        f'"Do not trust speed more than wisdom," the {elder.label_word} told them. '
        f'"A holy thing loves steady hands."'
    )
    helper.memes["trust"] += 1
    leader.memes["pride"] += 1
    world.say(
        f"{leader.id} felt proud to carry such a gift, and {helper.id} walked close beside "
        f"{leader.pronoun('object')} under the first blue shadow of night."
    )


def approach(world: World, obstacle: Obstacle) -> None:
    world.say(
        f"Then they reached {obstacle.phrase}. {obstacle.suspense}"
    )


def convenience_temptation(world: World, leader: Entity, helper: Entity, method: Method, obstacle: Obstacle) -> None:
    leader.memes["impatience"] += 1
    world.say(
        f'"If we hurry, we will save time," {leader.id} whispered. '
        f'"There is a kind of convenience in rushing before the dark grows deeper."'
    )
    world.say(
        f"But {helper.id} looked at the {obstacle.label} and at the relic, and did not answer at once."
    )
    pred = predict_loss(world)
    world.facts["predicted_danger"] = pred["danger"]
    helper.memes["caution"] += 1
    world.say(
        f'At last {helper.pronoun()} said, "Quick is not the same as safe. '
        f'If the burden tilts here, the night will grow bigger around us."'
    )
    world.say(
        f"Together they chose {method.label} instead, because old promises are kept by more than speed."
    )


def prepare_method(world: World, leader: Entity, helper: Entity, method: Method) -> None:
    leader.memes["holding"] = 1.0
    helper.memes["holding"] = 1.0
    world.facts["method_ok"] = True
    world.say(method.setup)


def crossing(world: World, leader: Entity, helper: Entity, relic: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"Step by step they entered the danger. {leader.id} went first for a breath, "
        f"and {helper.id} matched each pace."
    )
    relic.meters["tilt"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {obstacle.slip}, and the {relic.label} tipped in the dark."
    )
    world.say(
        f"For one heartbeat it seemed the whole errand might fail."
    )


def teamwork_rescue(world: World, leader: Entity, helper: Entity, method: Method, relic: Relic) -> None:
    propagate(world, narrate=False)
    world.say(method.rescue)
    world.say(
        f"Because neither child let go, the {relic.label} settled again and its light did not go out."
    )
    leader.memes["trust"] += 1
    helper.memes["trust"] += 1


def arrival(world: World, elder: Entity, leader: Entity, helper: Entity, relic: Relic, obstacle: Obstacle) -> None:
    world.get("relic").meters["arrived"] += 1
    for kid in (leader, helper):
        kid.memes["joy"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"When they reached {world.realm.shrine}, the waiting flame bowed toward the {relic.label} as if it knew its own kin."
    )
    world.say(
        f"The {elder.label_word} received it with a smile and said, "
        f'"You crossed {obstacle.label} the right way. A shared burden travels farther than a lonely one."'
    )
    world.say(
        f"That night {world.realm.blessing}, and from the shrine steps the children saw {obstacle.ending_image}."
    )


def tell(
    realm: Realm,
    relic_cfg: Relic,
    obstacle_cfg: Obstacle,
    method_cfg: Method,
    leader_name: str = "Ira",
    leader_type: str = "boy",
    helper_name: str = "Nemi",
    helper_type: str = "girl",
    elder_type: str = "priestess",
) -> World:
    world = World(realm)
    leader = world.add(Entity(id=leader_name, kind="character", type=leader_type, role="leader"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, role="elder", label="the elder"))
    relic = world.add(Entity(id="relic", kind="thing", type="relic", label=relic_cfg.label))
    path = world.add(Entity(id="path", kind="thing", type="path", label=obstacle_cfg.label))

    world.facts.update(
        leader=leader,
        helper=helper,
        elder=elder,
        relic_cfg=relic_cfg,
        obstacle=obstacle_cfg,
        method=method_cfg,
        relic_entity=relic,
        path=path,
        predicted_danger=0,
    )

    myth_opening(world, leader, helper, elder, relic_cfg)
    receive_charge(world, elder, leader, helper, relic_cfg)

    world.para()
    approach(world, obstacle_cfg)
    convenience_temptation(world, leader, helper, method_cfg, obstacle_cfg)
    prepare_method(world, leader, helper, method_cfg)

    world.para()
    crossing(world, leader, helper, relic, obstacle_cfg)
    teamwork_rescue(world, leader, helper, method_cfg, relic_cfg)

    world.para()
    arrival(world, elder, leader, helper, relic_cfg, obstacle_cfg)

    world.facts.update(
        succeeded=world.get("relic").meters["arrived"] >= THRESHOLD,
        feared=any(k.memes["fear"] >= THRESHOLD for k in world.kids()),
        secured=world.get("relic").meters["secured"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
REALMS = {
    "moon_hill": Realm(
        id="moon_hill",
        village="Moon-Hill",
        shrine="the Shrine of Returning Light",
        sky="the moon rode low over cedar smoke",
        blessing="the lamps of the village burned clear until morning",
        affords={"ravine", "steps"},
        tags={"shrine", "moon"},
    ),
    "reed_delta": Realm(
        id="reed_delta",
        village="Reed-Delta",
        shrine="the House of River Songs",
        sky="the clouds held back their rain to listen",
        blessing="the wells stayed sweet and the boats rested safely",
        affords={"river", "steps"},
        tags={"river", "shrine"},
    ),
    "sun_stair": Realm(
        id="sun_stair",
        village="Sun-Stair",
        shrine="the Terrace of the First Flame",
        sky="the west glowed like copper behind the peaks",
        blessing="the dawn came warm across the fields",
        affords={"ravine", "river", "steps"},
        tags={"sun", "shrine"},
    ),
}

RELICS = {
    "moon_jar": Relic(
        id="moon_jar",
        label="moon jar",
        phrase="a thin silver moon jar",
        glow="cold light trembled in it like milk",
        weight="light",
        fragile=True,
        water_harmed=False,
        gift="night-bright milk for the shrine lamp",
        tags={"fragile", "light"},
    ),
    "rain_drum": Relic(
        id="rain_drum",
        label="rain drum",
        phrase="the little rain drum of cedar and bronze",
        glow="its bronze rings murmured when the wind touched them",
        weight="heavy",
        fragile=False,
        water_harmed=False,
        gift="the beat that calls gentle weather",
        tags={"heavy", "drum"},
    ),
    "ember_basket": Relic(
        id="ember_basket",
        label="ember basket",
        phrase="a woven ember basket lined with ash-white clay",
        glow="a red breath glowed in its middle",
        weight="light",
        fragile=False,
        water_harmed=True,
        gift="the living ember that wakes the dawn fire",
        tags={"fire", "dry"},
    ),
}

OBSTACLES = {
    "ravine": Obstacle(
        id="ravine",
        label="the ravine",
        phrase="the black ravine where wind moved without feet",
        hazard="gap",
        suspense="No bird sang there. Only the old rope posts stood on either side, with darkness sleeping between them.",
        slip="a gust pressed at their sleeves",
        ending_image="the lamps of the village shining one by one beneath the cliff",
        tags={"gap", "wind"},
    ),
    "river": Obstacle(
        id="river",
        label="the river",
        phrase="the river ford where moonlight broke into shivering pieces",
        hazard="water",
        suspense="The stones were hidden under fast water, and every ripple looked like a hand that wanted to tug at their ankles.",
        slip="cold water swirled around their legs",
        ending_image="the river lying calm at last, with stars resting in it",
        tags={"water", "ford"},
    ),
    "steps": Obstacle(
        id="steps",
        label="the steep steps",
        phrase="the steep shrine steps carved long ago into the mountain face",
        hazard="steep",
        suspense="They climbed so sharply that the dark seemed to lean down over them, listening for a mistake.",
        slip="loose grit slid under one sandal",
        ending_image="the high stone stair glowing softly above the sleeping roofs",
        tags={"steep", "stone"},
    ),
}

METHODS = {
    "hand_line": Method(
        id="hand_line",
        label="the hand-line",
        teamwork=True,
        sense=3,
        guards={"span", "balance"},
        supports={"steady"},
        setup="They looped the old hand-line around their wrists and kept the relic between them, each child feeling the other child's pull.",
        rescue="The rope drew tight, and each child steadied the other before fear could grow into disaster.",
        qa_text="used the hand-line and steadied each other",
        tags={"rope", "teamwork"},
    ),
    "shoulder_pole": Method(
        id="shoulder_pole",
        label="the shoulder pole",
        teamwork=True,
        sense=3,
        guards={"balance"},
        supports={"heavy", "steady"},
        setup="They set the burden on a smooth shoulder pole, one end on each small shoulder, and breathed until their steps matched.",
        rescue="When the weight shifted, they bent together and lifted together, so the burden rode level again.",
        qa_text="carried it on a shoulder pole and balanced the weight together",
        tags={"pole", "teamwork"},
    ),
    "reed_tray": Method(
        id="reed_tray",
        label="the reed tray",
        teamwork=True,
        sense=3,
        guards={"water_safe", "dry"},
        supports={"steady"},
        setup="They raised the relic on a broad reed tray above the water, one child at each side, and kept it dry between them.",
        rescue="Both children lifted at once, holding the tray high while the water tugged and failed to reach the relic.",
        qa_text="held it high on a reed tray and kept it dry together",
        tags={"water", "teamwork"},
    ),
    "sling_pole": Method(
        id="sling_pole",
        label="the sling pole",
        teamwork=True,
        sense=3,
        guards={"water_safe", "dry", "balance"},
        supports={"heavy", "steady"},
        setup="They tied the burden in a sling beneath a carrying pole and shared the weight from both ends, with the relic hanging safe and high.",
        rescue="The sling swung only once, because they answered the danger together and set the pole firm again.",
        qa_text="used a sling pole and answered the danger together",
        tags={"pole", "water", "teamwork"},
    ),
    "solo_convenience": Method(
        id="solo_convenience",
        label="the solo convenience carry",
        teamwork=False,
        sense=1,
        guards={"balance"},
        supports={"heavy"},
        setup="",
        rescue="",
        qa_text="",
        tags={"shortcut"},
    ),
}

GIRL_NAMES = ["Ala", "Nemi", "Suri", "Lina", "Tavi", "Mira", "Ishi", "Pela"]
BOY_NAMES = ["Ira", "Tarin", "Moru", "Solen", "Beri", "Ketu", "Jorin", "Naru"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    realm: str
    relic: str
    obstacle: str
    method: str
    leader: str
    leader_gender: str
    helper: str
    helper_gender: str
    elder: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
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
    "rope": [
        (
            "Why can a rope help two people cross a dangerous place?",
            "A rope helps two people feel each other's pull, so they can steady one another. If one slips, the other can help stop the fall."
        )
    ],
    "pole": [
        (
            "Why is a carrying pole useful for a heavy load?",
            "A carrying pole shares the weight between two people. That makes a heavy thing easier to carry and easier to keep level."
        )
    ],
    "water": [
        (
            "Why do people hold important things high over water?",
            "They hold them high so splashing water cannot reach them. That keeps the object dry and safe."
        )
    ],
    "gap": [
        (
            "Why is a ravine dangerous at night?",
            "A ravine has a drop, and in the dark it is hard to judge where the safe ground ends. Wind can make the danger feel even worse."
        )
    ],
    "steep": [
        (
            "Why are steep steps hard to climb with a burden?",
            "Steep steps make people lean and work harder to keep balance. A burden can shift if they do not move carefully."
        )
    ],
    "ford": [
        (
            "What is a river ford?",
            "A ford is a shallow place where people can cross a river on foot. Even there, the water can still push at their legs."
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can break easily if it is dropped or bumped. Fragile things need careful hands."
        )
    ],
    "heavy": [
        (
            "Why is teamwork helpful with something heavy?",
            "Two people can share the weight and keep the object from tipping. Teamwork makes the load safer, not just easier."
        )
    ],
    "fire": [
        (
            "Why must an ember be kept dry?",
            "Water can smother an ember and stop it from glowing. If the ember goes out, it cannot light a fire."
        )
    ],
    "shortcut": [
        (
            "Is the fastest choice always the wisest choice?",
            "No. Sometimes the fastest choice only looks easy at first, but it can cause a bigger problem later."
        )
    ],
}
KNOWLEDGE_ORDER = ["shortcut", "gap", "ford", "steep", "fragile", "heavy", "rope", "pole", "water", "fire"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    relic = f["relic_cfg"]
    obstacle = f["obstacle"]
    return [
        f'Write a short myth-like story for a 3-to-5-year-old that includes the word "convenience" and centers on teamwork in a moment of suspense.',
        f"Tell a gentle myth where {leader.id} and {helper.id} must carry a {relic.label} across {obstacle.label} before night closes in, and working together saves the day.",
        "Write a small old-fashioned tale where children learn that a quick shortcut is not always wise, and the ending shows what changed in the world because they cooperated.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    helper = f["helper"]
    elder = f["elder"]
    relic = f["relic_cfg"]
    obstacle = f["obstacle"]
    method = f["method"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {leader.id} and {helper.id}, two children trusted with a sacred task, and the {elder.label_word} who sent them. They had to carry the {relic.label} to {world.realm.shrine} before the light was gone."
        ),
        (
            f"Why was the journey across {obstacle.label} scary?",
            f"It was scary because {obstacle.suspense.lower()} The danger made one wrong step feel as if the whole errand might fail."
        ),
        (
            "What did the children learn about convenience?",
            f"They learned that convenience is not the same thing as wisdom. Rushing would have made the danger worse, so they chose a careful shared method instead."
        ),
        (
            f"How did {leader.id} and {helper.id} keep the relic safe?",
            f"They {method.qa_text}. When the relic tipped, both children answered the danger at the same moment, and that teamwork stopped the problem from becoming a loss."
        ),
        (
            "How did the story end?",
            f"They reached the shrine safely, and {world.realm.blessing}. The ending proves that their teamwork changed more than their own feelings; it helped the whole village."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["method"].tags) | set(f["obstacle"].tags) | set(f["relic_cfg"].tags)
    if "wind" in tags:
        tags.add("gap")
    if "ford" in tags:
        tags.add("ford")
    if "stone" in tags:
        tags.add("steep")
    if "dry" in tags:
        tags.add("fire")
    if "shortcut" not in tags:
        tags.add("shortcut")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: method_ok={world.facts.get('method_ok')} predicted_danger={world.facts.get('predicted_danger')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
sensible(M) :- method(M), teamwork(M), sense(M,S), sense_min(Min), S >= Min.

needs_support(R, heavy) :- relic(R), weight(R, heavy).
needs_support(R, steady) :- relic(R), fragile(R).

needs_guard(O, span) :- obstacle(O), hazard(O, gap).
needs_guard(O, balance) :- obstacle(O), hazard(O, steep).
needs_guard(O, water_safe) :- obstacle(O), hazard(O, water).
needs_guard(R, dry) :- relic(R), water_harmed(R).

lacks_support(M, R) :- needs_support(R, Need), not supports(M, Need).
lacks_guard(M, O) :- needs_guard(O, Need), not guards(M, Need).
lacks_relic_guard(M, R) :- needs_guard(R, Need), not guards(M, Need).

valid(Realm, R, O, M) :-
    realm(Realm), affords(Realm, O),
    relic(R), obstacle(O), sensible(M),
    not lacks_support(M, R),
    not lacks_guard(M, O),
    not lacks_relic_guard(M, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for realm_id, realm in REALMS.items():
        lines.append(asp.fact("realm", realm_id))
        for obstacle_id in sorted(realm.affords):
            lines.append(asp.fact("affords", realm_id, obstacle_id))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        lines.append(asp.fact("weight", relic_id, relic.weight))
        if relic.fragile:
            lines.append(asp.fact("fragile", relic_id))
        if relic.water_harmed:
            lines.append(asp.fact("water_harmed", relic_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("hazard", obstacle_id, obstacle.hazard))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        if method.teamwork:
            lines.append(asp.fact("teamwork", method_id))
        for guard in sorted(method.guards):
            lines.append(asp.fact("guards", method_id, guard))
        for support in sorted(method.supports):
            lines.append(asp.fact("supports", method_id, support))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: valid combos match ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(5):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            generate(params)
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break
    else:
        print("OK: random generation smoke tests succeeded.")

    return rc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        realm="moon_hill",
        relic="moon_jar",
        obstacle="ravine",
        method="hand_line",
        leader="Ira",
        leader_gender="boy",
        helper="Nemi",
        helper_gender="girl",
        elder="priestess",
    ),
    StoryParams(
        realm="reed_delta",
        relic="ember_basket",
        obstacle="river",
        method="reed_tray",
        leader="Mira",
        leader_gender="girl",
        helper="Tarin",
        helper_gender="boy",
        elder="priest",
    ),
    StoryParams(
        realm="sun_stair",
        relic="rain_drum",
        obstacle="steps",
        method="shoulder_pole",
        leader="Solen",
        leader_gender="boy",
        helper="Ala",
        helper_gender="girl",
        elder="priestess",
    ),
    StoryParams(
        realm="sun_stair",
        relic="rain_drum",
        obstacle="river",
        method="sling_pole",
        leader="Pela",
        leader_gender="girl",
        helper="Naru",
        helper_gender="boy",
        elder="priest",
    ),
    StoryParams(
        realm="moon_hill",
        relic="moon_jar",
        obstacle="steps",
        method="hand_line",
        leader="Lina",
        leader_gender="girl",
        helper="Jorin",
        helper_gender="boy",
        elder="priestess",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Myth-like storyworld: children reject false convenience and use teamwork to carry a sacred burden through suspense."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="verify ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.realm and args.obstacle and args.obstacle not in REALMS[args.realm].affords:
        raise StoryError(
            f"(No story: {args.obstacle} does not belong to the path-world of {args.realm}.)"
        )

    if args.relic and args.obstacle and args.method:
        relic = RELICS[args.relic]
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_fits(method, relic, obstacle):
            raise StoryError(explain_method_rejection(method, relic, obstacle))

    combos = [
        combo for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.relic is None or combo[1] == args.relic)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, relic, obstacle, method = rng.choice(sorted(combos))
    leader, leader_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=leader)
    elder = args.elder or rng.choice(["priestess", "priest"])
    return StoryParams(
        realm=realm,
        relic=relic,
        obstacle=obstacle,
        method=method,
        leader=leader,
        leader_gender=leader_gender,
        helper=helper,
        helper_gender=helper_gender,
        elder=elder,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.relic not in RELICS:
        raise StoryError(f"(Unknown relic: {params.relic})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    realm = REALMS[params.realm]
    if params.obstacle not in realm.affords:
        raise StoryError(f"(No story: {params.obstacle} does not fit in {params.realm}.)")

    relic = RELICS[params.relic]
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not method_fits(method, relic, obstacle):
        raise StoryError(explain_method_rejection(method, relic, obstacle))

    world = tell(
        realm=realm,
        relic_cfg=relic,
        obstacle_cfg=obstacle,
        method_cfg=method,
        leader_name=params.leader,
        leader_type=params.leader_gender,
        helper_name=params.helper,
        helper_type=params.helper_gender,
        elder_type=params.elder,
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
        print(asp_program("#show sensible/1.\n#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (realm, relic, obstacle, method) combos:\n")
        for realm, relic, obstacle, method in combos:
            print(f"  {realm:10} {relic:12} {obstacle:8} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.leader} & {p.helper}: {p.relic} across {p.obstacle} ({p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
