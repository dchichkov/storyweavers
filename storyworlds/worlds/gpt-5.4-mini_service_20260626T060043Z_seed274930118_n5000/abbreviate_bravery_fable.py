#!/usr/bin/env python3
"""
A small fable-like storyworld about abbreviating a message with bravery.

The seed tale behind this world:
- A little messenger hears that danger is coming to the village.
- The first warning is too long to shout in time.
- A wise elder tells the messenger to abbreviate it.
- The messenger finds the courage to speak plainly and save the day.

This world keeps the motion small and classical: a short road, a few animals,
one worried message, one brave choice, and a change you can see at the end.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

# ---------------------------------------------------------------------------
# World data model
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caregiver: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "owl", "lion", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"mouse", "hare", "rabbit", "squirrel", "sparrow"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "they"

    def name_word(self) -> str:
        return self.label or self.type
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
class Message:
    id: str
    kind: str
    long_text: str
    short_text: str
    risk: str
    keyword: str
    difficulty: float
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
class StoryParams:
    place: str
    message: str
    hero_type: str
    hero_name: str
    elder_type: str
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
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "market": Setting(place="the market square", afford={"warning", "crowd"}),
    "bridge": Setting(place="the narrow bridge", afford={"warning", "crowd"}),
    "gate": Setting(place="the village gate", afford={"warning", "crowd"}),
}

MESSAGES = {
    "storm": Message(
        id="storm",
        kind="storm",
        long_text="A big storm is coming from the east, so everyone should hurry home before the road floods",
        short_text="Storm coming, go home now",
        risk="flooding",
        keyword="storm",
        difficulty=1.0,
    ),
    "fire": Message(
        id="fire",
        kind="fire",
        long_text="There is smoke in the forest, and the village should leave the path before the fire leaps closer",
        short_text="Fire in the forest, leave the path",
        risk="burning",
        keyword="fire",
        difficulty=1.0,
    ),
    "fox": Message(
        id="fox",
        kind="trouble",
        long_text="The fox is near the henyard, and the chickens must be counted before he slips away",
        short_text="Fox near the hens",
        risk="loss",
        keyword="fox",
        difficulty=1.0,
    ),
}

HEROES = {
    "mouse": {"label": "a little mouse", "traits": {"small", "quick"}},
    "hare": {"label": "a young hare", "traits": {"small", "swift"}},
    "squirrel": {"label": "a small squirrel", "traits": {"small", "curious"}},
    "sparrow": {"label": "a sparrow", "traits": {"small", "bright"}},
}

ELDERS = {
    "owl": {"label": "an old owl", "traits": {"wise"}},
    "fox": {"label": "a calm fox", "traits": {"clever"}},
    "badger": {"label": "a steady badger", "traits": {"steady"}},
}

NAMES = {
    "mouse": ["Milo", "Mina", "Nib", "Pip"],
    "hare": ["Holly", "Hareta", "Nell", "Tess"],
    "squirrel": ["Sumi", "Tara", "Nim", "Roo"],
    "sparrow": ["Pia", "Wren", "Lia", "Tilly"],
}

TRAITS = ["brave", "shy", "careful", "kind"]


# ---------------------------------------------------------------------------
# Fable logic
# ---------------------------------------------------------------------------

def can_story(place: str, message: str, hero_type: str, elder_type: str) -> bool:
    return place in SETTINGS and message in MESSAGES and hero_type in HEROES and elder_type in ELDERS


def explain_rejection() -> str:
    return "(No story: the requested fable needs a place, a message, a hero, and a wise helper.)"


def build_briefing(world: World, hero: Entity, elder: Entity, msg: Message) -> None:
    world.say(
        f"{hero.label.capitalize()} lived near {world.setting.place} and carried news more often than meals."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had a serious heart and a small voice, but {hero.pronoun('possessive')} "
        f"feet were quick when work needed doing."
    )
    world.say(
        f"One morning, {hero.id} heard that {msg.long_text.lower()}."
    )
    hero.memes["duty"] += 1
    hero.memes["worry"] += 1
    world.facts["message"] = msg
    world.facts["hero"] = hero
    world.facts["elder"] = elder


def predict_too_long(world: World, hero: Entity, msg: Message) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters["breath"] = 1
    return len(msg.long_text) > 55


def warn_and_abbreviate(world: World, hero: Entity, elder: Entity, msg: Message) -> None:
    world.say(
        f"{hero.id} ran to {elder.label} and began the warning, but the words were too long and the road was too short."
    )
    if predict_too_long(world, hero, msg):
        world.say(
            f'{elder.label.capitalize()} blinked and said, "Abbreviate it. Keep the true heart, and cut the rest."'
        )
        hero.memes["doubt"] += 1
        hero.memes["hope"] += 1
        hero.meters["breath"] += 1


def speak_bravely(world: World, hero: Entity, elder: Entity, msg: Message) -> None:
    hero.memes["bravery"] += 1
    hero.meters["voice"] += 1
    world.say(
        f"{hero.id} took a breath, stood straighter, and found the courage to speak plainly."
    )
    world.say(
        f'"{msg.short_text}," {hero.id} called. "{msg.risk.capitalize()}!"'
    )
    world.say(
        f"The small voice did not wobble now. It sounded brief, clear, and brave."
    )


def resolution(world: World, hero: Entity, elder: Entity, msg: Message) -> None:
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["pride"] += 1
    elder.memes["approval"] += 1
    world.say(
        f"The villagers hurried home in time, and the trouble the warning named did not get the upper hand."
    )
    world.say(
        f"{elder.label.capitalize()} smiled at {hero.id}. \"A brave message does not need many words,\" {elder.pronoun()} said."
    )
    world.say(
        f"By evening, {hero.id} was no longer hiding behind longer and longer sentences; {hero.pronoun().capitalize()} was carrying truth cleanly across {world.setting.place}."
    )


def tell(setting: Setting, message: Message, hero_type: str, hero_name: str, elder_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        traits=list(_safe_lookup(HEROES, hero_type)["traits"]) + ["brave"],
        meters={"voice": 0.0, "breath": 0.0},
        memes={"worry": 0.0, "duty": 0.0, "bravery": 0.0, "fear": 1.0, "pride": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=_safe_lookup(ELDERS, elder_type)["label"],
        traits=list(_safe_lookup(ELDERS, elder_type)["traits"]),
        meters={},
        memes={"approval": 0.0},
    ))
    build_briefing(world, hero, elder, message)
    world.para()
    warn_and_abbreviate(world, hero, elder, message)
    world.para()
    speak_bravely(world, hero, elder, message)
    resolution(world, hero, elder, message)
    world.facts.update(hero=hero, elder=elder, message=message, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    elder: Entity = _safe_fact(world, world.facts, "elder")
    msg: Message = _safe_fact(world, world.facts, "message")
    return [
        f"Write a fable-like story for children where {hero.id} learns to abbreviate a long warning and acts bravely.",
        f"Tell a short story about {hero.id}, {elder.label}, and a message about {msg.keyword} that gets shorter and clearer.",
        "Write a gentle animal fable where bravery means speaking plainly instead of hiding behind too many words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    elder: Entity = _safe_fact(world, world.facts, "elder")
    msg: Message = _safe_fact(world, world.facts, "message")
    return [
        QAItem(
            question=f"Why did {elder.label} tell {hero.id} to abbreviate the warning?",
            answer=(
                f"{elder.label.capitalize()} told {hero.id} to abbreviate the warning because the long version was too slow to say in time. "
                f"The shorter message kept the important truth and left out the extra words."
            ),
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do at {world.setting.place}?",
            answer=(
                f"{hero.id} stood up, took a breath, and spoke the warning clearly. "
                f"{hero.pronoun().capitalize()} did not hide or whisper; {hero.pronoun()} gave the short message out loud."
            ),
        ),
        QAItem(
            question=f"What was the warning about?",
            answer=(
                f"The warning was about {msg.kind}: {msg.short_text.lower()}. "
                f"It meant {msg.risk}, so the villagers needed to move quickly."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"The villagers got home safely, and {hero.id} ended the day feeling braver. "
                f"The little messenger had learned that a short true sentence can be stronger than a long frightened one."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to abbreviate a word or message?",
            answer=(
                "To abbreviate means to make something shorter while keeping the part that matters. "
                "People do this when they want to say the idea more quickly or fit it into a small space."
            ),
        ),
        QAItem(
            question="What is bravery?",
            answer=(
                "Bravery is doing the right thing even when you feel nervous or scared. "
                "A brave creature still feels fear, but it keeps going anyway."
            ),
        ),
        QAItem(
            question="Why can short words help in an emergency?",
            answer=(
                "Short words can help in an emergency because they are faster to say and easier to hear. "
                "That can matter when everyone needs to act quickly."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(H) :- hero_type(H).
elder(E) :- elder_type(E).
place(P) :- setting(P).
message(M) :- message_type(M).

valid(P,M,H,E) :- setting(P), message_type(M), hero_type(H), elder_type(E).

needs_abbreviation(M) :- message_long(M,L), L > 55.
brave_choice(H) :- hero_brave(H).

good_story(P,M,H,E) :- valid(P,M,H,E), needs_abbreviation(M), brave_choice(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for m in MESSAGES.values():
        lines.append(asp.fact("message_type", m.id))
        lines.append(asp.fact("message_long", m.id, len(m.long_text)))
    for h in HEROES:
        lines.append(asp.fact("hero_type", h))
        lines.append(asp.fact("hero_brave", h))
    for e in ELDERS:
        lines.append(asp.fact("elder_type", e))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in SETTINGS:
        for m in MESSAGES:
            for h in HEROES:
                for e in ELDERS:
                    out.append((p, m, h, e))
    return out


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    expected = {(p, m, h, e) for p in SETTINGS for m in MESSAGES for h in HEROES for e in ELDERS}
    if cl == expected:
        print(f"OK: ASP gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in asp:", sorted(cl - expected))
    print("only in python:", sorted(expected - cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable about abbreviating with bravery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--message", choices=MESSAGES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--elder", choices=ELDERS)
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
    combos = [
        (p, m, h, e)
        for p in SETTINGS
        for m in MESSAGES
        for h in HEROES
        for e in ELDERS
        if (getattr(args, "place", None) is None or getattr(args, "place", None) == p)
        and (getattr(args, "message", None) is None or getattr(args, "message", None) == m)
        and (getattr(args, "hero", None) is None or getattr(args, "hero", None) == h)
        and (getattr(args, "elder", None) is None or getattr(args, "elder", None) == e)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, message, hero, elder = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, hero))
    return StoryParams(place=place, message=message, hero_type=hero, hero_name=hero_name, elder_type=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MESSAGES, params.message), params.hero_type, params.hero_name, params.elder_type)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="market", message="storm", hero_type="mouse", hero_name="Milo", elder_type="owl"),
    StoryParams(place="bridge", message="fire", hero_type="hare", hero_name="Holly", elder_type="badger"),
    StoryParams(place="gate", message="fox", hero_type="sparrow", hero_name="Pia", elder_type="fox"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} good story combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
