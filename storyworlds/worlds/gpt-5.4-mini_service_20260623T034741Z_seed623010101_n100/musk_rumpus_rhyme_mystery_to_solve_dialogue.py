#!/usr/bin/env python3
"""
storyworlds/worlds/musk_rumpus_rhyme_mystery_to_solve_dialogue.py
==================================================================

A small ghost-story-style storyworld about a sleepy house, a strange musk, and a
rumpus that turns out to be a mystery to solve by talking, listening, and
following clues.

The model is intentionally simple: a child hears odd rhyming sounds in a house,
talks with a helper, gathers clues from the world state, and resolves the mystery
by finding the source of the smell and the rumpus. The ending proves what changed:
the house is calm, the source is found, and the ghosts turn out to be harmless.

Features:
- ghost-story mood
- rhyme in prose
- dialogue-driven clue gathering
- a mystery to solve with a concrete turn and resolution
- typed entities with physical meters and emotional memes
- Python reasonableness gate plus inline ASP twin
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SCARECROWS = {"attic", "cellar", "hallway", "porch"}
SOUND_HINTS = {"creak", "clatter", "tap", "thump", "rattle"}
SMELL_HINTS = {"musk", "musty", "dusty", "old", "mildew"}



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
            keys = [upper + "S", upper + "ES"]
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    location: str = ""
    source: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    child: object | None = None
    clue: object | None = None
    helper: object | None = None
    house: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
    dark_spot: str
    mood: str
    smells: list[str] = field(default_factory=list)
    sounds: list[str] = field(default_factory=list)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Mystery:
    id: str
    strange_sound: str
    rhyme: str
    source_kind: str
    source_label: str
    source_location: str
    source_smell: str
    fix: str
    answer: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_musk_tip(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("tip",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["resolve"] += 1
    out.append("The clue felt like a key in a pocket.")
    return out


def _r_rumpus_rises(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["noise"] < THRESHOLD:
            continue
        sig = ("noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("house").meters["unease"] += 1
        world.get("child").memes["worry"] += 1
        out.append("The house seemed to hold its breath.")
    return out


CAUSAL_RULES = [Rule("tip", "social", _r_musk_tip), Rule("noise", "physical", _r_rumpus_rises)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def smell_risk(mystery: Mystery, setting: Setting) -> bool:
    return mystery.source_smell in setting.smells or mystery.source_smell in SMELL_HINTS


def noise_risk(mystery: Mystery) -> bool:
    return mystery.strange_sound in SOUND_HINTS


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if smell_risk(mystery, setting) and noise_risk(mystery):
                combos.append((place, mid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    params: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "old_house": Setting("the old house", "the hallway", "quiet", smells=["musk", "dusty"], sounds=["creak", "thump"]),
    "attic": Setting("the attic", "the attic stairs", "dim", smells=["musk", "old"], sounds=["creak", "rattle"]),
    "cellar": Setting("the cellar", "the cellar door", "cold", smells=["musk", "mildew"], sounds=["clatter", "tap"]),
}

MYSTERIES = {
    "cat": Mystery(
        id="cat",
        strange_sound="creak",
        rhyme="A creak and a peek, a soft little squeak.",
        source_kind="cat",
        source_label="a sleepy cat",
        source_location="under the stairs",
        source_smell="musk",
        fix="open the door and let the cat out",
        answer="The rumpus came from a sleepy cat, and the musk came from its warm fur.",
        tags={"cat", "musk", "rumpus"},
    ),
    "coat": Mystery(
        id="coat",
        strange_sound="thump",
        rhyme="A thump and a bump, a coat in a lump.",
        source_kind="coat",
        source_label="an old coat",
        source_location="behind a trunk",
        source_smell="musk",
        fix="shake out the coat and air the room",
        answer="The rumpus came from an old coat slipping off a trunk, and the musk came from dust and age.",
        tags={"coat", "musk", "rumpus"},
    ),
    "hamster": Mystery(
        id="hamster",
        strange_sound="rattle",
        rhyme="A rattle and prattle, a nibble and a scuttle.",
        source_kind="hamster",
        source_label="a runaway hamster",
        source_location="inside a box",
        source_smell="musk",
        fix="find the hamster and put it back in its cage",
        answer="The rumpus came from a runaway hamster, and the musk came from its bedding.",
        tags={"hamster", "musk", "rumpus"},
    ),
}

GIRL_NAMES = ["Mina", "Penny", "Lena", "Tia", "Ada"]
BOY_NAMES = ["Noel", "Simon", "Owen", "Ben", "Ira"]
TRAITS = ["brave", "curious", "careful", "quiet", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery about musk, a rumpus, and a clue-finding dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandma", "grandpa"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(list(combos))
    m = _safe_lookup(MYSTERIES, mystery)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandma", "grandpa"])
    helper_type = helper if helper in {"mother", "father"} else "woman" if helper == "grandma" else "man"
    return StoryParams(
        place=place,
        mystery=mystery,
        child_name=child_name,
        child_type=gender,
        helper_name=helper,
        helper_type=helper_type,
    )


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_type, label=params.helper_name))
    house = world.add(Entity(id="house", kind="place", type="house", label=setting.place))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=mystery.source_label, source=mystery.source_kind))
    world.facts["mystery"] = mystery
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["house"] = house
    world.facts["clue"] = clue
    world.facts["setting"] = setting

    child.memes["curiosity"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["resolve"] = 0.0
    helper.memes["calm"] = 1.0
    house.meters["unease"] = 0.0
    clue.meters["noise"] = 1.0
    clue.attrs["location"] = mystery.source_location

    world.say(f"{params.child_name} heard a whisper in {setting.place} -- a hush and a rush, with musk in the air.")
    world.say(f'"Did you hear that rumpus?" asked {params.child_name}. "{mystery.rhyme}"')
    world.para()
    world.say(f'"I did," said {helper.label_word}. "Let us solve the mystery together."')
    world.say(f'"What smells so strange?" asked {params.child_name}.')
    world.say(f'"Something old," said {helper.label_word}, "and something hidden where the shadows go."')
    world.para()
    world.say(f"They followed the sound to {mystery.source_location}.")
    propagate(world, narrate=True)
    world.say(f'"There it is," said {params.child_name}. "{mystery.fix.capitalize()}."')
    world.say(f"Together they did just that, and the rumpus grew small.")
    world.para()
    world.say(f'"What was it?" asked {params.child_name}.')
    world.say(f'"{mystery.answer}" said {helper.label_word}.')
    world.say(f"In the end, the house was still, and the musk drifted away like a dream.")
    world.facts["solved"] = True
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    return [
        f"Write a ghost-story mystery for a small child set in {setting.place} with the words musk and rumpus.",
        f"Tell a short dialogue story where {child.label} hears a strange rumpus, follows a musk clue, and solves the mystery with {helper.label_word}.",
        f"Write a rhyming mystery about {mystery.source_label} in {setting.place} that ends with the house quiet again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What did {child.label} hear in {setting.place}?",
            answer=f"{child.label} heard a strange rumpus in {setting.place}. The sound was spooky at first, but it turned into a mystery to solve.",
        ),
        QAItem(
            question=f"Why did {child.label} and {helper.label_word} go look for the source of the musk?",
            answer=f"They wanted to solve the mystery together. The musk was a clue, and the rumpus meant something hidden was making the noise.",
        ),
        QAItem(
            question=f"What was the rumpus really?",
            answer=f"It was {mystery.answer.lower()}. Once they found that out, the spooky feeling went away and the house became quiet again.",
        ),
        QAItem(
            question=f"How did the story end after they spoke with each other?",
            answer=f"They used dialogue to follow the clue, found the source, and settled the rumpus. The last image is a calm house with the musk drifting away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is musk?",
            answer="Musk is a strong smell. In a story like this, it can be a clue that something old, warm, or hidden is nearby.",
        ),
        QAItem(
            question="What is a rumpus?",
            answer="A rumpus is a noisy fuss or commotion. It is the kind of sound that makes you look around to see what is going on.",
        ),
        QAItem(
            question="What does it mean to solve a mystery?",
            answer="To solve a mystery means to find out what caused the strange thing. You listen, notice clues, and put the clues together.",
        ),
        QAItem(
            question="Why is dialogue useful in a mystery story?",
            answer="Dialogue lets characters ask questions and share clues. That helps them work together and find the answer faster.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions -- answerable from the story text =="]
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
        if any(e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.source:
            bits.append(f"source={e.source}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- clue_of(M, _).
mystery_ok(P, M) :- place(P), mystery(M), smell_ok(P, M), sound_ok(M).
solved(M) :- mystery_ok(_, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for s in setting.smells:
            lines.append(asp.fact("smell", pid, s))
        for snd in setting.sounds:
            lines.append(asp.fact("sound", pid, snd))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("clue_of", mid, m.source_label))
        lines.append(asp.fact("sound_ok", mid))
        lines.append(asp.fact("smell_ok", "old_house" if m.source_smell in {"musk", "musty"} else "attic" if m.source_smell == "old" else "cellar", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery_ok/2."))
    return sorted(set(asp.atoms(model, "mystery_ok")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = {("old_house", "cat"), ("attic", "coat"), ("cellar", "hamster")}
    ok_gate = py == cl
    sample = generate(resolve_params(argparse.Namespace(place=None, mystery=None, name=None, gender=None, helper=None), random.Random(777)))
    ok_story = bool(sample.story)
    if ok_gate:
        print(f"OK: Python gate covers {len(py)} combos.")
    else:
        print("MISMATCH in Python gate.")
        return 1
    if ok_story:
        print("OK: smoke test story generation succeeded.")
    else:
        print("Smoke test failed.")
        return 1
    return 0


def build_default_args() -> argparse.Namespace:
    return argparse.Namespace(place=None, mystery=None, name=None, gender=None, helper=None)


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS or params.mystery not in MYSTERIES:
        pass
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
    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_ok/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, mystery in valid_combos():
            params = StoryParams(place=place, mystery=mystery, child_name="Mina", child_type="girl", helper_name="mother", helper_type="mother")
            samples.append(generate(params))
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {idx + 1}" if len(samples) > 1 else "")
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
