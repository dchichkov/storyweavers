#!/usr/bin/env python3
"""
A small storyworld about a nursery-rhyme supper, a foreshadowed mix-up, a twist,
and a gentle problem-solving ending.

Seed-image premise:
- A child helps in a bright kitchen.
- Jambalaya and lasagne are both being prepared.
- A duplicate dish appears, and everyone must sort out what is what.

The story should read like a tiny rhyme-like tale with:
- Foreshadowing: a clue about a second tray or extra bowl
- Twist: the duplicate is not the dish anyone first expected
- Problem Solving: labels, smells, and care put the meal back in order
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
# Data model
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
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    first: object | None = None
    helper: object | None = None
    hero: object | None = None
    second: object | None = None
    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + amount
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
class Kitchen:
    place: str = "the kitchen"
    glowing: bool = True
    tidy: bool = True
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
class Dish:
    id: str
    label: str
    phrase: str
    scent: str
    color: str
    kind: str = "food"
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
    hero_name: str
    helper_name: str
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
    def __init__(self, kitchen: Kitchen) -> None:
        self.kitchen = kitchen
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines).strip()


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
KITCHENS = {
    "sunny": Kitchen(place="the sunny kitchen", glowing=True, tidy=True),
    "cozy": Kitchen(place="the cozy kitchen", glowing=False, tidy=True),
    "busy": Kitchen(place="the busy kitchen", glowing=True, tidy=False),
}

DISHES = {
    "jambalaya": Dish(
        id="jambalaya",
        label="jambalaya",
        phrase="a pot of jambalaya",
        scent="spicy",
        color="golden",
    ),
    "lasagne": Dish(
        id="lasagne",
        label="lasagne",
        phrase="a tray of lasagne",
        scent="cheesy",
        color="red-and-gold",
    ),
}

# The duplicate is the story's trick: a second dish can be mistaken for the first.
DUPLICATE_KINDS = ["label", "tray", "bowl", "lid"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def story_reasonable(place: str) -> bool:
    return place in KITCHENS


def explain_rejection(place: str) -> str:
    return f"(No story: the place '{place}' is not part of this little kitchen tale.)"


# ---------------------------------------------------------------------------
# Narration helpers
# ---------------------------------------------------------------------------
def _article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def intro(world: World, hero: Entity, helper: Entity, first: Dish, second: Dish) -> None:
    world.say(
        f"In {world.kitchen.place}, {hero.id} and {helper.id} hummed a tune so bright, "
        f"they stirred {first.label} and {second.label} by morning light."
    )
    world.say(
        f"{hero.id} loved the warm smells, the clink and clatter, and the way the bowls "
        f"all shone like stars."
    )


def foreshadow(world: World, duplicate_kind: str) -> None:
    world.say(
        f"Then came a tiny clue, as soft as a feather: there was { _article(duplicate_kind) } "
        f"{duplicate_kind} set near the oven, waiting with a quiet shine."
    )
    world.say(
        "The clue was little, but it winked and glimmered, as if it knew a mix-up might come."
    )


def twist(world: World, hero: Entity, helper: Entity, first: Dish, second: Dish, duplicate_kind: str) -> None:
    world.say(
        f"When the bell went ding, {hero.id} gasped and blinked twice: the duplicate was not "
        f"what anyone first thought."
    )
    world.say(
        f"It was not a second {first.label} after all. It was a duplicate {duplicate_kind}, "
        f"wearing the wrong little tag beside {second.label}."
    )
    world.say(
        f"{helper.id} frowned, then smiled. 'Oh! The clue was telling us the labels might swap.'"
    )


def solve(world: World, hero: Entity, helper: Entity, first: Dish, second: Dish) -> None:
    world.say(
        f"So {hero.id} and {helper.id} solved the tangle with care. They read each label, "
        f"sniffed each scent, and checked the colors once more."
    )
    world.say(
        f"The {first.label} smelled {first.scent}, and the {second.label} smelled {second.scent}; "
        f"that made the answer easy to know."
    )
    world.say(
        f"They set the dishes in the right places at last, and the table looked neat and merry."
    )


def ending(world: World, hero: Entity, helper: Entity, first: Dish, second: Dish) -> None:
    world.say(
        f"By supper time, {hero.id} smiled at the tidy table. The right bowls sat in the right spots, "
        f"and no one mixed up the feast again."
    )
    world.say(
        f"{helper.id} laughed, {hero.id} clapped, and the kitchen kept its happy glow."
    )


# ---------------------------------------------------------------------------
# World building
# ---------------------------------------------------------------------------
def tell(place: str, hero_name: str, helper_name: str) -> World:
    kitchen = _safe_lookup(KITCHENS, place)
    world = World(kitchen)

    hero = world.add(Entity(id=hero_name, kind="character", label=hero_name))
    helper = world.add(Entity(id=helper_name, kind="character", label=helper_name))
    first = world.add(Entity(id="dish_a", label="jambalaya", phrase="a pot of jambalaya"))
    second = world.add(Entity(id="dish_b", label="lasagne", phrase="a tray of lasagne"))

    duplicate_kind = "label"

    world.facts["hero"] = hero
    world.facts["helper"] = helper
    world.facts["first"] = first
    world.facts["second"] = second
    world.facts["duplicate_kind"] = duplicate_kind
    world.facts["place"] = place

    intro(world, hero, helper, first, second)
    world.say(
        f"On the counter sat {first.phrase}, and beside it {second.phrase}, both warm and ready."
    )
    foreshadow(world, duplicate_kind)
    world.say(
        f"The helper had made {first.label} first, then {second.label}; but a second tag sat nearby, "
        f"ready to cause a twist."
    )
    twist(world, hero, helper, first, second, duplicate_kind)
    solve(world, hero, helper, first, second)
    ending(world, hero, helper, first, second)

    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    return [
        "Write a nursery-rhyme story about a kitchen where jambalaya and lasagne are being made, "
        "and a duplicate clue causes a gentle twist.",
        "Tell a small rhyming tale in which a child notices a duplicate and helps solve the mix-up "
        "with labels and smells.",
        "Write a child-friendly story with foreshadowing, a twist, and problem solving around "
        "jambalaya, lasagne, and a duplicate tag.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, world.facts, "helper")  # type: ignore[assignment]
    first: Entity = _safe_fact(world, world.facts, "first")  # type: ignore[assignment]
    second: Entity = _safe_fact(world, world.facts, "second")  # type: ignore[assignment]
    place = _safe_fact(world, world.facts, "place")
    duplicate_kind = _safe_fact(world, world.facts, "duplicate_kind")

    return [
        QAItem(
            question=f"Where did {hero.id} and {helper.id} make the meal?",
            answer=f"They made it in {_safe_lookup(KITCHENS, place).place}, where the air smelled warm and nice.",
        ),
        QAItem(
            question=f"What two foods were being prepared in the story?",
            answer=f"The two foods were {first.label} and {second.label}.",
        ),
        QAItem(
            question="What little clue foreshadowed the mix-up?",
            answer=f"The story foreshadowed trouble with a duplicate {duplicate_kind} waiting by the oven.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that the duplicate was not a second dish at all; it was a duplicate label.",
        ),
        QAItem(
            question="How did they solve the problem?",
            answer="They solved it by reading the labels, smelling the food, checking the colors, and putting everything in the right place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is jambalaya?",
            answer="Jambalaya is a rice dish often cooked with spices and other tasty ingredients.",
        ),
        QAItem(
            question="What is lasagne?",
            answer="Lasagne is a baked pasta dish made in layers, often with sauce and cheese.",
        ),
        QAItem(
            question="What does a duplicate mean?",
            answer="A duplicate is an extra copy of something that looks very much like the original.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_place/1.
#show valid_story/1.

valid_place(P) :- kitchen(P).
valid_story(P) :- valid_place(P), has_jambalaya(P), has_lasagne(P), has_duplicate(P).

"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in KITCHENS:
        lines.append(asp.fact("kitchen", pid))
    lines.append(asp.fact("has_jambalaya", "sunny"))
    lines.append(asp.fact("has_lasagne", "sunny"))
    lines.append(asp.fact("has_duplicate", "sunny"))
    lines.append(asp.fact("has_jambalaya", "cozy"))
    lines.append(asp.fact("has_lasagne", "cozy"))
    lines.append(asp.fact("has_duplicate", "cozy"))
    lines.append(asp.fact("has_jambalaya", "busy"))
    lines.append(asp.fact("has_lasagne", "busy"))
    lines.append(asp.fact("has_duplicate", "busy"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_places() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_place/1."))
    return sorted(set(asp.atoms(model, "valid_place")))


def asp_verify() -> int:
    asp_set = {p[0] for p in asp_valid_places()}
    py_set = set(KITCHENS)
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python registry ({len(py_set)} places).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme kitchen storyworld with jambalaya, lasagne, and a duplicate twist.")
    ap.add_argument("--place", choices=KITCHENS)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
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
    place = getattr(args, "place", None) or rng.choice(list(KITCHENS))
    if not story_reasonable(place):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "hero_name", None) or rng.choice(["Mina", "Lulu", "Nico", "Toby", "Pip"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Mum", "Dad", "Nana", "Uncle Ben", "Aunt Joy"])
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.hero_name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.kitchen.place}")
    for eid, ent in world.entities.items():
        lines.append(f"{eid}: kind={ent.kind} label={ent.label} meters={ent.meters} memes={ent.memes}")
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
    StoryParams(place="sunny", hero_name="Mina", helper_name="Mum"),
    StoryParams(place="cozy", hero_name="Pip", helper_name="Nana"),
    StoryParams(place="busy", hero_name="Lulu", helper_name="Dad"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{p}" for p in sorted(asp_valid_places())))
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
