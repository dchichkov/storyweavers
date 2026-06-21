#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py
======================================================================

A standalone story world for a tiny "space adventure with transformation" tale.

Premise:
    A child explorer and a calm grown-up land in a strange place and need help
    with one hard job: see through the dark, cross a gap, or carry something
    heavy. They have found a mysterious candidate pod that might transform into
    exactly the helper they need -- but only if they wake it with the right kind
    of energy for that place.

Why the constraint exists:
    This world refuses weak "magic fix" stories. Each pod has a known safe
    energy source, and each place only offers some energies. A story is valid
    only when the chosen place affords the chosen energy and that energy can
    safely wake the chosen pod. The transformed helper must also match the
    mission need. Fewer solid variants are better than many vague ones.

The world model tracks:
    - physical meters: dark, gap, heavy, glow, bridge, carry, active
    - emotional memes: wonder, worry, relief, courage, trust, joy

Run it:
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py --site moon --mission crossing
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py --pod moth_pod --energy storm_charge
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/candidate_transformation_space_adventure.py --verify
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
        female = {"girl", "mother", "woman", "captain_f"}
        male = {"boy", "father", "man", "captain_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        if self.type in {"mother", "father", "captain_f", "captain_m"}:
            return "captain"
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
class Site:
    id: str
    place: str
    sky: str
    need: str
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
class Mission:
    id: str
    need_key: str
    opening: str
    worry: str
    solved_by: str
    success: str
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
class Pod:
    id: str
    label: str
    shell: str
    preferred_energy: str
    transforms_to: str
    wake_line: str
    safe_line: str
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
class Energy:
    id: str
    label: str
    phrase: str
    gentle: bool
    powers: set[str] = field(default_factory=set)
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
class HelperForm:
    id: str
    label: str
    solves: str
    arrival: str
    action: str
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


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
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
        clone = World(self.site)
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    mission = world.get("mission")
    if mission.meters["blocked"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    captain = world.get("captain")
    hero.memes["worry"] += 1
    captain.memes["care"] += 1
    out.append("__blocked__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    pod = world.get("pod")
    energy = world.get("energy")
    helper = world.get("helper")
    if pod.meters["charged"] < THRESHOLD or pod.meters["compatible"] < THRESHOLD:
        return out
    sig = ("transform",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.meters["active"] += 1
    helper.meters["ready"] += 1
    hero = world.get("hero")
    hero.memes["wonder"] += 1
    out.append("__transform__")
    if energy.attrs.get("gentle"):
        hero.memes["trust"] += 1
    return out


def _r_solve(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    mission = world.get("mission")
    if helper.meters["active"] < THRESHOLD:
        return out
    helper_skill = helper.attrs.get("solves", "")
    mission_need = mission.attrs.get("need_key", "")
    if helper_skill != mission_need:
        return out
    sig = ("solve", helper_skill)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mission.meters["blocked"] = 0.0
    mission.meters["solved"] += 1
    hero = world.get("hero")
    captain = world.get("captain")
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    hero.memes["courage"] += 1
    captain.memes["relief"] += 1
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="transform", tag="physical", apply=_r_transform),
    Rule(name="solve", tag="physical", apply=_r_solve),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combo(site: Site, mission: Mission, pod: Pod, energy: Energy) -> bool:
    if energy.id not in site.affords:
        return False
    if energy.id != pod.preferred_energy:
        return False
    helper_id = pod.transforms_to
    if helper_id not in HELPERS:
        return False
    return HELPERS[helper_id].solves == mission.need_key


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for site_id, site in SITES.items():
        for mission_id, mission in MISSIONS.items():
            for pod_id, pod in PODS.items():
                for energy_id, energy in ENERGIES.items():
                    if valid_combo(site, mission, pod, energy):
                        combos.append((site_id, mission_id, pod_id, energy_id))
    return combos


def explain_invalid(site: Site, mission: Mission, pod: Pod, energy: Energy) -> str:
    if energy.id not in site.affords:
        return (
            f"(No story: {site.place} does not offer {energy.label}, so the pod "
            f"cannot be charged there.)"
        )
    if energy.id != pod.preferred_energy:
        return (
            f"(No story: the {pod.label} wakes safely only with {ENERGIES[pod.preferred_energy].label}, "
            f"not {energy.label}.)"
        )
    helper = HELPERS[pod.transforms_to]
    if helper.solves != mission.need_key:
        return (
            f"(No story: the {pod.label} transforms into {helper.label}, which solves "
            f"{helper.solves}, not {mission.need_key}.)"
        )
    return "(No story: this combination is not reasonable in the world.)"


def predict_success(world: World) -> dict:
    sim = world.copy()
    sim.get("pod").meters["charged"] += 1
    sim.get("pod").meters["compatible"] += 1
    propagate(sim, narrate=False)
    mission = sim.get("mission")
    helper = sim.get("helper")
    return {
        "active": helper.meters["active"] >= THRESHOLD,
        "solved": mission.meters["solved"] >= THRESHOLD,
    }


def intro(world: World, hero: Entity, captain: Entity, site: Site) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"{hero.id} rode beside the captain in a bright little shuttle as they swept over {site.sky}. "
        f"At last they landed at {site.place}, where the ground looked full of secrets."
    )


def mission_setup(world: World, hero: Entity, captain: Entity, mission: Mission) -> None:
    mission_ent = world.get("mission")
    mission_ent.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(mission.opening)
    world.say(
        f'{hero.id} looked ahead and whispered, "{mission.worry}"'
    )


def find_pod(world: World, hero: Entity, pod: Pod) -> None:
    world.say(
        f"Near a silver rock, {hero.id} found {pod.shell}. Inside it rested a {pod.label}, "
        f"still and folded like a sleeping secret."
    )
    world.say(
        f'"Could this be our candidate helper?" {hero.id} asked.'
    )


def inspect(world: World, captain: Entity, hero: Entity, pod: Pod, energy: Energy) -> None:
    pred = predict_success(world)
    world.facts["predicted_active"] = pred["active"]
    world.facts["predicted_solved"] = pred["solved"]
    hero.memes["trust"] += 1
    world.say(
        f'The captain knelt beside the pod. "{pod.wake_line}," {captain.pronoun()} said. '
        f'"We should use {energy.phrase} and be gentle."'
    )


def charge(world: World, hero: Entity, captain: Entity, pod: Pod, energy: Energy) -> None:
    pod_ent = world.get("pod")
    energy_ent = world.get("energy")
    pod_ent.meters["charged"] += 1
    pod_ent.meters["compatible"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"Together they guided {energy.phrase} over the pod. The shell gave a small hum, "
        f"then a brighter one."
    )
    propagate(world, narrate=False)


def transform(world: World, hero: Entity, pod: Pod, helper: HelperForm) -> None:
    world.say(
        f"{pod.safe_line} The shell unfolded, bent, and shimmered. "
        f"{helper.arrival}"
    )


def solve_mission(world: World, hero: Entity, captain: Entity, mission: Mission, helper: HelperForm) -> None:
    world.say(helper.action)
    world.say(mission.success)
    world.say(
        f'{hero.id} laughed. "It really was the right candidate," {hero.pronoun()} said.'
    )


def ending(world: World, hero: Entity, captain: Entity, helper: HelperForm) -> None:
    world.say(
        f"When they climbed back into the shuttle, {helper.ending_image} "
        f"{hero.id} no longer felt small in the wide dark. {hero.pronoun().capitalize()} felt ready for the next star."
    )


def tell(
    site: Site,
    mission: Mission,
    pod: Pod,
    energy: Energy,
    hero_name: str = "Nova",
    hero_type: str = "girl",
    captain_type: str = "captain_m",
) -> World:
    world = World(site)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, role="captain", label="the captain"))
    mission_ent = world.add(Entity(id="mission", type="mission", label=mission.id))
    mission_ent.attrs["need_key"] = mission.need_key
    if mission.need_key == "light":
        mission_ent.meters["dark"] = 1.0
    elif mission.need_key == "crossing":
        mission_ent.meters["gap"] = 1.0
    elif mission.need_key == "carry":
        mission_ent.meters["heavy"] = 1.0
    pod_ent = world.add(Entity(id="pod", type="pod", label=pod.label))
    pod_ent.attrs["preferred_energy"] = pod.preferred_energy
    energy_ent = world.add(Entity(id="energy", type="energy", label=energy.label))
    energy_ent.attrs["gentle"] = energy.gentle
    helper_cfg = HELPERS[pod.transforms_to]
    helper_ent = world.add(Entity(id="helper", type="helper", label=helper_cfg.label))
    helper_ent.attrs["solves"] = helper_cfg.solves

    world.facts["site"] = site
    world.facts["mission_cfg"] = mission
    world.facts["pod_cfg"] = pod
    world.facts["energy_cfg"] = energy
    world.facts["helper_cfg"] = helper_cfg
    world.facts["hero_name"] = hero_name

    intro(world, hero, captain, site)
    mission_setup(world, hero, captain, mission)

    world.para()
    find_pod(world, hero, pod)
    inspect(world, captain, hero, pod, energy)

    world.para()
    charge(world, hero, captain, pod, energy)
    transform(world, hero, pod, helper_cfg)
    solve_mission(world, hero, captain, mission, helper_cfg)

    world.para()
    ending(world, hero, captain, helper_cfg)

    world.facts.update(
        hero=hero,
        captain=captain,
        mission=mission_ent,
        pod=pod_ent,
        energy=energy_ent,
        helper=helper_ent,
        transformed=helper_ent.meters["active"] >= THRESHOLD,
        solved=mission_ent.meters["solved"] >= THRESHOLD,
    )
    return world


SITES = {
    "moon": Site(
        id="moon",
        place="the Echo Moon",
        sky="a velvet sky full of slow stars",
        need="crossing",
        affords={"sunbeam", "crystal_glow"},
        tags={"moon", "space"},
    ),
    "ring_station": Site(
        id="ring_station",
        place="the Blue Ring Station",
        sky="a round window of passing planets",
        need="light",
        affords={"crystal_glow", "engine_song"},
        tags={"station", "space"},
    ),
    "red_planet": Site(
        id="red_planet",
        place="the Red Dust Planet",
        sky="a copper sky with two tiny moons",
        need="carry",
        affords={"sunbeam", "engine_song"},
        tags={"planet", "space"},
    ),
}

MISSIONS = {
    "crossing": Mission(
        id="crossing",
        need_key="crossing",
        opening="They had come to map a crack in the moon plain, but a wide silver gap split the path in two.",
        worry="How will we get across?",
        solved_by="bridge_kite",
        success="Soon a safe shining path stretched over the gap, and the explorers crossed with careful moon-steps.",
        tags={"crossing", "bridge"},
    ),
    "light": Mission(
        id="light",
        need_key="light",
        opening="They had come to read the old star map room, but the hall beyond the air door was dark as a pocket.",
        worry="We cannot read anything in that black hall.",
        solved_by="glow_moth",
        success="Soft living light drifted through the hall, and the old star map woke in silver lines on the wall.",
        tags={"light", "dark"},
    ),
    "carry": Mission(
        id="carry",
        need_key="carry",
        opening="They had come to bring home a box of ice seeds, but the box was too heavy for small arms to lift.",
        worry="How can we carry the ice seeds back to the shuttle?",
        solved_by="cargo_beetle",
        success="The box rose with a steady whirr, and the ice seeds rode safely all the way to the shuttle ramp.",
        tags={"carry", "heavy"},
    ),
}

PODS = {
    "kite_pod": Pod(
        id="kite_pod",
        label="bridge candidate pod",
        shell="a folded shell shaped like a tiny silver kite",
        preferred_energy="sunbeam",
        transforms_to="bridge_kite",
        wake_line="This kind of pod opens when it drinks a warm sunbeam",
        safe_line="The warm light soaked in without a crack or spark.",
        tags={"candidate", "transformation"},
    ),
    "moth_pod": Pod(
        id="moth_pod",
        label="glow candidate pod",
        shell="a round glassy shell with soft dots inside",
        preferred_energy="crystal_glow",
        transforms_to="glow_moth",
        wake_line="This pod likes the quiet glow of a crystal lamp",
        safe_line="The dots inside the shell blinked in a sleepy pattern.",
        tags={"candidate", "transformation"},
    ),
    "beetle_pod": Pod(
        id="beetle_pod",
        label="cargo candidate pod",
        shell="a sturdy bronze shell with little tucked legs",
        preferred_energy="engine_song",
        transforms_to="cargo_beetle",
        wake_line="This pod wakes to the deep song of a patient engine",
        safe_line="The bronze shell trembled, then tapped the ground with tiny feet.",
        tags={"candidate", "transformation"},
    ),
}

ENERGIES = {
    "sunbeam": Energy(
        id="sunbeam",
        label="sunbeam",
        phrase="a warm stripe of sunbeam from the shuttle mirror",
        gentle=True,
        powers={"kite_pod"},
        tags={"sunbeam"},
    ),
    "crystal_glow": Energy(
        id="crystal_glow",
        label="crystal glow",
        phrase="the hush-blue glow of the captain's crystal lamp",
        gentle=True,
        powers={"moth_pod"},
        tags={"crystal", "light"},
    ),
    "engine_song": Energy(
        id="engine_song",
        label="engine song",
        phrase="the low engine song from the parked shuttle",
        gentle=True,
        powers={"beetle_pod"},
        tags={"engine"},
    ),
    "storm_charge": Energy(
        id="storm_charge",
        label="storm charge",
        phrase="a jumpy crackle from a storm jar",
        gentle=False,
        powers=set(),
        tags={"storm"},
    ),
}

HELPERS = {
    "bridge_kite": HelperForm(
        id="bridge_kite",
        label="a ribbon-wing bridge kite",
        solves="crossing",
        arrival="Out floated a ribbon-wing bridge kite, spreading long bright fins from side to side.",
        action="The bridge kite glided over the crack and laid its glowing wings flat, making a bridge where there had been empty air.",
        ending_image="the bridge kite coasted beside them, its wings catching starlight like silver paper",
        tags={"bridge", "kite"},
    ),
    "glow_moth": HelperForm(
        id="glow_moth",
        label="a lantern moth",
        solves="light",
        arrival="Out rose a lantern moth, with moon-pale wings and a golden belly bright as soup on a cold night.",
        action="The lantern moth fluttered ahead and poured warm light through the dark hall, turning fear into a path they could follow.",
        ending_image="the lantern moth rested on the window rim, glowing softly against the planets",
        tags={"light", "moth"},
    ),
    "cargo_beetle": HelperForm(
        id="cargo_beetle",
        label="a lifting beetle",
        solves="carry",
        arrival="Out clambered a lifting beetle, strong and shiny, with six neat legs and a humming back shell.",
        action="The lifting beetle tucked itself under the heavy box and raised it as if the load were no heavier than a lunch tin.",
        ending_image="the lifting beetle rode in the cargo nook, clicking contentedly beside the ice seeds",
        tags={"carry", "beetle"},
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Tess", "Ivy", "Zara", "Nia", "Skye"]
BOY_NAMES = ["Orion", "Finn", "Milo", "Leo", "Arlo", "Jace", "Nico", "Theo"]


@dataclass
class StoryParams:
    site: str
    mission: str
    pod: str
    energy: str
    hero_name: str
    hero_type: str
    captain_type: str
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
    "moon": [
        (
            "What is a moon?",
            "A moon is a world that goes around a planet. Some moons are rocky and quiet, and they can look very bright in space.",
        )
    ],
    "station": [
        (
            "What is a space station?",
            "A space station is a place built by people that stays in space. Astronauts can live and work there for a while.",
        )
    ],
    "planet": [
        (
            "What is a planet?",
            "A planet is a big round world that travels around a star. Earth is a planet too.",
        )
    ],
    "bridge": [
        (
            "What does a bridge do?",
            "A bridge helps you cross over an empty space or water safely. It gives you a path where there was none before.",
        )
    ],
    "dark": [
        (
            "Why do explorers need light?",
            "Explorers need light so they can see where they are going and what is around them. Light helps people stay safe and notice important things.",
        )
    ],
    "heavy": [
        (
            "Why is it hard to carry something heavy?",
            "Heavy things push down with more force, so your arms and legs have to work harder. Sometimes you need help or a tool to move them safely.",
        )
    ],
    "candidate": [
        (
            "What is a candidate?",
            "A candidate is something or someone being considered for a job or a special place. In this story, the pod was a candidate because it might become the helper they needed.",
        )
    ],
    "transformation": [
        (
            "What is a transformation?",
            "A transformation is a big change from one form into another. A tiny pod changing into a helpful creature is a transformation.",
        )
    ],
    "sunbeam": [
        (
            "What is a sunbeam?",
            "A sunbeam is a bright line of sunlight. It can feel warm when it shines on you.",
        )
    ],
    "crystal": [
        (
            "What is a crystal lamp?",
            "A crystal lamp is a made-up space lamp in this story that gives a soft steady glow. A gentle light can help you see without a hot flame.",
        )
    ],
    "engine": [
        (
            "What is an engine?",
            "An engine is a machine that gives power to make something move. In a spaceship, an engine helps the ship travel.",
        )
    ],
}

KNOWLEDGE_ORDER = [
    "candidate",
    "transformation",
    "moon",
    "station",
    "planet",
    "bridge",
    "dark",
    "heavy",
    "sunbeam",
    "crystal",
    "engine",
]


def generation_prompts(world: World) -> list[str]:
    site = world.facts["site"]
    mission = world.facts["mission_cfg"]
    pod = world.facts["pod_cfg"]
    helper = world.facts["helper_cfg"]
    hero = world.facts["hero"]
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "candidate" and a magical-feeling transformation.',
        f"Tell a gentle story where {hero.id} finds a {pod.label} on {site.place} and it transforms into {helper.label} to solve a problem.",
        f"Write a TinyStories-style tale about a child explorer facing {mission.need_key} in space, then watching the right helper wake up and save the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    site = world.facts["site"]
    mission = world.facts["mission_cfg"]
    pod = world.facts["pod_cfg"]
    energy = world.facts["energy_cfg"]
    helper = world.facts["helper_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young space explorer, and the captain on a trip to {site.place}. Together they had to solve one hard mission.",
        ),
        (
            "What problem did they have when they landed?",
            f"They were blocked by {mission.need_key}. {mission.success.split(',')[0].replace('Soon ', '').replace('Soft living light drifted through the hall', 'the dark hall').replace('The box rose with a steady whirr', 'a box that was too heavy')} was the trouble they needed to fix.",
        ),
        (
            "What did {0} find?".format(hero.id),
            f"{hero.id} found {pod.shell} with a {pod.label} inside. The captain thought it might be the right candidate helper for their mission.",
        ),
        (
            "How did the pod transform?",
            f"They used {energy.phrase} because that was the safe way to wake the pod. Then the shell unfolded and changed into {helper.label}.",
        ),
        (
            "How did the transformation help them?",
            f"It helped by solving {mission.need_key}. {helper.action} {mission.success}",
        ),
        (
            "How did {0} feel at the end?".format(hero.id),
            f"{hero.id} felt relieved and brave. The mission had looked too hard at first, but the new helper turned worry into wonder.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"candidate", "transformation"}
    tags |= set(world.facts["site"].tags)
    tags |= set(world.facts["mission_cfg"].tags)
    tags |= set(world.facts["energy_cfg"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v is False}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="moon",
        mission="crossing",
        pod="kite_pod",
        energy="sunbeam",
        hero_name="Nova",
        hero_type="girl",
        captain_type="captain_m",
    ),
    StoryParams(
        site="ring_station",
        mission="light",
        pod="moth_pod",
        energy="crystal_glow",
        hero_name="Orion",
        hero_type="boy",
        captain_type="captain_f",
    ),
    StoryParams(
        site="red_planet",
        mission="carry",
        pod="beetle_pod",
        energy="engine_song",
        hero_name="Mira",
        hero_type="girl",
        captain_type="captain_m",
    ),
]


def outcome_of(params: StoryParams) -> str:
    site = SITES[params.site]
    mission = MISSIONS[params.mission]
    pod = PODS[params.pod]
    energy = ENERGIES[params.energy]
    return "solved" if valid_combo(site, mission, pod, energy) else "invalid"


ASP_RULES = r"""
valid(S, M, P, E) :- site(S), mission(M), pod(P), energy(E),
                     affords(S, E),
                     pod_energy(P, E),
                     pod_form(P, F),
                     mission_need(M, N),
                     form_solves(F, N).

solved(S, M, P, E) :- valid(S, M, P, E).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        for energy in sorted(site.affords):
            lines.append(asp.fact("affords", site_id, energy))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("mission_need", mission_id, mission.need_key))
    for pod_id, pod in PODS.items():
        lines.append(asp.fact("pod", pod_id))
        lines.append(asp.fact("pod_energy", pod_id, pod.preferred_energy))
        lines.append(asp.fact("pod_form", pod_id, pod.transforms_to))
    for energy_id in ENERGIES:
        lines.append(asp.fact("energy", energy_id))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("form", helper_id))
        lines.append(asp.fact("form_solves", helper_id, helper.solves))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


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

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for params in CURATED:
        try:
            story = generate(params).story
            if "candidate" not in story.lower():
                rc = 1
                print(f"CHECK FAILED: missing required word in curated story {params}.")
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space adventure story world with a candidate pod and a helpful transformation."
    )
    ap.add_argument("--site", choices=sorted(SITES))
    ap.add_argument("--mission", choices=sorted(MISSIONS))
    ap.add_argument("--pod", choices=sorted(PODS))
    ap.add_argument("--energy", choices=sorted(ENERGIES))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain-type", choices=["captain_f", "captain_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible-story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.mission and args.pod and args.energy:
        site = SITES[args.site]
        mission = MISSIONS[args.mission]
        pod = PODS[args.pod]
        energy = ENERGIES[args.energy]
        if not valid_combo(site, mission, pod, energy):
            raise StoryError(explain_invalid(site, mission, pod, energy))

    combos = [
        combo
        for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.mission is None or combo[1] == args.mission)
        and (args.pod is None or combo[2] == args.pod)
        and (args.energy is None or combo[3] == args.energy)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, mission_id, pod_id, energy_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    captain_type = args.captain_type or rng.choice(["captain_f", "captain_m"])
    return StoryParams(
        site=site_id,
        mission=mission_id,
        pod=pod_id,
        energy=energy_id,
        hero_name=hero_name,
        hero_type=hero_type,
        captain_type=captain_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.site not in SITES:
        raise StoryError(f"(Unknown site: {params.site})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.pod not in PODS:
        raise StoryError(f"(Unknown pod: {params.pod})")
    if params.energy not in ENERGIES:
        raise StoryError(f"(Unknown energy: {params.energy})")
    site = SITES[params.site]
    mission = MISSIONS[params.mission]
    pod = PODS[params.pod]
    energy = ENERGIES[params.energy]
    if not valid_combo(site, mission, pod, energy):
        raise StoryError(explain_invalid(site, mission, pod, energy))
    world = tell(
        site=site,
        mission=mission,
        pod=pod,
        energy=energy,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        captain_type=params.captain_type,
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, mission, pod, energy) combos:\n")
        for site, mission, pod, energy in combos:
            print(f"  {site:12} {mission:10} {pod:10} {energy}")
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
            header = f"### {p.hero_name}: {p.mission} at {p.site} ({p.pod} + {p.energy})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
