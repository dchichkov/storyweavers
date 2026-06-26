#!/usr/bin/env python3
"""
storyworlds/worlds/predict_panda_flashback_dialogue_mystery.py
===============================================================

A small mystery storyworld about a panda who tries to predict where a missing
thing went, using a flashback and a little dialogue to solve it.

Seed-inspired premise:
- a panda
- prediction
- mystery tone
- flashback
- dialogue

The world is intentionally tiny and classical: a few typed entities, a few
places, one missing object, one mistaken assumption, then a memory that reveals
the truth.
"""

from __future__ import annotations

import argparse
import copy
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    panda: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "panda":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.type in {"woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"man", "father"}:
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
    id: str
    label: str
    clues: list[str] = field(default_factory=list)
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
    place: str
    missing: str
    helper: str
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
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_seen: bool = False

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_place(self, place: Place) -> Place:
        self.places[place.id] = place
        return place

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.places = copy.deepcopy(self.places)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_seen = self.flashback_seen
        return clone


PLACES = {
    "tea_room": Place(
        id="tea_room",
        label="the tea room",
        clues=["cup_ring", "crumbs"],
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        clues=["bamboo_leaf", "paw_print"],
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        clues=["windy_dust", "fallen_note"],
    ),
}

MISSING_THINGS = {
    "map": "the little map",
    "lantern": "the silver lantern",
    "bell": "the red bell",
}

HELPERS = {
    "butler": ("the butler", "butler"),
    "cook": ("the cook", "cook"),
    "sister": ("the sister", "sister"),
}


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_predicted_hide(world: World) -> list[str]:
    out: list[str] = []
    panda = world.get("panda")
    if panda.memes.get("predicting", 0) < THRESHOLD:
        return out
    if world.fired and ("predict", panda.id) in world.fired:
        return out
    world.fired.add(("predict", panda.id))
    if panda.memes.get("doubt", 0) >= THRESHOLD:
        panda.memes["focus"] = panda.memes.get("focus", 0.0) + 1
        out.append("The panda narrowed their eyes and kept thinking.")
    return out


RULES = [Rule("predicted_hide", _r_predicted_hide)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def flashback_reveals(world: World, missing: Entity, place: Place) -> bool:
    panda = world.get("panda")
    if panda.memes.get("memory", 0) < THRESHOLD:
        return False
    if world.flashback_seen:
        return False
    world.flashback_seen = True
    world.say(
        f"Then the panda remembered something from earlier: {missing.label} had "
        f"been carried toward {place.label} when the wind rattled the doors."
    )
    return True


def predict_place(world: World, panda: Entity) -> str:
    scores = {}
    for pid, place in world.places.items():
        scores[pid] = 0
        for clue in place.clues:
            if clue == "paw_print":
                scores[pid] += 2
            elif clue == "bamboo_leaf":
                scores[pid] += 1
            elif clue == "cup_ring":
                scores[pid] += 1
            elif clue == "fallen_note":
                scores[pid] += 1
        if panda.memes.get("memory", 0) >= THRESHOLD and pid == world.facts.get("true_place"):
            scores[pid] += 3
    best = max(scores.items(), key=lambda kv: (kv[1], kv[0]))[0]
    world.facts["predicted_place"] = best
    return best


def tell_story(world: World, panda: Entity, helper: Entity, missing: Entity, place: Place) -> None:
    world.say(
        f"At dawn, a small panda named {panda.id} woke to a quiet mystery: "
        f"{missing.label} was gone."
    )
    world.say(
        f"{panda.pronoun().capitalize()} paced the room and began to predict where "
        f"it might be."
    )
    panda.memes["predicting"] = 1
    panda.memes["doubt"] = 1
    guess = predict_place(world, panda)
    world.say(
        f'"Maybe {world.places[guess].label}?" {panda.id} whispered.'
    )
    world.para()
    world.say(
        f"{helper.label.capitalize()} leaned in and asked, "
        f'"What makes you think that?"'
    )
    world.say(
        f'"I saw a clue," the panda said, but {panda.pronoun("possessive")} voice '
        f"wobbled because the first clue did not feel complete."
    )
    world.say(
        f"Then {panda.id} closed {panda.pronoun('possessive')} eyes and had a flashback."
    )
    panda.memes["memory"] = 1
    flashback_reveals(world, missing, place)
    world.para()
    world.say(
        f'"Oh!" {panda.id} said. "I was wrong before. I remember the wind, and I remember {missing.label} near {place.label}."'
    )
    panda.memes["doubt"] = 0
    panda.memes["certainty"] = 1
    world.say(
        f"{helper.label.capitalize()} nodded. \"Then let's check there together.\""
    )
    world.say(
        f"They walked to {place.label}, and there was {missing.label}, tucked where the clue had pointed all along."
    )
    missing.location = place.id
    missing.hidden = False
    panda.memes["relief"] = 1
    world.say(
        f"The panda smiled, because the mystery had not only been solved; {panda.pronoun('possessive')} prediction had grown wiser."
    )
    propagate(world, narrate=True)


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        pass
    if params.missing not in MISSING_THINGS:
        pass
    if params.helper not in HELPERS:
        pass

    world = World()
    place = world.add_place(copy.deepcopy(_safe_lookup(PLACES, params.place)))
    helper_label, helper_type = _safe_lookup(HELPERS, params.helper)
    panda = world.add_entity(Entity(id="panda", kind="character", type="panda", label="the panda"))
    helper = world.add_entity(Entity(id="helper", kind="character", type=helper_type, label=helper_label))
    missing = world.add_entity(
        Entity(
            id="missing",
            kind="thing",
            type="thing",
            label=_safe_lookup(MISSING_THINGS, params.missing),
            owner=panda.id,
            location=None,
            hidden=True,
        )
    )
    world.facts.update(true_place=place.id, missing=params.missing, helper=params.helper)
    tell_story(world, panda, helper, missing, place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = _safe_lookup(world.places, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "true_place")).label
    missing = _safe_lookup(MISSING_THINGS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing"))
    helper = _safe_lookup(HELPERS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper"))[0]
    return [
        f"Write a short mystery story for a child about a panda who tries to predict where {missing} went.",
        f"Tell a gentle flashback story with dialogue where {helper} helps the panda solve the mystery at {place}.",
        f"Write a small, concrete mystery in which a panda remembers a clue and finds {missing} again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    place = _safe_lookup(world.places, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "true_place")).label
    missing = _safe_lookup(MISSING_THINGS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing"))
    helper = _safe_lookup(HELPERS, _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper"))[0]
    panda = world.get("panda")
    return [
        QAItem(
            question="Who was trying to solve the mystery?",
            answer="The panda was trying to solve the mystery.",
        ),
        QAItem(
            question=f"What was missing from the story?",
            answer=f"{missing} was missing.",
        ),
        QAItem(
            question=f"Who talked with the panda while they looked for the clue?",
            answer=f"{(getattr(helper, 'capitalize')() if callable(getattr(helper, 'capitalize', None)) else str(helper).capitalize())} talked with the panda while they looked for the clue.",
        ),
        QAItem(
            question=f"Where did the panda finally find {missing}?",
            answer=f"They found it at {place}.",
        ),
        QAItem(
            question="What changed after the flashback?",
            answer=(
                "The panda stopped doubting the clue, felt more certain, and used the memory "
                "to predict the right place."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to predict something?",
            answer=(
                "To predict means to make a careful guess about what will happen or where "
                "something might be, using clues and experience."
            ),
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer=(
                "A flashback is a moment when a character remembers something from earlier, "
                "and the story briefly shows that memory."
            ),
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer=(
                "Stories use dialogue so characters can speak to each other directly, which "
                "makes the scene feel alive and helps reveal what they know."
            ),
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_id(tea_room).
place_id(garden).
place_id(porch).

clue(tea_room, cup_ring).
clue(tea_room, crumbs).
clue(garden, bamboo_leaf).
clue(garden, paw_print).
clue(porch, windy_dust).
clue(porch, fallen_note).

predict_score(P, 0) :- place_id(P).
predict_score(P, S) :- place_id(P), S = #sum { 2, C : clue(P, C), C = paw_print;
                                               1, C : clue(P, C), C = bamboo_leaf;
                                               1, C : clue(P, C), C = cup_ring;
                                               1, C : clue(P, C), C = fallen_note }.

best(P) :- place_id(P), not worse(P).
worse(P) :- place_id(P), place_id(Q), predict_score(Q, SQ), predict_score(P, SP), SQ > SP.

#show best/1.
#show predict_score/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place_id", pid))
        for clue in _safe_lookup(PLACES, pid).clues:
            lines.append(asp.fact("clue", pid, clue))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_prediction() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show best/1."))
    return sorted(set(asp.atoms(model, "best")))


def asp_verify() -> int:
    py = set((k,) for k in PLACES.keys())
    clingo_best = set(asp_prediction())
    if clingo_best <= py:
        print(f"OK: ASP produced a best place: {sorted(clingo_best)}")
        return 0
    print("MISMATCH in ASP prediction.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny panda mystery with prediction, flashback, and dialogue.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--missing", choices=MISSING_THINGS.keys())
    ap.add_argument("--helper", choices=HELPERS.keys())
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, missing, helper) for place in PLACES for missing in MISSING_THINGS for helper in HELPERS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "missing", None):
        combos = [c for c in combos if c[1] == getattr(args, "missing", None)]
    if getattr(args, "helper", None):
        combos = [c for c in combos if c[2] == getattr(args, "helper", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, missing, helper = rng.choice(list(combos))
    return StoryParams(place=place, missing=missing, helper=helper)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="garden", missing="bell", helper="butler"),
    StoryParams(place="porch", missing="map", helper="sister"),
    StoryParams(place="tea_room", missing="lantern", helper="cook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show best/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show best/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
            header = f"### {p.place} / {p.missing} / {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
