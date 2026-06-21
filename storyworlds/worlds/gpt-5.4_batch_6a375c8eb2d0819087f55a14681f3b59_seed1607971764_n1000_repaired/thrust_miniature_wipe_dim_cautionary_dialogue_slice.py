#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py
=================================================================================

A standalone story world about a child building a miniature scene in fading
household light, then trying an unsafe way to brighten a lamp. The world keeps
track of physical state (wet cloth, live lamp, spark, darkness) and emotional
state (joy, caution, fear, relief), and the prose follows those changes.

Core shape
----------
A child is making a miniature project at home. The lamp nearby has gone
wipe-dim with dust and sticky smudges, so the child wants better light. A wet
cleaning cloth seems like a quick fix, and the child is tempted to thrust it up
toward the still-plugged lamp. Another child warns that water and electricity do
not belong together. Either the warning is strong enough and the risky move is
averted, or the child goes ahead and a sharp spark pops from the lamp. A grown-up
then responds sensibly by unplugging the lamp and helping in a safer way. The
ending proves the lesson by showing the miniature project finished under safe,
gentle light.

Run it
------
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py --project village --method damp_cloth --lamp desk_lamp
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py --lamp window   # rejected
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py --response blow_on_it   # rejected
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py --all
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/thrust_miniature_wipe_dim_cautionary_dialogue_slice.py --verify
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
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "watchful"}


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
    electric: bool = False
    wet: bool = False
    portable_light: bool = False
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
class Project:
    id: str
    scene: str
    pieces: str
    hope: str
    ending: str
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
    phrase: str
    wet: bool
    action: str
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
class Lamp:
    id: str
    label: str
    place: str
    glow: str
    fragility: int
    electric: bool = True
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
class SafeLight:
    id: str
    label: str
    phrase: str
    shine: str
    portable: bool = True
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
        return [e for e in self.entities.values() if e.role in {"maker", "warning_child"}]

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


def _r_spark(world: World) -> list[str]:
    lamp = world.get("lamp")
    cloth = world.get("cloth")
    if lamp.meters["touched"] < THRESHOLD or cloth.wet is False or not lamp.electric or lamp.meters["plugged"] < THRESHOLD:
        return []
    sig = ("spark", lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["sparked"] += 1
    lamp.meters["brightness"] = 0.0
    world.get("room").meters["dark"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    return ["__spark__"]


def _r_break(world: World) -> list[str]:
    lamp = world.get("lamp")
    room = world.get("room")
    if lamp.meters["sparked"] < THRESHOLD:
        return []
    severity = lamp.meters["severity"]
    if severity < 2:
        return []
    sig = ("broken", lamp.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lamp.meters["broken"] += 1
    room.meters["dark"] += 1
    return ["__broken__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="spark", tag="physical", apply=_r_spark),
    Rule(name="break", tag="physical", apply=_r_break),
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


def hazard_at_risk(method: Method, lamp: Lamp) -> bool:
    return method.wet and lamp.electric


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(lamp: Lamp, delay: int) -> int:
    return lamp.fragility + delay


def is_contained(response: Response, lamp: Lamp, delay: int) -> bool:
    return response.power >= severity_of(lamp, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, maker_age: int, warning_age: int, trait: str) -> bool:
    older_sibling = relation == "siblings" and warning_age > maker_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older_sibling else 0.0)
    return older_sibling and authority > BOLDNESS_INIT


def predict_spark(world: World) -> dict:
    sim = world.copy()
    _do_risky_touch(sim, narrate=False)
    return {
        "spark": sim.get("lamp").meters["sparked"] >= THRESHOLD,
        "dark": sim.get("room").meters["dark"] >= THRESHOLD,
    }


def _do_risky_touch(world: World, narrate: bool = True) -> None:
    world.get("lamp").meters["touched"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, maker: Entity, helper: Entity, project: Project) -> None:
    maker.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"After supper, {maker.id} spread out paper scraps, bottle caps, and little bits of string on the rug. "
        f"{maker.pronoun().capitalize()} was building {project.scene}, a miniature world with {project.pieces}."
    )
    world.say(
        f'"When this part is done," {maker.id} said, "{project.hope}."'
    )


def fading_light(world: World, maker: Entity, lamp: Lamp) -> None:
    world.say(
        f"Beside the rug stood {lamp.place}. Its light had gone wipe-dim, {lamp.glow}, "
        f"so the tiny corners of the project were hard to see."
    )
    world.say(
        f'"I can hardly see the little pieces," {maker.id} said.'
    )


def tempt(world: World, maker: Entity, method: Method) -> None:
    maker.memes["boldness"] += 1
    world.say(
        f"{maker.id} picked up {method.phrase} and looked up at the lamp. "
        f'"I will just {method.action}," {maker.pronoun()} said.'
    )
    world.say(
        "The quick idea felt easy for one second."
    )


def warn(world: World, helper: Entity, maker: Entity, method: Method, parent: Entity) -> None:
    pred = predict_spark(world)
    helper.memes["caution"] += 1
    world.facts["predicted_spark"] = pred["spark"]
    helper_extra = ""
    if helper.memes["caution"] >= 6:
        helper_extra = f" {helper.pronoun().capitalize()} took one step closer, already worried."
    world.say(
        f'"Wait," {helper.id} said. "{method.warning} Let {parent.label_word} help instead."{helper_extra}'
    )


def defy(world: World, maker: Entity, helper: Entity, method: Method) -> None:
    maker.memes["defiance"] += 1
    older_maker = maker.attrs.get("relation") == "siblings" and maker.age > helper.age
    if older_maker:
        world.say(
            f'"It will only take a tiny second," {maker.id} said. Because {maker.pronoun()} was the older sibling, '
            f"{helper.id} could not stop {maker.pronoun('object')}. {maker.id} stretched up and began to thrust "
            f"{method.phrase} toward the lamp."
        )
    else:
        world.say(
            f'"It will only take a tiny second," {maker.id} said, and began to thrust {method.phrase} toward the lamp.'
        )


def back_down(world: World, maker: Entity, helper: Entity, parent: Entity, project: Project) -> None:
    maker.memes["boldness"] = 0.0
    maker.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f'{maker.id} stopped with {maker.pronoun("possessive")} hand halfway up. '
        f'"You are right," {maker.pronoun()} said. "I do not want a spark."'
    )
    world.say(
        f"They set the cloth down and called for {parent.label_word}. Soon the project was waiting safely on the rug, "
        f"and nobody had to jump or reach near the lamp."
    )
    world.facts["project_pause"] = project.ending


def spark(world: World, maker: Entity, method: Method, lamp: Lamp) -> None:
    _do_risky_touch(world, narrate=True)
    world.say(
        f"The wet edge of {method.label} brushed the metal near the bulb. There was a sharp pop, a blue wink, "
        f"and {lamp.label} went dark at once."
    )
    world.say(
        f'"Oh!" {maker.id} gasped.'
    )


def alarm(world: World, helper: Entity, parent: Entity) -> None:
    world.say(f'"{parent.label_word.capitalize()}!" {helper.id} called. "Please come help!"')


def rescue(world: World, parent: Entity, response: Response, lamp: Entity) -> None:
    lamp.meters["plugged"] = 0.0
    lamp.meters["danger"] = 0.0
    body = response.text
    world.say(
        f"{parent.label_word.capitalize()} came quickly and {body}."
    )
    world.say(
        "The room stayed quiet except for everyone's breathing."
    )


def lesson(world: World, parent: Entity, maker: Entity, helper: Entity, method: Method) -> None:
    for kid in (maker, helper):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["love"] += 1
    world.say(
        f'{parent.label_word.capitalize()} knelt beside them. "I am glad you called me," {parent.pronoun()} said. '
        f'"Wet things and plugged-in lamps do not mix. Even a small job can turn scary fast."'
    )
    world.say(
        f'"Next time," {helper.id} whispered, "we ask first."'
    )
    world.say(
        f'"Next time," {maker.id} agreed.'
    )


def rescue_fail(world: World, parent: Entity, response: Response, lamp: Entity) -> None:
    lamp.meters["plugged"] = 0.0
    lamp.meters["broken"] += 1
    world.get("room").meters["dark"] += 1
    world.say(
        f"{parent.label_word.capitalize()} hurried over and {response.fail}."
    )
    world.say(
        f"But the bulb was already ruined, and the room stayed dim."
    )


def sadder_lesson(world: World, parent: Entity, maker: Entity, helper: Entity) -> None:
    for kid in (maker, helper):
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{parent.label_word.capitalize()} put an arm around both children. "You are safe, and that matters most," '
        f'{parent.pronoun()} said. "But now the lamp needs a new bulb because water touched something electric."'
    )


def safe_finish(world: World, parent: Entity, maker: Entity, helper: Entity,
                project: Project, light1: SafeLight, light2: SafeLight) -> None:
    for kid in (maker, helper):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then {parent.label_word} brought {light1.phrase} and {light2.phrase}. "
        f"{light1.phrase.capitalize()} {light1.shine}, and the other {light2.shine}."
    )
    world.say(
        f'"There," {parent.pronoun()} said. "Now your hands can stay low and your light can stay safe."'
    )
    world.say(
        f"{helper.id} held one light steady while {maker.id} set the last piece in place. "
        f"Soon {project.ending}."
    )


def tell(project: Project, method: Method, lamp_cfg: Lamp, lights: tuple[SafeLight, SafeLight],
         response: Response, maker_name: str = "Lena", maker_gender: str = "girl",
         helper_name: str = "Owen", helper_gender: str = "boy", parent_type: str = "mother",
         trait: str = "careful", delay: int = 0, maker_age: int = 5, helper_age: int = 7,
         relation: str = "siblings") -> World:
    world = World()
    maker = world.add(Entity(
        id=maker_name,
        kind="character",
        type=maker_gender,
        role="maker",
        age=maker_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="warning_child",
        age=helper_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    room = world.add(Entity(id="room", type="room", label="the room"))
    lamp = world.add(Entity(
        id="lamp",
        type="lamp",
        label=lamp_cfg.label,
        electric=lamp_cfg.electric,
    ))
    cloth = world.add(Entity(
        id="cloth",
        type="cloth",
        label=method.label,
        wet=method.wet,
    ))
    world.add(Entity(id="project", type="project", label=project.id))
    l1, l2 = lights
    world.add(Entity(id="safe1", type="light", label=l1.label, portable_light=True))
    world.add(Entity(id="safe2", type="light", label=l2.label, portable_light=True))

    lamp.meters["plugged"] = 1.0
    lamp.meters["brightness"] = 1.0
    lamp.meters["severity"] = float(severity_of(lamp_cfg, delay))
    room.meters["dark"] = 0.0
    maker.memes["boldness"] = BOLDNESS_INIT
    helper.memes["caution"] = initial_caution(trait)
    world.facts["delay"] = delay

    introduce(world, maker, helper, project)
    fading_light(world, maker, lamp_cfg)

    world.para()
    tempt(world, maker, method)
    warn(world, helper, maker, method, parent)

    averted = would_avert(relation, maker_age, helper_age, trait)

    if averted:
        back_down(world, maker, helper, parent, project)
        world.para()
        safe_finish(world, parent, maker, helper, project, l1, l2)
        contained = True
    else:
        defy(world, maker, helper, method)
        world.para()
        spark(world, maker, method, lamp_cfg)
        alarm(world, helper, parent)
        contained = is_contained(response, lamp_cfg, delay)
        world.para()
        if contained:
            rescue(world, parent, response, lamp)
            lesson(world, parent, maker, helper, method)
            world.para()
            safe_finish(world, parent, maker, helper, project, l1, l2)
        else:
            rescue_fail(world, parent, response, lamp)
            sadder_lesson(world, parent, maker, helper)
            world.para()
            safe_finish(world, parent, maker, helper, project, l1, l2)

    outcome = "averted" if averted else ("contained" if contained else "broken")
    world.facts.update(
        maker=maker,
        helper=helper,
        parent=parent,
        project_cfg=project,
        method_cfg=method,
        lamp_cfg=lamp_cfg,
        response=response,
        lights=(l1, l2),
        outcome=outcome,
        sparked=lamp.meters["sparked"] >= THRESHOLD,
        broken=lamp.meters["broken"] >= THRESHOLD,
        relation=relation,
        promised=maker.memes["lesson"] >= THRESHOLD or averted,
    )
    return world


PROJECTS = {
    "village": Project(
        id="village",
        scene="a miniature village",
        pieces="paper houses, a pond made from foil, and two matchbox buses",
        hope="the bakery will sit right beside the bridge",
        ending="the miniature village glowed softly, with the bakery beside the bridge and a paper moon over the roofs",
        tags={"miniature"},
    ),
    "zoo": Project(
        id="zoo",
        scene="a miniature zoo",
        pieces="tiny ticket booths, folded-paper trees, and a shoebox lion house",
        hope="the little gate will open right in front of the monkey trees",
        ending="the miniature zoo shone under the safe lights, and the little gate stood straight in front of the monkey trees",
        tags={"miniature"},
    ),
    "station": Project(
        id="station",
        scene="a miniature train station",
        pieces="a cardboard platform, bottle-cap clocks, and a tunnel made from a tea box",
        hope="the last silver train will slide neatly into the tunnel",
        ending="the miniature station looked finished at last, with the silver train tucked neatly into the tunnel",
        tags={"miniature"},
    ),
}

METHODS = {
    "damp_cloth": Method(
        id="damp_cloth",
        label="the damp cloth",
        phrase="the damp cloth",
        wet=True,
        action="wipe the shade quickly",
        warning="That cloth is wet, and the lamp is still plugged in",
        tags={"wet_cloth", "electricity"},
    ),
    "soapy_wipe": Method(
        id="soapy_wipe",
        label="the soapy wipe",
        phrase="the soapy wipe",
        wet=True,
        action="wipe the dusty part in one quick swipe",
        warning="That wipe is wet and slippery, and the lamp is still plugged in",
        tags={"wet_cloth", "electricity"},
    ),
    "spray_rag": Method(
        id="spray_rag",
        label="the sprayed rag",
        phrase="the rag she had just sprayed with cleaner" ,
        wet=True,
        action="rub the lamp clean before anyone noticed",
        warning="That rag has cleaner on it, and cleaner should not touch a plugged-in lamp",
        tags={"wet_cloth", "electricity"},
    ),
    "dry_duster": Method(
        id="dry_duster",
        label="the dry duster",
        phrase="the dry duster",
        wet=False,
        action="dust the top in one sweep",
        warning="That duster is safer, but climbing and reaching should still wait for a grown-up",
        tags={"duster"},
    ),
}

LAMPS = {
    "desk_lamp": Lamp(
        id="desk_lamp",
        label="the desk lamp",
        place="a brass desk lamp by the couch",
        glow="with a gray ring of dust along the shade",
        fragility=1,
        electric=True,
        tags={"lamp", "electricity"},
    ),
    "bedside_lamp": Lamp(
        id="bedside_lamp",
        label="the bedside lamp",
        place="the bedside lamp on the low table",
        glow="where fingerprints had made the fabric shade look tired",
        fragility=1,
        electric=True,
        tags={"lamp", "electricity"},
    ),
    "clip_lamp": Lamp(
        id="clip_lamp",
        label="the clip lamp",
        place="a clip lamp fastened to the bookshelf",
        glow="with a dusty metal neck and a cloudy rim",
        fragility=2,
        electric=True,
        tags={"lamp", "electricity"},
    ),
    "window": Lamp(
        id="window",
        label="the window",
        place="the open window by the rug",
        glow="where evening had turned the glass pale",
        fragility=0,
        electric=False,
        tags={"window"},
    ),
}

SAFE_LIGHTS = {
    "flashlight": SafeLight(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        shine="clicked on bright and clear",
        portable=True,
        tags={"flashlight"},
    ),
    "lantern": SafeLight(
        id="lantern",
        label="lantern",
        phrase="a little battery lantern",
        shine="glowed warm as milk",
        portable=True,
        tags={"lantern"},
    ),
    "booklight": SafeLight(
        id="booklight",
        label="book light",
        phrase="a bendy book light",
        shine="curved over the project with a soft white beam",
        portable=True,
        tags={"booklight"},
    ),
}

RESPONSES = {
    "unplug_then_dry": Response(
        id="unplug_then_dry",
        sense=3,
        power=3,
        text="pulled the plug from the wall first, set the wet cloth aside, and checked the lamp before anyone touched it again",
        fail="pulled the plug and checked the lamp, but the bulb had already popped",
        qa_text="unplugged the lamp, moved the wet cloth away, and checked it safely",
        tags={"unplug", "electricity"},
    ),
    "switch_help": Response(
        id="switch_help",
        sense=3,
        power=2,
        text="switched the lamp off, unplugged it, and took over the cleaning with dry hands",
        fail="switched the lamp off and unplugged it, but the bulb was already gone",
        qa_text="switched the lamp off, unplugged it, and finished the job safely",
        tags={"unplug", "electricity"},
    ),
    "blow_on_it": Response(
        id="blow_on_it",
        sense=1,
        power=1,
        text="blew at the socket and hoped the light would come back",
        fail="blew at the socket, which did nothing useful at all",
        qa_text="blew at the lamp",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Lena", "Mia", "Nora", "Eva", "Iris", "June", "Ruby", "Tess"]
BOY_NAMES = ["Owen", "Max", "Theo", "Eli", "Sam", "Finn", "Ben", "Noah"]
TRAITS = ["careful", "steady", "sensible", "watchful", "curious", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_responses():
        return combos
    for project_id in PROJECTS:
        for method_id, method in METHODS.items():
            for lamp_id, lamp in LAMPS.items():
                if hazard_at_risk(method, lamp):
                    combos.append((project_id, method_id, lamp_id))
    return combos


@dataclass
class StoryParams:
    project: str
    method: str
    lamp: str
    light1: str
    light2: str
    response: str
    maker: str
    maker_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    delay: int = 0
    maker_age: int = 5
    helper_age: int = 7
    relation: str = "siblings"
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
    "miniature": [
        (
            "What does miniature mean?",
            "Miniature means very small, like a tiny copy of something bigger. A child can make a miniature town or zoo from paper and boxes."
        )
    ],
    "lamp": [
        (
            "What does a lamp do?",
            "A lamp gives light so you can see when a room is dim. It should be used carefully, especially when it plugs into the wall."
        )
    ],
    "electricity": [
        (
            "Why should wet cloths stay away from plugged-in lamps?",
            "Water and electricity are a dangerous mix. A wet cloth can help electricity jump where it should not go, which can cause a spark or break the lamp."
        )
    ],
    "wet_cloth": [
        (
            "Why can a wet cloth be risky around electric things?",
            "A wet cloth carries water to places that should stay dry. That is why a grown-up should unplug electric things before cleaning them."
        )
    ],
    "unplug": [
        (
            "What does unplug mean?",
            "To unplug something is to pull its plug out of the wall socket. That stops electricity from flowing into it."
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight a safe way to get more light?",
            "A flashlight uses batteries and can be moved close to your work. It gives light without needing a child to reach up near a plugged-in lamp."
        )
    ],
    "lantern": [
        (
            "What is a battery lantern?",
            "A battery lantern is a portable light that glows all around. It can brighten a table or rug without cords in the way."
        )
    ],
    "booklight": [
        (
            "What is a book light for?",
            "A book light is a small lamp that clips onto something and shines in one spot. It helps you see tiny details without lighting the whole room."
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    project = f["project_cfg"]
    method = f["method_cfg"]
    lamp = f["lamp_cfg"]
    if f["outcome"] == "averted":
        return [
            f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "thrust", "miniature", and "wipe-dim". A child making {project.scene} is stopped before doing something unsafe with {method.label} and {lamp.label}.',
            f"Tell a gentle dialogue-heavy story where {maker.id} wants to clean a wipe-dim lamp while building {project.scene}, but {helper.id} warns about electricity and helps avert the mistake.",
            f"Write a home story where the danger is prevented in time, and the ending shows the miniature project finished under safe light.",
        ]
    if f["outcome"] == "broken":
        return [
            f'Write a cautionary slice-of-life story that includes "thrust", "miniature", and "wipe-dim". A child uses {method.label} on {lamp.label}, a spark happens, and the lamp is left broken even though everyone stays safe.',
            f"Tell a dialogue story where a quick choice around a wipe-dim lamp goes wrong, a grown-up helps, and the children learn to ask first.",
            f"Write a gentle but serious story about a miniature project, a wet cloth, and a lesson learned after the room suddenly goes dark.",
        ]
    return [
        f'Write a slice-of-life cautionary story for a 3-to-5-year-old that includes the words "thrust", "miniature", and "wipe-dim". A child making {project.scene} tries an unsafe shortcut with {method.label}, and a grown-up fixes the problem.',
        f"Tell a dialogue-heavy story where {maker.id} wants better light for {project.scene}, ignores a warning, and then learns why {method.label} should not touch {lamp.label}.",
        f"Write a home story with a clear beginning, a sharp middle turn, and a safe ending that proves the children learned to ask for help.",
    ]


def pair_noun(maker: Entity, helper: Entity, relation: str) -> str:
    if relation == "siblings":
        if maker.type == "boy" and helper.type == "boy":
            return "two brothers"
        if maker.type == "girl" and helper.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    maker = f["maker"]
    helper = f["helper"]
    parent = f["parent"]
    project = f["project_cfg"]
    method = f["method_cfg"]
    lamp = f["lamp_cfg"]
    response = f["response"]
    light1, light2 = f["lights"]
    pair = pair_noun(maker, helper, f["relation"])
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {maker.id} and {helper.id}, and their {pw}. They are at home working on {project.scene} together."
        ),
        (
            "What was the child making?",
            f"{maker.id} was making {project.scene} with {project.pieces}. The tiny pieces are why better light mattered so much."
        ),
        (
            "Why did the lamp matter in the story?",
            f"The children needed light to see the small parts of the project. The lamp had gone wipe-dim, so the quick cleaning idea felt tempting."
        ),
        (
            f"What warning did {helper.id} give?",
            f"{helper.id} warned that {method.label} was wet and {lamp.label} was still plugged in. That mattered because water near electricity can cause a spark."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {maker.id} stop before touching the lamp?",
                f"{maker.id} listened to {helper.id} and realized the warning was right. Because they stopped in time, no spark happened and the project could continue safely."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"Their {pw} brought {light1.phrase} and {light2.phrase}, and the children finished the project under safe light. The ending shows they changed their plan instead of reaching toward the plugged-in lamp."
            )
        )
    elif f["outcome"] == "contained":
        qa.append(
            (
                "What happened when the wet cloth touched the lamp?",
                f"There was a pop and a spark, and the lamp went dark. The room felt scary for a moment because the risky shortcut had turned into a real problem."
            )
        )
        qa.append(
            (
                f"How did their {pw} help?",
                f"Their {pw} {response.qa_text}. That calm response stopped anyone from touching the lamp again while it was still unsafe."
            )
        )
        qa.append(
            (
                "What did the children learn?",
                f"They learned that wet things and plugged-in lamps do not mix. After the scare, they used safe portable lights instead of trying another shortcut."
            )
        )
    else:
        qa.append(
            (
                "Did the lamp work after the spark?",
                f"No. The bulb was already ruined, so the lamp stayed dark even after their {pw} made things safe. The children were safe, but the quick choice still had a cost."
            )
        )
        qa.append(
            (
                "How did the story still end safely?",
                f"Their {pw} comforted them and brought safe lights so the project could be finished without touching the lamp again. The ending is gentler because the children are safe, but it still proves the mistake mattered."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["project_cfg"].tags) | set(f["method_cfg"].tags) | set(f["lamp_cfg"].tags)
    tags |= set(f["response"].tags)
    for light in f["lights"]:
        tags |= set(light.tags)
    order = ["miniature", "lamp", "electricity", "wet_cloth", "unplug", "flashlight", "lantern", "booklight"]
    out: list[tuple[str, str]] = []
    for tag in order:
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
        flags = [name for name, on in (("electric", e.electric), ("wet", e.wet), ("portable_light", e.portable_light)) if on]
        if flags:
            bits.append(f"flags={flags}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        project="village",
        method="damp_cloth",
        lamp="desk_lamp",
        light1="flashlight",
        light2="lantern",
        response="unplug_then_dry",
        maker="Lena",
        maker_gender="girl",
        helper="Owen",
        helper_gender="boy",
        parent="mother",
        trait="careful",
        delay=0,
        maker_age=5,
        helper_age=7,
        relation="siblings",
    ),
    StoryParams(
        project="station",
        method="soapy_wipe",
        lamp="clip_lamp",
        light1="booklight",
        light2="lantern",
        response="switch_help",
        maker="Theo",
        maker_gender="boy",
        helper="Mia",
        helper_gender="girl",
        parent="father",
        trait="thoughtful",
        delay=1,
        maker_age=6,
        helper_age=6,
        relation="friends",
    ),
    StoryParams(
        project="zoo",
        method="spray_rag",
        lamp="clip_lamp",
        light1="flashlight",
        light2="booklight",
        response="switch_help",
        maker="Nora",
        maker_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="mother",
        trait="watchful",
        delay=1,
        maker_age=7,
        helper_age=5,
        relation="siblings",
    ),
    StoryParams(
        project="village",
        method="damp_cloth",
        lamp="bedside_lamp",
        light1="lantern",
        light2="booklight",
        response="unplug_then_dry",
        maker="Eli",
        maker_gender="boy",
        helper="June",
        helper_gender="girl",
        parent="father",
        trait="steady",
        delay=0,
        maker_age=4,
        helper_age=7,
        relation="siblings",
    ),
]


def explain_rejection(method: Method, lamp: Lamp) -> str:
    if not lamp.electric:
        return (
            f"(No story: {lamp.label} is not an electric lamp, so {method.label} cannot cause the spark this world is about. "
            f"Pick an electric lamp like desk_lamp, bedside_lamp, or clip_lamp.)"
        )
    if not method.wet:
        return (
            f"(No story: {method.label} is not wet, so this world has no honest water-and-electricity danger to model. "
            f"Pick a wet method like damp_cloth, soapy_wipe, or spray_rag.)"
        )
    return "(No story: this combination does not create the cautionary hazard.)"


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of the safer responses: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.maker_age, params.helper_age, params.trait):
        return "averted"
    response = RESPONSES[params.response]
    lamp = LAMPS[params.lamp]
    return "contained" if is_contained(response, lamp, params.delay) else "broken"


ASP_RULES = r"""
hazard(M, L) :- wet_method(M), electric_lamp(L).
sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.
valid(P, M, L) :- project(P), method(M), lamp(L), hazard(M, L).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).

older_sibling :- relation(siblings), maker_age(MA), helper_age(HA), HA > MA.
bonus(3) :- older_sibling.
bonus(0) :- not older_sibling.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- older_sibling, authority(A), boldness_init(B), A > B.

severity(F + D) :- chosen_lamp(L), fragility(L, F), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
contained :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(contained) :- not averted, contained.
outcome(broken) :- not averted, not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PROJECTS:
        lines.append(asp.fact("project", pid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        if method.wet:
            lines.append(asp.fact("wet_method", mid))
    for lid, lamp in LAMPS.items():
        lines.append(asp.fact("lamp", lid))
        if lamp.electric:
            lines.append(asp.fact("electric_lamp", lid))
        lines.append(asp.fact("fragility", lid, lamp.fragility))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
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

    scenario = "\n".join(
        [
            asp.fact("chosen_lamp", params.lamp),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("maker_age", params.maker_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.trait),
        ]
    )
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

    clingo_sensible = set(asp_sensible())
    python_sensible = {r.id for r in sensible_responses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible responses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError while resolving seed {seed}.")
            break
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="smoke")
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generate()/emit() succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a miniature project, a wipe-dim lamp, and a risky shortcut with a wet cloth."
    )
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--lamp", choices=LAMPS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra head start for the mishap; higher makes a broken bulb more likely")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include prompts and Q&A")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP model against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and args.lamp:
        method = METHODS[args.method]
        lamp = LAMPS[args.lamp]
        if not hazard_at_risk(method, lamp):
            raise StoryError(explain_rejection(method, lamp))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.project is None or combo[0] == args.project)
        and (args.method is None or combo[1] == args.method)
        and (args.lamp is None or combo[2] == args.lamp)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    project_id, method_id, lamp_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    light1, light2 = rng.sample(sorted(SAFE_LIGHTS), 2)
    maker_name, maker_gender = _pick_child(rng)
    helper_name, helper_gender = _pick_child(rng, avoid=maker_name)
    parent_type = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    relation = rng.choice(["siblings", "friends"])
    maker_age, helper_age = rng.sample([4, 5, 6, 7], 2)
    return StoryParams(
        project=project_id,
        method=method_id,
        lamp=lamp_id,
        light1=light1,
        light2=light2,
        response=response_id,
        maker=maker_name,
        maker_gender=maker_gender,
        helper=helper_name,
        helper_gender=helper_gender,
        parent=parent_type,
        trait=trait,
        delay=delay,
        maker_age=maker_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.project not in PROJECTS:
        raise StoryError(f"Unknown project: {params.project}")
    if params.method not in METHODS:
        raise StoryError(f"Unknown method: {params.method}")
    if params.lamp not in LAMPS:
        raise StoryError(f"Unknown lamp: {params.lamp}")
    if params.response not in RESPONSES:
        raise StoryError(f"Unknown response: {params.response}")
    if params.light1 not in SAFE_LIGHTS or params.light2 not in SAFE_LIGHTS:
        raise StoryError("Unknown safe light.")
    if params.light1 == params.light2:
        raise StoryError("Choose two different safe lights.")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"Unknown parent type: {params.parent}")
    method = METHODS[params.method]
    lamp = LAMPS[params.lamp]
    if not hazard_at_risk(method, lamp):
        raise StoryError(explain_rejection(method, lamp))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        project=PROJECTS[params.project],
        method=method,
        lamp_cfg=lamp,
        lights=(SAFE_LIGHTS[params.light1], SAFE_LIGHTS[params.light2]),
        response=RESPONSES[params.response],
        maker_name=params.maker,
        maker_gender=params.maker_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        trait=params.trait,
        delay=params.delay,
        maker_age=params.maker_age,
        helper_age=params.helper_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (project, method, lamp) combos:\n")
        for project_id, method_id, lamp_id in combos:
            print(f"  {project_id:8} {method_id:11} {lamp_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.maker} & {p.helper}: {p.project} with {p.method} at {p.lamp} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
