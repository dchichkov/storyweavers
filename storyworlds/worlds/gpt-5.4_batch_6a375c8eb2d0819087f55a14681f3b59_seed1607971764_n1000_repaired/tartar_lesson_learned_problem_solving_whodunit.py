#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py
============================================================================

A small storyworld for a child-facing kitchen whodunit: **the cream of tartar
is missing right when a child and a grown-up are about to bake**, so they solve
the mystery by checking clues instead of blaming first.

The seed asked for:
- the word "tartar"
- a lesson learned
- problem solving
- a whodunit flavor

This world rebuilds that as a tiny simulation with typed entities, simple
physical/emotional state, a reasonableness gate, and an inline ASP twin.

Run it
------
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py --recipe cloud_kisses
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py --suspect grandpa_ben --use polish_kettle
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/tartar_lesson_learned_problem_solving_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
CAREFUL_TRAITS = {"careful", "patient", "thorough"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "grandpa": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain configuration
# ---------------------------------------------------------------------------
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
class Recipe:
    id: str
    label: str
    bowl_text: str
    why_tartar: str
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
class SuspectCfg:
    id: str
    name: str
    type: str
    relation: str
    allowed_uses: set[str] = field(default_factory=set)
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
class UseCfg:
    id: str
    gerund: str
    found_text: str
    apology_text: str
    clue: str = ""
    place: str = ""
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
class ClueCfg:
    id: str
    label: str
    discovery: str
    reasoning: str
    points_to: set[str] = field(default_factory=set)
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
class PlaceCfg:
    id: str
    label: str
    scene: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.paragraphs = [[]]
        out.fired = set(self.fired)
        out.facts = copy.deepcopy(self.facts)
        return out


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
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


def _r_case_open(world: World) -> list[str]:
    pantry = world.get("pantry")
    hero = world.get("hero")
    if pantry.meters["missing_tartar"] < THRESHOLD:
        return []
    sig = ("case_open",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.get("helper").memes["calm"] += 1
    world.facts["case_open"] = True
    return []


def _r_reason(world: World) -> list[str]:
    hero = world.get("hero")
    if world.facts.get("clue_seen") and world.facts.get("clue_matches_use"):
        sig = ("reason", world.facts.get("clue_id"))
        if sig in world.fired:
            return []
        world.fired.add(sig)
        hero.memes["confidence"] += 1
        world.get("pantry").meters["search_progress"] += 1
    return []


def _r_find(world: World) -> list[str]:
    if world.facts.get("searched_place") and world.facts.get("searched_place") == world.facts.get("actual_place"):
        sig = ("find", world.facts.get("searched_place"))
        if sig in world.fired:
            return []
        world.fired.add(sig)
        jar = world.get("jar")
        jar.meters["found"] += 1
        jar.meters["missing"] = 0.0
        world.get("hero").memes["relief"] += 1
        world.get("helper").memes["relief"] += 1
        return []
    return []


CAUSAL_RULES = [
    Rule(name="case_open", tag="story", apply=_r_case_open),
    Rule(name="reason", tag="story", apply=_r_reason),
    Rule(name="find", tag="story", apply=_r_find),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints and outcome helpers
# ---------------------------------------------------------------------------
def valid_combo(suspect_id: str, use_id: str, clue_id: str, place_id: str) -> bool:
    suspect = SUSPECTS[suspect_id]
    use = USES[use_id]
    clue = CLUES[clue_id]
    place = PLACES[place_id]
    return (
        use_id in suspect.allowed_uses
        and clue_id == use.clue
        and place_id == use.place
        and use_id in clue.points_to
        and use_id in place.supports
    )


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for recipe_id in RECIPES:
        for suspect_id in SUSPECTS:
            for use_id, use in USES.items():
                if valid_combo(suspect_id, use_id, use.clue, use.place):
                    combos.append((recipe_id, suspect_id, use_id, use.clue, use.place))
    return combos


def outcome_of(params: "StoryParams") -> str:
    return "patient" if params.trait in CAREFUL_TRAITS else "hasty"


def explain_rejection(suspect_id: str, use_id: str, clue_id: str, place_id: str) -> str:
    pieces = []
    suspect = SUSPECTS.get(suspect_id)
    use = USES.get(use_id)
    clue = CLUES.get(clue_id)
    place = PLACES.get(place_id)
    if suspect and use and use_id not in suspect.allowed_uses:
        pieces.append(f"{suspect.name} is not the sort of person who would be using the cream of tartar for {use.gerund}")
    if use and clue and clue_id != use.clue:
        pieces.append(f'the clue "{clue.label}" does not honestly point to that use')
    if use and place and place_id != use.place:
        pieces.append(f"that use would not leave the jar in {place.label}")
    if not pieces:
        return "(No story: the chosen mystery pieces do not make a coherent case.)"
    return "(No story: " + "; ".join(pieces) + ".)"


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, helper: Entity, recipe: Recipe) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"On a bright kitchen afternoon, {hero.id} stood on a little stool beside "
        f"{hero.pronoun('possessive')} {helper.label_word}. They were going to bake "
        f"{recipe.label} together."
    )
    world.say(recipe.bowl_text)


def discover_missing(world: World, hero: Entity, helper: Entity, recipe: Recipe) -> None:
    pantry = world.get("pantry")
    jar = world.get("jar")
    pantry.meters["missing_tartar"] = 1
    jar.meters["missing"] = 1
    world.facts["need"] = "cream of tartar"
    propagate(world, narrate=False)
    world.say(
        f"But when {helper.label_word} reached for the little jar of cream of tartar, "
        f"the shelf held only a pale ring of dust."
    )
    world.say(
        f'"Oh!" said {hero.id}. "The tartar is missing, and {recipe.why_tartar}."'
    )
    world.say(
        f'{hero.id} narrowed {hero.pronoun("possessive")} eyes. "This is a case."'
    )


def suspect_list(world: World, hero: Entity, suspect: SuspectCfg) -> None:
    world.say(
        f"{hero.id} thought of everyone who had padded through the kitchen that day. "
        f"{suspect.name} had been nearby, so {hero.pronoun()} wrote the first name in "
        f"{hero.pronoun('possessive')} pretend detective notebook."
    )


def caution_or_blurt(world: World, hero: Entity, helper: Entity, suspect: SuspectCfg, trait: str) -> None:
    world.facts["outcome"] = "patient" if trait in CAREFUL_TRAITS else "hasty"
    if trait in CAREFUL_TRAITS:
        hero.memes["patience"] += 1
        world.say(
            f'"A good detective checks clues before guessing," {helper.label_word} said. '
            f'{hero.id} nodded and took a slow detective breath.'
        )
    else:
        hero.memes["hasty"] += 1
        world.say(
            f'"I bet {suspect.name} took it!" {hero.id} burst out. But {helper.label_word} '
            f"gently shook {helper.pronoun('possessive')} head."
        )
        world.say(
            f'"Maybe, maybe not," {helper.label_word} said. "Let\'s look first, so we are fair."'
        )


def find_clue(world: World, hero: Entity, clue: ClueCfg, use: UseCfg) -> None:
    world.facts["clue_seen"] = True
    world.facts["clue_id"] = clue.id
    world.facts["clue_matches_use"] = clue.id == use.clue
    hero.meters["clue_seen"] += 1
    propagate(world, narrate=False)
    world.say(clue.discovery)
    world.say(clue.reasoning)


def reason_to_place(world: World, hero: Entity, place: PlaceCfg) -> None:
    hero.memes["confidence"] += 1
    world.say(
        f'"Then the trail points to {place.label}," said {hero.id}. '
        f'{hero.pronoun().capitalize()} tugged {helper.pronoun("object")} that way.'
    )


def search_place(world: World, place: PlaceCfg) -> None:
    world.facts["searched_place"] = place.id
    propagate(world, narrate=False)
    world.say(place.scene)


def reveal(world: World, suspect_ent: Entity, suspect_cfg: SuspectCfg, use: UseCfg) -> None:
    suspect_ent.memes["embarrassed"] += 1
    world.say(
        f"There was {suspect_cfg.name}, and beside {suspect_ent.pronoun('object')} sat the little jar."
    )
    world.say(use.found_text.format(name=suspect_cfg.name))


def solve(world: World, helper: Entity, suspect_cfg: SuspectCfg, use: UseCfg, recipe: Recipe) -> None:
    world.get("jar").meters["returned"] += 1
    world.get("hero").memes["pride"] += 1
    world.say(use.apology_text.format(name=suspect_cfg.name))
    world.say(
        f"{helper.label_word.capitalize()} thanked {suspect_cfg.name} for bringing it right back. "
        f"Soon the cream of tartar was in the bowl where it belonged."
    )
    world.say(
        f"The batter changed at once, and {recipe.why_tartar} no longer felt like a problem."
    )


def lesson(world: World, hero: Entity, helper: Entity, suspect_cfg: SuspectCfg) -> None:
    hero.memes["lesson"] += 1
    helper.memes["love"] += 1
    if world.facts.get("outcome") == "hasty":
        world.say(
            f'{hero.id} looked at {suspect_cfg.name} and whispered, "I\'m sorry I guessed before I knew."'
        )
        world.say(
            f'{helper.label_word.capitalize()} squeezed {hero.pronoun("possessive")} shoulder. '
            f'"Mysteries are solved with clues, not quick blame."'
        )
    else:
        world.say(
            f'{helper.label_word.capitalize()} smiled. "You were careful, and that helped you solve the mystery kindly."'
        )
    world.say(
        'Together they put a paper label on the shelf: "Please ask before borrowing."'
    )


def ending(world: World, hero: Entity, recipe: Recipe) -> None:
    hero.memes["joy"] += 1
    world.get("jar").meters["needed"] = 0.0
    world.get("tray").meters["baked"] += 1
    world.say(
        f"Before long, the kitchen smelled warm and sweet. {recipe.ending_image}"
    )


# ---------------------------------------------------------------------------
# Story assembly
# ---------------------------------------------------------------------------
def tell(
    recipe: Recipe,
    suspect_cfg: SuspectCfg,
    use: UseCfg,
    clue: ClueCfg,
    place: PlaceCfg,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    helper_type: str = "mother",
    trait: str = "careful",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", label=hero_name))
    helper = world.add(Entity(id="Parent", kind="character", type=helper_type, role="helper", label="the helper"))
    suspect_ent = world.add(
        Entity(
            id=suspect_cfg.name,
            kind="character",
            type=suspect_cfg.type,
            role="suspect",
            label=suspect_cfg.relation,
            attrs={"relation": suspect_cfg.relation},
        )
    )
    world.add(Entity(id="pantry", type="place", label="pantry"))
    world.add(Entity(id="jar", type="thing", label="cream of tartar"))
    world.add(Entity(id="tray", type="thing", label="tray"))
    world.facts.update(
        recipe=recipe,
        suspect_cfg=suspect_cfg,
        use=use,
        clue=clue,
        place=place,
        hero=hero,
        helper=helper,
        suspect=suspect_ent,
        actual_place=place.id,
        clue_seen=False,
        clue_matches_use=False,
        searched_place="",
        case_open=False,
        outcome="",
    )

    introduce(world, hero, helper, recipe)
    world.para()
    discover_missing(world, hero, helper, recipe)
    suspect_list(world, hero, suspect_cfg)
    caution_or_blurt(world, hero, helper, suspect_cfg, trait)
    world.para()
    find_clue(world, hero, clue, use)
    reason_to_place(world, hero, place)
    search_place(world, place)
    reveal(world, suspect_ent, suspect_cfg, use)
    world.para()
    solve(world, helper, suspect_cfg, use, recipe)
    lesson(world, hero, helper, suspect_cfg)
    ending(world, hero, recipe)

    world.facts.update(
        solved=world.get("jar").meters["found"] >= THRESHOLD,
        baked=world.get("tray").meters["baked"] >= THRESHOLD,
        patient=(trait in CAREFUL_TRAITS),
        borrowed_by=suspect_cfg.name,
        trait=trait,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
RECIPES = {
    "snickerdoodles": Recipe(
        id="snickerdoodles",
        label="snickerdoodles",
        bowl_text="Butter, sugar, and flour were already in the bowl, and only one important spoonful was left to add.",
        why_tartar="the cookies would not get their soft little crackle without it",
        ending_image="A plate of cinnamon-sugar snickerdoodles cooled on the table, each one crinkled just right.",
        tags={"baking", "cookies", "tartar"},
    ),
    "cloud_kisses": Recipe(
        id="cloud_kisses",
        label="cloud-kiss cookies",
        bowl_text="A shiny bowl of whipped egg whites waited like a puff of snow, but the recipe still needed one tiny helper ingredient.",
        why_tartar="the fluffy peaks would not stay tall without it",
        ending_image="The cloud-kiss cookies came out light as little moons, and {hero} could hardly wait to share them.".replace("{hero}", "the child"),
        tags={"baking", "cookies", "tartar"},
    ),
}

SUSPECTS = {
    "milo": SuspectCfg(
        id="milo",
        name="Milo",
        type="boy",
        relation="older brother",
        allowed_uses={"playdough"},
        tags={"sibling"},
    ),
    "tessa": SuspectCfg(
        id="tessa",
        name="Tessa",
        type="girl",
        relation="cousin",
        allowed_uses={"playdough"},
        tags={"family"},
    ),
    "grandpa_ben": SuspectCfg(
        id="grandpa_ben",
        name="Grandpa Ben",
        type="grandpa",
        relation="grandpa",
        allowed_uses={"polish_kettle"},
        tags={"family"},
    ),
    "aunt_june": SuspectCfg(
        id="aunt_june",
        name="Aunt June",
        type="aunt",
        relation="aunt",
        allowed_uses={"polish_kettle"},
        tags={"family"},
    ),
}

USES = {
    "playdough": UseCfg(
        id="playdough",
        gerund="making rainbow playdough",
        found_text="{name} was rolling a bright rope of homemade playdough between both hands.",
        apology_text='{name} blinked and said, "I borrowed the cream of tartar for the playdough and forgot to carry it back. I should have asked and returned it sooner."',
        clue="dough_crumb",
        place="craft_table",
        tags={"playdough", "borrowing"},
    ),
    "polish_kettle": UseCfg(
        id="polish_kettle",
        gerund="polishing the old copper kettle",
        found_text="{name} was rubbing the old copper kettle until it winked in the light.",
        apology_text='{name} looked up and said, "I used the cream of tartar to help clean the kettle and left the jar here by mistake. I should have told everyone."',
        clue="shiny_spoon",
        place="hall_cabinet",
        tags={"cleaning", "borrowing"},
    ),
}

CLUES = {
    "dough_crumb": ClueCfg(
        id="dough_crumb",
        label="a tiny rainbow crumb",
        discovery="Near the empty shelf, {hero} spotted a tiny rainbow crumb stuck to the counter. It looked just like a bit of dried playdough.".replace("{hero}", "the child"),
        reasoning='"Someone making doughy art passed through here," said the child. "That crumb did not come from cookie batter."',
        points_to={"playdough"},
        tags={"clue", "playdough"},
    ),
    "shiny_spoon": ClueCfg(
        id="shiny_spoon",
        label="a spoon polished bright as a mirror",
        discovery="Beside the sink, a spoon gleamed brighter than the rest, and the air held a sharp clean smell.",
        reasoning='"That looks like cleaning, not baking," said the child. "Maybe the jar went wherever the shiny things went."',
        points_to={"polish_kettle"},
        tags={"clue", "cleaning"},
    ),
}

PLACES = {
    "craft_table": PlaceCfg(
        id="craft_table",
        label="the craft table",
        scene="They followed the clue to the craft table by the window, where paper stars, cookie cutters, and little lumps of color lay in a cheerful mess.",
        supports={"playdough"},
        tags={"room", "playdough"},
    ),
    "hall_cabinet": PlaceCfg(
        id="hall_cabinet",
        label="the hall cabinet",
        scene="They tiptoed to the hall cabinet, where the old copper kettle sat on a folded towel beside a soft polishing cloth.",
        supports={"polish_kettle"},
        tags={"room", "cleaning"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Lucy", "Ella", "Maya"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Theo", "Sam", "Eli", "Noah"]
TRAITS = ["careful", "patient", "thorough", "excited", "impulsive", "quick"]
HELPERS = ["mother", "father"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    recipe: str = "snickerdoodles"
    suspect: str = "milo"
    use: str = "playdough"
    clue: str = "dough_crumb"
    place: str = "craft_table"
    hero_name: str = "Nora"
    hero_gender: str = "girl"
    helper_type: str = "mother"
    trait: str = "careful"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "tartar": [
        (
            "What is cream of tartar?",
            "Cream of tartar is a white powder used in some kitchen jobs. It can help some doughs and whipped mixtures behave the right way.",
        )
    ],
    "playdough": [
        (
            "Why might someone use cream of tartar in homemade playdough?",
            "It can help homemade playdough feel smoother and last longer. That is why a kitchen ingredient might turn up in an art project.",
        )
    ],
    "cleaning": [
        (
            "Can cream of tartar help clean some metal things?",
            "Yes. Grown-ups sometimes use it in gentle cleaning mixtures, especially for old metal items, because it can help lift dull spots.",
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. Good detectives use clues to test ideas instead of just guessing.",
        )
    ],
    "borrowing": [
        (
            "What should you do before borrowing something from a shared shelf?",
            "Ask first, and return it when you are done. That helps everyone find what they need and keeps little problems from turning into big ones.",
        )
    ],
    "baking": [
        (
            "Why is it helpful to follow a recipe carefully?",
            "Recipes work best when the ingredients are there and the steps are done in order. Careful checking helps you notice problems early and fix them.",
        )
    ],
}

KNOWLEDGE_ORDER = ["tartar", "clue", "borrowing", "playdough", "cleaning", "baking"]


def generation_prompts(world: World) -> list[str]:
    recipe = world.facts["recipe"]
    suspect = world.facts["suspect_cfg"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old where a child notices the cream of tartar is missing while baking {recipe.label}.',
        f"Tell a problem-solving mystery story where a child follows one small clue, finds that {suspect.name} borrowed the ingredient, and learns to check facts before blaming anyone.",
        'Write a short story that includes the word "tartar", has a lesson learned, and ends with the mystery solved kindly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    helper = world.facts["helper"]
    recipe = world.facts["recipe"]
    suspect = world.facts["suspect_cfg"]
    clue = world.facts["clue"]
    place = world.facts["place"]
    use = world.facts["use"]
    qa: list[tuple[str, str]] = [
        (
            "What problem started the mystery?",
            f"The little jar of cream of tartar was missing just when {hero.id} and {hero.pronoun('possessive')} {helper.label_word} needed it for {recipe.label}. That mattered because {recipe.why_tartar}.",
        ),
        (
            "What clue helped them solve the case?",
            f"The clue was {clue.label}. It mattered because it pointed toward someone who had been {use.gerund}.",
        ),
        (
            "How did they figure out where to look?",
            f"They did not guess wildly. They used the clue to reason that the jar should be near {place.label}, and then they went there to check.",
        ),
        (
            f"Who had the cream of tartar, and why?",
            f"{suspect.name} had it. {suspect.name} had borrowed it for {use.gerund} and forgot to bring it back.",
        ),
    ]
    if world.facts.get("outcome") == "hasty":
        qa.append(
            (
                "What lesson did the child learn?",
                f"{hero.id} learned not to blame someone before the clues were clear. Saying sorry mattered because being fair is part of solving a mystery well.",
            )
        )
    else:
        qa.append(
            (
                "What lesson did the child learn?",
                f"{hero.id} learned that careful checking helps solve problems kindly. Looking first kept the mystery calm and helped everyone work together.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"The jar was returned, the baking could continue, and they put a note on the shelf asking people to borrow things properly. The warm kitchen ending showed that the problem had truly been solved.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tartar", "clue", "borrowing", "baking"}
    recipe = world.facts["recipe"]
    use = world.facts["use"]
    tags |= set(recipe.tags)
    tags |= set(use.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {{'outcome': {world.facts.get('outcome')!r}, 'case_open': {world.facts.get('case_open')!r}, 'searched_place': {world.facts.get('searched_place')!r}}}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        recipe="snickerdoodles",
        suspect="milo",
        use="playdough",
        clue="dough_crumb",
        place="craft_table",
        hero_name="Nora",
        hero_gender="girl",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        recipe="cloud_kisses",
        suspect="grandpa_ben",
        use="polish_kettle",
        clue="shiny_spoon",
        place="hall_cabinet",
        hero_name="Leo",
        hero_gender="boy",
        helper_type="father",
        trait="patient",
    ),
    StoryParams(
        recipe="snickerdoodles",
        suspect="tessa",
        use="playdough",
        clue="dough_crumb",
        place="craft_table",
        hero_name="Ava",
        hero_gender="girl",
        helper_type="father",
        trait="quick",
    ),
    StoryParams(
        recipe="cloud_kisses",
        suspect="aunt_june",
        use="polish_kettle",
        clue="shiny_spoon",
        place="hall_cabinet",
        hero_name="Max",
        hero_gender="boy",
        helper_type="mother",
        trait="impulsive",
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(R,S,U,C,P) :- recipe(R), suspect(S), use(U), clue(C), place(P),
                    allowed(S,U), clue_of(U,C), place_of(U,P),
                    points_to(C,U), supports(P,U).

careful_trait(T) :- trait(T), is_careful(T).
outcome(patient) :- careful_trait(T).
outcome(hasty)   :- trait(T), not careful_trait(T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for recipe_id in RECIPES:
        lines.append(asp.fact("recipe", recipe_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for use_id in sorted(suspect.allowed_uses):
            lines.append(asp.fact("allowed", suspect_id, use_id))
    for use_id, use in USES.items():
        lines.append(asp.fact("use", use_id))
        lines.append(asp.fact("clue_of", use_id, use.clue))
        lines.append(asp.fact("place_of", use_id, use.place))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for use_id in sorted(clue.points_to):
            lines.append(asp.fact("points_to", clue_id, use_id))
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for use_id in sorted(place.supports):
            lines.append(asp.fact("supports", place_id, use_id))
    for trait in sorted(TRAITS):
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("is_careful", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(
        asp_program(
            "",
            f"{asp.fact('trait', params.trait)}\n#show outcome/1.",
        )
    )
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if outcome_of(params) != asp_outcome(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome comparisons failed.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=True, header="### smoke")
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: generate()/emit() smoke test passed.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny whodunit storyworld about missing cream of tartar, careful clues, and a kind solution."
    )
    ap.add_argument("--recipe", choices=RECIPES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--use", choices=USES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.suspect and args.use and args.clue and args.place:
        if not valid_combo(args.suspect, args.use, args.clue, args.place):
            raise StoryError(explain_rejection(args.suspect, args.use, args.clue, args.place))

    combos = [
        combo
        for combo in valid_combos()
        if (args.recipe is None or combo[0] == args.recipe)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.use is None or combo[2] == args.use)
        and (args.clue is None or combo[3] == args.clue)
        and (args.place is None or combo[4] == args.place)
    ]
    if not combos:
        suspect_id = args.suspect or next(iter(SUSPECTS))
        use_id = args.use or next(iter(USES))
        clue_id = args.clue or USES[use_id].clue
        place_id = args.place or USES[use_id].place
        raise StoryError(explain_rejection(suspect_id, use_id, clue_id, place_id))

    recipe_id, suspect_id, use_id, clue_id, place_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    helper_type = args.helper_type or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        recipe=recipe_id,
        suspect=suspect_id,
        use=use_id,
        clue=clue_id,
        place=place_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.recipe not in RECIPES:
        raise StoryError(f"Unknown recipe: {params.recipe}")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"Unknown suspect: {params.suspect}")
    if params.use not in USES:
        raise StoryError(f"Unknown use: {params.use}")
    if params.clue not in CLUES:
        raise StoryError(f"Unknown clue: {params.clue}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"Unknown hero gender: {params.hero_gender}")
    if params.helper_type not in HELPERS:
        raise StoryError(f"Unknown helper type: {params.helper_type}")
    if params.trait not in TRAITS:
        raise StoryError(f"Unknown trait: {params.trait}")
    if not valid_combo(params.suspect, params.use, params.clue, params.place):
        raise StoryError(explain_rejection(params.suspect, params.use, params.clue, params.place))

    world = tell(
        recipe=RECIPES[params.recipe],
        suspect_cfg=SUSPECTS[params.suspect],
        use=USES[params.use],
        clue=CLUES[params.clue],
        place=PLACES[params.place],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_type=params.helper_type,
        trait=params.trait,
    )

    story = world.render().replace("the child", params.hero_name, 1)
    if params.recipe == "cloud_kisses":
        story = story.replace("The cloud-kiss cookies came out light as little moons, and the child could hardly wait to share them.", f"The cloud-kiss cookies came out light as little moons, and {params.hero_name} could hardly wait to share them.")

    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (recipe, suspect, use, clue, place) combos:\n")
        for recipe_id, suspect_id, use_id, clue_id, place_id in combos:
            print(f"  {recipe_id:14} {suspect_id:12} {use_id:14} {clue_id:12} {place_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.recipe}, suspect {p.suspect}, {outcome_of(p)} detective"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
