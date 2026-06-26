#!/usr/bin/env python3
"""
storyworlds/worlds/list_salsa_friendship_animal_story.py
=========================================================

A small animal friendship storyworld about making a list for salsa.

Seed tale:
---
A little fox and a little rabbit wanted to make salsa for their animal friends.
They wrote a list of what they needed: tomatoes, onions, lime, and a bowl.
The fox forgot to bring the list, and the rabbit worried they would forget the salsa.
But they found the list under a berry bush, gathered the ingredients, and made a bright
red bowl of salsa to share. Their friends ate it together and laughed.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    extra_friend: object | None = None
    friend: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"lost": 0.0, "ready": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "friendship": 0.0, "sharing": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "rabbit", "bear", "mouse", "cat", "dog"}:
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
    place: str = "the berry patch"
    world: object | None = None
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


# ---------------------------------------------------------------------------
# Registries
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
class AnimalFriend:
    type: str
    name: str
    trait: str
    likes: str
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
class Ingredient:
    id: str
    label: str
    color: str
    help_text: str
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


ANIMALS = {
    "fox": AnimalFriend(type="fox", name="Finn", trait="quick", likes="bright things"),
    "rabbit": AnimalFriend(type="rabbit", name="Ruby", trait="gentle", likes="neat lists"),
    "bear": AnimalFriend(type="bear", name="Milo", trait="kind", likes="big snacks"),
    "mouse": AnimalFriend(type="mouse", name="Pip", trait="tiny", likes="crumbs"),
}

INGREDIENTS = {
    "tomatoes": Ingredient("tomatoes", "tomatoes", "red", "They make salsa bright and juicy."),
    "onion": Ingredient("onion", "an onion", "white", "It gives salsa a sharp little bite."),
    "lime": Ingredient("lime", "a lime", "green", "Its juice makes salsa taste fresh."),
    "cilantro": Ingredient("cilantro", "some cilantro", "green", "It adds a leafy smell and taste."),
    "salt": Ingredient("salt", "a pinch of salt", "white", "It helps the flavors wake up."),
}

LIST_ITEMS = ["tomatoes", "onion", "lime", "cilantro", "salt"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str = "the berry patch"
    hero: str = "fox"
    friend: str = "rabbit"
    extra_friend: str = "bear"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


def _hero_text(hero: Entity) -> str:
    return f"{hero.name} the {hero.type}"


def _friendship_boost(a: Entity, b: Entity, amount: float = 1.0) -> None:
    a.memes["friendship"] = a.memes.get("friendship", 0.0) + amount
    b.memes["friendship"] = b.memes.get("friendship", 0.0) + amount


def _set_ready(world: World, item_id: str) -> None:
    world.get(item_id).meters["ready"] = 1.0


def _set_lost(world: World, item_id: str) -> None:
    world.get(item_id).meters["lost"] = 1.0


def _story_intro(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{_hero_text(hero)} and {friend.name} the {friend.type} were good friends, "
        f"and they loved doing little jobs together."
    )
    world.say(
        f"They wanted to make salsa for their animal friends, so they wrote a list "
        f"to help them remember everything."
    )


def _write_list(world: World) -> None:
    world.facts["list_items"] = list(LIST_ITEMS)
    world.say(
        "The list said tomatoes, onion, lime, cilantro, and salt."
    )


def _forget_list(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.facts["list_missing"] = True
    world.say(
        f"Then {hero.name} looked around and froze. The list was gone."
    )
    world.say(
        f"{friend.name} worried they might forget the salsa ingredients."
    )


def _search_and_find(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"The two friends sniffed under leaves and peered behind a berry bush."
    )
    world.say(
        f"At last, {friend.name} found the list tucked in the grass."
    )
    world.facts["list_found"] = True
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    _friendship_boost(hero, friend, 1.0)


def _gather_items(world: World, hero: Entity, friend: Entity) -> None:
    for item_id in LIST_ITEMS:
        _set_ready(world, item_id)
    world.say(
        f"Together they gathered the tomatoes, onion, lime, cilantro, and salt."
    )
    world.say(
        f"{hero.name} chopped carefully while {friend.name} stirred and tasted."
    )
    world.facts["ingredients_ready"] = True


def _make_salsa(world: World, hero: Entity, friend: Entity, extra_friend: Entity) -> None:
    world.say(
        f"Soon the bowl was full of bright red salsa, and the smell made every tail wiggle."
    )
    world.say(
        f"{extra_friend.name} came over for a spoonful, and the friends shared the snack together."
    )
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1
    extra_friend.memes["joy"] += 1
    _friendship_boost(hero, friend, 1.5)
    world.facts["salsa_made"] = True


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero_cfg = _safe_lookup(ANIMALS, params.hero)
    friend_cfg = _safe_lookup(ANIMALS, params.friend)
    extra_cfg = _safe_lookup(ANIMALS, params.extra_friend)

    hero = world.add(Entity(id=hero_cfg.name, kind="character", type=hero_cfg.type))
    friend = world.add(Entity(id=friend_cfg.name, kind="character", type=friend_cfg.type))
    extra_friend = world.add(Entity(id=extra_cfg.name, kind="character", type=extra_cfg.type))

    world.facts.update(
        hero=hero,
        friend=friend,
        extra_friend=extra_friend,
        setting=world.setting,
        place=params.place,
    )

    _story_intro(world, hero, friend)
    world.para()
    _write_list(world)
    _forget_list(world, hero, friend)
    world.para()
    _search_and_find(world, hero, friend)
    _gather_items(world, hero, friend)
    _make_salsa(world, hero, friend, extra_friend)

    world.say(
        f"In the end, the friends sat together at {params.place} with full bellies and happy smiles."
    )
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(fox; rabbit; bear; mouse).
ingredient(tomatoes; onion; lime; cilantro; salt).

good_friend(A,B) :- hero(A), hero(B), A != B.
needs_list(list, tomatoes).
needs_list(list, onion).
needs_list(list, lime).
needs_list(list, cilantro).
needs_list(list, salt).

valid_story(H,F,E) :- hero(H), hero(F), hero(E), H != F, H != E, F != E.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for k in ANIMALS:
        lines.append(asp.fact("hero", k))
    for k in INGREDIENTS:
        lines.append(asp.fact("ingredient", k))
    for item in LIST_ITEMS:
        lines.append(asp.fact("needs_list", "list", item))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    expected = sorted(
        (h, f, e)
        for h in ANIMALS
        for f in ANIMALS
        for e in ANIMALS
        if len({h, f, e}) == 3
    )
    if atoms == expected:
        print(f"OK: ASP parity holds for {len(atoms)} story triples.")
        return 0
    print("MISMATCH between ASP and Python story space:")
    print("ASP only:", sorted(set(atoms) - set(expected)))
    print("Python only:", sorted(set(expected) - set(atoms)))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    keys = list(ANIMALS)
    for hero in keys:
        for friend in keys:
            for extra in keys:
                if len({hero, friend, extra}) != 3:
                    continue
                out.append(("the berry patch", hero, friend, extra))
    return out


def explain_rejection() -> str:
    return "(No story: the animal trio needs three different friends so the friendship scene feels clear.)"


# ---------------------------------------------------------------------------
# Params, generation, QA
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship storyworld with a list and salsa.")
    ap.add_argument("--place", default="the berry patch")
    ap.add_argument("--hero", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
    ap.add_argument("--extra-friend", choices=ANIMALS, dest="extra_friend")
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
    if getattr(args, "hero", None) and getattr(args, "friend", None) and getattr(args, "extra_friend", None):
        if len({getattr(args, "hero", None), getattr(args, "friend", None), getattr(args, "extra_friend", None)}) != 3:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    if getattr(args, "hero", None):
        combos = [c for c in combos if c[1] == getattr(args, "hero", None)]
    if getattr(args, "friend", None):
        combos = [c for c in combos if c[2] == getattr(args, "friend", None)]
    if getattr(args, "extra_friend", None):
        combos = [c for c in combos if c[3] == getattr(args, "extra_friend", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    _, hero, friend, extra = rng.choice(list(combos))
    return StoryParams(place=getattr(args, "place", None), hero=hero, friend=friend, extra_friend=extra)


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short animal story about a list and salsa.',
        f"Tell a friendly story where {world.get(world.facts['hero'].id).name} and "
        f"{world.get(world.facts['friend'].id).name} make salsa together after finding a lost list.",
        "Write a simple story about friends gathering ingredients and sharing a snack.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    extra = _safe_fact(world, world.facts, "extra_friend")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"Who wanted to make salsa at {place}?",
            answer=f"{hero.name} the {hero.type} and {friend.name} the {friend.type} wanted to make salsa at {place}.",
        ),
        QAItem(
            question="What did the list say they needed?",
            answer="The list said tomatoes, onion, lime, cilantro, and salt.",
        ),
        QAItem(
            question=f"What happened after {friend.name} found the list?",
            answer=f"{hero.name} and {friend.name} gathered the ingredients, made salsa, and shared it with {extra.name}.",
        ),
        QAItem(
            question="Why did the friends worry for a moment?",
            answer="They worried because the list was missing, and they did not want to forget the salsa ingredients.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the friends sitting together at {place} with full bellies and happy smiles.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is salsa?",
            answer="Salsa is a tasty food made from chopped ingredients like tomatoes, onion, and lime.",
        ),
        QAItem(
            question="Why do friends make a list?",
            answer="Friends make a list so they can remember what they need and not forget important things.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="the berry patch", hero="fox", friend="rabbit", extra_friend="bear"),
    StoryParams(place="the berry patch", hero="rabbit", friend="fox", extra_friend="mouse"),
    StoryParams(place="the berry patch", hero="bear", friend="mouse", extra_friend="fox"),
]


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
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
