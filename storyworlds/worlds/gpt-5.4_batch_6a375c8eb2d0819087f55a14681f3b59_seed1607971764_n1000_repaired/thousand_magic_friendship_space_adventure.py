#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py
=======================================================================

A standalone storyworld about two friends on a small magical space adventure.
They carry a jar of a thousand wish-stars to a faraway place, hit a state-driven
problem in space, and solve it by using the right magical helper together.

The reasonableness constraint is simple and concrete:

- each setting only affords certain space obstacles
- each obstacle has a practical need
- each magical helper only solves obstacles whose need it can truly meet

So the world refuses weak combinations, like trying to use a humming chime to
hold steady in a meteor breeze.

Run it
------
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py --place comet_harbor --obstacle meteor_breeze --helper ribbon_rope
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py --obstacle sleepy_gate --helper star_lantern
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py --all
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/thousand_magic_friendship_space_adventure.py --verify
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
class Setting:
    id: str
    place: str
    sky: str
    destination: str
    landing: str
    ending: str
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
class Obstacle:
    id: str
    label: str
    arrive: str
    need: str
    threat: str
    danger: str
    severity: int
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
class Helper:
    id: str
    label: str
    phrase: str
    power: str
    join_text: str
    success: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    use: str
    ending: str
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
        clone.facts = dict(self.facts)
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


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    ship = world.get("ship")
    if obstacle.meters["active"] >= THRESHOLD:
        sig = ("danger", obstacle.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ship.meters["drift"] += obstacle.attrs.get("severity", 1)
            for eid in ("hero", "friend"):
                world.get(eid).memes["worry"] += 1
            out.append("__danger__")
    return out


def _r_scatter(world: World) -> list[str]:
    out: list[str] = []
    ship = world.get("ship")
    cargo = world.get("cargo")
    if ship.meters["drift"] >= THRESHOLD and cargo.meters["secured"] < THRESHOLD:
        sig = ("scatter", cargo.id)
        if sig not in world.fired:
            world.fired.add(sig)
            cargo.meters["scattered"] += 1
            cargo.meters["lost_count"] += float(world.facts.get("spill_count", 12))
            out.append("__scatter__")
    return out


def _r_recover(world: World) -> list[str]:
    out: list[str] = []
    cargo = world.get("cargo")
    hero = world.get("hero")
    friend = world.get("friend")
    if (
        cargo.meters["scattered"] >= THRESHOLD
        and hero.meters["helping"] >= THRESHOLD
        and friend.meters["helping"] >= THRESHOLD
    ):
        sig = ("recover", cargo.id)
        if sig not in world.fired:
            world.fired.add(sig)
            cargo.meters["scattered"] = 0.0
            cargo.meters["recovered"] += 1
            out.append("__recover__")
    return out


CAUSAL_RULES = [
    Rule(name="danger", tag="physical", apply=_r_danger),
    Rule(name="scatter", tag="physical", apply=_r_scatter),
    Rule(name="recover", tag="physical", apply=_r_recover),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def helper_matches(obstacle: Obstacle, helper: Helper) -> bool:
    return obstacle.need == helper.power


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, setting in SETTINGS.items():
        for cargo_id in CARGOES:
            for obstacle_id in setting.affords:
                obstacle = OBSTACLES[obstacle_id]
                for helper_id, helper in HELPERS.items():
                    if helper_matches(obstacle, helper):
                        combos.append((place_id, cargo_id, obstacle_id, helper_id))
    return sorted(combos)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    obstacle = sim.get("obstacle")
    cargo = sim.get("cargo")
    obstacle.meters["active"] += 1
    cargo.meters["secured"] = 0.0
    propagate(sim, narrate=False)
    return {
        "drift": sim.get("ship").meters["drift"],
        "scattered": sim.get("cargo").meters["scattered"] >= THRESHOLD,
        "lost_count": int(sim.get("cargo").meters["lost_count"]),
    }


def intro(world: World, hero: Entity, friend: Entity, cargo: Cargo) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"{hero.id} and {friend.id} were best friends, and on the day of this adventure "
        f"their little silver rocket felt big enough for the whole sky."
    )
    world.say(
        f"They were carrying {cargo.phrase}, ready to bring them to {world.setting.destination}."
    )
    world.say(
        f"Inside the glass jar, the lights twinkled like a thousand tiny promises."
    )


def launch(world: World, hero: Entity, friend: Entity) -> None:
    ship = world.get("ship")
    ship.meters["steady"] = 1.0
    world.say(
        f"They lifted off through {world.setting.sky}, counting bright moons and waving at the stars."
    )
    world.say(
        f'"When we land at {world.setting.landing}," {friend.id} said, "let\'s do it together the whole way."'
    )


def obstacle_arrives(world: World, hero: Entity, friend: Entity, obstacle: Obstacle) -> None:
    world.say(
        f"But before they reached {world.setting.destination}, {obstacle.arrive}"
    )
    world.say(
        f'The rocket gave a wobble. "{obstacle.threat}," {hero.id} whispered.'
    )
    pred = predict_trouble(world)
    world.facts["predicted_drift"] = int(pred["drift"])
    world.facts["predicted_scattered"] = bool(pred["scattered"])
    world.facts["predicted_lost_count"] = int(pred["lost_count"])
    if pred["scattered"]:
        world.say(
            f'{friend.id} looked at the jar and said, "If we rush, we could spill some of the lights."'
        )


def rush_alone(world: World, hero: Entity, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    cargo = world.get("cargo")
    ship = world.get("ship")
    hero.memes["pride"] += 1
    cargo.meters["secured"] = 0.0
    ship.meters["steady"] = 0.0
    obstacle_ent.meters["active"] += 1
    markers = propagate(world, narrate=False)
    world.say(
        f'{hero.id} gripped the controls and said, "I can fix it myself with one quick magic spark."'
    )
    world.say(
        f"But the lonely little spell only made {obstacle.label} swirl harder around the rocket."
    )
    if "__scatter__" in markers:
        lost = int(cargo.meters["lost_count"])
        world.say(
            f"The rocket tipped, the jar popped open, and {lost} glowing stars whirled out into the dark."
        )
    elif "__danger__" in markers:
        world.say(
            f"The rocket slid sideways, and both friends grabbed their seats as the ship drifted."
        )
    world.say(obstacle.danger)


def friendship_turn(world: World, hero: Entity, friend: Entity, helper: Helper) -> None:
    hero.memes["shame"] += 1
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} did not scold. {friend.pronoun().capitalize()} reached out a hand instead."
    )
    world.say(
        f'"Magic works better when hearts work together," {friend.id} said. "Let\'s use {helper.phrase}."'
    )
    hero.memes["trust"] += 1
    friend.memes["trust"] += 1


def use_helper(world: World, hero: Entity, friend: Entity, obstacle: Obstacle, helper: Helper) -> None:
    obstacle_ent = world.get("obstacle")
    cargo = world.get("cargo")
    ship = world.get("ship")
    hero.meters["helping"] += 1
    friend.meters["helping"] += 1
    world.say(helper.join_text.format(hero=hero.id, friend=friend.id))
    obstacle_ent.meters["active"] = 0.0
    ship.meters["drift"] = 0.0
    ship.meters["steady"] = 1.0
    cargo.meters["secured"] = 1.0
    propagate(world, narrate=False)
    world.say(helper.success.format(obstacle=obstacle.label))
    if cargo.meters["recovered"] >= THRESHOLD:
        world.say(
            f"Working side by side, they caught every wandering light and tucked the little stars safely back into the jar."
        )
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.facts["used_together"] = True


def apology(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f'"I should have listened," {hero.id} said. "{friend.id}, thank you for staying with me."'
    )
    world.say(
        f'"That is what friends do," {friend.id} answered, and the ship felt warm again.'
    )


def landing(world: World, hero: Entity, friend: Entity, cargo: Cargo) -> None:
    cargo_ent = world.get("cargo")
    world.say(
        f"Soon the rocket slipped down at {world.setting.landing}, gentle as a feather."
    )
    world.say(
        f"There they used the shining cargo for {cargo.use}."
    )
    if cargo_ent.meters["lost_count"] >= THRESHOLD:
        world.say(
            f"Even after the spill, every light had been saved, and now they glowed even brighter for having been gathered together."
        )
    world.say(
        f"When the work was done, {world.setting.ending}."
    )
    world.say(
        f"Above them, the thousand wish-stars made a soft river of light, and the two friends smiled because they had learned the best magic was friendship shared."
    )


def tell(
    setting: Setting,
    cargo_cfg: Cargo,
    obstacle: Obstacle,
    helper: Helper,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    friend_name: str = "Orin",
    friend_type: str = "boy",
    parent_type: str = "mother",
) -> World:
    world = World(setting)
    world.facts["spill_count"] = 12
    world.facts["used_together"] = False
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, role="friend"))
    parent = world.add(Entity(id="guide", kind="character", type=parent_type, label="the guide", role="guide"))
    ship = world.add(Entity(id="ship", type="ship", label="rocket", attrs={"steady": True}))
    cargo = world.add(
        Entity(
            id="cargo",
            type="cargo",
            label=cargo_cfg.label,
            attrs={"ending": cargo_cfg.ending},
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            type="obstacle",
            label=obstacle.label,
            attrs={"need": obstacle.need, "severity": obstacle.severity},
        )
    )
    cargo.meters["secured"] = 1.0
    hero.meters["helping"] = 0.0
    friend.meters["helping"] = 0.0
    obstacle_ent.meters["active"] = 0.0
    ship.meters["drift"] = 0.0
    world.facts.update(
        hero=hero,
        friend=friend,
        guide=parent,
        setting=setting,
        cargo_cfg=cargo_cfg,
        helper=helper,
        obstacle_cfg=obstacle,
        cargo=cargo,
        obstacle=obstacle_ent,
    )

    intro(world, hero, friend, cargo_cfg)
    launch(world, hero, friend)
    world.para()
    obstacle_arrives(world, hero, friend, obstacle)
    rush_alone(world, hero, obstacle)
    world.para()
    friendship_turn(world, hero, friend, helper)
    use_helper(world, hero, friend, obstacle, helper)
    apology(world, hero, friend)
    world.para()
    landing(world, hero, friend, cargo_cfg)
    return world


SETTINGS = {
    "moon_meadow": Setting(
        id="moon_meadow",
        place="the Moon Meadow",
        sky="a velvet sky full of silver dust",
        destination="the Moon Meadow",
        landing="the pearl-white grass of the Moon Meadow",
        ending="they planted the lights in little round nests, and moonflowers opened all at once",
        affords={"shadow_fog", "sleepy_gate"},
        tags={"moon", "space"},
    ),
    "rainbow_ring": Setting(
        id="rainbow_ring",
        place="the Rainbow Ring Station",
        sky="the bright curve of a rainbow ring around a blue planet",
        destination="the Rainbow Ring Station",
        landing="a glowing ring-path above the clouds",
        ending="they tucked the lights into the ring lanterns, and the whole station shone in happy colors",
        affords={"shadow_fog", "meteor_breeze"},
        tags={"space", "station"},
    ),
    "comet_harbor": Setting(
        id="comet_harbor",
        place="Comet Harbor",
        sky="a deep purple night where comet tails streamed like ribbons",
        destination="Comet Harbor",
        landing="the soft ice docks of Comet Harbor",
        ending="they hung the lights along the harbor, and each sleeping comet boat woke with a friendly glow",
        affords={"meteor_breeze", "sleepy_gate"},
        tags={"space", "comet"},
    ),
}

OBSTACLES = {
    "shadow_fog": Obstacle(
        id="shadow_fog",
        label="the shadow fog",
        arrive="a band of shadow fog rolled across the stars and wrapped the window in dim gray curls.",
        need="light",
        threat="The path is hiding",
        danger="The dark made the rocket drift away from the bright star-path.",
        severity=1,
        tags={"fog", "light"},
    ),
    "meteor_breeze": Obstacle(
        id="meteor_breeze",
        label="the meteor breeze",
        arrive="a playful but pushy meteor breeze rushed past and bumped the rocket from side to side.",
        need="anchor",
        threat="The wind is pushing us off the lane",
        danger="The gusts tugged at the ship as if they wanted to spin it around.",
        severity=2,
        tags={"meteor", "wind"},
    ),
    "sleepy_gate": Obstacle(
        id="sleepy_gate",
        label="the sleepy gate",
        arrive="an old silver gate floated in front of them and would not open, only yawning slow moon-shaped yawns.",
        need="song",
        threat="The gate is still asleep",
        danger="The gate blocked the way so long that the rocket began to bob and turn in circles.",
        severity=1,
        tags={"gate", "song"},
    ),
}

HELPERS = {
    "star_lantern": Helper(
        id="star_lantern",
        label="star lantern",
        phrase="the star lantern",
        power="light",
        join_text="{hero} and {friend} held the star lantern together, and both of their thumbs warmed the same bright button.",
        success="A beam of friendly gold spread out, and {obstacle} melted back like a bad dream at morning.",
        tags={"lantern", "light"},
    ),
    "ribbon_rope": Helper(
        id="ribbon_rope",
        label="ribbon rope",
        phrase="the ribbon rope",
        power="anchor",
        join_text="{hero} and {friend} looped the ribbon rope around the steering post and pulled in the same steady rhythm.",
        success="The shining rope held fast, and {obstacle} could not tug the rocket away anymore.",
        tags={"rope", "anchor"},
    ),
    "humming_chime": Helper(
        id="humming_chime",
        label="humming chime",
        phrase="the humming chime",
        power="song",
        join_text="{hero} and {friend} rang the humming chime together, and its note floated out soft and round as moonlight.",
        success="The note curled through {obstacle}, and the sleepy silver way ahead slowly woke.",
        tags={"chime", "song"},
    ),
}

CARGOES = {
    "wish_stars": Cargo(
        id="wish_stars",
        label="wish-stars",
        phrase="a glass jar full of a thousand wish-stars",
        use="lighting the dark paths for little travelers",
        ending="the lights made every step look brave and welcoming",
        tags={"stars", "magic"},
    ),
    "moon_seeds": Cargo(
        id="moon_seeds",
        label="moon-seeds",
        phrase="a silver tin full of a thousand moon-seeds",
        use="planting new glowing flowers where the night felt empty",
        ending="tiny glowing stems lifted their heads and turned the quiet ground into a garden",
        tags={"seeds", "magic"},
    ),
    "comet_bells": Cargo(
        id="comet_bells",
        label="comet bells",
        phrase="a padded box with a thousand tiny comet bells",
        use="hanging music where lonely travelers needed a cheerful sound",
        ending="the bells chimed in the star-wind and made the whole place feel full of friends",
        tags={"bells", "magic"},
    ),
}

GIRL_NAMES = ["Mira", "Nova", "Luna", "Zara", "Ivy", "Ayla", "Nia", "Tali"]
BOY_NAMES = ["Orin", "Leo", "Finn", "Kai", "Milo", "Sol", "Nico", "Remy"]
TRAITS = ["brave", "curious", "gentle", "eager", "kind", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    cargo: str
    obstacle: str
    helper: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    parent: str
    hero_trait: str = "brave"
    friend_trait: str = "kind"
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
    "space": [
        (
            "What is space?",
            "Space is the huge place beyond Earth where the moon, planets, and stars are. It looks empty from far away, but it is full of amazing things.",
        )
    ],
    "moon": [
        (
            "What is the moon?",
            "The moon is the round world that circles Earth and shines in the night sky. It does not make its own light; it reflects light from the sun.",
        )
    ],
    "fog": [
        (
            "What is fog?",
            "Fog is a cloud so low that it hangs close around you. It can make it hard to see where you are going.",
        )
    ],
    "meteor": [
        (
            "What is a meteor?",
            "A meteor is a space rock or bit of dust that moves through space. When people talk about meteor showers, they mean many tiny bits streaking brightly across the sky.",
        )
    ],
    "gate": [
        (
            "What is a gate for?",
            "A gate is something that can open to let you pass through. When it is closed, it blocks the way until someone opens it.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see in dim places. In a story with magic, a lantern can also help guide the way.",
        )
    ],
    "rope": [
        (
            "What is a rope used for?",
            "A rope can help hold something steady or keep it from drifting away. It is useful when wind or movement would otherwise pull things around.",
        )
    ],
    "chime": [
        (
            "What is a chime?",
            "A chime is something that rings with a clear musical sound. Gentle sounds can be calming in stories and in real life.",
        )
    ],
    "stars": [
        (
            "What are stars?",
            "Stars are giant glowing balls of hot gas far away in space. In pretend stories, star-lights can also be magical little lights carried in jars or boxes.",
        )
    ],
    "friendship": [
        (
            "What does friendship mean?",
            "Friendship means caring about someone, helping them, and staying kind even when something goes wrong. Good friends do not have to be perfect; they keep trying together.",
        )
    ],
}
KNOWLEDGE_ORDER = ["space", "moon", "fog", "meteor", "gate", "lantern", "rope", "chime", "stars", "friendship"]


CURATED = [
    StoryParams(
        place="moon_meadow",
        cargo="wish_stars",
        obstacle="shadow_fog",
        helper="star_lantern",
        hero_name="Mira",
        hero_type="girl",
        friend_name="Orin",
        friend_type="boy",
        parent="mother",
        hero_trait="eager",
        friend_trait="kind",
    ),
    StoryParams(
        place="rainbow_ring",
        cargo="moon_seeds",
        obstacle="meteor_breeze",
        helper="ribbon_rope",
        hero_name="Leo",
        hero_type="boy",
        friend_name="Nova",
        friend_type="girl",
        parent="father",
        hero_trait="brave",
        friend_trait="thoughtful",
    ),
    StoryParams(
        place="comet_harbor",
        cargo="comet_bells",
        obstacle="sleepy_gate",
        helper="humming_chime",
        hero_name="Luna",
        hero_type="girl",
        friend_name="Kai",
        friend_type="boy",
        parent="mother",
        hero_trait="curious",
        friend_trait="gentle",
    ),
    StoryParams(
        place="moon_meadow",
        cargo="moon_seeds",
        obstacle="sleepy_gate",
        helper="humming_chime",
        hero_name="Finn",
        hero_type="boy",
        friend_name="Zara",
        friend_type="girl",
        parent="father",
        hero_trait="eager",
        friend_trait="kind",
    ),
    StoryParams(
        place="comet_harbor",
        cargo="wish_stars",
        obstacle="meteor_breeze",
        helper="ribbon_rope",
        hero_name="Ayla",
        hero_type="girl",
        friend_name="Remy",
        friend_type="boy",
        parent="mother",
        hero_trait="brave",
        friend_trait="thoughtful",
    ),
]


def explain_rejection(place: str, obstacle: Obstacle, helper: Helper) -> str:
    if obstacle.id not in SETTINGS[place].affords:
        return (
            f"(No story: {SETTINGS[place].place} does not fit {obstacle.label}. "
            f"Choose an obstacle that belongs in that part of the adventure.)"
        )
    return (
        f"(No story: {helper.phrase.capitalize()} cannot solve {obstacle.label}. "
        f"This obstacle needs {obstacle.need}, but that helper provides {helper.power}.)"
    )


ASP_RULES = r"""
valid(Place, Cargo, Obstacle, Helper) :-
    setting(Place), cargo(Cargo), affords(Place, Obstacle),
    obstacle(Obstacle), helper(Helper), need(Obstacle, Need), power(Helper, Need).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for obstacle_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, obstacle_id))
    for cargo_id in CARGOES:
        lines.append(asp.fact("cargo", cargo_id))
    for obstacle_id, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", obstacle_id))
        lines.append(asp.fact("need", obstacle_id, obstacle.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("power", helper_id, helper.power))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a magical space adventure where friendship helps solve the real problem."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include generation prompts and QA")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.obstacle and args.helper:
        setting = SETTINGS[args.place]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if args.obstacle not in setting.affords or not helper_matches(obstacle, helper):
            raise StoryError(explain_rejection(args.place, obstacle, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, cargo, obstacle, helper = rng.choice(combos)
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    friend_type = args.friend_type or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_type)
    friend_name = args.friend_name or _pick_name(rng, friend_type, avoid=hero_name)
    parent = args.parent or rng.choice(["mother", "father"])
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        cargo=cargo,
        obstacle=obstacle,
        helper=helper,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        parent=parent,
        hero_trait=hero_trait,
        friend_trait=friend_trait,
    )


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    cargo = world.facts["cargo_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    return [
        f'Write a short magical space adventure for a 3-to-5-year-old that uses the word "thousand" and ends with friendship solving the problem.',
        f"Tell a gentle story where {hero.label} and {friend.label} fly to {setting.place} with {cargo.phrase}, hit {obstacle.label}, and learn to use {helper.phrase} together.",
        f"Write a child-friendly space story about magic and friendship where a rushed choice causes trouble, but sharing the right helper makes the ending bright again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    cargo_cfg = world.facts["cargo_cfg"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper"]
    setting = world.facts["setting"]
    cargo = world.facts["cargo"]
    lost = int(cargo.meters["lost_count"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label} and {friend.label}, two best friends on a magical rocket trip. They were carrying {cargo_cfg.phrase} to {setting.place}.",
        ),
        (
            "What were they carrying?",
            f"They were carrying {cargo_cfg.phrase}. The story says the lights looked like a thousand tiny promises because the cargo was special and magical.",
        ),
        (
            f"What problem did they meet on the way to {setting.place}?",
            f"They ran into {obstacle.label}, which blocked or pushed their rocket off course. That problem mattered because it could make them lose their shining cargo before they landed.",
        ),
        (
            f"Why did trouble start when {hero.label} tried to fix things alone?",
            f"{hero.label} rushed and used a quick magic spark alone instead of working with {friend.label}. That made the obstacle worse, and the jar tipped so some of the lights flew out.",
        ),
        (
            f"How did {friend.label} help solve the problem?",
            f"{friend.label} stayed calm and reached out instead of scolding. Then the two friends used {helper.phrase} together, which matched what the obstacle needed and helped steady the rocket.",
        ),
    ]
    if cargo.meters["recovered"] >= THRESHOLD:
        qa.append(
            (
                "Did they get the lost lights back?",
                f"Yes. They worked side by side and gathered every wandering light back into the jar. The story shows that cooperation fixed both the space problem and the spill.",
            )
        )
    qa.append(
        (
            "What did they learn by the end?",
            f"They learned that friendship can make magic stronger. The ending proves it because they land safely, finish their job, and smile together under the thousand lights.",
        )
    )
    if lost > 0:
        qa.append(
            (
                f"How many lights spilled out when the rocket tipped?",
                f"{lost} little lights spilled out when the jar popped open. They were all saved later because the two friends worked together.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"space", "friendship"}
    setting = world.facts["setting"]
    obstacle = world.facts["obstacle_cfg"]
    helper = world.facts["helper"]
    cargo = world.facts["cargo_cfg"]
    tags |= set(setting.tags) | set(obstacle.tags) | set(helper.tags) | set(cargo.tags)
    if "moon" in tags:
        tags.add("moon")
    if "fog" in tags or obstacle.id == "shadow_fog":
        tags.add("fog")
    if "meteor" in tags or obstacle.id == "meteor_breeze":
        tags.add("meteor")
    if "gate" in tags or obstacle.id == "sleepy_gate":
        tags.add("gate")
    if helper.id == "star_lantern":
        tags.add("lantern")
    if helper.id == "ribbon_rope":
        tags.add("rope")
    if helper.id == "humming_chime":
        tags.add("chime")
    if cargo.id == "wish_stars":
        tags.add("stars")

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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.place]
    cargo_cfg = CARGOES[params.cargo]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]

    if params.obstacle not in setting.affords or not helper_matches(obstacle, helper):
        raise StoryError(explain_rejection(params.place, obstacle, helper))

    world = tell(
        setting=setting,
        cargo_cfg=cargo_cfg,
        obstacle=obstacle,
        helper=helper,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        parent_type=params.parent,
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
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases: list[StoryParams] = [CURATED[0]]
    try:
        smoke_cases.append(resolve_params(build_parser().parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAIL: resolve_params raised {err}")
        smoke_cases = [CURATED[0]]

    for i, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            buf = io.StringIO()
            with redirect_stdout(buf):
                emit(sample, trace=False, qa=(i == 1), header=f"### smoke {i}")
            if not sample.story.strip():
                raise StoryError("generated empty story")
        except Exception as err:  # pragma: no cover
            rc = 1
            print(f"SMOKE FAIL on case {i}: {err}")
        else:
            print(f"OK: smoke test {i} generated and emitted a story.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cargo, obstacle, helper) combos:\n")
        for place, cargo, obstacle, helper in combos:
            print(f"  {place:12} {cargo:12} {obstacle:14} {helper}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.obstacle} at {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
