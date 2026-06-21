#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py
==========================================================================

A standalone story world for a gentle Animal Story about teamwork: a chipper
little animal sets out with something important, meets a concrete obstacle,
stops to assess the problem, and succeeds only after friends help in a way that
actually fits the task.

The domain is intentionally small and constraint-checked. Different cargos need
different teamwork methods for different obstacles:

- a heavy wagon can be hauled up a hill with a rope team
- a wheeled wagon can cross a muddy rut on planks
- a wide kite frame can be steadied on a windy path by friends holding the corners

Invalid pairings are refused with a StoryError and a plain-language reason.

Run it
------
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --cargo kite_frame --obstacle windy_path
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --cargo soup_pot --obstacle muddy_rut
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --method corner_team --cargo pumpkin_wagon
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/chipper_radiate_assess_teamwork_animal_story.py --verify
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
class Setting:
    id: str
    place: str
    path_text: str
    ending_glow: str
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
    destination: str
    shape: str
    heavy: bool
    wheeled: bool
    wide: bool
    fragile: bool
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
    arrive_text: str
    solo_fail: str
    assess_text: str
    requires: str
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
    tool: str
    helpers: tuple[str, str]
    apply_text: str
    success_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_stuck_strain(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    hero = world.get("hero")
    if cargo.meters["stuck"] < THRESHOLD:
        return out
    sig = ("stuck_strain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["strain"] += 1
    hero.memes["worry"] += 1
    out.append("__stuck__")
    return out


def _r_tilt_worry(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["tilt"] < THRESHOLD:
        return out
    sig = ("tilt_worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.characters():
        ent.memes["care"] += 1
    out.append("__tilt__")
    return out


def _r_teamwork_relief(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    if cargo.meters["moving"] < THRESHOLD:
        return out
    sig = ("teamwork_relief",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in world.characters():
        ent.memes["joy"] += 1
        ent.memes["trust"] += 1
    out.append("__moving__")
    return out


CAUSAL_RULES = [
    Rule(name="stuck_strain", tag="physical", apply=_r_stuck_strain),
    Rule(name="tilt_worry", tag="emotional", apply=_r_tilt_worry),
    Rule(name="teamwork_relief", tag="social", apply=_r_teamwork_relief),
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


def method_fits(cargo: Cargo, obstacle: Obstacle, method: Method) -> bool:
    if method.id != obstacle.requires:
        return False
    if method.id in {"rope_team", "plank_team"} and not cargo.wheeled:
        return False
    if method.id == "rope_team" and not cargo.heavy:
        return False
    if method.id == "plank_team" and cargo.wide:
        return False
    if method.id == "corner_team" and not cargo.wide:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for cargo_id, cargo in CARGOS.items():
            for obstacle_id, obstacle in OBSTACLES.items():
                for method_id, method in METHODS.items():
                    if method_fits(cargo, obstacle, method):
                        combos.append((setting_id, cargo_id, obstacle_id, method_id))
    return combos


def explain_rejection(cargo: Cargo, obstacle: Obstacle, method: Method) -> str:
    if method.id != obstacle.requires:
        needed = METHODS[obstacle.requires].label
        return (
            f"(No story: {obstacle.label} needs {needed}, not {method.label}. "
            f"The teamwork has to match the obstacle.)"
        )
    if method.id in {"rope_team", "plank_team"} and not cargo.wheeled:
        return (
            f"(No story: {cargo.phrase} is not on wheels, so {method.label} would not "
            f"move it sensibly.)"
        )
    if method.id == "rope_team" and not cargo.heavy:
        return (
            f"(No story: {cargo.phrase} is not heavy enough to need a rope-pulling team. "
            f"A rope team would feel forced here.)"
        )
    if method.id == "plank_team" and cargo.wide:
        return (
            f"(No story: {cargo.phrase} is too wide and awkward for a simple plank crossing. "
            f"That fix would not honestly fit the object.)"
        )
    if method.id == "corner_team" and not cargo.wide:
        return (
            f"(No story: {method.label} is for a wide object with corners to steady. "
            f"{cargo.label.capitalize()} does not need that kind of help.)"
        )
    return "(No story: this combination does not make practical sense.)"


def assess_need(cargo: Cargo, obstacle: Obstacle) -> dict:
    stuck = obstacle.id in {"sunny_hill", "muddy_rut"}
    tilt = obstacle.id in {"muddy_rut", "windy_path"} or cargo.fragile
    risk = {
        "stuck": stuck,
        "tilt": tilt,
        "reason": obstacle.assess_text,
    }
    return risk


def _solo_attempt(world: World, cargo: Entity, obstacle: Obstacle, narrate: bool = True) -> None:
    if obstacle.id in {"sunny_hill", "muddy_rut"}:
        cargo.meters["stuck"] += 1
    if obstacle.id in {"muddy_rut", "windy_path"}:
        cargo.meters["tilt"] += 1
    propagate(world, narrate=narrate)


def predict_solo(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    _solo_attempt(sim, sim.get("cargo"), obstacle, narrate=False)
    cargo = sim.get("cargo")
    hero = sim.get("hero")
    return {
        "stuck": cargo.meters["stuck"] >= THRESHOLD,
        "tilt": cargo.meters["tilt"] >= THRESHOLD,
        "strain": hero.meters["strain"],
    }


def introduce(world: World, hero: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"On a bright morning by {world.setting.place}, {hero.id} the {hero.type} felt "
        f"chipper from whiskers to toes. {hero.pronoun('subject').capitalize()} had promised "
        f"to bring {cargo.phrase} to {cargo.destination}."
    )


def set_off(world: World, hero: Entity, cargo_ent: Entity, cargo: Cargo) -> None:
    cargo_ent.meters["ready"] += 1
    world.say(
        f"{hero.id} set off along {world.setting.path_text} with {cargo.label} in front of "
        f"{hero.pronoun('object')}. The job looked easy at first, and that made {hero.id} smile."
    )


def meet_obstacle(world: World, obstacle: Obstacle) -> None:
    world.say(obstacle.arrive_text)


def try_alone(world: World, hero: Entity, cargo_ent: Entity, obstacle: Obstacle) -> None:
    hero.memes["independence"] += 1
    _solo_attempt(world, cargo_ent, obstacle, narrate=False)
    world.say(obstacle.solo_fail)


def pause_and_assess(world: World, hero: Entity, cargo: Cargo, obstacle: Obstacle) -> None:
    pred = predict_solo(world, obstacle)
    world.facts["predicted_stuck"] = pred["stuck"]
    world.facts["predicted_tilt"] = pred["tilt"]
    world.say(
        f"{hero.id} stopped, took one slow breath, and tried to assess the trouble. "
        f"{obstacle.assess_text}"
    )


def call_friends(world: World, hero: Entity, helper_a: Entity, helper_b: Entity) -> None:
    hero.memes["humility"] += 1
    helper_a.memes["care"] += 1
    helper_b.memes["care"] += 1
    world.say(
        f'"I can do many things, but not every big thing alone," {hero.id} said. '
        f'So {hero.pronoun("subject")} called to {helper_a.id} the {helper_a.type} and '
        f'{helper_b.id} the {helper_b.type}.'
    )


def teamwork(world: World, hero: Entity, helper_a: Entity, helper_b: Entity,
             cargo_ent: Entity, cargo: Cargo, method: Method) -> None:
    cargo_ent.meters["stuck"] = 0.0
    cargo_ent.meters["tilt"] = 0.0
    cargo_ent.meters["moving"] += 1
    cargo_ent.meters["delivered"] += 1
    world.facts["used_tool"] = method.tool
    world.facts["helpers"] = (helper_a, helper_b)
    world.say(method.apply_text.format(
        hero=hero.id,
        h1=helper_a.id,
        h2=helper_b.id,
        cargo=cargo.label,
        destination=cargo.destination,
        tool=method.tool,
    ))
    propagate(world, narrate=False)
    world.say(method.success_text.format(
        hero=hero.id,
        h1=helper_a.id,
        h2=helper_b.id,
        cargo=cargo.label,
        destination=cargo.destination,
    ))


def ending(world: World, hero: Entity, cargo: Cargo) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"When they reached {cargo.destination}, the others gathered close. "
        f"Their pleased faces seemed to radiate right through the evening air."
    )
    world.say(
        f"Soon {world.setting.ending_glow}, and {hero.id} knew the best part had not been "
        f"bringing the {cargo.label}. The best part had been doing the hard part together."
    )


def tell(setting: Setting, cargo: Cargo, obstacle: Obstacle, method: Method,
         hero_name: str = "Pip", hero_type: str = "rabbit") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero"))
    helper_species = method.helpers
    helper_a = world.add(
        Entity(id=HELPER_NAMES[0], kind="character", type=helper_species[0], role="helper")
    )
    helper_b = world.add(
        Entity(id=HELPER_NAMES[1], kind="character", type=helper_species[1], role="helper")
    )
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label))
    cargo_ent.meters["ready"] = 0.0
    cargo_ent.meters["stuck"] = 0.0
    cargo_ent.meters["tilt"] = 0.0
    cargo_ent.meters["moving"] = 0.0
    cargo_ent.meters["delivered"] = 0.0
    hero.meters["strain"] = 0.0
    hero.memes["worry"] = 0.0
    helper_a.memes["care"] = 0.0
    helper_b.memes["care"] = 0.0
    world.facts.update(
        setting=setting,
        cargo_cfg=cargo,
        obstacle=obstacle,
        method=method,
        hero=hero,
    )

    introduce(world, hero, cargo)
    set_off(world, hero, cargo_ent, cargo)

    world.para()
    meet_obstacle(world, obstacle)
    try_alone(world, hero, cargo_ent, obstacle)
    pause_and_assess(world, hero, cargo, obstacle)
    call_friends(world, hero, helper_a, helper_b)

    world.para()
    teamwork(world, hero, helper_a, helper_b, cargo_ent, cargo, method)
    ending(world, hero, cargo)

    world.facts.update(
        cargo=cargo_ent,
        teamwork=True,
        delivered=cargo_ent.meters["delivered"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "meadow": Setting(
        id="meadow",
        place="the clover meadow",
        path_text="a soft path between daisies and clover",
        ending_glow="paper lanterns bobbed above the grass",
        tags={"meadow"},
    ),
    "orchard": Setting(
        id="orchard",
        place="the apple orchard",
        path_text="a path under neat rows of apple trees",
        ending_glow="tiny lanterns swung from the branches",
        tags={"orchard"},
    ),
    "pondside": Setting(
        id="pondside",
        place="the pondside green",
        path_text="a smooth trail beside the reeds and water",
        ending_glow="the pond shone with little floating lights",
        tags={"pond"},
    ),
}

CARGOS = {
    "pumpkin_wagon": Cargo(
        id="pumpkin_wagon",
        label="pumpkin wagon",
        phrase="a wagon carrying one enormous golden pumpkin",
        destination="the harvest table",
        shape="wagon",
        heavy=True,
        wheeled=True,
        wide=False,
        fragile=False,
        tags={"pumpkin", "wagon"},
    ),
    "soup_pot": Cargo(
        id="soup_pot",
        label="soup cart",
        phrase="a little cart with a big pot of acorn soup",
        destination="the supper stump",
        shape="wagon",
        heavy=False,
        wheeled=True,
        wide=False,
        fragile=True,
        tags={"soup", "cart"},
    ),
    "kite_frame": Cargo(
        id="kite_frame",
        label="kite frame",
        phrase="a wide star-kite frame covered in bright paper",
        destination="the hilltop line",
        shape="wide",
        heavy=False,
        wheeled=False,
        wide=True,
        fragile=True,
        tags={"kite", "paper"},
    ),
}

OBSTACLES = {
    "sunny_hill": Obstacle(
        id="sunny_hill",
        label="the sunny hill",
        arrive_text="But halfway there, the path tipped upward into a sunny hill so steep that the wheels seemed to stare back in alarm.",
        solo_fail="The wagon rolled halfway up, then creaked backward again. {hero} leaned harder, but the load was simply too heavy for one small body.".format(hero="The little animal"),
        assess_text="The hill was not mean; it was just stronger than one push from behind.",
        requires="rope_team",
        tags={"hill"},
    ),
    "muddy_rut": Obstacle(
        id="muddy_rut",
        label="the muddy rut",
        arrive_text="Soon the path sank into a muddy rut where yesterday's rain had left a brown, sticky channel across the way.",
        solo_fail="One wheel dropped with a plop, and the cart tipped sideways. A little slosh at the rim made the trouble feel much bigger.",
        assess_text="The mud was gripping the wheel, and a flat, steady crossing would be safer than dragging and hoping.",
        requires="plank_team",
        tags={"mud"},
    ),
    "windy_path": Obstacle(
        id="windy_path",
        label="the windy path",
        arrive_text="At the open part of the trail, a busy wind came skipping through the grass and tugged at every loose edge.",
        solo_fail="The wide frame wobbled, twisted, and nearly sailed out of line. Holding the middle alone left the corners free to flap and bend.",
        assess_text="The problem was not weight at all. The wide paper corners needed calm paws in more than one place at once.",
        requires="corner_team",
        tags={"wind"},
    ),
}

METHODS = {
    "rope_team": Method(
        id="rope_team",
        label="a rope team",
        verb="pull and push together",
        tool="a braided vine rope",
        helpers=("beaver", "turtle"),
        apply_text="{h1} hurried over with {tool}, while {h2} planted steady feet behind the wheels. {hero} took the front with the rope, and all three counted together: \"One, two, three!\"",
        success_text="The {cargo} bumped once, then climbed. With {h2} pushing and {h1} keeping the rope straight, it rolled all the way to {destination}.",
        tags={"rope", "teamwork"},
    ),
    "plank_team": Method(
        id="plank_team",
        label="a plank crossing team",
        verb="build a flat crossing",
        tool="two smooth birch planks",
        helpers=("beaver", "otter"),
        apply_text="{h1} and {h2} fetched {tool} and laid them across the rut, nose to tail and edge to edge. Then {hero} held the cart handles while the others guided each wheel onto the bridge.",
        success_text="The {cargo} rolled over the planks without another wobble, and not a drop was lost before they reached {destination}.",
        tags={"planks", "teamwork"},
    ),
    "corner_team": Method(
        id="corner_team",
        label="a corner-holding team",
        verb="steady all the corners",
        tool="four careful paws at the edges",
        helpers=("squirrel", "fox"),
        apply_text="{h1} caught one bright corner, {h2} held the other, and {hero} kept the middle straight. They moved slowly, letting {tool} do the quiet work the wind could not undo.",
        success_text="The {cargo} stopped twisting and glided neatly along until it stood safe at {destination}.",
        tags={"corners", "teamwork"},
    ),
}

HERO_TYPES = ["rabbit", "mouse", "hedgehog", "chipmunk"]
HERO_NAMES = ["Pip", "Nell", "Moss", "Tavi", "Dot", "Jun"]
HELPER_NAMES = ("Bram", "Tula")


@dataclass
class StoryParams:
    setting: str
    cargo: str
    obstacle: str
    method: str
    hero_name: str
    hero_type: str
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
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people or animals help one another on the same job. Each one does a part, and together they can do more than one can do alone.",
        )
    ],
    "rope": [
        (
            "Why does a rope help pull something heavy?",
            "A rope lets friends pull together from the front while others push from behind. That shared pull spreads the work across more bodies.",
        )
    ],
    "planks": [
        (
            "Why do planks help a cart cross mud?",
            "Planks make a flat path over soft mud. Wheels can roll on the wood instead of sinking into the sticky ground.",
        )
    ],
    "corners": [
        (
            "Why do two corners need help in the wind?",
            "Wind catches loose corners first and twists them around. Holding the corners keeps a wide light object steady.",
        )
    ],
    "mud": [
        (
            "Why do wheels get stuck in mud?",
            "Mud is soft and sticky, so wheels sink instead of rolling smoothly. That makes the load harder to move.",
        )
    ],
    "wind": [
        (
            "What can wind do to something light and wide?",
            "Wind can push, twist, and flap it around. The bigger and lighter it is, the easier the wind can grab it.",
        )
    ],
    "hill": [
        (
            "Why is a hill harder than flat ground?",
            "On a hill, you have to move the load upward as well as forward. That takes more effort than rolling on flat ground.",
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "hill", "mud", "wind", "rope", "planks", "corners"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo_cfg"]
    obstacle = f["obstacle"]
    return [
        (
            f'Write a short Animal Story for a 3-to-5-year-old using the words '
            f'"chipper," "assess," and "radiate," where a {hero.type} named {hero.id} '
            f'needs teamwork to bring {cargo.label} past {obstacle.label}.'
        ),
        (
            f"Tell a gentle story where {hero.id} starts out chipper, meets a real problem, "
            f"stops to assess it, and learns that friends can solve a job better together."
        ),
        (
            f"Write an animal tale about a shared task, a practical obstacle, and a warm ending "
            f"where everyone's smiles seem to radiate."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    cargo = f["cargo_cfg"]
    obstacle = f["obstacle"]
    method = f["method"]
    helper_a, helper_b = f["helpers"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and two friends, {helper_a.id} the "
            f"{helper_a.type} and {helper_b.id} the {helper_b.type}. They work together "
            f"to bring {cargo.label} to {cargo.destination}.",
        ),
        (
            f"Why did {hero.id} stop and assess the problem?",
            f"{hero.id} stopped because trying alone was not working. "
            f"{obstacle.assess_text} That pause helped {hero.pronoun('object')} choose help "
            f"that truly fit the trouble instead of pushing harder in the wrong way.",
        ),
        (
            f"How did the friends solve the problem at {obstacle.label}?",
            f"They used {method.label}. {method.success_text.format(hero=hero.id, h1=helper_a.id, h2=helper_b.id, cargo=cargo.label, destination=cargo.destination)} "
            f"The solution worked because it matched both the obstacle and the kind of thing they were moving.",
        ),
        (
            "What changed by the end of the story?",
            f"At first, {hero.id} tried to do the whole job alone. By the end, {hero.pronoun('subject')} knew "
            f"that asking friends for help was wise, and the happy glow at {cargo.destination} showed the teamwork had paid off.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"teamwork"} | set(f["obstacle"].tags) | set(f["method"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard",
        cargo="pumpkin_wagon",
        obstacle="sunny_hill",
        method="rope_team",
        hero_name="Pip",
        hero_type="rabbit",
    ),
    StoryParams(
        setting="pondside",
        cargo="soup_pot",
        obstacle="muddy_rut",
        method="plank_team",
        hero_name="Nell",
        hero_type="mouse",
    ),
    StoryParams(
        setting="meadow",
        cargo="kite_frame",
        obstacle="windy_path",
        method="corner_team",
        hero_name="Moss",
        hero_type="hedgehog",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "delivered"


def ensure_param_keys(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.cargo not in CARGOS:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.hero_type not in HERO_TYPES:
        raise StoryError(f"(Unknown hero type: {params.hero_type})")


ASP_RULES = r"""
fits_method(C, O, M) :- cargo(C), obstacle(O), method(M), requires(O, M),
                        wheeled(C), uses_wheels(M), heavy(C), needs_heavy(M).
fits_method(C, O, M) :- cargo(C), obstacle(O), method(M), requires(O, M),
                        wheeled(C), uses_wheels(M), not needs_heavy(M), not rejects_wide(M).
fits_method(C, O, M) :- cargo(C), obstacle(O), method(M), requires(O, M),
                        wide(C), needs_wide(M).

valid(S, C, O, M) :- setting(S), fits_method(C, O, M).

#show valid/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, cargo in CARGOS.items():
        lines.append(asp.fact("cargo", cid))
        if cargo.wheeled:
            lines.append(asp.fact("wheeled", cid))
        if cargo.heavy:
            lines.append(asp.fact("heavy", cid))
        if cargo.wide:
            lines.append(asp.fact("wide", cid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("requires", oid, obstacle.requires))
    for mid in METHODS:
        lines.append(asp.fact("method", mid))
    lines.append(asp.fact("uses_wheels", "rope_team"))
    lines.append(asp.fact("uses_wheels", "plank_team"))
    lines.append(asp.fact("needs_heavy", "rope_team"))
    lines.append(asp.fact("rejects_wide", "plank_team"))
    lines.append(asp.fact("needs_wide", "corner_team"))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "assess" not in sample.story or "radiate" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing required story content.)")
        print("OK: smoke test generated a normal story.")
    except Exception as exc:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if not sample.story:
                raise StoryError("(Generated empty story.)")
        except Exception as exc:  # pragma: no cover - verification path
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {exc}")
            break

    if rc == 0:
        print("OK: random generation smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal Story storyworld: a chipper animal meets a practical obstacle, "
        "assesses it, and solves it through teamwork."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cargo and args.obstacle and args.method:
        cargo = CARGOS[args.cargo]
        obstacle = OBSTACLES[args.obstacle]
        method = METHODS[args.method]
        if not method_fits(cargo, obstacle, method):
            raise StoryError(explain_rejection(cargo, obstacle, method))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, cargo_id, obstacle_id, method_id = rng.choice(sorted(combos))
    hero_name = args.hero or rng.choice(HERO_NAMES)
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    return StoryParams(
        setting=setting_id,
        cargo=cargo_id,
        obstacle=obstacle_id,
        method=method_id,
        hero_name=hero_name,
        hero_type=hero_type,
    )


def generate(params: StoryParams) -> StorySample:
    ensure_param_keys(params)
    cargo = CARGOS[params.cargo]
    obstacle = OBSTACLES[params.obstacle]
    method = METHODS[params.method]
    if not method_fits(cargo, obstacle, method):
        raise StoryError(explain_rejection(cargo, obstacle, method))

    world = tell(
        setting=SETTINGS[params.setting],
        cargo=cargo,
        obstacle=obstacle,
        method=method,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
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
        print(f"{len(combos)} compatible (setting, cargo, obstacle, method) combos:\n")
        for setting_id, cargo_id, obstacle_id, method_id in combos:
            print(f"  {setting_id:8} {cargo_id:14} {obstacle_id:11} {method_id}")
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
            header = f"### {p.hero_name}: {p.cargo} / {p.obstacle} / {p.method} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
