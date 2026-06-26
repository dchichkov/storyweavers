#!/usr/bin/env python3
"""
A tiny fable-style storyworld about a careful traveler, a perplexing kayak,
and a choice between boasting and patience.

The seed suggests two important words:
- "plethora" -> abundance, too many choices, a crowded storehouse
- "kayak" -> a narrow craft that can carry one or two across water

The domain is built as a small simulated world:
a fox-like traveler must cross a river, but a flood has left a plethora of
floating reeds, branches, and rafts. The traveler hears an inner monologue of
worry and temptation while suspense rises around the crossing.

The fable shape:
setup -> temptation -> inner deliberation -> careful action -> lesson.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    at: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    companion: object | None = None
    traveler: object | None = None
    vehicle: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "hare", "wolf"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"vixen", "rabbit", "owl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the riverbank"
    river: str = "the river"
    current: str = "strong"
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
    capacity: int
    stable: bool
    fits_water: bool = True
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
    traveler: str
    companion: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _join_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", and " + items[-1]


def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} stood beside {setting.river}, where the water ran {setting.current}."


def introduce(world: World, traveler: Entity, companion: Entity) -> None:
    world.say(
        f"Once in a time of bright leaves, {traveler.id}, a {traveler.traits[0]} {traveler.type}, "
        f"walked with {companion.id} to {world.setting.place}."
    )
    world.say(
        f"Every creature in the lane knew {traveler.id} for careful paws and a quick eye, "
        f"though {traveler.pronoun('subject')} often listened most closely to {traveler.pronoun('possessive')} own thoughts."
    )


def abundance(world: World) -> None:
    world.say(
        f"At the edge of the water there was a {world.facts['plethora_word']} of driftwood: "
        f"reeds, bark strips, a crooked crate, a half-log, and little floating planks."
    )
    world.say(
        f"It looked as if the river had piled up a whole feast of chances, and that abundance made the bank feel crowded."
    )


def desire(world: World, traveler: Entity, vehicle: Entity) -> None:
    traveler.memes["desire"] = traveler.memes.get("desire", 0.0) + 1
    world.say(
        f"{traveler.id} wanted to cross at once in the {vehicle.label}, because {vehicle.phrase} looked like the simplest path."
    )


def inner_monologue(world: World, traveler: Entity, vehicle: Entity) -> None:
    traveler.memes["worry"] = traveler.memes.get("worry", 0.0) + 1
    traveler.memes["suspense"] = traveler.memes.get("suspense", 0.0) + 1
    world.say(
        f'Inside {traveler.pronoun("possessive")} own head, {traveler.id} thought, '
        f'"If I rush, the current may spin me, and if I choose poorly, I will look foolish before the whole bank."'
    )
    world.say(
        f'"Still," {traveler.pronoun("subject")} thought, "a {vehicle.label} is small, steady, and kind to the water."'
    )


def suspense_rises(world: World, traveler: Entity) -> None:
    traveler.memes["suspense"] = traveler.memes.get("suspense", 0.0) + 1
    world.say(
        f"The river kept moving, and the reeds kept tapping the hull, as if the water were asking a question and waiting."
    )


def choose_carefully(world: World, traveler: Entity, vehicle: Entity) -> None:
    traveler.memes["patience"] = traveler.memes.get("patience", 0.0) + 1
    world.say(
        f"At last {traveler.id} drew a slow breath and chose the {vehicle.label} instead of the tempting pile of loose branches."
    )
    world.say(
        f"{traveler.id} checked the rope, set the little craft straight, and stepped in without hurrying."
    )


def cross(world: World, traveler: Entity, companion: Entity, vehicle: Entity) -> None:
    traveler.at = "across the river"
    companion.at = "across the river"
    vehicle.at = "across the river"
    traveler.meters["travel"] = traveler.meters.get("travel", 0.0) + 1
    world.say(
        f"The {vehicle.label} held fast, and the current could not shake it loose. "
        f"{traveler.id} paddled with {traveler.pronoun('possessive')} whole body, while {companion.id} watched from the stern."
    )
    world.say(
        f"They reached the far bank safely, with wet paws, calm hearts, and the sense that patience had done the strongest work."
    )


def lesson(world: World, traveler: Entity) -> None:
    traveler.memes["wisdom"] = traveler.memes.get("wisdom", 0.0) + 1
    world.say(
        f"And so {traveler.id} learned that a curious mind may see a plethora of choices, but wisdom chooses the one that truly fits."
    )


def tell(setting: Setting, vehicle_def: Vehicle, traveler_name: str, traveler_type: str, companion_type: str) -> World:
    world = World(setting)
    world.facts["plethora_word"] = "plethora"

    traveler = world.add(Entity(
        id=traveler_name,
        kind="character",
        type=traveler_type,
        traits=["careful", "thoughtful"],
        at=setting.place,
    ))
    companion = world.add(Entity(
        id="Moss",
        kind="character",
        type=companion_type,
        traits=["quiet"],
        at=setting.place,
    ))
    vehicle = world.add(Entity(
        id=vehicle_def.id,
        type="vehicle",
        label=vehicle_def.label,
        phrase=vehicle_def.phrase,
        at=setting.place,
    ))

    world.facts.update(traveler=traveler, companion=companion, vehicle=vehicle, vehicle_def=vehicle_def)

    introduce(world, traveler, companion)
    world.para()
    world.say(setting_line(setting))
    abundance(world)
    desire(world, traveler, vehicle)
    inner_monologue(world, traveler, vehicle)
    suspense_rises(world, traveler)
    world.para()
    choose_carefully(world, traveler, vehicle)
    cross(world, traveler, companion, vehicle)
    world.para()
    lesson(world, traveler)
    return world


SETTINGS = {
    "riverbank": Setting(place="the riverbank", river="the river", current="strong", affords={"kayak"}),
    "marsh_edge": Setting(place="the marsh edge", river="the slow river", current="twisting", affords={"kayak"}),
}

VEHICLES = {
    "kayak": Vehicle(
        id="kayak",
        label="kayak",
        phrase="its narrow shape could slip through reeds and carry two light travelers",
        capacity=2,
        stable=True,
        fits_water=True,
    ),
}

TRAVELER_TYPES = {
    "fox": {"name": "Fox", "companion": "heron"},
    "vixen": {"name": "Vixen", "companion": "otter"},
}

CURATED = [
    StoryParams(place="riverbank", vehicle="kayak", traveler="fox", companion="heron"),
    StoryParams(place="marsh_edge", vehicle="kayak", traveler="vixen", companion="otter"),
]

GAMES = ["careful crossing", "river choice", "quiet patience"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, "kayak", t) for p in SETTINGS for t in TRAVELER_TYPES]


def explain_rejection(place: str, vehicle: str) -> str:
    return f"(No story: {vehicle} does not suit {place} in this small fable-world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-style storyworld about a kayak, patience, and a river crossing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--traveler", choices=TRAVELER_TYPES)
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "vehicle", None) and getattr(args, "vehicle", None) != "kayak":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "vehicle", None) is None or c[1] == getattr(args, "vehicle", None))
              and (getattr(args, "traveler", None) is None or c[2] == getattr(args, "traveler", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, vehicle, traveler = rng.choice(list(combos))
    name = getattr(args, "name", None) or random.choice(["Rowan", "Pip", "Talon", "Clover"])
    return StoryParams(place=place, vehicle=vehicle, traveler=traveler, companion=_safe_lookup(TRAVELER_TYPES, traveler)["companion"])


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a child about "{f["plethora_word"]}" choices and a kayak crossing a river.',
        f"Tell a suspenseful little story where {f['traveler'].id} thinks carefully before using the kayak.",
        f"Write a gentle animal fable that ends with a lesson about choosing wisely when there are too many options.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    traveler = _safe_fact(world, f, "traveler")
    vehicle = _safe_fact(world, f, "vehicle")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {traveler.id}, a careful {traveler.type}, who crossed the river in a kayak.",
        ),
        QAItem(
            question=f"What problem did {traveler.id} face at the riverbank?",
            answer="There were many tempting things to choose from, but the water was moving fast and the wrong choice could have gone badly.",
        ),
        QAItem(
            question=f"How did {traveler.id} get across safely?",
            answer=f"{traveler.id} listened to the quiet warning in {traveler.pronoun('possessive')} own mind, chose the kayak, and crossed steadily with a companion.",
        ),
        QAItem(
            question="What lesson did the story teach?",
            answer="The lesson was that wisdom does not grab the flashiest choice; it picks the one that truly fits the task.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a kayak?",
            answer="A kayak is a narrow boat meant for paddling on water, often with one person sitting low inside it.",
        ),
        QAItem(
            question="What does plethora mean?",
            answer="A plethora means a very large amount of something, so many choices that the place can feel crowded or overwhelming.",
        ),
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the feeling of waiting to see what will happen next, especially when a choice might be risky.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the little voice of thoughts a character hears inside their own mind.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.at:
            bits.append(f"at={e.at}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A kayak story is valid when the setting affords it and the traveler type is one of the fable creatures.
valid(Place, Vehicle, Traveler) :- affords(Place, Vehicle), traveler_type(Traveler).

% The world is intentionally small: kayak is the only vehicle in this seed world.
safe_choice(Place, kayak, Traveler) :- valid(Place, kayak, Traveler).

#show valid/3.
#show safe_choice/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for v in sorted(s.affords):
            lines.append(asp.fact("affords", pid, v))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        if v.stable:
            lines.append(asp.fact("stable", vid))
        if v.fits_water:
            lines.append(asp.fact("water_vehicle", vid))
    for t in TRAVELER_TYPES:
        lines.append(asp.fact("traveler_type", t))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = sorted(set(asp.atoms(model, "valid")))
    safe = sorted(set(asp.atoms(model, "safe_choice")))
    py = sorted(valid_combos())
    py_safe = sorted((p, "kayak", t) for p, _, t in py)
    if valid == py and safe == py_safe:
        print(f"OK: ASP parity holds ({len(valid)} valid combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP valid:", valid)
    print("PY  valid:", py)
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    vehicle_def = _safe_lookup(VEHICLES, params.vehicle)
    traveler_type = params.traveler
    traveler_name = params.name or _safe_lookup(TRAVELER_TYPES, traveler_type)["name"]
    world = tell(setting, vehicle_def, traveler_name, traveler_type, params.companion)
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
        print(asp_program())
        return
    if getattr(args, "asp", None):
        print(asp_program())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
