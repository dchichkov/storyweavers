#!/usr/bin/env python3
"""
A small fairy-tale storyworld about a stubborn harpoon, a snorting creature,
and a teamwork fix that turns a problem into a celebration.

Seed inspiration:
- harpoon
- snort

Narrative instruments:
- Repetition
- Rhyme
- Teamwork
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
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    creature: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool_ent: object | None = None
    def __post_init__(self) -> None:
        for k in ("weight", "danger", "mess", "repair", "teamwork"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "mother", "mom"}
        male = {"boy", "king", "prince", "man", "father", "dad"}
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
    place: str = "the misty lake"
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
class Challenge:
    id: str
    verb: str
    gerund: str
    rush: str
    sign: str
    rhyme: str
    zone: set[str]
    keyword: str
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
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.facts: dict = {}
        self.challenge: Optional[Challenge] = None
        self.tool: Optional[Tool] = None

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
SETTINGS = {
    "harbor": Setting(place="the harbor", affords={"harpoon"}),
    "lake": Setting(place="the silver lake", affords={"harpoon"}),
    "river": Setting(place="the winding river", affords={"harpoon"}),
}

CHALLENGES = {
    "harpoon": Challenge(
        id="harpoon",
        verb="cast the harpoon",
        gerund="casting the harpoon",
        rush="dash toward the boat",
        sign="a splash and a snort",
        rhyme="The water was wide, but the line must guide.",
        zone={"water"},
        keyword="harpoon",
        tags={"harpoon", "water", "snort"},
    ),
}

TOOLS = [
    Tool(
        id="rope_team",
        label="a long rope",
        phrase="a long rope tied in two bright knots",
        covers={"water"},
        helps={"harpoon"},
        prep="join hands and hold the rope together",
        tail="held the rope side by side",
        plural=False,
    ),
    Tool(
        id="net_team",
        label="a wide net",
        phrase="a wide net with silver threads",
        covers={"water"},
        helps={"harpoon"},
        prep="lift the net together",
        tail="lifted the net together",
        plural=False,
    ),
]

HERO_NAMES = ["Alda", "Bran", "Cora", "Dorin", "Elin", "Fenn"]
CREATURE_NAMES = ["Snort", "Glim", "Murk", "Bramble"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    hero_name: str
    hero_kind: str
    helper_name: str
    helper_kind: str
    creature_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
% A challenge is available in a place that affords it.
valid(Place, Challenge) :- affords(Place, Challenge).

% A teamwork tool works when it is made for the challenge.
works(Tool, Challenge) :- tool(Tool), helps(Tool, Challenge).

% A full story exists when the place affords the challenge and a tool works.
valid_story(Place, Challenge, Tool) :- valid(Place, Challenge), works(Tool, Challenge).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for r in sorted(ch.zone):
            lines.append(asp.fact("zone", cid, r))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for c in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, c))
        for c in sorted(tool.covers):
            lines.append(asp.fact("covers", tool.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ch in setting.affords:
            out.append((place, ch))
    return out


def explain_rejection(place: str, challenge: str) -> str:
    if challenge not in CHALLENGES:
        return "(No story: that challenge is unknown.)"
    if challenge not in _safe_lookup(SETTINGS, place).affords:
        return f"(No story: {challenge} does not fit {place}.)"
    return "(No story: no reasonable tale here.)"


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def _snort(world: World, creature: Entity) -> None:
    creature.memes["snort"] += 1
    world.say(f"{creature.id} gave a great snort, snort, snort.")


def _attempt(world: World, hero: Entity, challenge: Challenge) -> None:
    hero.meters["danger"] += 1
    hero.memes["brave"] += 1
    world.say(
        f"{hero.id} tried to {challenge.verb}. "
        f"{challenge.rhyme}"
    )


def _warn(world: World, creature: Entity, hero: Entity, challenge: Challenge) -> None:
    creature.memes["worry"] += 1
    world.say(
        f'"Careful, careful," said {creature.id}. '
        f'"A snort means trouble, and trouble means hurry."'
    )


def _teamwork(world: World, hero: Entity, helper: Entity, tool: Tool, challenge: Challenge) -> None:
    hero.memes["hope"] += 1
    helper.memes["helpful"] += 1
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        protective=True,
        covers=set(tool.covers),
    ))
    tool_ent.worn_by = hero.id
    world.tool = tool
    world.say(
        f"{hero.id} and {helper.id} made a plan. "
        f"They would {tool.prep}, and then {challenge.verb} together."
    )
    world.say(
        f"{hero.id} and {helper.id} {tool.tail}. "
        f"The water stayed calm enough for a brave try."
    )


def tell(world: World, params: StoryParams) -> World:
    setting = world.setting
    challenge = _safe_lookup(CHALLENGES, params.challenge)
    world.challenge = challenge

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_kind))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_kind))
    creature = world.add(Entity(id=params.creature_name, kind="character", type="creature"))

    world.say(
        f"Once in {setting.place}, there lived {hero.id}, {helper.id}, and {creature.id}."
    )
    world.say(
        f"{hero.id} loved the old {challenge.keyword}. "
        f"Again and again, {hero.id} dreamed of the day to {challenge.verb}."
    )
    world.say(
        f"{creature.id} lived by the water and often made a little {challenge.sign}."
    )

    world.para()
    _snort(world, creature)
    _attempt(world, hero, challenge)
    _warn(world, creature, hero, challenge)

    world.para()
    tool = _safe_lookup(TOOLS, 0) if params.helper_kind == "friend" else _safe_lookup(TOOLS, 1)
    _teamwork(world, hero, helper, tool, challenge)

    world.para()
    hero.memes["joy"] += 1
    world.say(
        f"At last, the plan worked. {hero.id} could {challenge.verb}, and the snort turned to cheer."
    )
    world.say(
        f"{hero.id}, {helper.id}, and {creature.id} laughed in rhyme: "
        f"bright by night, and right with might."
    )

    world.facts.update(hero=hero, helper=helper, creature=creature, tool=tool, challenge=challenge)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch: Challenge = _safe_fact(world, f, "challenge")
    return [
        f'Write a fairy-tale story for a child that includes the word "{ch.keyword}" and the sound "{f["creature"].id}".',
        f"Tell a gentle tale where {f['hero'].id} wants to {ch.verb}, but teamwork with {f['helper'].id} helps.",
        f"Write a story that repeats a warning, uses a rhyme, and ends with friends working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, creature, ch = f["hero"], f["helper"], f["creature"], f["challenge"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the story?",
            answer=f"{hero.id} wanted to {ch.verb} at {world.setting.place}.",
        ),
        QAItem(
            question=f"Who gave the warning when the snorting began?",
            answer=f"{creature.id} gave the warning, because the snorting sounded like trouble.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} solve the problem?",
            answer=f"They used {tool.label} and worked together, so {hero.id} could {ch.verb} safely.",
        ),
        QAItem(
            question="What made the story feel like a fairy tale?",
            answer="It had a brave wish, a snorting creature, a warning repeated more than once, and a teamwork ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like might and night.",
        ),
        QAItem(
            question="What does a snort sound like?",
            answer="A snort is a short, rough burst of air through the nose, often making a funny sound.",
        ),
        QAItem(
            question="What is a harpoon?",
            answer="A harpoon is a long pointed tool or spear used to throw or aim at something from a distance.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld: harpoon, snort, teamwork, and rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-kind", choices=["prince", "princess", "child"], default=None)
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-kind", choices=["friend", "sibling", "wizard"], default=None)
    ap.add_argument("--creature-name")
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
    if getattr(args, "place", None) and getattr(args, "challenge", None) and getattr(args, "challenge", None) not in _safe_lookup(SETTINGS, getattr(args, "place", None)).affords:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "challenge", None):
        combos = [c for c in combos if c[1] == getattr(args, "challenge", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(list(combos))
    hero_kind = getattr(args, "hero_kind", None) or rng.choice(["prince", "princess", "child"])
    helper_kind = getattr(args, "helper_kind", None) or rng.choice(["friend", "sibling", "wizard"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in HERO_NAMES if n != hero_name])
    creature_name = getattr(args, "creature_name", None) or rng.choice(CREATURE_NAMES)
    return StoryParams(
        place=place,
        challenge=challenge,
        hero_name=hero_name,
        hero_kind=hero_kind,
        helper_name=helper_name,
        helper_kind=helper_kind,
        creature_name=creature_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    story_world = tell(world, params)
    return StorySample(
        params=params,
        story=story_world.render(),
        prompts=generation_prompts(story_world),
        story_qa=story_qa(story_world),
        world_qa=world_knowledge_qa(story_world),
        world=story_world,
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_stories()
        print(f"{len(triples)} valid story tuples:")
        for place, challenge, tool in triples:
            print(f"  {place:12} {challenge:10} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(
                place="harbor",
                challenge="harpoon",
                hero_name="Alda",
                hero_kind="princess",
                helper_name="Bram",
                helper_kind="friend",
                creature_name="Snort",
            ),
            StoryParams(
                place="lake",
                challenge="harpoon",
                hero_name="Cora",
                hero_kind="child",
                helper_name="Dorin",
                helper_kind="wizard",
                creature_name="Snort",
            ),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
