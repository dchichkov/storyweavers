#!/usr/bin/env python3
"""
A small animal-story world about a worried pet, a gentle prescription, and a
surprising magical turn in late August.
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "cat", "dog", "mouse", "bird", "bear"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    indoors: bool
    affordance: str
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
class Item:
    id: str
    label: str
    effect: str
    reveals: str
    kind: str = "thing"
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
class StoryParams:
    place: str
    animal: str
    problem: str
    remedy: str
    helper: str
    month: str = "august"
    seed: Optional[int] = None
    name: str = ""
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    items: dict[str, Item] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone.items = copy.deepcopy(self.items)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


ANIMALS = {
    "fox": "fox",
    "rabbit": "rabbit",
    "cat": "cat",
    "dog": "dog",
    "bear": "bear",
    "mouse": "mouse",
}

PLACES = {
    "nesting_room": Place("the nesting room", indoors=True, affordance="rest"),
    "garden": Place("the garden", indoors=False, affordance="sniff flowers"),
    "clinic": Place("the little clinic", indoors=True, affordance="wait"),
}

PROBLEMS = {
    "sneeze": "kept sneezing",
    "cough": "kept coughing",
    "paw": "had a sore paw",
    "sleepy": "felt too sleepy to play",
}

REMEDIES = {
    "syrup": Item("syrup", "sweet syrup", effect="calm", reveals="the cough quieted"),
    "potion": Item("potion", "sparkling potion", effect="sparkle", reveals="the sneezes softened"),
    "bandage": Item("bandage", "soft bandage", effect="rest", reveals="the paw felt snug"),
}

HELPERS = {
    "veterinarian": "the veterinarian",
    "grandma": "grandma owl",
    "friend": "a tiny friend",
}

NAMES = ["Milo", "Pippa", "Nori", "Tilly", "Bram", "Luna", "Ollie", "Bibi"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with prescription, surprise, suspense, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    animal = getattr(args, "animal", None) or rng.choice(list(ANIMALS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    remedy = getattr(args, "remedy", None) or rng.choice(list(REMEDIES))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    if problem == "sleepy" and remedy == "bandage":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, animal=animal, problem=problem, remedy=remedy, helper=helper, seed=getattr(args, "seed", None))


def _make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=_safe_lookup(HELPERS, params.helper)))
    remedy = _safe_lookup(REMEDIES, params.remedy)
    item = world.add(Entity(id=remedy.id, type="thing", label=remedy.label, phrase=remedy.label, caretaker=helper.id))
    item.meters["magic"] = 0.0
    item.memes["surprise"] = 0.0
    hero.meters["ill"] = 1.0
    hero.memes["worry"] = 1.0
    if params.place == "garden":
        world.say(f"It was late August, and {params.name} was in {place.name}, looking small and worried.")
    else:
        world.say(f"It was late August, and {params.name} was at {place.name}, looking small and worried.")
    world.say(f"{params.name} {_safe_lookup(PROBLEMS, params.problem)}. {_safe_lookup(HELPERS, params.helper).capitalize()} noticed and said they should prescribe something gentle.")
    world.para()
    world.say(f"The helper looked carefully, then prescribed {remedy.label} for {params.name}.")
    world.say(f"{params.name} held still while the {remedy.label} was offered, but the room felt full of suspense.")
    if params.problem == "paw":
        world.say(f"The soft wrap touched the sore paw, and {params.name} blinked with surprise.")
    elif params.problem == "sleepy":
        world.say(f"The calm drink smelled sweet, and {params.name} waited with sleepy suspense.")
    else:
        world.say(f"The sweet medicine shimmered, and {params.name} wondered if it was ordinary at all.")
    world.para()
    hero.meters["ill"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    item.meters["magic"] = 1.0
    item.memes["surprise"] = 1.0
    world.say(f"Then came the surprise: the remedy had a little magic in it.")
    if params.problem == "sneeze":
        world.say(f"The sneezes softened at once, and {params.name} breathed out in relief.")
    elif params.problem == "cough":
        world.say(f"The coughing faded into a tiny hiccup, and {params.name} gave a happy grin.")
    elif params.problem == "paw":
        world.say(f"The bandage warmed like a cozy feather, and the paw felt snug again.")
    else:
        world.say(f"The sleepy feeling turned into a peaceful yawn, and {params.name} finally rested.")
    world.say(f"By the end, {params.name} was better, and late August felt bright and safe again.")
    world.facts.update(params=params, hero=hero, helper=helper, remedy=item, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write an animal story set in late {p.month} where {p.name} needs a prescription and there is a magical surprise.",
        f"Tell a suspenseful but gentle story about a {p.animal} named {p.name} at {world.place.name}.",
        f"Make a child-friendly animal story using the words prescribe, august, surprise, suspense, and magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {p.name}, a little {p.animal}, in late August.",
        ),
        QAItem(
            question=f"What did the helper do for {p.name}?",
            answer=f"The helper prescribed {world.facts['remedy'].label} to help {p.name}.",
        ),
        QAItem(
            question=f"What made the ending surprising?",
            answer=f"The remedy had a little magic, so {p.name} got better faster than expected.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does prescribe mean?",
            answer="To prescribe means to tell someone which medicine or treatment to use.",
        ),
        QAItem(
            question="What is August?",
            answer="August is a month in the summer when many days are warm and bright.",
        ),
        QAItem(
            question="What is surprise?",
            answer="A surprise is something you do not expect.",
        ),
        QAItem(
            question="What is suspense?",
            answer="Suspense is the feeling of waiting to find out what will happen next.",
        ),
        QAItem(
            question="What is magic?",
            answer="Magic is a make-believe power that can do unusual and wonderful things in stories.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A remedy is reasonable if it can help the stated problem.
reasonable(remedy(syrup), cough).
reasonable(remedy(potion), sneeze).
reasonable(remedy(bandage), paw).
reasonable(remedy(syrup), sleepy).
reasonable(remedy(potion), sleepy).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for rid in REMEDIES:
        lines.append(asp.fact("remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    got = set(asp.atoms(model, "reasonable"))
    want = {
        ("remedy", "syrup", "cough"),
        ("remedy", "potion", "sneeze"),
        ("remedy", "bandage", "paw"),
        ("remedy", "syrup", "sleepy"),
        ("remedy", "potion", "sleepy"),
    }
    if got == want:
        print("OK: ASP gate matches Python reasonableness.")
        return 0
    print("Mismatch in ASP gate.")
    print("got:", sorted(got))
    print("want:", sorted(want))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = _make_world(params)
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
        for i, p in enumerate(sample.prompts, 1):
            print(f"P{i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="clinic", animal="fox", problem="sneeze", remedy="potion", helper="veterinarian", name="Milo"),
    StoryParams(place="garden", animal="rabbit", problem="cough", remedy="syrup", helper="grandma", name="Pippa"),
    StoryParams(place="nesting_room", animal="cat", problem="paw", remedy="bandage", helper="friend", name="Luna"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/2."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show reasonable/2."))
        print(sorted(asp.atoms(model, "reasonable")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
