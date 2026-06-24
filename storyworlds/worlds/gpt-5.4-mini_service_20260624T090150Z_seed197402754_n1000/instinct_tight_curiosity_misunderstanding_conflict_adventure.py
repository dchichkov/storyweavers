#!/usr/bin/env python3
"""
A small adventure storyworld about curiosity, a tight place, and a misunderstanding
that turns into teamwork.

Seed tale used to shape the world:
---
A curious child and a grown helper went on a little adventure near a narrow cave path.
The child had a strong instinct to explore, but the path was tight and the grown helper
thought the child should stay back. That misunderstanding caused a tense moment.
Then they looked carefully, found a safer way around, and the child got to explore
without getting stuck.
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
# Core model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
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
    place: str
    kind: str
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
class Pathway:
    id: str
    label: str
    width: str
    risk: str
    keyword: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    fix: str
    prep: str
    tail: str
    plural: bool = False
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
    setting: str
    path: str
    hero_name: str
    hero_type: str
    helper_type: str
    gear: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "forest": Setting(place="the forest trail", kind="outdoor", affords={"trail", "cave"}),
    "cave": Setting(place="the cave entrance", kind="outdoor", affords={"cave", "trail"}),
    "cliff": Setting(place="the cliff path", kind="outdoor", affords={"ridge", "trail"}),
}

PATHWAYS = {
    "tight_gap": Pathway(
        id="tight_gap",
        label="a tight gap",
        width="tight",
        risk="stuck",
        keyword="tight",
        tags={"tight", "cave", "adventure"},
    ),
    "narrow_bridge": Pathway(
        id="narrow_bridge",
        label="a narrow bridge",
        width="tight",
        risk="wobble",
        keyword="narrow",
        tags={"bridge", "adventure"},
    ),
    "rocky_passage": Pathway(
        id="rocky_passage",
        label="a rocky passage",
        width="tight",
        risk="scrape",
        keyword="rocky",
        tags={"rock", "adventure"},
    ),
}

GEAR = {
    "rope": Gear(
        id="rope",
        label="a sturdy rope",
        covers={"hands"},
        fix="steady",
        prep="tie on a sturdy rope and try the path slowly",
        tail="used the rope to move carefully",
    ),
    "lantern": Gear(
        id="lantern",
        label="a lantern",
        covers={"hands"},
        fix="see",
        prep="carry a lantern and look for another way",
        tail="followed the lantern light to a safer spot",
    ),
    "gloves": Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        fix="grip",
        prep="put on soft gloves and test the rocks first",
        tail="used the gloves to keep a better grip",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Luna", "Ivy", "Zoe", "Ava", "Maya"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Sam", "Noah", "Ben", "Theo"]
TRAITS = ["curious", "brave", "thoughtful", "spunky", "careful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A path is risky when it is tight and an explorer wants to take it.
at_risk(P) :- pathway(P), width(P, tight).

% A gear choice is reasonable if it helps with the risk and the path's problem.
has_fix(G, P) :- gear(G), at_risk(P), fix(G, _).

valid_story(S, P, G) :- setting(S), pathway(P), gear(G), afforded(S, P), at_risk(P), has_fix(G, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("afforded", sid, p))
    for pid, p in PATHWAYS.items():
        lines.append(asp.fact("pathway", pid))
        lines.append(asp.fact("width", pid, p.width))
        lines.append(asp.fact("risk", pid, p.risk))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        lines.append(asp.fact("fix", gid, g.fix))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    expected = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    got = set(asp.atoms(model, "valid_story"))
    if expected == got:
        print(f"OK: clingo gate matches valid_combos() ({len(got)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in python:", sorted(expected - got))
    print(" only in clingo:", sorted(got - expected))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for p_id, p in PATHWAYS.items():
            if p_id not in s.affords:
                continue
            for g_id in GEAR:
                if p.width == "tight":
                    combos.append((s_id, p_id, g_id))
    return combos


def path_at_risk(path: Pathway) -> bool:
    return path.width == "tight"


def select_gear(path: Pathway) -> Optional[Gear]:
    if not path_at_risk(path):
        return None
    for gear in GEAR.values():
        return gear
    return None


def predict_stuck(world: World, hero: Entity, path: Pathway) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["adventure"] = sim.get(hero.id).meters.get("adventure", 0) + 1
    return path_at_risk(path)


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    path = _safe_lookup(PATHWAYS, params.path)
    gear = GEAR[params.gear]

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"curiosity": 0.0, "adventure": 0.0, "fear": 0.0},
        memes={"Curiosity": 0.0, "Misunderstanding": 0.0, "Conflict": 0.0, "instinct": 0.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper_type,
    ))
    item = world.add(Entity(
        id="Gear",
        type="gear",
        label=gear.label,
        phrase=gear.label,
        caretaker=helper.id,
        owner=hero.id,
        plural=gear.plural,
    ))
    item.worn_by = hero.id

    hero.memes["Curiosity"] += 1
    hero.memes["instinct"] += 1

    world.say(
        f"{hero.id} was a little {params.hero_type} with a strong instinct for adventure, and "
        f"{hero.pronoun('possessive')} Curiosity was always peeking ahead."
    )
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {helper.type} went to {setting.place}, "
        f"where {path.label} looked ready for a brave little story."
    )

    world.para()
    world.say(
        f"{hero.id} wanted to go straight into {path.label}, because {hero.pronoun()} could feel "
        f"the pull of the trail in {hero.pronoun('possessive')} bones."
    )

    if predict_stuck(world, hero, path):
        hero.memes["Misunderstanding"] += 1
        hero.memes["Conflict"] += 1
        world.say(
            f"But {hero.pronoun('possessive')} {helper.type} thought the way was too risky and said, "
            f"\"Wait here.\""
        )
        world.say(
            f"{hero.id} thought that meant no adventure at all, and that misunderstanding made the air feel tight."
        )
        world.say(
            f"{hero.id} tried to step in anyway, but the tight gap looked even smaller up close."
        )
        gear_choice = gear
        if gear_choice is None:
            pass
        world.para()
        world.say(
            f"Then {hero.pronoun('possessive')} {helper.type} held up {gear_choice.label} and smiled. "
            f"\"Let's use this first,\" {helper.pronoun()} said."
        )
        world.say(
            f"They agreed to {gear_choice.prep}, and that turned the misunderstanding into teamwork."
        )
        hero.memes["Misunderstanding"] = 0.0
        hero.memes["Conflict"] = 0.0
        hero.meters["adventure"] += 1
        world.say(
            f"Soon {hero.id} was {path.risk}-safe and exploring with bright eyes, while "
            f"{gear_choice.label} helped {hero.pronoun('object')} keep steady."
        )
    else:
        world.say(
            f"Luckily, the way was open enough, so {hero.id} and {hero.pronoun('possessive')} {helper.type} "
            f"walked on without trouble."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        path=path,
        gear=gear,
        setting=setting,
        conflict=hero.memes["Conflict"] > 0,
        resolved=hero.memes["Conflict"] == 0,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    path = _safe_fact(world, f, "path")
    return [
        f'Write a short adventure story for a young child that includes the word "{path.keyword}".',
        f"Tell a story about {hero.id}, a curious {hero.type}, and a {helper.type} who disagree about a {path.label}.",
        f"Write a gentle adventure where a misunderstanding turns into teamwork near {path.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    path = _safe_fact(world, f, "path")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"What kind of feeling pushed {hero.id} to explore?",
            answer=f"{hero.id} had a strong instinct for adventure, and {hero.pronoun('possessive')} Curiosity kept pulling {hero.pronoun('object')} forward.",
        ),
        QAItem(
            question=f"What did {helper.type} misunderstand about the trip?",
            answer=f"{helper.pronoun().capitalize()} misunderstood {hero.id}'s eagerness and thought it meant {hero.id} should not go near {path.label} yet.",
        ),
        QAItem(
            question=f"How did the problem get solved near {path.label}?",
            answer=f"They used {gear.label} first, which helped {hero.id} stay safe and turned the Conflict into teamwork.",
        ),
        QAItem(
            question=f"How did {hero.id} feel by the end of the story?",
            answer=f"{hero.id} felt excited and proud, because the adventure continued without anyone getting stuck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    path = _safe_fact(world, f, "path")
    gear = _safe_fact(world, f, "gear")
    items = [
        QAItem(
            question="What does curiosity do?",
            answer="Curiosity makes someone want to look, ask, and learn about new things.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people think different things about the same moment.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the tense part of a story when characters want different things or are not sure what to do.",
        ),
    ]
    if path.width == "tight":
        items.append(QAItem(
            question="What does tight mean when you talk about a path?",
            answer="Tight means there is very little space, so people need to move carefully.",
        ))
    items.append(QAItem(
        question=f"What is {gear.label} for in this story?",
        answer=f"{gear.label.capitalize()} helps the travelers move carefully and stay steady on the path.",
    ))
    return items


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="forest", path="tight_gap", hero_name="Mia", hero_type="girl", helper_type="mother", gear="rope"),
    StoryParams(setting="cave", path="tight_gap", hero_name="Finn", hero_type="boy", helper_type="father", gear="lantern"),
    StoryParams(setting="cliff", path="rocky_passage", hero_name="Luna", hero_type="girl", helper_type="father", gear="gloves"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about Curiosity, Misunderstanding, and Conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHWAYS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    if getattr(args, "path", None) and getattr(args, "setting", None) and getattr(args, "path", None) not in _safe_lookup(SETTINGS, getattr(args, "setting", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "path", None) is None or c[1] == getattr(args, "path", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, path, gear = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, path=path, hero_name=name, hero_type=gender, helper_type=helper, gear=gear)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.hero_name}: {p.path} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
