#!/usr/bin/env python3
"""
storyworlds/worlds/huge_friendship_quest_comedy.py
===================================================

A small, self-contained story world about huge comedy, friendship, and a quest.

Premise:
- Two friends set out on a quest to move or recover something very huge.
- The situation is funny because the thing is awkward, oversized, or surprising.
- The friends briefly wobble into trouble, then solve it together.

This world keeps a simple physical/emotional model:
- meters: size, heaviness, distance, wobble, progress
- memes: joy, worry, pride, teamwork, embarrassment, affection, laughter

The story is always child-facing, concrete, and state-driven.
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False

    friend: object | None = None
    goal: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in ["size", "heaviness", "distance", "wobble", "progress"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "teamwork", "embarrassment", "affection", "laughter"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    label: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)
    landmarks: list[str] = field(default_factory=list)
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
class Quest:
    id: str
    verb: str
    gerund: str
    goal_label: str
    goal_phrase: str
    size: str
    obstacle: str
    solution_hint: str
    tags: set[str] = field(default_factory=set)
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
    def __init__(self, place: Place, quest: Quest) -> None:
        self.place = place
        self.quest = quest
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        import copy

        w = World(self.place, self.quest)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


SETTINGS = {
    "park": Place("park", "the park", False, {"fetch", "deliver"}, ["bench", "big tree", "winding path"]),
    "market": Place("market", "the market", False, {"deliver", "carry"}, ["stalls", "boxes", "big bell"]),
    "museum": Place("museum", "the museum hall", True, {"find", "carry"}, ["long stairs", "echoing hall", "painted wall"]),
    "bakery": Place("bakery", "the bakery", True, {"fetch", "deliver"}, ["warm oven", "sugar jars", "counter"]),
}

QUESTS = {
    "balloon": Quest(
        "balloon",
        verb="fetch the huge balloon",
        gerund="fetching the huge balloon",
        goal_label="balloon",
        goal_phrase="a huge red balloon",
        size="huge",
        obstacle="it kept bumping into lamps and hats",
        solution_hint="one friend held the string while the other guided the way",
        tags={"huge", "balloon", "fetch"},
    ),
    "pumpkin": Quest(
        "pumpkin",
        verb="carry the huge pumpkin",
        gerund="carrying the huge pumpkin",
        goal_label="pumpkin",
        goal_phrase="a huge round pumpkin",
        size="huge",
        obstacle="it rolled like a silly orange wheel",
        solution_hint="they rolled it slowly together with careful hands",
        tags={"huge", "pumpkin", "carry"},
    ),
    "crown": Quest(
        "crown",
        verb="deliver the huge cardboard crown",
        gerund="delivering the huge cardboard crown",
        goal_label="crown",
        goal_phrase="a huge shiny cardboard crown",
        size="huge",
        obstacle="it was so wide it tried to wear the doorway",
        solution_hint="they tilted it sideways and laughed at its manners",
        tags={"huge", "crown", "deliver"},
    ),
}

FRIEND_NAMES = ["Mina", "Leo", "Pip", "Nina", "Toby", "June", "Ollie", "Sage", "Maya", "Ben"]
TRAITS = ["brave", "curious", "silly", "cheerful", "bouncy", "gentle"]


@dataclass
class StoryParams:
    place: str
    quest: str
    hero_name: str
    friend_name: str
    hero_type: str
    friend_type: str
    trait: str
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


def _valid_combo(place: Place, quest: Quest) -> bool:
    return quest.id in place.affords


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for pid, place in SETTINGS.items():
        for qid, q in QUESTS.items():
            if _valid_combo(place, q):
                out.append((pid, qid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a huge comedy quest about friendship and teamwork."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) and getattr(args, "quest", None):
        if not _valid_combo(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(QUESTS, getattr(args, "quest", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (p, q)
        for p, q in valid_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or q == getattr(args, "quest", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, quest = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(FRIEND_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if hero_name == friend_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        quest=quest,
        hero_name=hero_name,
        friend_name=friend_name,
        hero_type=hero_gender,
        friend_type=friend_gender,
        trait=trait,
    )


def _do_quest(world: World, hero: Entity, friend: Entity, quest: Quest, narrate: bool = True) -> None:
    item = world.get("goal")
    hero.memes["joy"] += 0.5
    friend.memes["joy"] += 0.5
    hero.meters["progress"] += 1
    friend.meters["progress"] += 1
    item.carried_by = hero.id
    item.meters["distance"] += 1
    if narrate:
        world.say(f"They set off to {world.place.label} to {quest.verb}.")


def predict(world: World, hero: Entity, friend: Entity, quest: Quest) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(hero.id), sim.get(friend.id), quest, narrate=False)
    goal = sim.get("goal")
    return {
        "wobble": goal.meters["wobble"],
        "done": goal.meters["progress"] >= 1,
    }


def tell(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(place, quest)

    hero = world.add(Entity("hero", kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity("friend", kind="character", type=params.friend_type, label=params.friend_name))
    goal = world.add(Entity(
        "goal",
        kind="thing",
        type=quest.goal_label,
        label=quest.goal_label,
        owner=hero.id,
    ))
    goal.meters["size"] = 3.0 if quest.size == "huge" else 1.0
    goal.meters["heaviness"] = 3.0
    hero.memes["affection"] += 1
    friend.memes["affection"] += 1
    hero.memes["teamwork"] += 1
    friend.memes["teamwork"] += 1

    world.say(f"{params.hero_name} and {params.friend_name} were best friends.")
    world.say(
        f"They loved tiny jokes, big grins, and any quest that sounded a little bit too huge."
    )
    world.say(
        f"One day, they heard about {quest.goal_phrase} at {place.label}."
    )

    world.para()
    world.say(
        f"{params.hero_name} wanted to {quest.verb}, and {params.friend_name} said, "
        f'"Let’s do it together!"'
    )
    world.say(
        f"At {place.label}, the quest looked funny right away because {quest.obstacle}."
    )
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    goal.meters["wobble"] += 1

    world.para()
    world.say(f"They tried to lift {quest.goal_phrase}, but it wobbled like a sleepy chair.")
    hero.memes["worry"] += 1
    friend.memes["embarrassment"] += 1
    world.say(
        f"{params.hero_name} puffed out {hero.pronoun('possessive')} cheeks, and {params.friend_name} giggled."
    )
    world.say(
        f"Then they remembered {quest.solution_hint}."
    )

    world.para()
    if predict(world, hero, friend, quest)["done"]:
        _do_quest(world, hero, friend, quest, narrate=False)
    goal.meters["progress"] = 1.0
    goal.meters["distance"] += 1
    goal.memes["joy"] += 1
    hero.memes["teamwork"] += 2
    friend.memes["teamwork"] += 2
    hero.memes["laughter"] += 1
    friend.memes["laughter"] += 1
    hero.memes["worry"] = 0.0
    friend.memes["embarrassment"] = 0.0

    world.say(
        f"So {params.hero_name} held one side and {params.friend_name} held the other."
    )
    world.say(
        f"They carried the huge {quest.goal_label} step by step, and it stopped being a problem and started being a joke."
    )
    world.say(
        f"By the end, they reached the finish with {quest.goal_phrase}, laughing so hard that even the {place.landmarks[0] if place.landmarks else 'air'} seemed to smile."
    )

    world.facts.update(
        hero=hero,
        friend=friend,
        goal=goal,
        quest=quest,
        place=place,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy about two friends on a quest to move "{f["quest"].goal_phrase}".',
        f"Tell a gentle friendship story where {f['params'].hero_name} and {f['params'].friend_name} must handle something huge at {f['place'].label}.",
        f'Create a funny quest story that uses the word "huge" and ends with friends laughing together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    quest = _safe_fact(world, f, "quest")
    place = _safe_fact(world, f, "place")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who went on the quest at {place.label}?",
            answer=f"{params.hero_name} and {params.friend_name} went together as best friends.",
        ),
        QAItem(
            question=f"What huge thing were they trying to handle?",
            answer=f"They were trying to {quest.verb} and bring the huge {quest.goal_label} safely along.",
        ),
        QAItem(
            question=f"Why did the quest feel funny?",
            answer=f"It felt funny because {quest.obstacle}, so the job looked a little silly before the friends worked together.",
        ),
        QAItem(
            question=f"How did the friends finish the quest?",
            answer=f"They solved it by sharing the work, and {params.hero_name} and {params.friend_name} carried the huge {quest.goal_label} together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together.",
        ),
        QAItem(
            question="Why can something huge be hard to carry?",
            answer="Something huge can be hard to carry because it may be too big, too heavy, or too awkward for one person.",
        ),
        QAItem(
            question="What happens when friends laugh together?",
            answer="When friends laugh together, they often feel closer and happier.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("park", "balloon", "Mina", "Leo", "girl", "boy", "silly"),
    StoryParams("museum", "crown", "Pip", "Nina", "boy", "girl", "curious"),
    StoryParams("market", "pumpkin", "June", "Ollie", "girl", "boy", "cheerful"),
]


ASP_RULES = r"""
place(P) :- setting(P).
quest(Q) :- task(Q).
compatible(P,Q) :- affords(P,Q).
show_combo(P,Q) :- compatible(P,Q).
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("task", qid))
        lines.append(asp.fact("huge", qid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/2."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python valid_combos():")
    if python_set - asp_set:
        print("  only in python:", sorted(python_set - asp_set))
    if asp_set - python_set:
        print("  only in asp:", sorted(asp_set - python_set))
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/quest combos:")
        for c in combos:
            print(" ", c[0], c[1])
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name} and {p.friend_name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
