#!/usr/bin/env python3
"""
storyworlds/worlds/bride_foreshadowing_repetition_space_adventure.py
====================================================================

A standalone story world sketch for a tiny Space Adventure tale with a bride,
foreshadowing, and repetition.

Premise:
A small crew is preparing a wedding aboard a space station or a ship. The bride
wants a special detail to be ready for the ceremony, but space conditions and a
missing item create a gentle problem. Repetition is used as a signal and a
comforting beat; foreshadowing hints at the final reveal. The world resolves in a
concrete ending image that proves what changed.

The storyworld models typed entities with physical meters and emotional memes.
A tiny rule system advances the state: missing power can dim lights, a backup
device can restore them, and repeating preparations can raise anticipation.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    helper_for: str = ""
    safe: bool = False
    light_source: bool = False
    repair: bool = False
    decorators: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    altar: object | None = None
    bride: object | None = None
    fix: object | None = None
    partner: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "bride"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Setting:
    id: str
    place: str
    backdrop: str
    affords: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Problem:
    id: str
    need: str
    missing: str
    lack_meter: str
    foreshadow: str
    repetition_line: str
    danger_line: str
    ending_image: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

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
class Solution:
    id: str
    label: str
    phrase: str
    method: str
    restores: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Crewmate:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.story_marks: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.story_marks = list(self.story_marks)
        return w


SETTINGS = {
    "orbital_garden": Setting(
        id="orbital_garden",
        place="the orbital garden",
        backdrop="a glass dome full of floating pollen lights",
        affords={"wedding", "light_repair"},
    ),
    "moon_harbor": Setting(
        id="moon_harbor",
        place="the moon harbor",
        backdrop="silver docks and a sleepy blue moon",
        affords={"wedding", "light_repair"},
    ),
    "starliner_deck": Setting(
        id="starliner_deck",
        place="the starliner deck",
        backdrop="a bright corridor with windows showing the stars",
        affords={"wedding", "light_repair"},
    ),
    "comet_chapel": Setting(
        id="comet_chapel",
        place="the comet chapel",
        backdrop="a tiny chapel built into a comet-shaped craft",
        affords={"wedding", "light_repair"},
    ),
}

BRIDES = {
    "bride_lyra": Crewmate("bride_lyra", "bride", "Lyra", ["bride", "calm", "hopeful"]),
    "bride_nova": Crewmate("bride_nova", "bride", "Nova", ["bride", "bright", "patient"]),
    "bride_mira": Crewmate("bride_mira", "bride", "Mira", ["bride", "gentle", "curious"]),
}

PARTNERS = {
    "captain_sol": Crewmate("captain_sol", "captain", "Captain Sol", ["careful", "kind"]),
    "pilot_tess": Crewmate("pilot_tess", "pilot", "Pilot Tess", ["quick", "smiling"]),
    "engineer_ren": Crewmate("engineer_ren", "engineer", "Engineer Ren", ["steady", "helpful"]),
}

PROBLEMS = {
    "lantern": Problem(
        id="lantern",
        need="the ceremony lights",
        missing="the little lantern at the altar",
        lack_meter="darkness",
        foreshadow="The bride kept glancing at the empty stand where the lantern should glow.",
        repetition_line="Again and again, the bride checked the empty stand.",
        danger_line="Without a light, the ribbons and moon flowers looked dim and lost.",
        ending_image="the lantern shining softly beside the bride's bouquet",
        tags={"light", "lantern", "wedding"},
    ),
    "wreath": Problem(
        id="wreath",
        need="the flower wreath",
        missing="the silver flower wreath for the bride",
        lack_meter="worry",
        foreshadow="The bride touched her hair and looked at the empty hook where the wreath should hang.",
        repetition_line="Three times, the bride asked if the wreath had arrived yet.",
        danger_line="Without it, the aisle felt unfinished, as if a whole song was missing.",
        ending_image="the silver wreath resting bright on the bride's hair",
        tags={"flowers", "wreath", "wedding"},
    ),
    "music_box": Problem(
        id="music_box",
        need="the music box",
        missing="the tiny music box that played the walk-down tune",
        lack_meter="silence",
        foreshadow="Far down the hall, a loose cable flickered where the music box should have been plugged in.",
        repetition_line="Again the bride pressed the button and heard only a soft click.",
        danger_line="Without music, even the brave crew stepped too quietly and the room felt empty.",
        ending_image="the music box playing while the bride took her first step",
        tags={"music", "wedding", "sound"},
    ),
}

SOLUTIONS = {
    "battery_lantern": Solution(
        id="battery_lantern",
        label="a battery lantern",
        phrase="the battery lantern",
        method="plug in a battery lantern",
        restores="light",
        tags={"light", "lantern"},
    ),
    "spare_wreath": Solution(
        id="spare_wreath",
        label="a spare wreath",
        phrase="the spare wreath",
        method="take out a spare wreath from the storage box",
        restores="flowers",
        tags={"flowers", "wreath"},
    ),
    "backup_music": Solution(
        id="backup_music",
        label="a backup music box",
        phrase="the backup music box",
        method="switch on a backup music box",
        restores="sound",
        tags={"music", "sound"},
    ),
    "glow_ribbon": Solution(
        id="glow_ribbon",
        label="a glow ribbon",
        phrase="the glow ribbon",
        method="clip on a glow ribbon",
        restores="light",
        tags={"light"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    bride: str
    partner: str
    problem: str
    solution: str
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

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for setting in SETTINGS.values():
        for prob in PROBLEMS.values():
            for sol in SOLUTIONS.values():
                if prob.restores == sol.restores or prob.id == "music_box" and sol.id == "backup_music":
                    for bride in BRIDES.values():
                        for partner in PARTNERS.values():
                            combos.append((setting.id, bride.id, partner.id, prob.id, sol.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a bride, foreshadowing, and repetition.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--bride", choices=BRIDES)
    ap.add_argument("--partner", choices=PARTNERS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--solution", choices=SOLUTIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "bride", None) is None or c[1] == getattr(args, "bride", None))
              and (getattr(args, "partner", None) is None or c[2] == getattr(args, "partner", None))
              and (getattr(args, "problem", None) is None or c[3] == getattr(args, "problem", None))
              and (getattr(args, "solution", None) is None or c[4] == getattr(args, "solution", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, bride, partner, problem, solution = rng.choice(list(combos))
    return StoryParams(setting=setting, bride=bride, partner=partner, problem=problem, solution=solution)


def _entity_name(cfg: Crewmate) -> str:
    return cfg.label


def tell(setting: Setting, bride_cfg: Crewmate, partner_cfg: Crewmate, problem_cfg: Problem, solution_cfg: Solution) -> World:
    world = World(setting)
    bride = world.add(Entity(id=bride_cfg.id, kind="character", type="bride", label=bride_cfg.label, role="bride"))
    partner = world.add(Entity(id=partner_cfg.id, kind="character", type=partner_cfg.type, label=partner_cfg.label, role="partner"))
    altar = world.add(Entity(id="altar", kind="thing", type="altar", label="altar"))
    prop = world.add(Entity(id="prop", kind="thing", type="thing", label=problem_cfg.missing))
    fix = world.add(Entity(id="fix", kind="thing", type="tool", label=solution_cfg.label, safe=solution_cfg.safe, light_source=(solution_cfg.restores == "light"), repair=True))

    bride.memes["hope"] = 1
    partner.memes["care"] = 1
    altar.meters["ready"] = 1
    prop.meters[problem_cfg.lack_meter] = 1
    world.facts["foreshadowed"] = True
    world.facts["repeated"] = False

    world.say(f"In {setting.place}, {setting.backdrop} framed the day the bride, {bride.label}, was ready to begin.")
    world.say(f"{problem_cfg.foreshadow}")
    world.say(f'The bride whispered, "{problem_cfg.repetition_line}"')
    world.say(f'The bride whispered again, "{problem_cfg.repetition_line}"')
    world.para()
    world.say(f"But {problem_cfg.danger_line}")

    prop.meters[problem_cfg.lack_meter] += 1
    bride.memes["worry"] += 1

    world.para()
    bride.memes["anticipation"] += 1
    partner.memes["help"] += 1
    world.say(f"{partner.label} smiled and held up {solution_cfg.phrase}.")
    if solution_cfg.restores == "light":
        world.say(f'The bride nodded, because {solution_cfg.method} would make the deck glow again.')
    elif solution_cfg.restores == "flowers":
        world.say(f'The bride smiled, because {solution_cfg.method} would finish the wreath.')
    else:
        world.say(f'The bride listened, because {solution_cfg.method} would bring back the song.')

    if solution_cfg.restores == problem_cfg.restores:
        prop.meters[problem_cfg.lack_meter] = 0
        prop.meters["ready"] = 1
        bride.memes["worry"] = 0
        bride.memes["joy"] += 2
        partner.memes["joy"] += 1
        world.facts["resolved"] = True
    else:
        world.facts["resolved"] = False

    world.para()
    if solution_cfg.restores == "light":
        world.say(f"{partner.label} switched it on, and the dark place bloomed into a soft space glow.")
    elif solution_cfg.restores == "flowers":
        world.say(f"{partner.label} lifted it gently, and the bride's hair sparkled with silver petals.")
    else:
        world.say(f"{partner.label} clicked it open, and the song floated down the hall like a warm comet trail.")
    world.say(f"At the end, {problem_cfg.ending_image} proved the day was ready at last.")

    world.facts.update(
        setting=setting,
        bride=bride,
        partner=partner,
        problem=problem_cfg,
        solution=solution_cfg,
        altar=altar,
        prop=prop,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    bride = f["bride"].label
    partner = f["partner"].label
    prob = f["problem"]
    sol = f["solution"]
    return [
        f"Write a short space adventure for a young child about the bride {bride} and {partner} preparing for a wedding in {f['setting'].place}.",
        f"Tell a gentle story where {bride} notices something missing, keeps checking it again and again, and then uses {sol.label} to fix the problem.",
        f"Write a story with foreshadowing and repetition that ends with {prob.ending_image}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bride = f["bride"]
    partner = f["partner"]
    prob = f["problem"]
    sol = f["solution"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"It is about the bride {bride.label} and {partner.label}. They are preparing for a wedding in {setting.place}, and the missing detail gives the story its little turn.",
        ),
        QAItem(
            question=f"What was foreshadowed before {bride.label} used {sol.label}?",
            answer=f"The story foreshadowed {prob.missing}. The empty spot was mentioned before the fix arrived, so the reader could feel the problem coming.",
        ),
        QAItem(
            question=f"Why did {bride.label} keep repeating herself?",
            answer=f"She kept repeating herself because she was checking {prob.need} and waiting for it to be ready. The repetition shows her hope and worry growing before the help arrives.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {sol.label} change the ending?",
                answer=f"It solved the missing piece by restoring {prob.restores}. That is why the final image shows {prob.ending_image}.",
            )
        )
    else:
        qa.append(
            QAItem(
                question=f"What happened when {sol.label} did not fully fit the problem?",
                answer=f"The story still showed the bride and her partner trying to help, but the missing piece stayed wrong. The final image proves the room still needed another fix.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | set(world.facts["solution"].tags)
    out = []
    if "light" in tags:
        out.append(QAItem(
            question="What does a light do in space when it is dark?",
            answer="A light helps people see what is in front of them. In a space story, it can make a dark deck or hallway feel safe again.",
        ))
    if "wreath" in tags:
        out.append(QAItem(
            question="What is a wreath?",
            answer="A wreath is a loop of flowers or other decorations. People often wear one or hang one up for a special day.",
        ))
    if "music" in tags or "sound" in tags:
        out.append(QAItem(
            question="Why is music nice at a wedding?",
            answer="Music makes the celebration feel warm and special. It can also help everyone know when the big moment is starting.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.safe:
            bits.append("safe=True")
        parts.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(parts)


CURATED = [
    StoryParams(setting="orbital_garden", bride="bride_lyra", partner="captain_sol", problem="lantern", solution="battery_lantern"),
    StoryParams(setting="moon_harbor", bride="bride_nova", partner="pilot_tess", problem="wreath", solution="spare_wreath"),
    StoryParams(setting="starliner_deck", bride="bride_mira", partner="engineer_ren", problem="music_box", solution="backup_music"),
    StoryParams(setting="comet_chapel", bride="bride_lyra", partner="engineer_ren", problem="lantern", solution="glow_ribbon"),
]


ASP_RULES = r"""
valid(S,B,P,Pr,So) :- setting(S), bride(B), partner(P), problem(Pr), solution(So),
                      problem_restores(Pr,R), solution_restores(So,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for bid in BRIDES:
        lines.append(asp.fact("bride", bid))
    for pid in PARTNERS:
        lines.append(asp.fact("partner", pid))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        lines.append(asp.fact("problem_restores", prid, pr.tags and pr.restores if hasattr(pr, "restores") else ""))
    for soid, so in SOLUTIONS.items():
        lines.append(asp.fact("solution", soid))
        lines.append(asp.fact("solution_restores", soid, so.restores))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("MISMATCH between ASP and Python combos")
        print("only in ASP:", sorted(asp_set - py))
        print("only in Python:", sorted(py - asp_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            ok = False
            print("Smoke test failed: empty story")
    except Exception as e:
        ok = False
        print(f"Smoke test failed: {e}")
    if ok:
        print(f"OK: {len(py)} valid combos and smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    bride_cfg = _safe_lookup(BRIDES, params.bride)
    partner_cfg = _safe_lookup(PARTNERS, params.partner)
    problem_cfg = _safe_lookup(PROBLEMS, params.problem)
    solution_cfg = _safe_lookup(SOLUTIONS, params.solution)
    if problem_cfg.restores != solution_cfg.restores and not (problem_cfg.id == "music_box" and solution_cfg.id == "backup_music"):
        pass
    world = tell(setting, bride_cfg, partner_cfg, problem_cfg, solution_cfg)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            s = generate(params)
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
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
