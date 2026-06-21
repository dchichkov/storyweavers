#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py
==========================================================================================

A standalone storyworld for a tiny detective-story domain: a child notices a
small clue, makes a wrong early guess, learns to slow down and compare clues,
and then solves a gentle mystery with help and a happy ending.

The world model drives a complete story arc:
- premise: a favorite thing goes missing during play or work,
- foreshadowing: a small clue appears before the mystery is understood,
- tension: the young detective jumps to a suspect too quickly,
- turn: a helper encourages a more careful method because evidence is superior
  to guessing,
- resolution: the true cause is found, the missing thing is recovered, and the
  detective states the lesson learned.

Run it
------
    python storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py
    python storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py --case cookie --clue blue_thread
    python storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py --all
    python storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/superior_foreshadowing_lesson_learned_happy_ending_detective.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class CaseFile:
    id: str
    missing_label: str
    missing_phrase: str
    owner_line: str
    opening_need: str
    hiding_place: str
    ending_image: str
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
    label: str
    phrase: str
    points_to: str
    suspect: str
    foreshadow: str
    discovery: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class RedHerring:
    id: str
    suspect_label: str
    reason: str
    innocent_truth: str
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
class Method:
    id: str
    verb: str
    line: str
    success_line: str
    lesson_line: str
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
        self.history: list[str] = []

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.history = list(self.history)
        return w


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


def _r_clue_suggests(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return out
    detective = world.get("detective")
    case = world.facts["case_cfg"]
    if detective.memes["certainty"] >= THRESHOLD:
        return out
    sig = ("clue_suggests", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["suspicion"] += 1
    detective.memes["certainty"] += 1
    world.facts["first_guess"] = world.facts["red_herring"].suspect_label
    out.append(
        f"The clue seemed to whisper a quick answer about {world.facts['red_herring'].suspect_label}."
    )
    if case.id:
        world.history.append("clue_led_to_guess")
    return out


def _r_compare_cools(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    helper = world.get("helper")
    if helper.memes["guiding"] < THRESHOLD or detective.memes["suspicion"] < THRESHOLD:
        return out
    sig = ("compare_cools", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["certainty"] = 0.0
    detective.memes["care"] += 1
    detective.memes["patience"] += 1
    out.append("__careful__")
    world.history.append("helper_encouraged_comparison")
    return out


def _r_true_place_found(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    clue = world.get("clue")
    missing = world.get("missing")
    if detective.memes["care"] < THRESHOLD or clue.meters["tracked"] < THRESHOLD:
        return out
    sig = ("true_place_found", missing.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    missing.meters["found"] += 1
    detective.memes["joy"] += 1
    detective.memes["lesson"] += 1
    world.facts["solved"] = True
    world.history.append("true_place_found")
    out.append("__solved__")
    return out


CAUSAL_RULES = [
    Rule(name="clue_suggests", tag="thought", apply=_r_clue_suggests),
    Rule(name="compare_cools", tag="social", apply=_r_compare_cools),
    Rule(name="true_place_found", tag="physical", apply=_r_true_place_found),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combo(case_cfg: CaseFile, clue: Clue, red_herring: RedHerring, method: Method) -> bool:
    if clue.suspect != red_herring.id:
        return False
    if clue.points_to == red_herring.id:
        return False
    if clue.points_to not in {"window_seat", "toy_box", "apron_pocket", "book_bin"}:
        return False
    if method.id not in METHODS:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for case_id, case_cfg in CASES.items():
        for clue_id, clue in CLUES.items():
            for red_id, red in RED_HERRINGS.items():
                for method_id, method in METHODS.items():
                    if valid_combo(case_cfg, clue, red, method):
                        combos.append((case_id, clue_id, red_id, method_id))
    return combos


def predict_with_hunch(world: World) -> dict:
    sim = world.copy()
    sim.get("clue").meters["noticed"] += 1
    propagate(sim, narrate=False)
    return {
        "first_guess": sim.facts.get("first_guess", ""),
        "certainty": sim.get("detective").memes["certainty"],
    }


def introduce(world: World, detective: Entity, helper: Entity, case_cfg: CaseFile) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id} liked to pretend {detective.pronoun()} was the best little detective on the block. "
        f"On this morning, {helper.id} needed help because {case_cfg.owner_line}"
    )
    world.say(case_cfg.opening_need)


def foreshadow(world: World, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    world.say(clue_cfg.foreshadow)
    propagate(world, narrate=False)
    world.facts["foreshadowed"] = True


def announce_case(world: World, detective: Entity, helper: Entity, case_cfg: CaseFile) -> None:
    missing = world.get("missing")
    helper.memes["worry"] += 1
    world.say(
        f'"Detective {detective.id}," {helper.id} said, "my {missing.label} is gone. '
        f'Will you help me solve the case?"'
    )
    detective.memes["pride"] += 1
    world.say(
        f'{detective.id} stood very straight. "I will! I have sharp eyes and very superior notebook pages."'
    )


def jump_to_guess(world: World, detective: Entity, red: RedHerring, clue_cfg: Clue) -> None:
    pred = predict_with_hunch(world)
    world.facts["predicted_guess"] = pred["first_guess"]
    detective.memes["rush"] += 1
    world.say(
        f'{detective.id} spotted {clue_cfg.phrase} and gasped. '
        f'"Aha! It must be {red.suspect_label}," {detective.pronoun()} whispered.'
    )
    world.say(red.reason)
    world.history.append("detective_rushed_to_guess")


def helper_slows(world: World, detective: Entity, helper: Entity, method_cfg: Method, red: RedHerring) -> None:
    helper.memes["guiding"] += 1
    world.say(
        f'But {helper.id} knelt beside {detective.id} and spoke softly. '
        f'"Let us not blame {red.suspect_label} too fast. {method_cfg.line}"'
    )
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} blinked. Guessing suddenly felt smaller than looking carefully.'
    )


def compare_clues(world: World, detective: Entity, method_cfg: Method, clue_cfg: Clue) -> None:
    clue = world.get("clue")
    clue.meters["tracked"] += 1
    detective.memes["focus"] += 1
    world.say(
        f"Together they {method_cfg.verb}. {clue_cfg.discovery}"
    )
    world.say(method_cfg.success_line)
    propagate(world, narrate=False)
    world.history.append("detective_compared_clues")


def reveal_truth(world: World, detective: Entity, helper: Entity, case_cfg: CaseFile, red: RedHerring) -> None:
    missing = world.get("missing")
    world.say(
        f"They hurried to {case_cfg.hiding_place}, and there was {missing.phrase}, safe and waiting."
    )
    world.say(
        f"{red.innocent_truth} Nobody had stolen anything at all."
    )
    world.say(case_cfg.ending_image)
    detective.memes["pride"] = 0.0
    detective.memes["gratitude"] += 1
    helper.memes["worry"] = 0.0


def lesson(world: World, detective: Entity, helper: Entity, method_cfg: Method) -> None:
    detective.memes["lesson"] += 1
    detective.memes["care"] += 1
    world.say(
        f'"I learned something today," {detective.id} said. "{method_cfg.lesson_line}"'
    )
    world.say(
        f'{helper.id} smiled. "That is how a real detective grows wiser."'
    )
    world.history.append("lesson_spoken")


def ending(world: World, detective: Entity, helper: Entity, case_cfg: CaseFile) -> None:
    detective.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Soon the case file was closed, the missing {case_cfg.missing_label} was back where it belonged, "
        f"and {detective.id} felt proud in a quieter, kinder way."
    )
    world.say(
        f"From then on, whenever a mystery began, {detective.id} looked for facts before pointing a finger."
    )


def tell(
    case_cfg: CaseFile,
    clue_cfg: Clue,
    red_cfg: RedHerring,
    method_cfg: Method,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    helper_type: str = "aunt",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        label=detective_name,
        traits=["curious", "earnest"],
        attrs={"guessed_wrong": False},
    ))
    helper = world.add(Entity(
        id="Mina",
        kind="character",
        type=helper_type,
        role="helper",
        label="the helper",
        traits=["calm", "warm"],
        attrs={},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="missing_item",
        label=case_cfg.missing_label,
        phrase=case_cfg.missing_phrase,
        role="missing",
        attrs={"place": case_cfg.hiding_place},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_cfg.label,
        phrase=clue_cfg.phrase,
        role="clue",
        attrs={"points_to": clue_cfg.points_to, "suspect": clue_cfg.suspect},
    ))

    world.facts.update(
        case_cfg=case_cfg,
        clue_cfg=clue_cfg,
        red_herring=red_cfg,
        method_cfg=method_cfg,
        detective=detective,
        helper=helper,
        missing=missing,
        clue=clue,
        first_guess="",
        predicted_guess="",
        solved=False,
        foreshadowed=False,
    )

    introduce(world, detective, helper, case_cfg)
    world.para()
    foreshadow(world, clue_cfg)
    announce_case(world, detective, helper, case_cfg)
    jump_to_guess(world, detective, red_cfg, clue_cfg)
    detective.attrs["guessed_wrong"] = True
    world.para()
    helper_slows(world, detective, helper, method_cfg, red_cfg)
    compare_clues(world, detective, method_cfg, clue_cfg)
    world.para()
    reveal_truth(world, detective, helper, case_cfg, red_cfg)
    lesson(world, detective, helper, method_cfg)
    ending(world, detective, helper, case_cfg)

    world.facts.update(
        guessed_wrong=detective.attrs["guessed_wrong"],
        found=missing.meters["found"] >= THRESHOLD,
        lesson_learned=detective.memes["lesson"] >= THRESHOLD,
        happy_ending=helper.memes["joy"] >= THRESHOLD and detective.memes["joy"] >= THRESHOLD,
    )
    return world


CASES = {
    "cookie": CaseFile(
        id="cookie",
        missing_label="star cookie cutter",
        missing_phrase="the shiny star cookie cutter",
        owner_line="the shiny star cookie cutter could not be found before baking time.",
        opening_need="The kitchen smelled like butter and cinnamon, but one important tool was missing.",
        hiding_place="the apron pocket hanging by the pantry door",
        ending_image="A stripe of sun fell across the table as the cookie cutter winked like a tiny silver badge.",
        tags={"kitchen", "baking"},
    ),
    "library": CaseFile(
        id="library",
        missing_label="library stamp",
        missing_phrase="the red library stamp",
        owner_line="the red library stamp had vanished before story hour.",
        opening_need="The reading rug was ready, the picture books were stacked, and still the special stamp was nowhere to be seen.",
        hiding_place="the rolling book bin beside the window",
        ending_image="The stamp sat on top of the books like a bright little cherry, ready for the next page.",
        tags={"books", "library"},
    ),
    "garden": CaseFile(
        id="garden",
        missing_label="seed packet",
        missing_phrase="the striped seed packet",
        owner_line="the striped seed packet had disappeared just when planting was about to begin.",
        opening_need="A trowel, a watering can, and neat little pots waited on the bench, but the seeds were missing.",
        hiding_place="the toy box near the back steps",
        ending_image="The packet peeked from the box, and soon the whole garden bench looked busy and hopeful again.",
        tags={"garden", "seeds"},
    ),
}

CLUES = {
    "blue_thread": Clue(
        id="blue_thread",
        label="blue thread",
        phrase="a tiny blue thread on the floor",
        points_to="apron_pocket",
        suspect="cat",
        foreshadow="Before anyone said the word mystery, a tiny blue thread clung to the floor by the pantry door.",
        discovery="The blue thread matched the apron pocket, not the cat's basket at all.",
        tags={"thread", "evidence"},
    ),
    "red_smudge": Clue(
        id="red_smudge",
        label="red smudge",
        phrase="a small red smudge on a wooden handle",
        points_to="book_bin",
        suspect="younger_brother",
        foreshadow="Long before the search began, a faint red smudge waited on a handle near the window.",
        discovery="The red smudge matched the stamp ink on the rolling book bin.",
        tags={"ink", "evidence"},
    ),
    "soil_dots": Clue(
        id="soil_dots",
        label="soil dots",
        phrase="three little soil dots by the back steps",
        points_to="toy_box",
        suspect="puppy",
        foreshadow="At the very start, three little soil dots rested near the back steps like a quiet secret.",
        discovery="The soil dots led neatly toward the toy box, where the seed packet had slipped beside the toy shovel.",
        tags={"soil", "evidence"},
    ),
}

RED_HERRINGS = {
    "cat": RedHerring(
        id="cat",
        suspect_label="the cat",
        reason="The cat did love curling up near towels and strings, so the guess sounded possible for a moment.",
        innocent_truth="The cat was only asleep under a chair with both paws tucked in.",
        tags={"pet", "false_guess"},
    ),
    "younger_brother": RedHerring(
        id="younger_brother",
        suspect_label="little Ben",
        reason="Little Ben liked stamping paper hearts, so the guess sounded possible for a moment.",
        innocent_truth="Little Ben had been building a block tower the whole time and had never touched the stamp.",
        tags={"sibling", "false_guess"},
    ),
    "puppy": RedHerring(
        id="puppy",
        suspect_label="the puppy",
        reason="The puppy did carry socks and leaves sometimes, so the guess sounded possible for a moment.",
        innocent_truth="The puppy only wagged from the porch, proud of a very ordinary stick.",
        tags={"pet", "false_guess"},
    ),
}

METHODS = {
    "compare": Method(
        id="compare",
        verb="followed the clue, checked one place after another, and compared what really matched",
        line="A careful comparison is superior to a quick hunch.",
        success_line="Each new fact made the puzzle less foggy and more fair.",
        lesson_line="Facts are superior to guesses, and I should look twice before I blame someone.",
        tags={"compare", "lesson"},
    ),
    "notebook": Method(
        id="notebook",
        verb="made a tiny list, drew the clue in a notebook, and checked where it truly belonged",
        line="A notebook full of facts is superior to a finger pointed too soon.",
        success_line="The list kept their thoughts tidy, and the right answer had room to appear.",
        lesson_line="Writing down facts is superior to guessing, because it helps me be careful and kind.",
        tags={"notebook", "lesson"},
    ),
}


@dataclass
class StoryParams:
    case: str
    clue: str
    red_herring: str
    method: str
    detective_name: str
    detective_type: str
    helper_type: str
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


KNOWLEDGE = {
    "evidence": [
        (
            "What is evidence in a mystery?",
            "Evidence is a clue that helps you learn what really happened. A good detective uses evidence instead of making wild guesses."
        )
    ],
    "false_guess": [
        (
            "Why should you not blame someone too fast?",
            "Blaming someone too fast can hurt feelings and can also be wrong. It is better to slow down and check the facts first."
        )
    ],
    "compare": [
        (
            "Why is comparing clues helpful?",
            "Comparing clues helps you see what truly matches and what only seems close. That makes your answer stronger and fairer."
        )
    ],
    "notebook": [
        (
            "Why might a detective use a notebook?",
            "A notebook helps a detective remember clues in the right order. Writing things down can stop a rushed mistake."
        )
    ],
    "thread": [
        (
            "What can a thread tell you?",
            "A thread can show where cloth or clothing has been. In a mystery, even a tiny thread can point to the right place."
        )
    ],
    "ink": [
        (
            "Why is ink a useful clue?",
            "Ink can leave a color mark where an object was used or set down. That color can help you connect a clue to the right tool or place."
        )
    ],
    "soil": [
        (
            "Why are soil dots a good clue?",
            "Soil dots can show where something came from or where it was carried. Small marks on the ground can tell a careful story."
        )
    ],
}
KNOWLEDGE_ORDER = ["evidence", "false_guess", "compare", "notebook", "thread", "ink", "soil"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    case_cfg = f["case_cfg"]
    clue_cfg = f["clue_cfg"]
    return [
        f'Write a gentle detective story for ages 3 to 5 that includes the word "superior" and a clue like {clue_cfg.label}.',
        f"Tell a child-facing mystery where {detective.id} makes a quick wrong guess, then learns to follow evidence and find the missing {case_cfg.missing_label}.",
        f"Write a detective story with foreshadowing, a lesson learned, and a happy ending, where a tiny clue turns out to matter."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    case_cfg = f["case_cfg"]
    clue_cfg = f["clue_cfg"]
    red = f["red_herring"]
    method_cfg = f["method_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a young detective, and {helper.id}, who asked for help finding a missing {case_cfg.missing_label}. Together they turned an everyday problem into a little mystery."
        ),
        (
            f"What was missing in the story?",
            f"The missing thing was {case_cfg.missing_phrase}. It mattered because {case_cfg.owner_line}"
        ),
        (
            "What was the foreshadowing clue?",
            f"The foreshadowing clue was {clue_cfg.phrase}. It appeared before the mystery was solved, so the story quietly prepared the answer ahead of time."
        ),
        (
            f"Why did {detective.id} make a wrong guess at first?",
            f"{detective.id} saw {clue_cfg.phrase} and quickly guessed it meant {red.suspect_label} had taken the missing item. That guess felt possible for a moment, but it came from rushing instead of checking more evidence."
        ),
        (
            f"How did {helper.id} help solve the case?",
            f"{helper.id} slowed the search down and reminded {detective.id} that {method_cfg.line.lower()} They worked step by step, which turned a shaky hunch into a real answer."
        ),
    ]
    if f.get("found"):
        qa.append(
            (
                "How was the mystery solved?",
                f"They solved it by following the clue carefully until it matched the true hiding place, {case_cfg.hiding_place}. The evidence pointed there more clearly than the first guess ever did."
            )
        )
    if f.get("lesson_learned"):
        qa.append(
            (
                f"What lesson did {detective.id} learn?",
                f"{detective.id} learned that {method_cfg.lesson_line.lower()} The lesson mattered because it helped {detective.pronoun('object')} be both smarter and kinder."
            )
        )
    if f.get("happy_ending"):
        qa.append(
            (
                "Why is the ending happy?",
                f"The ending is happy because the missing {case_cfg.missing_label} was found, nobody had been truly blamed, and everyone could go back to the good part of the day. The final picture shows that the problem is over and the room feels bright again."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"evidence", "false_guess"} | set(world.facts["clue_cfg"].tags) | set(world.facts["method_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  history: {world.history}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        case="cookie",
        clue="blue_thread",
        red_herring="cat",
        method="compare",
        detective_name="Nora",
        detective_type="girl",
        helper_type="aunt",
        seed=None,
    ),
    StoryParams(
        case="library",
        clue="red_smudge",
        red_herring="younger_brother",
        method="notebook",
        detective_name="Max",
        detective_type="boy",
        helper_type="mother",
        seed=None,
    ),
    StoryParams(
        case="garden",
        clue="soil_dots",
        red_herring="puppy",
        method="compare",
        detective_name="Lila",
        detective_type="girl",
        helper_type="father",
        seed=None,
    ),
]


def explain_rejection(case_id: str, clue_id: str, red_id: str, method_id: str) -> str:
    case_cfg = CASES.get(case_id)
    clue_cfg = CLUES.get(clue_id)
    red_cfg = RED_HERRINGS.get(red_id)
    method_cfg = METHODS.get(method_id)
    if not all([case_cfg, clue_cfg, red_cfg, method_cfg]):
        return "(No story: one or more requested options do not exist in this world.)"
    if clue_cfg.suspect != red_cfg.id:
        return (
            f"(No story: the clue '{clue_id}' tempts the detective to suspect {RED_HERRINGS[clue_cfg.suspect].suspect_label}, "
            f"not {red_cfg.suspect_label}. The early wrong guess must be grounded in the clue.)"
        )
    if clue_cfg.points_to == red_cfg.id:
        return "(No story: the clue cannot point to the red herring and the true answer at the same time.)"
    return "(No story: this combination is outside the world's detective logic.)"


ASP_RULES = r"""
valid(Case, Clue, Red, Method) :-
    case(Case), clue(Clue), red_herring(Red), method(Method),
    clue_suspect(Clue, Red),
    clue_points_to(Clue, Place),
    true_place(Place),
    not clue_points_to(Clue, Red).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for case_id in CASES:
        lines.append(asp.fact("case", case_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_suspect", clue_id, clue.suspect))
        lines.append(asp.fact("clue_points_to", clue_id, clue.points_to))
    for red_id in RED_HERRINGS:
        lines.append(asp.fact("red_herring", red_id))
    for method_id in METHODS:
        lines.append(asp.fact("method", method_id))
    for place in ["window_seat", "toy_box", "apron_pocket", "book_bin"]:
        lines.append(asp.fact("true_place", place))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def verify_smoke() -> None:
    params = resolve_params(build_parser().parse_args([]), random.Random(123))
    params.seed = 123
    sample = generate(params)
    if not sample.story or "superior" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story missing text or required word.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
    try:
        verify_smoke()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    for params in CURATED:
        try:
            sample = generate(params)
            if not sample.story:
                raise StoryError("empty story")
        except Exception as err:
            rc = 1
            print(f"CURATED GENERATION FAILED for {params}: {err}")
    if rc == 0:
        print(f"OK: curated generation succeeded for {len(CURATED)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a gentle child detective learns that evidence is superior to guessing."
    )
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--red-herring", dest="red_herring", choices=RED_HERRINGS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


GIRL_NAMES = ["Nora", "Lila", "Mia", "Ava", "Ella", "Ruby"]
BOY_NAMES = ["Max", "Leo", "Sam", "Finn", "Theo", "Eli"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.case and args.clue and args.red_herring and args.method:
        if not valid_combo(CASES[args.case], CLUES[args.clue], RED_HERRINGS[args.red_herring], METHODS[args.method]):
            raise StoryError(explain_rejection(args.case, args.clue, args.red_herring, args.method))

    combos = [
        c for c in valid_combos()
        if (args.case is None or c[0] == args.case)
        and (args.clue is None or c[1] == args.clue)
        and (args.red_herring is None or c[2] == args.red_herring)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    case_id, clue_id, red_id, method_id = rng.choice(sorted(combos))
    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(["mother", "father", "aunt", "uncle"])
    return StoryParams(
        case=case_id,
        clue=clue_id,
        red_herring=red_id,
        method=method_id,
        detective_name=detective_name,
        detective_type=detective_type,
        helper_type=helper_type,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.case not in CASES:
        raise StoryError(f"(Unknown case '{params.case}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue '{params.clue}'.)")
    if params.red_herring not in RED_HERRINGS:
        raise StoryError(f"(Unknown red herring '{params.red_herring}'.)")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method '{params.method}'.)")
    if params.detective_type not in {"girl", "boy"}:
        raise StoryError(f"(Unknown detective type '{params.detective_type}'.)")
    if params.helper_type not in {"mother", "father", "aunt", "uncle"}:
        raise StoryError(f"(Unknown helper type '{params.helper_type}'.)")

    case_cfg = CASES[params.case]
    clue_cfg = CLUES[params.clue]
    red_cfg = RED_HERRINGS[params.red_herring]
    method_cfg = METHODS[params.method]
    if not valid_combo(case_cfg, clue_cfg, red_cfg, method_cfg):
        raise StoryError(explain_rejection(params.case, params.clue, params.red_herring, params.method))

    world = tell(
        case_cfg=case_cfg,
        clue_cfg=clue_cfg,
        red_cfg=red_cfg,
        method_cfg=method_cfg,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        helper_type=params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (case, clue, red_herring, method) combos:\n")
        for case_id, clue_id, red_id, method_id in combos:
            print(f"  {case_id:8} {clue_id:12} {red_id:16} {method_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.case} case ({p.clue}, {p.red_herring}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
