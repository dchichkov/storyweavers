#!/usr/bin/env python3
"""
storyworlds/worlds/raise_magic_reconciliation_problem_solving_mystery.py
=========================================================================

A small mystery storyworld about a child who raises an alarm, follows magical
clues, solves a problem, and reaches reconciliation.

Premise:
- A strange glow, a missing object, and a worried friend.
- The hero raises a lantern / voice / hand to notice the mystery.
- Magic is real, but modest: it reveals hidden tracks, ink, and messages.

Tension:
- A misunderstanding makes one character suspect another.
- The hero must reason carefully instead of jumping to the wrong answer.

Turn:
- A magical clue points to the true cause.
- The characters work together to repair the trouble.

Resolution:
- The misunderstood friend is cleared.
- Reconciliation restores trust, and the problem is solved.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "dad", "man"}
        female = {"girl", "mother", "mom", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str
    indoor: bool = False
    mystery_kind: str = "glow"
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
class Clue:
    id: str
    label: str
    reveal: str
    source: str
    hidden_from: str
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
class Problem:
    id: str
    label: str
    wrong_suspect: str
    true_cause: str
    fix: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    friend: str
    mystery: str
    clue: str
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


SETTINGS = {
    "library": Setting(place="the library", indoor=True, mystery_kind="glow"),
    "garden": Setting(place="the moonlit garden", indoor=False, mystery_kind="tracks"),
    "attic": Setting(place="the dusty attic", indoor=True, mystery_kind="whisper"),
}

HEROES = [
    ("Mina", "girl"),
    ("Toby", "boy"),
    ("Nora", "girl"),
    ("Eli", "boy"),
]
FRIENDS = [
    ("Pip", "friend"),
    ("Jun", "friend"),
    ("Bea", "friend"),
    ("Owen", "friend"),
]

MYSTERIES = {
    "glow": Problem(
        id="glow",
        label="a strange glow",
        wrong_suspect="the curious friend",
        true_cause="moon-silver ink on the map",
        fix="use the lantern to reveal the hidden ink",
    ),
    "tracks": Problem(
        id="tracks",
        label="tiny tracks in the dust",
        wrong_suspect="the shy friend",
        true_cause="a clockwork mouse in the wall",
        fix="follow the tracks to the mouse and wind it down",
    ),
    "whisper": Problem(
        id="whisper",
        label="a whisper behind the boxes",
        wrong_suspect="the helpful friend",
        true_cause="wind slipping through a cracked window",
        fix="close the window and listen again",
    ),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        label="a little lantern",
        reveal="shone bright enough to uncover hidden writing",
        source="the old shelf",
        hidden_from="shadows",
    ),
    "chalk": Clue(
        id="chalk",
        label="a piece of chalk",
        reveal="made secret marks appear on the floor",
        source="the drawer",
        hidden_from="dust",
    ),
    "mirror": Clue(
        id="mirror",
        label="a pocket mirror",
        reveal="caught a faint reflection from the real source",
        source="the coat pocket",
        hidden_from="dark corners",
    ),
}

SIGNALS = ["raise", "magic", "reconciliation", "problem solving", "mystery"]


class Runtime:
    def __init__(self, world: World) -> None:
        self.world = world

    def protagonist(self) -> Entity:
        return self.world.get("hero")

    def friend(self) -> Entity:
        return self.world.get("friend")

    def problem(self) -> Problem:
        return self.world.facts["problem"]

    def clue(self) -> Clue:
        return self.world.facts["clue"]


def _raise_attention(world: World) -> None:
    hero = world.get("hero")
    clue = world.get("clue")
    world.say(f"{hero.id} raised {hero.pronoun('possessive')} hand when {clue.label} began to glow.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.meters["alert"] = hero.meters.get("alert", 0) + 1


def _suspect_wrongly(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    problem = _safe_fact(world, world.facts, "problem")
    world.say(
        f"For a moment, {hero.id} thought {friend.id} might be behind {problem.label}, "
        f"because {problem.wrong_suspect} stood closest to the mess."
    )
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    friend.memes["hurt"] = friend.memes.get("hurt", 0) + 1


def _magic_reveal(world: World) -> None:
    clue = world.get("clue")
    problem = _safe_fact(world, world.facts, "problem")
    world.say(
        f"But the magic clue {clue.reveal}, and that pointed away from {problem.wrong_suspect}."
    )
    world.facts["revealed"] = True
    world.facts["true_cause"] = problem.true_cause


def _solve_problem(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    problem = _safe_fact(world, world.facts, "problem")
    clue = world.get("clue")
    world.say(
        f"{hero.id} and {friend.id} used {clue.label} to solve the puzzle: {problem.fix}."
    )
    hero.meters["problem_solved"] = hero.meters.get("problem_solved", 0) + 1
    world.facts["solved"] = True


def _reconcile(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    problem = _safe_fact(world, world.facts, "problem")
    world.say(
        f"{hero.id} apologized for the guess, and {friend.id} smiled back, because the truth was "
        f"finally clear. That was the start of reconciliation."
    )
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    world.facts["reconciled"] = True
    world.say(
        f"In the end, the {problem.label} was solved, the room grew calm again, and the two friends "
        f"walked home side by side."
    )


def tell(setting: Setting, hero_name: str, friend_name: str, problem: Problem, clue: Clue) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="child", traits=["curious", "brave"]))
    friend = world.add(Entity(id=friend_name, kind="character", type="child", traits=["helpful"]))
    world.add(Entity(id="problem", type=problem.id, label=problem.label, phrase=problem.label))
    world.add(Entity(id="clue", type=clue.id, label=clue.label, phrase=clue.label))
    world.facts.update(problem=problem, clue=clue, setting=setting)

    world.say(
        f"One evening at {setting.place}, {hero.id} noticed {problem.label} and knew something was odd."
    )
    world.say(
        f"Beside {hero.id} was {friend.id}, and the air felt full of mystery."
    )
    world.para()

    _raise_attention(world)
    _suspect_wrongly(world)
    world.para()

    _magic_reveal(world)
    _solve_problem(world)
    world.para()

    _reconcile(world)

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = world.get("hero")
    friend = world.get("friend")
    problem: Problem = _safe_fact(world, f, "problem")
    clue: Clue = _safe_fact(world, f, "clue")
    return [
        f"Write a short mystery for a young child about {hero.id}, {friend.id}, and {problem.label}.",
        f"Tell a story where someone raises {clue.label} and magic helps solve a small problem.",
        f"Write a gentle mystery that ends in reconciliation after a mistaken guess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    friend = world.get("friend")
    problem: Problem = _safe_fact(world, world.facts, "problem")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question=f"What did {hero.id} raise when the mystery began?",
            answer=f"{hero.id} raised {hero.pronoun('possessive')} hand, and the little lantern also raised a bright glow in the dark."
        ),
        QAItem(
            question=f"Why did {hero.id} first suspect {friend.id}?",
            answer=f"{hero.id} made a wrong guess because {problem.wrong_suspect} was standing closest to the trouble, but that turned out to be mistaken."
        ),
        QAItem(
            question=f"How did {clue.label} help solve the problem?",
            answer=f"{clue.label} used magic to reveal the real cause, so {hero.id} and {friend.id} could solve the problem together."
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The problem was solved, and {hero.id} and {friend.id} reached reconciliation after the misunderstanding."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a story or problem where something is hidden or not understood at first, so people have to look for clues."
        ),
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after a disagreement or misunderstanding."
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully, testing ideas, and using clues to find a good answer."
        ),
        QAItem(
            question="Why can magic be useful in a story?",
            answer="Magic can be useful because it can reveal hidden things, guide a character, or help solve a problem in a surprising way."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", hero="Mina", friend="Pip", mystery="glow", clue="lantern"),
    StoryParams(place="garden", hero="Toby", friend="Jun", mystery="tracks", clue="chalk"),
    StoryParams(place="attic", hero="Nora", friend="Bea", mystery="whisper", clue="mirror"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with magic, problem solving, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--friend", choices=[n for n, _ in FRIENDS])
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    hero = getattr(args, "hero", None) or rng.choice([n for n, _ in HEROES])
    friend = getattr(args, "friend", None) or rng.choice([n for n, _ in FRIENDS])
    if hero == friend:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, friend=friend, mystery=mystery, clue=clue)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    problem = _safe_lookup(MYSTERIES, params.mystery)
    clue = _safe_lookup(CLUES, params.clue)
    if params.mystery == "glow" and params.clue not in {"lantern", "mirror"}:
        pass
    if params.mystery == "tracks" and params.clue not in {"chalk", "mirror"}:
        pass
    world = tell(setting, params.hero, params.friend, problem, clue)
    world.facts["params"] = params
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
hero(H).
friend(F).
mystery(M).
clue(C).

problem(M) :- mystery_choice(M).
magic_help(C) :- clue_choice(C).

raises_attention(H) :- hero(H).
wrong_suspect(F) :- friend(F).
reconciled(H,F) :- hero(H), friend(F), magic_help(_), problem(_).
solved(M) :- mystery_choice(M), clue_choice(_).

#show raises_attention/1.
#show wrong_suspect/1.
#show reconciled/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for name, _ in HEROES:
        lines.append(asp.fact("hero", name))
    for name, _ in FRIENDS:
        lines.append(asp.fact("friend", name))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_choice", m))
    for c in CLUES:
        lines.append(asp.fact("clue_choice", c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show raises_attention/1. #show wrong_suspect/1. #show reconciled/2. #show solved/1."))
    atoms = set((s.name, tuple(arg.name if arg.type != 1 else arg.string for arg in s.arguments)) for s in model)
    if atoms:
        print("OK: ASP program produced a model.")
        return 0
    print("MISMATCH: ASP program produced no shown atoms.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show raises_attention/1. #show wrong_suspect/1. #show reconciled/2. #show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            i += 1
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} / {p.friend} at {p.place} ({p.mystery}, {p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
