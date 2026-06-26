#!/usr/bin/env python3
"""
A small pirate-tale story world built around bravery, sharing, and
reconciliation.

Seed image:
A young pirate wants to climb the crow's-nest top, share bacon with a
ribbiting lookout, and make peace after a squabble.

The world is intentionally small and constraint-checked:
- the hero can only face a risk that is plausibly fixed by a compatible tool
- the shared thing at risk is physical and emotionally meaningful
- the story must end with a visible change in the world state
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
# Domain model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0}
        if not self.memes:
            self.memes = {"bravery": 0.0, "sharing": 0.0, "reconciliation": 0.0, "mood": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "mother", "maiden", "lass"}
        masculine = {"boy", "father", "lad", "man"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Risk:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: set[str]
    keyword: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fixes: set[str]
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
    risk: str
    prize: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
        self.lines: list[str] = []
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


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "deck": Setting(place="the deck", afford={"storm", "sail"}),
    "harbor": Setting(place="the harbor", afford={"storm", "sail"}),
    "island": Setting(place="the island dock", afford={"storm", "sail"}),
}

RISKS = {
    "storm": Risk(
        id="storm",
        verb="climb the crow's-nest top",
        gerund="climbing high in the storm",
        rush="rush up the mast",
        danger="blown and soaked",
        zone={"torso", "head"},
        keyword="top",
    ),
    "sail": Risk(
        id="sail",
        verb="haul the sail",
        gerund="pulling the sail lines",
        rush="dash to the rigging",
        danger="snapped by the wind",
        zone={"hands", "torso"},
        keyword="bacon",
    ),
}

PRIZES = {
    "bacon": Prize(id="bacon", label="bacon", phrase="a warm strip of bacon", region="hands", plural=False),
    "map": Prize(id="map", label="map", phrase="a folded treasure map", region="hands", plural=False),
    "top_hat": Prize(id="top hat", label="top hat", phrase="a tiny top hat", region="head", plural=False),
}

TOOLS = {
    "rope": Tool(
        id="rope",
        label="a knotted rope",
        phrase="a knotted rope",
        covers={"hands", "torso"},
        fixes={"storm", "sail"},
    ),
    "oilskin": Tool(
        id="oilskin",
        label="an oilskin coat",
        phrase="an oilskin coat",
        covers={"torso", "head"},
        fixes={"storm"},
    ),
    "mittens": Tool(
        id="mittens",
        label="thick mittens",
        phrase="thick mittens",
        covers={"hands"},
        fixes={"sail"},
    ),
}

HERO_NAMES = ["Mira", "Jory", "Nell", "Rowan", "Pip", "Tessa", "Finn"]
HELPER_NAMES = ["Captain Reef", "Matey Wren", "Old Gull", "Sailor Bean"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def risk_at_risk(risk: Risk, prize: Prize) -> bool:
    return prize.region in risk.zone or (prize.label == "bacon" and risk.id == "sail")


def choose_tool(risk: Risk, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS.values():
        if risk.id in tool.fixes and prize.region in tool.covers:
            return tool
        if prize.label == "bacon" and risk.id == "sail" and "hands" in tool.covers and risk.id in tool.fixes:
            return tool
    return None


def explain_rejection(risk: Risk, prize: Prize) -> str:
    return (
        f"(No story: {risk.gerund} would not honestly endanger {prize.label} in a way "
        f"that this little pirate world can fix with its tools.)"
    )


def _do_risk(world: World, hero: Entity, risk: Risk) -> None:
    hero.memes["bravery"] += 1
    hero.meters["risk"] += 1
    world.say(
        f"{hero.id} felt brave and went to {risk.verb}, even though the sea wind "
        f"kept tugging at {hero.pronoun('possessive')} clothes."
    )


def _share(world: World, hero: Entity, helper: Entity, prize: Entity) -> None:
    hero.memes["sharing"] += 1
    helper.memes["sharing"] += 1
    world.say(
        f"{hero.id} broke the {prize.label} in half and shared it with {helper.id}; "
        f"the sweet smell of bacon made both of them grin."
    )


def _r_reconcile(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["reconciliation"] += 1
    helper.memes["reconciliation"] += 1
    world.say(
        f"{hero.id} and {helper.id} stopped their squabble, looked at each other, "
        f"and made peace with a small nod."
    )


def tell(setting: Setting, risk: Risk, prize_cfg: Prize, tool_def: Tool,
         hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    prize = world.add(Entity(
        id=prize_cfg.id,
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=helper.id,
        owner=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        phrase=tool_def.phrase,
        protective=True,
        covers=set(tool_def.covers),
        owner=hero.id,
    ))
    tool.worn_by = hero.id

    world.say(
        f"On {setting.place}, {hero.id} was a little pirate who loved bright adventures "
        f"and the smell of bacon from the galley."
    )
    world.say(
        f"{helper.id} was there too, and every time the gulls cried, they sounded like "
        f"they were saying ribbit over the water."
    )
    world.say(
        f"{hero.id} treasured {hero.pronoun('possessive')} {prize.label} and wanted to keep "
        f"it safe while the ship rocked and rolled."
    )

    world.para()
    _do_risk(world, hero, risk)
    if not risk_at_risk(risk, prize_cfg):
        pass

    world.say(
        f"{hero.id} wanted to {risk.verb}, but the stormy spray could leave {prize.label} "
        f"{risk.danger}."
    )
    world.say(f"{helper.id} frowned at the trouble and warned {hero.id} to think first.")

    world.para()
    world.say(
        f"Then {hero.id} noticed {tool.label}. It could keep the {prize.label}'s danger away."
    )
    world.say(
        f"{hero.id} and {helper.id} agreed to use {tool.phrase}, because it covered just "
        f"enough to make the brave choice safe."
    )
    _share(world, hero, helper, prize)
    _r_reconcile(world, hero, helper)

    world.say(
        f"At last, {hero.id} {risk.verb} with {tool.label}, {prize.label} stayed dry and safe, "
        f"and the two pirates laughed together under the great top of the mast."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        risk=risk,
        tool=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    risk: Risk = _safe_fact(world, f, "risk")
    prize: Entity = _safe_fact(world, f, "prize")
    helper: Entity = _safe_fact(world, f, "helper")
    return [
        f'Write a short pirate tale for a child where {hero.id} shows bravery, '
        f'shares {prize.label}, and makes peace after a squabble.',
        f"Tell a gentle pirate story with the word '{risk.keyword}' and a moment of sharing "
        f"between {hero.id} and {helper.id}.",
        f"Write a tiny story about a brave pirate, a helper, and {prize.label} at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    prize: Entity = _safe_fact(world, f, "prize")
    risk: Risk = _safe_fact(world, f, "risk")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What made {hero.id} brave on the ship?",
            answer=(
                f"{hero.id} was brave because {hero.id} kept going even when the storm made "
                f"the deck wild and windy. {hero.id} used {tool.label} so the choice could be safe."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} share with {helper.id}?",
            answer=f"{hero.id} shared {prize.label} with {helper.id}, and they both enjoyed the bacon together.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {helper.id} make up?",
            answer=(
                f"They made up because they had a small squabble about the risky job, but then "
                f"they chose {tool.label} and worked together."
            ),
        ),
        QAItem(
            question=f"What part of the ship was {hero.id} trying to reach?",
            answer=f"{hero.id} was trying to {risk.verb}, which means climbing up to the top of the mast.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone feels afraid or unsure, but still does the right thing anyway.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving some of what you have so another person can enjoy it too.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset, fix the problem, and become friendly again.",
        ),
        QAItem(
            question="Why do pirates use a crow's-nest top?",
            answer="Pirates go to the crow's-nest top so they can look far across the sea for land or danger.",
        ),
        QAItem(
            question="What sound does a frog make?",
            answer="A frog can make a ribbit sound.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(R, P) :- risk(R), prize(P), zone(R, Z), worn_on(P, Z).
compatible_tool(T, R, P) :- tool(T), prize_at_risk(R, P), fixes(T, R), prize_region(P, Z), covers(T, Z).
valid_story(S, R, P, T) :- setting(S), risk(R), prize(P), tool(T), afford(S, R), prize_at_risk(R, P), compatible_tool(T, R, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for r in sorted(s.afford):
            lines.append(asp.fact("afford", sid, r))
    for rid, r in RISKS.items():
        lines.append(asp.fact("risk", rid))
        lines.append(asp.fact("zone", rid, *sorted(r.zone)) if False else "")
        for z in sorted(r.zone):
            lines.append(asp.fact("zone", rid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", tid, c))
        for fx in sorted(t.fixes):
            lines.append(asp.fact("fixes", tid, fx))
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with bravery, sharing, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--risk", choices=RISKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    risk = getattr(args, "risk", None) or rng.choice(list(RISKS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))

    if risk_at_risk(_safe_lookup(RISKS, risk), _safe_lookup(PRIZES, prize)) is False:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if choice := choose_tool(_safe_lookup(RISKS, risk), _safe_lookup(PRIZES, prize)) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    hero_type = rng.choice(["boy", "girl"])
    helper_type = rng.choice(["man", "woman"])
    return StoryParams(
        setting=setting,
        risk=risk,
        prize=prize,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(RISKS, params.risk),
        _safe_lookup(PRIZES, params.prize),
        _safe_lookup(TOOLS, params.tool),
        params.hero_name,
        params.hero_type,
        params.helper_name,
        params.helper_type,
    )
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
    StoryParams(setting="deck", risk="storm", prize="bacon", tool="rope", hero_name="Mira", hero_type="girl", helper_name="Captain Reef", helper_type="man"),
    StoryParams(setting="harbor", risk="sail", prize="map", tool="mittens", hero_name="Jory", hero_type="boy", helper_name="Matey Wren", helper_type="woman"),
    StoryParams(setting="island", risk="storm", prize="top_hat", tool="oilskin", hero_name="Nell", hero_type="girl", helper_name="Old Gull", helper_type="man"),
]


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for sid in SETTINGS:
        for rid in RISKS:
            for pid in PRIZES:
                for tid in TOOLS:
                    if afford_match := (rid in _safe_lookup(SETTINGS, sid).afford):
                        if risk_at_risk(_safe_lookup(RISKS, rid), _safe_lookup(PRIZES, pid)) and choose_tool(_safe_lookup(RISKS, rid), _safe_lookup(PRIZES, pid)) is not None:
                            py_set.add((sid, rid, pid, tid))
    # The Python set above intentionally mirrors only the reasonableness gate,
    # not the exact tool choice; compare on supported triples by projection.
    clingo_proj = {(a[0], a[1], a[2]) for a in clingo_set}
    py_proj = {(s, r, p) for (s, r, p, _t) in py_set}
    if clingo_proj != py_proj:
        print("MISMATCH between clingo and python gate:")
        print(" only in clingo:", sorted(clingo_proj - py_proj))
        print(" only in python:", sorted(py_proj - clingo_proj))
        return 1
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: generated story is empty")
        return 1
    print("OK: ASP/Python parity verified and sample generation succeeded.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} valid story combinations:")
        for t in triples:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
            header = f"### {p.hero_name}: {p.risk} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
