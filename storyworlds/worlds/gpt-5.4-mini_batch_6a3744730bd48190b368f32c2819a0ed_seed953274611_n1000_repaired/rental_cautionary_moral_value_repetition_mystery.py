#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rental_cautionary_moral_value_repetition_mystery.py
===================================================================================

A tiny mystery storyworld about a rental, a repeated clue, a cautionary choice,
and a small moral turn.

Premise
-------
A child and a grown-up rent a curious object for one night. The object keeps
making the same odd sign, and the child is tempted to ignore it. The story turns
when the repeated clue reveals what is wrong, and the family chooses the careful
moral answer instead of the risky one.

This world is designed to be:
- small and classical
- state-driven, not template-swapped
- cautionary, with a moral value ending
- lightly repetitive in a mystery style

It supports:
- default run
- -n, --all, --seed, --trace, --qa, --json
- --asp, --verify, --show-asp

The ASP twin mirrors the Python reasonableness gate and ending selection.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    dim: str
    noise: str
    clue_spot: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class RentalItem:
    id: str
    label: str
    label_phrase: str
    type: str
    clue: str
    risky_effect: str
    moral: str
    reveals: str
    clue_count: int = 0
    suspicious: bool = False
    has_problem: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Signal:
    id: str
    label: str
    kind: str
    repeats: int
    message: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


@dataclass
class Fix:
    id: str
    label: str
    power: int
    safe: bool
    text: str
    moral_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


class World:
    def __init__(self) -> None:
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("rental_item")
    sig = world.get("signal")
    if item.meters["heard"] >= THRESHOLD and item.clue_count < sig.repeats:
        key = ("repeat", item.id, item.clue_count)
        if key in world.fired:
            return []
        world.fired.add(key)
        item.clue_count += 1
        item.meters["clue"] += 1
        item.meters["odd"] += 0.5
        out.append(sig.message)
    return out


def _r_problem(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("rental_item")
    if item.meters["odd"] >= THRESHOLD and not item.has_problem:
        key = ("problem", item.id)
        if key in world.fired:
            return []
        world.fired.add(key)
        item.has_problem = True
        item.suspicious = True
        world.get("child").memes["worry"] += 1
        out.append("__problem__")
    return out


CAUSAL_RULES = [Rule("repeat", "mystery", _r_repeat), Rule("problem", "mystery", _r_problem)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, item_id: str) -> dict:
    sim = world.copy()
    sim.get(item_id).meters["heard"] += 1
    propagate(sim, narrate=False)
    item = sim.get(item_id)
    return {"odd": item.meters["odd"], "problem": item.has_problem, "clues": item.clue_count}


def reasonableness_ok(item: RentalItem, signal: Signal) -> bool:
    return signal.repeats >= 2 and item.clue == signal.kind


def is_safe(fix: Fix, item: RentalItem) -> bool:
    return fix.safe and fix.power >= 1 and item.has_problem


def setup(world: World, child: Entity, parent: Entity, place: Place, item: RentalItem, signal: Signal) -> None:
    child.memes["curiosity"] += 1
    parent.memes["calm"] += 1
    world.say(
        f"On a quiet evening, {child.id} and {parent.label_word} went to {place.label} to return a rental."
    )
    world.say(
        f"The place was dim and full of little echoes. {place.noise} came and went around the counter."
    )
    world.say(
        f"{item.label_phrase} was on the table, and something about it felt strange."
    )


def mystery_turn(world: World, child: Entity, item: RentalItem, signal: Signal, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} heard the same odd clue again and again: {signal.message}"
    )
    world.say(
        f"That clue pointed toward {place.clue_spot}, and {child.id} looked there once, then again."
    )
    world.say(
        f"The repeated hint made the rental seem less ordinary and more like a mystery."
    )
    item.meters["heard"] += 1
    propagate(world, narrate=True)


def caution(world: World, child: Entity, parent: Entity, item: RentalItem) -> None:
    parent.memes["care"] += 1
    world.say(
        f'{parent.id} put a gentle hand on {child.id}\'s shoulder. "If something keeps repeating, we should not ignore it," {parent.pronoun()} said.'
    )
    world.say(
        f'"A mystery can be solved carefully. We do the safe thing first."'
    )


def risky_choice(world: World, child: Entity, item: RentalItem) -> None:
    child.memes["impulse"] += 1
    world.say(
        f'{child.id} wanted to poke at the rental and call it nothing, just to see what would happen.'
    )
    world.say(
        f"But {child.id} remembered the repeated clue and stopped short."
    )


def fix_problem(world: World, parent: Entity, fix: Fix, item: RentalItem, child: Entity) -> None:
    world.say(
        f"{parent.label_word.capitalize()} chose the careful answer: {fix.text}."
    )
    world.say(
        f"That was enough to settle the problem and keep everyone safe."
    )
    child.memes["relief"] += 1
    parent.memes["pride"] += 1


def moral_end(world: World, parent: Entity, child: Entity, fix: Fix, item: RentalItem) -> None:
    world.say(
        f"{parent.label_word.capitalize()} smiled and gave the lesson plainly: {item.moral}."
    )
    world.say(
        f"{fix.moral_text} {child.id} nodded, remembering the clue and the caution both."
    )
    world.say(
        f"In the end, the rental was returned safely, and the little mystery was solved the honest way."
    )


def tell(place: Place, item: RentalItem, signal: Signal, fix: Fix,
         child_name: str = "Mia", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    rental = world.add(Entity(id="rental_item", type=item.type, label=item.label))
    world.add(Entity(id="signal", type="signal", label=signal.label))
    child.memes["curiosity"] = 1.0
    parent.memes["care"] = 1.0

    setup(world, child, parent, place, item, signal)
    world.para()
    mystery_turn(world, child, item, signal, place)
    caution(world, child, parent, item)
    risky_choice(world, child, item)
    world.para()
    if fix.safe and reasonableness_ok(item, signal):
        item.has_problem = True
        if is_safe(fix, item):
            fix_problem(world, parent, fix, item, child)
            moral_end(world, parent, child, fix, item)
        else:
            raise StoryError("Chosen fix is not safe enough for this mystery.")
    else:
        raise StoryError("This storyworld needs a repeated clue and a matching rental mystery.")

    world.facts.update(
        child=child,
        parent=parent,
        place=place,
        item=item,
        signal=signal,
        fix=fix,
        solved=True,
        repeated=item.clue_count,
        odd=item.meters["odd"],
    )
    return world


PLACES = {
    "market": Place(id="market", label="the night market", dim="glow", noise="soft bells", clue_spot="the lamp post", tags={"mystery"}),
    "dock": Place(id="dock", label="the little dock", dim="mist", noise="water tapping wood", clue_spot="the crate corner", tags={"mystery"}),
    "hall": Place(id="hall", label="the old hall", dim="shadows", noise="footsteps and whispers", clue_spot="the curtain edge", tags={"mystery"}),
}

ITEMS = {
    "lantern": RentalItem(
        id="lantern", label="lantern", label_phrase="a rented lantern", type="thing",
        clue="flicker", risky_effect="got hot", moral="not every strange thing is meant to be ignored",
        reveals="a loose battery", clue_count=0, suspicious=False, has_problem=False,
        tags={"rental", "mystery"},
    ),
    "bicycle": RentalItem(
        id="bicycle", label="bicycle", label_phrase="a borrowed bicycle", type="thing",
        clue="rattle", risky_effect="wobbled badly", moral="care is wiser than guessing",
        reveals="a loose wheel", clue_count=0, suspicious=False, has_problem=False,
        tags={"rental", "mystery"},
    ),
    "radio": RentalItem(
        id="radio", label="radio", label_phrase="a rented radio", type="thing",
        clue="click", risky_effect="kept cutting out", moral="when a clue repeats, listen to it",
        reveals="a sticky button", clue_count=0, suspicious=False, has_problem=False,
        tags={"rental", "mystery"},
    ),
}

SIGNALS = {
    "flicker": Signal(id="flicker", label="flicker", kind="flicker", repeats=2, message="flicker, flicker", tags={"repeat"}),
    "rattle": Signal(id="rattle", label="rattle", kind="rattle", repeats=3, message="rattle, rattle", tags={"repeat"}),
    "click": Signal(id="click", label="click", kind="click", repeats=2, message="click, click", tags={"repeat"}),
}

FIXES = {
    "tighten": Fix(id="tighten", label="tighten the loose part", power=1, safe=True,
                   text="tighten the loose part and check it carefully",
                   moral_text="A careful look can solve what a quick guess cannot.",
                   tags={"safe", "moral"}),
    "return": Fix(id="return", label="return it to the desk", power=1, safe=True,
                  text="call the desk and return it for a proper check",
                  moral_text="The honest choice is often the safest one.",
                  tags={"safe", "moral"}),
}

@dataclass
class StoryParams:
    place: str
    item: str
    signal: str
    fix: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in ITEMS.items():
            for sid, sig in SIGNALS.items():
                if item.clue == sig.kind and sig.repeats >= 2:
                    for fid, fix in FIXES.items():
                        combos.append((pid, iid, sid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rental mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--signal", choices=SIGNALS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.item and args.signal:
        if ITEMS[args.item].clue != SIGNALS[args.signal].kind:
            raise StoryError("This rental clue does not match the repeated signal.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.signal is None or c[2] == args.signal)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, signal = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mia", "Nora", "Theo", "Eli", "Ava", "Noah"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, item=item, signal=signal, fix=fix,
                       child_name=name, child_gender=gender, parent_type=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mystery story for a small child that includes the word "rental" and a repeated clue.',
        f"Tell a cautious story where {f['child'].id} notices the same clue over and over at {f['place'].label}.",
        f"Write a short moral mystery where the safe choice wins after a rental item acts strangely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, place, item, signal, fix = f["child"], f["parent"], f["place"], f["item"], f["signal"], f["fix"]
    return [
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"The same clue kept coming back again and again, so {child.id} and {parent.label_word} had to pay close attention. The repetition pointed them toward the problem instead of letting it stay hidden."
        ),
        QAItem(
            question="Why did the parent tell the child not to ignore it?",
            answer=f"Because repeated clues are worth checking, and guessing can make a small problem worse. The parent chose caution so they could solve the rental safely."
        ),
        QAItem(
            question="How did they fix the problem?",
            answer=f"They chose to {fix.text}. That careful choice matched the clue and kept the rental from causing any harm."
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{item.moral.capitalize()}. The story shows that listening carefully and telling the truth about a problem is the brave thing to do."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rental?",
            answer="A rental is something you use for a little while and then give back."
        ),
        QAItem(
            question="Why do repeated clues matter in a mystery?",
            answer="Repeated clues matter because they can point to something important. If the same sign keeps showing up, it may be trying to tell you where to look."
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful before you act. It helps people avoid making a small problem worse."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("clue", iid, item.clue))
    for sid, sig in SIGNALS.items():
        lines.append(asp.fact("signal", sid))
        lines.append(asp.fact("kind", sid, sig.kind))
        lines.append(asp.fact("repeats", sid, sig.repeats))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,I,S) :- place(P), item(I), signal(S), clue(I,C), kind(S,C), repeats(S,R), R >= 2.
safe_fix(F) :- fix(F).
outcome(solved) :- valid(_,_,_), safe_fix(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gates.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("item", ITEMS), ("signal", SIGNALS), ("fix", FIXES)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    place = PLACES[params.place]
    item = ITEMS[params.item]
    signal = SIGNALS[params.signal]
    fix = FIXES[params.fix]
    if item.clue != signal.kind:
        raise StoryError("The chosen rental item and repeated signal do not match.")
    if not reasonableness_ok(item, signal):
        raise StoryError("This mystery needs a repeated clue and a matching rental.")
    world = tell(place, item, signal, fix, params.child_name, params.child_gender, params.parent_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="market", item="lantern", signal="flicker", fix="tighten", child_name="Mia", child_gender="girl", parent_type="mother"),
    StoryParams(place="dock", item="bicycle", signal="rattle", fix="return", child_name="Theo", child_gender="boy", parent_type="father"),
    StoryParams(place="hall", item="radio", signal="click", fix="tighten", child_name="Ava", child_gender="girl", parent_type="mother"),
]


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
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(show="#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
