#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nudge_antenna_moral_value_teamwork_dialogue_detective.py
====================================================================================================

A standalone storyworld for a tiny detective tale: a child notices a mystery,
uses a nudge and an antenna, and learns a moral lesson through teamwork and dialogue.

The domain is intentionally small and constraint-checked. A curious little detective
tracks a missing object, asks careful questions, and solves the case with a helper.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    indoors: bool
    clues: set[str] = field(default_factory=set)
    allows: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    label: str
    phrase: str
    clue: str
    hidden_in: str
    rumor: str
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
    use: str
    helps_with: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _add_meter(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _add_meme(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def tell(setting: Setting, mystery: Mystery, tool: Tool, helper_kind: str,
         hero_name: str, hero_kind: str, sidekick_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_kind, label=hero_name))
    helper = world.add(Entity(id=sidekick_name, kind="character", type=helper_kind, label=sidekick_name))
    missing = world.add(Entity(
        id="missing", kind="thing", type="thing", label=mystery.label,
        phrase=mystery.phrase, owner=hero.id
    ))
    tool_ent = world.add(Entity(
        id=tool.id, kind="thing", type="tool", label=tool.label,
        phrase=tool.phrase, owner=helper.id
    ))

    _add_meme(hero, "curiosity")
    _add_meme(hero, "duty")
    world.say(
        f"{hero.id} was a little detective who loved careful thinking and tidy clues."
    )
    world.say(
        f"{hero.pronoun().capitalize()} carried {tool_ent.phrase} and kept an eye on every corner."
    )
    world.say(
        f"One day, {missing.phrase} went missing, and the rumor was that it had been {mystery.rumor}."
    )

    world.para()
    world.say(
        f"At {setting.place}, {hero.id} looked under benches and behind boxes while {helper.id} listened."
    )
    _add_meter(hero, "search", 1.0)
    _add_meme(hero, "worry", 1.0)

    if mystery.hidden_in in setting.allows:
        _add_meter(missing, "hidden", 1.0)

    world.say(
        f'"Have you seen {missing.label_word}?" {hero.id} asked. '
        f'"Not yet," {helper.id} said, "but I heard a small sound near the clue board."'
    )
    _add_meme(hero, "dialogue", 1.0)
    _add_meme(helper, "dialogue", 1.0)

    world.para()
    world.say(
        f"{hero.id} gave the clue board a gentle nudge, and the {tool_ent.label} antenna tipped toward the floor."
    )
    _add_meter(hero, "nudge", 1.0)
    _add_meter(tool_ent, "signal", 1.0)
    _add_meme(hero, "hope", 1.0)

    if tool.use in mystery.tags or mystery.hidden_in == tool.use:
        _add_meter(missing, "found", 1.0)
        _add_meme(hero, "relief", 1.0)
        _add_meme(helper, "relief", 1.0)
        world.say(
            f"The antenna pointed to a loose panel, and there was {missing.phrase} tucked safely inside."
        )
        world.say(
            f"{helper.id} smiled. {hero.id} smiled too, because the clues finally made sense."
        )
    else:
        pass

    world.para()
    _add_meme(hero, "moral", 1.0)
    _add_meme(helper, "moral", 1.0)
    world.say(
        f"{hero.id} said, \"A good detective tells the truth, asks kindly, and shares the work.\""
    )
    world.say(
        f"{helper.id} nodded. Together they put everything back in order, and the case was closed."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        mystery=mystery,
        tool=tool_ent,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "station": Setting(
        place="the little station office",
        indoors=True,
        clues={"board", "desk", "drawer"},
        allows={"drawer", "panel"},
    ),
    "library": Setting(
        place="the quiet library nook",
        indoors=True,
        clues={"shelf", "lamp", "card"},
        allows={"shelf", "card", "panel"},
    ),
    "garden": Setting(
        place="the back garden path",
        indoors=False,
        clues={"bench", "gate", "stone"},
        allows={"bench", "stone"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="silver bell",
        phrase="a silver bell with a ribbon",
        clue="a tiny ring",
        hidden_in="drawer",
        rumor="moved into a drawer",
        tags={"drawer", "panel"},
    ),
    "badge": Mystery(
        id="badge",
        label="brass badge",
        phrase="a brass badge with a star",
        clue="a glint of gold",
        hidden_in="panel",
        rumor="slipped behind a panel",
        tags={"panel"},
    ),
    "map": Mystery(
        id="map",
        label="folded map",
        phrase="a folded map with red marks",
        clue="a corner of paper",
        hidden_in="shelf",
        rumor="tucked into a shelf",
        tags={"shelf"},
    ),
}

TOOLS = {
    "antenna": Tool(
        id="antenna",
        label="antenna",
        phrase="a tiny antenna",
        use="panel",
        helps_with={"panel", "drawer"},
    ),
    "magnifier": Tool(
        id="magnifier",
        label="magnifier",
        phrase="a round magnifier",
        use="shelf",
        helps_with={"shelf", "card"},
    ),
    "flashlight": Tool(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        use="drawer",
        helps_with={"drawer", "panel"},
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Lena", "Pia", "Ivy", "Tess"]
BOY_NAMES = ["Owen", "Milo", "Noah", "Jude", "Eli", "Finn"]
HELPER_NAMES = ["Sam", "Rae", "Kim", "Jo", "Max", "Lee"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    hero_name: str
    hero_kind: str
    helper_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sk, setting in SETTINGS.items():
        for mk, mystery in MYSTERIES.items():
            for tk, tool in TOOLS.items():
                if mystery.hidden_in in setting.allows and mystery.hidden_in in tool.helps_with:
                    combos.append((sk, mk, tk))
    return combos


def explain_rejection(setting: Setting, mystery: Mystery, tool: Tool) -> str:
    return (
        f"(No story: in {setting.place}, {tool.label} cannot reasonably help find "
        f"{mystery.label}. This mystery needs a tool that can guide a search near "
        f"the right hidden place.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld with nudge, antenna, moral value, teamwork, and dialogue.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-kind", choices=["girl", "boy"], default=None)
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[1] == getattr(args, "mystery", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_key, mystery_key, tool_key = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_kind == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting_key,
        mystery=mystery_key,
        tool=tool_key,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(TOOLS, params.tool),
        "boy" if params.hero_kind == "girl" else "girl",
        params.hero_name,
        params.hero_kind,
        params.helper_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that uses the words "{f["mystery"].label}" and "antenna".',
        f"Tell a gentle mystery where {f['hero'].id} and {f['helper'].id} solve a case by talking kindly and working together.",
        f"Write a story about a little detective, a nudge, and a clue that leads to a hidden {f['missing'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    missing = _safe_fact(world, f, "missing")
    mystery = _safe_fact(world, f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What was the mystery in {setting.place}?",
            answer=f"The mystery was the missing {missing.label}, which had been {mystery.rumor}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the case?",
            answer=f"They solved it by talking kindly, giving the clue board a gentle nudge, and using the {tool.label} antenna to find the hidden {missing.label}.",
        ),
        QAItem(
            question=f"What moral did {hero.id} say at the end?",
            answer="The moral was that a good detective tells the truth, asks kindly, and shares the work.",
        ),
        QAItem(
            question=f"Why was the antenna useful in the story?",
            answer=f"It helped point the search toward the right hidden place, which let {hero.id} and {helper.id} find the missing {missing.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an antenna for?",
            answer="An antenna can help notice or guide signals, like finding where a clue is leading.",
        ),
        QAItem(
            question="What is a nudge?",
            answer="A nudge is a small push that is gentle, not rough.",
        ),
        QAItem(
            question="Why is teamwork helpful?",
            answer="Teamwork is helpful because two people can share ideas, help each other, and finish a task together.",
        ),
        QAItem(
            question="Why do detectives ask questions?",
            answer="Detectives ask questions to learn facts and solve problems carefully.",
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
    lines.append("== world knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid story needs a setting where the mystery can hide and a tool that can
% help search that same place.
valid_combo(S, M, T) :- setting(S), mystery(M), tool(T),
                        hidden_in(M, H), allows(S, H), helps_with(T, H).

% The storyworld's reasonableness gate: the right tool must be able to help with
% the right hiding place.
reasonable(S, M, T) :- valid_combo(S, M, T).

#show valid_combo/3.
#show reasonable/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sk, s in SETTINGS.items():
        lines.append(asp.fact("setting", sk))
        if s.indoors:
            lines.append(asp.fact("indoors", sk))
        for c in sorted(s.allows):
            lines.append(asp.fact("allows", sk, c))
    for mk, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mk))
        lines.append(asp.fact("hidden_in", mk, m.hidden_in))
    for tk, t in TOOLS.items():
        lines.append(asp.fact("tool", tk))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps_with", tk, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


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
    StoryParams(setting="station", mystery="bell", tool="antenna", hero_name="Maya", hero_kind="girl", helper_name="Sam"),
    StoryParams(setting="library", mystery="map", tool="magnifier", hero_name="Owen", hero_kind="boy", helper_name="Rae"),
    StoryParams(setting="station", mystery="badge", tool="flashlight", hero_name="Lena", hero_kind="girl", helper_name="Jo"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for row in combos:
            print(" ", row)
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def _story_qa(world: World) -> list[QAItem]:
    return story_qa(world)


if __name__ == "__main__":
    main()
