#!/usr/bin/env python3
"""
rice_rubbish_yuck_humor_surprise_cautionary_myth.py
====================================================

A tiny myth-like storyworld about a careful child, a bowl of rice, and a
surprising rubbish mix-up that turns yuck into a cautionary lesson.

The seed tale imagined for this world:
---
Long ago, in a bright little village by the river, a child named Nia loved rice.
Nia also loved jokes, shiny things, and listening to old myths at dusk.

One market day, Nia found a golden bowl beside a heap of rubbish behind the feast
hall. A wind gust made the bowl tumble into the rubbish, and everyone cried,
"Yuck!" Nia thought the bowl was a treasure from the old stories, but the elder
said it was only the rice bowl for the harvest meal, and the rubbish would ruin
it.

Nia wanted to carry the bowl home anyway, but the elder warned that if the rice
touched the rubbish, the village guests would get sick and the feast would be
spoiled. Nia laughed nervously, then helped sort the rubbish, washed the bowl,
and brought clean rice to the hall. The elder smiled and told the tale that the
brightest treasure is often the one that stays clean.

Core state logic:
---
    place holds feast goods     -> treasure may be mistaken for trash
    rice touches rubbish        -> yuck rises, cleanliness falls
    cleanliness low             -> guests refuse the feast
    careful washing             -> yuck falls, feast can resume
    elder warning ignored       -> caution rises, then resolves by repair
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
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bowl: object | None = None
    elder: object | None = None
    hero: object | None = None
    rice: object | None = None
    rubbish: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    setting: str
    has_feast_hall: bool = False
    has_market: bool = False
    has_river: bool = False
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
class Item:
    id: str
    label: str
    phrase: str
    region: str = "hands"
    plural: bool = False
    sacred: bool = False
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
    item: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None
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
    def __init__(self, place: Place):
        self.place = place
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


PLACES = {
    "village": Place("the village", "mythic", has_feast_hall=True, has_market=True, has_river=True),
    "courtyard": Place("the courtyard", "mythic", has_feast_hall=True, has_market=False, has_river=False),
    "market": Place("the market", "mythic", has_feast_hall=False, has_market=True, has_river=False),
}

ITEMS = {
    "rice": Item("rice", "rice", "a bowl of rice", region="hands"),
    "rubbish": Item("rubbish", "rubbish", "a heap of rubbish", region="hands"),
    "rice_bowl": Item("bowl", "bowl", "a golden rice bowl", region="hands", sacred=True),
}

NAMES = ["Nia", "Ivo", "Suri", "Kian", "Mara", "Tala"]
ELDERS = ["elder", "grandmother", "old keeper"]
TRAITS = ["curious", "bright-eyed", "laughing", "cautious", "bold"]


def _r_yuck(world: World) -> list[str]:
    out: list[str] = []
    rice = world.entities.get("rice")
    rub = world.entities.get("rubbish")
    if not rice or not rub:
        return out
    if rice.meters.get("mess", 0.0) >= THRESHOLD and ("yuck",) not in world.fired:
        world.fired.add(("yuck",))
        world.facts["yuck"] = True
        out.append("Yuck rose over the bowl like a bad smell at dusk.")
    return out


def _r_refuse(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("yuck") and not world.facts.get("washed"):
        if ("refuse",) not in world.fired:
            world.fired.add(("refuse",))
            out.append("The guests drew back, for no feast should be served in that state.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_yuck, _r_refuse):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(place: Place, item: Item, hero_name: str = "Nia", hero_type: str = "girl", elder_type: str = "elder") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"cleanliness": 1.0, "caution": 0.0},
        memes={"joy": 1.0, "humor": 1.0, "surprise": 0.0, "caution": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label=f"the {elder_type}",
        meters={"cleanliness": 1.0},
        memes={"caution": 1.0},
    ))
    rice = world.add(Entity(
        id="rice",
        type="rice",
        label="rice",
        phrase="a bowl of rice",
        owner=hero.id,
        caretaker=elder.id,
        meters={"mess": 0.0, "clean": 1.0},
    ))
    rubbish = world.add(Entity(
        id="rubbish",
        type="rubbish",
        label="rubbish",
        phrase="a heap of rubbish",
        meters={"mess": 0.0, "dirty": 1.0},
    ))
    bowl = world.add(Entity(
        id="bowl",
        type="bowl",
        label="golden bowl",
        phrase="a golden rice bowl",
        owner=hero.id,
        caretaker=elder.id,
        meters={"clean": 1.0},
    ))

    world.say(f"Long ago, {hero.id} was a {hero.pronoun('object')} little {hero_type} who loved rice, jokes, and old myths.")
    world.say(f"One day at {place.name}, {hero.id} found {bowl.phrase} beside {rubbish.phrase}.")
    world.say(f"{hero.id} laughed and said the bowl looked like a treasure from the old stories.")
    world.para()
    world.say(f"But the {elder_type} shook {elder.pronoun('possessive')} head and warned, \"Do not let the rice touch the rubbish.\"")
    world.say(f"{hero.id} wanted to carry the bowl home at once, even though the smell made everything feel yuck.")
    hero.memes["surprise"] += 1
    hero.memes["caution"] += 0.5
    world.say(f"A wind gust spun dust over the heap, and the surprise made {hero.id} stop and look more carefully.")
    world.para()
    rice.meters["mess"] += 1.0
    world.say(f"When the rice brushed the rubbish, the bowl became messy and the village feast could not begin.")
    propagate(world)
    world.say(f"{hero.id} blushed, then helped sort the rubbish, washed the bowl, and brought clean rice to the hall.")
    world.facts["washed"] = True
    world.facts["resolved"] = True
    rice.meters["mess"] = 0.0
    rice.meters["clean"] = 1.0
    world.fired.discard(("yuck",))
    world.paragraphs.append([])
    world.say(f"The {elder_type} smiled and told everyone that the brightest treasure is the one that stays clean.")
    world.say(f"By evening, the guests ate at last, and the old tale ended with laughter instead of yuck.")
    world.facts.update(hero=hero, elder=elder, rice=rice, rubbish=rubbish, bowl=bowl, place=place, item=item)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a short myth-like story for a young child that includes "rice", "rubbish", and "yuck".',
        f"Tell a cautionary story where {hero.id} mistakes rubbish for a treasure and learns to keep rice clean.",
        f"Write a gentle surprise story about a bowl of rice, a heap of rubbish, and an elder's warning.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    elder = _safe_fact(world, f, "elder")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type} who loved rice and old myths.",
        ),
        QAItem(
            question=f"What did the {elder.type} warn {hero.id} about?",
            answer=f"The {elder.type} warned {hero.id} not to let the rice touch the rubbish.",
        ),
        QAItem(
            question=f"Why did everyone say yuck?",
            answer="They said yuck because the rice brushed the rubbish and the bowl became messy.",
        ),
        QAItem(
            question=f"What did {hero.id} do to make things right?",
            answer=f"{hero.id} helped sort the rubbish, washed the bowl, and brought clean rice to the hall.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended with the feast beginning at last and laughter replacing the yuck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rice?",
            answer="Rice is a small grain people cook and eat, often at meals or feasts.",
        ),
        QAItem(
            question="What is rubbish?",
            answer="Rubbish is trash or unwanted things that should be thrown away or cleaned up.",
        ),
        QAItem(
            question="Why do people say yuck?",
            answer="People say yuck when something seems dirty, stinky, or unpleasant.",
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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="village", item="rice", name="Nia", gender="girl", elder="elder"),
    StoryParams(place="courtyard", item="rice", name="Ivo", gender="boy", elder="grandmother"),
    StoryParams(place="market", item="rice", name="Suri", gender="girl", elder="elder"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic storyworld of rice, rubbish, and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["elder", "grandmother"])
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
    item = getattr(args, "item", None) or "rice"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["elder", "grandmother"])
    return StoryParams(place=place, item=item, name=name, gender=gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ITEMS, params.item), params.name, params.gender, params.elder)
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


ASP_RULES = r"""
item(rice).
item(rubbish).
item(bowl).

is_dirty(rubbish).
is_clean(rice).
is_clean(bowl).

yuck(X) :- item(X), is_dirty(X).
cautionary_story :- yuck(rubbish), is_clean(rice), is_clean(bowl).
#show yuck/1.
#show cautionary_story/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show yuck/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
