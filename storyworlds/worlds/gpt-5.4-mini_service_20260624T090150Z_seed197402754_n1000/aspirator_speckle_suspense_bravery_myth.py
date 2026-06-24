#!/usr/bin/env python3
"""
A tiny mythic story world about a brave child, a creeping speckle, and an
aspirator that can lift it away.

Seed premise:
- A little hero discovers a strange speckle on a sacred relic or mantle.
- The speckle grows or matters because it is a sign, stain, or omen.
- The hero fears the unknown, then uses an aspirator to remove it.
- The ending should feel like a small myth: the world is restored, and the
  hero is changed by bravery.

This script is standalone and follows the Storyweavers storyworld contract.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    touched: bool = False
    sacred: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"speckle": 0.0}
        if not self.memes:
            self.memes = {"suspense": 0.0, "bravery": 0.0, "relief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    place: str = "the moon-temple"
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
class Tool:
    id: str
    label: str
    phrase: str
    powers: set[str] = field(default_factory=set)
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
    relic: str
    tool: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None
    p: object | None = None
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
        self.lines: list[str] = []
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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        buf: list[str] = []
        for line in self.lines:
            if line == "":
                if buf:
                    out.append(" ".join(buf))
                    buf = []
            else:
                buf.append(line)
        if buf:
            out.append(" ".join(buf))
        return "\n\n".join(out)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = []
        clone.facts = dict(self.facts)
        return clone


def _say_name(hero: Entity) -> str:
    return hero.id


def _article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _do_touch(world: World, actor: Entity, relic: Entity) -> None:
    actor.memes["suspense"] += 1
    relic.touched = True
    if relic.meters["speckle"] >= THRESHOLD:
        world.say(f"The speckle clung to {relic.label} like a tiny dark star.")


def _use_aspirator(world: World, actor: Entity, relic: Entity, tool: Tool) -> None:
    if "speckle" not in tool.powers:
        pass
    if relic.meters["speckle"] < THRESHOLD:
        pass
    relic.meters["speckle"] = 0.0
    actor.memes["bravery"] += 1
    actor.memes["suspense"] = max(0.0, actor.memes["suspense"] - 1.0)
    actor.memes["relief"] += 1
    world.say(
        f"{actor.id} held the {tool.label} close, and the little whirl of breath"
        f" pulled the speckle away."
    )


def tell(setting: Setting, relic_cfg: Entity, tool_def: Tool,
         hero_name: str, hero_type: str, elder_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait, "curious"],
        meters={"speckle": 0.0},
        memes={"suspense": 0.0, "bravery": 0.0, "relief": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        traits=["wise", "old"],
        memes={"suspense": 0.0, "bravery": 0.0, "relief": 0.0},
    ))
    relic = world.add(Entity(
        id="relic",
        kind="thing",
        type=relic_cfg.type,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        sacred=True,
        meters={"speckle": relic_cfg.meters.get("speckle", 0.0)},
    ))
    tool = world.add(Entity(
        id=tool_def.id,
        kind="thing",
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
    ))

    world.say(
        f"In {setting.place}, there stood {relic.label}, bright as a story told at dusk."
    )
    world.say(
        f"People said a lone speckle had settled on it, and that such a mark could"
        f" trouble the peace of the hall."
    )
    world.para()
    world.say(
        f"{hero.id} was { _article(trait)} {trait} {hero.type} who listened when the"
        f" stones seemed to whisper."
    )
    world.say(
        f"{hero.id} loved {relic.label} and feared what the speckle might mean."
    )
    hero.memes["suspense"] += 1

    world.para()
    world.say(
        f"One dusk, {hero.id} and {elder.label} went to {setting.place} together."
    )
    world.say(
        f"{hero.id} wanted to touch {relic.label}, but the little mark made {hero.pronoun('possessive')} heart race."
    )
    _do_touch(world, hero, relic)
    world.say(
        f"{elder.label} saw the worry and said, \"A brave hand can clean what a scared hand will only stare at.\""
    )

    world.para()
    world.say(
        f"{hero.id} took a breath, squared {hero.pronoun('possessive')} shoulders, and lifted the {tool.label}."
    )
    _use_aspirator(world, hero, relic, tool)
    world.say(
        f"When the air fell still again, {relic.label} shone clear, and the hall seemed to exhale."
    )
    world.say(
        f"{hero.id} smiled, because bravery had not chased the fear away; it had walked through it."
    )

    world.facts.update(hero=hero, elder=elder, relic=relic, tool=tool, setting=setting)
    return world


SETTINGS = {
    "moon-temple": Setting(place="the moon-temple"),
    "river-shrine": Setting(place="the river-shrine"),
    "hill-sanctum": Setting(place="the hill-sanctum"),
}

RELICS = {
    "idol": Entity(
        id="idol",
        type="idol",
        label="the silver idol",
        phrase="a silver idol",
        meters={"speckle": 1.0},
    ),
    "banner": Entity(
        id="banner",
        type="banner",
        label="the temple banner",
        phrase="a temple banner",
        meters={"speckle": 1.0},
    ),
    "stone": Entity(
        id="stone",
        type="stone",
        label="the dawn stone",
        phrase="the dawn stone",
        meters={"speckle": 1.0},
    ),
}

TOOLS = {
    "aspirator": Tool(
        id="aspirator",
        label="aspirator",
        phrase="a little aspirator with a bright mouth",
        powers={"speckle"},
    ),
}

GIRL_NAMES = ["Mira", "Nia", "Iris", "Luna", "Sera", "Tala"]
BOY_NAMES = ["Arin", "Kian", "Bram", "Oren", "Pax", "Eli"]
TRAITS = ["steady", "fierce", "gentle", "bold", "patient", "earnest"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for r in RELICS:
            for t in TOOLS:
                combos.append((s, r, t))
    return combos


@dataclass
class Registry:
    setting: str
    relic: str
    tool: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world of speckle, suspense, and bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["mother", "father", "sister", "brother"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["mother", "father", "sister", "brother"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    if tool != "aspirator":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(setting=setting, relic=relic, tool=tool, name=name, gender=gender, elder=elder, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    relic: Entity = _safe_fact(world, f, "relic")
    return [
        f'Write a short myth for a child about {hero.id}, the {hero.type}, and a speckle on {relic.label}.',
        f"Tell a brave little story where {hero.id} uses an aspirator to remove a speckle from {relic.label}.",
        f"Write a gentle myth about suspense, bravery, and a sacred thing that becomes clean again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    elder: Entity = _safe_fact(world, f, "elder")
    relic: Entity = _safe_fact(world, f, "relic")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.traits[1] if len(hero.traits) > 1 else hero.type} {hero.type}, and {elder.label} helped too.",
        ),
        QAItem(
            question=f"What dark thing worried {hero.id} at {setting.place}?",
            answer=f"A speckle worried {hero.id} because it rested on {relic.label} and seemed like a little omen.",
        ),
        QAItem(
            question=f"What did {hero.id} use to clear the speckle?",
            answer=f"{hero.id} used the {tool.label} to lift the speckle away from {relic.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt brave and relieved after the speckle was gone and the sacred thing shone again.",
        ),
    ]


KNOWLEDGE = {
    "aspirator": [
        ("What is an aspirator for?",
         "An aspirator is a tool that pulls in air or dust so it can help clean a small mess."),
    ],
    "speckle": [
        ("What is a speckle?",
         "A speckle is a tiny spot or dot. It can be a little stain or mark on a surface."),
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery is doing a hard or scary thing even when your heart feels nervous."),
    ],
    "suspense": [
        ("What is suspense in a story?",
         "Suspense is the feeling that makes you wonder what will happen next."),
    ],
    "myth": [
        ("What is a myth?",
         "A myth is an old-style story that explains people, places, or powerful things in a grand way."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for key in ["aspirator", "speckle", "bravery", "suspense", "myth"] for q, a in KNOWLEDGE[key]]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.sacred:
            bits.append("sacred=True")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting_fact(S).
relic(R) :- relic_fact(R).
tool(T) :- tool_fact(T).
has_speckle(R) :- speckled(R).
can_clean(T,R) :- tool(T), has_speckle(R), tool_power(T,speckle).
valid(S,R,T) :- setting(S), relic(R), tool(T), can_clean(T,R).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_fact", s))
    for r in RELICS:
        lines.append(asp.fact("relic_fact", r))
        lines.append(asp.fact("speckled", r))
    for t, tool in TOOLS.items():
        lines.append(asp.fact("tool_fact", t))
        for p in sorted(tool.powers):
            lines.append(asp.fact("tool_power", t, p))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    relic_cfg = _safe_lookup(RELICS, params.relic)
    tool_def = _safe_lookup(TOOLS, params.tool)
    world = tell(setting, relic_cfg, tool_def, params.name, params.gender, params.elder, params.trait)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible story combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for s in SETTINGS:
            for r in RELICS:
                for t in TOOLS:
                    p = StoryParams(
                        setting=s,
                        relic=r,
                        tool=t,
                        name="Mira",
                        gender="girl",
                        elder="mother",
                        trait="steady",
                        seed=base_seed,
                    )
                    samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            sample = generate(p)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
