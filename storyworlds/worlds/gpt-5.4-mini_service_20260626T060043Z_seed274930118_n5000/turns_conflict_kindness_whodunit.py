#!/usr/bin/env python3
"""
Standalone storyworld: turns_conflict_kindness_whodunit

A small whodunit-style domain where a puzzling loss creates conflict,
kindness unlocks the next clue, and the ending explains who took what
and why the turn mattered.
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
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    found_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    helper: object | None = None
    suspect_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "aunt"}
        male = {"boy", "man", "father", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Place:
    id: str
    label: str
    kind: str
    clues: list[str] = field(default_factory=list)
    hidden_item: Optional[str] = None
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
class Suspect:
    id: str
    type: str
    label: str
    motive: str
    alibi: str
    kindness: str
    guilt: float = 0.0
    kindness_score: float = 0.0
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
    place: str
    culprit: str
    item: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
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


PLACES = {
    "library": Place(
        id="library",
        label="the library",
        kind="quiet",
        clues=["a torn paper bookmark", "a tiny ink smudge", "a note tucked by a shelf"],
        hidden_item="ledger",
    ),
    "bakery": Place(
        id="bakery",
        label="the bakery",
        kind="sweet",
        clues=["a flour trail", "a missing tray", "a sugar print on the counter"],
        hidden_item="recipe_card",
    ),
    "garden": Place(
        id="garden",
        label="the garden",
        kind="green",
        clues=["a bent stem", "a muddy footprint", "a ribbon on a bench"],
        hidden_item="gloves",
    ),
}

ITEMS = {
    "ledger": ("the blue ledger", "a blue ledger", "ledger"),
    "recipe_card": ("the recipe card", "a recipe card", "recipe card"),
    "gloves": ("the striped gloves", "a pair of striped gloves", "gloves"),
}

SUSPECTS = {
    "janitor": Suspect("janitor", "man", "the janitor", "he was seen near the door", "he had keys", "he shared a spare pencil"),
    "baker": Suspect("baker", "woman", "the baker", "she needed the missing item", "she was stirring dough", "she offered warm rolls"),
    "gardener": Suspect("gardener", "woman", "the gardener", "she wanted to finish first", "she was watering seedlings", "she fixed a broken pot"),
    "clerk": Suspect("clerk", "man", "the clerk", "he was worried about a mistake", "he was counting stamps", "he returned a dropped receipt"),
}

DETECTIVE_NAMES = ["Milo", "Ivy", "Nora", "Theo", "Lena", "Owen"]
HELPER_NAMES = ["Pip", "Mira", "Juno", "Ari", "Bea", "Max"]


class World:
    def __init__(self, place: Place, culprit: Suspect, item_id: str) -> None:
        self.place = place
        self.culprit = culprit
        self.item_id = item_id
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.turns: list[str] = []
        self.clues_seen: list[str] = []

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

    def clue_found(self, clue: str) -> bool:
        return clue in self.clues_seen

    def note_turn(self, label: str) -> None:
        self.turns.append(label)


def _turn_conflict(world: World) -> list[str]:
    out = []
    if "conflict" in world.fired:
        return out
    world.fired.add("conflict")
    detective = world.get("detective")
    helper = world.get("helper")
    detective.memes["worry"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"At {world.place.label}, something was wrong: the {_safe_lookup(ITEMS, world.item_id)[2]} was gone."
    )
    world.say(
        f"{detective.id} frowned and asked everyone to stay calm, but the room filled with whispers."
    )
    out.append("conflict")
    return out


def _turn_kindness(world: World) -> list[str]:
    out = []
    if "kindness" in world.fired:
        return out
    helper = world.get("helper")
    detective = world.get("detective")
    if helper.memes.get("kindness", 0.0) < THRESHOLD:
        return out
    world.fired.add("kindness")
    clue = world.place.clues[0]
    world.clues_seen.append(clue)
    helper.memes["trust"] += 1
    detective.memes["hope"] += 1
    world.say(
        f"{helper.id} noticed a little clue and spoke softly instead of blaming anyone."
    )
    world.say(
        f"That kindness made the room feel safer, and {detective.id} picked up {clue}."
    )
    out.append("kindness")
    return out


def _turn_reveal(world: World) -> list[str]:
    out = []
    if "reveal" in world.fired:
        return out
    if not world.clue_found(world.place.clues[0]):
        return out
    world.fired.add("reveal")
    detective = world.get("detective")
    culprit = world.get(world.culprit.id)
    item_label = _safe_lookup(ITEMS, world.item_id)[0]
    culprit.memes["nervous"] += 1
    world.say(
        f"{detective.id} followed the clue trail and saw that the {item_label} had not been stolen at all."
    )
    world.say(
        f"It had been moved by {culprit.label}, who was trying to hide a surprise and kept dropping clues in a hurry."
    )
    out.append("reveal")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for step in (_turn_conflict, _turn_kindness, _turn_reveal):
            got = step(world)
            if got:
                changed = True
                out.extend(got)
    if narrate:
        for s in out:
            world.lines.append(s)
    return out


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    culprit = _safe_lookup(SUSPECTS, params.culprit)
    world = World(place, culprit, params.item)

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        meters={"care": 1.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        meters={"care": 1.0},
        memes={"kindness": 1.0},
    ))
    suspect_ent = world.add(Entity(
        id=culprit.id,
        kind="character",
        type=culprit.type,
        label=culprit.label,
        meters={},
        memes={"nervous": 0.0},
    ))
    item_label, item_phrase, _ = _safe_lookup(ITEMS, params.item)
    world.add(Entity(
        id=params.item,
        kind="thing",
        type="object",
        label=item_label,
        phrase=item_phrase,
        owner="town",
        hidden=True,
    ))

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=suspect_ent,
        item=params.item,
        place=place,
        clue=place.clues[0],
    )

    world.say(
        f"{detective.id} was a small detective who loved turns, because every odd detail might matter."
    )
    world.say(
        f"{helper.id} stayed close, and {helper.id} was the kind of friend who could calm a room."
    )
    world.para()
    world.say(
        f"One morning, at {place.label}, the {item_label} was missing."
    )
    world.say(
        f"Everyone looked at one another, and the silence turned sharp."
    )
    world.para()
    world.say(
        f"{detective.id} asked gentle questions while {helper.id} looked for clues without accusing anyone."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"In the end, {detective.id} smiled, because the clue trail led to a misunderstanding, not a mean theft."
    )
    world.say(
        f"{culprit.label} admitted moving the {item_label} for a surprise, and thanked {helper.id} for being kind."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a whodunit for young children set at {place.label} about a missing object and a surprising answer.',
        f"Tell a story where {detective.id} investigates the loss of a {world.item_id.replace('_', ' ')} and {helper.id} helps with kindness.",
        f"Write a gentle mystery with conflict, kindness, and a final turn that explains who moved the item.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    culprit = _safe_fact(world, f, "culprit")
    place = _safe_fact(world, f, "place")
    item_label = ITEMS[f["item"]][0]
    return [
        QAItem(
            question=f"What was missing at {place.label}?",
            answer=f"The missing thing was {item_label}. That was the puzzle {detective.id} had to solve.",
        ),
        QAItem(
            question=f"Who helped {detective.id} by being kind?",
            answer=f"{helper.id} helped by being kind and quiet, which made it easier to notice a clue.",
        ),
        QAItem(
            question=f"Who had moved the {item_label} in the end?",
            answer=f"It was {culprit.label}. They had moved it for a surprise, not to cause trouble.",
        ),
        QAItem(
            question=f"Why did the mystery turn out to be less serious than it seemed?",
            answer=(
                f"The first moment felt like conflict because something was missing, "
                f"but the ending turn showed it was a misunderstanding. "
                f"{culprit.label} had moved the item, and the kind helper helped everyone calm down."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
        QAItem(
            question="Why can kindness help during a conflict?",
            answer="Kindness can help because it makes people feel safe enough to tell the truth and listen.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully at facts and clues to solve a puzzle or mystery.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.hidden:
            parts.append("hidden=True")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"turns={world.turns}")
    lines.append(f"clues_seen={world.clues_seen}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            lines.append(asp.fact("clue", pid, clue))
        if place.hidden_item:
            lines.append(asp.fact("hides", pid, place.hidden_item))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        lines.append(asp.fact("motive", sid, suspect.motive))
        lines.append(asp.fact("kindness", sid, suspect.kindness))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    return "\n".join(lines)


ASP_RULES = r"""
{ took(S,I) : suspect(S) } = 1 :- item(I).
conflict(I) :- item(I), not found(I).
kindness_help(S) :- kindness(S, _).
reveal(I) :- hides(P,I), clue(P,_), kindness_help(_).
found(I) :- reveal(I).
culprit(S) :- took(S,I).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show found/1. #show culprit/1."))
    return 0 if model is not None else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with conflict and kindness.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--culprit", choices=sorted(SUSPECTS))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("--type", dest="detective_type", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--helper-type", choices=["girl", "boy", "woman", "man"])
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACES))
    culprit = getattr(args, "culprit", None) or rng.choice(sorted(SUSPECTS))
    item = getattr(args, "item", None) or _safe_lookup(PLACES, place).hidden_item or rng.choice(sorted(ITEMS))
    detective_type = getattr(args, "detective_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(DETECTIVE_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in HELPER_NAMES if n != name])
    if place not in PLACES or culprit not in SUSPECTS or item not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, culprit=culprit, item=item,
                        detective_name=name, detective_type=detective_type,
                        helper_name=helper_name, helper_type=helper_type)


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


CURATED = [
    StoryParams(place="library", culprit="janitor", item="ledger", detective_name="Milo", detective_type="boy", helper_name="Ivy", helper_type="girl"),
    StoryParams(place="bakery", culprit="baker", item="recipe_card", detective_name="Nora", detective_type="girl", helper_name="Pip", helper_type="boy"),
    StoryParams(place="garden", culprit="gardener", item="gloves", detective_name="Theo", detective_type="boy", helper_name="Lena", helper_type="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show found/1. #show culprit/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        if len(samples) > 1:
            print(f"### variant {idx + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
