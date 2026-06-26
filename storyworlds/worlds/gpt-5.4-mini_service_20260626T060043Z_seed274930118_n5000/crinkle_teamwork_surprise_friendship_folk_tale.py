#!/usr/bin/env python3
"""
storyworlds/worlds/crinkle_teamwork_surprise_friendship_folk_tale.py
=====================================================================

A tiny folk-tale story world about a crinkly thing, a shared task, a surprise,
and a friendship that grows stronger when the characters help each other.

Premise:
- Two small villagers find a crinkled old bundle of trail-clues.
- The bundle hides a surprise: a lost seed-satchel that can help the village.
- They cannot reach it alone, so they must work together.

World model:
- Physical meters track things like crinkle, climb, carry, and found.
- Emotional memes track trust, worry, delight, and friendship.
- The tale turns when the crinkly clue leads them to a surprise prize, and the
  shared rescue proves their teamwork.

The generated prose should feel like a folk tale: simple, concrete, communal,
and gently magical.
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
    with_who: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def rel(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
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
    name: str
    kind: str
    features: set[str] = field(default_factory=set)
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    kind: str
    surprise: str
    benefits: str
    tags: set[str] = field(default_factory=set)
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
    object: str
    hero_a: str
    hero_b: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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


PLACES = {
    "pine_hill": Place("Pine Hill", "hill", {"path", "wind", "lookout"}),
    "river_bend": Place("River Bend", "river", {"water", "bridge", "reed"}),
    "old_wood": Place("Old Wood", "forest", {"trees", "roots", "hollow"}),
}

OBJECTS = {
    "crinkle_map": ObjectDef(
        id="crinkle_map",
        label="crinkled map",
        phrase="an old crinkled map tied with a blue thread",
        kind="map",
        surprise="a hidden seed-satchel",
        benefits="bring spring back to the little garden",
        tags={"crinkle", "map", "surprise"},
    ),
    "crinkle_basket": ObjectDef(
        id="crinkle_basket",
        label="crinkled basket",
        phrase="a crinkled basket with a lining of soft moss",
        kind="basket",
        surprise="a silver song-stone",
        benefits="call the villagers together",
        tags={"crinkle", "basket", "surprise"},
    ),
    "crinkle_cloak": ObjectDef(
        id="crinkle_cloak",
        label="crinkled cloak",
        phrase="a crinkled cloak folded around a note",
        kind="cloak",
        surprise="a warm loaf wrapped in linen",
        benefits="feed the travelers and cheer the fire",
        tags={"crinkle", "cloak", "surprise"},
    ),
}

NAMES = ["Mira", "Bram", "Tavi", "Nell", "Oren", "Lina", "Perrin", "Sela"]
KINDS = {"girl", "boy", "mother", "father"}


def folk_opening(hero_a: Entity, hero_b: Entity, place: Place, obj: ObjectDef) -> str:
    return (
        f"Long ago, in the {place.name}, there lived {hero_a.id} and {hero_b.id}, "
        f"who were dear friends. One day they found {obj.phrase}."
    )


def introduce_crinkle(world: World, hero_a: Entity, obj: Entity) -> None:
    hero_a.memes["curious"] += 1
    obj.meters["crinkle"] += 1
    world.say(
        f"{hero_a.id} ran a thumb over the crinkle, and the paper whispered like dry leaves."
    )


def teamwork_challenge(world: World, hero_a: Entity, hero_b: Entity, obj: Entity, place: Place) -> None:
    hero_a.memes["worry"] += 1
    hero_b.memes["worry"] += 1
    if place.kind == "forest":
        world.say(
            f"The path into the {place.name} was steep, and the bundle kept slipping from their hands."
        )
    elif place.kind == "river":
        world.say(
            f"At the river, the current tugged at their ankles, and the bundle almost flew away."
        )
    else:
        world.say(
            f"On the hill, the wind worried the crinkled bundle and made it dance in their arms."
        )
    world.say(
        f"They knew they could not solve the riddle alone, so they took turns and worked as one."
    )
    hero_a.memes["teamwork"] += 1
    hero_b.memes["teamwork"] += 1
    obj.meters["opened"] = 1


def reveal_surprise(world: World, hero_a: Entity, hero_b: Entity, objdef: ObjectDef, obj: Entity) -> None:
    obj.meters["found"] = 1
    obj.meters["surprise"] = 1
    hero_a.memes["delight"] += 1
    hero_b.memes["delight"] += 1
    hero_a.memes["friendship"] += 1
    hero_b.memes["friendship"] += 1
    world.say(
        f"When they opened it together, out came {objdef.surprise}."
    )
    world.say(
        f"It was the sort of surprise that made them laugh, because the clue had been hiding a gift all along."
    )


def finish(world: World, hero_a: Entity, hero_b: Entity, objdef: ObjectDef) -> None:
    hero_a.memes["friendship"] += 1
    hero_b.memes["friendship"] += 1
    world.say(
        f"With the surprise in hand, the two friends used it to {objdef.benefits}."
    )
    world.say(
        f"And from that day on, {hero_a.id} and {hero_b.id} were known as the pair who could turn a crinkle into a blessing."
    )


def tell(place: Place, objdef: ObjectDef, hero_a_name: str, hero_b_name: str) -> World:
    world = World(place)
    a = world.add(Entity(id=hero_a_name, kind="character", type="girl"))
    b = world.add(Entity(id=hero_b_name, kind="character", type="boy"))
    obj = world.add(Entity(id=objdef.id, type=objdef.kind, label=objdef.label, phrase=objdef.phrase, owner=a.id))
    world.facts.update(hero_a=a, hero_b=b, obj=obj, objdef=objdef, place=place)

    world.say(folk_opening(a, b, place, objdef))
    world.para()
    introduce_crinkle(world, a, obj)
    teamwork_challenge(world, a, b, obj, place)
    world.para()
    reveal_surprise(world, a, b, objdef, obj)
    finish(world, a, b, objdef)
    return world


SETTINGS = PLACES
OBJECTS_REGISTRY = OBJECTS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, o) for p in SETTINGS for o in OBJECTS_REGISTRY]


@dataclass
class Reason:
    place: str
    object: str
    name_a: str
    name_b: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a young child about "{f["objdef"].label}" and a surprising gift.',
        f"Tell a gentle story where {f['hero_a'].id} and {f['hero_b'].id} use teamwork to open a crinkly object.",
        f"Write a simple story that includes the word 'crinkle' and ends with friendship growing after a surprise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a: Entity = _safe_fact(world, f, "hero_a")
    b: Entity = _safe_fact(world, f, "hero_b")
    objdef: ObjectDef = _safe_fact(world, f, "objdef")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who found the {objdef.label} in the story?",
            answer=f"{a.id} and {b.id} found it together in the {place.name}.",
        ),
        QAItem(
            question=f"What made the object feel special before they opened it?",
            answer=f"It was crinkled, and the crinkle made it seem old, secret, and important.",
        ),
        QAItem(
            question=f"What did they need in order to open it safely?",
            answer=f"They needed teamwork, because one friend alone could not solve the little task.",
        ),
        QAItem(
            question=f"What was the surprise inside?",
            answer=f"The surprise was {objdef.surprise}.",
        ),
        QAItem(
            question=f"How did the story end for the two friends?",
            answer=f"They were even better friends at the end, because they shared the surprise and used it to {objdef.benefits}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you do not expect until the moment it appears.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share, and stay kind.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = []
    lines.append("== (1) Generation prompts ==")
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
        lines.append(f"  {e.id:12} ({e.kind}/{e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: the pairing of {place} and {obj} does not produce a clear crinkly teamwork surprise.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    obj = getattr(args, "object", None) or rng.choice(sorted(OBJECTS_REGISTRY))
    if (place, obj) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_a = getattr(args, "hero_a", None) or rng.choice(NAMES)
    hero_b = getattr(args, "hero_b", None) or rng.choice([n for n in NAMES if n != hero_a])
    return StoryParams(place=place, object=obj, hero_a=hero_a, hero_b=hero_b, seed=None)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(SETTINGS, params.place)
    objdef = OBJECTS_REGISTRY[params.object]
    world = tell(place, objdef, params.hero_a, params.hero_b)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale story world: crinkle, teamwork, surprise, friendship.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--object", choices=sorted(OBJECTS_REGISTRY))
    ap.add_argument("--hero-a")
    ap.add_argument("--hero-b")
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


ASP_RULES = r"""
place(P) :- setting(P).
obj(O) :- object(O).
pair(P,O) :- place(P), obj(O).
#show pair/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for o in OBJECTS_REGISTRY:
        lines.append(asp.fact("object", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show pair/2."))
    return sorted(set(asp.atoms(model, "pair")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_pairs())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show pair/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_pairs()
        print(f"{len(pairs)} compatible place/object pairs:\n")
        for p, o in pairs:
            print(f"  {p:12} {o}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, o in valid_combos():
            params = StoryParams(place=p, object=o, hero_a="Mira", hero_b="Bram")
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
            header = f"### {p.place} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
