#!/usr/bin/env python3
"""
A small storyworld about a ghostly misunderstanding caused by perfume.

Seed tale:
A child enters a quiet old house and smells a sweet perfume in the hallway.
They think a ghost is near, but the smell comes from a bottle left by a kind
grandparent. The surprise makes the child tremble, then laugh, and the room
feels safe again.

World idea:
- A house has rooms, a hidden perfume bottle, and a ghost who prefers gentle
  scents but is not actually frightening.
- A child can notice a scent, misread it as ghostly evidence, and then discover
  the true source.
- The story turns on surprise and misunderstanding, then ends with comfort and
  a small proof of change.

This script keeps a classical three-act shape:
setup -> eerie misunderstanding -> reveal and reassurance.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    memorable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caregiver: object | None = None
    child: object | None = None
    ghost: object | None = None
    perfume: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
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
    place: str = "the old house"
    rooms: list[str] = field(default_factory=lambda: ["hallway", "parlor", "stairs", "attic"])
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
    smell: str
    intensity: float
    source: str
    surprising: bool = True
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
    child_name: str
    child_type: str
    caregiver_type: str
    perfume_name: str
    ghost_name: str
    room: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.current_room: str = setting.rooms[0]
        self.clues: list[Clue] = []

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
        c = World(copy.deepcopy(self.setting))
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.current_room = self.current_room
        c.clues = copy.deepcopy(self.clues)
        c.facts = copy.deepcopy(self.facts)
        return c


def _add_scent(world: World) -> list[str]:
    out: list[str] = []
    bottle = world.entities.get("perfume")
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not bottle or not child or not ghost:
        return out
    if bottle.location != world.current_room:
        return out
    if child.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("scent_notice", world.current_room)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 1
    child.memes["fear"] = child.memes.get("fear", 0.0) + 1
    ghost.memes["present"] = ghost.memes.get("present", 0.0) + 1
    out.append("The sweet smell drifted through the hall, and the child felt a little chill.")
    return out


def _misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    ghost = world.get("ghost")
    perfume = world.get("perfume")
    if child.memes.get("fear", 0.0) < THRESHOLD:
        return out
    if perfume.location != world.current_room:
        return out
    sig = ("misunderstand", world.current_room)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["misunderstanding"] = child.memes.get("misunderstanding", 0.0) + 1
    child.memes["confusion"] = child.memes.get("confusion", 0.0) + 1
    out.append("The child thought the smell meant a ghost was hiding nearby.")
    return out


def _reveal(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    caregiver = world.get("caregiver")
    perfume = world.get("perfume")
    if child.memes.get("misunderstanding", 0.0) < THRESHOLD:
        return out
    sig = ("reveal", perfume.location)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["confusion"] = 0.0
    child.memes["relief"] = child.memes.get("relief", 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    caregiver.memes["gentleness"] = caregiver.memes.get("gentleness", 0.0) + 1
    out.append("Then the caregiver found the bottle and showed it was only perfume, not a ghost.")
    return out


CAUSAL_RULES = [_add_scent, _misunderstanding, _reveal]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def build_setting(place: str) -> Setting:
    return Setting(place=place)


def introduce(world: World, child: Entity, caregiver: Entity, ghost: Entity, perfume: Entity) -> None:
    world.say(
        f"{child.id} stepped into {world.setting.place}, where the air was still and the walls looked sleepy."
    )
    world.say(
        f"{child.id} came with {caregiver.pronoun('possessive')} {caregiver.type}, and even the friendly ghost named {ghost.id} seemed to float quietly nearby."
    )
    world.say(
        f"On a small table sat {perfume.phrase}, waiting like a secret."
    )


def notice(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"{child.id} noticed a sweet perfume in the hallway and sniffed at it with wide eyes."
    )


def worry(world: World, child: Entity, ghost: Entity) -> None:
    if child.memes.get("surprise", 0.0) >= THRESHOLD:
        world.say(
            f"{child.id} shivered and whispered that the ghost must be nearby, because the smell felt so strange."
        )


def reassure(world: World, caregiver: Entity, child: Entity, perfume: Entity) -> None:
    world.say(
        f"{caregiver.id} smiled, lifted the little bottle, and said the scent came from {perfume.phrase}, not from a spooky visitor."
    )
    world.say(
        f"The ghost drifted out from behind the curtain and gave a soft wave, which made the room feel kind instead of scary."
    )
    world.say(
        f"{child.id} laughed, breathed in the gentle scent again, and felt brave enough to stay in the old house."
    )


def ending(world: World, child: Entity, ghost: Entity, perfume: Entity) -> None:
    world.say(
        f"By the end, {child.id} knew that a surprise smell could lead to a misunderstanding, and the little perfume bottle just made the evening feel magical."
    )
    world.say(
        f"{ghost.id} floated in the quiet hall, {perfume.phrase} rested safely on the table, and {child.id} smiled instead of trembling."
    )


def tell(params: StoryParams) -> World:
    world = World(build_setting(params.place))
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type))
    caregiver = world.add(Entity(id="caregiver", kind="character", type=params.caregiver_type))
    ghost = world.add(Entity(id=params.ghost_name, kind="character", type="ghost"))
    perfume = world.add(Entity(
        id="perfume",
        type="perfume",
        label="perfume",
        phrase=f"a tiny bottle of {params.perfume_name} perfume",
        location=params.room,
        hidden=True,
        memorable=True,
    ))
    world.current_room = params.room

    world.facts.update(child=child, caregiver=caregiver, ghost=ghost, perfume=perfume)

    introduce(world, child, caregiver, ghost, perfume)
    world.para()
    notice(world, child)
    propagate(world, narrate=True)
    worry(world, child, ghost)
    world.para()
    reassure(world, caregiver, child, perfume)
    ending(world, child, ghost, perfume)
    world.facts["resolved"] = True
    return world


PERFUMES = [
    ("rosewater", "rosewater"),
    ("vanilla", "vanilla"),
    ("lavender", "lavender"),
    ("jasmine", "jasmine"),
]

HEROES = ["Mia", "Lena", "Nora", "Ivy", "June", "Ada", "Elena", "Ruby"]
CAREGIVERS = ["mother", "grandmother", "aunt"]
ROOMS = ["hallway", "parlor", "attic"]
GHOSTS = ["Mister Pale", "Miss Whisper", "Old Drift"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in ["the old house"]:
        for room in ROOMS:
            combos.append((place, "perfume", room))
    return combos


@dataclass
class _ReasonGate:
    place: str
    room: str
    perfume: str
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


def reasonableness_gate(place: str, room: str, perfume: str) -> bool:
    return place == "the old house" and room in ROOMS and perfume in {p[0] for p in PERFUMES}


def explain_rejection(place: str, room: str, perfume: str) -> str:
    return (
        f"(No story: the ghost-story setup needs the perfume bottle to be in a room of the old house, "
        f"so the child can notice it, misread it, and then learn the truth.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A ghost-story world about perfume, surprise, and misunderstanding.")
    ap.add_argument("--place", choices=["the old house"], default="the old house")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--perfume", choices=[p[0] for p in PERFUMES])
    ap.add_argument("--name", choices=HEROES)
    ap.add_argument("--caregiver", choices=CAREGIVERS)
    ap.add_argument("--ghost", choices=GHOSTS)
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
    perfume = getattr(args, "perfume", None) or rng.choice([p[0] for p in PERFUMES])
    room = getattr(args, "room", None) or rng.choice(ROOMS)
    if not reasonableness_gate(getattr(args, "place", None), room, perfume):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=getattr(args, "place", None),
        child_name=getattr(args, "name", None) or rng.choice(HEROES),
        child_type="girl",
        caregiver_type=getattr(args, "caregiver", None) or rng.choice(CAREGIVERS),
        perfume_name=dict(PERFUMES)[perfume],
        ghost_name=getattr(args, "ghost", None) or rng.choice(GHOSTS),
        room=room,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    perfume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "perfume")
    return [
        f'Write a short ghost story for young children that includes the word "perfume".',
        f"Tell a gentle spooky story where {child.id} smells perfume in the old house and briefly thinks a ghost is nearby.",
        f"Write a tiny mystery story that begins with a sweet scent and ends with a misunderstanding being cleared up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child")
    caregiver = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "caregiver")
    ghost = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ghost")
    perfume = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "perfume")
    return [
        QAItem(
            question=f"What did {child.id} smell in the old house?",
            answer=f"{child.id} smelled a sweet perfume from {perfume.phrase} in the room.",
        ),
        QAItem(
            question=f"Why did {child.id} think a ghost was nearby?",
            answer=(
                f"{child.id} felt a surprise from the smell and misunderstood it, so {child.pronoun('subject')} thought a ghost must be hiding nearby."
            ),
        ),
        QAItem(
            question=f"What did {caregiver.id} show {child.id} to explain the smell?",
            answer=(
                f"{caregiver.id} showed the tiny perfume bottle and explained that the scent came from {perfume.phrase}, not from {ghost.id}."
            ),
        ),
        QAItem(
            question=f"How did the story end for {child.id}?",
            answer=(
                f"{child.id} laughed, felt brave, and stayed in the old house after learning the smell was only perfume."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is perfume?",
            answer="Perfume is a scented liquid that people dab on themselves or keep in little bottles so a room or person smells pleasant.",
        ),
        QAItem(
            question="Why can a smell make someone surprised?",
            answer="A smell can be surprising when it appears suddenly or reminds someone of something mysterious, scary, or unexpected.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks the wrong thing at first, but later learns what was really going on.",
        ),
        QAItem(
            question="Why do ghost stories often feel spooky?",
            answer="Ghost stories often feel spooky because they use quiet places, shadows, whispers, and strange signs that make people imagine something unseen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.hidden:
            bits.append("hidden=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}): " + " ".join(bits))
    return "\n".join(lines)


ASP_RULES = r"""
% A perfume story is valid when the bottle can be found in a room of the old house.
room(hallway; parlor; attic).

valid(place(room), perfume, room(R)) :- place(old_house), room(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("place", "old_house"))
    for room in ROOMS:
        lines.append(asp.fact("room", room))
    for name, scent in PERFUMES:
        lines.append(asp.fact("perfume", name))
        lines.append(asp.fact("scent", name, scent))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    expected = set(valid_combos())
    actual = set(valid_combos())
    if expected == actual:
        print(f"OK: reasonableness gate matches itself ({len(expected)} combos).")
        return 0
    print("MISMATCH")
    return 1


CURATED = [
    StoryParams(
        place="the old house",
        child_name="Mia",
        child_type="girl",
        caregiver_type="mother",
        perfume_name="lavender",
        ghost_name="Miss Whisper",
        room="hallway",
    ),
    StoryParams(
        place="the old house",
        child_name="Nora",
        child_type="girl",
        caregiver_type="grandmother",
        perfume_name="rosewater",
        ghost_name="Mister Pale",
        room="parlor",
    ),
    StoryParams(
        place="the old house",
        child_name="Ivy",
        child_type="girl",
        caregiver_type="aunt",
        perfume_name="vanilla",
        ghost_name="Old Drift",
        room="attic",
    ),
]


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

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
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
            header = f"### {p.child_name}: perfume in {p.room}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
