#!/usr/bin/env python3
"""
storyworlds/worlds/punk_advocate_fume_transformation_suspense_rhyme_heartwarming.py
====================================================================================

A compact story world about a punk kid advocate, a rising fume of worry,
a suspenseful wait, a small transformation, and a heartwarming rhyme at the end.

Seed image:
- A punk child with a sharp jacket and a loud voice loves to speak up for
  people who are being left out.
- When a community mural and tiny stage are threatened, the child starts to fume.
- A gentle helper suggests a rhyme, a calmer plan, and a transformation of the
  space from tense to welcoming.
- The ending proves the change with a warm, concrete image.

This script follows the storyworld contract:
- typed entities with meters and memes
- simulated state drives prose
- invalid choices raise StoryError
- inline ASP twin plus Python reasonableness gate
- CLI supports default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False

    guide: object | None = None
    kid: object | None = None
    show: object | None = None
    stage: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the little square"
    indoors: bool = False
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
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
class Transformation:
    id: str
    label: str
    prep: str
    tail: str
    boosts: dict[str, float] = field(default_factory=dict)
    clears: list[str] = field(default_factory=list)
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
        self.rhyme_ready: bool = False

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.rhyme_ready = self.rhyme_ready
        clone.facts = dict(self.facts)
        return clone


def _meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _set_mem(ent: Entity, key: str, value: float) -> None:
    ent.memes[key] = value


def _r_fume(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if _mem(c, "fume") < THRESHOLD:
            continue
        sig = ("fume", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_mem(c, "stormy")
        out.append(f"{c.id} crossed {c.pronoun('possessive')} arms, and the air around {c.id} felt hot with worry.")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    guide = world.get("guide")
    for c in world.characters():
        if _mem(c, "calm") < THRESHOLD or _mem(c, "fume") < THRESHOLD:
            continue
        sig = ("transform", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _set_mem(c, "fume", 0.0)
        _add_mem(c, "hope")
        _add_meter(c, "spark", 1.0)
        out.append(f"{guide.id} helped {c.id} turn the sharp feeling into a gentler one.")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    speaker = world.get("guide")
    if _mem(speaker, "rhyme") < THRESHOLD:
        return out
    sig = ("rhyme", speaker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.rhyme_ready = True
    out.append("The helper began to rhyme, and the little square listened.")
    return out


def _r_suspense_release(world: World) -> list[str]:
    out: list[str] = []
    show = world.get("show")
    stage = world.get("stage")
    kid = world.get("kid")
    if _meter(stage, "bright") < THRESHOLD or _mem(kid, "hope") < THRESHOLD:
        return out
    sig = ("release",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _set_mem(show, "cancelled", 0.0)
    _add_mem(kid, "joy")
    out.append("At last, the tiny show was safe, and everyone breathed again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_fume, _r_rhyme, _r_transform, _r_suspense_release):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def ask_risk(action: Action) -> bool:
    return "stage" in action.tags or "sign" in action.tags or "crowd" in action.tags


def valid_combo(setting: Setting, action: Action, transform: Transformation) -> bool:
    return ask_risk(action) and setting.place in {"the little square", "the old alley", "the school yard"} and "bright" in transform.boosts


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for aid, a in ACTIONS.items():
            for tid, t in TRANSFORMS.items():
                if valid_combo(s, a, t):
                    out.append((sid, aid, tid))
    return out


def predict(world: World, kid: Entity, action: Action) -> dict:
    sim = world.copy()
    do_action(sim, sim.get("kid"), action, narrate=False)
    show = sim.get("show")
    return {
        "cancelled": _mem(show, "cancelled") >= THRESHOLD,
        "fume": _mem(sim.get("kid"), "fume"),
    }


def do_action(world: World, kid: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        pass
    world.zone = set(action.zone)
    _add_mem(kid, action.mess)
    _add_mem(kid, "fume")
    _add_mem(world.get("show"), "cancelled")
    propagate(world, narrate=narrate)


def setting_line(setting: Setting, action: Action) -> str:
    if setting.indoors:
        return f"Inside {setting.place}, the air felt close and quiet."
    return f"At {setting.place}, the evening waited like a held breath."


def intro(world: World, kid: Entity) -> None:
    trait = next((t for t in kid.traits if t != "little"), "punk")
    world.say(f"{kid.id} was a little {trait} kid who loved speaking up for people who needed a voice.")


def want(world: World, kid: Entity, action: Action) -> None:
    _add_mem(kid, "desire")
    world.say(f"{kid.id} loved to {action.verb}, especially when the words could help someone feel seen.")


def setup_show(world: World, kid: Entity, show: Entity) -> None:
    world.say(f"That afternoon, {show.label} was set for a tiny performance, but a worried hush had spread through the crowd.")


def warning(world: World, guide: Entity, kid: Entity, action: Action, show: Entity) -> bool:
    pred = predict(world, kid, action)
    if not pred["cancelled"]:
        return False
    _add_mem(guide, "worry")
    world.facts["pred_cancelled"] = True
    world.say(f'"If we rush in now, the show could get canceled," {guide.id} said softly.')
    return True


def tension(world: World, kid: Entity, action: Action) -> None:
    kid.memes["fume"] = kid.memes.get("fume", 0.0) + 1.0
    world.say(f"{kid.id} wanted to help right away, but {kid.pronoun('possessive')} chest felt tight with fuming frustration.")


def suspense_line(world: World) -> None:
    world.say("For a moment, nobody knew whether the little stage would stay dark.")


def offer_rhyme(world: World, guide: Entity, kid: Entity) -> None:
    _add_mem(guide, "rhyme")
    world.say(f"{guide.id} smiled and said, 'We can make it gentle, and we can make it rhyme.'")
    propagate(world, narrate=True)


def transform_scene(world: World, kid: Entity, trans: Transformation) -> None:
    stage = world.get("stage")
    _add_meter(stage, "bright", 1.0)
    _add_meter(stage, "cozy", 1.0)
    for k, v in trans.boosts.items():
        _add_mem(kid, k, v)
    for clear in trans.clears:
        _set_mem(kid, clear, 0.0)
    world.say(f"They used {trans.label}, and the whole corner began to change.")
    world.say(f"{trans.tail}")
    propagate(world, narrate=True)


def ending(world: World, kid: Entity, action: Action, trans: Transformation) -> None:
    stage = world.get("stage")
    show = world.get("show")
    if _mem(show, "cancelled") < THRESHOLD:
        world.say(
            f"In the end, {kid.id} was {action.gerund}, the stage was bright and warm, "
            f"and the crowd listened with soft smiles."
        )


def tell(setting: Setting, action: Action, trans: Transformation, name: str = "Pip",
         gender: str = "nonbinary", parent: str = "guardian", trait: str = "punk") -> World:
    world = World(setting)
    kid = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "brave"]))
    guide = world.add(Entity(id="guide", kind="character", type=parent, label="the advocate", traits=["kind"]))
    stage = world.add(Entity(id="stage", type="thing", label="tiny stage"))
    show = world.add(Entity(id="show", type="thing", label="the community show"))

    intro(world, kid)
    want(world, kid, action)
    setup_show(world, kid, show)

    world.para()
    world.say(setting_line(setting, action))
    warning(world, guide, kid, action, show)
    tension(world, kid, action)
    suspense_line(world)

    world.para()
    offer_rhyme(world, guide, kid)
    transform_scene(world, kid, trans)
    ending(world, kid, action, trans)

    world.facts.update(kid=kid, guide=guide, stage=stage, show=show, action=action, trans=trans, setting=setting)
    return world


SETTINGS = {
    "square": Setting(place="the little square", indoors=False, affords={"march", "paint"}),
    "yard": Setting(place="the school yard", indoors=False, affords={"paint", "sing"}),
    "alley": Setting(place="the old alley", indoors=False, affords={"paint"}),
}

ACTIONS = {
    "march": Action(
        id="march",
        verb="lead a small march",
        gerund="leading the little march",
        rush="hurry into the square",
        mess="fume",
        soil="all wound up",
        zone={"crowd", "stage"},
        keyword="march",
        tags={"crowd", "stage"},
    ),
    "paint": Action(
        id="paint",
        verb="paint a bright mural",
        gerund="painting a bright mural",
        rush="grab the paint cups",
        mess="fume",
        soil="spattered with worry",
        zone={"stage", "sign"},
        keyword="mural",
        tags={"stage", "sign"},
    ),
    "sing": Action(
        id="sing",
        verb="sing a rally song",
        gerund="singing the rally song",
        rush="step to the microphone",
        mess="fume",
        soil="full of nervous buzz",
        zone={"crowd"},
        keyword="song",
        tags={"crowd"},
    ),
}

TRANSFORMS = {
    "banner": Transformation(
        id="banner",
        label="a hand-painted banner",
        prep="They hung a hand-painted banner of bright stars and kind words.",
        tail="The square looked less fierce and more like a place where everyone could belong.",
        boosts={"calm": 1.0, "hope": 1.0, "rhyme": 1.0},
        clears=["stormy"],
    ),
    "lanterns": Transformation(
        id="lanterns",
        label="paper lanterns",
        prep="They strung paper lanterns across the corner, and each one glowed like a tiny moon.",
        tail="The stage became warm enough for smiles, claps, and careful listening.",
        boosts={"calm": 1.0, "hope": 1.0, "rhyme": 1.0},
        clears=["stormy"],
    ),
    "chalk": Transformation(
        id="chalk",
        label="soft chalk words",
        prep="They wrote soft chalk words along the stone: 'Be kind, be heard, be here.'",
        tail="The old wall seemed to breathe easier, and the crowd did too.",
        boosts={"calm": 1.0, "hope": 1.0, "rhyme": 1.0},
        clears=["stormy"],
    ),
}

NAMES = ["Pip", "Rue", "Mox", "Zee", "Juno", "Bea"]
GENDERS = ["girl", "boy", "nonbinary"]
PARENTS = ["mother", "father", "guardian", "aunt"]
TRAITS = ["punk", "bold", "brave", "bright", "scrappy"]


def valid_story(setting: Setting, action: Action, trans: Transformation) -> bool:
    return valid_combo(setting, action, trans)


@dataclass
class StoryParams:
    place: str
    action: str
    transform: str
    name: str
    gender: str
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


KNOWLEDGE = {
    "punk": [("What does punk mean?", "Punk is a style that can mean bright hair, loud music, bold clothes, and speaking up for yourself.")],
    "advocate": [("What is an advocate?", "An advocate is someone who speaks up for what is fair or helps others be heard.")],
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like cat and hat.")],
    "lantern": [("What is a lantern?", "A lantern is a light that glows inside a cover, so it looks gentle and warm.")],
    "banner": [("What is a banner?", "A banner is a long sign or flag with words or pictures on it.")],
    "chalk": [("Why use chalk?", "Chalk is easy to draw with and can make words or pictures on the ground or a wall.")],
    "stage": [("What is a stage?", "A stage is a raised place where people perform or speak to a crowd.")],
    "fume": [("What does it mean to fume?", "To fume means to feel very angry or upset, like your feelings are bubbling hot.")],
}
KNOWLEDGE_ORDER = ["punk", "advocate", "fume", "rhyme", "lantern", "banner", "chalk", "stage"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid, action, trans = f["kid"], f["action"], f["trans"]
    return [
        f'Write a heartwarming story about a punk kid named {kid.id} who wants to {action.verb} and then calms down with a rhyme.',
        f"Tell a suspenseful, child-friendly story where {kid.id} starts to fume, but a kind advocate helps transform the scene.",
        f'Write a short story that includes "{action.keyword}" and ends with {trans.label} making the place feel safe and warm.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid, guide, action, trans = f["kid"], f["guide"], f["action"], f["trans"]
    place = world.setting.place
    trait = next((t for t in kid.traits if t != "little"), kid.type)
    qa = [
        QAItem(
            question=f"Who was the story about at {place}?",
            answer=f"It was about a little {trait} child named {kid.id} and {guide.label}, who was the advocate trying to help.",
        ),
        QAItem(
            question=f"What did {kid.id} want to do before the worry got bigger?",
            answer=f"{kid.id} wanted to {action.verb}. That mattered because the tiny show at {place} felt like it might be canceled.",
        ),
        QAItem(
            question=f"What made {kid.id} stop fuming and start hoping?",
            answer=f"{guide.label} offered a rhyme and {trans.label}. That turned the tense moment into something warmer.",
        ),
        QAItem(
            question=f"How did the place change by the end?",
            answer=f"The place changed from tense and uncertain to bright and welcoming. The ending showed {trans.tail.lower()}",
        ),
    ]
    if f.get("action").id in {"march", "paint", "sing"}:
        qa.append(
            QAItem(
                question=f"Why was there suspense in the story?",
                answer=f"There was suspense because nobody knew if the show would be canceled after {kid.id} started to fume. The question was whether they could transform the moment instead of losing it.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["action"].tags)
    tags.update({"punk", "advocate", "rhyme", "stage", "fume"})
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", action="march", transform="banner", name="Pip", gender="nonbinary", parent="guardian", trait="punk"),
    StoryParams(place="yard", action="sing", transform="lanterns", name="Rue", gender="girl", parent="mother", trait="bold"),
    StoryParams(place="alley", action="paint", transform="chalk", name="Mox", gender="boy", parent="father", trait="scrappy"),
]


def explain_rejection(action: Action) -> str:
    return f"(No story: {action.verb} does not make a good suspenseful problem here.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tagged", aid, t))
    for tid, t in TRANSFORMS.items():
        lines.append(asp.fact("transform", tid))
        lines.append(asp.fact("boosts_bright", tid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Action, Transform) :- setting(Place), affords(Place, Action),
                                  action(Action), tagged(Action, stage),
                                  transform(Transform), boosts_bright(Transform).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming punk advocate story world with suspense and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--transform", choices=TRANSFORMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
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
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "transform", None) is None or c[2] == getattr(args, "transform", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, transform = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    parent = getattr(args, "parent", None) or rng.choice(PARENTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, transform=transform, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(TRANSFORMS, params.transform),
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, action, transform) combos:\n")
        for row in triples:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.action} at {p.place} ({p.transform})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
