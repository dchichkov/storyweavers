#!/usr/bin/env python3
"""
storyworlds/worlds/expose_margarita_misunderstanding_fairy_tale.py
===================================================================

A small fairy-tale story world about Margarita, an expose/reveal event, and a
misunderstanding that resolves into kindness.

Seed tale sketch:
---
Once upon a time, Margarita lived in a quiet village beside a willow wood.
She loved lantern-light, secret paths, and the old stories people told about
the moon. One evening she found a silver ribbon hiding a small fairy door.
When she pulled the ribbon aside, the villagers thought she had exposed a
secret on purpose. But Margarita only wanted to help a trapped little fairy.
The misunderstanding cleared when the fairy came out and thanked her.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden_by: Optional[str] = None
    revealed: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    observer: object | None = None
    secret_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        feminine = {"girl", "woman", "mother", "queen", "fairy"}
        masculine = {"boy", "man", "father", "king", "sprite"}
        if self.type in feminine:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in masculine:
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
class Place:
    name: str
    indoor: bool = False
    can_hide: set[str] = field(default_factory=set)
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
class Secret:
    label: str
    phrase: str
    reveal_verb: str
    hidden_in: str
    glow: str
    keyword: str = "margarita"
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
class Witness:
    id: str
    label: str
    role: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.understanding: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.understanding = self.understanding
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    secret: str
    witness: str
    name: str = "Margarita"
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


PLACES = {
    "village_green": Place(name="the village green", can_hide={"curtain", "ribbon", "bush"}),
    "willow_wood": Place(name="the willow wood", can_hide={"leaf", "ribbon", "moss"}),
    "moon_garden": Place(name="the moon garden", can_hide={"veil", "ribbon", "flower"}),
}

SECRETS = {
    "fairy_door": Secret(
        label="fairy door",
        phrase="a tiny door of silver wood",
        reveal_verb="expose",
        hidden_in="ribbon",
        glow="silver",
        keyword="margarita",
    ),
    "lost_lantern": Secret(
        label="lantern",
        phrase="a little lantern with a warm gold heart",
        reveal_verb="expose",
        hidden_in="curtain",
        glow="gold",
        keyword="margarita",
    ),
    "sleeping_fairy": Secret(
        label="sleeping fairy",
        phrase="a small fairy curled in a mossy cradle",
        reveal_verb="reveal",
        hidden_in="moss",
        glow="blue",
        keyword="margarita",
    ),
}

WITNESSES = {
    "elder": Witness(id="elder", label="the elder", role="elder"),
    "queen": Witness(id="queen", label="the queen", role="queen"),
    "miller": Witness(id="miller", label="the miller", role="miller"),
}

NAMES = ["Margarita", "Anya", "Lina", "Iris", "Nora", "Eliza"]
TRAITS = ["gentle", "curious", "brave", "kind"]


ASP_RULES = r"""
place(village_green). place(willow_wood). place(moon_garden).
can_hide(village_green,curtain). can_hide(village_green,ribbon). can_hide(village_green,bush).
can_hide(willow_wood,leaf). can_hide(willow_wood,ribbon). can_hide(willow_wood,moss).
can_hide(moon_garden,veil). can_hide(moon_garden,ribbon). can_hide(moon_garden,flower).

secret(fairy_door). secret(lost_lantern). secret(sleeping_fairy).
hidden_in(fairy_door,ribbon). hidden_in(lost_lantern,curtain). hidden_in(sleeping_fairy,moss).

witness(elder). witness(queen). witness(miller).

compatible(P,S) :- can_hide(P,H), hidden_in(S,H).
misunderstanding(P,S,W) :- compatible(P,S), witness(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for h in sorted(p.can_hide):
            lines.append(asp.fact("can_hide", pid, h))
    for sid, s in SECRETS.items():
        lines.append(asp.fact("secret", sid))
        lines.append(asp.fact("hidden_in", sid, s.hidden_in))
    for wid in WITNESSES:
        lines.append(asp.fact("witness", wid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_valid_misunderstandings() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show misunderstanding/3."))
    return sorted(set(asp.atoms(model, "misunderstanding")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, p in PLACES.items():
        for secret, s in SECRETS.items():
            if s.hidden_in in p.can_hide:
                combos.append((place, secret))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale world about Margarita, an expose, and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--secret", choices=SECRETS)
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "secret", None):
        if (getattr(args, "place", None), getattr(args, "secret", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "secret", None) is None or c[1] == getattr(args, "secret", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, secret = rng.choice(list(combos))
    witness = getattr(args, "witness", None) or rng.choice(sorted(WITNESSES))
    name = getattr(args, "name", None) or "Margarita"
    return StoryParams(place=place, secret=secret, witness=witness, name=name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale with the word "{f["secret"].keyword}" and the action "expose".',
        f"Tell a gentle story about {f['hero'].id} in {f['place'].name} where a misunderstanding is cleared up.",
        f"Write a child-friendly tale where {f['hero'].id} finds a hidden {f['secret'].label} and a witness thinks the wrong thing at first.",
    ]


def maybe_misunderstand(world: World, hero: Entity, witness: Entity, secret: Secret) -> None:
    world.facts["misunderstanding"] = True
    hero.memes["worry"] += 1
    witness.memes["alarm"] += 1
    world.say(f"{witness.label} gasped, because it looked as if {hero.id} meant to expose a secret to the whole lane.")


def resolve_misunderstanding(world: World, hero: Entity, witness: Entity, secret: Secret) -> None:
    hero.memes["kindness"] += 1
    witness.memes["relief"] += 1
    world.understanding = 1.0
    secret_entity = world.get(secret.label)
    secret_entity.revealed = True
    world.say(
        f"But {hero.id} only lifted the ribbon so the hidden {secret.label} could see the light."
    )
    world.say(
        f"When the {secret.label} blinked awake and thanked {hero.id}, {witness.label} softened at once."
    )
    world.say(
        f"So the village learned that sometimes a thing that looks like expose is really a kind reveal."
    )


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    secret = _safe_lookup(SECRETS, params.secret)
    witness = _safe_lookup(WITNESSES, params.witness)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="girl", traits=["little", "gentle", "curious"]))
    observer = world.add(Entity(id=witness.id, kind="character", type="woman" if witness.role == "queen" else "man", label=witness.label))
    secret_ent = world.add(Entity(id=secret.label, kind="thing", type=secret.label, label=secret.label, phrase=secret.phrase, hidden_by=secret.hidden_in))

    world.say(f"Once upon a time, {hero.id} lived near {place.name}.")
    world.say(f"{hero.id} loved old paths, soft songs, and the bright word {secret.keyword}.")
    world.say(f"One evening, {hero.id} found {secret.phrase}, tucked away behind a {secret.hidden_in}.")
    world.para()
    world.say(f"{hero.id} wanted to {secret.reveal_verb} it gently, just enough for the moon to notice.")
    maybe_misunderstand(world, hero, observer, secret)
    world.para()
    resolve_misunderstanding(world, hero, observer, secret)

    world.facts.update(hero=hero, witness=observer, secret=secret, place=place, secret_entity=secret_ent)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    witness = _safe_fact(world, f, "witness")
    secret = _safe_fact(world, f, "secret")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, who lives near {place.name} and acts with a gentle heart.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the hidden {secret.label}?",
            answer=f"{hero.id} wanted to {secret.reveal_verb} it gently, so the hidden {secret.label} could see the light.",
        ),
        QAItem(
            question=f"Why did {witness.label} get upset at first?",
            answer=f"{witness.label} thought {hero.id} was exposing a secret to everyone, but that was a misunderstanding.",
        ),
        QAItem(
            question=f"What happened when the misunderstanding was cleared up?",
            answer=f"The hidden {secret.label} came into the open, thanked {hero.id}, and {witness.label} felt relieved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first and later learns what really meant to happen.",
        ),
        QAItem(
            question="What does it mean to expose something?",
            answer="To expose something means to uncover it so it can be seen.",
        ),
        QAItem(
            question="Why might a hidden door need to be uncovered carefully?",
            answer="A hidden door may be delicate, so uncovering it gently helps keep it safe.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.hidden_by:
            bits.append(f"hidden_by={e.hidden_by}")
        if e.revealed:
            bits.append("revealed=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  understanding={world.understanding}")
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
    StoryParams(place="village_green", secret="fairy_door", witness="elder", name="Margarita"),
    StoryParams(place="willow_wood", secret="sleeping_fairy", witness="miller", name="Margarita"),
    StoryParams(place="moon_garden", secret="lost_lantern", witness="queen", name="Margarita"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def asp_program_show(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program_show("#show misunderstanding/3."))
    return sorted(set(asp.atoms(model, "misunderstanding")))


def valid_story_combos() -> list[tuple[str, str]]:
    return valid_combos()


def asp_verify_gate() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program_show("#show misunderstanding/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, secret) combos:")
        for place, secret in triples:
            print(f"  {place:14} {secret}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.secret} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
