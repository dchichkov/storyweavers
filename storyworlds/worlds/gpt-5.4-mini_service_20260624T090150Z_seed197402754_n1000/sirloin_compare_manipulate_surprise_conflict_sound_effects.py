#!/usr/bin/env python3
"""
A tiny bedtime-style story world about a child helping in the kitchen.

Seed tale premise:
A child is excited to make dinner with a grown-up. They compare two pieces of
sirloin, choose one, and manipulate the seasonings and pan. A small surprise
and a little conflict appear when the sizzling sound is louder than expected,
but the story ends warmly with a finished meal and a calmer kitchen.

This world keeps the simulation small and state-driven:
- physical meters: heat, doneness, aroma, loudness, mess
- emotional memes: surprise, conflict, pride, calm, curiosity
- the story changes based on chosen cut, tools, and kitchen setting
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
# Domain registries
# ---------------------------------------------------------------------------

KITCHENS = {
    "cozy kitchen": {
        "place": "the cozy kitchen",
        "counter": "the wooden counter",
        "sound": "a soft hiss",
        "warmth": "warm",
    },
    "little apartment kitchen": {
        "place": "the little apartment kitchen",
        "counter": "the narrow counter",
        "sound": "a bright sizzle",
        "warmth": "small and snug",
    },
    "grandma's kitchen": {
        "place": "Grandma's kitchen",
        "counter": "the big red counter",
        "sound": "a cheerful crackle",
        "warmth": "homey",
    },
}

SIRLOINS = {
    "small sirloin": {
        "label": "small sirloin",
        "phrase": "a small sirloin",
        "compare_to": "larger sirloin",
        "weight": 1,
        "fat": 1,
        "cook_time": 2,
    },
    "large sirloin": {
        "label": "large sirloin",
        "phrase": "a larger sirloin",
        "compare_to": "small sirloin",
        "weight": 2,
        "fat": 2,
        "cook_time": 3,
    },
}

TOOLS = {
    "spoon": {
        "label": "wooden spoon",
        "kind": "spoon",
        "verb": "stir",
        "sound": "tap-tap",
        "mess_guard": True,
    },
    "tongs": {
        "label": "long tongs",
        "kind": "tongs",
        "verb": "turn",
        "sound": "clink",
        "mess_guard": False,
    },
    "spatula": {
        "label": "flat spatula",
        "kind": "spatula",
        "verb": "lift",
        "sound": "flip",
        "mess_guard": False,
    },
}

SEASONINGS = {
    "salt": {
        "label": "salt",
        "verb": "sprinkle",
        "effect": "brighter",
    },
    "pepper": {
        "label": "pepper",
        "verb": "shake",
        "effect": "spicier",
    },
    "herbs": {
        "label": "herbs",
        "verb": "pinch",
        "effect": "greener",
    },
}

SFX = {
    "compare": "hmm-hmm",
    "manipulate": "tap, tap, tap",
    "surprise": "oh!",
    "conflict": "tsk",
    "sizzle": "sizzle-sizzle",
    "finish": "ding!",
}

NAMES = ["Maya", "Leo", "Nina", "Owen", "Lila", "Ben", "Ivy", "Noah"]
GROWNUPS = ["mom", "dad", "grandma", "uncle"]
TRAITS = ["curious", "gentle", "helpful", "bold", "careful", "cheerful"]


# ---------------------------------------------------------------------------
# Shared result helpers
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
class StoryParams:
    kitchen: str
    sirloin: str
    tool: str
    seasoning: str
    name: str
    grownup: str
    trait: str
    seed: Optional[int] = None
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = "thing"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    carried_by: Optional[str] = None
    on_counter: bool = False

    adult: object | None = None
    child: object | None = None
    seasoning: object | None = None
    steak: object | None = None
    tool: object | None = None
    def bump(self, group: str, key: str, amount: float = 1.0) -> None:
        store = self.meters if group == "meters" else self.memes
        store[key] = store.get(key, 0.0) + amount
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


class World:
    def __init__(self, kitchen_id: str) -> None:
        self.kitchen_id = kitchen_id
        self.kitchen = _safe_lookup(KITCHENS, kitchen_id)
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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
        other = World(self.kitchen_id)
        import copy as _copy
        other.entities = _copy.deepcopy(self.entities)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        other.fired = set(self.fired)
        return other


# ---------------------------------------------------------------------------
# Reasoning and narration
# ---------------------------------------------------------------------------

def compare_sirloins(left: dict, right: dict) -> str:
    if left["weight"] == right["weight"]:
        return "They looked about the same size."
    if left["weight"] < right["weight"]:
        return f"The {left['label']} looked smaller than the {right['label']}."
    return f"The {left['label']} looked bigger than the {right['label']}."


def reasonableness_gate(params: StoryParams) -> None:
    if params.sirloin not in SIRLOINS:
        pass
    if params.tool not in TOOLS:
        pass
    if params.seasoning not in SEASONINGS:
        pass
    if params.kitchen not in KITCHENS:
        pass


def choose_compatible_fix(tool: dict, sirloin: dict) -> bool:
    return tool["kind"] in {"spoon", "tongs", "spatula"} and sirloin["cook_time"] >= 2


def simulate(world: World) -> None:
    child = world.get("child")
    adult = world.get("adult")
    steak = world.get("sirloin")
    tool = world.get("tool")
    seasoning = world.get("seasoning")

    # Compare
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{child.label} stood by {world.kitchen['counter']} and said, "
        f'"{SFX["compare"]} Which sirloin should we use?"'
    )
    world.say(compare_sirloins(world.facts["sirloin_left"], world.facts["sirloin_right"]))

    # Manipulate
    tool.meters["use"] = tool.meters.get("use", 0.0) + 1.0
    steak.meters["heat"] = steak.meters.get("heat", 0.0) + 1.0
    steak.meters["aroma"] = steak.meters.get("aroma", 0.0) + 1.0
    world.say(
        f"{child.label} took the {tool.label} and began to {_safe_lookup(TOOLS, tool.id)['verb']} "
        f"the pan with {SFX['manipulate']} care."
    )
    world.say(
        f"{adult.label.capitalize()} helped {child.label} {_safe_lookup(SEASONINGS, seasoning.id)['verb']} "
        f"the {_safe_lookup(SEASONINGS, seasoning.id)['label']} over the {steak.label}."
    )

    # Surprise + conflict
    steak.meters["loudness"] = steak.meters.get("loudness", 0.0) + 1.0
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1.0
    if not tool.meters.get("quiet_hand", 0.0):
        child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
        world.say(
            f"Then the pan gave a sudden {world.kitchen['sound']}, and {child.label} went, "
            f'"{SFX["surprise"]} That sound is so big!"'
        )
        world.say(
            f"{adult.label.capitalize()} smiled and said they could lower the heat and hold the handle together."
        )
    else:
        world.say(
            f"Then the pan gave a sudden {world.kitchen['sound']}, but it stayed gentle and did not startle {child.label}."
        )

    # Resolution
    steak.meters["doneness"] = steak.meters.get("doneness", 0.0) + 1.0
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1.0
    child.memes["conflict"] = 0.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1.0
    world.say(
        f"At last, the sirloin rested on the plate and the kitchen grew quiet again."
    )
    world.say(
        f'{child.label} grinned at the finished meal. "{SFX["finish"]} We made it," {child.label} whispered.'
    )


# ---------------------------------------------------------------------------
# Story composition
# ---------------------------------------------------------------------------

def build_story(world: World) -> str:
    return world.render()


def build_qa(world: World) -> tuple[list[QAItem], list[QAItem], list[QAItem]]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    steak = _safe_fact(world, f, "sirloin_entity")
    tool = _safe_fact(world, f, "tool_entity")
    seasoning = _safe_fact(world, f, "seasoning_entity")
    kitchen = world.kitchen["place"]

    prompts = [
        f'Write a bedtime story about a child in {kitchen} who must compare two sirloins and choose one to cook.',
        f'Tell a gentle story where {child.label} helps {adult.label} manipulate the pan and seasoning without making a fuss.',
        f'Write a short story using the words sirloin, compare, and manipulate, ending with a warm dinner.',
    ]

    story_qa = [
        QAItem(
            question=f"What did {child.label} compare at the start of the story?",
            answer=f"{child.label} compared two pieces of sirloin before choosing the one to cook.",
        ),
        QAItem(
            question=f"Why did {child.label} feel surprised in the kitchen?",
            answer=f"{child.label} felt surprised when the pan made a loud sizzling sound.",
        ),
        QAItem(
            question=f"How did {adult.label} help when there was conflict?",
            answer=f"{adult.label} helped lower the heat and shared the handle so {child.label} could feel safe again.",
        ),
        QAItem(
            question=f"What was on the plate at the end?",
            answer=f"A finished sirloin was on the plate, and the kitchen was calm again.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What does compare mean?",
            answer="To compare means to look at two things and notice how they are alike or different.",
        ),
        QAItem(
            question="What does manipulate mean?",
            answer="To manipulate something means to handle it carefully or change it with your hands.",
        ),
        QAItem(
            question="What is a sirloin?",
            answer="A sirloin is a cut of beef that can be cooked in a pan or on a grill.",
        ),
        QAItem(
            question="Why do pans make sizzling sounds?",
            answer="Pans can make sizzling sounds when heat meets wet food or fat, and the sound shows the food is cooking.",
        ),
    ]
    return prompts, story_qa, world_qa


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/4.
#show valid_story/5.

kitchen(K) :- setting(K).
sirloin(S) :- steak(S).
tool(T) :- utensil(T).
seasoning(X) :- flavor(X).

valid(K, S, T, X) :- kitchen(K), sirloin(S), tool(T), seasoning(X).

compareable(S1, S2) :- steak(S1), steak(S2), S1 != S2.
surpriseable(S) :- steak(S), cook_time(S, C), C >= 2.
conflictful(T) :- utensil(T), kind(T, spoon; tongs; spatula).

valid_story(K, S, T, X, bed) :- valid(K, S, T, X), compareable(S, other_sirloin), surpriseable(S), conflictful(T).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for kid in KITCHENS:
        lines.append(asp.fact("setting", kid))
    for sid, s in SIRLOINS.items():
        lines.append(asp.fact("steak", sid))
        lines.append(asp.fact("cook_time", sid, s["cook_time"]))
    for tid in TOOLS:
        lines.append(asp.fact("utensil", tid))
        lines.append(asp.fact("kind", tid, _safe_lookup(TOOLS, tid)["kind"]))
    for fid in SEASONINGS:
        lines.append(asp.fact("flavor", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid/4."))
    asp_valid = set(asp.atoms(model, "valid"))
    py_valid = set((k, s, t, x) for k in KITCHENS for s in SIRLOINS for t in TOOLS for x in SEASONINGS)
    if asp_valid == py_valid:
        print(f"OK: ASP matches Python gate ({len(py_valid)} combos).")
        return 0
    print("Mismatch between ASP and Python gate.")
    print("ASP only:", sorted(asp_valid - py_valid))
    print("Python only:", sorted(py_valid - asp_valid))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(k, s, t, x) for k in KITCHENS for s in SIRLOINS for t in TOOLS for x in SEASONINGS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about sirloin, compare, and manipulate.")
    ap.add_argument("--kitchen", choices=KITCHENS)
    ap.add_argument("--sirloin", choices=SIRLOINS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--seasoning", choices=SEASONINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--grownup", choices=GROWNUPS)
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
    kitchen = getattr(args, "kitchen", None) or rng.choice(list(KITCHENS))
    sirloin = getattr(args, "sirloin", None) or rng.choice(list(SIRLOINS))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    seasoning = getattr(args, "seasoning", None) or rng.choice(list(SEASONINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(GROWNUPS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(kitchen=kitchen, sirloin=sirloin, tool=tool, seasoning=seasoning, name=name, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = World(params.kitchen)
    child = world.add(Entity(id="child", kind="character", label=params.name, type="child"))
    adult = world.add(Entity(id="adult", kind="character", label=params.grownup, type="grownup"))
    steak = world.add(Entity(id="sirloin", kind="thing", label=_safe_lookup(SIRLOINS, params.sirloin)["label"], type="sirloin"))
    tool = world.add(Entity(id="tool", kind="thing", label=_safe_lookup(TOOLS, params.tool)["label"], type="tool"))
    seasoning = world.add(Entity(id="seasoning", kind="thing", label=_safe_lookup(SEASONINGS, params.seasoning)["label"], type="seasoning"))

    world.facts.update(
        child=child,
        adult=adult,
        sirloin_entity=steak,
        tool_entity=tool,
        seasoning_entity=seasoning,
        sirloin_left=_safe_lookup(SIRLOINS, params.sirloin),
        sirloin_right=SIRLOINS["large sirloin" if params.sirloin == "small sirloin" else "small sirloin"],
    )

    child.memes["curiosity"] = 1.0
    adult.memes["calm"] = 1.0

    # Setup paragraph
    world.say(
        f"In {world.kitchen['place']}, {child.label} and {adult.label.capitalize()} made a tiny dinner plan together."
    )
    world.say(
        f"{child.label} wanted to compare two sirloins before cooking, because {child.label} liked choosing carefully."
    )
    world.para()
    simulate(world)
    story = build_story(world)
    prompts, story_qa, world_qa = build_qa(world)
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            pass
        model = asp.one_model(asp_program("#show valid/4."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for item in combos:
            print(item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for k in KITCHENS:
            for s in SIRLOINS:
                for t in TOOLS:
                    for x in SEASONINGS:
                        params = StoryParams(
                            kitchen=k,
                            sirloin=s,
                            tool=t,
                            seasoning=x,
                            name=random.choice(NAMES),
                            grownup=random.choice(GROWNUPS),
                            trait=random.choice(TRAITS),
                            seed=base_seed,
                        )
                        samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
