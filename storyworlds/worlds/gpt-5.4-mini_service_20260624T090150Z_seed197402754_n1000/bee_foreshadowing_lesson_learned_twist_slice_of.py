#!/usr/bin/env python3
"""
A small slice-of-life story world about a child, a bee, a little worry, and a
gentle lesson learned.

Seed tale:
---
A child is in the garden with a snack and notices a bee. The child gets nervous
because the bee keeps circling the sweet drink. A parent explains that bees are
busy workers, not bullies, and suggests staying calm and watching from a safe
distance. The child learns not to swat, and the surprise twist is that the bee
was interested in the flowers nearby, helping the garden bloom.

World shape:
---
This script simulates a tiny, concrete story domain:
* a child, a parent, a bee
* a place with flowers, fruit, and sweet food
* a foreshadowed worry that turns into a small lesson
* a twist that re-frames the bee as helpful

The prose is generated from world state, not from a frozen template. The state
tracks physical meters (distance, sweetness, bloom, calm, etc.) and emotional
memes (worry, curiosity, trust, pride).
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
# Entities and world state
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
    kind: str = "thing"          # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bee: object | None = None
    child: object | None = None
    flower: object | None = None
    parent: object | None = None
    snack: object | None = None
    def __post_init__(self):
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str
    affords: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    snack: str
    flower: str
    child_name: str
    child_type: str
    parent_type: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", affords={"bee"}),
    "backyard": Setting(place="the backyard", affords={"bee"}),
    "picnic": Setting(place="the picnic table", affords={"bee"}),
}

SNACKS = {
    "cookie": {"phrase": "a sweet cookie", "sweetness": 1.0},
    "juice": {"phrase": "a cup of berry juice", "sweetness": 1.0},
    "jam": {"phrase": "a jam sandwich", "sweetness": 0.8},
}

FLOWERS = {
    "daisy": {"phrase": "bright daisies", "bloom": 1.0},
    "sunflower": {"phrase": "tall sunflowers", "bloom": 1.2},
    "lavender": {"phrase": "soft purple lavender", "bloom": 0.9},
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Finn", "Max", "Theo", "Noah"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(garden).
place(backyard).
place(picnic).

snack(cookie). snack(juice). snack(jam).
flower(daisy). flower(sunflower). flower(lavender).

affords(garden, bee).
affords(backyard, bee).
affords(picnic, bee).

sweet(cookie).
sweet(juice).
sweet(jam).

bloomy(daisy).
bloomy(sunflower).
bloomy(lavender).

valid(P, S, F) :- affords(P, bee), sweet(S), bloomy(F).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        for a in sorted(_safe_lookup(SETTINGS, p).affords):
            lines.append(asp.fact("affords", p, a))
    for s in SNACKS:
        lines.append(asp.fact("snack", s))
        if _safe_lookup(SNACKS, s)["phrase"]:
            pass
        if _safe_lookup(SNACKS, s)["sweetness"] > 0.0:
            lines.append(asp.fact("sweet", s))
    for f in FLOWERS:
        lines.append(asp.fact("flower", f))
        lines.append(asp.fact("bloomy", f))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "bee" not in setting.affords:
            continue
        for snack in SNACKS:
            for flower in FLOWERS:
                combos.append((place, snack, flower))
    return combos

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bee story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--flower", choices=FLOWERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "snack", None) is None or c[1] == getattr(args, "snack", None))
              and (getattr(args, "flower", None) is None or c[2] == getattr(args, "flower", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, snack, flower = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, snack=snack, flower=flower, child_name=name, child_type=gender, parent_type=parent)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------
def generate_story(world: World, child: Entity, parent: Entity, bee: Entity, snack: Entity, flower: Entity) -> None:
    place = world.setting.place

    world.say(f"{child.id} was spending a quiet day at {place}.")
    world.say(f"{child.pronoun('subject').capitalize()} had {snack.phrase} and liked how the snack made the afternoon feel special.")
    world.say(f"Near the flowers, a small bee hummed past again and again, and {child.id} started to wonder if it wanted the sweet crumbs.")

    world.para()
    child.memes["worry"] += 1
    child.meters["distance_to_bee"] = 2.0
    world.say(f"{child.id} took a careful step back. The bee kept drifting in gentle circles, and that made the moment feel bigger than it was.")
    world.say(f"{parent.id} noticed the look on {child.id}'s face and said, \"Bees usually care about flowers, not about bothering people.\"")
    world.say(f"{parent.id} pointed toward {flower.phrase}, where the bee had been visiting the blossoms all along.")

    world.para()
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    child.memes["lesson"] = 1.0
    child.meters["distance_to_bee"] = 4.0
    flower.meters["bloom"] += 1.0
    bee.meters["pollination"] += 1.0
    bee.meters["thirst"] = 0.0
    world.say(f"{child.id} stopped wanting to swat at anything. Instead, {child.pronoun('subject')} watched from a safe spot and listened.")
    world.say(f"The bee slid from one blossom to the next, and the flowers looked even brighter in the afternoon light.")
    world.say(f"Then the little twist made {child.id} grin: the bee had not been chasing the snack at all. {child.pronoun('subject').capitalize()} had been helping the garden bloom.")

    world.para()
    child.memes["pride"] = child.memes.get("pride", 0.0) + 1
    child.memes["worry"] = 0.0
    world.say(f"{child.id} gave a small nod and kept the snack in both hands. The bee hummed on, busy and harmless.")
    world.say(f"By the time the sun moved lower, {flower.phrase} looked fuller, {snack.phrase} was still safe, and {child.id} had learned that a calm pause can show the real story.")

    world.facts.update(
        child=child,
        parent=parent,
        bee=bee,
        snack=snack,
        flower=flower,
        place=place,
    )

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type))
    bee = world.add(Entity(id="bee", kind="thing", type="bee", label="bee"))
    snack_cfg = _safe_lookup(SNACKS, params.snack)
    flower_cfg = _safe_lookup(FLOWERS, params.flower)
    snack = world.add(Entity(id="snack", type="snack", label=params.snack, phrase=snack_cfg["phrase"], meters={"sweetness": snack_cfg["sweetness"]}))
    flower = world.add(Entity(id="flower", type="flower", label=params.flower, phrase=flower_cfg["phrase"], meters={"bloom": flower_cfg["bloom"]}))
    generate_story(world, child, parent, bee, snack, flower)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    snack: Entity = _safe_fact(world, f, "snack")
    flower: Entity = _safe_fact(world, f, "flower")
    return [
        f"Write a gentle slice-of-life story about a child named {child.id}, a bee, and {snack.phrase}.",
        f"Tell a story where a small bee near {flower.phrase} first makes {child.id} worry, then helps the child learn something kind.",
        f"Write a simple story with a foreshadowing moment, a lesson learned, and a twist about a bee in {f['place']}.",
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    parent: Entity = _safe_fact(world, f, "parent")
    snack: Entity = _safe_fact(world, f, "snack")
    flower: Entity = _safe_fact(world, f, "flower")
    return [
        QAItem(
            question=f"Why did {child.id} first move back from the bee?",
            answer=f"{child.id} moved back because the bee kept circling near {snack.phrase}, and that made {child.pronoun('object')} nervous for a moment.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn from {parent.id}?",
            answer=f"{child.id} learned that bees usually care about flowers, so it is better to stay calm and watch from a safe distance instead of swatting.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that the bee was not trying to steal the snack. It was visiting {flower.phrase} and helping the garden bloom.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What do bees do with flowers?",
            answer="Bees visit flowers to gather nectar and spread pollen, which helps plants make seeds and grow.",
        ),
        QAItem(
            question="Why should people stay calm around a bee?",
            answer="People should stay calm because a bee is often just busy doing its work, and sudden swatting can make the bee feel scared.",
        ),
    ]

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / serialization
# ---------------------------------------------------------------------------
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
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="garden", snack="cookie", flower="daisy", child_name="Mia", child_type="girl", parent_type="mother"),
    StoryParams(place="backyard", snack="juice", flower="sunflower", child_name="Leo", child_type="boy", parent_type="father"),
    StoryParams(place="picnic", snack="jam", flower="lavender", child_name="Ava", child_type="girl", parent_type="mother"),
]

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, snack, flower) combos:\n")
        for place, snack, flower in combos:
            print(f"  {place:8} {snack:8} {flower:10}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
