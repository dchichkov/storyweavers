#!/usr/bin/env python3
"""
storyworlds/worlds/thistle_fury_debbie_foreshadowing_superhero_story.py
=======================================================================

A small superhero story world built from the seed words:
thistle, fury, debbie, and the narrative instrument foreshadowing.

Premise:
- Debbie is a young hero with a thistle-shaped badge.
- A simmering fury begins to rise in the city when a prankster threatens a
  community garden and its power relay.
- A tiny foreshadowed clue lets Debbie anticipate the danger, gather the right
  tool, and stop the trouble before it spreads.

The world models physical meters and emotional memes, and it renders story from
state changes rather than from a frozen template.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    debbie: object | None = None
    kit_ent: object | None = None
    mentor: object | None = None
    relay: object | None = None
    def __post_init__(self):
        for k in ("energy", "damage", "alert", "signal", "trust", "fury", "hope"):
            self.meters.setdefault(k, 0.0)
        for k in ("worry", "courage", "pride", "fear", "friendship", "foresight"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str = "the city garden"
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
class HeroKit:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    grants: set[str]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str
    threat: str
    kit: str
    name: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "garden": Setting(place="the city garden", affords={"thistle"}),
    "rooftop": Setting(place="the rooftop", affords={"fury"}),
    "alley": Setting(place="the lantern alley", affords={"fury", "thistle"}),
}

THREATS = {
    "thistle": {
        "id": "thistle",
        "label": "thistle vines",
        "phrase": "sharp thistle vines",
        "mess": "scratch",
        "warn": "the thistles were already bending toward the relay box",
        "danger": "scratch the power relay",
        "spread": "scratched",
        "zone": {"hands", "legs"},
        "keyword": "thistle",
        "tags": {"thistle"},
    },
    "fury": {
        "id": "fury",
        "label": "fury flare",
        "phrase": "a blazing fury flare",
        "mess": "burn",
        "warn": "a bright red glow was crawling over the wires",
        "danger": "burn the signal tower",
        "spread": "scorched",
        "zone": {"hands", "torso"},
        "keyword": "fury",
        "tags": {"fury"},
    },
}

KITS = {
    "gloves": HeroKit(
        id="gloves",
        label="thistle gloves",
        phrase="a pair of thistle gloves",
        protects_from={"scratch"},
        grants={"grip"},
    ),
    "shield": HeroKit(
        id="shield",
        label="a sunshield",
        phrase="a bright sunshield",
        protects_from={"burn"},
        grants={"cover"},
    ),
    "cape": HeroKit(
        id="cape",
        label="a blue rescue cape",
        phrase="a blue rescue cape",
        protects_from={"scratch", "burn"},
        grants={"flight", "cover"},
    ),
}

NAMES = ["Debbie", "Maya", "Nina", "Ivy", "Zara"]
TRAITS = ["brave", "quick", "clever", "kind", "steady"]


def _m(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _v(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def foreshadow(threat: dict) -> str:
    return f"Even before anyone ran, {threat['warn']}."


def can_cover(kit: HeroKit, threat: dict) -> bool:
    return threat["mess"] in kit.protects_from


def predict_damage(world: World, hero: Entity, threat: dict) -> float:
    sim = world.copy()
    _face_threat(sim, sim.get(hero.id), threat, narrate=False)
    target = sim.entities["relay"]
    return target.meters["damage"]


def _face_threat(world: World, hero: Entity, threat: dict, narrate: bool = True) -> None:
    hero.meters["energy"] -= 1
    if can_cover(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "kit"), threat):
        target = world.get("relay")
        _m(target, "damage", 0)
    else:
        target = world.get("relay")
        _m(target, "damage", 1)
        _m(target, "signal", -1)
        _v(hero, "worry", 1)
    if narrate and target.meters["damage"] >= THRESHOLD:
        world.say(f"The {target.label} would have been in danger.")


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)
    threat = _safe_lookup(THREATS, params.threat)
    kit = _safe_lookup(KITS, params.kit)

    debbie = world.add(Entity(
        id=params.name,
        kind="character",
        type="heroine",
        label=params.name,
        traits=["little", "steady", "brave"],
    ))
    mentor = world.add(Entity(
        id="mentor",
        kind="character",
        type="woman",
        label="Aunt Jo",
        traits=["wise"],
    ))
    relay = world.add(Entity(
        id="relay",
        type="thing",
        label="relay box",
        phrase="the city relay box",
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label="thistle badge",
        phrase="a tiny thistle badge",
    ))
    kit_ent = world.add(Entity(
        id=kit.id,
        type="thing",
        label=kit.label,
        phrase=kit.phrase,
        owner=debbie.id,
    ))
    kit_ent.carried_by = debbie.id

    world.facts.update(
        hero=debbie,
        mentor=mentor,
        relay=relay,
        clue=clue,
        threat=threat,
        kit=kit,
        kit_ent=kit_ent,
    )

    world.say(f"{debbie.id} was a little {debbie.traits[1]} hero who watched the city with kind eyes.")
    world.say(f"She kept a {clue.label} in her pocket, because a hero should notice small signs.")
    world.say(f"{debbie.id} liked helping people in {world.setting.place}.")

    world.para()
    world.say(foreshadow(threat))
    world.say(f"{mentor.label} pointed at the {threat['label']} and said it could {threat['danger']}.")
    _v(debbie, "foresight", 1)
    _v(debbie, "worry", 1)

    world.para()
    world.say(f"Then {params.name} hurried to {world.setting.place} and saw the trouble up close.")
    world.say(f"{params.name} wanted to stop it fast, but the {threat['label']} was already near the relay.")
    _v(debbie, "courage", 1)

    world.para()
    if kit.id == "cape":
        world.say(f"{params.name} grabbed {kit.label}, wrapped up tight, and stepped into the light.")
    else:
        world.say(f"{params.name} slipped on {kit.label} and breathed in, ready to help.")

    _face_threat(world, debbie, threat, narrate=False)
    if can_cover(kit, threat):
        _m(relay, "damage", 0)
        _m(relay, "signal", 1)
        _v(debbie, "pride", 1)
        _v(debbie, "hope", 1)
        world.say(
            f"{params.name} used {kit.label} and blocked the {threat['label']} before it could "
            f"{threat['danger']}."
        )
        world.say(
            f"The relay box stayed safe, the glow faded, and the city lights blinked back on."
        )
        world.say(
            f"{params.name} smiled at the thistle badge, because the little clue had helped save the day."
        )
    else:
        _m(relay, "damage", 1)
        world.say(f"The plan was too small for the danger, and the relay box still got hurt.")

    world.facts["resolved"] = can_cover(kit, threat)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the word "{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat")["keyword"]}".',
        f"Tell a gentle hero story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} noticing a clue, feeling a little fury in the city, and choosing the right tool.",
        f"Write a simple story where foreshadowing helps a hero named {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} save the day in {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    mentor = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mentor")
    threat = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat")
    kit = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "kit")
    relay = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relay")

    qa = [
        QAItem(
            question=f"Who is the hero in the story?",
            answer=f"The hero is {hero.id}, a little brave heroine who helps in {world.setting.place}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} get ready for trouble?",
            answer=f"The clue was a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue").label}. It reminded {hero.id} to watch for danger early.",
        ),
        QAItem(
            question=f"What did {mentor.label} warn about?",
            answer=f"{mentor.label} warned that the {threat['label']} could {threat['danger']}.",
        ),
        QAItem(
            question=f"How did {hero.id} stop the danger?",
            answer=(
                f"{hero.id} used {kit.label} to block the {threat['label']} and protect the relay box."
                if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "resolved")
                else f"{hero.id} tried to help, but the danger was bigger than the gear."
            ),
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=(
                f"The relay box stayed safe, the city lights came back, and {hero.id} felt proud and hopeful."
                if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "resolved")
                else f"The relay box was hurt, so the city still needed help."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small clue that hints something important may happen later.",
        ),
        QAItem(
            question="What is a thistle?",
            answer="A thistle is a prickly plant with sharp leaves and flowers, so you should be careful around it.",
        ),
        QAItem(
            question="What does fury mean?",
            answer="Fury means a very strong angry feeling, like a hot burst that is hard to ignore.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 0}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        out.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero story world with foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--name", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    threat = getattr(args, "threat", None) or rng.choice(list(THREATS))
    kit = getattr(args, "kit", None) or rng.choice(list(KITS))
    name = getattr(args, "name", None) or rng.choice(NAMES)

    if threat == "thistle" and kit not in {"gloves", "cape"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if threat == "fury" and kit not in {"shield", "cape"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if threat not in _safe_lookup(SETTINGS, place).affords and getattr(args, "place", None) is not None and getattr(args, "threat", None) is not None:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, threat=threat, kit=kit, name=name)


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
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
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        params_list = [
            StoryParams(place="garden", threat="thistle", kit="gloves", name="Debbie"),
            StoryParams(place="rooftop", threat="fury", kit="shield", name="Debbie"),
            StoryParams(place="alley", threat="thistle", kit="cape", name="Debbie"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
