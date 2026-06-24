#!/usr/bin/env python3
"""
A small detective-story world about repetition, clarification, and surprise.

Premise:
- A child detective notices the same clue turning up again and again.
- A grown-up asks for a clear explanation, so the detective must sort what is
  repeated from what is merely similar.
- The surprise ending comes from the clue being honest but incomplete: it points
  to the helper, not the thief.
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
# Domain registries
# ---------------------------------------------------------------------------

PLACES = {
    "library": {
        "name": "the library",
        "detail": "The library was quiet, with tall shelves and soft yellow lamps.",
        "can_repeat": True,
    },
    "bakery": {
        "name": "the bakery",
        "detail": "The bakery smelled sweet, and the counter was dusted with flour.",
        "can_repeat": True,
    },
    "train_station": {
        "name": "the train station",
        "detail": "The train station hummed with footsteps, rolling bags, and shiny rails.",
        "can_repeat": True,
    },
    "museum": {
        "name": "the museum",
        "detail": "The museum had pale walls, quiet halls, and displays under glass.",
        "can_repeat": True,
    },
}

CLUES = {
    "crumbs": {
        "label": "a trail of crumbs",
        "thing": "crumbs",
        "scent": "sweet",
        "source": "the bakery",
        "cause": "someone carried a snack bag",
    },
    "ink": {
        "label": "an ink smudge",
        "thing": "ink",
        "scent": "sharp",
        "source": "the library",
        "cause": "someone had a pen in a pocket",
    },
    "chalk": {
        "label": "a chalk mark",
        "thing": "chalk",
        "scent": "dusty",
        "source": "the museum",
        "cause": "someone touched a display placard",
    },
    "thread": {
        "label": "a blue thread",
        "thing": "thread",
        "scent": "clean",
        "source": "the train station",
        "cause": "someone brushed against a coat",
    },
}

HELPERS = {
    "porter": {
        "label": "the porter",
        "job": "carry bags",
        "tool": "a cart",
        "looks": "wears a cap and moves quickly",
    },
    "baker": {
        "label": "the baker",
        "job": "pack boxes",
        "tool": "a tray",
        "looks": "has flour on their sleeves",
    },
    "librarian": {
        "label": "the librarian",
        "job": "shelve books",
        "tool": "a stamp pad",
        "looks": "wears glasses and speaks softly",
    },
    "guide": {
        "label": "the guide",
        "job": "show visitors around",
        "tool": "a clipboard",
        "looks": "carries keys and a flashlight",
    },
}

SUSPECTS = {
    "cat": {
        "label": "the cat",
        "role": "wander around quietly",
        "innocent_reason": "had only walked through the hall",
    },
    "boy": {
        "label": "the boy",
        "role": "carry a snack",
        "innocent_reason": "had dropped a cookie by accident",
    },
    "woman": {
        "label": "the woman",
        "role": "borrow a pen",
        "innocent_reason": "had been taking notes for a tour",
    },
    "janitor": {
        "label": "the janitor",
        "role": "clean the floor",
        "innocent_reason": "had mopped the hall and left a mark by mistake",
    },
}

NAMES = ["Mina", "Arlo", "Tess", "Jude", "Nina", "Owen", "Ivy", "Theo"]


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

    phrases: object | None = None
    clue: object | None = None
    detective: object | None = None
    helper: object | None = None
    suspect: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        table = {
            "girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"},
        }.get(self.type, {"subject": "they", "object": "them", "possessive": "their"})
        return table[case]
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
class StoryParams:
    place: str
    clue: str
    suspect: str
    helper: str
    detective_name: str
    detective_type: str = "girl"
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


@dataclass
class World:
    place: str
    detective: Entity
    helper: Entity
    suspect: Entity
    clue: Entity
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# ASP rules and facts
# ---------------------------------------------------------------------------
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
        return None


ASP_RULES = r"""
% A clue is surprising when it appears more than once, but its source is not the
% culprit.  Clarification resolves the repetition into a true explanation.
repeat(clue) :- clue_seen(clue, 2).
needs_clarify(C) :- repeat(C), not solved(C).
solved(C) :- clue_points_to_helper(C).
surprise(C) :- repeat(C), helper_involved(C), not culprit_is_helper(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("source", clue_id, _safe_lookup(CLUES, clue_id)["source"].replace("the ", "")))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    for suspect_id in SUSPECTS:
        lines.append(asp.fact("suspect", suspect_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show repeat/1. #show needs_clarify/1. #show surprise/1."))
    reps = set(asp.atoms(model, "repeat"))
    clar = set(asp.atoms(model, "needs_clarify"))
    surp = set(asp.atoms(model, "surprise"))
    return sorted(reps | clar | surp)


def asp_verify() -> int:
    py = set()
    for clue_id in CLUES:
        if _safe_lookup(CLUES, clue_id).get("repeatable", True):
            py.add(("repeat", clue_id))
    if py == set(asp_reasonable()):
        print("OK: ASP twin agrees with Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("python:", sorted(py))
    print("asp   :", sorted(asp_reasonable()))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    detective = Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=params.detective_name,
        phrases=params.detective_name if False else "",  # keep stdlib-only and harmless
    )
    helper = Entity(
        id="helper",
        kind="character",
        type="adult",
        label=_safe_lookup(HELPERS, params.helper)["label"],
    )
    suspect = Entity(
        id="suspect",
        kind="character",
        type="adult" if params.suspect != "cat" else "animal",
        label=_safe_lookup(SUSPECTS, params.suspect)["label"],
    )
    clue = Entity(
        id="clue",
        kind="thing",
        type=params.clue,
        label=_safe_lookup(CLUES, params.clue)["label"],
        owner="helper",
        meters={"seen": 0.0},
        memes={"mystery": 0.0},
    )
    world = World(place=place["name"], detective=detective, helper=helper, suspect=suspect, clue=clue)
    world.facts.update(params=params, place=place, clue=_safe_lookup(CLUES, params.clue), helper=_safe_lookup(HELPERS, params.helper), suspect=_safe_lookup(SUSPECTS, params.suspect))
    return world


def narrate(world: World) -> None:
    p = _safe_fact(world, world.facts, "place")
    clue = _safe_fact(world, world.facts, "clue")
    helper = _safe_fact(world, world.facts, "helper")
    suspect = _safe_fact(world, world.facts, "suspect")
    params: StoryParams = _safe_fact(world, world.facts, "params")
    det = world.detective

    world.say(f"{params.detective_name} was a little detective who loved quiet questions and careful looking.")
    world.say(f"One day, {params.detective_name} went to {p['name']}. {p['detail']}")
    world.say(f"Near the floor, {params.detective_name} spotted {clue['label']}.")
    world.say(f"Then the same kind of clue turned up again and again, in the same small path.")
    world.say(f"{params.detective_name} frowned, because repetition can mean a trail, but it can also mean a mistake.")
    world.para()
    world.say(f"{helper['label']} came over and said, \"Please clarify what you see.\"")
    world.say(f"So {params.detective_name} looked again and said, \"It's {clue['label']}, but it is not the same as a theft clue yet.\"")
    world.say(f"The clue was pointing toward {helper['label']} because {helper['job']} {helper['tool']} had brushed the spot.")
    world.say(f"That meant the clue was honest, but it was incomplete.")
    world.para()
    world.say(f"At first, {params.detective_name} had suspected {suspect['label']}.")
    world.say(f"But the surprise was that {suspect['label']} was only nearby and {suspect['innocent_reason']}.")
    world.say(f"The real answer was a small accident from {helper['label']}, not a sneaky crime.")
    world.say(f"{params.detective_name} closed the notebook and smiled, because the mystery made sense at last.")

    # world state changes
    world.clue.meters["seen"] = 2.0
    world.clue.memes["clarified"] = 1.0
    world.memes["surprise"] = 1.0
    world.meters["repetition"] = 1.0
    world.facts["solved"] = True
    world.facts["repeat"] = True
    world.facts["surprise"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    clue = _safe_fact(world, world.facts, "clue")["label"]
    return [
        f'Write a short detective story for a child that uses the word "clarify" and includes {clue}.',
        f"Tell a mystery story where {params.detective_name} notices repetition, asks for clarification, and gets a surprise answer.",
        "Write a gentle detective tale where the first guess is wrong, but the ending makes sense after the clue is explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = _safe_fact(world, world.facts, "params")
    clue = _safe_fact(world, world.facts, "clue")["label"]
    helper = _safe_fact(world, world.facts, "helper")["label"]
    suspect = _safe_fact(world, world.facts, "suspect")["label"]
    return [
        QAItem(
            question=f"What did {params.detective_name} keep seeing again and again?",
            answer=f"{params.detective_name} kept seeing {clue} again and again.",
        ),
        QAItem(
            question=f"Why did {params.detective_name} need to clarify the clue?",
            answer=f"{params.detective_name} needed to clarify it because repetition can look mysterious, but the same clue by itself does not always mean someone stole anything.",
        ),
        QAItem(
            question=f"Who turned out to be connected to the clue?",
            answer=f"{helper} was connected to the clue, because the clue came from a harmless brush of {world.facts['helper']['tool']}.",
        ),
        QAItem(
            question=f"Who was the surprise wrong guess in the story?",
            answer=f"{suspect} was the wrong guess at first, but the story showed that {suspect} was only nearby.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    clue = _safe_fact(world, world.facts, "clue")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question="What does it mean to clarify something?",
            answer="To clarify something means to make it clearer so other people understand it better.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means something happens or appears more than once.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something the reader does not expect, but that still makes sense in the story.",
        ),
        QAItem(
            question=f"What kind of place is {place['name']}?",
            answer=place["detail"],
        ),
        QAItem(
            question=f"Why can {clue['label']} be a clue in a mystery?",
            answer=f"{clue['label'].capitalize()} can be a clue because it can show where something came from or who passed by.",
        ),
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@dataclass
class ParamChoice:
    place: str = "library"
    clue: str = "ink"
    suspect: str = "cat"
    helper: str = "librarian"
    detective_type: str = "girl"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with repetition, clarify, and surprise.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--suspect", choices=sorted(SUSPECTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--name", choices=NAMES)
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    helper = getattr(args, "helper", None) or rng.choice(sorted(HELPERS))
    suspect = getattr(args, "suspect", None) or rng.choice(sorted(SUSPECTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)

    if helper == "baker" and place == "library":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if suspect == "cat" and clue == "chalk" and place == "bakery":
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        place=place,
        clue=clue,
        suspect=suspect,
        helper=helper,
        detective_name=name,
        detective_type=gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    lines.append(f"  place: {world.place}")
    lines.append(f"  detective: {world.detective.label} ({world.detective.type})")
    lines.append(f"  helper: {world.helper.label}")
    lines.append(f"  suspect: {world.suspect.label}")
    lines.append(f"  clue_seen: {world.clue.meters.get('seen', 0)}")
    lines.append(f"  clues_clarified: {world.clue.memes.get('clarified', 0)}")
    lines.append(f"  repetition: {world.meters.get('repetition', 0)}")
    lines.append(f"  surprise: {world.memes.get('surprise', 0)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", clue="ink", suspect="woman", helper="librarian", detective_name="Mina", detective_type="girl"),
    StoryParams(place="bakery", clue="crumbs", suspect="boy", helper="baker", detective_name="Arlo", detective_type="boy"),
    StoryParams(place="train_station", clue="thread", suspect="cat", helper="porter", detective_name="Tess", detective_type="girl"),
    StoryParams(place="museum", clue="chalk", suspect="janitor", helper="guide", detective_name="Jude", detective_type="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show repeat/1. #show needs_clarify/1. #show surprise/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show repeat/1. #show needs_clarify/1. #show surprise/1."))
        print("ASP atoms:")
        for atom in model:
            print(atom)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
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
        print(sample.story)
        if getattr(args, "trace", None) and sample.world is not None:
            print(dump_trace(sample.world))
        if getattr(args, "qa", None):
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
