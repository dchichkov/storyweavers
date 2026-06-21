#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py
===================================================================================

A standalone story world in a folk-tale mode: a village child must carry an
errand through a dark place watched by a sensitive guardian animal. The child
can try to dominate the crossing by hurry and force, or choose the fitting act
of courtesy and move gently. The world prefers the gentle act, predicts danger
before the turn, and tells either a safe crossing or a cautionary mishap.

Run it
------
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py --place bridge --courtesy hush_song
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py --place hill_steps --courtesy clover_gift --haste 1
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py --json
    python storyworlds/worlds/gpt-5.4/dominate_sensitive_inner_monologue_suspense_folk_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    fragile: bool = False
    edible: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother"}
        male = {"boy", "man", "grandfather", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
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
class Guardian:
    id: str
    label: str
    phrase: str
    sensitivity: str
    nature: str
    warning: str
    yield_text: str
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
class Place:
    id: str
    label: str
    path_text: str
    suspense_text: str
    guardian: str
    risk: int
    destination_text: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    need_text: str
    loss_text: str
    ending_text: str
    fragile: bool = False
    edible: bool = False
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
class Courtesy:
    id: str
    label: str
    soothes: str
    sense: int
    power: int
    act_text: str
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


def _r_yield(world: World) -> list[str]:
    guardian = world.get("guardian")
    if guardian.memes["trust"] < THRESHOLD:
        return []
    if guardian.memes["trust"] < guardian.memes["alarm"]:
        return []
    sig = ("yield", guardian.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("path").meters["open"] += 1
    guardian.memes["alarm"] = 0.0
    return ["__yield__"]


def _r_startle(world: World) -> list[str]:
    guardian = world.get("guardian")
    if guardian.memes["alarm"] <= guardian.memes["trust"]:
        return []
    sig = ("startle", guardian.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    cargo = world.get("cargo")
    child.memes["fear"] += 1
    cargo.meters["wobble"] += 1
    world.get("path").meters["blocked"] += 1
    return ["__startle__"]


def _r_drop(world: World) -> list[str]:
    cargo = world.get("cargo")
    if cargo.meters["wobble"] < THRESHOLD:
        return []
    sig = ("drop", cargo.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child = world.get("child")
    cargo.meters["lost"] += 1
    child.memes["sorrow"] += 1
    return ["__drop__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="yield", tag="social", apply=_r_yield),
    Rule(name="startle", tag="social", apply=_r_startle),
    Rule(name="drop", tag="physical", apply=_r_drop),
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
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


GUARDIANS = {
    "hound": Guardian(
        id="hound",
        label="black hound",
        phrase="a black hound with moonlit eyes",
        sensitivity="noise",
        nature="The hound was a sensitive watcher, troubled by sharp sounds on the hollow planks.",
        warning="If startled, it would leap sideways and turn the narrow crossing wild.",
        yield_text="The hound lowered its head, listened, and stepped aside from the middle plank.",
        tags={"hound", "noise", "gentleness"},
    ),
    "goose": Guardian(
        id="goose",
        label="white goose",
        phrase="a white goose standing like a gate carved from frost",
        sensitivity="sudden_motion",
        nature="The goose was a sensitive keeper, quick to flap and cry at sudden movement.",
        warning="If rushed, it would beat its wings and fill the gate with confusion.",
        yield_text="The goose folded its wings and opened a quiet lane between the stones.",
        tags={"goose", "movement", "gentleness"},
    ),
    "ram": Guardian(
        id="ram",
        label="old ram",
        phrase="an old ram with lantern-curled horns",
        sensitivity="challenge",
        nature="The ram was a sensitive creature in its own proud way, and hard eyes made it plant its hooves.",
        warning="If challenged, it would lower its horns and make the steep steps dangerous.",
        yield_text="The ram sniffed the offering, breathed out, and moved from the center of the stair.",
        tags={"ram", "challenge", "gentleness"},
    ),
}

PLACES = {
    "bridge": Place(
        id="bridge",
        label="Drum Bridge",
        path_text="At the edge of the village stood Drum Bridge, a wooden span over dark water.",
        suspense_text="Every plank gave a hollow note, and the river below kept swallowing the moon.",
        guardian="hound",
        risk=2,
        destination_text="On the far bank, the cottage window burned like a seed of gold.",
        tags={"bridge", "river", "night"},
    ),
    "orchard_gate": Place(
        id="orchard_gate",
        label="the Orchard Gate",
        path_text="Beyond the last cottage lay the Orchard Gate, where pear trees leaned over an old stone arch.",
        suspense_text="Leaves whispered over one another, and pale feathers glimmered between the trunks.",
        guardian="goose",
        risk=1,
        destination_text="Past the gate, the path curled to the elder's lamp among the trees.",
        tags={"orchard", "gate", "night"},
    ),
    "hill_steps": Place(
        id="hill_steps",
        label="the Hill Steps",
        path_text="Above the mill ran the Hill Steps, cut long ago into the dark side of the slope.",
        suspense_text="Mist dragged across the stones, and each step vanished into the one above it.",
        guardian="ram",
        risk=3,
        destination_text="At the top, the elder's roof sat under the moon like a folded cloak.",
        tags={"hill", "mist", "night"},
    ),
}

CARGOS = {
    "bread": Cargo(
        id="bread",
        label="round loaf",
        phrase="a round loaf wrapped in a warm cloth",
        need_text="the loaf for the elder's supper",
        loss_text="The loaf tumbled from the cloth and rolled into the reeds.",
        ending_text="The elder broke the loaf and shared the first sweet steam with the child.",
        fragile=False,
        edible=True,
        tags={"bread", "supper"},
    ),
    "herbs": Cargo(
        id="herbs",
        label="bundle of herbs",
        phrase="a bundle of bitter herbs tied with blue thread",
        need_text="the herbs for the elder's aching chest",
        loss_text="The blue thread snapped, and the herbs scattered over the wet stones.",
        ending_text="The elder hung the herbs by the hearth, and their clean smell filled the room.",
        fragile=False,
        edible=False,
        tags={"herbs", "healing"},
    ),
    "honey_jar": Cargo(
        id="honey_jar",
        label="honey jar",
        phrase="a little honey jar sealed with wax",
        need_text="the honey for the elder's dry cough",
        loss_text="The jar struck a stone, cracked, and poured a golden shine across the ground.",
        ending_text="The elder stirred the honey into tea until the cup smelled of summer fields.",
        fragile=True,
        edible=True,
        tags={"honey", "healing"},
    ),
}

COURTESIES = {
    "hush_song": Courtesy(
        id="hush_song",
        label="a hush-song",
        soothes="noise",
        sense=3,
        power=3,
        act_text="sang a low hush-song, so soft that it seemed to mend the air between the planks",
        qa_text="sang a low hush-song to steady the frightened guardian",
        tags={"song", "gentleness"},
    ),
    "slow_bow": Courtesy(
        id="slow_bow",
        label="a slow bow",
        soothes="sudden_motion",
        sense=3,
        power=2,
        act_text="set both feet still and gave a slow bow, moving as carefully as a leaf settling on water",
        qa_text="stopped still and bowed slowly so the startled guardian could see there was no threat",
        tags={"bow", "gentleness"},
    ),
    "clover_gift": Courtesy(
        id="clover_gift",
        label="a clover gift",
        soothes="challenge",
        sense=3,
        power=3,
        act_text="lowered those bold eyes, held out a sprig of clover, and waited without a tug on the rope",
        qa_text="offered clover and lowered those challenging eyes instead of pushing forward",
        tags={"clover", "gentleness"},
    ),
    "shout": Courtesy(
        id="shout",
        label="a sharp shout",
        soothes="noise",
        sense=1,
        power=0,
        act_text="shouted into the dark",
        qa_text="shouted at the guardian",
        tags={"noise"},
    ),
    "wave_stick": Courtesy(
        id="wave_stick",
        label="a waved stick",
        soothes="challenge",
        sense=1,
        power=0,
        act_text="waved a stick in the air",
        qa_text="waved a stick at the guardian",
        tags={"challenge"},
    ),
}

GIRL_NAMES = ["Mira", "Anya", "Lina", "Tessa", "Iria", "Nela", "Sora", "Petra"]
BOY_NAMES = ["Oren", "Toma", "Milan", "Ivo", "Rian", "Pavel", "Darin", "Luka"]
TRAITS = ["careful", "patient", "kind", "steady", "brave", "thoughtful"]


def valid_combo(place_id: str, courtesy_id: str) -> bool:
    if place_id not in PLACES or courtesy_id not in COURTESIES:
        return False
    place = PLACES[place_id]
    courtesy = COURTESIES[courtesy_id]
    guardian = GUARDIANS[place.guardian]
    return courtesy.sense >= SENSE_MIN and courtesy.soothes == guardian.sensitivity


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        guardian = GUARDIANS[place.guardian]
        for cargo_id in CARGOS:
            for courtesy_id, courtesy in COURTESIES.items():
                if courtesy.sense >= SENSE_MIN and courtesy.soothes == guardian.sensitivity:
                    combos.append((place_id, cargo_id, courtesy_id))
    return combos


def outcome_for(place: Place, courtesy: Courtesy, haste: int) -> str:
    return "safe" if courtesy.power >= place.risk + haste else "spilled"


def predict_mishap(world: World, haste: int) -> dict:
    sim = world.copy()
    guardian = sim.get("guardian")
    guardian.memes["trust"] = 0.0
    guardian.memes["alarm"] = float(sim.facts["place"].risk + max(1, haste))
    markers = propagate(sim, narrate=False)
    cargo = sim.get("cargo")
    return {
        "startled": "__startle__" in markers,
        "lost": cargo.meters["lost"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
    }


def introduce(world: World, child: Entity, elder: Entity, cargo_cfg: Cargo) -> None:
    world.say(
        f"In the old days, when the moon was treated like a listening lantern, "
        f"{child.id} lived in a village of mills and pear trees."
    )
    world.say(
        f"One evening, {child.pronoun('possessive')} {elder.label_word} needed "
        f"{cargo_cfg.need_text}, and no one else could go so quickly."
    )
    world.say(
        f"So {child.id} took {cargo_cfg.phrase} in both hands and set out before the night grew deeper."
    )


def approach(world: World, child: Entity, place: Place, guardian_cfg: Guardian) -> None:
    child.memes["resolve"] += 1
    world.say(place.path_text)
    world.say(place.suspense_text)
    world.say(
        f"There, in the narrow way, stood {guardian_cfg.phrase}. {guardian_cfg.nature}"
    )


def inner_warning(world: World, child: Entity, guardian_cfg: Guardian, prediction: dict) -> None:
    child.memes["worry"] += 1
    line = (
        f"{child.id} felt the night draw close and thought, "
        f'"If I try to dominate this moment, I will only make it worse."'
    )
    if prediction["lost"]:
        line += (
            f" {child.pronoun().capitalize()} imagined one rough step, one frightened spring, "
            f"and the errand gone into the dark."
        )
    world.say(line)
    world.say(
        f"Then another thought came, small but steady: "
        f'"This watcher is sensitive. I must be gentler than my fear."'
    )


def hurry(world: World, child: Entity, guardian: Entity, haste: int) -> None:
    if haste <= 0:
        return
    child.memes["urgency"] += float(haste)
    guardian.memes["alarm"] += float(haste)
    if haste == 1:
        world.say(
            f"But the elder's need tugged at {child.id}'s sleeves, and {child.pronoun()} almost stepped too fast."
        )
    else:
        world.say(
            f"The thought of being late beat in {child.id}'s ears like a drum, and for one dangerous breath "
            f"{child.pronoun()} nearly rushed the narrow way."
        )


def act_of_courtesy(world: World, child: Entity, guardian: Entity, courtesy: Courtesy) -> None:
    child.memes["kindness"] += 1
    guardian.memes["trust"] += float(courtesy.power)
    world.say(f"So {child.id} {courtesy.act_text}.")
    propagate(world, narrate=False)


def suspense_result(world: World, child: Entity, place: Place, guardian_cfg: Guardian, cargo_cfg: Cargo) -> None:
    guardian = world.get("guardian")
    cargo = world.get("cargo")
    path = world.get("path")
    if path.meters["open"] >= THRESHOLD:
        child.memes["relief"] += 1
        child.meters["crossed"] += 1
        cargo.meters["delivered"] += 1
        world.say(guardian_cfg.yield_text)
        world.say(
            f"{child.id} passed without another sound. {place.destination_text}"
        )
    elif cargo.meters["lost"] >= THRESHOLD:
        world.say(guardian_cfg.warning)
        world.say(cargo_cfg.loss_text)
    else:
        world.say(
            f"For a heartbeat, nothing moved at all, and even the moon seemed to wait."
        )


def deliver(world: World, child: Entity, elder: Entity, cargo_cfg: Cargo) -> None:
    child.memes["love"] += 1
    world.say(
        f"When {child.id} reached the door, {elder.label_word.capitalize()} opened it at once and drew "
        f"{child.pronoun('object')} into the firelight."
    )
    world.say(
        f"{cargo_cfg.ending_text} Then {elder.label_word} touched {child.id}'s brow and said, "
        f'"A gentle heart crosses where a hard one stumbles."'
    )
    world.say(
        f"After that night, whenever worry began to dominate {child.id}'s thoughts, "
        f"{child.pronoun()} remembered how softly the world sometimes had to be met."
    )


def loss_ending(world: World, child: Entity, elder: Entity, cargo_cfg: Cargo) -> None:
    child.memes["lesson"] += 1
    world.say(
        f"{child.id} stood very still, with empty hands and a hot face, while the dark water and stones kept their secret sounds."
    )
    world.say(
        f"{child.pronoun().capitalize()} went back to {elder.label_word}'s cottage and told the truth before any excuse could grow."
    )
    world.say(
        f"{elder.label_word.capitalize()} sighed, then wrapped a shawl around {child.pronoun('object')} and said, "
        f'"Better an honest child than a hidden lie. Next time, do not let hurry try to dominate your hands."'
    )
    world.say(
        f"Before dawn, neighbors brought what the house still needed, and {child.id} never again forgot "
        f"how a sensitive creature can be frightened by force."
    )


def tell(
    place: Place,
    cargo_cfg: Cargo,
    courtesy: Courtesy,
    child_name: str = "Mira",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "careful",
    haste: int = 0,
) -> World:
    guardian_cfg = GUARDIANS[place.guardian]
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="child",
        traits=[trait],
        attrs={},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        role="elder",
        label="the elder",
        attrs={},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type="guardian",
        label=guardian_cfg.label,
        role="guardian",
        attrs={"sensitivity": guardian_cfg.sensitivity},
    ))
    cargo = world.add(Entity(
        id="cargo",
        kind="thing",
        type="cargo",
        label=cargo_cfg.label,
        role="cargo",
        fragile=cargo_cfg.fragile,
        edible=cargo_cfg.edible,
        attrs={},
    ))
    path = world.add(Entity(
        id="path",
        kind="thing",
        type="path",
        label=place.label,
        role="path",
        attrs={},
    ))

    child.memes["resolve"] = 1.0 if trait in {"steady", "brave"} else 0.0
    child.memes["care"] = 1.0 if trait in {"careful", "patient", "kind", "thoughtful"} else 0.0
    guardian.memes["alarm"] = float(place.risk)
    guardian.memes["trust"] = 0.0
    world.facts.update(
        place=place,
        cargo_cfg=cargo_cfg,
        courtesy=courtesy,
        guardian_cfg=guardian_cfg,
        child=child,
        elder=elder,
        haste=haste,
    )

    introduce(world, child, elder, cargo_cfg)
    world.para()
    approach(world, child, place, guardian_cfg)
    prediction = predict_mishap(world, haste)
    world.facts["prediction"] = prediction
    inner_warning(world, child, guardian_cfg, prediction)
    hurry(world, child, guardian, haste)
    act_of_courtesy(world, child, guardian, courtesy)

    world.para()
    suspense_result(world, child, place, guardian_cfg, cargo_cfg)
    safe = world.get("path").meters["open"] >= THRESHOLD
    world.facts["outcome"] = "safe" if safe else "spilled"
    world.facts["guardian_alarm"] = guardian.memes["alarm"]
    world.facts["guardian_trust"] = guardian.memes["trust"]
    if safe:
        deliver(world, child, elder, cargo_cfg)
    else:
        loss_ending(world, child, elder, cargo_cfg)
    return world


@dataclass
class StoryParams:
    place: str
    cargo: str
    courtesy: str
    child_name: str
    child_gender: str
    elder_type: str
    trait: str
    haste: int = 0
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
    "gentleness": [(
        "Why can gentleness help with frightened animals?",
        "A frightened animal watches for danger. Slow, gentle behavior helps it notice that no harm is coming."
    )],
    "hound": [(
        "Why might a dog dislike a loud, hollow bridge?",
        "Echoing sounds can confuse or upset a dog because the noise seems to come from many places at once. A calm voice can make the place feel safer."
    )],
    "goose": [(
        "Why should you move slowly near a goose?",
        "Geese can flap and rush if they think something is charging at them. Slow movement gives them time to see you are not trying to scare them."
    )],
    "ram": [(
        "Why is staring at a ram a bad idea?",
        "A hard stare can feel like a challenge to a ram. Looking softer and giving it space can keep everyone safer."
    )],
    "bridge": [(
        "Why can a narrow bridge feel scary at night?",
        "At night you see less clearly and sounds seem bigger, so a bridge can feel more dangerous than it does in daylight."
    )],
    "orchard": [(
        "What is an orchard?",
        "An orchard is a place where fruit trees grow in rows. People care for the trees so they can bear fruit."
    )],
    "hill": [(
        "Why are steep stone steps slippery in mist?",
        "Mist leaves a little water on the stones. Wet stone can be slick under shoes or hooves."
    )],
    "bread": [(
        "Why would a warm loaf matter in a folk tale village?",
        "A fresh loaf is a real supper and a sign of care. Bringing bread can mean bringing comfort to a home."
    )],
    "herbs": [(
        "Why were herbs used in old stories for sickness?",
        "People often used herbs to make the air smell cleaner or to brew soothing drinks. In tales, carrying herbs often means carrying help."
    )],
    "honey": [(
        "Why is honey sometimes stirred into tea for a cough?",
        "Honey can coat a sore throat and make a warm drink taste soothing. That is why many stories pair honey with rest and care."
    )],
    "song": [(
        "Why can a soft song calm a tense moment?",
        "A soft song gives everyone one gentle sound to follow. It can slow breathing and make a frightening place feel less sharp."
    )],
    "bow": [(
        "What does a bow show in a story?",
        "A bow can show respect and peaceful intent. It tells the other person or creature that you are not rushing in to take over."
    )],
    "clover": [(
        "Why might an animal accept clover more easily than a push?",
        "Food offered calmly can feel friendly, while a shove feels like force. An animal often trusts a peaceful gift more than pressure."
    )],
}
KNOWLEDGE_ORDER = [
    "gentleness", "hound", "goose", "ram", "bridge", "orchard", "hill",
    "bread", "herbs", "honey", "song", "bow", "clover",
]


def generation_prompts(world: World) -> list[str]:
    place = world.facts["place"]
    cargo = world.facts["cargo_cfg"]
    courtesy = world.facts["courtesy"]
    child = world.facts["child"]
    outcome = world.facts["outcome"]
    prompts = [
        f'Write a folk-tale style story for a 3-to-5-year-old about a child carrying {cargo.label} through {place.label} at night. Include the words "dominate" and "sensitive".',
        f"Tell a suspenseful village tale where {child.id} meets a sensitive guardian and must use {courtesy.label} instead of force.",
    ]
    if outcome == "safe":
        prompts.append(
            "Write a gentle suspense story with inner monologue, where the child thinks through the danger, chooses kindness, and reaches the elder safely."
        )
    else:
        prompts.append(
            "Write a cautionary folk tale with inner monologue, where hurry almost makes the child try to dominate the moment, the errand is lost, and the lesson is learned."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    child = world.facts["child"]
    elder = world.facts["elder"]
    place = world.facts["place"]
    cargo = world.facts["cargo_cfg"]
    courtesy = world.facts["courtesy"]
    guardian_cfg = world.facts["guardian_cfg"]
    prediction = world.facts.get("prediction", {})
    outcome = world.facts["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who carried {cargo.phrase} through {place.label} at night for {child.pronoun('possessive')} {elder.label_word}. The story follows the choice {child.pronoun()} makes when a guardian blocks the way."
        ),
        (
            f"Why was {child.id} out so late?",
            f"{child.id} was bringing {cargo.need_text} to {elder.label_word}. That need is what made the dark journey feel urgent."
        ),
        (
            f"What made the moment suspenseful at {place.label}?",
            f"{guardian_cfg.phrase.capitalize()} stood in the narrow way, and the place itself felt dark and uncertain. The danger came from knowing one hurried move could frighten the guardian and ruin the errand."
        ),
        (
            f"What did {child.id} think to {child.pronoun('object')}self?",
            f"{child.id} thought that trying to dominate the moment would only make it worse. Then {child.pronoun()} reminded {child.pronoun('object')}self that the guardian was sensitive and needed gentleness."
        ),
    ]
    if prediction.get("lost"):
        qa.append((
            f"Why did {child.id} stop and think before moving?",
            f"{child.pronoun().capitalize()} imagined the cargo being lost if the guardian was startled. That inner warning helped {child.pronoun('object')} choose care over force."
        ))
    if outcome == "safe":
        qa.append((
            f"How did {child.id} get past the guardian?",
            f"{child.pronoun().capitalize()} {courtesy.qa_text}. Because that kindness matched what frightened the guardian, the path opened instead of turning wild."
        ))
        qa.append((
            f"How did the story end?",
            f"{child.id} reached {elder.label_word}'s house safely and delivered the errand. The ending shows that gentleness did what hurry could not."
        ))
    else:
        qa.append((
            f"What went wrong?",
            f"The guardian was still more alarmed than soothed, so the path became unsafe and the cargo was lost. Hurry mattered because it added fear before the kind act could fully work."
        ))
        qa.append((
            f"What lesson did {child.id} learn?",
            f"{child.pronoun().capitalize()} learned not to let hurry dominate {child.pronoun('possessive')} hands. The loss taught {child.pronoun('object')} that sensitive creatures need calm, not force."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    place = world.facts["place"]
    cargo = world.facts["cargo_cfg"]
    courtesy = world.facts["courtesy"]
    guardian_cfg = world.facts["guardian_cfg"]
    tags |= set(place.tags)
    tags |= set(cargo.tags)
    tags |= set(courtesy.tags)
    tags |= set(guardian_cfg.tags)
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place_id: str, courtesy_id: str) -> str:
    if place_id not in PLACES:
        return "(No story: unknown place.)"
    if courtesy_id not in COURTESIES:
        return "(No story: unknown courtesy.)"
    place = PLACES[place_id]
    courtesy = COURTESIES[courtesy_id]
    guardian = GUARDIANS[place.guardian]
    if courtesy.sense < SENSE_MIN:
        return (
            f"(Refusing courtesy '{courtesy_id}': it scores too low on common sense "
            f"(sense={courtesy.sense} < {SENSE_MIN}). This world prefers gentle, fitting acts.)"
        )
    return (
        f"(No story: {courtesy.label} does not suit {guardian.label}, who is sensitive to "
        f"{guardian.sensitivity.replace('_', ' ')}. Pick the courtesy that truly calms that guardian.)"
    )


def explain_haste(haste: int) -> str:
    return f"(No story: haste must be 0, 1, or 2, not {haste}.)"


CURATED = [
    StoryParams(
        place="bridge",
        cargo="bread",
        courtesy="hush_song",
        child_name="Mira",
        child_gender="girl",
        elder_type="grandmother",
        trait="careful",
        haste=0,
    ),
    StoryParams(
        place="orchard_gate",
        cargo="herbs",
        courtesy="slow_bow",
        child_name="Oren",
        child_gender="boy",
        elder_type="grandfather",
        trait="patient",
        haste=1,
    ),
    StoryParams(
        place="hill_steps",
        cargo="honey_jar",
        courtesy="clover_gift",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        trait="kind",
        haste=1,
    ),
    StoryParams(
        place="bridge",
        cargo="honey_jar",
        courtesy="hush_song",
        child_name="Luka",
        child_gender="boy",
        elder_type="grandfather",
        trait="steady",
        haste=2,
    ),
]


ASP_RULES = r"""
% reasonableness
valid(P,Cg,Co) :- place(P), cargo(Cg), courtesy(Co),
                  guarded_by(P,G), sensitive_to(G,S),
                  soothes(Co,S), sense(Co,N), sense_min(M), N >= M.

% outcome
severity(R + H) :- chosen_place(P), risk(P,R), haste(H).
safe :- chosen_courtesy(Co), power(Co,Pw), severity(Sv), Pw >= Sv.
outcome(safe) :- safe.
outcome(spilled) :- not safe.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("risk", place_id, place.risk))
        lines.append(asp.fact("guarded_by", place_id, place.guardian))
    for cargo_id in CARGOS:
        lines.append(asp.fact("cargo", cargo_id))
    for guardian_id, guardian in GUARDIANS.items():
        lines.append(asp.fact("guardian", guardian_id))
        lines.append(asp.fact("sensitive_to", guardian_id, guardian.sensitivity))
    for courtesy_id, courtesy in COURTESIES.items():
        lines.append(asp.fact("courtesy", courtesy_id))
        lines.append(asp.fact("soothes", courtesy_id, courtesy.soothes))
        lines.append(asp.fact("sense", courtesy_id, courtesy.sense))
        lines.append(asp.fact("power", courtesy_id, courtesy.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", params.place),
        asp.fact("chosen_courtesy", params.courtesy),
        asp.fact("haste", params.haste),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a village errand, a sensitive guardian, and a gentle crossing."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--courtesy", choices=COURTESIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["grandmother", "grandfather"])
    ap.add_argument("--name")
    ap.add_argument("--haste", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and smoke-test ordinary generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.haste is not None and args.haste not in {0, 1, 2}:
        raise StoryError(explain_haste(args.haste))
    if args.place and args.courtesy and not valid_combo(args.place, args.courtesy):
        raise StoryError(explain_rejection(args.place, args.courtesy))
    if args.courtesy and COURTESIES[args.courtesy].sense < SENSE_MIN:
        if args.place:
            raise StoryError(explain_rejection(args.place, args.courtesy))
        raise StoryError(
            f"(Refusing courtesy '{args.courtesy}': it scores too low on common sense "
            f"(sense={COURTESIES[args.courtesy].sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.courtesy is None or combo[2] == args.courtesy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cargo_id, courtesy_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    elder_type = args.elder or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    haste = args.haste if args.haste is not None else rng.randint(0, 2)
    return StoryParams(
        place=place_id,
        cargo=cargo_id,
        courtesy=courtesy_id,
        child_name=child_name,
        child_gender=gender,
        elder_type=elder_type,
        trait=trait,
        haste=haste,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.cargo not in CARGOS:
        raise StoryError(f"(No story: unknown cargo '{params.cargo}'.)")
    if params.courtesy not in COURTESIES:
        raise StoryError(f"(No story: unknown courtesy '{params.courtesy}'.)")
    if params.haste not in {0, 1, 2}:
        raise StoryError(explain_haste(params.haste))
    if not valid_combo(params.place, params.courtesy):
        raise StoryError(explain_rejection(params.place, params.courtesy))

    world = tell(
        place=PLACES[params.place],
        cargo_cfg=CARGOS[params.cargo],
        courtesy=COURTESIES[params.courtesy],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        trait=params.trait,
        haste=params.haste,
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
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure for seed {seed}.")
            break

    mismatches = [p for p in cases if asp_outcome(p) != outcome_for(PLACES[p.place], COURTESIES[p.courtesy], p.haste)]
    if not mismatches:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)} scenario outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_sample = generate(smoke_params)
        with io.StringIO() as buf, redirect_stdout(buf):
            emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: ordinary generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, courtesy) combos:\n")
        for place_id, cargo_id, courtesy_id in combos:
            print(f"  {place_id:13} {cargo_id:10} {courtesy_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name}: {p.place}, {p.cargo}, {p.courtesy}, "
                f"{outcome_for(PLACES[p.place], COURTESIES[p.courtesy], p.haste)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
