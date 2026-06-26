#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100/glee_cracker_dialogue_cautionary_twist_bedtime_story.py
================================================================================================

A tiny bedtime-story world about a child, a cracker, a gentle caution, and a
small twist that turns worry into glee.

Premise:
- A sleepy child wants to share a cracker at bedtime.
- The parent warns that a crumbly snack near a sleeping pet could wake it.
- Dialogue, caution, and a twist resolve the tension.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
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
    worn_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    pet: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str = "the bedroom"
    bedtime: bool = True
    quiet: bool = True
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
class Snack:
    label: str
    phrase: str
    crumbly: bool = True
    noisy: bool = True
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
class Caution:
    warning: str
    risk: str
    safer_choice: str
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
class Twist:
    reveal: str
    helper: str
    twist: object | None = None
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_crumbs(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    snack = world.get("snack")
    pet = world.get("pet")
    if child.meters.get("crumbs", 0) < THRESHOLD:
        return out
    sig = ("crumbs",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if pet.location == world.setting.place and pet.memes.get("sleepy", 0) >= THRESHOLD:
        pet.memes["startled"] = pet.memes.get("startled", 0) + 1
        child.memes["worry"] = child.memes.get("worry", 0) + 1
        out.append(f"A few crumbs fell, and the sleeping {pet.label} twitched its nose.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    pet = world.get("pet")
    child = world.get("child")
    if pet.memes.get("startled", 0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pet.memes["sleepy"] = pet.memes.get("sleepy", 0) + 1
    out.append(f"The room stayed soft and still, so the {pet.label} settled again.")
    return out


CAUSAL_RULES = [
    _r_crumbs,
    _r_calm,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def story_risk(snack: Snack) -> bool:
    return snack.crumbly and snack.noisy


def best_caution(snack: Snack, pet: Entity) -> Caution:
    return Caution(
        warning=f"Be gentle with that {snack.label}",
        risk=f"crumbs might wake the {pet.label}",
        safer_choice=f"try a softer snack or break it very slowly",
    )


def predict(world: World, child: Entity) -> dict:
    sim = world.copy()
    sim.get("child").meters["crumbs"] = 1
    propagate(sim, narrate=False)
    pet = sim.get("pet")
    return {
        "startled": pet.memes.get("startled", 0) >= THRESHOLD,
    }


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    pet: str
    snack: str
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", bedtime=True, quiet=True),
    "nursery": Setting(place="the nursery", bedtime=True, quiet=True),
}

SNACKS = {
    "cracker": Snack(label="cracker", phrase="a little buttery cracker", crumbly=True, noisy=True),
    "ricecake": Snack(label="rice cake", phrase="a plain rice cake", crumbly=True, noisy=False),
}

PETS = {
    "mouse": ("mouse", "a tiny mouse"),
    "kitten": ("kitten", "a sleepy kitten"),
}

NAMES = {
    "girl": ["Mia", "Luna", "Nora", "Ivy"],
    "boy": ["Noah", "Finn", "Eli", "Theo"],
}

TRAITS = ["gentle", "curious", "brave", "soft-spoken"]


def intro(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.type} with a pocket full of glee and a sleepy heart.")


def setup(world: World, child: Entity, parent: Entity, snack: Entity, pet: Entity) -> None:
    world.say(f"At bedtime, {child.id} sat near {world.setting.place} with {parent.label} beside {child.pronoun('object')}.")
    world.say(f"{child.id} loved {snack.phrase}, and {pet.label} was curled up nearby.")


def dialogue_caution(world: World, parent: Entity, child: Entity, snack: Entity, pet: Entity, caution: Caution) -> None:
    world.say(f'"{caution.warning}," {parent.label} said.')
    world.say(f'"{caution.risk}," {parent.label} whispered. "{caution.safer_choice}."')
    child.memes["want"] = child.memes.get("want", 0) + 1


def attempt(world: World, child: Entity, snack: Entity) -> None:
    child.meters["crumbs"] = child.meters.get("crumbs", 0) + 1
    child.memes["glee"] = child.memes.get("glee", 0) + 1
    world.say(f"{child.id} tried to nibble {snack.it()} very carefully, hoping to keep the night calm.")


def twist_reveal(world: World, pet: Entity, twist: Twist) -> None:
    world.say(f"Then came the twist: {twist.reveal}.")
    world.say(f"It turned out {twist.helper} was the one who wanted the cracker all along.")


def resolution(world: World, child: Entity, parent: Entity, snack: Entity, pet: Entity) -> None:
    child.memes["glee"] = child.memes.get("glee", 0) + 1
    child.memes["worry"] = 0
    world.say(f"{parent.label} helped {child.id} break the cracker in two tiny, quiet bites.")
    world.say(f"The crumbs stayed on the plate, and the {pet.label} kept breathing slow and dreamy.")
    world.say(f"{child.id} smiled in the dark, warm with glee, while the bedtime room stayed gentle and still.")


def tell(params: StoryParams) -> World:
    setting = random.choice(list(SETTINGS.values()))
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        memes={"glee": 1.0},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent,
        label="Mom" if params.parent == "mother" else "Dad",
    ))
    snack_cfg = _safe_lookup(SNACKS, params.snack)
    snack = world.add(Entity(id="snack", type="snack", label=snack_cfg.label, phrase=snack_cfg.phrase))
    pet_kind, pet_phrase = _safe_lookup(PETS, params.pet)
    pet = world.add(Entity(id="pet", kind="character", type=pet_kind, label=pet_kind, phrase=pet_phrase, memes={"sleepy": 1.0}))
    twist = Twist(
        reveal=f"the rustle was not danger, just the {pet.label} waking for a snack",
        helper=f"the {pet.label}",
    )

    intro(world, child)
    setup(world, child, parent, snack, pet)
    world.para()
    caution = best_caution(snack_cfg, pet)
    dialogue_caution(world, parent, child, snack, pet, caution)
    attempt(world, child, snack)
    propagate(world, narrate=True)

    world.para()
    twist_reveal(world, pet, twist)
    resolution(world, child, parent, snack, pet)

    world.facts.update(
        child=child,
        parent=parent,
        snack=snack,
        pet=pet,
        caution=caution,
        twist=twist,
        risk=story_risk(snack_cfg),
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    snack = _safe_fact(world, f, "snack")
    pet = _safe_fact(world, f, "pet")
    return [
        f'Write a bedtime story about {child.id}, a {snack.label}, and a sleepy {pet.label}.',
        f'Write a gentle story with dialogue where a parent warns a child not to make crumbs near a sleeping {pet.label}.',
        f'Write a bedtime story with a cautionary moment and a twist that ends in glee.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    parent = _safe_fact(world, f, "parent")
    snack = _safe_fact(world, f, "snack")
    pet = _safe_fact(world, f, "pet")
    return [
        QAItem(
            question=f"Why did {parent.label} warn {child.id} about the {snack.label}?",
            answer=f"{parent.label} warned {child.id} because the {snack.label} could make crumbs, and the crumbs might wake the {pet.label}.",
        ),
        QAItem(
            question=f"What did {child.id} do after hearing the warning?",
            answer=f"{child.id} tried to nibble the {snack.label} very carefully so the room could stay quiet.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the rustle was not danger at all; it was the {pet.label} waking for a snack.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the snack broken into tiny quiet bites, the {pet.label} settled down again, and {child.id} feeling glee at bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are crumbs?",
            answer="Crumbs are tiny broken bits of food that can fall onto a plate, blanket, or floor.",
        ),
        QAItem(
            question="Why should people be gentle near a sleeping pet?",
            answer="Being gentle keeps the pet from getting startled, so it can rest peacefully.",
        ),
        QAItem(
            question="What does glee mean?",
            answer="Glee means bright, happy delight.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Mia", gender="girl", parent="mother", pet="mouse", snack="cracker"),
    StoryParams(name="Noah", gender="boy", parent="father", pet="kitten", snack="cracker"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with glee, cracker, dialogue, caution, and a twist.")
    ap.add_argument("--name", choices=[n for names in NAMES.values() for n in names])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--pet", choices=PETS)
    ap.add_argument("--snack", choices=SNACKS)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    pet = getattr(args, "pet", None) or rng.choice(list(PETS))
    snack = getattr(args, "snack", None) or "cracker"
    if snack not in SNACKS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if snack == "cracker" and pet == "mouse" and getattr(args, "parent", None) is None:
        pass
    return StoryParams(name=name, gender=gender, parent=parent, pet=pet, snack=snack)


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


ASP_RULES = r"""
child_wants_snack(C,S) :- child(C), snack(S).
risk(C,S,P) :- child_wants_snack(C,S), pet(P), crumbly(S), noisy(S).
warns(P,C,S) :- risk(C,S,P).
twist(P) :- pet(P), sleepy(P).
happy_end(C) :- child(C).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for gender, names in NAMES.items():
        for n in names:
            lines.append(asp.fact("child", n))
            lines.append(asp.fact("gender", n, gender))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        if snack.crumbly:
            lines.append(asp.fact("crumbly", sid))
        if snack.noisy:
            lines.append(asp.fact("noisy", sid))
    for pid in PETS:
        lines.append(asp.fact("pet", pid))
        lines.append(asp.fact("sleepy", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show risk/3.\n#show warns/3.\n#show twist/1.\n")
    model = asp.one_model(program)
    atoms = set((a[0], a[1], a[2]) for a in asp.atoms(model, "risk"))
    py = set()
    for gender, names in NAMES.items():
        for n in names:
            for pid in PETS:
                s = SNACKS["cracker"]
                if s.crumbly and s.noisy:
                    py.add((n, "cracker", pid))
    if atoms == py:
        print("OK: ASP parity matches Python reasonableness.")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show risk/3.\n#show warns/3.\n#show twist/1.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.snack} with {p.pet}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
