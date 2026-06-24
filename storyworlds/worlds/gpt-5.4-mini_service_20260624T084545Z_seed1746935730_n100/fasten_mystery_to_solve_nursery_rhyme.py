#!/usr/bin/env python3
"""
storyworlds/worlds/fasten_mystery_to_solve_nursery_rhyme.py
===========================================================

A small nursery-rhyme story world about fastening clues together to solve a mystery.

Seed tale:
---
Little Nell found a ribbon in the meadow. She loved to tie and fasten things,
and she loved to sing little rhymes while she worked. One morning, her toy
lamb was missing its tiny bell. Nell noticed a trail of shiny buttons, a loose
bow, and a snagged kite string. She wondered which clue belonged to the bell.

Nell asked her granny, who said, "Look for the piece that fastens the others
together." Nell followed the clues, tied the ribbon around the kite string, and
noticed the bell had been hooked onto the bow. She fastened the bow to the lamb,
and the tiny bell rang at last.

Causal state updates:
---
    noticing clues -> seeker.memes["curiosity"] += 1
    clue collected -> clue.meters["held"] += 1
    clue fastened to clue -> world.links += 1 ; seeker.memes["confidence"] += 1
    solved mystery -> seeker.memes["joy"] += 1 ; seeker.memes["confidence"] += 1
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
    fastened_to: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        self.meters.setdefault("held", 0.0)
        self.meters.setdefault("visible", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("confidence", 0.0)
        self.memes.setdefault("joy", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "granny"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the meadow"
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
    kind: str
    hint: str
    can_fasten_to: set[str] = field(default_factory=set)
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
class Mystery:
    missing: str
    reveal_with: str
    solution_label: str
    solved_by: str
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
class StoryParams:
    place: str
    hero: str
    hero_type: str
    helper: str
    clue_a: str
    clue_b: str
    missing: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def valid_pair(a: Clue, b: Clue) -> bool:
    return b.kind in a.can_fasten_to or a.kind in b.can_fasten_to


def reasonableness_gate(mystery: Mystery, a: Clue, b: Clue) -> bool:
    return mystery.reveal_with in {a.id, b.id} and valid_pair(a, b)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme storyworld about fastening clues to solve a mystery."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--hero", choices=sorted(HERO_NAMES))
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["granny", "mother", "father", "friend"])
    ap.add_argument("--clue-a", choices=sorted(CLUES))
    ap.add_argument("--clue-b", choices=sorted(CLUES))
    ap.add_argument("--missing", choices=sorted(MYSTERIES))
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


def select_from(registry: dict, key: Optional[str], rng: random.Random):
    return registry[key] if key else registry[rng.choice(sorted(registry))]


SETTINGS = {
    "meadow": Setting("the meadow"),
    "garden": Setting("the garden"),
    "playroom": Setting("the playroom"),
}

HERO_NAMES = ["Nell", "Mina", "Pip", "Ruby", "Lottie", "Tess"]

CLUES = {
    "ribbon": Clue("ribbon", "a ribbon", "a little ribbon", "cloth", "ties"),
    "button": Clue("button", "a button", "a shiny button", "round", "loops", {"thread"}),
    "string": Clue("string", "a kite string", "a snagged kite string", "thin", "ties", {"ribbon"}),
    "bow": Clue("bow", "a bow", "a loose bow", "soft", "ties", {"ribbon"}),
    "bell": Clue("bell", "a tiny bell", "a tiny bell", "metal", "rings", {"bow", "ribbon"}),
    "thread": Clue("thread", "a thread", "a stray thread", "thin", "ties", {"button"}),
}

MYSTERIES = {
    "missing-bell": Mystery("missing-bell", "bell", "tiny bell", "fastened"),
    "lost-bow": Mystery("lost-bow", "bow", "loose bow", "tied"),
}

HELPER_LINES = {
    "granny": "her granny smiled and said",
    "mother": "her mother smiled and said",
    "father": "her father smiled and said",
    "friend": "her friend smiled and said",
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for a in CLUES.values():
            for b in CLUES.values():
                if a.id == b.id:
                    continue
                for m in MYSTERIES.values():
                    if reasonableness_gate(m, a, b):
                        combos.append((place, a.id, b.id))
    return sorted(set(combos))


ASP_RULES = r"""
clue(A) :- clue_def(A).
fastenable(A,B) :- fastens_to(A,B).
pair_ok(A,B) :- fastenable(A,B); fastenable(B,A).

valid_combo(P,A,B) :- place(P), clue(A), clue(B), A != B, pair_ok(A,B), mystery(M), reveals(M,A); reveals(M,B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue_def", cid))
        for tgt in sorted(c.can_fasten_to):
            lines.append(asp.fact("fastens_to", cid, tgt))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("reveals", mid, m.reveal_with))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_story(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    a: Clue = _safe_fact(world, f, "clue_a")
    b: Clue = _safe_fact(world, f, "clue_b")
    mystery: Mystery = _safe_fact(world, f, "mystery")

    world.say(
        f"Little {hero.id} went a-walking to {world.setting.place}, "
        f"where the grass was soft and the day was bright."
    )
    world.say(
        f"{hero.id} liked to notice little things, and {hero.pronoun('subject')} "
        f"liked to fasten clues together like pieces of a song."
    )
    world.say(
        f"Then {hero.id} found {a.phrase} and {b.phrase}; both looked as if they belonged to a story."
    )
    hero.memes["curiosity"] += 1
    a.meters["visible"] += 1
    b.meters["visible"] += 1

    world.para()
    world.say(
        f"But something was missing: the {mystery.solution_label} was nowhere in sight."
    )
    world.say(
        f"'{hero.id}, dear,' {_safe_lookup(HELPER_LINES, helper.type)}: "
        f"'look for the clue that can fasten the others nice and tight.'"
    )
    hero.memes["confidence"] += 0.5

    world.para()
    world.say(
        f"So {hero.id} picked up {a.label} and {b.label}, one in each hand, "
        f"and gave them a gentle try."
    )
    if valid_pair(a, b):
        a.carried_by = hero.id
        b.carried_by = hero.id
        a.meters["held"] += 1
        b.meters["held"] += 1
        world.say(
            f"They fitted together snug as a bug, and {hero.id} could see "
            f"they were made to fasten."
        )
        world.say(
            f"Then {hero.id} noticed the {mystery.solution_label} hooked close by, "
            f"waiting for the right link."
        )
        if mystery.reveal_with in {a.id, b.id}:
            world.say(
                f"With a careful twist, {hero.id} fastened the {mystery.solution_label} "
                f"to the pair, and the little mystery began to sing."
            )
            hero.memes["confidence"] += 1
            hero.memes["joy"] += 1
            world.facts["solved"] = True
        else:
            world.say(
                f"But the pair was not the true key, and the mystery still stayed quiet."
            )
            world.facts["solved"] = False
    else:
        world.say(
            f"They would not fasten at all, so {hero.id} tried again, patient as rain."
        )
        world.facts["solved"] = False

    if world.facts["solved"]:
        world.para()
        world.say(
            f"At last the tiny bell rang bright and clear, and the meadow felt merry."
        )
        world.say(
            f"{hero.id} laughed, {helper.id} smiled, and the found things stayed fastened "
            f"as neat as a nursery rhyme."
        )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper))
    clue_a = world.add(copy.deepcopy(_safe_lookup(CLUES, params.clue_a)))
    clue_b = world.add(copy.deepcopy(_safe_lookup(CLUES, params.clue_b)))
    mystery = _safe_lookup(MYSTERIES, params.missing)
    world.facts.update(hero=hero, helper=helper, clue_a=clue_a, clue_b=clue_b, mystery=mystery)
    build_story(world)
    world.facts["params"] = params
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clue_a: Clue = _safe_fact(world, f, "clue_a")
    clue_b: Clue = _safe_fact(world, f, "clue_b")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a gentle nursery-rhyme story about a child named {hero.id} who finds {clue_a.label} and {clue_b.label}.',
        f"Tell a rhyme-like mystery where {hero.id} must fasten clues together to find the {mystery.solution_label}.",
        f'Write a short child-friendly story that includes the word "fasten" and ends with the mystery solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue_a: Clue = _safe_fact(world, f, "clue_a")
    clue_b: Clue = _safe_fact(world, f, "clue_b")
    mystery: Mystery = _safe_fact(world, f, "mystery")
    solved = _safe_fact(world, f, "solved")
    qa = [
        QAItem(
            question=f"What did {hero.id} like to do with clues?",
            answer=f"{hero.id} liked to fasten clues together and look for the little pattern hiding in them.",
        ),
        QAItem(
            question=f"What two clues did {hero.id} find?",
            answer=f"{hero.id} found {clue_a.phrase} and {clue_b.phrase}.",
        ),
        QAItem(
            question=f"Who gave {hero.id} a hint about the mystery?",
            answer=f"{helper.id} gave the hint and said to look for the clue that could fasten the others nice and tight.",
        ),
    ]
    if solved:
        qa.append(
            QAItem(
                question=f"What solved the mystery in the end?",
                answer=f"The mystery was solved when {hero.id} fastened the {mystery.solution_label} to the right clue pair.",
            )
        )
        qa.append(
            QAItem(
                question=f"What sound did the solution make?",
                answer="The tiny bell rang bright and clear.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to fasten something?",
            answer="To fasten something means to join or tie it so it stays together.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information or a thing that helps solve a mystery.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a puzzle or secret that needs to be figured out.",
        ),
    ]


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
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.fastened_to:
            bits.append(f"fastened_to={e.fastened_to}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for place in SETTINGS:
        for a in CLUES:
            for b in CLUES:
                if a == b:
                    continue
                for missing in MYSTERIES:
                    if reasonableness_gate(_safe_lookup(MYSTERIES, missing), _safe_lookup(CLUES, a), _safe_lookup(CLUES, b)):
                        combos.append((place, a, b, missing))
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "clue_a", None):
        combos = [c for c in combos if c[1] == getattr(args, "clue_a", None)]
    if getattr(args, "clue_b", None):
        combos = [c for c in combos if c[2] == getattr(args, "clue_b", None)]
    if getattr(args, "missing", None):
        combos = [c for c in combos if c[3] == getattr(args, "missing", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ca, cb, missing = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["granny", "mother", "father", "friend"])
    return StoryParams(place=place, hero=hero, hero_type=hero_type, helper=helper, clue_a=ca, clue_b=cb, missing=missing)


def generate(params: StoryParams) -> StorySample:
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


CURATED = [
    StoryParams(place="meadow", hero="Nell", hero_type="girl", helper="granny", clue_a="ribbon", clue_b="bell", missing="missing-bell"),
    StoryParams(place="garden", hero="Pip", hero_type="boy", helper="mother", clue_a="string", clue_b="ribbon", missing="missing-bell"),
    StoryParams(place="playroom", hero="Ruby", hero_type="girl", helper="father", clue_a="button", clue_b="thread", missing="lost-bow"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
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
