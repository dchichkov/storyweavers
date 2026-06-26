#!/usr/bin/env python3
"""
A small standalone story world: an animal friendship tale about a camera,
a misunderstanding, and a brave act that fixes it.

Premise:
- A little animal loves a camera.
- A friend misreads the camera as something scary or strange.
- Brave, gentle explanation turns the misunderstanding into friendship.

The world is intentionally small and constraint-checked so every generated
story has a clear setup, a tension beat, and a resolution.
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


# ---------------------------------------------------------------------------
# World data
# ---------------------------------------------------------------------------


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
    kind: str = "thing"  # "animal" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    camera: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
    place: str
    afford_camera: bool = True
    light: str = "soft"
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
class Camera:
    label: str
    phrase: str
    flash: bool = True
    shiny: bool = True
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
    hero_trait: str
    friend_trait: str
    camera: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", light="bright"),
    "riverbank": Setting(place="the riverbank", light="sparkling"),
    "treehouse": Setting(place="the treehouse", light="warm"),
}

HEROES = {
    "bunny": ("bunny", "curious"),
    "fox": ("fox", "gentle"),
    "bear": ("bear", "careful"),
    "panda": ("panda", "quiet"),
}

FRIENDS = {
    "kitten": ("kitten", "shy"),
    "duckling": ("duckling", "wobbly"),
    "mouse": ("mouse", "tiny"),
    "puppy": ("puppy", "playful"),
}

CAMERAS = {
    "camera": Camera(label="camera", phrase="a small shiny camera", flash=True, shiny=True),
    "little_camera": Camera(label="camera", phrase="a little blue camera", flash=True, shiny=False),
    "soft_camera": Camera(label="camera", phrase="a soft-looking camera with a round lens", flash=False, shiny=False),
}

HERO_NAMES = ["Milo", "Pip", "Tavi", "Nori", "Juno", "Bibi", "Kiko", "Luna"]
FRIEND_NAMES = ["Pip", "Mimi", "Otto", "Didi", "Toto", "Nina", "Rumi", "Wren"]
TRAITS = ["brave", "kind", "curious", "gentle", "careful", "shy"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place: str, hero: str, friend: str, camera: str) -> bool:
    return place in SETTINGS and hero in HEROES and friend in FRIENDS and camera in CAMERAS


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HEROES:
            for friend in FRIENDS:
                if friend == hero:
                    continue
                for camera in CAMERAS:
                    combos.append((place, hero, friend, camera))
    return combos


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(meadow). place(riverbank). place(treehouse).
hero(bunny). hero(fox). hero(bear). hero(panda).
friend(kitten). friend(duckling). friend(mouse). friend(puppy).
camera(camera). camera(little_camera). camera(soft_camera).

valid(Place, Hero, Friend, Camera) :-
    place(Place), hero(Hero), friend(Friend), camera(Camera), Hero != Friend.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for h in HEROES:
        lines.append(asp.fact("hero", h))
    for f in FRIENDS:
        lines.append(asp.fact("friend", f))
    for c in CAMERAS:
        lines.append(asp.fact("camera", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP matches Python ({len(p)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(p - a))
    print("only in asp:", sorted(a - p))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    hero_type, hero_core_trait = _safe_lookup(HEROES, params.hero)
    friend_type, friend_core_trait = _safe_lookup(FRIENDS, params.friend)
    cam = _safe_lookup(CAMERAS, params.camera)

    hero = world.add(Entity(
        id=params.hero,
        kind="animal",
        type=hero_type,
        label=params.hero,
        traits=["little", params.hero_trait, hero_core_trait],
        meters={"bravery": 0.0, "joy": 0.0},
        memes={"confidence": 0.0, "friendship": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend,
        kind="animal",
        type=friend_type,
        label=params.friend,
        traits=["little", params.friend_trait, friend_core_trait],
        meters={"worry": 0.0, "joy": 0.0},
        memes={"trust": 0.0, "misunderstanding": 0.0},
    ))
    camera = world.add(Entity(
        id="camera",
        kind="thing",
        type="camera",
        label="camera",
        phrase=cam.phrase,
        owner=hero.id,
        meters={"shine": 1.0 if cam.shiny else 0.3},
    ))

    world.facts.update(hero=hero, friend=friend, camera=camera, cam=cam, setting=world.setting)
    return world


def tell_story(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    friend: Entity = _safe_fact(world, world.facts, "friend")
    camera: Entity = _safe_fact(world, world.facts, "camera")
    cam: Camera = _safe_fact(world, world.facts, "cam")
    place = world.setting.place

    world.say(
        f"{hero.id} was a little {hero.type} who loved {camera.phrase}. "
        f"{hero.id} liked to point it at bees, leaves, and puddles so the day could be saved."
    )
    world.say(
        f"One bright afternoon at {place}, {hero.id} met {friend.id}, a little {friend.type} with soft paws and a shy smile."
    )

    world.para()
    hero.meters["bravery"] += 1
    hero.memes["confidence"] += 1
    world.say(
        f"{hero.id} wanted to take a picture, but when {hero.id} raised the {camera.label}, "
        f"{friend.id} stepped back. "
        f'"It has a shiny eye," {friend.id} whispered, thinking the {camera.label} might be a strange animal.'
    )
    friend.memes["misunderstanding"] += 1
    friend.meters["worry"] += 1

    if cam.flash:
        world.say(
            f"When the little flash blinked, {friend.id} yelped and hid behind a tuft of grass."
        )

    world.para()
    hero.meters["bravery"] += 1
    world.say(
        f"{hero.id} did not laugh. Instead, {hero.id} sat down, held the {camera.label} low, and said it was only a camera, "
        f"a tiny machine for keeping happy moments safe."
    )
    world.say(
        f"To show {friend.id}, {hero.id} took a brave photo of a butterfly on a flower, then turned the screen so {friend.id} could see."
    )
    hero.memes["friendship"] += 1
    friend.memes["trust"] += 1
    friend.memes["misunderstanding"] = 0.0
    friend.meters["worry"] = 0.0

    world.para()
    world.say(
        f"{friend.id}'s ears perked up. The {camera.label} was not scary at all; it was a way to remember nice things together."
    )
    world.say(
        f"{friend.id} smiled, stepped closer, and sat beside {hero.id} for another picture. "
        f"This time they both looked at the lens, and the flash felt like a tiny star."
    )
    hero.memes["friendship"] += 1
    friend.memes["joy"] += 1
    hero.meters["joy"] += 1

    world.facts["resolved"] = True
    world.facts["place"] = place


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    cam: Camera = _safe_fact(world, f, "cam")
    return [
        f'Write an animal story for a small child where {hero.id} uses a {cam.label} and {friend.id} first feels unsure, then feels safe.',
        f"Tell a gentle friendship story at {world.setting.place} about {hero.id}, {friend.id}, and a shiny camera.",
        f'Write a short animal story that includes bravery, friendship, and a misunderstanding about a camera.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    cam: Camera = _safe_fact(world, f, "cam")
    return [
        QAItem(
            question=f"What did {hero.id} love carrying around?",
            answer=f"{hero.id} loved carrying a {cam.phrase} and using it to save happy moments.",
        ),
        QAItem(
            question=f"Why did {friend.id} move back when {hero.id} raised the camera?",
            answer=f"{friend.id} misunderstood the shiny camera and thought it might be strange or scary.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery and help {friend.id} feel better?",
            answer=f"{hero.id} stayed calm, explained what the camera was, and took a gentle photo to show it was safe.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The misunderstanding faded, and {hero.id} and {friend.id} ended up smiling together as friends.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a camera for?",
            answer="A camera is for taking pictures so you can remember people, places, and happy moments.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary while staying calm and kind.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people or animals care about each other, help each other, and like being together.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but it is not, and then they learn the real idea.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==",]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a camera, bravery, friendship, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--friend", choices=FRIENDS)
    ap.add_argument("--camera", choices=CAMERAS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "hero", None):
        combos = [c for c in combos if c[1] == getattr(args, "hero", None)]
    if getattr(args, "friend", None):
        combos = [c for c in combos if c[2] == getattr(args, "friend", None)]
    if getattr(args, "camera", None):
        combos = [c for c in combos if c[3] == getattr(args, "camera", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, hero, friend, camera = rng.choice(list(combos))
    hero_trait = rng.choice(TRAITS)
    friend_trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        hero=getattr(args, "name", None) or _safe_lookup(HEROES, hero)[0].capitalize(),
        friend=friend.capitalize() if getattr(args, "friend", None) is None else getattr(args, "friend", None).capitalize(),
        hero_trait=hero_trait,
        friend_trait=friend_trait,
        camera=camera,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, e.meters, e.memes)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="meadow", hero="bunny", friend="kitten", hero_trait="brave", friend_trait="shy", camera="camera"),
            StoryParams(place="riverbank", hero="fox", friend="duckling", hero_trait="gentle", friend_trait="wobbly", camera="little_camera"),
            StoryParams(place="treehouse", hero="bear", friend="mouse", hero_trait="careful", friend_trait="tiny", camera="soft_camera"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
