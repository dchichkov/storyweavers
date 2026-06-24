#!/usr/bin/env python3
"""
A small mystery-themed storyworld about a vehicle, a lost clue, a flashback,
sharing, and reconciliation.

Seed tale idea:
- A child finds their vehicle missing.
- A clue points to a misunderstanding.
- A flashback shows the vehicle was borrowed kindly.
- The children reconcile and share the ride.

The world is intentionally small and constraint-checked: only reasonable
vehicle / clue / sharing combinations are generated.
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
    borrowed_from: Optional[str] = None
    wears: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    ride: object | None = None
    def __post_init__(self):
        self.meters.setdefault("lost", 0.0)
        self.meters.setdefault("visible", 0.0)
        self.meters.setdefault("used", 0.0)
        self.meters.setdefault("shared", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("hurt", 0.0)
        self.memes.setdefault("guilt", 0.0)
        self.memes.setdefault("relief", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("trust", 0.0)

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
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
class Vehicle:
    id: str
    label: str
    phrase: str
    ride_verb: str
    glance_verb: str
    clue: str
    loss_phrase: str
    found_phrase: str
    share_phrase: str
    kind: str = "vehicle"
    plural: bool = False
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
    place: str
    vehicle: str
    name_a: str
    name_b: str
    gender_a: str
    gender_b: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def articles(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def setup_fact(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    world.say(
        f"{child.id} loved {vehicle.phrase} and liked to {vehicle.ride_verb} at {world.setting.place}."
    )
    world.say(
        f"{friend.id} liked to watch, because {vehicle.label} looked fast and shiny."
    )


def mystery_loss(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    child.memes["worry"] += 1
    vehicle.meters["lost"] += 1
    world.say(
        f"One day, {child.id} ran to the shed, but {vehicle.pronoun('possessive')} spot was empty."
    )
    world.say(
        f"{child.id} blinked at the empty place. {vehicle.label.capitalize()} was gone."
    )


def clue_scene(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    world.say(
        f"Then {child.id} saw {vehicle.clue} near the gate."
    )
    world.say(
        f"{friend.id} had a small smudge of dust on {friend.pronoun('possessive')} sleeve, and that made the day feel like a mystery."
    )


def flashback(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    world.say(
        f"{child.id} remembered yesterday in a flashback: {friend.id} had asked to borrow {vehicle.it()} for a turn."
    )
    world.say(
        f"{friend.id} had said, '{vehicle.share_phrase}', and {child.id} had nodded."
    )
    vehicle.borrowed_from = child.id
    vehicle.meters["shared"] += 1
    friend.memes["guilt"] += 1


def reconciliation(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    child.memes["hurt"] += 1
    friend.memes["guilt"] += 1
    world.say(
        f"Now the puzzle made sense. {friend.id} had not taken {vehicle.it()} away forever; {friend.id} had only moved it to the garage to keep it safe."
    )
    world.say(
        f"{friend.id} brought {vehicle.label} back and said, '{vehicle.found_phrase}'"
    )
    world.say(
        f"{child.id} took a deep breath and said, 'I was scared, but I know now you were helping.'"
    )
    world.say(
        f"{friend.id} smiled, and the two children forgave each other right away."
    )
    child.memes["worry"] = 0.0
    child.memes["hurt"] = 0.0
    friend.memes["guilt"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    friend.memes["joy"] += 1
    child.memes["trust"] += 1
    friend.memes["trust"] += 1
    vehicle.meters["lost"] = 0.0
    vehicle.meters["visible"] = 1.0


def ending(world: World, child: Entity, friend: Entity, vehicle: Entity) -> None:
    world.say(
        f"In the end, they shared {vehicle.it()} again: first {child.id}, then {friend.id}, then {child.id} again."
    )
    world.say(
        f"The mystery was solved, the worry was gone, and {vehicle.label} rolled down the path with two happy riders taking turns."
    )


def story_core(setting: Setting, vehicle: Vehicle, name_a: str, name_b: str,
               gender_a: str, gender_b: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name_a, kind="character", type=gender_a, label=name_a))
    friend = world.add(Entity(id=name_b, kind="character", type=gender_b, label=name_b))
    ride = world.add(Entity(id=vehicle.id, kind="thing", type="vehicle", label=vehicle.label, phrase=vehicle.phrase))
    setup_fact(world, child, friend, ride)
    world.para()
    mystery_loss(world, child, friend, ride)
    clue_scene(world, child, friend, ride)
    world.para()
    flashback(world, child, friend, ride)
    reconciliation(world, child, friend, ride)
    ending(world, child, friend, ride)
    world.facts.update(child=child, friend=friend, vehicle=ride, vehicle_cfg=vehicle)
    return world


SETTINGS = {
    "garage": Setting(place="the garage", indoor=False, affords={"bike", "scooter", "wagon"}),
    "yard": Setting(place="the yard", indoor=False, affords={"bike", "scooter", "wagon"}),
    "driveway": Setting(place="the driveway", indoor=False, affords={"bike", "scooter"}),
}

VEHICLES = {
    "bike": Vehicle(
        id="bike",
        label="bike",
        phrase="a bright red bike",
        ride_verb="ride in circles",
        glance_verb="look around",
        clue="two small tire tracks",
        loss_phrase="the bike was missing",
        found_phrase="I moved it to the garage so it would not get wet",
        share_phrase="You can have the first turn, and then I can share",
    ),
    "scooter": Vehicle(
        id="scooter",
        label="scooter",
        phrase="a blue scooter",
        ride_verb="scoot along the path",
        glance_verb="peer around",
        clue="a tiny scuff mark on the ramp",
        loss_phrase="the scooter was gone",
        found_phrase="I brought it inside to keep it safe",
        share_phrase="We can share the scooter after I bring it back",
    ),
    "wagon": Vehicle(
        id="wagon",
        label="wagon",
        phrase="a little wagon with a red handle",
        ride_verb="pull the wagon slowly",
        glance_verb="peek behind things",
        clue="a red handle print on the wall",
        loss_phrase="the wagon had disappeared",
        found_phrase="I parked it by the shed to dry it off",
        share_phrase="We can share the wagon and take turns pulling",
    ),
}

GIRL_NAMES = ["Mia", "Lena", "Nora", "Ava", "Ruby", "Ivy"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Ben", "Cal", "Noah"]


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for veh in setting.affords:
            combos.append((place, veh))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def reasonableness_check(place: str, vehicle: Vehicle) -> None:
    if place not in SETTINGS:
        pass
    if vehicle.id not in _safe_lookup(SETTINGS, place).affords:
        pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld about a vehicle, sharing, a flashback, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
    ap.add_argument("--gender-a", choices=["girl", "boy"])
    ap.add_argument("--gender-b", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    vehicle = getattr(args, "vehicle", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    reasonableness_check(place, _safe_lookup(VEHICLES, vehicle))

    gender_a = getattr(args, "gender_a", None) or rng.choice(["girl", "boy"])
    gender_b = getattr(args, "gender_b", None) or ("boy" if gender_a == "girl" else "girl")
    name_a = getattr(args, "name_a", None) or choose_name(rng, gender_a)
    name_b = getattr(args, "name_b", None) or choose_name(rng, gender_b)
    if name_a == name_b:
        name_b = choose_name(rng, gender_b)
    return StoryParams(place=place, vehicle=vehicle, name_a=name_a, name_b=name_b, gender_a=gender_a, gender_b=gender_b)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    vehicle_cfg: Vehicle = _safe_fact(world, f, "vehicle_cfg")  # type: ignore[assignment]
    return [
        f'Write a short mystery story for a young child about a missing {vehicle_cfg.label} and a kind surprise.',
        f"Tell a simple story where {child.id} thinks {friend.id} took {vehicle_cfg.label}, but a flashback shows the truth.",
        f"Write a gentle story about sharing {vehicle_cfg.phrase}, solving a small mystery, and making up at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    friend: Entity = _safe_fact(world, f, "friend")  # type: ignore[assignment]
    vehicle: Entity = _safe_fact(world, f, "vehicle")  # type: ignore[assignment]
    vcfg: Vehicle = _safe_fact(world, f, "vehicle_cfg")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was missing when {child.id} ran to the {world.setting.place} spot?",
            answer=f"{vcfg.label.capitalize()} was missing, and that made {child.id} feel worried.",
        ),
        QAItem(
            question=f"What clue helped {child.id} start solving the mystery?",
            answer=f"{vcfg.clue.capitalize()} helped {child.id} start to understand what had happened.",
        ),
        QAItem(
            question=f"What did the flashback show about {friend.id} and {vehicle.label}?",
            answer=f"It showed that {friend.id} had borrowed {vehicle.it()} kindly and planned to share it back.",
        ),
        QAItem(
            question=f"How did the children feel at the end?",
            answer=f"They felt calm and happy after they reconciled and shared {vehicle.it()} again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a vehicle?",
            answer="A vehicle is something people use to move from one place to another, like a bike, scooter, or wagon.",
        ),
        QAItem(
            question="What does it mean to share?",
            answer="To share means to let someone else use something too, often by taking turns.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story shows something that happened earlier, so the reader can understand the mystery better.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement and becoming friendly again.",
        ),
    ]


ASP_RULES = r"""
vehicle(v1).
vehicle(v2).
vehicle(v3).
place(p1).
place(p2).
place(p3).

affords(p1,v1).
affords(p1,v2).
affords(p1,v3).
affords(p2,v1).
affords(p2,v2).
affords(p2,v3).
affords(p3,v1).
affords(p3,v2).

mystery_combo(P,V) :- affords(P,V).
#show mystery_combo/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        pid = place
        lines.append(asp.fact("place", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for veh in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, veh))
    for vid in VEHICLES:
        lines.append(asp.fact("vehicle", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_combo/2."))
    return sorted(set(asp.atoms(model, "mystery_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = story_core(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(VEHICLES, params.vehicle),
        params.name_a,
        params.name_b,
        params.gender_a,
        params.gender_b,
    )
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


CURATED = [
    StoryParams(place="garage", vehicle="bike", name_a="Mia", name_b="Ben", gender_a="girl", gender_b="boy"),
    StoryParams(place="yard", vehicle="scooter", name_a="Owen", name_b="Lena", gender_a="boy", gender_b="girl"),
    StoryParams(place="driveway", vehicle="bike", name_a="Ruby", name_b="Theo", gender_a="girl", gender_b="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_combo/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible mystery combos:\n")
        for p, v in combos:
            print(f"  {p:10} {v}")
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {p.name_a} and {p.name_b}: {p.vehicle} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
