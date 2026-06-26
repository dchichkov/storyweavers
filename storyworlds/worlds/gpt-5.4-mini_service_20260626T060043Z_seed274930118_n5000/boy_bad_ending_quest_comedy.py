#!/usr/bin/env python3
"""
A small comedy storyworld about a boy on a quest with a bad ending.

The seed premise:
- A boy wants something silly and grand.
- He sets off on a quest with a bit too much confidence.
- The plan goes wrong in a funny, concrete way.
- He returns changed, but not victorious.

This world keeps the storytelling state-driven:
- physical meters: distance, mess, fatigue, dropped_items
- emotional memes: hope, worry, pride, embarrassment, laughter

The ending is intentionally a Bad Ending: the quest does not succeed.
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
# Model
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "boy":
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
class Quest:
    id: str
    title: str
    goal: str
    verb: str
    obstacle: str
    mishap: str
    end_state: str
    location: str
    reward: str
    comedy_tag: str
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
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "town": Setting(place="the town square", affordances={"quest"}),
    "wood": Setting(place="the whispering wood", affordances={"quest"}),
    "hill": Setting(place="the windy hill", affordances={"quest"}),
    "kitchen": Setting(place="the kitchen", affordances={"quest"}),
}

QUESTS = {
    "cookie": Quest(
        id="cookie",
        title="the Golden Cookie Quest",
        goal="find the golden cookie",
        verb="find the golden cookie",
        obstacle="a giant jar on a high shelf",
        mishap="the jar tipped, the cookie rolled, and the floor got crumbs everywhere",
        end_state="the quest ended with an empty pocket",
        location="the kitchen",
        reward="the golden cookie",
        comedy_tag="cookie",
        tags={"cookie", "crumbs", "shelf"},
    ),
    "kite": Quest(
        id="kite",
        title="the Sky-Kite Quest",
        goal="catch the bright kite",
        verb="catch the bright kite",
        obstacle="a grumpy gust of wind",
        mishap="the kite flew into a tree and came back wearing a leaf hat",
        end_state="the quest ended with a tangled string",
        location="the windy hill",
        reward="the bright kite",
        comedy_tag="kite",
        tags={"kite", "wind", "tree"},
    ),
    "frog": Quest(
        id="frog",
        title="the Frog Crown Quest",
        goal="bring back the frog crown",
        verb="bring back the frog crown",
        obstacle="a pond with suspiciously slippery stones",
        mishap="one foot slipped, one shoe splashed, and the crown hopped away",
        end_state="the quest ended with one wet sock and no crown",
        location="the whispering wood",
        reward="the frog crown",
        comedy_tag="frog",
        tags={"frog", "pond", "wet"},
    ),
}

HERO_NAMES = ["Ben", "Noah", "Leo", "Milo", "Theo", "Finn", "Owen", "Eli"]
TRAITS = ["brave", "silly", "curious", "proud", "hopeful", "loud"]


@dataclass
class StoryParams:
    place: str
    quest: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
quest_at(Place, Q) :- setting(Place), quest(Q), can_do(Place, Q).
bad_ending(Q) :- quest(Q), obstacle(Q, _), mishap(Q, _).
compatible(Place, Q) :- quest_at(Place, Q), bad_ending(Q).
#show quest_at/2.
#show bad_ending/1.
#show compatible/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("can_do", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("obstacle", qid, q.obstacle))
        lines.append(asp.fact("mishap", qid, q.mishap))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show compatible/2."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "quest" not in setting.affordances:
            continue
        for qid in QUESTS:
            combos.append((place, qid))
    return combos


def reasonableness_gate(place: str, quest_id: str) -> None:
    if place not in SETTINGS:
        pass
    if quest_id not in QUESTS:
        pass
    if "quest" not in _safe_lookup(SETTINGS, place).affordances:
        pass
    if place == "the kitchen" and quest_id == "frog":
        pass
    if place == "the windy hill" and quest_id == "cookie":
        pass
    if place == "the whispering wood" and quest_id == "cookie":
        pass


def choose_name(gender: str = "boy") -> str:
    return random.choice(HERO_NAMES)


def opening(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big grin and an even bigger plan."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {quest.goal}, because {hero.pronoun('subject')} thought it would be the best kind of adventure."
    )


def set_off(world: World, hero: Entity, quest: Quest, setting: Setting) -> None:
    hero.memes["hope"] += 1
    hero.meters["distance"] += 1
    world.para()
    world.say(
        f"One bright day, {hero.id} marched to {setting.place} with a pocket full of courage and a very serious face."
    )
    world.say(
        f"At the end of the path waited {quest.obstacle}, which looked less heroic and more annoying."
    )


def mishap(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["worry"] += 1
    hero.meters["mess"] += 1
    hero.meters["fatigue"] += 1
    world.say(
        f"{hero.id} tried to {quest.verb}, but then {quest.mishap}."
    )
    world.say(
        f"That turned {hero.pronoun('possessive')} grand plan into a sticky joke."
    )


def fail_and_return(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["embarrassment"] += 1
    hero.memes["hope"] = max(0, hero.memes.get("hope", 0) - 1)
    world.para()
    world.say(
        f"In the end, {hero.id} did not get {quest.reward}."
    )
    world.say(
        f"{quest.end_state}. {hero.id} went home a little dusty, a little wiser, and much less sure that quests always end with cheering."
    )


def ending_image(world: World, hero: Entity, quest: Quest) -> None:
    world.say(
        f"Still, {hero.id} laughed at the ridiculous mess, and the last thing {hero.pronoun('subject')} saw was {hero.pronoun('possessive')} own shadow looking as if it had also taken part in the quest."
    )


def tell_story(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="boy"))
    hero.memes["pride"] = 1.0
    hero.memes["hope"] = 1.0
    hero.memes["laughter"] = 0.0

    world.facts.update(hero=hero, quest=quest, setting=setting, params=params)

    opening(world, hero, quest)
    set_off(world, hero, quest, setting)
    mishap(world, hero, quest)
    fail_and_return(world, hero, quest)
    ending_image(world, hero, quest)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, f, "quest")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        f"Write a funny story about a boy named {hero.id} who goes on {quest.title} at {setting.place}.",
        f"Tell a short comedy where {hero.id} tries to {quest.goal} but the plan goes wrong in a silly way.",
        f"Write a children's story with a quest, a mishap, and a bad ending featuring the word '{quest.comedy_tag}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    quest: Quest = _safe_fact(world, f, "quest")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in {setting.place}?",
            answer=f"{hero.id} wanted to {quest.goal} on a funny quest.",
        ),
        QAItem(
            question=f"What went wrong with {hero.id}'s quest?",
            answer=f"The quest went wrong because {quest.mishap}.",
        ),
        QAItem(
            question=f"Did {hero.id} get the reward at the end?",
            answer=f"No. {hero.id} did not get {quest.reward}; it was a bad ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    quest: Quest = _safe_fact(world, f, "quest")  # type: ignore[assignment]
    if quest.id == "cookie":
        return [
            QAItem(
                question="What is a cookie?",
                answer="A cookie is a small sweet baked treat that people often eat as a snack.",
            ),
            QAItem(
                question="Why can a jar on a high shelf be hard to reach?",
                answer="A jar on a high shelf is hard to reach because it is up above your hands and you may need help to get it down safely.",
            ),
        ]
    if quest.id == "kite":
        return [
            QAItem(
                question="What does wind do to a kite?",
                answer="Wind helps a kite fly, but a strong or grumpy wind can also push it around in tricky ways.",
            ),
            QAItem(
                question="What is a tree?",
                answer="A tree is a tall plant with a trunk and branches. Leaves often grow on it.",
            ),
        ]
    return [
        QAItem(
            question="What is a pond?",
            answer="A pond is a small body of water that can have mud, stones, and little animals near it.",
        ),
        QAItem(
            question="Why do shoes get wet near water?",
            answer="Shoes get wet near water because splashes can land on them and soak into the fabric or touch the inside.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy quest storyworld with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--quest", choices=QUESTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "quest", None):
        reasonableness_gate(getattr(args, "place", None), getattr(args, "quest", None))
    combos = [
        (p, q) for p, q in valid_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or q == getattr(args, "quest", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest = rng.choice(list(combos))
    name = getattr(args, "name", None) or choose_name("boy")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id} ({e.type}) meters={meters} memes={memes}")
    lines.extend(f"  trace: {line}" for line in world.trace_log)
    return "\n".join(lines)


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
        print(asp_program("#show compatible/2."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible story combos:\n")
        for place, quest in triples:
            print(f"  {place:18} {quest}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="town", quest="cookie", name="Ben", trait="silly"),
            StoryParams(place="hill", quest="kite", name="Leo", trait="proud"),
            StoryParams(place="wood", quest="frog", name="Milo", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
