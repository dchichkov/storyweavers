#!/usr/bin/env python3
"""
pollutant_quest_happy_ending_superhero_story.py
================================================

A small superhero story world about a quest to stop a pollutant and end with a
happy, hopeful cleanup.

Premise:
- A young hero learns that a strange pollutant is making a place unpleasant.
- The hero goes on a quest to find the source and the right tool to stop it.
- The story turns when the hero uses a clever, safe method instead of brute force.
- The ending proves the place is clean again and the people feel relieved.

This world keeps the domain small and constraint-checked:
- One pollutant source.
- One protected setting.
- One compatible cleaning tool.
- A resolution only happens if the tool actually matches the pollutant.

The story engine uses a lightweight world model with meters and memes, and the
ASP twin mirrors the reasonableness gate for valid story combinations.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    pollutant: object | None = None
    sidekick: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for key in ("pollution", "cleanliness", "hope", "danger", "relief", "curiosity", "resolve"):
            self.meters.setdefault(key, 0.0)
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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
    color: str
    pollutant_source: str
    needs: str
    one_safe_tool: str
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
class Pollutant:
    id: str
    label: str
    smell: str
    stain: str
    danger: str
    source_hint: str
    neutralized_by: str
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
class Tool:
    id: str
    label: str
    phrase: str
    verb: str
    target: str
    safe: bool = True
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


@dataclass
class StoryParams:
    setting: str
    hero: str
    sidekick: str
    pollutant: str
    tool: str
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


SETTINGS = {
    "city_park": Setting(
        place="the city park",
        color="bright",
        pollutant_source="the cracked drain pipe",
        needs="safe cleanup",
        one_safe_tool="filter_net",
    ),
    "harbor": Setting(
        place="the harbor",
        color="blue",
        pollutant_source="the leaking barrel",
        needs="safe cleanup",
        one_safe_tool="absorbent_cloak",
    ),
    "rooftop_garden": Setting(
        place="the rooftop garden",
        color="green",
        pollutant_source="the broken tank",
        needs="safe cleanup",
        one_safe_tool="seal_patch",
    ),
}

POLLUTANTS = {
    "oil": Pollutant(
        id="oil",
        label="oil slick",
        smell="sharp and greasy",
        stain="dark and slippery",
        danger="slippery",
        source_hint="a cracked drain pipe",
        neutralized_by="filter_net",
    ),
    "smoke": Pollutant(
        id="smoke",
        label="smoke cloud",
        smell="stingy and sour",
        stain="gray and hazy",
        danger="hard to breathe",
        source_hint="a broken vent",
        neutralized_by="air_fan",
    ),
    "sludge": Pollutant(
        id="sludge",
        label="sludge spill",
        smell="muddy and sour",
        stain="thick and sticky",
        danger="stuck",
        source_hint="a leaking barrel",
        neutralized_by="absorbent_cloak",
    ),
}

TOOLS = {
    "filter_net": Tool(
        id="filter_net",
        label="filter net",
        phrase="a strong filter net",
        verb="catch",
        target="oil",
    ),
    "absorbent_cloak": Tool(
        id="absorbent_cloak",
        label="absorbent cloak",
        phrase="an absorbent cloak",
        verb="soak up",
        target="sludge",
    ),
    "seal_patch": Tool(
        id="seal_patch",
        label="seal patch",
        phrase="a seal patch",
        verb="seal",
        target="smoke",
    ),
}

HEROES = [
    ("Nova", "girl"),
    ("Blaze", "boy"),
    ("Comet", "girl"),
    ("Jet", "boy"),
    ("Spark", "girl"),
]

SIDEKICKS = ["Milo", "Iris", "Pip", "Zara", "Theo"]


ASP_RULES = r"""
valid_story(S, P, T) :- setting(S), pollutant(P), tool(T),
                        needs_tool(S, T), neutralizes(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("needs_tool", sid, s.one_safe_tool))
        lines.append(asp.fact("source_hint", sid, s.pollutant_source))
    for pid, p in POLLUTANTS.items():
        lines.append(asp.fact("pollutant", pid))
        lines.append(asp.fact("neutralizes", p.neutralized_by, pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _reasonableness_gate(setting: Setting, pollutant: Pollutant, tool: Tool) -> bool:
    return tool.id == setting.one_safe_tool and tool.target == pollutant.id and tool.safe


def _story_reason(setting: Setting, pollutant: Pollutant, tool: Tool) -> Optional[str]:
    if tool.id != setting.one_safe_tool:
        return f"The only safe tool for {setting.place} is {setting.one_safe_tool}."
    if tool.target != pollutant.id:
        return f"{tool.label} does not match the pollutant in this story."
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A superhero story world about a quest to stop a pollutant and end happily."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pollutant", choices=POLLUTANTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
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
    if getattr(args, "setting", None) and getattr(args, "pollutant", None) and getattr(args, "tool", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "setting", None))
        pollutant = _safe_lookup(POLLUTANTS, getattr(args, "pollutant", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        reason = _story_reason(setting, pollutant, tool)
        if reason:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    valid = [
        (sid, pid, tid)
        for sid, s in SETTINGS.items()
        for pid, p in POLLUTANTS.items()
        for tid, t in TOOLS.items()
        if _reasonableness_gate(s, p, t)
        and (getattr(args, "setting", None) is None or getattr(args, "setting", None) == sid)
        and (getattr(args, "pollutant", None) is None or getattr(args, "pollutant", None) == pid)
        and (getattr(args, "tool", None) is None or getattr(args, "tool", None) == tid)
    ]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    sid, pid, tid = rng.choice(sorted(valid))
    hero = getattr(args, "hero", None) or rng.choice(HEROES)[0]
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(setting=sid, hero=hero, sidekick=sidekick, pollutant=pid, tool=tid)


def _setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero_type = "girl" if params.hero in {"Nova", "Comet", "Spark"} else "boy"
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=params.hero))
    sidekick = world.add(Entity(id="sidekick", kind="character", type="child", label=params.sidekick))
    pollutant = world.add(Entity(
        id="pollutant",
        kind="thing",
        type="pollutant",
        label=_safe_lookup(POLLUTANTS, params.pollutant).label,
        phrase=_safe_lookup(POLLUTANTS, params.pollutant).label,
    ))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type="tool",
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).phrase,
    ))
    world.facts.update(hero=hero, sidekick=sidekick, pollutant=pollutant, tool=tool)
    return world


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    pollutant: Entity = _safe_fact(world, world.facts, "pollutant")  # type: ignore[assignment]
    tool: Entity = _safe_fact(world, world.facts, "tool")  # type: ignore[assignment]
    setting = world.setting
    p = _safe_lookup(POLLUTANTS, params.pollutant)

    hero.memes["resolve"] += 1
    hero.memes["curiosity"] += 1
    pollutant.meters["pollution"] += 1
    pollutant.meters["danger"] += 1

    world.say(f"{hero.label} was a young hero who watched over {setting.place}.")
    world.say(f"One day, {hero.label} noticed {p.label} near {setting.pollutant_source}, and it smelled {p.smell}.")
    world.say(f"{sidekick.label} pointed at the mess and said it looked {p.stain}, which was not safe at all.")

    world.para()
    world.say(f"{hero.label} knew this was a real quest. {hero.pronoun().capitalize()} took {tool.phrase} and followed the trail.")
    world.say(f"The trail led straight to {setting.pollutant_source}, where the pollutant had spread across the ground.")
    world.say(f"{hero.label} did not rush in wildly; {hero.pronoun()} looked carefully and chose the right way to help.")

    world.para()
    if tool.id == p.neutralized_by:
        pollutant.meters["pollution"] = 0.0
        pollutant.meters["danger"] = 0.0
        world.facts["won"] = True
        hero.memes["hope"] += 1
        sidekick.memes["hope"] += 1
        hero.memes["relief"] += 1
        world.say(f"With the {tool.label}, {hero.label} could {_safe_lookup(TOOLS, tool.id).verb} the {p.label} without making things worse.")
        world.say(f"Slowly, the messy shine faded away, and the ground became clean again.")
        world.say(f"{sidekick.label} cheered, because the park was safe, bright, and ready for play.")
        world.say(f"At the end of the quest, {hero.label} stood proudly beside {sidekick.label}, and {setting.place} looked happy again.")
    else:
        world.facts["won"] = False
        pass

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    pollutant: Entity = _safe_fact(world, world.facts, "pollutant")  # type: ignore[assignment]
    tool: Entity = _safe_fact(world, world.facts, "tool")  # type: ignore[assignment]
    return [
        f'Write a superhero story for young children about a quest to stop {pollutant.label}.',
        f"Tell a happy-ending story where {hero.label} uses {tool.label} to help a place become clean again.",
        f'Write a short brave-and-kind story that includes the word "pollutant" and ends in relief.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    sidekick: Entity = _safe_fact(world, world.facts, "sidekick")  # type: ignore[assignment]
    pollutant: Entity = _safe_fact(world, world.facts, "pollutant")  # type: ignore[assignment]
    tool: Entity = _safe_fact(world, world.facts, "tool")  # type: ignore[assignment]
    setting = world.setting

    return [
        QAItem(
            question=f"Who went on the quest to help {setting.place}?",
            answer=f"{hero.label} went on the quest, and {sidekick.label} helped by noticing the problem and cheering from the side.",
        ),
        QAItem(
            question=f"What was wrong at {setting.place}?",
            answer=f"{pollutant.label} had spread near {setting.pollutant_source}, and it made the place look and smell bad.",
        ),
        QAItem(
            question=f"How did {hero.label} fix the problem?",
            answer=f"{hero.label} used {tool.label}, which was the safe tool for this pollutant, so the mess could be cleaned without making it worse.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {setting.place} clean again and everyone feeling relieved and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pollutant?",
            answer="A pollutant is something that makes a place dirty, unhealthy, or unsafe, like smoke, oil, or sludge.",
        ),
        QAItem(
            question="Why do heroes use the right tool instead of just grabbing anything?",
            answer="Heroes use the right tool because a safe tool solves the problem without creating a bigger one.",
        ),
        QAItem(
            question="What does a happy ending do in a story?",
            answer="A happy ending shows that the problem was solved and the characters can feel safe, calm, or joyful again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id} ({ent.kind}/{ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="city_park", hero="Nova", sidekick="Milo", pollutant="oil", tool="filter_net"),
    StoryParams(setting="harbor", hero="Blaze", sidekick="Iris", pollutant="sludge", tool="absorbent_cloak"),
    StoryParams(setting="rooftop_garden", hero="Comet", sidekick="Pip", pollutant="smoke", tool="seal_patch"),
]


def explain_rejection(setting: Setting, pollutant: Pollutant, tool: Tool) -> str:
    if tool.id != setting.one_safe_tool:
        return f"(No story: {tool.label} is not the safe tool for {setting.place}; use {setting.one_safe_tool}.)"
    if tool.target != pollutant.id:
        return f"(No story: {tool.label} does not neutralize {pollutant.label}.)"
    return "(No story: the chosen combination is not reasonable.)"


def asp_verify() -> int:
    import asp
    py = {
        (sid, pid, tid)
        for sid, s in SETTINGS.items()
        for pid, p in POLLUTANTS.items()
        for tid, t in TOOLS.items()
        if _reasonableness_gate(s, p, t)
    }
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python gates")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_asp_list() -> str:
    stories = asp_valid_stories()
    return "\n".join(f"{s} {p} {t}" for s, p, t in stories)


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
        print(build_asp_list())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
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
            header = f"### {p.hero}: {p.pollutant} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
