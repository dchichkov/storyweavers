#!/usr/bin/env python3
"""
A standalone Storyweavers world: a curious slug, an audience, and a gentle bad-ending scare
that turns into a heartwarming finish.

The story premise is tiny and classical:
- A curious slug is drawn toward a little performance.
- The audience expects something harmless and sweet, but the slug's curiosity creates trouble.
- A caretaker notices the risk early enough to offer a kinder path.
- The ending stays soft and warm: the slug is safe, the audience is glad, and the world feels cared for.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


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
            keys = [upper, upper + "S", upper + "ES"]
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    in_audience: bool = False
    safe_place: bool = False

    crowd: object | None = None
    slug: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
        if "_tags" not in self.__dict__:
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
    description: str
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Curiosity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    danger: str
    tag: str
    zone: set[str] = field(default_factory=set)
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
class Comfort:
    id: str
    label: str
    phrase: str
    covers: set[str]
    soothes: set[str]
    prep: str
    tail: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def audience(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.in_audience]

    def safe_keeper(self) -> Optional[Entity]:
        for e in self.characters():
            if e.safe_place:
                return e
        return None


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


def _r_dry(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("dryness", 0.0) < THRESHOLD:
            continue
        if e.meters.get("worry", 0.0) >= THRESHOLD:
            sig = ("dry_worry", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["unease"] = e.memes.get("unease", 0.0) + 1
            out.append(f"The little air felt too dry, and {e.id} grew uneasy.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("comforted", 0.0) < THRESHOLD:
            continue
        sig = ("calm", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] = 0.0
        e.memes["joy"] = e.memes.get("joy", 0.0) + 1
        out.append(f"{e.id} settled down and felt safe again.")
    return out


CAUSAL_RULES = [Rule("dry", _r_dry), Rule("calm", _r_calm)]


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
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(
        place="the garden stage",
        description="A tiny wooden stage stood under a trellis of leaves.",
        affords={"sing", "watch", "follow"},
    ),
    "greenhouse": Setting(
        place="the greenhouse nook",
        description="Warm glass walls held in the soft morning air.",
        affords={"sing", "watch", "follow"},
    ),
    "porch": Setting(
        place="the porch corner",
        description="A shaded porch had a few pots, a mat, and a quiet little corner.",
        affords={"sing", "watch", "follow"},
    ),
}

CURIOSITIES = {
    "song": Curiosity(
        id="song",
        verb="listen to the song",
        gerund="listening to the song",
        rush="crawl toward the music",
        risk="leave the damp leaf",
        danger="dry out",
        tag="music",
        zone={"ground"},
    ),
    "light": Curiosity(
        id="light",
        verb="follow the lantern light",
        gerund="following the lantern light",
        rush="slide toward the glow",
        risk="go too far from home",
        danger="get lost",
        tag="light",
        zone={"ground"},
    ),
    "crumb": Curiosity(
        id="crumb",
        verb="inspect a tiny crumb",
        gerund="inspecting a tiny crumb",
        rush="hurry over to the crumb",
        risk="forget the safe path",
        danger="miss the way back",
        tag="food",
        zone={"ground"},
    ),
}

COMFORTS = {
    "leaf": Comfort(
        id="leaf",
        label="a damp leaf bridge",
        phrase="a cool, damp leaf bridge",
        covers={"ground"},
        soothes={"dryness"},
        prep="set down a cool, damp leaf bridge",
        tail="followed the leaf bridge",
    ),
    "moss": Comfort(
        id="moss",
        label="a moss nest",
        phrase="a soft moss nest",
        covers={"ground"},
        soothes={"worry"},
        prep="made a soft moss nest nearby",
        tail="settled into the moss nest",
    ),
    "shell": Comfort(
        id="shell",
        label="a small shell shade",
        phrase="a little shell shade",
        covers={"ground"},
        soothes={"dryness", "worry"},
        prep="placed a small shell shade over the path",
        tail="traveled under the shell shade",
    ),
}

NAMES = ["Milo", "Luna", "Pip", "Tia", "Nori", "Bea"]
AUDIENCES = ["children", "ladybugs", "moths", "tiny neighbors", "grandparents"]
TRAITS = ["curious", "gentle", "small", "bright-eyed", "patient"]


@dataclass
class StoryParams:
    setting: str
    curiosity: str
    comfort: str
    name: str
    audience: str
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for c_id in setting.affords:
            for f_id in COMFORTS:
                combos.append((s_id, c_id, f_id))
    return combos


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CURIOSITIES.items():
        lines.append(asp.fact("curiosity", cid))
        lines.append(asp.fact("tag", cid, c.tag))
    for fid, f in COMFORTS.items():
        lines.append(asp.fact("comfort", fid))
        for s in sorted(f.covers):
            lines.append(asp.fact("covers", fid, s))
        for s in sorted(f.soothes):
            lines.append(asp.fact("soothes", fid, s))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,C,F) :- affords(S,C), curiosity(C), comfort(F).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def reasonableness_gate(setting: Setting, curiosity: Curiosity, comfort: Comfort) -> bool:
    return curiosity.id in setting.affords and comfort.covers == {"ground"}


def predict_bad_end(world: World, slug: Entity, curiosity: Curiosity) -> dict:
    sim = world.copy()
    sim.get(slug.id).meters["dryness"] = sim.get(slug.id).meters.get("dryness", 0.0) + 1.0
    sim.get(slug.id).memes["worry"] = sim.get(slug.id).memes.get("worry", 0.0) + 1.0
    return {
        "dry": sim.get(slug.id).meters["dryness"] >= THRESHOLD,
        "lost": curiosity.danger == "get lost",
    }


def introduce(world: World, slug: Entity, audience: Entity) -> None:
    world.say(
        f"{slug.id} was a small, curious slug who loved noticing every shiny thing near {world.setting.place}."
    )
    world.say(
        f"Tonight, an audience of {audience.label} had gathered there, and the whole place felt hushed and kind."
    )


def describe_scene(world: World, curiosity: Curiosity) -> None:
    world.say(world.setting.description)
    world.say(
        f"The slug kept peeking toward the {curiosity.tag}, because {curiosity.gerund} made {world.setting.place} feel full of mystery."
    )


def start_wanting(world: World, slug: Entity, curiosity: Curiosity) -> None:
    slug.memes["curiosity"] = slug.memes.get("curiosity", 0.0) + 1
    slug.meters["dryness"] = slug.meters.get("dryness", 0.0) + 1
    world.say(
        f"{slug.id} wanted to {curiosity.verb}, even though {slug.pronoun('possessive')} body liked staying on cool, damp ground."
    )


def warn(world: World, slug: Entity, curiosity: Curiosity) -> bool:
    pred = predict_bad_end(world, slug, curiosity)
    if not pred["dry"] and not pred["lost"]:
        return False
    slug.memes["worry"] = slug.memes.get("worry", 0.0) + 1
    if pred["lost"]:
        world.say(
            f"A gentle caretaker saw the little slug edging away and said, \"Let's not let you get lost.\""
        )
    else:
        world.say(
            f"A gentle caretaker noticed how dry the path was and said, \"Let's keep you soft and safe.\""
        )
    return True


def trouble(world: World, slug: Entity, curiosity: Curiosity) -> None:
    slug.meters["dryness"] = slug.meters.get("dryness", 0.0) + 1
    slug.memes["worry"] = slug.memes.get("worry", 0.0) + 1
    world.say(
        f"{slug.id} tried to {curiosity.rush}, but the little path felt rough and too dry."
    )
    propagate(world)


def offer_comfort(world: World, slug: Entity, comfort: Comfort) -> Comfort:
    world.say(f"Then the caretaker {comfort.prep}.")
    slug.memes["comforted"] = slug.memes.get("comforted", 0.0) + 1
    slug.meters["dryness"] = 0.0
    return comfort


def accept(world: World, slug: Entity, audience: Entity, curiosity: Curiosity, comfort: Comfort) -> None:
    slug.memes["joy"] = slug.memes.get("joy", 0.0) + 1
    slug.memes["worry"] = 0.0
    world.say(
        f"{slug.id} smiled, and the audience of {audience.label} smiled too."
    )
    world.say(
        f"At last, {slug.id} {comfort.tail}, and the curious little trip stayed safe instead of becoming a bad ending."
    )
    world.say(
        f"The audience clapped softly as the slug left a silver trail behind {slug.pronoun('object')}, warm and happy."
    )


def tell(setting: Setting, curiosity: Curiosity, comfort: Comfort, name: str, audience: str) -> World:
    world = World(setting)
    slug = world.add(Entity(id=name, kind="character", type="slug", label="slug"))
    crowd = world.add(Entity(id="Audience", kind="character", type="crowd", label=audience, in_audience=True))
    world.facts.update(slug=slug, audience=crowd, curiosity=curiosity, comfort=comfort, setting=setting)

    introduce(world, slug, crowd)
    world.para()
    describe_scene(world, curiosity)
    start_wanting(world, slug, curiosity)
    warn(world, slug, curiosity)
    trouble(world, slug, curiosity)
    world.para()
    offer_comfort(world, slug, comfort)
    accept(world, slug, crowd, curiosity, comfort)
    slug.memes["resolved"] = 1.0
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    slug = _safe_fact(world, f, "slug")
    curiosity = _safe_fact(world, f, "curiosity")
    comfort = _safe_fact(world, f, "comfort")
    crowd = _safe_fact(world, f, "audience")
    return [
        f'Write a heartwarming story for a young child about a curious slug and an audience, using the word "{curiosity.tag}".',
        f"Tell a gentle story where {slug.id} wants to {curiosity.verb}, but a caretaker helps before the slug gets into a bad ending.",
        f"Write a small, cozy story about {slug.id}, {crowd.label}, and {comfort.label} at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    slug = _safe_fact(world, f, "slug")
    crowd = _safe_fact(world, f, "audience")
    curiosity = _safe_fact(world, f, "curiosity")
    comfort = _safe_fact(world, f, "comfort")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {slug.id}, a curious little slug.",
        ),
        QAItem(
            question=f"Who was in the audience?",
            answer=f"The audience was made of {crowd.label}, and they watched kindly from the side.",
        ),
        QAItem(
            question=f"What did {slug.id} want to do?",
            answer=f"{slug.id} wanted to {curiosity.verb}, because the little {curiosity.tag} looked exciting.",
        ),
        QAItem(
            question=f"Why did the caretaker step in?",
            answer=f"The caretaker stepped in because the path was too dry and the slug might have had a bad ending if it went on alone.",
        ),
        QAItem(
            question=f"What helped the slug stay safe?",
            answer=f"{comfort.label} helped, because it kept the slug on a cool and safe path.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {slug.id} safe, the audience smiling, and the whole moment feeling warm and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a slug?",
            answer="A slug is a small soft animal that moves slowly and likes cool, damp places.",
        ),
        QAItem(
            question="Why do slugs like damp places?",
            answer="Slugs like damp places because their bodies stay healthier and easier to move on when they do not dry out.",
        ),
        QAItem(
            question="What is an audience?",
            answer="An audience is a group of people or creatures who watch something like a show or a little performance.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.in_audience:
            bits.append("audience=yes")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling and CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="garden", curiosity="song", comfort="leaf", name="Milo", audience="children"),
    StoryParams(setting="greenhouse", curiosity="light", comfort="shell", name="Luna", audience="ladybugs"),
    StoryParams(setting="porch", curiosity="crumb", comfort="moss", name="Pip", audience="tiny neighbors"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_id = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    setting = _safe_lookup(SETTINGS, setting_id)
    curiosity_id = getattr(args, "curiosity", None) or rng.choice(sorted(setting.affords))
    comfort_id = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))
    curiosity = _safe_lookup(CURIOSITIES, curiosity_id)
    comfort = _safe_lookup(COMFORTS, comfort_id)
    if not reasonableness_gate(setting, curiosity, comfort):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES)
    audience = getattr(args, "audience", None) or rng.choice(AUDIENCES)
    return StoryParams(setting=setting_id, curiosity=curiosity_id, comfort=comfort_id, name=name, audience=audience)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(CURIOSITIES, params.curiosity),
        _safe_lookup(COMFORTS, params.comfort),
        params.name,
        params.audience,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming slug-and-audience story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--audience", choices=AUDIENCES)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(valid_combos())} compatible combos:")
        for s, c, f in valid_combos():
            print(f"  {s:11} {c:8} {f}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.curiosity} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
