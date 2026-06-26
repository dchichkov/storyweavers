#!/usr/bin/env python3
"""
Standalone story world: a tall-tale cautionary sharing story in a laundry room.

A small, self-contained simulation where a child wants to share a treasured
thing in the laundry room, but a cautionary adult warns that the wrong kind of
sharing could damage a delicate artery-shaped repair in a toy creature called a
smurf. The story turns on a realistic risk, a concrete compromise, and a warm
resolution.
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
# Domain model
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    fragile: bool = False
    artery: object | None = None
    hero: object | None = None
    parent: object | None = None
    smurf: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the laundry room"
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
class Treasure:
    label: str
    phrase: str
    type: str
    fragile: bool = False
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
class Compromise:
    label: str
    prep: str
    tail: str
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
class StoryParams:
    name: str
    gender: str
    parent: str
    treasure: str
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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTING = Setting(place="the laundry room")

TREASURES = {
    "sock": Treasure(
        label="sock",
        phrase="a bright red sock",
        type="sock",
        fragile=True,
    ),
    "patch": Treasure(
        label="patch",
        phrase="a stitched patch for the old toy smurf",
        type="patch",
        fragile=True,
    ),
    "button": Treasure(
        label="button",
        phrase="a shiny brass button",
        type="button",
        fragile=True,
    ),
}

COMPROMISES = {
    "basket": Compromise(
        label="laundry basket",
        prep="set the treasure in the laundry basket first",
        tail="rolled the basket to the table and shared the work",
    ),
    "folding": Compromise(
        label="folding table",
        prep="place the treasure on the folding table first",
        tail="laid everything out neat as a parade drum",
    ),
    "line": Compromise(
        label="clothesline clip",
        prep="clip the treasure to the clothesline first",
        tail="hung it high and dry",
    ),
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure is risky to share in the laundry room if steam, soap, or spinning
% can reach it.
risky(T) :- treasure(T), fragile(T), room(laundry_room), can_spill(soap, T).

% A compromise is reasonable only if it keeps the risky treasure away from the
% wet floor and away from the spinning machine.
good_fix(C, T) :- compromise(C), treasure(T), risky(T), protects(C, T).

valid_story(P, T, C) :- person(P), treasure(T), compromise(C), good_fix(C, T).
"""


def asp_facts() -> str:
    import asp  # lazy import

    lines: list[str] = []
    lines.append(asp.fact("room", "laundry_room"))
    lines.append(asp.fact("person", "child"))
    lines.append(asp.fact("person", "parent"))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.fragile:
            lines.append(asp.fact("fragile", tid))
        lines.append(asp.fact("can_spill", "soap", tid))
    for cid, c in COMPROMISES.items():
        lines.append(asp.fact("compromise", cid))
        lines.append(asp.fact("protects", cid, "sock"))
        lines.append(asp.fact("protects", cid, "patch"))
        lines.append(asp.fact("protects", cid, "button"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def choose_treasure(name: str) -> Treasure:
    if name not in TREASURES:
        pass
    return _safe_lookup(TREASURES, name)


def choose_compromise(treasure: Treasure) -> Compromise:
    if treasure.label == "sock":
        return COMPROMISES["basket"]
    if treasure.label == "patch":
        return COMPROMISES["line"]
    return COMPROMISES["folding"]


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    smurf = world.add(Entity(id="Smurf", kind="thing", type="smurf", label="the little smurf"))
    artery = world.add(Entity(id="Artery", kind="thing", type="artery", label="the red artery", fragile=True))
    treasure = world.add(Entity(
        id="Treasure",
        kind="thing",
        type=params.treasure,
        label=choose_treasure(params.treasure).label,
        phrase=choose_treasure(params.treasure).phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))
    hero.memes["hope"] = 1
    hero.memes["sharing"] = 0
    smurf.meters["patched"] = 1
    artery.meters["delicate"] = 1

    comp = choose_compromise(_safe_lookup(TREASURES, params.treasure))

    # Act 1: setup, tall-tale flavor
    world.say(
        f"{hero.id} was a little {params.gender} with a grin as wide as a wagon wheel, "
        f"and {hero.pronoun('possessive')} favorite play place was {world.setting.place}."
    )
    world.say(
        f"Inside that laundry room stood {smurf.label}, a pocket-sized smurf no bigger than a spoon, "
        f"and beside {smurf.it()} shimmered {artery.label}, a thin red thread that kept the toy steady."
    )
    world.say(
        f"{hero.id} loved {treasure.phrase} and wanted to share {treasure.it()} with everybody."
    )

    # Act 2: cautionary warning
    world.para()
    hero.memes["desire"] = 1
    world.say(
        f"One windy afternoon, {hero.id} marched into the laundry room with {treasure.phrase} tucked under {hero.pronoun('possessive')} arm."
    )
    world.say(
        f"{hero.id} wanted to let {smurf.label} play with {treasure.it()}, but {parent.label} gave a cautionary cough."
    )
    world.say(
        f'"Don\'t dismiss the warning," said {parent.label}. "A splash of soap or a tumble by the washer could nip that delicate artery and spoil the whole sharing plan."'
    )
    hero.memes["dismissed_warning"] = 1

    # Act 3: compromise and resolution
    world.para()
    world.say(
        f"{hero.id} paused, looked at {smurf.label}, and did not dismiss the caution after all."
    )
    world.say(
        f'Instead, {hero.id} and {parent.label} chose to {comp.prep}.'
    )
    hero.memes["sharing"] = 1
    hero.memes["joy"] = 1
    world.say(
        f"Then they shared the work and the wonder, and {comp.tail}."
    )
    world.say(
        f"In the end, {smurf.label} stayed safe, {artery.label} stayed straight and sound, and {hero.id} learned that sharing is grandest when it is careful."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        smurf=smurf,
        artery=artery,
        treasure=treasure,
        compromise=comp,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    treasure: Entity = _safe_fact(world, f, "treasure")
    return [
        f'Write a tall-tale style story set in a laundry room about {hero.id} learning to share {treasure.phrase} carefully.',
        f"Tell a cautionary story where the word 'dismiss' matters and a smurf and an artery must stay safe.",
        f"Write a child-friendly story about sharing in the laundry room that ends with a clever compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    treasure: Entity = _safe_fact(world, f, "treasure")
    comp: Compromise = _safe_fact(world, f, "compromise")
    smurf: Entity = _safe_fact(world, f, "smurf")
    artery: Entity = _safe_fact(world, f, "artery")
    return [
        QAItem(
            question=f"What did {hero.id} want to share in the laundry room?",
            answer=f"{hero.id} wanted to share {treasure.phrase} with {smurf.label}.",
        ),
        QAItem(
            question=f"Why did {parent.label} give a cautionary warning?",
            answer=f"{parent.label} warned that soap or the washer could damage {artery.label} and spoil the sharing plan.",
        ),
        QAItem(
            question=f"What careful plan did {hero.id} and {parent.label} choose?",
            answer=f"They used the {comp.label} so the treasure could be shared without hurting {smurf.label} or {artery.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a smurf in stories like this?",
            answer="A smurf is a tiny imaginary little character, usually cheerful and blue in classic stories.",
        ),
        QAItem(
            question="What is an artery?",
            answer="An artery is a blood vessel that carries blood through a body, so in a story it can stand for something delicate and important.",
        ),
        QAItem(
            question="Why is a laundry room a risky place for fragile things?",
            answer="A laundry room can have soap, water, and spinning machines, so fragile things can get wet or bumped.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------
def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    # Reasonableness gate is intentionally small: one story shape.
    py = {("child", "sock", "basket"), ("child", "patch", "line"), ("child", "button", "folding")}
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(cl)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("Python:", sorted(py))
    print("ASP:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale cautionary sharing story in a laundry room.")
    ap.add_argument("--name", default="Milo")
    ap.add_argument("--gender", choices=["boy", "girl"], default="boy")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
    ap.add_argument("--treasure", choices=sorted(TREASURES), default=None)
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
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    return StoryParams(
        name=getattr(args, "name", None),
        gender=getattr(args, "gender", None),
        parent=getattr(args, "parent", None),
        treasure=treasure,
        seed=getattr(args, "seed", None),
    )


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for treasure in TREASURES:
            params = StoryParams(
                name=getattr(args, "name", None),
                gender=getattr(args, "gender", None),
                parent=getattr(args, "parent", None),
                treasure=treasure,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
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
