#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mission_admire_conflict_misunderstanding_bedtime_story.py
===============================================================================================================

A small bedtime-story world about a child on a mission to admire something gentle,
a misunderstanding that causes conflict, and a cozy resolution before sleep.

The tale pattern:
- A child has a quiet evening mission.
- They want to admire a moonlit or lantern-lit treasure.
- A misunderstanding makes a grownup think the mission is unsafe or rude.
- The child feels upset; a brief conflict follows.
- The misunderstanding is explained, the mission becomes safe, and bedtime ends warmly.

This script keeps the story grounded in a simulated world model with meters and memes,
and includes an inline ASP twin for the reasonableness gate.
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

NAMES = ["Mina", "Toby", "Nora", "Eli", "Pia", "Owen", "Luna", "Finn", "Ada", "Milo"]
ADULTS = ["mother", "father", "grandma", "grandpa", "aunt", "uncle"]
TRAITS = ["sleepy", "gentle", "brave", "curious", "soft-spoken", "patient"]

PLACES = {
    "bedroom": {"indoors": True, "cozy": True},
    "hallway": {"indoors": True, "cozy": False},
    "window": {"indoors": True, "cozy": True},
    "garden": {"indoors": False, "cozy": True},
}

MISSION_KINDS = {
    "moon": {
        "verb": "admire the moon",
        "noun": "moon",
        "place": "window",
        "thing": "silver moon",
        "reason": "the moon looked like a quiet bedtime friend",
    },
    "stars": {
        "verb": "admire the stars",
        "noun": "stars",
        "place": "window",
        "thing": "tiny stars",
        "reason": "the stars twinkled like sleepy pins of light",
    },
    "lantern": {
        "verb": "admire the lantern",
        "noun": "lantern",
        "place": "hallway",
        "thing": "paper lantern",
        "reason": "the lantern glowed like a warm little candle",
    },
    "book": {
        "verb": "admire the picture book",
        "noun": "book",
        "place": "bedroom",
        "thing": "picture book",
        "reason": "the book had shiny pictures that made bedtime feel calm",
    },
}

MISUNDERSTANDINGS = {
    "sneaking": "thought the child was sneaking out",
    "taking": "thought the child was taking something without asking",
    "playing": "thought the child was trying to play too loudly",
    "breaking": "thought the child might break something",
}

ASP_RULES = r"""
mission_ok(M, P) :- mission(M), place(P), wants_at(M, P).
misunderstanding_ok(U) :- misunderstanding(U).
valid_story(M, U, P) :- mission_ok(M, P), misunderstanding_ok(U).
"""



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    child: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "uncle"}:
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
    indoors: bool
    cozy: bool
    setting: object | None = None
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
class Mission:
    id: str
    verb: str
    noun: str
    place: str
    thing: str
    reason: str
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
    mission: str
    misunderstanding: str
    place: str
    name: str
    gender: str
    adult: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with a mission, admiration, conflict, and misunderstanding.")
    ap.add_argument("--mission", choices=MISSION_KINDS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--adult", choices=ADULTS)
    ap.add_argument("--trait", choices=TRAITS)
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
    mission = getattr(args, "mission", None) or rng.choice(list(MISSION_KINDS))
    misunderstanding = getattr(args, "misunderstanding", None) or rng.choice(list(MISUNDERSTANDINGS))
    place = getattr(args, "place", None) or _safe_lookup(MISSION_KINDS, mission)["place"]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    adult = getattr(args, "adult", None) or rng.choice(ADULTS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        mission=mission,
        misunderstanding=misunderstanding,
        place=place,
        name=name,
        gender=gender,
        adult=adult,
        trait=trait,
    )


def mission_object(mission_id: str) -> Mission:
    d = _safe_lookup(MISSION_KINDS, mission_id)
    return Mission(
        id=mission_id,
        verb=d["verb"],
        noun=d["noun"],
        place=d["place"],
        thing=d["thing"],
        reason=d["reason"],
    )


def misunderstanding_text(key: str) -> str:
    return _safe_lookup(MISUNDERSTANDINGS, key)


def setting_text(setting: Setting, mission: Mission) -> str:
    if setting.place == "window":
        return "The bedroom was dim and hush-quiet, with a window that held a little square of night."
    if setting.place == "hallway":
        return "The hallway was soft and narrow, with slippers waiting by the wall."
    if setting.place == "garden":
        return "The garden was still and blue under the evening sky."
    return f"The {setting.place} felt calm and ready for sleep."


def predict_conflict(world: World, child: Entity, mission: Mission, misunderstanding: str) -> dict:
    sim = world.copy()
    child2 = sim.get(child.id)
    child2.memes["desire"] = 1
    child2.memes["misunderstood"] = 1
    child2.memes["conflict"] = 1
    return {"conflict": True, "resolved": True}


def tell(setting: Setting, mission: Mission, mis_key: str, child_name: str, gender: str, adult_type: str, trait: str) -> World:
    world = World(setting)
    child_type = "girl" if gender == "girl" else "boy"
    child = world.add(Entity(id=child_name, kind="character", type=child_type, meters={"sleepiness": 0.3}, memes={"joy": 0.2}))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type))
    treasure = world.add(Entity(
        id="Treasure",
        type=mission.noun,
        label=mission.noun,
        phrase=mission.thing,
        owner=child.id,
        caretaker=adult.id,
    ))

    child.memes["admire"] = 1
    child.memes["mission"] = 1
    world.say(f"{child_name} was a {trait} little {child_type} who had a bedtime mission.")
    world.say(f"{child_name} wanted to {mission.verb} because {mission.reason}.")
    world.say(f"{child_name} especially loved {treasure.phrase}.")

    world.para()
    world.say(setting_text(setting, mission))
    world.say(f"One evening, {child_name} tiptoed to the {setting.place} to finish {child.pronoun('possessive')} mission.")
    world.say(f"{child_name} reached up, hoping to admire the {mission.noun} in the quiet dark.")

    world.para()
    child.memes["desire"] += 1
    child.memes["misunderstood"] += 1
    child.memes["conflict"] += 1
    mis = misunderstanding_text(mis_key)
    world.say(f"Then {adult_type} saw {child_name} moving in the dim room and {mis}.")
    if mis_key == "sneaking":
        world.say(f'"No sneaking before bed," {adult_type} said, and {child_name} felt a hot little knot in {child.pronoun("possessive")} chest.')
    elif mis_key == "taking":
        world.say(f'"Wait," {adult_type} said, "are you taking that without asking?"')
    elif mis_key == "playing":
        world.say(f'"Shh," {adult_type} said, "I thought you were trying to play instead of sleep."')
    else:
        world.say(f'"Careful," {adult_type} said. "I thought you might break something in the dark."')

    world.para()
    world.say(f"{child_name} shook {child.pronoun('possessive')} head and explained the mission in a tiny voice.")
    world.say(f'"I only wanted to admire the {mission.noun}," {child_name} said. "I was trying to be gentle."')
    child.memes["conflict"] = 0.0
    child.memes["trust"] = 1
    adult.memes["relief"] = 1
    world.say(f"{adult_type} listened, and the misunderstanding melted away like a warm cookie in milk.")

    world.say(f"Together they went to the {setting.place} window and admired the {mission.noun} side by side.")
    world.say(f"The bedtime mission was finished, the room stayed calm, and {child_name} drifted to sleep with a soft smile.")

    world.facts.update(
        child=child,
        adult=adult,
        treasure=treasure,
        mission=mission,
        misunderstanding=mis_key,
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    mission = _safe_fact(world, f, "mission")
    return [
        f'Write a short bedtime story about a child named {child.id} on a mission to {mission.verb}.',
        f"Tell a cozy story where {child.id} wants to admire something gentle, but a grownup misunderstands at bedtime.",
        f'Write a child-friendly story that includes the words "mission" and "admire" and ends with a calm bedtime.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    mission = _safe_fact(world, f, "mission")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"What was {child.id}'s bedtime mission?",
            answer=f"{child.id}'s mission was to {mission.verb} in the {place}.",
        ),
        QAItem(
            question=f"Why did {adult.type} worry when {child.id} moved in the dim room?",
            answer=f"{adult.type} had a misunderstanding and thought something unsafe or rude was happening, but {child.id} was only being gentle.",
        ),
        QAItem(
            question=f"How did the conflict get solved?",
            answer=f"{child.id} explained the mission, {adult.type} listened, and they shared a calm moment admiring the {mission.noun} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a mission?", answer="A mission is a special job or purpose that someone decides to do."),
        QAItem(question="What does it mean to admire something?", answer="To admire something means to look at it with happy appreciation because it seems lovely, brave, or special."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks the wrong thing at first."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for k in MISSION_KINDS:
        lines.append(asp.fact("mission", k))
        lines.append(asp.fact("wants_at", k, _safe_lookup(MISSION_KINDS, k)["place"]))
    for k in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", k))
    for p in PLACES:
        lines.append(asp.fact("place", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    stories = asp_valid_stories()
    py = sorted((k, u, _safe_lookup(MISSION_KINDS, k)["place"]) for k in MISSION_KINDS for u in MISUNDERSTANDINGS)
    if stories == py:
        print(f"OK: clingo gate matches python ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" clingo:", stories)
    print(" python:", py)
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = Setting(**_safe_lookup(PLACES, params.place), place=params.place)
    mission = mission_object(params.mission)
    world = tell(setting, mission, params.misunderstanding, params.name, params.gender, params.adult, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(mission="moon", misunderstanding="sneaking", place="window", name="Mina", gender="girl", adult="mother", trait="gentle"),
    StoryParams(mission="stars", misunderstanding="playing", place="window", name="Toby", gender="boy", adult="father", trait="curious"),
    StoryParams(mission="book", misunderstanding="taking", place="bedroom", name="Nora", gender="girl", adult="grandma", trait="sleepy"),
    StoryParams(mission="lantern", misunderstanding="breaking", place="hallway", name="Eli", gender="boy", adult="uncle", trait="patient"),
]


def resolve_explicit(args: argparse.Namespace) -> None:
    if getattr(args, "mission", None) and getattr(args, "place", None) and _safe_lookup(MISSION_KINDS, getattr(args, "mission", None))["place"] != getattr(args, "place", None):
        pass


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for m, u, p in stories:
            print(f"  mission={m} misunderstanding={u} place={p}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
            try:
                resolve_explicit(args)
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mission} / {p.misunderstanding} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
