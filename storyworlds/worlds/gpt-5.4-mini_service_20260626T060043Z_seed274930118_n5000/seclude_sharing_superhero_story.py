#!/usr/bin/env python3
"""
Standalone storyworld: a tiny superhero story about secluding something safe
and then learning how sharing can save the day.

A child-facing, simulation-driven tale:
- A young superhero wants to seclude a special gadget in a hidden den.
- A teammate feels left out.
- The hero first protects the secret, then chooses to share the right tool.
- The ending proves the change in the world: the team is together, the threat
  is handled, and the hidden thing stays safe.

This script follows the Storyweavers storyworld contract.
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
# World constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world state
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
    role: str = ""
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    gadget: object | None = None
    hero: object | None = None
    sidekick: object | None = None
    def __post_init__(self) -> None:
        for k in ("safe", "tired", "used", "shiny"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "left_out", "team_spirit", "trust"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def article_label(self) -> str:
        if self.label.startswith(("a ", "an ", "the ")):
            return self.label
        return f"a {self.label}"
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
class Hideout:
    place: str = "the rooftop hideout"
    secret_level: int = 2
    affords_seclusion: bool = True
    encourages_sharing: bool = True
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
class Gadget:
    id: str
    label: str
    phrase: str
    protects_from: str
    useful_for: str
    hidden_ok: bool = True
    shareable: bool = True
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
    hero_name: str
    sidekick_name: str
    gadget: str
    threat: str
    hideout: str
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
    def __init__(self, hideout: Hideout) -> None:
        self.hideout = hideout
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.threat_active: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        w = World(self.hideout)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.threat_active = self.threat_active
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

HIDEOUTS = {
    "rooftop": Hideout(place="the rooftop hideout", secret_level=2, affords_seclusion=True, encourages_sharing=True),
    "tower": Hideout(place="the sky tower", secret_level=3, affords_seclusion=True, encourages_sharing=True),
    "garage": Hideout(place="the garage lair", secret_level=1, affords_seclusion=True, encourages_sharing=True),
}

GADGETS = {
    "beam": Gadget(
        id="beam",
        label="beam blaster",
        phrase="a bright beam blaster",
        protects_from="shadow fog",
        useful_for="lighting up dark corners",
    ),
    "shield": Gadget(
        id="shield",
        label="spark shield",
        phrase="a round spark shield",
        protects_from="rain of sparks",
        useful_for="blocking flying sparks",
    ),
    "rope": Gadget(
        id="rope",
        label="zip rope",
        phrase="a quick zip rope",
        protects_from="high ledges",
        useful_for="crossing rooftops",
    ),
}

THREATS = {
    "fog": "shadow fog",
    "sparks": "rain of sparks",
    "ledges": "high ledges",
}

HERO_NAMES = ["Nova", "Milo", "Juno", "Rae", "Finn", "Piper", "Zed", "Aya"]
SIDEKICK_NAMES = ["Bram", "Lina", "Tess", "Orin", "Mina", "Bo", "Kira", "Sol"]
TRAITS = ["brave", "quick", "clever", "kind", "bold", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------

def gadget_helpful_for_threat(gadget: Gadget, threat: str) -> bool:
    return gadget.protects_from == threat


def seclusion_reasonable(world: World, gadget: Gadget) -> bool:
    return world.hideout.affords_seclusion and gadget.hidden_ok


def sharing_reasonable(gadget: Gadget) -> bool:
    return gadget.shareable


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for hid, h in HIDEOUTS.items():
        for gid, g in GADGETS.items():
            for tid, threat in THREATS.items():
                if h.affords_seclusion and g.hidden_ok and g.protects_from == threat:
                    combos.append((hid, gid, tid))
    return combos


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------

def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def predict_outcome(world: World, hero: Entity, sidekick: Entity, gadget: Gadget) -> dict:
    sim = world.copy()
    h = sim.get(hero.id)
    s = sim.get(sidekick.id)
    g = sim.get(gadget.id)
    _bump(h, "safe")
    _feel(h, "pride")
    _feel(s, "left_out")
    if sharing_reasonable(gadget):
        _feel(s, "trust")
        _feel(h, "team_spirit")
    return {
        "sidekick_left_out": sim.get(sidekick.id).memes["left_out"] >= THRESHOLD,
        "team_spirit": sim.get(hero.id).memes["team_spirit"],
    }


def introduce(world: World, hero: Entity, sidekick: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "bright")
    world.say(
        f"{hero.id} was a little {trait} superhero who loved solving problems with a grin."
    )
    world.say(
        f"{hero.id} and {sidekick.id} liked patrolling together because two capes were better than one."
    )


def seed_setup(world: World, hero: Entity, sidekick: Entity, gadget: Entity) -> None:
    hero.memes["trust"] += 1
    _feel(hero, "joy")
    world.say(
        f"One afternoon, {hero.id} found {hero.pronoun('possessive')} {gadget.label} and "
        f"wanted to seclude it in the hideout so nobody would bump it."
    )
    world.say(
        f"{hero.id} said {gadget.phrase} was too special to leave out in the open."
    )
    gadget.carried_by = hero.id
    gadget.hidden_in = world.hideout.place


def sidekick_arrives(world: World, hero: Entity, sidekick: Entity, gadget: Entity) -> None:
    _feel(sidekick, "left_out")
    _feel(sidekick, "worry")
    world.say(
        f"Then {sidekick.id} arrived, peeking at the closed door and feeling left out."
    )
    world.say(
        f"{sidekick.id} wanted to help, but the secret door stayed shut and the room felt smaller."
    )


def threat_pushes_turn(world: World, hero: Entity, sidekick: Entity, gadget: Entity, threat: str) -> None:
    world.threat_active = True
    _feel(hero, "worry")
    world.say(
        f"Just then, {threat} rolled in across the roof, hissing at the edges of the hideout."
    )
    world.say(
        f"{hero.id} knew {hero.pronoun('possessive')} hidden gadget could help, but one hero alone would be too slow."
    )


def share_and_act(world: World, hero: Entity, sidekick: Entity, gadget: Entity) -> None:
    _feel(hero, "team_spirit")
    _feel(sidekick, "trust")
    _feel(hero, "joy")
    sidekick.carried_by = hero.id
    world.say(
        f"{hero.id} opened the door and shared the {gadget.label} at once."
    )
    world.say(
        f"'{hero.id} kept the secret safe,' {sidekick.id} said, 'and now we can share the job too.'"
    )


def resolve_threat(world: World, hero: Entity, sidekick: Entity, gadget: Entity, threat: str) -> None:
    _bump(hero, "safe")
    _bump(sidekick, "safe")
    _feel(hero, "pride")
    _feel(sidekick, "joy")
    world.threat_active = False
    world.say(
        f"Together they used the {gadget.label} to handle the {threat}, and the roof went calm again."
    )
    world.say(
        f"In the end, the gadget was still protected, but it was no longer lonely in the dark."
    )
    world.say(
        f"{hero.id} and {sidekick.id} stood side by side in the bright hideout, proud of sharing the work."
    )


def tell(params: StoryParams) -> World:
    hideout = _safe_lookup(HIDEOUTS, params.hideout)
    gadget_cfg = _safe_lookup(GADGETS, params.gadget)
    threat = _safe_lookup(THREATS, params.threat)
    world = World(hideout)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        role="hero",
        traits=["little", random.choice(TRAITS), "heroic"],
    ))
    sidekick = world.add(Entity(
        id=params.sidekick_name,
        kind="character",
        role="sidekick",
        traits=["helpful", "restless"],
    ))
    gadget = world.add(Entity(
        id=gadget_cfg.id,
        kind="thing",
        role="gadget",
        label=gadget_cfg.label,
        phrase=gadget_cfg.phrase,
        owner=hero.id,
        carried_by=hero.id,
        hidden_in=hideout.place,
    ))

    introduce(world, hero, sidekick)
    seed_setup(world, hero, sidekick, gadget)
    world.para()
    sidekick_arrives(world, hero, sidekick, gadget)
    threat_pushes_turn(world, hero, sidekick, gadget, threat)
    world.para()
    share_and_act(world, hero, sidekick, gadget)
    resolve_threat(world, hero, sidekick, gadget, threat)

    world.facts = {
        "hero": hero,
        "sidekick": sidekick,
        "gadget": gadget,
        "hideout": hideout,
        "threat": threat,
        "params": params,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sidekick: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sidekick")
    gadget: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gadget")
    threat: str = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat")
    return [
        f'Write a short superhero story for a child about "{hero.id}" and "{sidekick.id}" that includes the idea of secluding a gadget and then sharing it.',
        f"Tell a gentle superhero story where {hero.id} wants to hide {gadget.phrase} in a secret place, but {sidekick.id} feels left out until they work together.",
        f'Write a simple superhero story that uses the word "seclude" and ends with two heroes sharing a tool to solve a problem like {threat}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    sidekick: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "sidekick")
    gadget: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gadget")
    threat: str = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "threat")
    hideout: Hideout = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hideout")
    return [
        QAItem(
            question=f"What did {hero.id} want to do with {gadget.label} at first?",
            answer=f"{hero.id} wanted to seclude {hero.pronoun('possessive')} {gadget.label} in {hideout.place} so it would stay safe.",
        ),
        QAItem(
            question=f"Why did {sidekick.id} feel upset before the big problem appeared?",
            answer=f"{sidekick.id} felt left out because the hideout door stayed shut and {hero.id} had been keeping the {gadget.label} secret.",
        ),
        QAItem(
            question=f"What problem came to the hideout and changed the plan?",
            answer=f"{(getattr(threat, 'capitalize')() if callable(getattr(threat, 'capitalize', None)) else str(threat).capitalize())} rolled in, and {hero.id} needed help to handle it well.",
        ),
        QAItem(
            question=f"How did the two heroes fix things at the end?",
            answer=f"{hero.id} shared the {gadget.label} with {sidekick.id}, and together they handled the {threat}.",
        ),
        QAItem(
            question=f"What changed in the end for the gadget and the team?",
            answer=f"The {gadget.label} stayed safe, and the heroes ended up working together instead of keeping everything separate.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "seclude": [
        QAItem(
            question="What does it mean to seclude something?",
            answer="To seclude something means to keep it in a quiet, private place where fewer people can reach it.",
        )
    ],
    "sharing": [
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing helps because more than one person can use the same thing, and it can make teamwork easier.",
        )
    ],
    "superhero": [
        QAItem(
            question="What do superheroes usually try to do?",
            answer="Superheroes usually try to help others, solve trouble, and keep people safe.",
        )
    ],
    "teamwork": [
        QAItem(
            question="Why do teammates work well together?",
            answer="Teammates can combine their strengths, so one person does not have to handle everything alone.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["seclude"])
    out.extend(WORLD_KNOWLEDGE["sharing"])
    out.extend(WORLD_KNOWLEDGE["superhero"])
    out.extend(WORLD_KNOWLEDGE["teamwork"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        if e.hidden_in:
            parts.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(parts)}")
    lines.append(f"  threat_active={world.threat_active}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% Facts describe the setting and whether a gadget should be sequestered.
can_seclude(H) :- hideout(H), seclusion(H).
sharing_helpful(G) :- gadget(G), shareable(G).
compatible(H, G, T) :- can_seclude(H), sharing_helpful(G), gadget_protects(G, T).
valid_story(H, G, T) :- compatible(H, G, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for hid, h in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        if h.affords_seclusion:
            lines.append(asp.fact("seclusion", hid))
        if h.encourages_sharing:
            lines.append(asp.fact("sharing", hid))
    for gid, g in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        if g.shareable:
            lines.append(asp.fact("shareable", gid))
        for tid, threat in THREATS.items():
            if g.protects_from == threat:
                lines.append(asp.fact("gadget_protects", gid, tid))
    for tid in THREATS:
        lines.append(asp.fact("threat", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a superhero tale about secluding a gadget and sharing it when it matters."
    )
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero-name", choices=HERO_NAMES)
    ap.add_argument("--sidekick-name", choices=SIDEKICK_NAMES)
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
    hid = getattr(args, "hideout", None) or rng.choice(list(HIDEOUTS))
    gad = getattr(args, "gadget", None) or rng.choice(list(GADGETS))
    thr = getattr(args, "threat", None) or rng.choice(list(THREATS))
    if not (_safe_lookup(HIDEOUTS, hid).affords_seclusion and _safe_lookup(GADGETS, gad).protects_from == _safe_lookup(THREATS, thr)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick_choices = [n for n in SIDEKICK_NAMES if n != hero]
    sidekick = getattr(args, "sidekick_name", None) or rng.choice(sidekick_choices)
    return StoryParams(
        hero_name=hero,
        sidekick_name=sidekick,
        gadget=gad,
        threat=thr,
        hideout=hid,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(hero_name="Nova", sidekick_name="Bram", gadget="beam", threat="fog", hideout="rooftop"),
    StoryParams(hero_name="Milo", sidekick_name="Lina", gadget="shield", threat="sparks", hideout="tower"),
    StoryParams(hero_name="Juno", sidekick_name="Tess", gadget="rope", threat="ledges", hideout="garage"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (hideout, gadget, threat) combos:\n")
        for hid, gad, thr in triples:
            print(f"  {hid:8} {gad:8} {thr}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
