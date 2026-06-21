#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py
==================================================

A standalone storyworld for a small cautionary myth about a child who is warned
not to disturb a sacred fern at twilight. In some versions the child listens; in
others the child plucks a glowing frond and wakes the briars of the hill; in the
happiest endings a wise elder uses a proper old remedy and the grove is calmed.

The world is intentionally narrow. It models:
- a sacred place with a protective fern
- a tempting goal that seems helpful or pretty
- a warning from a companion who can foresee the danger
- a disturbance that wakes a mythic threat
- either obedience, successful repair, or a lingering loss

Run it
------
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py --fern moonfern --goal lantern
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py --goal basket
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py --all
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/fern_cautionary_myth.py --verify
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
AWE_INIT = 5.0
REVERENT_TRAITS = {"reverent", "careful", "thoughtful", "gentle"}


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
    sacred: bool = False
    thorny: bool = False
    luminous: bool = False
    # physical and emotional dimensions
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "crone", "sister"}
        male = {"boy", "man", "father", "elder", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mother",
            "father": "father",
            "elder": "elder",
            "crone": "elder",
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
class Place:
    id: str
    scene: str
    entry: str
    omen: str
    closing: str
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
class SacredFern:
    id: str
    label: str
    phrase: str
    glow: str
    law: str
    gift: str
    loss: str
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
class Goal:
    id: str
    want: str
    excuse: str
    carry: str
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
class Disturbance:
    id: str
    act: str
    wound: str
    consequence: str
    spread: int
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
class Remedy:
    id: str
    sense: int
    power: int
    method: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def children(self) -> list[Entity]:
        return [e for e in self.people() if e.role in {"seeker", "watcher"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
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


def _r_briar_rise(world: World) -> list[str]:
    out: list[str] = []
    fern = world.get("fern")
    briars = world.get("briars")
    hill = world.get("hill")
    if fern.meters["wounded"] >= THRESHOLD:
        sig = ("briar_rise",)
        if sig not in world.fired:
            world.fired.add(sig)
            briars.meters["awake"] += 1
            hill.meters["danger"] += 1
            for child in world.children():
                child.memes["fear"] += 1
            out.append("__briars__")
    return out


def _r_path_dim(world: World) -> list[str]:
    out: list[str] = []
    briars = world.get("briars")
    path = world.get("path")
    if briars.meters["awake"] >= THRESHOLD:
        sig = ("path_dim",)
        if sig not in world.fired:
            world.fired.add(sig)
            path.meters["blocked"] += 1
            out.append("__path__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="briar_rise", tag="physical", apply=_r_briar_rise),
    Rule(name="path_dim", tag="physical", apply=_r_path_dim),
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
        for sentence in produced:
            world.say(sentence)
    return produced


def danger_at_risk(goal: Goal, disturbance: Disturbance) -> bool:
    return disturbance.spread > 0 and goal.id in {"lantern", "garland", "proof"}


def sensible_remedies() -> list[Remedy]:
    return [r for r in REMEDIES.values() if r.sense >= SENSE_MIN]


def fern_severity(disturbance: Disturbance, delay: int) -> int:
    return disturbance.spread + delay


def is_soothed(remedy: Remedy, disturbance: Disturbance, delay: int) -> bool:
    return remedy.power >= fern_severity(disturbance, delay)


def initial_reverence(trait: str) -> float:
    return 5.0 if trait in REVERENT_TRAITS else 3.0


def would_refrain(relation: str, seeker_age: int, watcher_age: int, trait: str) -> bool:
    watcher_older = relation == "siblings" and watcher_age > seeker_age
    weight = initial_reverence(trait) + 1.0 + (4.0 if watcher_older else 0.0)
    return watcher_older and weight > AWE_INIT


def predict_disturbance(world: World) -> dict:
    sim = world.copy()
    _do_disturb(sim, narrate=False)
    return {
        "briars_awake": sim.get("briars").meters["awake"] >= THRESHOLD,
        "danger": sim.get("hill").meters["danger"],
        "path_blocked": sim.get("path").meters["blocked"] >= THRESHOLD,
    }


def _do_disturb(world: World, narrate: bool = True) -> None:
    fern = world.get("fern")
    fern.meters["wounded"] += 1
    fern.meters["glow_loss"] += 1
    propagate(world, narrate=narrate)


def open_myth(world: World, seeker: Entity, watcher: Entity, place: Place) -> None:
    seeker.memes["wonder"] += 1
    watcher.memes["wonder"] += 1
    world.say(
        f"In the old days, when evening still listened to small footsteps, {place.entry}"
    )
    world.say(
        f"{seeker.id} and {watcher.id} climbed together, and all around them {place.scene}."
    )


def show_fern(world: World, fern_cfg: SacredFern) -> None:
    world.say(
        f"At the crown of the hill grew {fern_cfg.phrase}. It {fern_cfg.glow}."
    )
    world.say(
        f"The old people of the valley always said, \"{fern_cfg.law}\""
    )


def need(world: World, seeker: Entity, goal: Goal) -> None:
    seeker.memes["desire"] += 1
    world.say(
        f"But that evening {seeker.id} had {goal.want}. {goal.excuse}"
    )


def tempt(world: World, seeker: Entity, goal: Goal, fern_cfg: SacredFern) -> None:
    seeker.memes["boldness"] += 1
    world.say(
        f'{seeker.id} looked at the fern and whispered, "If I take only one frond, '
        f'it can {goal.carry}."'
    )
    world.say(
        f"For one quick breath, the fern's pale light seemed like an answer waiting to be picked."
    )


def warn(world: World, watcher: Entity, seeker: Entity, helper: Entity, fern_cfg: SacredFern,
         disturbance: Disturbance) -> None:
    pred = predict_disturbance(world)
    watcher.memes["reverence"] += 1
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_path_blocked"] = pred["path_blocked"]
    extra = ""
    if watcher.memes["reverence"] >= 6:
        extra = f" {watcher.pronoun().capitalize()} held {seeker.id}'s sleeve and would not let go."
    world.say(
        f'{watcher.id} shook {watcher.pronoun("possessive")} head. "{helper.label_word.capitalize()} said '
        f'the fern keeps the hill quiet. If you {disturbance.act}, the briars will wake."{extra}'
    )


def back_down(world: World, seeker: Entity, watcher: Entity, helper: Entity,
              fern_cfg: SacredFern, goal: Goal) -> None:
    seeker.memes["relief"] += 1
    watcher.memes["relief"] += 1
    seeker.memes["boldness"] = 0.0
    world.say(
        f"{seeker.id} reached out, then stopped. The old warning felt heavier than the wish in "
        f"{seeker.pronoun('possessive')} hand."
    )
    world.say(
        f'Together the children turned away from the fern and walked down to ask {helper.label_word} '
        f'for help with {goal.id}.'
    )


def defy(world: World, seeker: Entity, watcher: Entity, relation: str) -> None:
    seeker.memes["defiance"] += 1
    older = relation == "siblings" and seeker.age > watcher.age
    if older:
        rel = "big brother" if seeker.type == "boy" else "big sister"
        world.say(
            f'"Only one," {seeker.id} said, and because {seeker.pronoun("subject")} was '
            f'{watcher.id}\'s {rel}, {watcher.id} could not stop {seeker.pronoun("object")}.'
        )
    else:
        world.say(
            f'"Only one," {seeker.id} said, and pulled free before {watcher.id} could stop '
            f'{seeker.pronoun("object")}.'
        )


def disturb(world: World, seeker: Entity, fern_cfg: SacredFern, disturbance: Disturbance) -> None:
    _do_disturb(world)
    world.say(
        f"{seeker.id} {disturbance.act}. At once {disturbance.wound}, and the hill gave a cold shiver."
    )
    world.say(
        f"{disturbance.consequence}"
    )


def alarm(world: World, watcher: Entity, helper: Entity) -> None:
    world.say(f'"Elder!" {watcher.id} cried. "Please come quickly!"')


def soothe(world: World, helper: Entity, remedy: Remedy, fern_cfg: SacredFern) -> None:
    world.get("briars").meters["awake"] = 0.0
    world.get("hill").meters["danger"] = 0.0
    world.get("path").meters["blocked"] = 0.0
    body = remedy.method.replace("{fern}", fern_cfg.label)
    world.say(
        f"{helper.label_word.capitalize()} came up the path without running, as if the old hill knew "
        f"{helper.pronoun('object')}. {helper.pronoun().capitalize()} {body}."
    )
    world.say(
        "The briars uncurled, the dark hush loosened, and the path shone pale between the stones again."
    )


def lesson(world: World, helper: Entity, seeker: Entity, watcher: Entity, fern_cfg: SacredFern) -> None:
    for child in (seeker, watcher):
        child.memes["fear"] = 0.0
        child.memes["relief"] += 1
        child.memes["lesson"] += 1
    world.say(
        f'"The hill does not keep treasures for greedy hands," {helper.label_word} said softly. '
        f'"{fern_cfg.gift}, but only while it is left in peace."'
    )
    world.say(
        f"{seeker.id} bowed {seeker.pronoun('possessive')} head, and {watcher.id} bowed too."
    )


def blessing_end(world: World, helper: Entity, seeker: Entity, watcher: Entity,
                 fern_cfg: SacredFern, goal: Goal, place: Place) -> None:
    for child in (seeker, watcher):
        child.memes["wonder"] += 1
        child.memes["safety"] += 1
    world.say(
        f"Then {helper.label_word} showed them a safer kindness: {fern_cfg.gift.lower()}."
    )
    if goal.id == "lantern":
        world.say(
            f"With that borrowed light, they found their way home without touching a single leaf."
        )
    elif goal.id == "garland":
        world.say(
            "They wove meadow grass instead, and the plain wreath smelled of wind and clean earth."
        )
    else:
        world.say(
            "They carried no stolen token at all, only the story of what the hill had spared."
        )
    world.say(place.closing)


def soothe_fail(world: World, helper: Entity, remedy: Remedy, fern_cfg: SacredFern) -> None:
    world.get("hill").meters["danger"] += 1
    world.get("path").meters["blocked"] += 1
    body = remedy.fail.replace("{fern}", fern_cfg.label)
    world.say(
        f"{helper.label_word.capitalize()} {body}."
    )
    world.say(
        "The briars lashed higher and stitched the hillside into a black wall of thorns."
    )


def loss_end(world: World, helper: Entity, seeker: Entity, watcher: Entity,
             fern_cfg: SacredFern, goal: Goal, place: Place) -> None:
    for child in (seeker, watcher):
        child.memes["lesson"] += 1
        child.memes["sorrow"] += 1
        child.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} led the children away by a longer road, and behind them "
        f"the hill stayed dark."
    )
    world.say(
        f"After that, no one in the valley picked from that place again. {fern_cfg.loss}"
    )
    world.say(
        f"So the tale was told to every child: leave sacred growing things where they belong, or beauty "
        f"will close its hand against you."
    )


def tell(place: Place, fern_cfg: SacredFern, goal: Goal, disturbance: Disturbance,
         remedy: Remedy, seeker_name: str = "Ivo", seeker_type: str = "boy",
         watcher_name: str = "Mira", watcher_type: str = "girl",
         trait: str = "reverent", helper_type: str = "elder", delay: int = 0,
         seeker_age: int = 6, watcher_age: int = 8, relation: str = "siblings") -> World:
    world = World(place)
    seeker = world.add(Entity(
        id=seeker_name,
        kind="character",
        type=seeker_type,
        role="seeker",
        traits=["curious"],
        age=seeker_age,
        attrs={"relation": relation},
    ))
    watcher = world.add(Entity(
        id=watcher_name,
        kind="character",
        type=watcher_type,
        role="watcher",
        traits=[trait],
        age=watcher_age,
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        role="elder",
        label="the elder",
    ))
    world.add(Entity(id="fern", type="fern", label=fern_cfg.label, sacred=True, luminous=True))
    world.add(Entity(id="briars", type="briars", label="the briars", thorny=True))
    world.add(Entity(id="hill", type="hill", label="the hill"))
    world.add(Entity(id="path", type="path", label="the path"))

    seeker.memes["awe"] = AWE_INIT
    watcher.memes["reverence"] = initial_reverence(trait)
    world.facts["relation"] = relation

    open_myth(world, seeker, watcher, place)
    show_fern(world, fern_cfg)

    world.para()
    need(world, seeker, goal)
    tempt(world, seeker, goal, fern_cfg)
    warn(world, watcher, seeker, helper, fern_cfg, disturbance)

    refrained = would_refrain(relation, seeker_age, watcher_age, trait)

    if refrained:
        back_down(world, seeker, watcher, helper, fern_cfg, goal)
        world.para()
        blessing_end(world, helper, seeker, watcher, fern_cfg, goal, place)
        severity = 0
        soothed = True
    else:
        defy(world, seeker, watcher, relation)
        world.para()
        disturb(world, seeker, fern_cfg, disturbance)
        alarm(world, watcher, helper)

        severity = fern_severity(disturbance, delay)
        world.get("fern").meters["severity"] = float(severity)
        soothed = is_soothed(remedy, disturbance, delay)

        world.para()
        if soothed:
            soothe(world, helper, remedy, fern_cfg)
            lesson(world, helper, seeker, watcher, fern_cfg)
            world.para()
            blessing_end(world, helper, seeker, watcher, fern_cfg, goal, place)
        else:
            soothe_fail(world, helper, remedy, fern_cfg)
            loss_end(world, helper, seeker, watcher, fern_cfg, goal, place)

    outcome = "refrained" if refrained else ("soothed" if soothed else "blighted")
    world.facts.update(
        place=place,
        fern_cfg=fern_cfg,
        goal=goal,
        disturbance=disturbance,
        remedy=remedy,
        seeker=seeker,
        watcher=watcher,
        helper=helper,
        wounded=world.get("fern").meters["wounded"] >= THRESHOLD,
        outcome=outcome,
        severity=severity,
        delay=delay,
    )
    return world


PLACES = {
    "moon_hill": Place(
        id="moon_hill",
        scene="silver grass bowed around old stones and a stream whispered below",
        entry="there was a hill where the moon came down first",
        omen="the air smelled of mint and rain",
        closing="And ever since then, the valley children have greeted the hill with open eyes and empty hands.",
        tags={"hill", "myth"},
    ),
    "hollow_glen": Place(
        id="hollow_glen",
        scene="the trees leaned close as if listening, and the moss kept the day's last gold",
        entry="there was a glen tucked inside a fold of the world",
        omen="no bird sang after sunset there",
        closing="So the glen stayed bright for the gentle and silent for the grasping.",
        tags={"glen", "myth"},
    ),
    "stone_ford": Place(
        id="stone_ford",
        scene="mist lay low on the water and the stepping stones shone like fish scales",
        entry="there was a ford where river spirits counted every footstep",
        omen="the reeds rattled with a warning music",
        closing="That is why the ford still gleams for travelers who pass with respect.",
        tags={"river", "myth"},
    ),
}

FERNS = {
    "moonfern": SacredFern(
        id="moonfern",
        label="moonfern",
        phrase="a moonfern older than the oldest roof in the valley",
        glow="held a white shimmer in every curling leaf",
        law="Take nothing from the moonfern, and the hill will light your way.",
        gift="It gives guidance, not ownership",
        loss="Its glow never again bent close to show the easiest path.",
        tags={"fern", "light", "sacred"},
    ),
    "dewfern": SacredFern(
        id="dewfern",
        label="dewfern",
        phrase="a dewfern whose fronds were edged with tiny stars of water",
        glow="gleamed as if dawn had hidden inside it and refused to leave",
        law="Pluck not the dewfern, and the briars will sleep at its roots.",
        gift="It lends calm to patient hearts",
        loss="The roots still lived, but the soft starry gleam was gone.",
        tags={"fern", "dew", "sacred"},
    ),
    "goldfern": SacredFern(
        id="goldfern",
        label="goldfern",
        phrase="a goldfern said to have sprung from one dropped sunbeam",
        glow="burned softly like banked fire without any heat",
        law="Leave the goldfern whole, and the old paths will stay open.",
        gift="It keeps roads open for those who wait",
        loss="Afterward the path twisted and lost itself among the stones.",
        tags={"fern", "path", "sacred"},
    ),
}

GOALS = {
    "lantern": Goal(
        id="lantern",
        want="grown dusk around them and wanted a little more light for the walk home",
        excuse="The way down looked dim between the rocks.",
        carry="shine like a lantern",
        tags={"light", "night"},
    ),
    "garland": Goal(
        id="garland",
        want="promised to bring home the prettiest thing on the hill",
        excuse="A festival waited in the valley below, and beauty felt like a prize to be carried away.",
        carry="sit in a garland brighter than meadow flowers",
        tags={"festival", "wreath"},
    ),
    "proof": Goal(
        id="proof",
        want="wished for a marvel to show the other children",
        excuse="It seemed easier to hold wonder in a hand than to describe it truthfully later.",
        carry="serve as proof that no story had been exaggerated",
        tags={"boast", "wonder"},
    ),
    "basket": Goal(
        id="basket",
        want="wanted something easy for the long walk back",
        excuse="But the fern was no help for carrying ordinary things, and the old danger would have no honest cause in this tale.",
        carry="line a berry basket",
        tags={"ordinary"},
    ),
}

DISTURBANCES = {
    "pluck": Disturbance(
        id="pluck",
        act="plucked a bright frond free",
        wound="the cut stem bled a thread of cold silver",
        consequence="From the roots, black briars stirred and began to creep across the stones.",
        spread=2,
        tags={"pluck", "briars"},
    ),
    "break": Disturbance(
        id="break",
        act="snapped the tallest frond at the stem",
        wound="the broken edge darkened as if a small night had opened there",
        consequence="A ring of thorn-vines lifted from the ground and hissed over the path.",
        spread=3,
        tags={"break", "briars"},
    ),
    "tear": Disturbance(
        id="tear",
        act="tore at the fern with both hands",
        wound="the leaves sagged at once and their light shivered out through the air",
        consequence="The sleeping thicket woke in a rush and lashed from root to root.",
        spread=3,
        tags={"tear", "briars"},
    ),
}

REMEDIES = {
    "return_frond": Remedy(
        id="return_frond",
        sense=3,
        power=3,
        method="laid the torn frond back at the root and sang the hill's old naming song until the fern's light knitted itself whole again",
        fail="laid the frond back and sang, but the wound in the {fern} had already gone too deep",
        qa_text="laid the frond back and sang the old naming song to soothe the fern",
        tags={"song", "repair"},
    ),
    "spring_water": Remedy(
        id="spring_water",
        sense=3,
        power=4,
        method="poured spring water around the roots and spoke a blessing older than the stones",
        fail="poured spring water at the roots, but the briars had already climbed beyond blessing",
        qa_text="poured spring water around the roots and spoke a blessing",
        tags={"water", "repair"},
    ),
    "ash_throw": Remedy(
        id="ash_throw",
        sense=1,
        power=1,
        method="threw cold hearth ash at the briars and hoped fear would drive them back",
        fail="threw cold ash at the briars, but wild thorns do not obey panic",
        qa_text="threw cold ash at the briars",
        tags={"ash", "poor_fix"},
    ),
}

GIRL_NAMES = ["Mira", "Tala", "Neri", "Ona", "Lina", "Sava", "Eda", "Runa"]
BOY_NAMES = ["Ivo", "Tarin", "Bram", "Eno", "Lior", "Pavel", "Rami", "Toma"]
TRAITS = ["reverent", "careful", "thoughtful", "gentle", "brave", "restless"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_remedies():
        return combos
    for place_id in PLACES:
        for fern_id in FERNS:
            for goal_id, goal in GOALS.items():
                if goal_id == "basket":
                    continue
                for dist_id, dist in DISTURBANCES.items():
                    if danger_at_risk(goal, dist):
                        combos.append((place_id, fern_id, goal_id))
                        break
    return combos


@dataclass
class StoryParams:
    place: str
    fern: str
    goal: str
    disturbance: str
    remedy: str
    seeker: str
    seeker_gender: str
    watcher: str
    watcher_gender: str
    helper: str
    trait: str
    delay: int = 0
    seeker_age: int = 6
    watcher_age: int = 8
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
    "fern": [(
        "What is a fern?",
        "A fern is a green plant with many feathery leaves called fronds. It does not make flowers like a rose does."
    )],
    "sacred": [(
        "What does sacred mean?",
        "Sacred means something is treated with special care and respect. People believe it should not be harmed or grabbed thoughtlessly."
    )],
    "briars": [(
        "What are briars?",
        "Briars are thorny plants with sharp stems. They can catch on clothes and scratch skin."
    )],
    "song": [(
        "Why do old stories use songs or blessings to fix trouble?",
        "In myths, songs and blessings often show respect for the world instead of force. They matter because the problem began when someone forgot to be respectful."
    )],
    "water": [(
        "Why is spring water special in many myths?",
        "Fresh spring water is often a symbol of life and cleansing in old tales. It can stand for making something right again."
    )],
    "light": [(
        "Why would someone want light at dusk?",
        "Dusk is when the day gets dim and the path becomes hard to see. A little light can help people walk safely."
    )],
    "wreath": [(
        "What is a garland?",
        "A garland is a ring or string made from leaves or flowers. People wear it or hang it as a decoration."
    )],
    "boast": [(
        "Why is showing off sometimes a bad reason to take something?",
        "Showing off can make a person grab first and think later. That can lead to harm when respect should come first."
    )],
}
KNOWLEDGE_ORDER = ["fern", "sacred", "briars", "light", "wreath", "boast", "song", "water"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two children"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    seeker, watcher = f["seeker"], f["watcher"]
    fern_cfg, goal = f["fern_cfg"], f["goal"]
    outcome = f["outcome"]
    if outcome == "refrained":
        return [
            f'Write a short cautionary myth for a young child that includes the word "fern" and ends with respect instead of theft.',
            f"Tell a mythic story where {seeker.id} wants to take from a sacred {fern_cfg.label} for {goal.id}, but {watcher.id} stops the mistake before harm begins.",
            f"Write a gentle old-style warning tale in which children leave a shining fern untouched and learn why sacred things must stay where they grow.",
        ]
    if outcome == "blighted":
        return [
            f'Write a cautionary myth that includes the word "fern" and has a sad ending after a child disobeys an old warning.',
            f"Tell a mythic story where {seeker.id} plucks from a sacred {fern_cfg.label}, wakes briars, and the place loses part of its blessing.",
            f"Write a warning tale about greed and disrespect in which beauty closes itself away after being taken.",
        ]
    return [
        f'Write a short cautionary myth that includes the word "fern" and shows a child learning respect after trouble begins.',
        f"Tell a mythic story where {seeker.id} disturbs a sacred {fern_cfg.label}, an elder uses an old remedy, and the children end wiser than before.",
        f"Write an old-fashioned warning tale with a frightened moment, a calm repair, and an ending image that proves the hill is peaceful again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    seeker, watcher, helper = f["seeker"], f["watcher"], f["helper"]
    fern_cfg, goal = f["fern_cfg"], f["goal"]
    remedy = f["remedy"]
    relation = f["relation"]
    pair = pair_noun(seeker, watcher, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {seeker.id} and {watcher.id}, and the elder who knows the hill's old law."
        ),
        (
            f"Why did {seeker.id} want to touch the fern?",
            f"{seeker.id} wanted to take a piece of the {fern_cfg.label} because {goal.excuse} {seeker.pronoun().capitalize()} thought one shining frond could help with {goal.id}. That wish made the forbidden idea feel useful for a moment."
        ),
        (
            f"What warning did {watcher.id} give?",
            f"{watcher.id} warned that the fern kept the hill quiet and that disturbing it would wake the briars. The warning came before the danger, because {watcher.pronoun()} understood the old rule."
        ),
    ]
    if f["outcome"] == "refrained":
        qa.append((
            f"Why did {seeker.id} stop before touching the fern?",
            f"{seeker.id} listened to the warning and felt the old law mattered more than the quick wish in {seeker.pronoun('possessive')} hand. Because the children turned back in time, the hill stayed peaceful."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the children leaving the fern alone and receiving help in a safer way. The last image shows respect changing what they carry home."
        ))
    elif f["outcome"] == "soothed":
        body = remedy.qa_text.replace("{fern}", fern_cfg.label)
        qa.append((
            "What happened when the fern was disturbed?",
            f"The fern was wounded and the sleeping briars woke up around the path. The hill turned dangerous because something sacred had been taken by force."
        ))
        qa.append((
            f"How did the elder calm the danger?",
            f"The elder {body}. That remedy worked because it answered harm with respect instead of more grabbing or panic."
        ))
        qa.append((
            "What did the children learn?",
            f"They learned that sacred gifts are not the same as things you own. After the fright, they understood that wonder must sometimes be left in its place."
        ))
    else:
        qa.append((
            "Could the elder fully fix the trouble?",
            "No. The elder tried, but the wound had gone too deep and the briars kept the place dark. The loss lasted, which is why the tale is told as a warning."
        ))
        qa.append((
            "What changed at the end of the story?",
            f"The hill lost part of its blessing, and people stopped picking from that place. The ending image proves that one greedy choice can change a beautiful thing for everyone."
        ))
        qa.append((
            "What is the lesson of the tale?",
            "The lesson is that sacred growing things should not be taken just because they seem useful or pretty. A selfish hand can close a gift that was meant to be shared only by looking."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"fern", "sacred", "briars"} | set(f["goal"].tags)
    if f["outcome"] == "soothed":
        tags |= set(f["remedy"].tags)
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
        flags = [n for n, on in (("sacred", ent.sacred), ("thorny", ent.thorny), ("luminous", ent.luminous)) if on]
        if flags:
            bits.append(f"flags={flags}")
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
        place="moon_hill",
        fern="moonfern",
        goal="lantern",
        disturbance="pluck",
        remedy="spring_water",
        seeker="Ivo",
        seeker_gender="boy",
        watcher="Mira",
        watcher_gender="girl",
        helper="elder",
        trait="reverent",
        delay=0,
        seeker_age=5,
        watcher_age=7,
        relation="siblings",
    ),
    StoryParams(
        place="hollow_glen",
        fern="dewfern",
        goal="garland",
        disturbance="pluck",
        remedy="return_frond",
        seeker="Tala",
        seeker_gender="girl",
        watcher="Eno",
        watcher_gender="boy",
        helper="elder",
        trait="careful",
        delay=0,
        seeker_age=7,
        watcher_age=5,
        relation="friends",
    ),
    StoryParams(
        place="stone_ford",
        fern="goldfern",
        goal="proof",
        disturbance="break",
        remedy="return_frond",
        seeker="Bram",
        seeker_gender="boy",
        watcher="Lina",
        watcher_gender="girl",
        helper="elder",
        trait="thoughtful",
        delay=1,
        seeker_age=7,
        watcher_age=6,
        relation="siblings",
    ),
    StoryParams(
        place="moon_hill",
        fern="goldfern",
        goal="lantern",
        disturbance="tear",
        remedy="spring_water",
        seeker="Neri",
        seeker_gender="girl",
        watcher="Rami",
        watcher_gender="boy",
        helper="elder",
        trait="gentle",
        delay=2,
        seeker_age=7,
        watcher_age=5,
        relation="friends",
    ),
    StoryParams(
        place="hollow_glen",
        fern="moonfern",
        goal="proof",
        disturbance="pluck",
        remedy="spring_water",
        seeker="Pavel",
        seeker_gender="boy",
        watcher="Ona",
        watcher_gender="girl",
        helper="elder",
        trait="reverent",
        delay=0,
        seeker_age=4,
        watcher_age=8,
        relation="siblings",
    ),
]


def explain_rejection(goal: Goal) -> str:
    if goal.id == "basket":
        return (
            "(No story: lining a berry basket with a fern is too ordinary for this cautionary myth. "
            "The tale needs a tempting reason that feels magical or urgent enough to awaken the old danger.)"
        )
    return "(No story: that choice does not create the right mythic danger.)"


def outcome_of(params: StoryParams) -> str:
    if would_refrain(params.relation, params.seeker_age, params.watcher_age, params.trait):
        return "refrained"
    remedy = REMEDIES[params.remedy]
    disturbance = DISTURBANCES[params.disturbance]
    return "soothed" if is_soothed(remedy, disturbance, params.delay) else "blighted"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, F, G) :- place(P), fern(F), goal(G), not ordinary_goal(G).
sensible(R)    :- remedy(R), sense(R, S), sense_min(M), S >= M.

% --- outcome inference -----------------------------------------------------
reverent_now(T) :- trait(T), is_reverent(T).
init_reverence(5) :- trait(T), reverent_now(T).
init_reverence(3) :- trait(T), not reverent_now(T).

watcher_older :- relation(siblings), seeker_age(SA), watcher_age(WA), WA > SA.
bonus(4)      :- watcher_older.
bonus(0)      :- not watcher_older.
weight(R + 1 + B) :- init_reverence(R), bonus(B).
refrained     :- watcher_older, weight(W), awe_init(A), W > A.

severity(Sp + D) :- chosen_disturbance(Ds), spread(Ds, Sp), delay(D).
remedy_power(P)  :- chosen_remedy(R), power(R, P).
soothed         :- remedy_power(P), severity(S), P >= S.

outcome(refrained) :- refrained.
outcome(soothed)   :- not refrained, soothed.
outcome(blighted)  :- not refrained, not soothed.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for fern_id in FERNS:
        lines.append(asp.fact("fern", fern_id))
    for goal_id in GOALS:
        lines.append(asp.fact("goal", goal_id))
        if goal_id == "basket":
            lines.append(asp.fact("ordinary_goal", goal_id))
    for dist_id, dist in DISTURBANCES.items():
        lines.append(asp.fact("disturbance", dist_id))
        lines.append(asp.fact("spread", dist_id, dist.spread))
    for remedy_id, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", remedy_id))
        lines.append(asp.fact("sense", remedy_id, remedy.sense))
        lines.append(asp.fact("power", remedy_id, remedy.power))
    for trait in sorted(REVERENT_TRAITS):
        lines.append(asp.fact("is_reverent", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("awe_init", int(AWE_INIT)))
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
        asp.fact("chosen_disturbance", params.disturbance),
        asp.fact("chosen_remedy", params.remedy),
        asp.fact("delay", params.delay),
        asp.fact("relation", params.relation),
        asp.fact("seeker_age", params.seeker_age),
        asp.fact("watcher_age", params.watcher_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {r.id for r in sensible_remedies()}
    asp_sens = set(asp_sensible())
    if py_sensible == asp_sens:
        print(f"OK: sensible remedies match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible remedies: clingo={sorted(asp_sens)} python={sorted(py_sensible)}")

    parser = build_parser()
    cases = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not mismatches:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("generated story was empty")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a cautionary myth about a sacred fern. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--fern", choices=FERNS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--disturbance", choices=DISTURBANCES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=["elder", "crone"], default=None)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="head start the briars get before the elder acts")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.goal:
        goal = GOALS[args.goal]
        if goal.id == "basket":
            raise StoryError(explain_rejection(goal))
    if args.remedy and REMEDIES[args.remedy].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing remedy '{args.remedy}': it scores too low on common sense "
            f"(sense={REMEDIES[args.remedy].sense} < {SENSE_MIN}). Try one of: "
            f"{', '.join(sorted(r.id for r in sensible_remedies()))}.)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.fern is None or combo[1] == args.fern)
        and (args.goal is None or combo[2] == args.goal)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, fern_id, goal_id = rng.choice(sorted(combos))
    disturbance_id = args.disturbance or rng.choice(sorted(DISTURBANCES))
    remedy_id = args.remedy or rng.choice(sorted(r.id for r in sensible_remedies()))
    seeker_name, seeker_gender = _pick_child(rng)
    watcher_name, watcher_gender = _pick_child(rng, avoid=seeker_name)
    helper_type = args.helper or rng.choice(["elder", "crone"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    seeker_age, watcher_age = rng.sample([4, 5, 6, 7, 8], 2)

    return StoryParams(
        place=place_id,
        fern=fern_id,
        goal=goal_id,
        disturbance=disturbance_id,
        remedy=remedy_id,
        seeker=seeker_name,
        seeker_gender=seeker_gender,
        watcher=watcher_name,
        watcher_gender=watcher_gender,
        helper=helper_type,
        trait=trait,
        delay=delay,
        seeker_age=seeker_age,
        watcher_age=watcher_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        fern_cfg = FERNS[params.fern]
        goal = GOALS[params.goal]
        disturbance = DISTURBANCES[params.disturbance]
        remedy = REMEDIES[params.remedy]
    except KeyError as exc:
        raise StoryError(f"(Unknown parameter value: {exc.args[0]})") from None

    if goal.id == "basket":
        raise StoryError(explain_rejection(goal))
    if remedy.sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing remedy '{params.remedy}': it scores too low on common sense for this world.)"
        )

    world = tell(
        place=place,
        fern_cfg=fern_cfg,
        goal=goal,
        disturbance=disturbance,
        remedy=remedy,
        seeker_name=params.seeker,
        seeker_type=params.seeker_gender,
        watcher_name=params.watcher,
        watcher_type=params.watcher_gender,
        trait=params.trait,
        helper_type=params.helper,
        delay=params.delay,
        seeker_age=params.seeker_age,
        watcher_age=params.watcher_age,
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
        print(f"sensible remedies: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, fern, goal) combos:\n")
        for place_id, fern_id, goal_id in combos:
            print(f"  {place_id:12} {fern_id:9} {goal_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
                f"### {p.seeker} & {p.watcher}: {p.fern} for {p.goal} "
                f"({p.place}, {p.disturbance}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
