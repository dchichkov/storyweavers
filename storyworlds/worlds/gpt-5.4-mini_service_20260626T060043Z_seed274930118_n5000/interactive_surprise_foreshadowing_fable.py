#!/usr/bin/env python3
"""
storyworlds/worlds/interactive_surprise_foreshadowing_fable.py
==============================================================

A small fable-style story world with foreshadowing and a surprise turn.

The premise is simple: an animal friend has a small task, notices a clue,
meets a choice, and later learns that the clue mattered. The story is built
from simulated world state rather than a frozen template, and the ending
shows what changed.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    trait: str = ""
    hero: object | None = None
    keeper: object | None = None
    prize_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "hen"}
        male = {"boy", "father", "man", "fox", "wolf", "dog", "cat", "bear"}
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
    mood: str
    afford: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    risk: str
    clue: str
    surprise: str
    moral: str
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
class Prize:
    label: str
    phrase: str
    type: str
    risk_meter: str
    owner_kind: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "orchard": Setting(place="the orchard", mood="sunny", afford={"find", "pick", "share"}),
    "lantern_path": Setting(place="the lantern path", mood="twilight", afford={"follow", "guide", "listen"}),
    "garden": Setting(place="the garden", mood="quiet", afford={"water", "find", "rest"}),
}

TASKS = {
    "follow": Task(
        id="follow",
        verb="follow the little trail",
        gerund="following the little trail",
        risk="get lost",
        clue="crumbs on a stone",
        surprise="the crumbs belonged to a friend who was helping all along",
        moral="A small clue can point to a big kindness.",
        tags={"trail", "clue", "kindness", "interactive"},
    ),
    "pick": Task(
        id="pick",
        verb="pick the sweetest fruit",
        gerund="picking the sweetest fruit",
        risk="drop the basket",
        clue="a leaf tied with a ribbon",
        surprise="the ribbon marked a basket hidden for a celebration",
        moral="Patience can make a surprise sweeter.",
        tags={"fruit", "clue", "gift", "interactive"},
    ),
    "water": Task(
        id="water",
        verb="water the sleeping flowers",
        gerund="watering the sleeping flowers",
        risk="wake the bees",
        clue="a soft hum near the fence",
        surprise="the hum was a bee friend waiting to share honey",
        moral="Listening gently can turn fear into friendship.",
        tags={"flowers", "clue", "listening", "interactive"},
    ),
}

PRIZES = {
    "berries": Prize(label="berries", phrase="a red berry pie", type="berries", risk_meter="dropped", owner_kind="helper"),
    "lantern": Prize(label="lantern", phrase="a small brass lantern", type="lantern", risk_meter="dimmed", owner_kind="elder"),
    "bouquet": Prize(label="bouquet", phrase="a bright bouquet", type="bouquet", risk_meter="bruised", owner_kind="friend"),
}

NAMES = ["Milo", "Ruby", "Pip", "Nina", "Toby", "Sage", "Ollie", "Fern"]
KINDS = [("fox", "fox"), ("rabbit", "rabbit"), ("crow", "crow"), ("mouse", "mouse"), ("hedgehog", "hedgehog")]
TRAITS = ["brave", "curious", "gentle", "patient", "lively", "small"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    name: str
    kind: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable with foreshadowing and surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=[k for k, _ in KINDS])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s, setting in SETTINGS.items():
        for t, task in TASKS.items():
            if t not in setting.afford:
                continue
            for p in PRIZES:
                combos.append((s, t, p))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tagged", tid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risk_meter", pid, p.risk_meter))
        lines.append(asp.fact("owner_kind", pid, p.owner_kind))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,T,P) :- affords(S,T), setting(S), task(T), prize(P).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, task, prize = rng.choice(list(combos))
    kind, _ = rng.choice(KINDS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, task=task, prize=prize, name=name, kind=kind, trait=trait)


def story_intro(world: World, hero: Entity, task: Task, prize: Prize, keeper: Entity) -> None:
    world.say(f"{hero.id} was a {hero.trait} little {hero.type} who lived near {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} loved {task.gerund}, because it made the day feel like a game.")
    world.say(f"One day, {keeper.label} brought {hero.pronoun('object')} {prize.phrase}, and {hero.id} was proud to carry it.")


def story_middle(world: World, hero: Entity, task: Task, prize: Prize, keeper: Entity) -> None:
    world.para()
    world.say(f"At {world.setting.place}, {hero.id} wanted to {task.verb}.")
    world.say(f"But {hero.pronoun('possessive')} {keeper.label} noticed {task.clue} first.")
    world.say(f'That was a quiet hint that something mattered nearby, even before the surprise arrived.')
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.facts["foreshadow"] = task.clue
    world.facts["risk"] = task.risk
    world.facts["risk_meter"] = prize.risk_meter


def story_turn(world: World, hero: Entity, task: Task, prize: Prize, keeper: Entity) -> None:
    world.say(f"Then the small trouble came: if {hero.id} went on, {hero.pronoun('possessive')} {prize.label} might {prize.risk_meter}.")
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    keeper.memes["care"] = keeper.memes.get("care", 0) + 1
    if task.id == "follow":
        world.say(f"{hero.id} nearly hurried into the trees, but the trail of crumbs seemed to say, 'Wait and look.'")
    elif task.id == "pick":
        world.say(f"{hero.id} nearly reached for the highest fruit, but the ribbon on the leaf seemed to say, 'Be patient.'")
    else:
        world.say(f"{hero.id} nearly splashed ahead, but the soft hum by the fence seemed to say, 'Listen first.'")


def story_surprise(world: World, hero: Entity, task: Task, prize: Prize, keeper: Entity) -> None:
    world.para()
    world.say(f"At last, the surprise appeared.")
    world.say(f"{task.surprise.capitalize()}.")
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    hero.memes["worry"] = max(0, hero.memes.get("worry", 0) - 1)
    world.facts["surprise"] = task.surprise
    world.facts["resolved"] = True
    world.say(
        f"{hero.id} smiled and held the {prize.label} carefully, and {keeper.label} smiled too."
    )
    world.say(f"In the end, {task.moral}")


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    task = _safe_lookup(TASKS, params.task)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting=setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.kind, trait=params.trait))
    keeper = world.add(Entity(id="Keeper", kind="character", type="elder", label="the keeper", trait="wise"))
    prize_ent = world.add(Entity(id="Prize", type=prize.type, label=prize.label, phrase=prize.phrase, owner=hero.id))

    world.facts.update(hero=hero, keeper=keeper, prize=prize_ent, task=task, setting=setting)

    story_intro(world, hero, task, prize_ent, keeper)
    story_middle(world, hero, task, prize_ent, keeper)
    story_turn(world, hero, task, prize_ent, keeper)
    story_surprise(world, hero, task, prize_ent, keeper)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short fable for a young child about {hero.id} and the clue "{task.clue}".',
        f"Tell an interactive-feeling story where a {hero.type} can notice a hint before a surprise about a {prize.label}.",
        f'Write a gentle fable with foreshadowing, a small worry, and a surprise ending using the word "{task.id}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    prize = _safe_fact(world, f, "prize")
    keeper = _safe_fact(world, f, "keeper")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.trait} little {hero.type}, and {keeper.label}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice before the surprise?",
            answer=f"{hero.id} noticed {task.clue}, which was a hint that something important was nearby.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about the {prize.label}?",
            answer=f"{hero.id} worried because going on too quickly could make the {prize.label} {prize.risk_meter}.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {task.surprise}.",
        ),
        QAItem(
            question=f"What did the story teach at the end?",
            answer=task.moral,
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a small clue early in a story that hints something important will happen later.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that often uses animals and ends with a lesson.",
        ),
        QAItem(
            question="Why can a surprise make a story fun?",
            answer="A surprise can make a story fun because it changes what the reader expects and makes the ending feel new.",
        ),
    ]


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
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


CURATED = [
    StoryParams(setting="orchard", task="pick", prize="berries", name="Milo", kind="fox", trait="curious"),
    StoryParams(setting="lantern_path", task="follow", prize="lantern", name="Ruby", kind="rabbit", trait="gentle"),
    StoryParams(setting="garden", task="water", prize="bouquet", name="Pip", kind="crow", trait="patient"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(" ", v)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
