#!/usr/bin/env python3
"""
A small whodunit storyworld: someone lost a button, someone hid bouillon,
someone's slacks were suspicious, and teamwork plus bravery solved the mystery
with a few sound effects along the way.
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
# Core data model
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
    kind: str = "thing"  # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_ent: object | None = None
    culprit: object | None = None
    detective: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    mood: str
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
class Clue:
    id: str
    label: str
    phrase: str
    found_in: str
    suspicious: bool = False
    noisy: bool = False
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
class SuspectProfile:
    id: str
    label: str
    type: str
    job: str
    bravery: str
    teamwork: str
    sound: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

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
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="busy", affords={"search", "stir", "listen"}),
    "parlor": Setting(place="the parlor", mood="quiet", affords={"search", "listen", "whisper"}),
    "hall": Setting(place="the hall", mood="echoing", affords={"search", "listen", "run"}),
}

SUSPECTS = {
    "chef": SuspectProfile(
        id="chef",
        label="the chef",
        type="woman",
        job="stirring the supper pot",
        bravery="steady",
        teamwork="helpful",
        sound="clink-clink",
    ),
    "butler": SuspectProfile(
        id="butler",
        label="the butler",
        type="man",
        job="polishing silver",
        bravery="careful",
        teamwork="polite",
        sound="tap-tap",
    ),
    "neighbor": SuspectProfile(
        id="neighbor",
        label="the neighbor",
        type="woman",
        job="borrowing sugar",
        bravery="nervy",
        teamwork="friendly",
        sound="hush-hush",
    ),
}

CLUES = {
    "button": Clue(
        id="button",
        label="button",
        phrase="a tiny blue button",
        found_in="under the bench",
        suspicious=True,
        noisy=False,
    ),
    "bouillon": Clue(
        id="bouillon",
        label="bouillon",
        phrase="a little paper packet of bouillon",
        found_in="behind the sugar jar",
        suspicious=True,
        noisy=False,
    ),
    "slacks": Clue(
        id="slacks",
        label="slacks",
        phrase="a pair of gray slacks",
        found_in="by the laundry basket",
        suspicious=False,
        noisy=True,
    ),
    "spoon": Clue(
        id="spoon",
        label="spoon",
        phrase="a bent spoon",
        found_in="near the stove",
        suspicious=False,
        noisy=True,
    ),
}

HERO_NAMES = ["Mira", "Noah", "Tess", "Owen", "June", "Ivy", "Eli", "Ruby"]
TRAITS = ["curious", "brave", "sharp-eyed", "patient", "bold"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    culprit: str
    clue: str
    detective: str
    helper: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World construction and narration
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


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    detective = world.add(Entity(id=params.detective, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="child"))
    culprit = world.add(Entity(
        id=params.culprit,
        kind="character",
        type=_safe_lookup(SUSPECTS, params.culprit).type,
        label=_safe_lookup(SUSPECTS, params.culprit).label,
    ))
    clue = _safe_lookup(CLUES, params.clue)
    clue_ent = world.add(Entity(
        id=clue.id,
        type="thing",
        label=clue.label,
        phrase=clue.phrase,
        owner=culprit.id,
    ))
    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        clue=clue_ent,
        culprit_profile=_safe_lookup(SUSPECTS, params.culprit),
        setting=world.setting,
        params=params,
    )
    return world


def tell(world: World) -> None:
    p = _safe_fact(world, world.facts, "params")
    culprit = _safe_fact(world, world.facts, "culprit")
    helper = _safe_fact(world, world.facts, "helper")
    detective = _safe_fact(world, world.facts, "detective")
    clue = _safe_fact(world, world.facts, "clue")
    profile = _safe_fact(world, world.facts, "culprit_profile")

    world.say(
        f"{detective.id} was a {p.trait} little detective who loved a good whodunit."
    )
    world.say(
        f"One evening in {world.setting.place}, something odd was missing: a button, a bit of bouillon, and the calm of the room."
    )
    world.say(
        f"{helper.id} stayed close, because {world.setting.mood} places made small clues easier to miss."
    )

    world.para()
    world.say(
        f"Then came a clue trail. There was {clue.phrase} {clue.found_in}, and the nearest pair of slacks made a soft {profile.sound} when someone brushed past them."
    )
    world.say(
        f"{detective.id} noticed that {culprit.label} had the kind of careful hands that could hide a packet, but also the kind of teamwork that could bring it back."
    )

    world.para()
    world.say(
        f"{helper.id} took a brave breath and checked the flour tin while {detective.id} looked under the bench."
    )
    world.say(
        f"Together they matched the bouillon smell to the soup pot, then found the missing button caught in a loose cuff."
    )
    world.say(
        f"{culprit.label} had not stolen the clues at all; {culprit.pronoun('subject')} had simply been fixing the slacks, and the bouillon packet had slipped nearby with a little {profile.sound}."
    )
    world.say(
        f"In the end, everyone laughed, the supper was saved, and the detective knew that bravery and teamwork can solve even a quiet mystery."
    )

    world.facts["solution"] = "fixing the slacks and dropping the bouillon packet"
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f"Write a child-friendly whodunit set in {world.setting.place} that features a button and bouillon.",
        f"Tell a mystery story where {p.detective} and {p.helper} use teamwork and bravery to solve a clue about slacks.",
        "Write a short whodunit with a quiet clue trail, a mistaken suspect, and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    culprit: Entity = _safe_fact(world, world.facts, "culprit")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    detective: Entity = _safe_fact(world, world.facts, "detective")
    clue: Entity = _safe_fact(world, world.facts, "clue")
    prof: SuspectProfile = _safe_fact(world, world.facts, "culprit_profile")

    return [
        QAItem(
            question=f"Who was the detective in the mystery?",
            answer=f"The detective was {detective.id}, a {p.trait} child who kept watching for clues.",
        ),
        QAItem(
            question=f"What clue did they find by the end?",
            answer=f"They found {clue.phrase} and a missing button, which helped solve the mystery.",
        ),
        QAItem(
            question=f"Why did {culprit.label} seem suspicious at first?",
            answer=f"{culprit.label} seemed suspicious because the slacks made a sound and the bouillon packet was found nearby, but that turned out to be misleading.",
        ),
        QAItem(
            question=f"How did {detective.id} and {helper.id} solve the case?",
            answer=f"They used teamwork and brave searching. {helper.id} checked one spot while {detective.id} checked another, and together they matched the clues to {culprit.label}.",
        ),
        QAItem(
            question=f"What really happened to the bouillon?",
            answer=f"The bouillon packet slipped while {culprit.label} was fixing the slacks, so it was not a theft at all.",
        ),
        QAItem(
            question=f"What did the sound effect suggest?",
            answer=f"The {prof.sound} sound effect made it seem like someone was sneaking around, but it was really just a small accident.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bouillon?",
            answer="Bouillon is a tasty broth or a small packet used to add flavor to soup.",
        ),
        QAItem(
            question="What are slacks?",
            answer="Slacks are a kind of trousers that people can wear for work or for nicer everyday clothes.",
        ),
        QAItem(
            question="What is a button for?",
            answer="A button helps fasten clothing, like a shirt, coat, or pair of slacks.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to solve a problem.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means being willing to do something scary or difficult anyway.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = [f"{e.kind}/{e.type}"]
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        lines.append("  " + " ".join(bits))
    lines.append("  events:")
    lines.extend("    - " + ev for ev in world.trace_events)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Facts define settings, suspects, and clues.
% A clue is suspicious if it was marked suspicious in the registry.
suspicious(C) :- clue(C), suspicious_clue(C).

% The mystery is solved when teamwork and bravery connect the suspect to the
% clue trail without needing a true theft.
solved(P) :- detective(P), teamwork(P), bravery(P), clue(button), clue(bouillon).

#show solved/1.
#show suspicious/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("place", sid))
        lines.append(asp.fact("mood", sid, s.mood))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, prof in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("suspect_type", sid, prof.type))
        lines.append(asp.fact("job", sid, prof.job))
        lines.append(asp.fact("teamwork", sid))
        lines.append(asp.fact("bravery", sid))
        lines.append(asp.fact("sound_effect", sid, prof.sound))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.suspicious:
            lines.append(asp.fact("suspicious_clue", cid))
        if clue.noisy:
            lines.append(asp.fact("noisy_clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show suspicious/1.\n#show solved/1."))
    atoms = asp.atoms(model, "suspicious") + asp.atoms(model, "solved")
    if ("button",) in atoms and ("bouillon",) in atoms:
        print("OK: ASP twin sees the suspicious clues.")
        return 0
    print("Mismatch in ASP twin.")
    return 1


# ---------------------------------------------------------------------------
# Params, parsing, generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    culprit: str
    clue: str
    detective: str
    helper: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with bouillon, slacks, and a button.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    culprit = getattr(args, "culprit", None) or rng.choice(list(SUSPECTS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    detective = getattr(args, "detective", None) or rng.choice(HERO_NAMES)
    helper_choices = [n for n in HERO_NAMES if n != detective]
    helper = getattr(args, "helper", None) or rng.choice(helper_choices)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    if clue == "button" and culprit == "butler":
        pass
    if clue == "bouillon" and place == "hall":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, culprit=culprit, clue=clue, detective=detective, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show solved/1.\n#show suspicious/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solved/1.\n#show suspicious/1."))
        print(asp.atoms(model, "suspicious"))
        print(asp.atoms(model, "solved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()

    if getattr(args, "all", None):
        curated = [
            StoryParams("kitchen", "chef", "bouillon", "Mira", "Owen", "curious"),
            StoryParams("parlor", "butler", "button", "Tess", "Ivy", "sharp-eyed"),
            StoryParams("hall", "neighbor", "slacks", "Noah", "Ruby", "brave"),
        ]
        samples = [generate(p) for p in curated]
    else:
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} in {p.place} (culprit={p.culprit}, clue={p.clue})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
