#!/usr/bin/env python3
"""
A small story world about a child, a grocer, adhesive, a misunderstanding, and
a heartwarming-but-bad ending.

The seed premise:
- A child needs adhesive for something torn or broken.
- The grocer misunderstands what is needed.
- Kindness remains, but the repair does not fully succeed.

This script is self-contained aside from the shared result containers in
storyworlds/results.py and the optional clingo helper in storyworlds/asp.py.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grocer: object | None = None
    sticky: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


@dataclass
class Setting:
    place: str
    smell: str
    sound: str
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
class RepairTarget:
    id: str
    label: str
    phrase: str
    kind: str
    can_be_fixed_with: set[str]
    can_fail_if: set[str] = field(default_factory=set)
    emotional_value: str = "special"
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
class Adhesive:
    id: str
    label: str
    phrase: str
    strength: str
    works_on: set[str]
    warns: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "corner_store": Setting(
        place="the corner grocer",
        smell="of warm bread and oranges",
        sound="of a little bell over the door",
    )
}

ADHESIVES = {
    "glue": Adhesive(
        id="glue",
        label="a bottle of glue",
        phrase="a bottle of clear glue",
        strength="sticky",
        works_on={"paper", "cardboard", "wood"},
        warns="It works best on dry edges.",
    ),
    "tape": Adhesive(
        id="tape",
        label="a roll of tape",
        phrase="a roll of wide tape",
        strength="quick",
        works_on={"paper", "cardboard"},
        warns="It sticks fast, but it can peel on curved things.",
    ),
}

TARGETS = {
    "kite": RepairTarget(
        id="kite",
        label="kite",
        phrase="a red paper kite",
        kind="paper",
        can_be_fixed_with={"glue", "tape"},
        can_fail_if={"wet", "bent"},
        emotional_value="favorite",
    ),
    "poster": RepairTarget(
        id="poster",
        label="poster",
        phrase="a bright poster with stars",
        kind="paper",
        can_be_fixed_with={"glue", "tape"},
        can_fail_if={"wet"},
        emotional_value="special",
    ),
    "birdhouse": RepairTarget(
        id="birdhouse",
        label="birdhouse",
        phrase="a tiny wooden birdhouse",
        kind="wood",
        can_be_fixed_with={"glue"},
        can_fail_if={"wet", "split"},
        emotional_value="proud",
    ),
}

NAMES = ["Mina", "Leo", "Ivy", "Ben", "Nora", "Owen", "Zoe", "Eli"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    target: str
    adhesive: str
    name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    params: object | None = None
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


ASP_RULES = r"""
% A repair is reasonable when the adhesive works on the target material.
repairable(T, A) :- target(T), adhesive(A), kind(T, K), works_on(A, K).

% A repair can still fail when the target is fragile in the current condition.
bad_end(T, A) :- target(T), adhesive(A), repairable(T, A), can_fail(T, wet).
bad_end(T, A) :- target(T), adhesive(A), repairable(T, A), can_fail(T, bent).

% A story is valid if there is some repairable target with the chosen adhesive.
valid_story(S, T, A) :- setting(S), target(T), adhesive(A), repairable(T, A).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ADHESIVES.items():
        lines.append(asp.fact("adhesive", aid))
        for k in sorted(a.works_on):
            lines.append(asp.fact("works_on", aid, k))
    for tid, t in TARGETS.items():
        lines.append(asp.fact("target", tid))
        lines.append(asp.fact("kind", tid, t.kind))
        for a in sorted(t.can_be_fixed_with):
            lines.append(asp.fact("can_fix", tid, a))
        for c in sorted(t.can_fail_if):
            lines.append(asp.fact("can_fail", tid, c))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_stories() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    if set(valid_combos()) == {(s, t, a) for s, t, a in asp_valid_stories()}:
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos()")
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TARGETS.values():
            for a in ADHESIVES.values():
                if t.kind in a.works_on and a.id in t.can_be_fixed_with:
                    combos.append((s, t.id, a.id))
    return combos

def explain_rejection(target: RepairTarget, adhesive: Adhesive) -> str:
    return (
        f"(No story: {adhesive.label} does not sensibly help with {target.phrase}. "
        f"Choose a target material that the adhesive can actually hold together.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------
def predict_repair(world: World, target: Entity, adhesive: Adhesive) -> dict:
    sim = world.copy()
    sim.get(target.id).meters["damage"] += 1
    sim.get(target.id).memes["hope"] += 1
    failed = "wet" in _safe_lookup(TARGETS, target.id).can_fail_if and adhesive.id == "glue"
    return {"fails": failed}

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    grocer = world.add(Entity(id="Grocer", kind="character", type="grocer", label="the grocer"))
    target_cfg = _safe_lookup(TARGETS, params.target)
    adhesive_cfg = _safe_lookup(ADHESIVES, params.adhesive)
    target = world.add(Entity(
        id=target_cfg.id,
        kind="thing",
        type=target_cfg.kind,
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        owner=child.id,
        caretaker=grocer.id,
    ))
    sticky = world.add(Entity(
        id=adhesive_cfg.id,
        kind="thing",
        type="adhesive",
        label=adhesive_cfg.label,
        phrase=adhesive_cfg.phrase,
        owner=grocer.id,
    ))

    child.memes["need"] = 1
    child.memes["worry"] = 1
    grocer.memes["kindness"] = 1
    grocer.memes["attention"] = 1
    target.meters["damage"] = 1
    target.meters["precious"] = 1

    world.say(
        f"{child.id} stood outside {world.setting.place}, where the air had a little "
        f"smell {world.setting.smell} and the doorway had {world.setting.sound}."
    )
    world.say(
        f"{child.id} was holding {target.phrase}. One torn edge kept flapping, and "
        f"{child.pronoun('possessive')} heart felt small."
    )

    world.para()
    world.say(
        f"Inside, {child.id} asked the grocer for {sticky.phrase} to fix it."
    )
    world.say(
        f"But the grocer misunderstood and thought {child.id} wanted help with a "
        f"paper sign in the window."
    )
    world.say(
        f"{grocer.pronoun().capitalize()} brought out {sticky.label} and nodded, "
        f"as if that solved everything."
    )
    child.memes["confusion"] = 1
    grocer.memes["confusion"] = 1

    world.para()
    if target_cfg.kind == "paper":
        world.say(
            f"Together they tried to press the torn edges flat, while {world.setting.place} "
            f"kept buzzing softly around them."
        )
    else:
        world.say(
            f"Together they tried to press the split wood flat, careful not to chip the "
            f"little corners."
        )

    outcome = predict_repair(world, target, adhesive_cfg)
    if outcome["fails"]:
        target.meters["damage"] += 1
        target.memes["hope"] -= 1
        child.memes["sadness"] = 1
        grocer.memes["regret"] = 1
        world.say(
            f"The glue did not hold. The damp place on the tear made the patch slide off, "
            f"and the piece drooped even more."
        )
        world.say(
            f"{child.id} blinked fast, because the fix was not a fix at all."
        )
        world.para()
        world.say(
            f"Then the grocer did something kinder than fixing it: {grocer.pronoun().capitalize()} "
            f"set out a paper bag, two warm buns, and a strip of plain cardboard."
        )
        world.say(
            f"{grocer.pronoun().capitalize()} said, 'We can still make something gentle out of this.' "
            f"{child.id} sat beside {grocer.pronoun('object')} and nodded."
        )
        target.memes["comfort"] = 1
        child.memes["comfort"] = 1
        world.say(
            f"They made a tiny collage together, but {target_cfg.phrase} stayed torn in the end. "
            f"{child.id} carried it home carefully, and the grocer waved from the door with a soft smile."
        )
    else:
        target.meters["repaired"] = 1
        child.memes["relief"] = 1
        world.say(
            f"This time the adhesive held the tear closed, and the object looked steadier, "
            f"though it still had a little scar."
        )
        world.say(
            f"{child.id} smiled, and the grocer smiled back, pleased that patience had helped."
        )

    world.facts.update(
        child=child,
        grocer=grocer,
        target=target,
        target_cfg=target_cfg,
        adhesive_cfg=adhesive_cfg,
        outcome="bad" if outcome["fails"] else "good",
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming short story for a young child about a grocer and a child named {f["child"].id} who needs {f["adhesive_cfg"].label}.',
        f"Tell a story where {f['child'].id} asks for {f['adhesive_cfg'].phrase} but the grocer misunderstands and the repair goes wrong.",
        f"Write a gentle shop story that ends with kindness even though {f['target_cfg'].phrase} is not fully fixed.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    grocer: Entity = _safe_fact(world, f, "grocer")
    target_cfg: RepairTarget = _safe_fact(world, f, "target_cfg")
    adhesive_cfg: Adhesive = _safe_fact(world, f, "adhesive_cfg")
    target: Entity = _safe_fact(world, f, "target")
    qa = [
        QAItem(
            question=f"What did {child.id} bring to the grocer's shop?",
            answer=f"{child.id} brought {target_cfg.phrase} and hoped {adhesive_cfg.label} would help mend it.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding at the shop?",
            answer=f"The grocer thought {child.id} wanted help with a sign, not with {target_cfg.phrase}, so the wrong kind of help was prepared first.",
        ),
        QAItem(
            question=f"What happened when they tried the adhesive?",
            answer=f"The adhesive did not hold the torn part together, so the repair did not work the way {child.id} hoped.",
        ),
    ]
    if f["outcome"] == "bad":
        qa.append(QAItem(
            question=f"How did the story end for {target.label}?",
            answer=f"It ended sadly for the object itself: {target_cfg.phrase} stayed torn, even though the grocer and {child.id} were gentle with each other.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did the story end for {target.label}?",
            answer=f"It ended with a small repair and a kind smile from the grocer, even though the object still showed a little scar.",
        ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is adhesive used for?",
            answer="Adhesive is used to make things stick together, like paper, cardboard, or wood.",
        ),
        QAItem(
            question="Who is a grocer?",
            answer="A grocer is a person who sells food and useful things in a small shop.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming adhesive-and-grocer story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--adhesive", choices=ADHESIVES)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "target", None):
        combos = [c for c in combos if c[1] == getattr(args, "target", None)]
    if getattr(args, "adhesive", None):
        combos = [c for c in combos if c[2] == getattr(args, "adhesive", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, target, adhesive = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, target=target, adhesive=adhesive, name=name)

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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            bits = []
            if meters:
                bits.append(f"meters={meters}")
            if memes:
                bits.append(f"memes={memes}")
            print(f"{e.id}: {e.kind} {e.type} {' '.join(bits)}")
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
        for s, t, a in stories:
            print(f"{s} {t} {a}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for setting, target, adhesive in valid_combos():
            params = StoryParams(setting=setting, target=target, adhesive=adhesive, name="Mina")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
