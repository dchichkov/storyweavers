#!/usr/bin/env python3
"""
A small storyworld about a tutor, a worried warning, and a lesson that ends
softly but not perfectly.

Seed tale:
---
A child met with a kind tutor to finish a hard little project. The tutor warned
the child not to rush or use the wrong glue, because the page would wrinkle and
the work would not dry right. The child did not listen, tried a quick shortcut,
and the project ended up ruined. Even so, the tutor stayed gentle, helped clean
up, and promised to try again tomorrow.

World model:
---
- The child has a meter for confidence and a meter for mess.
- The project has meters for smudged, wrinkled, and ruined.
- The tutor has a meter for concern and warmth.
- Warning matters: if the child ignores it, the wrong shortcut causes the bad
  ending.
- Heartwarming tone comes from care and comfort, even when the result is sad.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    project: object | None = None
    tutor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "tutor"}
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
    place: str = "the little study nook"
    quiet: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    tags: set[str] = field(default_factory=set)
    keyword: str = ""
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
class Project:
    label: str
    phrase: str
    type: str
    surface: str
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


@dataclass
class Shortcut:
    id: str
    label: str
    prep: str
    tail: str
    risk: str
    guards: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    project = world.get("project")
    tutor = world.get("tutor")
    if child.meters.get("rush", 0) < THRESHOLD:
        return out
    if world.facts.get("shortcut_taken"):
        sig = ("smudge",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        project.meters["smudged"] = project.meters.get("smudged", 0) + 1
        project.meters["ruined"] = project.meters.get("ruined", 0) + 1
        tutor.memes["concern"] = tutor.memes.get("concern", 0) + 1
        out.append("The page bent and smeared.")
    return out


def _r_sad_end(world: World) -> list[str]:
    project = world.get("project")
    child = world.get("child")
    tutor = world.get("tutor")
    if project.meters.get("ruined", 0) < THRESHOLD:
        return []
    sig = ("ending",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["disappointment"] = child.memes.get("disappointment", 0) + 1
    tutor.memes["warmth"] = tutor.memes.get("warmth", 0) + 1
    return ["__ending__"]


CAUSAL_RULES = [_r_smudge, _r_sad_end]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__ending__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_bad_end(world: World, child: Entity, activity: Activity) -> bool:
    sim = world.copy()
    sim.get("child").meters["rush"] = 1
    sim.facts["shortcut_taken"] = True
    propagate(sim, narrate=False)
    return sim.get("project").meters.get("ruined", 0) >= THRESHOLD


def setting_detail(setting: Setting) -> str:
    if setting.quiet:
        return f"{setting.place.capitalize()} was quiet, with a small lamp glowing on the table."
    return f"{setting.place.capitalize()} was bright and tidy, ready for careful work."


def story_intro(world: World, child: Entity, tutor: Entity, project: Entity, activity: Activity) -> None:
    world.say(f"{child.id} came to the little study nook to work with {tutor.label}.")
    world.say(f"{tutor.id} smiled and showed {child.id} {project.phrase} on the table.")
    world.say(f"{child.id} loved {activity.gerund}, because it felt like making something kind and clever.")


def caution(world: World, tutor: Entity, child: Entity, project: Entity, activity: Activity) -> bool:
    if not predict_bad_end(world, child, activity):
        return False
    world.say(
        f'"Please do not {activity.rush}," {tutor.label} said gently. '
        f'"If you hurry, {project.label} will {activity.soil}."'
    )
    world.facts["warned"] = True
    return True


def ignore_warning(world: World, child: Entity, activity: Activity) -> None:
    child.meters["rush"] = child.meters.get("rush", 0) + 1
    child.memes["confidence"] = child.memes.get("confidence", 0) + 1
    world.say(f"{child.id} nodded, but the shortcut looked easier than waiting.")
    world.say(f"Then {child.id} tried to {activity.rush}.")


def try_shortcut(world: World, shortcut: Shortcut) -> None:
    world.facts["shortcut_taken"] = True
    world.say(f"{child_name(world)} reached for {shortcut.label} {shortcut.prep}.")
    world.say(f"{shortcut.tail}, even though {shortcut.risk}.")


def child_name(world: World) -> str:
    return world.get("child").id


def resolution(world: World, tutor: Entity, child: Entity, project: Entity) -> None:
    if project.meters.get("ruined", 0) < THRESHOLD:
        return
    world.say(f"{child.id} stared at the wrinkled page and went very quiet.")
    world.say(f"{tutor.label} did not scold {child.id}. Instead, {tutor.pronoun()} sat beside {child.id}.")
    world.say(
        f'"We can clean up and try again tomorrow," {tutor.label} said. '
        f'"A hard page is not the same as a hard lesson."'
    )
    world.say(
        f"{child.id} leaned close and let {tutor.label} fold the ruined paper into the bin. "
        f"Then {child.id} held the pencil more carefully, even though the first try was lost."
    )
    world.facts["resolved_with_kindness"] = True


SETTINGS = {
    "study nook": Setting(place="the little study nook", quiet=True, affords={"worksheet"}),
    "library corner": Setting(place="the library corner", quiet=True, affords={"worksheet"}),
    "kitchen table": Setting(place="the kitchen table", quiet=False, affords={"worksheet"}),
}

ACTIVITIES = {
    "glue": Activity(
        id="glue",
        verb="glue the pieces quickly",
        gerund="gluing little pieces",
        rush="smear the glue too fast",
        mess="smudged",
        soil="wrinkle and smear",
        tags={"paper", "messy"},
        keyword="glue",
    ),
    "paint": Activity(
        id="paint",
        verb="paint the border quickly",
        gerund="painting neat borders",
        rush="slap on the paint too fast",
        mess="smudged",
        soil="smear and drip",
        tags={"paint", "messy"},
        keyword="paint",
    ),
}

PROJECTS = {
    "poster": Project(
        label="poster",
        phrase="a paper poster with little stars",
        type="paper",
        surface="page",
    ),
    "worksheet": Project(
        label="worksheet",
        phrase="a worksheet with friendly letters",
        type="paper",
        surface="page",
    ),
}

SHORTCUTS = {
    "thick-glue": Shortcut(
        id="thick-glue",
        label="the thick glue bottle",
        prep="from the shelf",
        tail="It spread in lumpy streaks across the page",
        risk="it dries unevenly",
        guards={"glue"},
    ),
    "wet-brush": Shortcut(
        id="wet-brush",
        label="the wet paintbrush",
        prep="without wiping it first",
        tail="It left a shiny puddle at the edge",
        risk="the paper bends",
        guards={"paint"},
    ),
}

NAMES = ["Mina", "Noah", "Ruby", "Eli", "Sara", "Owen"]
TUTOR_NAMES = ["Ms. Pine", "Mr. Bell", "Tutor June", "Tutor Sam"]


@dataclass
class StoryParams:
    place: str
    activity: str
    project: str
    child_name: str
    tutor_name: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for proj in PROJECTS:
                combos.append((place, act, proj))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A cautionary, bad-ending, heartwarming storyworld about a tutor and a child."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--name", dest="child_name")
    ap.add_argument("--tutor")
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
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "project", None) is None or c[2] == getattr(args, "project", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, project = rng.choice(list(combos))
    return StoryParams(
        place=place,
        activity=activity,
        project=project,
        child_name=getattr(args, "child_name", None) or rng.choice(NAMES),
        tutor_name=getattr(args, "tutor", None) or rng.choice(TUTOR_NAMES),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type="child"))
    tutor = world.add(Entity(id="tutor", kind="character", type="tutor", label=params.tutor_name))
    project = world.add(Entity(id="project", type="project", label=_safe_lookup(PROJECTS, params.project).label, phrase=_safe_lookup(PROJECTS, params.project).phrase))
    activity = _safe_lookup(ACTIVITIES, params.activity)

    story_intro(world, child, tutor, project, activity)
    world.para()
    world.say(setting_detail(world.setting))
    caution(world, tutor, child, project, activity)
    ignore_warning(world, child, activity)
    try_shortcut(world, SHORTCUTS["thick-glue"] if params.activity == "glue" else SHORTCUTS["wet-brush"])
    propagate(world, narrate=True)
    world.para()
    resolution(world, tutor, child, project)

    world.facts.update(child=child, tutor=tutor, project=project, activity=activity, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    a = _safe_fact(world, world.facts, "activity")
    return [
        f"Write a gentle story about a tutor who warns a child not to {a.rush}, but the child does it anyway.",
        f"Tell a short heartwarming story set in {p.place} where {p.child_name} and {p.tutor_name} work on a {p.project}.",
        f"Write a cautionary tale with a sad ending and a kind tutor, using the word '{a.keyword}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    tutor = _safe_fact(world, f, "tutor")
    project = _safe_fact(world, f, "project")
    activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, who came to work with {tutor.label} on {project.label}.",
        ),
        QAItem(
            question=f"What did the tutor warn {child.id} not to do?",
            answer=f"{tutor.label} warned {child.id} not to {activity.rush}, because the {project.label} would {activity.soil}.",
        ),
        QAItem(
            question=f"What happened when {child.id} ignored the warning?",
            answer=f"The {project.label} got wrinkled and ruined, so the first try did not work.",
        ),
        QAItem(
            question=f"How did the tutor help at the end?",
            answer=f"{tutor.label} stayed gentle, helped clean up, and promised to try again tomorrow.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tutor?",
            answer="A tutor is a person who helps someone learn by teaching carefully and kindly.",
        ),
        QAItem(
            question="Why should people wait for glue or paint to dry?",
            answer="They should wait because wet glue or paint can smear, bend, or ruin the paper.",
        ),
        QAItem(
            question="What does it mean to be careful with school work?",
            answer="Being careful means doing the work slowly enough to avoid mistakes and keep the page neat.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:8} ({e.type:8}) meters={e.meters} memes={e.memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
warned :- tutor(t), child(c), activity(a), project(p), predicts_bad_end(a,p).
bad_end :- warned, shortcut_taken, ruined(project).

predicts_bad_end(a,p) :- activity(a), project(p), risky(a,p).
risky(glue, poster).
risky(glue, worksheet).
risky(paint, poster).
risky(paint, worksheet).

shortcut_taken :- use_shortcut.
ruined(project) :- smudged(project).
smudged(project) :- shortcut_taken, risky(_, _).

valid_story(Place, Activity, Project) :- setting(Place), affords(Place, Activity), project(Project).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", place, a))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PROJECTS:
        lines.append(asp.fact("project", p))
    lines.append(asp.fact("tutor", "tutor"))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("use_shortcut"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="study nook", activity="glue", project="worksheet", child_name="Mina", tutor_name="Tutor June"),
    StoryParams(place="library corner", activity="paint", project="poster", child_name="Noah", tutor_name="Ms. Pine"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for c in combos:
            print(c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
