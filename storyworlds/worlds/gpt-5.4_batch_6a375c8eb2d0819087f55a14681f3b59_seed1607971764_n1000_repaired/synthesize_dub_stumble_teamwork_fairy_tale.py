#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py
=========================================================================

A standalone storyworld for a small fairy-tale domain about **teamwork at a
dangerous crossing**. Two young companions must carry a dawn bell across an
obstacle before sunrise. They study the problem, synthesize a plan from what
the place offers, and begin the crossing together. In the middle turn, one of
them will stumble. If their chosen method and helper are strong enough, the
others catch them and the bell reaches the tower in time; if not, the bell is
lost and the kingdom wakes late.

Required seed words appear naturally in every story:
- **synthesize**: the children synthesize a plan from the place, materials, and help
- **dub**: the ending gives a title or name
- **stumble**: the dangerous middle turn always includes a stumble

Run it
------
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py --obstacle broken_bridge --method silver_thread --helper spider
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py --obstacle misty_brook --method silver_thread
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/synthesize_dub_stumble_teamwork_fairy_tale.py --verify
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
        female = {"girl", "fairy_queen", "mother", "woman"}
        male = {"boy", "king", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    ruler: str
    opening: str
    tower: str
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
class Obstacle:
    id: str
    label: str
    scene: str
    risk: int
    footing: str
    needed: str
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
    verb: str
    works_for: set[str]
    power: int
    body: str
    fail_body: str
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
class HelperCfg:
    id: str
    label: str
    kind: str
    helps_with: set[str]
    power: int
    entrance: str
    assist: str
    fail_assist: str
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


def _r_stumble_fear(world: World) -> list[str]:
    child = world.get("child1")
    if child.meters["stumbling"] < THRESHOLD:
        return []
    sig = ("stumble_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child1").memes["fear"] += 1
    world.get("child2").memes["fear"] += 1
    world.get("bell").meters["endangered"] += 1
    return []


def _r_save(world: World) -> list[str]:
    if world.get("crossing").meters["support"] < THRESHOLD:
        return []
    if world.get("child1").meters["stumbling"] < THRESHOLD:
        return []
    sig = ("save",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("child1").meters["stumbling"] = 0.0
    world.get("bell").meters["endangered"] = 0.0
    world.get("bell").meters["safe"] += 1
    for eid in ("child1", "child2", "helper"):
        if eid in world.entities:
            world.get(eid).memes["trust"] += 1
    return []


def _r_loss(world: World) -> list[str]:
    if world.get("crossing").meters["support"] >= THRESHOLD:
        return []
    if world.get("child1").meters["stumbling"] < THRESHOLD:
        return []
    sig = ("loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("bell").meters["lost"] += 1
    world.get("quest").meters["late"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="stumble_fear", tag="emotional", apply=_r_stumble_fear),
    Rule(name="save", tag="physical", apply=_r_save),
    Rule(name="loss", tag="physical", apply=_r_loss),
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
                produced.extend(out)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def method_fits(obstacle: Obstacle, method: Method) -> bool:
    return obstacle.id in method.works_for


def helper_fits(method: Method, helper: HelperCfg) -> bool:
    return method.id in helper.helps_with


def teamwork_score(method: Method, helper: HelperCfg) -> int:
    return method.power + helper.power


def succeeds(obstacle: Obstacle, method: Method, helper: HelperCfg) -> bool:
    return teamwork_score(method, helper) >= obstacle.risk


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id in REALMS:
        for obstacle_id, obstacle in OBSTACLES.items():
            for method_id, method in METHODS.items():
                for helper_id, helper in HELPERS.items():
                    if method_fits(obstacle, method) and helper_fits(method, helper):
                        combos.append((realm_id, obstacle_id, method_id, helper_id))
    return combos


def explain_rejection(obstacle: Obstacle, method: Method, helper: HelperCfg) -> str:
    if not method_fits(obstacle, method):
        return (
            f"(No story: {method.label} does not honestly solve {obstacle.label}. "
            f"The crossing needs {obstacle.needed}.)"
        )
    if not helper_fits(method, helper):
        return (
            f"(No story: {helper.label} cannot reasonably help with {method.label}. "
            f"Choose a helper who knows that kind of work.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def outcome_of(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    helper = HELPERS[params.helper]
    return "saved" if succeeds(obstacle, method, helper) else "late"


def introduce(world: World, child1: Entity, child2: Entity, bell: Entity, realm: Realm) -> None:
    for kid in (child1, child2):
        kid.memes["hope"] += 1
        kid.memes["duty"] += 1
    world.say(
        f"In {realm.place}, where {realm.opening}, two young friends named "
        f"{child1.id} and {child2.id} were trusted with a small silver bell."
    )
    world.say(
        f"Every dawn, the bell had to be rung from {realm.tower} so the birds, bakers, "
        f"and broom-makers of the realm would wake in good order."
    )
    world.say(
        f"{child1.id} carried the bell in both hands, and {child2.id} walked beside "
        f"{child1.pronoun('object')} as carefully as if they were guarding a star."
    )


def set_quest(world: World, realm: Realm, obstacle: Obstacle) -> None:
    world.say(
        f"But on the path to the tower they found {obstacle.scene}. "
        f"Without a safe way across, the morning song of {realm.ruler} would begin in silence."
    )


def meet_helper(world: World, helper: Entity, helper_cfg: HelperCfg) -> None:
    helper.memes["kindness"] += 1
    world.say(helper_cfg.entrance)


def synthesize_plan(
    world: World,
    child1: Entity,
    child2: Entity,
    obstacle: Obstacle,
    method: Method,
    helper_cfg: HelperCfg,
) -> None:
    child1.memes["thought"] += 1
    child2.memes["thought"] += 1
    world.say(
        f'The friends did not rush. They stopped, looked, listened, and tried to '
        f'synthesize a plan from the wind, the stones, and the trouble before them.'
    )
    world.say(
        f'{child2.id} pointed at {obstacle.label}, and together with {helper_cfg.label}, '
        f'they chose to {method.verb}.'
    )


def build_crossing(world: World, obstacle: Obstacle, method: Method, helper_cfg: HelperCfg) -> None:
    world.get("crossing").meters["built"] += 1
    world.say(method.body.format(obstacle=obstacle.label, helper=helper_cfg.label))


def start_crossing(world: World, child1: Entity, child2: Entity, bell: Entity, obstacle: Obstacle) -> None:
    bell.meters["carried"] += 1
    world.say(
        f"Step by step they moved over {obstacle.label}. {child1.id} held the bell, "
        f"and {child2.id} kept one hand ready at {child1.pronoun('possessive')} elbow."
    )


def stumble_turn(world: World, child1: Entity, obstacle: Obstacle) -> None:
    child1.meters["stumbling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then, right in the middle, {child1.id} did stumble on {obstacle.footing}. "
        f"The silver bell tipped, and for one bright, dreadful blink it seemed ready to fall."
    )


def rescue(world: World, child1: Entity, child2: Entity, helper_cfg: HelperCfg, method: Method) -> None:
    world.get("crossing").meters["support"] += 1
    world.get("quest").meters["on_time"] += 1
    propagate(world, narrate=False)
    child1.memes["relief"] += 1
    child2.memes["relief"] += 1
    world.get("helper").memes["relief"] += 1
    world.say(
        f"But {child2.id} caught {child1.id} by the sleeve, and {helper_cfg.assist}. "
        f"Because they worked as one little team, the bell stayed safe."
    )
    world.say(
        f"They hurried on to the tower, rang the bell before the last star winked out, "
        f"and the whole kingdom woke to a clear silver note."
    )
    world.say(
        f"After that, the people of the realm would dub the crossing "
        f'"{method.label}," remembering how teamwork held fast where fear had slipped.'
    )


def fail(world: World, child1: Entity, child2: Entity, helper_cfg: HelperCfg, method: Method, realm: Realm) -> None:
    world.get("crossing").meters["support"] = 0.0
    propagate(world, narrate=False)
    child1.memes["sadness"] += 1
    child2.memes["sadness"] += 1
    world.get("helper").memes["sadness"] += 1
    world.say(
        f"{child2.id} reached for {child1.id}, but {helper_cfg.fail_assist}. "
        f"The bell slipped from small fingers and vanished below with a single lonely splash."
    )
    world.say(
        f"They climbed to the tower anyway, empty-handed and quiet. When dawn came, "
        f"{realm.place} woke slowly, for no silver ringing flew ahead of the sun."
    )
    world.say(
        f"Even so, the three of them stood together and promised to mend the way properly. "
        f"Later, the villagers would dub that place " 
        f'"Second-Try Crossing," so no one would forget that brave hearts still need good help.'
    )


def closing_blessing(world: World, realm: Realm, success: bool) -> None:
    if success:
        world.say(
            f"And from that morning on, whenever the bell sang from {realm.tower}, "
            f"children remembered that clever hands are brightest when they work together."
        )
    else:
        world.say(
            f"And from that morning on, whenever the first light touched {realm.tower}, "
            f"children remembered that wishes alone cannot hold a bridge, but honest teamwork can begin again."
        )


def tell(
    realm: Realm,
    obstacle: Obstacle,
    method: Method,
    helper_cfg: HelperCfg,
    child1_name: str = "Lina",
    child1_type: str = "girl",
    child2_name: str = "Rowan",
    child2_type: str = "boy",
    ruler_type: str = "fairy_queen",
) -> World:
    world = World()
    child1 = world.add(Entity(id="child1", kind="character", type=child1_type, label=child1_name, role="carrier"))
    child2 = world.add(Entity(id="child2", kind="character", type=child2_type, label=child2_name, role="partner"))
    ruler = world.add(Entity(id="ruler", kind="character", type=ruler_type, label=realm.ruler, role="ruler"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_cfg.kind, label=helper_cfg.label, role="helper"))
    bell = world.add(Entity(id="bell", type="bell", label="the silver bell"))
    crossing = world.add(Entity(id="crossing", type="crossing", label=obstacle.label))
    quest = world.add(Entity(id="quest", type="quest", label="the dawn errand"))

    world.facts.update(
        child1=child1,
        child2=child2,
        ruler=ruler,
        helper=helper,
        bell=bell,
        crossing=crossing,
        quest=quest,
        realm=realm,
        obstacle=obstacle,
        method=method,
        helper_cfg=helper_cfg,
        child1_name=child1_name,
        child2_name=child2_name,
    )

    introduce(world, child1, child2, bell, realm)
    set_quest(world, realm, obstacle)

    world.para()
    meet_helper(world, helper, helper_cfg)
    synthesize_plan(world, child1, child2, obstacle, method, helper_cfg)
    build_crossing(world, obstacle, method, helper_cfg)

    world.para()
    start_crossing(world, child1, child2, bell, obstacle)
    stumble_turn(world, child1, obstacle)

    success = succeeds(obstacle, method, helper_cfg)
    world.para()
    if success:
        rescue(world, child1, child2, helper_cfg, method)
        outcome = "saved"
    else:
        fail(world, child1, child2, helper_cfg, method, realm)
        outcome = "late"

    world.para()
    closing_blessing(world, realm, success)

    world.facts.update(
        outcome=outcome,
        success=success,
        bell_lost=bell.meters["lost"] >= THRESHOLD,
        bell_safe=bell.meters["safe"] >= THRESHOLD,
        teamwork=teamwork_score(method, helper_cfg),
    )
    return world


REALMS = {
    "moss_hollow": Realm(
        id="moss_hollow",
        place="Moss Hollow",
        ruler="the Fern Queen",
        opening="fireflies stitched gold dots over the reeds each evening",
        tower="the Moss Bell Tower",
        tags={"forest", "fairy_tale"},
    ),
    "moonmeadow": Realm(
        id="moonmeadow",
        place="Moonmeadow",
        ruler="the Dew King",
        opening="every daisy kept a bead of moonlight until dawn",
        tower="the Moonmeadow Dawn Tower",
        tags={"meadow", "fairy_tale"},
    ),
    "thistle_glen": Realm(
        id="thistle_glen",
        place="Thistle Glen",
        ruler="the Queen of Thistles",
        opening="the hedges hummed softly when the night wind passed through",
        tower="the Thistle Watch Tower",
        tags={"glen", "fairy_tale"},
    ),
}

OBSTACLES = {
    "broken_bridge": Obstacle(
        id="broken_bridge",
        label="the broken bridge",
        scene="a wooden bridge with its middle slats snapped away above the stream",
        risk=4,
        footing="the splintered boards",
        needed="something woven and strong enough to bind the bridge back together",
        tags={"bridge", "stream"},
    ),
    "misty_brook": Obstacle(
        id="misty_brook",
        label="the misty brook",
        scene="a brook running over round, sleepy stones, with mist hiding the safest steps",
        risk=3,
        footing="a wet stone hidden by mist",
        needed="a clear, steady path over the water",
        tags={"brook", "stones"},
    ),
    "thorn_gap": Obstacle(
        id="thorn_gap",
        label="the thorn gap",
        scene="a thorny gap where the old path had crumbled away beside a bramble bank",
        risk=5,
        footing="the loose edge of the path",
        needed="a firm way to span the empty place and keep the bell clear of the thorns",
        tags={"brambles", "cliff"},
    ),
}

METHODS = {
    "silver_thread": Method(
        id="silver_thread",
        label="Silver Thread Span",
        verb="synthesize a shining thread from moonwater and spider silk, then lace the bridge tight",
        works_for={"broken_bridge", "thorn_gap"},
        power=3,
        body="With patient fingers they began to synthesize a shining thread from moonwater and spider silk, and soon a bright braid tied {obstacle} into one steady line.",
        fail_body="The pale thread gleamed prettily, but it was too slight to master {obstacle}.",
        qa_text="They made a bright silver thread and laced the crossing back together.",
        tags={"bridge", "spider_silk", "synthesize"},
    ),
    "stepping_song": Method(
        id="stepping_song",
        label="Stepping Song",
        verb="sing the stepping song and set flat stones where the notes told them to",
        works_for={"misty_brook"},
        power=2,
        body="They sang the stepping song and set flat stones one by one until {obstacle} held a little path like buttons on a ribbon.",
        fail_body="The stones were too few and too smooth, and the song could not make them wider.",
        qa_text="They placed flat stepping stones in a singing path.",
        tags={"brook", "stones", "song"},
    ),
    "reed_raft": Method(
        id="reed_raft",
        label="Reed Raft",
        verb="bind river reeds into a raft broad enough for the bell and two pairs of feet",
        works_for={"misty_brook", "thorn_gap"},
        power=2,
        body="They bound river reeds together into a raft and pushed it into place until {obstacle} had a floating way across.",
        fail_body="The raft bobbed and twisted, never growing steady enough.",
        qa_text="They tied reeds into a raft to carry the bell across.",
        tags={"raft", "reeds"},
    ),
    "lantern_ladder": Method(
        id="lantern_ladder",
        label="Lantern Ladder",
        verb="set a ladder of willow poles and hanging lantern-vines across the gap",
        works_for={"thorn_gap", "broken_bridge"},
        power=3,
        body="They set willow poles from side to side and hung lantern-vines between them until {obstacle} looked almost like a glowing stair.",
        fail_body="The ladder shone softly, yet the poles still trembled too much.",
        qa_text="They built a willow ladder with lantern-vines across the gap.",
        tags={"ladder", "willow", "lantern"},
    ),
}

HELPERS = {
    "spider": HelperCfg(
        id="spider",
        label="a silver garden spider",
        kind="spider",
        helps_with={"silver_thread"},
        power=2,
        entrance="From a fern tip came a silver garden spider, who bowed and offered a satchel full of strong silk.",
        assist="the spider spun one last brave strand and fastened the line before it could snap",
        fail_assist="the spider cast silk as fast as silk could fly, but it was not enough to catch bell and child together",
        tags={"spider", "silk"},
    ),
    "otter": HelperCfg(
        id="otter",
        label="an otter in a rushy cape",
        kind="otter",
        helps_with={"reed_raft", "stepping_song"},
        power=1,
        entrance="An otter in a rushy cape popped from the water, whiskers shining, and offered to shove, nudge, and steady anything that floated.",
        assist="the otter braced the path with both paws and kept the water from twisting it away",
        fail_assist="the otter splashed and shoved with all his might, but the crossing rolled under the bell's weight",
        tags={"otter", "water"},
    ),
    "wren": HelperCfg(
        id="wren",
        label="a little amber wren",
        kind="bird",
        helps_with={"stepping_song", "lantern_ladder"},
        power=1,
        entrance="A little amber wren fluttered down from a hawthorn branch and said she knew every safe note and every steady branch in the glen.",
        assist="the wren sang the true note at the true moment, and the whole crossing held still as if listening",
        fail_assist="the wren sang bravely, but song alone could not hold the shaking way",
        tags={"wren", "song"},
    ),
    "badger": HelperCfg(
        id="badger",
        label="a badger with a mossy tool-belt",
        kind="badger",
        helps_with={"lantern_ladder", "reed_raft"},
        power=2,
        entrance="Out of the roots lumbered a badger with a mossy tool-belt, already carrying pegs, cord, and a small wooden mallet.",
        assist="the badger drove the last peg deep and made the whole crossing answer with a solid thump",
        fail_assist="even the badger's pegs could not make the swaying crossing firm enough in time",
        tags={"badger", "tools"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Elsie", "Nessa", "Wren", "Ada", "Faye", "Iris"]
BOY_NAMES = ["Rowan", "Tobin", "Finn", "Milo", "Alder", "Pip", "Jory", "Nico"]


@dataclass
class StoryParams:
    realm: str
    obstacle: str
    method: str
    helper: str
    child1_name: str
    child1_type: str
    child2_name: str
    child2_type: str
    ruler_type: str
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


def pair_names(rng: random.Random) -> tuple[str, str, str, str]:
    t1 = rng.choice(["girl", "boy"])
    t2 = rng.choice(["girl", "boy"])
    n1 = rng.choice(GIRL_NAMES if t1 == "girl" else BOY_NAMES)
    pool = [n for n in (GIRL_NAMES if t2 == "girl" else BOY_NAMES) if n != n1]
    n2 = rng.choice(pool)
    return n1, t1, n2, t2


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    realm, obstacle, method, helper_cfg = f["realm"], f["obstacle"], f["method"], f["helper_cfg"]
    c1, c2 = f["child1"], f["child2"]
    if f["success"]:
        return [
            f'Write a fairy tale for a young child that includes the words "synthesize", "dub", and "stumble". Two friends in {realm.place} must carry a silver bell across {obstacle.label} with teamwork.',
            f"Tell a gentle fairy-tale story where {c1.label} and {c2.label} synthesize a plan with {helper_cfg.label}, one child stumbles in the middle, and the team saves the bell.",
            f"Write a teamwork fairy tale where a crossing is repaired with {method.label}, the danger turns on a stumble, and the ending gives the crossing a new name.",
        ]
    return [
        f'Write a fairy tale for a young child that includes the words "synthesize", "dub", and "stumble". Two friends in {realm.place} try to carry a silver bell across {obstacle.label}, but their plan is not strong enough.',
        f"Tell a wistful fairy tale where {c1.label} and {c2.label} work together with {helper_cfg.label}, but after a stumble the bell is lost and the village learns a careful lesson.",
        f"Write a teamwork fairy tale with a dangerous crossing, a brave but imperfect fix, and an ending where the place is given a warning name.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c1, c2 = f["child1"], f["child2"]
    realm, obstacle, method, helper_cfg = f["realm"], f["obstacle"], f["method"], f["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two young friends, {c1.label} and {c2.label}, who were carrying a silver bell through {realm.place}. They were trying to bring it to {realm.tower} before dawn.",
        ),
        (
            "What problem did they find on the way?",
            f"They found {obstacle.scene}. That meant they could not simply walk to the tower with the bell.",
        ),
        (
            "What plan did they make?",
            f"They stopped to synthesize a plan instead of rushing. With {helper_cfg.label}, they chose {method.qa_text}",
        ),
        (
            f"What happened in the middle of the crossing?",
            f"{c1.label} did stumble on {obstacle.footing}, and the bell tipped dangerously. That frightening moment is where the story turns from planning into action.",
        ),
    ]
    if f["success"]:
        qa.extend([
            (
                "How did teamwork help them?",
                f"{c2.label} caught {c1.label}, and {helper_cfg.label} gave the last bit of help that made the crossing hold. Because they acted together at the same moment, the bell stayed safe instead of falling.",
            ),
            (
                "How did the story end?",
                f"They reached the tower in time and rang the bell before sunrise. After that, the people would dub the crossing {method.label}, because teamwork had saved the morning there.",
            ),
        ])
    else:
        qa.extend([
            (
                "Why did they fail to save the bell?",
                f"They were brave and tried to help one another, but the crossing was still too weak for the danger. When {c1.label} stumbled, the team could not keep both child and bell secure at once.",
            ),
            (
                "How did the story end?",
                f"They climbed to the tower without the bell, and the realm woke late and quietly. Later the villagers would dub the place Second-Try Crossing, so everyone would remember to build a stronger way next time.",
            ),
        ])
    return qa


KNOWLEDGE = {
    "bridge": [
        (
            "Why can a broken bridge be dangerous?",
            "A broken bridge is dangerous because feet can slip through gaps or loose boards. If you carry something important while crossing it, you can fall or drop what you are holding.",
        )
    ],
    "brook": [
        (
            "Why are wet stones slippery?",
            "Wet stones can feel smooth and slick under your shoes. Water makes it easier for feet to slide instead of grip.",
        )
    ],
    "spider": [
        (
            "Why is spider silk useful?",
            "Spider silk is very thin, but some kinds are surprisingly strong for their size. In stories, people imagine it as a good thread for weaving or tying delicate things.",
        )
    ],
    "raft": [
        (
            "What does a raft do?",
            "A raft floats on water and can carry people or objects across a stream. It works best when it is broad and steady.",
        )
    ],
    "song": [
        (
            "Why do people sing while they work?",
            "Singing can help people keep the same rhythm together. When everyone moves in time, teamwork becomes easier.",
        )
    ],
    "tools": [
        (
            "Why are pegs and cords useful for building?",
            "Pegs hold pieces in place, and cords tie them together. Small fastening tools can make a structure much steadier.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another toward the same goal instead of each trying alone. A team can do hard things better when each member adds a different kind of help.",
        )
    ],
}

KNOWLEDGE_ORDER = ["bridge", "brook", "spider", "raft", "song", "tools", "teamwork"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["obstacle"].tags) | set(f["method"].tags) | set(f["helper_cfg"].tags) | {"teamwork"}
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
        if e.label and e.label != e.id:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        realm="moss_hollow",
        obstacle="broken_bridge",
        method="silver_thread",
        helper="spider",
        child1_name="Lina",
        child1_type="girl",
        child2_name="Rowan",
        child2_type="boy",
        ruler_type="fairy_queen",
    ),
    StoryParams(
        realm="moonmeadow",
        obstacle="misty_brook",
        method="stepping_song",
        helper="wren",
        child1_name="Mira",
        child1_type="girl",
        child2_name="Finn",
        child2_type="boy",
        ruler_type="king",
    ),
    StoryParams(
        realm="thistle_glen",
        obstacle="thorn_gap",
        method="lantern_ladder",
        helper="badger",
        child1_name="Elsie",
        child1_type="girl",
        child2_name="Tobin",
        child2_type="boy",
        ruler_type="fairy_queen",
    ),
    StoryParams(
        realm="moonmeadow",
        obstacle="misty_brook",
        method="reed_raft",
        helper="otter",
        child1_name="Pip",
        child1_type="boy",
        child2_name="Ada",
        child2_type="girl",
        ruler_type="king",
    ),
    StoryParams(
        realm="thistle_glen",
        obstacle="thorn_gap",
        method="silver_thread",
        helper="spider",
        child1_name="Nessa",
        child1_type="girl",
        child2_name="Milo",
        child2_type="boy",
        ruler_type="fairy_queen",
    ),
]


ASP_RULES = r"""
fits_method(O, M) :- works_for(M, O).
fits_helper(M, H) :- helps_with(H, M).
valid(R, O, M, H) :- realm(R), obstacle(O), method(M), helper(H), fits_method(O, M), fits_helper(M, H).

teamwork(M, H, Pm + Ph) :- chosen_method(M), chosen_helper(H), method_power(M, Pm), helper_power(H, Ph).
success :- chosen_obstacle(O), obstacle_risk(O, R), teamwork(_, _, T), T >= R.
outcome(saved) :- success.
outcome(late) :- not success.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid in REALMS:
        lines.append(asp.fact("realm", rid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("obstacle_risk", oid, obstacle.risk))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("method_power", mid, method.power))
        for oid in sorted(method.works_for):
            lines.append(asp.fact("works_for", mid, oid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("helper_power", hid, helper.power))
        for mid in sorted(helper.helps_with):
            lines.append(asp.fact("helps_with", hid, mid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_obstacle", params.obstacle),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_helper", params.helper),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale teamwork storyworld: two friends carry a dawn bell across a dangerous crossing."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--ruler", choices=["fairy_queen", "king"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.obstacle and args.method and args.helper:
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        helper = HELPERS[args.helper]
        if not (method_fits(obstacle, method) and helper_fits(method, helper)):
            raise StoryError(explain_rejection(obstacle, method, helper))

    combos = [
        c for c in valid_combos()
        if (args.realm is None or c[0] == args.realm)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.method is None or c[2] == args.method)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, obstacle, method, helper = rng.choice(sorted(combos))
    n1, t1, n2, t2 = pair_names(rng)
    ruler_type = args.ruler or rng.choice(["fairy_queen", "king"])
    return StoryParams(
        realm=realm,
        obstacle=obstacle,
        method=method,
        helper=helper,
        child1_name=n1,
        child1_type=t1,
        child2_name=n2,
        child2_type=t2,
        ruler_type=ruler_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    realm = REALMS[params.realm]
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    helper_cfg = HELPERS[params.helper]
    if not method_fits(obstacle, method) or not helper_fits(method, helper_cfg):
        raise StoryError(explain_rejection(obstacle, method, helper_cfg))

    world = tell(
        realm=realm,
        obstacle=obstacle,
        method=method,
        helper_cfg=helper_cfg,
        child1_name=params.child1_name,
        child1_type=params.child1_type,
        child2_name=params.child2_name,
        child2_type=params.child2_type,
        ruler_type=params.ruler_type,
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
    for s in range(60):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, obstacle, method, helper) combos:\n")
        for realm, obstacle, method, helper in combos:
            print(f"  {realm:13} {obstacle:14} {method:15} {helper}")
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
            header = (
                f"### {p.child1_name} & {p.child2_name}: {p.obstacle} with {p.method} "
                f"and {p.helper} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
