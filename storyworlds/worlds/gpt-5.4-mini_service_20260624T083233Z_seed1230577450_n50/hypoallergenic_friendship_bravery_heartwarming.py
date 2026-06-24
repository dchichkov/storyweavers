#!/usr/bin/env python3
"""
A small heartwarming storyworld about friendship and bravery:
a child wants to meet a new hypoallergenic animal friend, feels nervous,
and learns that gentle courage can make a happy beginning.

The domain is intentionally compact and constraint-checked. The simulated state
tracks physical meters (like allergies, closeness, and comfort) and emotional
memes (like courage, worry, trust, and joy). Story events are authored from
that state instead of from a frozen text template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0



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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    pet: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj(self) -> str:
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
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Pet:
    id: str
    label: str
    phrase: str
    type: str
    hypoallergenic: bool = False
    shy: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class ComfortItem:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "home": Setting("the cozy home", {"gentle"}),
    "garden": Setting("the sunny garden", {"gentle", "visit"}),
    "vet": Setting("the animal clinic", {"gentle", "visit"}),
}

PETS = {
    "bunny": Pet(
        id="bunny",
        label="bunny",
        phrase="a tiny hypoallergenic bunny with silky ears",
        type="bunny",
        hypoallergenic=True,
        shy=True,
        tags={"animal", "hypoallergenic", "gentle"},
    ),
    "kitten": Pet(
        id="kitten",
        label="kitten",
        phrase="a hypoallergenic kitten with a soft little purr",
        type="kitten",
        hypoallergenic=True,
        shy=False,
        tags={"animal", "hypoallergenic", "friendship"},
    ),
    "dog": Pet(
        id="dog",
        label="dog",
        phrase="a playful hypoallergenic dog with bright eyes",
        type="dog",
        hypoallergenic=True,
        shy=False,
        tags={"animal", "hypoallergenic", "friendship", "bravery"},
    ),
}

ITEMS = {
    "blanket": ComfortItem(
        id="blanket",
        label="soft blanket",
        phrase="a soft blanket for a slow first hello",
        helps={"calm", "close"},
        tags={"comfort", "gentle"},
    ),
    "brush": ComfortItem(
        id="brush",
        label="little brush",
        phrase="a little brush for gentle grooming",
        helps={"calm", "trust"},
        tags={"comfort", "bravery"},
    ),
    "treats": ComfortItem(
        id="treats",
        label="small treats",
        phrase="small treats for a friendly welcome",
        helps={"trust", "close"},
        tags={"comfort", "friendship"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Zoe", "Ava", "Lily", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Noah", "Eli", "Max", "Theo"]
TRAITS = ["gentle", "curious", "shy", "brave", "kind", "careful"]


@dataclass
class StoryParams:
    place: str
    pet: str
    item: str
    name: str
    gender: str
    parent: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pet_id, pet in PETS.items():
            if "visit" not in setting.affords and place != "home":
                continue
            for item_id in ITEMS:
                if pet.hypoallergenic:
                    combos.append((place, pet_id, item_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming story world: a child, a hypoallergenic pet, and a brave first hello."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "pet", None) and getattr(args, "pet", None) not in PETS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "pet", None) and not _safe_lookup(PETS, getattr(args, "pet", None)).hypoallergenic:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "pet", None) is None or c[1] == getattr(args, "pet", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, pet_id, item_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, pet=pet_id, item=item_id, name=name,
                       gender=gender, parent=parent, trait=trait)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PETS.items():
        lines.append(asp.fact("pet", pid))
        if p.hypoallergenic:
            lines.append(asp.fact("hypoallergenic", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("pet_tag", pid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for t in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, t))
    for sid, s in SETTINGS.items():
        for pid in sorted(PETS):
            if sid == "home" or "visit" in s.affords:
                lines.append(asp.fact("can_place", sid, pid))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(S,P,I) :- can_place(S,P), hypoallergenic(P), item(I).
valid_story(S,P,I) :- compatible(S,P,I).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


def _do_visit(world: World, child: Entity, pet: Entity, item: Entity, narrate: bool = True) -> None:
    child.memes["bravery"] += 1
    if pet.hypoallergenic:
        child.meters["sneeze"] = max(0.0, child.meters.get("sneeze", 0.0) - 1.0)
    child.meters["close"] = child.meters.get("close", 0.0) + 1.0
    pet.meters["comfort"] = pet.meters.get("comfort", 0.0) + 1.0
    if narrate:
        world.say(f"{child.id} took a careful breath and stepped closer.")
        world.say(f"{pet.phrase.capitalize()} waited with a soft, patient look.")


def tell(setting: Setting, pet_cfg: Pet, item_cfg: ComfortItem,
         hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    pet = world.add(Entity(id=pet_cfg.id, kind="character", type=pet_cfg.type, label=pet_cfg.label,
                           phrase=pet_cfg.phrase, tags=set(pet_cfg.tags)))
    item = world.add(Entity(id=item_cfg.id, type="item", label=item_cfg.label, phrase=item_cfg.phrase,
                            tags=set(item_cfg.tags)))
    child.meters["worry"] = 1.0
    child.memes["love"] = 1.0
    parent.memes["care"] = 1.0
    pet.memes["shy"] = 1.0 if pet_cfg.shy else 0.0

    world.say(f"{child.id} was a {trait} {hero_type} who loved quiet, kind things.")
    world.say(f"One day, {child.id} and {child.pronoun('possessive')} {parent.label_word if hasattr(parent, 'label_word') else 'parent'} went to {setting.place}.")
    world.say(f"They had brought {item.phrase}, because meeting {pet.label} felt important and a little big.")

    world.para()
    child.memes["desire"] = 1.0
    world.say(f"{child.id} wanted to meet {pet.label}, but {child.pronoun('possessive')} heart thumped fast.")
    if pet_cfg.hypoallergenic:
        world.say(f"{parent.pronoun('subject').capitalize()} reminded {child.id} that {pet.label} was hypoallergenic.")
    world.say(f'"You can be brave one tiny step at a time," {parent.pronoun("subject")} said.')

    world.para()
    world.say(f"{child.id} held {item.label} out like a friendly bridge.")
    _do_visit(world, child, pet, item)
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    pet.memes["trust"] = pet.memes.get("trust", 0.0) + 1.0
    world.say(f"{pet.id} sniffed the {item.label} and came closer on soft paws.")
    world.say(f"{child.id} smiled, and the little room felt warmer right away.")

    world.para()
    world.say(f"By the end, {child.id} was laughing gently beside {pet.label}.")
    world.say(f"{pet.phrase.capitalize()} was no longer a worry at all; it was a new friend.")
    world.facts.update(child=child, parent=parent, pet=pet, item=item, setting=setting, trait=trait)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    pet = f["pet"]
    item = f["item"]
    return [
        f'Write a heartwarming story about {child.id} meeting a hypoallergenic {pet.type} with {item.label}.',
        f"Tell a gentle bravery story where {child.id} feels nervous, then finds courage to befriend {pet.label}.",
        f'Write a short story for a young child that includes the word "hypoallergenic" and ends in a warm friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    pet = f["pet"]
    item = f["item"]
    parent = f["parent"]
    return [
        QAItem(
            question=f"Who was brave enough to meet {pet.label}?",
            answer=f"{child.id} was brave enough to meet {pet.label}.",
        ),
        QAItem(
            question=f"Why did {child.id} feel safer about {pet.label}?",
            answer=f"{pet.label} was hypoallergenic, so the meeting felt safer and kinder.",
        ),
        QAItem(
            question=f"What did {child.id} hold out to help the first hello?",
            answer=f"{child.id} held out {item.phrase} to make the first hello gentle.",
        ),
        QAItem(
            question=f"How did {child.id} feel at the end?",
            answer=f"{child.id} felt happy and warm inside, because {pet.label} became a new friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hypoallergenic mean?",
            answer="Hypoallergenic means something is less likely to bother people with allergies.",
        ),
        QAItem(
            question="Why can a gentle first hello help a shy animal?",
            answer="A gentle first hello gives a shy animal time to feel safe and trust the new person.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is doing something a little scary when you know it matters.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other and spend kind time together.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"  {e.id:8} ({e.type:7}) meters={{{', '.join(f'{k}: {v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}: {v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(place="home", pet="bunny", item="blanket", name="Mia", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="garden", pet="kitten", item="treats", name="Leo", gender="boy", parent="father", trait="brave"),
    StoryParams(place="vet", pet="dog", item="brush", name="Nora", gender="girl", parent="mother", trait="curious"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PETS, params.pet), _safe_lookup(ITEMS, params.item),
                 params.name, params.gender, params.parent, params.trait)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.name}: {p.pet} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
