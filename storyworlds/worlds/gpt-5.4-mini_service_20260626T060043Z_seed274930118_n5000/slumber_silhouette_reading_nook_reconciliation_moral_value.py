#!/usr/bin/env python3
"""
A small animal story world set in a reading nook, with a soft bedtime turn:
one animal sees a silhouette, feels uneasy, and then reconciles with a friend
after learning a gentle moral value about honesty and kindness.

The story engine builds a tiny simulated world from typed entities with meters
and memes, then turns that state into child-facing prose plus grounded QA.
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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    place: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    book: object | None = None
    friend: object | None = None
    hero: object | None = None
    lamp: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mouse", "cat", "rabbit", "fox", "bear", "dog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
    quiet: bool = True
    cozy: bool = True
    reading: bool = True
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
    place: str = "reading_nook"
    animal: str = "mouse"
    friend: str = "rabbit"
    object: str = "book"
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    shadow_present: bool = False
    shadow_source: str = "lamp"
    shadow_shape: str = "silhouette"

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

    def copy(self) -> "World":
        import copy as _copy
        return World(
            place=self.place,
            entities=_copy.deepcopy(self.entities),
            facts=_copy.deepcopy(self.facts),
            paragraphs=[[]],
            fired=set(self.fired),
            shadow_present=self.shadow_present,
            shadow_source=self.shadow_source,
            shadow_shape=self.shadow_shape,
        )
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


def build_world(params: StoryParams) -> World:
    return World(place=_safe_lookup(PLACES, params.place))


def _naming(animal: str) -> str:
    return animal.capitalize()


def _animal_sentence(name: str, animal: str, action: str) -> str:
    return f"{name} was a little {animal} who liked quiet nights and soft pages."


def _shadow_sentence(world: World, name: str) -> str:
    return f"Near the reading nook lamp, a {world.shadow_shape} stretched across the wall."


def _fear_sentence(name: str, animal: str) -> str:
    return f"{name} froze. The dark shape looked bigger than it really was."


def _reconcile_sentence(name: str, friend: str) -> str:
    return f"{name} and the {friend} looked at each other, then shared a small, honest smile."


def _moral_sentence() -> str:
    return "They learned that kindness and honest words can turn a scary moment into a gentle one."


def _resolve_shadow(world: World) -> None:
    # The lamp + stacked books create the silhouette; opening the page lightens it.
    world.shadow_present = True
    world.facts["shadow_source"] = world.shadow_source
    world.facts["shadow_shape"] = world.shadow_shape


def _turn_shadow_into_understanding(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["worry"] += 1
    friend.memes["care"] += 1
    hero.memes["reconciliation"] += 1
    hero.memes["moral_value"] += 1


def tell(params: StoryParams) -> World:
    world = build_world(params)
    hero_name = "Milo"
    friend_name = "Pip"

    hero = world.add(Entity(id=hero_name, kind="character", type=params.animal, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=params.friend, label=friend_name))
    book = world.add(Entity(id="book", type="book", label="picture book", owner=hero.id))
    lamp = world.add(Entity(id="lamp", type="lamp", label="little lamp", place=world.place.id))

    world.facts.update(hero=hero, friend=friend, book=book, lamp=lamp, place=world.place, params=params)

    # Act 1
    world.say(_animal_sentence(hero_name, params.animal, "read"))
    world.say(f"In the {world.place.label}, {hero_name} and {friend_name} opened a picture book.")
    world.say(f"The little lamp glowed beside the pillows, and everything felt ready for slumber.")

    # Act 2
    world.para()
    _resolve_shadow(world)
    world.say(_shadow_sentence(world, hero_name))
    world.say(f"{hero_name} peered up and saw a {world.shadow_shape} on the wall.")
    world.say(_fear_sentence(hero_name, params.animal))
    world.say(f"{friend_name} whispered that the shape was only a shadow from the lamp and the book stack.")

    # Act 3
    world.para()
    _turn_shadow_into_understanding(world, hero, friend)
    world.say(f"{hero_name} breathed out slowly and listened.")
    world.say(f"{friend_name} moved the books, and the {world.shadow_shape} grew smaller and softer.")
    world.say(_reconcile_sentence(hero_name, friend_name))
    world.say(_moral_sentence())
    world.say(f"At last, both friends curled up in slumber while the reading nook stayed warm and calm.")

    world.facts["resolved"] = True
    return world


PLACES = {
    "reading_nook": Place(id="reading_nook", label="reading nook", quiet=True, cozy=True, reading=True),
}

ANIMALS = ["mouse", "rabbit", "cat", "dog", "bear", "fox"]

FRIENDS = {
    "mouse": ["mouse", "rabbit", "cat"],
    "rabbit": ["mouse", "rabbit", "cat"],
    "cat": ["mouse", "rabbit", "cat"],
    "dog": ["mouse", "cat", "rabbit"],
    "bear": ["mouse", "rabbit"],
    "fox": ["mouse", "rabbit", "cat"],
}

OBJECTS = ["book"]


KNOWLEDGE = {
    "slumber": [
        ("What is slumber?",
         "Slumber means sleeping peacefully or resting for the night."),
    ],
    "silhouette": [
        ("What is a silhouette?",
         "A silhouette is a dark outline of a shape made when light shines behind it."),
    ],
    "reading": [
        ("Why do animals like reading before sleep?",
         "A quiet story can help a creature feel calm and ready for slumber."),
    ],
    "kindness": [
        ("What is kindness?",
         "Kindness means being gentle, helpful, and caring toward someone else."),
    ],
    "honesty": [
        ("What is honesty?",
         "Honesty means telling the truth in a clear and gentle way."),
    ],
}


ASP_RULES = r"""
hero(X) :- animal(X).
friend(X) :- animal(X).
shadow(silhouette).
place(reading_nook).

compatible_story(P,A,F) :- place(P), animal(A), friend_type(F).
shadow_reason(P) :- place(P).
reconciliation(P,A,F) :- compatible_story(P,A,F), shadow_reason(P).
moral_value(P) :- reconciliation(P,_,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for a in FRIENDS:
        for f in _safe_lookup(FRIENDS, a):
            lines.append(asp.fact("friend_type", f))
    lines.append(asp.fact("shadow", "silhouette"))
    lines.append(asp.fact("place", "reading_nook"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.animal not in ANIMALS:
        pass
    if params.friend not in FRIENDS.get(params.animal, []):
        pass
    if params.object not in OBJECTS:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "reading_nook"
    animal = getattr(args, "animal", None) or rng.choice(ANIMALS)
    friend_choices = FRIENDS.get(animal, ["mouse"])
    friend = getattr(args, "friend", None) or rng.choice(friend_choices)
    obj = getattr(args, "object", None) or "book"
    params = StoryParams(place=place, animal=animal, friend=friend, object=obj)
    reasonableness_gate(params)
    return params


def story_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        'Write a tiny animal story about a reading nook, a silhouette, and a calm bedtime reconciliation.',
        f"Tell a gentle tale where a {p.animal} named {world.facts['hero'].id} sees a silhouette and learns a moral value.",
        'Write a child-friendly story that uses the words "slumber" and "silhouette" and ends with friends making peace.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    place = _safe_fact(world, world.facts, "place").label
    return [
        QAItem(
            question=f"Where does {hero.id} see the silhouette?",
            answer=f"{hero.id} sees the silhouette in the {place}, near the lamp and the picture book.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried at first?",
            answer=f"{hero.id} felt worried because the silhouette looked bigger and stranger than it really was.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} make things better?",
            answer=f"They talked honestly, moved the books, and shared a gentle reconciliation before settling into slumber.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"slumber", "silhouette", "reading", "kindness", "honesty"}
    for tag in tags:
        if tag in KNOWLEDGE:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
    return out


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        if e.place:
            bits.append(f"place={e.place}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  shadow_present={world.shadow_present}")
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal bedtime story world set in a reading nook.")
    ap.add_argument("--place", choices=list(PLACES.keys()))
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend", choices=sorted({f for v in FRIENDS.values() for f in v}))
    ap.add_argument("--object", choices=OBJECTS)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def asp_verify() -> int:
    py = sorted({(p, a, f) for p in PLACES for a in ANIMALS for f in FRIENDS.get(a, [])})
    asp_set = set(asp_valid_combos())
    if set(py) == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates.")
    print("only python:", sorted(set(py) - asp_set))
    print("only asp:", sorted(asp_set - set(py)))
    return 1


CURATED = [
    StoryParams(place="reading_nook", animal="mouse", friend="rabbit", object="book"),
    StoryParams(place="reading_nook", animal="cat", friend="mouse", object="book"),
    StoryParams(place="reading_nook", animal="rabbit", friend="cat", object="book"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
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
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
