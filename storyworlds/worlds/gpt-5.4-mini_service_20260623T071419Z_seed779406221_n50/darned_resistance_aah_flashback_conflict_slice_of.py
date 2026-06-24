#!/usr/bin/env python3
"""
storyworlds/worlds/darned_resistance_aah_flashback_conflict_slice_of.py
======================================================================

A standalone slice-of-life storyworld about a child, a picky piece of clothing,
a small flashback, and a gentle conflict that ends in a compromise.

Seed words and narrative instruments:
- darned
- resistance
- aah
- Flashback
- Conflict

Initial tale idea:
---
On a windy morning, a child did not want to wear the darned new scarf. It felt
scratchy and made a grumpy face with its wool. The parent said they needed it for
the cold walk to the shop, but the child pushed back and said, "Aah, no!"
Then the child remembered a flashback: last winter, a kind grandma had knitted
the scarf and laughed when the yarn tickled their nose. That memory softened the
child's resistance. Together they found a way to make the scarf feel better, and
the child went out warm, proud, and less grumpy.

This world models:
- a cold walk where bare necks get chilly
- a scratchy scarf that raises resistance
- a flashback that lowers resistance and adds love
- a parent-child conflict that resolves through a small, child-sized fix
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    warm: bool = False
    scratchy: bool = False
    soft: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    scarf_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
class Weather:
    label: str
    cold: bool = False
    windy: bool = False
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Clothing:
    id: str
    label: str
    phrase: str
    warms: set[str] = field(default_factory=set)
    comfort_fix: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, weather: Weather) -> None:
        self.weather = weather
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
        w = World(self.weather)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_cold(world: World) -> list[str]:
    out = []
    child = world.get("child")
    scarf = world.get("scarf")
    if not scarf.worn_by or scarf.worn_by != child.id:
        return out
    if not world.weather.cold:
        return out
    if child.meters["bare_neck"] < THRESHOLD:
        return out
    sig = ("cold", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["grumpy"] += 1
    out.append("The wind found the child's neck and made the walk feel colder.")
    return out


def _r_conflict(world: World) -> list[str]:
    child = world.get("child")
    parent = world.get("parent")
    if child.memes["resistance"] < THRESHOLD:
        return []
    sig = ("conflict", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["conflict"] += 1
    parent.memes["worry"] += 1
    return ["__CONFLICT__"]


def _r_flashback(world: World) -> list[str]:
    child = world.get("child")
    scarf = world.get("scarf")
    if child.memes["conflict"] < THRESHOLD or child.memes["memory"] < THRESHOLD:
        return []
    sig = ("flashback", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["resistance"] = max(0.0, child.memes["resistance"] - 1.5)
    child.memes["love"] += 1
    scarf.meters["meaning"] += 1
    return ["__FLASHBACK__"]


RULES = [
    Rule(name="cold", apply=_r_cold),
    Rule(name="conflict", apply=_r_conflict),
    Rule(name="flashback", apply=_r_flashback),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            res = rule.apply(world)
            if res:
                changed = True
                out.extend([r for r in res if not r.startswith("__")])
    if narrate:
        for line in out:
            world.say(line)
    return out


def assess_need(child: Entity, weather: Weather) -> bool:
    return weather.cold and weather.windy and child.meters["bare_neck"] >= THRESHOLD


def comfort_fix_for(scarf: Clothing) -> bool:
    return "soft_lining" in scarf.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for weather_id, weather in WEATHER.items():
        for scarf_id, scarf in SCARVES.items():
            if weather.cold and scarf.comfort_fix:
                combos.append((weather_id, scarf_id))
    return combos


@dataclass
class StoryParams:
    weather: str
    scarf: str
    child_name: str
    child_type: str
    parent_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


WEATHER = {
    "windy_morning": Weather(label="a windy morning", cold=True, windy=True),
    "cool_afternoon": Weather(label="a cool afternoon", cold=True, windy=False),
    "mild_day": Weather(label="a mild day", cold=False, windy=False),
}

SCARVES = {
    "darned_scarf": Clothing(
        id="darned_scarf",
        label="the darned new scarf",
        phrase="a darned new scarf",
        warms={"neck"},
        comfort_fix="soft lining",
        tags={"soft_lining", "scarves", "warm"},
    ),
    "striped_scarf": Clothing(
        id="striped_scarf",
        label="the striped scarf",
        phrase="a striped scarf",
        warms={"neck"},
        comfort_fix="longer tag",
        tags={"scarves", "warm"},
    ),
}

NAMES = {
    "girl": ["Mia", "Lina", "Nora", "Ava", "Sophie"],
    "boy": ["Theo", "Finn", "Eli", "Max", "Leo"],
}

TRAITS = ["quiet", "curious", "stubborn", "careful", "cheerful"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life story for a little child named {f["child"].id} who '
        f"doesn't want to wear {f['scarf'].label} on {f['weather'].label}. Include the word 'darned'.",
        f"Tell a gentle story where {f['parent'].id} and {f['child'].id} have a small conflict about a scarf, and a flashback changes the child's mind.",
        f'Write a short story with the word "aah" where a child resists getting dressed, then feels better after remembering something kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    scarf = f["scarf"]
    weather = f["weather"]
    qa = [
        QAItem(
            question=f"Why didn't {child.id} want to wear {scarf.label}?",
            answer=(
                f"{child.id} thought {scarf.label} felt scratchy and was showing resistance. "
                f"The weather was {weather.label}, so the scarf seemed annoying at first."
            ),
        ),
        QAItem(
            question=f"What did {parent.pronoun('subject').capitalize()} ask {child.id} to do?",
            answer=(
                f"{parent.id} asked {child.id} to wear {scarf.label} for the cold walk. "
                f"{parent.pronoun().capitalize()} knew the scarf would help keep {child.pronoun('object')} warm."
            ),
        ),
        QAItem(
            question="What changed the child's mind?",
            answer=(
                f"A flashback did. {child.id} remembered {f['memory_line']} and the feeling of being loved, "
                f"so the resistance got smaller and the conflict softened."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {child.id} end up feeling at the end?",
                answer=(
                    f"{child.id} felt warm, proud, and calmer. In the end, {child.pronoun().capitalize()} wore {scarf.label} and went out with {parent.id}."
                ),
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "scarves": [
        (
            "What is a scarf for?",
            "A scarf helps keep your neck warm when the air is cold or windy.",
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story briefly remembers something that happened before.",
        )
    ],
    "resistance": [
        (
            "What does resistance mean here?",
            "Resistance means not wanting to do something right away, even if someone asks nicely.",
        )
    ],
    "conflict": [
        (
            "What is a conflict?",
            "A conflict is when two people want different things and need to work it out.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["scarf"].tags)
    tags.update({"flashback", "resistance", "conflict"})
    out = []
    for tag in ["resistance", "conflict", "flashback", "scarves"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def tell(weather: Weather, scarf: Clothing, child_name: str, child_type: str, parent_type: str) -> World:
    world = World(weather)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["small"],
        attrs={"role": "child"},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        traits=["steady"],
        attrs={"role": "parent"},
    ))
    scarf_ent = world.add(Entity(
        id="scarf",
        type="thing",
        label=scarf.label,
        phrase=scarf.phrase,
        soft="soft lining" in scarf.tags,
    ))
    scarf_ent.worn_by = child.id

    child.meters["bare_neck"] = 1.0
    child.memes["resistance"] = 1.0
    child.memes["memory"] = 0.0
    child.memes["conflict"] = 0.0
    child.memes["love"] = 0.0
    parent.memes["worry"] = 0.0
    scarf_ent.meters["meaning"] = 0.0

    # beginning
    world.say(
        f"{child.id} stood by the door on {weather.label} and wrinkled {child.pronoun('possessive')} nose at {scarf.label}."
    )
    world.say(
        f'"Aah, do I have to wear the {scarf.label.split("the ", 1)[-1]}?" {child.id} asked, while {parent.id} waited with the coat.'
    )
    world.say(
        f"{parent.id} said yes, because the walk to the shop would be chilly and the wind would nip at {child.pronoun('possessive')} neck."
    )

    # middle
    world.para()
    child.memes["resistance"] += 1.0
    world.say(
        f"{child.id} crossed {child.pronoun('possessive')} arms and kept resisting, because the scarf felt darned scratchy."
    )
    propagate(world, narrate=False)
    if weather.cold:
        world.say(
            f"The cold air kept waiting at the door, and {child.id} could almost feel it on {child.pronoun('possessive')} skin."
        )

    # flashback
    world.para()
    child.memes["memory"] = 1.0
    world.say(
        f"Then came a flashback: {fancy_flashback(scarf, child)}"
    )
    child.memes["conflict"] = 1.0
    propagate(world, narrate=False)
    if child.memes["resistance"] < 1.0:
        world.say(
            f"The memory made {child.id}'s resistance sink, like a pebble dropping into a quiet puddle."
        )

    # resolution
    world.para()
    if comfort_fix_for(scarf):
        world.say(
            f"{parent.id} tucked the soft lining flat and folded the scarf so it would not scratch."
        )
        child.memes["love"] += 1.0
        child.memes["conflict"] = 0.0
        world.say(
            f"{child.id} tried it again. This time it felt much better, and the conflict turned into a small nod."
        )
        world.say(
            f"{child.id} opened the door with {parent.id} and went out warm, with the scarf wrapped neatly around {child.pronoun('possessive')} neck."
        )
        resolved = True
    else:
        world.say(
            f"{parent.id} tried to help, but the scarf still felt scratchy, so the story ended with {child.id} choosing a different coat."
        )
        resolved = False

    world.facts.update(
        child=child,
        parent=parent,
        scarf=scarf_ent,
        weather=weather,
        memory_line="Grandma laughing softly while the yarn tickled a tiny nose",
        resolved=resolved,
    )
    return world


def fancy_flashback(scarf: Clothing, child: Entity) -> str:
    return (
        f"{child.id} remembered Grandma sitting in a bright chair and finishing {scarf.phrase}, "
        f"smiling as she said the yarn was made for a warm neck and a brave walk."
    )


def valid_combo_weather(weather: Weather, scarf: Clothing) -> bool:
    return weather.cold and comfort_fix_for(scarf)


CURATED = [
    StoryParams(
        weather="windy_morning",
        scarf="darned_scarf",
        child_name="Mia",
        child_type="girl",
        parent_type="mother",
    ),
    StoryParams(
        weather="cool_afternoon",
        scarf="striped_scarf",
        child_name="Theo",
        child_type="boy",
        parent_type="father",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: a scarf, resistance, and a flashback.")
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--scarf", choices=SCARVES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--parent-type", choices=["mother", "father"])
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
              if (getattr(args, "weather", None) is None or c[0] == getattr(args, "weather", None))
              and (getattr(args, "scarf", None) is None or c[1] == getattr(args, "scarf", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    weather, scarf = rng.choice(list(combos))
    child_type = getattr(args, "child_type", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "child_name", None) or rng.choice(_safe_lookup(NAMES, child_type))
    parent_type = getattr(args, "parent_type", None) or rng.choice(["mother", "father"])
    return StoryParams(
        weather=weather,
        scarf=scarf,
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
    )


ASP_RULES = r"""
cold_need(W,S) :- weather(W), cold(W), scarf(S), warms(S, neck).
conflict(C) :- resistance(C), child(C).
flashback(C) :- conflict(C), memory(C).
resolved(C) :- flashback(C), soft_fix(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for wid, w in WEATHER.items():
        lines.append(asp.fact("weather", wid))
        if w.cold:
            lines.append(asp.fact("cold", wid))
        if w.windy:
            lines.append(asp.fact("windy", wid))
    for sid, s in SCARVES.items():
        lines.append(asp.fact("scarf", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
        if comfort_fix_for(s):
            lines.append(asp.fact("soft_fix", sid))
        for w in sorted(s.warms):
            lines.append(asp.fact("warms", sid, w))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show cold_need/2."))
    return sorted(set(asp.atoms(model, "cold_need")))


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for wid, w in WEATHER.items():
        for sid, s in SCARVES.items():
            if valid_combo_weather(w, s):
                combos.append((wid, sid))
    return combos


def asp_verify() -> int:
    import asp
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a != p:
        print("MISMATCH")
        print("only in asp:", sorted(a - p))
        print("only in python:", sorted(p - a))
        return 1
    print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("ERROR: smoke story empty")
        return 1
    print("OK: smoke generation succeeded.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(WEATHER[params.weather], _safe_lookup(SCARVES, params.scarf), params.child_name, params.child_type, params.parent_type)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show cold_need/2."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("", "#show cold_need/2."))
        print(asp.atoms(model, "cold_need"))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
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
