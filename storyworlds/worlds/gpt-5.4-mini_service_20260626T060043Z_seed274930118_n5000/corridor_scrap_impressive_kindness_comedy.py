#!/usr/bin/env python3
"""
A standalone storyworld for a tiny comedy about a corridor, a scrap, and an
impressive act of kindness.
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
    carried_by: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    scrap: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    name: str = "the corridor"
    echoes: bool = True
    narrow: bool = True
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
class Scrap:
    label: str
    phrase: str
    type: str = "scrap"
    fragile: bool = True
    impressive: bool = False
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
class StoryParams:
    place: str
    scrap: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


def _r_drop_scrap(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    scrap = world.entities.get("scrap")
    if not child or not scrap:
        return out
    if child.meters.get("clumsy", 0) < THRESHOLD:
        return out
    sig = ("drop",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scrap.meters["on_floor"] = 1
    out.append("The scrap fluttered out of reach and landed on the corridor floor.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    helper = world.entities.get("helper")
    child = world.entities.get("child")
    scrap = world.entities.get("scrap")
    if not helper or not child or not scrap:
        return out
    if helper.memes.get("kindness", 0) < THRESHOLD:
        return out
    if scrap.meters.get("on_floor", 0) < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    scrap.meters["rescued"] = 1
    out.append("That was so kind it almost deserved a medal with tiny gold stickers.")
    return out


RULES = [_r_drop_scrap, _r_kindness]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_rescue(world: World, child: Entity, helper: Entity, scrap: Entity) -> dict[str, bool]:
    sim = world.copy()
    sim.get(child.id).meters["clumsy"] += 1
    propagate(sim, narrate=False)
    sim.get(helper.id).memes["kindness"] += 1
    propagate(sim, narrate=False)
    return {
        "on_floor": bool(sim.get(scrap.id).meters.get("on_floor", 0) >= THRESHOLD),
        "rescued": bool(sim.get(scrap.id).meters.get("rescued", 0) >= THRESHOLD),
    }


def setup_world(params: StoryParams) -> World:
    world = World(Place(name=params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    scrap = world.add(Entity(id="scrap", type="scrap", label="scrap", phrase=_safe_lookup(SCRAPS, params.scrap).phrase))
    world.facts.update(child=child, helper=helper, scrap=scrap, scrap_cfg=_safe_lookup(SCRAPS, params.scrap))
    return world


def tell(world: World) -> World:
    child: Entity = _safe_fact(world, world.facts, "child")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    scrap: Entity = _safe_fact(world, world.facts, "scrap")  # type: ignore[assignment]
    cfg: Scrap = _safe_fact(world, world.facts, "scrap_cfg")  # type: ignore[assignment]

    world.say(f"{child.label} was hurrying down the corridor with a nose for trouble and a grin for it.")
    world.say(f"{{}} had found {cfg.phrase}, and {child.pronoun('possessive')} day felt suddenly important.".format(child.label))
    world.say(f"The corridor was long, echoey, and just narrow enough for comic timing.")

    world.para()
    world.say(f"{child.label} wanted to carry {scrap.phrase} all the way to the end of the corridor.")
    if cfg.impressive:
        world.say(f"It was so impressive that even the hallway seemed to stand a little straighter.")
    child.meters["clumsy"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"Then {child.label} bumped a shoulder on the wall, because the corridor had the manners of a cupboard.")
    world.say(f"The scrap spun out of {child.pronoun('possessive')} hands and skittered away like a tiny skating star.")
    propagate(world, narrate=True)

    world.para()
    pred = predict_rescue(world, child, helper, scrap)
    if pred["on_floor"]:
        helper.memes["kindness"] += 1
        world.say(f"{helper.label} saw the scrap, crouched fast, and said, 'I've got it.'")
        world.say(f"{helper.label} used a careful two-finger pinch, as if rescuing a priceless cookie crumb.")
        propagate(world, narrate=True)
        if pred["rescued"]:
            world.say(f"{child.label} laughed so hard that {child.pronoun('subject')} had to lean on the wall.")
            world.say(f"By the end, the scrap was safe again, and the corridor had a new legend about the bravest kindness in the building.")
    else:
        pass

    return world


def build_story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    scrap_cfg: Scrap = _safe_fact(world, f, "scrap_cfg")  # type: ignore[assignment]
    return [
        f'Write a short comedy for a child about {child.label} in a corridor, a {scrap_cfg.label}, and a surprising act of kindness.',
        f'Tell a gentle funny story that includes the word "corridor" and ends with someone helping rescue a {scrap_cfg.label}.',
        f'Write a tiny story where a clumsy moment turns into an impressive act of kindness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    scrap_cfg: Scrap = _safe_fact(world, f, "scrap_cfg")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was carrying the {scrap_cfg.label} in the corridor?",
            answer=f"{child.label} was carrying the {scrap_cfg.label} at first.",
        ),
        QAItem(
            question=f"Why did the {scrap_cfg.label} end up on the floor?",
            answer=f"It slipped away after {child.label} bumped into the wall in the narrow corridor.",
        ),
        QAItem(
            question=f"How did {helper.label} help?",
            answer=f"{helper.label} picked up the {scrap_cfg.label} carefully and showed impressive kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a corridor?",
            answer="A corridor is a long hallway that connects rooms or doors.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, or being gentle with someone else.",
        ),
        QAItem(
            question="Why can a scrap be easy to lose?",
            answer="A scrap is usually a small piece, so it can slip, flutter, or fall out of hand easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


SETTINGS = {
    "corridor": Place(name="the corridor"),
}

SCRAPS = {
    "paper": Scrap(label="paper scrap", phrase="a small paper scrap", impressive=True),
    "ribbon": Scrap(label="ribbon scrap", phrase="a shiny ribbon scrap", impressive=True),
    "wrapper": Scrap(label="wrapper scrap", phrase="a glittery wrapper scrap", impressive=False),
}

CHILDREN = [
    ("Milo", "boy"),
    ("Nia", "girl"),
    ("Ollie", "boy"),
    ("Pia", "girl"),
]

HELPERS = [
    ("Aunt Joy", "woman"),
    ("Uncle Bean", "man"),
    ("Mara", "girl"),
    ("Toby", "boy"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, scrap) for place in SETTINGS for scrap in SCRAPS]


@dataclass
class NarrativeForm:
    style: str = "comedy"
    feature: str = "kindness"
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "scrap", None) and getattr(args, "scrap", None) not in SCRAPS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or "corridor"
    scrap = getattr(args, "scrap", None) or rng.choice(list(SCRAPS))
    child_name, child_type = (getattr(args, "name", None), getattr(args, "gender", None)) if False else (None, None)
    if getattr(args, "child_name", None):
        child_name = getattr(args, "child_name", None)
    else:
        child_name, child_type = rng.choice(CHILDREN)
    if getattr(args, "child_type", None):
        child_type = getattr(args, "child_type", None)
    elif child_type is None:
        child_type = rng.choice(["boy", "girl"])
    helper_name, helper_type = rng.choice(HELPERS)
    return StoryParams(
        place=place,
        scrap=scrap,
        child_name=child_name,
        child_type=child_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    world = tell(world)
    return StorySample(
        params=params,
        story=build_story_text(world),
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
place(corridor).
scrap(paper).
scrap(ribbon).
scrap(wrapper).

valid_story(P, S) :- place(P), scrap(S).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for s in SCRAPS:
        lines.append(asp.fact("scrap", s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py_set:
        print(" only in clingo:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in python:", sorted(py_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a corridor, a scrap, and kindness.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--scrap", choices=list(SCRAPS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["boy", "girl", "woman", "man"])
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, scrap in valid_combos():
            params = StoryParams(
                place=place,
                scrap=scrap,
                child_name="Milo",
                child_type="boy",
                helper_name="Mara",
                helper_type="girl",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
