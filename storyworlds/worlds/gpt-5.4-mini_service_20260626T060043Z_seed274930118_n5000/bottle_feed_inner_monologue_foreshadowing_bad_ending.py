#!/usr/bin/env python3
"""
A mythic storyworld about a bottle-feed, inner monologue, foreshadowing,
and a bad ending.

The world is small on purpose: a single caretaker, a small child, a bottle,
and a few sacred places where feeding may happen. The prose is built from
state changes so the story reads like a short legend rather than a frozen
template.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    broken: bool = False
    sacred: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    b: object | None = None
    child: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"hunger": 0.0, "spill": 0.0, "risk": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "worry": 0.0, "love": 0.0, "guilt": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "man", "boy"}:
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
    name: str
    kind: str
    allows_bottle_feed: bool = True
    omen: str = ""
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
class Bottle:
    id: str
    name: str
    phrase: str
    fragile: bool = False
    sacred: bool = False
    fills_hunger: float = 1.0
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    caretaker_name: str
    caretaker_type: str
    child_name: str
    child_type: str
    bottle: str
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
    "hearth": Place("hearth", "the hearth room", "house", True, "the fire sang low"),
    "shrine": Place("shrine", "the moon shrine", "temple", True, "the bells did not ring"),
    "well": Place("well", "the old well court", "courtyard", False, "the stones listened"),
}

BOTTLES = {
    "clay": Bottle("clay", "a clay bottle", "the clay bottle", fragile=True, sacred=False, fills_hunger=0.7),
    "glass": Bottle("glass", "a glass bottle", "the glass bottle", fragile=True, sacred=False, fills_hunger=0.9),
    "bronze": Bottle("bronze", "a bronze bottle", "the bronze bottle", fragile=False, sacred=True, fills_hunger=1.0),
}

CAREGIVERS = {
    "mother": "mother",
    "father": "father",
    "aunt": "aunt",
}

CHILDREN = {
    "boy": "boy",
    "girl": "girl",
    "child": "child",
}


def _do_bottle_feed(world: World, caretaker: Entity, child: Entity, bottle: Bottle) -> None:
    if not world.place.allows_bottle_feed:
        child.memes["worry"] += 1
        world.say(f"The place itself refused the rite of bottle-feed.")
        return
    child.meters["hunger"] = max(0.0, child.meters["hunger"] - bottle.fills_hunger)
    child.memes["hope"] += 1
    if bottle.fragile and world.place.kind == "courtyard":
        child.meters["spill"] += 1
        caretaker.meters["risk"] += 1
        caretaker.memes["guilt"] += 1
        bottle.broken = True
        world.say(f"The bottle-feed shook the bottle, and the milk ran like a pale omen across the stones.")
    else:
        world.say(f"The bottle-feed soothed the child for a little while.")


def _foreshadow(world: World, caretaker: Entity, child: Entity, bottle: Bottle) -> None:
    caretaker.memes["worry"] += 1
    if bottle.fragile:
        world.say(
            f"{caretaker.id} looked at the {bottle.name} and thought, in silence, "
            f"that glass and clay remember every fall."
        )
    if world.place.omen:
        world.say(f"Even before the feeding began, {world.place.omen}.")


def _inner_monologue(world: World, caretaker: Entity, child: Entity, bottle: Bottle) -> None:
    if child.meters["hunger"] >= THRESHOLD:
        world.say(
            f'Inside {caretaker.pronoun("possessive")} chest, a small voice said, '
            f'"Feed {child.id} now, or the crying will grow into thunder."'
        )
    if bottle.fragile:
        world.say(
            f'Another thought answered, "Be careful; one rough hand can turn a blessing into shards."'
        )


def _bad_ending(world: World, caretaker: Entity, child: Entity, bottle: Bottle) -> None:
    if child.meters["hunger"] > 0.0:
        world.say(
            f"At the end, {child.id} was still hungry, and the night kept that hunger like a wolf in a cage."
        )
    if bottle.broken:
        world.say(
            f"The {bottle.label} lay broken, and {caretaker.id} knelt among the spill, "
            f"watching the milk disappear into the stones."
        )
    world.say(
        f"So the house fell quiet, not with peace, but with the heavy quiet that follows a bad choice."
    )


def tell(world: World, caretaker: Entity, child: Entity, bottle: Bottle) -> None:
    world.say(
        f"Long ago, in {world.place.name}, there lived {caretaker.id}, who kept {child.id} close like a small star."
    )
    world.say(
        f"{child.id} was a little {child.type}, and {caretaker.id} carried {bottle.phrase} for the sacred bottle-feed."
    )
    world.para()
    _foreshadow(world, caretaker, child, bottle)
    _inner_monologue(world, caretaker, child, bottle)
    world.say(
        f"{child.id} cried softly, and the sound made even the rafters seem to listen."
    )
    _do_bottle_feed(world, caretaker, child, bottle)
    world.say(
        f"But the place was wrong for such a tender rite, and the gods of the floor did not forgive clumsy hands."
    )
    world.para()
    _bad_ending(world, caretaker, child, bottle)
    world.facts.update(
        caretaker=caretaker,
        child=child,
        bottle=bottle,
        place=world.place,
        broken=bottle.broken,
        hungry=child.meters["hunger"] > 0.0,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child about a bottle-feed in {f["place"].name}.',
        f"Tell a gentle legend where {f['caretaker'].id} tries to feed {f['child'].id} from {f['bottle'].name}, but a warning in the caretaker's mind matters too late.",
        f"Write a tiny myth with foreshadowing, inner monologue, and a bad ending about {f['bottle'].name}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    caretaker: Entity = _safe_fact(world, f, "caretaker")
    child: Entity = _safe_fact(world, f, "child")
    bottle: Bottle = _safe_fact(world, f, "bottle")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who tried to do the bottle-feed in {place.name}?",
            answer=f"{caretaker.id} tried to do the bottle-feed for {child.id} in {place.name}.",
        ),
        QAItem(
            question=f"Why was {caretaker.id} uneasy before the feeding?",
            answer=(
                f"{caretaker.id} was uneasy because the bottle looked fragile, and "
                f"the mind warned that a blessing can turn into shards."
            ),
        ),
        QAItem(
            question=f"What happened to the bottle at the end?",
            answer=(
                f"The {bottle.name} broke during the feeding, and milk spilled across the stones."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=(
                f"It ended badly: {child.id} was still hungry, and the house grew quiet after the spill."
            ),
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a bottle?",
        answer="A bottle is a container that holds liquid like milk or water.",
    ),
    QAItem(
        question="What is foreshadowing?",
        answer="Foreshadowing is a hint that something important may happen later.",
    ),
    QAItem(
        question="What is an inner monologue?",
        answer="An inner monologue is the quiet talk a person hears in their own mind.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    out = list(WORLD_KNOWLEDGE)
    if world.facts["bottle"].fragile:
        out.append(QAItem(
            question="Why can a fragile bottle be dangerous?",
            answer="A fragile bottle can crack or break if it is dropped or handled roughly.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} broken={e.broken}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for bottle_id, bottle in BOTTLES.items():
            if place.allows_bottle_feed or bottle.sacred:
                combos.append((place_id, bottle_id))
    return combos


ASP_RULES = r"""
place(P) :- setting(P).
bottle(B) :- bottle_kind(B).

valid(P,B) :- place(P), bottle(B), allows_feed(P).
valid(P,B) :- place(P), bottle(B), sacred_bottle(B).

#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if place.allows_bottle_feed:
            lines.append(asp.fact("allows_feed", pid))
        if place.omen:
            lines.append(asp.fact("omen", pid))
    for bid, bottle in BOTTLES.items():
        lines.append(asp.fact("bottle_kind", bid))
        if bottle.sacred:
            lines.append(asp.fact("sacred_bottle", bid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: clingo gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("python-only:", sorted(p - a))
    print("clingo-only:", sorted(a - p))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic bottle-feed world with bad endings.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--bottle", choices=BOTTLES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name")
    ap.add_argument("--child-name")
    ap.add_argument("--caretaker")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "bottle", None) is None or c[1] == getattr(args, "bottle", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, bottle = rng.choice(list(combos))
    caretaker_type = getattr(args, "caretaker", None) or rng.choice(sorted(CAREGIVERS))
    child_type = rng.choice(sorted(CHILDREN))
    caretaker_name = getattr(args, "name", None) or rng.choice(["Asha", "Mara", "Soren", "Iris", "Tovin"])
    child_name = getattr(args, "child_name", None) or rng.choice(["Niko", "Lena", "Pax", "Ria", "Orin"])
    return StoryParams(
        place=place,
        caretaker_name=caretaker_name,
        caretaker_type=caretaker_type,
        child_name=child_name,
        child_type=child_type,
        bottle=bottle,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    caretaker = world.add(Entity(id=params.caretaker_name, kind="character", type=params.caretaker_type))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    bottle = _safe_lookup(BOTTLES, params.bottle)
    b = world.add(Entity(
        id=bottle.id,
        kind="thing",
        type="bottle",
        label=bottle.name,
        phrase=bottle.phrase,
        owner=child.id,
        caretaker=caretaker.id,
        broken=False,
    ))
    child.meters["hunger"] = 1.0
    tell(world, caretaker, child, bottle)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="hearth", caretaker_name="Asha", caretaker_type="mother", child_name="Niko", child_type="boy", bottle="clay"),
    StoryParams(place="shrine", caretaker_name="Mara", caretaker_type="aunt", child_name="Lena", child_type="girl", bottle="glass"),
    StoryParams(place="well", caretaker_name="Soren", caretaker_type="father", child_name="Pax", child_type="child", bottle="glass"),
]


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} valid (place, bottle) combos:")
        for p, b in triples:
            print(f"  {p:10} {b}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
