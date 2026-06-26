#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/maternal_spread_flatten_nap_room_problem_solving.py
==============================================================================================================

A standalone story world for a tiny detective-style nap-room problem:
something has spread out where it should not, the room needs flattening,
and a maternal helper plus a friend solve it through dialogue and care.

The story premise is intentionally small and classical:
- In a nap room, a child notices a problem.
- A maternal helper helps reason through the clues.
- A friend joins in.
- They flatten the trouble, restoring a calm room for rest.

The generated stories stay grounded in world state, with meters and memes
driving the prose rather than a fixed paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    helper: object | None = None
    hero: object | None = None
    target: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Room:
    place: str = "the nap room"
    quiet: bool = True
    clean: bool = True
    world: object | None = None
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
class Problem:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    clue: str
    spread_kind: str
    spread_region: str
    fix: str
    fix_verb: str
    tags: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    kind: str = "mother"
    traits: list[str] = field(default_factory=list)
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
    def __init__(self, room: Room) -> None:
        self.room = room
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
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _set_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _set_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def room_message(room: Room) -> str:
    return f"The {room.place.removeprefix('the ')} was quiet, but not quite calm."


def intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    return f"{hero.id} was a little {trait} {hero.type} who noticed every tiny clue."


def problem_line(hero: Entity, problem: Problem) -> str:
    return (
        f"{hero.pronoun().capitalize()} liked detective games, and {problem.gerund} "
        f"in the {problem.label} made {hero.pronoun('object')} curious."
    )


def solve_prediction(world: World, hero: Entity, problem: Problem) -> bool:
    sim = world.copy()
    _trigger_problem(sim, sim.get(hero.id), problem, narrate=False)
    target = sim.get(problem.id)
    return target.meters.get("spread", 0.0) >= THRESHOLD


def _trigger_problem(world: World, hero: Entity, problem: Problem, narrate: bool = True) -> None:
    target = world.get(problem.id)
    _set_meter(target, "spread", 1.0)
    _set_meme(hero, "curiosity", 1.0)
    if narrate:
        world.say(
            f"A clue showed up: {target.label} had {problem.spread_kind} "
            f"across {problem.spread_region}."
        )


def _trigger_fix(world: World, helper: Entity, friend: Entity, problem: Problem) -> None:
    target = world.get(problem.id)
    target.meters["spread"] = 0.0
    target.meters["flat"] = 1.0
    _set_meme(helper, "warmth", 1.0)
    _set_meme(friend, "helpfulness", 1.0)
    _set_meme(world.get("hero"), "relief", 1.0)
    _set_meme(world.get("hero"), "friendship", 1.0)
    world.room.quiet = True
    world.room.clean = True


def describe_spread(problem: Problem) -> str:
    return f"{problem.clue} had spread over the {problem.label}, leaving it lumpy."


def detective_turn(hero: Entity, helper: Entity, problem: Problem) -> str:
    return (
        f"\"I think I found the trouble,\" {hero.id} said. "
        f"\"Something {problem.spread_kind} is keeping the {problem.label} from lying flat.\" "
        f"\"Good eye,\" {helper.label} said. \"Let's look at the clues together.\""
    )


def friend_dialogue(friend: Entity, problem: Problem) -> str:
    return (
        f"\"I can help,\" {friend.id} said. \"If we lift one side first, maybe it will stop {problem.spread_kind}.\""
    )


def resolve_line(hero: Entity, helper: Entity, friend: Entity, problem: Problem) -> str:
    return (
        f"Together they pressed, patted, and smoothed the {problem.label} until it was flat. "
        f"\"There,\" {helper.label} said. \"Now the room can rest.\" "
        f"{hero.id} smiled at {friend.id}. \"Best clue team ever,\" {hero.id} whispered."
    )


def tell(problem: Problem, hero_name: str = "Mina", hero_type: str = "girl") -> World:
    world = World(Room())
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, traits=["little", "curious", "steady"]))
    hero.id = hero_name
    world.entities.pop("hero")
    world.entities[hero_name] = hero

    helper = world.add(Entity(id="mom", kind="character", type="mother", label="Mom", traits=["maternal", "calm"]))
    friend = world.add(Entity(id="sage", kind="character", type="girl", label="Sage", traits=["friendly", "brave"]))
    target = world.add(Entity(id=problem.id, type=problem.label, label=problem.label, phrase=problem.label))
    target.meters["spread"] = 0.0
    target.meters["flat"] = 0.0

    world.say(intro(hero))
    world.say(problem_line(hero, problem))
    world.say(room_message(world.room))

    world.para()
    world.say(describe_spread(problem))
    world.say(detective_turn(hero, helper, problem))
    world.say(f"\"{problem.fix},\" {helper.label} said.")
    world.say(friend_dialogue(friend, problem))

    _trigger_problem(world, hero, problem)
    world.para()
    if solve_prediction(world, hero, problem):
        _trigger_fix(world, helper, friend, problem)
        world.say(resolve_line(hero, helper, friend, problem))

    world.facts.update(hero=hero, helper=helper, friend=friend, problem=problem, room=world.room)
    return world


PROBLEMS = {
    "mat": Problem(
        id="mat",
        label="nap mat",
        verb="flatten the mat",
        gerund="the mat spreading",
        rush="push the corners apart",
        clue="a soft corner",
        spread_kind="bunches",
        spread_region="the middle",
        fix="Let's flatten it together",
        fix_verb="flatten",
        tags={"flatten", "spread", "nap room"},
    ),
    "blanket": Problem(
        id="blanket",
        label="nap blanket",
        verb="flatten the blanket",
        gerund="the blanket spreading",
        rush="pull the edges loose",
        clue="a tuggy fold",
        spread_kind="folds",
        spread_region="one side",
        fix="We can smooth it out",
        fix_verb="smooth",
        tags={"flatten", "spread", "nap room"},
    ),
    "pillow": Problem(
        id="pillow",
        label="rest pillow",
        verb="flatten the pillow stack",
        gerund="the pillows spreading",
        rush="stack them too high",
        clue="a tall little tower",
        spread_kind="pillows",
        spread_region="the corner",
        fix="Let's make it low and neat",
        fix_verb="flatten",
        tags={"flatten", "spread", "nap room"},
    ),
}


@dataclass
class StoryParams:
    problem: str
    name: str
    gender: str
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


CURATED = [
    StoryParams(problem="mat", name="Mina", gender="girl"),
    StoryParams(problem="blanket", name="Theo", gender="boy"),
    StoryParams(problem="pillow", name="Lina", gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective story world set in a nap room.")
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "gender", None) and getattr(args, "name", None) is None:
        pass
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(["Mina", "Theo", "Lina", "Noah", "Ivy", "Bea", "Owen"])
    return StoryParams(problem=problem, name=name, gender=gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem: Problem = _safe_fact(world, f, "problem")
    hero: Entity = _safe_fact(world, f, "hero")
    return [
        f'Write a short detective-style story for a young child in a nap room using the words "{problem.spread_kind}" and "{problem.fix_verb}".',
        f"Tell a gentle story where {hero.id} notices a problem in the nap room, talks it through with Mom, and solves it with a friend.",
        f"Write a friendship story with dialogue where a maternal helper helps {hero.id} flatten a messy nap-room clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    friend: Entity = _safe_fact(world, f, "friend")
    problem: Problem = _safe_fact(world, f, "problem")
    return [
        QAItem(
            question=f"What did {hero.id} notice in the nap room?",
            answer=f"{hero.id} noticed that the {problem.label} was spreading out and would not stay flat.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the nap-room problem?",
            answer=f"{helper.label} helped {hero.id}, and {friend.id} joined in as a friend.",
        ),
        QAItem(
            question=f"What did they do to fix the trouble?",
            answer=f"They worked together to flatten the {problem.label} until it was neat and calm again.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy because the room was flat, quiet, and ready for rest.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nap room for?",
            answer="A nap room is a quiet room where children rest or sleep for a while during the day.",
        ),
        QAItem(
            question="What does it mean to flatten something?",
            answer="To flatten something means to make it smooth and level instead of bumpy or piled up.",
        ),
        QAItem(
            question="Why do friends help solve problems?",
            answer="Friends help solve problems because two careful heads can notice more clues and make a job easier.",
        ),
        QAItem(
            question="What does maternal mean?",
            answer="Maternal means motherly, or caring in a way that reminds you of a mom.",
        ),
    ]


ASP_RULES = r"""
hero(H) :- child(H).
helper(M) :- mother(M).
problem(P) :- item(P).

spread_problem(P) :- item(P), spread(P).
needs_flattening(P) :- spread_problem(P).

solved(P) :- needs_flattening(P), flattening(P).
calm_room :- solved(_).

detective_story(H,P) :- hero(H), needs_flattening(P), maternal_help(_), friendship(_), dialogue(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("room", "nap_room"))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("mother", "mom"))
    lines.append(asp.fact("friend", "sage"))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("item", pid))
        lines.append(asp.fact("spread", pid))
        lines.append(asp.fact("flattening", pid))
    lines.append(asp.fact("maternal_help", "mom"))
    lines.append(asp.fact("friendship", "sage"))
    lines.append(asp.fact("dialogue", "spoken"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show detective_story/2.\n#show solved/1."))
    atoms = set()
    for sym in model:
        if sym.name in {"detective_story", "solved"}:
            atoms.add((sym.name, tuple(str(a) for a in sym.arguments)))
    if atoms:
        print("OK: ASP program produced a detective-style solved story model.")
        return 0
    print("MISMATCH: ASP model did not produce expected atoms.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  room: quiet={world.room.quiet} clean={world.room.clean}")
    return "\n".join(lines)


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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    problem = _safe_lookup(PROBLEMS, params.problem)
    world = tell(problem, hero_name=params.name, hero_type=params.gender)
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
        print(asp_program("#show detective_story/2.\n#show solved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show detective_story/2.\n#show solved/1."))
        print("\n".join(str(a) for a in model))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
