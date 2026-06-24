#!/usr/bin/env python3
"""
storyworlds/worlds/tortilla_dog_dim_cheetah_moral_value_inner.py
===============================================================

A small adventure storyworld built from the seed words:
tortilla, dog-dim, cheetah.

Premise:
A child-like explorer discovers a missing tortilla at a jungle camp, suspects
a "dog-dim" clue, and follows a cheetah trail to solve the mystery. The story
turns on inner monologue, a moral value choice, and a concrete resolution.

This world supports:
- Moral Value
- Inner Monologue
- Mystery to Solve
- Adventure style

The simulation keeps state in meters (physical quantities) and memes (emotional
/ ethical quantities), then renders prose from the evolving world.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    cheetah: object | None = None
    dog: object | None = None
    hero: object | None = None
    tortilla: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Setting:
    place: str = "the jungle camp"
    mystery_spot: str = "the storage crate"
    trail: str = "a muddy trail"
    afford: set[str] = field(default_factory=lambda: {"search", "follow", "share"})
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
class Clue:
    id: str
    label: str
    hint: str
    trail_text: str
    mystery_kind: str = "mystery"
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
class Goal:
    id: str
    item: str
    moral_value: str
    moral_price: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_nibble(world: World) -> list[str]:
    out: list[str] = []
    tortilla = world.get("tortilla")
    dog = world.get("dog")
    cheetah = world.get("cheetah")
    if tortilla.meters.get("missing", 0) < THRESHOLD:
        return out
    if dog.meters.get("sniffed", 0) >= THRESHOLD and cheetah.meters.get("tracks", 0) >= THRESHOLD:
        sig = ("nibble",)
        if sig not in world.fired:
            world.fired.add(sig)
            tortilla.meters["nibbled"] = 1
            out.append("The missing tortilla had been nibbled, not stolen.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _r_nibble(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def introduce(world: World, hero: Entity, dog: Entity, cheetah: Entity, clue: Clue, goal: Goal) -> None:
    world.say(
        f"{hero.id} was a young explorer at {world.setting.place}, always ready for a small adventure."
    )
    world.say(
        f"Beside {hero.pronoun('object')} wandered {dog.label}, a dog-dim companion who loved sniffing for clues, "
        f"and in the brush ahead there were fresh cheetah tracks."
    )
    world.say(
        f"That morning, one tortilla from the camp basket had vanished, and the whole camp felt like a mystery to solve."
    )
    world.say(
        f'{hero.id} thought, "If I follow the clue and keep my promise to be fair, I can solve this."'
    )


def search(world: World, hero: Entity, dog: Entity, cheetah: Entity, clue: Clue, goal: Goal) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["resolve"] += 1
    dog.meters["sniffed"] = 1
    cheetah.meters["tracks"] = 1
    world.say(
        f"{hero.id} followed {clue.trail_text} from the crate toward the trees."
    )
    world.say(
        f'In {hero.id}\'s inner monologue, a careful thought flickered: "Do not blame the first creature you see. Find the real answer."'
    )
    propagate(world, narrate=False)


def reveal(world: World, hero: Entity, dog: Entity, cheetah: Entity, clue: Clue, goal: Goal) -> None:
    tortilla = world.get("tortilla")
    tortilla.meters["missing"] = 0
    tortilla.meters["found"] = 1
    hero.memes["relief"] += 1
    hero.memes["moral_value"] += 1
    world.say(
        f"At last, {hero.id} found the tortilla tucked under a leaf, warm and dusty, with tiny bite marks."
    )
    world.say(
        f"{hero.id} smiled at {dog.label} and then at the cheetah tracks. The cheetah had only been sniffing around the camp fire ring; it was the crumbs that tempted it."
    )


def choose_wisely(world: World, hero: Entity, dog: Entity, goal: Goal) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f'{hero.id} said, "We should share the food and keep it safe for everyone."'
    )
    world.say(
        f"{hero.id} set the tortilla back into the basket and made a fair rule for the camp: food belongs in the food basket, not on the ground."
    )


def ending(world: World, hero: Entity, dog: Entity, cheetah: Entity) -> None:
    world.say(
        f"By sunset, the camp was calm again. {dog.label} curled up in the shade, the cheetah slipped back into the grass, and {hero.id} felt proud for solving the mystery without blaming anyone."
    )


def tell(setting: Setting, clue: Clue, goal: Goal, hero_name: str = "Maya") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    dog = world.add(Entity(id="dog", kind="character", type="dog", label="the dog-dim dog"))
    cheetah = world.add(Entity(id="cheetah", kind="character", type="cheetah", label="the cheetah"))
    tortilla = world.add(Entity(id="tortilla", type="food", label="tortilla", phrase="a tortilla", owner=hero.id))
    tortilla.meters["missing"] = 1
    world.add(Entity(id="crate", type="container", label="storage crate"))
    world.facts.update(hero=hero, dog=dog, cheetah=cheetah, tortilla=tortilla, clue=clue, goal=goal)
    introduce(world, hero, dog, cheetah, clue, goal)
    world.para()
    search(world, hero, dog, cheetah, clue, goal)
    world.para()
    reveal(world, hero, dog, cheetah, clue, goal)
    choose_wisely(world, hero, dog, goal)
    world.para()
    ending(world, hero, dog, cheetah)
    return world


SETTINGS = {
    "camp": Setting(place="the jungle camp", mystery_spot="the storage crate", trail="a muddy trail"),
}

CLUES = {
    "crumbs": Clue(
        id="crumbs",
        label="crumbs",
        hint="tiny bites",
        trail_text="tiny tortilla crumbs",
        mystery_kind="mystery",
    ),
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        hint="light tracks",
        trail_text="a line of pawprints mixed with dust",
        mystery_kind="mystery",
    ),
}

GOALS = {
    "fairness": Goal(
        id="fairness",
        item="the tortilla",
        moral_value="fairness",
        moral_price="blaming the wrong creature",
    ),
}


@dataclass
class StoryParams:
    setting: str
    clue: str
    goal: str
    name: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, c, g) for s in SETTINGS for c in CLUES for g in GOALS]


KNOWLEDGE = {
    "tortilla": [
        ("What is a tortilla?", "A tortilla is a soft flatbread made from dough. People can fold it, fill it, and eat it."),
    ],
    "dog": [
        ("What does a dog do with its nose?", "A dog uses its nose to sniff scents and follow trails."),
    ],
    "cheetah": [
        ("What is a cheetah?", "A cheetah is a very fast wild cat with spots."),
    ],
    "fairness": [
        ("What does fairness mean?", "Fairness means giving people a fair chance and not blaming someone without a good reason."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is something you do not understand yet, so you look for clues to solve it."),
    ],
    "adventure": [
        ("What is an adventure?", "An adventure is an exciting trip or story where someone goes to explore or solve a problem."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a 3-to-5-year-old where a child at {world.setting.place} solves a mystery to find a missing tortilla.',
        f"Tell a gentle story with inner monologue where {f['hero'].id} follows clue '{f['clue'].trail_text}' and learns a moral value about fairness.",
        f'Write a simple mystery story that includes a dog-dim dog, a cheetah, and a tortilla, ending with a kind choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    return [
        QAItem(
            question=f"What mystery did {hero.id} solve at the camp?",
            answer="The mystery was where the missing tortilla had gone, and the clues led to the answer.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the tortilla?",
            answer="The dog-dim dog helped by sniffing, and the cheetah tracks helped point the way too.",
        ),
        QAItem(
            question=f"What moral value did {hero.id} show?",
            answer="She showed fairness by not blaming the first creature she saw and by sharing the food fairly.",
        ),
        QAItem(
            question=f"What did {hero.id}'s inner monologue say?",
            answer="Her inner monologue told her to be careful, follow the clues, and find the real answer before judging anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["tortilla", "dog", "cheetah", "fairness", "mystery", "adventure"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "goal", None) is None or c[2] == getattr(args, "goal", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, clue, goal = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        clue=clue,
        goal=goal,
        name=getattr(args, "name", None) or "Maya",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(CLUES, params.clue), _safe_lookup(GOALS, params.goal), params.name)
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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: tortilla, dog-dim, cheetah, and a mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--name")
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


def _asp_import():
    import asp
    return asp


ASP_RULES = r"""
mystery_to_solve(S) :- setting(S), clue(C), goal(G).
moral_value(V) :- goal(fairness), V = fairness.
"""
def asp_facts() -> str:
    asp = _asp_import()
    lines = [asp.fact("setting", s) for s in SETTINGS]
    lines += [asp.fact("clue", c) for c in CLUES]
    lines += [asp.fact("goal", g) for g in GOALS]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    asp = _asp_import()
    model = asp.one_model(asp_program("#show mystery_to_solve/1.\n#show moral_value/1."))
    atoms_mystery = asp.atoms(model, "mystery_to_solve")
    atoms_moral = asp.atoms(model, "moral_value")
    ok = bool(atoms_mystery) and bool(atoms_moral)
    print("OK" if ok else "MISMATCH", ": ASP rules are present.")
    return 0 if ok else 1


def valid_story_choice() -> tuple[str, str, str]:
    return next(iter(valid_combos()))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_to_solve/1.\n#show moral_value/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show mystery_to_solve/1.\n#show moral_value/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(setting=s, clue=c, goal=g, name="Maya")) for s, c, g in valid_combos()]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
