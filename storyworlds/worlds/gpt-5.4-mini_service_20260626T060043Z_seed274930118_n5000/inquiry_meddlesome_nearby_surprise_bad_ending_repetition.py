#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inquiry_meddlesome_nearby_surprise_bad_ending_repetition.py
================================================================================

A small slice-of-life storyworld about a nearby surprise, a meddlesome inquiry,
and the kind of bad ending that can happen when someone will not stop asking.

Premise:
- A child is trying to keep a surprise secret for someone nearby.
- A meddlesome person keeps making inquiries and repeating the same question.
- The repeated inquiry can cause the surprise to be revealed too early.
- If the secret is spoiled, the ending is "bad" in a gentle, child-facing way:
  the surprise is lost, disappointment appears, and the characters must clean up
  or try again another day.

This is intentionally compact: a small household domain with strong causal
state, limited variants, and a clear beginning -> pressure -> reveal -> ending.
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    nearby_to: Optional[str] = None
    hidden: bool = False
    opened: bool = False
    repeated: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    meddler: object | None = None
    surprise: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type in {"boxes", "cookies"} else "it"
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
class Place:
    name: str
    indoor: bool = True
    nearby_spots: tuple[str, ...] = ("table", "kitchen counter", "sofa")
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
class SurprisePlan:
    id: str
    label: str
    phrase: str
    hide_spot: str
    reveal_spot: str
    reveal_tell: str
    spoil_reason: str
    aftermath: str
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
class InquiryStyle:
    question: str
    repeat_line: str
    meddle_action: str
    pressure_word: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = dataclasses.deepcopy(self.entities) if hasattr(dataclasses, "deepcopy") else __import__("copy").deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place("the kitchen", indoor=True, nearby_spots=("table", "counter", "sink")),
    "living_room": Place("the living room", indoor=True, nearby_spots=("sofa", "armchair", "window")),
    "porch": Place("the porch", indoor=True, nearby_spots=("bench", "door", "shoe rack")),
}

SURPRISES = {
    "cake": SurprisePlan(
        id="cake",
        label="cake",
        phrase="a small birthday cake with blue sprinkles",
        hide_spot="the fridge",
        reveal_spot="the counter",
        reveal_tell="smelled sweet and buttery",
        spoil_reason="the frosting got smudged",
        aftermath="the cake had to be fixed before anyone could sing",
    ),
    "gift": SurprisePlan(
        id="gift",
        label="gift",
        phrase="a wrapped gift with shiny ribbon",
        hide_spot="under the sofa",
        reveal_spot="beside the sofa",
        reveal_tell="had bright paper and a bow on top",
        spoil_reason="the ribbon came loose",
        aftermath="the wrapping was no longer secret",
    ),
    "note": SurprisePlan(
        id="note",
        label="note",
        phrase="a tiny note with a happy drawing",
        hide_spot="inside a book",
        reveal_spot="on the table",
        reveal_tell="had a smiling sun drawn on it",
        spoil_reason="the drawing got crumpled",
        aftermath="the message looked rushed instead of special",
    ),
}

INQUIRIES = {
    "what": InquiryStyle(
        question="What is it?",
        repeat_line="What is it? What is it?",
        meddle_action="peeked too closely",
        pressure_word="curiosity",
    ),
    "where": InquiryStyle(
        question="Where is it?",
        repeat_line="Where is it? Where is it?",
        meddle_action="kept looking around nearby",
        pressure_word="suspense",
    ),
    "who": InquiryStyle(
        question="Who is it for?",
        repeat_line="Who is it for? Who is it for?",
        meddle_action="leaned in again and again",
        pressure_word="wonder",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nina", "Theo", "Ava", "Ben"]
MEDDLERS = ["Max", "Lena", "Maya", "Owen"]
ADULTS = ["Mom", "Dad", "Aunt Jo", "Grandma"]
MOODS = ["patient", "careful", "secretive", "nervous"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    surprise: str
    inquiry: str
    child_name: str
    meddler_name: str
    adult_name: str
    mood: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for surprise in SURPRISES:
            for inquiry in INQUIRIES:
                combos.append((place, surprise, inquiry))
    return combos


def explain_rejection(place: str, surprise: str, inquiry: str) -> str:
    return (
        f"(No story: the combination {place!r}, {surprise!r}, {inquiry!r} "
        f"does not describe a clear nearby-surprise scene.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id="child", kind="character", type="girl", label=params.child_name))
    meddler = world.add(Entity(id="meddler", kind="character", type="boy", label=params.meddler_name))
    adult = world.add(Entity(id="adult", kind="character", type="woman", label=params.adult_name))
    surprise = world.add(Entity(
        id="surprise",
        kind="thing",
        type=params.surprise,
        label=_safe_lookup(SURPRISES, params.surprise).label,
        phrase=_safe_lookup(SURPRISES, params.surprise).phrase,
        owner="adult",
        nearby_to="child",
        hidden=True,
    ))

    world.facts.update(
        child=child,
        meddler=meddler,
        adult=adult,
        surprise=surprise,
        plan=_safe_lookup(SURPRISES, params.surprise),
        inquiry=_safe_lookup(INQUIRIES, params.inquiry),
        params=params,
    )
    return world


def simulate(world: World) -> None:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    meddler: Entity = _safe_fact(world, f, "meddler")
    adult: Entity = _safe_fact(world, f, "adult")
    surprise: Entity = _safe_fact(world, f, "surprise")
    plan: SurprisePlan = _safe_fact(world, f, "plan")
    inquiry: InquiryStyle = _safe_fact(world, f, "inquiry")

    child.memes["care"] = 1
    adult.memes["hope"] = 1
    meddler.memes["curiosity"] = 1

    world.say(f"{child.label} was helping nearby {adult.label} with a little secret.")
    world.say(f"{they(child)} were keeping {surprise.label} hidden {plan.hide_spot}.")
    world.say(f"It was meant to be a surprise, so {child.label} stayed close and spoke softly.")

    world.para()
    world.say(f"But {meddler.label} came by and asked, \"{inquiry.question}\"")
    world.say(f"{meddler.label} did not wait for an answer; {meddler.label} {inquiry.meddle_action}.")
    meddler.memes["curiosity"] += 1
    meddler.meters["nearby"] = 1
    surprise.meters["pressure"] = surprise.meters.get("pressure", 0.0) + 0.5

    world.para()
    world.say(f"Then the same question came again: \"{inquiry.repeat_line}\"")
    meddler.repeated = True
    surprise.meters["pressure"] += 1.0
    adult.memes["worry"] += 1
    child.memes["alarm"] += 1

    # If repeated inquiry reaches the secret, it gets revealed too early.
    if surprise.meters["pressure"] >= THRESHOLD:
        surprise.hidden = False
        surprise.opened = True
        world.say(f"The box was no longer easy to hide, and the secret was lost.")
        world.say(
            f"On the {plan.reveal_spot}, the {surprise.label} {plan.reveal_tell}, "
            f"but now everyone had seen it too soon."
        )
        adult.memes["disappointment"] += 1
        child.memes["disappointment"] += 1
        meddler.memes["guilt"] += 1

        world.para()
        world.say(
            f"{adult.label} sighed and said the surprise was spoiled because "
            f"{plan.spoil_reason}."
        )
        world.say(
            f"{child.label} looked down, because the happy moment had turned into a bad ending."
        )
        world.say(
            f"They cleaned up the {surprise.label} and tried to make it nice again, but the first surprise was gone."
        )
        world.say(
            f"Still, {adult.label} promised to find another cheerful moment later, when everyone could be more careful."
        )
        child.memes["bad_ending"] = 1
        f["ending"] = "bad"
    else:
        world.say(
            f"{adult.label} moved the {surprise.label} farther away, and the secret stayed safe for now."
        )
        world.say(
            f"{child.label} gave {meddler.label} a serious look and asked for one quiet minute."
        )
        f["ending"] = "safe"

    world.facts["surprise_revealed"] = surprise.opened
    world.facts["repeated"] = meddler.repeated
    world.facts["bad_ending"] = world.facts["ending"] == "bad"


def they(child: Entity) -> str:
    return "she" if child.type in {"girl", "woman", "mother"} else "he"


# ---------------------------------------------------------------------------
# Prose generation
# ---------------------------------------------------------------------------

def build_story(params: StoryParams) -> StorySample:
    world = setup_world(params)
    simulate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    return [
        f"Write a slice-of-life story for a young child about a nearby surprise and a repeated question.",
        f"Tell a short gentle story where {params.child_name} tries to keep a {params.surprise} secret, but {params.meddler_name} keeps asking {_safe_lookup(INQUIRIES, params.inquiry).question}",
        f"Write a simple home story with inquiry, meddlesome behavior, nearby tension, and a bad ending when a surprise is spoiled.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    params: StoryParams = _safe_fact(world, f, "params")
    plan: SurprisePlan = _safe_fact(world, f, "plan")
    inquiry: InquiryStyle = _safe_fact(world, f, "inquiry")
    child: Entity = _safe_fact(world, f, "child")
    meddler: Entity = _safe_fact(world, f, "meddler")
    adult: Entity = _safe_fact(world, f, "adult")

    return [
        QAItem(
            question=f"What was {child.label} trying to keep secret nearby?",
            answer=f"{child.label} was trying to keep {plan.phrase} secret {plan.hide_spot}.",
        ),
        QAItem(
            question=f"What question did {meddler.label} keep repeating?",
            answer=f"{meddler.label} kept repeating, \"{inquiry.repeat_line}\"",
        ),
        QAItem(
            question=f"Why did the story end badly?",
            answer=(
                f"It ended badly because {meddler.label} kept making inquiries nearby, "
                f"so the surprise was revealed too early and {plan.spoil_reason}."
            ),
        ),
        QAItem(
            question=f"Who felt disappointed when the surprise was spoiled?",
            answer=f"{child.label} and {adult.label} both felt disappointed when the secret was no longer special.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    plan: SurprisePlan = _safe_fact(world, f, "plan")
    inquiry: InquiryStyle = _safe_fact(world, f, "inquiry")
    return [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something kept secret for a while so someone can discover it later.",
        ),
        QAItem(
            question="What does meddlesome mean?",
            answer="Meddlesome means getting into other people's business in a way that is not helpful.",
        ),
        QAItem(
            question="What does nearby mean?",
            answer="Nearby means close by, not far away.",
        ),
        QAItem(
            question="Why can repeating a question bother people?",
            answer="Repeating a question can bother people because it may make them feel rushed or unable to keep a secret.",
        ),
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things do not go the happy way the characters hoped for.",
        ),
        QAItem(
            question=f"What kind of thing was the surprise in this story?",
            answer=f"It was {plan.phrase}, which fit the home setting and could be hidden nearby.",
        ),
        QAItem(
            question=f"What was the repeated question like in this story?",
            answer=f"It was the kind of inquiry that would not stop, because {inquiry.question} was asked again and again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} hidden={e.hidden} opened={e.opened} "
            f"nearby_to={e.nearby_to} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid_story/4.
#show spoiled/3.

valid_story(Place, Surprise, Inquiry, Ending) :- place(Place), surprise(Surprise), inquiry(Inquiry),
                                                 outcome(Place, Surprise, Inquiry, Ending).

spoiled(Place, Surprise, Inquiry) :- outcome(Place, Surprise, Inquiry, bad).

outcome(Place, Surprise, Inquiry, bad) :- place(Place), surprise(Surprise), inquiry(Inquiry),
                                          can_hide_nearby(Place, Surprise),
                                          meddlesome(Inquiry),
                                          repeats(Inquiry).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("can_hide_nearby", pid, "x"))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    for iid in INQUIRIES:
        lines.append(asp.fact("inquiry", iid))
        lines.append(asp.fact("meddlesome", iid))
        lines.append(asp.fact("repeats", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set((p, s, i, "bad") for p, s, i in valid_combos())
    asp_set = set(asp_valid_stories())
    if python_set == asp_set:
        print(f"OK: ASP and Python agree on {len(python_set)} valid stories.")
        return 0
    print("MISMATCH between ASP and Python:")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in ASP:", sorted(asp_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life world about nearby secrets, repeated inquiries, and bad endings.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--inquiry", choices=INQUIRIES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", "--n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--child-name", choices=CHILD_NAMES)
    ap.add_argument("--meddler-name", choices=MEDDLERS)
    ap.add_argument("--adult-name", choices=ADULTS)
    ap.add_argument("--mood", choices=MOODS)
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    inquiry = getattr(args, "inquiry", None) or rng.choice(list(INQUIRIES))
    if (place, surprise, inquiry) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        surprise=surprise,
        inquiry=inquiry,
        child_name=getattr(args, "child_name", None) or rng.choice(CHILD_NAMES),
        meddler_name=getattr(args, "meddler_name", None) or rng.choice(MEDDLERS),
        adult_name=getattr(args, "adult_name", None) or rng.choice(ADULTS),
        mood=getattr(args, "mood", None) or rng.choice(MOODS),
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


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
        print(asp_program("#show valid_story/4."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story shapes:")
        for row in stories:
            print("  ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place in PLACES:
            for surprise in SURPRISES:
                for inquiry in INQUIRIES:
                    params = StoryParams(
                        place=place,
                        surprise=surprise,
                        inquiry=inquiry,
                        child_name=_safe_lookup(CHILD_NAMES, 0),
                        meddler_name=_safe_lookup(MEDDLERS, 0),
                        adult_name=_safe_lookup(ADULTS, 0),
                        mood=_safe_lookup(MOODS, 0),
                        seed=base_seed,
                    )
                    samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
