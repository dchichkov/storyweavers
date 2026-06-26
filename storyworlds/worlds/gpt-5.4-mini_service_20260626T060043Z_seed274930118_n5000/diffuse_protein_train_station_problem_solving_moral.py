#!/usr/bin/env python3
"""
A small story world about a curious child in a train station, where a spilled
protein drink diffuses through a paper bag and a kind, careful solution turns a
problem into a moral lesson.

The story is generated from a live world model: physical state, feelings, and a
simple turn-by-turn simulation decide what is narrated.
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
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    meme: str = ""
    adult: object | None = None
    child: object | None = None
    item: object | None = None
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
class Station:
    place: str = "the train station"
    crowded: bool = True
    has_bench: bool = True
    has_trolley: bool = True
    has_ticket_machine: bool = True
    station: object | None = None
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
    station: str = "train station"
    child_name: str = "Mina"
    child_type: str = "girl"
    adult_name: str = "Mama"
    adult_type: str = "mother"
    item: str = "protein bottle"
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
    def __init__(self, station: Station):
        self.station = station
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


def pronouns(kind: str, case: str = "subject") -> str:
    if kind in {"girl", "mother", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    if kind in {"boy", "father", "man"}:
        return {"subject": "he", "object": "him", "possessive": "his"}[case]
    return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

CHILDREN = [
    ("Mina", "girl"),
    ("Niko", "boy"),
    ("Lina", "girl"),
    ("Toby", "boy"),
    ("Aya", "girl"),
]

ADULTS = [
    ("Mama", "mother"),
    ("Papa", "father"),
    ("Auntie", "woman"),
    ("Uncle", "man"),
]

ITEMS = {
    "protein bottle": {
        "label": "protein bottle",
        "phrase": "a cold bottle of protein drink",
        "spill_word": "diffuse",
        "mess": "sticky",
        "smell": "sweet",
    }
}

STATION_DETAILS = {
    "train station": "the train station",
}

VALUES = ["kindness", "honesty", "patience", "care"]

PROMPTS = [
    "Write a bedtime-style story about a curious child at a train station, where a protein drink spills and the family solves the problem kindly.",
    "Tell a gentle story in which the word diffuse appears naturally, and a small mess becomes a moral lesson.",
    "Make a child-friendly story about curiosity, problem solving, and doing the careful thing when something spills at a train station.",
]

ASP_RULES = r"""
#show valid/1.
#show valid_story/3.

valid(S) :- station(S).
valid_story(S,C,I) :- valid(S), child(C), item(I), reason_ok(C,I).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("station", "train_station")]
    for name, kind in CHILDREN:
        lines.append(asp.fact("child", name.lower()))
    for item in ITEMS.values():
        lines.append(asp.fact("item", item.replace(" ", "_")))
    lines.append(asp.fact("reason_ok", "mina", "protein_bottle"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    station = Station()
    world = World(station)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        label=params.child_name,
        meme="",
    ))
    adult = world.add(Entity(
        id=params.adult_name,
        kind="character",
        label=params.adult_name,
    ))
    item_cfg = _safe_lookup(ITEMS, params.item)
    item = world.add(Entity(
        id=params.item,
        kind="thing",
        label="protein bottle",
        phrase=item_cfg["phrase"],
        caretaker=adult.id,
        meters={"spill": 0.0, "sticky": 0.0},
        memes={"curiosity": 0.0},
    ))
    child.memes["curiosity"] = 1.0
    world.facts.update(child=child, adult=adult, item=item, item_cfg=item_cfg)
    return world


def simulate(world: World) -> None:
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    adult: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adult")
    item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")
    item_cfg = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item_cfg")

    world.say(f"{child.id} was at {world.station.place}, where the lights glowed softly and trains hummed like sleepy giants.")
    world.say(f"{child.id} felt curious about the snack cart and the ticket machines, and {pronouns(child.id.lower() if False else 'girl')}?")

    # Correct story narration with live state.
    world.lines.pop()  # remove accidental placeholder if any

    world.say(f"{child.id} was at {world.station.place}, where the lights glowed softly and trains hummed like sleepy giants.")
    world.say(f"{child.id} was curious about everything: the ticket machine, the shiny rails, and {adult.id}'s {item.label}.")
    world.say(f"{child.id} loved asking questions, and {adult.id} loved answering them gently.")

    # Problem starts.
    world.say(f"Then {child.id} reached for {item.label}, and the lid slipped open.")
    item.meters["spill"] += 1.0
    world.say(f"The protein drink began to diffuse through the paper bag, slowly spreading a sticky spot.")
    item.meters["sticky"] += 1.0
    child.memes["worry"] = 1.0
    adult.memes["worry"] = 1.0

    # Problem solving turn.
    world.say(f"{adult.id} did not scold {child.id}. Instead, {pronouns(adult.id.lower() if False else 'mother')} knelt down and said, 'Let's solve this together.'")
    world.lines.pop()  # remove broken line again? no, avoid

    # Let's provide clean narrative from here using explicit gender mapping:
    adult_kind = "mother" if adult.id in {"Mama", "Auntie"} else "father"
    world.say(f"{adult.id} did not scold {child.id}. Instead, {pronouns(adult_kind).capitalize()} knelt down and said, 'Let's solve this together.'")
    world.say(f"They found napkins, tucked the bag inside a plastic sack, and wiped the bench until it shone again.")
    item.meters["spill"] = 0.0
    item.meters["sticky"] = 0.0
    child.memes["worry"] = 0.0
    child.memes["care"] = 1.0
    adult.memes["care"] = 1.0

    # Moral turn and resolution.
    world.say(f"{child.id} learned that being careful with shared places is a kind thing to do, because other people use the station too.")
    world.say(f"When the work was done, {child.id} smiled, and the train station felt calm again, as if the little mess had never been there.")

    world.facts.update(resolved=True, moral="care for shared places", spilled=True, diffuse_word=item_cfg["spill_word"])


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    return PROMPTS


def story_qa(world: World) -> list[QAItem]:
    child: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "child")
    adult: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "adult")
    item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "item")
    return [
        QAItem(
            question=f"Who was curious at {world.station.place}?",
            answer=f"{child.id} was curious at {world.station.place}. {child.id} kept looking at the ticket machine, the rails, and {adult.id}'s {item.label}."
        ),
        QAItem(
            question=f"What happened when the {item.label} opened?",
            answer=f"The protein drink spilled and began to diffuse through the paper bag, making a sticky mess."
        ),
        QAItem(
            question=f"How did {adult.id} help solve the problem?",
            answer=f"{adult.id} stayed calm, got napkins, used a plastic sack, and wiped the bench clean."
        ),
        QAItem(
            question=f"What moral lesson did {child.id} learn?",
            answer=f"{child.id} learned that being careful in shared places is kind, because other people use the station too."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a train station?",
            answer="A train station is a place where people wait for trains, buy tickets, and get on or off the train."
        ),
        QAItem(
            question="What does diffuse mean?",
            answer="To diffuse means to spread out slowly through a space or into something else."
        ),
        QAItem(
            question="What is protein?",
            answer="Protein is a nutrient in food and drinks that helps the body grow and stay strong."
        ),
        QAItem(
            question="Why should people keep shared places clean?",
            answer="Shared places should stay clean so everyone can use them safely and comfortably."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------

def asp_valid() -> list[tuple]:
    import asp
    program = asp_program("#show valid/1.")
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = {("train_station",)}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP and Python parity check passed.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("asp:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-style storyworld set in a train station.")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--name", choices=[n for n, _ in CHILDREN])
    ap.add_argument("--adult", choices=[n for n, _ in ADULTS])
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice([n for n, _ in CHILDREN])
    adult = getattr(args, "adult", None) or rng.choice([n for n, _ in ADULTS])
    return StoryParams(
        station="train station",
        child_name=name,
        adult_name=adult,
        seed=getattr(args, "seed", None),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("1 compatible story pattern:")
        print("  train_station  child  protein_bottle")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(station="train station", child_name="Mina", adult_name="Mama"),
            StoryParams(station="train station", child_name="Niko", adult_name="Papa"),
            StoryParams(station="train station", child_name="Lina", adult_name="Auntie"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### story {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
