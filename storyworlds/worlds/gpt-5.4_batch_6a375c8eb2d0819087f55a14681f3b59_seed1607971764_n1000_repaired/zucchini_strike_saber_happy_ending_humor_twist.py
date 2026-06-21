#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py
=============================================================================

A standalone story world for a tiny myth-shaped tale: a child hears a mighty
night-time strike from a hill shrine, marches out with a toy saber to face what
must surely be a monster, and discovers a ridiculous truth instead.

The world is built around a simple causal chain:

    moving cause + loose zucchini on a slope -> zucchini rolls
    rolling zucchini + hanging bronze thing  -> loud strike
    loud strike + boastful guess             -> hero fears a "monster"
    helper advises calm search               -> hero inspects instead of attacks
    inspection reveals the twist             -> laughter + feast + lesson

The stories are playful "mini-myths": moonlit hill, shrine, village, bold
promise, comic mistake, happy ending.  The required seed words all appear in
state-driven prose: zucchini, strike, saber.

Run it
------
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py --realm moon_hill --cause goat
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py --cause breeze --hanger bell
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py --hanger fountain
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py --all
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/zucchini_strike_saber_happy_ending_humor_twist.py --verify
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
NOISE_MIN = 2
BRAG_MIN = 5


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
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
        female = {"girl", "woman", "mother", "aunt", "priestess"}
        male = {"boy", "man", "father", "uncle", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "priestess": "priestess",
            "priest": "priest",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configs
# ---------------------------------------------------------------------------
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
    sky: str
    shrine: str
    path: str
    image: str
    villagers: str
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
class Cause:
    id: str
    label: str
    kind: str
    power: int
    text: str
    clue: str
    funny: str
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
class Hanger:
    id: str
    label: str
    article: str
    sound: str
    strike_verb: str
    hangs: bool
    loudness: int
    text: str
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
class SaberKind:
    id: str
    phrase: str
    brave_style: str
    harmless: bool = True
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
class HelperKind:
    id: str
    type: str
    title: str
    wisdom: str
    comfort: str
    feast_line: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_roll(world: World) -> list[str]:
    zucchini = world.get("zucchini")
    cause = world.get("cause")
    if cause.meters["push"] < THRESHOLD or zucchini.meters["loose"] < THRESHOLD:
        return []
    sig = ("roll",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    zucchini.meters["rolling"] += 1
    world.get("path").meters["rattled"] += 1
    return ["__roll__"]


def _r_strike(world: World) -> list[str]:
    zucchini = world.get("zucchini")
    hanger = world.get("hanger")
    if zucchini.meters["rolling"] < THRESHOLD or hanger.meters["hanging"] < THRESHOLD:
        return []
    sig = ("strike",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hanger.meters["struck"] += 1
    world.get("night").meters["noise"] += float(world.facts["noise_value"])
    return ["__strike__"]


def _r_guess(world: World) -> list[str]:
    hero = world.get("hero")
    night = world.get("night")
    if night.meters["noise"] < THRESHOLD or hero.memes["brag"] < THRESHOLD:
        return []
    sig = ("guess_monster",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["resolve"] += 1
    world.facts["monster_guess"] = True
    return ["__guess__"]


RULES = [
    Rule(name="roll", tag="physical", apply=_r_roll),
    Rule(name="strike", tag="physical", apply=_r_strike),
    Rule(name="guess", tag="social", apply=_r_guess),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend(res)
    if narrate:
        for item in out:
            if not item.startswith("__"):
                world.say(item)
    return out


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def cause_can_move(cause: Cause) -> bool:
    return cause.power >= 1


def can_make_strike(cause: Cause, hanger: Hanger) -> bool:
    return cause_can_move(cause) and hanger.hangs and (cause.power + hanger.loudness >= NOISE_MIN)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for realm_id in REALMS:
        for cause_id, cause in CAUSES.items():
            for hanger_id, hanger in HANGERS.items():
                if can_make_strike(cause, hanger):
                    combos.append((realm_id, cause_id, hanger_id))
    return combos


def noise_value(cause: Cause, hanger: Hanger) -> int:
    return cause.power + hanger.loudness


def outcome_for(params: "StoryParams") -> str:
    return "loud_laugh" if params.brag >= BRAG_MIN else "gentle_laugh"


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_night(world: World) -> dict:
    sim = world.copy()
    sim.get("cause").meters["push"] += 1
    propagate(sim, narrate=False)
    return {
        "rolling": sim.get("zucchini").meters["rolling"] >= THRESHOLD,
        "noise": sim.get("night").meters["noise"],
        "monster_guess": bool(sim.facts.get("monster_guess")),
    }


# ---------------------------------------------------------------------------
# Story verbs
# ---------------------------------------------------------------------------
def opening(world: World, hero: Entity, helper: Entity, realm: Realm) -> None:
    hero.memes["joy"] += 1
    helper.memes["care"] += 1
    world.say(
        f"In the old days, when {realm.sky} and every hill kept a rumor, "
        f"{realm.villagers} told stories about {realm.shrine}."
    )
    world.say(
        f"There lived {hero.id}, a young {hero.type} who liked brave poses, "
        f"bright promises, and the clack of a toy saber against {hero.pronoun('possessive')} sandal."
    )
    world.say(
        f"{helper.title.capitalize()} {helper.id} often smiled at those poses and said, "
        f'"{helper.attrs["wisdom"]}"'
    )


def offering_setup(world: World, realm: Realm) -> None:
    zucchini = world.get("zucchini")
    zucchini.meters["loose"] = 1
    world.say(
        f"That evening, someone left a giant zucchini on the shrine step as an offering, "
        f"green as river glass and almost as long as a baby goat."
    )
    world.say(
        f"It rested beside {realm.path}, where stones tilted downward in a sly little slope."
    )


def boast(world: World, hero: Entity, saber: SaberKind) -> None:
    hero.memes["brag"] = float(world.facts["brag"])
    world.say(
        f"{hero.id} lifted {hero.pronoun('possessive')} {saber.phrase} and whispered that "
        f"if any shadow-beast came creeping, one noble strike would send it hopping home."
    )


def night_sound(world: World, cause: Cause, hanger: Hanger) -> None:
    world.get("cause").meters["push"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {cause.text}. The zucchini wriggled, rolled down the step, and "
        f"{hanger.strike_verb} {hanger.article} {hanger.label}."
    )
    world.say(
        f"{hanger.sound.capitalize()}! The sound ran over the hill so loudly that even the olives seemed to listen."
    )


def fear_guess(world: World, hero: Entity, hanger: Hanger) -> None:
    if not world.facts.get("monster_guess"):
        return
    hero.memes["boast_scared"] += 1
    world.say(
        f"{hero.id}'s heart gave a hop. Because the night strike had been so loud, "
        f"{hero.pronoun()} decided it must belong to a moon-ogre sharpening seven teeth behind the shrine."
    )
    world.say(
        f'"Stay back," {hero.pronoun()} declared, though {hero.pronoun("possessive")} voice came out smaller than {hanger.article} {hanger.label}.'
    )


def helper_warning(world: World, helper: Entity, hero: Entity, cause: Cause) -> None:
    pred = predict_night(world)
    world.facts["predicted_noise"] = pred["noise"]
    helper.memes["calm"] += 1
    world.say(
        f"But {helper.title} {helper.id} saw {cause.clue} and noticed the fresh scrape on the shrine stone."
    )
    world.say(
        f'"Big noises do not always mean big monsters," {helper.pronoun()} said. '
        f'"Come see with your eyes before your knees start shaking the whole hill."'
    )


def search(world: World, hero: Entity, helper: Entity, realm: Realm) -> None:
    hero.memes["resolve"] += 1
    helper.memes["care"] += 1
    world.say(
        f"So the two climbed {realm.path} together, {helper.id} carrying a lamp and "
        f"{hero.id} carrying the saber as solemnly as if the stars were watching a contest."
    )


def reveal(world: World, hero: Entity, helper: Entity, cause: Cause, hanger: Hanger) -> None:
    zucchini = world.get("zucchini")
    hero.memes["fear"] = 0.0
    hero.memes["surprise"] += 1
    hero.memes["laughter"] += 1
    helper.memes["laughter"] += 1
    zucchini.meters["split"] += 1
    world.facts["twist"] = "zucchini"
    if outcome_for(world.facts["params"]) == "loud_laugh":
        world.say(
            f"Behind the shrine there was no moon-ogre at all. There was only the great zucchini, "
            f"stuck under the hanging {hanger.label}, rocking back and forth as if it wanted another strike."
        )
        world.say(
            f"{hero.id} gave it one brave poke with the saber. The zucchini split with a soft pop, "
            f"sprayed pale seeds on {hero.pronoun('possessive')} ankles, and looked less like a demon than a very surprised supper."
        )
    else:
        world.say(
            f"Behind the shrine there was no moon-ogre at all. The mighty troublemaker was the giant zucchini, "
            f"which had rolled under the hanging {hanger.label} and kept nudging it like a clumsy drummer."
        )
        world.say(
            f"When {hero.id} touched it with the tip of the saber, the vegetable tipped over and bumped {helper.id}'s sandal. "
            f"It was hard to fear an enemy that behaved like a sleepy green log."
        )
    world.say(
        f"For one breath they stared. Then {helper.id} laughed first, and soon {hero.id} laughed too, "
        f"because the fearsome night strike had come from {cause.funny} and one wandering zucchini."
    )


def feast(world: World, hero: Entity, helper: Entity, realm: Realm, cause: Cause) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By dawn, {realm.villagers} knew the truth. No one built a monster shrine; they built a cooking fire instead."
    )
    world.say(
        f"{helper.title.capitalize()} {helper.id} {helper.attrs['feast_line']}, and {hero.id} told the story of the terrible vegetable with such grand gestures that the children nearly rolled down the hill themselves."
    )
    world.say(
        f"After that, whenever a sudden strike echoed over {realm.place}, people smiled before they worried. "
        f"And {hero.id}, wiser and happier, still carried the saber -- but now mostly for pointing at runaway squash."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(
    realm: Realm,
    cause: Cause,
    hanger: Hanger,
    saber_kind: SaberKind,
    helper_kind: HelperKind,
    *,
    hero_name: str = "Ivo",
    hero_type: str = "boy",
    helper_name: str = "Tala",
    brag: int = 5,
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, role="hero", label=hero_name))
    helper = world.add(
        Entity(id="helper", kind="character", type=helper_kind.type, role="helper", label=helper_name)
    )
    helper.attrs["wisdom"] = helper_kind.wisdom
    helper.attrs["feast_line"] = helper_kind.feast_line
    world.add(Entity(id="zucchini", type="zucchini", label="zucchini"))
    world.add(Entity(id="cause", type=cause.kind, label=cause.label))
    world.add(Entity(id="hanger", type="hanger", label=hanger.label))
    world.add(Entity(id="night", type="night", label="the night"))
    world.add(Entity(id="path", type="path", label=realm.path))
    world.get("hanger").meters["hanging"] = 1
    world.facts["noise_value"] = noise_value(cause, hanger)
    world.facts["monster_guess"] = False
    world.facts["twist"] = ""
    world.facts["brag"] = brag

    opening(world, hero, helper, realm)
    offering_setup(world, realm)

    world.para()
    boast(world, hero, saber_kind)
    night_sound(world, cause, hanger)
    fear_guess(world, hero, hanger)
    helper_warning(world, helper, hero, cause)

    world.para()
    search(world, hero, helper, realm)
    reveal(world, hero, helper, cause, hanger)
    feast(world, hero, helper, realm, cause)

    world.facts.update(
        hero=hero,
        helper=helper,
        realm=realm,
        cause_cfg=cause,
        hanger_cfg=hanger,
        saber_cfg=saber_kind,
        helper_cfg=helper_kind,
        discovered="zucchini",
        outcome=outcome_for(world.facts["params"]),
        loud_noise=world.get("night").meters["noise"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
REALMS = {
    "moon_hill": Realm(
        id="moon_hill",
        place="Moon Hill",
        sky="the moon sat low over the cedar trees",
        shrine="the little hill shrine of the silver bowl",
        path="the pebble path that curled like a snail shell",
        image="moon",
        villagers="the goat-herds of Moon Hill",
        tags={"myth", "hill"},
    ),
    "olive_gate": Realm(
        id="olive_gate",
        place="Olive Gate",
        sky="the first stars trembled above the olive groves",
        shrine="the gate shrine where travelers tied blue ribbons",
        path="the old olive path worn smooth by sandals",
        image="olive",
        villagers="the olive-pickers of Olive Gate",
        tags={"myth", "grove"},
    ),
    "sun_steps": Realm(
        id="sun_steps",
        place="Sun Steps",
        sky="the last gold of sunset still clung to the stones",
        shrine="the stair shrine of the patient sun",
        path="the steep stair path of warm red stone",
        image="sun",
        villagers="the bakers of Sun Steps",
        tags={"myth", "steps"},
    ),
}

CAUSES = {
    "goat": Cause(
        id="goat",
        label="goat",
        kind="goat",
        power=2,
        text="a temple goat reached its nosy nose through the rail and nibbled the offering's stem",
        clue="hoofprints in the dust",
        funny="a nosy goat",
        tags={"goat", "animal"},
    ),
    "breeze": Cause(
        id="breeze",
        label="breeze",
        kind="wind",
        power=1,
        text="a hill breeze slipped between the shrine posts and gave the offering a sly little shove",
        clue="ribbons fluttering in the same direction",
        funny="a pushy breeze",
        tags={"wind", "weather"},
    ),
    "monkey": Cause(
        id="monkey",
        label="monkey",
        kind="monkey",
        power=2,
        text="a striped orchard monkey tried to steal the offering and dropped it in surprise",
        clue="a monkey tail flicking out of the fig tree",
        funny="a thieving monkey",
        tags={"monkey", "animal"},
    ),
}

HANGERS = {
    "gong": Hanger(
        id="gong",
        label="bronze gong",
        article="a",
        sound="BONG",
        strike_verb="struck",
        hangs=True,
        loudness=2,
        text="a bronze gong hung beside the shrine",
        tags={"gong", "bronze"},
    ),
    "bell": Hanger(
        id="bell",
        label="temple bell",
        article="a",
        sound="CLANG",
        strike_verb="banged against",
        hangs=True,
        loudness=1,
        text="a temple bell hung beside the shrine",
        tags={"bell", "bronze"},
    ),
    "shield": Hanger(
        id="shield",
        label="ceremonial shield",
        article="a",
        sound="TANG",
        strike_verb="smacked",
        hangs=True,
        loudness=1,
        text="a ceremonial shield hung beside the shrine",
        tags={"shield", "bronze"},
    ),
    "fountain": Hanger(
        id="fountain",
        label="stone fountain",
        article="a",
        sound="plunk",
        strike_verb="bumped",
        hangs=False,
        loudness=0,
        text="a stone fountain sat beside the shrine",
        tags={"stone"},
    ),
}

SABERS = {
    "wood": SaberKind(
        id="wood",
        phrase="wooden saber",
        brave_style="held high",
        tags={"saber", "wood"},
    ),
    "reed": SaberKind(
        id="reed",
        phrase="reed saber wrapped in red thread",
        brave_style="pointed toward the dark",
        tags={"saber", "reed"},
    ),
    "painted": SaberKind(
        id="painted",
        phrase="painted practice saber",
        brave_style="tucked under one arm like a hero in training",
        tags={"saber", "painted"},
    ),
}

HELPERS = {
    "priestess": HelperKind(
        id="priestess",
        type="priestess",
        title="priestess",
        wisdom="Courage walks best when it brings its eyes along.",
        comfort="steady",
        feast_line="cut the zucchini into ribbons and cooked it with garlic and honey",
        tags={"elder", "food"},
    ),
    "aunt": HelperKind(
        id="aunt",
        type="aunt",
        title="aunt",
        wisdom="A loud sound may be only a foolish thing falling.",
        comfort="warm",
        feast_line="fried the zucchini in a broad pan until the edges curled and shone",
        tags={"family", "food"},
    ),
    "priest": HelperKind(
        id="priest",
        type="priest",
        title="priest",
        wisdom="The dark grows monsters fastest inside a hurried mind.",
        comfort="calm",
        feast_line="stewed the zucchini with beans and herbs for the whole square",
        tags={"elder", "food"},
    ),
}

GIRL_NAMES = ["Nia", "Mira", "Eli", "Sela", "Rina", "Thia"]
BOY_NAMES = ["Ivo", "Daro", "Pelin", "Niko", "Timo", "Aren"]
HELPER_NAMES = ["Tala", "Maro", "Sira", "Yorin", "Besa", "Leto"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    realm: str
    cause: str
    hanger: str
    saber: str
    helper: str
    hero_name: str
    hero_type: str
    helper_name: str
    brag: int = 5
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "zucchini": [
        (
            "What is a zucchini?",
            "A zucchini is a long green vegetable. People can cook it in many ways, and it is not scary at all.",
        )
    ],
    "gong": [
        (
            "What does a gong sound like?",
            "A gong makes a deep ringing sound when something strikes it. Big metal things can sound much louder than they look.",
        )
    ],
    "bell": [
        (
            "Why can a bell sound loud?",
            "A bell is shaped to ring when it is hit or shaken. The metal helps the sound travel far.",
        )
    ],
    "shield": [
        (
            "Can a shield make a sound?",
            "Yes. If something hits a metal shield, it can clang or ring.",
        )
    ],
    "goat": [
        (
            "Why do goats sniff and nibble things?",
            "Goats are curious animals and often explore with their noses and mouths. That can get them into silly trouble.",
        )
    ],
    "monkey": [
        (
            "Why are monkeys often troublemakers in stories?",
            "Monkeys are quick, curious, and grabby, so they are good at making comic messes in stories.",
        )
    ],
    "wind": [
        (
            "Can wind move things?",
            "Yes. Even a breeze can push or roll a loose thing if it is light enough or sitting on a slope.",
        )
    ],
    "saber": [
        (
            "What is a saber?",
            "A saber is a kind of sword with a long blade. In this story, the saber is only a toy or practice one, so it is for pretending, not hurting.",
        )
    ],
    "fear": [
        (
            "Why do small sounds sometimes feel bigger at night?",
            "At night you cannot see as much, so your mind may guess before your eyes do. That can make an ordinary sound feel mysterious.",
        )
    ],
}
KNOWLEDGE_ORDER = ["zucchini", "gong", "bell", "shield", "goat", "monkey", "wind", "saber", "fear"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    realm = f["realm"]
    cause = f["cause_cfg"]
    hanger = f["hanger_cfg"]
    return [
        'Write a short child-facing myth that includes the words "zucchini", "strike", and "saber", and ends happily with a comic twist.',
        f"Tell a tiny myth set at {realm.place} where {hero.label} hears a mighty strike in the night, marches out with a saber, and discovers that the trouble came from {cause.funny} and a runaway zucchini.",
        f"Write a gentle humorous legend where {helper.label} helps {hero.label} learn that a loud noise from {hanger.label} does not always mean a monster.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    realm = f["realm"]
    cause = f["cause_cfg"]
    hanger = f["hanger_cfg"]
    saber = f["saber_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.label}, a young would-be hero, and {helper.label}, the {helper.label_word} who helps {hero.pronoun('object')} think calmly. They live in the mythic place called {realm.place}.",
        ),
        (
            "Why did the hero think something dangerous was near the shrine?",
            f"{hero.label} heard a loud strike in the night after the hanging {hanger.label} was hit. Because the sound was sudden and big, {hero.pronoun()} guessed a monster must be hiding there.",
        ),
        (
            f"Why was {helper.label} not fooled so quickly?",
            f"{helper.label} noticed {cause.clue} and the scrape by the shrine. Those clues pointed to something physical and silly, not a hidden beast.",
        ),
        (
            f"What was the twist?",
            f"The terrible night troublemaker was only a zucchini that had rolled and hit the {hanger.label}. The sound was real, but the monster was imaginary.",
        ),
        (
            f"Why was the saber funny instead of frightening?",
            f"{hero.label} carried a {saber.phrase}, which made {hero.pronoun('object')} feel grand. Once the truth came out, the brave pose looked funny because the enemy was just a runaway vegetable.",
        ),
        (
            "How did the story end?",
            f"It ended happily with laughter and food. The villagers cooked the zucchini, and everyone remembered to look before panicking.",
        ),
    ]
    if f["predicted_noise"] >= THRESHOLD:
        out.append(
            (
                f"Why did the sound travel across the hill?",
                f"The rolling zucchini struck the hanging {hanger.label}, which was made to ring loudly. That is why one bump turned into a night sound the whole village could hear.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"zucchini", "saber", "fear"}
    cause = f["cause_cfg"]
    hanger = f["hanger_cfg"]
    if cause.id == "goat":
        tags.add("goat")
    elif cause.id == "monkey":
        tags.add("monkey")
    elif cause.id == "breeze":
        tags.add("wind")
    if hanger.id in ("gong", "bell", "shield"):
        tags.add(hanger.id)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        realm="moon_hill",
        cause="goat",
        hanger="gong",
        saber="wood",
        helper="priestess",
        hero_name="Ivo",
        hero_type="boy",
        helper_name="Tala",
        brag=6,
    ),
    StoryParams(
        realm="olive_gate",
        cause="breeze",
        hanger="bell",
        saber="reed",
        helper="aunt",
        hero_name="Mira",
        hero_type="girl",
        helper_name="Besa",
        brag=4,
    ),
    StoryParams(
        realm="sun_steps",
        cause="monkey",
        hanger="shield",
        saber="painted",
        helper="priest",
        hero_name="Aren",
        hero_type="boy",
        helper_name="Yorin",
        brag=7,
    ),
    StoryParams(
        realm="moon_hill",
        cause="monkey",
        hanger="bell",
        saber="wood",
        helper="aunt",
        hero_name="Sela",
        hero_type="girl",
        helper_name="Maro",
        brag=3,
    ),
]


def explain_rejection(cause: Cause, hanger: Hanger) -> str:
    if not hanger.hangs:
        return (
            f"(No story: a rolling zucchini can make a comic strike only if something hanging can ring or clang. "
            f"{hanger.article.capitalize()} {hanger.label} does not hang, so the night noise never becomes myth-sized.)"
        )
    if not cause_can_move(cause):
        return (
            f"(No story: {cause.label} cannot reasonably move the zucchini enough to start the chain of events.)"
        )
    return "(No story: this combination cannot make the loud shrine strike the tale needs.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
can_move(C) :- cause(C), power(C, P), P >= 1.
can_strike(C, H) :- can_move(C), hanger(H), hangs(H), power(C, P), loudness(H, L), P + L >= 2.
valid(R, C, H) :- realm(R), cause(C), hanger(H), can_strike(C, H).

loud_laugh :- brag(B), B >= 5.
gentle_laugh :- brag(B), B < 5.
outcome(loud_laugh) :- loud_laugh.
outcome(gentle_laugh) :- gentle_laugh.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for realm_id in REALMS:
        lines.append(asp.fact("realm", realm_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("power", cause_id, cause.power))
    for hanger_id, hanger in HANGERS.items():
        lines.append(asp.fact("hanger", hanger_id))
        if hanger.hangs:
            lines.append(asp.fact("hangs", hanger_id))
        lines.append(asp.fact("loudness", hanger_id, hanger.loudness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("brag", params.brag)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_for(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_for() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "zucchini" not in sample.story or "saber" not in sample.story:
            raise StoryError("(Smoke test failed: generated story missing required core content.)")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a comic mini-myth of a runaway zucchini, a ringing strike, and a toy saber."
    )
    ap.add_argument("--realm", choices=REALMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hanger", choices=HANGERS)
    ap.add_argument("--saber", choices=SABERS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hero-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--brag", type=int, choices=list(range(0, 8)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (realm, cause, hanger) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.cause and args.hanger:
        cause = CAUSES[args.cause]
        hanger = HANGERS[args.hanger]
        if not can_make_strike(cause, hanger):
            raise StoryError(explain_rejection(cause, hanger))

    combos = [
        combo
        for combo in valid_combos()
        if (args.realm is None or combo[0] == args.realm)
        and (args.cause is None or combo[1] == args.cause)
        and (args.hanger is None or combo[2] == args.hanger)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    realm, cause, hanger = rng.choice(sorted(combos))
    saber = args.saber or rng.choice(sorted(SABERS))
    helper = args.helper or rng.choice(sorted(HELPERS))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name] or HELPER_NAMES)
    brag = args.brag if args.brag is not None else rng.randint(3, 7)
    return StoryParams(
        realm=realm,
        cause=cause,
        hanger=hanger,
        saber=saber,
        helper=helper,
        hero_name=hero_name,
        hero_type=gender,
        helper_name=helper_name,
        brag=brag,
    )


def generate(params: StoryParams) -> StorySample:
    if params.realm not in REALMS:
        raise StoryError(f"(Unknown realm: {params.realm})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.hanger not in HANGERS:
        raise StoryError(f"(Unknown hanger: {params.hanger})")
    if params.saber not in SABERS:
        raise StoryError(f"(Unknown saber: {params.saber})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    cause = CAUSES[params.cause]
    hanger = HANGERS[params.hanger]
    if not can_make_strike(cause, hanger):
        raise StoryError(explain_rejection(cause, hanger))

    seed_world_params = copy.deepcopy(params)
    world = World()
    world.facts["params"] = seed_world_params
    world = tell(
        REALMS[params.realm],
        cause,
        hanger,
        SABERS[params.saber],
        HELPERS[params.helper],
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        helper_name=params.helper_name,
        brag=params.brag,
    )
    world.facts["params"] = seed_world_params
    world.facts["predicted_noise"] = world.facts.get("predicted_noise", 0)
    return StorySample(
        params=params,
        story=world.render().replace("hero", params.hero_name).replace("helper", params.helper_name),
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (realm, cause, hanger) combos:\n")
        for realm, cause, hanger in combos:
            print(f"  {realm:10} {cause:8} {hanger}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            samples.append(generate(params))
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
            header = f"### {p.hero_name}: {p.cause} + {p.hanger} at {p.realm} ({outcome_for(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
