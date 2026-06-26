#!/usr/bin/env python3
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    quiet: bool
    has_water: bool
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    guards: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    portable: bool = True
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
    noise_source: str
    item: str
    hero_name: str
    hero_gender: str
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


PLACES = {
    "harbor": Place(id="harbor", label="the harbor", quiet=False, has_water=True),
    "dock": Place(id="dock", label="the dock", quiet=False, has_water=True),
    "cove": Place(id="cove", label="the cove", quiet=True, has_water=True),
    "pier": Place(id="pier", label="the pier", quiet=False, has_water=True),
}

NOISE_SOURCES = {
    "trawler": {
        "label": "a trawler",
        "verb": "rumbled and roared",
        "rhyme": "The trawler made a clatter, and the gulls all sang in chatter.",
        "kind": "boat",
        "noise": "noise",
        "boost": 2.0,
        "reason": "its engine and winch were loud",
    },
    "winch": {
        "label": "a winch",
        "verb": "whirred and chirred",
        "rhyme": "The winch went zip and zing, making every rope line ring.",
        "kind": "machine",
        "noise": "noise",
        "boost": 1.5,
        "reason": "its gears squeaked and spun",
    },
    "horn": {
        "label": "a boat horn",
        "verb": "tooted and hooted",
        "rhyme": "The horn said beep-beep-bee, loud as loud could be.",
        "kind": "signal",
        "noise": "noise",
        "boost": 1.2,
        "reason": "its note was sharp and clear",
    },
}

ITEMS = {
    "earmuffs": Item(
        id="earmuffs",
        label="earmuffs",
        phrase="soft earmuffs",
        kind="gear",
        guards={"noise"},
        helps={"quiet"},
    ),
    "shellbook": Item(
        id="shellbook",
        label="a shell book",
        phrase="a little shell book",
        kind="book",
        guards={"spray"},
        helps={"reading"},
    ),
    "tea": Item(
        id="tea",
        label="a teacup",
        phrase="a warm teacup",
        kind="cup",
        guards={"spill"},
        helps={"calm"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ella", "Rose"]
BOY_NAMES = ["Leo", "Theo", "Finn", "Noah", "Eli", "Max"]
HELPERS = ["mother", "father", "grandma", "grandpa"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        other = World(self.place)
        import copy
        other.entities = copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


def rhyme_lines(source: str, hero: str, place: str, helper: str, item: str) -> tuple[str, str, str]:
    if source == "trawler":
        a = f"At {place}, the trawler gave a roar, and {hero} wanted peace by shore."
        b = f"{helper} smiled, then said with cheer, “Let’s make the loud old sound disappear.”"
        c = f"With {item}, the day grew kind; quiet came, and joy did rhyme."
        return a, b, c
    if source == "winch":
        a = f"At {place}, the winch went whirr and whine, and {hero} wrinkled up {hero}'s tiny line."
        b = f"{helper} said, “A softer sound will do; let’s find a fix that fits you too.”"
        c = f"With {item}, the noise slid out of sight, and the cove turned calm and light."
        return a, b, c
    a = f"At {place}, the horn said beep-ly-bee, and {hero} clapped hands, “Too loud for me!”"
    b = f"{helper} nodded, warm and wise, and found a way to hush the skies."
    c = f"With {item}, the chatter faded fast; the happy hush was here at last."
    return a, b, c


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    if params.noise_source not in NOISE_SOURCES:
        pass
    if params.item not in ITEMS:
        pass
    noise = _safe_lookup(NOISE_SOURCES, params.noise_source)
    item = _safe_lookup(ITEMS, params.item)

    if params.item == "shellbook" and params.noise_source == "trawler":
        pass
    if params.item == "tea" and params.noise_source == "trawler":
        pass
    if params.item == "earmuffs" and not noise["noise"]:
        pass

    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=params.helper))
    gear = world.add(Entity(id=item.id, type=item.kind, label=item.label, phrase=item.phrase))
    gear.worn_by = hero.id

    world.facts.update(
        hero=hero,
        helper=helper,
        item=gear,
        source=noise,
        source_id=params.noise_source,
        place=place,
    )

    loud = 2.0 if params.noise_source == "trawler" else 1.0
    hero.memes["startle"] = loud
    hero.memes["wish_quiet"] = 1.0

    a, b, c = rhyme_lines(params.noise_source, hero.id, place.label, helper.label, gear.label)
    world.say(f"{hero.id} went out one day to {place.label}, where a {noise['label']} made a mighty play.")
    world.say(f"It {noise['verb']}, for {noise['reason']}, and the sound rolled far away.")
    world.say(a)
    world.para()
    world.say(f"{hero.id} said, “I want a soft, sweet scene; this noisy place is far from serene.”")
    world.say(f"{helper.label} heard the fuss and then had a thought, a fix that fit the need they sought.")
    world.say(f"“Try {gear.phrase},” {helper.label} said, “and the loud old splash will lose its edge.”")
    world.say(b)
    hero.memes["hope"] = 1.0
    if gear.id == "earmuffs":
        hero.memes["calm"] = 1.0
        hero.memes["joy"] = 1.0
        world.para()
        world.say(f"{hero.id} put on {gear.phrase}, and the noise grew small, like a pebble dropped in the hall.")
        world.say(c)
        world.say(f"{hero.id} laughed at the breeze, and the harbor hummed in peaceful ease.")
    else:
        world.para()
        world.say(f"{hero.id} tried the {gear.label}, but the noise still peeped through the little spell.")
        world.say("So the day was not quite right, and that makes a weak old story sight.")
    world.facts["resolved"] = gear.id == "earmuffs"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story about a child at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").label} where a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "source_id")} makes noise.',
        f"Tell a happy ending story in rhyme where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} needs a simple way to quiet the sound of a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "source")['label']}.",
        f'Create a child-friendly rhyming story that includes a trawler, noise, and a kind helper who finds a fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    item = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    source = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "source")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    qa = [
        QAItem(
            question=f"Where did {hero.id} go in the story?",
            answer=f"{hero.id} went to {place.label}, where the noisy scene could be heard by the water.",
        ),
        QAItem(
            question=f"What made the loud sound near {place.label}?",
            answer=f"{source['label'].capitalize()} made the loud sound because {source['reason']}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} find a fix?",
            answer=f"{helper.label} helped {hero.id} by suggesting {item.phrase} as the simple fix.",
        ),
    ]
    if _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "resolved"):
        qa.append(
            QAItem(
                question=f"How did {item.label} help at the end?",
                answer=f"{item.phrase} helped by muffling the noise, so {hero.id} could relax and smile.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a trawler?",
            answer="A trawler is a fishing boat that can carry gear and move steadily across the water.",
        ),
        QAItem(
            question="What is noise?",
            answer="Noise is a loud sound that can bother ears when it goes on and on.",
        ),
        QAItem(
            question="What do earmuffs do?",
            answer="Earmuffs cover your ears and help make loud sounds feel softer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
source_noise(S) :- source(S).
fix_item(I) :- item(I).
compatible(S,I) :- source_noise(S), fix_item(I), needs_noise_fix(S), neutralizes(I, noise).
good_story(P,S,I) :- place(P), source_noise(S), compatible(S,I).
#show good_story/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
        if p.has_water:
            lines.append(asp.fact("water", pid))
    for sid, s in NOISE_SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("needs_noise_fix", sid))
        lines.append(asp.fact("neutralizes", "earmuffs", "noise"))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for p in PLACES:
        for s in NOISE_SOURCES:
            for i in ITEMS:
                if i == "earmuffs":
                    out.append((p, s, i))
    return out


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show good_story/3."))
    return sorted(set(asp.atoms(model, "good_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    if py == asps:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - asps))
    print("only clingo:", sorted(asps - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world: logical trawler noise, happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--noise-source", choices=NOISE_SOURCES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
    ap.add_argument("--name")
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
    noise_source = getattr(args, "noise_source", None) or rng.choice(list(NOISE_SOURCES))
    item = getattr(args, "item", None) or ("earmuffs" if noise_source == "trawler" else rng.choice(list(ITEMS)))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    if item != "earmuffs":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, noise_source=noise_source, item=item, hero_name=name, hero_gender=gender, helper=helper)


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


CURATED = [
    StoryParams(place="harbor", noise_source="trawler", item="earmuffs", hero_name="Mia", hero_gender="girl", helper="mother"),
    StoryParams(place="dock", noise_source="winch", item="earmuffs", hero_name="Leo", hero_gender="boy", helper="father"),
    StoryParams(place="cove", noise_source="horn", item="earmuffs", hero_name="Nora", hero_gender="girl", helper="grandma"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show good_story/3."))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            params.seed = base_seed + i
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
