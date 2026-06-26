#!/usr/bin/env python3
"""
Standalone storyworld: witness_bad_ending_reconciliation_flashback_detective_story.py

A small detective-style world with a witness, a bad ending, a flashback, and a
reconciliation. The model is state-driven: clues, suspicion, memory, truth, and
repair all matter to what gets narrated.
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
# Core world model
# ---------------------------------------------------------------------------


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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    cul: object | None = None
    det: object | None = None
    obj: object | None = None
    wit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective"}
        male = {"boy", "man", "father", "detective"}
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
class Location:
    id: str
    label: str
    indoors: bool = True
    traits: set[str] = field(default_factory=set)
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
    setting: str
    detective: str
    witness: str
    culprit: str
    object: str
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


@dataclass
class WitnessProfile:
    name: str
    type: str
    clue: str
    saw: str
    memory_trigger: str
    reconciles_with: str
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


@dataclass
class World:
    location: Location
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    flashback_active: bool = False

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.location)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_active = self.flashback_active
        return clone


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


LOCATIONS = {
    "dock": Location("dock", "the old dock", indoors=False, traits={"wet", "echoing", "quiet"}),
    "station": Location("station", "the train station", indoors=True, traits={"busy", "echoing"}),
    "library": Location("library", "the little library", indoors=True, traits={"quiet", "dusty"}),
    "alley": Location("alley", "the narrow alley", indoors=False, traits={"dark", "echoing"}),
}

WITNESSES = {
    "shopkeeper": WitnessProfile(
        name="Mara",
        type="woman",
        clue="a blue ribbon",
        saw="a blue ribbon fluttering in the wind",
        memory_trigger="the ribbon",
        reconciles_with="the detective",
    ),
    "porter": WitnessProfile(
        name="Otto",
        type="man",
        clue="a muddy shoeprint",
        saw="a muddy shoeprint beside the bench",
        memory_trigger="the shoeprint",
        reconciles_with="the detective",
    ),
    "child": WitnessProfile(
        name="Nia",
        type="girl",
        clue="a lost button",
        saw="a lost button shining under the stairs",
        memory_trigger="the button",
        reconciles_with="the detective",
    ),
}

CULPRITS = {
    "thief": "the thief",
    "messenger": "the hurried messenger",
    "cat": "the small cat",
}

OBJECTS = {
    "note": "a folded note",
    "key": "a tiny brass key",
    "pin": "a silver pin",
}

DET_NAMES = ["Detective June", "Detective Bram", "Detective Mina", "Detective Sol"]
TRAITS = ["patient", "careful", "sharp-eyed", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for loc in LOCATIONS:
        for wit in WITNESSES:
            for cul in CULPRITS:
                for obj in OBJECTS:
                    combos.append((loc, wit, cul, obj))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: the chosen witness/case combination is not reasonable.)"


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------

def introduce(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    world.say(
        f"{det.id} was a careful detective who liked quiet places and small clues."
    )
    world.say(
        f"One evening, {wit.id} came with a worried face and said there had been a missing thing."
    )


def setup_case(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    obj = world.get("object")
    world.say(
        f"{wit.id} pointed to {obj.phrase} and said it had been there before, but now it was gone."
    )
    det.memes["curiosity"] = det.memes.get("curiosity", 0.0) + 1
    wit.memes["fear"] = wit.memes.get("fear", 0.0) + 1


def flashback(world: World) -> None:
    if world.flashback_active:
        return
    world.flashback_active = True
    wit = world.get("witness")
    cul = world.get("culprit")
    obj = world.get("object")
    world.para()
    world.say(
        f"Then {wit.id} remembered something from earlier. In the flashback, {wit.id} had seen {cul.label} near {obj.phrase}."
    )
    world.say(
        f"{wit.id} had not understood it at the time, but the clue had been there all along."
    )
    wit.memes["memory"] = wit.memes.get("memory", 0.0) + 1
    world.facts["flashback"] = True


def investigate(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    cul = world.get("culprit")
    obj = world.get("object")
    world.para()
    world.say(
        f"{det.id} followed the clue from {wit.id} and looked where the light was thin."
    )
    world.say(
        f"At {world.location.label}, {det.id} found signs that matched {cul.label} and the missing {obj.phrase}."
    )
    det.meters["evidence"] = det.meters.get("evidence", 0.0) + 1
    world.facts["evidence_found"] = True


def bad_ending(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    cul = world.get("culprit")
    obj = world.get("object")
    world.para()
    world.say(
        f"For a moment, it looked like a bad ending."
    )
    world.say(
        f"{det.id} thought the trail had broken, and {wit.id} looked ready to cry because {obj.phrase} still seemed lost."
    )
    world.say(
        f"Even {cul.label} had slipped out of sight, leaving only worry behind."
    )
    world.facts["bad_ending"] = True


def reconcile(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    cul = world.get("culprit")
    obj = world.get("object")
    world.para()
    world.say(
        f"Then {wit.id} took a slow breath and walked back to {det.id}."
    )
    world.say(
        f"{wit.id} admitted the clue had been hard to trust at first, and {det.id} answered kindly instead of blaming {wit.id}."
    )
    world.say(
        f"Together they found {obj.phrase}, and the misunderstanding with {cul.label} finally made sense."
    )
    wit.memes["relief"] = wit.memes.get("relief", 0.0) + 1
    det.memes["trust"] = det.memes.get("trust", 0.0) + 1
    world.facts["reconciled"] = True
    world.facts["object_found"] = True


def ending(world: World) -> None:
    det = world.get("detective")
    wit = world.get("witness")
    obj = world.get("object")
    cul = world.get("culprit")
    world.para()
    world.say(
        f"In the end, {obj.phrase} was back where it belonged."
    )
    world.say(
        f"{det.id} and {wit.id} stood together in the quiet room, and the case was solved."
    )
    world.say(
        f"It was not a perfect night, but it ended with honesty, a calmer heart, and the mystery no longer hiding in the dark."
    )
    world.facts["ending"] = "resolved"


def tell_story(world: World) -> World:
    introduce(world)
    setup_case(world)
    flashback(world)
    investigate(world)
    bad_ending(world)
    reconcile(world)
    ending(world)
    return world


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
witness(W) :- witness_profile(W).
clue_for(W, C) :- witness_clue(W, C).
case_possible(L, W, U, O) :- location(L), witness(W), culprit(U), object(O).
flashback_needed(W) :- witness(W), witness_clue(W, _).
bad_ending(C) :- culprit(C).
reconciled(W) :- witness(W), detective(detective).
resolved_case(L, W, U, O) :- case_possible(L, W, U, O), flashback_needed(W), bad_ending(U), reconciled(W).
#show resolved_case/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for lid, loc in LOCATIONS.items():
        lines.append(asp.fact("location", lid))
        if loc.indoors:
            lines.append(asp.fact("indoors", lid))
        for t in sorted(loc.traits):
            lines.append(asp.fact("trait", lid, t))
    lines.append(asp.fact("detective", "detective"))
    for wid, w in WITNESSES.items():
        lines.append(asp.fact("witness_profile", wid))
        lines.append(asp.fact("witness_clue", wid, w.clue))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    return "\n".join(lines)


def asp_program(show: str = "#show resolved_case/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_resolved_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolved_case/4."))
    return sorted(set(asp.atoms(model, "resolved_case")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    clingo_like = set(asp_resolved_cases())
    if py == clingo_like:
        print(f"OK: clingo gate matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - clingo_like:
        print("  only in python:", sorted(py - clingo_like))
    if clingo_like - py:
        print("  only in ASP:", sorted(clingo_like - py))
    return 1


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective story world with witness, flashback, bad ending, and reconciliation.")
    ap.add_argument("--setting", choices=LOCATIONS)
    ap.add_argument("--detective", choices=["June", "Bram", "Mina", "Sol"])
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
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
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "witness", None):
        combos = [c for c in combos if c[1] == getattr(args, "witness", None)]
    if getattr(args, "culprit", None):
        combos = [c for c in combos if c[2] == getattr(args, "culprit", None)]
    if getattr(args, "object_", None):
        combos = [c for c in combos if c[3] == getattr(args, "object_", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, witness, culprit, obj = rng.choice(list(combos))
    return StoryParams(
        setting=setting,
        detective=getattr(args, "detective", None) or rng.choice(DET_NAMES),
        witness=witness,
        culprit=culprit,
        object=obj,
    )


def generate(params: StoryParams) -> StorySample:
    location = _safe_lookup(LOCATIONS, params.setting)
    world = World(location)
    det = world.add(Entity(id=params.detective, kind="character", type="detective", label=params.detective))
    wit_profile = _safe_lookup(WITNESSES, params.witness)
    wit = world.add(Entity(id=wit_profile.name, kind="character", type=wit_profile.type, label=wit_profile.name))
    cul = world.add(Entity(id=_safe_lookup(CULPRITS, params.culprit), kind="character", type="man", label=_safe_lookup(CULPRITS, params.culprit)))
    obj = world.add(Entity(id=params.object, kind="thing", type="thing", label=_safe_lookup(OBJECTS, params.object), phrase=_safe_lookup(OBJECTS, params.object)))
    world.facts.update(
        setting=params.setting,
        witness=params.witness,
        culprit=params.culprit,
        object=params.object,
        detective=params.detective,
    )
    tell_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts
    return [
        f"Write a short detective story for a young child about a witness named {p['witness']} and a missing thing.",
        f"Tell a gentle mystery with a flashback, a bad ending, and a reconciliation at {world.location.label}.",
        f"Write a simple detective tale where a witness helps solve a case and the ending turns from bad to better.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts
    wit = world.get("witness")
    det = world.get("detective")
    obj = world.get("object")
    cul = world.get("culprit")
    return [
        QAItem(
            question=f"Who was the witness in the story?",
            answer=f"The witness was {wit.id}, who noticed a clue and helped with the case.",
        ),
        QAItem(
            question=f"What clue did the witness remember in the flashback?",
            answer=f"{wit.id} remembered {WITNESSES[p['witness']].saw}, and that memory helped the detective look in the right place.",
        ),
        QAItem(
            question=f"Why did the story have a bad ending for a moment?",
            answer=f"It seemed like a bad ending because {obj.phrase} still looked lost and the trail to {cul.label} seemed to disappear.",
        ),
        QAItem(
            question=f"How did the detective and witness reconcile?",
            answer=f"{det.id} stayed kind, {wit.id} told the truth about the clue, and together they found {obj.phrase} again.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a witness?",
            answer="A witness is a person who sees something important and can help explain what happened.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a memory of something that happened earlier, shown in the middle of the story.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make things better between them.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when things seem like they might go wrong, even if the story later gets better.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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
    StoryParams(setting="dock", detective="June", witness="shopkeeper", culprit="thief", object="note"),
    StoryParams(setting="station", detective="Mina", witness="porter", culprit="messenger", object="key"),
    StoryParams(setting="library", detective="Bram", witness="child", culprit="cat", object="pin"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved_case/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show resolved_case/4."))
        print(f"{len(set(asp.atoms(model, 'resolved_case')))} resolved cases:")
        for t in sorted(set(asp.atoms(model, "resolved_case"))):
            print(" ", t)
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.detective} / {p.witness} / {p.culprit} / {p.object} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
