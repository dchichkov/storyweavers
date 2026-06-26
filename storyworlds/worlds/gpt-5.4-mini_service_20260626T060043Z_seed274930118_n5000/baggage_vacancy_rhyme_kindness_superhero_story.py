#!/usr/bin/env python3
"""
A small superhero story world about a team, a vacant spot, and the baggage that
nearly keeps a hero from joining. The turn comes from kindness and rhyme: a
friendly chant helps calm the worry, and a warm rescue proves the new hero can
fit the team.
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
# Core model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine", "mother"}
        male = {"boy", "man", "hero", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
class City:
    name: str
    place: str
    affordance: str
    atmosphere: str
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
class Hero:
    id: str
    type: str
    trait: str
    power: str
    cape: str
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
class Opportunity:
    id: str
    label: str
    vacancy_text: str
    sign: str
    task: str
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
class Baggage:
    id: str
    label: str
    phrase: str
    burden: str
    weight: str
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


class World:
    def __init__(self, city: City) -> None:
        self.city = city
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

        clone = World(self.city)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CITIES = {
    "downtown": City("downtown", "the downtown square", "rescue", "bright and busy"),
    "harbor": City("harbor", "the harbor bridge", "rescue", "windy and open"),
    "museum": City("museum", "the museum roof", "guard", "quiet and high"),
}

HEROES = {
    "Bolt": Hero("Bolt", "hero", "brave", "speed", "blue cape"),
    "Nova": Hero("Nova", "hero", "kind", "light", "silver cape"),
    "Comet": Hero("Comet", "hero", "cheerful", "flight", "red cape"),
}

OPPORTUNITIES = {
    "vacancy": Opportunity(
        "vacancy",
        "vacancy",
        "an open spot on the city rescue team",
        "A vacancy sign blinked on the tower",
        "join the rescue team",
    ),
    "watch": Opportunity(
        "watch",
        "watch",
        "a vacant watch post by the river",
        "A vacancy note hung by the gate",
        "keep watch over the river",
    ),
}

BAGGAGES = {
    "suitcase": Baggage(
        "suitcase",
        "baggage",
        "a heavy suitcase full of old worries",
        "worry",
        "heavy",
    ),
    "bundle": Baggage(
        "bundle",
        "baggage",
        "a messy bundle of baggage straps and papers",
        "doubt",
        "messy",
    ),
    "box": Baggage(
        "box",
        "baggage",
        "a dusty box of baggage from a long trip",
        "hesitation",
        "dusty",
    ),
}


@dataclass
class StoryParams:
    city: str
    hero: str
    opportunity: str
    baggage: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
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


def _hero_ent(world: World, hero: Hero) -> Entity:
    return world.add(Entity(id=hero.id, kind="character", type="hero"))


def _opportunity_ent(world: World, opp: Opportunity) -> Entity:
    return world.add(Entity(id=opp.id, type="opportunity", label=opp.label, phrase=opp.vacancy_text))


def _baggage_ent(world: World, bag: Baggage) -> Entity:
    return world.add(Entity(id=bag.id, type="baggage", label=bag.label, phrase=bag.phrase))


def _predicted_spill(world: World, hero: Entity, bag: Entity) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["nervous"] = 1
    sim.get(bag.id).meters["burden"] = 1
    return sim.get(bag.id).meters.get("burden", 0) >= 1


def tell(city: City, hero_cfg: Hero, opp_cfg: Opportunity, bag_cfg: Baggage) -> World:
    world = World(city)
    hero = _hero_ent(world, hero_cfg)
    opp = _opportunity_ent(world, opp_cfg)
    bag = _baggage_ent(world, bag_cfg)

    hero.memes["hope"] = 1
    hero.memes["kindness"] = 0
    bag.meters["burden"] = 1
    bag.meters["weight"] = 1

    world.say(
        f"{hero.id} was a {hero_cfg.trait} superhero with {hero_cfg.power} and {hero_cfg.cape}."
    )
    world.say(
        f"{hero.id} found {opp.phrase} at {city.place}, but {bag.label} sat by the door like a hard little cloud."
    )

    world.para()
    world.say(
        f"{opp.sign} for {opp.task}, and the city needed help right away."
    )
    world.say(
        f"{hero.id} wanted to go, but {hero.pronoun('possessive')} baggage felt too heavy to lift."
    )

    if _predicted_spill(world, hero, bag):
        hero.memes["doubt"] = 1
        world.say(
            f"{hero.id} worried there was no room for {hero.pronoun('object')} on the team."
        )

    world.para()
    hero.memes["kindness"] += 1
    hero.memes["joy"] = 1
    hero.memes["doubt"] = 0
    bag.meters["burden"] = 0
    world.say(
        f"Then {hero_cfg.power} slowed, and {hero.id} heard a kind rhyme from {opp.label}:"
    )
    world.say(
        f"\"One brave heart, one helping spark; kind words shine bright in the dark.\""
    )
    world.say(
        f"The rhyme made {hero.id} smile, and {hero.id} stepped forward anyway."
    )

    world.para()
    hero.memes["ready"] = 1
    world.say(
        f"{hero.id} used {hero_cfg.power} to reach the {opp.task} fast, and {hero.id} helped right where the vacancy was."
    )
    world.say(
        f"At the end, the team welcomed {hero.id}, the baggage felt light, and the vacant spot was filled at last."
    )

    world.facts.update(hero=hero, hero_cfg=hero_cfg, opp=opp, bag=bag, city=city)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero: Hero = _safe_fact(world, f, "hero_cfg")
    opp: Opportunity = _safe_fact(world, f, "opp")
    return [
        f'Write a short superhero story for a young child about {hero.id}, a {hero.trait} hero, and a {opp.label} with a vacancy.',
        f'Write a gentle story where a superhero worries about baggage but is helped by kindness and a rhyme.',
        f'Tell a simple story in which an open spot on a team is filled after someone remembers to be kind.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Hero = _safe_fact(world, f, "hero_cfg")
    opp: Opportunity = _safe_fact(world, f, "opp")
    bag: Baggage = _safe_fact(world, f, "bag")
    city: City = _safe_fact(world, f, "city")
    return [
        QAItem(
            question=f"Who was the superhero in the story at {city.place}?",
            answer=f"The superhero was {hero.id}, who had {hero.power} and a {hero.cape}.",
        ),
        QAItem(
            question=f"What problem made {hero.id} hesitate before going to {opp.task}?",
            answer=f"{hero.id} hesitated because the baggage felt heavy and seemed like too much to carry.",
        ),
        QAItem(
            question=f"What helped {hero.id} feel ready to step into the vacancy?",
            answer=f"A kind rhyme helped {hero.id} feel brave, and then {hero.id} went to fill the open spot.",
        ),
        QAItem(
            question=f"How did the story end for the vacant spot?",
            answer=f"The vacant spot was filled when {hero.id} joined the team and helped with the rescue task.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful toward someone else.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a line of words that sounds catchy because the endings sound alike.",
        ),
        QAItem(
            question="What is a vacancy?",
            answer="A vacancy is an open spot or empty place that needs someone to fill it.",
        ),
        QAItem(
            question="What is baggage?",
            answer="Baggage is luggage or packed things someone carries on a trip.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
hero(H) :- hero_name(H).
opportunity(O) :- opp_name(O).
baggage(B) :- bag_name(B).

vacancy_open(O) :- opportunity(O), vacancy(O).
kind_fix(H, O) :- hero(H), opportunity(O), kind(H).
story_valid(C, H, O, B) :- city(C), hero(H), opportunity(O), baggage(B),
                           vacancy_open(O), kind_fix(H, O).
#show story_valid/4.
#show vacancy_open/1.
#show kind_fix/2.
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CITIES:
        lines.append(asp.fact("city", cid))
    for hid, h in HEROES.items():
        lines.append(asp.fact("hero_name", hid))
        lines.append(asp.fact("kind", hid) if h.trait == "kind" else asp.fact("brave", hid))
    for oid, o in OPPORTUNITIES.items():
        lines.append(asp.fact("opp_name", oid))
        lines.append(asp.fact("vacancy", oid))
    for bid in BAGGAGES:
        lines.append(asp.fact("bag_name", bid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show story_valid/4."))
    asp_set = set(asp.atoms(model, "story_valid"))
    py_set = set()
    for cid in CITIES:
        for hid, h in HEROES.items():
            for oid in OPPORTUNITIES:
                for bid in BAGGAGES:
                    if h.trait == "kind":
                        py_set.add((cid, hid, oid, bid))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} valid story tuples).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with baggage, vacancy, rhyme, and kindness.")
    ap.add_argument("--city", choices=CITIES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--opportunity", choices=OPPORTUNITIES)
    ap.add_argument("--baggage", choices=BAGGAGES)
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
    city = getattr(args, "city", None) or rng.choice(list(CITIES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    opportunity = getattr(args, "opportunity", None) or rng.choice(list(OPPORTUNITIES))
    baggage = getattr(args, "baggage", None) or rng.choice(list(BAGGAGES))
    if getattr(args, "hero", None) and _safe_lookup(HEROES, getattr(args, "hero", None)).trait != "kind":
        # We keep the main storyworld centered on kindness.
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if hero not in HEROES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if opportunity not in OPPORTUNITIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(city=city, hero=hero, opportunity=opportunity, baggage=baggage)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(CITIES, params.city), _safe_lookup(HEROES, params.hero), _safe_lookup(OPPORTUNITIES, params.opportunity), _safe_lookup(BAGGAGES, params.baggage))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
    StoryParams(city="downtown", hero="Nova", opportunity="vacancy", baggage="suitcase"),
    StoryParams(city="harbor", hero="Bolt", opportunity="watch", baggage="box"),
    StoryParams(city="museum", hero="Nova", opportunity="vacancy", baggage="bundle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show story_valid/4."))
        tuples = sorted(set(asp.atoms(model, "story_valid")))
        for t in tuples:
            print(t)
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
