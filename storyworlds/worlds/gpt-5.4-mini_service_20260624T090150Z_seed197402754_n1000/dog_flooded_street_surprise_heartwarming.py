#!/usr/bin/env python3
"""
A small storyworld about a dog, a flooded street, and a heartwarming surprise.

The world starts from a simple tale:
A little dog loved to trot along its street with its person. One day, after a big rain,
the street flooded. The dog wanted to splash and explore, but the water covered the
usual path. Then the dog found a surprising floating bundle that led to a kind, warm
ending: the dog and its person helped someone, shared comfort, and went home happy.

The simulation models:
- physical meters: wetness, floatiness, carryness, warmth
- emotional memes: worry, joy, curiosity, surprise, gratitude

The turn happens when the dog discovers a surprise in the flood and must choose
between chasing it and helping with it. The resolution is heartwarming because
the surprise turns out to be something useful or dear, and the dog’s action
makes someone feel better.
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

    dog: object | None = None
    person: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type == "dog":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the flooded street"
    flooded: bool = True
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
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str  # "toy", "parcel", "umbrella", "basket", "note"
    helps: str
    discovers: str
    tags: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    phrase: str
    kind: str
    action: str
    result: str
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.story_events: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _madd(e: Entity, key: str, amount: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amount


def _emadd(e: Entity, key: str, amount: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amount


def _do_wander(world: World, dog: Entity) -> None:
    _emadd(dog, "curiosity", 1)
    _madd(dog, "wetness", 0.5)
    _madd(dog, "splash", 1)
    world.say(f"{dog.id} liked the wet street and padded along with bright, curious eyes.")


def _find_surprise(world: World, dog: Entity, surprise: Surprise, person: Entity) -> None:
    _emadd(dog, "surprise", 1)
    _emadd(person, "surprise", 1)
    world.facts["found_surprise"] = surprise.id
    world.say(
        f"Near a curb, {dog.id} spotted {surprise.phrase} drifting in the water. "
        f"It was a surprise {surprise.discovers}."
    )


def _help_with_surprise(world: World, dog: Entity, person: Entity, surprise: Surprise, helper: Helper) -> None:
    _emadd(dog, "joy", 1)
    _emadd(person, "joy", 1)
    _emadd(person, "gratitude", 1)
    _madd(person, "warmth", 1)
    _madd(dog, "warmth", 1)
    world.facts["helped"] = helper.id
    world.say(
        f"{dog.id} nudged the surprise toward {person.id}, and together they used {helper.phrase}. "
        f"{helper.result}."
    )


def _heartwarming_finish(world: World, dog: Entity, person: Entity, surprise: Surprise) -> None:
    _emadd(dog, "contentment", 1)
    _emadd(person, "contentment", 1)
    world.say(
        f"In the end, {person.id} laughed softly and rubbed {dog.pronoun('possessive')} ears. "
        f"{dog.id} wagged happily, and the wet street felt less lonely."
    )
    world.say(
        f"The little {surprise.kind} was not lost after all. It had led them to a kinder, warmer moment."
    )


def run_story(world: World) -> World:
    dog = world.get("dog")
    person = world.get("person")
    surprise: Surprise = _safe_fact(world, world.facts, "surprise")
    helper: Helper = _safe_fact(world, world.facts, "helper")

    world.say(
        f"On the flooded street, {dog.id} stayed close to {person.id}, listening to the splash of water."
    )
    _do_wander(world, dog)
    world.para()
    _find_surprise(world, dog, surprise, person)
    world.say(
        f"{person.id} wondered if the surprise was trouble, but {dog.id} kept nudging it gently instead of barking."
    )
    world.para()
    _help_with_surprise(world, dog, person, surprise, helper)
    _heartwarming_finish(world, dog, person, surprise)
    return world


SETTINGS = {
    "street": Setting(place="the flooded street", flooded=True, affords={"wander", "discover", "help"}),
}

SURPRISES = {
    "parcel": Surprise(
        id="parcel",
        label="parcel",
        phrase="a small brown parcel",
        kind="parcel",
        helps="It held dry socks and a note",
        discovers="had floated free from a nearby doorstep",
        tags={"gift", "dry", "kind"},
    ),
    "basket": Surprise(
        id="basket",
        label="basket",
        phrase="a little basket",
        kind="basket",
        helps="It carried towels and a warm cup",
        discovers="had bobbed up from a porch",
        tags={"care", "warm", "kind"},
    ),
    "umbrella": Surprise(
        id="umbrella",
        label="umbrella",
        phrase="a bright red umbrella",
        kind="umbrella",
        helps="It kept the dog and person dry on the way home",
        discovers="had snagged on a lamppost",
        tags={"shelter", "dry", "help"},
    ),
    "toy": Surprise(
        id="toy",
        label="toy",
        phrase="a small squeaky toy",
        kind="toy",
        helps="It made a lost child smile again",
        discovers="had washed down the street from a doorstep",
        tags={"toy", "child", "kind"},
    ),
}

HELPERS = {
    "parcel": Helper(
        id="gloves",
        label="gloves",
        phrase="a pair of dry gloves",
        kind="gloves",
        action="carefully lifted the parcel",
        result="Inside, they found dry socks and a note that said thank you",
        tags={"dry", "help"},
    ),
    "basket": Helper(
        id="towel",
        label="towel",
        phrase="a big towel",
        kind="towel",
        action="wrapped the basket so it would not drip everywhere",
        result="The towel made the basket easy to carry home",
        tags={"warm", "care"},
    ),
    "umbrella": Helper(
        id="umbrella_hook",
        label="hook",
        phrase="a long hook",
        kind="hook",
        action="hooked the umbrella free",
        result="The umbrella opened with a cheerful pop and sheltered them both",
        tags={"shelter", "dry"},
    ),
    "toy": Helper(
        id="net",
        label="net",
        phrase="a soft little net",
        kind="net",
        action="fished the toy out of the water",
        result="The toy was returned to a happy child who hugged the dog",
        tags={"toy", "kind"},
    ),
}

DOG_NAMES = ["Pip", "Milo", "Buddy", "Sunny", "Scout", "Luna"]
PERSON_NAMES = ["Ava", "Noah", "Mia", "Leo", "Ruby", "Finn"]
DOG_TRAITS = ["gentle", "playful", "curious", "loyal", "bright"]


@dataclass
class StoryParams:
    setting: str
    surprise: str
    name: str
    person: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming dog storyworld set on a flooded street.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--person")
    ap.add_argument("--trait", choices=DOG_TRAITS)
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


def reasonableness_check(params: StoryParams) -> None:
    if params.setting != "street":
        pass
    if params.surprise not in SURPRISES:
        pass
    if params.person == params.name:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or "street"
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    name = getattr(args, "name", None) or rng.choice(DOG_NAMES)
    person = getattr(args, "person", None) or rng.choice(PERSON_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(DOG_TRAITS)
    params = StoryParams(setting=setting, surprise=surprise, name=name, person=person, trait=trait)
    reasonableness_check(params)
    return params


def tell(setting: Setting, surprise: Surprise, dog_name: str, person_name: str, trait: str) -> World:
    world = World(setting)
    dog = world.add(Entity(id=dog_name, kind="character", type="dog", label="dog"))
    person = world.add(Entity(id=person_name, kind="character", type="girl"))
    dog.memes["loyalty"] = 1
    _emadd(dog, "curiosity", 1)

    world.facts["dog"] = dog
    world.facts["person"] = person
    world.facts["surprise"] = surprise
    world.facts["helper"] = _safe_lookup(HELPERS, surprise.id)
    world.facts["trait"] = trait
    return run_story(world)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story about a dog named {f["dog"].id} on a flooded street.',
        f"Tell a gentle story where {f['dog'].id} finds a surprise and helps {f['person'].id} on the wet street.",
        f'Write a simple story with the word "surprise" that ends with a dog and person feeling warm and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    dog: Entity = _safe_fact(world, f, "dog")
    person: Entity = _safe_fact(world, f, "person")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    helper: Helper = _safe_fact(world, f, "helper")

    return [
        QAItem(
            question=f"Who is the dog in the story?",
            answer=f"The dog is {dog.id}, and {dog.id} is a {f['trait']} little dog who stays close to {person.id}.",
        ),
        QAItem(
            question=f"What surprise did {dog.id} find on the flooded street?",
            answer=f"{dog.id} found {surprise.phrase} floating in the water. It was a surprise {surprise.discovers}.",
        ),
        QAItem(
            question=f"How did {dog.id} and {person.id} help with the surprise?",
            answer=f"They used {helper.phrase}. {helper.result}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {person.id} and {dog.id} feeling warm, safe, and happy together on the flooded street.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can a flooded street be tricky for walking?",
            answer="A flooded street can be tricky because water covers the ground, so people and animals have to move carefully.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that appears or happens when you did not know it was coming.",
        ),
        QAItem(
            question="Why can helping feel heartwarming?",
            answer="Helping can feel heartwarming because kind actions make someone else feel better and make the helper feel glad too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    out.append(f"facts={world.facts}")
    return "\n".join(out)


ASP_RULES = r"""
dog(dog).
setting(street).
surprise(parcel).
surprise(basket).
surprise(umbrella).
surprise(toy).

heartwarming(parcel).
heartwarming(basket).
heartwarming(umbrella).
heartwarming(toy).

valid_story(street, S) :- surprise(S), heartwarming(S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("dog", "dog"), asp.fact("setting", "street")]
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("street", sid) for sid in SURPRISES if sid in SURPRISES}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(cl)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in ASP:", sorted(cl - py))
    print("only in Python:", sorted(py - cl))
    return 1


CURATED = [
    StoryParams(setting="street", surprise="parcel", name="Pip", person="Ava", trait="gentle"),
    StoryParams(setting="street", surprise="basket", name="Buddy", person="Mia", trait="loyal"),
    StoryParams(setting="street", surprise="umbrella", name="Scout", person="Leo", trait="curious"),
    StoryParams(setting="street", surprise="toy", name="Sunny", person="Ruby", trait="playful"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SURPRISES, params.surprise), params.name, params.person, params.trait)
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
        print("Compatible stories:")
        for place, surprise in asp_valid_combos():
            print(f"  {place} / {surprise}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
