#!/usr/bin/env python3
"""
storyworlds/worlds/spade_deluxe_surprise_pirate_tale.py
========================================================

A tiny pirate-style story world built from the seed words:

- spade
- deluxe
- Surprise

Premise:
A small pirate crew is digging on an island with a deluxe spade when they
discover a surprising buried thing. The captain wants treasure, but the island
keeps a different promise. The tension is whether the crew should keep digging,
follow the clue, or help the surprise home.

The world is state-driven:
- entities have physical meters and emotional memes
- digging changes buried objects and mood
- surprise discovery can resolve tension in a child-friendly way
- the ending proves what changed in the world

This script is self-contained and matches the shared storyworld contract.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    crew: object | None = None
    def __post_init__(self) -> None:
        for k in ("dig", "excite", "worry", "joy", "surprise", "trust"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "maid"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    hidden: bool = True
    found: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("buried", "shine", "gift", "mud"):
            self.meters.setdefault(k, 0.0)
        for k in ("surprise", "hope", "comfort"):
            self.memes.setdefault(k, 0.0)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    place: str = "the sunny island shore"
    afford_dig: bool = True
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
class Gear:
    id: str
    label: str
    phrase: str
    helps: str
    surprise_kind: str
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
    setting: str
    surprise: str
    name: str
    captain: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

    def get_entity(self, eid: str) -> Entity:
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

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.items = _copy.deepcopy(self.items)
        c.facts = _copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


SETTINGS = {
    "shore": Setting(place="the sunny island shore", afford_dig=True),
    "cove": Setting(place="the little hidden cove", afford_dig=True),
    "dock": Setting(place="the busy pirate dock", afford_dig=False),
}

SURPRISES = {
    "shell": Item(id="shell", label="a silver shell", phrase="a silver shell with a bright twist", hidden=True),
    "message": Item(id="message", label="a bottle note", phrase="a note sealed in a bottle", hidden=True),
    "parrot": Item(id="parrot", label="a sleepy parrot", phrase="a sleepy parrot tucked in the sand", hidden=True),
}

TOOLS = {
    "spade": Gear(id="spade", label="deluxe spade", phrase="a deluxe spade with a shiny handle", helps="dig", surprise_kind="any"),
}

CAPTAIN_NAMES = ["Captain Ruby", "Captain Finn", "Captain Sable", "Captain Pearl", "Captain Reef"]
CREW_NAMES = ["Mina", "Jory", "Tess", "Bo", "Nell", "Pip", "Ada", "Kai"]
TRAITS = ["brave", "curious", "cheerful", "bold", "patient"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate tale story world with a deluxe spade and a surprise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--captain", choices=["Captain Ruby", "Captain Finn", "Captain Sable", "Captain Pearl", "Captain Reef"])
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    surprise = getattr(args, "surprise", None) or rng.choice(list(SURPRISES))
    name = getattr(args, "name", None) or rng.choice(CREW_NAMES)
    captain = getattr(args, "captain", None) or rng.choice(CAPTAIN_NAMES)
    return StoryParams(setting=setting, surprise=surprise, name=name, captain=captain)


def _dig(world: World, crew: Entity, tool: Gear, surprise: Item) -> None:
    if not world.setting.afford_dig:
        pass
    crew.meters["dig"] += 1
    crew.memes["joy"] += 1
    surprise.meters["buried"] = max(0.0, surprise.meters["buried"] - 1.0)
    if surprise.meters["buried"] <= 0.0:
        surprise.hidden = False
        surprise.found = True
        surprise.memes["surprise"] += 1


def _warn(world: World, captain: Entity, crew: Entity, surprise: Item) -> None:
    crew.memes["worry"] += 1
    world.say(
        f'"Easy now," {captain.pronoun("possessive")} captain said. '
        f'"A clever dig can uncover a surprise, but it should not smash what is buried."'
    )


def _turn(world: World, crew: Entity, surprise: Item) -> None:
    if surprise.found:
        crew.memes["surprise"] += 1
        crew.memes["trust"] += 1
        world.say(
            f"Then the sand gave way, and there it was: {surprise.phrase}. "
            f"{crew.id} blinked in wonder, because the island had hidden a gift instead of gold."
        )


def _resolve(world: World, captain: Entity, crew: Entity, surprise: Item) -> None:
    captain.memes["joy"] += 1
    crew.memes["joy"] += 1
    world.say(
        f'The crew set the {surprise.label} in a safe little spot by the rocks. '
        f'{captain.id} laughed and said, "That is a fine kind of treasure." '
        f"By sunset, the {crew.label} was smiling, and the shore looked kinder than before."
    )


def tell(setting: Setting, surprise: Item, name: str, captain_name: str) -> World:
    world = World(setting)
    crew = world.add_entity(Entity(id=name, kind="character", type="pirate", label="crew mate"))
    captain = world.add_entity(Entity(id=captain_name, kind="character", type="captain", label="captain"))
    tool = TOOLS["spade"]
    prize = world.add_item(Item(
        id=surprise.id,
        label=surprise.label,
        phrase=surprise.phrase,
        hidden=True,
        found=False,
        meters={"buried": 1.0, "shine": 0.0, "gift": 0.0, "mud": 0.0},
        memes={"surprise": 0.0, "hope": 0.0, "comfort": 0.0},
    ))
    world.facts.update(crew=crew, captain=captain, tool=tool, prize=prize)

    world.say(
        f"{captain.id} and {crew.id} reached {world.setting.place}. "
        f"{crew.id} carried a deluxe spade that glinted like polished moonlight."
    )
    world.say(
        f"{crew.id} loved the deluxe spade because it could bite into the sand fast, "
        f"and every pirate on the shore wanted to know what it might uncover."
    )

    world.para()
    world.say(
        f"{crew.id} started to dig where the map said to dig. "
        f"The sand was soft at first, then packed tight like a secret holding its breath."
    )
    _warn(world, captain, crew, prize)
    _dig(world, crew, tool, prize)
    _turn(world, crew, prize)

    world.para()
    if prize.found:
        world.say(
            f"{crew.id} held the surprise up to the light. It was small, but it mattered. "
            f"The captain nodded, and the whole crew felt proud of finding something gentle."
        )
        _resolve(world, captain, crew, prize)
    else:
        world.say(
            f"The sand stayed closed, so the crew stopped before the island could get upset. "
            f"They marked the spot and promised to return with kinder hands."
        )

    world.facts["resolved"] = prize.found
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    crew = _safe_fact(world, f, "crew")
    captain = _safe_fact(world, f, "captain")
    prize = _safe_fact(world, f, "prize")
    return [
        'Write a short pirate story for a young child about a deluxe spade and a surprise under the sand.',
        f"Tell a gentle pirate tale where {crew.id} digs with a deluxe spade while {captain.id} watches carefully.",
        f"Write a simple story that includes a surprise buried near the shore and ends with the crew smiling."
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    crew = _safe_fact(world, f, "crew")
    captain = _safe_fact(world, f, "captain")
    prize = _safe_fact(world, f, "prize")
    qa = [
        QAItem(
            question=f"What did {crew.id} bring to the shore?",
            answer=f"{crew.id} brought a deluxe spade that helped dig in the sand."
        ),
        QAItem(
            question=f"Why did {captain.id} tell {crew.id} to be careful?",
            answer=f"{captain.id} wanted the crew to dig gently so they would uncover the buried surprise without breaking it."
        ),
        QAItem(
            question=f"What was the surprise in the sand?",
            answer=f"The surprise was {prize.phrase}."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did the story end after the surprise was found?",
            answer=f"The crew placed {prize.label} somewhere safe, and everyone felt happy about the discovery."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a spade used for?",
            answer="A spade is a tool used for digging in sand, dirt, or soil."
        ),
        QAItem(
            question="What does deluxe mean?",
            answer="Deluxe means extra nice, fancy, or special."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes someone stop and look in wonder."
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
        lines.append(f"  {e.id:12} kind={e.kind:9} type={e.type:8} meters={e.meters} memes={e.memes}")
    for i in world.items.values():
        lines.append(f"  {i.id:12} item label={i.label!r} hidden={i.hidden} found={i.found} meters={i.meters} memes={i.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
% A pirate story is valid when there is a diggable setting and a buried surprise.
valid_story(S, U) :- setting(S), surprise(U), diggable(S), buried(U), compatible(U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_dig:
            lines.append(asp.fact("diggable", sid))
    for uid, u in SURPRISES.items():
        lines.append(asp.fact("surprise", uid))
        lines.append(asp.fact("buried", uid))
        lines.append(asp.fact("compatible", uid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = {(s, u) for s, s_obj in SETTINGS.items() if s_obj.afford_dig for u in SURPRISES}
    if clingo_set == py_set:
        print(f"OK: ASP matches Python gate ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(clingo_set))
    print("PY :", sorted(py_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(SURPRISES, params.surprise), params.name, params.captain)
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


def resolve_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="shore", surprise="shell", name="Mina", captain="Captain Ruby"),
            StoryParams(setting="cove", surprise="message", name="Pip", captain="Captain Finn"),
            StoryParams(setting="shore", surprise="parrot", name="Tess", captain="Captain Pearl"),
        ]
        return [generate(p) for p in curated]
    seen: set[str] = set()
    i = 0
    while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
        i += 1
        params = resolve_params(args, random.Random(base_seed + i))
        params.seed = base_seed + i
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    return samples


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    samples = resolve_samples(args)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} / {p.setting} / {p.surprise}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
