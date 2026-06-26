#!/usr/bin/env python3
"""
A standalone fairy-tale storyworld about a buffalo, a hundred, and a stammer.

Seed tale:
---
Once, in a windy meadow beside a silver river, a little buffalo named Bruno
lived with a kind grandmother. Bruno loved to count things because counting made
the world feel safe. One day the grandmother gave Bruno a golden pouch and said
it held a hundred bright berries for the queen's supper.

Bruno set off through the trees, but the path led to a narrow bridge guarded by
a worried fox. The fox said the queen had ordered the berries to arrive before
moonrise, yet the bridge only opened when a traveler answered a riddle aloud.
Bruno was so nervous that he began to stammer. The fox laughed, the river
murmured below, and the berries seemed heavier with every step.

At last Bruno took a breath, counted the berries one by one, and asked the fox
to let him try. He spoke slowly, finished the riddle, and the bridge opened.
Bruno crossed safely, delivered the hundred berries, and the queen praised his
courage. The meadow felt brighter because Bruno had learned that a shaky voice
can still be brave.
---
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift: object | None = None
    guard: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "grandmother", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "grandfather", "father", "man", "fox"}:
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
class Setting:
    place: str = "the meadow"
    bridge: str = "the silver bridge"
    river: str = "the silver river"
    SETTING: object | None = None
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
class Prophecy:
    title: str
    clue: str
    need_count: int = 100
    PROPHECY: object | None = None
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
class Challenge:
    guard: str
    demand: str
    risk: str
    CHALLENGE: object | None = None
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
class Gift:
    label: str
    phrase: str
    type: str = "gift"
    plural: bool = False
    GIFT: object | None = None
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
    name: str
    companion: str
    count: int
    seed: Optional[int] = None
    params: object | None = None
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
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about buffalo, a hundred, and a stammer.")
    ap.add_argument("--name")
    ap.add_argument("--companion", choices=["grandmother", "fox", "queen"], default=None)
    ap.add_argument("--count", type=int)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    count = getattr(args, "count", None) if getattr(args, "count", None) is not None else 100
    if count != 100:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    companion = getattr(args, "companion", None) or rng.choice(["grandmother", "fox", "queen"])
    name = getattr(args, "name", None) or rng.choice(["Bruno", "Bram", "Benny", "Basil", "Boyo"])
    return StoryParams(name=name, companion=companion, count=count)


SETTING = Setting()


BUFFALO = {
    "buffalo": Entity(id="hero", kind="character", type="buffalo", label="little buffalo"),
    "grandmother": Entity(id="grandmother", kind="character", type="grandmother", label="grandmother"),
    "fox": Entity(id="fox", kind="character", type="fox", label="fox"),
    "queen": Entity(id="queen", kind="character", type="queen", label="queen"),
}

PROPHECY = Prophecy(title="the hundred berries", clue="a pouch of a hundred bright berries", need_count=100)

CHALLENGE = Challenge(
    guard="the bridge asks a riddle aloud",
    demand="speak clearly",
    risk="a stammer may keep the bridge shut",
)

GIFT = Gift(label="golden pouch", phrase="a golden pouch full of bright berries", plural=False)


def _count_berries(world: World, hero: Entity, amount: int) -> None:
    hero.meters["berries"] = amount
    hero.memes["calm"] += 1 if amount >= 100 else 0


def predict_failure(world: World, hero: Entity) -> bool:
    sim = world.copy()
    return sim.get(hero.id).memes.get("nervous", 0.0) >= THRESHOLD


def setup(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"In {world.setting.place}, there lived a little buffalo named {hero.id} who loved counting."
    )
    world.say(
        f"Every evening, {hero.id} listened to {companion.label} tell stories about {PROPHECY.title}."
    )
    world.say(
        f"One day {companion.label} gave {hero.pronoun('object')} {GIFT.phrase} and asked {hero.pronoun('object')} to carry it across {world.setting.bridge}."
    )


def start_journey(world: World, hero: Entity) -> None:
    hero.meters["travel"] += 1
    hero.memes["duty"] += 1
    world.para()
    world.say(
        f"{hero.id} walked toward {world.setting.bridge}, and the pouch bumped softly at {hero.pronoun('possessive')} side."
    )
    world.say(
        f"Below, {world.setting.river} whispered like a secret, and the path felt long."
    )


def encounter_guard(world: World, hero: Entity, guard: Entity) -> None:
    hero.memes["nervous"] += 1
    hero.memes["suspense"] += 1
    world.say(
        f"At the bridge, {guard.label} stepped forward and said that no traveler could pass until the riddle was spoken aloud."
    )
    world.say(
        f"That made {hero.id}'s heart skip, because {hero.id} wanted to help but felt a stammer tugging at every word."
    )


def stammer(world: World, hero: Entity) -> None:
    if hero.memes.get("nervous", 0.0) >= THRESHOLD:
        hero.memes["stammer"] += 1
        world.say(
            f"{hero.id} tried to answer, but the first words came out in a stammer: 'I-I-I can do it.'"
        )
        world.say(
            f"The guard waited, and the river kept whispering below."
        )


def brave_count(world: World, hero: Entity, count: int) -> None:
    hero.memes["courage"] += 1
    hero.meters["berries"] = count
    world.say(
        f"Then {hero.id} took one slow breath and counted the berries one by one, from one to {count}."
    )


def solve_riddle(world: World, hero: Entity, guard: Entity) -> None:
    hero.memes["suspense"] += 1
    hero.memes["courage"] += 1
    world.say(
        f"With the counting still steady in {hero.pronoun('possessive')} mind, {hero.id} answered the riddle in a careful, steady voice."
    )
    world.say(
        f"{guard.label} nodded, the bridge opened, and the waiting was over at last."
    )


def finish(world: World, hero: Entity, companion: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["nervous"] = 0.0
    world.para()
    world.say(
        f"{hero.id} crossed {world.setting.bridge}, delivered the hundred berries, and {companion.label} smiled with pride."
    )
    world.say(
        f"By moonrise, the pouch was empty, but {hero.id}'s voice was steady, and the meadow felt safe again."
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="buffalo", label=f"little buffalo {params.name}"))
    companion = world.add(BUFFALO[params.companion])
    guard = world.add(Entity(id="guard", kind="character", type="fox", label="the bridge fox"))
    gift = world.add(Entity(id="pouch", type="gift", label="golden pouch", phrase=GIFT.phrase, owner=hero.id))
    gift.meters["berries"] = params.count
    world.facts.update(hero=hero, companion=companion, guard=guard, gift=gift, params=params)

    setup(world, hero, companion)
    start_journey(world, hero)
    encounter_guard(world, hero, guard)
    stammer(world, hero)
    brave_count(world, hero, params.count)
    solve_riddle(world, hero, guard)
    finish(world, hero, companion)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    return [
        f'Write a fairy tale for young children about a buffalo named {hero.id}, a hundred berries, and a bridge with a riddle.',
        f"Tell a gentle story where {hero.id} must carry a hundred berries for {companion.label} but begins to stammer at a guarded bridge.",
        "Write a suspenseful but kind fairy tale with a brave buffalo who speaks slowly, counts carefully, and saves the day.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    guard = _safe_fact(world, f, "guard")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little buffalo who must carry a hundred berries across the bridge.",
        ),
        QAItem(
            question=f"Why did {hero.id} begin to stammer at the bridge?",
            answer=f"{hero.id} began to stammer because the fox guard asked for a spoken riddle, and the moment felt scary and important.",
        ),
        QAItem(
            question=f"What did {hero.id} carry in the golden pouch?",
            answer=f"{hero.id} carried a hundred bright berries in the golden pouch for the {companion.label_word if hasattr(companion, 'label_word') else companion.label}.",
        ),
        QAItem(
            question=f"How did {hero.id} get past {guard.label}?",
            answer=f"{hero.id} took a breath, counted the berries, answered the riddle in a steady voice, and the bridge opened.",
        ),
        QAItem(
            question=f"What changed by the end of the tale?",
            answer=f"By the end, {hero.id} was no longer frightened, and the berries were delivered safely before moonrise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a buffalo?",
            answer="A buffalo is a large animal with a strong body and a heavy head, and it can walk through rough places.",
        ),
        QAItem(
            question="What does stammer mean?",
            answer="To stammer means to speak with broken starts or repeated sounds when you are nervous or excited.",
        ),
        QAItem(
            question="Why is the number hundred special in stories?",
            answer="A hundred feels like a very big number, so it can make a task seem important or hard to finish.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of wondering what will happen next because the result is not clear yet.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a story with a magical or old-time feeling, often with a brave character, a test, and a happy ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        out.append(f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(out)


ASP_RULES = r"""
hero(buffalo).
count_hundred(100).
stammering_when_nervous(H) :- nervous(H), asks_riddle(guard).
bridge_opens(H) :- answers_steadily(H), count_hundred(100).
resolved_story(H) :- bridge_opens(H), delivered(H).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "buffalo"),
        asp.fact("count_hundred", 100),
        asp.fact("guard", "fox"),
        asp.fact("setting", "bridge"),
        asp.fact("feature", "conflict"),
        asp.fact("feature", "suspense"),
        asp.fact("style", "fairy_tale"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as e:
        print(f"ASP unavailable: {e}")
        return 1
    model = asp.one_model(asp_program("#show hero/1."))
    ok = any(sym.name == "hero" for sym in model)
    if ok:
        print("OK: ASP program loads and produces a model.")
        return 0
    print("ASP verification failed.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(["Bruno", "Bram", "Benny", "Basil", "Boyo"])
    companion = getattr(args, "companion", None) or rng.choice(["grandmother", "fox", "queen"])
    count = getattr(args, "count", None) if getattr(args, "count", None) is not None else 100
    if count != 100:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(name=name, companion=companion, count=count)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show hero/1."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for idx, comp in enumerate(["grandmother", "fox", "queen"]):
            params = StoryParams(name=["Bruno", "Bram", "Benny"][idx], companion=comp, count=100, seed=base_seed + idx)
            samples.append(generate(params))
    else:
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
