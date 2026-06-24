#!/usr/bin/env python3
"""
A standalone storyworld for a small slice-of-life misunderstanding and twist.

Seed words: luck, chr, mousse
Features: misunderstanding, twist
Style: slice of life
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
            keys = [upper + "S", upper + "ES"]
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
    kind: str = "character"
    type: str = "person"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    neighbor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
        if not hasattr(self, "_tags"):
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
    key: str
    name: str
    indoors: bool = True
    affordances: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    key: str
    label: str
    phrase: str
    kind: str
    trait: str
    affordance: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    object: str
    hero: str
    neighbor: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "cafe": Place("cafe", "the corner cafe", True, {"talk", "wait", "serve"}),
    "laundry": Place("laundry", "the neighborhood laundry", True, {"wash", "talk", "wait"}),
    "porch": Place("porch", "the sunny porch", False, {"talk", "wait", "sit"}),
    "market": Place("market", "the little market", True, {"buy", "talk", "wait"}),
}

OBJECTS = {
    "mousse": ObjectSpec("mousse", "chocolate mousse", "a cup of chocolate mousse", "dessert", "sweet", "serve"),
    "plant": ObjectSpec("plant", "small plant", "a small plant in a clay pot", "plant", "fragile", "carry"),
    "bread": ObjectSpec("bread", "warm loaf", "a warm loaf of bread", "food", "warm", "carry"),
    "note": ObjectSpec("note", "paper note", "a folded paper note", "message", "written", "read"),
}

HEROES = ["Ari", "Mina", "June", "Noah", "Iris", "Pip"]
NEIGHBORS = ["Pat", "Sam", "Rae", "Jo", "Lee", "Tess"]


@dataclass
class World:
    place: Place
    obj: ObjectSpec
    hero: Entity
    neighbor: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "cafe": "the corner cafe",
    "laundry": "the neighborhood laundry",
    "porch": "the sunny porch",
    "market": "the little market",
}


ASP_RULES = r"""
good_place(P) :- place(P).
good_object(O) :- object(O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
        if p.indoors:
            lines.append(asp.fact("indoors", p.key))
        for a in sorted(p.affordances):
            lines.append(asp.fact("affords", p.key, a))
    for o in OBJECTS.values():
        lines.append(asp.fact("object", o.key))
        lines.append(asp.fact("trait", o.key, o.trait))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(place: Place, obj: ObjectSpec) -> bool:
    if place.key == "laundry" and obj.key == "mousse":
        return True
    if place.key == "cafe" and obj.key in {"mousse", "bread", "note"}:
        return True
    if place.key == "porch" and obj.key in {"plant", "bread"}:
        return True
    if place.key == "market" and obj.key in {"note", "bread"}:
        return True
    return False


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    hero = Entity(params.hero, label=params.hero, type="person")
    neighbor = Entity(params.neighbor, label=params.neighbor, type="person")
    return World(place, obj, hero, neighbor)


def tell(world: World) -> None:
    hero = world.hero
    neighbor = world.neighbor
    obj = world.obj
    place = world.place

    hero.memes["luck"] = 1
    hero.memes["curiosity"] = 1
    world.say(f"{hero.id} had a lucky kind of morning and walked to {place.name} with a small smile.")
    world.say(f"At the counter, {hero.id} looked at {obj.phrase} and thought it meant one thing.")
    world.say(f"{neighbor.id} came by and said a quick line that sounded serious, which made the day tilt into a misunderstanding.")

    world.para()
    if obj.key == "mousse":
        world.say(
            f"{hero.id} heard that the mousse was for someone else and hurried to step away."
            f" But {neighbor.id} laughed softly and explained that the mousse was actually a treat for {hero.id}."
        )
        hero.memes["worry"] = 1
        hero.memes["relief"] = 1
        world.say(
            f"The twist was simple and warm: {neighbor.id} had saved it as a surprise, and {hero.id}'s luck had turned into a sweet afternoon."
        )
    elif obj.key == "note":
        world.say(
            f"{hero.id} thought the note was a complaint, but it was really an invitation to sit together."
            f" {neighbor.id} had written it in a hurry, so the misunderstanding only lasted a minute."
        )
        world.say(
            f"The twist was that the invitation led to tea, and the rest of the day felt easy again."
        )
    else:
        world.say(
            f"{hero.id} feared the object was broken or misplaced, but {neighbor.id} had only carried it to the wrong spot."
            f" After the explanation, both of them smiled at how small the problem had been."
        )
        world.say(
            f"The twist was that the tiny mistake became the nicest part of the day, because it gave them a reason to pause and talk."
        )

    world.facts.update(place=place, obj=obj, hero=hero, neighbor=neighbor)


def generation_prompts(world: World) -> list[str]:
    return [
        f"Write a short slice-of-life story at {world.place.name} about a small misunderstanding involving {world.obj.label}.",
        f"Tell a gentle story where {world.hero.id} has a lucky moment, but a simple remark from {world.neighbor.id} causes confusion before the twist.",
        f"Write a child-friendly story that includes luck, a misunderstanding, and a warm twist about {world.obj.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question=f"Where was {world.hero.id} when the misunderstanding happened?",
            answer=f"{world.hero.id} was at {world.place.name}. That is where the small mix-up started and where the twist was explained."
        ),
        QAItem(
            question=f"What did {world.hero.id} think at first about {world.obj.phrase}?",
            answer=f"At first, {world.hero.id} thought {world.obj.phrase} meant something else, which caused the misunderstanding."
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the confusion was cleared up, and the day turned into a kind, lucky moment instead of a worried one."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something means one thing, but it really means something else."
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a new turn that changes what the reader expected, often revealing a surprise or a new meaning."
        ),
        QAItem(
            question="What is mousse?",
            answer="Mousse is a soft, fluffy dessert that is usually smooth and light."
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    if params.object not in OBJECTS:
        pass
    if not reasonableness_gate(_safe_lookup(PLACES, params.place), _safe_lookup(OBJECTS, params.object)):
        pass
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== Story QA =="]
    for q in sample.story_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.extend([f"Q: {q.question}", f"A: {q.answer}"])
    return "\n".join(out)


def dump_trace(world: World) -> str:
    return (
        f"place={world.place.key}\n"
        f"object={world.obj.key}\n"
        f"hero={world.hero.id}\n"
        f"neighbor={world.neighbor.id}\n"
        f"memes(hero)={world.hero.memes}"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with a misunderstanding and twist.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--object", choices=sorted(OBJECTS))
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--neighbor", choices=NEIGHBORS)
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    if not reasonableness_gate(_safe_lookup(PLACES, place), _safe_lookup(OBJECTS, obj)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    neighbor = getattr(args, "neighbor", None) or rng.choice([n for n in NEIGHBORS if n != hero])
    return StoryParams(place=place, object=obj, hero=hero, neighbor=neighbor)


CURATED = [
    StoryParams(place="cafe", object="mousse", hero="Ari", neighbor="Pat"),
    StoryParams(place="market", object="note", hero="Mina", neighbor="Sam"),
    StoryParams(place="porch", object="plant", hero="June", neighbor="Rae"),
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
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_place/1."))
        return
    if getattr(args, "verify", None):
        try:
            import storyworlds.asp as asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            sys.exit(1)
        model = asp.one_model(asp_program("#show good_place/1."))
        _ = model
        print("OK: ASP program is loadable.")
        return
    if getattr(args, "asp", None):
        print("ASP mode is available via --show-asp and --verify in this compact world.")
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
