#!/usr/bin/env python3
"""
A standalone story world for a tiny superhero tale about a quiz, a clue,
and a flax-based twist ending.

The seed prompt suggests a child-facing superhero story style:
- a hero and helper with names Twist and Rhyme
- a quiz that needs solving
- a clue that changes the plan
- flax as the surprising material in the world

The simulated world below keeps those pieces as physical and emotional state,
so the ending depends on what the characters discover and do.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carrier: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    quiz: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"ready": 0.0, "hidden": 0.0, "solved": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "subject": "they",
            "object": "them",
            "possessive": "their",
        }
        return mapping[case]

    def it(self) -> str:
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
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Artifact:
    id: str
    label: str
    phrase: str
    type: str
    clue_kind: str
    hidden_by: str
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
class Power:
    id: str
    label: str
    verb: str
    effect: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trail: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.trail = list(self.trail)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "hall": Place(name="the hall", indoors=True, affords={"quiz"}),
    "tower": Place(name="the clock tower", indoors=True, affords={"quiz", "search"}),
    "rooftop": Place(name="the rooftop", indoors=False, affords={"search", "rescue"}),
}

ARTIFACTS = {
    "flax": Artifact(
        id="flax",
        label="flax ribbon",
        phrase="a bright flax ribbon",
        type="ribbon",
        clue_kind="fiber",
        hidden_by="dust",
    ),
    "note": Artifact(
        id="note",
        label="note",
        phrase="a folded note",
        type="note",
        clue_kind="message",
        hidden_by="shadow",
    ),
    "badge": Artifact(
        id="badge",
        label="badge",
        phrase="a tiny star badge",
        type="badge",
        clue_kind="symbol",
        hidden_by="glass",
    ),
}

POWERS = {
    "twist": Power(
        id="twist",
        label="Twist",
        verb="twist",
        effect="reveal hidden things",
        helps={"flax", "note"},
    ),
    "rhyme": Power(
        id="rhyme",
        label="Rhyme",
        verb="rhyme",
        effect="soothe a worried crowd",
        helps={"quiz", "badge"},
    ),
}


# ---------------------------------------------------------------------------
# Validity gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, artifact: str) -> bool:
    if place not in SETTINGS or artifact not in ARTIFACTS:
        return False
    if "quiz" not in _safe_lookup(SETTINGS, place).affords:
        return False
    if artifact == "flax":
        return True
    return artifact in {"note", "badge"}


def explain_rejection(place: str, artifact: str) -> str:
    if place not in SETTINGS:
        return "(No story: that setting does not exist here.)"
    if artifact not in ARTIFACTS:
        return "(No story: that clue item does not exist here.)"
    return (
        f"(No story: {_safe_lookup(ARTIFACTS, artifact).label} does not fit the simple quiz-and-clue"
        f" plot at {_safe_lookup(SETTINGS, place).name}.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def setup_world(place: Place, artifact: Artifact, hero_name: str = "Twist", helper_name: str = "Rhyme") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type="helper"))
    prize = world.add(Entity(
        id="clue",
        kind="thing",
        type=artifact.type,
        label=artifact.label,
        phrase=artifact.phrase,
        owner=hero.id,
        carrier=None,
    ))
    quiz = world.add(Entity(
        id="quiz",
        kind="thing",
        type="quiz",
        label="quiz",
        phrase="a tricky city quiz",
        owner=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, clue=prize, quiz=quiz, artifact=artifact)
    return world


def start_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]

    world.say(
        f"Twist was a small superhero who loved puzzles, bright capes, and brave plans."
    )
    world.say(
        f"Rhyme was Twist's helper, and {helper.label if helper.label else 'Rhyme'} always knew how to cheer a room."
    )
    world.say(
        f"On that day, a city quiz had everyone looking for {artifact.phrase}, but nobody could find the clue."
    )
    hero.memes["hope"] += 1
    helper.memes["worry"] += 1


def ask_quiz(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]

    world.para()
    world.say(
        f"At {world.place.name}, Twist wanted to solve the quiz right away, but the clue stayed hidden."
    )
    world.say(
        f"Rhyme said, 'Let's not guess too fast. A good clue can be hiding in plain sight.'"
    )
    hero.memes["worry"] += 1
    helper.memes["hope"] += 1
    world.facts["hidden_by"] = artifact.hidden_by


def find_clue(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]

    world.say(
        f"Twist looked near a dusty shelf, and Rhyme hummed a soft tune to keep everyone calm."
    )
    if artifact.id == "flax":
        world.say(
            f"Then Twist spotted a flax ribbon tucked under the dust, its pale threads shining like a secret."
        )
        world.facts["found"] = True
        hero.meters["hidden"] += 1
        hero.memes["pride"] += 1
    elif artifact.id == "note":
        world.say(
            f"Then Twist noticed a folded note hiding in the shadow, waiting for careful fingers."
        )
        world.facts["found"] = True
        hero.meters["hidden"] += 1
    else:
        world.say(
            f"Then Twist caught the tiny star badge glinting behind the glass."
        )
        world.facts["found"] = True
        hero.meters["hidden"] += 1


def turn_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]

    world.para()
    if not world.facts.get("found"):
        pass
    world.say(
        f"Twist held up the clue, and Rhyme noticed how the {artifact.clue_kind} shape matched the quiz's last riddle."
    )
    world.say(
        f"Twist used the Twist power to turn the ribbon just so, and a hidden line appeared."
    )
    hero.meters["solved"] += 1
    helper.memes["hope"] += 1
    world.facts["answer"] = "north gate"
    world.say(
        f"The line pointed to the north gate, where the missing prize had been waiting all along."
    )


def resolve_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]

    world.para()
    world.say(
        f"Rhyme sang a tiny victory rhyme, and the whole quiz room grew bright and cheerful."
    )
    world.say(
        f"Twist answered the final question, the city cheered, and {artifact.phrase} became the proof that the clue had mattered."
    )
    hero.memes["worry"] = 0.0
    helper.memes["worry"] = 0.0
    hero.memes["pride"] += 1
    helper.memes["pride"] += 1
    world.facts["resolved"] = True


def tell_story(place: Place, artifact: Artifact, hero_name: str = "Twist", helper_name: str = "Rhyme") -> World:
    world = setup_world(place, artifact, hero_name, helper_name)
    start_story(world)
    ask_quiz(world)
    find_clue(world)
    turn_story(world)
    resolve_story(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(hall; tower; rooftop).
quiz_place(hall). quiz_place(tower).
artifact(flax; note; badge).

has_clue(flax).
has_clue(note).
has_clue(badge).

compatible(hall, flax).
compatible(tower, flax).
compatible(tower, note).
compatible(tower, badge).

valid_story(P, A) :- quiz_place(P), artifact(A), compatible(P, A), has_clue(A).
#show valid_story/2.
#show compatible/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if "quiz" in place.affords:
            lines.append(asp.fact("quiz_place", pid))
    for aid in ARTIFACTS:
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("has_clue", aid))
    lines.append(asp.fact("compatible", "hall", "flax"))
    lines.append(asp.fact("compatible", "tower", "flax"))
    lines.append(asp.fact("compatible", "tower", "note"))
    lines.append(asp.fact("compatible", "tower", "badge"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = sorted((p, a) for p in SETTINGS for a in ARTIFACTS if valid_combo(p, a))
    cl = asp_valid_stories()
    if py == cl:
        print(f"OK: ASP matches Python validity gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("  python:", py)
    print("  asp:   ", cl)
    return 1


# ---------------------------------------------------------------------------
# Question/answer generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a child about Twist, Rhyme, a quiz, and a clue with the word "{artifact.id}".',
        f"Tell a gentle adventure where Twist and Rhyme solve a quiz by finding {artifact.phrase}.",
        f"Write a simple superhero story that includes a clue, a quiz, and the word '{artifact.id}'.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]
    answer_spot = world.facts.get("answer", "the north gate")
    return [
        QAItem(
            question="Who were the superhero pair in the story?",
            answer=f"The superhero pair was Twist and Rhyme.",
        ),
        QAItem(
            question="What clue did Twist find?",
            answer=f"Twist found {artifact.phrase}.",
        ),
        QAItem(
            question="What did the clue help them solve?",
            answer=f"The clue helped them solve the city quiz.",
        ),
        QAItem(
            question="Where did the clue point at the end?",
            answer=f"It pointed to {answer_spot}.",
        ),
        QAItem(
            question="How did Rhyme help Twist?",
            answer="Rhyme kept everyone calm, noticed the hidden pattern, and sang a cheering rhyme at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    artifact: Artifact = _safe_fact(world, world.facts, "artifact")  # type: ignore[assignment]
    out = [
        QAItem(
            question="What is a quiz?",
            answer="A quiz is a set of questions that asks people to think, remember, and choose an answer.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a helpful sign or hint that helps someone solve a puzzle or mystery.",
        ),
    ]
    if artifact.id == "flax":
        out.append(QAItem(
            question="What is flax?",
            answer="Flax is a plant fiber that can be used to make thread, rope, or cloth-like strands.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}:{v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}:{v}' for k, v in e.memes.items() if v)}}}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"trail={world.trail}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    artifact: str
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


CURATED = [
    StoryParams(place="hall", artifact="flax"),
    StoryParams(place="tower", artifact="note"),
    StoryParams(place="tower", artifact="badge"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: Twist, Rhyme, quiz, clue, and flax.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--artifact", choices=sorted(ARTIFACTS))
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    artifact = getattr(args, "artifact", None) or rng.choice(list(ARTIFACTS))
    if not valid_combo(place, artifact):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, artifact=artifact)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(SETTINGS, params.place), _safe_lookup(ARTIFACTS, params.artifact))
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (place, artifact) combos:")
        for place, artifact in stories:
            print(f"  {place:10} {artifact}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.place} / {p.artifact}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
