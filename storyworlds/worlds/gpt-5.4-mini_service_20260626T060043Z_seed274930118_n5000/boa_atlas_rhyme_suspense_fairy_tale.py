#!/usr/bin/env python3
"""
A small fairy-tale story world about a brave child, a secret path, a boa, and
an atlas. The tale uses rhyme and suspense: the world model tracks whether the
boa is feared, whether the atlas is missing, and whether careful help can lead
to a safe, magical ending.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother"}
        male = {"boy", "prince", "king", "father"}
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
class Setting:
    place: str = "the moonlit garden"
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
class Creature:
    id: str
    label: str
    kind: str
    danger: str
    rhyme: str
    lair: str
    clue: str
    tames: str
    fear: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

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
        return clone


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    parent_type: str
    creature: str
    item: str
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


SETTINGS = {
    "garden": Setting("the moonlit garden", {"creature", "search"}),
    "library": Setting("the candlelit library", {"creature", "search"}),
    "tower": Setting("the ivy tower", {"creature", "search"}),
    "pond": Setting("the silver pond", {"creature", "search"}),
}

CREATURES = {
    "boa": Creature(
        id="boa",
        label="boa",
        kind="snake",
        danger="quietly large",
        rhyme="boa / glows / knows",
        lair="under the rose arch",
        clue="a soft trail of pearl scales",
        tames="hums a lullaby",
        fear="a hush in the hedge",
        tags={"boa", "snake", "suspense"},
    ),
    "atlas": Creature(
        id="atlas",
        label="atlas",
        kind="book",
        danger="old and important",
        rhyme="atlas / past us / map paths",
        lair="on the highest shelf",
        clue="a missing page of maps",
        tames="opens to the right road",
        fear="a riddle in the shelves",
        tags={"atlas", "map", "suspense"},
    ),
}

ITEMS = {
    "atlas": Entity(
        id="atlas",
        type="book",
        label="atlas",
        phrase="a little atlas with gold corners",
        owner="hero",
        caretaker="parent",
        plural=False,
    ),
    "boa": Entity(
        id="boa",
        type="snake",
        label="boa",
        phrase="a friendly boa with bright green eyes",
        owner="garden",
        caretaker="parent",
        plural=False,
    ),
}

NAMES_GIRL = ["Ava", "Mila", "Luna", "Iris", "Nora", "Elia"]
NAMES_BOY = ["Theo", "Finn", "Jude", "Oren", "Sage", "Eli"]
TRAITS = ["brave", "curious", "gentle", "bright", "careful"]

KNOWLEDGE = {
    "boa": [
        ("What is a boa?", "A boa is a big snake that moves in slow, smooth waves."),
        ("Is a boa always scary?", "No. A boa can be calm, but people should still be careful around snakes."),
    ],
    "atlas": [
        ("What is an atlas?", "An atlas is a book of maps that helps people find places."),
        ("Why do maps matter?", "Maps matter because they show roads, rivers, and paths that are hard to guess."),
    ],
    "map": [
        ("What does a map do?", "A map shows where things are and how to travel from one place to another."),
    ],
    "suspense": [
        ("What is suspense in a story?", "Suspense is the feeling of wondering what will happen next."),
    ],
    "snake": [
        ("How do snakes move?", "Snakes move by making their long bodies ripple across the ground."),
    ],
}
KNOWLEDGE_ORDER = ["boa", "atlas", "map", "snake", "suspense"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} and {b}, soft and low, in the fairy moonlight's golden glow."


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale world: boa, atlas, rhyme, suspense.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--item", choices=["atlas", "boa"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_combo(place: str, creature: str, item: str) -> bool:
    if creature == item:
        return False
    if place not in SETTINGS:
        return False
    return True


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    creature = getattr(args, "creature", None) or rng.choice(list(CREATURES))
    item = getattr(args, "item", None) or ("atlas" if creature == "boa" else "boa")
    if not valid_combo(place, creature, item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, hero_name=name, hero_type=gender, parent_type=parent, creature=creature, item=item)


def _setup(world: World, hero: Entity, parent: Entity, item: Entity, creature: Creature) -> None:
    hero.memes["wonder"] = 1
    item.owner = hero.id
    item.caretaker = parent.id
    world.say(f"{hero.id} lived near {world.setting.place} where every leaf seemed to listen.")
    world.say(f"{hero.id} loved {item.label} because it held roads, rivers, and a bit of starlight.")
    world.say(f"One hush-hush night, {hero.id} and {parent.label or 'the parent'} went to {world.setting.place}.")
    world.say(f"There, a {creature.danger} {creature.label} waited {creature.lair}, as quiet as a page turned late.")
    world.say(rhyme_line(hero.id, creature.label))


def _predict(world: World, hero: Entity, item: Entity, creature: Creature) -> bool:
    sim = world.copy()
    sim.get(hero.id).memes["fear"] += 1
    sim.get(item.id).meters["lost"] = 1
    return True


def _search(world: World, hero: Entity, parent: Entity, item: Entity, creature: Creature) -> None:
    hero.memes["fear"] += 1
    world.say(f"{hero.id} wanted to go closer, but {hero.pronoun('possessive')} heart began to flutter.")
    world.say(f'"If the {item.label} is missing, we need it," said {parent.label or "the parent"}, peering past the ivy.')
    if _predict(world, hero, item, creature):
        world.say(f"The moon seemed to whisper a warning, and even the roses looked a little nervous.")
    world.say(f"{hero.id} tiptoed on, following {creature.clue}.")


def _turn(world: World, hero: Entity, parent: Entity, item: Entity, creature: Creature) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    if creature.id == "boa":
        world.say(f"Then the {creature.label} uncurled, not to frighten, but to show a hidden hollow in the roots.")
        world.say(f"There lay the {item.label}, gleaming like a tiny crown among the moss.")
    else:
        world.say(f"Then the {creature.label} opened to one marked page, and the map shone bright as dawn.")
        world.say(f"The missing road had been hiding there all along, snug between the covers.")


def _resolution(world: World, hero: Entity, parent: Entity, item: Entity, creature: Creature) -> None:
    hero.memes["joy"] = 2
    hero.memes["fear"] = 0
    item.meters["found"] = 1
    world.say(f"{hero.id} laughed with relief and hugged {parent.label or 'the parent'} tight.")
    world.say(f"The {creature.label} {creature.tames}, and the night grew gentle again.")
    world.say(f"In the end, {hero.id} carried the {item.label} home, and the stars seemed to rhyme with the road.")


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent_type, label="the parent"))
    item = world.add(Entity(id=params.item, type="book" if params.item == "atlas" else "snake", label=params.item))
    creature = _safe_lookup(CREATURES, params.creature)

    _setup(world, hero, parent, item, creature)
    world.para()
    _search(world, hero, parent, item, creature)
    world.para()
    _turn(world, hero, parent, item, creature)
    _resolution(world, hero, parent, item, creature)

    world.facts.update(hero=hero, parent=parent, item=item, creature=creature, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    creature = _safe_fact(world, f, "creature")
    item = _safe_fact(world, f, "item")
    return [
        f"Write a fairy tale for a small child about {hero.id}, a {creature.label}, and a missing {item.label}.",
        f"Tell a rhyming story with suspense where {hero.id} must find a {item.label} near a {creature.label}.",
        f"Write a gentle story that includes the words boa and atlas and ends with a safe surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    item = _safe_fact(world, f, "item")
    creature = _safe_fact(world, f, "creature")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, who went with {parent.label or 'the parent'} to find the {item.label}.",
        ),
        QAItem(
            question=f"What caused the suspense in the garden?",
            answer=f"The suspense came from wondering where the {item.label} had gone and what the {creature.label} might do next.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The ending was happy because {hero.id} found the {item.label} and went home safely with the {parent.label or 'the parent'}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"suspense"}
    tags.add(world.facts["creature"].id)
    tags.add(world.facts["item"].label)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
item_type(atlas,book).
item_type(boa,snake).

distinct(X,Y) :- item_type(X,_), item_type(Y,_), X != Y.

compatible(P,C,I) :- place(P), creature(C), item_type(I,_), C != I.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for c in CREATURES:
        lines.append(asp.fact("creature", c))
    for i in ("atlas", "boa"):
        lines.append(asp.fact("item_type", i, "book" if i == "atlas" else "snake"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, c, i) for p in SETTINGS for c in CREATURES for i in ("atlas", "boa") if valid_combo(p, c, i)}
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} combos.")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("garden", "Ava", "girl", "mother", "boa", "atlas"),
    StoryParams("library", "Theo", "boy", "father", "atlas", "boa"),
    StoryParams("tower", "Luna", "girl", "mother", "boa", "atlas"),
]


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        for c in combos:
            print(c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.creature} with {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
