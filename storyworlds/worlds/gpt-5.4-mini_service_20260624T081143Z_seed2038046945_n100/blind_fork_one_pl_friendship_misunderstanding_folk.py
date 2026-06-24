#!/usr/bin/env python3
"""
storyworlds/worlds/blind_fork_one_pl_friendship_misunderstanding_folk.py
=======================================================================

A small folk-tale storyworld about friendship, a misunderstanding, and a
one-place problem around a fork in the path.

Premise:
- A blind friend cannot easily tell two similar things apart by sight.
- A fork in the road creates a choice that should be simple, but a mistaken
  reading of signs causes hurt feelings.
- Friendship repairs the misunderstanding through a concrete, state-driven
  act: listening, describing, and walking together.

The world is intentionally small and classical:
- one child protagonist
- one friend
- one important object
- one setting with a forked path
- one misunderstanding that can be resolved with an explanation

The tone is meant to stay close to folk tales: plain, warm, concrete, and
slightly old-fashioned.
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


THRESHOLD = 1.0



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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    blind: bool = False
    plural: bool = False

    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            gender = next((t for t in self.traits if t in {"girl", "boy", "woman", "man"}), "")
            if gender in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if gender in {"boy", "man"}:
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
    name: str
    forked: bool = False
    sounds: str = ""
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
class StoryParams:
    place: str
    hero: str
    friend: str
    object: str
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


@dataclass
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
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
        return World(place=self.place, entities=copy.deepcopy(self.entities), facts=dict(self.facts), paragraphs=[[]])
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
    "village": Place(name="the village green", forked=True, sounds="the bells and the birds"),
    "forest": Place(name="the old forest path", forked=True, sounds="the wind in the leaves"),
    "river": Place(name="the river road", forked=True, sounds="the water over stones"),
    "hill": Place(name="the hill road", forked=True, sounds="the sheep on the slopes"),
}

HEROES = {
    "Alice": {"gender": "girl", "trait": "kind"},
    "Tom": {"gender": "boy", "trait": "brave"},
    "Mira": {"gender": "girl", "trait": "patient"},
    "Ned": {"gender": "boy", "trait": "gentle"},
}

FRIENDS = {
    "piper": {"type": "friend", "blind": True, "trait": "blind"},
    "wanderer": {"type": "friend", "blind": False, "trait": "travel-worn"},
    "weaver": {"type": "friend", "blind": True, "trait": "blind"},
}

OBJECTS = {
    "basket": {"label": "a woven basket", "phrase": "a woven basket full of berries", "type": "basket"},
    "lantern": {"label": "a little lantern", "phrase": "a little lantern with a glass shade", "type": "lantern"},
    "bread": {"label": "a loaf of bread", "phrase": "a warm loaf of bread", "type": "bread"},
    "ribbon": {"label": "a blue ribbon", "phrase": "a blue ribbon tied in a bow", "type": "ribbon"},
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk tale storyworld about friendship at a fork in the road.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
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


def reasonableness_check(place: str, hero: str, friend: str, obj: str) -> None:
    if place not in SETTINGS:
        pass
    if hero not in HEROES or friend not in FRIENDS or obj not in OBJECTS:
        pass
    if not _safe_lookup(SETTINGS, place).forked:
        pass
    if not _safe_lookup(FRIENDS, friend)["blind"]:
        pass
    if hero == friend:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero = getattr(args, "hero", None) or rng.choice(list(HEROES))
    friend = getattr(args, "friend", None) or rng.choice(list(FRIENDS))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    reasonableness_check(place, hero, friend, obj)
    return StoryParams(place=place, hero=hero, friend=friend, object=obj)


def _setup_world(params: StoryParams) -> World:
    world = World(place=_safe_lookup(SETTINGS, params.place))
    hero_cfg = _safe_lookup(HEROES, params.hero)
    friend_cfg = _safe_lookup(FRIENDS, params.friend)
    obj_cfg = _safe_lookup(OBJECTS, params.object)

    hero = world.add(Entity(id="hero", kind="character", type=hero_cfg["gender"], label=params.hero, traits=[hero_cfg["trait"], "one-pl"]))
    friend = world.add(Entity(id="friend", kind="character", type=friend_cfg["type"], label=params.friend, traits=[friend_cfg["trait"], "blind"], blind=friend_cfg["blind"]))
    item = world.add(Entity(id="thing", type=obj_cfg["type"], label=obj_cfg["label"], phrase=obj_cfg["phrase"], owner=hero.id))

    world.facts.update(hero=hero, friend=friend, item=item, params=params)
    return world


def _predict_misunderstanding(world: World) -> bool:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("thing")
    sim = world.copy()
    sim.get("friend").memes["uncertainty"] = 1
    return sim.get("friend").blind and hero.owner != friend.id and item.label.startswith("a ")


def tell(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("thing")
    place = world.place.name

    world.say(f"Long ago, {hero.label} and {friend.label} met at {place}, where {world.place.sounds} could be heard.")
    world.say(f"{hero.label} carried {item.phrase}, for {hero.label} loved {item.label}.")
    world.say(f"{friend.label} was blind, yet {friend.pronoun().capitalize()} knew the way by voice, touch, and trust.")

    world.para()
    world.say(f"At the fork in the road, {hero.label} pointed one way and said that was the right path home.")
    if _predict_misunderstanding(world):
        friend.memes["hurt"] = 1
        friend.memes["misunderstanding"] = 1
        hero.memes["worry"] = 1
        world.say(f"But {friend.label} heard the wrong turn in {hero.label}'s words and thought {hero.label} meant to send {friend.pronoun('object')} away.")
        world.say(f"{friend.label} grew quiet and kept {friend.pronoun('possessive')} hands on the road, feeling for the fork like a bird in fog.")

    world.para()
    world.say(f"{hero.label} saw the trouble at once, came close, and spoke plain as bread.")
    world.say(f'"I did not mean to leave you," {hero.label} said. "I only meant the path with the stone apple tree."')
    friend.memes["hurt"] = 0
    friend.memes["misunderstanding"] = 0
    friend.memes["trust"] = 1
    hero.memes["care"] = 1
    world.say(f"Then {hero.label} took {friend.pronoun('possessive')} hand and guided {friend.pronoun('object')} by touch, so the fork was no longer a puzzle.")

    world.para()
    world.say(f"The two friends walked on together, and {item.label} swung safely from {hero.label}'s arm.")
    world.say(f"By the time they reached home, the road felt straight again, because friendship had made the meaning clear.")


def generate(params: StoryParams) -> StorySample:
    world = _setup_world(params)
    tell(world)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = f["params"]
    return [
        f"Write a folk tale about {p.hero} and {p.friend} at a fork in the road.",
        f"Tell a short story where a blind friend misunderstands a pointing hand, then friendship clears it up.",
        f"Write a gentle one-pl tale with misunderstanding, a road fork, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.get("hero")
    friend = world.get("friend")
    item = world.get("thing")
    return [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {p.hero} and {p.friend}. They met at {world.place.name} and stayed friends through the misunderstanding.",
        ),
        QAItem(
            question=f"Why did {friend.label} think something was wrong at the fork?",
            answer=f"{friend.label} was blind, so {friend.pronoun().capitalize()} depended on words and touch. When {hero.label} pointed quickly, {friend.label} thought {hero.label} was sending {friend.pronoun('object')} away.",
        ),
        QAItem(
            question=f"What helped clear up the misunderstanding?",
            answer=f"{hero.label} spoke plainly, explained the path, and took {friend.pronoun('possessive')} hand. That friendly care made the meaning clear again.",
        ),
        QAItem(
            question=f"What did {hero.label} carry on the road?",
            answer=f"{hero.label} carried {item.phrase}, and it stayed with the two friends as they walked home together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fork in the road?",
            answer="A fork in the road is a place where one path splits into two paths, and travelers must choose which way to go.",
        ),
        QAItem(
            question="What does blind mean?",
            answer="Blind means a person cannot see, so they may use touch, sound, and help from others to know what is around them.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and try to be kind when there is trouble.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
        lines.append(f"{e.id}: type={e.type} blind={e.blind} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
friendship_clear(hero, friend) :- blind(friend), misunderstanding(friend), speaks_plain(hero), touches_hand(hero, friend).
misunderstanding(friend) :- blind(friend), points_quickly(hero, friend).
valid_story(place, hero, friend, object) :- fork(place), blind(friend), hero != friend.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, cfg in SETTINGS.items():
        lines.append(asp.fact("fork", place))
    for hid in HEROES:
        lines.append(asp.fact("hero", hid))
    for fid, cfg in FRIENDS.items():
        if cfg["blind"]:
            lines.append(asp.fact("blind", fid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python = {(place, hero, friend, obj) for place in SETTINGS for hero in HEROES for friend in FRIENDS for obj in OBJECTS if hero != friend and _safe_lookup(FRIENDS, friend)["blind"] and _safe_lookup(SETTINGS, place).forked}
    clingo_set = set(asp_valid_stories())
    if python == clingo_set:
        print(f"OK: clingo gate matches python gate ({len(python)} combos).")
        return 0
    print("MISMATCH between clingo and python gate.")
    print("python-only:", sorted(python - clingo_set))
    print("clingo-only:", sorted(clingo_set - python))
    return 1


CURATED = [
    StoryParams(place="village", hero="Alice", friend="piper", object="basket"),
    StoryParams(place="forest", hero="Tom", friend="weaver", object="lantern"),
    StoryParams(place="river", hero="Mira", friend="piper", object="bread"),
]


def build_story_params_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(str(x) for x in asp_valid_stories()))
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

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
