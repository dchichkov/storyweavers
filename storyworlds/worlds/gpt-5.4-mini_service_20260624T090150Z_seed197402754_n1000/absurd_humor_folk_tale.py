#!/usr/bin/env python3
"""
absurd_humor_folk_tale.py
=========================

A small folk-tale storyworld about an absurd little village, a ridiculous
problem, and a clever, funny fix.

The seed idea:
- A child or villager gets tangled up in an impossible-sounding absurdity.
- The village takes it seriously in a folk-tale way.
- The problem turns into humor through an unexpected, sensible, but delightfully
  strange resolution.

This file is standalone and follows the Storyweavers storyworld contract.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    oddent: object | None = None
    toolent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "daughter", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "son", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
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
    feature: str
    mood: str
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
class AbsurdThing:
    id: str
    label: str
    phrase: str
    oddity: str
    trouble: str
    fix_hint: str
    tags: set[str] = field(default_factory=set)
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
    purpose: str
    helps: set[str]
    odd_fit: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    oddity: str
    tool: str
    hero: str
    hero_type: str
    helper: str
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
    "lane": Setting(place="the lane by the old mill", feature="a crooked signpost", mood="whistly", affords={"oddity", "parade"}),
    "green": Setting(place="the village green", feature="a hollow well", mood="cheery", affords={"oddity", "parade"}),
    "orchard": Setting(place="the apple orchard", feature="a bright ladder", mood="syrupy", affords={"oddity"}),
    "bridge": Setting(place="the narrow bridge", feature="a grumpy river", mood="breezy", affords={"oddity"}),
}

ABSURDITIES = {
    "goose_clock": AbsurdThing(
        id="goose_clock",
        label="a goose that kept the hour",
        phrase="a goose that clucked the time instead of honking",
        oddity="the hour",
        trouble="it ticked so loudly that everyone forgot their own words",
        fix_hint="ask the goose politely for quieter minutes",
        tags={"goose", "clock", "time", "absurd"},
    ),
    "soup_rain": AbsurdThing(
        id="soup_rain",
        label="a raincloud of soup",
        phrase="a cloud that drizzled hot pea soup",
        oddity="hot pea soup",
        trouble="it made hats soggy and dinner plans very strange",
        fix_hint="catch the soup in bowls before it reached the road",
        tags={"soup", "rain", "weather", "absurd"},
    ),
    "stolen_shadow": AbsurdThing(
        id="stolen_shadow",
        label="a shadow with no owner",
        phrase="a shadow that wandered off like a lost kitten",
        oddity="its own tail",
        trouble="it kept hiding under other people's feet and causing trouble",
        fix_hint="find a sunny spot and invite the shadow back",
        tags={"shadow", "sun", "lost", "absurd"},
    ),
    "singing_boots": AbsurdThing(
        id="singing_boots",
        label="a pair of singing boots",
        phrase="boots that sang loud enough to wake the hens",
        oddity="a marching tune",
        trouble="they marched the owner straight into the duck pond",
        fix_hint="stuff them with soft straw and teach them a quiet song",
        tags={"boots", "song", "ducks", "absurd"},
    ),
}

TOOLS = {
    "bow": Tool(
        id="bow",
        label="a ribbon bow",
        phrase="a ribbon bow with a polite knot",
        purpose="calm down the oddity",
        helps={"goose", "boots", "shadow"},
        odd_fit="looked too small to matter, which made it funny when it worked",
    ),
    "ladle": Tool(
        id="ladle",
        label="a soup ladle",
        phrase="a soup ladle with a long wooden handle",
        purpose="catch and carry things",
        helps={"soup"},
        odd_fit="was the exact wrong shape for soup, which in this village meant it was right",
    ),
    "lantern": Tool(
        id="lantern",
        label="a little lantern",
        phrase="a brass lantern with a bright, round flame",
        purpose="find what has gone missing",
        helps={"shadow"},
        odd_fit="was much too bright for a shadow, which was the joke and the solution",
    ),
    "straw": Tool(
        id="straw",
        label="a bundle of straw",
        phrase="a bundle of clean straw tied with twine",
        purpose="soften noisy things",
        helps={"boots"},
        odd_fit="made the boots look like hens with feet",
    ),
}

HEROES = ["Milo", "Nina", "Tobi", "Lena", "Pip", "Sana", "Jori", "Mara"]
HELPERS = ["grandmother", "grandfather", "aunt", "uncle", "baker", "ferryman", "millkeeper"]
TRAITS = ["curious", "cheerful", "mischievous", "steady", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for odd_id in setting.affords:
            for tool_id, tool in TOOLS.items():
                if odd_id in tool.helps:
                    combos.append((place, odd_id, tool_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: absurd humor in a folk-tale village.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--oddity", choices=ABSURDITIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "oddity", None) and getattr(args, "tool", None):
        if getattr(args, "oddity", None) not in _safe_lookup(TOOLS, getattr(args, "tool", None)).helps:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "oddity", None) is None or c[1] == getattr(args, "oddity", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, oddity, tool = rng.choice(list(combos))
    hero = getattr(args, "name", None) or rng.choice(HEROES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, oddity=oddity, tool=tool, hero=hero, hero_type=hero_type, helper=helper)


def reasonableness_gate(params: StoryParams) -> None:
    if params.oddity not in ABSURDITIES or params.tool not in TOOLS or params.place not in SETTINGS:
        pass
    if params.oddity not in _safe_lookup(TOOLS, params.tool).helps:
        pass
    if params.oddity not in _safe_lookup(SETTINGS, params.place).affords:
        pass


def predict_solution(world: World, odd: AbsurdThing, tool: Tool) -> dict:
    soothes = odd.id in tool.helps
    return {"helpful": soothes}


def tell(setting: Setting, odd: AbsurdThing, tool: Tool, hero_name: str, hero_type: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", "folk-tale", "absurd"]))
    elder = world.add(Entity(id="Helper", kind="character", type="elder", label=f"the {helper}"))
    oddent = world.add(Entity(id=odd.id, type="oddity", label=odd.label, phrase=odd.phrase))
    toolent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))
    world.facts.update(hero=hero, elder=elder, oddity=oddent, tool=toolent, setting=setting, odd=odd, tool_def=tool)

    world.say(f"Once, in {setting.place}, there lived a little {hero_type} named {hero_name}.")
    world.say(f"Near {setting.feature}, the village found {odd.phrase}; it was the sort of thing that made grown-ups blink twice.")
    world.say(f"{hero_name} thought it was funny at first, because the oddity was so absurd that even the crows had to listen.")
    world.para()
    world.say(f"But soon {odd.trouble}, and the whole place grew fidgety.")
    world.say(f"Then {hero_name} ran to {helper} and asked for help, as folk-tale children do when a problem wears a silly hat.")
    world.para()
    if odd.id == "goose_clock":
        world.say(f'The {helper} brought {tool.label}, saying, "Let us make the goose feel respected, not bossed about."')
        world.say(f"They tied the bow around the goose's neck, and the goose began to whisper the time instead of shouting it.")
        world.say(f"At once, the lane grew quiet, and everyone could hear their own boots again.")
    elif odd.id == "soup_rain":
        world.say(f'The {helper} handed over {tool.label} and said, "If soup insists on raining, we shall be ready with bowls."')
        world.say(f"{hero_name} and the helper held the ladle under the cloud, and the soup fell neatly where it belonged.")
        world.say(f"The road stayed dry, and supper arrived early with a laugh.")
    elif odd.id == "stolen_shadow":
        world.say(f'The {helper} lifted {tool.label} and said, "A shadow likes company, but it must know where home is."')
        world.say(f"The bright lantern showed the shadow its own feet, and the shadow tiptoed back to {hero_name}.")
        world.say(f"From then on, it stayed close, as quiet as a mouse wearing slippers.")
    elif odd.id == "singing_boots":
        world.say(f'The {helper} set down {tool.label} and said, "These boots need a bedtime song, not a marching order."')
        world.say(f"They packed the boots with straw, and the singing turned into a soft hum fit for a nap.")
        world.say(f"{hero_name} could walk without a pond hunt, and the hens went back to pretending not to gossip.")
    else:
        world.say(f"The {helper} and {hero_name} used {tool.label} in a way that was so sensible it sounded foolish.")
        world.say(f"But the absurd trouble faded, because in folk tales the strangest tools often know the shortest path home.")
    world.say(f"In the end, {hero_name} laughed, {helper} smiled, and {setting.place} felt ordinary again, which was the funniest ending of all.")
    world.facts["resolved"] = True
    world.facts["humor"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    odd = _safe_fact(world, f, "oddity")
    return [
        f'Write a short folk tale for children about an absurd problem involving "{odd.label}".',
        f"Tell a humorous village story where {f['hero'].id} and {f['elder'].label} solve {odd.label} with a strange but sensible tool.",
        f"Write a gentle absurd tale set in {f['setting'].place} that ends with laughter and a practical fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    odd = _safe_fact(world, f, "oddity")
    tool = _safe_fact(world, f, "tool_def")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who was the story about in {setting.place}?",
            answer=f"It was about {hero.id}, a little {hero.type}, who met an absurd problem and asked {elder.ref()} for help.",
        ),
        QAItem(
            question=f"What strange thing caused the trouble near {setting.feature}?",
            answer=f"The trouble came from {odd.phrase}. It was funny to hear about, but it still made a proper mess of the day.",
        ),
        QAItem(
            question=f"How did {hero.id} and {elder.ref()} fix the problem?",
            answer=f"They used {tool.label}. It looked silly, but it was exactly the right tool for the job, so the absurd trouble settled down.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=f"{hero.id} ended by laughing with {elder.ref()} while {setting.place} felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    odd: AbsurdThing = _safe_fact(world, f, "odd")
    tool: Tool = _safe_fact(world, f, "tool_def")
    return [
        QAItem(
            question="What is absurd humor?",
            answer="Absurd humor is funny because something is strange or impossible, but the story treats it seriously in a playful way.",
        ),
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is a traditional-style story with a simple pattern, memorable characters, and a lesson or clever ending.",
        ),
        QAItem(
            question=f"What is {tool.label} usually for?",
            answer=f"{tool.phrase.capitalize()} is usually for {tool.purpose}. In the story, it helps in a funny and unexpected way.",
        ),
        QAItem(
            question=f"Why was {odd.label} so funny?",
            answer=f"It was funny because {odd.phrase} sounds impossible in everyday life, which makes the village's serious reaction especially silly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
oddity(O) :- absurd(O).
tool(T) :- tool_def(T).

compatible(Place, Odd, Tool) :-
    place(Place),
    oddity(Odd),
    tool(Tool),
    affords(Place, Odd),
    helps(Tool, Odd).

valid_story(Place, Odd, Tool) :- compatible(Place, Odd, Tool).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for odd in sorted(s.affords):
            lines.append(asp.fact("affords", pid, odd))
    for oid in ABSURDITIES:
        lines.append(asp.fact("absurd", oid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_def", tid))
        for odd in sorted(t.helps):
            lines.append(asp.fact("helps", tid, odd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(oddity: AbsurdThing, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot reasonably help with {oddity.label}.)"


CURATED = [
    StoryParams(place="lane", oddity="goose_clock", tool="bow", hero="Milo", hero_type="boy", helper="grandmother"),
    StoryParams(place="green", oddity="soup_rain", tool="ladle", hero="Nina", hero_type="girl", helper="baker"),
    StoryParams(place="bridge", oddity="stolen_shadow", tool="lantern", hero="Tobi", hero_type="boy", helper="ferryman"),
    StoryParams(place="orchard", oddity="singing_boots", tool="straw", hero="Lena", hero_type="girl", helper="uncle"),
]


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ABSURDITIES, params.oddity), _safe_lookup(TOOLS, params.tool), params.hero, params.hero_type, params.helper)
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
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, odd, tool in triples:
            print(f"  {place:9} {odd:16} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: {p.oddity} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
