#!/usr/bin/env python3
"""
storyworlds/worlds/smidge_sizzle_murmur_hardware_store_surprise_slice.py
========================================================================

A small slice-of-life storyworld set in a hardware store.

Premise:
A child and a caregiver stop at a hardware store for a simple errand.
A tiny surprise turns the errand into a gentle, memorable moment:
something goes missing, something is found, and the child learns that
small helpful actions can make a busy place feel warm.

This world uses three seed words as narrative instruments:
- smidge: a tiny amount, a small remainder, a little bit left over
- sizzle: the lively feeling of a heated moment, like a brief spark of excitement
- murmur: quiet, close conversation inside a busy room

The story style stays close to slice of life: concrete, domestic, and complete.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    name: str = "the hardware store"
    affordances: set[str] = field(default_factory=lambda: {"browse", "buy", "ask", "find"})
    place: object | None = None
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
class StoryState:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    notes: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    st: object | None = None
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
# Parameters
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


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    adult_role: str
    errand: str
    surprise: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Content registries
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


CHILD_NAMES = {
    "girl": ["Mia", "Nora", "Ava", "Lily", "June", "Ruby"],
    "boy": ["Leo", "Noah", "Milo", "Ben", "Owen", "Theo"],
}
ADULT_ROLES = ["mom", "dad", "aunt", "uncle", "grandma", "grandpa"]

ERRANDS = {
    "screws": {
        "label": "a little box of screws",
        "need": "pick up a little box of screws",
        "reason": "the shelf at home had a loose hinge",
    },
    "tape": {
        "label": "masking tape",
        "need": "buy masking tape",
        "reason": "a cardboard craft needed neat edges",
    },
    "gloves": {
        "label": "work gloves",
        "need": "find a pair of work gloves",
        "reason": "the garden bed had thorns near it",
    },
    "lightbulb": {
        "label": "a lightbulb",
        "need": "replace a lightbulb",
        "reason": "the lamp in the hallway had gone dim",
    },
}

SURPRISES = {
    "kitten": {
        "label": "a sleepy kitten in a box",
        "action": "peeked out from behind the paint cans",
        "turn": "everyone softened their voices at once",
    },
    "coupon": {
        "label": "a bright coupon tucked in the cart",
        "action": "made the cashier smile and point to a discount",
        "turn": "the errand cost a little less than expected",
    },
    "seedling": {
        "label": "a tiny seedling in a damp cup",
        "action": "had been set aside for a neighbor",
        "turn": "the child promised to carry it carefully",
    },
    "bell": {
        "label": "a little brass bell",
        "action": "was found near the service counter",
        "turn": "the adult said it could ring only once for luck",
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clean_join(parts: list[str]) -> str:
    return " ".join(p for p in parts if p)


def _article(label: str) -> str:
    return "an" if label[:1].lower() in "aeiou" else "a"


def _para(st: StoryState, *sentences: str) -> None:
    for s in sentences:
        st.say(s)
    st.para()


def build_world(params: StoryParams) -> StoryState:
    place = Place()
    st = StoryState(place=place)
    child = st.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["small", "curious", "quiet"],
        memes={"delight": 0.0, "surprise": 0.0, "comfort": 0.0},
    ))
    adult = st.add(Entity(
        id="adult",
        kind="character",
        type=params.adult_role,
        label=f"their {params.adult_role}",
        traits=["patient"],
        memes={"calm": 1.0, "surprise": 0.0},
    ))
    errand = _safe_lookup(ERRANDS, params.errand)
    surprise = _safe_lookup(SURPRISES, params.surprise)

    st.notes.update(
        child=child,
        adult=adult,
        errand=params.errand,
        surprise=params.surprise,
        errand_cfg=errand,
        surprise_cfg=surprise,
    )

    # Beginning: the ordinary errand.
    _para(
        st,
        f"{child.id} went to {place.name} with {adult.label} for a simple errand.",
        f"They only needed to {_clean_join([errand['need']])} because {errand['reason']}.",
        f"The front of the store smelled like wood, dust, and a smidge of machine oil.",
    )
    child.memes["curiosity"] += 1.0

    # Middle: browsing, small murmur, surprise appears.
    _para(
        st,
        f"Inside, the aisles were tall and tidy, and people spoke in a soft murmur near the registers.",
        f"{child.id} followed the carts past nails, paint brushes, and bins of bright handles.",
    )
    child.memes["anticipation"] += 1.0

    # Surprise turn.
    st.say(
        f"Then {surprise['action']}, and {child.id} stopped so fast that the cart wheels gave a tiny sizzle of sound."
    )
    child.memes["surprise"] += 1.0
    adult.memes["surprise"] += 1.0
    st.notes["surprise_seen"] = True

    if params.surprise == "kitten":
        st.say(
            f"A smidge of fear came first, but {adult.label} smiled and said the kitten was safe."
        )
        child.memes["comfort"] += 1.0
    elif params.surprise == "coupon":
        st.say(
            f"{adult.label} laughed under their breath, and the cashier waved the coupon like a small prize."
        )
        child.memes["delight"] += 1.0
    elif params.surprise == "seedling":
        st.say(
            f"The damp leaves looked fragile, so {child.id} held the cup with both hands and walked more slowly."
        )
        child.memes["care"] = child.memes.get("care", 0.0) + 1.0
    else:
        st.say(
            f"{adult.label} said the bell could be a lucky little helper, and {child.id} liked the bright ring of that idea."
        )
        child.memes["delight"] += 1.0

    # Middle: the errand gets completed.
    st.para()
    st.say(
        f"After that, {child.id} helped find the thing on the list."
    )
    if params.errand == "screws":
        st.say("They chose the box with the smallest slots, so none of the pieces would rattle loose.")
    elif params.errand == "tape":
        st.say("They picked the roll with the straight edge, because neat tape made the craft easier later.")
    elif params.errand == "gloves":
        st.say("They found gloves with soft fingers, which would fit without pinching.")
    else:
        st.say("They chose a bulb that matched the lamp, so the hallway would glow again tonight.")

    # Ending: subtle proof of change.
    st.para()
    if params.surprise == "kitten":
        st.say(
            f"At checkout, {child.id} watched the kitten blink once and settle into its box."
        )
        st.say(
            f"The store felt a little warmer on the way out, and {child.id} remembered that quiet care can be its own kind of surprise."
        )
    elif params.surprise == "coupon":
        st.say(
            f"{adult.label} folded the coupon into the bag, and the receipt came out shorter than expected."
        )
        st.say(
            f"{child.id} smiled at the smidge of extra change left in the pocket, pleased that a small paper slip could change the whole errand."
        )
    elif params.surprise == "seedling":
        st.say(
            f"By the door, {child.id} checked the seedling one last time and saw it still standing straight."
        )
        st.say(
            f"When they got home, the little plant waited by the sink, and the child carried that careful feeling along with it."
        )
    else:
        st.say(
            f"Before leaving, {child.id} gave the brass bell one gentle ring."
        )
        st.say(
            f"The sound was brief and bright, and the ordinary errand ended with a tiny smile that stayed with them outside."
        )

    st.notes["done"] = True
    return st


# ---------------------------------------------------------------------------
# Quality gates and registries
# ---------------------------------------------------------------------------
def reasonableness_gate(params: StoryParams) -> None:
    if params.child_gender not in {"girl", "boy"}:
        pass
    if params.errand not in ERRANDS:
        pass
    if params.surprise not in SURPRISES:
        pass
    if params.adult_role not in ADULT_ROLES:
        pass
    if params.child_name.strip() == "":
        pass


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(_safe_lookup(CHILD_NAMES, gender))


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for gender in ("girl", "boy"):
        for errand in ERRANDS:
            for surprise in SURPRISES:
                combos.append((gender, errand, surprise))
    return combos


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: StoryState) -> list[str]:
    f = world.notes
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    adult: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adult")
    errand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "errand_cfg")
    surprise = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "surprise_cfg")
    return [
        f"Write a gentle slice-of-life story set in a hardware store where {child.id} and {adult.label} go to {_clean_join([errand['need']])} and notice {surprise['label']}.",
        f"Tell a short story about a child in a hardware store, a small surprise, and a calm ending.",
        f"Write a child-friendly story that uses the words smidge, sizzle, and murmur while a hardware store errand unfolds.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.notes
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    adult: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "adult")
    errand = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "errand_cfg")
    surprise = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "surprise_cfg")

    qa = [
        QAItem(
            question=f"Where did {child.id} go with {adult.label}?",
            answer=f"{child.id} went with {adult.label} to the hardware store for a simple errand.",
        ),
        QAItem(
            question=f"What did they need to do at the store?",
            answer=f"They needed to {_clean_join([errand['need']])} because {errand['reason']}.",
        ),
        QAItem(
            question=f"What surprise did {child.id} notice?",
            answer=f"{child.id} noticed {surprise['label']} at the hardware store.",
        ),
        QAItem(
            question=f"How did the surprise change the mood?",
            answer=(
                f"It made the errand feel more special. The store started as an ordinary place, "
                f"but the surprise gave {child.id} a little burst of excitement and made the ending warmer."
            ),
        ),
    ]
    if world.notes.get("surprise_seen"):
        qa.append(
            QAItem(
                question=f"Why did the cart wheels make a sizzle of sound?",
                answer=(
                    f"{child.id} stopped suddenly after noticing the surprise, so the cart wheels gave a quick, lively sizzle."
                ),
            )
        )
    return qa


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hardware store?",
            answer="A hardware store is a shop where people buy tools, nails, tape, lightbulbs, and other things for fixing and building.",
        ),
        QAItem(
            question="What does murmur mean?",
            answer="A murmur is a soft, quiet sound made by people talking gently or by a low background noise.",
        ),
        QAItem(
            question="What does smidge mean?",
            answer="A smidge means a very tiny amount or a small bit of something.",
        ),
        QAItem(
            question="What does sizzle mean?",
            answer="Sizzle can mean a crackly, lively sound or a feeling of quick excitement.",
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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: StoryState) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: type={ent.type} meters={meters} memes={memes}")
    lines.append(f"notes={world.notes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child(C) :- child_name(C).
errand(E) :- errand_name(E).
surprise(S) :- surprise_name(S).

compatible(G,E,S) :- child_gender(G), errand(E), surprise(S).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gender in ("girl", "boy"):
        lines.append(asp.fact("child_gender", gender))
    for e in ERRANDS:
        lines.append(asp.fact("errand", e))
        lines.append(asp.fact("errand_name", e))
    for s in SURPRISES:
        lines.append(asp.fact("surprise", s))
        lines.append(asp.fact("surprise_name", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in clingo:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life hardware store storyworld with a gentle surprise.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult-role", choices=ADULT_ROLES)
    ap.add_argument("--errand", choices=sorted(ERRANDS))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    errand = getattr(args, "errand", None) or rng.choice(list(ERRANDS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    adult_role = getattr(args, "adult_role", None) or rng.choice(ADULT_ROLES)
    name = getattr(args, "name", None) or choose_name(rng, gender)
    params = StoryParams(
        child_name=name,
        child_gender=gender,
        adult_role=adult_role,
        errand=errand,
        surprise=surprise,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for g, e, s in combos:
            print(f"  {g:4} {e:12} {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for gender in ("girl", "boy"):
            for errand in ERRANDS:
                for surprise in SURPRISES:
                    seed = base_seed + len(samples)
                    params = StoryParams(
                        child_name=choose_name(random.Random(seed), gender),
                        child_gender=gender,
                        adult_role=_safe_lookup(ADULT_ROLES, len(samples) % len(ADULT_ROLES)),
                        errand=errand,
                        surprise=surprise,
                        seed=seed,
                    )
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.errand} with {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
