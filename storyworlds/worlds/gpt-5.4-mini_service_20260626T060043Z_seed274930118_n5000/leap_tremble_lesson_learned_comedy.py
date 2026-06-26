#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/leap_tremble_lesson_learned_comedy.py
===============================================================================================================

A small comedy storyworld about a character who wants to leap, causes a tremble,
and learns a lesson the funny way.

The seed image:
---
A cheerful little raccoon named Pip wanted to leap over a stack of boxes in the
garage. The boxes trembled, the lamp wobbled, and a cookie tin rolled across the
floor with a loud clink-clink-clink. After the funny chaos, Pip learned that
looking first is better than leaping first.

This world turns that premise into a tiny simulation:
- physical state: balance, wobble, clutter, rescued items
- emotional state: pride, alarm, laugh, lesson learned
- comedy tone: silly mishaps, harmless surprise, a clear lesson learned ending
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
    wearer: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
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
    place: str = "the garage"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    noise: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    fragile: bool = True
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
class StoryParams:
    setting: str
    action: str
    prize: str
    name: str
    species: str
    helper: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

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
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "garage": Setting(place="the garage", afford={"leap"}),
    "yard": Setting(place="the yard", afford={"leap"}),
    "stage": Setting(place="the play stage", afford={"leap"}),
}

ACTIONS = {
    "leap_boxes": Action(
        id="leap_boxes",
        verb="leap over the boxes",
        gerund="leaping over the boxes",
        rush="spring at the stack of boxes",
        effect="trembled",
        noise="boing",
        keyword="leap",
    ),
    "leap_puddle": Action(
        id="leap_puddle",
        verb="leap across the puddle",
        gerund="leaping across the puddle",
        rush="hop for the puddle",
        effect="trembled",
        noise="splish",
        keyword="leap",
    ),
    "leap_drum": Action(
        id="leap_drum",
        verb="leap onto the drum",
        gerund="leaping onto the drum",
        rush="bound toward the drum",
        effect="trembled",
        noise="bomp",
        keyword="leap",
    ),
}

PRIZES = {
    "cookie_tin": Prize(label="cookie tin", phrase="a shiny cookie tin"),
    "hat": Prize(label="hat", phrase="a crooked party hat"),
    "stack": Prize(label="stack of books", phrase="a stack of careful books", plural=True),
}

NAMES = ["Pip", "Milo", "Nina", "Ruby", "Otto", "Luna", "Mabel", "Toby"]
SPECIES = ["raccoon", "fox", "cat", "bear", "rabbit"]
HELPERS = ["parent", "big sister", "grandpa", "teacher"]
TRAITS = ["cheerful", "silly", "bouncy", "curious", "playful"]


def add_meter(ent: Entity, key: str, amount: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def add_meme(ent: Entity, key: str, amount: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return action.id in {"leap_boxes", "leap_puddle", "leap_drum"} and prize.fragile


def select_lesson(action: Action, prize: Prize) -> bool:
    return prize_at_risk(action, prize)


ASP_RULES = r"""
at_risk(A,P) :- action(A), prize(P), fragile(P), leap_action(A).
lesson(A,P) :- at_risk(A,P).
valid_story(S,A,P) :- setting(S), action(A), prize(P), at_risk(A,P), lesson(A,P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("leap_action", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if p.fragile:
            lines.append(asp.fact("fragile", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for aid in setting.afford:
            for pid in PRIZES:
                if select_lesson(_safe_lookup(ACTIONS, aid), _safe_lookup(PRIZES, pid)):
                    combos.append((sid, aid, pid))
    return combos


def asp_verify() -> int:
    import asp

    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a leap, a tremble, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "action", None):
        combos = [c for c in combos if c[1] == getattr(args, "action", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, action, prize = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        action=action,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        species=getattr(args, "species", None) or rng.choice(SPECIES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def _tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    action = _safe_lookup(ACTIONS, params.action)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.species, meters={}, memes={}))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}", meters={}, memes={}))
    prize = world.add(Entity(id="Prize", type=params.prize, label=prize_cfg.label, phrase=prize_cfg.phrase, plural=prize_cfg.plural, owner=hero.id, meters={}, memes={}))

    add_meme(hero, "joy", 1)
    add_meme(hero, "pride", 1)
    world.say(f"{hero.id} was a {params.trait} {hero.type} who loved silly little tricks.")
    world.say(f"{hero.pronoun().capitalize()} wanted to {action.verb}, and {action.noise} felt like the funniest sound in the world.")
    world.say(f"One day, {params.helper} brought home {prize.phrase}, and {hero.id} smiled at it like it was a treasure.")

    world.para()
    world.say(f"At {setting.place}, {hero.id} got a big idea.")
    world.say(f"{hero.pronoun().capitalize()} tried to {action.rush}, but the floor was not nearly as steady as it looked.")

    add_meter(hero, "balance", 1)
    add_meter(world.get("Prize"), "wiggle", 1)
    add_meter(hero, "wobble", 1)
    add_meme(hero, "alarm", 1)

    if prize_at_risk(action, prize_cfg):
        add_meter(world.get("Prize"), "tremble", 1)
        add_meme(helper, "surprise", 1)
        world.say(f"The {prize.label} {action.effect} and gave a tiny {action.noise}-clink as it skidded.")
        world.say(f"Even the air seemed to tremble for a second, which was very dramatic for such a small mess.")

    world.para()
    world.say(f"{params.helper.capitalize()} blinked, then laughed before anyone could be grumpy.")
    world.say(f'"Maybe," said {params.helper}, "we should look first and leap second."')
    add_meme(hero, "embarrassment", 1)
    add_meme(hero, "understanding", 1)

    world.say(f"{hero.id} rubbed {hero.pronoun('possessive')} nose and nodded. That was a good lesson, and also a funny one.")
    world.say(f"So {hero.id} picked up the {prize.label}, checked the floor, and made a much smaller leap that did not make anything tremble.")
    add_meme(hero, "lesson_learned", 1)
    world.say(f"After that, {hero.id} grinned and said, 'First look, then leap!' and {params.helper} laughed so hard they nearly snorted.")

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        action=action,
        setting=setting,
        lesson=True,
        tremble=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        f'Write a short comedy story for a child about a {hero.type} who wants to {action.verb}.',
        f'Tell a funny story where {hero.id} makes the {prize.label} tremble and learns to look first.',
        f'Write a playful lesson-learned story using the words "leap" and "tremble".',
        f'Create a tiny comedic tale about {hero.id} and {helper.label} with a happy lesson at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    action: Action = _safe_fact(world, f, "action")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"What did {hero.id} want to do at {setting.place}?",
            answer=f"{hero.id} wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} during the funny part?",
            answer=f"The {prize.label} {action.effect}, and that made the scene silly and a little bouncy.",
        ),
        QAItem(
            question=f"Who helped {hero.id} learn the lesson?",
            answer=f"{helper.label.capitalize()} helped {hero.id} learn to look first and leap second.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that it is better to look first and leap second.",
        ),
    ]


KNOWLEDGE = [
    QAItem(
        question="What does it mean to leap?",
        answer="To leap means to jump quickly through the air.",
    ),
    QAItem(
        question="What does tremble mean?",
        answer="To tremble means to shake a little, often because something is wobbly or surprising.",
    ),
    QAItem(
        question="Why can comedy stories be fun?",
        answer="Comedy stories are fun because they use silly trouble, playful surprises, and happy endings.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garage", action="leap_boxes", prize="cookie_tin", name="Pip", species="raccoon", helper="parent", trait="cheerful"),
    StoryParams(setting="yard", action="leap_puddle", prize="hat", name="Milo", species="rabbit", helper="big sister", trait="silly"),
    StoryParams(setting="stage", action="leap_drum", prize="stack", name="Nina", species="fox", helper="teacher", trait="playful"),
]


def generate(params: StoryParams) -> StorySample:
    world = _tell(params)
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


def asp_verify_and_print() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_and_print())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print(" ", item)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.action} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
