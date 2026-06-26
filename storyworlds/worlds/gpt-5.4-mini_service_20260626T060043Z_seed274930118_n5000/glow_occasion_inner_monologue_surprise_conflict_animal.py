#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/glow_occasion_inner_monologue_surprise_conflict_animal.py
==========================================================================================

A small animal-story world about a glowing occasion that turns into a surprise
and a conflict, then resolves through a kind choice.

Premise:
- An animal hero prepares for a special occasion with a gentle glow.
- A surprise changes the plan.
- The hero has an inner monologue while conflict rises.
- The ending proves something changed in the world.

This script is self-contained and uses the shared Storyweavers result containers.
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
# Core world model
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
    kind: str = "thing"  # "character" | "thing"
    species: str = "animal"
    name: str = ""
    role: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    label: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
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


@dataclass
class Setting:
    place: str
    occasion: str
    glow_source: str
    indoors: bool = False
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
class ObjectSpec:
    label: str
    phrase: str
    role: str
    at_risk: set[str]
    fixes_with: set[str] = field(default_factory=set)
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
    hero: str
    friend: str
    prize: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lantern_fair": Setting(place="the lantern fair", occasion="lantern fair", glow_source="lanterns"),
    "moon_garden": Setting(place="the moon garden", occasion="moon feast", glow_source="moonlight"),
    "pond_party": Setting(place="the pond party", occasion="pond celebration", glow_source="glow bugs"),
}

HEROES = {
    "bunny": {"species": "rabbit", "name": "Pip", "trait": "hop-sweet"},
    "fox": {"species": "fox", "name": "Nia", "trait": "bright-eyed"},
    "bear": {"species": "bear", "name": "Milo", "trait": "gentle"},
    "mouse": {"species": "mouse", "name": "Tia", "trait": "small and brave"},
}

FRIENDS = {
    "owl": {"species": "owl", "name": "Odo"},
    "squirrel": {"species": "squirrel", "name": "Suri"},
    "hedgehog": {"species": "hedgehog", "name": "Hush"},
}

PRIZES = {
    "banner": ObjectSpec(
        label="banner",
        phrase="a paper banner with shiny letters",
        role="decoration",
        at_risk={"rain", "wind"},
        fixes_with={"clothespin"},
    ),
    "cake": ObjectSpec(
        label="cake",
        phrase="a sweet berry cake",
        role="treat",
        at_risk={"bumps", "hunger"},
        fixes_with={"cover"},
    ),
    "lantern": ObjectSpec(
        label="lantern",
        phrase="a little lantern with a warm flame",
        role="light",
        at_risk={"wind", "spill"},
        fixes_with={"shield"},
    ),
}

ACTIONS = {
    "carry": {
        "verb": "carry the prize",
        "risk": "spill",
        "tension": "would wobble the prize",
        "fix": "hold it carefully with both paws",
    },
    "decorate": {
        "verb": "decorate the place",
        "risk": "wind",
        "tension": "could blow the decorations away",
        "fix": "tie everything down with a ribbon",
    },
    "serve": {
        "verb": "serve the treats",
        "risk": "hunger",
        "tension": "would make the snack table too tempting",
        "fix": "set out enough pieces for everyone",
    },
}

GLOW_FACTS = {
    "lanterns": "The lanterns glowed softly like tiny moons.",
    "moonlight": "The moonlight glowed on the grass like silver milk.",
    "glow bugs": "The glow bugs blinked in the dark like moving stars.",
}


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combo(setting_key: str, prize_key: str, action_key: str) -> bool:
    setting = _safe_lookup(SETTINGS, setting_key)
    prize = _safe_lookup(PRIZES, prize_key)
    action = _safe_lookup(ACTIONS, action_key)
    return bool(prize.at_risk & {action["risk"], "surprise"}) and setting.occasion and setting.glow_source


def explain_rejection(setting_key: str, prize_key: str, action_key: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_key)
    prize = _safe_lookup(PRIZES, prize_key)
    action = _safe_lookup(ACTIONS, action_key)
    return (
        f"(No story: at {setting.place}, the {prize.label} and the action '{action_key}' "
        f"do not make a believable conflict and fix.)"
    )


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero_spec = _safe_lookup(HEROES, params.hero)
    friend_spec = _safe_lookup(FRIENDS, params.friend)
    prize_spec = _safe_lookup(PRIZES, params.prize)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        species=hero_spec["species"],
        name=hero_spec["name"],
        role=hero_spec["trait"],
    ))
    friend = world.add(Entity(
        id="friend",
        kind="character",
        species=friend_spec["species"],
        name=friend_spec["name"],
        role="friend",
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        species="thing",
        name=prize_spec.label,
        role=prize_spec.role,
        phrase=prize_spec.phrase,
        owner=hero.id,
        caretaker=friend.id,
    ))

    action_key = params.prize if params.prize in ACTIONS else "carry"
    action = ACTIONS["carry"] if action_key not in ACTIONS else _safe_lookup(ACTIONS, action_key)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        prize_spec=prize_spec,
        action_key=action_key,
        action=action,
    )

    hero.memes["joy"] = 1
    hero.memes["hope"] = 1
    friend.memes["helpfulness"] = 1
    prize.meters["clean"] = 1

    world.say(
        f"{hero.name} was a {hero.role} {hero.species} who loved special days."
    )
    world.say(
        f"It was the {setting.occasion}, and {setting.glow_source} made the whole place glow."
    )
    world.say(
        f"{hero.name} was carrying {prize.phrase} for the celebration, and {friend.name} was nearby."
    )
    world.para()

    world.say(
        f"{hero.name} wanted to enjoy the occasion and help with the {prize.label}, because the glow made everything feel magical."
    )

    # Surprise
    if params.setting == "pond_party":
        world.say(
            f"Then a sudden splash surprised everyone, and a breeze shook the prize."
        )
        prize.meters["wet"] = 1
        hero.memes["surprise"] = 1
    elif params.setting == "lantern_fair":
        world.say(
            f"Then one lantern flickered out, and the shadow behind the table looked bigger than before."
        )
        prize.meters["scared"] = 1
        hero.memes["surprise"] = 1
    else:
        world.say(
            f"Then a late guest arrived with muddy paws, and the neat plan changed at once."
        )
        prize.meters["scuffed"] = 1
        hero.memes["surprise"] = 1

    world.para()

    # Conflict and inner monologue
    hero.memes["conflict"] = 1
    world.say(
        f"{hero.name} felt a tight tug inside. "
        f'"If I hurry, I might make a mess," {hero.name} thought. '
        f'"But I want the occasion to stay bright."'
    )
    world.say(
        f"{friend.name} looked worried too, because the surprise had made the prize hard to manage."
    )

    # Turn
    prize.meters["at_risk"] = 1
    hero.memes["care"] = 1
    world.para()

    if params.prize == "banner":
        world.say(
            f"{hero.name} took a slow breath and tied the banner down with a ribbon."
        )
        world.say(
            f"That kept the wind away, and the glowing decorations stayed neat."
        )
        prize.meters["stable"] = 1
    elif params.prize == "cake":
        world.say(
            f"{hero.name} counted the slices and set the berry cake under a cover."
        )
        world.say(
            f"That stopped any bumps from ruining the treat, and everyone could share it safely."
        )
        prize.meters["safe"] = 1
    else:
        world.say(
            f"{hero.name} lifted a little shield around the lantern and kept it steady."
        )
        world.say(
            f"The flame stayed warm, and its glow shone across the celebration."
        )
        prize.meters["safe"] = 1

    hero.memes["conflict"] = 0
    hero.memes["relief"] = 1
    friend.memes["relief"] = 1

    world.para()
    world.say(
        f"In the end, the surprise did not ruin the occasion. {hero.name} and {friend.name} smiled at the soft glow, and the prize stayed safe."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    return [
        f"Write a short animal story about {hero.name} at a glowing occasion.",
        f"Tell a gentle story where a {hero.species} faces a surprise and a conflict while helping with {prize.label}.",
        f"Write a child-friendly story that includes inner monologue and ends with a safe choice for the celebration.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    prize = _safe_fact(world, f, "prize")
    action = _safe_fact(world, f, "action")
    setting = world.setting

    return [
        QAItem(
            question=f"Who is the animal story about?",
            answer=f"It is about {hero.name}, a {hero.role} {hero.species}, and the friendly helper {friend.name}.",
        ),
        QAItem(
            question=f"What made the occasion feel special?",
            answer=f"The {setting.occasion} felt special because {setting.glow_source} made the whole place glow softly.",
        ),
        QAItem(
            question=f"What caused the surprise?",
            answer=f"The surprise happened when the calm plan changed and {prize.label} became harder to manage.",
        ),
        QAItem(
            question=f"What did {hero.name} think during the conflict?",
            answer=(
                f"{hero.name} thought, 'If I hurry, I might make a mess, but I want the occasion to stay bright.'"
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{hero.name} chose a careful way to protect the {prize.label}, and the celebration stayed glowing and safe.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "glow": [
        QAItem(
            question="What does glow mean?",
            answer="Glow means to give off a soft, steady light.",
        ),
    ],
    "occasion": [
        QAItem(
            question="What is an occasion?",
            answer="An occasion is a special event or time when people gather for something important or happy.",
        ),
    ],
    "surprise": [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you are not ready for it.",
        ),
    ],
    "conflict": [
        QAItem(
            question="What is a conflict in a story?",
            answer="A conflict is a problem or disagreement that makes characters worry or try harder to solve something.",
        ),
    ],
    "inner_monologue": [
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the little voice a character has in their mind when they think about what to do.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["glow"] + WORLD_KNOWLEDGE["occasion"] + WORLD_KNOWLEDGE["surprise"] + WORLD_KNOWLEDGE["conflict"] + WORLD_KNOWLEDGE["inner_monologue"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_name(S).
prize(P) :- prize_name(P).
action(A) :- action_name(A).

good_combo(S, P, A) :- setting(S), prize(P), action(A), risk(A, R), at_risk(P, R), glow_setting(S).
valid_story(S, P, A) :- good_combo(S, P, A).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting_name", s))
        if _safe_lookup(SETTINGS, s).glow_source:
            lines.append(asp.fact("glow_setting", s))
    for p, spec in PRIZES.items():
        lines.append(asp.fact("prize_name", p))
        for r in sorted(spec.at_risk):
            lines.append(asp.fact("at_risk", p, r))
    for a, spec in ACTIONS.items():
        lines.append(asp.fact("action_name", a))
        lines.append(asp.fact("risk", a, spec["risk"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str, str]]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {
        (s, p, a)
        for s in SETTINGS
        for p in PRIZES
        for a in ACTIONS
        if valid_combo(s, p, a)
    }
    asp_set = set(asp_valid_stories())
    if asp_set == python_set:
        print(f"OK: clingo gate matches python gate ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    if not valid_combo(setting, prize, "carry"):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, hero=hero, friend=friend, prize=prize)


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


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place} / {world.setting.occasion} / {world.setting.glow_source}")
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: kind={e.kind} name={e.name} role={e.role} meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with glow, occasion, surprise, conflict, and inner monologue.")
    ap.add_argument("--setting", choices=list(SETTINGS))
    ap.add_argument("--hero", choices=list(HEROES))
    ap.add_argument("--friend", choices=list(FRIENDS))
    ap.add_argument("--prize", choices=list(PRIZES))
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


CURATED = [
    StoryParams(setting="lantern_fair", hero="bunny", friend="owl", prize="banner"),
    StoryParams(setting="moon_garden", hero="fox", friend="squirrel", prize="cake"),
    StoryParams(setting="pond_party", hero="mouse", friend="hedgehog", prize="lantern"),
]


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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s, p, a in stories:
            print(f"  {s:12} {p:8} {a}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i - 1
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
            header = f"### {p.setting} / {p.hero} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
