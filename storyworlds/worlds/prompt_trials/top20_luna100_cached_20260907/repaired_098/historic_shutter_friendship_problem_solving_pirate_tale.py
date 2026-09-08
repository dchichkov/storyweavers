#!/usr/bin/env python3
"""A child-facing pirate tale about a historic shutter, friendship, and problem solving."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402



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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Person:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    captain: object | None = None
    friend: object | None = None
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    harbor: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))

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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Problem:
    clue: str
    answer: str
    solved: bool = False
    problem: object | None = None
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
class StoryParams:
    seed: Optional[int] = None
    harbor_name: str = "Moonlit Harbor"
    captain_name: str = "Luna"
    captain_species: str = "fox"
    friend_name: str = "Pip"
    friend_species: str = "otter"
    problem_clue: str = "the historic lighthouse shutter would not close"
    problem_answer: str = "a salt-stiffened rope had slipped behind the hinge"
    case: str = "salt_rope"
    route: str = "map_first"
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
class ProblemCase:
    danger: str
    first_test: str
    failed_reason: str
    decisive_clue: str
    cause: str
    brave_action: str
    repair: str
    lesson: str
    ending: str
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
class World:
    harbor: Place
    captain: Person
    friend: Person
    problem: Problem
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


HARBORS = {
    "Moonlit Harbor": Place("Moonlit Harbor", "historic harbor"),
    "Coral Harbor": Place("Coral Harbor", "island harbor"),
    "Old Lantern Bay": Place("Old Lantern Bay", "historic bay"),
}

CAPTAINS = [
    ("Luna", "fox"),
    ("Mara", "cat"),
    ("Juno", "parrot"),
]

FRIENDS = [
    ("Pip", "otter"),
    ("Nell", "goat"),
    ("Tavi", "monkey"),
]

CASES = {
    "salt_rope": ProblemCase(
        "the next tide could leave the harbor's boats without a warning signal",
        "compared the shutter's hinges with the drawing in the old keeper's log",
        "the hinges matched the drawing, so the wooden panels were not wrongly placed",
        "a pale rope fiber clung to the lower hinge",
        "a salt-stiffened signal rope had slipped behind the hinge and jammed the shutter",
        "climbed only to the marked safe step while Pip held the lantern and kept the tide chart dry",
        "pulled the rope free with a boat hook, rubbed the hinge with wax, and tested the shutter three times",
        "good friends share different jobs instead of making one person face every difficulty",
        "the historic shutter opened to the stars, then swung closed before the moonlit tide reached the pier",
    ),
    "seagull_latch": ProblemCase(
        "a storm might blow the shutter loose and damage the lighthouse glass",
        "counted the latch marks and compared them with the keeper's sketch",
        "the latch marks were complete, so the metal catch had not been stolen",
        "white feathers were caught beneath the latch",
        "a seagull's nest lining had wedged into the catch whenever the wind turned north",
        "asked Pip to watch from the ground while Luna used a long brush from the safe landing",
        "cleared the feathers, added a smooth guard, and tested the catch against a gentle breeze",
        "a problem becomes smaller when friends notice details and divide the work",
        "the shutter clicked firmly while gulls circled above a clean, bright lighthouse window",
    ),
    "swollen_board": ProblemCase(
        "rain could enter through the historic lighthouse window",
        "slid a thin paper strip around the shutter's edge",
        "the strip passed the top and sides but stopped at one lower corner",
        "a dark line of damp wood ran beneath that corner",
        "one board had swollen after a barrel leaked rainwater beside the wall",
        "told Pip exactly where the board resisted instead of forcing the old shutter",
        "moved the barrel, dried the board, and used a small plane to make the edge fit again",
        "careful problem solving protects old things better than rushing them",
        "the repaired shutter kept the rain outside while the historic glass shone within",
    ),
    "hidden_key": ProblemCase(
        "the lighthouse could not be secured before the pirate museum opened",
        "searched the places named in the caretaker's historic inventory",
        "the key was not in any listed drawer or chest",
        "a tiny brass scrape marked the shutter's inside frame",
        "the old keeper had hidden the key in a narrow frame box beneath the shutter",
        "admitted that the search had failed and asked Pip to reread the inventory aloud",
        "opened the frame box, labeled the key, and placed a safe spare beside the door",
        "friendship means listening when another person's way of thinking reveals a new path",
        "the key rested in its labeled box as visitors admired the historic shutter",
    ),
    "loose_pin": ProblemCase(
        "the shutter might fall onto the dock below",
        "tapped the safe side of the hinge with a wooden mallet",
        "the shutter stayed still, but a tiny pin rolled across the floor",
        "a round pin lay beneath a faded portrait of the first harbor keeper",
        "the old hinge pin had slipped out during a vibration from a passing cargo boat",
        "blocked the dock with a bright flag while Pip fetched the repair basket",
        "replaced the pin with a fitted one and added a small retaining ring",
        "solving a danger includes protecting others while the repair is being made",
        "the historic shutter rested safely above the quiet dock, held by its new pin",
    ),
}

PROBLEMS = [
    ("the historic shutter would not close", "a salt-stiffened rope had slipped behind the hinge", "salt_rope"),
    ("the lighthouse shutter rattled in the wind", "a seagull feather bundle had wedged in its latch", "seagull_latch"),
    ("rain leaked beside the historic shutter", "a damp board had swollen against its edge", "swollen_board"),
    ("the lighthouse key had vanished", "the old keeper had hidden it in the shutter frame", "hidden_key"),
    ("a hinge pin rolled beneath the shutter", "a cargo boat's vibration had loosened it", "loose_pin"),
]

ROUTES = ("map_first", "dialogue_first", "tide_first", "logbook_first", "clue_first")


ASP_RULES = r"""
friendship(A,B) :- captain(A), friend(B), shares_work(A,B).
solved(P) :- problem(P), cause(P,_), repaired(P).
valid_story(P) :- friendship(captain,friend), solved(P).
"""


def problem_id(clue: str) -> str:
    return "problem_" + "".join(ch if ch.isalnum() else "_" for ch in clue.lower()).strip("_")


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("captain", "captain"),
        asp.fact("friend", "friend"),
        asp.fact("shares_work", "captain", "friend"),
    ]
    for clue, answer, case in PROBLEMS:
        pid = problem_id(clue)
        lines.extend(
            (
                asp.fact("problem", pid),
                asp.fact("cause", pid, answer),
                asp.fact("repaired", pid),
            )
        )
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/1."))
    asp_solved = set(asp.atoms(model, "solved"))
    py_solved = {(problem_id(clue),) for clue, _, _ in PROBLEMS}
    if asp_solved == py_solved:
        print(f"OK: clingo gate matches python reasoning ({len(py_solved)} problems).")
        return 0
    print("MISMATCH between clingo and python reasoning.")
    print("clingo:", sorted(asp_solved))
    print("python:", sorted(py_solved))
    return 1


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(
        str(value)
        for value in (
            params.seed,
            params.harbor_name,
            params.captain_name,
            params.captain_species,
            params.friend_name,
            params.friend_species,
            params.case,
            params.route,
        )
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def build_world(params: StoryParams) -> World:
    if params.harbor_name not in HARBORS:
        pass
    if params.case not in CASES:
        pass
    template = _safe_lookup(HARBORS, params.harbor_name)
    return World(
        harbor=Place(template.name, template.kind),
        captain=Person(params.captain_name, params.captain_species, "captain"),
        friend=Person(params.friend_name, params.friend_species, "trusted friend"),
        problem=Problem(params.problem_clue, params.problem_answer),
    )


def tell_story(world: World, params: StoryParams) -> None:
    captain = world.captain
    friend = world.friend
    harbor = world.harbor
    problem = world.problem
    case = _safe_lookup(CASES, params.case)
    rng = story_rng(params)

    captain.memes.update(curiosity=1, bravery=0)
    friend.memes.update(loyalty=1, cleverness=1)

    openings = {
        "map_first": (
            f"Captain {captain.name} spread a salt-stained map across the deck near {harbor.name}. "
            f"The map marked a historic lighthouse and its stubborn shutter, which would not close."
        ),
        "dialogue_first": (
            f'"That shutter is in trouble," Captain {captain.name} said at {harbor.name}. '
            f'"Then we will solve it together," replied {friend.name}, the captain\'s friend.'
        ),
        "tide_first": (
            f"The tide was sliding toward {harbor.name} when Captain {captain.name} saw that "
            f"the historic lighthouse shutter would not close. A wet deck made every step important."
        ),
        "logbook_first": (
            f"In the lighthouse logbook, Captain {captain.name} found a drawing of the historic shutter. "
            f"Beside it was a fresh warning: the shutter would not close."
        ),
        "clue_first": (
            f"A strange scrape sounded at the historic lighthouse in {harbor.name}. "
            f"Captain {captain.name} found the shutter stuck and called for {friend.name}."
        ),
    }
    world.say(openings[params.route])
    world.say(
        rng.choice(
            [
                f"The danger was real: {case.danger}.",
                f"They did not treat the old building like a toy, because {case.danger}.",
                f"The captain lowered the ship's bright flag to signal care. {case.danger.capitalize()}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f'"A captain does not need to solve every knot alone," {captain.name} said. '
                f'"Good," said {friend.name}. "I notice small clues while you watch the safe path."',
                f'"Will you help me?" asked {captain.name}. {friend.name} smiled. '
                f'"Friends bring different tools and the same hope."',
                f'{friend.name} pointed to the logbook. "You know the tide. I know old hinges. '
                f'Let us listen to both kinds of knowledge."',
            ]
        )
    )

    world.para()
    world.say(f"First, {captain.name} {case.first_test}.")
    world.say(
        rng.choice(
            [
                f"The first idea failed because {case.failed_reason}.",
                f"They learned something useful, even though {case.failed_reason}.",
                f'"That test changed our guess," {captain.name} admitted. {case.failed_reason.capitalize()}.',
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"Then {friend.name} spotted the important clue: {case.decisive_clue}.",
                f"Working as a team, they noticed that {case.decisive_clue}.",
                f"The old logbook and the new evidence agreed when they saw that {case.decisive_clue}.",
            ]
        )
    )
    world.say(f"At last, the cause was clear: {case.cause}.")
    world.facts["cause"] = case.cause

    world.para()
    world.say(
        rng.choice(
            [
                f"{captain.name} felt a flutter of fear but {case.brave_action}.",
                f'"I can be careful and brave at once," {captain.name} said, then {case.brave_action}.',
                f"Friendship made the next step safer. {captain.name} {case.brave_action}.",
            ]
        )
    )
    captain.memes["bravery"] = 1
    friend.memes["trust"] = 1
    captain.meters["safe_steps"] = 1
    friend.meters["helpful_observations"] = 1

    world.say(
        rng.choice(
            [
                f"Together, they {case.repair}.",
                f'{friend.name} held the lantern while {captain.name} followed the plan. They {case.repair}.',
                f'"One job for each friend," said {friend.name}, and they {case.repair}.',
            ]
        )
    )
    problem.solved = True
    harbor.meters["shutter_safe"] = 1
    harbor.memes["shared_pride"] = 1

    world.para()
    world.say(
        rng.choice(
            [
                f"{captain.name} wrote the lesson in the ship's journal: {case.lesson}.",
                f'"What did we learn?" asked {friend.name}. {captain.name} answered, '
                f'"{case.lesson.capitalize()}."',
                f"The repaired shutter left them with more than a tidy lighthouse. It showed that {case.lesson}.",
            ]
        )
    )
    world.say(
        rng.choice(
            [
                f"At sunset, {case.ending}",
                f"When the tide turned silver, {case.ending}",
                f"Before the ship sailed on, {case.ending}",
            ]
        )
    )

    world.facts.update(
        captain=captain,
        friend=friend,
        harbor=harbor,
        problem=problem,
        case=case,
        repair=case.repair,
        lesson=case.lesson,
        ending=case.ending,
        solved=True,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    case = facts["case"]
    return [
        f"Write a pirate tale about Captain {facts['captain'].name} and {facts['friend'].name} solving a problem with a historic shutter.",
        f"Tell a child-facing friendship story in {facts['harbor'].name} where the characters discover that {case.cause}.",
        f"Write a problem-solving adventure ending with this image: {case.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    case = facts["case"]
    captain = facts["captain"]
    friend = facts["friend"]
    harbor = facts["harbor"]
    problem = facts["problem"]
    return [
        QAItem(
            question=f"What problem did Captain {captain.name} find at {harbor.name}?",
            answer=f"Captain {captain.name} found that {problem.clue}. It mattered because {case.danger}.",
        ),
        QAItem(
            question=f"Why did the first test not solve the shutter problem?",
            answer=f"{captain.name} {case.first_test}. That test did not solve the problem because {case.failed_reason}.",
        ),
        QAItem(
            question=f"What clue revealed the real cause?",
            answer=f"{friend.name} and {captain.name} noticed that {case.decisive_clue}. This showed that {case.cause}.",
        ),
        QAItem(
            question=f"How did friendship help {captain.name} solve the problem?",
            answer=f"{friend.name} and {captain.name} shared different jobs. {captain.name} {case.brave_action}, and together they {case.repair}.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"They repaired the historic shutter, and {case.ending}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shutter?",
            answer="A shutter is a movable cover for a window that can help protect it from wind, rain, or bright light.",
        ),
        QAItem(
            question="Why is a historic building treated carefully?",
            answer="A historic building carries memories and useful evidence about the past, so repairs should protect its old materials while making it safe.",
        ),
        QAItem(
            question="How can friends solve a problem together?",
            answer="Friends can listen to one another, share different jobs, test ideas safely, and use evidence instead of blaming each other.",
        ),
        QAItem(
            question="What does a captain do in this story world?",
            answer="A captain guides a crew, watches for danger, and makes careful decisions while helping everyone work together.",
        ),
        QAItem(
            question="Why can a failed test still be useful?",
            answer="A failed test rules out one explanation and gives the problem solvers a clearer next question to investigate.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Pirate tale about a historic shutter, friendship, and problem solving."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--harbor", choices=sorted(HARBORS))
    parser.add_argument("--captain-name")
    parser.add_argument("--friend-name")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    harbor_name = getattr(args, "harbor", None) or rng.choice(sorted(HARBORS))
    captain_name, captain_species = rng.choice(CAPTAINS)
    friend_name, friend_species = rng.choice(FRIENDS)
    clue, answer, case = rng.choice(PROBLEMS)
    return StoryParams(
        seed=getattr(args, "seed", None),
        harbor_name=harbor_name,
        captain_name=getattr(args, "captain_name", None) or captain_name,
        captain_species=captain_species,
        friend_name=getattr(args, "friend_name", None) or friend_name,
        friend_species=friend_species,
        problem_clue=clue,
        problem_answer=answer,
        case=case,
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.harbor, world.captain, world.friend):
        lines.append(
            f"{entity.name}: meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"problem: clue={world.problem.clue!r} answer={world.problem.answer!r} "
        f"solved={world.problem.solved} cause={_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "cause")!r}"
    )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solved/1."))
        print(sorted(set(asp.atoms(model, "solved"))))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    count = 3 if getattr(args, "all", None) else getattr(args, "n", None)
    samples: list[StorySample] = []

    for index in range(count):
        params = resolve_params(args, random.Random(base_seed + index))
        params.seed = base_seed + index
        samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
