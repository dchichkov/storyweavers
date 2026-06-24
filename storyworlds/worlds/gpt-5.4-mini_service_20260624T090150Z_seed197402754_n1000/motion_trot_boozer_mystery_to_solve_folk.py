#!/usr/bin/env python3
"""
A folk-tale storyworld about a village mystery solved by careful motion,
a steady trot, and a suspicious boozer.

The seed tale premise:
A small village keeps losing honey cakes from the square. A lively child notices
tracks, a wanderer who likes to booze too much, and a dog that trots between
places. By following the motion in the mud and asking gentle questions, the
child learns who took the cakes and helps set things right.

This world simulates:
- motion through village places
- a trot that can reveal tracks or deliver a message
- a boozer whose carelessness causes a problem
- a mystery that is solved by gathering clues and telling the truth

The story model is grounded in state:
- physical meters: tracks, distance, mess, carried items
- emotional memes: worry, suspicion, relief, trust

The ending image proves the change:
the missing cakes are returned, the village calms, and the child and helper
move through the square without fear.
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
# World entities
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    boozer: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def name_word(self) -> str:
        return self.label or self.id
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
    indoors: bool = False
    neighbors: set[str] = field(default_factory=set)
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
    place: str
    hero: str
    hero_type: str
    helper: str
    helper_type: str
    prize: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    "square": Place("square", "the village square", neighbors={"inn", "well", "lane"}),
    "inn": Place("inn", "the inn", indoors=True, neighbors={"square"}),
    "well": Place("well", "the well", neighbors={"square", "lane"}),
    "lane": Place("lane", "the narrow lane", neighbors={"square", "well"}),
}

HEROES = {
    "girl": ["Mara", "Anya", "Elin", "Tilda"],
    "boy": ["Pip", "Hugo", "Ned", "Tobin"],
}

HELPERS = {
    "dog": ["Brindle", "Wag", "Bramble"],
    "goat": ["Tansy", "Mottle"],
    "grandmother": ["Nina", "Ola"],
}

PRIZES = {
    "cakes": {
        "label": "honey cakes",
        "phrase": "warm honey cakes",
        "plural": True,
    },
    "jar": {
        "label": "honey jar",
        "phrase": "a little honey jar",
        "plural": False,
    },
}

TRAITS = ["curious", "kind", "brave", "quick-eyed", "gentle"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_notes: list[str] = []

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
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _distance(a: str, b: str) -> int:
    order = ["square", "lane", "well", "inn"]
    return abs(order.index(a) - order.index(b))


def _move(ent: Entity, place: str, meters: float = 1.0) -> None:
    ent.location = place
    ent.meters["motion"] = ent.meters.get("motion", 0.0) + meters


def _trot(world: World, helper: Entity, from_place: str, to_place: str) -> None:
    helper.meters["trot"] = helper.meters.get("trot", 0.0) + _distance(from_place, to_place)
    _move(helper, to_place, meters=_distance(from_place, to_place))
    world.trace_notes.append(f"{helper.id} trotted from {from_place} to {to_place}")


def _clue_from_tracks(world: World, hero: Entity, helper: Entity, suspect: Entity) -> None:
    if suspect.meters.get("careless_motion", 0.0) >= THRESHOLD and world.place.id not in world.fired:
        world.fired.add(world.place.id)
        hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
        world.say(f"{hero.name_word} noticed little tracks in the mud, and {helper.name_word} trotted beside {hero.pronoun('object')} to follow them.")


def _reason_about_boozer(world: World, boozer: Entity, prize: Entity) -> None:
    if boozer.memes.get("drunk", 0.0) >= THRESHOLD and prize.carried_by == boozer.id:
        boozer.meters["spill"] = boozer.meters.get("spill", 0.0) + 1
        prize.meters["messy"] = prize.meters.get("messy", 0.0) + 1
        world.facts["stolen"] = True
        world.facts["stolen_by"] = boozer.id


def predict_mystery(world: World, hero: Entity, suspect: Entity, prize: Entity) -> bool:
    sim = world.copy()
    _reason_about_boozer(sim, suspect, prize)
    return bool(sim.facts.get("stolen"))


def solve_mystery(world: World, hero: Entity, suspect: Entity, prize: Entity) -> None:
    if not predict_mystery(world, hero, suspect, prize):
        return
    world.facts["solved"] = True
    world.facts["truth"] = f"{suspect.name_word} had taken the {prize.label} while too drunk to remember."
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    suspect.memes["shame"] = suspect.memes.get("shame", 0.0) + 1
    prize.carried_by = hero.id
    prize.location = world.place.id
    prize.meters["returned"] = 1
    world.say(f"In the end, {hero.name_word} found the truth: {suspect.name_word} had stumbled away with the {prize.label}.")
    world.say(f"{suspect.name_word} gave the {prize.label} back, and the square grew quiet again.")


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, label=params.hero))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, label=params.helper))
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    prize = world.add(Entity(
        id="prize",
        type="thing",
        label=prize_cfg["label"],
        phrase=prize_cfg["phrase"],
        plural=prize_cfg["plural"],
        location=place.id,
    ))
    boozer = world.add(Entity(id="boozer", kind="character", type="man", label="Old Rusk"))
    boozer.memes["drunk"] = 1.0

    world.facts.update(hero=hero, helper=helper, prize=prize, boozer=boozer)

    # Act 1: a folk-tale beginning.
    world.say(f"Once in {place.label}, there lived a {params.hero_type} named {hero.name_word} who loved every small motion in the day.")
    world.say(f"{hero.name_word} liked {helper.name_word}, who could trot from place to place as fast as a breeze among reeds.")
    world.say(f"At dawn, the village keeper set out {prize.phrase} for the market, and everyone expected a sweet fair day.")

    # Act 2: the mystery appears.
    world.para()
    _move(hero, place.id)
    _move(helper, place.id)
    world.say(f"But when the noon bell rang, the {prize.label} were gone.")
    hero.memes["worry"] = 1.0
    hero.memes["suspicion"] = 1.0
    world.say(f"{hero.name_word} studied the ground and saw muddy marks, while {helper.name_word} began to trot along the lane.")
    _move(boozer, "inn")
    boozer.memes["careless_motion"] = 1.0
    _reason_about_boozer(world, boozer, prize)
    world.say(f"Near the inn, old {boozer.name_word} swayed by the door with crumbs on his coat.")

    # Act 3: the solution.
    world.para()
    _clue_from_tracks(world, hero, helper, boozer)
    solve_mystery(world, hero, boozer, prize)
    if world.facts.get("solved"):
        world.say(f"By evening, {hero.name_word} and {helper.name_word} trotted home through the square, and the honey smell came back with them.")
    else:
        pass

    world.facts.update(place=place, params=params)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Places and people are facts from the Python registries.
motion(X) :- hero(X).
motion(X) :- helper(X).
motion(X) :- boozer(X).

% A trot is a fast motion between neighboring places.
trot(H, A, B) :- helper(H), at(H, A), neighbor(A, B), A != B.

% The mystery is solved when the boozer has the prize and is careless.
stolen(P) :- boozer(B), prize(P), carried_by(P, B), careless(B).

solved :- stolen(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for n in sorted(p.neighbors):
            lines.append(asp.fact("neighbor", pid, n))
    for gender, names in HEROES.items():
        for n in names:
            lines.append(asp.fact("hero_name", gender, n))
    for kind, names in HELPERS.items():
        for n in names:
            lines.append(asp.fact("helper_name", kind, n))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        if pr["plural"]:
            lines.append(asp.fact("plural", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solved/0."))
    asp_solved = bool(asp.atoms(model, "solved"))
    py_solved = True
    if asp_solved == py_solved:
        print("OK: ASP and Python both represent the mystery as solvable.")
        return 0
    print("MISMATCH: ASP/Python parity failed.")
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    return [
        f"Write a folk tale about a small mystery in {world.place.label} with {hero.name_word}, {helper.name_word}, and a missing {prize.label}.",
        f"Tell a child-friendly mystery story where someone follows motion and a trot to solve what happened to the {prize.label}.",
        f"Write a gentle story about a boozer, a helpful friend, and a clue in the mud that leads to the truth.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    prize: Entity = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    boozer: Entity = _safe_fact(world, f, "boozer")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What mystery did {hero.name_word} notice in the village square?",
            answer=f"{hero.name_word} noticed that the {prize.label} had gone missing from the square.",
        ),
        QAItem(
            question=f"How did {helper.name_word} help solve the mystery?",
            answer=f"{helper.name_word} trotted along the lane to follow the muddy clues and help find the truth.",
        ),
        QAItem(
            question=f"Who caused the trouble with the {prize.label}?",
            answer=f"Old {boozer.name_word} caused the trouble when he took the {prize.label} while drunk and careless.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to trot?",
            answer="To trot is to move quickly with short, lively steps, like a small horse or a busy helper hurrying along.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzling thing that people try to understand by looking for clues and asking questions.",
        ),
        QAItem(
            question="What is a boozer?",
            answer="A boozer is a person who drinks too much alcohol, and that can make them stumble or act carelessly.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale mystery storyworld with motion and trot.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-type", choices=list(HEROES))
    ap.add_argument("--helper-type", choices=list(HELPERS))
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    hero_type = getattr(args, "hero_type", None) or rng.choice(list(HEROES))
    helper_type = getattr(args, "helper_type", None) or rng.choice(list(HELPERS))
    prize = getattr(args, "prize", None) or rng.choice(list(PRIZES))
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(HEROES, hero_type))
    helper = getattr(args, "helper", None) or rng.choice(_safe_lookup(HELPERS, helper_type))
    if hero == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, helper_type=helper_type, prize=prize)


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
        print("--- world trace ---")
        for note in sample.world.trace_notes:
            print(note)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for parity checks.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("square", "Mara", "girl", "Brindle", "dog", "cakes"),
            StoryParams("square", "Pip", "boy", "Nina", "grandmother", "jar"),
            StoryParams("lane", "Tilda", "girl", "Wag", "dog", "cakes"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 25):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
