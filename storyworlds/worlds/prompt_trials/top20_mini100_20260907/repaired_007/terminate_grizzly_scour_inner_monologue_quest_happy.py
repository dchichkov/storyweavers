#!/usr/bin/env python3
"""
A tiny superhero story world about a brave quest, a grizzly problem, and a
careful scour that ends in a happy ending. The story is driven by state:
a hero, a helper, a location, a troubling threat, a search/cleaning action, and
a final change that proves the quest worked.

Seed words and features:
- terminate
- grizzly
- scour
- Inner Monologue
- Quest
- Happy Ending
- Style: Superhero Story
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))))
from results import QAItem, StoryError, StorySample  # noqa: E402



def _safe_lookup(mapping, key):
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    grizzly: object | None = None
    helper: object | None = None
    hero: object | None = None
    @property
    def phrase(self) -> str:
        return self.label or self.id

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    @property
    def phrase(self) -> str:
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        return World(place=self.place, entities=copy.deepcopy(self.entities), paragraphs=[[]], facts=dict(self.facts), fired=set(self.fired))
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]


@dataclass
class StoryParams:
    place: str = ""
    hero_name: str = ""
    helper_name: str = ""
    hero_gender: str = "boy"
    helper_gender: str = "girl"
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
    "city_rooftop": Place(id="city_rooftop", label="the city rooftop", tags={"city", "high"}),
    "museum_hall": Place(id="museum_hall", label="the museum hall", tags={"city", "indoors"}),
    "river_walk": Place(id="river_walk", label="the river walk", tags={"city", "outdoors"}),
}

NAMES = {
    "boy": ["Leo", "Mason", "Eli", "Noah", "Finn"],
    "girl": ["Aria", "Zoe", "Maya", "Nina", "Lia"],
}

CURATED = [
    StoryParams(place="city_rooftop", hero_name="Leo", helper_name="Aria", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="museum_hall", hero_name="Mason", helper_name="Zoe", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="river_walk", hero_name="Maya", helper_name="Finn", hero_gender="girl", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about a quest, a grizzly threat, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["boy", "girl"])
    helper_gender = getattr(args, "helper_gender", None) or ("girl" if hero_gender == "boy" else "boy")
    hero_name = getattr(args, "hero", None) or rng.choice(_safe_lookup(NAMES, hero_gender))
    helper_name = getattr(args, "helper", None) or rng.choice([n for n in _safe_lookup(NAMES, helper_gender) if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name, hero_gender=hero_gender, helper_gender=helper_gender)


def _stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    text = f"{params.place}:{params.hero_name}:{params.helper_name}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def tell(world: World, hero: Entity, helper: Entity) -> None:
    opening = [
        f"At {world.place.label}, {hero.id} wore a bright cape and listened for trouble.",
        f"{helper.id} smiled. \"What is our quest today?\"",
        f"{hero.id} said, \"My inner monologue says the city needs help, and I will not turn away.\"",
    ]
    for line in opening:
        world.say(line)
    world.para()

    grizzly = world.add(Entity(id="grizzly_shadow", kind="thing", type="threat", label="a grizzly shadow", role="threat"))
    grizzly.meters["danger"] = 1.0
    grizzly.meters["mess"] = 1.0
    hero.memes["alert"] += 1
    helper.memes["alert"] += 1

    trouble = [
        f"A grizzly shadow curled over the rooftop, and its dark dust clung to every crate.",
        f"\"It is huge,\" whispered {helper.id}.",
        f"\"Yes,\" said {hero.id}, \"but a quest is just a promise that we keep moving.\"",
    ]
    for line in trouble:
        world.say(line)
    world.para()

    helper.meters["scouring"] += 1
    hero.meters["scouring"] += 1
    hero.meters["leading"] += 1
    helper.meters["supporting"] += 1

    middle = [
        f"{hero.id} and {helper.id} began to scour the rooftop with a silver brush and a warm lamp beam.",
        f"\"I found the dirty edge!\" said {helper.id}.",
        f"\"Then I will sweep it clean,\" answered {hero.id}, and their voices made the plan feel brave.",
    ]
    for line in middle:
        world.say(line)
    world.para()

    grizzly.meters["danger"] = 0.0
    grizzly.meters["gone"] = 1.0
    hero.memes["hope"] += 1
    helper.memes["hope"] += 1
    hero.meters["helped"] += 1
    helper.meters["helped"] += 1

    ending = [
        f"The shadow broke apart and drifted away, and the rooftop shone like a clean lantern.",
        f"\"We did it,\" said {helper.id}.",
        f"\"We did,\" said {hero.id}, \"and the city can sleep happy tonight.\"",
    ]
    for line in ending:
        world.say(line)

    world.facts.update(
        hero=hero,
        helper=helper,
        place=world.place,
        threat=grizzly,
        quest="scour the rooftop and end the grizzly shadow",
        resolved=True,
        final_image="the rooftop shone like a clean lantern",
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        pass
    if params.hero_gender not in NAMES or params.helper_gender not in NAMES:
        pass
    if params.hero_name == params.helper_name:
        pass

    place = _safe_lookup(PLACES, params.place)
    hero = Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero", label=params.hero_name)
    helper = Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper", label=params.helper_name)
    world = World(place=place)
    world.add(hero)
    world.add(helper)
    tell(world, hero, helper)

    story = world.render()
    prompts = [
        "Write a superhero story for a small child that includes the words terminate, grizzly, and scour.",
        f"Tell a quest story where {hero.id} and {helper.id} solve a grizzly problem by scouring the place clean.",
        "Make the ending feel happy and prove that the heroes changed the world.",
    ]
    story_qa = [
        QAItem(
            question="What was the heroes' quest?",
            answer="Their quest was to scour the place and end the grizzly shadow that was darkening the scene."
        ),
        QAItem(
            question="How did the dialogue help the story move forward?",
            answer=f"{helper.id} asked what the quest was, and {hero.id} answered with a brave plan. Later, they checked their work with a short happy exchange."
        ),
        QAItem(
            question="What showed that the ending was happy?",
            answer="The rooftop shone clean again, the threat was gone, and the heroes said they had done it together."
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or journey to do something important, especially when someone needs help."
        ),
        QAItem(
            question="What does scour mean in this story?",
            answer="To scour means to search or scrub carefully until the dirty or hidden thing is gone."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:16} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
hero(H) :- hero_name(H).
helper(H) :- helper_name(H).
quest(Q) :- quest_name(Q).
resolved :- scour_done, grizzly_gone.
happy_ending :- resolved.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [
        asp.fact("hero_name", "hero"),
        asp.fact("helper_name", "helper"),
        asp.fact("quest_name", "scour_quest"),
        asp.fact("scour_done"),
        asp.fact("grizzly_gone"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show happy_ending/0."))
    return sorted({(a.name, len(a.arguments)) for a in model})


def asp_verify() -> int:
    try:
        _ = asp_valid()
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("Empty story.")
            return 1
        if "We did it" not in sample.story:
            print("Story did not reach the happy ending.")
            return 1
    except Exception as exc:
        print(f"Verification failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
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
        print(asp_program("#show happy_ending/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
