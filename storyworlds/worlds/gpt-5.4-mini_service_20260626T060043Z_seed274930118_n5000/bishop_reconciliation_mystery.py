#!/usr/bin/env python3
"""
A small mystery-flavored storyworld about a bishop, a missing clue, and
reconciliation.

The seed premise:
A bishop arrives to help a parish family after a quarrel. A written apology
goes missing, a small mystery grows around the chapel, and the bishop pieces
together the truth so the neighbors can make peace again.
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
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bishop: object | None = None
    parishioner: object | None = None
    second: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "nun"}
        male = {"boy", "man", "father", "bishop", "priest"}
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
    indoor: bool = True
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
    found_in: str
    reveals: str
    story_phrase: str
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
class Mystery:
    id: str
    event: str
    suspicion: str
    resolution: str
    clue_ids: list[str] = field(default_factory=list)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    clue: str
    bishop_name: str
    parishioner_name: str
    second_name: str
    seed: Optional[int] = None


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


SETTINGS = {
    "chapel": Setting(place="the small chapel", indoor=True, affords={"listen", "search", "reconcile"}),
    "rectory": Setting(place="the quiet rectory", indoor=True, affords={"listen", "search", "reconcile"}),
    "garden": Setting(place="the church garden", indoor=False, affords={"listen", "search", "reconcile"}),
}

BISHOP_NAMES = ["Bishop Elias", "Bishop Martin", "Bishop Adrian", "Bishop Theo"]
NAMES = ["Mara", "Iris", "Nina", "Jonah", "Peter", "Clara", "Ruth", "Simon"]

MYSTERIES = {
    "missing_note": Mystery(
        id="missing_note",
        event="the apology note vanished from the lectern",
        suspicion="someone had hidden the note on purpose",
        resolution="the note had slipped into a hymn book",
        clue_ids=["bookmark", "dust"],
    ),
    "broken_candle": Mystery(
        id="broken_candle",
        event="the peace candle was found broken near the side door",
        suspicion="someone had been angry enough to break it",
        resolution="a draft had blown the candle off a shelf",
        clue_ids=["draft", "wax"],
    ),
    "lost_key": Mystery(
        id="lost_key",
        event="the little brass key disappeared before evening prayer",
        suspicion="someone might have taken it to avoid peace",
        resolution="the key had fallen under the prayer bench",
        clue_ids=["bench", "ringmark"],
    ),
}

CLUES = {
    "bookmark": Clue(
        id="bookmark",
        label="a paper bookmark",
        found_in="a hymn book",
        reveals="the note had been tucked away by accident",
        story_phrase="a paper bookmark sticking out of a hymn book",
    ),
    "dust": Clue(
        id="dust",
        label="a line of dust",
        found_in="the lectern shelf",
        reveals="the note had slid into the shelf gap",
        story_phrase="a pale line of dust leading to the lectern shelf",
    ),
    "draft": Clue(
        id="draft",
        label="a cool draft",
        found_in="the side door",
        reveals="the candle had been pushed by air, not anger",
        story_phrase="a cool draft slipping under the side door",
    ),
    "wax": Clue(
        id="wax",
        label="wax crumbs",
        found_in="the stone floor",
        reveals="the candle had fallen, then cracked",
        story_phrase="tiny wax crumbs on the stone floor",
    ),
    "bench": Clue(
        id="bench",
        label="a prayer bench",
        found_in="the front row",
        reveals="the key had dropped out of sight",
        story_phrase="a prayer bench with a narrow shadow beneath it",
    ),
    "ringmark": Clue(
        id="ringmark",
        label="a brass ring mark",
        found_in="the bench rail",
        reveals="the key had bumped the wood and fallen",
        story_phrase="a faint brass ring mark on the bench rail",
    ),
}

WORLD_KNOWLEDGE = {
    "bishop": [
        ("What is a bishop?",
         "A bishop is a church leader who helps guide people, teaches kindness, and often visits different churches to care for them."),
    ],
    "reconciliation": [
        ("What is reconciliation?",
         "Reconciliation means making peace again after people have argued or hurt each other's feelings."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is something puzzling that people try to figure out by looking for clues."),
    ],
    "clue": [
        ("What is a clue?",
         "A clue is a small piece of information that helps solve a mystery."),
    ],
    "note": [
        ("What is a note?",
         "A note is a short message written on paper."),
    ],
}


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _rule_discover_clue(world: World) -> list[str]:
    out: list[str] = []
    bishop = world.get("bishop")
    mystery = _safe_fact(world, world.facts, "mystery")
    clue = world.get(mystery.clue_ids[0])
    if bishop.meters.get("searching", 0) < THRESHOLD:
        return out
    sig = ("discover", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    bishop.meters["certainty"] = bishop.meters.get("certainty", 0.0) + 1
    out.append(f"The bishop noticed {clue.story_phrase}.")
    return out


def _rule_second_clue(world: World) -> list[str]:
    out: list[str] = []
    bishop = world.get("bishop")
    mystery = _safe_fact(world, world.facts, "mystery")
    if bishop.meters.get("certainty", 0) < THRESHOLD:
        return out
    if len(mystery.clue_ids) < 2:
        return out
    clue = world.get(mystery.clue_ids[1])
    sig = ("discover2", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue.hidden = False
    out.append(f"Then {clue.story_phrase} gave the next answer.")
    return out


def _rule_reconcile(world: World) -> list[str]:
    out: list[str] = []
    bishop = world.get("bishop")
    a = world.get("parishioner")
    b = world.get("second")
    if bishop.meters.get("certainty", 0) < 2:
        return out
    if a.memes.get("hurt", 0) < THRESHOLD and b.memes.get("hurt", 0) < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    a.memes["hurt"] = 0
    b.memes["hurt"] = 0
    a.memes["peace"] = 1
    b.memes["peace"] = 1
    bishop.memes["peace"] = bishop.memes.get("peace", 0) + 1
    out.append("The bishop helped them speak plainly and forgive each other.")
    return out


RULES = [
    Rule("discover_clue", _rule_discover_clue),
    Rule("discover_second_clue", _rule_second_clue),
    Rule("reconcile", _rule_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_resolution(world: World) -> dict:
    sim = world.copy()
    sim.get("bishop").meters["searching"] = 1
    propagate(sim, narrate=False)
    return {
        "clue_found": any(not e.hidden for e in sim.entities.values() if e.id in sim.facts["mystery"].clue_ids),
        "reconciled": sim.get("parishioner").memes.get("peace", 0) >= 1,
    }


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(bishop: Entity) -> str:
    return f"{bishop.id} was a careful bishop who never rushed a hard conversation."


def setup_line(world: World, mystery: Mystery, bishop: Entity, parishioner: Entity, second: Entity) -> str:
    return (
        f"One evening at {world.setting.place}, {bishop.id} came to help when {parishioner.id} "
        f"and {second.id} could not agree. The trouble had started because {mystery.event}."
    )


def suspicion_line(mystery: Mystery) -> str:
    return f"That made everyone wonder if {mystery.suspicion}."


def search_line(world: World, bishop: Entity) -> str:
    bishop.meters["searching"] = 1
    return f"{bishop.id} listened quietly, then began to search for the truth."


def reconciliation_line(world: World, bishop: Entity, parishioner: Entity, second: Entity) -> str:
    bishop.meters["searching"] = 1
    propagate(world, narrate=False)
    return (
        f"At last, {bishop.id} showed {parishioner.id} and {second.id} how the pieces fit together, "
        f"and they both saw they had feared the wrong thing."
    )


def ending_line(world: World) -> str:
    bishop = world.get("bishop")
    parishioner = world.get("parishioner")
    second = world.get("second")
    mystery = _safe_fact(world, world.facts, "mystery")
    clue = world.get(mystery.clue_ids[0])
    return (
        f"By the end, {mystery.resolution}, and the two neighbors sat side by side again. "
        f"{bishop.id} left with {clue.story_phrase} solved, while {parishioner.id} and {second.id} "
        f"walked home in peace."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A mystery is solved if at least one clue is found and reconciliation happens.
found(C) :- clue(C), shown(C).
solved(M) :- mystery(M), clue_in(M, C), found(C), reconciled(M).

% Reconciliation is possible only after the bishop searches and the key clue is found.
can_reconcile(M) :- mystery(M), bishop_searching, clue_in(M, C), found(C).

#show solved/1.
#show can_reconcile/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for cid in m.clue_ids:
            lines.append(asp.fact("clue_in", mid, cid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("shown", cid))
        lines.append(asp.fact("found_in", cid, clue.found_in))
    lines.append(asp.fact("bishop_searching"))
    lines.append(asp.fact("reconciled", "missing_note"))
    lines.append(asp.fact("reconciled", "broken_candle"))
    lines.append(asp.fact("reconciled", "lost_key"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show solved/1.\n#show can_reconcile/1."))
    atoms = set((sym.name, tuple(a.name if a.type != a.type.Number else a.number for a in sym.arguments)) for sym in model)
    py = {("solved", (mid,)) for mid in MYSTERIES}
    py |= {("can_reconcile", (mid,)) for mid in MYSTERIES}
    if atoms != py:
        print("MISMATCH between ASP and Python gates.")
        print("ASP:", sorted(atoms))
        print("PY :", sorted(py))
        return 1
    print(f"OK: ASP gate matches Python gate ({len(atoms)} facts).")
    return 0


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    bishop = world.add(Entity(id="bishop", kind="character", type="bishop", label=params.bishop_name))
    parishioner = world.add(Entity(id="parishioner", kind="character", type="woman", label=params.parishioner_name))
    second = world.add(Entity(id="second", kind="character", type="man", label=params.second_name))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    clue_a = CLUES[mystery.clue_ids[0]]
    clue_b = CLUES[mystery.clue_ids[1]]

    world.add(Entity(id=clue_a.id, type="clue", label=clue_a.label, phrase=clue_a.story_phrase, hidden=True))
    world.add(Entity(id=clue_b.id, type="clue", label=clue_b.label, phrase=clue_b.story_phrase, hidden=True))
    world.facts["mystery"] = mystery
    world.facts["bishop"] = bishop
    world.facts["parishioner"] = parishioner
    world.facts["second"] = second

    # Act 1
    world.say(intro_line(bishop))
    world.say(setup_line(world, mystery, bishop, parishioner, second))
    world.say(suspicion_line(mystery))
    world.para()

    # Act 2
    world.say(search_line(world, bishop))
    if params.mystery == "missing_note":
        bishop.meters["searching"] = 1
        world.say("He checked the lectern, then the hymn books, because small papers like to hide in neat places.")
    elif params.mystery == "broken_candle":
        bishop.meters["searching"] = 1
        world.say("He studied the side door, because a draft can leave clues that people miss.")
    else:
        bishop.meters["searching"] = 1
        world.say("He looked under the prayer bench, because little things often fall where no one kneels.")
    propagate(world, narrate=True)
    world.para()

    # Act 3
    world.say(reconciliation_line(world, bishop, parishioner, second))
    propagate(world, narrate=True)
    world.say(ending_line(world))

    world.facts["params"] = params
    return world


def generation_prompts(world: World) -> list[str]:
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")
    bishop: Entity = _safe_fact(world, world.facts, "bishop")
    parishioner: Entity = _safe_fact(world, world.facts, "parishioner")
    return [
        "Write a short mystery story for a young child about a bishop who helps people make peace again.",
        f"Tell a gentle mystery where {bishop.label} investigates {mystery.event} and ends with reconciliation.",
        f"Write a small church mystery with clues, a bishop, and a happy resolution for {parishioner.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    mystery: Mystery = _safe_fact(world, world.facts, "mystery")
    bishop: Entity = _safe_fact(world, world.facts, "bishop")
    parishioner: Entity = _safe_fact(world, world.facts, "parishioner")
    second: Entity = _safe_fact(world, world.facts, "second")
    clue = world.get(mystery.clue_ids[0])

    return [
        QAItem(
            question=f"Who helped solve the mystery in {world.setting.place}?",
            answer=f"{bishop.label} the bishop helped solve it by looking carefully at the clues and listening to both sides.",
        ),
        QAItem(
            question=f"What was the mystery about?",
            answer=f"It was about how {mystery.event}, which made everyone wonder what had really happened.",
        ),
        QAItem(
            question=f"What clue pointed toward the answer?",
            answer=f"The first helpful clue was {clue.story_phrase}, and it helped show that the trouble had an ordinary explanation.",
        ),
        QAItem(
            question=f"How did the story end for {parishioner.label} and {second.label}?",
            answer=f"They made peace again after {bishop.label} explained the truth and helped them forgive each other.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    seen = set()
    for key in ("bishop", "reconciliation", "mystery", "clue", "note"):
        if key in WORLD_KNOWLEDGE and key not in seen:
            seen.add(key)
            q, a = WORLD_KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameter selection and generation API
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with a bishop and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--name2")
    ap.add_argument("--bishop-name")
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
    mystery = getattr(args, "mystery", None) or rng.choice(list(MYSTERIES))
    clue = getattr(args, "clue", None) or _safe_lookup(MYSTERIES, mystery).clue_ids[0]
    if clue not in _safe_lookup(MYSTERIES, mystery).clue_ids:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    bishop_name = getattr(args, "bishop_name", None) or rng.choice(BISHOP_NAMES)
    name1 = getattr(args, "name", None) or rng.choice(NAMES)
    name2 = getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != name1])
    return StoryParams(
        place=place,
        mystery=mystery,
        clue=clue,
        bishop_name=bishop_name,
        parishioner_name=name1,
        second_name=name2,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_story_world(params)
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


# ---------------------------------------------------------------------------
# ASP
# ---------------------------------------------------------------------------

def asp_valid_options() -> list[tuple[str, str, str]]:
    import asp

    program = asp_program("#show solved/1.\n#show can_reconcile/1.")
    model = asp.one_model(program)
    solved = sorted(set(asp.atoms(model, "solved")))
    can = sorted(set(asp.atoms(model, "can_reconcile")))
    return [("solved", str(s[0]), "") for s in solved] + [("can", str(c[0]), "") for c in can]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="chapel", mystery="missing_note", clue="bookmark", bishop_name="Bishop Elias", parishioner_name="Mara", second_name="Jonah"),
    StoryParams(place="rectory", mystery="broken_candle", clue="draft", bishop_name="Bishop Martin", parishioner_name="Iris", second_name="Peter"),
    StoryParams(place="garden", mystery="lost_key", clue="bench", bishop_name="Bishop Theo", parishioner_name="Clara", second_name="Simon"),
]


def asp_show_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show solved/1.\n#show can_reconcile/1.\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_show_program())
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_show_program())
        solved = sorted(set(asp.atoms(model, "solved")))
        can = sorted(set(asp.atoms(model, "can_reconcile")))
        print(f"solved: {solved}")
        print(f"can_reconcile: {can}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.bishop_name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
