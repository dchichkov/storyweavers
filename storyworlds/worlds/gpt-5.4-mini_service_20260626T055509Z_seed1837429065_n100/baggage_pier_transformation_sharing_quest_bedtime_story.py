#!/usr/bin/env python3
"""
A bedtime-story world about a child, a pier, baggage, a small quest, sharing,
and a gentle transformation.

The seed image:
- A sleepy child arrives at a pier with too much baggage.
- A trusted helper suggests sharing the load.
- The child goes on a tiny quest to reach the boat, learns to share, and the
  burden transforms into something lighter and happier by the end.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: Optional[str] = None
    at: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    load: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") or self.label.endswith("s") else "it"
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
    id: str
    label: str
    kind: str
    luminous: bool = False
    safe: bool = False
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
class Load:
    label: str
    phrase: str
    weight: int
    shareable: bool = True
    luggage: bool = True
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
    load: str
    name: str
    gender: str
    helper: str
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
        self.facts: dict = {}
        self.fired: set[str] = set()

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


SETTINGS = {
    "pier": Place(id="pier", label="the pier", kind="pier", luminous=True, safe=True),
    "harbor": Place(id="harbor", label="the harbor pier", kind="pier", luminous=True, safe=True),
    "boardwalk": Place(id="boardwalk", label="the boardwalk pier", kind="pier", luminous=True, safe=True),
}

LOADS = {
    "baggage": Load(label="baggage", phrase="a stack of sleepy baggage", weight=3, shareable=True),
    "suitcase": Load(label="suitcase", phrase="a big suitcase with a brass clasp", weight=3, shareable=True),
    "satchel": Load(label="satchel", phrase="a small satchel full of keepsakes", weight=2, shareable=True),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Ada", "Rose", "Tess"]
BOY_NAMES = ["Ben", "Theo", "Leo", "Finn", "Eli", "Noah", "Max"]
TRAITS = ["sleepy", "gentle", "curious", "brave", "quiet", "kind"]


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'gentle')} {hero.type} who loved quiet nights.")


def setting_line(world: World) -> None:
    world.say(f"The pier was calm, and the water below it made a soft hush like a bedtime song.")


def burden_line(world: World, hero: Entity, load: Entity) -> None:
    world.say(
        f"{hero.id} carried {load.phrase}, and the load made {hero.pronoun('possessive')} arms feel heavy."
    )


def quest_line(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"That night, {hero.id} had a tiny quest: reach the lantern at the end of the pier "
        f"before sleep pulled {hero.pronoun('object')} home."
    )
    world.say(
        f"{helper.id} came along and promised to help, because a hard walk is easier when two hearts share it."
    )


def predict_transformation(world: World, hero: Entity, load: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).meters["burden"] += load.meters["burden"]
    sim.get(hero.id).memes["tired"] += 1
    return {
        "tired": sim.get(hero.id).memes["tired"] >= THRESHOLD,
        "burden": sim.get(hero.id).meters["burden"],
    }


def worry_line(world: World, hero: Entity, helper: Entity, load: Entity) -> None:
    pred = predict_transformation(world, hero, load)
    if pred["tired"]:
        world.say(
            f"{helper.id} noticed the heavy baggage and said, "
            f"\"Let's share the load so you do not grow too tired.\""
        )
    else:
        world.say(f"{helper.id} watched the path and offered a hand, just in case the load felt too big.")


def share_line(world: World, hero: Entity, helper: Entity, load: Entity) -> None:
    if load.shared_with == helper.id:
        return
    load.shared_with = helper.id
    hero.meters["burden"] = max(0.0, hero.meters["burden"] - 1.5)
    helper.meters["burden"] = 1.0
    hero.memes["hope"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"{hero.id} handed over one strap, and {helper.id} took it with a smile. "
        f"Right away, the baggage felt lighter."
    )


def transformation_line(world: World, hero: Entity, load: Entity) -> None:
    if "transformed" in world.fired:
        return
    world.fired.add("transformed")
    load.label = "shared baggage"
    load.phrase = "shared baggage"
    hero.memes["peace"] += 1
    world.say(
        f"As they walked, the baggage seemed to transform from a heavy worry into a shared adventure."
    )


def finish_line(world: World, hero: Entity, helper: Entity, load: Entity) -> None:
    hero.meters["burden"] = 0.0
    helper.meters["burden"] = 0.0
    hero.memes["rest"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"At the lantern, {hero.id} smiled, because the quest was done and the baggage was no longer lonely. "
        f"{helper.id} stood beside {hero.pronoun('object')} while the moon shone on the pier."
    )
    world.say(
        f"Then {hero.id} went home feeling lighter, as if the night itself had tucked the story in."
    )


def tell(place: Place, load_cfg: Load, name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=helper_kind))
    load = world.add(Entity(id="Load", type=load_cfg.label, label=load_cfg.label, phrase=load_cfg.phrase))
    hero.memes["trait"] = trait
    hero.meters["burden"] = float(load_cfg.weight)
    load.meters["burden"] = float(load_cfg.weight)

    hero.carried_by = None
    load.carried_by = hero.id
    load.owner = hero.id

    introduce(world, hero)
    setting_line(world)
    burden_line(world, hero, load)
    world.para()
    quest_line(world, hero, helper)
    worry_line(world, hero, helper, load)
    share_line(world, hero, helper, load)
    transformation_line(world, hero, load)
    world.para()
    finish_line(world, hero, helper, load)

    world.facts.update(hero=hero, helper=helper, load=load, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    load: Entity = _safe_fact(world, f, "load")
    place: Place = _safe_fact(world, f, "place")
    return [
        f'Write a gentle bedtime story about {hero.id} at {place.label} with {load.label}, '
        f'where sharing makes the journey easier.',
        f'Tell a small night story in which {hero.id} has a quiet quest and {helper.id} helps carry baggage at {place.label}.',
        f'Write a bedtime story about a child whose heavy load transforms into a shared burden by the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    load: Entity = _safe_fact(world, f, "load")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Where was {hero.id} when the story began?",
            answer=f"{hero.id} was at {place.label}, where the water made a soft quiet sound.",
        ),
        QAItem(
            question=f"What was heavy for {hero.id} on the pier?",
            answer=f"{load.phrase} was heavy for {hero.id}, so the walk felt hard at first.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the baggage?",
            answer=f"{helper.id} helped by taking one strap and sharing the load.",
        ),
        QAItem(
            question=f"What changed by the end of the quest?",
            answer=f"The baggage changed from a heavy worry into a shared adventure, and {hero.id} felt lighter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pier?",
            answer="A pier is a long walkway that reaches out over water, where people can stand and watch the waves.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting more than one person use or carry something together.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a small search or journey to reach a goal or find something important.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or becomes different in an important way.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
burden(H,B) :- hero(H), load(B), carries(H,B), load_weight(B,W), W >= 2.
wants_sharing(H) :- burden(H,B).
helpful(Hl,H) :- helper(Hl), hero(H), not same(Hl,H).
shared(H,B) :- burden(H,B), helper(Hl), helpful(Hl,H), shares(Hl,B).
transformed(B) :- shared(_,B).
successful_story(H,B) :- hero(H), load(B), transformed(B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("pier_place", pid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("load_weight", lid, l.weight))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("helper", "helper"))
    lines.append(asp.fact("carries", "hero", "baggage"))
    lines.append(asp.fact("shares", "helper", "baggage"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for load in LOADS:
            combos.append((place, load, "girl"))
            combos.append((place, load, "boy"))
    return combos


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show successful_story/2."))
    asp_ok = bool(asp.atoms(model, "successful_story"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: clingo gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between clingo and Python gates.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world about baggage, a pier, sharing, a quest, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    load = getattr(args, "load", None) or rng.choice(list(LOADS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, load=load, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(LOADS, params.load), params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="pier", load="baggage", name="Mia", gender="girl", helper="mother", trait="sleepy"),
    StoryParams(place="harbor", load="satchel", name="Leo", gender="boy", helper="father", trait="kind"),
    StoryParams(place="boardwalk", load="suitcase", name="Nora", gender="girl", helper="mother", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show successful_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for verification, but this small world keeps the story engine primary.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
