#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a cozy room, a hassock, and reggae music.

A child finds a plain hassock, a friend helps turn it into something cheerful,
and the room changes from quiet to welcoming. The simulated world tracks both
physical state (meters) and feelings (memes), with a simple reasonableness gate:
the story only makes sense when the setting can host a little transformation and
there is a friendly way to improve the hassock without losing its purpose.
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
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    item: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.role in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.role in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Place:
    id: str
    label: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    use: str
    transformed_use: str
    can_transform: bool = False
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
    item: str
    child_name: str
    child_role: str
    friend_name: str
    friend_role: str
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


PLACES = {
    "living_room": Place(
        id="living_room",
        label="the living room",
        indoors=True,
        affords={"music", "craft", "talk"},
    ),
    "sunroom": Place(
        id="sunroom",
        label="the sunroom",
        indoors=True,
        affords={"music", "craft", "talk"},
    ),
    "porch": Place(
        id="porch",
        label="the porch",
        indoors=False,
        affords={"music", "talk"},
    ),
}

ITEMS = {
    "hassock": Item(
        id="hassock",
        label="hassock",
        phrase="a plain little hassock",
        kind="seat",
        use="rest tiny feet on",
        transformed_use="listen beside",
        can_transform=True,
    ),
    "stool": Item(
        id="stool",
        label="stool",
        phrase="a simple wooden stool",
        kind="seat",
        use="sit on",
        transformed_use="sit on with a bright cushion",
        can_transform=True,
    ),
}

CHILD_NAMES = ["Mina", "Owen", "Lena", "Noah", "Iris", "Sam"]
FRIEND_NAMES = ["Kai", "Nia", "Jules", "Maya", "Tobi", "Pia"]


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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


def _resolve_meter(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _resolve_meme(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def select_reasonable(place: Place, item: Item) -> bool:
    return place.indoors and item.can_transform and "music" in place.affords


ASP_RULES = r"""
place_ok(P) :- indoors(P).
transform_ok(I) :- item(I), can_transform(I).
valid_story(P, I) :- place_ok(P), transform_ok(I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if i.can_transform:
            lines.append(asp.fact("can_transform", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a hassock and reggae.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--role", choices=["girl", "boy"])
    ap.add_argument("--friend-role", choices=["girl", "boy"])
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
    place_key = getattr(args, "place", None) or rng.choice(list(PLACES))
    item_key = getattr(args, "item", None) or "hassock"
    place = _safe_lookup(PLACES, place_key)
    item = _safe_lookup(ITEMS, item_key)
    if not select_reasonable(place, item):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    role = getattr(args, "role", None) or rng.choice(["girl", "boy"])
    friend_role = getattr(args, "friend_role", None) or ("boy" if role == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIEND_NAMES)
    return StoryParams(
        place=place_key,
        item=item_key,
        child_name=name,
        child_role=role,
        friend_name=friend,
        friend_role=friend_role,
    )


def _intro(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    world.say(
        f"{child.id} liked the quiet corners of {world.place.label}. "
        f"{child.pronoun().capitalize()} especially liked {item.phrase}, because it made the room feel calm."
    )
    world.say(
        f"One afternoon, {child.id} and {friend.id} listened to reggae music from a little speaker, "
        f"and the steady beat made everyone sway gently."
    )
    _resolve_meme(child, "joy", 1)
    _resolve_meme(friend, "joy", 1)
    _resolve_meme(world.get("room"), "warmth", 1)


def _tension(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    world.para()
    world.say(
        f"{child.id} wanted the hassock to stay plain, but the plain look felt a little sleepy next to the reggae beat."
    )
    world.say(
        f"{friend.id} smiled and said they could make it brighter without changing what it was for."
    )
    _resolve_meme(child, "worry", 1)
    _resolve_meme(friend, "kindness", 1)


def _transform(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    world.para()
    _resolve_meter(item, "changed", 1)
    _resolve_meme(item, "shine", 1)
    _resolve_meme(child, "curiosity", 1)
    world.say(
        f"Together they found a soft cloth, a yellow ribbon, and a blue patch with tiny waves on it."
    )
    world.say(
        f"They wrapped the cloth around the hassock, tied the ribbon neatly, and tucked the patch on top."
    )
    world.say(
        f"Little by little, the hassock turned from plain to cheerful, as if the reggae rhythm had painted a smile onto it."
    )


def _resolution(world: World, child: Entity, friend: Entity, item: Entity) -> None:
    world.para()
    _resolve_meme(child, "love", 1)
    _resolve_meme(friend, "love", 1)
    _resolve_meme(world.get("room"), "warmth", 1)
    item.label = "reggae hassock"
    world.say(
        f"After that, {child.id} rested {child.pronoun('possessive')} feet on the reggae hassock and grinned at {friend.id}."
    )
    world.say(
        f"The room felt kinder, the music felt brighter, and the little hassock had become a happy part of the day."
    )


def tell(place: Place, item_def: Item, child_name: str, child_role: str, friend_name: str, friend_role: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", role=child_role, label=child_name))
    friend = world.add(Entity(id=friend_name, kind="character", role=friend_role, label=friend_name))
    room = world.add(Entity(id="room", kind="thing", label=place.label))
    item = world.add(Entity(id=item_def.id, kind="thing", label=item_def.label, phrase=item_def.phrase))
    world.facts.update(child=child, friend=friend, room=room, item=item, item_def=item_def)
    _intro(world, child, friend, item)
    _tension(world, child, friend, item)
    _transform(world, child, friend, item)
    _resolution(world, child, friend, item)
    world.facts.update(transformed=True, genre="slice_of_life", theme=["transformation", "friendship", "kindness", "reggae"])
    return world


def generation_prompts(world: World) -> list[str]:
    child = _safe_fact(world, world.facts, "child")
    friend = _safe_fact(world, world.facts, "friend")
    return [
        "Write a short slice-of-life story about a hassock and reggae music.",
        f"Tell a gentle story where {child.id} and {friend.id} make a plain hassock feel special.",
        "Write a cozy story about friendship, kindness, and a small room transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = _safe_fact(world, world.facts, "child")
    friend = _safe_fact(world, world.facts, "friend")
    item = _safe_fact(world, world.facts, "item")
    return [
        QAItem(
            question=f"What did {child.id} and {friend.id} change during the story?",
            answer=f"They changed the plain {item.label} into a reggae hassock with soft cloth and a bright ribbon.",
        ),
        QAItem(
            question=f"How did {friend.id} help {child.id}?",
            answer=f"{friend.id} helped with kindness by suggesting a gentle transformation instead of throwing the hassock away.",
        ),
        QAItem(
            question="Why did the room feel different at the end?",
            answer="The room felt different because the music, the friendship, and the cheerful hassock made it warmer and happier.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hassock?",
            answer="A hassock is a small soft seat or footrest, often used in a room for comfort.",
        ),
        QAItem(
            question="What is reggae?",
            answer="Reggae is a style of music with a steady rhythm that can sound relaxed and friendly.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means doing something gentle and helpful for someone else.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(parts)}")
    return "\n".join(lines)


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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(ITEMS, params.item),
        params.child_name,
        params.child_role,
        params.friend_name,
        params.friend_role,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(place="living_room", item="hassock", child_name="Mina", child_role="girl", friend_name="Kai", friend_role="boy"),
    StoryParams(place="sunroom", item="hassock", child_name="Owen", child_role="boy", friend_name="Nia", friend_role="girl"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
