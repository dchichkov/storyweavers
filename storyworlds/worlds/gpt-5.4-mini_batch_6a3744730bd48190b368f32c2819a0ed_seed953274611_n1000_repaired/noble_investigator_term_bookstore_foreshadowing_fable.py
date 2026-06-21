#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/noble_investigator_term_bookstore_foreshadowing_fable.py
=========================================================================================

A small standalone storyworld for a fable-like bookstore tale: a noble helper,
an investigator, and a mysterious term slip lead to a foreshadowed search among
books, labels, and whispers. The model is deliberately tiny: typed entities with
physical meters and emotional memes, a simple causal engine, a reasonableness
gate, and a matching ASP twin.

The seed words are woven into the domain:
- noble
- investigator
- term
- bookstore
Style: fable
Setting: bookstore
Feature: foreshadowing
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
CALM_MIN = 2.0


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
        female = {"girl", "mother", "mom", "woman", "ewe", "hen"}
        male = {"boy", "father", "dad", "man", "ram", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class StoryParams:
    helper: str
    helper_type: str
    investigator: str
    investigator_type: str
    noble: str
    noble_type: str
    term_kind: str
    clue_kind: str
    resolution: str
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


@dataclass
class BookstoreItem:
    id: str
    label: str
    kind: str
    hidden: bool = False
    delicate: bool = False
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
class Clue:
    id: str
    hint: str
    foreshadow: str
    concern: str
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
class Resolution:
    id: str
    sense: int
    effect: int
    text: str
    fail: str
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
        self.shelves: dict[str, str] = {}

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
        clone.shelves = dict(self.shelves)
        return clone


@dataclass
class Rule:
    name: str
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


def _r_unsettle(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["missing"] >= THRESHOLD and ("unsettle", e.id) not in world.fired:
            world.fired.add(("unsettle", e.id))
            for ent in list(world.entities.values()):
                if ent.kind == "character":
                    ent.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("clue_seen") and ("clue",) not in world.fired:
        world.fired.add(("clue",))
        helper = world.get("helper")
        helper.memes["hope"] += 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("unsettle", _r_unsettle), Rule("clue", _r_clue)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def good_resolutions() -> list[Resolution]:
    return [r for r in RESOLUTIONS.values() if r.sense >= CALM_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for helper in HELPERS:
        for clue in CLUES:
            for term in TERMS:
                if clue_at_work(clue, term):
                    combos.append((helper, clue, term))
    return combos


def clue_at_work(clue: Clue, term: BookstoreItem) -> bool:
    return "bookstore" in term.tags and "term" in term.tags and "book" in clue.tags


def _quote(name: str) -> str:
    return f'"{name}"'


def tell(helper: BookstoreItem, clue: Clue, term: BookstoreItem, resolution: Resolution,
         noble: str = "Nora", investigator: str = "Iris",
         noble_type: str = "girl", investigator_type: str = "owl") -> World:
    world = World()
    n = world.add(Entity(id=noble, kind="character", type=noble_type, role="noble",
                         traits=["kind", "patient"]))
    i = world.add(Entity(id=investigator, kind="character", type=investigator_type,
                         role="investigator", traits=["careful", "curious"]))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper.kind,
                                  role="helper", label=helper.label))
    term_ent = world.add(Entity(id="term", kind="thing", type="term", label=term.label))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="clue", label=clue.hint))

    n.memes["nobility"] = 1
    i.memes["attention"] = 1
    world.shelves["first"] = helper.id
    world.shelves["second"] = term.id

    world.say(
        f"In a little bookstore where the windows shone like lantern glass, "
        f"{noble} was known as the noble one, and {investigator} was the "
        f"investigator who noticed tiny things."
    )
    world.say(
        f"Every morning, {investigator} watched the shelves and said, "
        f'"Some stories hide their answers in plain sight." '
        f"Near the front desk, {clue.foreshadow}."
    )

    world.para()
    world.say(
        f"One afternoon, {noble} found a missing {term_kind_word(term)} slip "
        f"stuck inside a book with a torn ribbon. The clerk frowned, because a "
        f"missing term made the shelves feel unsteady."
    )
    clue_ent.meters["missing"] += 0.5
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)

    world.say(
        f"{investigator} leaned close and read the warning in the clue: "
        f"{clue.hint}."
    )
    helper_ent.memes["worry"] += 1

    world.para()
    world.say(
        f'"If the {term.label_word} stays lost," {investigator} said, '
        f'"the right book may wander to the wrong shelf by closing time."'
    )
    world.say(
        f"{noble} nodded, gentle but steady. " 
        f'"Then let us search with bright eyes and soft paws," {noble} said.'
    )

    if resolution.sense < CALM_MIN:
        raise StoryError(f"Refusing weak resolution {resolution.id!r}.")
    world.facts["resolution"] = resolution.id

    world.para()
    term_ent.meters["missing"] += 1
    helper_ent.meters["missing"] += 1
    world.facts["clue_seen"] = True
    propagate(world, narrate=False)

    if resolution.effect >= 2:
        world.say(
            f"They followed the foreshadowed hint to the reading nook, where "
            f"the missing {term.label_word} waited under a chair leg. {noble} "
            f"slid it free, and {investigator} placed it back where it belonged."
        )
    else:
        world.say(
            f"They searched the mystery corner, then the checkout table, and at "
            f"last {investigator} found the missing {term.label_word} tucked in a "
            f"cup beside the alphabet books."
        )

    world.para()
    term_ent.meters["missing"] = 0.0
    helper_ent.meters["missing"] = 0.0
    helper_ent.memes["calm"] += 1
    i.memes["pride"] += 1
    n.memes["joy"] += 1

    world.say(
        f"{resolution.text.format(term=term.label)} "
        f"The clerk smiled, the shelves grew tidy again, and the bookstore "
        f"felt as peaceful as a bedtime tale."
    )
    world.say(
        f"That evening, {investigator} pinned the clue into a notebook, and "
        f"{noble} watched the lamplight rest on the rescued {term.label_word}."
    )

    world.facts.update(
        noble=n, investigator=i, helper=helper_ent, term_ent=term_ent, clue_ent=clue_ent,
        helper_cfg=helper, clue_cfg=clue, term_cfg=term, resolution_cfg=resolution,
        outcome="resolved",
    )
    return world


def term_kind_word(term: BookstoreItem) -> str:
    return term.kind


HELPERS = {
    "rabbit": BookstoreItem(id="rabbit", label="noble rabbit clerk", kind="rabbit",
                            tags={"bookstore", "noble"}),
    "mouse": BookstoreItem(id="mouse", label="noble mouse helper", kind="mouse",
                           tags={"bookstore", "noble"}),
    "bird": BookstoreItem(id="bird", label="noble bird page-tender", kind="bird",
                          tags={"bookstore", "noble"}),
}

TERMS = {
    "term_card": BookstoreItem(id="term_card", label="term card", kind="term",
                               hidden=True, delicate=True,
                               tags={"bookstore", "term", "book"}),
    "term_label": BookstoreItem(id="term_label", label="term label", kind="term",
                                hidden=True, delicate=True,
                                tags={"bookstore", "term", "book"}),
    "term_note": BookstoreItem(id="term_note", label="term note", kind="term",
                               hidden=True, delicate=True,
                               tags={"bookstore", "term", "book"}),
}

CLUES = {
    "dusty_book": Clue(id="dusty_book", hint="a dusty book had a ribbon hanging loose",
                       foreshadow="a dusty book on the front table had one ribbon hanging loose",
                       concern="the missing slip had drifted out from the shelves",
                       tags={"book", "bookstore"}),
    "bell": Clue(id="bell", hint="the little bell gave a soft shake from the back room",
                 foreshadow="the little bell on the door gave one soft shake from the back room",
                 concern="someone had been moving books too quickly",
                 tags={"book", "bookstore"}),
    "bookmark": Clue(id="bookmark", hint="a bookmark peeked out like a tail from a tall book",
                     foreshadow="a red bookmark peeked out like a tail from a tall book",
                     concern="something important was hiding inside a story",
                     tags={"book", "bookstore"}),
}

RESOLUTIONS = {
    "quiet_search": Resolution(
        id="quiet_search", sense=3, effect=2,
        text="With quiet steps and patient eyes, they put the {term} back in its place.",
        fail="They looked everywhere, but the {term} had slipped too far away to find",
        tags={"calm", "search"},
    ),
    "careful_sort": Resolution(
        id="careful_sort", sense=3, effect=3,
        text="Together they sorted the nearby books until the little {term} was found again.",
        fail="Their careful sorting was not enough, and the {term} stayed hidden",
        tags={"calm", "sort"},
    ),
    "bookish_memory": Resolution(
        id="bookish_memory", sense=2, effect=2,
        text="Then the investigator remembered the shelf map and led everyone to the right spot.",
        fail="Even the shelf map could not rescue the {term} in time",
        tags={"calm", "memory"},
    ),
    "loud_shout": Resolution(
        id="loud_shout", sense=1, effect=1,
        text="They shouted and ran about, which only made the books wobble harder.",
        fail="Their shouting made the books wobble and the {term} stay lost",
        tags={"noisy"},
    ),
}

TRAITS = ["kind", "patient", "curious", "careful"]


@dataclass
class StoryParams:
    helper: str
    helper_type: str
    investigator: str
    investigator_type: str
    noble: str
    noble_type: str
    term_kind: str
    clue_kind: str
    resolution: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable-like bookstore storyworld.")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--term", choices=TERMS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--noble")
    ap.add_argument("--investigator")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.resolution and RESOLUTIONS[args.resolution].sense < CALM_MIN:
        raise StoryError("The chosen ending is too noisy for this gentle fable.")
    combos = [c for c in valid_combos()
              if (args.helper is None or c[0] == args.helper)
              and (args.clue is None or c[1] == args.clue)
              and (args.term is None or c[2] == args.term)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    helper, clue, term = rng.choice(sorted(combos))
    resolution = args.resolution or rng.choice(sorted(r for r in RESOLUTIONS if RESOLUTIONS[r].sense >= CALM_MIN))
    noble = args.noble or rng.choice(["Nora", "Milo", "Asha", "Bram"])
    investigator = args.investigator or rng.choice(["Iris", "Otto", "Pip", "Esme"])
    helper_type = HELPERS[helper].kind
    return StoryParams(
        helper=helper, helper_type=helper_type,
        investigator=investigator, investigator_type="owl",
        noble=noble, noble_type="girl" if noble in {"Nora", "Asha", "Esme"} else "boy",
        term_kind=term, clue_kind=clue, resolution=resolution,
    )


def generate(params: StoryParams) -> StorySample:
    helper = HELPERS.get(params.helper)
    clue = CLUES.get(params.clue_kind)
    term = TERMS.get(params.term_kind)
    resolution = RESOLUTIONS.get(params.resolution)
    if not (helper and clue and term and resolution):
        raise StoryError("Invalid parameters for this storyworld.")
    world = tell(helper, clue, term, resolution,
                 noble=params.noble, investigator=params.investigator,
                 noble_type=params.noble_type, investigator_type=params.investigator_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    clue = f["clue_cfg"]
    term = f["term_cfg"]
    return [
        f'Write a fable set in a bookstore that includes the words noble, investigator, and term.',
        f"Tell a gentle story about a noble helper and an investigator who follow a foreshadowed clue to find a missing {term.label}.",
        f'Write a bookstore fable where a clue hints that a {term.label} has gone missing before the search even begins.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who are the story's main characters?",
         f"It is about {f['noble'].id} the noble helper and {f['investigator'].id} the investigator. Together they keep the bookstore calm and orderly."),
        ("What was foreshadowed early in the story?",
         f"A small clue near the front desk hinted that something was off before the search began. That hint prepared the reader for the later discovery of the missing {f['term_cfg'].label}."),
        ("How did the story end?",
         f"They found the missing {f['term_cfg'].label} and put it back in its place. The bookstore became peaceful again, which proves the clue mattered."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a bookstore?",
         "A bookstore is a place where people buy and read books. Shelves, labels, and careful sorting help books stay easy to find."),
        ("What does an investigator do?",
         "An investigator looks closely for clues and tries to solve a mystery. They pay attention to small details that other people might miss."),
        ("What does noble mean?",
         "Noble means honorable, kind, and worthy of respect. In a fable, a noble character often behaves with calm courage."),
        ("What is foreshadowing?",
         "Foreshadowing is a hint placed early in a story that prepares you for something important later. It makes the ending feel connected to the beginning."),
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
helper(H) :- helper_name(H).
clue(C) :- clue_name(C).
term(T) :- term_name(T).
reasonable(T) :- term(T), bookstore_term(T).
foreshadow(C) :- clue(C), clue_kind(C).
story_valid(H,C,T) :- helper(H), clue(C), reasonable(T), foreshadow(C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for hid in HELPERS:
        lines.append(asp.fact("helper_name", hid))
    for cid in CLUES:
        lines.append(asp.fact("clue_name", cid))
    for tid, t in TERMS.items():
        lines.append(asp.fact("term_name", tid))
        if "bookstore" in t.tags:
            lines.append(asp.fact("bookstore_term", tid))
    for cid in CLUES:
        lines.append(asp.fact("clue_kind", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show story_valid/3."))
    return sorted(set(asp.atoms(model, "story_valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH between clingo and Python gate.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            helper=None, clue=None, term=None, resolution=None, noble=None, investigator=None
        ), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test produced a story.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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
    StoryParams(helper="rabbit", helper_type="rabbit", investigator="Iris", investigator_type="owl",
                noble="Nora", noble_type="girl", term_kind="term_card", clue_kind="dusty_book",
                resolution="quiet_search"),
    StoryParams(helper="mouse", helper_type="mouse", investigator="Otto", investigator_type="owl",
                noble="Milo", noble_type="boy", term_kind="term_label", clue_kind="bookmark",
                resolution="careful_sort"),
    StoryParams(helper="bird", helper_type="bird", investigator="Pip", investigator_type="owl",
                noble="Asha", noble_type="girl", term_kind="term_note", clue_kind="bell",
                resolution="bookish_memory"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show story_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for h in HELPERS:
        for c in CLUES:
            for t in TERMS:
                if clue_at_work(CLUES[c], TERMS[t]):
                    combos.append((h, c, t))
    return combos


if __name__ == "__main__":
    main()
