#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py
============================================================================

A standalone story world for a gentle ghost story built around a hollow place,
a frightened disagreement, and a kind solution. The world model tracks a small
set of typed entities with physical meters and emotional memes, then lets those
states drive a complete story: suspense, conflict, a turn, and a final image
that proves what changed.

Premise
-------
At dusk, two children hear an eerie sound coming from a hollow place. One child
wants to run, scold, or block the opening. The other notices that the sound is
not angry but troubled. If the gentle child has enough standing to stop the
mistake, they help at once. Otherwise the frightened child makes the ghost's
trouble worse first, and the story turns on apology and repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py --ghost shawl_ghost
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py --hollow wall_niche --ghost shawl_ghost
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/hollow_suspense_conflict_kindness_ghost_story.py --verify
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
KIND_MIN = 2
COURAGE_INIT = 5.0
BRAVE_KIND_TRAITS = {"steady", "gentle", "kind", "thoughtful"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    weather: str
    dusk_line: str
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
class Hollow:
    id: str
    label: str
    phrase: str
    opening: str
    sound_place: str
    supports: set[str] = field(default_factory=set)
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
class Ghost:
    id: str
    label: str
    need: str
    whisper: str
    reveal: str
    relief: str
    gift: str
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
class Kindness:
    id: str
    sense: int
    aids: set[str]
    offer: str
    action: str
    result: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"gentle", "fearful"}]

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


def _r_eerie_sound(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    hollow = world.get("hollow")
    if ghost.meters["distress"] < THRESHOLD:
        return out
    if hollow.meters["blocked"] >= THRESHOLD:
        return out
    sig = ("eerie", int(ghost.meters["distress"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hollow.meters["echo"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__eerie__")
    return out


def _r_blocked_distress(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    hollow = world.get("hollow")
    if hollow.meters["blocked"] < THRESHOLD:
        return out
    sig = ("blocked", int(hollow.meters["blocked"]))
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["distress"] += 1
    for kid in world.kids():
        kid.memes["guilt"] += 1
    out.append("__blocked__")
    return out


def _r_help_glow(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    if ghost.memes["helped"] < THRESHOLD:
        return out
    sig = ("helped",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.meters["distress"] = 0.0
    ghost.meters["glow"] += 1
    for kid in world.kids():
        kid.memes["fear"] = 0.0
        kid.memes["wonder"] += 1
    out.append("__glow__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="eerie_sound", tag="physical", apply=_r_eerie_sound),
    Rule(name="blocked_distress", tag="physical", apply=_r_blocked_distress),
    Rule(name="help_glow", tag="emotional", apply=_r_help_glow),
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


def need_supported(hollow: Hollow, ghost: Ghost) -> bool:
    return ghost.need in hollow.supports


def sensible_kindnesses() -> list[Kindness]:
    return [k for k in KINDNESS.values() if k.sense >= KIND_MIN]


def select_best_kindness(ghost: Ghost) -> Optional[Kindness]:
    choices = [k for k in sensible_kindnesses() if ghost.need in k.aids]
    if not choices:
        return None
    return max(choices, key=lambda k: k.sense)


def initial_kindness(trait: str) -> float:
    return 5.0 if trait in BRAVE_KIND_TRAITS else 3.0


def would_help_early(relation: str, gentle_age: int, fearful_age: int, trait: str) -> bool:
    older = relation == "siblings" and gentle_age > fearful_age
    authority = initial_kindness(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > COURAGE_INIT


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    ghost = sim.get("ghost")
    ghost.meters["distress"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": sum(k.memes["fear"] for k in sim.kids()),
        "echo": sim.get("hollow").meters["echo"],
    }


def raise_ghost_distress(world: World) -> None:
    ghost = world.get("ghost")
    ghost.meters["distress"] += 1
    propagate(world, narrate=False)


def introduce(world: World, gentle: Entity, fearful: Entity, caretaker: Entity) -> None:
    world.say(
        f"One {world.setting.weather} evening, {gentle.id} and {fearful.id} walked with "
        f"{gentle.pronoun('possessive')} {caretaker.label_word} past {world.setting.place}. "
        f"{world.setting.dusk_line}"
    )


def notice_hollow(world: World, gentle: Entity, fearful: Entity, hollow: Hollow) -> None:
    for kid in (gentle, fearful):
        kid.memes["curiosity"] += 1
    world.say(
        f"Near the path stood {hollow.phrase}. Its {hollow.opening} looked so dark and "
        f"deep that it seemed to be holding its breath."
    )
    world.say(
        f'{fearful.id} slowed down. "Did you hear that?" {fearful.pronoun()} whispered.'
    )


def eerie_sound(world: World, ghost_cfg: Ghost, hollow: Hollow) -> None:
    raise_ghost_distress(world)
    world.say(
        f"From inside the hollow came {ghost_cfg.whisper}, thin and trembling, as if "
        f"the night itself had found a little voice in {hollow.sound_place}."
    )


def warning(world: World, gentle: Entity, fearful: Entity, hollow: Hollow) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_fear"] = pred["fear"]
    fearful.memes["alarm"] += 1
    extra = ""
    if pred["fear"] >= 2:
        extra = " The sound made the shadows feel closer than they really were."
    world.say(
        f'{fearful.id} grabbed {gentle.id}\'s sleeve. "It\'s a ghost," '
        f'{fearful.pronoun()} said. "We should make it stay in that hollow and not come out."'
        f"{extra}"
    )


def argue(world: World, gentle: Entity, fearful: Entity) -> None:
    gentle.memes["empathy"] += 1
    fearful.memes["defiance"] += 1
    world.say(
        f'"Wait," {gentle.id} said softly. "That doesn\'t sound mean. It sounds sad."'
    )


def stop_early(world: World, gentle: Entity, fearful: Entity) -> None:
    gentle.memes["resolve"] += 1
    fearful.memes["trust"] += 1
    sib = ""
    if world.facts.get("relation") == "siblings":
        sib = " big sibling voice"
    world.say(
        f"{gentle.id} stepped in front of the hollow with a calm{sib}. "
        f'"No," {gentle.pronoun()} said. "If someone is frightened in there, we have to be gentle."'
    )


def harmful_move(world: World, fearful: Entity, hollow: Hollow) -> None:
    hollow_ent = world.get("hollow")
    hollow_ent.meters["blocked"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But fear jumped ahead of sense. {fearful.id} snatched a flat piece of bark and "
        f"pressed it over {hollow.opening}, trying to shut the sound inside."
    )
    world.say(
        "At once the whisper turned into a hurt little flutter, and even the leaves seemed to wince."
    )


def reveal_ghost(world: World, gentle: Entity, ghost_cfg: Ghost, hollow: Hollow) -> None:
    ghost = world.get("ghost")
    hollow_ent = world.get("hollow")
    hollow_ent.meters["blocked"] = 0.0
    ghost.meters["seen"] += 1
    world.say(
        f"{gentle.id} pulled the bark away and knelt beside the hollow. In the dim dark "
        f"appeared {ghost_cfg.reveal}"
    )


def kind_act(world: World, gentle: Entity, kindness: Kindness, ghost_cfg: Ghost) -> None:
    ghost = world.get("ghost")
    gentle.memes["kindness"] += 1
    ghost.memes["helped"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{gentle.id} held still for one brave breath, then {kindness.offer}. '
        f"{kindness.action}"
    )
    world.say(
        f"{ghost_cfg.relief} {kindness.result}"
    )


def apology(world: World, fearful: Entity, ghost_cfg: Ghost) -> None:
    fearful.memes["remorse"] += 1
    fearful.memes["kindness"] += 1
    world.say(
        f'"I thought it wanted to scare us," {fearful.id} whispered. '
        f'"I was wrong. I\'m sorry I made {ghost_cfg.label} more afraid."'
    )


def caretaker_line(world: World, caretaker: Entity, ghost_cfg: Ghost) -> None:
    world.say(
        f'{caretaker.label_word.capitalize()} set a warm hand on both children\'s shoulders. '
        f'"The darkest sounds are not always dangerous," {caretaker.pronoun()} said. '
        f'"Sometimes they are only lonely, and kindness lets us hear the difference."'
    )


def ending(world: World, gentle: Entity, fearful: Entity, ghost_cfg: Ghost, hollow: Hollow) -> None:
    ghost = world.get("ghost")
    if ghost.meters["glow"] >= THRESHOLD:
        world.say(
            f"After that, {hollow.phrase} no longer looked hungry or haunted. "
            f"A pearl-soft shine rested in the hollow, and whenever {gentle.id} and "
            f"{fearful.id} passed it at dusk, {ghost_cfg.gift} glimmered there like a tiny, thankful star."
        )


def tell(
    setting: Setting,
    hollow_cfg: Hollow,
    ghost_cfg: Ghost,
    kindness_cfg: Kindness,
    gentle_name: str = "Nora",
    gentle_gender: str = "girl",
    fearful_name: str = "Ben",
    fearful_gender: str = "boy",
    caretaker_type: str = "grandmother",
    gentle_trait: str = "gentle",
    relation: str = "siblings",
    gentle_age: int = 7,
    fearful_age: int = 5,
) -> World:
    world = World(setting)
    gentle = world.add(Entity(
        id=gentle_name,
        kind="character",
        type=gentle_gender,
        role="gentle",
        age=gentle_age,
        traits=[gentle_trait],
        attrs={"relation": relation},
    ))
    fearful = world.add(Entity(
        id=fearful_name,
        kind="character",
        type=fearful_gender,
        role="fearful",
        age=fearful_age,
        traits=["jumpy"],
        attrs={"relation": relation},
    ))
    caretaker = world.add(Entity(
        id="Caretaker",
        kind="character",
        type=caretaker_type,
        role="caretaker",
        label="the caretaker",
    ))
    hollow_ent = world.add(Entity(
        id="hollow",
        kind="thing",
        type="hollow",
        label=hollow_cfg.label,
        attrs={"opening": hollow_cfg.opening},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label=ghost_cfg.label,
        attrs={"need": ghost_cfg.need},
    ))

    world.facts.update(
        setting=setting,
        hollow_cfg=hollow_cfg,
        ghost_cfg=ghost_cfg,
        kindness_cfg=kindness_cfg,
        relation=relation,
    )

    gentle.memes["courage"] = COURAGE_INIT
    gentle.memes["kindness"] = initial_kindness(gentle_trait)
    fearful.memes["fear"] = 0.0
    fearful.memes["trust"] = 4.0
    ghost.meters["distress"] = 0.0
    hollow_ent.meters["blocked"] = 0.0

    introduce(world, gentle, fearful, caretaker)
    notice_hollow(world, gentle, fearful, hollow_cfg)

    world.para()
    eerie_sound(world, ghost_cfg, hollow_cfg)
    warning(world, gentle, fearful, hollow_cfg)
    argue(world, gentle, fearful)

    early = would_help_early(relation, gentle_age, fearful_age, gentle_trait)

    world.para()
    if early:
        stop_early(world, gentle, fearful)
        reveal_ghost(world, gentle, ghost_cfg, hollow_cfg)
        kind_act(world, gentle, kindness_cfg, ghost_cfg)
        outcome = "soothed"
        made_worse = False
    else:
        harmful_move(world, fearful, hollow_cfg)
        reveal_ghost(world, gentle, ghost_cfg, hollow_cfg)
        kind_act(world, gentle, kindness_cfg, ghost_cfg)
        apology(world, fearful, ghost_cfg)
        outcome = "apology"
        made_worse = True

    world.para()
    caretaker_line(world, caretaker, ghost_cfg)
    ending(world, gentle, fearful, ghost_cfg, hollow_cfg)

    world.facts.update(
        gentle=gentle,
        fearful=fearful,
        caretaker=caretaker,
        ghost=ghost,
        hollow=hollow_ent,
        outcome=outcome,
        made_worse=made_worse,
        revealed=ghost.meters["seen"] >= THRESHOLD,
        resolved=ghost.meters["glow"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "orchard": Setting(
        id="orchard",
        place="the old orchard behind the cottage",
        weather="misty",
        dusk_line="Mist slid between the trunks, and the last light lay pale on the grass",
        tags={"night", "orchard"},
    ),
    "churchyard": Setting(
        id="churchyard",
        place="the quiet churchyard path",
        weather="windy",
        dusk_line="The yew branches stirred above the stones, and the sky had gone silver-gray",
        tags={"night", "churchyard"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the ivy-bright courtyard by the gate",
        weather="foggy",
        dusk_line="Fog curled around the paving stones, and every corner looked full of secrets",
        tags={"night", "courtyard"},
    ),
}

HOLLOWS = {
    "oak_tree": Hollow(
        id="oak_tree",
        label="oak tree",
        phrase="a bent old oak with a hollow in its trunk",
        opening="round hollow",
        sound_place="the bark",
        supports={"lost", "cold"},
        tags={"tree", "hollow"},
    ),
    "stump": Hollow(
        id="stump",
        label="stump",
        phrase="a mossy stump with a hollow center",
        opening="dark hollow mouth",
        sound_place="the split wood",
        supports={"lost", "cold"},
        tags={"stump", "hollow"},
    ),
    "wall_niche": Hollow(
        id="wall_niche",
        label="stone wall",
        phrase="an old stone wall with a hollow niche near the gate",
        opening="narrow hollow niche",
        sound_place="the stones",
        supports={"lost", "stuck"},
        tags={"wall", "hollow"},
    ),
}

GHOSTS = {
    "lantern_ghost": Ghost(
        id="lantern_ghost",
        label="the little lantern ghost",
        need="lost",
        whisper="a tiny clink-clink and a soft moan",
        reveal="a small pale ghost with empty hands, peering about as if it had misplaced something dear",
        relief="The ghost's eyes brightened at once.",
        gift="its tiny lantern",
        tags={"ghost", "lost", "lantern"},
    ),
    "shawl_ghost": Ghost(
        id="shawl_ghost",
        label="the shivering ghost",
        need="cold",
        whisper="a whispery oooh that shook like teeth in winter",
        reveal="a small white ghost folded tight into itself, shivering in the draft",
        relief="The ghost stopped trembling and drifted higher, light as milkweed fluff.",
        gift="a neat fold of moon-pale shawl",
        tags={"ghost", "cold", "shawl"},
    ),
    "gate_ghost": Ghost(
        id="gate_ghost",
        label="the gate ghost",
        need="stuck",
        whisper="a faint rattle-rattle and a tired sigh",
        reveal="a little gray ghost caught by a twist of ivy that had snagged its trailing hem",
        relief="The ghost gave one astonished blink, then floated free with a delighted spin.",
        gift="its bright key",
        tags={"ghost", "stuck", "gate"},
    ),
}

KINDNESS = {
    "return_lantern": Kindness(
        id="return_lantern",
        sense=3,
        aids={"lost"},
        offer="held out the tiny lantern lying in the grass beside the roots",
        action="The ghost reached for it carefully, as if kindness might break if touched too fast.",
        result="When the little lantern clicked alight, the shadows drew back instead of creeping closer.",
        qa_text="gave the little ghost back its lantern",
        tags={"lantern", "kindness"},
    ),
    "share_shawl": Kindness(
        id="share_shawl",
        sense=3,
        aids={"cold"},
        offer="slipped off a warm shawl from the basket and lifted it toward the trembling shape",
        action="The cloth did not fall through at all. It settled around the ghost like a soft cloud.",
        result="The chill in the air loosened, and the frightening whisper melted into a grateful hum.",
        qa_text="wrapped the cold ghost in a warm shawl",
        tags={"shawl", "kindness"},
    ),
    "lift_ivy": Kindness(
        id="lift_ivy",
        sense=3,
        aids={"stuck"},
        offer="carefully lifted the ivy twist away from the ghost's trailing hem",
        action="Not one leaf was torn. The child moved slowly, as if untangling moonlight.",
        result="The rattling stopped, and the gate gave a happy little click in the breeze.",
        qa_text="freed the ghost from the ivy that had it stuck",
        tags={"gate", "kindness"},
    ),
    "wave_stick": Kindness(
        id="wave_stick",
        sense=1,
        aids=set(),
        offer="waved a stick at the hollow",
        action="Nothing about that helped the trouble inside.",
        result="The night only felt more worried.",
        qa_text="waved a stick at the hollow",
        tags={"unkind"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Eva", "Clara", "June", "Hazel", "Wren"]
BOY_NAMES = ["Ben", "Max", "Theo", "Finn", "Jude", "Noah", "Eli", "Sam"]
TRAITS = ["gentle", "steady", "kind", "thoughtful", "curious", "quiet"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for hollow_id, hollow in HOLLOWS.items():
            for ghost_id, ghost in GHOSTS.items():
                if not need_supported(hollow, ghost):
                    continue
                for kindness_id, kindness in KINDNESS.items():
                    if kindness.sense < KIND_MIN:
                        continue
                    if ghost.need in kindness.aids:
                        combos.append((setting_id, hollow_id, ghost_id, kindness_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    hollow: str
    ghost: str
    kindness: str
    gentle_name: str
    gentle_gender: str
    fearful_name: str
    fearful_gender: str
    caretaker: str
    trait: str
    relation: str = "siblings"
    gentle_age: int = 7
    fearful_age: int = 5
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
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a story with spooky feelings, strange sounds, and shadows that make you wonder what is there. In gentle ghost stories, the scary thing often turns out to need help instead of hurting anyone."
    )],
    "hollow": [(
        "What does hollow mean?",
        "Hollow means empty inside. A hollow tree or wall has an open space inside it where air, animals, or even a storybook ghost might hide."
    )],
    "lantern": [(
        "What is a lantern?",
        "A lantern is a small light with a cover around it. People carry lanterns so they can see in the dark."
    )],
    "shawl": [(
        "What is a shawl?",
        "A shawl is a soft piece of cloth worn around the shoulders to keep warm. It can feel like a light blanket."
    )],
    "gate": [(
        "What is ivy?",
        "Ivy is a climbing plant with long stems and leaves. It can curl around walls, trees, and gates."
    )],
    "kindness": [(
        "Why can kindness help when someone seems scary?",
        "Kindness helps you slow down and notice what is really wrong. Sometimes a frightened or lonely person only seems scary because they are hurting."
    )],
}
KNOWLEDGE_ORDER = ["ghost", "hollow", "lantern", "shawl", "gate", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    gentle = f["gentle"]
    fearful = f["fearful"]
    hollow_cfg = f["hollow_cfg"]
    ghost_cfg = f["ghost_cfg"]
    return [
        f'Write a short ghost story for a 3-to-5-year-old that includes the word "hollow" and ends kindly.',
        f"Tell a suspenseful story where {gentle.id} and {fearful.id} hear a strange sound in {hollow_cfg.phrase}, argue about what to do, and discover a ghost that needs help.",
        f"Write a gentle spooky story about {ghost_cfg.label}, a frightened disagreement, and a child who chooses kindness instead of fear.",
    ]


def pair_noun(gentle: Entity, fearful: Entity, relation: str) -> str:
    if relation == "siblings":
        if gentle.type == "boy" and fearful.type == "boy":
            return "two brothers"
        if gentle.type == "girl" and fearful.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    gentle = f["gentle"]
    fearful = f["fearful"]
    caretaker = f["caretaker"]
    ghost_cfg = f["ghost_cfg"]
    hollow_cfg = f["hollow_cfg"]
    kindness_cfg = f["kindness_cfg"]
    relation = f["relation"]
    pair = pair_noun(gentle, fearful, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {gentle.id} and {fearful.id}, and {gentle.id}'s {caretaker.label_word}. It is also about {ghost_cfg.label}, hidden in a hollow place."
        ),
        (
            "What made the story feel spooky at first?",
            f"The children were out at dusk, and a strange trembling sound came from {hollow_cfg.phrase}. The dark hollow and the uncertain whisper made them think something dangerous might be hiding there."
        ),
        (
            f"Why did {fearful.id} want to shut the hollow?",
            f"{fearful.id} was frightened and thought the sound meant a ghost wanted to scare them. Fear made {fearful.pronoun()} want to trap the trouble instead of listening closely."
        ),
    ]
    if f["outcome"] == "soothed":
        qa.append((
            f"How did {gentle.id} solve the problem?",
            f"{gentle.id} stopped the frightened idea before anyone made things worse and then {kindness_cfg.qa_text}. That act of kindness showed that the ghost was troubled, not cruel."
        ))
    else:
        qa.append((
            f"What mistake happened before the problem was solved?",
            f"{fearful.id} covered the hollow for a moment because {fearful.pronoun()} was scared, and the ghost sounded more hurt right away. Then {gentle.id} undid that mistake and {kindness_cfg.qa_text}."
        ))
        qa.append((
            f"Why did {fearful.id} apologize?",
            f"{fearful.id} realized the ghost had needed help all along. The apology mattered because {fearful.pronoun()} understood that fear had made the trouble worse."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with the hollow looking peaceful instead of haunted. The children learned that kindness can change a scary night into a gentle one."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "hollow", "kindness"} | set(world.facts["ghost_cfg"].tags) | set(world.facts["kindness_cfg"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="orchard",
        hollow="oak_tree",
        ghost="lantern_ghost",
        kindness="return_lantern",
        gentle_name="Nora",
        gentle_gender="girl",
        fearful_name="Ben",
        fearful_gender="boy",
        caretaker="grandmother",
        trait="gentle",
        relation="siblings",
        gentle_age=7,
        fearful_age=5,
    ),
    StoryParams(
        setting="churchyard",
        hollow="stump",
        ghost="shawl_ghost",
        kindness="share_shawl",
        gentle_name="Theo",
        gentle_gender="boy",
        fearful_name="Mina",
        fearful_gender="girl",
        caretaker="grandfather",
        trait="steady",
        relation="siblings",
        gentle_age=8,
        fearful_age=5,
    ),
    StoryParams(
        setting="courtyard",
        hollow="wall_niche",
        ghost="gate_ghost",
        kindness="lift_ivy",
        gentle_name="Clara",
        gentle_gender="girl",
        fearful_name="Max",
        fearful_gender="boy",
        caretaker="mother",
        trait="curious",
        relation="friends",
        gentle_age=6,
        fearful_age=6,
    ),
    StoryParams(
        setting="orchard",
        hollow="stump",
        ghost="shawl_ghost",
        kindness="share_shawl",
        gentle_name="June",
        gentle_gender="girl",
        fearful_name="Eli",
        fearful_gender="boy",
        caretaker="father",
        trait="kind",
        relation="friends",
        gentle_age=6,
        fearful_age=7,
    ),
]


def explain_rejection(hollow: Hollow, ghost: Ghost, kindness: Optional[Kindness] = None) -> str:
    if not need_supported(hollow, ghost):
        return (
            f"(No story: {hollow.phrase} is not a good match for {ghost.label}. "
            f"This hollow can support needs {sorted(hollow.supports)}, but that ghost needs {ghost.need}.)"
        )
    if kindness is not None:
        if kindness.sense < KIND_MIN:
            return (
                f"(Refusing kindness '{kindness.id}': it scores too low on common sense "
                f"(sense={kindness.sense} < {KIND_MIN}). A kind fix must actually help.)"
            )
        if ghost.need not in kindness.aids:
            return (
                f"(No story: {kindness.id} does not help a ghost whose need is '{ghost.need}'. "
                f"Choose a kindness that truly solves the trouble.)"
            )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    if would_help_early(params.relation, params.gentle_age, params.fearful_age, params.trait):
        return "soothed"
    return "apology"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S,H,G,K) :- setting(S), hollow(H), ghost(G), kindness(K),
                  need(G,N), supports(H,N),
                  sense(K,Sc), kind_min(M), Sc >= M,
                  aids(K,N).

sensible(K) :- kindness(K), sense(K,Sc), kind_min(M), Sc >= M.

% --- outcome model ---------------------------------------------------------
brave_kind(T) :- trait(T), brave_trait(T).
init_kindness(5) :- trait(T), brave_kind(T).
init_kindness(3) :- trait(T), not brave_kind(T).

older_gentle :- relation(siblings), gentle_age(GA), fearful_age(FA), GA > FA.
bonus(3) :- older_gentle.
bonus(0) :- not older_gentle.

authority(K + 1 + B) :- init_kindness(K), bonus(B).
help_early :- older_gentle, authority(A), courage_init(C), A > C.

outcome(soothed) :- help_early.
outcome(apology) :- not help_early.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid, hollow in HOLLOWS.items():
        lines.append(asp.fact("hollow", hid))
        for need in sorted(hollow.supports):
            lines.append(asp.fact("supports", hid, need))
    for gid, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("need", gid, ghost.need))
    for kid, kind in KINDNESS.items():
        lines.append(asp.fact("kindness", kid))
        lines.append(asp.fact("sense", kid, kind.sense))
        for aid in sorted(kind.aids):
            lines.append(asp.fact("aids", kid, aid))
    for trait in sorted(BRAVE_KIND_TRAITS):
        lines.append(asp.fact("brave_trait", trait))
    lines.append(asp.fact("kind_min", KIND_MIN))
    lines.append(asp.fact("courage_init", int(COURAGE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(k for (k,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("relation", params.relation),
        asp.fact("gentle_age", params.gentle_age),
        asp.fact("fearful_age", params.fearful_age),
        asp.fact("trait", params.trait),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("smoke test failed: generated story was empty")
    emit(sample, trace=False, qa=False, header="")


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
    python_sensible = {k.id for k in sensible_kindnesses()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible kindnesses match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible kindnesses: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    for s in range(200):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            params.seed = s
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        print("Smoke test:")
        _smoke_test()
        print("OK: normal generate/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a hollow, a frightened conflict, and a kind ghostly ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hollow", choices=HOLLOWS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--caretaker", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check Python/ASP parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.hollow and args.ghost:
        hollow = HOLLOWS[args.hollow]
        ghost = GHOSTS[args.ghost]
        if not need_supported(hollow, ghost):
            raise StoryError(explain_rejection(hollow, ghost))
    if args.ghost and args.kindness:
        ghost = GHOSTS[args.ghost]
        kindness = KINDNESS[args.kindness]
        if kindness.sense < KIND_MIN or ghost.need not in kindness.aids:
            hollow = HOLLOWS[args.hollow] if args.hollow else next(iter(HOLLOWS.values()))
            raise StoryError(explain_rejection(hollow, ghost, kindness))
    if args.kindness and KINDNESS[args.kindness].sense < KIND_MIN:
        ghost = GHOSTS[args.ghost] if args.ghost else next(iter(GHOSTS.values()))
        hollow = HOLLOWS[args.hollow] if args.hollow else next(iter(HOLLOWS.values()))
        raise StoryError(explain_rejection(hollow, ghost, KINDNESS[args.kindness]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.hollow is None or combo[1] == args.hollow)
        and (args.ghost is None or combo[2] == args.ghost)
        and (args.kindness is None or combo[3] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, hollow_id, ghost_id, kindness_id = rng.choice(sorted(combos))
    gentle_name, gentle_gender = _pick_name(rng)
    fearful_name, fearful_gender = _pick_name(rng, avoid=gentle_name)
    caretaker = args.caretaker or rng.choice(["mother", "father", "grandmother", "grandfather"])
    relation = args.relation or rng.choice(["siblings", "friends"])
    trait = args.trait or rng.choice(TRAITS)
    ages = rng.sample([4, 5, 6, 7, 8], 2)
    return StoryParams(
        setting=setting_id,
        hollow=hollow_id,
        ghost=ghost_id,
        kindness=kindness_id,
        gentle_name=gentle_name,
        gentle_gender=gentle_gender,
        fearful_name=fearful_name,
        fearful_gender=fearful_gender,
        caretaker=caretaker,
        trait=trait,
        relation=relation,
        gentle_age=max(ages),
        fearful_age=min(ages) if relation == "siblings" and rng.random() < 0.5 else ages[1],
    )


def _lookup_or_error(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(Unknown {label}: {key})")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    setting = _lookup_or_error(SETTINGS, params.setting, "setting")
    hollow = _lookup_or_error(HOLLOWS, params.hollow, "hollow")
    ghost = _lookup_or_error(GHOSTS, params.ghost, "ghost")
    kindness = _lookup_or_error(KINDNESS, params.kindness, "kindness")
    if not need_supported(hollow, ghost):
        raise StoryError(explain_rejection(hollow, ghost))
    if kindness.sense < KIND_MIN or ghost.need not in kindness.aids:
        raise StoryError(explain_rejection(hollow, ghost, kindness))

    world = tell(
        setting=setting,
        hollow_cfg=hollow,
        ghost_cfg=ghost,
        kindness_cfg=kindness,
        gentle_name=params.gentle_name,
        gentle_gender=params.gentle_gender,
        fearful_name=params.fearful_name,
        fearful_gender=params.fearful_gender,
        caretaker_type=params.caretaker,
        gentle_trait=params.trait,
        relation=params.relation,
        gentle_age=params.gentle_age,
        fearful_age=params.fearful_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible kindnesses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, hollow, ghost, kindness) combos:\n")
        for setting_id, hollow_id, ghost_id, kindness_id in combos:
            print(f"  {setting_id:10} {hollow_id:10} {ghost_id:14} {kindness_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.gentle_name} & {p.fearful_name}: {p.ghost} in {p.hollow} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
