#!/usr/bin/env python3
"""
storyworlds/worlds/fanny_sillybilly_prank_foreshadowing_detective_story.py
===========================================================================

A small detective-style storyworld about foreshadowed pranks, clues, and a
gentle solve.

Seed tale idea:
---
At the quiet school fair, Detective Fanny noticed little clues before the prank
even happened: a dropped feather, a half-hidden grin, and sticky jam on the
floor. Sillybilly kept acting innocent, but the clues pointed everywhere.
Fanny followed the signs, found the prank in time, and turned the trouble into
a laugh instead of a disaster.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    targeted: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    suspect: object | None = None
    victim: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
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
    indoors: bool = False
    atmosphere: str = "quiet"
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
class Prank:
    id: str
    title: str
    verb: str
    clue: str
    mess: str
    consequence: str
    foreshadow: list[str]
    cleanup: str
    keyword: str = "prank"
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
class StoryParams:
    place: str
    prank: str
    detective_name: str
    detective_kind: str
    suspect_name: str
    suspect_kind: str
    victim_name: str
    victim_kind: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_clue_chain(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    prank = _safe_fact(world, world.facts, "prank")
    for clue in prank.foreshadow:
        sig = ("clue", clue)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        detective.memes["curiosity"] += 1
        out.append(clue)
    return out


def _r_prank_revealed(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    prank = _safe_fact(world, world.facts, "prank")
    if detective.memes.get("curiosity", 0) < THRESHOLD:
        return []
    if suspect.memes.get("nervous", 0) < THRESHOLD:
        return []
    sig = ("reveal", prank.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["caught"] = 1.0
    detective.memes["confidence"] += 1
    return [f"__reveal__:{prank.title}"]


CAUSAL_RULES = [_r_clue_chain, _r_prank_revealed]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule(world)
            if parts:
                changed = True
                produced.extend(parts)
    if narrate:
        for line in produced:
            if not line.startswith("__reveal__:"):
                world.say(line)
    return produced


SETTINGS = {
    "school": Setting(
        place="the quiet school fair",
        indoors=False,
        atmosphere="careful",
        affords={"prank"},
    ),
    "library": Setting(
        place="the little library",
        indoors=True,
        atmosphere="hushed",
        affords={"prank"},
    ),
    "garden": Setting(
        place="the neighbor's garden party",
        indoors=False,
        atmosphere="bright",
        affords={"prank"},
    ),
}

PRANKS = {
    "feather": Prank(
        id="feather",
        title="the feather prank",
        verb="hide a paper badge and scatter feather fluff",
        clue="A white feather kept turning up in the same hallway corner.",
        mess="feather fluff",
        consequence="everyone would think the wind had come inside",
        foreshadow=[
            "First, Fanny found a white feather on the floor.",
            "Then she spotted a tiny trail of fluff near the snack table.",
            "Last, there was a single dropped grin-shaped sticker by the curtain.",
        ],
        cleanup="sweep up the fluff and smooth the badges back into place",
    ),
    "ink": Prank(
        id="ink",
        title="the ink prank",
        verb="swap a pen with a leaky one",
        clue="A dark blue dot kept appearing on the desk edge.",
        mess="ink spots",
        consequence="one good note would end up blotched",
        foreshadow=[
            "First, Fanny noticed a dark blue dot on the desk edge.",
            "Then she saw a wet stripe on a sleeve cuff.",
            "Last, a pen cap rolled out from under a chair like it was trying to escape.",
        ],
        cleanup="replace the pen, wipe the desk, and dry the page",
    ),
    "jelly": Prank(
        id="jelly",
        title="the jelly prank",
        verb="hide a jelly sandwich where it should not be",
        clue="A sweet smell drifted from the wrong corner of the room.",
        mess="sticky jam",
        consequence="the carpet would get sticky",
        foreshadow=[
            "First, Fanny smelled something sweet near the back wall.",
            "Then she found a shiny crumb trail under the bench.",
            "Last, a napkin was folded in a way that looked far too careful.",
        ],
        cleanup="carry the sandwich away and wipe the sticky spot",
    ),
}

TYPES = ["girl", "boy", "cat", "dog"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prank_id) for place, s in SETTINGS.items() for prank_id in s.affords if prank_id in PRANKS]


@dataclass
class WorldFacts:
    detective: Entity
    suspect: Entity
    victim: Entity
    prank: Prank
    setting: Setting
    solved: bool = False
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


def tell(setting: Setting, prank: Prank, detective_name: str, detective_kind: str,
         suspect_name: str, suspect_kind: str, victim_name: str, victim_kind: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_kind,
        label=detective_name,
        traits=["careful", "smart"],
        meters={"attention": 0.0},
        memes={"curiosity": 0.0, "confidence": 0.0},
    ))
    suspect = world.add(Entity(
        id="suspect",
        kind="character",
        type=suspect_kind,
        label=suspect_name,
        traits=["silly", "wiggly"],
        meters={},
        memes={"nervous": 0.0, "guilt": 0.0},
    ))
    victim = world.add(Entity(
        id="victim",
        kind="character",
        type=victim_kind,
        label=victim_name,
        traits=["kind"],
        meters={},
        memes={"surprise": 0.0},
    ))

    world.facts.update(
        detective=detective,
        suspect=suspect,
        victim=victim,
        prank=prank,
        setting=setting,
    )

    world.say(
        f"{detective.label} was a young detective who liked quiet places and little clues."
    )
    world.say(
        f"At {setting.place}, {victim.label} was getting ready for the day, "
        f"and {suspect.label} kept wandering by with a too-bright smile."
    )
    world.say(
        f"Even before anything happened, {detective.label} noticed the signs: "
        f"{prank.foreshadow[0].lower()}"
    )

    world.para()
    detective.meters["attention"] += 1
    detective.memes["curiosity"] += 1
    suspect.memes["nervous"] += 0.5
    victim.memes["surprise"] += 0.5
    world.say(
        f"The place felt {setting.atmosphere}, but the clues did not match the calm."
    )
    world.say(prank.foreshadow[1])
    world.say(
        f"{detective.label} followed the clue and found it led toward {suspect.label}."
    )
    propagate(world, narrate=True)

    world.para()
    suspect.memes["nervous"] += 1.0
    world.say(
        f"{suspect.label} tried to look innocent, but {detective.label} had already "
        f"noticed {prank.foreshadow[2].lower()}"
    )
    world.say(
        f'"Was it you?" asked {detective.label}. {suspect.label} fidgeted, then sighed.'
    )
    world.say(
        f'"I only meant to make a silly {prank.keyword}," {suspect.label} admitted.'
    )
    reveal = f"The prank was {prank.title}, and it would have made {prank.consequence}."
    world.say(reveal)
    propagate(world, narrate=True)

    world.para()
    detective.memes["confidence"] += 1
    victim.memes["surprise"] += 1
    world.say(
        f"{detective.label} did not shout. Instead, {detective.label} showed the clues "
        f"one by one and explained how they pointed to {suspect.label}."
    )
    world.say(
        f"{victim.label} blinked, then laughed when the prank turned out to be harmless."
    )
    world.say(
        f"Together they used {prank.cleanup}."
    )
    world.say(
        f"In the end, the room was tidy again, {suspect.label} looked relieved, and "
        f"{detective.label} had solved the case before the mischief could grow."
    )

    world.facts["solved"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    suspect = _safe_fact(world, f, "suspect")
    victim = _safe_fact(world, f, "victim")
    prank = _safe_fact(world, f, "prank")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Who solved the prank story at {setting.place}?",
            answer=f"{detective.label} solved it by following the clues carefully.",
        ),
        QAItem(
            question=f"Who was acting nervous before the prank was revealed?",
            answer=f"{suspect.label} was the one fidgeting and looking too innocent.",
        ),
        QAItem(
            question=f"What was the prank in the story?",
            answer=f"It was {prank.title}, which could have made {prank.consequence}.",
        ),
        QAItem(
            question=f"Why did the clues matter so much in the story?",
            answer=(
                f"The clues mattered because they foreshadowed the prank before it fully happened, "
                f"so {detective.label} could stop the trouble in time."
            ),
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=(
                f"The prank was explained, everyone laughed, and the mess was cleaned up so "
                f"the place could feel calm again."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer=(
                "Foreshadowing is when a story gives small clues early so readers can guess "
                "what may happen later."
            ),
        ),
        QAItem(
            question="What does a detective do?",
            answer=(
                "A detective looks for clues, asks careful questions, and tries to figure out "
                "what really happened."
            ),
        ),
        QAItem(
            question="What is a prank?",
            answer=(
                "A prank is a playful trick. A good prank is harmless and should not hurt anyone "
                "or cause a big problem."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    prank = _safe_fact(world, f, "prank")
    setting = _safe_fact(world, f, "setting")
    detective = _safe_fact(world, f, "detective")
    return [
        f'Write a child-friendly detective story set at {setting.place} that uses foreshadowing and the word "{prank.keyword}".',
        f"Tell a short mystery where {detective.label} notices clues before a silly prank is revealed.",
        f"Write a gentle detective story in which small clues point to a prank, and the ending turns into a calm cleanup.",
    ]


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
        lines.append(f"  {e.id:9} ({e.type:7}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({name for name, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="school",
        prank="feather",
        detective_name="Fanny",
        detective_kind="girl",
        suspect_name="Sillybilly",
        suspect_kind="boy",
        victim_name="Mrs. Pine",
        victim_kind="woman",
    ),
    StoryParams(
        place="library",
        prank="ink",
        detective_name="Fanny",
        detective_kind="girl",
        suspect_name="Sillybilly",
        suspect_kind="boy",
        victim_name="Mr. Vale",
        victim_kind="man",
    ),
    StoryParams(
        place="garden",
        prank="jelly",
        detective_name="Fanny",
        detective_kind="girl",
        suspect_name="Sillybilly",
        suspect_kind="boy",
        victim_name="Nina",
        victim_kind="girl",
    ),
]


def explain_rejection(place: str, prank_id: str) -> str:
    if (place, prank_id) not in valid_combos():
        return "(No story: that setting and prank do not fit this small world.)"
    return ""


ASP_RULES = r"""
setting_place(P) :- setting(P).
prank_kind(K) :- prank(K).

compatible(P, K) :- affords(P, K).

#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PRANKS:
        lines.append(asp.fact("prank", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective-story world with foreshadowed pranks.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--prank", choices=PRANKS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "prank", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "prank", None) is None or c[1] == getattr(args, "prank", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prank_id = rng.choice(list(combos))
    detective_name = getattr(args, "name", None) or "Fanny"
    suspect_name = "Sillybilly"
    victim_name = "Mrs. Pine" if place != "garden" else "Nina"
    return StoryParams(
        place=place,
        prank=prank_id,
        detective_name=detective_name,
        detective_kind="girl",
        suspect_name=suspect_name,
        suspect_kind="boy",
        victim_name=victim_name,
        victim_kind="woman" if victim_name == "Mrs. Pine" else "girl",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PRANKS, params.prank),
        params.detective_name,
        params.detective_kind,
        params.suspect_name,
        params.suspect_kind,
        params.victim_name,
        params.victim_kind,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible setting/prank combos:\n")
        for place, prank in combos:
            print(f"  {place:10} {prank}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective_name}: {p.prank} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
