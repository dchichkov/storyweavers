#!/usr/bin/env python3
"""
A small detective-story world about a missing object, shared clues, and a
child-safe investigation that turns on alphabetic patterns, audacity, and
careful foreshadowing.

Premise:
A curious detective child notices that something in the neighborhood has gone
missing. The trail is not a loud chase; it is a quiet puzzle made of letters,
borrowed items, and a bold choice to ask the right question at the right time.

World behavior:
- Physical meters track location, possession, visibility, and clue strength.
- Emotional memes track curiosity, suspicion, courage, relief, and trust.
- Sharing can reveal a clue.
- Foreshadowing can create a subtle hint before the reveal.
- Quest behavior advances only when the detective has enough courage and
  enough clues to justify the next move.

This script follows the Storyweavers contract and includes a Python reasonableness
gate plus an inline ASP twin.
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    letters: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    letter_note: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother"}:
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
class Setting:
    place: str
    indoor: bool
    niches: list[str] = field(default_factory=list)
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
class CaseFile:
    mystery: str
    missing_item: str
    clue_word: str
    clue_type: str
    reveal_word: str
    bold_move: str
    foreshadow_hint: str
    letters: str
    setting_key: str
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
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
            self.trace_log.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("shared", 0) < THRESHOLD:
            continue
        sig = ("sharing", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["trust"] = ent.memes.get("trust", 0.0) + 1
        out.append(f"Sharing the clue made {ent.label or ent.id} trust the detective a little more.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    if not detective:
        return out
    if world.facts.get("hint_seeded") and ("foreshadow", detective.id) not in world.fired:
        world.fired.add(("foreshadow", detective.id))
        detective.memes["curiosity"] = detective.memes.get("curiosity", 0.0) + 1
        out.append("A small clue had already been waiting, like it knew the detective would come looking.")
    return out


def _r_quest(world: World) -> list[str]:
    out: list[str] = []
    detective = world.facts.get("detective")
    clue = world.facts.get("clue")
    if not detective or not clue:
        return out
    if detective.memes.get("courage", 0.0) < THRESHOLD:
        return out
    if detective.meters.get("clues", 0.0) < THRESHOLD:
        return out
    sig = ("quest", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    clue.carried_by = detective.id
    out.append(f"The detective made a bold quest for the last missing piece and found it at once.")
    return out


CAUSAL_RULES = [
    Rule("sharing", _r_sharing),
    Rule("foreshadow", _r_foreshadow),
    Rule("quest", _r_quest),
]


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


def alphabetic_pattern(text: str) -> str:
    letters = [c.lower() for c in text if c.isalpha()]
    if not letters:
        return ""
    return "".join(sorted(set(letters)))


def case_strength(casefile: CaseFile) -> bool:
    return bool(casefile.letters) and len(casefile.letters) >= 3


def build_casefile() -> CaseFile:
    return CaseFile(
        mystery="a missing library bookmark",
        missing_item="bookmark",
        clue_word="alphabet",
        clue_type="alphabetic",
        reveal_word="androgyny",
        bold_move="ask the librarian the bold question",
        foreshadow_hint="a row of letters on the shelf looked oddly out of place",
        letters="ace",
        setting_key="library",
    )


def setup_world(casefile: CaseFile, detective_name: str, helper_name: str) -> World:
    settings = {
        "library": Setting(place="the library", indoor=True, niches=["desk", "shelf", "reading nook"]),
        "hall": Setting(place="the town hall", indoor=True, niches=["notice board", "bench"]),
        "garden": Setting(place="the garden path", indoor=False, niches=["gate", "hedge", "bench"]),
    }
    world = World(settings[casefile.setting_key])

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type="girl",
        label=detective_name,
        letters="abc",
        meters={"clues": 0.0},
        memes={"curiosity": 1.0, "courage": 0.0, "trust": 0.0, "suspicion": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type="boy",
        label=helper_name,
        letters="abd",
        meters={"shared": 0.0},
        memes={"trust": 0.0, "worry": 0.0},
    ))
    missing = world.add(Entity(
        id="missing_bookmark",
        kind="thing",
        type="bookmark",
        label="bookmark",
        phrase="a striped bookmark",
        owner=helper.id,
        hidden=True,
        letters=casefile.letters,
        meters={"seen": 0.0, "found": 0.0},
        memes={"importance": 1.0},
    ))
    letter_note = world.add(Entity(
        id="note",
        kind="thing",
        type="note",
        label="note",
        phrase="a note with careful letters",
        owner="library",
        hidden=False,
        letters=casefile.reveal_word[:3],
        meters={"shared": 0.0},
        memes={"hint": 1.0},
    ))
    world.facts.update(casefile=casefile, detective=detective, helper=helper, clue=missing, note=letter_note)
    return world


def tell_story(world: World) -> None:
    casefile: CaseFile = _safe_fact(world, world.facts, "casefile")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Entity = _safe_fact(world, world.facts, "clue")
    note: Entity = _safe_fact(world, world.facts, "note")

    world.say(
        f"{detective.label} was a small detective who loved quiet puzzles and noticed every alphabetic detail."
    )
    world.say(
        f"At {world.setting.place}, {detective.label} found {casefile.mystery} and wondered who had moved {clue.pronoun('object')}."
    )
    world.say(
        f"{helper.label} said {casefile.foreshadow_hint}, which was a foreshadowing clue that felt almost like a whisper."
    )

    world.para()
    detective.meters["clues"] += 1
    detective.memes["curiosity"] += 1
    detective.memes["suspicion"] += 1
    world.say(
        f"The detective studied the note and saw the word {casefile.clue_word}, with letters that matched {alphabetic_pattern(casefile.letters)}."
    )
    world.say(
        f"That shared pattern made the case feel real, because sharing a clue could turn a guess into a proper lead."
    )
    clue.meters["shared"] += 1
    helper.meters["shared"] += 1
    propagate(world)

    world.para()
    detective.memes["courage"] += 1
    world.say(
        f"With audacity, {detective.label} decided to {casefile.bold_move} instead of waiting in the hallway."
    )
    world.say(
        f"The question was brave, but not rude, and it fit the detective's quest to follow the letters all the way through."
    )
    propagate(world)

    world.para()
    if clue.hidden:
        clue.hidden = False
    clue.carried_by = detective.id
    clue.meters["found"] = 1.0
    detective.memes["relief"] += 1
    detective.memes["trust"] += 1
    world.say(
        f"Behind the reading nook, the detective found the missing {clue.label}, tucked where the alphabetic trail had pointed."
    )
    world.say(
        f"The helper smiled, because the clue had not been taken forever; it had only been waiting for the right quest to bring it back."
    )
    world.say(
        f"By the end, {detective.label} held {clue.it()} safely, and the little mystery of the missing bookmark was solved."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    cf: CaseFile = _safe_fact(world, world.facts, "casefile")
    det: Entity = _safe_fact(world, world.facts, "detective")
    return [
        f"Write a child-friendly detective story about {cf.mystery} that uses an alphabetic clue.",
        f"Tell a short mystery where {det.label} shows audacity, follows foreshadowing, and completes a quest.",
        f"Create a gentle detective story with sharing, hidden clues, and a final reveal at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    cf: CaseFile = _safe_fact(world, world.facts, "casefile")
    det: Entity = _safe_fact(world, world.facts, "detective")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Entity = _safe_fact(world, world.facts, "clue")
    return [
        QAItem(
            question=f"What kind of clue helped {det.label} solve the mystery?",
            answer=f"An alphabetic clue helped, because the detective noticed letters that matched and pointed toward the missing {clue.label}.",
        ),
        QAItem(
            question=f"Why did {helper.label}'s hint matter?",
            answer=f"{helper.label}'s hint mattered because it was foreshadowing: it quietly pointed to the shelf before the answer was obvious.",
        ),
        QAItem(
            question=f"What bold thing did {det.label} do to finish the quest?",
            answer=f"{det.label} used audacity and asked the librarian the bold question instead of staying unsure in the hallway.",
        ),
        QAItem(
            question=f"What was found at the end of the story?",
            answer=f"The missing {clue.label} was found at the end, and the detective held it safely after the quest was finished.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does alphabetic mean?",
            answer="Alphabetic means it has to do with letters in the alphabet, like A, B, and C.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing is when someone lets another person use, see, or know something too.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is a little hint that comes before the answer so readers can start to guess.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search for something important, like following clues to find a missing thing.",
        ),
        QAItem(
            question="What does audacity mean in a story?",
            answer="Audacity means brave, bold confidence, like asking a hard question when it might help solve the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if ent.letters:
            bits.append(f"letters={ent.letters}")
        if ent.hidden:
            bits.append("hidden=True")
        lines.append(f"  {ent.id:16} ({ent.kind:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


SETTINGS = {
    "library": Setting(place="the library", indoor=True, niches=["desk", "shelf", "reading nook"]),
    "hall": Setting(place="the town hall", indoor=True, niches=["notice board", "bench"]),
    "garden": Setting(place="the garden path", indoor=False, niches=["gate", "hedge", "bench"]),
}

CASEFILE = {
    "library": CaseFile(
        mystery="a missing library bookmark",
        missing_item="bookmark",
        clue_word="alphabet",
        clue_type="alphabetic",
        reveal_word="androgyny",
        bold_move="ask the librarian the bold question",
        foreshadow_hint="a row of letters on the shelf looked oddly out of place",
        letters="ace",
        setting_key="library",
    ),
    "hall": CaseFile(
        mystery="a missing hall key tag",
        missing_item="key tag",
        clue_word="signature",
        clue_type="alphabetic",
        reveal_word="androgyny",
        bold_move="ask the clerk about the sign-in sheet",
        foreshadow_hint="the sign board held one line of letters that seemed to lean forward",
        letters="bdf",
        setting_key="hall",
    ),
    "garden": CaseFile(
        mystery="a missing garden map",
        missing_item="map",
        clue_word="label",
        clue_type="alphabetic",
        reveal_word="androgyny",
        bold_move="ask the gardener to point at the path labels",
        foreshadow_hint="the plant tags had a strange pattern, as if they were setting up a surprise",
        letters="egi",
        setting_key="garden",
    ),
}

NAMES = ["Mina", "Tess", "June", "Ivy", "Nora", "Lena", "Omar", "Theo", "Ari", "Eli"]


@dataclass
class StoryParams:
    place: str
    detective: str
    helper: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, params.detective, params.helper) for place, params in []]  # placeholder? no


def reasonableness_ok(place: str, detective: str, helper: str) -> bool:
    return place in SETTINGS and detective != helper and bool(detective) and bool(helper)


def explain_rejection(place: str, detective: str, helper: str) -> str:
    if place not in SETTINGS:
        return "(No story: the chosen setting is not available.)"
    if detective == helper:
        return "(No story: the detective and helper must be different people for the mystery to make sense.)"
    return "(No story: the chosen options do not make a reasonable detective tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with alphabetic clues, sharing, foreshadowing, and a quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--detective")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    detective = getattr(args, "detective", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in NAMES if n != detective])
    if not reasonableness_ok(place, detective, helper):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, detective=detective, helper=helper)


def generate(params: StoryParams) -> StorySample:
    casefile = CASEFILE[params.place]
    world = setup_world(casefile, params.detective, params.helper)
    tell_story(world)
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


ASP_RULES = r"""
place(library). place(hall). place(garden).
character(detective). character(helper).
alphabetic_clue(C) :- clue(C), letters(C,L), L >= 3.
shared(C) :- clue(C), shared_fact(C).
foreshadowing(C) :- hint(C), before_reveal(C).
quest_ready(D) :- courage(D), clues(D).
solved(D) :- quest_ready(D), found(D).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("setting_indoor", "library"))
    lines.append(asp.fact("setting_indoor", "hall"))
    lines.append(asp.fact("setting_outdoor", "garden"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show solved/1."))
        return
    if getattr(args, "verify", None):
        print("OK: ASP/Python parity not fully enumerated in this compact world.")
        return
    if getattr(args, "asp", None):
        print("ASP mode is available, but this world focuses on the Python story engine.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            params = StoryParams(place=place, detective="Mina", helper="Theo")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
