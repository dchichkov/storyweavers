#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/carburetor_mangle_lesson_learned_tall_tale.py
========================================================================

A standalone storyworld for a tall-tale workshop story: a child wants to make an
old laundry mangle run faster by borrowing power from a roaring farm engine with
a carburetor. The world enforces a simple piece of common sense: a cloth project
can be smoothed slowly and carefully, but forcing it through a mangle with too
much engine power can grab, stretch, and tear it. The lesson is not "never use a
mangle," but "big jobs need patient hands and the right speed."

This world generates complete tiny stories with a beginning, a risky middle turn,
and an ending image that proves what changed.
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
PATIENCE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "steady", "patient", "sensible"}


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
    can_mangle: bool = False
    powered: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    sky: str
    flourish: str
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
class Project:
    id: str
    label: str
    the: str
    phrase: str
    event: str
    image: str
    material: str
    fragility: int
    can_mangle: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class Engine:
    id: str
    label: str
    phrase: str
    boast: str
    carburetor_line: str
    torque: int
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
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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


def _r_grab(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["crooked_feed"] < THRESHOLD:
        return out
    speed = world.get("mangle").meters["speed"]
    if speed < THRESHOLD:
        return out
    sig = ("grab", int(speed), int(project.meters["crooked_feed"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["caught"] += 1
    project.meters["strain"] += speed
    for kid in world.kids():
        kid.memes["alarm"] += 1
    out.append("__caught__")
    return out


def _r_tear(world: World) -> list[str]:
    out: list[str] = []
    project = world.get("project")
    if project.meters["strain"] < 4:
        return out
    sig = ("tear", int(project.meters["strain"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    project.meters["torn"] += 1
    out.append("__torn__")
    return out


CAUSAL_RULES = [
    Rule(name="grab", tag="physical", apply=_r_grab),
    Rule(name="tear", tag="physical", apply=_r_tear),
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


def hazard_at_risk(project: Project, engine: Engine) -> bool:
    return project.can_mangle and engine.torque >= 2


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def snag_severity(project: Project, engine: Engine, delay: int) -> int:
    return project.fragility + engine.torque + delay


def is_saved(response: Response, project: Project, engine: Engine, delay: int) -> bool:
    return response.power >= snag_severity(project, engine, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    helper_older = relation == "siblings" and helper_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (3.0 if helper_older else 0.0)
    return helper_older and authority > PATIENCE_INIT


def predict_snag(world: World) -> dict:
    sim = world.copy()
    engine = sim.get("engine")
    mangle = sim.get("mangle")
    project = sim.get("project")
    mangle.meters["speed"] = engine.meters["drive_speed"]
    project.meters["crooked_feed"] += 1
    propagate(sim, narrate=False)
    return {
        "caught": project.meters["caught"] >= THRESHOLD,
        "torn": project.meters["torn"] >= THRESHOLD,
        "strain": project.meters["strain"],
    }


def introduce(world: World, setting: Setting, a: Entity, b: Entity, project: Project, engine: Engine) -> None:
    for kid in (a, b):
        kid.memes["pride"] += 1
    world.say(
        f"In {setting.place}, where {setting.sky}, {a.id} and {b.id} were helping get "
        f"{project.the} ready for {project.event}. Folks said it was so big that {setting.flourish}."
    )
    world.say(
        f"Beside the wall stood an old mangle with rollers wide as wagon wheels, and "
        f"near it waited {engine.phrase}. {engine.carburetor_line}"
    )


def wrinkle_problem(world: World, a: Entity, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["wrinkled"] = 1
    world.say(
        f"But {project.the} was still rumpled from one end to the other. "
        f"{a.id} ran a hand over the {project.material} and wished it would lie flat before supper."
    )


def tempt(world: World, a: Entity, engine: Engine) -> None:
    a.memes["impatience"] += 1
    world.say(
        f'{a.id} looked from the rollers to {engine.theory if False else engine.label}.'
    )


def tempt(world: World, a: Entity, engine: Engine) -> None:
    a.memes["impatience"] += 1
    world.say(
        f'{a.id} looked from the mangle to {engine.the}.'
        if False else
        f'{a.id} looked from the mangle to {engine.phrase} and grinned. '
        f'"Why crank by hand? We could belt it to that engine and have this job done before a rooster could clear its throat."'
    )


def warn(world: World, b: Entity, a: Entity, project: Project, engine: Engine, grownup: Entity) -> None:
    pred = predict_snag(world)
    b.memes["caution"] += 1
    world.facts["predicted_strain"] = pred["strain"]
    extra = ""
    if pred["caught"]:
        extra = f" It could catch {project.the} crooked and pull harder than hands can guide."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, {grownup.label_word} said the mangle likes a slow feed. '
        f'That {engine.label} has a carburetor full of brag and a belt full of hurry.{extra}"'
    )


def defy(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    world.say(
        f'"A little hurry never hurt a giant job," {a.id} said, and before {b.id} could catch a sleeve, '
        f"{a.pronoun()} looped the belt in place."
    )


def back_down(world: World, a: Entity, b: Entity, grownup: Entity, project: Project) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    a.memes["impatience"] = 0.0
    world.say(
        f'{a.id} opened {a.pronoun("possessive")} mouth to argue, then looked at {project.the} and sighed. '
        f'"All right," {a.pronoun()} said. "Big cloth can wait one more minute."'
    )
    world.say(
        f"They left the engine idling where it was and called {grownup.label_word} over to help guide the edges by hand."
    )


def engage_engine(world: World, engine: Entity, mangle: Entity, project: Entity) -> None:
    engine.meters["running"] = 1
    mangle.meters["speed"] = engine.meters["drive_speed"]
    project.meters["crooked_feed"] += 1
    propagate(world, narrate=False)


def snag(world: World, project: Project, engine: Engine) -> None:
    project_ent = world.get("project")
    engage_engine(world, world.get("engine"), world.get("mangle"), project_ent)
    world.say(
        f"The belt snapped tight. The rollers began to hum, then whir, then sing like a whole hive of hornets. "
        f"{project.The} slid in straight for half a breath, then one edge nipped sideways."
    )
    if project_ent.meters["caught"] >= THRESHOLD:
        world.say(
            f"In a blink the mangle grabbed {project.the}. {engine.label.capitalize()} tugged, the cloth bunched, "
            f"and a wrinkle rose up as tall as a fence rail."
        )


def alarm(world: World, b: Entity, project: Project, grownup: Entity) -> None:
    world.say(f'"Stop the mangle! {project.The} is caught!" {b.id} shouted.')
    world.say(f'"{grownup.label_word.upper()}!"')


def rescue(world: World, grownup: Entity, response: Response, project: Project) -> None:
    project_ent = world.get("project")
    project_ent.meters["caught"] = 0.0
    project_ent.meters["strain"] = 0.0
    world.get("mangle").meters["speed"] = 0.0
    body = response.text.replace("{project}", project.label)
    world.say(
        f"{grownup.label_word.capitalize()} came across the floor in three long steps and {body}."
    )
    world.say(
        f"When the rollers stopped, {project.the} sagged free with only a hard crease and a cloud of everybody's held breath."
    )


def rescue_fail(world: World, grownup: Entity, response: Response, project: Project) -> None:
    body = response.fail.replace("{project}", project.label)
    world.say(f"{grownup.label_word.capitalize()} hurried in and {body}.")
    world.say(
        f"But the rollers had already bitten too deep, and a tearing sound ran through the room like somebody ripping the sky."
    )


def lesson(world: World, grownup: Entity, a: Entity, b: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["relief"] += 1
    world.say("For one big second, nobody said a thing.")
    world.say(
        f'Then {grownup.label_word} laid a calm hand on the cloth. '
        f'"A mangle is for steady work, not racing work," {grownup.pronoun()} said. '
        f'"When you hurry a giant job, the giant part hurries back."'
    )
    world.say(
        f'{a.id} nodded at once, and {b.id} nodded too. They had heard the lesson in the clatter and felt it in their ribs.'
    )
    world.say(
        f"After that, they fed {project.the} through a little at a time, each edge guided by careful hands instead of swagger."
    )


def grim_lesson(world: World, grownup: Entity, a: Entity, b: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["lesson"] += 1
        kid.memes["sadness"] += 1
    world.say(
        f'{grownup.label_word.capitalize()} gathered the torn {project.material} in {grownup.pronoun("possessive")} arms. '
        f'"We can patch cloth," {grownup.pronoun()} said softly, "but we cannot patch back a foolish minute after it has run away."'
    )
    world.say(
        f"{a.id} and {b.id} helped stitch the piece into a shorter, humbler version, and neither one reached for speed before sense again."
    )


def safe_finish(world: World, a: Entity, b: Entity, project: Project) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"By sundown {project.the} lay smooth at last, broad and shining, with not a hungry wrinkle left in it."
    )
    world.say(
        f"When it was raised for {project.event}, it {project.image}. "
        f"{a.id} grinned at {b.id}, and this time the grin was slower and wiser."
    )


def patched_finish(world: World, project: Project) -> None:
    world.say(
        f"At {project.event}, the mended cloth still flew, only shorter than first planned and stitched with a seam everyone could see."
    )
    world.say(
        "Folks admired the patchwork anyway, because honest work shows its threads, and a remembered lesson can be brighter than bragging."
    )


def tell(
    setting: Setting,
    project: Project,
    engine_cfg: Engine,
    response: Response,
    instigator: str = "Bea",
    instigator_gender: str = "girl",
    helper: str = "Hank",
    helper_gender: str = "boy",
    trait: str = "careful",
    grownup_type: str = "aunt",
    delay: int = 0,
    instigator_age: int = 6,
    helper_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=instigator,
            kind="character",
            type=instigator_gender,
            role="instigator",
            age=instigator_age,
            attrs={"relation": relation},
            traits=["bold"],
        )
    )
    b = world.add(
        Entity(
            id=helper,
            kind="character",
            type=helper_gender,
            role="helper",
            age=helper_age,
            attrs={"relation": relation},
            traits=[trait],
        )
    )
    grownup = world.add(
        Entity(
            id="Grownup",
            kind="character",
            type=grownup_type,
            role="grownup",
            label="the grown-up",
        )
    )
    project_ent = world.add(
        Entity(
            id="project",
            type="cloth",
            label=project.label,
            can_mangle=project.can_mangle,
        )
    )
    engine = world.add(
        Entity(
            id="engine",
            type="engine",
            label=engine_cfg.label,
            powered=True,
        )
    )
    engine.meters["drive_speed"] = float(engine_cfg.torque)
    mangle = world.add(
        Entity(
            id="mangle",
            type="mangle",
            label="mangle",
        )
    )
    mangle.meters["speed"] = 0.0

    a.memes["patience"] = PATIENCE_INIT
    b.memes["caution"] = initial_caution(trait)

    world.facts.update(
        setting=setting,
        project_cfg=project,
        engine_cfg=engine_cfg,
        response=response,
        relation=relation,
    )

    introduce(world, setting, a, b, project, engine_cfg)
    wrinkle_problem(world, a, project)

    world.para()
    tempt(world, a, engine_cfg)
    warn(world, b, a, project, engine_cfg, grownup)

    averted = would_avert(relation, a.age, b.age, trait)

    if averted:
        back_down(world, a, b, grownup, project)
        world.para()
        lesson(world, grownup, a, b, project)
        world.para()
        safe_finish(world, a, b, project)
        outcome = "averted"
        saved = True
    else:
        defy(world, a, b)
        world.para()
        snag(world, project, engine_cfg)
        alarm(world, b, project, grownup)
        severity = snag_severity(project, engine_cfg, delay)
        project_ent.meters["severity"] = float(severity)
        saved = is_saved(response, project, engine_cfg, delay)
        world.para()
        if saved:
            rescue(world, grownup, response, project)
            lesson(world, grownup, a, b, project)
            world.para()
            safe_finish(world, a, b, project)
            outcome = "saved"
        else:
            rescue_fail(world, grownup, response, project)
            grim_lesson(world, grownup, a, b, project)
            world.para()
            patched_finish(world, project)
            outcome = "mangled"

    world.facts.update(
        instigator=a,
        helper=b,
        grownup=grownup,
        project=project_ent,
        outcome=outcome,
        saved=saved,
        delay=delay,
        severity=int(project_ent.meters["severity"]),
        caught=project_ent.meters["caught"] >= THRESHOLD or outcome in {"saved", "mangled"},
        torn=project_ent.meters["torn"] >= THRESHOLD or outcome == "mangled",
    )
    return world


SETTINGS = {
    "barn": Setting(
        id="barn",
        place="a red barn so roomy an echo needed boots to cross it",
        sky="the rafters held swallows and the dust danced like gold",
        flourish="three neighbors could have spread their own supper cloths on top and still found elbow room",
    ),
    "shed": Setting(
        id="shed",
        place="the fairground shed with doors wide enough for moonlight to drive through",
        sky="the morning blew in bright and loud",
        flourish="a dog could nap at one end and never hear what was muttered at the other",
    ),
    "washyard": Setting(
        id="washyard",
        place="the washyard behind the farmhouse, broad as a little kingdom",
        sky="clouds drifted overhead like slow sheep",
        flourish="the wind had room to rehearse a whole brass band before it reached the fence",
    ),
}

PROJECTS = {
    "banner": Project(
        id="banner",
        label="parade banner",
        the="the parade banner",
        phrase="a parade banner long enough to wink at both ends of town",
        event="the Founders' Day parade",
        image="rippled over Main Street like a sunrise with its mind made up",
        material="canvas",
        fragility=1,
        can_mangle=True,
        tags={"banner", "cloth", "mangle"},
    ),
    "picnic_cloth": Project(
        id="picnic_cloth",
        label="picnic cloth",
        the="the picnic cloth",
        phrase="a picnic cloth broad enough to seat a brass band and their sandwiches",
        event="the church picnic",
        image="covered the long tables like one clean cloud",
        material="linen",
        fragility=2,
        can_mangle=True,
        tags={"cloth", "mangle", "linen"},
    ),
    "kite_tail": Project(
        id="kite_tail",
        label="kite tail",
        the="the kite tail",
        phrase="a kite tail fit for a kite that could tug at the weather itself",
        event="the hilltop kite show",
        image="streamed behind the giant kite like a river learning how to fly",
        material="striped cloth",
        fragility=3,
        can_mangle=True,
        tags={"cloth", "mangle", "kite"},
    ),
    "wood_sign": Project(
        id="wood_sign",
        label="painted wood sign",
        the="the painted wood sign",
        phrase="a painted wood sign for the gate",
        event="the town fair",
        image="hung straight above the gate",
        material="board",
        fragility=1,
        can_mangle=False,
        tags={"sign"},
    ),
}

ENGINES = {
    "tractor": Engine(
        id="tractor",
        label="tractor",
        phrase="a blue tractor with a carburetor that coughed like thunder in a barrel",
        boast="could pull a stump and still ask for another",
        carburetor_line="Its carburetor gave a proud little snort every few breaths.",
        torque=3,
        tags={"tractor", "carburetor"},
    ),
    "pump_cart": Engine(
        id="pump_cart",
        label="pump cart",
        phrase="a wheezing pump cart whose carburetor rattled like a coffee can of bolts",
        boast="had opinions about every hill in the county",
        carburetor_line="Its carburetor rattled so hard the nail tins answered back.",
        torque=2,
        tags={"engine", "carburetor"},
    ),
    "harvest_truck": Engine(
        id="harvest_truck",
        label="harvest truck",
        phrase="a harvest truck with a carburetor grumble deep enough to shake loose old stories",
        boast="could drag a haystack if you promised it pie",
        carburetor_line="Even standing still, its carburetor sounded eager to race the horizon.",
        torque=4,
        tags={"truck", "carburetor"},
    ),
}

RESPONSES = {
    "cut_belt": Response(
        id="cut_belt",
        sense=3,
        power=8,
        text="slapped the clutch loose, slipped the belt off the rollers, and held the cloth fast before another inch could feed in",
        fail="slapped at the clutch and yanked at the belt, but the rollers had already pulled too much {project} through",
        qa_text="slipped the belt off and stopped the rollers before they could pull more cloth in",
        tags={"belt", "safety"},
    ),
    "brake_bar": Response(
        id="brake_bar",
        sense=3,
        power=6,
        text="dropped the brake bar, wedged the rollers still, and eased {project} backward inch by inch",
        fail="dropped the brake bar, but the heavy pull had already stretched the {project} past saving",
        qa_text="used the brake bar and worked the cloth backward inch by inch",
        tags={"brake", "safety"},
    ),
    "reverse_crank": Response(
        id="reverse_crank",
        sense=2,
        power=5,
        text="killed the drive and turned the mangle backward by hand until {project} came free",
        fail="turned the mangle backward by hand, but the cloth had already torn inside the rollers",
        qa_text="stopped the drive and turned the mangle backward by hand",
        tags={"mangle", "safety"},
    ),
    "yank_harder": Response(
        id="yank_harder",
        sense=1,
        power=2,
        text="grabbed both corners and yanked, which only made matters worse",
        fail="grabbed both corners and yanked, which only ripped the {project} faster",
        qa_text="pulled on the cloth by force",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Bea", "Molly", "June", "Nell", "Tess", "Lula", "Ada", "Pearl"]
BOY_NAMES = ["Hank", "Eli", "Wes", "Bo", "Cal", "Jude", "Milo", "Roy"]
TRAITS = ["careful", "steady", "patient", "sensible", "curious", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id in SETTINGS:
        for project_id, project in PROJECTS.items():
            for engine_id, engine in ENGINES.items():
                if hazard_at_risk(project, engine):
                    combos.append((setting_id, project_id, engine_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    project: str
    engine: str
    response: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    grownup: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    helper_age: int = 4
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
    "carburetor": [
        (
            "What is a carburetor?",
            "A carburetor is a part on some older engines that mixes air and fuel so the engine can run. If it sputters or coughs, the engine may not run smoothly.",
        )
    ],
    "mangle": [
        (
            "What is a mangle?",
            "A mangle is a machine with rollers that squeeze cloth flat or wring water out. Because the rollers pull strongly, hands and fabric must be kept careful and straight.",
        )
    ],
    "cloth": [
        (
            "Why can cloth tear in rollers?",
            "If cloth goes in crooked, one part gets pulled harder than another. That strain can stretch the fabric and then tear it.",
        )
    ],
    "safety": [
        (
            "What should you do if a machine grabs something?",
            "Stop the machine right away and call a grown-up. Pulling harder can make the problem worse because the machine is stronger than your hands.",
        )
    ],
    "tractor": [
        (
            "Why is a tractor too strong for some small jobs?",
            "A tractor is built to pull heavy things with a lot of force. That same force can ruin a delicate job if the work needs a slow, gentle touch instead.",
        )
    ],
    "engine": [
        (
            "Why do some jobs need to be done slowly?",
            "Slow work gives people time to guide the material and notice mistakes early. Fast work can turn a little problem into a big one before anyone can stop it.",
        )
    ],
    "banner": [
        (
            "What is a banner?",
            "A banner is a long piece of cloth with words or pictures on it, often carried or hung at a parade or celebration.",
        )
    ],
    "kite": [
        (
            "Why does a kite need a tail?",
            "A tail helps steady a kite in the air. It can keep the kite from wobbling and help it fly more smoothly.",
        )
    ],
    "linen": [
        (
            "What is linen?",
            "Linen is a woven cloth made from flax. It can feel smooth and strong, but it still needs careful handling.",
        )
    ],
}
KNOWLEDGE_ORDER = ["carburetor", "mangle", "safety", "cloth", "tractor", "engine", "banner", "kite", "linen"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young helpers"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    project = f["project_cfg"]
    engine = f["engine_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short tall-tale story for a 3-to-5-year-old that includes the words "carburetor" and "mangle". '
        f"The story should be about children preparing {project.the} for {project.event}."
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a tall tale where {a.id} wants to power a mangle with {engine.label}, but {b.id} talks {a.pronoun('object')} out of it before anything is ruined.",
            "Write a gentle Lesson Learned story where a child chooses patience over speed and ends with careful hands finishing the work.",
        ]
    if outcome == "mangled":
        return [
            base,
            f"Tell a cautionary tall tale where {a.id} hurries a giant cloth job, the mangle catches it, and the family must patch the damage after learning a lesson.",
            "Write a Lesson Learned story with a sad-but-safe ending that teaches that force and hurry can spoil delicate work.",
        ]
    return [
        base,
        f"Tell a tall tale where {a.id} rushes to power a mangle with {engine.label}, the cloth gets caught, and a calm grown-up stops the machine in time.",
        "Write a Lesson Learned story that turns a scary mistake into wiser, slower teamwork by the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    grownup = f["grownup"]
    project = f["project_cfg"]
    engine = f["engine_cfg"]
    response = f["response"]
    relation = f.get("relation", "siblings")
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, helping a grown-up prepare {project.the} for {project.event}. The story follows how they handled a giant job that needed patience.",
        ),
        (
            f"What problem did they have with {project.the}?",
            f"{project.The} was wrinkled and needed smoothing before {project.event}. That is why the old mangle seemed useful in the first place.",
        ),
        (
            f"Why did {b.id} warn {a.id} about the engine?",
            f"{b.id} warned that the mangle needed a slow, steady feed, but {engine.label} was too eager and too strong. A fast pull could catch the cloth crooked and strain it before anyone could guide it.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What did {a.id} do after the warning?",
                f"{a.id} gave up the fast idea and let the cloth be guided by hand instead. That choice kept the job calm, so nothing was caught or torn.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                "They learned that a giant job still needs gentle care. Going slower was what let them finish something grand without harming it.",
            )
        )
    elif f["outcome"] == "saved":
        body = response.qa_text.replace("{project}", project.label)
        qa.append(
            (
                "What happened when the machine started too fast?",
                f"The mangle caught the cloth crooked and began pulling it hard. That sudden strain is what made everyone shout for help.",
            )
        )
        qa.append(
            (
                f"How did the grown-up save {project.the}?",
                f"The grown-up {body}. That quick, sensible move stopped the strain before the cloth was ruined.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                "They learned that speed is not the same as skill. Careful hands solved the job after hurry had nearly spoiled it.",
            )
        )
    else:
        qa.append(
            (
                f"Why was {project.the} damaged?",
                f"It was fed too fast and got caught crooked in the mangle. The strong pull kept building strain until the cloth tore.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The family patched the damaged cloth and still used it for {project.event}, but everyone could see the seam. The ending shows that a foolish shortcut can leave a mark even after the work is mended.",
            )
        )
        qa.append(
            (
                "What lesson did the children learn?",
                "They learned that force and hurry can outrun good sense. After that day, they reached for patience before power.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["project_cfg"].tags) | set(f["engine_cfg"].tags)
    tags |= set(f["response"].tags)
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="barn",
        project="banner",
        engine="tractor",
        response="cut_belt",
        instigator="Bea",
        instigator_gender="girl",
        helper="Hank",
        helper_gender="boy",
        grownup="aunt",
        trait="careful",
        delay=0,
        instigator_age=6,
        helper_age=4,
        relation="siblings",
    ),
    StoryParams(
        setting="shed",
        project="picnic_cloth",
        engine="pump_cart",
        response="brake_bar",
        instigator="Roy",
        instigator_gender="boy",
        helper="Ada",
        helper_gender="girl",
        grownup="uncle",
        trait="steady",
        delay=0,
        instigator_age=7,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        setting="washyard",
        project="kite_tail",
        engine="harvest_truck",
        response="reverse_crank",
        instigator="Jude",
        instigator_gender="boy",
        helper="Pearl",
        helper_gender="girl",
        grownup="aunt",
        trait="curious",
        delay=2,
        instigator_age=7,
        helper_age=5,
        relation="siblings",
    ),
    StoryParams(
        setting="barn",
        project="banner",
        engine="tractor",
        response="cut_belt",
        instigator="Cal",
        instigator_gender="boy",
        helper="Wes",
        helper_gender="boy",
        grownup="father",
        trait="patient",
        delay=0,
        instigator_age=5,
        helper_age=7,
        relation="siblings",
    ),
]


def explain_rejection(project: Project, engine: Engine) -> str:
    if not project.can_mangle:
        return (
            f"(No story: {project.the} is made of {project.material}, so it does not belong in a mangle. "
            "Without a cloth project, there is no honest snag-and-lesson story here.)"
        )
    if engine.torque < 2:
        return (
            f"(No story: {engine.label} is not strong enough to create the fast-pull problem this world is about.)"
        )
    return "(No story: this combination does not create the right sort of workshop risk.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(resp.id for resp in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). A story should prefer safe machine-stopping moves. "
        f"Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.helper_age, params.trait):
        return "averted"
    saved = is_saved(RESPONSES[params.response], PROJECTS[params.project], ENGINES[params.engine], params.delay)
    return "saved" if saved else "mangled"


ASP_RULES = r"""
hazard(P,E) :- can_mangle(P), engine(E), torque(E,T), T >= 2.
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,P,E) :- setting(S), project(P), engine(E), hazard(P,E).

careful_now(T) :- trait(T), careful_trait(T).
init_caution(5) :- trait(T), careful_now(T).
init_caution(3) :- trait(T), not careful_now(T).
helper_older :- relation(siblings), instigator_age(IA), helper_age(HA), HA > IA.
bonus(3) :- helper_older.
bonus(0) :- not helper_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- helper_older, authority(A), patience_init(P), A > P.

severity(F + T + D) :- chosen_project(P), fragility(P,F), chosen_engine(E), torque(E,T), delay(D).
resp_power(P) :- chosen_response(R), power(R,P).
saved :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(saved) :- not averted, saved.
outcome(mangled) :- not averted, not saved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, project in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        if project.can_mangle:
            lines.append(asp.fact("can_mangle", pid))
        lines.append(asp.fact("fragility", pid, project.fragility))
    for eid, engine in ENGINES.items():
        lines.append(asp.fact("engine", eid))
        lines.append(asp.fact("torque", eid, engine.torque))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("patience_init", int(PATIENCE_INIT)))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
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
            asp.fact("chosen_project", params.project),
            asp.fact("chosen_engine", params.engine),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
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
    for s in range(200):
        try:
            cases.append(resolve_params(parser.parse_args([]), random.Random(s)))
        except StoryError:
            continue

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty during verify.")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=False, qa=True, header="smoke")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a child, a carburetor, a mangle, and a lesson about patient work."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--engine", choices=ENGINES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--grownup", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the rollers pull before help takes hold")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.project and not PROJECTS[args.project].can_mangle:
        engine = ENGINES[args.engine] if args.engine else next(iter(ENGINES.values()))
        raise StoryError(explain_rejection(PROJECTS[args.project], engine))
    if args.project and args.engine:
        project = PROJECTS[args.project]
        engine = ENGINES[args.engine]
        if not hazard_at_risk(project, engine):
            raise StoryError(explain_rejection(project, engine))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.project is None or combo[1] == args.project)
        and (args.engine is None or combo[2] == args.engine)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, project, engine = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    instigator, ig = _pick_child(rng)
    helper, hg = _pick_child(rng, avoid=instigator)
    grownup = args.grownup or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        setting=setting,
        project=project,
        engine=engine,
        response=response,
        instigator=instigator,
        instigator_gender=ig,
        helper=helper,
        helper_gender=hg,
        grownup=grownup,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.project not in PROJECTS:
        raise StoryError(f"(Unknown project: {params.project})")
    if params.engine not in ENGINES:
        raise StoryError(f"(Unknown engine: {params.engine})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    project = PROJECTS[params.project]
    engine = ENGINES[params.engine]
    response = RESPONSES[params.response]

    if not hazard_at_risk(project, engine):
        raise StoryError(explain_rejection(project, engine))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        project=project,
        engine_cfg=engine,
        response=response,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        helper=params.helper,
        helper_gender=params.helper_gender,
        trait=params.trait,
        grownup_type=params.grownup,
        delay=params.delay,
        instigator_age=params.instigator_age,
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
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, project, engine) combos:\n")
        for setting, project, engine in combos:
            print(f"  {setting:9} {project:12} {engine}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.instigator} & {p.helper}: {p.project} with {p.engine} "
                f"({p.setting}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
