#!/usr/bin/env python3
"""
A small animal-story world about a pastry bake, a bit of carbon dust, and a
foreshadowed rescue of the sweets before they burn.

The story model is built from a short source-tale premise:
- a small animal baker wants to make pastry
- something carbon-like near the oven hints that the heat may become too strong
- the smell, smoke, and dark crumbs foreshadow trouble
- a helper notices the sign and turns the story toward a kinder ending
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    carbon: object | None = None
    helper: object | None = None
    hero: object | None = None
    pastry: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "fox", "cat", "dog", "bear", "squirrel"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type

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
    place: str = "the bakery"
    indoors: bool = True
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
class Pastry:
    id: str
    label: str
    phrase: str
    fragility: str
    heat_risk: bool = True
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
class Foreshadow:
    sign: str
    hint: str
    danger: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "bakery": Setting(place="the bakery", indoors=True),
    "kitchen": Setting(place="the kitchen", indoors=True),
    "oven_room": Setting(place="the warm oven room", indoors=True),
}

PSTRS = {
    "bun": Pastry("bun", "a honey bun", "a sticky honey bun", "soft and sweet"),
    "tart": Pastry("tart", "a berry tart", "a tiny berry tart", "delicate and crumbly"),
    "roll": Pastry("roll", "a cinnamon roll", "a swirly cinnamon roll", "warm and fluffy"),
}

FORESHADOWS = {
    "carbon_smell": Foreshadow(
        sign="a little carbon smell",
        hint="the air smelled like a fireplace after a long winter night",
        danger="the oven might be getting too hot",
    ),
    "dark_dust": Foreshadow(
        sign="a black crumb on the tray",
        hint="one crumb looked dark as soot beside the golden dough",
        danger="something nearby was turning the pastry too dark",
    ),
    "smoke_tuft": Foreshadow(
        sign="a thin tuft of smoke",
        hint="a wisp curled up from the oven door like a warning ribbon",
        danger="the pastry could scorch before it was ready",
    ),
}

ANIMAL_NAMES = ["Milo", "Mina", "Nori", "Pip", "Tia", "Luna", "Benny", "Coco"]
ANIMAL_TYPES = ["rabbit", "mouse", "fox", "cat", "dog", "bear", "squirrel"]
HELPER_TYPES = ["rabbit", "mouse", "cat", "dog", "squirrel"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A pastry is in danger if carbon signs, smoke, or heat hint at burning.
danger(P) :- pastry(P), sign(carbon_smell).
danger(P) :- pastry(P), sign(dark_dust).
danger(P) :- pastry(P), sign(smoke_tuft).

% A helper can fix the story when they notice the danger and cool the oven.
resolved(P) :- danger(P), helper(H), notices(H, P), cools_oven(H), rescues(H, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "bakery"))
    for pid, p in PSTRS.items():
        lines.append(asp.fact("pastry", pid))
        lines.append(asp.fact("fragile", pid, p.fragility))
    for sid in FORESHADOWS:
        lines.append(asp.fact("sign", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:  # pragma: no cover
        print(f"ASP unavailable: {err}")
        return 1
    model = asp.one_model(asp_program("#show danger/1."))
    atoms = set(asp.atoms(model, "danger"))
    expected = {(pid,) for pid in PSTRS}
    if atoms == expected:
        print(f"OK: ASP gate matches danger model ({len(atoms)} pastries).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("  ASP:", sorted(atoms))
    print("  PY :", sorted(expected))
    return 1


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    pastry: str
    foreshadow: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Core simulation
# ---------------------------------------------------------------------------
    params: object | None = None
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
class Trace:
    pastry_danger: float = 0.0
    helper_alert: float = 0.0
    oven_heat: float = 0.0
    rescued: bool = False
    burnt: bool = False
    trace: object | None = None
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


def make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    pastry = world.add(Entity(
        id="pastry",
        kind="thing",
        type="pastry",
        label=_safe_lookup(PSTRS, params.pastry).label,
        phrase=_safe_lookup(PSTRS, params.pastry).phrase,
    ))
    carbon = world.add(Entity(
        id="carbon",
        kind="thing",
        type="carbon",
        label="carbon",
        phrase="a little pile of carbon",
    ))
    world.facts.update(hero=hero, helper=helper, pastry=pastry, carbon=carbon, foreshadow=_safe_lookup(FORESHADOWS, params.foreshadow))
    return world


def simulate(world: World) -> Trace:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    pastry: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "pastry")
    foreshadow: Foreshadow = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "foreshadow")
    trace = Trace()

    world.say(f"{hero.label} the {hero.type} was busy in {world.setting.place}, baking {pastry.phrase}.")
    world.say(f"Near the tray sat a tiny bit of carbon, and {foreshadow.hint}.")
    trace.oven_heat += 1.0
    trace.pastry_danger += 1.0
    if foreshadow.sign == "a thin tuft of smoke":
        trace.pastry_danger += 0.5
    if foreshadow.sign == "a black crumb on the tray":
        trace.pastry_danger += 0.25

    world.para()
    world.say(f"{hero.label} noticed the sign, but wanted the pastry to finish just right.")
    world.say(f"Then {helper.label} the {helper.type} sniffed the air and said, \"That {foreshadow.danger}.\"")
    trace.helper_alert += 1.0

    world.para()
    if trace.pastry_danger >= 1.0 and trace.helper_alert >= 1.0:
        trace.rescued = True
        world.say(f"{helper.label} opened the oven door, let the hot air out, and moved the tray to a cooler shelf.")
        world.say(f"After that, the pastry stayed golden instead of scorched, and the carbon smell faded away.")
        world.say(f"{hero.label} smiled, because the little warning had helped them save the treat in time.")
    else:
        trace.burnt = True
        world.say(f"The oven stayed too hot, and the pastry came out dark and bitter.")
        world.say(f"{hero.label} sighed, wishing they had listened to the warning sooner.")

    world.facts["trace"] = trace
    return trace


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: Pastry = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "pastry")
    foreshadow: Foreshadow = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "foreshadow")
    return [
        f'Write a short animal story for a young child about a {p.label} and a helpful warning sign.',
        f"Tell a gentle story where a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").type} notices {foreshadow.sign} while baking {p.phrase}.",
        f'Write a tiny story that includes carbon, pastry, and a clue that hints trouble before the ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    pastry: Pastry = _safe_lookup(PSTRS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "pastry").id)
    foreshadow: Foreshadow = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "foreshadow")
    trace: Trace = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trace")
    qa = [
        QAItem(
            question=f"What was {hero.label} making in {world.setting.place}?",
            answer=f"{hero.label} was making {pastry.phrase} in {world.setting.place}.",
        ),
        QAItem(
            question=f"What warning sign hinted that the bake might go wrong?",
            answer=f"The story used {foreshadow.sign} to hint that {foreshadow.danger}.",
        ),
        QAItem(
            question=f"Who helped fix the problem with the pastry?",
            answer=f"{helper.label} the {helper.type} helped by cooling the oven and moving the tray.",
        ),
    ]
    if trace.rescued:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"The pastry stayed golden, the carbon smell faded, and {hero.label} felt glad the warning had been noticed.",
            )
        )
    if trace.burnt:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"The pastry burned because the warning came too late.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is pastry?",
            answer="Pastry is a doughy treat that is baked until it becomes soft, flaky, or crisp.",
        ),
        QAItem(
            question="What is carbon in this story?",
            answer="Carbon here is a dark, sooty substance that can hint at smoke or something getting too hot.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little clue early on that hints at what may happen later.",
        ),
    ]


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for pastry in PSTRS:
            for fs in FORESHADOWS:
                combos.append((setting, pastry, fs))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "pastry", None) and getattr(args, "foreshadow", None) and getattr(args, "foreshadow", None) == "carbon_smell" and getattr(args, "pastry", None) == "tart":
        pass
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    pastry = getattr(args, "pastry", None) or rng.choice(list(PSTRS))
    foreshadow = getattr(args, "foreshadow", None) or rng.choice(list(FORESHADOWS))
    hero_type = getattr(args, "hero_type", None) or rng.choice(ANIMAL_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    if getattr(args, "helper_type", None) is None and helper_type == hero_type and helper_type not in {"rabbit", "mouse", "cat", "dog", "squirrel"}:
        helper_type = "mouse"
    hero_name = getattr(args, "hero_name", None) or rng.choice(ANIMAL_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in ANIMAL_NAMES if n != hero_name])
    return StoryParams(
        setting=setting,
        pastry=pastry,
        foreshadow=foreshadow,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    simulate(world)
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
        bits = []
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.phrase:
            bits.append(f"phrase={e.phrase!r}")
        lines.append(f"  {e.id:8} ({e.type:8}) " + " ".join(bits))
    trace: Trace = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "trace")
    lines.append(f"  trace: danger={trace.pastry_danger} alert={trace.helper_alert} rescued={trace.rescued} burnt={trace.burnt}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world: pastry, carbon, and foreshadowing.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--pastry", choices=PSTRS)
    ap.add_argument("--foreshadow", choices=FORESHADOWS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=ANIMAL_TYPES)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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


def format_rejection(reason: str) -> str:
    return f"(No story: {reason})"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show danger/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show danger/1.\n#show resolved/1."))
        print("danger:", sorted(asp.atoms(model, "danger")))
        print("resolved:", sorted(asp.atoms(model, "resolved")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for setting in SETTINGS:
            for pastry in PSTRS:
                for foreshadow in FORESHADOWS:
                    params = StoryParams(
                        setting=setting,
                        pastry=pastry,
                        foreshadow=foreshadow,
                        hero_name="Milo",
                        hero_type="rabbit",
                        helper_name="Luna",
                        helper_type="mouse",
                    )
                    samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
        if idx:
            print("\n" + "=" * 70 + "\n")
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### {p.hero_name} the {p.hero_type}: {p.pastry} with {p.foreshadow}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)


if __name__ == "__main__":
    main()
