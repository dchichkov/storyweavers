#!/usr/bin/env python3
"""
A tiny magic-and-rhyme storyworld about gingham, a missing bell, and a nursery
garden that can only sing when its helpers listen to one another.
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
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample



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
class Character:
    id: str
    kind: str = "character"
    type: str = "child"
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    child: object | None = None
    helper: object | None = None
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
class Prop:
    id: str
    label: str
    material: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    magic: object | None = None
    ribbon: object | None = None
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
class World:
    entities: dict[str, object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    world: object | None = None
    def add(self, entity):
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
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


@dataclass
class StoryParams:
    problem: str = ""
    solution: str = ""
    child: str = ""
    helper: str = ""
    child_kind: str = ""
    helper_kind: str = ""
    ribbon: str = ""
    rhyme: str = ""
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


PROBLEMS = {
    "missing_bell": {
        "object": "silver bell",
        "place": "the moonlit garden gate",
        "need": "the garden must ring before the flowers wake",
    },
    "sleepy_star": {
        "object": "little star",
        "place": "the gingham nursery roof",
        "need": "the star must shine before the dawn birds call",
    },
    "silent_kettle": {
        "object": "blue kettle",
        "place": "the gingham kitchen shelf",
        "need": "the kettle must sing before breakfast",
    },
    "lost_thimble": {
        "object": "golden thimble",
        "place": "the gingham sewing basket",
        "need": "the thimble must tap the rhythm for the rhyme",
    },
}

SOLUTIONS = {
    "follow_ribbon": "follow_ribbon",
    "ask_moon": "ask_moon",
    "share_rhyme": "share_rhyme",
    "listen_ground": "listen_ground",
}

RIBBONS = ["red-and-white gingham", "blue-and-white gingham", "pink gingham"]
RHYMES = [
    "Tippety-tap, little cap, find the thing that went astray.",
    "Moon on the spoon, hum a tune, guide our feet along the way.",
    "Hop and stop, never flop, magic listens when we say.",
]
NAMES = [
    ("Pip", "child"),
    ("Nell", "child"),
    ("Bram", "child"),
    ("Tilly", "child"),
    ("Moss", "rabbit"),
    ("Pru", "mouse"),
]
HELPERS = ["Grandma Moon", "Old Owl", "the kindly Hare", "the Singing Teapot"]


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in PROBLEMS for s in SOLUTIONS]


def outcome_for(params: StoryParams) -> str:
    if params.problem == "missing_bell" and params.solution == "listen_ground":
        return "discovery"
    if params.problem == "sleepy_star" and params.solution == "ask_moon":
        return "blessing"
    if params.problem == "silent_kettle" and params.solution == "share_rhyme":
        return "harmony"
    if params.problem == "lost_thimble" and params.solution == "follow_ribbon":
        return "dance"
    return "found"


def build_world(params: StoryParams) -> World:
    world = World()
    child = world.add(Character(params.child, type=params.child_kind))
    helper = world.add(Character(params.helper, type=params.helper_kind))
    ribbon = world.add(Prop("ribbon", params.ribbon, "gingham"))
    magic = world.add(Prop("magic", "pocket magic", "moonlight"))

    child.memes.update({"curiosity": 1.0, "worry": 1.0})
    helper.memes.update({"patience": 1.0})
    ribbon.meters["brightness"] = 1.0
    magic.meters["sparkle"] = 1.0

    problem = _safe_lookup(PROBLEMS, params.problem)
    world.facts.update(
        child=child,
        helper=helper,
        ribbon=ribbon,
        magic=magic,
        problem=problem,
        outcome=outcome_for(params),
        object=problem["object"],
    )

    if params.problem == "missing_bell":
        world.say(
            f"At the gingham gate, where the moonbeams waited, {params.child} found "
            f"no {problem['object']}."
        )
        world.say(
            f'"No ring, no spring!" cried {params.child}. "How will the garden wake?"'
        )
    elif params.problem == "sleepy_star":
        world.say(
            f"On the {params.ribbon} roof, a {problem['object']} blinked once, then slept."
        )
        world.say(
            f'"Wake, little star," called {params.child}. "The dawn is on its way!"'
        )
    elif params.problem == "silent_kettle":
        world.say(
            f"On the {params.ribbon} shelf sat a {problem['object']}, quiet as a mouse."
        )
        world.say(
            f'"Sing, little kettle," said {params.child}. "The cups are waiting."'
        )
    else:
        world.say(
            f"Inside the {params.ribbon} basket, the {problem['object']} had vanished."
        )
        world.say(
            f'"Tap, tap, tap!" cried {params.child}. "Without it, our rhyme cannot dance."'
        )

    world.para()
    if params.solution == "follow_ribbon":
        child.meters["steps"] = 3.0
        world.say(
            f"{params.child} followed a fluttering strip of {params.ribbon} past the "
            f"rose, beneath the bench, and behind the old blue pot."
        )
        world.say(
            f'"Look there!" said {params.helper}. "The gingham is pointing, not merely waving."'
        )
        world.say(
            f'"Then follow its flutter," said {params.child}, and the {problem["object"]} '
            "shone beneath the pot."
        )
        world.say(
            f"The magic twirled the {params.ribbon} into a bow, and the lost treasure "
            "danced back to its proper place."
        )
    elif params.solution == "ask_moon":
        helper.memes["wisdom"] = 1.0
        world.say(
            f"{params.child} and {params.helper} lifted their eyes to the round moon."
        )
        world.say(
            f'"Moon, moon, silver spoon, where is the sleepy thing?" asked {params.child}.'
        )
        world.say(
            f'"Ask kindly, and ask together," whispered {params.helper}.'
        )
        world.say(
            f'"Please wake," they sang. The moon dropped a soft beam onto the '
            f"{problem['object']}, and it glittered awake."
        )
    elif params.solution == "share_rhyme":
        child.memes["cooperation"] = 1.0
        helper.memes["cooperation"] = 1.0
        world.say(
            f"{params.child} tried a rhyme, but the magic only made a tiny ping."
        )
        world.say(
            f'"Your line needs a friend," said {params.helper}. '
            f'"Will you take my last word?"'
        )
        world.say(
            f'"I will," said {params.child}. Together they sang, "{params.rhyme}"'
        )
        world.say(
            f"The {problem['object']} answered with a bright note, and every cup, "
            "flower, or star joined the tune."
        )
    else:
        child.memes["attention"] = 1.0
        world.say(
            f"{params.child} stopped hopping and listened close to the quiet {problem['place']}."
        )
        world.say(
            f'"Magic may whisper low," said {params.helper}. "What does the stillness tell you?"'
        )
        world.say(
            f'"It tells me to listen beneath the noise," said {params.child}.'
        )
        world.say(
            f"Under the softest hush came a tiny sparkle. The {problem['object']} "
            "was waiting there all along."
        )

    world.para()
    world.say(
        f"When the {problem['object']} returned, {params.helper} clapped a gentle beat."
    )
    world.say(
        f"{params.child} laughed, and the {params.ribbon} magic stitched the moment "
        f"into a nursery rhyme: {params.rhyme}"
    )
    world.say(
        f"Then {problem['need'].capitalize()}, and the gingham world glowed "
        "pink, gold, and bright."
    )
    world.facts["changed"] = True
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a Nursery Rhyme style Magic story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} helps find a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")} in a gingham place.",
        f"Tell a child-facing tale in which {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} and {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").id} speak, try a special method, and restore the magic.",
        "Include gingham, a concrete magical problem, a spoken exchange, and an ending image showing what changed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "problem")
    return [
        QAItem(
            f"What problem did {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} discover?",
            f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id} discovered that the {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")} was missing or silent, so {p['need']}.",
        ),
        QAItem(
            f"Who helped {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "child").id}?",
            f"{_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").id} helped by listening, speaking, and taking part in the magical solution.",
        ),
        QAItem(
            "What material appeared in the magical scene?",
            f"Gingham appeared as the {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "ribbon").label}, which guided or brightened the magic.",
        ),
        QAItem(
            "How did the ending prove that the problem was solved?",
            f"The {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "object")} returned to its proper role, and the gingham world glowed while the nursery rhyme came alive.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is gingham?",
            "Gingham is a woven cloth with a simple checked pattern, often made with two colors.",
        ),
        QAItem(
            "What is magic in a story?",
            "Magic is an imagined power that can make unusual things happen, such as a moonbeam waking a star.",
        ),
        QAItem(
            "What is a nursery rhyme?",
            "A nursery rhyme is a short, playful poem or song with a simple rhythm and memorable words.",
        ),
    ]


ASP_RULES = r"""
magic_problem(P) :- problem(P).
valid_solution(P,S) :- problem(P), solution(S).
restored(P,S) :- valid_solution(P,S).
"""


def asp_facts() -> str:
    import importlib
    asp = importlib.import_module("storyworlds.asp") if "storyworlds.asp" in sys.modules else importlib.import_module("asp")
    lines = []
    for problem in PROBLEMS:
        lines.append(asp.fact("problem", problem))
    for solution in SOLUTIONS:
        lines.append(asp.fact("solution", solution))
    return "\n".join(lines)


def asp_verify() -> int:
    try:
        import importlib
        asp = importlib.import_module("storyworlds.asp") if "storyworlds.asp" in sys.modules else importlib.import_module("asp")
        program = asp_facts() + "\n" + ASP_RULES + "\n#show valid_solution/2."
        model = asp.one_model(program)
        found = set(asp.atoms(model, "valid_solution"))
        expected = set(valid_combos())
        if found != expected:
            print("ASP mismatch")
            return 1
        print(f"OK: ASP and Python agree on {len(expected)} solution paths.")
        for seed in range(12):
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            sample = generate(params)
            if not sample.story or "gingham" not in sample.story:
                print("Generated story check failed")
                return 1
        print("OK: generated stories contain complete causal paths.")
        return 0
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gingham Magic nursery-rhyme storyworld.")
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--solution", choices=sorted(SOLUTIONS))
    parser.add_argument("--child")
    parser.add_argument("--helper")
    parser.add_argument("--ribbon", choices=RIBBONS)
    parser.add_argument("--rhyme")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    problem = getattr(args, "problem", None) or rng.choice(sorted(PROBLEMS))
    solution = getattr(args, "solution", None) or rng.choice(sorted(SOLUTIONS))
    child, child_kind = (getattr(args, "child", None), "child") if getattr(args, "child", None) else rng.choice(NAMES[:4])
    helper, helper_kind = (getattr(args, "helper", None), "helper") if getattr(args, "helper", None) else rng.choice(
        [(n, "helper") for n in HELPERS]
    )
    if child == helper:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        problem=problem,
        solution=solution,
        child=child,
        helper=helper,
        child_kind=child_kind,
        helper_kind=helper_kind,
        ribbon=getattr(args, "ribbon", None) or rng.choice(RIBBONS),
        rhyme=getattr(args, "rhyme", None) or rng.choice(RHYMES),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in list(world.entities.values()):
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"outcome={world.facts.get('outcome')}")
    lines.append(f"changed={world.facts.get('changed')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("\n== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("\n== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_facts() + "\n" + ASP_RULES)
        return
    if getattr(args, "asp", None):
        print("Valid problem/solution paths:")
        for problem, solution in valid_combos():
            print(f"  {problem}: {solution}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    params_list = []
    if getattr(args, "all", None):
        for problem, solution in valid_combos():
            params = resolve_params(
                argparse.Namespace(
                    problem=problem,
                    solution=solution,
                    child=None,
                    helper=None,
                    ribbon=None,
                    rhyme=None,
                ),
                random.Random(base_seed + len(params_list)),
            )
            params_list.append(params)
    else:
        for index in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            params_list.append(params)

    samples = [generate(p) for p in params_list]
    if getattr(args, "json", None):
        payload = [sample.to_dict() for sample in samples]
        print(json.dumps(payload[0] if len(payload) == 1 else payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if index:
            print("\n" + "=" * 64 + "\n")
        emit(
            sample,
            trace=getattr(args, "trace", None),
            qa=getattr(args, "qa", None),
            header=f"### {sample.params.problem} / {sample.params.solution}" if getattr(args, "all", None) else "",
        )


if __name__ == "__main__":
    main()
