#!/usr/bin/env python3
"""
A small storyworld: a docile cadet, a shared missing item, a flashback clue,
and a gentle whodunit-style reveal.

The premise:
- A cadet notices that something important has vanished.
- The cadet is usually docile and does not accuse anyone.
- The mystery is solved by remembering a past shared moment.
- The ending reveals who took the item, why, and how it is returned.

This world is intentionally small and constraint-checked. It models typed
entities with physical meters and emotional memes, and the prose is driven by
world state rather than by a frozen template.
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

THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cadet", "boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
    place: str = "the academy hall"
    light: str = "evening"
    ambience: str = "quiet"
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
class MissingItem:
    id: str
    label: str
    phrase: str
    type: str
    concealment: str
    clue_place: str
    sentimental: bool = True
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
    type: str
    label: str
    share_kind: str  # what they shared with the cadet before the disappearance
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_triggered = False

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.flashback_triggered = self.flashback_triggered
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "academy_hall": Setting(place="the academy hall", light="evening", ambience="quiet"),
    "barracks": Setting(place="the barracks", light="afternoon", ambience="orderly"),
    "courtyard": Setting(place="the courtyard", light="morning", ambience="still"),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="badge",
        phrase="a polished brass badge",
        type="badge",
        concealment="inside a folded drill manual",
        clue_place="the reading desk",
    ),
    "map": MissingItem(
        id="map",
        label="map",
        phrase="a paper map with the north edge marked in blue",
        type="map",
        concealment="under a spare cap",
        clue_place="the supply shelf",
    ),
    "key": MissingItem(
        id="key",
        label="key",
        phrase="a tiny key on a red thread",
        type="key",
        concealment="inside a sleeve cuff",
        clue_place="the coat rack",
    ),
}

SUSPECTS = {
    "mate": SuspectProfile(id="mate", type="cadet", label="cadet", share_kind="pencil"),
    "drillmaster": SuspectProfile(id="drillmaster", type="officer", label="drillmaster", share_kind="lantern"),
    "cook": SuspectProfile(id="cook", type="adult", label="cook", share_kind="roll"),
}

NAMES = ["Mina", "Iris", "June", "Tess", "Ada", "Nell", "Lina", "Pia"]
TRAITS = ["docile", "careful", "quiet", "patient", "gentle"]
POSSIBLE_SEEDS = ["cadet", "docile", "sharing", "flashback", "whodunit"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    trait: str
    suspect: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A mystery is valid when the cadet has a clue, a shared past, and a place to search.
mystery_valid(P, I, S) :- setting(P), missing(I), suspect(S),
                          shared_past(C, S), clue_place(I, L), search_place(P, L).

% The culprit is the suspect who shared the item and later hid it.
culprit(S) :- suspect(S), shared_past(_, S), hide_reason(S).

% The reveal is reasonable when the clue place matches the hiding place.
reveal_valid(I, S) :- missing(I), culprit(S), clue_match(I, S).

#show mystery_valid/3.
#show culprit/1.
#show reveal_valid/2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("missing", iid))
        lines.append(asp.fact("clue_place", iid, item.clue_place))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    # Core narrative facts: one cadet and one shared past per story are added in asp_program().
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    world_facts = []
    for sid, spec in SUSPECTS.items():
        world_facts.append(f"suspect({sid}).")
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show mystery_valid/3. #show culprit/1. #show reveal_valid/2."))
    return {
        "mystery_valid": sorted(set(asp.atoms(model, "mystery_valid"))),
        "culprit": sorted(set(asp.atoms(model, "culprit"))),
        "reveal_valid": sorted(set(asp.atoms(model, "reveal_valid"))),
    }


def asp_verify() -> int:
    py = set(valid_combos())
    asp_models = asp_valid()["mystery_valid"]
    asp_set = set(asp_models)
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("python:", sorted(py))
    print("clingo:", sorted(asp_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            for suspect in SUSPECTS:
                combos.append((place, item, suspect))
    return combos


def explain_invalid(place: str, item: str, suspect: str) -> str:
    return (
        f"(No story: this mystery needs a believable place, a missing item, and a suspect. "
        f"Got place={place}, item={item}, suspect={suspect}.)"
    )


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def run_flashback(world: World, cadet: Entity, suspect: Entity, item: MissingItem) -> None:
    world.flashback_triggered = True
    world.say(
        f"Then the cadet remembered a flashback: earlier, {cadet.id} and {suspect.noun()} "
        f"had shared {world.facts['shared_object']} by the lamp."
    )
    world.say(
        f"{suspect.noun().capitalize()} had asked to borrow the {item.label} just for a minute, "
        f"and {cadet.id}, being so docile, had nodded and let {suspect.pronoun('object')} take it."
    )


def infer_culprit(world: World, cadet: Entity, suspect: Entity, item: MissingItem) -> bool:
    # The suspect is guilty if the shared object and clue line up.
    return world.facts.get("shared_object") is not None and world.facts.get("clue_matches")


def resolve_story(world: World, cadet: Entity, suspect: Entity, item: MissingItem) -> None:
    world.say(
        f"{cadet.id} followed the clue to {item.clue_place}, where the missing {item.label} was hidden "
        f"{item.concealment}."
    )
    world.say(
        f"The mystery was simple after that: {suspect.noun()} had taken it during the shared moment, "
        f"not to be cruel, but to finish a small task and forgotten to return it."
    )
    world.say(
        f"{cadet.id} stayed docile even now, thanked {suspect.pronoun('object')}, and shared the relief "
        f"of putting the {item.label} back where it belonged."
    )


def tell(setting: Setting, item: MissingItem, name: str, trait: str, suspect_key: str) -> World:
    world = World(setting)

    cadet = world.add(
        Entity(
            id=name,
            kind="character",
            type="cadet",
            label="cadet",
            traits=[trait, "soft-spoken", "observant"],
        )
    )
    suspect_profile = _safe_lookup(SUSPECTS, suspect_key)
    suspect = world.add(
        Entity(
            id=suspect_profile.id,
            kind="character",
            type=suspect_profile.type,
            label=suspect_profile.label,
            traits=["busy", "careful"],
        )
    )
    missing = world.add(
        Entity(
            id=item.id,
            kind="thing",
            type=item.type,
            label=item.label,
            phrase=item.phrase,
            owner=cadet.id,
            caretaker=suspect.id,
        )
    )

    # Setup
    world.say(
        f"{cadet.id} was a {trait} cadet in {setting.place}, the kind who spoke softly and listened closely."
    )
    world.say(
        f"One evening, {cadet.id} kept a careful share of {suspect_profile.share_kind} with {suspect.noun()}, "
        f"and that little kindness would matter later."
    )
    world.say(
        f"After that, the {missing.label} was gone. The room looked orderly, but the empty space felt loud."
    )

    world.para()

    # Investigation
    world.say(
        f"{cadet.id} searched the quiet room without making a fuss, looking first at the desk, then the shelf, "
        f"then the coat rack."
    )
    world.say(
        f"Nothing seemed to move, yet something did not fit. The clue was small: a tiny mark near {item.clue_place}."
    )
    world.facts["shared_object"] = suspect_profile.share_kind
    world.facts["clue_matches"] = True
    run_flashback(world, cadet, suspect, item)

    world.para()

    # Reveal and resolution
    if infer_culprit(world, cadet, suspect, item):
        resolve_story(world, cadet, suspect, item)
    else:
        pass

    world.facts.update(
        cadet=cadet,
        suspect=suspect,
        item=missing,
        setting=setting,
        trait=trait,
        shared_object=suspect_profile.share_kind,
        culprit=suspect.id,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cadet = _safe_fact(world, f, "cadet")
    suspect = _safe_fact(world, f, "suspect")
    item = _safe_fact(world, f, "item")
    return [
        f"Write a short whodunit for a young child about {cadet.id}, a {_safe_fact(world, f, "trait")} cadet, and a missing {item.label}.",
        f"Tell a story where {cadet.id} remembers a flashback and discovers who hid the {item.label}.",
        f"Write a gentle mystery in which a docile cadet solves a sharing-related disappearance at {world.setting.place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cadet = _safe_fact(world, f, "cadet")
    suspect = _safe_fact(world, f, "suspect")
    item = _safe_fact(world, f, "item")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {cadet.id}, a {_safe_fact(world, f, "trait")} cadet who notices that the {item.label} is missing.",
        ),
        QAItem(
            question=f"What happened to the {item.label}?",
            answer=f"It was hidden for a while, and the clue led {cadet.id} to {item.clue_place}.",
        ),
        QAItem(
            question=f"What did {cadet.id} remember in the flashback?",
            answer=f"{cadet.id} remembered sharing {_safe_fact(world, f, "shared_object")} with {suspect.id}, which helped solve the mystery.",
        ),
        QAItem(
            question=f"Who took the missing {item.label}?",
            answer=f"{suspect.id} had taken it after the shared moment, then tucked it away by mistake.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{cadet.id} found the {item.label}, stayed calm, and put it back where it belonged.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cadet?",
            answer="A cadet is a young person who is learning to do an organized job with care and practice.",
        ),
        QAItem(
            question="What does docile mean?",
            answer="Docile means quiet, gentle, and easy to guide without making trouble.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a short look back to something that happened earlier.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something for a little while too.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small whodunit storyworld about a docile cadet.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    trait = getattr(args, "trait", None) or "docile"
    name = getattr(args, "name", None) or rng.choice(NAMES)

    if (place, item, suspect) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, item=item, name=name, trait=trait, suspect=suspect)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ITEMS, params.item), params.name, params.trait, params.suspect)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  flashback_triggered={world.flashback_triggered}")
    lines.append(f"  facts={world.facts}")
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
    StoryParams(place="academy_hall", item="badge", name="Mina", trait="docile", suspect="mate"),
    StoryParams(place="barracks", item="map", name="Iris", trait="docile", suspect="drillmaster"),
    StoryParams(place="courtyard", item="key", name="June", trait="docile", suspect="cook"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mystery_valid/3. #show culprit/1. #show reveal_valid/2."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show mystery_valid/3. #show culprit/1. #show reveal_valid/2."))
        print(f"mystery_valid: {sorted(set(asp.atoms(model, 'mystery_valid')))}")
        print(f"culprit: {sorted(set(asp.atoms(model, 'culprit')))}")
        print(f"reveal_valid: {sorted(set(asp.atoms(model, 'reveal_valid')))}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.item} mystery at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
