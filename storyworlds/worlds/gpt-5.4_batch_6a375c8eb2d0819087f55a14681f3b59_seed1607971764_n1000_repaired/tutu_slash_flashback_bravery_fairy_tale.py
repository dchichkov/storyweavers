#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py
=====================================================================

A standalone story world for a small fairy-tale domain: a little fairy in a
tutu must cross a fearful obstacle to fetch a needed treasure for the evening's
celebration. When fear rises, she touches an old stitched slash in her tutu and
falls into a flashback of a mentor's lesson about bravery. The remembered lesson
changes what she does next.

The world models:
- physical state in meters (crossed, carried, mended, glow, etc.)
- emotional state in memes (fear, bravery, relief, joy)
- a simple reasonableness gate: an aid must suit the obstacle and be strong
  enough to work
- an inline ASP twin of the same gate and outcome logic

Run it
------
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py --setting rose_keep --obstacle thorn_gate --aid moon_shears
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py --obstacle shadow_tunnel --aid satin_sash
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/tutu_slash_flashback_bravery_fairy_tale.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "mother", "queen", "woman"}
        male = {"boy", "man", "king", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    celebration: str
    beyond: str
    affords: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    phrase: str
    risk: str
    severity: int
    warning: str
    crossing: str
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
class Aid:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    power: int = 0
    action: str = ""
    qa_text: str = ""
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
class Prize:
    id: str
    label: str
    phrase: str
    glow: str
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
class Helper:
    id: str
    label: str
    phrase: str
    arrival: str
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
        self.facts: dict = {
            "memory_ready": False,
            "flashbacked": False,
            "celebration_started": False,
            "outcome": "",
            "tiny_slash_worsened": False,
            "new_slash": False,
        }

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


def _r_flashback(world: World) -> list[str]:
    hero = world.entities.get("hero")
    if hero is None:
        return []
    if hero.memes["fear"] < THRESHOLD or not world.facts.get("memory_ready", False):
        return []
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["bravery"] += 1
    hero.memes["steady"] += 1
    world.facts["flashbacked"] = True
    return ["__flashback__"]


def _r_celebrate(world: World) -> list[str]:
    prize = world.entities.get("prize")
    village = world.entities.get("village")
    if prize is None or village is None:
        return []
    if prize.meters["returned"] < THRESHOLD:
        return []
    sig = ("celebrate", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.memes["joy"] += 1
    world.facts["celebration_started"] = True
    return ["__celebrate__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="flashback", tag="memory", apply=_r_flashback),
    Rule(name="celebrate", tag="social", apply=_r_celebrate),
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


SETTINGS = {
    "rose_keep": Setting(
        id="rose_keep",
        place="the Rose Keep",
        opening="At the edge of the Rose Keep, moonflowers climbed the old walls and silver dew waited on every leaf.",
        celebration="the Moon Dance",
        beyond="beyond the rose wall",
        affords={"bramble_arch", "thorn_gate"},
    ),
    "willow_glen": Setting(
        id="willow_glen",
        place="Willow Glen",
        opening="In Willow Glen, the stream talked softly to the roots of the trees and fireflies stitched light under the leaves.",
        celebration="the Lantern Waltz",
        beyond="past the willow roots",
        affords={"shadow_tunnel", "windy_bridge"},
    ),
    "starlit_moor": Setting(
        id="starlit_moor",
        place="the Starlit Moor",
        opening="Across the Starlit Moor, little blue stars bloomed in the grass and the wind carried songs from hidden doors.",
        celebration="the Star Supper",
        beyond="on the far side of the moor",
        affords={"windy_bridge", "shadow_tunnel", "thorn_gate"},
    ),
}

OBSTACLES = {
    "bramble_arch": Obstacle(
        id="bramble_arch",
        label="bramble arch",
        phrase="a low bramble arch",
        risk="sharp",
        severity=2,
        warning="Its hooked twigs could catch cloth and nip at anything soft.",
        crossing="the hooked twigs whispered at her sleeves and skirt",
        tags={"brambles", "sharp"},
    ),
    "thorn_gate": Obstacle(
        id="thorn_gate",
        label="thorn gate",
        phrase="a tall thorn gate",
        risk="sharp",
        severity=3,
        warning="Its black thorns were long enough to make a real slash in delicate cloth.",
        crossing="the thorns leaned close like a row of little spears",
        tags={"thorns", "sharp"},
    ),
    "shadow_tunnel": Obstacle(
        id="shadow_tunnel",
        label="shadow tunnel",
        phrase="a tunnel of shadows under old roots",
        risk="dark",
        severity=2,
        warning="Inside it, the path folded into darkness and swallowed the edges of things.",
        crossing="the dark closed around the path until even her slippers looked small",
        tags={"dark", "shadow"},
    ),
    "windy_bridge": Obstacle(
        id="windy_bridge",
        label="windy bridge",
        phrase="a windy plank bridge",
        risk="wind",
        severity=2,
        warning="The wind liked to tug at ribbons and wobble small brave feet.",
        crossing="the bridge sang and shivered over the water",
        tags={"bridge", "wind"},
    ),
}

AIDS = {
    "moon_shears": Aid(
        id="moon_shears",
        label="moon shears",
        phrase="a pair of moon shears",
        guards={"sharp"},
        power=3,
        action="trimmed a neat opening through the cruelest tangle",
        qa_text="used the moon shears to cut a safe little way through the thorns",
        tags={"shears", "sharp"},
    ),
    "silver_cloak": Aid(
        id="silver_cloak",
        label="silver cloak",
        phrase="a silver cloak",
        guards={"sharp"},
        power=2,
        action="wrapped the silver cloak tight and eased through the prickly opening",
        qa_text="wrapped herself in the silver cloak and slipped through carefully",
        tags={"cloak", "sharp"},
    ),
    "glow_jar": Aid(
        id="glow_jar",
        label="glow jar",
        phrase="a glow jar",
        guards={"dark"},
        power=2,
        action="lifted the glow jar high until its warm light found each stepping stone",
        qa_text="held up the glow jar so its light could show the path",
        tags={"light", "dark"},
    ),
    "satin_sash": Aid(
        id="satin_sash",
        label="satin sash",
        phrase="a long satin sash",
        guards={"wind"},
        power=2,
        action="looped the satin sash along the rail and held it like a bright guide line",
        qa_text="held the satin sash like a guide line across the bridge",
        tags={"sash", "wind"},
    ),
}

PRIZES = {
    "bell": Prize(
        id="bell",
        label="moon bell",
        phrase="the moon bell",
        glow="rang with a sound as clear as water in glass",
        tags={"bell"},
    ),
    "spool": Prize(
        id="spool",
        label="sun-gold spool",
        phrase="the sun-gold spool",
        glow="shone like a sleeping sunbeam",
        tags={"spool"},
    ),
    "seed": Prize(
        id="seed",
        label="star seed",
        phrase="the star seed",
        glow="glimmered like a tiny heart of morning",
        tags={"seed"},
    ),
}

HELPERS = {
    "moth": Helper(
        id="moth",
        label="moth",
        phrase="a velvet moth",
        arrival="A velvet moth fluttered beside her, soft as a drifting petal.",
        tags={"moth"},
    ),
    "mouse": Helper(
        id="mouse",
        label="mouse",
        phrase="a field mouse",
        arrival="A field mouse popped up from the grass and put both paws to its chest as if cheering for her.",
        tags={"mouse"},
    ),
    "robin": Helper(
        id="robin",
        label="robin",
        phrase="a red-breasted robin",
        arrival="A red-breasted robin dipped onto the rail and watched with bright patient eyes.",
        tags={"robin"},
    ),
}

FAIRY_NAMES = ["Lina", "Mira", "Tessa", "Nella", "Orla", "Pippa", "Faye", "Elsie"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for oid in sorted(setting.affords):
            obstacle = OBSTACLES[oid]
            for aid_id, aid in AIDS.items():
                if obstacle.risk in aid.guards and aid.power >= obstacle.severity:
                    combos.append((sid, oid, aid_id))
    return sorted(combos)


@dataclass
class StoryParams:
    setting: str
    obstacle: str
    aid: str
    prize: str
    helper: str
    hero: str
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


def obstacle_supported(setting: Setting, obstacle: Obstacle) -> bool:
    return obstacle.id in setting.affords


def aid_works(obstacle: Obstacle, aid: Aid) -> bool:
    return obstacle.risk in aid.guards and aid.power >= obstacle.severity


def outcome_of(params: StoryParams) -> str:
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if not aid_works(obstacle, aid):
        return "invalid"
    if obstacle.risk == "sharp" and aid.power == obstacle.severity:
        return "slashed"
    return "clean"


def explain_rejection(setting: Setting, obstacle: Obstacle, aid: Aid) -> str:
    if not obstacle_supported(setting, obstacle):
        return (
            f"(No story: {obstacle.phrase} does not belong in {setting.place}. "
            f"Choose an obstacle that fits that place.)"
        )
    if obstacle.risk not in aid.guards:
        return (
            f"(No story: {aid.phrase} does not solve a {obstacle.label}. "
            f"The aid must match the danger of the obstacle.)"
        )
    if aid.power < obstacle.severity:
        return (
            f"(No story: {aid.phrase} is too weak for {obstacle.phrase}. "
            f"In this world, the brave plan must be strong enough to work.)"
        )
    return "(No story: this combination is not reasonable.)"


def predict_crossing(world: World, obstacle_id: str, aid_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    obstacle = sim.get("obstacle")
    aid = sim.get("aid")
    hero.memes["fear"] += 1
    sim.facts["memory_ready"] = True
    propagate(sim, narrate=False)
    bravery_total = hero.memes["bravery"] + aid.attrs["power"]
    success = bravery_total >= obstacle.attrs["severity"]
    slash = (
        success
        and obstacle.attrs["risk"] == "sharp"
        and aid.attrs["power"] == obstacle.attrs["severity"]
    )
    return {"success": success, "slash": slash, "bravery_total": bravery_total}


def introduce(world: World, hero: Entity, prize: Prize) -> None:
    world.say(
        f"{world.setting.opening} In that bright place lived {hero.id}, a little fairy "
        f"who loved to spin in a soft tutu while everyone prepared for {world.setting.celebration}."
    )
    world.say(
        f"On this evening, the hall could not begin without {prize.phrase}, which had been left {world.setting.beyond}."
    )


def old_slash_memory_seed(world: World, hero: Entity) -> None:
    hero.attrs["old_slash_place"] = "the hem of her tutu"
    hero.meters["old_slash"] = 1
    hero.meters["mended"] = 1
    world.say(
        f"Near {hero.pronoun('possessive')} hem lay a tiny silver stitch where an old slash had once been mended."
    )


def call_to_quest(world: World, hero: Entity, obstacle: Obstacle, helper: Helper, prize: Prize) -> None:
    hero.memes["duty"] += 1
    world.say(
        f'"I will fetch {prize.phrase}," said {hero.id}, though {obstacle.phrase} waited in the way.'
    )
    world.say(helper.arrival)
    world.say(
        f"{helper.phrase.capitalize()} seemed to agree, yet even from far off {obstacle.warning}"
    )


def face_obstacle(world: World, hero: Entity, obstacle: Obstacle, aid: Aid) -> None:
    hero.memes["fear"] += 1
    world.facts["memory_ready"] = True
    world.facts["predicted"] = predict_crossing(world, obstacle.id, aid.id)
    world.say(
        f"When {hero.id} reached {obstacle.phrase}, {obstacle.crossing}. "
        f"{hero.pronoun('possessive').capitalize()} heart gave one frightened jump."
    )
    propagate(world, narrate=False)


def flashback(world: World, hero: Entity) -> None:
    if not world.facts.get("flashbacked"):
        return
    mentor = hero.attrs.get("mentor", "Grandmother Star")
    world.say(
        f"{hero.id} touched the old silver stitch on {hero.pronoun('possessive')} tutu, and a flashback came to {hero.pronoun('object')}."
    )
    world.say(
        f"Long ago, when a thorn had made that little slash, {mentor} had knelt beside {hero.pronoun('object')} and said, "
        f'"Bravery is not a heart that never trembles. It is a heart that keeps walking toward what is kind."'
    )


def choose_plan(world: World, hero: Entity, aid: Aid, obstacle: Obstacle) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} drew a breath, took up {aid.phrase}, and {aid.action}."
    )
    if obstacle.risk == "dark":
        world.say(
            f"The light made the hidden roots behave like honest roots again."
        )
    elif obstacle.risk == "wind":
        world.say(
            f"The sash fluttered, but now the wild air had something steady to pull against."
        )
    else:
        world.say(
            f"Each careful move made the dangerous way feel smaller than before."
        )


def cross_success(world: World, hero: Entity, obstacle: Obstacle, aid: Aid, prize: Prize, helper: Helper) -> None:
    obstacle_ent = world.get("obstacle")
    prize_ent = world.get("prize")
    obstacle_ent.meters["crossed"] = 1
    hero.memes["bravery"] += 1
    prize_ent.meters["carried"] = 1
    prize_ent.meters["returned"] = 1
    if obstacle.risk == "sharp" and aid.power == obstacle.severity:
        hero.meters["new_slash"] = 1
        world.facts["new_slash"] = True
        world.facts["tiny_slash_worsened"] = True
        world.say(
            f"One thorn still kissed the hem of her tutu and left a fresh little slash, but it was only cloth, and {hero.id} did not turn back."
        )
    world.say(
        f"On the far side she found {prize.phrase}. It {prize.glow} as if glad to be gathered into brave hands."
    )
    world.say(
        f"{helper.phrase.capitalize()} danced around her while she carried the treasure home."
    )
    propagate(world, narrate=False)


def homecoming(world: World, hero: Entity, prize: Prize) -> None:
    village = world.get("village")
    village.memes["gratitude"] += 1
    if world.facts.get("new_slash"):
        hero.meters["mended"] += 1
        world.say(
            f"Back at {world.setting.place}, the tailor-fairies laughed softly, mended the new slash with silver thread, and kissed the tip of the needle for luck."
        )
    else:
        world.say(
            f"Back at {world.setting.place}, everyone saw at once that fear had crossed home with her and changed into courage."
        )
    world.say(
        f"Then {prize.phrase} was set in its place, and {world.setting.celebration} began at last."
    )
    world.say(
        f"{hero.id} spun in her tutu once more, and this time she looked smaller than the hall and greater than her fear."
    )


def tell(
    setting: Setting,
    obstacle: Obstacle,
    aid: Aid,
    prize: Prize,
    helper: Helper,
    hero_name: str = "Lina",
) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            type="fairy",
            label=hero_name,
            phrase=hero_name,
            role="hero",
            attrs={"mentor": "Grandmother Star"},
            tags={"fairy", "hero"},
        )
    )
    village = world.add(
        Entity(
            id="village",
            kind="thing",
            type="hall",
            label=setting.place,
            phrase=setting.place,
            role="village",
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            role="obstacle",
            attrs={"risk": obstacle.risk, "severity": obstacle.severity},
            tags=set(obstacle.tags),
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            phrase=aid.phrase,
            role="aid",
            attrs={"power": aid.power, "guards": set(aid.guards)},
            tags=set(aid.tags),
        )
    )
    prize_ent = world.add(
        Entity(
            id="prize",
            kind="thing",
            type="prize",
            label=prize.label,
            phrase=prize.phrase,
            role="prize",
            tags=set(prize.tags),
        )
    )
    helper_ent = world.add(
        Entity(
            id="helper",
            kind="character",
            type="creature",
            label=helper.label,
            phrase=helper.phrase,
            role="helper",
            tags=set(helper.tags),
        )
    )
    hero.label = hero_name
    hero.phrase = hero_name
    hero.memes["bravery"] = 1
    hero.memes["fear"] = 0
    hero.meters["new_slash"] = 0
    world.facts.update(
        hero=hero,
        village=village,
        obstacle_cfg=obstacle,
        aid_cfg=aid,
        prize_cfg=prize,
        helper_cfg=helper,
    )

    introduce(world, hero, prize)
    old_slash_memory_seed(world, hero)

    world.para()
    call_to_quest(world, hero, obstacle, helper, prize)

    world.para()
    face_obstacle(world, hero, obstacle, aid)
    flashback(world, hero)
    choose_plan(world, hero, aid, obstacle)
    cross_success(world, hero, obstacle, aid, prize, helper)

    world.para()
    homecoming(world, hero, prize)

    world.facts["outcome"] = outcome_of(
        StoryParams(
            setting=setting.id,
            obstacle=obstacle.id,
            aid=aid.id,
            prize=prize.id,
            helper=helper.id,
            hero=hero_name,
        )
    )
    return world


KNOWLEDGE = {
    "tutu": [
        (
            "What is a tutu?",
            "A tutu is a light, fluffy skirt worn for dancing. It can swish and spin when someone twirls."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the right or kind thing even when you feel afraid. It does not mean your fear disappears first."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is a short look back to something that happened earlier. It helps explain why a character feels or acts a certain way now."
        )
    ],
    "thorns": [
        (
            "Why are thorns sharp?",
            "Thorns are hard, pointed parts of some plants. They can poke skin or cloth and sometimes make a scratch or a slash."
        )
    ],
    "shadow": [
        (
            "Why can darkness feel scary?",
            "Darkness can feel scary because it hides where things are. When you cannot see the path clearly, your body may feel unsure."
        )
    ],
    "bridge": [
        (
            "Why should you cross a bridge carefully?",
            "A bridge can wobble or feel narrow, so careful steps help you stay steady. Holding something firm can make crossing safer."
        )
    ],
    "light": [
        (
            "How can a light help in the dark?",
            "A light shows where the path and obstacles are. When you can see clearly, it is easier to choose safe steps."
        )
    ],
    "shears": [
        (
            "What are shears?",
            "Shears are strong scissors used for cutting tougher things. In stories, they can trim branches or thorny plants."
        )
    ],
    "cloak": [
        (
            "What does a cloak do?",
            "A cloak is a loose outer cloth worn over clothes. It can help keep someone warm or protect what is underneath."
        )
    ],
    "sash": [
        (
            "What is a sash?",
            "A sash is a long strip of cloth or ribbon. It can be tied around someone or used to mark the way."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "tutu",
    "bravery",
    "flashback",
    "thorns",
    "shadow",
    "bridge",
    "light",
    "shears",
    "cloak",
    "sash",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle_cfg"]
    prize = f["prize_cfg"]
    return [
        f'Write a fairy-tale story for a 3-to-5-year-old that includes the words "tutu" and "slash" and uses a flashback to teach bravery.',
        f"Tell a gentle fairy tale where {hero.label} must cross {obstacle.phrase} to bring back {prize.phrase}, and a remembered lesson helps her be brave.",
        f"Write a short story in which a little fairy touches a mended place on her tutu, remembers an old warning, and then chooses courage.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    prize = f["prize_cfg"]
    helper = f["helper_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a little fairy in a tutu, who went to fetch {prize.phrase} for {world.setting.celebration}. She wanted to help everyone, even though the way was frightening.",
        ),
        (
            f"Why did {hero.label} have to go out?",
            f"The celebration could not begin without {prize.phrase}, which had been left {world.setting.beyond}. She went because the missing treasure mattered to everyone waiting at home.",
        ),
        (
            f"What made {hero.label} feel afraid?",
            f"{obstacle.phrase.capitalize()} stood between her and the treasure, and it seemed dangerous. Its danger matched the world around it, so her fear came from a real risk, not from nothing.",
        ),
        (
            f"What was the flashback about?",
            f"When {hero.label} touched the old silver stitch on her tutu, she remembered the time a thorn had made a little slash there. In that memory, Grandmother Star told her that bravery means walking toward what is kind even while your heart trembles.",
        ),
        (
            f"How did {hero.label} get past the obstacle?",
            f"She used {aid.phrase} and {aid.qa_text}. The remembered lesson made her steadier, so she could use the plan instead of giving in to fear.",
        ),
    ]
    if outcome == "slashed":
        qa.append(
            (
                f"Did anything happen to the tutu?",
                f"Yes. A thorn made a fresh little slash in the hem of her tutu, but she kept going and still carried the treasure home. Later the tailor-fairies mended it with silver thread, which showed that a brave choice can leave a mark and still end well.",
            )
        )
    else:
        qa.append(
            (
                f"How did the story end?",
                f"{hero.label} brought back {prize.phrase}, and {world.setting.celebration} began at last. She spun in her tutu again, but now everyone could see that she had grown braver than before.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"tutu", "bravery", "flashback"}
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    if obstacle.risk == "sharp":
        tags.add("thorns")
    elif obstacle.risk == "dark":
        tags.update({"shadow", "light"})
    elif obstacle.risk == "wind":
        tags.add("bridge")
        tags.add("sash")
    if aid.id == "moon_shears":
        tags.add("shears")
    if aid.id == "silver_cloak":
        tags.add("cloak")
    if aid.id == "glow_jar":
        tags.add("light")
    if aid.id == "satin_sash":
        tags.add("sash")
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: { {k: v for k, v in world.facts.items() if k not in {'hero', 'village', 'obstacle_cfg', 'aid_cfg', 'prize_cfg', 'helper_cfg'}} }")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,A) :- setting(S), obstacle(O), aid(A), affords(S,O), guards(A,R), risk(O,R), power(A,P), severity(O,V), P >= V.

outcome(slug_clean,S,O,A) :- valid(S,O,A), risk(O,R), R != sharp.
outcome(slug_clean,S,O,A) :- valid(S,O,A), risk(O,sharp), power(A,P), severity(O,V), P > V.
outcome(slug_slashed,S,O,A) :- valid(S,O,A), risk(O,sharp), power(A,P), severity(O,V), P = V.

#show valid/3.
#show outcome/4.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for oid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, oid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("risk", oid, obstacle.risk))
        lines.append(asp.fact("severity", oid, obstacle.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for guard in sorted(aid.guards):
            lines.append(asp.fact("guards", aid_id, guard))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcomes() -> dict[tuple[str, str, str], str]:
    import asp

    model = asp.one_model(asp_program())
    out: dict[tuple[str, str, str], str] = {}
    for slug, setting, obstacle, aid in asp.atoms(model, "outcome"):
        if slug == "slug_clean":
            out[(setting, obstacle, aid)] = "clean"
        elif slug == "slug_slashed":
            out[(setting, obstacle, aid)] = "slashed"
    return out


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: valid_combos matches ASP ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in ASP:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in Python:", sorted(py_set - asp_set))

    asp_map = asp_outcomes()
    cases: list[StoryParams] = list(CURATED)
    for seed in range(80):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        key = (params.setting, params.obstacle, params.aid)
        if outcome_of(params) != asp_map.get(key, "invalid"):
            mismatches.append((key, outcome_of(params), asp_map.get(key, "invalid")))
    if not mismatches:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print("MISMATCH in outcomes:")
        for key, py_out, asp_out in mismatches[:10]:
            print(f"  {key}: python={py_out} asp={asp_out}")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        sample.to_json()
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="verify-smoke")
        print("OK: generate/emit smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        setting="rose_keep",
        obstacle="bramble_arch",
        aid="silver_cloak",
        prize="bell",
        helper="moth",
        hero="Lina",
    ),
    StoryParams(
        setting="rose_keep",
        obstacle="thorn_gate",
        aid="moon_shears",
        prize="seed",
        helper="robin",
        hero="Mira",
    ),
    StoryParams(
        setting="willow_glen",
        obstacle="shadow_tunnel",
        aid="glow_jar",
        prize="spool",
        helper="mouse",
        hero="Tessa",
    ),
    StoryParams(
        setting="starlit_moor",
        obstacle="windy_bridge",
        aid="satin_sash",
        prize="bell",
        helper="robin",
        hero="Nella",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a fairy tale of a tutu, a remembered slash, and bravery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting is not None and args.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {args.setting})")
    if args.obstacle is not None and args.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {args.obstacle})")
    if args.aid is not None and args.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {args.aid})")
    if args.prize is not None and args.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {args.prize})")
    if args.helper is not None and args.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {args.helper})")

    if args.setting and args.obstacle and args.aid:
        setting = SETTINGS[args.setting]
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if not (obstacle_supported(setting, obstacle) and aid_works(obstacle, aid)):
            raise StoryError(explain_rejection(setting, obstacle, aid))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, obstacle_id, aid_id = rng.choice(combos)
    prize_id = args.prize or rng.choice(sorted(PRIZES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    hero = args.hero or rng.choice(FAIRY_NAMES)
    return StoryParams(
        setting=setting_id,
        obstacle=obstacle_id,
        aid=aid_id,
        prize=prize_id,
        helper=helper_id,
        hero=hero,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if not (obstacle_supported(setting, obstacle) and aid_works(obstacle, aid)):
        raise StoryError(explain_rejection(setting, obstacle, aid))

    world = tell(
        setting=setting,
        obstacle=obstacle,
        aid=aid,
        prize=PRIZES[params.prize],
        helper=HELPERS[params.helper],
        hero_name=params.hero,
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
        outs = asp_outcomes()
        print(f"{len(combos)} compatible (setting, obstacle, aid) combos:\n")
        for setting, obstacle, aid in combos:
            print(f"  {setting:13} {obstacle:14} {aid:12} -> {outs[(setting, obstacle, aid)]}")
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
            header = f"### {p.hero}: {p.obstacle} at {p.setting} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
