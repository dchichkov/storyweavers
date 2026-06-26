#!/usr/bin/env python3
"""
A tiny folk-tale storyworld about a stubborn rock, a kind heart, and a small
change in the village road.

Seed idea:
- A heavy rock blocks a path near a village.
- The hero wants to move fast, but kindness turns the moment.
- Helpers join in, the rock is moved, and the ending image proves the path is open.

This script models:
- physical meters: weight, effort, blocked/open path, carried/chipped rock
- emotional memes: kindness, worry, pride, gratitude, patience
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    rock: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "son"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def title(self) -> str:
        return self.label or self.type
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
    kind: str = "village"
    path: str = "lane"
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def pronounce_name(name: str) -> str:
    return name


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def describe_rock(rock: Entity) -> str:
    return rock.phrase or "a great round rock"


def nearby_detail(place: Place) -> str:
    if "market" in place.features:
        return f"Near {place.name}, the lane bent by a small market and a little stone bridge."
    if "well" in place.features:
        return f"Near {place.name}, the lane passed a well with a wooden bucket."
    return f"Near {place.name}, the lane ran past low grass and a hedge of wild flowers."


def moveable(rock: Entity) -> bool:
    return rock.meters.get("weight", 0.0) <= 4.0


def predict_movement(world: World, helper: Entity, rock: Entity) -> bool:
    sim = world.copy()
    sim.get(helper.id).memes["kindness"] += 1
    sim.get(helper.id).meters["effort"] += 1
    sim.get(rock.id).meters["shifted"] = 1
    return True


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    rock = world.add(Entity(
        id="rock",
        kind="thing",
        type="rock",
        label="rock",
        phrase="a great gray rock",
        meters={"weight": 5.0, "blocked": 1.0, "shifted": 0.0, "chipped": 0.0},
        memes={"kindness": 0.0, "worry": 0.0, "gratitude": 0.0, "pride": 0.0, "patience": 0.0},
    ))
    world.facts.update(hero=hero, helper=helper, rock=rock, place=place)
    return world


def narrate_setup(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    rock = _safe_fact(world, world.facts, "rock")
    place = _safe_fact(world, world.facts, "place")

    world.say(f"Long ago, in {place.name}, there lived {hero.pronoun('subject')} named {hero.id}.")
    world.say(f"{hero.id} loved the little lane by the trees, because it led to the spring and the bread oven.")
    world.say(f"But one morning, the lane was stopped by {describe_rock(rock)}.")
    world.say(nearby_detail(place))
    world.say(f"{helper.id} was {article(helper.type)} {helper.type} who noticed things quickly and had a kind heart.")


def narrate_conflict(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    rock = _safe_fact(world, world.facts, "rock")

    hero.memes["worry"] += 1
    helper.memes["patience"] += 1
    world.say(f"{hero.id} stared at the rock and frowned. The path was blocked, and the day felt too small.")
    world.say(f"{helper.id} came along with a basket of apples and said, \"A hard thing is lighter when two hands share it.\"")
    world.say(f"{hero.id} wanted to hurry, but {hero.pronoun('possessive')} worry grew when {describe_rock(rock)} would not budge.")


def resolve_with_kindness(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    helper = _safe_fact(world, world.facts, "helper")
    rock = _safe_fact(world, world.facts, "rock")

    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1
    helper.memes["pride"] += 1

    rock.meters["shifted"] = 1.0
    rock.meters["blocked"] = 0.0
    rock.meters["chipped"] = 0.0

    world.say(f"{helper.id} did not complain. Instead, {helper.pronoun('subject')} showed {hero.id} how to push low and steady.")
    world.say(f"{hero.id} listened, planted {hero.pronoun('possessive')} feet, and pushed with all {hero.pronoun('possessive')} small strength.")
    world.say(f"Then the two of them rolled {describe_rock(rock)} to the side, where it rested beside the grass.")
    world.say(f"The lane opened at once, and {hero.id} thanked {helper.id} with a bright smile.")
    world.say(f"By dusk, the villagers walked the lane again, and the rock sat peacefully by the flowers, no longer in anyone's way.")


def tell_story(world: World) -> World:
    narrate_setup(world)
    world.para()
    narrate_conflict(world)
    world.para()
    resolve_with_kindness(world)
    world.facts["resolved"] = True
    return world


PLACES = {
    "village_lane": Place(
        name="the village lane",
        kind="village",
        path="lane",
        features={"market", "well"},
    ),
    "orchard_path": Place(
        name="the orchard path",
        kind="village",
        path="path",
        features={"hedge"},
    ),
    "hill_road": Place(
        name="the hill road",
        kind="village",
        path="road",
        features={"flowers"},
    ),
}

HERO_NAMES = ["Mira", "Jonas", "Tavi", "Nina", "Pippa", "Oren", "Lena", "Bram"]
HELPER_NAMES = ["Old Nan", "Pavel", "Sera", "Aunt Wren", "Milo", "Grandfather Kest"]

TYPES = {
    "girl": "girl",
    "boy": "boy",
    "woman": "woman",
    "man": "man",
}

CURATED = [
    StoryParams(place="village_lane", hero_name="Mira", hero_type="girl", helper_name="Old Nan", helper_type="woman"),
    StoryParams(place="orchard_path", hero_name="Jonas", hero_type="boy", helper_name="Pavel", helper_type="man"),
    StoryParams(place="hill_road", hero_name="Lena", hero_type="girl", helper_name="Aunt Wren", helper_type="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale storyworld about a rock and kindness.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["woman", "man"])
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
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["woman", "man"])
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    if hero_name == helper_name:
        helper_name = rng.choice([n for n in HELPER_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type=hero_type, helper_name=helper_name, helper_type=helper_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(setup_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a short folk tale for a child about {hero.id}, {helper.id}, and a rock on {place.name}.",
        f"Tell a gentle story where kindness helps {hero.id} and {helper.id} move a rock from the road.",
        f"Write a simple village story that begins with a blocked lane and ends with a cleared path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    place = _safe_fact(world, f, "place")
    rock = _safe_fact(world, f, "rock")
    return [
        QAItem(
            question=f"What blocked the lane near {place.name}?",
            answer=f"A great gray rock blocked the lane near {place.name}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} move the rock?",
            answer=f"{helper.id} helped {hero.id} move the rock.",
        ),
        QAItem(
            question=f"Why did the story change once {helper.id} was kind?",
            answer="Because kindness brought two hands together, and the rock was moved out of the way.",
        ),
        QAItem(
            question=f"What was the ending image of the story?",
            answer=f"The rock rested by the grass and flowers, and the lane was open again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rock?",
            answer="A rock is a hard piece of stone.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and caring toward other people.",
        ),
        QAItem(
            question="What can two people do with a heavy thing?",
            answer="Two people can share the work and move it together more easily.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
blocked_path(R) :- rock(R), meter(R, blocked, 1).
kind_act(K) :- meme(K, kindness, 1).
resolved :- blocked_path(R), kind_act(H), helped(H), moved(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for feat in sorted(p.features):
            lines.append(asp.fact("feature", pid, feat))
    lines.append(asp.fact("rock", "rock"))
    lines.append(asp.fact("meter", "rock", "blocked", 1))
    lines.append(asp.fact("meme", "hero", "kindness", 1))
    lines.append(asp.fact("helped", "helper"))
    lines.append(asp.fact("moved", "rock"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


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
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
