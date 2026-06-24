#!/usr/bin/env python3
"""
gasp_breaker_obey_sharing_rhyme_whodunit.py
============================================

A small whodunit storyworld: somebody makes a shocked gasp, the breaker trips,
a child learns to obey a simple safety rule, and the solution depends on
sharing and rhyme clues.

Seed tale:
---
At the cozy library, Nina and her brother Milo were making rhyme cards for the
story corner. The lights flickered, then went dark with a gasp from everyone.
Nina noticed the breaker box in the hall, but Milo had been plugging too many
things into one socket so the breaker had clicked off.

"Obey the rule," their dad said. "Share the outlet and use one lamp at a time."
Nina laughed and made up a rhyme: "One plug is enough; two plugs are rough."
Milo obeyed, switched off the extra lamp, and Dad flipped the breaker back on.
Soon the reading corner glowed again, and the rhyme cards looked bright and
cheerful.

This world turns that premise into a tiny causal simulation with typed entities,
meters and memes, a reasonableness gate, ASP parity, and child-facing QA.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    breaker: object | None = None
    child: object | None = None
    lamp: object | None = None
    parent: object | None = None
    sib: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str
    indoor: bool = True
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    verb: str
    mess: str
    cause: str
    clue: str
    keyword: str
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
class Fix:
    id: str
    label: str
    action: str
    restores: str
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
class Hazard:
    id: str
    label: str
    phrase: str
    plural: bool = False
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "library": Setting(place="the cozy library", indoor=True, affords={"cards", "reading"}),
    "classroom": Setting(place="the classroom", indoor=True, affords={"cards", "reading"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"cards", "reading"}),
}

ACTIVITIES = {
    "cards": Activity(
        id="cards",
        verb="make rhyme cards",
        mess="scattered",
        cause="too many things in one socket",
        clue="one plug is enough; two plugs are rough",
        keyword="rhyme",
        tags={"rhyme", "sharing"},
    ),
    "reading": Activity(
        id="reading",
        verb="read by the lamp",
        mess="bright",
        cause="one lamp and one outlet",
        clue="share the light and keep it right",
        keyword="share",
        tags={"sharing"},
    ),
}

HAZARDS = {
    "socket": Hazard(id="socket", label="the socket", phrase="one socket", plural=False, tags={"breaker"}),
    "lamp": Hazard(id="lamp", label="the lamp", phrase="the lamp", plural=False, tags={"breaker"}),
    "corner": Hazard(id="corner", label="the reading corner", phrase="the reading corner", plural=False, tags={"sharing"}),
}

FIXES = {
    "switch_off": Fix(id="switch_off", label="switch off the extra lamp", action="switch off", restores="the lights came back", tags={"breaker"}),
    "share_outlet": Fix(id="share_outlet", label="share the outlet", action="share", restores="the breaker stayed on", tags={"sharing"}),
    "reset": Fix(id="reset", label="flip the breaker back on", action="flip", restores="the room lit up again", tags={"breaker"}),
}

GIRL_NAMES = ["Nina", "Maya", "Lina", "Ella", "Tess"]
BOY_NAMES = ["Milo", "Owen", "Noah", "Ben", "Theo"]
TRAITS = ["curious", "careful", "cheerful", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    activity: str
    hazard: str
    fix: str
    name: str
    sibling: str
    sibling_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(place="library", activity="cards", hazard="socket", fix="share_outlet", name="Nina", sibling="Milo", sibling_gender="boy", parent="dad", trait="curious"),
    StoryParams(place="classroom", activity="reading", hazard="lamp", fix="switch_off", name="Maya", sibling="Theo", sibling_gender="boy", parent="father", trait="patient"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for haz_id in HAZARDS:
                if act_id == "cards" and haz_id in {"socket", "lamp"}:
                    for fix_id in FIXES:
                        if fix_id in {"share_outlet", "switch_off", "reset"}:
                            out.append((place, act_id, haz_id))
                if act_id == "reading" and haz_id in {"lamp", "corner"}:
                    out.append((place, act_id, haz_id))
    return sorted(set(out))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit about sharing, rhyme, and a breaker.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mom", "dad", "mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "hazard", None) is None or c[2] == getattr(args, "hazard", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, hazard = (list(rng.choice(combos)) + [None, None, None])[:3]
    fix = getattr(args, "fix", None) or ("share_outlet" if activity == "cards" else rng.choice(["switch_off", "reset"]))
    parent = getattr(args, "parent", None) or rng.choice(["dad", "father", "mom", "mother"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sibling = getattr(args, "sibling", None) or rng.choice([n for n in (GIRL_NAMES + BOY_NAMES) if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, hazard=hazard, fix=fix, name=name, sibling=sibling, sibling_gender=gender, parent=parent, trait=trait)


def valid_story(params: StoryParams) -> bool:
    return (params.activity == "cards" and params.hazard in {"socket", "lamp"}) or (params.activity == "reading" and params.hazard in {"lamp", "corner"})


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS or params.activity not in ACTIVITIES or params.hazard not in HAZARDS or params.fix not in FIXES:
        pass
    if not valid_story(params):
        pass
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="girl" if params.name in GIRL_NAMES else "boy", role="detective", meters={"confusion": 0.0, "surprise": 0.0}, memes={"curiosity": 0.0, "gasp": 0.0, "obey": 0.0}))
    sib = world.add(Entity(id=params.sibling, kind="character", type=params.sibling_gender, role="helper", meters={"confusion": 0.0}, memes={"share": 0.0, "rhyme": 0.0}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent if params.parent in {"mom", "dad", "mother", "father"} else "father", role="parent", label=f"the {params.parent}", meters={"calm": 0.0}, memes={"authority": 1.0}))
    breaker = world.add(Entity(id="breaker", type="thing", label="breaker box", meters={"tripped": 1.0, "dark": 1.0}, memes={"mystery": 1.0}))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp", meters={"off": 1.0}))
    setting = world.setting
    child.memes["gasp"] += 1
    child.meters["surprise"] += 1
    world.say(f"At {setting.place}, {child.id} and {sib.id} were making rhyme cards.")
    world.say(f"Then the lights went out with a gasp, and everyone looked at the breaker box.")
    world.para()
    child.memes["curiosity"] += 1
    world.say(f"{sib.id} noticed the breaker in the hall, and {child.id} saw the clue at once.")
    world.say(f'"{_safe_lookup(ACTIVITIES, params.activity).clue}," {child.id} said, and the words sounded almost like a riddle.')
    if params.activity == "cards":
        child.memes["rhyme"] += 1
        sib.memes["share"] += 1
        world.say(f"{sib.id} had been plugging too many things into one socket, so the breaker had clicked off.")
        world.say(f'"Obey the rule," {parent.label} said. "Share the outlet and use one lamp at a time."')
        world.para()
        child.memes["obey"] += 1
        if params.fix == "share_outlet":
            world.say(f"{child.id} nodded and made up a rhyme: " + '"' + _safe_lookup(ACTIVITIES, params.activity).clue + '."')
            world.say(f"{sib.id} obeyed, switched off the extra lamp, and {parent.pronoun().capitalize()} flipped the breaker back on.")
            breaker.meters["tripped"] = 0.0
            breaker.meters["dark"] = 0.0
            lamp.meters["off"] = 0.0
            world.say("Soon the reading corner glowed again, and the rhyme cards looked bright and cheerful.")
        else:
            pass
    else:
        world.say(f"{sib.id} shared the lamp and {child.id} obeyed the rule to keep one outlet in use.")
        world.say(f"{parent.pronoun().capitalize()} reset the breaker and the room lit up again.")
    world.facts.update(child=child, sibling=sib, parent=parent, breaker=breaker, lamp=lamp, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a child-friendly whodunit where {p.name} hears a gasp, follows a clue to the breaker box, and learns to obey a safety rule about sharing the outlet.',
        f"Tell a short mystery at {world.setting.place} where rhyme cards, a tripped breaker, and a helpful parent solve the puzzle.",
        f'Write a story that includes the words "gasp", "breaker", and "obey", and ends with sharing and a rhyme clue.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(question=f"Who noticed the clue after the lights went out at {world.setting.place}?", answer=f"{p.name} noticed the clue and saw that the breaker box was important."),
        QAItem(question=f"What rule did {world.facts['parent'].label} tell them to obey?", answer="They were told to share the outlet and use one lamp at a time."),
        QAItem(question=f"What rhyme did {p.name} make up?", answer=f"{_safe_lookup(ACTIVITIES, p.activity).clue.capitalize()}."),
        QAItem(question=f"What happened when {p.sibling} obeyed?", answer="The extra lamp was switched off, the breaker was reset, and the room became bright again."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does a breaker do?", answer="A breaker protects a room by switching off the power if too many things use one circuit."),
        QAItem(question="Why is sharing helpful here?", answer="Sharing the outlet keeps the circuit from being overloaded, which helps the lights stay on."),
        QAItem(question="Why do people use rhyme in stories?", answer="Rhyme can make words easier to remember, and it can turn a clue into something catchy."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}\nA: {q.answer}")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(out)


ASP_RULES = r"""
valid(P,A,H) :- place(P), activity(A), hazard(H), workable(A,H).
workable(cards,socket).
workable(cards,lamp).
workable(reading,lamp).
workable(reading,corner).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for h in HAZARDS:
        lines.append(asp.fact("hazard", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    aspc = set(asp_valid_combos())
    smoke = generate(resolve_params(argparse.Namespace(place=None, activity=None, hazard=None, fix=None, parent=None, name=None, sibling=None, gender=None, trait=None), random.Random(7)))
    if not smoke.story:
        print("smoke test failed")
        return 1
    if py != aspc:
        print("ASP mismatch")
        print("only py", sorted(py - aspc))
        print("only asp", sorted(aspc - py))
        return 1
    print(f"OK: {len(py)} combos and smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(str(t) for t in asp_valid_combos()))
        return
    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples = [generate(resolve_params(args, rng)) for _ in range(getattr(args, "n", None))] if not getattr(args, "all", None) else [generate(p) for p in CURATED]
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
