#!/usr/bin/env python3
"""
storyworlds/worlds/problem_haunt_dialogue_humor_friendship_nursery_rhyme.py
===========================================================================

A small, constraint-checked story world in a nursery-rhyme style about a
friendly haunt, a little problem, and a talking-through friendship solution.

Premise:
- A child and a friendly ghostly visitor share a cozy place.
- The haunt creates a small problem by startling things, stealing the rhythm,
  or hiding a needed object.
- Dialogue, humor, and friendship turn the problem into a gentle resolution.

The model tracks:
- physical meters: presence, scare, disorder, hiddenness, tidiness
- emotional memes: joy, worry, friendship, courage, humor, trust
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: {
        "presence": 0.0,
        "scare": 0.0,
        "disorder": 0.0,
        "hidden": 0.0,
        "tidy": 0.0,
    })
    memes: dict[str, float] = field(default_factory=lambda: {
        "joy": 0.0,
        "worry": 0.0,
        "friendship": 0.0,
        "courage": 0.0,
        "humor": 0.0,
        "trust": 0.0,
    })

    child: object | None = None
    haunt: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def name_word(self) -> str:
        return self.label or self.id
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
    cozy: bool = True
    sounds: str = ""
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
class Problem:
    id: str
    kind: str
    verb: str
    consequence: str
    resolution_hint: str
    theme_word: str = "problem"
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
class Haunt:
    id: str
    label: str
    type: str = "ghost"
    prank: str = ""
    is_friendly: bool = True
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


class World:
    def __init__(self, setting: Setting):
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nursery": Setting(place="the nursery", cozy=True, sounds="a hush and a hum"),
    "attic": Setting(place="the attic", cozy=False, sounds="a creak and a thump"),
    "hall": Setting(place="the hall", cozy=True, sounds="a tap-tap-tap"),
}

PROBLEMS = {
    "missing_bell": Problem(
        id="missing_bell",
        kind="missing",
        verb="hide the little bell",
        consequence="the rhyme went wrong",
        resolution_hint="look together under the blanket",
        theme_word="problem",
    ),
    "bump_in_dark": Problem(
        id="bump_in_dark",
        kind="spooky",
        verb="make a bump in the dark",
        consequence="the child gave a tiny start",
        resolution_hint="light a lamp and laugh at the bump",
        theme_word="problem",
    ),
    "tangled_song": Problem(
        id="tangled_song",
        kind="rhythm",
        verb="tangle the song",
        consequence="the tune lost its hop",
        resolution_hint="clap hands and sing it slow",
        theme_word="problem",
    ),
}

HAUNTS = {
    "mottle": Haunt(id="mottle", label="Mottle", prank="tip the spoon"),
    "puff": Haunt(id="puff", label="Puff", prank="hide the bell"),
    "whisp": Haunt(id="whisp", label="Whisp", prank="make the curtains swish"),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Eli", "Ruby", "Finn", "Ivy", "Milo"]
TRAITS = ["brave", "curious", "cheery", "gentle", "lively", "tiny"]


@dataclass
class StoryParams:
    setting: str
    problem: str
    haunt: str
    child_name: str
    child_type: str
    parent_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
problematic(P) :- problem(P).
haunts(H) :- haunt(H).
at_risk(P) :- problem(P), depends_on_song(P).
needs_togetherness(P) :- problematic(P), haunts(_).
friendly_fix(P) :- at_risk(P), friendly_haunt(_), together(P).
valid_story(S, P, H) :- setting(S), problem(P), haunt(H),
                        allows(S, P), allows_haunt(S, H),
                        compatible(P, H), friendly_haunt(H).
#show valid_story/3.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("allows", sid, "missing_bell"))
        lines.append(asp.fact("allows", sid, "bump_in_dark"))
        lines.append(asp.fact("allows", sid, "tangled_song"))
        if sid == "nursery":
            lines.append(asp.fact("cozy", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        if pid in {"missing_bell", "tangled_song"}:
            lines.append(asp.fact("depends_on_song", pid))
    for hid in HAUNTS:
        lines.append(asp.fact("haunt", hid))
        lines.append(asp.fact("friendly_haunt", hid))
        lines.append(asp.fact("compatible", "missing_bell", hid))
        lines.append(asp.fact("compatible", "bump_in_dark", hid))
        lines.append(asp.fact("compatible", "tangled_song", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Causal model
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            for h in HAUNTS:
                if p == "missing_bell" and h in HAUNTS:
                    combos.append((s, p, h))
                elif p == "bump_in_dark" and _safe_lookup(HAUNTS, h).is_friendly:
                    combos.append((s, p, h))
                elif p == "tangled_song":
                    combos.append((s, p, h))
    return combos


def make_story(world: World, child: Entity, parent: Entity, haunt: Entity, problem: Problem) -> None:
    child.memes["joy"] += 1
    child.memes["friendship"] += 1
    world.say(
        f"Little {child.name_word()} lived in {world.setting.place}, where there was "
        f"{world.setting.sounds} and a cozy little nook."
    )
    world.say(
        f"{child.name_word()} liked to sing in a soft nursery rhyme, and even the air "
        f"seemed to sway and hum."
    )
    world.say(
        f"Then along came {haunt.label}, a friendly haunt who loved to {haunt.prank}, "
        f"and that made one small {problem.theme_word}."
    )

    world.para()
    child.memes["worry"] += 1
    haunt.meters["presence"] += 1
    if problem.kind == "missing":
        world.say(
            f"When the little bell went missing, {child.name_word()} frowned and said, "
            f"\"Oh dear me, where can it be?\""
        )
        world.say(
            f"{haunt.label} peeked from behind a pillow and whispered, "
            f"\"I did not mean to be sly; I only wanted a joke, by and by.\""
        )
    elif problem.kind == "spooky":
        world.say(
            f"A bump sounded in the dark, and {child.name_word()} gave a tiny start."
        )
        world.say(
            f"{haunt.label} said, \"Boo for a tick, but never for long; I only meant a funny song.\""
        )
    else:
        world.say(
            f"The tune got tangled and tripped, and {child.name_word()} said, "
            f"\"My rhyme has slipped!\""
        )
        world.say(
            f"{haunt.label} giggled, \"Let's clap it true; two soft hands can help us through.\""
        )

    child.memes["humor"] += 1
    world.say(
        f"{child.name_word()} giggled, for {haunt.label} looked more silly than scary, "
        f"with a round little shadow and a wobble in the air."
    )

    world.para()
    world.say(
        f"{child.name_word()} said, \"If we work together, we can mend this sight, "
        f"and make the house feel merry and bright.\""
    )
    haunt.memes["trust"] += 1
    world.say(
        f"{haunt.label} answered, \"Yes indeed, my friend so true; show me the way, and I'll help too.\""
    )

    if problem.id == "missing_bell":
        world.say(
            f"They looked under the blanket, behind the chair, and in a shoe, until the little bell "
            f"gave a shiny ding-dong cue."
        )
    elif problem.id == "bump_in_dark":
        world.say(
            f"They lit a lamp, and the bump was only a basket, sitting lopsided and brisk."
        )
    else:
        world.say(
            f"They clapped slow, then clapped fast, and the song came back at last."
        )

    child.memes["joy"] += 1
    child.memes["friendship"] += 1
    child.memes["courage"] += 1
    haunt.memes["friendship"] += 1
    world.say(
        f"At the end, {child.name_word()} and {haunt.label} laughed together in the glow, "
        f"and the little problem was smaller than a snowflake's toe."
    )
    world.say(
        f"The nursery stayed cozy, the rhyme stayed kind, and friend and haunt were easy to find."
    )

    world.facts.update(
        child=child,
        parent=parent,
        haunt=haunt,
        problem=problem,
        setting=world.setting,
        resolved=True,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme style story about a child, a friendly haunt, and a "{f["problem"].theme_word}".',
        f"Tell a gentle story set in {f['setting'].place} where {f['child'].name_word()} and {f['haunt'].label} solve a small problem with dialogue and humor.",
        "Write a tiny story with a spooky-but-silly visitor, a talking back-and-forth, and a warm friendship ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = _safe_fact(world, world.facts, "child")
    h = _safe_fact(world, world.facts, "haunt")
    p = _safe_fact(world, world.facts, "problem")
    return [
        QAItem(
            question=f"Who was the story mainly about in {world.setting.place}?",
            answer=f"The story was about little {c.name_word()}, who met the friendly haunt {h.label}.",
        ),
        QAItem(
            question=f"What small {p.theme_word} happened when {h.label} arrived?",
            answer=f"{h.label} made a small {p.kind} problem, and that was what the child and haunt needed to fix together.",
        ),
        QAItem(
            question=f"How did {c.name_word()} and {h.label} solve the trouble?",
            answer="They talked kindly, laughed a little, and worked together until the problem was fixed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a haunt in a story?",
            answer="A haunt is a spooky or ghostly visitor in a story, and it can be silly, kind, or mysterious.",
        ),
        QAItem(
            question="Why can dialogue help in a problem?",
            answer="Dialogue helps because the characters can say what they need, hear each other, and find a good plan together.",
        ),
        QAItem(
            question="What makes a friendship story feel warm?",
            answer="A friendship story feels warm when the characters care about each other, speak kindly, and help instead of fighting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        out.append(f"{e.id} ({e.type}): meters={meters} memes={memes}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme world about a problem, a haunt, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if getattr(args, "haunt", None):
        combos = [c for c in combos if c[2] == getattr(args, "haunt", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, haunt = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if getattr(args, "gender", None) == "girl" and name in {"Eli", "Finn", "Milo"}:
        name = rng.choice([n for n in CHILD_NAMES if n not in {"Eli", "Finn", "Milo"}])
    if getattr(args, "gender", None) == "boy" and name in {"Mia", "Nora", "Ruby", "Ivy"}:
        name = rng.choice([n for n in CHILD_NAMES if n not in {"Mia", "Nora", "Ruby", "Ivy"}])
    return StoryParams(setting=setting, problem=problem, haunt=haunt, child_name=name,
                       child_type=gender, parent_type=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="parent"))
    haunt = world.add(Entity(id=params.haunt, kind="character", type="ghost", label=_safe_lookup(HAUNTS, params.haunt).label))
    problem = _safe_lookup(PROBLEMS, params.problem)
    make_story(world, child, parent, haunt, problem)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for s in SETTINGS:
            for p in PROBLEMS:
                for h in HAUNTS:
                    params = StoryParams(setting=s, problem=p, haunt=h, child_name="Mia", child_type="girl",
                                         parent_type="mother", trait="curious")
                    samples.append(generate(params))
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


if __name__ == "__main__":
    main()
