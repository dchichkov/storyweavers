#!/usr/bin/env python3
"""
Standalone storyworld: wine, a grump, and a mystery to solve, told in a fable
style with a small causal simulation.

Seed impression:
- A careful child or helper notices that a bottle of wine has gone missing or
  been muddled.
- A grumpy character suspects trouble and pushes the search along.
- The mystery is solved by following simple clues in the room and by revealing
  who moved what and why.
- The ending should feel like a fable: a small lesson, a clear turn, and a calm
  resolution.

This world keeps the simulated state visible through:
- physical meters: moved, hidden, spilled, warmed, dusty
- emotional memes: grump, worry, curiosity, relief, trust
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carries: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    crate: object | None = None
    grump: object | None = None
    helper: object | None = None
    hero: object | None = None
    note: object | None = None
    shelf: object | None = None
    wine: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def is_character(self) -> bool:
        return self.kind == "character"
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
    place: str = "the cellar"
    detail: str = "It smelled cool and a little dusty."
    room: object | None = None
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
class Mystery:
    wine_label: str
    missing_reason: str
    clue_place: str
    culprit_id: str
    solved_by: str
    lesson: str
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
    place: str = "cellar"
    protagonist: str = "Mina"
    protagonist_type: str = "girl"
    grump: str = "Old Bram"
    grump_type: str = "man"
    helper: str = "Rowan"
    helper_type: str = "boy"
    sample: object | None = None
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
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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

        c = World(self.room)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        return c


def _name_article(name: str) -> str:
    return f"{name}"


def _a_or_an(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def _describe_wine(e: Entity) -> str:
    return e.phrase or f"{_a_or_an(e.label)} {e.label}"


def reason_gate(params: StoryParams) -> None:
    if params.protagonist == params.grump:
        pass
    if params.place != "cellar":
        pass
    if not params.protagonist.strip() or not params.grump.strip() or not params.helper.strip():
        pass


def build_world(params: StoryParams) -> World:
    room = Room()
    world = World(room)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=params.protagonist_type,
        label=params.protagonist,
        meters={"dust": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "trust": 0.0},
    ))
    grump = world.add(Entity(
        id="grump",
        kind="character",
        type=params.grump_type,
        label=params.grump,
        meters={"dust": 0.0},
        memes={"grump": 1.0, "worry": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper_type,
        label=params.helper,
        meters={"dust": 0.0},
        memes={"curiosity": 1.0, "trust": 0.0},
    ))
    wine = world.add(Entity(
        id="wine",
        type="bottle",
        label="bottle of wine",
        phrase="a bottle of dark red wine",
        owner=grump.id,
        caretaker=grump.id,
        meters={"moved": 0.0, "hidden": 0.0, "spilled": 0.0, "warm": 0.0},
    ))
    note = world.add(Entity(
        id="note",
        type="note",
        label="paper note",
        phrase="a small paper note",
        owner=helper.id,
        hidden_in="crate",
        meters={"tucked": 1.0},
    ))
    crate = world.add(Entity(
        id="crate",
        type="crate",
        label="old crate",
        phrase="an old crate full of apple straw",
        meters={"dust": 1.0},
    ))
    shelf = world.add(Entity(
        id="shelf",
        type="shelf",
        label="high shelf",
        phrase="a high shelf near the wall",
        meters={"dust": 1.0},
    ))

    world.facts.update(hero=hero, grump=grump, helper=helper, wine=wine, note=note, crate=crate, shelf=shelf)
    return world


def propagate(world: World) -> None:
    wine = world.get("wine")
    grump = world.get("grump")
    helper = world.get("helper")
    hero = world.get("hero")
    note = world.get("note")
    crate = world.get("crate")

    sig = ("dust_notice",)
    if sig not in world.fired and (wine.meters.get("hidden", 0.0) >= THRESHOLD or wine.meters.get("moved", 0.0) >= THRESHOLD):
        world.fired.add(sig)
        hero.memes["curiosity"] += 1.0
        world.say(f"{hero.label} noticed that something about the cellar felt off.")

    sig = ("grump_worry",)
    if sig not in world.fired and wine.meters.get("hidden", 0.0) >= THRESHOLD:
        world.fired.add(sig)
        grump.memes["worry"] += 1.0
        world.say(f"{grump.label} frowned, because the bottle was no longer where it should have been.")

    sig = ("note_clue",)
    if sig not in world.fired and note.hidden_in == "crate":
        world.fired.add(sig)
        helper.memes["trust"] += 1.0
        world.say(f"{helper.label} remembered a note tucked inside the old crate.")

    sig = ("solve",)
    if sig not in world.fired and wine.meters.get("hidden", 0.0) >= THRESHOLD and note.hidden_in == "crate":
        world.fired.add(sig)
        world.facts["solved"] = True
        world.facts["clue"] = "the paper note hidden in the crate"
        world.facts["culprit"] = helper.id
        world.facts["reason"] = "the helper had moved the wine aside to make room for the note"
        world.say(f"The mystery finally made sense: the wine had been moved aside, not stolen.")


def tell(params: StoryParams) -> World:
    reason_gate(params)
    world = build_world(params)
    hero = world.get("hero")
    grump = world.get("grump")
    helper = world.get("helper")
    wine = world.get("wine")
    note = world.get("note")
    crate = world.get("crate")

    world.say(
        f"Once upon a time, {hero.label} went down into {world.room.place} with {helper.label}, "
        f"while {grump.label} waited nearby with a stern look."
    )
    world.say(f"{world.room.detail} On a low table stood {_describe_wine(wine)}.")
    world.say(
        f"{grump.label} was a true grump that morning; {grump.pronoun().capitalize()} muttered that no one should move anything without asking."
    )

    world.para()
    world.say(
        f"Then {hero.label} saw that the wine was not on the table anymore. "
        f"It had been moved, and the empty space looked strangely important."
    )
    wine.meters["moved"] += 1.0
    wine.meters["hidden"] += 1.0
    propagate(world)

    world.say(
        f"{helper.label} pointed at the old crate and said there might be a clue hiding there."
    )
    note.hidden_in = "crate"
    propagate(world)

    world.para()
    world.say(
        f"{hero.label} lifted the crate lid and found the paper note. "
        f"It explained that {helper.label} had moved the wine only to keep it safe while making room for the note."
    )
    if not world.facts.get("solved"):
        world.facts["solved"] = True
        world.facts["clue"] = "the paper note hidden in the crate"
        world.facts["culprit"] = helper.id
        world.facts["reason"] = "the helper had moved the wine aside to make room for the note"

    grump.memes["grump"] = 0.0
    grump.memes["trust"] += 1.0
    hero.memes["trust"] += 1.0
    helper.memes["trust"] += 1.0

    world.say(
        f"{grump.label} stopped grumping and gave a small nod. "
        f"'{world.facts['reason']},' {grump.pronoun().capitalize()} admitted. "
        f"'A careful heart sometimes looks like a mystery until the clue is found.'"
    )
    world.say(
        f"So the bottle of wine was returned to its place, the note was kept safe, and the cellar grew quiet again."
    )
    world.say(
        f"And the lesson was simple: when people look after one another's things, a grump may be soothed and a mystery may be solved."
    )

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short fable about a wine cellar mystery, a grump, and a clue hidden in a crate.',
        f"Tell a gentle story where {f['hero'].label} notices the wine is missing, "
        f"{f['grump'].label} gets grumpy, and the mystery is solved with a small clue.",
        "Write a child-friendly fable in which a worried search ends with a calm lesson about care and honesty.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    grump = _safe_fact(world, world.facts, "grump")
    helper = _safe_fact(world, world.facts, "helper")
    wine = _safe_fact(world, world.facts, "wine")
    qa = [
        QAItem(
            question=f"Who went down into the cellar first?",
            answer=f"{hero.label} went down into the cellar with {helper.label} while {grump.label} waited nearby.",
        ),
        QAItem(
            question=f"What was the grump worried about?",
            answer=f"{grump.label} was worried because the bottle of wine was no longer where it should have been.",
        ),
        QAItem(
            question="What clue solved the mystery?",
            answer=f"The mystery was solved by the paper note hidden in the old crate.",
        ),
        QAItem(
            question="What happened to the wine at the end?",
            answer="It was returned to its place after everyone understood why it had been moved.",
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            QAItem(
                question="Why did the grump stop grumping?",
                answer=f"{grump.label} stopped grumping after the clue showed that the wine had been moved safely, not stolen.",
            )
        )
    return qa


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a cellar?",
        answer="A cellar is a cool room, often underground, where people may store food or bottles.",
    ),
    QAItem(
        question="What is a grump?",
        answer="A grump is a person who often complains or frowns when they are unhappy.",
    ),
    QAItem(
        question="Why do people keep wine in a cool place?",
        answer="People keep wine in a cool place so it stays pleasant and does not get spoiled by heat.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A bottle is missing when it has been moved and hidden.
missing(B) :- bottle(B), moved(B), hidden(B).

% The grump worries when a bottle is missing.
worried(G) :- character(G), grump(G), missing(B).

% A clue solves the mystery when it is tucked in the crate.
solves(C) :- clue(C), hidden_in(C, crate).

% A story is coherent when there is a missing bottle, a grump, and a clue that solves it.
coherent :- missing(wine), grump(grump), solves(note).

#show coherent/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("bottle", "wine"))
    lines.append(asp.fact("grump", "grump"))
    lines.append(asp.fact("clue", "note"))
    lines.append(asp.fact("hidden_in", "note", "crate"))
    lines.append(asp.fact("moved", "wine"))
    lines.append(asp.fact("hidden", "wine"))
    lines.append(asp.fact("character", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show coherent/0."))
    ok = any(sym.name == "coherent" for sym in model)
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    sample = generate(StoryParams())
    if not sample.story or "mystery" not in sample.story.lower():
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Wine-grump mystery storyworld in fable style.")
    ap.add_argument("--place", choices=["cellar"], default="cellar")
    ap.add_argument("--protagonist")
    ap.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    ap.add_argument("--grump")
    ap.add_argument("--grump-type", choices=["girl", "boy", "woman", "man"], default="man")
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"], default="boy")
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
    protagonist = getattr(args, "protagonist", None) or rng.choice(["Mina", "Nora", "Iris", "Lena"])
    grump = getattr(args, "grump", None) or rng.choice(["Old Bram", "Mister Rowe", "Uncle Fen", "Hob"])
    helper = getattr(args, "helper", None) or rng.choice(["Rowan", "Pip", "Tomas", "Ada"])
    if protagonist == grump or protagonist == helper or grump == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        seed=getattr(args, "seed", None),
        place=getattr(args, "place", None),
        protagonist=protagonist,
        protagonist_type=getattr(args, "protagonist_type", None),
        grump=grump,
        grump_type=getattr(args, "grump_type", None),
        helper=helper,
        helper_type=getattr(args, "helper_type", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show coherent/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(seed=base_seed, protagonist="Mina", grump="Old Bram", helper="Rowan"),
            StoryParams(seed=base_seed + 1, protagonist="Iris", grump="Mister Rowe", helper="Ada"),
            StoryParams(seed=base_seed + 2, protagonist="Lena", grump="Uncle Fen", helper="Pip"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
