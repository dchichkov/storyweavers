#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chihuahua_freight_evolution_foreshadowing_kindness_detective_story.py
=================================================================================================

A small detective-story world about a tiny chihuahua, a freight yard mystery,
and a kinder way of solving it. The seed words are threaded into a world model
where clues, cargo, suspicion, foreshadowing, and kindness all matter.

Premise:
- A careful chihuahua detective notices freight delays at a busy depot.
- Small clues foreshadow that the "missing" cargo is not stolen.
- The resolution shows an evolution from suspicion to kindness, and the final
  image proves what changed in the world.

This script follows the Storyweavers contract:
- standalone stdlib script
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of storyworlds/results.py containers
- lazy import of storyworlds/asp.py in ASP helpers
- inline ASP_RULES twin plus Python reasonableness gate
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
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    box: object | None = None
    det: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"dog", "chihuahua"}:
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
    place: str
    indoors: bool = False
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
class Case:
    id: str
    clue: str
    trail: str
    reveal: str
    risk: str
    signal: str
    topic: str
    tags: set[str] = field(default_factory=set)
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
class Cargo:
    id: str
    label: str
    phrase: str
    region: str
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
class Gear:
    id: str
    label: str
    clue: str
    helps: set[str]
    covers: set[str]
    tags: set[str] = field(default_factory=set)
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "freight_yard": Setting(
        place="the freight yard",
        indoors=False,
        affords={"track_clues", "crate_search", "kindness_talk"},
    ),
    "station_office": Setting(
        place="the station office",
        indoors=True,
        affords={"paperwork", "clue_board", "kindness_talk"},
    ),
    "loading_bay": Setting(
        place="the loading bay",
        indoors=True,
        affords={"crate_search", "clue_board", "kindness_talk"},
    ),
}

CASES = {
    "missing_crate": Case(
        id="missing_crate",
        clue="a torn paper seal",
        trail="tiny paw prints near the dock",
        reveal="the crate had been moved to keep it dry",
        risk="the freight would miss its train",
        signal="a warm, apologetic note",
        topic="freight",
        tags={"freight", "clue"},
    ),
    "late_manifest": Case(
        id="late_manifest",
        clue="a stamp smudged with rain",
        trail="ink marks leading to the office door",
        reveal="the manifest was still being checked",
        risk="the shipment would not leave on time",
        signal="a calm, careful message",
        topic="paperwork",
        tags={"freight", "clue"},
    ),
    "quiet_whistle": Case(
        id="quiet_whistle",
        clue="a whistle tied with twine",
        trail="soft footprints beside stacked boxes",
        reveal="the whistle had been set aside so it would not scare the dog",
        risk="the dog would keep barking at the noise",
        signal="a gentle, friendly hush",
        topic="kindness",
        tags={"kindness", "clue"},
    ),
}

CARGOES = {
    "tea": Cargo(id="tea", label="tea crates", phrase="carefully packed tea crates", region="dock", plural=True),
    "books": Cargo(id="books", label="book boxes", phrase="sturdy book boxes", region="dock", plural=True),
    "fruit": Cargo(id="fruit", label="fruit crates", phrase="bright fruit crates", region="dock", plural=True),
}

GEAR = {
    "notebook": Gear(
        id="notebook",
        label="a small notebook",
        clue="pages for notes",
        helps={"clue", "paperwork"},
        covers={"dock", "office"},
        tags={"clue"},
    ),
    "raincoat": Gear(
        id="raincoat",
        label="a yellow raincoat",
        clue="keeps the rain off",
        helps={"freight"},
        covers={"dock"},
        tags={"freight"},
    ),
    "soft_leash": Gear(
        id="soft_leash",
        label="a soft leash",
        clue="keeps the chihuahua close without pulling",
        helps={"kindness"},
        covers={"dock", "office"},
        tags={"kindness"},
    ),
}

NAMES = ["Pip", "Milo", "Tia", "Nina", "Coco", "Remy", "Luna", "Bix"]
HUMAN_NAMES = ["Ms. Vale", "Mr. Finch", "Mrs. Lane", "Mr. Otis"]
TRAITS = ["sharp-eyed", "brave", "patient", "gentle", "clever"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    case: str
    cargo: str
    detective_name: str
    helper_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def case_needs_kindness(case: Case) -> bool:
    return "kindness" in case.tags or case.id == "quiet_whistle"


def case_is_detective_story(case: Case, cargo: Cargo) -> bool:
    return "clue" in case.tags and cargo.region == "dock"


def select_gear(case: Case) -> Optional[Gear]:
    if "kindness" in case.tags:
        return GEAR["soft_leash"]
    if "paperwork" in case.topic:
        return GEAR["notebook"]
    if "freight" in case.tags:
        return GEAR["raincoat"]
    return None


def explain_rejection(case: Case, cargo: Cargo) -> str:
    return (
        f"(No story: this case does not make a convincing detective scene with "
        f"{cargo.label}. Pick a freight-related clue and a cargo on the dock.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A case is story-worthy when it has a clue and the cargo is dockside freight.
story_case(Case, Cargo) :- case(Case), clue_case(Case), cargo(Cargo), dockside(Cargo).

% Kindness is required when the case has a kindness tag.
needs_kindness(Case) :- kindness_case(Case).

% A gear choice is compatible when it matches the case kind.
compatible_gear(Case, Gear) :- story_case(Case, Cargo), gear(Gear), helps(Gear, freight), freight_case(Case), cargo(Cargo).
compatible_gear(Case, Gear) :- story_case(Case, Cargo), gear(Gear), helps(Gear, kindness), kindness_case(Case), cargo(Cargo).
compatible_gear(Case, Gear) :- story_case(Case, Cargo), gear(Gear), helps(Gear, paperwork), paperwork_case(Case), cargo(Cargo).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("clue_case", cid))
        lines.append(asp.fact("dockside", "tea"))
        if "kindness" in c.tags:
            lines.append(asp.fact("kindness_case", cid))
        if "freight" in c.tags:
            lines.append(asp.fact("freight_case", cid))
        if "paperwork" in c.topic:
            lines.append(asp.fact("paperwork_case", cid))
    for cg in CARGOES.values():
        lines.append(asp.fact("cargo", cg.id))
        lines.append(asp.fact("dockside", cg.id))
    for g in GEAR.values():
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show story_case/2."))
    return sorted(set(asp.atoms(model, "story_case")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for case_id in setting.affords:
            case = CASES.get(case_id)
            if not case:
                continue
            for cargo_id, cargo in CARGOES.items():
                if case_is_detective_story(case, cargo):
                    combos.append((setting_id, case_id, cargo_id))
    return combos


def foreshadow_line(case: Case, cargo: Cargo) -> str:
    return f"The first clue was {case.clue}, and it seemed to whisper that the missing freight had a harmless reason."


def intro_line(det: Entity, helper: Entity, setting: Setting) -> str:
    return f"{det.id} was a tiny chihuahua detective who liked quiet corners and careful questions."


def story_begin(world: World, det: Entity, helper: Entity, case: Case, cargo: Cargo) -> None:
    world.say(intro_line(det, helper, world.setting))
    world.say(
        f"{det.id} and {helper.id} often walked through {world.setting.place} looking for signs that others missed."
    )
    world.say(
        f"That day, the freight workers worried about {cargo.label}, because {case.risk}."
    )
    world.say(foreshadow_line(case, cargo))


def investigate(world: World, det: Entity, helper: Entity, case: Case, cargo: Cargo) -> None:
    det.memes["curiosity"] = det.memes.get("curiosity", 0) + 1
    det.memes["focus"] = det.memes.get("focus", 0) + 1
    world.para()
    world.say(f"{det.id} lowered her nose and followed {case.trail}.")
    world.say(
        f"{helper.id} held up the notebook, because a good detective story needs patient clues, not loud guesses."
    )
    world.say(
        f"The trail ended where the cargo sat safely under a tarp, which was the first sign that the freight was not stolen."
    )
    world.say(
        f"That small clue foreshadowed a kinder answer: someone had moved the load to protect it from the weather."
    )


def reveal(world: World, det: Entity, helper: Entity, case: Case, cargo: Cargo, gear: Gear) -> None:
    det.memes["relief"] = det.memes.get("relief", 0) + 1
    det.memes["kindness"] = det.memes.get("kindness", 0) + 1
    world.para()
    world.say(
        f"At last, {helper.id} found {case.signal} tucked beside the manifest, and the whole mystery turned clear."
    )
    world.say(
        f"The missing {cargo.label} had only been moved so it would stay dry and safe."
    )
    world.say(
        f"{det.id} wagged once, then nodded, because the best detective work was not sharp suspicion alone but kindness."
    )
    world.say(
        f"They used {gear.label} and returned the freight to the track just in time, with no blame needed."
    )
    world.say(
        f"By evening, the story had evolved from worry into trust, and {det.id} looked proud beside the neatly delivered cargo."
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    cargo = _safe_lookup(CARGOES, params.cargo)
    world = World(setting)

    det = world.add(Entity(id=params.detective_name, kind="character", type="chihuahua", label="detective"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type="human", label="helper"))
    box = world.add(Entity(id=cargo.id, type="cargo", label=cargo.label, phrase=cargo.phrase))

    gear = select_gear(case)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    world.facts.update(det=det, helper=helper, case=case, cargo=cargo, gear=gear, box=box)

    story_begin(world, det, helper, case, cargo)
    investigate(world, det, helper, case, cargo)
    reveal(world, det, helper, case, cargo, gear)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    det = _safe_fact(world, f, "det")
    case = _safe_fact(world, f, "case")
    cargo = _safe_fact(world, f, "cargo")
    return [
        f"Write a short detective story for a child about a chihuahua named {det.id} who solves a freight mystery with kindness.",
        f"Tell a foreshadowing-heavy story where {det.id} follows a clue, finds {cargo.label}, and learns that the problem was not theft.",
        f"Write a gentle detective story about {det.id}, freight, and a clue that leads to a kinder explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    det = _safe_fact(world, f, "det")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    cargo = _safe_fact(world, f, "cargo")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who is the detective in the story?",
            answer=f"The detective is a tiny chihuahua named {det.id}. She is the one who notices the clues first.",
        ),
        QAItem(
            question=f"What was the freight mystery about?",
            answer=f"It was about {cargo.label} and the fear that {case.risk}. The answer turned out to be a safe, kind one.",
        ),
        QAItem(
            question=f"What clue helped solve the case?",
            answer=f"The main clue was {case.clue}. It foreshadowed that the freight had been moved for a good reason.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by holding the notebook and staying calm, so the detective could follow the trail carefully.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, suspicion had evolved into kindness and trust, and the freight was delivered safely.",
        ),
        QAItem(
            question=f"What gear did they use?",
            answer=f"They used {gear.label} because it fit the story's needs and helped them solve the freight problem kindly.",
        ),
    ]


KNOWLEDGE = {
    "chihuahua": [
        (
            "What is a chihuahua?",
            "A chihuahua is a very small dog with a big voice and quick, alert eyes.",
        )
    ],
    "freight": [
        (
            "What is freight?",
            "Freight is cargo or goods that are carried from one place to another, often by train or truck.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help, speak gently, or understand someone instead of blaming them right away.",
        )
    ],
    "foreshadowing": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is when a story gives a small hint early on about something that will matter later.",
        )
    ],
    "evolution": [
        (
            "What does evolution mean?",
            "Evolution means a slow change over time, like when a feeling, idea, or way of acting gradually becomes different.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"chihuahua", "freight", "kindness", "foreshadowing", "evolution"}
    out: list[QAItem] = []
    for tag in ["chihuahua", "freight", "kindness", "foreshadowing", "evolution"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective-story world about a chihuahua, freight, foreshadowing, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--cargo", choices=CARGOES.keys())
    ap.add_argument("--detective-name", choices=NAMES)
    ap.add_argument("--helper-name", choices=HUMAN_NAMES)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
        and (getattr(args, "cargo", None) is None or c[2] == getattr(args, "cargo", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, case, cargo = rng.choice(list(filtered))
    return StoryParams(
        setting=setting,
        case=case,
        cargo=cargo,
        detective_name=getattr(args, "detective_name", None) or rng.choice(NAMES),
        helper_name=getattr(args, "helper_name", None) or rng.choice(HUMAN_NAMES),
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show story_case/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, case, cargo) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="freight_yard", case="missing_crate", cargo="tea", detective_name="Pip", helper_name="Ms. Vale"),
            StoryParams(setting="station_office", case="late_manifest", cargo="books", detective_name="Tia", helper_name="Mr. Finch"),
            StoryParams(setting="loading_bay", case="quiet_whistle", cargo="fruit", detective_name="Coco", helper_name="Mrs. Lane"),
        ]
        samples = [generate(p) for p in curated]
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
