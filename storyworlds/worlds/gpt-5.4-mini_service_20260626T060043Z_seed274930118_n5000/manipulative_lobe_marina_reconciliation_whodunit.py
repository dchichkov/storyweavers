#!/usr/bin/env python3
"""
A small whodunit-style storyworld set at a marina, with a mystery, clues,
suspects, and a reconciliation ending.

The seed prompt emphasized:
- manipulative
- lobe
- reconciliation
- whodunit
- marina

This world turns those into a child-friendly mystery: someone plays a tricky,
manipulative prank at the marina, clues point to the wrong suspect, and the
ending reveals the real culprit and a sincere reconciliation.
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

METER_THRESHOLD = 1.0



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
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    lobe: object | None = None
    manipulative: object | None = None
    secret: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def ref(self) -> str:
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
class Dock:
    name: str = "the marina"
    places: list[str] = field(default_factory=lambda: ["the dock", "the bait shop", "the floating pier", "the office"])
    clue_spots: list[str] = field(default_factory=lambda: ["the dock", "the floating pier", "the office"])
    world: object | None = None
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
class Suspect:
    id: str
    label: str
    type: str
    role: str
    alibi: str
    clue: str
    innocent_reason: str
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
    name: str
    gender: str
    helper: str
    suspect: str
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
    def __init__(self, dock: Dock) -> None:
        self.dock = dock
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()

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


HELPERS = {
    "finn": Suspect("Finn", "Finn the dockhand", "boy", "dockhand",
                    "he was tying ropes near the fuel barrel",
                    "a wet rope loop was left on the pier",
                    "he only tied knots, and knots do not hide keys"),
    "mira": Suspect("Mira", "Mira the fish seller", "girl", "fish seller",
                    "she was counting silver fish in the bait shop",
                    "fish scales sparkled on the counter",
                    "she stayed inside with her crate and never left"),
    "otis": Suspect("Otis", "Otis the boat painter", "boy", "painter",
                    "he was dipping a brush in blue paint",
                    "a blue paint drop was on the office step",
                    "the paint was old and dry, from yesterday's work"),
}

SUSPECTS = {
    "finn": Suspect("Finn", "Finn the dockhand", "boy", "dockhand",
                    "he was tying ropes near the fuel barrel",
                    "a wet rope loop was left on the pier",
                    "he only tied knots, and knots do not hide keys"),
    "mira": Suspect("Mira", "Mira the fish seller", "girl", "fish seller",
                    "she was counting silver fish in the bait shop",
                    "fish scales sparkled on the counter",
                    "she stayed inside with her crate and never left"),
    "otis": Suspect("Otis", "Otis the boat painter", "boy", "painter",
                    "he was dipping a brush in blue paint",
                    "a blue paint drop was on the office step",
                    "the paint was old and dry, from yesterday's work"),
}

BOY_NAMES = ["Noah", "Leo", "Finn", "Owen", "Eli", "Theo"]
GIRL_NAMES = ["Maya", "Nina", "Lily", "Sofia", "Ava", "Zoe"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A marina whodunit with a clue, a trick, and reconciliation.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=list(HELPERS))
    ap.add_argument("--suspect", choices=list(SUSPECTS))
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    if suspect == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, gender=gender, helper=helper, suspect=suspect)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "marina"),
        asp.fact("mystery_place", "marina"),
    ]
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("role", sid, s.role))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("role", hid, h.role))
    return "\n".join(lines)


ASP_RULES = r"""
% A suspect is plausible if they are at the marina and have a clue-like detail.
plausible(S) :- suspect(S).
% A whodunit resolves only when one culprit is chosen and reconciliation happens.
resolved :- culprit(_), reconciliation.
culprit(S) :- plausible(S), not innocent(S).
"""

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show culprit/1."))
    culprits = sorted(set(asp.atoms(model, "culprit")))
    expected = [("mira",), ("otis",), ("finn",)]
    if culprits == expected:
        print("OK: ASP twin loads and emits the expected culprit space.")
        return 0
    print("ASP verification mismatch.")
    print("Got:", culprits)
    print("Expected:", expected)
    return 1


def generate_world(params: StoryParams) -> World:
    world = World(Dock())
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, role="young detective"))
    helper = world.add(Entity(id=params.helper, kind="character", type=_safe_lookup(HELPERS, params.helper).type, role="friend"))
    suspect = world.add(Entity(id=params.suspect, kind="character", type=_safe_lookup(SUSPECTS, params.suspect).type, role=_safe_lookup(SUSPECTS, params.suspect).role))

    secret = world.add(Entity(id="secret", kind="thing", type="key", label="little brass key", phrase="a little brass key"))
    lobe = world.add(Entity(id="lobe", kind="thing", type="lobe", label="lobe-shaped charm", phrase="a lobe-shaped charm"))

    world.facts.update(hero=hero, helper=helper, suspect=suspect, secret=secret, lobe=lobe)

    manipulative = world.add(Entity(id="manipulation", kind="thing", type="trick", label="manipulative trick", phrase="a manipulative trick"))
    manipulative.meters["deception"] = 1.0

    world.say(f"{hero.id} loved solving little puzzles at the marina.")
    world.say(f"One bright morning, {hero.id} found a {secret.label} missing from the office hook.")
    world.say(f"Near the dock, someone had left a {lobe.label}, as if it had fallen during a hurried visit.")
    world.say(f"{hero.id} knew someone had used a manipulative trick, because the clue was placed too neatly to be an accident.")

    world.para()
    world.say(f"{helper.id} whispered that {suspect.id} looked suspicious.")
    world.say(f"But {suspect.id} had an alibi: {_safe_lookup(SUSPECTS, params.suspect).alibi}.")
    world.say(f"The only clue was {_safe_lookup(SUSPECTS, params.suspect).clue}, and it did not match the missing key.")
    world.say(f"{hero.id} followed the trail instead of the hunch.")

    world.para()
    world.say(f"At the end of the pier, {hero.id} found the real trick.")
    world.say(f"The {secret.label} had slipped into a coil of rope after {helper.id} had dropped it while fixing a float.")
    world.say(f"{helper.id} had tried to hide the mistake with a manipulative story, but the clue gave it away.")
    world.say(f"{helper.id} blushed, returned the {secret.label}, and said sorry.")

    world.para()
    world.say(f"{hero.id} listened, then nodded.")
    world.say(f"{helper.id} promised to tell the truth next time, and {suspect.id} was relieved to be cleared.")
    world.say(f"That was the reconciliation: the marina felt calm again, and the little brass key hung safely on its hook.")

    world.facts["resolved"] = True
    world.facts["culprit"] = helper
    world.facts["reconciliation"] = True
    world.facts["manipulative"] = True
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    suspect = _safe_fact(world, f, "suspect")
    secret = _safe_fact(world, f, "secret")
    return [
        QAItem(
            question=f"What kind of story happens at the marina?",
            answer=f"It is a whodunit story about {hero.id} solving a small mystery at the marina."
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"The missing thing was the {secret.label}, a little brass key."
        ),
        QAItem(
            question=f"Who really caused the trouble?",
            answer=f"It was {helper.id}. {helper.id} made the problem worse by telling a manipulative story instead of admitting the mistake."
        ),
        QAItem(
            question=f"Why did {suspect.id} stop looking guilty?",
            answer=f"{suspect.id} had a clear alibi and a clue that did not fit the missing key, so {suspect.id} was cleared."
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with reconciliation: the truth came out, the key was returned, and everyone felt calm again."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a marina?",
            answer="A marina is a place by the water where people keep boats, walk on docks, and tie up ropes."
        ),
        QAItem(
            question="What is a clue in a whodunit?",
            answer="A clue is a small piece of evidence that helps solve the mystery."
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people make peace after a problem by telling the truth, apologizing, and starting fresh."
        ),
        QAItem(
            question="What does manipulative mean?",
            answer="Manipulative means trying to control a situation in a sneaky or unfair way, often by misleading others."
        ),
        QAItem(
            question="What is a lobe?",
            answer="A lobe is a soft rounded part of something, like an ear lobe; in stories it can also be used as a small shape for a clue."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle whodunit set at a marina where a child detective solves a small mystery and ends with reconciliation.",
        f"Tell a short story about {f['hero'].id} discovering a manipulative trick, following a clue, and clearing an innocent suspect.",
        "Write a child-friendly mystery about a missing key, a false suspicion, and a sorry that repairs the friendship.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:12} ({ent.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def resolve_all() -> list[StoryParams]:
    out = []
    for gender, names in [("girl", GIRL_NAMES), ("boy", BOY_NAMES)]:
        for helper in HELPERS:
            for suspect in SUSPECTS:
                if helper != suspect:
                    out.append(StoryParams(name=names[0], gender=gender, helper=helper, suspect=suspect))
    return out


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show culprit/1.\n#show reconciliation/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show culprit/1."))
        print("culprits:", sorted(set(asp.atoms(model, "culprit"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, params in enumerate(resolve_all()):
            params.seed = base_seed + i
            samples.append(generate(params))
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
            header = f"### {p.name}: helper={p.helper}, suspect={p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
