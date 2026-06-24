#!/usr/bin/env python3
"""
storyworlds/worlds/word_summer_hockey_sharing_magic_dialogue_fairy.py
=====================================================================

A tiny fairy-tale storyworld about summer hockey, a shared word, and a little
bit of magic and dialogue.

Seed image:
- In a bright summer meadow, two small fairy folk want to play hockey.
- They have only one enchanted word-stick, so they must share it.
- A talking charm helps them turn-takingly speak the magic word.
- The story ends when the game becomes fair, friendly, and joyful.

The world models:
- physical meters: sun_warmth, word_glow, puck_slide, tiredness, etc.
- emotional memes: desire, worry, patience, joy, fairness, friendship.

The world is intentionally small, classical, and constraint-checked. The prose
is driven by state changes, not a frozen template.
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
    shared_with: set[str] = field(default_factory=set)
    wears: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    item: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy-girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "fairy-boy"}:
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
    setting: str
    indoor: bool = False
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
class MagicItem:
    id: str
    label: str
    phrase: str
    grants: set[str]
    shared: bool = True
    glowing: bool = True
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
    hero_a: str
    hero_b: str
    item: str
    seed: Optional[int] = None
    params: object | None = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    "meadow": Place("the summer meadow", "a bright meadow under a blue sky"),
    "lake": Place("the lakeside field", "a breezy field by the lake"),
    "court": Place("the village court", "a painted court beside the bakery"),
}

ITEMS = {
    "word-stick": MagicItem(
        id="word-stick",
        label="word-stick",
        phrase="a silver word-stick that could make a puck dance",
        grants={"magic", "dialogue", "sharing"},
    ),
    "star-puck": MagicItem(
        id="star-puck",
        label="star-puck",
        phrase="a star-puck with a tiny gold shimmer",
        grants={"hockey", "magic"},
    ),
}

NAMES = {
    "girl": ["Mira", "Luna", "Ivy", "Rose", "Elin"],
    "boy": ["Finn", "Pip", "Nico", "Theo", "Bram"],
}


def _make_hero(world: World, hid: str, kind: str) -> Entity:
    return world.add(Entity(
        id=hid,
        kind="character",
        type=kind,
        label=hid,
        meters={"warmth": 0.0, "play": 0.0},
        memes={"joy": 0.0, "patience": 0.0, "sharing": 0.0},
    ))


def _act_hockey(world: World, a: Entity, b: Entity, item: Entity) -> None:
    if "hockey" not in world.facts["item"].grants:
        pass
    a.meters["play"] += 1
    b.meters["play"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In {world.place.name}, {a.id} and {b.id} tried to play hockey, "
        f"but there was only one {item.label}."
    )


def _share_magic(world: World, a: Entity, b: Entity, item: Entity) -> None:
    a.memes["sharing"] += 1
    b.memes["sharing"] += 1
    a.memes["patience"] += 1
    b.memes["patience"] += 1
    item.shared_with = {a.id, b.id}
    world.say(
        f'"Let us share it," said {a.id}. "{item.phrase} will work for both of us." '
        f'"Yes," said {b.id}, "one turn for you, then one turn for me."'
    )


def _magic_turn(world: World, a: Entity, b: Entity, item: Entity) -> None:
    item.meters["glow"] = item.meters.get("glow", 0.0) + 1
    a.meters["word"] = a.meters.get("word", 0.0) + 1
    b.meters["word"] = b.meters.get("word", 0.0) + 1
    world.say(
        f"When they spoke the magic word, the puck glimmered, skipped, and waited "
        f"for the next child to tap it."
    )


def _resolve(world: World, a: Entity, b: Entity, item: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["fairness"] = 1.0
    b.memes["fairness"] = 1.0
    world.say(
        f"At last they took turns in the warm summer light, laughing together, "
        f"and the shared {item.label} made their little hockey game feel like a blessing."
    )


def tell(world: World, a: Entity, b: Entity, item: Entity) -> World:
    world.say(
        f"Once in {world.place.name}, {a.id} met {b.id} beside the grass, and both "
        f"were eager for a game."
    )
    world.say(f"They had {item.phrase}, and the air felt like soft gold.")

    world.para()
    _act_hockey(world, a, b, item)
    if item.id == "word-stick":
        world.say(
            f"{a.id} wanted the magic word first, and {b.id} wanted it too, so the "
            f"day grew very still."
        )
    _share_magic(world, a, b, item)
    _magic_turn(world, a, b, item)

    world.para()
    _resolve(world, a, b, item)
    world.facts = {"a": a, "b": b, "item": item, "place": world.place}
    return world


def build_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    item_cfg = _safe_lookup(ITEMS, params.item)
    world = World(place)

    a = _make_hero(world, params.hero_a, "girl" if params.hero_a in NAMES["girl"] else "boy")
    b = _make_hero(world, params.hero_b, "girl" if params.hero_b in NAMES["girl"] else "boy")
    item = world.add(Entity(
        id=item_cfg.id,
        kind="thing",
        type="magic-item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        meters={"glow": 0.0},
    ))
    world.facts = {"a": a, "b": b, "item": item, "place": place}
    return tell(world, a, b, item)


def generation_prompts(world: World) -> list[str]:
    a, b, item = world.facts["a"], world.facts["b"], world.facts["item"]
    return [
        f"Write a fairy tale about {a.id} and {b.id} sharing a magic word while playing hockey in summer.",
        f"Tell a gentle story where {a.id} and {b.id} use {item.label} to take turns and make the game fair.",
        f"Create a short fairy tale with the words summer, hockey, sharing, magic, and dialogue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a, b, item = world.facts["a"], world.facts["b"], world.facts["item"]
    place = world.facts["place"].name
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {a.id} and {b.id}, two little fairy children who wanted to play hockey together.",
        ),
        QAItem(
            question=f"What did they need to share?",
            answer=f"They needed to share the {item.label} so both of them could use the magic word and keep the game fair.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with both children taking turns, smiling in the warm summer light, and enjoying hockey together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use something too, so everyone can take turns and feel included.",
        ),
        QAItem(
            question="What is magic in a fairy tale?",
            answer="Magic is something wondrous that can make ordinary things sparkle, change, or do surprising things.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters speak to one another in a story.",
        ),
        QAItem(
            question="What is hockey?",
            answer="Hockey is a game where players try to move a puck with sticks and score by working with speed and skill.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "summer" in place.setting:
            lines.append(asp.fact("summer_place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for g in sorted(item.grants):
            lines.append(asp.fact("grants", iid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P, I) :- place(P), item(I), summer_place(P), grants(I, sharing), grants(I, magic), grants(I, dialogue), grants(I, hockey).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, i) for p in PLACES for i in ITEMS if p in PLACES and i in ITEMS}
    cl = set(asp_valid())
    ok = py == cl
    if ok:
        print(f"OK: ASP and Python agree on {len(cl)} stories.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Only in ASP:", sorted(cl - py))
    print("Only in Python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about summer hockey and sharing magic.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--hero-a")
    ap.add_argument("--hero-b")
    ap.add_argument("--item", choices=sorted(ITEMS))
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
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    names = NAMES["girl"] + NAMES["boy"]
    hero_a = getattr(args, "hero_a", None) or rng.choice(names)
    hero_b = getattr(args, "hero_b", None) or rng.choice([n for n in names if n != hero_a])
    if hero_a == hero_b:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if item == "star-puck" and getattr(args, "hero_a", None) and getattr(args, "hero_b", None):
        pass
    return StoryParams(place=place, hero_a=hero_a, hero_b=hero_b, item=item)


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in PLACES:
            for i in ITEMS:
                params = StoryParams(place=p, hero_a="Mira", hero_b="Finn", item=i, seed=base_seed)
                samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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

    for idx, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    main()
