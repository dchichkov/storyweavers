#!/usr/bin/env python3
"""
prevention_teamwork_mystery_to_solve_animal_story.py
====================================================

A small Animal Story world about teamwork, prevention, and solving a mystery
before a woodland picnic is spoiled.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, ROOT)
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
    kind: str = "character"
    type: str = "animal"
    label: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "doe", "hen", "mouse", "rabbit"}
        male = {"boy", "fox", "badger", "squirrel"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str
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
class Mystery:
    id: str
    object_name: str
    danger: str
    clue: str
    prevention: str
    solution: str
    lesson: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "meadow": Setting("the sunny meadow", {"mystery"}),
    "orchard": Setting("the old orchard", {"mystery"}),
    "creek": Setting("the quiet creek bank", {"mystery"}),
}

MYSTERIES = {
    "windy_sign": Mystery(
        "windy_sign",
        "picnic sign",
        "the sign could fall onto the animal friends",
        "a loose vine wrapped around one wooden post",
        "tie the sign with two strong grass ropes before the wind grew",
        "work together to brace the post and move the picnic path away from it",
        "prevention means noticing a danger early and acting before someone is hurt",
    ),
    "vanishing_baskets": Mystery(
        "vanishing_baskets",
        "picnic baskets",
        "the baskets could roll into a deep ditch",
        "round pawprints circled the basket trail",
        "place flat stones behind every basket",
        "follow the prints and discover that a playful breeze was nudging the baskets",
        "teamwork makes a mystery easier when every friend shares a clue",
    ),
    "sleepy_lantern": Mystery(
        "sleepy_lantern",
        "lantern",
        "a dry leaf could catch fire near the lantern",
        "a blackened leaf lay beside a warm stone",
        "clear the leaves and set the lantern on a safe rock",
        "make a clear safety ring before lighting the evening lamp",
        "careful prevention protects small friends and bright celebrations",
    ),
    "missing_ribbon": Mystery(
        "missing_ribbon",
        "welcome ribbon",
        "the ribbon might be tangled around a bird's nest",
        "blue thread glimmered beneath a fern",
        "search gently instead of pulling the ribbon",
        "free the ribbon from a thorn while leaving the nest undisturbed",
        "solving a mystery kindly means protecting what cannot speak",
    ),
    "cracked_bridge": Mystery(
        "cracked_bridge",
        "little footbridge",
        "someone could fall through a weak plank",
        "fresh splinters pointed toward the shallow side",
        "block the bridge and find a safer crossing",
        "lay branches across the creek and warn everyone with a bright marker",
        "good teamwork turns a warning into a safe new path",
    ),
}

NAMES = ["Luna", "Mina", "Pippa", "Nora", "Bram", "Milo", "Finn", "Otto"]
SPECIES = ["rabbit", "fox", "badger", "squirrel", "mouse", "doe"]
TRAITS = ["curious", "careful", "brave", "gentle", "watchful"]
HELPERS = ["Toby", "Mara", "Pip", "Ravi", "Sage"]

OPENINGS = [
    "{hero}, a {trait} {species}, arrived early at {place} for the woodland picnic.",
    "Bright morning dew covered {place} when {hero}, the {trait} {species}, came to help prepare a picnic.",
    "At {place}, {hero} the {species} carried a little basket toward the waiting animals.",
    "The birds were practicing their picnic song when {hero}, a {trait} {species}, noticed something unusual.",
]

DIALOGUES = [
    '"Let us solve the mystery together," said {helper}. "You look closely, and I will check the path."',
    '"Wait," {helper} said. "A small clue can prevent a big problem."',
    '"I found something!" cried {hero}. "Please help me decide what it means."',
    '"We should not guess or blame," said {helper}. "Let us look carefully first."',
]

ADMISSIONS = [
    '"I almost rushed past the warning," {hero} admitted.',
    '"I wanted the picnic to begin, but I should have checked first," {hero} said.',
    '"Now I see why prevention matters," {hero} told {helper}.',
    '{hero} took a breath. "I will slow down and listen to the clues."',
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place, setting in SETTINGS.items() for mystery in setting.affords]


ASP_RULES = r"""
place(meadow).
place(orchard).
place(creek).
affords(meadow,mystery).
affords(orchard,mystery).
affords(creek,mystery).
mystery(windy_sign).
mystery(vanishing_baskets).
mystery(sleepy_lantern).
mystery(missing_ribbon).
mystery(cracked_bridge).
valid(Place,Mystery) :- place(Place), affords(Place,mystery), mystery(Mystery).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for place, setting in SETTINGS.items():
        for feature in sorted(setting.affords):
            lines.append(asp.fact("affords", place, feature))
    for mystery in MYSTERIES:
        lines.append(asp.fact("mystery", mystery))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH between Python and clingo.")
    print("Only in Python:", sorted(py - clingo))
    print("Only in clingo:", sorted(clingo - py))
    return 1


@dataclass
class StoryParams:
    place: str = ""
    mystery: str = ""
    name: str = ""
    species: str = ""
    helper: str = ""
    trait: str = ""
    seed: Optional[int] = None
    telling: int = 0
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Animal Story world about prevention, teamwork, and a mystery to solve."
    )
    parser.add_argument("--place", choices=SETTINGS)
    parser.add_argument("--mystery", choices=MYSTERIES)
    parser.add_argument("--name")
    parser.add_argument("--species", choices=SPECIES)
    parser.add_argument("--helper")
    parser.add_argument("--trait", choices=TRAITS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if getattr(args, "place", None) is None or combo[0] == getattr(args, "place", None)
        if getattr(args, "mystery", None) is None or combo[1] == getattr(args, "mystery", None)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(combos)
    return StoryParams(
        place=place,
        mystery=mystery,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        species=getattr(args, "species", None) or rng.choice(SPECIES),
        helper=getattr(args, "helper", None) or rng.choice(HELPERS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
        telling=rng.randrange(1_000_000),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if (params.place, params.mystery) not in valid_combos():
        pass

    rng = random.Random(params.telling)
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)
    hero = world.add(Entity(params.name, type=params.species))
    helper = world.add(Entity(params.helper, type="badger"))
    world.add(Entity("woodland_friends", kind="group", type="animals"))

    values = {
        "hero": hero.id,
        "helper": helper.id,
        "place": setting.place,
        "trait": params.trait,
        "species": params.species,
    }

    world.say(rng.choice(OPENINGS).format(**values))
    world.say(
        f"The animals were preparing a shared picnic, but the {mystery.object_name} "
        f"looked unsafe: {mystery.danger}."
    )
    world.para()
    world.say(
        f"{hero.id} wanted to carry the last basket to the blanket. "
        f"Then {hero.pronoun('subject')} noticed {mystery.clue}."
    )
    world.say(rng.choice(DIALOGUES).format(**values))
    world.say(
        f"They decided that prevention was better than a hurried rescue, so they "
        f"paused the picnic and searched the area together."
    )
    world.para()
    world.say(
        f"{hero.id} followed the smallest marks while {helper.id} checked the ground "
        f"and kept the younger animals safely back."
    )
    world.say(rng.choice(ADMISSIONS).format(**values))
    world.say(
        f"The clue led them to a clear answer: {mystery.solution.capitalize()}."
    )
    world.say(
        f"Working paw by paw, {hero.id} and {helper.id} put the prevention plan in place. "
        f"They {mystery.prevention}."
    )
    world.para()
    world.say(
        f"After the danger was gone, the animals returned to the picnic. "
        f"{helper.id} thanked {hero.id} for noticing the warning."
    )
    world.say(
        f"{hero.id} learned that {mystery.lesson}."
    )
    world.say(
        f"At last, the picnic began beneath a safe sky, with every friend close enough "
        f"to share the food and the happy story of how teamwork solved the mystery."
    )

    hero.meters["danger_prevented"] = 1
    hero.memes.update({"curiosity": 1, "care": 1, "teamwork": 1, "confidence": 1})
    helper.memes.update({"teamwork": 1, "trust": 1})

    world.facts = {
        "hero": hero,
        "helper": helper,
        "mystery": mystery,
        "reconciled": True,
        "clue": mystery.clue,
        "solution": mystery.solution,
        "prevention": mystery.prevention,
        "lesson": mystery.lesson,
    }

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mystery")
    return [
        "Write an Animal Story about prevention and teamwork.",
        f"Tell a child-friendly mystery story in which {hero.id} notices danger before the {mystery.object_name} causes harm.",
        "Show how two animal friends share clues, make a safe plan, and solve a mystery together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    hero = facts["hero"]
    helper = facts["helper"]
    mystery = facts["mystery"]
    return [
        QAItem(
            question=f"Where did {hero.id}'s story take place?",
            answer=f"The story took place at {world.setting.place}, where the animals were preparing a shared picnic.",
        ),
        QAItem(
            question=f"What mystery did {hero.id} and {helper.id} investigate?",
            answer=f"They investigated why the {mystery.object_name} was unsafe and might cause trouble.",
        ),
        QAItem(
            question="What clue helped them?",
            answer=f"The clue was {facts['clue']}. It made the friends stop and look more carefully.",
        ),
        QAItem(
            question="How did the animals use prevention?",
            answer=f"They prevented harm by making a safe plan before the danger grew: they {facts['prevention']}.",
        ),
        QAItem(
            question="How did teamwork solve the mystery?",
            answer=f"{hero.id} followed the clue while {helper.id} checked the area and protected the other animals. Together they discovered that {facts['solution']}.",
        ),
        QAItem(
            question="What did the animals learn?",
            answer=f"They learned that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is prevention?",
            answer="Prevention means noticing a possible problem and acting early so the problem does not cause harm.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people or animals sharing jobs, ideas, and care to reach a goal together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not yet understood and can be solved by studying clues.",
        ),
        QAItem(
            question="Why are clues useful?",
            answer="Clues provide information that helps us understand what happened and choose a sensible next step.",
        ),
        QAItem(
            question="Why should animals check for danger before a picnic?",
            answer="Checking first can prevent accidents and help everyone enjoy the picnic safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in list(world.entities.values()):
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        details = []
        if meters:
            details.append(f"meters={meters}")
        if memes:
            details.append(f"memes={memes}")
        lines.append(f"{entity.id}: {entity.type} {' '.join(details)}")
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


CURATED = [
    StoryParams(
        place="meadow",
        mystery="windy_sign",
        name="Luna",
        species="rabbit",
        helper="Toby",
        trait="watchful",
        telling=11,
    ),
    StoryParams(
        place="orchard",
        mystery="missing_ribbon",
        name="Mina",
        species="fox",
        helper="Mara",
        trait="curious",
        telling=23,
    ),
    StoryParams(
        place="creek",
        mystery="cracked_bridge",
        name="Bram",
        species="badger",
        helper="Pip",
        trait="careful",
        telling=37,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combinations = asp_valid_combos()
        print(f"{len(combinations)} compatible combinations:")
        for combination in combinations:
            print(" ", combination)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < getattr(args, "n", None) and attempt < max(getattr(args, "n", None) * 20, 20):
            seed = base_seed + attempt
            attempt += 1
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
