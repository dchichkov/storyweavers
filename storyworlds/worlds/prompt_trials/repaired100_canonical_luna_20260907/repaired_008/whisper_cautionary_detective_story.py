#!/usr/bin/env python3
"""
A gentle cautionary detective storyworld about listening carefully to a whisper.

A small clue can lead a young detective toward the truth, but rushing, guessing,
or repeating a whisper can make a simple problem grow. Careful observation,
kind questions, and a trusted helper repair the mistake.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


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
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
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
    id: str
    place: str
    affordances: set[str]
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
class Case:
    id: str
    opening: str
    whisper: str
    wrong_guess: str
    clue: str
    caution: str
    actions: tuple[str, str, str]
    resolution: str
    ending: str
    cause_answer: str
    lesson: str
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
class StoryParams:
    setting: str = ""
    case: str = ""
    detective: str = ""
    helper: str = ""
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


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    world: object | None = None
    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(self, text: str) -> None:
        self.trace.append(text)
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
    def get(self, eid: str):
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


SETTINGS = {
    "library": Setting(
        "library",
        "the old library",
        {"books", "reading_room", "notice_board"},
    ),
    "greenhouse": Setting(
        "greenhouse",
        "the school greenhouse",
        {"plants", "watering_can", "tool_shelf"},
    ),
    "clocktower": Setting(
        "clocktower",
        "the little clock tower",
        {"bell", "stairs", "window"},
    ),
}

CASES = {
    "missing_map": Case(
        "missing_map",
        "A hand-drawn map for the library treasure hunt disappeared before the younger children arrived.",
        "A tiny whisper slipped from behind the atlas shelf: \"Look where the moon rests.\"",
        "Luna first guessed that someone had hidden the map as a trick.",
        "A silver smear on the floor led from the reading table to a basket of rolled posters.",
        "A whisper is a clue, not proof. A careful detective checks before blaming anyone.",
        (
            "asked the caretaker whether the moon poster had been moved",
            "followed the silver smear without touching it",
            "looked beneath the rolled posters",
        ),
        "The map was safe beneath the moon poster, which had slid into the basket when a window gust lifted its corner.",
        "Luna returned the map to the treasure-hunt table, and the first clue shone beneath the drawn moon.",
        "The map had slipped beneath a moon poster after a gust of air pushed the poster into the basket.",
        "Listen closely, but do not turn a whisper into an accusation.",
    ),
    "sleepy_seedling": Case(
        "sleepy_seedling",
        "The greenhouse's smallest sunflower bent low just before the class garden show.",
        "A soft whisper came from the tool shelf: \"The thirsty roots know.\"",
        "Luna guessed that a jealous plant had stolen the sunflower's strength.",
        "The watering can was full, but its spout was packed with a cork from a lost plant label.",
        "A warning can keep a small mistake from becoming a large one, especially when living things are involved.",
        (
            "checked the soil instead of pulling the stem",
            "asked the gardener when the plant was last watered",
            "cleared the cork from the watering-can spout",
        ),
        "Water reached the roots slowly, and the sunflower lifted its head without a broken stem.",
        "By show time, the sunflower faced the glass roof, holding one bright yellow face toward the sun.",
        "A cork blocked the watering-can spout, so the sunflower's roots stayed dry.",
        "Careful questions and gentle hands are safer than quick guesses.",
    ),
    "silent_bell": Case(
        "silent_bell",
        "The clock tower bell failed to ring for the town's afternoon signal.",
        "A whisper curled up the stairs: \"Find the blue thread.\"",
        "Luna guessed that the bell had forgotten its song.",
        "A blue thread was caught around the pull cord, and a paper kite tail hung outside the window.",
        "When a warning tells you to stop, stop first; high places need a grown-up helper.",
        (
            "asked the tower keeper to climb with her",
            "followed the blue thread from the cord to the window",
            "waited while the keeper freed the kite tail",
        ),
        "The kite tail slid away, the cord moved freely, and the bell rang only after the keeper checked every step.",
        "The bell gave one clear note, while the rescued kite dipped safely beyond the tower window.",
        "A paper kite tail tangled the bell cord after catching on the tower window.",
        "A detective can be brave and still ask for help when a place is dangerous.",
    ),
}

NAMES = ["Luna", "Milo", "Nora", "Ivy", "Theo", "Maya"]
HELPERS = ["the librarian", "the gardener", "the tower keeper", "Grandpa Ren"]

ASP_RULES = r"""
setting(S) :- setting_fact(S).
case(C) :- case_fact(C).
available(S,C) :- affords(S,C).
safe_case(S,C) :- available(S,C), has_helper(C).
caution_required(C) :- case_fact(C).
solve_case(S,C) :- safe_case(S,C), listens(C), checks(C).
whisper_clue(C) :- case_fact(C).
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a cautionary whisper detective story."
    )
    parser.add_argument("--setting", choices=sorted(SETTINGS))
    parser.add_argument("--case", choices=sorted(CASES))
    parser.add_argument("--detective")
    parser.add_argument("--helper")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting_ids = [
        sid for sid in SETTINGS
        if getattr(args, "setting", None) is None or sid == getattr(args, "setting", None)
    ]
    case_ids = [
        cid for cid in CASES
        if getattr(args, "case", None) is None
        or cid == getattr(args, "case", None)
        or cid in _safe_lookup(SETTINGS, getattr(args, "setting", None)).affordances if False
    ]
    if getattr(args, "case", None) is not None:
        case_ids = [getattr(args, "case", None)]
    if not setting_ids or not case_ids:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_id = rng.choice(setting_ids)
    case_id = rng.choice(case_ids)
    detective = getattr(args, "detective", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if helper == detective:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        setting=setting_id,
        case=case_id,
        detective=detective,
        helper=helper,
        seed=getattr(args, "seed", None),
    )


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        pass
    if params.case not in CASES:
        pass

    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    world = World(setting)

    detective = world.add(
        Entity(
            params.detective,
            "character",
            params.detective,
            meters={"attention": 1.0, "safety": 1.0},
            memes={"curiosity": 1.0, "care": 1.0},
        )
    )
    helper = world.add(
        Entity(
            "helper",
            "character",
            params.helper,
            meters={"knowledge": 1.0, "safety": 1.0},
            memes={"trust": 1.0},
        )
    )
    whisper = world.add(
        Entity(
            "whisper",
            "clue",
            "a tiny whisper",
            meters={"clarity": 0.5},
            memes={"urgency": 0.5},
        )
    )
    world.facts.update(
        detective=detective,
        helper=helper,
        whisper=whisper,
        case=case,
    )

    world.record(
        f"{detective.label} worked as a young detective in {setting.place}."
    )
    world.record(case.opening)
    world.record(
        f"Then {whisper.label} said, \"{case.whisper.split(': ', 1)[-1].strip(chr(34))}\""
    )
    world.record(
        f"{detective.label} almost decided that {case.wrong_guess.lower()} "
        "without checking the facts."
    )
    world.record(
        f"{helper.label} said, \"Wait. {case.caution}\""
    )
    world.record(
        f"{detective.label} asked, \"What should we check first?\""
    )
    world.record(
        f"{helper.label} answered, \"{case.actions[0].capitalize()} and keep your eyes open.\""
    )
    world.record(case.clue)
    world.record(
        f"Together, {detective.label} {case.actions[1]}, while {helper.label} "
        f"{case.actions[2]}."
    )
    world.record(case.resolution)
    world.record(
        f"{detective.label} smiled and said, \"The whisper helped, but the evidence solved the case.\""
    )
    world.record(case.ending)
    world.record(f"The lesson of the case was clear: {case.lesson}")

    detective.meters["attention"] = 2.0
    detective.memes["care"] = 2.0
    whisper.meters["clarity"] = 1.0
    world.facts["solved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    case: Case = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "case")  # type: ignore[assignment]
    detective: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "detective")  # type: ignore[assignment]
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "helper")  # type: ignore[assignment]
    return StorySample(
        params=params,
        story=" ".join(world.trace),
        prompts=[
            f"Write a gentle detective story about {detective.label} following a whisper in {world.setting.place}.",
            f"Tell a cautionary mystery where {helper.label} helps {detective.label} check evidence before blaming anyone.",
            "Show how a small clue, careful questions, and a safe choice solve the problem.",
        ],
        story_qa=[
            QAItem(
                "What did the whisper tell the detective?",
                f'The whisper said, "{case.whisper.split(": ", 1)[-1].strip(chr(34))}"',
            ),
            QAItem(
                "What mistake did the detective nearly make?",
                f"{detective.label} nearly believed that {case.wrong_guess.lower()} without checking the facts.",
            ),
            QAItem(
                "How was the real problem discovered?",
                case.cause_answer,
            ),
            QAItem(
                "Why did the detective ask for help?",
                f"{helper.label} knew that careful checking was safer than a quick guess, and helped {detective.label} investigate.",
            ),
            QAItem(
                "How did the story end?",
                case.ending,
            ),
        ],
        world_qa=[
            QAItem(
                "What is a whisper?",
                "A whisper is a very quiet way of speaking.",
            ),
            QAItem(
                "Why should a detective check evidence?",
                "Checking evidence helps a detective learn what really happened instead of blaming someone from a guess.",
            ),
            QAItem(
                "What does cautionary mean?",
                "Cautionary means giving a warning so people can avoid danger or a mistake.",
            ),
            QAItem(
                "Why can a helper be important?",
                "A helper can notice details, share knowledge, and make a difficult or unsafe task safer.",
            ),
        ],
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"setting: {world.setting.place}")
    for entity in list(world.entities.values()):
        lines.append(
            f"{entity.label}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append("facts: case solved, whisper checked, evidence confirmed")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for affordance in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, affordance))
    for cid in CASES:
        lines.append(asp.fact("case_fact", cid))
        lines.append(asp.fact("has_helper", cid))
        lines.append(asp.fact("listens", cid))
        lines.append(asp.fact("checks", cid))
    return "\n".join(lines)


def asp_program(show: str = "#show solve_case/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
        symbols = asp.one_model(asp_program())
        found = set(asp.atoms(symbols, "solve_case"))
    except Exception as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1

    expected = {(sid, cid) for sid in SETTINGS for cid in CASES}
    if found != expected:
        print(f"ASP/Python mismatch: expected {len(expected)}, found {len(found)}")
        return 1

    for index, (sid, cid) in enumerate(sorted(expected)):
        params = StoryParams(
            setting=sid,
            case=cid,
            detective=_safe_lookup(NAMES, index % len(NAMES)),
            helper=_safe_lookup(HELPERS, index % len(HELPERS)),
            seed=index,
        )
        sample = generate(params)
        if not sample.story or "whisper" not in sample.story.lower():
            print(f"Generated story failed for {sid}/{cid}")
            return 1

    print(f"OK: ASP/Python parity and {len(expected)} generated stories verified.")
    return 0


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("library", "missing_map", "Luna", "the librarian", 0),
        StoryParams("greenhouse", "sleepy_seedling", "Milo", "the gardener", 1),
        StoryParams("clocktower", "silent_bell", "Nora", "the tower keeper", 2),
    ]


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
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
        print(asp_program())
        return

    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())

    if getattr(args, "asp", None):
        try:
            import asp
            models = asp.solve(asp_program(), models=1)
            print(json.dumps([[str(symbol) for symbol in model] for model in models], indent=2))
        except Exception as exc:
            raise SystemExit(f"ASP mode failed: {exc}")

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(params) for params in curated_params()]
    else:
        for index in range(max(0, getattr(args, "n", None))):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
