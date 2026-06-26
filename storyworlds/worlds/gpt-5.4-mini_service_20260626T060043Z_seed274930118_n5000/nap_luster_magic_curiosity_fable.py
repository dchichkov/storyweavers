#!/usr/bin/env python3
"""
Standalone storyworld: nap, luster, magic, curiosity, fable.

A small fable-like domain where a curious child, a shining charm, and a
well-timed nap change what magic can do.
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
# World model
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
    keeper: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Setting:
    place: str = "the hill of lantern grass"
    indoor: bool = False
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
class Magic:
    id: str
    label: str
    verb: str
    glow: str
    gift: str
    cost: str
    can_sleep: bool = False
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
class Curiosity:
    id: str
    urge: str
    poke: str
    quest: str
    keyword: str = "curiosity"
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting("the meadow"),
    "orchard": Setting("the orchard"),
    "lanternfield": Setting("the lantern field"),
}

MAGICS = {
    "glowseed": Magic(
        id="glowseed",
        label="a glowseed",
        verb="wake up the tiny lights",
        glow="a soft gold luster",
        gift="made the path shimmer kindly",
        cost="needed a quiet mind",
        can_sleep=True,
    ),
    "mirthglass": Magic(
        id="mirthglass",
        label="a round mirthglass",
        verb="show bright truths",
        glow="a clear silver luster",
        gift="showed hidden things on the grass",
        cost="liked to slip away when children were too restless",
        can_sleep=False,
    ),
    "sunthread": Magic(
        id="sunthread",
        label="a sunthread ribbon",
        verb="catch afternoon sparkle",
        glow="a warm honey luster",
        gift="wrapped the air in shine",
        cost="worked best after a calm pause",
        can_sleep=True,
    ),
}

CURIOSITIES = {
    "birdsong": Curiosity(
        id="birdsong",
        urge="listen closely to the birds",
        poke="follow the song",
        quest="learn where the melody began",
    ),
    "fireflies": Curiosity(
        id="fireflies",
        urge="count the blinking fireflies",
        poke="chase each little light",
        quest="see why they gathered",
    ),
    "stone": Curiosity(
        id="stone",
        urge="turn over a smooth stone",
        poke="peek under it",
        quest="find the tiny secret beneath",
    ),
}

HERO_NAMES = ["Mina", "Lio", "Nori", "Pip", "Ari", "Tavi", "Esme", "Rowan"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["curious", "gentle", "brave", "bright", "patient"]


@dataclass
class StoryParams:
    setting: str
    magic: str
    curiosity: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Fable logic
# ---------------------------------------------------------------------------
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


def _sleepy(world: World, hero: Entity) -> None:
    hero.meters["sleep"] = hero.meters.get("sleep", 0.0) + 1
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1


def _curious(world: World, hero: Entity, curiosity: Curiosity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {curiosity.urge}, because {hero.pronoun('possessive')} "
        f"mind was full of questions."
    )


def _magic_flicker(world: World, hero: Entity, magic: Magic) -> None:
    hero.meters["luster"] = hero.meters.get("luster", 0.0) + 1
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1
    world.say(
        f"{magic.label} gave off {magic.glow}, and the world around {hero.id} seemed to listen."
    )


def _rest_turn(world: World, hero: Entity, magic: Magic) -> None:
    hero.meters["nap"] = hero.meters.get("nap", 0.0) + 1
    hero.memes["rest"] = hero.memes.get("rest", 0.0) + 1
    world.say(
        f"So {hero.id} sat down for a small nap beneath the quiet sky."
    )
    if magic.can_sleep:
        world.say(
            f"While {hero.id} slept, {magic.label} grew steadier, and its shine became easier to hold."
        )
    else:
        world.say(
            f"While {hero.id} rested, even {magic.label} stopped wobbling and remembered its shape."
        )


def _resolution(world: World, hero: Entity, magic: Magic, curiosity: Curiosity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["wisdom"] = hero.memes.get("wisdom", 0.0) + 1
    world.say(
        f"When {hero.id} woke, {magic.label} was brighter than before, "
        f"and {hero.id} finally understood that {curiosity.quest}."
    )
    world.say(
        f"From then on, {hero.id} learned that curiosity is fine, but a little rest can make magic last."
    )


def tell(setting: Setting, magic: Magic, curiosity: Curiosity,
         name: str = "Mina", gender: str = "girl", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, meters={}, memes={}))
    hero.memes["curiosity"] = 1.0
    hero.memes["wonder"] = 0.5
    hero.traits = [trait]  # type: ignore[attr-defined]

    world.say(
        f"{hero.id} was a little {trait} {gender} who lived near {setting.place}."
    )
    world.say(
        f"{hero.id} carried {magic.label}, a charm with {magic.glow}, and loved to see what it would do."
    )

    world.para()
    world.say(
        f"One day, {hero.id} followed a bit of {curiosity.keyword} around {setting.place}, "
        f"hoping to {curiosity.poke}."
    )
    _curious(world, hero, curiosity)
    _magic_flicker(world, hero, magic)
    world.say(
        f"But {magic.label} {magic.cost}, and the shine grew thin whenever {hero.id} hurried too much."
    )

    world.para()
    world.say(
        f"{hero.id} grew still and listened to the wind."
    )
    _rest_turn(world, hero, magic)

    world.para()
    _resolution(world, hero, magic, curiosity)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(meadow).
setting(orchard).
setting(lanternfield).

magic(glowseed).
magic(mirthglass).
magic(sunthread).

curiosity(birdsong).
curiosity(fireflies).
curiosity(stone).

can_sleep(glowseed).
can_sleep(sunthread).

luster(glowseed,gold).
luster(mirthglass,silver).
luster(sunthread,honey).

compatible(S, M, C) :- setting(S), magic(M), curiosity(C).
sleep_helpful(M) :- can_sleep(M).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MAGICS.items():
        lines.append(asp.fact("magic", mid))
        lines.append(asp.fact("luster", mid, m.glow))
        if m.can_sleep:
            lines.append(asp.fact("can_sleep", mid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    asp_set = set(asp.atoms(model, "compatible"))
    py_set = set((s, m, c) for s in SETTINGS for m in MAGICS for c in CURIOSITIES)
    if asp_set == py_set:
        print(f"OK: clingo gate matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if asp_set - py_set:
        print("  only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print("  only in Python:", sorted(py_set - asp_set))
    return 1


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    magic: Magic = _safe_fact(world, f, "magic")  # type: ignore[assignment]
    curiosity: Curiosity = _safe_fact(world, f, "curiosity")  # type: ignore[assignment]
    return [
        f'Write a short fable for a child about {hero.id}, {magic.label}, and {curiosity.keyword}.',
        f"Tell a gentle story where {hero.id} learns that {magic.label} grows clearer after a nap.",
        f'Write a story that uses the words "nap" and "luster" and ends with a wise lesson.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    magic: Magic = _safe_fact(world, f, "magic")  # type: ignore[assignment]
    curiosity: Curiosity = _safe_fact(world, f, "curiosity")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little curious child at {setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} carry?",
            answer=f"{hero.id} carried {magic.label}, which gave off {magic.glow}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do because of {curiosity.keyword}?",
            answer=f"{hero.id} wanted to {curiosity.urge}, but first had to learn patience.",
        ),
        QAItem(
            question=f"What helped the magic become steadier?",
            answer=f"A small nap helped {magic.label} grow steadier and brighter.",
        ),
        QAItem(
            question=f"What lesson did the story end with?",
            answer="The story ended with the lesson that curiosity is good, but rest can make magic last.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    magic: Magic = _safe_fact(world, f, "magic")  # type: ignore[assignment]
    return [
        QAItem(
            question="What is a nap?",
            answer="A nap is a short sleep taken during the day to rest your body and mind.",
        ),
        QAItem(
            question="What is luster?",
            answer="Luster is the soft shine a surface or object gives off when light touches it.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know more, ask questions, and learn what is hidden.",
        ),
        QAItem(
            question=f"Why is {magic.label} special?",
            answer=f"{magic.label} is special because it has {magic.glow} and can change how the world feels.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: nap, luster, magic, curiosity, fable.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    magic = getattr(args, "magic", None) or rng.choice(list(MAGICS))
    curiosity = getattr(args, "curiosity", None) or rng.choice(list(CURIOSITIES))
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, magic=magic, curiosity=curiosity, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(MAGICS, params.magic),
        _safe_lookup(CURIOSITIES, params.curiosity),
        name=params.name,
        gender=params.gender,
        trait=params.trait,
    )
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
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.kind, e.type, e.meters, e.memes)
    if qa:
        print("\n== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(setting="meadow", magic="glowseed", curiosity="fireflies", name="Mina", gender="girl", trait="curious"),
    StoryParams(setting="orchard", magic="sunthread", curiosity="birdsong", name="Lio", gender="boy", trait="gentle"),
    StoryParams(setting="lanternfield", magic="mirthglass", curiosity="stone", name="Nori", gender="girl", trait="bright"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

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
