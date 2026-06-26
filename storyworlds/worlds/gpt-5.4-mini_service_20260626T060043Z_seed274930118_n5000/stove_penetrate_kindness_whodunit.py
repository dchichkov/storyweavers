#!/usr/bin/env python3
"""
storyworlds/worlds/stove_penetrate_kindness_whodunit.py
========================================================

A small whodunit-style story world about a kitchen mystery, a warm stove,
and a kind clue that helps solve the case.

The seed imagines a child noticing a puzzling kitchen scene:
- the stove is warm,
- a smell seems to penetrate the hallway,
- someone has acted with kindness,
- and the question is: who did it, and why?

This world turns that into a gentle mystery with a clear clue trail and a
reveal that proves what changed.
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
    caretaker: Optional[str] = None
    wore: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    stove: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt", "sister", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "uncle", "brother", "grandfather", "grandpa"}
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
    cozy: bool = True
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
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    action: str
    effect: str
    kindness: str
    keyword: str = "stove"
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    mystery: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None
    params: object | None = None
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


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen", cozy=True),
}

MYSTERIES = {
    "stove": Mystery(
        id="stove",
        clue="a warm stove and a smell that could penetrate the hallway",
        cause="someone had warmed soup for a neighbor who was feeling ill",
        reveal="the kind helper had used the stove to make soup and left it ready to carry across the street",
        action="make soup",
        effect="the soup got warm and the room smelled like carrots and onions",
        kindness="they wanted to help",
        keyword="stove",
        tags={"stove", "kindness", "smell", "warm"},
    )
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Noah", "Sam", "Ben", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle whodunit story world with a kitchen mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or "kitchen"
    mystery = getattr(args, "mystery", None) or "stove"

    if place not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if mystery not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    child_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)

    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    helper_name = getattr(args, "helper", None) or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)

    if child_name == helper_name:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(
        place=place,
        mystery=mystery,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
    )


def _make_entities(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        type=params.child_gender,
        traits=["curious", "careful"],
        memes={"wonder": 0.0, "kindness": 0.0, "suspicion": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_gender,
        traits=["kind", "quiet"],
        memes={"kindness": 1.0, "suspicion": 0.0, "relief": 0.0},
    ))
    stove = world.add(Entity(
        id="stove",
        kind="thing",
        type="stove",
        label="the stove",
        phrase="the warm stove",
        meters={"heat": 1.0, "smell": 1.0},
    ))
    return child, helper, stove


def _solve_mystery(world: World, child: Entity, helper: Entity, stove: Entity, mystery: Mystery) -> None:
    child.memes["wonder"] += 1.0
    world.say(
        f"{child.id} noticed something odd in {world.place.label}. "
        f"The {mystery.keyword} was warm, and {mystery.clue}."
    )
    world.say(
        f"{child.id} looked around like a small detective and thought, "
        f'"Who did this?"'
    )

    world.para()
    child.memes["suspicion"] += 1.0
    world.say(
        f"First {child.id} checked the counter, then the sink, then the door. "
        f"No crumbs, no spilled water, no broken cup. "
        f"The clue kept pointing back to the {mystery.keyword}."
    )
    world.say(
        f"Then {child.id} found a little note beside the pot: "
        f'"I used the stove because {mystery.kindness}."'
    )

    world.para()
    helper.meters["seen_with_pot"] = 1.0
    world.say(
        f"At last, {helper.id} came in and smiled. "
        f'{helper.pronoun().capitalize()} explained that {mystery.cause}.'
    )
    world.say(
        f"{child.id} understood the case at once. "
        f"It was not a sneaky mistake at all. "
        f"It was a kindness."
    )

    world.para()
    child.memes["relief"] += 1.0
    helper.memes["relief"] += 1.0
    world.say(
        f"{child.id} helped carry the soup, and the two of them walked to the next door together. "
        f"By then, the warm smell had faded from the room, but the good deed still seemed to linger."
    )
    world.say(
        f"At the end, the stove was off, the kitchen was tidy, and the mystery was solved."
    )

    world.facts.update(
        child=child,
        helper=helper,
        stove=stove,
        mystery=mystery,
        solved=True,
        clue=mystery.clue,
        cause=mystery.cause,
        kindness=mystery.kindness,
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(PLACES, params.place))
    child, helper, stove = _make_entities(world, params)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    _solve_mystery(world, child, helper, stove, mystery)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a short whodunit for a young child set in {world.place.label} with the word "{mystery.keyword}".',
        f"Tell a gentle mystery where {child.id} notices a clue near the stove and learns that {helper.id} was helping someone.",
        f"Write a story about a warm kitchen clue, a missing answer, and a kind reveal.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    mystery = _safe_fact(world, f, "mystery")
    return [
        QAItem(
            question=f"What did {child.id} notice first in the kitchen?",
            answer=f"{child.id} noticed a warm stove and a smell that could penetrate the hallway.",
        ),
        QAItem(
            question=f"Who turned out to be the one behind the mystery?",
            answer=f"{helper.id} was behind it, but not for a bad reason. {helper.id} was being kind.",
        ),
        QAItem(
            question="Why did the helper use the stove?",
            answer=f"{helper.id} used the stove because {mystery.cause}.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The stove was turned off, the soup was carried away, and the mystery was solved with kindness.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a stove do?",
            answer="A stove gives off heat so people can cook or warm food.",
        ),
        QAItem(
            question="What does penetrate mean in this story?",
            answer="Here, penetrate means the smell spread into the hallway and reached farther away.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means doing something helpful and caring for someone else.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
stove(stove).
place(kitchen).
kindness(helping).

story_valid(kitchen, stove) :- place(kitchen), stove(stove), kindness(helping).
#show story_valid/2.
"""


def asp_facts() -> str:
    return "place(kitchen).\nstove(stove).\nkindness(helping).\n"


def asp_program(show: str) -> str:
    return f"{asp_facts()}{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_valid/2."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    py = {("kitchen", "stove")}
    asp_set = set(asp_valid())
    if asp_set == py:
        print("OK: ASP and Python agree on the valid mystery.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(asp_set))
    return 1


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
        print(asp_program("#show story_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible mystery:\n")
        for place, mystery in asp_valid():
            print(f"  {place} {mystery}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = StoryParams(place="kitchen", mystery="stove", child_name="Mia", child_gender="girl",
                             helper_name="Theo", helper_gender="boy")
        samples = [generate(params)]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
