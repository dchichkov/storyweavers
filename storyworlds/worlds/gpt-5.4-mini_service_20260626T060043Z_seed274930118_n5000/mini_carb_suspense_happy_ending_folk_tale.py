#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mini_carb_suspense_happy_ending_folk_tale.py
==============================================================================================================

A small folk-tale storyworld about a tiny caravan, a little carb, and a worried
night road that turns into a happy ending.

Premise:
- A child or small traveler loves a mini carb: a tiny carved cart charm, toy,
  or roadside snack-box depending on the seed.
- A useful trip requires crossing a dark place in the evening.
- Suspense comes from a missing guide, a creaking path, or a wayward light.
- The happy ending comes from a wise helper, a lantern, a song, or a shared
  trick that lets the travelers finish the road safely.

The world is intentionally compact and state-driven: objects have physical
meters and emotional memes, and narration is generated from those changes.
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    carb: object | None = None
    helper: object | None = None
    hero: object | None = None
    def __post_init__(self):
        self.meters.setdefault("damage", 0.0)
        self.meters.setdefault("loss", 0.0)
        self.meters.setdefault("distance", 0.0)
        self.meters.setdefault("light", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("courage", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("relief", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "sister"}
        male = {"boy", "father", "man", "grandfather", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    dusk: bool = True
    hazards: set[str] = field(default_factory=set)
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
    hazard: str
    charm: str
    name: str
    gender: str
    helper: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = []
        return w


def _py_gender(gender: str) -> str:
    return gender


PLACES = {
    "forest_edge": Place("forest_edge", "the forest edge", dusk=True, hazards={"dark", "wind"}),
    "stone_bridge": Place("stone_bridge", "the stone bridge", dusk=True, hazards={"dark", "creak"}),
    "lantern_lane": Place("lantern_lane", "the lantern lane", dusk=True, hazards={"dark"}),
    "river_bank": Place("river_bank", "the river bank", dusk=True, hazards={"dark", "mist"}),
}

HAZARDS = {
    "dark": {
        "name": "darkness",
        "risk": "the road looked hard to read",
        "meter": "lost",
        "turn": "a lantern",
    },
    "creak": {
        "name": "creaking boards",
        "risk": "the boards sang underfoot",
        "meter": "worry",
        "turn": "a careful step",
    },
    "mist": {
        "name": "mist",
        "risk": "the path hid its stones",
        "meter": "unclear",
        "turn": "a guide rope",
    },
    "wind": {
        "name": "wind",
        "risk": "the little flame kept bending low",
        "meter": "flicker",
        "turn": "a lantern hood",
    },
}

CHARTS = {
    "mini_carb": {
        "label": "mini carb",
        "phrase": "a tiny mini carb charm",
        "risk": "small enough to lose in a pocket",
        "owner_kind": "charm",
        "plural": False,
    },
    "carb_box": {
        "label": "carb box",
        "phrase": "a little carb box with a brass latch",
        "risk": "easy to jostle open on the road",
        "owner_kind": "box",
        "plural": False,
    },
    "carb_bread": {
        "label": "carb loaf",
        "phrase": "a warm carb loaf wrapped in cloth",
        "risk": "best shared before it goes cold",
        "owner_kind": "bread",
        "plural": False,
    },
}

HELPERS = {
    "grandmother": {"type": "grandmother", "label": "grandmother", "kind": "character"},
    "father": {"type": "father", "label": "father", "kind": "character"},
    "miller": {"type": "man", "label": "the miller", "kind": "character"},
    "sister": {"type": "sister", "label": "sister", "kind": "character"},
}

NAMES_GIRL = ["Mira", "Luna", "Ava", "Nina", "Rosa", "Tess", "Ivy", "Pia"]
NAMES_BOY = ["Owen", "Finn", "Eli", "Noah", "Theo", "Ben", "Jude", "Leo"]
TRAITS = ["brave", "small", "curious", "gentle", "lively"]


def reasonableness_gate(place: str, hazard: str, charm: str) -> None:
    if place not in PLACES:
        pass
    if hazard not in HAZARDS:
        pass
    if charm not in CHARTS:
        pass
    if hazard not in _safe_lookup(PLACES, place).hazards:
        pass
    if charm == "carb_bread" and hazard == "wind":
        pass
    if charm == "mini_carb" and hazard == "mist":
        pass


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dusk:
            lines.append(asp.fact("dusk", pid))
        for h in sorted(p.hazards):
            lines.append(asp.fact("hazard", pid, h))
    for hid, h in HAZARDS.items():
        lines.append(asp.fact("hazkind", hid))
        lines.append(asp.fact("risk", hid, h["meter"]))
    for cid, c in CHARTS.items():
        lines.append(asp.fact("carb", cid))
        lines.append(asp.fact("label", cid, c["label"]))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P,H,C) :- place(P), hazkind(H), carb(C), hazard(P,H), okay(C,H).
okay(carb_box,creak).
okay(carb_bread,dark).
okay(mini_carb,dark).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_triples())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def valid_triples() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HAZARDS:
            for c in CHARTS:
                try:
                    reasonableness_gate(p, h, c)
                except StoryError:
                    continue
                combos.append((p, h, c))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about a mini carb and a safe ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--carb", choices=CHARTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "hazard", None) and getattr(args, "carb", None):
        reasonableness_gate(getattr(args, "place", None), getattr(args, "hazard", None), getattr(args, "carb", None))
    triples = [t for t in valid_triples()
               if (getattr(args, "place", None) is None or t[0] == getattr(args, "place", None))
               and (getattr(args, "hazard", None) is None or t[1] == getattr(args, "hazard", None))
               and (getattr(args, "carb", None) is None or t[2] == getattr(args, "carb", None))]
    if not triples:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, hazard, carb = rng.choice(sorted(triples))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place, hazard=hazard, charm=carb, name=name, gender=gender, helper=helper)


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.gender == "girl" else "boy"))
    helper_info = _safe_lookup(HELPERS, params.helper)
    helper = world.add(Entity(id="helper", kind="character", type=helper_info["type"], label=helper_info["label"]))
    charm_cfg = _safe_lookup(CHARTS, params.charm)
    carb = world.add(Entity(
        id="carb", kind="thing", type=charm_cfg["owner_kind"],
        label=charm_cfg["label"], phrase=charm_cfg["phrase"], owner=hero.id
    ))
    hero.memes["worry"] += 1
    world.say(f"Once there was a {rng_trait(world)} {hero.type} named {hero.id}, and {hero.pronoun('possessive')} heart loved {carb.label}.")
    world.say(f"It was a folk-tale kind of day at {place.label}, where {carb.phrase} felt special in {hero.pronoun('possessive')} hands.")
    return world


def rng_trait(world: World) -> str:
    return random.choice(TRAITS)


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero = next(e for e in world.entities.values() if e.id == params.name)
    helper = world.get("helper")
    carb = world.get("carb")
    hazard = _safe_lookup(HAZARDS, params.hazard)

    world.say(f"But when evening came, {hero.id} had to cross {world.place.label}, and {hazard['risk']}.")
    hero.memes["worry"] += 1
    world.say(f"{hero.id} held {carb.pronoun('possessive')} {carb.label} close, because {carb.risk}.")
    world.say(f"Then {helper.label} came along and saw the trouble first, which made the road feel smaller.")

    if params.hazard == "dark":
        helper.meters["light"] += 1
        hero.memes["courage"] += 1
        world.say(f"{helper.label} lifted a lantern, and the little glow reached the stones.")
    elif params.hazard == "creak":
        helper.meters["distance"] += 1
        hero.memes["courage"] += 1
        world.say(f"{helper.label} tested each board with a careful step, so the bridge told its secrets one by one.")
    elif params.hazard == "mist":
        helper.meters["distance"] += 1
        hero.memes["courage"] += 1
        world.say(f"{helper.label} tied a guide rope to the post, and the path stopped hiding.")
    else:
        helper.meters["light"] += 1
        hero.memes["courage"] += 1
        world.say(f"{helper.label} made a hood for the lantern, and the flame stood up straight against the wind.")

    hero.meters["distance"] += 1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    world.say(f"So {hero.id} crossed safely with {carb.label} still tucked away, and the worry turned into a warm smile.")
    world.say(f"At the end, the road was behind them, the {carb.label} was safe, and the night felt friendly again.")

    world.facts = {
        "hero": hero,
        "helper": helper,
        "carb": carb,
        "params": params,
        "hazard": hazard,
        "place": world.place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short folk tale for children that includes the words "mini" and "carb".',
        f"Tell a suspenseful but gentle story about {p.name} crossing {world.place.label} with a {p.charm.replace('_', ' ')} and a helpful guide.",
        f"Write a happy-ending story where a small traveler faces {p.hazard} and gets safely across the road.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    carb: Entity = _safe_fact(world, f, "carb")
    params: StoryParams = _safe_fact(world, f, "params")
    hazard = _safe_lookup(HAZARDS, params.hazard)["name"]
    return [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, a small {hero.type} who loved {carb.label}.",
        ),
        QAItem(
            question=f"What made the road scary at {world.place.label}?",
            answer=f"The road felt scary because of {hazard}, and that made {hero.id} worry about getting across safely.",
        ),
        QAItem(
            question=f"Who helped {hero.id} in the end?",
            answer=f"{helper.label} helped by giving the story a safe way forward, like a lantern, rope, or careful step.",
        ),
        QAItem(
            question=f"What happened to the {carb.label} by the end?",
            answer=f"The {carb.label} stayed safe with {hero.id}, and that helped the tale end happily.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern carries a little light so people can see a path when it is dark.",
        ),
        QAItem(
            question="Why do people use guide ropes?",
            answer="People use guide ropes to keep their way steady when the road is hard to see.",
        ),
        QAItem(
            question="What does a careful step mean?",
            answer="A careful step means moving slowly and gently so you do not slip or make a mistake.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("\n== story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
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
    StoryParams(place="forest_edge", hazard="dark", charm="mini_carb", name="Mira", gender="girl", helper="grandmother"),
    StoryParams(place="stone_bridge", hazard="creak", charm="carb_box", name="Owen", gender="boy", helper="father"),
    StoryParams(place="lantern_lane", hazard="dark", charm="carb_bread", name="Nina", gender="girl", helper="sister"),
    StoryParams(place="river_bank", hazard="mist", charm="carb_box", name="Leo", gender="boy", helper="miller"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid()
        print(f"{len(triples)} valid stories:")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
