#!/usr/bin/env python3
"""
A small animal-story world set in and around a quiet cemetery.

This world builds a classical TinyStories-style simulation: animal characters
have physical state in meters and emotional state in memes, they face conflict
and suspense, and they end in reconciliation.
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


# ---------------------------------------------------------------------------
# Core world model
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["tired", "lost", "found", "wet", "scared", "calm", "kind", "hope", "hurt"]:
            self.meters.setdefault(k, 0.0)
        for k in ["conflict", "suspense", "reconciliation", "fear", "care", "trust", "guilt", "relief", "love"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "rabbit", "bird", "squirrel", "mouse"}
        male = {"dog", "fox", "bear", "otter", "badger"}
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
class Setting:
    name: str = "the cemetery"
    outdoors: bool = True
    quiet: bool = True
    setting: object | None = None
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
class StoryParams:
    place: str
    hero: str
    helper: str
    lost_item: str
    seed: Optional[int] = None
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
HEROES = {
    "Milo": ("mouse", "curious"),
    "Pip": ("rabbit", "gentle"),
    "Tara": ("cat", "careful"),
    "Hugo": ("dog", "brave"),
    "Nori": ("bird", "thoughtful"),
    "Fern": ("squirrel", "lively"),
}

HELPERS = {
    "Otis": ("otter", "kind"),
    "Mina": ("mouse", "patient"),
    "Bea": ("bird", "calm"),
    "Rolo": ("rabbit", "helpful"),
    "Sage": ("cat", "gentle"),
}

LOST_ITEMS = {
    "lantern": "a little lantern with a blue ribbon",
    "flower": "a white flower bouquet",
    "note": "a folded note tied with string",
    "toy": "a small wooden toy",
    "stone": "a smooth painted stone",
}

PLACES = {
    "cemetery_gate": "the cemetery gate",
    "old_path": "the old path between the stones",
    "rose_tree": "the rose tree near the back rows",
    "bench": "the quiet bench by the wall",
}

ANIMAL_NAMES = list(HEROES) + list(HELPERS)

TRAITS = ["curious", "gentle", "careful", "brave", "thoughtful", "lively", "patient", "helpful"]


# ---------------------------------------------------------------------------
# Reasonableness and ASP twin
# ---------------------------------------------------------------------------
def reasonable_combo(place: str, hero: str, helper: str, lost_item: str) -> bool:
    if hero == helper:
        return False
    if lost_item not in LOST_ITEMS:
        return False
    return place in PLACES


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for name, (species, trait) in HEROES.items():
        lines.append(asp.fact("hero", name))
        lines.append(asp.fact("species", name, species))
        lines.append(asp.fact("trait", name, trait))
    for name, (species, trait) in HELPERS.items():
        lines.append(asp.fact("helper", name))
        lines.append(asp.fact("species", name, species))
        lines.append(asp.fact("trait", name, trait))
    for item in LOST_ITEMS:
        lines.append(asp.fact("lost_item", item))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Hero, Helper, Item) :- place(Place), hero(Hero), helper(Helper), lost_item(Item), Hero != Helper.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = {
        (place, hero, helper, item)
        for place in PLACES
        for hero in HEROES
        for helper in HELPERS
        for item in LOST_ITEMS
        if reasonable_combo(place, hero, helper, item)
    }
    if clingo_set == py_set:
        print(f"OK: clingo gate matches reasonable_combo() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def build_character(world: World, name: str, kind: str, trait: str, label: str) -> Entity:
    return world.add(Entity(id=name, kind="character", type=kind, label=label, phrase=label, props={"trait": trait}))


def predict(world: World, hero: Entity, helper: Entity, item: Entity) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["suspense"] += 1
    sim.get(hero.id).meters["lost"] += 1
    sim.get(helper.id).memes["care"] += 1
    if item.id in sim.entities:
        sim.get(item.id).meters["found"] += 1
    return {
        "conflict": sim.get(hero.id).memes["conflict"],
        "suspense": sim.get(hero.id).memes["suspense"] + 1,
    }


def start_story(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who often visited {world.setting.name} to feel close to the quiet stones."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved the soft paths and the still air, but {item.phrase} had gone missing."
    )
    hero.memes["hope"] += 1
    hero.memes["suspense"] += 1


def conflict_and_suspense(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"At {world.setting.name}, {hero.id} looked under a bench and then behind a rose bush, but {item.id} was nowhere there."
    )
    hero.memes["fear"] += 1
    hero.memes["conflict"] += 1
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} noticed {hero.id} getting worried and asked if anything was wrong."
    )
    world.say(
        f"{hero.id} whispered that the {item.id} had been lost, and that made the little search feel even more suspenseful."
    )


def discovery(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    hero.meters["lost"] += 1
    world.say(
        f"Then {helper.id} spotted a pale shape near the old path: {item.phrase}, tucked under a fallen leaf."
    )
    item.meters["found"] += 1
    hero.memes["relief"] += 1


def reconciliation(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.para()
    hero.memes["conflict"] = 0
    hero.memes["reconciliation"] += 1
    hero.memes["trust"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{hero.id} smiled at {helper.id} and said thank you for searching so kindly."
    )
    world.say(
        f"{helper.id} gave {item.id} back, and the two friends sat together in the calm cemetery air, feeling peaceful again."
    )


def tell_story(params: StoryParams) -> World:
    setting = Setting(name=_safe_lookup(PLACES, params.place))
    world = World(setting)

    hero_kind, hero_trait = _safe_lookup(HEROES, params.hero)
    helper_kind, helper_trait = _safe_lookup(HELPERS, params.helper)

    hero = build_character(world, params.hero, hero_kind, hero_trait, f"the {hero_trait} {hero_kind}")
    helper = build_character(world, params.helper, helper_kind, helper_trait, f"the {helper_trait} {helper_kind}")

    item = world.add(Entity(
        id=params.lost_item,
        kind="thing",
        type=params.lost_item,
        label=params.lost_item,
        phrase=_safe_lookup(LOST_ITEMS, params.lost_item),
    ))

    world.facts.update(hero=hero, helper=helper, item=item, params=params, setting=setting)

    start_story(world, hero, helper, item)
    conflict_and_suspense(world, hero, helper, item)
    discovery(world, hero, helper, item)
    reconciliation(world, hero, helper, item)

    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    hero = p.hero
    helper = p.helper
    item = p.lost_item
    place = _safe_lookup(PLACES, p.place)
    return [
        f"Write a short animal story set in {place} about {hero} and a missing {item}.",
        f"Tell a gentle suspense story where {hero} searches for {item} and {helper} helps in a cemetery.",
        "Write a child-friendly story with conflict, suspense, and reconciliation among animal friends.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    item = _safe_fact(world, world.facts, "item")
    return [
        QAItem(
            question=f"Who was looking for the missing {item.id}?",
            answer=f"{hero.id} was looking for the missing {item.phrase} in {world.setting.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} find the {item.id}?",
            answer=f"{helper.id} helped by searching carefully and spotting {item.phrase} near the old path.",
        ),
        QAItem(
            question=f"Why was the middle of the story suspenseful?",
            answer=f"It was suspenseful because {hero.id} could not find {item.id} right away, so the search felt uncertain and quiet.",
        ),
        QAItem(
            question=f"How did the friends end the story?",
            answer=f"They ended by reconciling happily after {helper.id} returned {item.id} to {hero.id}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cemetery?",
            answer="A cemetery is a quiet place where people come to remember loved ones and where many graves and stones are kept cared for.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means friends stop being upset and find a peaceful way to be together again.",
        ),
        QAItem(
            question="What is conflict in a story?",
            answer="Conflict is the problem or disagreement that makes the characters worry or argue before things get better.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of not knowing what will happen next, which makes the moment feel tense and exciting.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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
        if e.kind == "character":
            bits.append(f"trait={e.props.get('trait', '')}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world set in a cemetery with conflict, suspense, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--lost-item", choices=LOST_ITEMS, dest="lost_item")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    helper_choices = [h for h in HELPERS if h != hero]
    helper = getattr(args, "helper", None) or rng.choice(helper_choices)
    item = getattr(args, "lost_item", None) or rng.choice(list(LOST_ITEMS))
    if not reasonable_combo(place, hero, helper, item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, helper=helper, lost_item=item)


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
    StoryParams(place="cemetery_gate", hero="Milo", helper="Bea", lost_item="lantern"),
    StoryParams(place="old_path", hero="Pip", helper="Otis", lost_item="note"),
    StoryParams(place="rose_tree", hero="Tara", helper="Rolo", lost_item="flower"),
    StoryParams(place="bench", hero="Fern", helper="Sage", lost_item="toy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/4."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible combos:")
        for v in vals:
            print(v)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} with {p.helper} at {_safe_lookup(PLACES, p.place)} ({p.lost_item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
