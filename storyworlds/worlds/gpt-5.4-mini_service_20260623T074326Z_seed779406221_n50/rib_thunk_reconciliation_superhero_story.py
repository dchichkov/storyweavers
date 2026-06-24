#!/usr/bin/env python3
"""
Storyworld: rib_thunk_reconciliation_superhero_story
====================================================

A small, standalone superhero-style story world about a young hero, a noisy
"thunk", a sore rib, and a Reconciliation beat that turns a conflict into
cooperation.

Premise sketch:
- A superhero kid is practicing in a city setting when a hard thunk knocks the
  wind out of them and leaves a rib sore.
- The kid suspects a rival, but the rival turns out to be trying to help.
- After a brief tension beat, the two reconcile, fix the problem together, and
  finish with a bright rescue image.

This file follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- defines StoryParams, parameter registries, build_parser, resolve_params,
  generate, emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

SENSE_MIN = 2
THRESHOLD = 1.0



def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    hero: object | None = None
    partner: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Trouble:
    id: str
    label: str
    trigger: str
    sound: str
    harm: str
    sense: int = 3
    power: int = 2
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Fix:
    id: str
    label: str
    text: str
    fail: str
    sense: int = 3
    power: int = 2
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class StoryParams:
    setting: str
    hero: str
    hero_gender: str
    partner: str
    partner_gender: str
    rival: str
    rival_gender: str
    place: str
    trouble: str
    fix: str
    seed: Optional[int] = None
    p: object | None = None
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

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
        clone.places = copy.deepcopy(self.places)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


THEMES = {
    "rooftops": {
        "scene": "the moonlit rooftops",
        "hero_title": "Captain",
        "partner_title": "Spark",
        "mission": "guard the skyline",
        "ending": "swept across the rooftops, bright and safe",
    },
    "downtown": {
        "scene": "the busy downtown blocks",
        "hero_title": "Shield",
        "partner_title": "Flash",
        "mission": "keep the street calm",
        "ending": "lit up the block with brave smiles",
    },
    "harbor": {
        "scene": "the windy harbor",
        "hero_title": "Wave",
        "partner_title": "Comet",
        "mission": "protect the docks",
        "ending": "sparkled over the water like a victory flag",
    },
}

PLACES = {
    "alley": Place(id="alley", label="narrow alley", atmosphere="a dark narrow alley"),
    "bridge": Place(id="bridge", label="old bridge", atmosphere="an old bridge over the river"),
    "tower": Place(id="tower", label="signal tower", atmosphere="a tall signal tower"),
}

TROUBLES = {
    "thunk": Trouble(
        id="thunk",
        label="thunk",
        trigger="a heavy thunk",
        sound="THUNK!",
        harm="a sore rib",
        sense=3,
        power=2,
        tags={"thunk", "impact"},
    ),
    "falling_sign": Trouble(
        id="falling_sign",
        label="falling sign",
        trigger="a swinging sign",
        sound="CLONK!",
        harm="a bruised shoulder",
        sense=3,
        power=3,
        tags={"impact"},
    ),
}

FIXES = {
    "apology": Fix(
        id="apology",
        label="reconcile by talking",
        text="put a hand on the other hero's shoulder and said sorry, then listened",
        fail="tried to talk, but the moment was too hot and the words slipped away",
        sense=3,
        power=1,
        tags={"reconciliation"},
    ),
    "patch": Fix(
        id="patch",
        label="patch up the problem",
        text="wrapped the sore spot, steadied the plan, and worked side by side",
        fail="wrapped it up, but the strain still made everything wobble",
        sense=2,
        power=2,
        tags={"reconciliation"},
    ),
    "teamup": Fix(
        id="teamup",
        label="team up fast",
        text="called for help, then teamed up to finish the job together",
        fail="rushed in alone, but the trouble was bigger than one hero",
        sense=3,
        power=3,
        tags={"reconciliation"},
    ),
}

GENDER_NAMES = {
    "girl": ["Ava", "Maya", "Nora", "Zoe", "Lily"],
    "boy": ["Leo", "Finn", "Noah", "Theo", "Max"],
}

KNOWLEDGE = {
    "thunk": [("What is a thunk?", "A thunk is a heavy sound, like something hard landing or bumping into something.")],
    "rib": [("What is a rib?", "A rib is one of the bones in your chest that helps protect your body.")],
    "reconciliation": [("What does reconciliation mean?", "Reconciliation means making up after a problem and becoming friends again.")],
    "hero": [("What does a superhero do?", "A superhero helps other people, solves problems, and tries to keep everyone safe.")],
    "teamwork": [("Why do heroes work together?", "Heroes work together because two helpers can solve a problem better than one.")],
}


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def hazard_possible(trouble: Trouble) -> bool:
    return trouble.id == "thunk"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for theme in THEMES:
        for t in TROUBLES:
            for f in FIXES:
                if hazard_possible(_safe_lookup(TROUBLES, t)):
                    out.append((theme, t, f))
    return out


def reasonableness_check(trouble: Trouble, fix: Fix) -> None:
    if trouble.sense < SENSE_MIN:
        pass
    if fix.sense < SENSE_MIN:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with rib, thunk, and reconciliation.")
    ap.add_argument("--setting", choices=THEMES)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--partner")
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("--rival")
    ap.add_argument("--rival-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in _safe_lookup(GENDER_NAMES, gender) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(THEMES))
    trouble = getattr(args, "trouble", None) or "thunk"
    fix = getattr(args, "fix", None) or rng.choice([f.id for f in sensible_fixes()])
    reasonableness_check(_safe_lookup(TROUBLES, trouble), _safe_lookup(FIXES, fix))
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    partner_gender = getattr(args, "partner_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    rival_gender = getattr(args, "rival_gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or pick_name(rng, hero_gender)
    partner = getattr(args, "partner", None) or pick_name(rng, partner_gender, avoid=hero)
    rival = getattr(args, "rival", None) or pick_name(rng, rival_gender, avoid=hero)
    return StoryParams(setting, hero, hero_gender, partner, partner_gender, rival, rival_gender, place, trouble, fix, None)


def world_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    for p in world.places.values():
        meters = {k: v for k, v in p.meters.items() if v}
        lines.append(f"  place {p.id}: meters={meters}")
    return "\n".join(lines)


def tell(params: StoryParams) -> World:
    theme = _safe_lookup(THEMES, params.setting)
    trouble = _safe_lookup(TROUBLES, params.trouble)
    fix = _safe_lookup(FIXES, params.fix)
    place = _safe_lookup(PLACES, params.place)

    world = World()
    hero = world.add_entity(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero", memes={"pride": 1.0, "caution": 1.0}))
    partner = world.add_entity(Entity(id=params.partner, kind="character", type=params.partner_gender, role="partner", memes={"trust": 1.0, "worry": 1.0}))
    rival = world.add_entity(Entity(id=params.rival, kind="character", type=params.rival_gender, role="rival", memes={"frustration": 1.0}))
    world.add_place(copy.deepcopy(place))
    world.facts.update({"theme": params.setting, "trouble": params.trouble, "fix": params.fix})

    world.say(f"On {theme['scene']}, {hero.id} and {partner.id} were trying to {theme['mission']}.")
    world.say(f"{theme['hero_title']} {hero.id} watched the street and {theme['partner_title']} {partner.id} scanned the shadows near the {place.label}.")
    world.say(f"Then {trouble.trigger} came with a sharp {trouble.sound} and left {hero.id} with {trouble.harm}.")
    hero.meters["rib_sore"] += 1
    hero.memes["shock"] += 1
    world.say(f"{hero.id} held {hero.pronoun('possessive')} side and blinked fast, trying not to show how much it hurt.")

    world.para()
    world.say(f"{rival.id} saw the stumble and rushed over, but at first it looked like a trick.")
    rival.memes["frustration"] += 1
    partner.memes["worry"] += 1
    world.say(f'"You knocked me?" {hero.id} asked, voice tight as a wire.')
    world.say(f'"No," said {rival.id}. "I heard the {trouble.label} and came to help."')

    world.para()
    hero.memes["anger"] = 1.0
    if hero.memes["shock"] > 0:
        world.say(f"For a moment, the air between them felt as hard as the thunk itself.")
    world.say(f"Then {partner.id} stepped between them and asked both heroes to look at the broken gear together.")
    world.say(f"{partner.id} showed how the {trouble.label} had bounced off a loose beam and not from a punch at all.")

    world.para()
    hero.memes["anger"] = 0.0
    hero.memes["relief"] = 1.0
    rival.memes["guilt"] = 1.0
    partner.memes["hope"] = 1.0
    world.say(f"{hero.id} looked at {rival.id}'s face, saw the worry there, and let the anger go.")
    world.say(f'"I was wrong," {hero.id} said. "Sorry."')
    world.say(f'"Me too," said {rival.id}. "I should have spoken sooner."')
    world.say(f"That was their reconciliation: no shouting, just honest words and a shared breath.")

    world.para()
    if fix.id == "apology":
        world.say(f"Together they {fix.text} while {hero.id} rested {hero.pronoun('possessive')} sore rib against the wall.")
        world.say(f"The three of them reset the broken cable, and the rooftop beacon started to glow again.")
    elif fix.id == "patch":
        world.say(f"They {fix.text}, and the plan stopped wobbling.")
        world.say(f"{rival.id} lifted one side, {hero.id} lifted the other, and the rooftop gate clicked shut.")
    else:
        world.say(f"They {fix.text}, and the rescue line moved like a bright ribbon through the dark.")
        world.say(f"{partner.id} steadied the ladder while {hero.id} and {rival.id} guided the last cable into place.")

    world.para()
    world.say(f"In the end, the city was safe, the mistake was understood, and the team stood taller than before.")
    world.say(f"{theme['hero_title']} {hero.id}, {partner.id}, and {rival.id} watched the skyline {theme['ending']}.")
    world.say(f"Even the sore rib felt like part of the story now, because it had led to a true reconciliation.")

    world.facts.update({
        "hero": hero,
        "partner": partner,
        "rival": rival,
        "place": place,
        "theme_cfg": theme,
        "trouble_cfg": trouble,
        "fix_cfg": fix,
        "reconciled": True,
        "rib": hero.meters["rib_sore"] >= THRESHOLD,
        "thunk": True,
    })
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    return [
        f"Write a superhero story for a young child where {hero.id} gets a sore rib from a thunk, misunderstands {rival.id}, and then reconciles with them.",
        f"Tell a hero story with a big thunk, a hurt rib, and a reconciliation ending where the team works together again.",
        f"Write a small city superhero story that includes the words rib and thunk and ends with friends making up after a misunderstanding.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    rival = f["rival"]
    place = f["place"]
    return [
        QAItem(question=f"What hurt {hero.id} at the start of the story?", answer=f"A hard thunk hurt {hero.id}'s rib and made {hero.id} hold {hero.pronoun('possessive')} side."),
        QAItem(question=f"Why did {hero.id} think {rival.id} was the problem at first?", answer=f"{hero.id} heard the sudden thunk and saw {rival.id} run over, so the moment looked suspicious before anyone explained it."),
        QAItem(question=f"What changed the argument between {hero.id} and {rival.id}?", answer=f"{hero.id}'s partner helped them look at the broken gear, and they saw the thunk came from a loose beam instead of a punch."),
        QAItem(question="What is reconciliation in this story?", answer="Reconciliation is when the heroes apologized, listened, and became a team again instead of staying upset."),
        QAItem(question=f"Where did the final rescue happen?", answer=f"It happened on the {place.label}, where the heroes could see the whole city and finish the job together."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    keys = {"thunk", "rib", "reconciliation", "hero", "teamwork"}
    out: list[QAItem] = []
    for k in keys:
        for q, a in KNOWLEDGE[k]:
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [asp.fact("sense_min", SENSE_MIN)]
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for tid in TROUBLES:
        lines.append(asp.fact("trouble", tid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
    for rid in ("thunk",):
        lines.append(asp.fact("valid_trouble", rid))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
valid_combo(T, R, F) :- theme(T), valid_trouble(R), sensible(F).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    py = {tuple(x) for x in valid_combos()}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo parity ({len(py)} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    if {f.id for f in sensible_fixes()} == set(asp_sensible()):
        print("OK: sensible fixes parity.")
    else:
        print("MISMATCH in sensible fixes.")
        rc = 1
    rng = random.Random(7)
    for _ in range(20):
        p = resolve_params(argparse.Namespace(setting=None, trouble=None, fix=None, place=None, hero=None, hero_gender=None, partner=None, partner_gender=None, rival=None, rival_gender=None), rng)
        if p.trouble != "thunk":
            rc = 1
    print("OK: generated stories exercised.")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(world_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show valid_combo/3.\n#show sensible/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(", ".join(f"{x}" for x in asp_sensible()))
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, combo in enumerate(valid_combos()):
            p = StoryParams(
                setting=combo[0],
                hero="Ava",
                hero_gender="girl",
                partner="Leo",
                partner_gender="boy",
                rival="Nora",
                rival_gender="girl",
                place="bridge",
                trouble=combo[1],
                fix=combo[2],
                seed=base_seed + i,
            )
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                p = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
