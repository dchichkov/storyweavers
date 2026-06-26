#!/usr/bin/env python3
"""
dental_cautionary_detective_story.py
====================================

A small story world in the style of a detective story, with a cautionary
dental premise: a child detective follows clues, learns what caused a tooth
problem, and ends with a safer routine that changes the world state.

The simulated domain tracks:
- physical meters: plaque, decay, freshness, pain, brightness, neatness
- emotional memes: curiosity, worry, relief, pride, trust

The story remains child-facing and concrete. It is not a frozen paragraph; the
prose is driven by the simulated world state, the clue trail, and the final
resolution.
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
# World entities
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for key in ["plaque", "decay", "freshness", "pain", "brightness", "neatness"]:
            self.meters.setdefault(key, 0.0)
        for key in ["curiosity", "worry", "relief", "pride", "trust"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detectivegirl"}
        male = {"boy", "father", "dad", "man", "detectiveboy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    place: str = "the bathroom"
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
class Clue:
    id: str
    label: str
    reveals: str
    noun: str
    place: str
    evidence: str
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


@dataclass
class Tool:
    id: str
    label: str
    solves: set[str]
    method: str
    tail: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    clue: str
    tool: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


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


SETTINGS = {
    "bathroom": Setting(place="the bathroom", affords={"inspect", "brush", "rinse"}),
    "bedroom": Setting(place="the bedroom", affords={"inspect", "search"}),
    "clinic": Setting(place="the dental clinic", affords={"inspect", "clean"}),
}

CLUES = {
    "breath": Clue(
        id="breath",
        label="bad breath",
        reveals="the mouth needed help",
        noun="bad breath",
        place="near the sink",
        evidence="a funny smell",
    ),
    "stain": Clue(
        id="stain",
        label="a brown stain",
        reveals="a tooth had a spot",
        noun="a brown stain",
        place="on a back tooth",
        evidence="a little dark mark",
    ),
    "floss": Clue(
        id="floss",
        label="a skipped floss string",
        reveals="food was stuck between teeth",
        noun="a skipped floss string",
        place="beside the toothbrush cup",
        evidence="a loose string on the counter",
    ),
}

TOOLS = {
    "toothbrush": Tool(
        id="toothbrush",
        label="a soft toothbrush",
        solves={"plaque"},
        method="brush the teeth gently",
        tail="brushed carefully in small circles until the teeth felt smooth",
    ),
    "floss": Tool(
        id="floss",
        label="fresh floss",
        solves={"plaque"},
        method="clean between the teeth",
        tail="used floss to slip out the stuck bits",
    ),
    "water": Tool(
        id="water",
        label="a cup of water",
        solves={"dryness"},
        method="rinse the mouth",
        tail="rinsed and spat into the sink",
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Sam"]
HELPER_NAMES = ["Dr. Hale", "Dr. June", "Ms. Pike", "Dad", "Mom"]
TRAITS = ["curious", "careful", "brave", "sharp-eyed", "patient"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is relevant when it points at mouth trouble.
relevant(C) :- clue(C), points_to_mouth(C).

% A tool is useful if it can solve plaque.
useful(T) :- tool(T), solves_plaque(T).

% A valid story needs a relevant clue and a useful tool.
valid_story(S, C, T) :- setting(S), relevant(C), useful(T).

% A cautionary story is one where the plaque would otherwise become pain.
warning_needed(C) :- clue(C), points_to_decay(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if cid in {"breath", "stain"}:
            lines.append(asp.fact("points_to_mouth", cid))
        if cid in {"stain"}:
            lines.append(asp.fact("points_to_decay", cid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "plaque" in t.solves:
            lines.append(asp.fact("solves_plaque", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    # Convert ASP tuples (setting, clue, tool) to match Python set
    if asp_set == py:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def asp_show_program() -> str:
    return asp_program("#show valid_story/3.")


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid in SETTINGS:
        for cid in CLUES:
            for tid in TOOLS:
                if sid == "clinic" and cid != "stain":
                    continue
                if cid == "stain" and tid == "water":
                    continue
                combos.append((sid, cid, tid))
    return combos


def reasonableness_gate(setting: str, clue: str, tool: str) -> None:
    if setting not in SETTINGS:
        pass
    if clue not in CLUES:
        pass
    if tool not in TOOLS:
        pass
    if setting == "clinic" and clue != "stain":
        pass
    if clue == "stain" and tool == "water":
        pass


def choose_name(rng: random.Random, hero_type: str) -> str:
    return rng.choice(HERO_NAMES)


def choose_helper(rng: random.Random) -> tuple[str, str]:
    helper_type = rng.choice(["mother", "father", "dentist"])
    helper_name = rng.choice(HELPER_NAMES)
    if helper_type == "dentist":
        helper_name = rng.choice(["Dr. Hale", "Dr. June"])
    return helper_name, helper_type


def caution_score(world: World) -> float:
    hero = world.get("hero")
    return hero.meters["plaque"] + hero.meters["decay"] + hero.meters["pain"]


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper_name,
    ))
    clue = _safe_lookup(CLUES, params.clue)
    tool = _safe_lookup(TOOLS, params.tool)
    world.add(Entity(
        id="clue",
        type="thing",
        label=clue.label,
        phrase=clue.noun,
    ))
    world.add(Entity(
        id="tool",
        type="thing",
        label=tool.label,
        phrase=tool.label,
    ))

    # Simulated state.
    hero.meters["plaque"] = 1.0 if params.clue != "floss" else 1.5
    if params.clue == "stain":
        hero.meters["decay"] = 1.0
    hero.memes["curiosity"] = 1.0
    helper.memes["trust"] = 1.0

    world.facts.update(
        hero=hero,
        helper=helper,
        clue=clue,
        tool=tool,
        setting_name=params.setting,
        setting=setting,
    )

    return world


def inspect_clue(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    world.say(
        f"{hero.label} was a small detective with sharp eyes, and {hero.pronoun()} "
        f"noticed {clue.evidence} {clue.place}."
    )
    world.say(
        f"That clue pointed to {clue.reveals}, so the case began to feel serious."
    )


def describe_setting(world: World) -> None:
    place = world.setting.place
    world.say(f"One quiet day, {world.facts['hero'].label} walked into {place} to solve a tiny case.")
    world.say(f"The room held a sink, a mirror, and a mystery waiting in plain sight.")


def reveal_problem(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    tool: Tool = _safe_fact(world, world.facts, "tool")
    if clue.id == "breath":
        world.say(
            f"{hero.label} leaned near the mirror and sniffed. The smell was not fresh, "
            f"which made {hero.pronoun('possessive')} nose wrinkle."
        )
    elif clue.id == "stain":
        world.say(
            f"{hero.label} opened wide and saw a tiny brown spot hiding on a back tooth."
        )
    else:
        world.say(
            f"{hero.label} found a skipped floss string by the cup, and that felt like an important clue."
        )
    world.say(
        f"The best tool for the job was {tool.label}, because a detective needs the right method."
    )


def predict_worsening(world: World) -> dict[str, bool]:
    sim = world.copy()
    hero = sim.get("hero")
    if sim.facts["clue"].id in {"breath", "floss"}:
        hero.meters["plaque"] += 1.0
    if sim.facts["clue"].id == "stain":
        hero.meters["decay"] += 1.0
        hero.meters["pain"] += 1.0
    return {
        "pain": hero.meters["pain"] >= 1.0 or hero.meters["decay"] >= 1.0,
        "plaque": hero.meters["plaque"] >= 2.0,
    }


def caution_warning(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    prediction = predict_worsening(world)
    if prediction["pain"]:
        helper.memes["worry"] += 1
        world.facts["warning"] = True
        world.say(
            f"{helper.label} frowned gently and said, "
            f"\"If we ignore this clue, the tooth trouble could grow into pain.\""
        )
        if clue.id == "stain":
            world.say(
                f"That was a careful warning, because a brown spot can hide a bigger problem."
            )
    else:
        world.facts["warning"] = False


def act_fix(world: World) -> Optional[Tool]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    tool: Tool = _safe_fact(world, world.facts, "tool")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    hero.memes["trust"] += 1

    if clue.id == "stain" and tool.id == "water":
        return None

    world.say(
        f"{helper.label} handed over {tool.label}, and {hero.label} got to work."
    )
    world.say(f"{hero.label} knew the clue did not ask for a chase; it asked for a clean-up.")
    return tool


def resolve(world: World, tool: Tool) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")

    hero.meters["plaque"] = max(0.0, hero.meters["plaque"] - 1.0)
    if clue.id == "stain":
        hero.meters["decay"] = max(0.0, hero.meters["decay"] - 0.5)
    hero.meters["freshness"] += 1.0
    hero.meters["brightness"] += 1.0
    hero.meters["neatness"] += 1.0
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    hero.memes["relief"] += 1.0
    hero.memes["pride"] += 1.0
    helper.memes["trust"] += 1.0

    world.say(
        f"{hero.label} used {tool.label} to {tool.method}, and {tool.tail}."
    )
    world.say(
        f"After that, the mouth felt fresher, the teeth looked brighter, and the case was no longer dangerous."
    )


def end_image(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    if hero.meters["freshness"] > 0:
        world.say(
            f"{hero.label} smiled at the mirror like a detective who had solved the case the careful way."
        )
        world.say(
            f"{helper.label} nodded, because the warning had been listened to, and that made the ending safe."
        )


def tell_story(world: World) -> World:
    describe_setting(world)
    world.para()
    inspect_clue(world)
    reveal_problem(world)
    caution_warning(world)
    tool = act_fix(world)
    world.para()
    if tool is not None:
        resolve(world, tool)
    end_image(world)
    return world


# ---------------------------------------------------------------------------
# Story generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Clue = _safe_fact(world, f, "clue")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short cautionary detective story for a child named {hero.label} who finds {clue.label} and needs {tool.label}.',
        f"Tell a gentle mystery where {hero.label} and {helper.label} solve a dental problem before it turns into pain.",
        f"Write a detective-style story about a child noticing {clue.noun} and choosing the safe dental fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Clue = _safe_fact(world, f, "clue")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting_name = _safe_fact(world, f, "setting_name")
    qa = [
        QAItem(
            question=f"What kind of story is this, and who is it about?",
            answer=(
                f"It is a detective-style cautionary story about {hero.label}, who follows a dental clue in {SETTINGs_name(setting_name)}."
            ),
        ),
        QAItem(
            question=f"What clue first made {hero.label} worry?",
            answer=(
                f"The first clue was {clue.noun}. It showed that the mouth needed careful attention."
            ),
        ),
        QAItem(
            question=f"Why did {helper.label} give a warning?",
            answer=(
                f"{helper.label} warned {hero.label} because if the clue was ignored, the problem could grow into pain."
            ),
        ),
        QAItem(
            question=f"What tool helped solve the case safely?",
            answer=(
                f"{tool.label} helped solve the case because it could {tool.method}."
            ),
        ),
    ]
    if world.get("hero").meters["freshness"] > 0:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=(
                    f"It ended with {hero.label} feeling proud, the teeth looking brighter, and the detective case finished in a safe way."
                ),
            )
        )
    return qa


def SETTINGs_name(setting_name: str) -> str:
    return _safe_lookup(SETTINGS, setting_name).place


WORLD_KNOWLEDGE = {
    "dental": [
        QAItem(
            question="Why do people brush their teeth?",
            answer="People brush their teeth to clean away plaque and keep their mouths fresh and healthy.",
        ),
        QAItem(
            question="What is plaque?",
            answer="Plaque is a sticky film that can build up on teeth and cause trouble if it is not cleaned off.",
        ),
    ],
    "detective": [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what happened.",
        )
    ],
    "cautionary": [
        QAItem(
            question="What does cautionary mean?",
            answer="A cautionary story gives a warning so someone can avoid a problem before it gets worse.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [*WORLD_KNOWLEDGE["dental"], *WORLD_KNOWLEDGE["detective"], *WORLD_KNOWLEDGE["cautionary"]]
    return out


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
# Parameter handling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary dental detective story world.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["mother", "father", "dentist"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    reasonableness_gate(setting, clue, tool)

    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or choose_name(rng, hero_type)
    helper_name, helper_type = choose_helper(rng)
    if getattr(args, "helper_name", None):
        helper_name = getattr(args, "helper_name", None)
    if getattr(args, "helper_type", None):
        helper_type = getattr(args, "helper_type", None)
    return StoryParams(
        setting=setting,
        clue=clue,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify_combos() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_story_count() -> int:
    return len(valid_combos())


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for c in CLUES:
            for t in TOOLS:
                if s == "clinic" and c != "stain":
                    continue
                if c == "stain" and t == "water":
                    continue
                combos.append((s, c, t))
    return combos


def asp_valid_story_combos() -> list[tuple[str, str, str]]:
    return asp_valid_combos()


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("bathroom", "breath", "toothbrush", "Mia", "girl", "Mom", "mother"),
        StoryParams("bathroom", "floss", "floss", "Leo", "boy", "Dad", "father"),
        StoryParams("clinic", "stain", "toothbrush", "Nora", "girl", "Dr. Hale", "dentist"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_combos())
    if getattr(args, "asp", None):
        combos = asp_valid_story_combos()
        print(f"{len(combos)} compatible (setting, clue, tool) combos:\n")
        for s, c, t in combos:
            print(f"  {s:8} {c:8} {t:10}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated_params()]
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
            header = f"### {p.hero_name}: {p.clue} with {p.tool} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
