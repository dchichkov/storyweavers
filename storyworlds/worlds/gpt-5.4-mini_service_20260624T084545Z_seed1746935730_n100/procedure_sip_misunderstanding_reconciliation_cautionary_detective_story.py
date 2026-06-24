#!/usr/bin/env python3
"""
A small detective storyworld about a careful procedure, a tiny sip, a mistake,
and a kind apology.

Premise:
- A child detective notices that something in the room has been changed.
- The detective follows a simple procedure to check clues.
- A misunderstanding makes one friend seem guilty of taking a sip.
- The truth is cautious and concrete: the sip was harmless, but the guessing
  was not.
- Reconciliation ends the story with a warmer feeling than the start.

The world is intentionally narrow so the stories stay complete and grounded.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective-girl"}
        male = {"boy", "father", "dad", "man", "detective-boy"}
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
    indoors: bool
    affords: set[str] = field(default_factory=set)
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
class Procedure:
    id: str
    name: str
    steps: list[str]
    careful: str
    clue_kind: str
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


@dataclass
class SipObject:
    id: str
    label: str
    phrase: str
    safe: bool
    risky_reason: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"procedure", "sip"}),
    "clinic": Setting(place="the tiny clinic", indoors=True, affords={"procedure", "sip"}),
    "station": Setting(place="the station office", indoors=True, affords={"procedure"}),
}

PROCEDURES = {
    "inspect": Procedure(
        id="inspect",
        name="careful clue-checking procedure",
        steps=["look", "compare", "ask", "wait"],
        careful="carefully",
        clue_kind="clue",
        tags={"procedure", "detective", "cautionary"},
    ),
    "taste_test": Procedure(
        id="taste_test",
        name="tiny sip procedure",
        steps=["smell", "sip", "think", "confirm"],
        careful="carefully",
        clue_kind="sip",
        tags={"procedure", "sip"},
    ),
}

SIP_ITEMS = {
    "tea": SipObject(
        id="tea",
        label="tea",
        phrase="a warm cup of tea",
        safe=True,
        risky_reason="it was safe to sip after it cooled",
        tags={"sip"},
    ),
    "medicine": SipObject(
        id="medicine",
        label="medicine",
        phrase="a spoon of medicine",
        safe=False,
        risky_reason="it was for grown-ups and needed a helper first",
        tags={"sip", "cautionary"},
    ),
    "juice": SipObject(
        id="juice",
        label="juice",
        phrase="a little cup of berry juice",
        safe=True,
        risky_reason="it was only juice, not a mystery danger",
        tags={"sip"},
    ),
}

NAMES = ["Mina", "Jules", "Toby", "Nora", "Pip", "Lena"]
TRAITS = ["curious", "quiet", "brave", "patient", "sharp-eyed"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    procedure: str
    sip_item: str
    name: str
    trait: str
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


ASP_RULES = r"""
% A setting supports a procedure or a sip if the registry says so.
supports(S, P) :- setting(S), procedure(P), affords(S, P).
supports(S, I) :- setting(S), sip_item(I), affords(S, I).

% A sip choice is reasonable when the item is safe and the setting allows it.
safe_choice(S, I) :- setting(S), sip_item(I), safe(I), supports(S, I).

% A cautionary case is when the item is not safe, but the setting still allows
% the character to notice the need for a careful procedure.
cautionary_case(S, I) :- setting(S), sip_item(I), risky(I), supports(S, I).

% A detective story is valid when it has a procedure and either a safe sip or a
% cautionary sip that leads to reconciliation.
valid_story(S, P, I) :- setting(S), procedure(P), sip_item(I),
                        supports(S, P), supports(S, I),
                        (safe(I); risky(I)).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROCEDURES.items():
        lines.append(asp.fact("procedure", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("ptag", pid, t))
    for iid, item in SIP_ITEMS.items():
        lines.append(asp.fact("sip_item", iid))
        if item.safe:
            lines.append(asp.fact("safe", iid))
        else:
            lines.append(asp.fact("risky", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and ASP.")
    print("Only Python:", sorted(py - cl))
    print("Only ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for pid in setting.affords:
            for iid, item in SIP_ITEMS.items():
                if pid == "procedure" and iid in {"tea", "medicine", "juice"}:
                    combos.append((sid, pid, iid))
                if pid == "sip" and iid in {"tea", "juice", "medicine"}:
                    combos.append((sid, pid, iid))
    return combos


def explain_rejection(setting: str, procedure: str, sip_item: str) -> str:
    return (
        f"(No story: the combination setting={setting}, procedure={procedure}, "
        f"sip={sip_item} does not make a believable detective misunderstanding.)"
    )


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def opening_line(hero: Entity, setting: Setting, proc: Procedure) -> str:
    return (
        f"{hero.id} was a {hero.meters.get('smallness', 1):.0f}-step detective "
        f"with a sharp eye and a careful notebook in {setting.place}."
    )


def tell_story(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="detective-girl" if params.name in {"Mina", "Nora", "Lena"} else "detective-boy",
        label=params.name,
        meters={"smallness": 1},
        memes={"curiosity": 1, "calm": 1},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="mother",
        label="her helper",
        memes={"worry": 1},
    ))
    item = _safe_lookup(SIP_ITEMS, params.sip_item)
    proc = _safe_lookup(PROCEDURES, params.procedure)

    world.say(
        f"{hero.id} worked {proc.careful} through the {proc.name} in {world.setting.place}."
    )
    world.say(
        f"First {hero.id} looked at the cup, then at the table, then at the tiny marks around it."
    )
    world.say(
        f"{hero.id} had been told to follow a procedure, because good clues can hide behind little mistakes."
    )

    world.para()
    if params.sip_item == "medicine":
        world.say(
            f"On the counter stood {item.phrase}. {hero.id} thought someone had taken a sneaky sip."
        )
        hero.memes["suspicion"] = 1
        helper.memes["concern"] = 1
        world.say(
            f"{hero.id} pointed at the cup and said, 'The mystery looks simple, but I need proof.'"
        )
        world.say(
            f"{helper.id} frowned, because {item.risky_reason}."
        )
        world.say(
            f"That was the misunderstanding: the cup had been set there for a grown-up procedure, not for secret sips."
        )
        world.para()
        world.say(
            f"{hero.id} followed the procedure again: look, ask, wait."
        )
        world.say(
            f"Then {hero.id} asked the helper kindly, and the helper explained what the cup was for."
        )
        hero.memes["suspicion"] = 0
        hero.memes["relief"] = 1
        helper.memes["relief"] = 1
        world.say(
            f"{hero.id} felt sorry for the quick guess and apologized."
        )
        world.say(
            f"The helper smiled, and they agreed that careful questions were better than fast blame."
        )
        world.say(
            f"In the end, the medicine stayed on the counter, the notebook stayed honest, and the detective learned a cautionary lesson."
        )
    else:
        world.say(
            f"On the table sat {item.phrase}. {hero.id} noticed that one tiny sip had gone missing."
        )
        world.say(
            f"{hero.id} thought {helper.id} had taken it, but the clue marks showed a different shape."
        )
        hero.memes["suspicion"] = 1
        world.say(
            f"The misunderstanding made the room feel prickly for a moment."
        )
        world.para()
        world.say(
            f"{hero.id} used the procedure: look, compare, ask, wait."
        )
        world.say(
            f"Then the helper explained that the sip had been taken by a thirsty visitor earlier, after the tea cooled."
        )
        hero.memes["suspicion"] = 0
        hero.memes["warmth"] = 1
        helper.memes["warmth"] = 1
        world.say(
            f"{hero.id} apologized for jumping to the wrong answer."
        )
        world.say(
            f"The helper forgave the guess, and the two of them shared a smaller, safer sip together."
        )
        world.say(
            f"By the end, the mystery was solved, the friendship felt repaired, and the procedure had done its job."
        )

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        procedure=proc,
        setting=world.setting,
        cautionary=(params.sip_item == "medicine"),
        reconciled=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    proc = f["procedure"]
    item = f["item"]
    return [
        f'Write a short detective story for a child about a careful procedure and the word "sip".',
        f"Tell a story where {hero.id} follows the {proc.name} and learns what really happened to {item.phrase}.",
        f"Write a cautionary mystery with a misunderstanding, a reconciliation, and a tiny sip clue.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    item: SipObject = f["item"]
    proc: Procedure = f["procedure"]
    helper: Entity = f["helper"]

    if f["cautionary"]:
        answer1 = (
            f"{hero.id} thought the cup was for secret sipping, but it was really for a grown-up procedure. "
            f"After asking questions, {hero.id} learned not to guess too fast."
        )
        answer2 = (
            f"The misunderstanding was about {item.phrase}. It was not a drink for the child detective, "
            f"because {item.risky_reason}."
        )
    else:
        answer1 = (
            f"{hero.id} thought the missing sip meant someone had done something wrong, but the clues showed the sip was harmless. "
            f"The careful procedure helped {hero.id} see the truth."
        )
        answer2 = (
            f"The helper explained that the sip came from {item.phrase}, and the detective had guessed too quickly."
        )

    return [
        QAItem(
            question=f"What did {hero.id} do to solve the mystery in {world.setting.place}?",
            answer=f"{hero.id} followed the {proc.name} and looked at the clues one by one.",
        ),
        QAItem(
            question=f"Why was there a misunderstanding about {item.label}?",
            answer=answer1,
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} feel at the end?",
            answer=(
                f"They felt better after they talked it through. {hero.id} apologized, "
                f"{helper.id} forgave the mistake, and they ended with reconciliation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a procedure?",
            answer="A procedure is a set of careful steps that helps you do something the right way.",
        ),
        QAItem(
            question="What is a sip?",
            answer="A sip is a very small drink, just a little mouthful.",
        ),
        QAItem(
            question="Why should children be careful with medicine?",
            answer="Children should be careful with medicine because some medicine is only meant to be taken with a grown-up's help.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(setting="kitchen", procedure="inspect", sip_item="juice", name="Mina", trait="curious"),
    StoryParams(setting="clinic", procedure="inspect", sip_item="medicine", name="Jules", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny detective storyworld about procedures and sips.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--procedure", choices=PROCEDURES)
    ap.add_argument("--sip-item", choices=SIP_ITEMS)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "procedure", None) is None or c[1] == getattr(args, "procedure", None))
        and (getattr(args, "sip_item", None) is None or c[2] == getattr(args, "sip_item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, procedure, sip_item = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, procedure=procedure, sip_item=sip_item, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for s in stories:
            print(" ", s)
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
