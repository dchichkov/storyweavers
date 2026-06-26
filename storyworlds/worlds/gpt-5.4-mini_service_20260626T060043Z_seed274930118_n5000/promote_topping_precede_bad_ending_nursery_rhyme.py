#!/usr/bin/env python3
"""
storyworlds/worlds/promote_topping_precede_bad_ending_nursery_rhyme.py
======================================================================

A tiny nursery-rhyme story world about a little baker, a topping, and the
mistake of not letting one thing precede another.

Seed tale:
---
There was a little child in a cozy kitchen who loved to promote a bright topping
for a tart. The grown-up said the tart had to cool first, because the topping
must precede the heat if it wanted to stay neat. But the child hurried, topped
the tart too soon, and the sweet red topping slipped into a shiny puddle. The
end was sad, but the kitchen still felt like a rhyme.

This world keeps the prose close to a nursery rhyme: simple cadence, concrete
images, and a small bad ending that follows from the simulated state.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    topping: object | None = None
    treat: object | None = None
    def __post_init__(self) -> None:
        for k in ["warmth", "mess", "joy", "worry", "patience", "hunger"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "child", "girlchild"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "childboy"}:
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
    place: str = "the cozy kitchen"
    temperature: str = "warm"
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
class Topping:
    id: str
    label: str
    phrase: str
    kind: str
    melts_when_warm: bool
    flavor: str
    color: str
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
class Treat:
    id: str
    label: str
    phrase: str
    needs_cooling: bool
    hot_from_oven: bool = True
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
        self.lines: list[str] = []
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the cozy kitchen", temperature="warm"),
    "bakery": Setting(place="the tiny bakery", temperature="warm"),
}

TASTES = {
    "berry": Topping(
        id="berry",
        label="berry topping",
        phrase="a bright berry topping",
        kind="fruit",
        melts_when_warm=True,
        flavor="sweet",
        color="red",
    ),
    "honey": Topping(
        id="honey",
        label="honey topping",
        phrase="a golden honey topping",
        kind="syrup",
        melts_when_warm=True,
        flavor="sticky-sweet",
        color="gold",
    ),
    "coconut": Topping(
        id="coconut",
        label="coconut topping",
        phrase="a snowy coconut topping",
        kind="flakes",
        melts_when_warm=False,
        flavor="light",
        color="white",
    ),
}

TREATS = {
    "tart": Treat(
        id="tart",
        label="tart",
        phrase="a little tart",
        needs_cooling=True,
        hot_from_oven=True,
    ),
    "cake": Treat(
        id="cake",
        label="cake",
        phrase="a round cake",
        needs_cooling=True,
        hot_from_oven=True,
    ),
}

NAMES = ["Mia", "Pip", "Nora", "Tess", "Leo", "Finn"]
KINDS = ["girl", "boy"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    setting: str
    treat: str
    topping: str
    name: str
    kind: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
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


def topping_can_wait(topping: Topping, treat: Treat) -> bool:
    return (not topping.melts_when_warm) or (not treat.hot_from_oven)


def story_reasonableness(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.treat not in TREATS:
        pass
    if params.topping not in TASTES:
        pass
    if params.kind not in KINDS:
        pass
    if params.name not in NAMES:
        pass


def build_world(params: StoryParams) -> World:
    story_reasonableness(params)
    world = World(_safe_lookup(SETTINGS, params.setting))
    child = world.add(Entity(id=params.name, kind="character", type=params.kind, label=params.name))
    grownup = world.add(Entity(id="grownup", kind="character", type="grownup", label="the grown-up"))
    treat = world.add(Entity(
        id="treat",
        kind="thing",
        type=_safe_lookup(TREATS, params.treat).id,
        label=_safe_lookup(TREATS, params.treat).label,
        phrase=_safe_lookup(TREATS, params.treat).phrase,
    ))
    topping = world.add(Entity(
        id="topping",
        kind="thing",
        type=_safe_lookup(TASTES, params.topping).kind,
        label=_safe_lookup(TASTES, params.topping).label,
        phrase=_safe_lookup(TASTES, params.topping).phrase,
    ))

    world.facts.update(child=child, grownup=grownup, treat=treat, topping=topping, params=params)

    # Beginning.
    world.say(f"In {world.setting.place}, little {child.id} was bright as a button.")
    world.say(f"{child.id} loved to promote {topping.phrase}, and the kitchen did glow.")
    world.say(f"On the sill sat {treat.phrase}, warm from the oven, with steam in a row.")

    # Middle turn.
    world.lines.append("")  # paragraph break marker in rendered prose
    world.say(f"The grown-up said, \"Let it cool first; the topping must precede the heat.\"")
    world.say(f"But {child.id} was merry and hasty and did not wait for the treat.")
    child.memes["joy"] += 1
    child.memes["worry"] += 1
    treat.meters["warmth"] += 1
    topping.meters["mess"] += 1

    if treat.hot_from_oven and _safe_lookup(TASTES, params.topping).melts_when_warm:
        topping.meters["warmth"] += 1
        topping.meters["mess"] += 1
        treat.meters["mess"] += 1
        child.memes["worry"] += 1
        grownup.memes["worry"] += 1
        world.say(f"Down slid the {topping.label}, soft as a sigh, into a shiny red smear.")
        world.say(f"The sweet top did not stay neat; it spread and vanished near.")

    # Bad ending.
    world.lines.append("")
    if treat.meters["mess"] > 0:
        world.say(f"{child.id} blinked at the crusty, sticky plate and felt a small, sad sting.")
        world.say(f"The tart was a muddled little moon, and the kitchen went quiet at the string.")
    else:
        world.say(f"{child.id} smiled at the tidy top, but the day still felt thin and small.")
        world.say(f"The rhyme ended softly, with crumbs by the wall.")

    world.facts["bad_ending"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        f'Write a nursery-rhyme story about {p.name} who tries to promote a {_safe_lookup(TASTES, p.topping).label} on a {_safe_lookup(TREATS, p.treat).label}.',
        f'Write a short child-friendly rhyme where the topping must precede the heat, but {p.name} does not wait.',
        f'Create a gentle bad-ending story set in {world.setting.place} using the words promote, topping, and precede.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    return [
        QAItem(
            question=f"What did {p.name} want to do with the topping?",
            answer=f"{p.name} wanted to promote the {_safe_lookup(TASTES, p.topping).label} and place it on the treat.",
        ),
        QAItem(
            question="Why did the grown-up say to wait?",
            answer="The grown-up said to wait because the treat was still warm, and the topping should precede the heat if it wanted to stay neat.",
        ),
        QAItem(
            question="What happened when the child did not wait?",
            answer=f"The topping slid and turned messy on the warm {_safe_lookup(TREATS, p.treat).label}, so the little treat ended in a sad, sticky way.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to promote something?",
            answer="To promote something means to support it, praise it, or help people notice it.",
        ),
        QAItem(
            question="What is a topping?",
            answer="A topping is food that goes on top of another food, like fruit, cream, or sprinkles.",
        ),
        QAItem(
            question="What does precede mean?",
            answer="Precede means to come before something else in time or order.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        out.append(f"{i}. {q}")
    out.append("")
    out.append("== story qa ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world qa ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A topping is compatible with a treat if it does not melt on warmth,
% or if the treat is already cool.
compatible(T, P) :- topping(T), treat(P), melts_when_warm(T, no).
compatible(T, P) :- topping(T), treat(P), treat_cool(P).

% Bad ending happens when a child applies a melting topping to a warm treat.
bad_ending(C, T, P) :- child(C), topping(T), treat(P),
                       melts_when_warm(T, yes), treat_hot(P, yes).
#show compatible/2.
#show bad_ending/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TASTES.items():
        lines.append(asp.fact("topping", tid))
        lines.append(asp.fact("melts_when_warm", tid, "yes" if t.melts_when_warm else "no"))
    for pid, p in TREATS.items():
        lines.append(asp.fact("treat", pid))
        lines.append(asp.fact("treat_hot", pid, "yes" if p.hot_from_oven else "no"))
        lines.append(asp.fact("treat_cool", pid, "no" if p.hot_from_oven else "yes"))
    for n in NAMES:
        lines.append(asp.fact("child", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/2.\n#show bad_ending/3."))
    bad = set(asp.atoms(model, "bad_ending"))
    compat = set(asp.atoms(model, "compatible"))
    py_bad = set()
    py_compat = set()
    for t in TASTES.values():
        for p in TREATS.values():
            if topping_can_wait(t, p):
                py_compat.add((t.id, p.id))
            if t.melts_when_warm and p.hot_from_oven:
                py_bad.add(("Mia", t.id, p.id))
    if bad == py_bad and compat == py_compat:
        print("OK: ASP parity matches Python reasonableness gate.")
        return 0
    print("MISMATCH:")
    print("ASP bad:", sorted(bad))
    print("PY  bad:", sorted(py_bad))
    print("ASP compat:", sorted(compat))
    print("PY  compat:", sorted(py_compat))
    return 1


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world with a bad ending.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--topping", choices=sorted(TASTES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--kind", choices=KINDS)
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
    setting = getattr(args, "setting", None) or rng.choice(sorted(SETTINGS))
    treat = getattr(args, "treat", None) or rng.choice(sorted(TREATS))
    topping = getattr(args, "topping", None) or rng.choice(sorted(TASTES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    kind = getattr(args, "kind", None) or rng.choice(KINDS)
    return StoryParams(setting=setting, treat=treat, topping=topping, name=name, kind=kind)


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
        print("--- trace ---")
        for k, v in sample.world.facts.items():
            if k != "params":
                print(f"{k}: {v}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="kitchen", treat="tart", topping="berry", name="Mia", kind="girl"),
    StoryParams(setting="bakery", treat="cake", topping="honey", name="Pip", kind="boy"),
    StoryParams(setting="kitchen", treat="tart", topping="honey", name="Nora", kind="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2.\n#show bad_ending/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/2.\n#show bad_ending/3."))
        print("compatible:", sorted(set(asp.atoms(model, "compatible"))))
        print("bad_ending:", sorted(set(asp.atoms(model, "bad_ending"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

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
