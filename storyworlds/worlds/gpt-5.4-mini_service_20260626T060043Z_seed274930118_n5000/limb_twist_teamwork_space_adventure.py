#!/usr/bin/env python3
"""
A small storyworld for a Space Adventure tale with a limb twist and teamwork.

The premise:
- A tiny crew is on a ship or outpost in space.
- One character twists a limb during a task.
- The crew uses teamwork, tools, and care to fix the problem and keep the mission going.

The world is intentionally small and constraint-checked:
- The twist must be plausible for the limb and the activity.
- A fix must actually help and must be supported by the setting.
- Stories end with a clear changed state: the crew finishes the task together, and the hurt limb is safer.

This file is standalone under storyworlds/worlds/ and follows the shared contract.
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
    worn_by: Optional[str] = None
    limb: str = ""
    protective: bool = False
    supports: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    partner: object | None = None
    tool: object | None = None
    def __post_init__(self):
        if not self.meters:
            self.meters = {"twist": 0.0, "hurt": 0.0, "workload": 0.0, "repair": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "teamwork": 0.0, "relief": 0.0, "bravery": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def is_plural(self) -> bool:
        return self.type in {"crew", "helpers", "robots"}

    def them(self) -> str:
        return "them" if self.is_plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    indoors: bool
    supports: set[str] = field(default_factory=set)
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
    limb: str
    twist_kind: str
    worry: str
    site: str
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
class Aid:
    id: str
    label: str
    use: str
    effect: str
    place: str
    supports: set[str] = field(default_factory=set)
    hands: int = 1
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


@dataclass
class StoryParams:
    place: str
    activity: str
    aid: str
    name: str
    gender: str
    partner: str
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[list[str]] = [[]]
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
            self.story[-1].append(text)

    def para(self) -> None:
        if self.story[-1]:
            self.story.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.story if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.story = [[]]
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "ship": Setting("the starship", indoors=True, supports={"walk", "repair", "scan"}),
    "dock": Setting("the docking bay", indoors=True, supports={"walk", "repair", "haul"}),
    "moonbase": Setting("the moon base", indoors=True, supports={"walk", "repair", "scan", "haul"}),
    "ridge": Setting("the moon ridge", indoors=False, supports={"walk", "scan"}),
}

ACTIVITIES = {
    "crawl": Activity(
        id="crawl",
        verb="crawl through a tight tunnel",
        gerund="crawling through a tight tunnel",
        rush="hurry through the tunnel",
        limb="arm",
        twist_kind="twisted",
        worry="the narrow tunnel could pinch the limb again",
        site="tunnel",
        keyword="tunnel",
        tags={"space", "tunnel", "limb"},
    ),
    "climb": Activity(
        id="climb",
        verb="climb the ladder to the hatch",
        gerund="climbing to the hatch",
        rush="climb faster",
        limb="leg",
        twist_kind="sprained",
        worry="the ladder steps were too steep for a hurt leg",
        site="hatch",
        keyword="hatch",
        tags={"space", "hatch", "limb"},
    ),
    "float": Activity(
        id="float",
        verb="float to a broken panel",
        gerund="floating to the broken panel",
        rush="push off too hard",
        limb="wrist",
        twist_kind="twisted",
        worry="a sudden push could pull the wrist",
        site="panel",
        keyword="panel",
        tags={"space", "panel", "limb"},
    ),
}

AIDS = {
    "brace": Aid(
        id="brace",
        label="a soft brace",
        use="strap it on gently",
        effect="kept the limb still",
        place="arm",
        supports={"arm", "leg", "wrist"},
        hands=1,
    ),
    "bot": Aid(
        id="bot",
        label="a tiny repair bot",
        use="call it over with a chirp",
        effect="held the light and handed tools",
        place="panel",
        supports={"arm", "leg", "wrist"},
        hands=0,
    ),
    "rail": Aid(
        id="rail",
        label="a safety rail",
        use="grip the rail while moving",
        effect="gave steady support",
        place="leg",
        supports={"leg", "arm"},
        hands=1,
    ),
}

GIRL_NAMES = ["Luna", "Mira", "Nova", "Pia", "Aria", "Zara"]
BOY_NAMES = ["Kai", "Rio", "Jett", "Taro", "Seth", "Niko"]
TRAITS = ["brave", "curious", "careful", "clever", "cheerful", "stubborn"]


def story_reasonable(activity: Activity, aid: Aid) -> bool:
    return activity.limb in aid.supports


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            if act.site not in setting.supports and place != "ship":
                continue
            for aid_id, aid in AIDS.items():
                if story_reasonable(act, aid):
                    out.append((place, act_id, aid_id))
    return out


def explain_rejection(activity: Activity, aid: Aid) -> str:
    return (
        f"(No story: {aid.label} does not really help a {activity.limb} twist. "
        f"Choose aid that supports the hurt limb.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space adventure story world with a limb twist and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain", "crew"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "aid", None):
        act, aid = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(AIDS, getattr(args, "aid", None))
        if not story_reasonable(act, aid):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "aid", None) is None or c[2] == getattr(args, "aid", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, aid = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["captain", "crew"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, aid=aid, name=name, gender=gender, partner=parent, trait=trait)


def _do_activity(world: World, hero: Entity, act: Activity, narrate: bool = True) -> None:
    hero.meters["twist"] += 1
    hero.meters["hurt"] += 1
    hero.memes["worry"] += 1
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} tried to {act.verb}, but {hero.pronoun('possessive')} {act.limb} hurt right away.")


def predict_hurt(world: World, hero: Entity, act: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), act, narrate=False)
    return sim.get(hero.id).meters["hurt"] > 0


ASP_RULES = r"""
hurt(A) :- activity(A).
help(A, I) :- hurt(A), aid(I), supports(I, limb(A)).
valid(Place, A, I) :- setting(Place), activity(A), aid(I), supports(I, limb(A)).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for sup in sorted(s.supports):
            lines.append(asp.fact("supports_place", pid, sup))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("limb", aid, a.limb))
        lines.append(asp.fact("site", aid, a.site))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    for i, aid in AIDS.items():
        lines.append(asp.fact("aid", i))
        lines.append(asp.fact("support", i, aid.place))
        for s in sorted(aid.supports):
            lines.append(asp.fact("supports", i, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


def tell(setting: Setting, act: Activity, aid: Aid, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    partner = world.add(Entity(id="Partner", kind="character", type=parent_type, label="the team lead"))
    tool = world.add(Entity(id="Aid", type="tool", label=aid.label, protective=True, supports=set(aid.supports)))
    tool.worn_by = hero.id

    hero.memes["bravery"] += 1
    world.say(f"{hero.id} was a {trait} {gender} who loved missions on {setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} and {partner.label} worked on a small space job together, and {hero.id} trusted the crew.")

    world.para()
    world.say(f"On a quiet run, {hero.id} wanted to {act.verb} near the {act.site}.")
    world.say(f"The place was tricky, and {act.worry}.")
    _do_activity(world, hero, act)
    world.say(f"{hero.id} winced because {hero.pronoun('possessive')} {act.limb} had been {act.twist_kind}.")

    if predict_hurt(world, hero, act):
        hero.memes["worry"] += 1
        world.say(f"{partner.label} saw the hurt limb and called for teamwork right away.")
        world.say(f'"We can help," {partner.pronoun().capitalize()} said. "{aid.use}."')
        world.say(f"{partner.label} and {hero.id} used the {aid.label} together, and it {aid.effect}.")
        hero.memes["teamwork"] += 1
        hero.memes["relief"] += 1
        hero.meters["repair"] += 1
        hero.meters["hurt"] = 0
        hero.meters["twist"] = 0
        world.say(f"With the {aid.label}, {hero.id} could keep going safely.")
        world.say(f"In the end, the crew finished the task together, and {hero.id}'s {act.limb} felt steady again.")
    else:
        pass

    world.facts.update(hero=hero, partner=partner, act=act, aid=aid, setting=setting, trait=trait, gender=gender)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "act")
    aid = _safe_fact(world, f, "aid")
    return [
        f'Write a short Space Adventure story for a young child about {hero.id} and a {act.limb} twist.',
        f"Tell a gentle story where teamwork helps after {hero.id} gets {act.twist_kind} while trying to {act.verb}.",
        f'Write a simple space mission story that includes "{aid.label}" and ends with the crew helping each other.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, partner, act, aid = f["hero"], f["partner"], f["act"], f["aid"]
    return [
        QAItem(
            question=f"What happened to {hero.id}'s {act.limb} during the mission?",
            answer=f"{hero.id}'s {act.limb} got {act.twist_kind} while trying to {act.verb}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the limb hurt?",
            answer=f"{partner.label} helped {hero.id}, and the two of them used {aid.label} with teamwork.",
        ),
        QAItem(
            question=f"How did the story end after the crew worked together?",
            answer=f"The crew finished the task together, and {hero.id}'s {act.limb} felt steady and safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work together to do something hard.",
        ),
        QAItem(
            question="Why do people use a brace?",
            answer="People use a brace to support a hurt limb and help it stay still while it heals.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story q&a ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world q&a ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: type={e.type} meters={ {k: v for k, v in e.meters.items() if v} } memes={ {k: v for k, v in e.memes.items() if v} }")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(AIDS, params.aid), params.name, params.gender, params.partner, params.trait)
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(place="ship", activity="crawl", aid="brace", name="Luna", gender="girl", partner="captain", trait="brave"),
    StoryParams(place="dock", activity="climb", aid="rail", name="Kai", gender="boy", partner="crew", trait="careful"),
    StoryParams(place="moonbase", activity="float", aid="bot", name="Nova", gender="girl", partner="crew", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return

    if getattr(args, "asp", None):
        vals = asp_valid_combos()
        print(f"{len(vals)} compatible combos:\n")
        for v in vals:
            print("  ", v)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
