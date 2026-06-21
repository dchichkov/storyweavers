#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py
====================================================================

A standalone storyworld about a child in a coat and a costume beard who thinks a
friend played a trick, only to discover a twist: the missing beard was snagged on
the coat all along. The child says sorry, the friend chooses to forgive, and the
rhyming ending proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py --json
    python storyworlds/worlds/gpt-5.4/forgive_beard_coat_twist_rhyming_story.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SOFT_TRAITS = {"gentle", "merry", "kind"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
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
class RoleTheme:
    id: str
    title: str
    task: str
    line: str
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
class BeardCfg:
    id: str
    label: str
    phrase: str
    texture: str
    fastener: str
    snags_on: set[str] = field(default_factory=set)
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
class CoatCfg:
    id: str
    label: str
    phrase: str
    color: str
    snag_points: set[str] = field(default_factory=set)
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
class SearchMove:
    id: str
    action: str
    reveal: str
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
class StoryParams:
    setting: str
    role: str
    beard: str
    coat: str
    search: str
    wearer_name: str
    wearer_gender: str
    helper_name: str
    helper_gender: str
    relation: str
    helper_trait: str
    grownup: str
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


def _r_false_blame_hurts(world: World) -> list[str]:
    out: list[str] = []
    wearer = world.get("wearer")
    helper = world.get("helper")
    beard = world.get("beard")
    if beard.meters["missing"] < THRESHOLD:
        return out
    if wearer.memes["blame"] < THRESHOLD:
        return out
    if beard.attrs.get("where") != "coat":
        return out
    sig = ("false_blame_hurts", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["hurt"] += 1
    wearer.memes["worry"] += 1
    out.append("__hurt__")
    return out


def _r_found_brings_relief(world: World) -> list[str]:
    out: list[str] = []
    beard = world.get("beard")
    wearer = world.get("wearer")
    helper = world.get("helper")
    if beard.meters["found"] < THRESHOLD:
        return out
    sig = ("found_relief", beard.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    wearer.memes["relief"] += 1
    helper.memes["relief"] += 1
    wearer.memes["surprise"] += 1
    out.append("__relief__")
    return out


def _r_apology_opens_forgiveness(world: World) -> list[str]:
    out: list[str] = []
    wearer = world.get("wearer")
    helper = world.get("helper")
    if wearer.memes["apology"] < THRESHOLD or helper.memes["hurt"] < THRESHOLD:
        return out
    sig = ("forgive", helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bonus = 1.0 if helper.attrs.get("forgive_mode") == "easy" else 0.5
    helper.memes["forgive"] += bonus
    helper.memes["warmth"] += 1
    wearer.memes["gratitude"] += 1
    out.append("__forgive__")
    return out


CAUSAL_RULES = [
    Rule(name="false_blame_hurts", tag="social", apply=_r_false_blame_hurts),
    Rule(name="found_relief", tag="social", apply=_r_found_brings_relief),
    Rule(name="apology_opens_forgiveness", tag="social", apply=_r_apology_opens_forgiveness),
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
    "schoolyard": Setting(
        id="schoolyard",
        place="the schoolyard gate",
        opening="After school, the flag rope hummed in the breeze.",
        closing="the gate clicked shut behind them while the evening sky glowed pink",
        tags={"school"},
    ),
    "market": Setting(
        id="market",
        place="the little market lane",
        opening="Paper pennants bobbed over the cobbles like bright fish in a stream.",
        closing="the stalls shone warm as lanterns and the cobbles softly gleamed",
        tags={"market"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        opening="A brass bell by the door made a tiny, tinny ring.",
        closing="the porch light made a gold square on the step",
        tags={"home"},
    ),
}

ROLES = {
    "winter_king": RoleTheme(
        id="winter_king",
        title="Winter King",
        task="recite a chilly rhyme for the evening line",
        line='“Snow in a sweep, snow in a ring, make way, make way for the Winter King!”',
        tags={"rhyme", "parade"},
    ),
    "moss_wizard": RoleTheme(
        id="moss_wizard",
        title="Moss Wizard",
        task="chant a green and giggly spell",
        line='“Twig and stone, leaf and lizard, tap your toes for the Moss Wizard!”',
        tags={"rhyme", "parade"},
    ),
    "harbor_poet": RoleTheme(
        id="harbor_poet",
        title="Harbor Poet",
        task="sing a salty verse for the crowd",
        line='“Boat and float, foam and tide, let a harbor song go skipping wide!”',
        tags={"rhyme", "parade"},
    ),
}

BEARDS = {
    "wool_curl": BeardCfg(
        id="wool_curl",
        label="beard",
        phrase="a curly wool beard",
        texture="curly as a sleepy lamb",
        fastener="a looped string",
        snags_on={"toggle", "button"},
        tags={"beard", "costume"},
    ),
    "braided_beard": BeardCfg(
        id="braided_beard",
        label="beard",
        phrase="a braided yarn beard",
        texture="soft and swishy",
        fastener="two little ties",
        snags_on={"button", "zipper"},
        tags={"beard", "costume"},
    ),
    "tinsel_beard": BeardCfg(
        id="tinsel_beard",
        label="beard",
        phrase="a silver tinsel beard",
        texture="light as winter fluff",
        fastener="a shiny ribbon",
        snags_on={"velcro", "toggle"},
        tags={"beard", "costume"},
    ),
}

COATS = {
    "duffel": CoatCfg(
        id="duffel",
        label="coat",
        phrase="a red duffel coat",
        color="red",
        snag_points={"toggle", "button"},
        tags={"coat", "winter"},
    ),
    "pea": CoatCfg(
        id="pea",
        label="coat",
        phrase="a blue pea coat",
        color="blue",
        snag_points={"button"},
        tags={"coat", "winter"},
    ),
    "puffer": CoatCfg(
        id="puffer",
        label="coat",
        phrase="a green puffer coat",
        color="green",
        snag_points={"zipper", "velcro"},
        tags={"coat", "winter"},
    ),
    "slick_rain": CoatCfg(
        id="slick_rain",
        label="coat",
        phrase="a slick yellow rain coat",
        color="yellow",
        snag_points=set(),
        tags={"coat", "smooth"},
    ),
}

SEARCHES = {
    "straighten_collar": SearchMove(
        id="straighten_collar",
        action="smoothed the collar and tugged the coat straight",
        reveal="there, by the neck, the lost beard gave a tiny bounce",
        tags={"search", "coat"},
    ),
    "lift_hood": SearchMove(
        id="lift_hood",
        action="lifted the hood and shook the coat once",
        reveal="there, under the hood seam, the beard dangled like a fuzzy moon",
        tags={"search", "coat"},
    ),
    "pat_toggle": SearchMove(
        id="pat_toggle",
        action="patted the toggles one by one",
        reveal="on the top toggle the beard was hooked and swinging",
        tags={"search", "coat"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Poppy", "Nora", "Tessa", "Ruby", "Etta", "Maisie"]
BOY_NAMES = ["Theo", "Milo", "Owen", "Jasper", "Finn", "Rowan", "Benji", "Arlo"]
HELPER_TRAITS = ["gentle", "merry", "careful", "patient", "kind", "steady"]


def snaggable(beard: BeardCfg, coat: CoatCfg) -> bool:
    return bool(set(beard.snags_on) & set(coat.snag_points))


def forgiving_mode(relation: str, helper_trait: str) -> str:
    if relation == "siblings" or helper_trait in SOFT_TRAITS:
        return "easy"
    return "after_apology"


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id in SETTINGS:
        for role_id in ROLES:
            for beard_id, beard in BEARDS.items():
                for coat_id, coat in COATS.items():
                    if not snaggable(beard, coat):
                        continue
                    for search_id in SEARCHES:
                        combos.append((setting_id, role_id, beard_id, coat_id, search_id))
    return combos


def predict_false_blame(world: World) -> dict:
    sim = world.copy()
    wearer = sim.get("wearer")
    beard = sim.get("beard")
    beard.meters["missing"] = 1
    beard.attrs["where"] = "coat"
    wearer.memes["blame"] = 1
    propagate(sim, narrate=False)
    helper = sim.get("helper")
    return {
        "helper_hurt": helper.memes["hurt"] >= THRESHOLD,
        "worry": wearer.memes["worry"],
    }


def introduce(world: World, wearer: Entity, helper: Entity, grownup: Entity,
              role: RoleTheme, beard: BeardCfg, coat: CoatCfg) -> None:
    wearer.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{SETTINGS[world.setting.id].opening} {wearer.id} wore {coat.phrase}, and "
        f"{helper.id} helped tie on {beard.phrase} for the {role.title} part."
    )
    world.say(
        f"They were hurrying to {role.task}, and the words already wanted to sing. "
        f'{wearer.id} whispered, {role.line}'
    )
    world.facts["grownup_word"] = grownup.label_word


def gust_and_snag(world: World, wearer: Entity, helper: Entity, beard_cfg: BeardCfg, coat_cfg: CoatCfg) -> None:
    beard = world.get("beard")
    beard.meters["slipped"] = 1
    beard.meters["missing"] = 1
    beard.attrs["where"] = "coat"
    beard.attrs["snag_point"] = sorted(set(beard_cfg.snags_on) & set(coat_cfg.snag_points))[0]
    wearer.memes["alarm"] += 1
    world.say(
        f"Then a frisking gust came skimming past. It flipped the {coat_cfg.label}, "
        f"twitched the {beard_cfg.fastener}, and the beard slipped out of sight very fast."
    )
    world.say(
        f"{wearer.id} touched {wearer.pronoun('possessive')} chin and gasped, "
        f'"My beard! It was here, and now it is not!"'
    )
    world.facts["beard_missing"] = True
    world.facts["helper_helped_tie"] = helper.id


def accuse(world: World, wearer: Entity, helper: Entity) -> None:
    pred = predict_false_blame(world)
    wearer.memes["blame"] = 1
    propagate(world, narrate=False)
    extra = ""
    if pred["helper_hurt"]:
        extra = f" {helper.id}'s smile went small at once."
    world.say(
        f'{wearer.id} turned too quickly and said, "{helper.id}, did you tuck it away as a joke?"{extra}'
    )
    world.say(
        f'"I did not," said {helper.id}. "{wearer.id}, I only tied it neat."'
    )


def hurt_beat(world: World, wearer: Entity, helper: Entity) -> None:
    if helper.memes["hurt"] >= THRESHOLD:
        world.say(
            f"The air felt tight and thin. {helper.id} looked down at the paving stones, "
            f"and even the little rhyme in the wind seemed to lose its tune."
        )


def search_for_beard(world: World, wearer: Entity, helper: Entity, search: SearchMove) -> None:
    helper.memes["care"] += 1
    world.say(
        f"Still, {helper.id} stayed close instead of stomping away. "
        f"{helper.pronoun().capitalize()} {search.action}."
    )


def reveal_twist(world: World, wearer: Entity, helper: Entity, beard_cfg: BeardCfg, coat_cfg: CoatCfg,
                 search: SearchMove) -> None:
    beard = world.get("beard")
    beard.meters["found"] = 1
    beard.meters["missing"] = 0
    beard.attrs["where"] = "found_on_coat"
    propagate(world, narrate=False)
    world.say(
        f"And there was the twist: {search.reveal}. The missing beard had been "
        f"caught on {wearer.id}'s own {coat_cfg.label} all along."
    )
    world.say(
        f"{wearer.id} blinked at the {beard_cfg.texture} beard and felt the hot red pop of a mistake."
    )


def apologize(world: World, wearer: Entity, helper: Entity) -> None:
    wearer.memes["apology"] = 1
    propagate(world, narrate=False)
    world.say(
        f'"Oh, {helper.id}," said {wearer.id}, soft and slow, "I blamed you before I knew. '
        f'I am sorry. Will you forgive me for that hasty guess?"'
    )


def forgive_scene(world: World, wearer: Entity, helper: Entity, role: RoleTheme) -> None:
    mode = helper.attrs.get("forgive_mode", "after_apology")
    if mode == "easy":
        world.say(
            f'{helper.id} gave a small nod. "Yes," {helper.pronoun()} said. '
            f'"I was hurt, but I can forgive you. Next time, let us look before we blame."'
        )
    else:
        world.say(
            f"{helper.id} took one breath, then another, until the hurt settled down. "
            f'"Yes," {helper.pronoun()} said at last. "I forgive you. Thank you for telling the truth and saying sorry."'
        )
    world.say(
        f"They fixed the beard, buttoned the coat, and tried the rhyme again. "
        f"This time their voices skipped together instead of apart."
    )
    world.facts["closing_line"] = role.line


def ending(world: World, wearer: Entity, helper: Entity, role: RoleTheme) -> None:
    world.say(
        f"Soon they stepped on toward {world.setting.place}, beard in place and coat snug tight, "
        f"while {SETTINGS[world.setting.id].closing}."
    )
    world.say(
        f'{wearer.id} sang first, {helper.id} sang next, and the words rang clear and bright: '
        f'{role.line} A quick sharp guess had bent the day, but forgive set it right.'
    )


def tell(setting: Setting, role: RoleTheme, beard_cfg: BeardCfg, coat_cfg: CoatCfg, search: SearchMove,
         wearer_name: str = "Lila", wearer_gender: str = "girl",
         helper_name: str = "Theo", helper_gender: str = "boy",
         relation: str = "friends", helper_trait: str = "gentle",
         grownup_type: str = "mother") -> World:
    world = World(setting)
    wearer = world.add(Entity(
        id="wearer",
        kind="character",
        type=wearer_gender,
        label=wearer_name,
        phrase=wearer_name,
        role="wearer",
        traits=["eager"],
        attrs={"relation": relation},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        phrase=helper_name,
        role="helper",
        traits=[helper_trait],
        attrs={"relation": relation, "forgive_mode": forgiving_mode(relation, helper_trait)},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="the grown-up",
        phrase="the grown-up",
        role="grownup",
        attrs={},
    ))
    beard = world.add(Entity(
        id="beard",
        kind="thing",
        type="costume",
        label="beard",
        phrase=beard_cfg.phrase,
        attrs={"where": "chin", "snag_point": ""},
    ))
    coat = world.add(Entity(
        id="coat",
        kind="thing",
        type="clothing",
        label="coat",
        phrase=coat_cfg.phrase,
        attrs={"worn_by": "wearer"},
    ))

    for ent in (wearer, helper, grownup, beard, coat):
        ent.meters["dummy"] += 0
        ent.memes["dummy"] += 0

    world.facts.update(
        wearer=wearer,
        helper=helper,
        grownup=grownup,
        beard_cfg=beard_cfg,
        coat_cfg=coat_cfg,
        role=role,
        search=search,
        relation=relation,
        helper_trait=helper_trait,
        forgive_mode=helper.attrs["forgive_mode"],
        setting=setting,
    )

    introduce(world, wearer, helper, grownup, role, beard_cfg, coat_cfg)
    world.para()
    gust_and_snag(world, wearer, helper, beard_cfg, coat_cfg)
    accuse(world, wearer, helper)
    hurt_beat(world, wearer, helper)
    world.para()
    search_for_beard(world, wearer, helper, search)
    reveal_twist(world, wearer, helper, beard_cfg, coat_cfg, search)
    apologize(world, wearer, helper)
    forgive_scene(world, wearer, helper, role)
    world.para()
    ending(world, wearer, helper, role)

    world.facts.update(
        beard_found=world.get("beard").meters["found"] >= THRESHOLD,
        helper_hurt=world.get("helper").memes["hurt"] >= THRESHOLD,
        forgiven=world.get("helper").memes["forgive"] >= 0.5,
        apology=world.get("wearer").memes["apology"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "beard": [
        (
            "What is a costume beard?",
            "A costume beard is a pretend beard made from soft materials like yarn or wool. People wear one for dress-up or a play."
        )
    ],
    "coat": [
        (
            "What does a coat do?",
            "A coat helps keep your body warm when the air is cold or windy. Some coats also have buttons, toggles, or zippers on the front."
        )
    ],
    "toggle": [
        (
            "What is a toggle on a coat?",
            "A toggle is a little fastener on some coats. A loop can catch on it if something soft or stringy swings nearby."
        )
    ],
    "zipper": [
        (
            "What is a zipper?",
            "A zipper is a row of tiny teeth that close together when you pull the tab. Loose ribbons or yarn can sometimes catch in it."
        )
    ],
    "forgive": [
        (
            "What does forgive mean?",
            "To forgive means choosing not to stay angry after someone is sorry for a mistake. It does not make the mistake good, but it helps people mend the hurt."
        )
    ],
    "apology": [
        (
            "Why does an apology help?",
            "An apology helps because it shows that you know you caused hurt and want to make things better. Honest sorry words can open the door to trust again."
        )
    ],
}

KNOWLEDGE_ORDER = ["beard", "coat", "toggle", "zipper", "apology", "forgive"]


def generation_prompts(world: World) -> list[str]:
    wearer = world.facts["wearer"]
    helper = world.facts["helper"]
    role = world.facts["role"]
    coat_cfg = world.facts["coat_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that uses the words "forgive", "beard", and "coat", and includes a gentle twist.',
        f"Tell a short rhyming tale where {wearer.label} loses a costume beard, blames {helper.label}, and then discovers the beard was caught on a {coat_cfg.label} all along.",
        f"Write a child-friendly poem-story about a {role.title.lower()} costume, a mistaken guess, an apology, and a warm ending where friends forgive each other.",
    ]


def pair_noun(relation: str) -> str:
    return "two siblings" if relation == "siblings" else "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    wearer = world.facts["wearer"]
    helper = world.facts["helper"]
    role = world.facts["role"]
    beard_cfg = world.facts["beard_cfg"]
    coat_cfg = world.facts["coat_cfg"]
    search = world.facts["search"]
    relation = world.facts["relation"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(relation)}, {wearer.label} and {helper.label}. They were on the way to perform as the {role.title}."
        ),
        (
            f"Why was {wearer.label} wearing a beard and a coat?",
            f"{wearer.label} was dressed for a costume part and wore {beard_cfg.phrase} with {coat_cfg.phrase}. The beard fit the dress-up role, and the coat kept the child warm on the way."
        ),
        (
            f"Why did {helper.label}'s feelings get hurt?",
            f"{helper.label}'s feelings got hurt because {wearer.label} blamed {helper.label} before knowing what really happened. The helper had been trying to help, so the quick accusation felt unfair."
        ),
        (
            "What was the twist in the story?",
            f"The beard was not stolen or hidden at all. It had snagged on the coat, and {helper.label} found it when {helper.pronoun()} {search.action}."
        ),
        (
            f"Why did {wearer.label} ask to be forgiven?",
            f"{wearer.label} asked to be forgiven because the blame was a mistake. After seeing the beard caught on the coat, {wearer.pronoun()} understood that the hurt came from speaking too fast."
        ),
        (
            "How did the story end?",
            f"It ended with an apology, forgiveness, and the costume fixed again. They walked on together with the beard in place, and the ending image shows the friendship mended as clearly as the coat buttoned snug."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"beard", "coat", "apology", "forgive"}
    coat_cfg = world.facts["coat_cfg"]
    if "toggle" in coat_cfg.snag_points:
        tags.add("toggle")
    if "zipper" in coat_cfg.snag_points:
        tags.add("zipper")
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
            shown = {k: v for k, v in ent.attrs.items() if v not in ("", None)}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="schoolyard",
        role="winter_king",
        beard="wool_curl",
        coat="duffel",
        search="pat_toggle",
        wearer_name="Lila",
        wearer_gender="girl",
        helper_name="Theo",
        helper_gender="boy",
        relation="friends",
        helper_trait="gentle",
        grownup="mother",
    ),
    StoryParams(
        setting="market",
        role="moss_wizard",
        beard="braided_beard",
        coat="pea",
        search="straighten_collar",
        wearer_name="Milo",
        wearer_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        relation="siblings",
        helper_trait="steady",
        grownup="father",
    ),
    StoryParams(
        setting="porch",
        role="harbor_poet",
        beard="tinsel_beard",
        coat="puffer",
        search="lift_hood",
        wearer_name="Poppy",
        wearer_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        relation="friends",
        helper_trait="patient",
        grownup="teacher",
    ),
]


def explain_rejection(beard_cfg: BeardCfg, coat_cfg: CoatCfg) -> str:
    if not coat_cfg.snag_points:
        return (
            f"(No story: {coat_cfg.phrase} is too smooth for a believable beard twist. "
            f"A snagged beard needs a coat with something catchable, like a toggle, button, or zipper.)"
        )
    return (
        f"(No story: {beard_cfg.phrase} does not plausibly snag on {coat_cfg.phrase}. "
        f"Pick a beard and coat whose ties and fasteners can catch.)"
    )


def outcome_of(params: StoryParams) -> str:
    return forgiving_mode(params.relation, params.helper_trait)


ASP_RULES = r"""
possible_snag(B,C) :- beard(B), coat(C), beard_hook(B,T), coat_point(C,T).
valid(S,R,B,C,Se) :- setting(S), role(R), search(Se), possible_snag(B,C).

easy_forgive :- relation(siblings).
easy_forgive :- helper_trait(T), soft_trait(T).
outcome(easy) :- easy_forgive.
outcome(after_apology) :- not easy_forgive.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    for bid, beard in BEARDS.items():
        lines.append(asp.fact("beard", bid))
        for hook in sorted(beard.snags_on):
            lines.append(asp.fact("beard_hook", bid, hook))
    for cid, coat in COATS.items():
        lines.append(asp.fact("coat", cid))
        for point in sorted(coat.snag_points):
            lines.append(asp.fact("coat_point", cid, point))
    for sid in SEARCHES:
        lines.append(asp.fact("search", sid))
    for trait in sorted(SOFT_TRAITS):
        lines.append(asp.fact("soft_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("helper_trait", params.helper_trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming storyworld: a beard goes missing, a coat hides the twist, and forgiveness mends the day."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--beard", choices=BEARDS)
    ap.add_argument("--coat", choices=COATS)
    ap.add_argument("--search", choices=SEARCHES)
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("--grownup", choices=["mother", "father", "teacher"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [n for n in pool if n != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.beard and args.coat:
        beard_cfg = BEARDS[args.beard]
        coat_cfg = COATS[args.coat]
        if not snaggable(beard_cfg, coat_cfg):
            raise StoryError(explain_rejection(beard_cfg, coat_cfg))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.role is None or c[1] == args.role)
        and (args.beard is None or c[2] == args.beard)
        and (args.coat is None or c[3] == args.coat)
        and (args.search is None or c[4] == args.search)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, role_id, beard_id, coat_id, search_id = rng.choice(sorted(combos))
    wearer_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    wearer_name = _pick_name(rng, wearer_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=wearer_name)
    relation = args.relation or rng.choice(["friends", "siblings"])
    helper_trait = rng.choice(HELPER_TRAITS)
    grownup = args.grownup or rng.choice(["mother", "father", "teacher"])
    return StoryParams(
        setting=setting_id,
        role=role_id,
        beard=beard_id,
        coat=coat_id,
        search=search_id,
        wearer_name=wearer_name,
        wearer_gender=wearer_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        relation=relation,
        helper_trait=helper_trait,
        grownup=grownup,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.role not in ROLES:
        raise StoryError(f"(Unknown role: {params.role})")
    if params.beard not in BEARDS:
        raise StoryError(f"(Unknown beard: {params.beard})")
    if params.coat not in COATS:
        raise StoryError(f"(Unknown coat: {params.coat})")
    if params.search not in SEARCHES:
        raise StoryError(f"(Unknown search move: {params.search})")
    if params.relation not in {"friends", "siblings"}:
        raise StoryError(f"(Unknown relation: {params.relation})")
    if params.grownup not in {"mother", "father", "teacher"}:
        raise StoryError(f"(Unknown grown-up: {params.grownup})")

    beard_cfg = BEARDS[params.beard]
    coat_cfg = COATS[params.coat]
    if not snaggable(beard_cfg, coat_cfg):
        raise StoryError(explain_rejection(beard_cfg, coat_cfg))

    world = tell(
        setting=SETTINGS[params.setting],
        role=ROLES[params.role],
        beard_cfg=beard_cfg,
        coat_cfg=coat_cfg,
        search=SEARCHES[params.search],
        wearer_name=params.wearer_name,
        wearer_gender=params.wearer_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        relation=params.relation,
        helper_trait=params.helper_trait,
        grownup_type=params.grownup,
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
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during verify for seed {s}.")
            break

    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: forgiveness outcome matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} forgiveness outcomes differ.")

    smoke_cases = [CURATED[0]]
    try:
        smoke_cases.append(resolve_params(parser.parse_args([]), random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"ERROR: default resolve_params smoke test failed: {err}")

    for i, p in enumerate(smoke_cases, 1):
        try:
            sample = generate(p)
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                emit(sample, trace=False, qa=False)
            finally:
                sys.stdout = old
            if not sample.story.strip():
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"ERROR: smoke generation {i} failed: {err}")
        else:
            print(f"OK: smoke generation {i} succeeded.")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, role, beard, coat, search) combos:\n")
        for setting_id, role_id, beard_id, coat_id, search_id in combos:
            print(f"  {setting_id:10} {role_id:12} {beard_id:13} {coat_id:10} {search_id}")
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
            header = f"### {p.wearer_name} and {p.helper_name}: {p.beard} on {p.coat} ({p.role})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
