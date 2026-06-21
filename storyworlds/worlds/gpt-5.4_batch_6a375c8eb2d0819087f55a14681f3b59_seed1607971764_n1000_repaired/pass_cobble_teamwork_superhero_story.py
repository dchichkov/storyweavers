#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py
==================================================================

A standalone story world for a tiny superhero-style teamwork tale: a small team
of children in capes faces a rain-cut gap, cannot solve it alone, and learns to
work together by making a line and calling "Pass!" as they hand a cobble along
to build a safe crossing.

The world model is intentionally small and classical:
- a scene provides a fixed number of useful cobbles
- a gap requires enough coverage and enough grip to become passable
- the heroes' teamwork raises confidence and lets the plan succeed
- prose is rendered from the simulated state, not from a frozen template

Run it
------
    python storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py
    python storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/pass_cobble_teamwork_superhero_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Scene:
    id: str
    place: str
    skyline: str
    stash_label: str
    cobble_count: int
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
    item: str
    item_phrase: str
    recipient: str
    need_line: str
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
class Gap:
    id: str
    label: str
    phrase: str
    sound: str
    need: int
    slip_need: int
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
class Cobble:
    id: str
    label: str
    phrase: str
    cover: int
    grip: int
    shine: str
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

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in ("leader", "partner")]

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


def _r_path_ready(world: World) -> list[str]:
    out: list[str] = []
    gap = world.get("gap")
    if gap.meters["filled"] < gap.attrs["need"]:
        return out
    sig = ("path_ready",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gap.meters["passable"] += 1
    for hero in world.heroes():
        hero.memes["hope"] += 1
    out.append("__path__")
    return out


def _r_team_glow(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("line_formed", 0) < THRESHOLD:
        return out
    sig = ("team_glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for hero in world.heroes():
        hero.memes["teamwork"] += 1
        hero.memes["courage"] += 1
    out.append("__team__")
    return out


CAUSAL_RULES = [
    Rule(name="path_ready", tag="physical", apply=_r_path_ready),
    Rule(name="team_glow", tag="social", apply=_r_team_glow),
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


SCENES = {
    "rooftop_lane": Scene(
        id="rooftop_lane",
        place="Maple Lane",
        skyline="Cape shadows fluttered on fences like tiny bat signals.",
        stash_label="beside the flower bed",
        cobble_count=3,
        tags={"street", "rain"},
    ),
    "school_walk": Scene(
        id="school_walk",
        place="Brightbrick Walk",
        skyline="The puddles flashed like little mirrors between the houses.",
        stash_label="near the school garden",
        cobble_count=4,
        tags={"school", "rain"},
    ),
    "market_corner": Scene(
        id="market_corner",
        place="Sunbeam Corner",
        skyline="Store windows winked back at every bright cape.",
        stash_label="by the old tree ring",
        cobble_count=3,
        tags={"market", "rain"},
    ),
}

MISSIONS = {
    "books": Mission(
        id="books",
        item="library books",
        item_phrase="a stack of library books",
        recipient="the story porch",
        need_line="The books had to stay dry for story time.",
        ending_image="Soon the books were on the porch, and the pages stayed crisp and dry.",
        tags={"books", "helping"},
    ),
    "soup": Mission(
        id="soup",
        item="soup pot",
        item_phrase="a warm soup pot with a lid",
        recipient="Mr. Vale next door",
        need_line="The soup was still steaming, and it needed a steady trip.",
        ending_image="Soon the soup pot was safe in Mr. Vale's hands, with one curl of steam still rising.",
        tags={"soup", "neighbor"},
    ),
    "banner": Mission(
        id="banner",
        item="party banner",
        item_phrase="a bright party banner rolled under one arm",
        recipient="the block-party gate",
        need_line="The banner had to arrive clean so the street could sparkle.",
        ending_image="Soon the banner was tied across the gate, bright and straight in the clean air.",
        tags={"banner", "celebration"},
    ),
}

GAPS = {
    "gutter": Gap(
        id="gutter",
        label="gutter",
        phrase="a rain gutter rushing across the sidewalk",
        sound="It hissed and gurgled under the curb.",
        need=2,
        slip_need=1,
        tags={"gutter", "water"},
    ),
    "rill": Gap(
        id="rill",
        label="rain rill",
        phrase="a rain-cut rill slicing through the path",
        sound="It whispered over the stones and tugged at every loose thing.",
        need=3,
        slip_need=2,
        tags={"rill", "water"},
    ),
    "mud_crack": Gap(
        id="mud_crack",
        label="mud crack",
        phrase="a muddy crack opened by the storm",
        sound="The edges looked soft and slippy.",
        need=3,
        slip_need=1,
        tags={"mud", "gap"},
    ),
}

COBBLES = {
    "flat_cobble": Cobble(
        id="flat_cobble",
        label="flat cobble",
        phrase="a flat cobble",
        cover=1,
        grip=2,
        shine="smooth on top and rough underneath",
        tags={"cobble", "stone"},
    ),
    "garden_cobble": Cobble(
        id="garden_cobble",
        label="garden cobble",
        phrase="a garden cobble",
        cover=1,
        grip=1,
        shine="round at the sides but steady enough when pressed down",
        tags={"cobble", "stone"},
    ),
    "broad_cobble": Cobble(
        id="broad_cobble",
        label="broad cobble",
        phrase="a broad cobble",
        cover=2,
        grip=2,
        shine="wide and heavy like a superhero stepping stone",
        tags={"cobble", "stone"},
    ),
}

GIRL_NAMES = ["Nova", "Skye", "Ruby", "Mina", "Luna", "Ava", "Zara", "Ivy"]
BOY_NAMES = ["Bolt", "Dash", "Leo", "Max", "Finn", "Theo", "Jace", "Eli"]
TRAITS = ["brave", "quick", "steady", "kind", "clever", "careful"]


def usable_combo(scene: Scene, gap: Gap, cobble: Cobble) -> bool:
    return scene.cobble_count * cobble.cover >= gap.need and cobble.grip >= gap.slip_need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for gap_id, gap in GAPS.items():
            for cobble_id, cobble in COBBLES.items():
                if usable_combo(scene, gap, cobble):
                    combos.append((scene_id, gap_id, cobble_id))
    return combos


def route_style(params: "StoryParams") -> str:
    extra = COBBLES[params.cobble].cover * SCENES[params.scene].cobble_count - GAPS[params.gap].need
    if params.team_size >= 3 and extra >= 1:
        return "swift"
    return "careful"


@dataclass
class StoryParams:
    scene: str
    mission: str
    gap: str
    cobble: str
    leader: str
    leader_gender: str
    partner1: str
    partner1_gender: str
    partner2: str = ""
    partner2_gender: str = ""
    parent: str = "mother"
    leader_trait: str = "brave"
    team_size: int = 2
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


def predict_fill(world: World, placements: int) -> dict:
    sim = world.copy()
    gap = sim.get("gap")
    cobble = sim.get("stash")
    for _ in range(placements):
        gap.meters["filled"] += cobble.attrs["cover"]
    propagate(sim, narrate=False)
    return {
        "filled": gap.meters["filled"],
        "passable": gap.meters["passable"] >= THRESHOLD,
    }


def introduce(world: World, leader: Entity, partners: list[Entity], scene: Scene) -> None:
    names = ", ".join([leader.id] + [p.id for p in partners[:-1]])
    if partners:
        if len(partners) == 1:
            team = f"{leader.id} and {partners[0].id}"
        else:
            team = f"{names}, and {partners[-1].id}"
    else:
        team = leader.id
    world.say(
        f"On a silver-after-rain afternoon, {team} clipped bright towels around their shoulders "
        f"and became the Maple Maskers, the smallest superhero team in {scene.place}. {scene.skyline}"
    )


def mission_call(world: World, leader: Entity, mission: Mission, parent: Entity) -> None:
    for hero in world.heroes():
        hero.memes["purpose"] += 1
        hero.memes["joy"] += 1
    world.say(
        f"{leader.id} carried {mission.item_phrase}, and {leader.pronoun('possessive')} "
        f"{parent.label_word} pointed toward {mission.recipient}. \"Heroes, this must get across,\" "
        f"{parent.label_word} said. {mission.need_line}"
    )


def reveal_gap(world: World, gap_cfg: Gap) -> None:
    gap = world.get("gap")
    gap.meters["open"] = 1.0
    world.say(
        f"But halfway there they stopped short. A storm had left {gap_cfg.phrase}. {gap_cfg.sound}"
    )


def solo_try(world: World, leader: Entity, mission: Mission) -> None:
    leader.memes["strain"] += 1
    leader.memes["worry"] += 1
    world.say(
        f"{leader.id} lifted one foot as if pure superhero courage might do the trick, "
        f"but the jump looked too big while carrying {mission.item_phrase}."
    )


def teamwork_warning(world: World, partners: list[Entity], gap_cfg: Gap, scene: Scene, cobble: Cobble) -> None:
    predicted = predict_fill(world, scene.cobble_count)
    world.facts["predicted_fill"] = predicted["filled"]
    world.facts["predicted_passable"] = predicted["passable"]
    speaker = partners[0]
    speaker.memes["idea"] += 1
    world.say(
        f"\"A lone leap is not our power,\" said {speaker.id}. \"Look {scene.stash_label}—there are "
        f"{scene.cobble_count} bits of cobble there. If we work together, we can build a pass over the water.\""
    )


def form_line(world: World, leader: Entity, partners: list[Entity]) -> None:
    world.facts["line_formed"] = 1.0
    propagate(world, narrate=False)
    line = [leader.id] + [p.id for p in partners]
    world.facts["line_order"] = list(line)
    world.say(
        f"In a flash they made a hero line: {' → '.join(line)}."
    )


def pass_cobbles(world: World, scene: Scene, gap_cfg: Gap, cobble: Cobble) -> None:
    gap = world.get("gap")
    stash = world.get("stash")
    needed = gap_cfg.need
    used = 0
    for _ in range(scene.cobble_count):
        if gap.meters["filled"] >= gap.attrs["need"]:
            break
        stash.meters["remaining"] -= 1
        gap.meters["filled"] += cobble.cover
        used += 1
        world.say(
            f"\"Pass!\" they cried, and {cobble.phrase} flew from hand to hand. "
            f"Each cobble landed with a brave clack."
        )
    world.facts["used_cobbles"] = used
    propagate(world, narrate=False)
    if gap.meters["passable"] >= THRESHOLD:
        gap.meters["stable"] = 1.0
        world.say(
            f"Soon the stones made a small shining path across the {gap_cfg.label}."
        )
    else:
        raise StoryError("(No story: even all the cobbles together would not make a safe path.)")
    if used < needed:
        world.facts["extra_cobbles"] = scene.cobble_count - used
    else:
        world.facts["extra_cobbles"] = scene.cobble_count - used


def cross_and_deliver(world: World, leader: Entity, partners: list[Entity], mission: Mission) -> None:
    gap = world.get("gap")
    if gap.meters["passable"] < THRESHOLD:
        raise StoryError("(No story: the gap never became passable.)")
    for hero in [leader] + partners:
        hero.memes["fear"] = 0.0
        hero.memes["joy"] += 1
        hero.memes["pride"] += 1
    gap.meters["crossed"] = 1.0
    world.facts["delivered"] = True
    tail = "with the others guarding every step" if partners else "all alone"
    world.say(
        f"{leader.id} crossed first {tail}, holding {mission.item_phrase} steady. "
        f"Then the whole team followed over their new pass."
    )
    world.say(mission.ending_image)


def ending(world: World, partners: list[Entity], parent: Entity) -> None:
    group = "The team" if partners else "The hero"
    world.say(
        f"{group} looked back at the neat little bridge of cobble, and {parent.label_word} smiled. "
        f"\"That is how superheroes win,\" {parent.pronoun()} said. \"Not by showing off, but by helping.\""
    )
    world.say(
        "Their capes snapped in the clean breeze, and even the puddles looked as if they were clapping."
    )


def tell(
    scene: Scene,
    mission: Mission,
    gap_cfg: Gap,
    cobble_cfg: Cobble,
    leader_name: str = "Nova",
    leader_gender: str = "girl",
    partner1_name: str = "Bolt",
    partner1_gender: str = "boy",
    partner2_name: str = "",
    partner2_gender: str = "",
    parent_type: str = "mother",
    leader_trait: str = "brave",
    team_size: int = 2,
) -> World:
    world = World()
    leader = world.add(Entity(
        id=leader_name,
        kind="character",
        type=leader_gender,
        role="leader",
        traits=[leader_trait],
        attrs={},
    ))
    partner1 = world.add(Entity(
        id=partner1_name,
        kind="character",
        type=partner1_gender,
        role="partner",
        traits=["helpful"],
        attrs={},
    ))
    partners = [partner1]
    if team_size == 3 and partner2_name:
        partner2 = world.add(Entity(
            id=partner2_name,
            kind="character",
            type=partner2_gender,
            role="partner",
            traits=["helpful"],
            attrs={},
        ))
        partners.append(partner2)
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
        attrs={},
    ))
    gap = world.add(Entity(
        id="gap",
        kind="thing",
        type="gap",
        label=gap_cfg.label,
        attrs={"need": gap_cfg.need, "slip_need": gap_cfg.slip_need},
    ))
    stash = world.add(Entity(
        id="stash",
        kind="thing",
        type="cobble_stash",
        label="cobble pile",
        attrs={"cover": cobble_cfg.cover, "grip": cobble_cfg.grip},
    ))
    stash.meters["remaining"] = float(scene.cobble_count)
    world.facts["line_formed"] = 0.0
    world.facts["delivered"] = False
    world.facts["used_cobbles"] = 0
    world.facts["extra_cobbles"] = 0
    world.facts["scene"] = scene
    world.facts["mission"] = mission
    world.facts["gap_cfg"] = gap_cfg
    world.facts["cobble_cfg"] = cobble_cfg
    world.facts["leader"] = leader
    world.facts["partners"] = partners
    world.facts["parent"] = parent
    world.facts["team_size"] = team_size

    introduce(world, leader, partners, scene)
    mission_call(world, leader, mission, parent)

    world.para()
    reveal_gap(world, gap_cfg)
    solo_try(world, leader, mission)
    teamwork_warning(world, partners, gap_cfg, scene, cobble_cfg)

    world.para()
    form_line(world, leader, partners)
    pass_cobbles(world, scene, gap_cfg, cobble_cfg)
    cross_and_deliver(world, leader, partners, mission)

    world.para()
    ending(world, partners, parent)
    world.facts["route_style"] = route_style(StoryParams(
        scene=scene.id,
        mission=mission.id,
        gap=gap_cfg.id,
        cobble=cobble_cfg.id,
        leader=leader_name,
        leader_gender=leader_gender,
        partner1=partner1_name,
        partner1_gender=partner1_gender,
        partner2=partner2_name,
        partner2_gender=partner2_gender,
        parent=parent_type,
        leader_trait=leader_trait,
        team_size=team_size,
    ))
    return world


KNOWLEDGE = {
    "teamwork": [(
        "What is teamwork?",
        "Teamwork is when people help one another do one job together. A hard problem can become easier when everyone shares a part of it."
    )],
    "cobble": [(
        "What is a cobble?",
        "A cobble is a rounded stone, often the size of a hand or a little bigger. People can use cobbles to make paths or edges because the stones are strong."
    )],
    "gutter": [(
        "What is a gutter by a street?",
        "A gutter is the low edge where rainwater runs along the side of a road or sidewalk. After a storm, water can rush there quickly."
    )],
    "stepping": [(
        "Why do stepping stones help people cross water?",
        "Stepping stones make small dry places for your feet. If they are steady and close enough together, they turn a splashy crossing into a safer path."
    )],
    "superhero": [(
        "Do superheroes always win by being strongest?",
        "No. The best superheroes also think, help, and protect others. Being brave together can matter more than being the loudest or strongest."
    )],
    "neighbor": [(
        "Why is bringing food to a neighbor kind?",
        "It shows care when someone might need help or company. Small helpful acts can make a whole neighborhood feel warmer."
    )],
    "books": [(
        "Why should library books stay dry?",
        "Water can wrinkle pages and spoil the covers. Keeping books dry helps many children enjoy them later."
    )],
    "banner": [(
        "What does a banner do at a party?",
        "A banner shows people where the celebration is and makes the place feel special. Bright signs can make a street feel welcoming."
    )],
}
KNOWLEDGE_ORDER = ["teamwork", "superhero", "cobble", "gutter", "stepping", "neighbor", "books", "banner"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    leader = f["leader"]
    mission = f["mission"]
    gap_cfg = f["gap_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "pass" and "cobble".',
        f"Tell a teamwork story where {leader.id} and friends must get {mission.item} across a {gap_cfg.label} after the rain.",
        f"Write a child-facing story in which a small superhero team cannot solve a problem alone, forms a line, and saves the day together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    leader = f["leader"]
    partners = f["partners"]
    parent = f["parent"]
    mission = f["mission"]
    gap_cfg = f["gap_cfg"]
    cobble_cfg = f["cobble_cfg"]
    team_names = ", ".join([leader.id] + [p.id for p in partners[:-1]])
    if partners:
        if len(partners) == 1:
            group = f"{leader.id} and {partners[0].id}"
        else:
            group = f"{team_names}, and {partners[-1].id}"
    else:
        group = leader.id
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {group}, a little superhero team in capes. They were trying to carry {mission.item} safely to {mission.recipient}."
        ),
        (
            "What problem stopped the heroes?",
            f"A {gap_cfg.label} cut across their way after the storm, so the path was not safe to cross while carrying {mission.item}. The rushing water turned an ordinary sidewalk into a real problem."
        ),
        (
            f"Why did {leader.id} stop trying to do it alone?",
            f"{leader.id} saw that one brave jump would not be safe while carrying {mission.item_phrase}. The job needed steady hands, not showing off."
        ),
        (
            "How did the team solve the problem?",
            f"They formed a line and shouted \"Pass!\" as they handed each {cobble_cfg.label} from one hero to the next. By working together, they laid enough stone to make a safe little crossing."
        ),
        (
            "Why did teamwork matter in this story?",
            f"No one child could fix the path as neatly alone. The heroes succeeded because each one took a part of the job and trusted the others to do theirs."
        ),
        (
            "How did the story end?",
            f"They crossed over the new pass and delivered the {mission.item}. At the end, the little bridge of cobble showed exactly what had changed: the problem had become a path."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork", "superhero", "cobble", "stepping"}
    gap_cfg = f["gap_cfg"]
    mission = f["mission"]
    if "gutter" in gap_cfg.tags:
        tags.add("gutter")
    if mission.id == "soup":
        tags.add("neighbor")
    if mission.id == "books":
        tags.add("books")
    if mission.id == "banner":
        tags.add("banner")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: delivered={world.facts.get('delivered')} used_cobbles={world.facts.get('used_cobbles')}")
    return "\n".join(lines)


def explain_rejection(scene: Scene, gap: Gap, cobble: Cobble) -> str:
    if scene.cobble_count * cobble.cover < gap.need:
        return (
            f"(No story: {scene.place} only has enough {cobble.label} coverage for "
            f"{scene.cobble_count * cobble.cover}, but the {gap.label} needs {gap.need}. "
            f"The heroes would not have enough stone to build a safe pass.)"
        )
    if cobble.grip < gap.slip_need:
        return (
            f"(No story: {cobble.label} is too slippery for the {gap.label}. "
            f"The path would wobble instead of helping.)"
        )
    return "(No story: this scene, gap, and cobble do not make a reasonable crossing.)"


ASP_RULES = r"""
capacity(S,Cb,N) :- scene(S), cobble(Cb), scene_count(S,Count), cobble_cover(Cb,Cov), N = Count * Cov.
usable(S,G,Cb) :- capacity(S,Cb,N), gap_need(G,Need), N >= Need, cobble_grip(Cb,Grip), gap_slip(G,Slip), Grip >= Slip.

style(swift)   :- team_size(T), T >= 3, chosen_scene(S), chosen_gap(G), chosen_cobble(Cb),
                  capacity(S,Cb,N), gap_need(G,Need), N > Need.
style(careful) :- not style(swift).

valid_story(S,G,Cb) :- usable(S,G,Cb).

#show valid_story/3.
#show style/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        lines.append(asp.fact("scene_count", scene_id, scene.cobble_count))
    for gap_id, gap in GAPS.items():
        lines.append(asp.fact("gap", gap_id))
        lines.append(asp.fact("gap_need", gap_id, gap.need))
        lines.append(asp.fact("gap_slip", gap_id, gap.slip_need))
    for cobble_id, cobble in COBBLES.items():
        lines.append(asp.fact("cobble", cobble_id))
        lines.append(asp.fact("cobble_cover", cobble_id, cobble.cover))
        lines.append(asp.fact("cobble_grip", cobble_id, cobble.grip))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_style(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_scene", params.scene),
        asp.fact("chosen_gap", params.gap),
        asp.fact("chosen_cobble", params.cobble),
        asp.fact("team_size", params.team_size),
    ])
    model = asp.one_model(asp_program(extra))
    styles = asp.atoms(model, "style")
    return styles[0][0] if styles else "?"


def _validate_params(params: StoryParams) -> None:
    if params.scene not in SCENES:
        raise StoryError(f"(No story: unknown scene '{params.scene}'.)")
    if params.mission not in MISSIONS:
        raise StoryError(f"(No story: unknown mission '{params.mission}'.)")
    if params.gap not in GAPS:
        raise StoryError(f"(No story: unknown gap '{params.gap}'.)")
    if params.cobble not in COBBLES:
        raise StoryError(f"(No story: unknown cobble '{params.cobble}'.)")
    if params.team_size not in (2, 3):
        raise StoryError("(No story: team_size must be 2 or 3.)")
    if params.team_size == 3 and not params.partner2:
        raise StoryError("(No story: a team of three needs a second partner name.)")
    if params.team_size == 2 and params.partner2:
        raise StoryError("(No story: team of two should not include a third hero.)")
    scene = SCENES[params.scene]
    gap = GAPS[params.gap]
    cobble = COBBLES[params.cobble]
    if not usable_combo(scene, gap, cobble):
        raise StoryError(explain_rejection(scene, gap, cobble))


CURATED = [
    StoryParams(
        scene="rooftop_lane",
        mission="books",
        gap="gutter",
        cobble="flat_cobble",
        leader="Nova",
        leader_gender="girl",
        partner1="Bolt",
        partner1_gender="boy",
        parent="mother",
        leader_trait="brave",
        team_size=2,
    ),
    StoryParams(
        scene="school_walk",
        mission="soup",
        gap="rill",
        cobble="broad_cobble",
        leader="Dash",
        leader_gender="boy",
        partner1="Ruby",
        partner1_gender="girl",
        partner2="Finn",
        partner2_gender="boy",
        parent="father",
        leader_trait="kind",
        team_size=3,
    ),
    StoryParams(
        scene="market_corner",
        mission="banner",
        gap="mud_crack",
        cobble="garden_cobble",
        leader="Skye",
        leader_gender="girl",
        partner1="Leo",
        partner1_gender="boy",
        partner2="Mina",
        partner2_gender="girl",
        parent="mother",
        leader_trait="quick",
        team_size=3,
    ),
    StoryParams(
        scene="school_walk",
        mission="books",
        gap="rill",
        cobble="flat_cobble",
        leader="Ava",
        leader_gender="girl",
        partner1="Max",
        partner1_gender="boy",
        parent="father",
        leader_trait="careful",
        team_size=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: little superheroes use teamwork, pass a cobble hand to hand, and solve a rainy-day problem."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gap", choices=GAPS)
    ap.add_argument("--cobble", choices=COBBLES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--team-size", type=int, choices=[2, 3], dest="team_size")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid scene-gap-cobble combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.gap and args.cobble:
        scene = SCENES[args.scene]
        gap = GAPS[args.gap]
        cobble = COBBLES[args.cobble]
        if not usable_combo(scene, gap, cobble):
            raise StoryError(explain_rejection(scene, gap, cobble))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.gap is None or combo[1] == args.gap)
        and (args.cobble is None or combo[2] == args.cobble)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, gap_id, cobble_id = rng.choice(sorted(combos))
    mission_id = args.mission or rng.choice(sorted(MISSIONS))
    team_size = args.team_size if args.team_size is not None else rng.choice([2, 3])
    parent = args.parent or rng.choice(["mother", "father"])
    leader_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    leader = _pick_name(rng, leader_gender, used)
    used.add(leader)
    partner1_gender = rng.choice(["girl", "boy"])
    partner1 = _pick_name(rng, partner1_gender, used)
    used.add(partner1)
    partner2 = ""
    partner2_gender = ""
    if team_size == 3:
        partner2_gender = rng.choice(["girl", "boy"])
        partner2 = _pick_name(rng, partner2_gender, used)
    leader_trait = rng.choice(TRAITS)
    return StoryParams(
        scene=scene_id,
        mission=mission_id,
        gap=gap_id,
        cobble=cobble_id,
        leader=leader,
        leader_gender=leader_gender,
        partner1=partner1,
        partner1_gender=partner1_gender,
        partner2=partner2,
        partner2_gender=partner2_gender,
        parent=parent,
        leader_trait=leader_trait,
        team_size=team_size,
    )


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        scene=SCENES[params.scene],
        mission=MISSIONS[params.mission],
        gap_cfg=GAPS[params.gap],
        cobble_cfg=COBBLES[params.cobble],
        leader_name=params.leader,
        leader_gender=params.leader_gender,
        partner1_name=params.partner1,
        partner1_gender=params.partner1_gender,
        partner2_name=params.partner2,
        partner2_gender=params.partner2_gender,
        parent_type=params.parent,
        leader_trait=params.leader_trait,
        team_size=params.team_size,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: ASP gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"MISMATCH: resolve_params failed unexpectedly for seed {seed}.")
    style_bad = 0
    for params in cases:
        if asp_style(params) != route_style(params):
            style_bad += 1
    if style_bad == 0:
        print(f"OK: ASP style matches Python route_style() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {style_bad}/{len(cases)} style decisions differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, gap, cobble) combos:\n")
        for scene_id, gap_id, cobble_id in combos:
            print(f"  {scene_id:13} {gap_id:10} {cobble_id}")
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
            header = f"### {p.leader}: {p.mission} across {p.gap} at {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
