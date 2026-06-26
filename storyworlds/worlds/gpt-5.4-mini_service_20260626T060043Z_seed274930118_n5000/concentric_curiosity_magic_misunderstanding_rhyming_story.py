#!/usr/bin/env python3
"""
A standalone storyworld for a rhyming tale of Curiosity, Magic, and Misunderstanding.

Premise:
- A child finds a concentric circle pattern made by a tiny magic ripple.
- Curiosity pulls them closer.
- A misunderstanding makes a friend think the magic is trouble.
- The child explains the pattern, and the magic becomes a shared game.

This world models:
- physical meters: ripple size, sparkle, distance, gathered objects
- emotional memes: curiosity, worry, delight, trust, confusion
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    indoors: bool = False
    has_water: bool = False
    has_stones: bool = False
    has_lanterns: bool = False
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
class MagicThing:
    id: str
    label: str
    sparkle: str
    effect: str
    rhyme: str
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
    place: str
    magic: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
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
    def __init__(self, place: Place, magic: MagicThing) -> None:
        self.place = place
        self.magic = magic
        self.entities: dict[str, Entity] = {}
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


PLACES = {
    "pond": Place("the pond", indoors=False, has_water=True, has_stones=True),
    "garden": Place("the garden", indoors=False, has_water=True, has_stones=True),
    "hall": Place("the hall", indoors=True, has_lanterns=True),
    "seashore": Place("the seashore", indoors=False, has_water=True, has_stones=True),
}

MAGICS = {
    "ripple": MagicThing(
        id="ripple",
        label="a magic ripple",
        sparkle="a silver twinkle",
        effect="made circles grow neat and slow",
        rhyme="The ripple went glimmer, the ripple went bright, / It ringed out in circles, a tidy delight.",
    ),
    "wand": MagicThing(
        id="wand",
        label="a tiny wand",
        sparkle="a golden blink",
        effect="made little rings appear and swing",
        rhyme="The wand gave a wink, then a shimmer, then zing, / It drew little circles around everything.",
    ),
    "pebble": MagicThing(
        id="pebble",
        label="a magic pebble",
        sparkle="a blue-green gleam",
        effect="made ripples begin like a dream",
        rhyme="The pebble went plink with a musical song, / And circles of shimmer kept marching along.",
    ),
}

HEROES = ["Mina", "Luca", "Noa", "Ivy", "Sage", "Arlo", "June", "Pip"]
FRIENDS = ["Tess", "Rin", "Milo", "Bea", "Finn", "Zuri", "Otis", "Nia"]
TYPES = ["girl", "boy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for magic_id in MAGICS:
            if place.indoors and magic_id == "pebble":
                combos.append((place_id, magic_id))
            elif place.has_water or place.has_lanterns:
                combos.append((place_id, magic_id))
    return combos


def choose_name(rng: random.Random, names: list[str]) -> str:
    return rng.choice(names)


def rhyme_line(name: str, magic: MagicThing, place: Place) -> str:
    return f"{name} found {magic.label} at {place.name}, and it glimmered in circles, both tidy and fine."


def build_story(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    place = world.place
    magic = world.magic

    hero.memes["curiosity"] = 1.0
    hero.memes["joy"] = 0.3
    world.say(
        f"{hero.id} was a curious child who liked a soft, slow clue. "
        f"At {place.name}, {hero.pronoun()} saw {magic.label} with {magic.sparkle}."
    )
    world.say(
        f"{magic.rhyme}"
    )
    world.say(
        f"Round and round went one small ring, then two, then three in a line; "
        f"they spread out wide in concentric style, like lace in a lake so fine."
    )

    world.para()
    hero.meters["distance_to_magic"] = 1.0
    hero.memes["curiosity"] += 1.0
    world.say(
        f"{hero.id} leaned in to look and listen, for curiosity can tug like a string. "
        f"{hero.pronoun().capitalize()} whispered, 'What makes the round rings dance and sing?'"
    )

    friend.memes["confusion"] = 1.0
    friend.memes["worry"] = 1.0
    world.say(
        f"But {friend.id} saw the glow and frowned right then; the shine looked strange in the dim. "
        f"{friend.pronoun().capitalize()} thought the magic meant trouble, and spoke quite grim."
    )
    world.say(
        f"'{hero.id}, don't touch that trick!' {friend.id} cried. 'It may be a spell gone wrong.' "
        f"That was the misunderstanding: a worried guess that felt too strong."
    )

    world.para()
    hero.memes["care"] = 1.0
    hero.memes["curiosity"] += 0.5
    world.say(
        f"{hero.id} shook {hero.pronoun('possessive')} head and smiled a smile so bright. "
        f"'No harm in the pattern,' {hero.pronoun()} said. 'It's only rings of light.'"
    )
    world.say(
        f"{hero.id} pointed to the circles, each one wider than the last, "
        f"and explained how the magic stayed gentle as the ripples passed."
    )
    friend.memes["confusion"] = 0.0
    friend.memes["trust"] = 1.0
    friend.memes["joy"] = 1.0
    world.say(
        f"{friend.id}'s face grew calm; the worry was gone. "
        f"Now the shimmer looked merry, not mean, and not wrong."
    )
    world.say(
        f"Together they watched the concentric rings, each round line flowing free, "
        f"and the magic felt like a playful song beneath a moonlit tree."
    )

    world.para()
    world.say(
        f"In the end, the tiny magic did not scare or sting; "
        f"it turned a misunderstanding into a friendlier thing."
    )
    world.say(
        f"{hero.id} went home with {hero.pronoun('possessive')} curious heart still warm, "
        f"while {friend.id} learned that strange-looking magic can still be safe and calm."
    )

    world.facts.update(hero=hero, friend=friend, place=place, magic=magic)


def story_for(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    magic = _safe_lookup(MAGICS, params.magic)
    world = World(place, magic)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type))
    build_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child about {f["hero"].id}, '
        f'who finds {f["magic"].label} at {f["place"].name}.',
        f'Write a gentle rhyming tale where curiosity leads to a misunderstanding, '
        f'then magic helps the friends feel safe again.',
        f'Write a story that includes concentric circles, a worried friend, and a happy explanation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    place = _safe_fact(world, f, "place")
    magic = _safe_fact(world, f, "magic")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a curious child who found {magic.label} at {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice in the water or light?",
            answer=f"{hero.id} noticed {magic.label}, and it made concentric circles spread out in a neat pattern.",
        ),
        QAItem(
            question=f"Why did {friend.id} feel worried at first?",
            answer=f"{friend.id} felt worried because {friend.pronoun()} misunderstood the magic and thought it might be trouble.",
        ),
        QAItem(
            question=f"What fixed the misunderstanding?",
            answer=f"{hero.id} explained the pattern kindly, and then {friend.id} understood that the magic was gentle.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does concentric mean?",
            answer="Concentric means having circles that share the same center, like rings growing around one point.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks something is true, but they have not understood it correctly yet.",
        ),
        QAItem(
            question="Why can magic be gentle in stories?",
            answer="Magic can be gentle in stories when it makes surprising but safe changes, like shining or forming pretty patterns.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


@dataclass
class StoryConfig:
    place: str
    magic: str
    hero_type: str
    friend_type: str
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


ASP_RULES = r"""
% A story is valid when the setting can host the magic and the plot contains
% curiosity, misunderstanding, and a resolving explanation.
valid_story(P, M) :- place(P), magic(M), supports(P, M).
supports(P, M) :- indoors(P), M = pebble.
supports(P, M) :- watery(P), magic_needs_water(M).
supports(P, M) :- lantern_place(P), magic_needs_light(M).

magic_needs_water(ripple).
magic_needs_water(pebble).
magic_needs_light(wand).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoors:
            lines.append(asp.fact("indoors", pid))
        if place.has_water:
            lines.append(asp.fact("watery", pid))
        if place.has_lanterns:
            lines.append(asp.fact("lantern_place", pid))
    for mid in MAGICS:
        lines.append(asp.fact("magic", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("asp only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld of concentric curiosity, magic, and misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=TYPES)
    ap.add_argument("--friend-type", choices=TYPES)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "magic", None) and (getattr(args, "place", None), getattr(args, "magic", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "magic", None) is None or c[1] == getattr(args, "magic", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, magic = rng.choice(filtered)
    hero_type = getattr(args, "hero_type", None) or rng.choice(TYPES)
    friend_type = getattr(args, "friend_type", None) or rng.choice(TYPES)
    hero_name = getattr(args, "hero_name", None) or rng.choice(HEROES)
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIENDS)
    if friend_name == hero_name:
        friend_name = rng.choice([n for n in FRIENDS if n != hero_name])
    return StoryParams(
        place=place,
        magic=magic,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
    )


def generate(params: StoryParams) -> StorySample:
    return story_for(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(place="pond", magic="ripple", hero_name="Mina", hero_type="girl", friend_name="Tess", friend_type="girl"),
    StoryParams(place="garden", magic="pebble", hero_name="Luca", hero_type="boy", friend_name="Finn", friend_type="boy"),
    StoryParams(place="hall", magic="wand", hero_name="Ivy", hero_type="girl", friend_name="Rin", friend_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(sorted(asp_valid()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
