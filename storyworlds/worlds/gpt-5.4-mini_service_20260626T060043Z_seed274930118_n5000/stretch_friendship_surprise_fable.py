#!/usr/bin/env python3
"""
A small fable-style story world about stretch, friendship, and surprise.

A gentle seed tale:
A rabbit and a mole were friends. Each day, the rabbit liked to stretch
before play, and the mole liked to help by holding the ribbon that marked
their little path. One morning, they found a too-short bridge across a ditch.
The rabbit wanted to stretch across it alone, but the mole saw a safer way:
they could stretch a vine between the banks together and make a better path.
The surprise was that the vine held, and their friendship made the crossing
easy for everyone.

The world model tracks:
- physical meters: tension, length, balance, access, usefulness
- emotional memes: trust, worry, wonder, pride, friendship, surprise
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    friend: object | None = None
    hero: object | None = None
    obj: object | None = None
    def __post_init__(self) -> None:
        for k in ("length", "tension", "balance", "access", "usefulness"):
            self.meters.setdefault(k, 0.0)
        for k in ("trust", "worry", "wonder", "pride", "friendship", "surprise"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "rabbit", "hare"}
        male = {"boy", "father", "man", "mole", "fox", "crow", "dog"}
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
class Place:
    name: str
    setting_word: str
    affords: set[str] = field(default_factory=set)
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
class ObjectSpec:
    label: str
    phrase: str
    kind: str
    region: str
    helps_with: set[str] = field(default_factory=set)
    can_bridge: bool = False
    surprise_help: bool = False
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
    hero: str
    friend: str
    object: str
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
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.surprised: bool = False

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.surprised = self.surprised
        return w


PLACES = {
    "meadow": Place("the meadow", "outdoor", {"stretch", "cross"}),
    "orchard": Place("the orchard", "outdoor", {"stretch", "cross"}),
    "garden": Place("the garden", "outdoor", {"stretch", "cross"}),
}

HEROES = {
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "mole": {"type": "mole", "label": "mole"},
    "fox": {"type": "fox", "label": "fox"},
    "crow": {"type": "crow", "label": "crow"},
}

FRIENDS = {
    "mole": {"type": "mole", "label": "mole"},
    "rabbit": {"type": "rabbit", "label": "rabbit"},
    "dog": {"type": "dog", "label": "dog"},
    "hedgehog": {"type": "hedgehog", "label": "hedgehog"},
}

OBJECTS = {
    "vine": ObjectSpec(
        label="vine",
        phrase="a long green vine",
        kind="vine",
        region="bridge",
        helps_with={"stretch", "cross"},
        can_bridge=True,
        surprise_help=True,
    ),
    "ribbon": ObjectSpec(
        label="ribbon",
        phrase="a bright ribbon",
        kind="ribbon",
        region="path",
        helps_with={"mark"},
        can_bridge=False,
        surprise_help=True,
    ),
    "rope": ObjectSpec(
        label="rope",
        phrase="a sturdy rope",
        kind="rope",
        region="bridge",
        helps_with={"stretch", "cross"},
        can_bridge=True,
        surprise_help=False,
    ),
}

NAMES = ["Pip", "Mina", "Toby", "Luna", "Bram", "Nia", "Ollie", "Dora"]
TRAITS = ["kind", "curious", "gentle", "brave", "patient", "cheerful"]


def _do_stretch(world: World, hero: Entity, obj: Entity) -> None:
    hero.meters["length"] += 1
    hero.memes["wonder"] += 1
    obj.meters["tension"] += 1
    if obj.type == "vine":
        obj.meters["length"] += 1


def _rule_surprise(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("attempted") and world.facts.get("helped") and not world.surprised:
        hero = world.get(world.facts["hero_id"])
        friend = world.get(world.facts["friend_id"])
        obj = world.get(world.facts["object_id"])
        if obj.meters["usefulness"] >= THRESHOLD:
            world.surprised = True
            hero.memes["surprise"] += 1
            friend.memes["surprise"] += 1
            out.append(f"To their surprise, {obj.label} worked better than anyone had hoped.")
    return out


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        lines = _rule_surprise(world)
        if lines:
            changed = True
            for s in lines:
                world.say(s)


def reasonableness(place: Place, obj: ObjectSpec) -> bool:
    return "stretch" in place.affords and obj.can_bridge


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_bridge:
            lines.append(asp.fact("bridgeable", oid))
        if o.surprise_help:
            lines.append(asp.fact("surprising", oid))
        for a in sorted(o.helps_with):
            lines.append(asp.fact("helps", oid, a))
    return "\n".join(lines)


ASP_RULES = r"""
good(P,O) :- affords(P,stretch), bridgeable(O), helps(O,stretch).
surprise(O) :- surprising(O), good(_,O).
#show good/2.
#show surprise/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good/2."))
    return sorted(set(asp.atoms(model, "good")))


def asp_verify() -> int:
    python = {(p, o) for p, pz in PLACES.items() for o, oz in OBJECTS.items() if reasonableness(pz, oz)}
    clingo = set(asp_valid())
    if python == clingo:
        print(f"OK: ASP matches Python ({len(python)} cases).")
        return 0
    print("Mismatch.")
    print("only python:", sorted(python - clingo))
    print("only asp:", sorted(clingo - python))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style world of stretch, friendship, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [(p, h, f, o) for p in PLACES for h in HEROES for f in FRIENDS for o in OBJECTS
              if h != f and reasonableness(_safe_lookup(PLACES, p), _safe_lookup(OBJECTS, o))]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "hero", None):
        combos = [c for c in combos if c[1] == getattr(args, "hero", None)]
    if getattr(args, "friend", None):
        combos = [c for c in combos if c[2] == getattr(args, "friend", None)]
    if getattr(args, "object", None):
        combos = [c for c in combos if c[3] == getattr(args, "object", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    p, h, f, o = rng.choice(list(combos))
    return StoryParams(place=p, hero=h, friend=f, object=o)


def make_names(params: StoryParams, rng: random.Random) -> tuple[str, str]:
    hero = params.name or rng.choice(NAMES)
    friend = params.friend_name or rng.choice([n for n in NAMES if n != hero])
    return hero, friend


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero_name, friend_name = params.hero_name, params.friend_name_value
    hero = world.add(Entity(id=hero_name, kind="character", type=params.hero, label=params.hero))
    friend = world.add(Entity(id=friend_name, kind="character", type=params.friend, label=params.friend))
    obj_spec = _safe_lookup(OBJECTS, params.object)
    obj = world.add(Entity(id=obj_spec.label, type=obj_spec.kind, label=obj_spec.label, phrase=obj_spec.phrase))

    hero.traits = ["little", "kind"]
    friend.traits = ["little", "helpful"]

    world.say(f"{hero_name} the {hero.label} and {friend_name} the {friend.label} were friends who liked to help one another.")
    world.say(f"Each morning, {hero_name} liked to stretch before play, and {friend_name} liked to watch and smile.")
    world.para()
    world.say(f"One day in {world.place.name}, they found {obj.phrase} beside a narrow ditch.")
    world.say(f"{hero_name} wanted to stretch across it at once, but that way looked wobbly and unkind to little feet.")
    world.say(f"{friend_name} thought of a safer plan: they could stretch the {obj.label} between the banks and make a small bridge.")
    world.facts.update(hero_id=hero.id, friend_id=friend.id, object_id=obj.id, attempted=True)

    _do_stretch(world, hero, obj)
    obj.meters["usefulness"] += 1
    world.facts["helped"] = True
    world.say(f"Together, they tied and pulled until the {obj.label} held firm.")
    propagate(world)

    world.para()
    world.say(f"The surprise was sweet: the bridge stayed strong, and both friends crossed with easy steps.")
    world.say(f"{hero_name} stretched in relief, while {friend_name} laughed, glad that friendship had made the path possible.")
    world.say(f"By the end, the little bridge was more useful than anyone expected, and both friends felt proud.")
    world.facts.update(hero=hero, friend=friend, object=obj, place=world.place, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short fable for a child about stretch, friendship, and surprise.',
        f"Tell a gentle story where two friends in {world.place.name} solve a crossing problem together.",
        "Write a simple fable in which a surprise turns a risky stretch into a safe bridge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    obj = _safe_fact(world, world.facts, "object")
    place = _safe_fact(world, world.facts, "place").name
    return [
        QAItem(
            question=f"Who were the friends in the story?",
            answer=f"The friends were {hero.id} the {hero.label} and {friend.id} the {friend.label}.",
        ),
        QAItem(
            question=f"What did they use to make a bridge in {place}?",
            answer=f"They used {obj.phrase} to make a small bridge.",
        ),
        QAItem(
            question=f"Why was the ending a surprise?",
            answer="It was a surprise because the little bridge held strong, and the friends crossed safely when they had first worried about the ditch.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is friendship?", answer="Friendship is when people or animals care about one another and help each other."),
        QAItem(question="What is a surprise?", answer="A surprise is something unexpected that makes you feel amazed or delighted."),
        QAItem(question="What does stretch mean?", answer="To stretch means to reach out or make something longer."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        m = {k: v for k, v in e.meters.items() if v}
        n = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if n:
            bits.append(f"memes={n}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed or 0)
    hero_name, friend_name = make_names(params, rng)
    params = StoryParams(place=params.place, hero=params.hero, friend=params.friend, object=params.object, seed=params.seed)
    params.hero_name = hero_name  # type: ignore[attr-defined]
    params.friend_name_value = friend_name  # type: ignore[attr-defined]
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
    StoryParams(place="meadow", hero="rabbit", friend="mole", object="vine"),
    StoryParams(place="orchard", hero="fox", friend="dog", object="rope"),
    StoryParams(place="garden", hero="crow", friend="hedgehog", object="vine"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good/2.\n#show surprise/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good/2.\n#show surprise/1."))
        print(f"good combos: {sorted(set(asp.atoms(model, 'good')))}")
        print(f"surprises: {sorted(set(asp.atoms(model, 'surprise')))}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for i, p in enumerate(CURATED):
            p.seed = base_seed + i
            samples.append(generate(p))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
