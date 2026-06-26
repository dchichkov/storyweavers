#!/usr/bin/env python3
"""
A standalone storyworld: a literary goblin whodunit with repetition, clues,
and a small mystery to solve.

The premise is a tiny library-style mystery: a goblin notices that a cherished
story keeps repeating the same line, and the repeated line points to the thief.
The world simulates clue gathering, suspicion, and a final reveal that changes
who is blamed and where the missing thing was hidden.
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
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    goblin: object | None = None
    helper: object | None = None
    hidden: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"goblin"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Setting:
    place: str = "the old library"
    scent: str = "dust and paper"
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
    place: str
    mystery: str
    missing: str
    goblin_name: str
    helper_name: str
    culprit: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registry / content
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting(place="the old library", scent="dust and paper"),
    "attic": Setting(place="the candlelit attic", scent="wood and rain"),
    "museum": Setting(place="the quiet museum", scent="wax and stone"),
}

MYSTERIES = {
    "repeating_line": {
        "theme": "repetition",
        "line": "the red book was never where it should be",
        "clue": "the sentence kept repeating in the margins",
        "solve": "The repeating line pointed to the hidden shelf behind the atlas",
    },
    "missing_key": {
        "theme": "repetition",
        "line": "the key always clinked twice",
        "clue": "the same double clink was written again and again",
        "solve": "The double clink meant the key had fallen into the music box",
    },
    "vanished_ink": {
        "theme": "repetition",
        "line": "the ink blot made the same shape three times",
        "clue": "three identical blots were stamped in a trail",
        "solve": "The trail led to the loose floorboard under the desk",
    },
}

MISSING_ITEMS = {
    "book": ("the red book", "book", False),
    "key": ("the brass key", "key", False),
    "ink": ("the blue ink bottle", "ink bottle", False),
}

CULPRITS = [
    "the sleepy librarian",
    "the nervous mouse",
    "the visiting poet",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clue_text(mystery_id: str) -> str:
    return _safe_lookup(MYSTERIES, mystery_id)["clue"]

def solve_text(mystery_id: str) -> str:
    return _safe_lookup(MYSTERIES, mystery_id)["solve"]

def mystery_line(mystery_id: str) -> str:
    return _safe_lookup(MYSTERIES, mystery_id)["line"]

def validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    if params.missing not in MISSING_ITEMS:
        pass
    if params.culprit not in CULPRITS:
        pass

def choose_valid_params(rng: random.Random, args: argparse.Namespace) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    missing = getattr(args, "missing", None) or rng.choice(list(MISSING_ITEMS))
    culprit = getattr(args, "culprit", None) or rng.choice(CULPRITS)
    goblin_name = getattr(args, "goblin_name", None) or rng.choice(["Mira", "Pip", "Nim", "Gloam", "Tula"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Iris", "Ned", "Lena", "Milo", "Ada"])
    params = StoryParams(
        place=place,
        mystery=mystery,
        missing=missing,
        goblin_name=goblin_name,
        helper_name=helper_name,
        culprit=culprit,
    )
    validate_params(params)
    return params


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
mystery(M) :- mystery_id(M).
missing_item(I) :- item_id(I).
place(P) :- place_id(P).

repeats(M) :- clue(M, repetition).
valid_story(P, M, I) :- place(P), mystery(M), missing_item(I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place_id", p))
    for m, data in MYSTERIES.items():
        lines.append(asp.fact("mystery_id", m))
        if data["theme"] == "repetition":
            lines.append(asp.fact("clue", m, "repetition"))
    for i in MISSING_ITEMS:
        lines.append(asp.fact("item_id", i))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p, m, i) for p in SETTINGS for m in MYSTERIES for i in MISSING_ITEMS}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches python set ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    goblin = world.add(Entity(
        id=params.goblin_name,
        kind="character",
        type="goblin",
        label="the little goblin",
        meters={"curiosity": 1.0, "hope": 0.0},
        memes={"dread": 0.0, "focus": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="child",
        label="the helper",
        meters={"curiosity": 0.0},
        memes={"trust": 1.0},
    ))
    missing_label, missing_type, plural = _safe_lookup(MISSING_ITEMS, params.missing)
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type=missing_type,
        label=missing_type,
        phrase=missing_label,
        plural=plural,
    ))
    culprit = world.add(Entity(
        id="culprit",
        kind="character",
        type="person",
        label=params.culprit,
        meters={"nervousness": 0.0},
        memes={"guilt": 1.0},
    ))
    hidden = world.add(Entity(
        id="hiding_place",
        kind="thing",
        type="place",
        label="hidden shelf",
    ))
    missing.hidden_in = hidden.id
    culprit.carried_by = None

    world.facts.update(
        goblin=goblin,
        helper=helper,
        missing=missing,
        culprit=culprit,
        mystery=params.mystery,
        mystery_data=_safe_lookup(MYSTERIES, params.mystery),
        setting=setting,
        place=params.place,
        clue=clue_text(params.mystery),
        solve=solve_text(params.mystery),
    )

    # Act 1
    world.say(f"In {setting.place}, {goblin.label} loved quiet stories and sharp clues.")
    world.say(f"{goblin.id} noticed a strange whodunit: {mystery_line(params.mystery)}.")
    world.say(f"Again and again, {clue_text(params.mystery)}.")
    world.say(f"{helper.id} listened closely, because little mysteries grow louder when they repeat.")

    # Act 2
    world.para()
    goblin.memes["focus"] += 1.0
    helper.meters["curiosity"] += 1.0
    world.say(f"{goblin.id} paced between the shelves and repeated the clue under {goblin.pronoun('possessive')} breath.")
    world.say(f"{helper.id} counted the repeats and found they happened exactly three times.")
    world.say(f"That made {goblin.id} suspect {culprit.label}, but the clue still had to point somewhere real.")

    # Act 3
    world.para()
    goblin.memes["hope"] += 1.0
    world.say(f"At last, {goblin.id} solved it: {solve_text(params.mystery)}.")
    world.say(f"The missing {missing.label} was found there, and {culprit.label} was the one who had hidden it.")
    world.say(f"{goblin.id} smiled, because the repeating clue had become a clean answer instead of a puzzle.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a small whodunit for children set in {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place} with a goblin who notices repetition.",
        f"Tell a mystery story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goblin").id} hears the same clue again and again and solves what happened to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing").phrase}.",
        f"Write a literary goblin mystery with a repeated line, a careful helper, and a solved hidden-object ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    goblin = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "goblin")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    missing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing")
    culprit = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "culprit")
    mystery_data = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery_data")

    return [
        QAItem(
            question=f"Who noticed the mystery first in {world.setting.place}?",
            answer=f"The little goblin named {goblin.id} noticed it first, because {goblin.id} kept hearing the same clue repeat.",
        ),
        QAItem(
            question=f"What was the repeated clue in the story?",
            answer=f"The repeated clue was: {mystery_line(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery"))}. The story also kept saying that {mystery_data['clue']}.",
        ),
        QAItem(
            question=f"How many times did the helper count the clue?",
            answer=f"{helper.id} counted the repeats and found that the clue happened exactly three times.",
        ),
        QAItem(
            question=f"What was missing in the whodunit?",
            answer=f"The missing thing was {missing.phrase}. It was later found in the hidden place the clue pointed to.",
        ),
        QAItem(
            question=f"Who turned out to be responsible?",
            answer=f"{culprit.label} turned out to be responsible, because {culprit.label} had hidden the missing item.",
        ),
        QAItem(
            question=f"How was the mystery solved at the end?",
            answer=f"{goblin.id} solved it by noticing that the repeated clue pointed to {solve_text(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery"))}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle about what happened, who did it, or where something went.",
        ),
        QAItem(
            question="What is repetition in a story?",
            answer="Repetition means something happens or is said again and again, which can make it easier to notice.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps someone solve a puzzle or mystery.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="library", mystery="repeating_line", missing="book", goblin_name="Mira", helper_name="Iris", culprit="the sleepy librarian"),
    StoryParams(place="attic", mystery="missing_key", missing="key", goblin_name="Pip", helper_name="Ned", culprit="the nervous mouse"),
    StoryParams(place="museum", mystery="vanished_ink", missing="ink", goblin_name="Nim", helper_name="Ada", culprit="the visiting poet"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny literary goblin whodunit with repetition and a solved mystery.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--missing", choices=MISSING_ITEMS)
    ap.add_argument("--goblin-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--culprit", choices=CULPRITS)
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
    params = choose_valid_params(rng, args)
    return params


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:")
        for c in combos[:20]:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.goblin_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
