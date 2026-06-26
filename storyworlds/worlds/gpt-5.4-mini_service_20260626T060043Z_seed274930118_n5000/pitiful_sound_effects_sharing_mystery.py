#!/usr/bin/env python3
"""
A small storyworld about a mystery of pitiful sound effects and sharing.

Premise:
A child hears a pitiful sound effect in a quiet place and wants to find out
where it is coming from. The only clue is a tiny shared object, and the mystery
resolves when the children decide to share carefully and discover the cause.

This world keeps the story close to mystery: a clue, a search, a false worry,
and a gentle reveal.
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
# Model
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    child_a: object | None = None
    child_b: object | None = None
    clue: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
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
class Room:
    name: str
    darkness: bool = False
    nooks: list[str] = field(default_factory=list)
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


@dataclass
class Clue:
    label: str
    sound: str
    source: str
    hidden_in: str
    true_note: str
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
    room: str
    clue: str
    child_a: str
    child_b: str
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
    def __init__(self, room: Room):
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

ROOMS = {
    "attic": Room("the attic", darkness=True, nooks=["old trunks", "a dusty rug", "a low window"]),
    "kitchen": Room("the kitchen", darkness=False, nooks=["under the table", "by the sink", "behind the chair"]),
    "closet": Room("the closet", darkness=True, nooks=["on a shelf", "in a shoe box", "behind coats"]),
    "playroom": Room("the playroom", darkness=False, nooks=["behind blocks", "under a blanket fort", "next to a basket"]),
}

CLUES = {
    "toy_mouse": Clue(
        label="a toy mouse",
        sound="pitiful squeak",
        source="a little mouse toy with a loose wheel",
        hidden_in="a shoe box",
        true_note="the wheel was rubbing on the box",
    ),
    "music_box": Clue(
        label="a music box",
        sound="pitiful tinkle",
        source="an old music box with one bent tooth",
        hidden_in="behind coats",
        true_note="one tooth was catching and making the tiny note wobble",
    ),
    "speaker": Clue(
        label="a small speaker",
        sound="pitiful beep",
        source="a small speaker with a weak battery",
        hidden_in="under the table",
        true_note="the battery was low and the sound came out thin",
    ),
    "balloon": Clue(
        label="a balloon",
        sound="pitiful squeal",
        source="a balloon rubbing on a shelf corner",
        hidden_in="on a shelf",
        true_note="the balloon kept brushing the wood",
    ),
}

CHILD_NAMES = ["Mia", "Leo", "Nora", "Sam", "Ava", "Theo", "Ivy", "Ben"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle mystery about pitiful sounds and sharing.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--child-a")
    ap.add_argument("--child-b")
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
    room = getattr(args, "room", None) or rng.choice(list(ROOMS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    a = getattr(args, "child_a", None) or rng.choice(CHILD_NAMES)
    b = getattr(args, "child_b", None) or rng.choice([n for n in CHILD_NAMES if n != a])
    if a == b:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(room=room, clue=clue, child_a=a, child_b=b)


def mismatch_reason(room: str, clue: str) -> str:
    if room == "kitchen" and clue == "music_box":
        return "The kitchen is too bright and busy for that kind of soft hidden mystery."
    return "That combination does not make a clear enough mystery."


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for room in ROOMS:
        for clue in CLUES:
            out.append((room, clue))
    return out


def choose_children(rng: random.Random, a: Optional[str], b: Optional[str]) -> tuple[str, str]:
    first = a or rng.choice(CHILD_NAMES)
    second = b or rng.choice([n for n in CHILD_NAMES if n != first])
    if first == second:
        pass
    return first, second


# ---------------------------------------------------------------------------
# World construction and narration
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    room = _safe_lookup(ROOMS, params.room)
    clue_def = _safe_lookup(CLUES, params.clue)
    world = World(room)

    child_a = world.add(Entity(id=params.child_a, kind="character", type="child", label=params.child_a, meters={}, memes={"curiosity": 1.0}))
    child_b = world.add(Entity(id=params.child_b, kind="character", type="child", label=params.child_b, meters={}, memes={"curiosity": 1.0}))
    clue = world.add(Entity(id="clue", type=clue_def.label, label=clue_def.label, phrase=clue_def.source, owner=child_a.id, held_by=None))

    world.facts.update(room=room, clue=clue_def, child_a=child_a, child_b=child_b)

    # Act 1
    world.say(f"{child_a.id} and {child_b.id} were in {room.name} on a quiet afternoon.")
    world.say(f"They were sharing a little basket of toys and taking turns the careful way.")
    world.say(f"Then they heard a pitiful {clue_def.sound} from somewhere nearby.")

    # Act 2
    world.para()
    world.say(f"{child_a.id} stopped and listened. {child_b.id} held still too.")
    world.say(f'"Did you hear that?" {child_a.id} asked. "It sounded like something was asking for help."')
    world.say(f"They followed the sound past {room.nooks[0]}, then past {room.nooks[1]}.")
    world.say(f"The clue seemed to move, but really it was only hiding in {clue_def.hidden_in}.")

    # Turn
    world.para()
    world.say(f"{child_b.id} reached first, but instead of grabbing the toy, {child_b.id} said, " +
              f'"Let us share the search."')
    world.say(f"So they peered together and found {clue_def.source}.")
    world.say(f"The mystery made sense at last: {clue_def.true_note}.")

    # Ending
    world.say(f"{child_a.id} smiled. {child_b.id} smiled too.")
    world.say(f"They shared the clue between them, and the pitiful sound became a funny little sound effect instead of a scary one.")
    world.say(f"By the end, the room felt calm again, and the children kept sharing the rest of their toys.")

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
    return [
        f"Write a short mystery story for young children in {f['room'].name} about a pitiful sound effect and sharing.",
        f"Tell a gentle story where {f['child_a'].id} and {f['child_b'].id} hear a pitiful sound and solve the mystery together.",
        f"Write a child-friendly mystery that includes a pitiful sound effect, careful listening, and two children sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    room: Room = _safe_fact(world, f, "room")
    clue: Clue = _safe_fact(world, f, "clue")
    a: Entity = _safe_fact(world, f, "child_a")
    b: Entity = _safe_fact(world, f, "child_b")
    return [
        QAItem(
            question=f"Where did {a.id} and {b.id} hear the pitiful sound?",
            answer=f"They heard it in {room.name}, where they were quietly sharing toys and listening carefully.",
        ),
        QAItem(
            question=f"What kind of sound did they hear?",
            answer=f"They heard a pitiful {clue.sound}, which was the clue that started the mystery.",
        ),
        QAItem(
            question=f"What did the children do to solve the mystery?",
            answer=f"They shared the search, listened together, and found {clue.source}.",
        ),
        QAItem(
            question=f"Why did the sound stop feeling scary?",
            answer=f"It stopped feeling scary because they learned what made it and turned the mystery into a shared discovery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what is really happening.",
        ),
        QAItem(
            question="Why is sharing helpful?",
            answer="Sharing is helpful because two people can look, listen, and think together, which can make a hard problem easier.",
        ),
        QAItem(
            question="What does a pitiful sound mean?",
            answer="A pitiful sound is a soft, sad, or needy sound that makes you want to look closer and see what needs help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"room: {world.room.name}")
    for e in list(world.entities.values()):
        bits = []
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room(R) :- room_fact(R).
clue(C) :- clue_fact(C).

mystery(R,C) :- room(R), clue(C), clue_works(R,C).
share_solution(R,C) :- mystery(R,C), sharing(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for rid in ROOMS:
        lines.append(asp.fact("room_fact", rid))
    for cid in CLUES:
        lines.append(asp.fact("clue_fact", cid))
    for rid, room in ROOMS.items():
        for cid, clue in CLUES.items():
            lines.append(asp.fact("clue_works", rid, cid))
            lines.append(asp.fact("sharing", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} mystery combos:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for room in ROOMS:
            for clue in CLUES:
                params = StoryParams(room=room, clue=clue, child_a="Mia", child_b="Leo")
                samples.append(generate(params))
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
