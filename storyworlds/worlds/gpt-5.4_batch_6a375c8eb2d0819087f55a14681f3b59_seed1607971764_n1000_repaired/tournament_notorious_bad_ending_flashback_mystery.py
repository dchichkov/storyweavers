#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py
================================================================================

A standalone story world for a child-facing mystery about a school tournament,
a missing team badge, a notorious suspect, and a flashback that may or may not
help in time.

Premise
-------
Two children reach the final round of a school tournament. Just then, the team
badge they need is missing. A notorious child nearby looks suspicious, but the
hero also remembers an earlier clue. If they trust the flashback and search the
right place in the right way, they can solve the mystery. If they accuse first,
time slips away and they lose the tournament, ending with a sad lesson about
jumping to conclusions.

Run it
------
    python storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py
    python storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py --all
    python storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py --qa
    python storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/tournament_notorious_bad_ending_flashback_mystery.py --verify
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
TIME_LIMIT = 3


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"              # "character" | "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    searchable: bool = False
    # world model axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "coach"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "coach": "coach"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain config
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
class Tournament:
    id: str
    label: str
    venue: str
    final_round: str
    prize: str
    atmosphere: str
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
class MissingItem:
    id: str
    label: str
    phrase: str
    purpose: str
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    prep: str
    search_with: set[str] = field(default_factory=set)
    searchable: bool = True
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
class Clue:
    id: str
    label: str
    memory_text: str
    points_to: str
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
    label: str
    verb: str
    success_text: str
    fail_text: str
    suits: set[str] = field(default_factory=set)
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
class Approach:
    id: str
    label: str
    accuse_first: bool = False
    time_cost: int = 0


# ---------------------------------------------------------------------------
# World state
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_false_accusation(world: World) -> list[str]:
    hero = world.get("hero")
    rival = world.get("rival")
    if hero.memes["accused"] < THRESHOLD:
        return []
    sig = ("false_accusation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["false_accusation"] = True
    rival.memes["hurt"] += 1
    hero.memes["guilt"] += 1
    world.get("clock").meters["time"] += 1
    return []


def _r_found_relief(world: World) -> list[str]:
    badge = world.get("badge")
    hero = world.get("hero")
    partner = world.get("partner")
    if badge.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["relief"] += 1
    partner.memes["relief"] += 1
    return []


def _r_late_loss(world: World) -> list[str]:
    clock = world.get("clock")
    if clock.meters["time"] < TIME_LIMIT:
        return []
    sig = ("late_loss",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["late"] = True
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="false_accusation", tag="social", apply=_r_false_accusation),
    Rule(name="found_relief", tag="emotional", apply=_r_found_relief),
    Rule(name="late_loss", tag="time", apply=_r_late_loss),
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
        for sent in produced:
            world.say(sent)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def clue_matches_place(clue: Clue, place: HidingPlace) -> bool:
    return clue.points_to == place.id


def method_suits_place(method: Method, place: HidingPlace) -> bool:
    return place.id in method.suits and method.id in place.search_with


def valid_combo(clue: Clue, place: HidingPlace, method: Method) -> bool:
    return clue_matches_place(clue, place) and method_suits_place(method, place)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for tid in TOURNAMENTS:
        for clue_id, clue in CLUES.items():
            for place_id, place in HIDING_PLACES.items():
                for method_id, method in METHODS.items():
                    if valid_combo(clue, place, method):
                        combos.append((tid, clue_id, place_id, method_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    bad = APPROACHES[params.approach].accuse_first
    return "bad_ending" if bad else "solved"


# ---------------------------------------------------------------------------
# Prediction / flashback
# ---------------------------------------------------------------------------
def flashback_prediction(world: World, clue_id: str, place_id: str, method_id: str) -> dict:
    sim = world.copy()
    clue = CLUES[clue_id]
    place = HIDING_PLACES[place_id]
    method = METHODS[method_id]
    if clue_matches_place(clue, place) and method_suits_place(method, place):
        sim.get("badge").meters["found"] += 1
        sim.get("badge").attrs["location"] = place.id
        propagate(sim, narrate=False)
    return {
        "would_find": sim.get("badge").meters["found"] >= THRESHOLD,
        "time_after": sim.get("clock").meters["time"],
    }


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def setup_tournament(world: World, hero: Entity, partner: Entity, rival: Entity,
                     coach: Entity, tournament: Tournament, item: MissingItem) -> None:
    hero.memes["hope"] += 1
    partner.memes["hope"] += 1
    world.say(
        f"By the time the school {tournament.label} reached its final round, the hallway outside "
        f"{tournament.venue} felt full of whispers. {tournament.atmosphere}"
    )
    world.say(
        f"{hero.id} and {partner.id} had made it all the way to {tournament.final_round}, "
        f"and they could almost picture {tournament.prize} if they did well."
    )
    world.say(
        f"They only needed {item.phrase} to step through the last door."
    )
    world.say(
        f"Nearby stood {rival.id}, the notorious child everyone watched during games, "
        f"and {coach.label_word} Maren was checking the clock."
    )


def discover_loss(world: World, hero: Entity, partner: Entity, item: MissingItem) -> None:
    badge = world.get("badge")
    badge.meters["missing"] = 1.0
    hero.memes["alarm"] += 1
    partner.memes["alarm"] += 1
    world.say(
        f"But when {hero.id} reached into {hero.pronoun('possessive')} pocket, "
        f"{item.the_phrase if hasattr(item, 'the_phrase') else item.phrase} was gone."
    )
    world.say(
        f'"Our {item.label} is missing," {partner.id} whispered. '
        f"The words felt heavy in the quiet hall."
    )


def suspicion(world: World, hero: Entity, partner: Entity, rival: Entity) -> None:
    hero.memes["suspicion"] += 1
    partner.memes["suspicion"] += 1
    world.say(
        f"At once both children looked at {rival.id}. {rival.id} had a notorious name for pranks, "
        f"and that old story tried to solve the mystery all by itself."
    )


def flashback(world: World, hero: Entity, clue: Clue, place: HidingPlace, method: Method) -> None:
    hero.memes["memory"] += 1
    pred = flashback_prediction(world, clue.id, place.id, method.id)
    world.facts["flashback_would_find"] = pred["would_find"]
    world.say(
        f"Then a flashback flickered through {hero.id}'s mind. Just after the last riddle, "
        f"{clue.memory_text}"
    )
    world.say(
        f"The memory was small, but it tugged at the mystery like a loose thread."
    )


def accuse_first(world: World, hero: Entity, partner: Entity, rival: Entity, coach: Entity) -> None:
    hero.memes["accused"] += 1
    world.get("clock").meters["time"] += APPROACHES["accuse"].time_cost
    propagate(world, narrate=False)
    world.say(
        f'"Did you take it?" {hero.id} blurted to {rival.id}.'
    )
    world.say(
        f"{rival.id}'s face went red. {rival.pronoun().capitalize()} turned out {rival.pronoun('possessive')} pockets, "
        f"showing only a pencil stub and a crumpled napkin."
    )
    world.say(
        f'Coach Maren stepped between them. "Mysteries need clues, not guesses," '
        f"{coach.pronoun()} said, but the clock had already marched on."
    )
    partner.memes["worry"] += 1


def search(world: World, hero: Entity, partner: Entity, item: MissingItem,
           place: HidingPlace, method: Method) -> None:
    world.get("clock").meters["time"] += 1
    place_ent = world.get("place")
    place_ent.meters["searched"] += 1
    hero.memes["focus"] += 1
    partner.memes["focus"] += 1
    world.say(
        f"Now they hurried {place.prep} and {method.verb}."
    )
    if method_suits_place(method, place):
        world.say(method.success_text.format(item=item.label, place=place.label))
    else:
        world.say(method.fail_text.format(item=item.label, place=place.label))


def recover_item(world: World, hero: Entity, partner: Entity, item: MissingItem,
                 place: HidingPlace, method: Method) -> None:
    badge = world.get("badge")
    badge.meters["found"] = 1.0
    badge.meters["missing"] = 0.0
    badge.attrs["location"] = place.id
    propagate(world, narrate=False)
    world.say(
        f"There, tucked {place.prep}, lay the {item.label}. "
        f"{partner.id} let out a tiny gasp, and {hero.id} knew the flashback had been right."
    )


def reach_final(world: World, hero: Entity, partner: Entity, tournament: Tournament) -> None:
    world.say(
        f"They dashed into {tournament.venue} just before the final clue was read. "
        f"The mystery was solved, and their hearts thumped with bright relief."
    )
    world.say(
        f"That day they did not win every round, but they stood tall all the same, "
        f"because they had trusted a real clue instead of a rumor."
    )


def miss_final(world: World, hero: Entity, partner: Entity, rival: Entity,
               tournament: Tournament) -> None:
    hero.memes["sadness"] += 1
    partner.memes["sadness"] += 1
    world.say(
        f"By the time they found the badge and ran to {tournament.venue}, the last bell had already rung."
    )
    world.say(
        f"The door was closed. Inside, another team answered the final question, and "
        f"{hero.id} and {partner.id} were out of the tournament."
    )
    if world.facts.get("false_accusation"):
        world.say(
            f"{rival.id} stood in the hallway twisting the crumpled napkin in {rival.pronoun('possessive')} hand. "
            f"The mystery was solved, but the hurt from the false guess stayed behind."
        )


def lesson_end(world: World, hero: Entity, partner: Entity, rival: Entity, coach: Entity,
               good: bool) -> None:
    if good:
        hero.memes["lesson"] += 1
        partner.memes["lesson"] += 1
        world.say(
            f'Later, Coach Maren smiled and said, "A careful memory can be a better key than a loud suspicion."'
        )
        world.say(
            f"{hero.id} tucked that lesson away like a secret note for the next mystery."
        )
    else:
        hero.memes["guilt"] += 1
        partner.memes["lesson"] += 1
        world.say(
            f'Coach Maren rested a hand on the wall and spoke softly. "Being notorious does not make someone guilty," '
            f"{coach.pronoun()} said."
        )
        world.say(
            f"{hero.id} whispered sorry to {rival.id}. {rival.id} nodded, but the sad ending of that day "
            f"stayed with them longer than any missing badge."
        )


# ---------------------------------------------------------------------------
# Tale assembly
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    tournament: str
    item: str = "badge"
    clue: str = "blue_thread"
    hiding_place: str = "curtain_fold"
    method: str = "feel_fold"
    approach: str = "remember"
    hero_name: str = "Nina"
    hero_type: str = "girl"
    partner_name: str = "Owen"
    partner_type: str = "boy"
    rival_name: str = "Rafe"
    rival_type: str = "boy"
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


def tell(tournament: Tournament, item: MissingItem, clue: Clue, place: HidingPlace,
         method: Method, approach: Approach, hero_name: str = "Nina",
         hero_type: str = "girl", partner_name: str = "Owen",
         partner_type: str = "boy", rival_name: str = "Rafe",
         rival_type: str = "boy", coach_type: str = "coach") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero",
                            traits=["careful", "curious"]))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_type, role="partner",
                               traits=["steady", "kind"]))
    rival = world.add(Entity(id=rival_name, kind="character", type=rival_type, role="rival",
                             traits=["notorious", "fidgety"]))
    coach = world.add(Entity(id="Maren", kind="character", type=coach_type, role="coach",
                             label="the coach"))
    badge = world.add(Entity(id="badge", kind="thing", type="badge", role="missing_item",
                             label=item.label, portable=True, attrs={"location": place.id}))
    place_ent = world.add(Entity(id="place", kind="thing", type="place", role="hiding_place",
                                 label=place.label, searchable=place.searchable))
    clock = world.add(Entity(id="clock", kind="thing", type="clock", role="clock", label="the clock"))

    world.facts.update(
        tournament=tournament,
        item=item,
        clue=clue,
        place=place,
        method=method,
        approach=approach,
        false_accusation=False,
        late=False,
    )

    setup_tournament(world, hero, partner, rival, coach, tournament, item)
    discover_loss(world, hero, partner, item)
    world.para()
    suspicion(world, hero, partner, rival)
    flashback(world, hero, clue, place, method)

    world.para()
    if approach.accuse_first:
        accuse_first(world, hero, partner, rival, coach)

    search(world, hero, partner, item, place, method)
    if valid_combo(clue, place, method):
        recover_item(world, hero, partner, item, place, method)
    propagate(world, narrate=False)

    world.para()
    if outcome_of(StoryParams(
        tournament=tournament.id,
        item=item.id,
        clue=clue.id,
        hiding_place=place.id,
        method=method.id,
        approach=approach.id,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
        rival_name=rival_name,
        rival_type=rival_type,
        seed=None,
    )) == "solved":
        reach_final(world, hero, partner, tournament)
        lesson_end(world, hero, partner, rival, coach, good=True)
        outcome = "solved"
    else:
        miss_final(world, hero, partner, rival, tournament)
        lesson_end(world, hero, partner, rival, coach, good=False)
        outcome = "bad_ending"

    world.facts.update(
        hero=hero,
        partner=partner,
        rival=rival,
        coach=coach,
        badge=badge,
        clock=clock,
        outcome=outcome,
        found=badge.meters["found"] >= THRESHOLD,
        final_time=clock.meters["time"],
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
TOURNAMENTS = {
    "riddle_cup": Tournament(
        id="riddle_cup",
        label="Riddle Cup tournament",
        venue="the music room",
        final_round="the moon-round of the tournament",
        prize="the silver owl ribbon",
        atmosphere="A paper banner rustled above the door, and every scrape of a chair sounded important.",
        tags={"tournament", "mystery"},
    ),
    "map_dash": Tournament(
        id="map_dash",
        label="Map Dash tournament",
        venue="the library",
        final_round="the map-table final",
        prize="the bright gold compass sticker",
        atmosphere="Sunlight from the high windows striped the floor like secret paths.",
        tags={"tournament", "mystery"},
    ),
    "code_circle": Tournament(
        id="code_circle",
        label="Code Circle tournament",
        venue="the art room",
        final_round="the final code board",
        prize="the blue ribbon with little stars",
        atmosphere="Even the paint jars seemed to wait in silence while teams listened for the next clue.",
        tags={"tournament", "mystery"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="team badge",
        phrase="the brass team badge",
        purpose="to enter the final round",
        tags={"badge", "tournament"},
    ),
}

HIDING_PLACES = {
    "curtain_fold": HidingPlace(
        id="curtain_fold",
        label="curtain fold",
        phrase="the fold of the stage curtain",
        prep="to the stage curtain and felt inside the thick fold",
        search_with={"feel_fold"},
        searchable=True,
        tags={"curtain"},
    ),
    "snack_box": HidingPlace(
        id="snack_box",
        label="snack box",
        phrase="the paper snack box",
        prep="to the refreshment table and lifted the paper snack box",
        search_with={"lift_box"},
        searchable=True,
        tags={"snack"},
    ),
    "umbrella_stand": HidingPlace(
        id="umbrella_stand",
        label="umbrella stand",
        phrase="the tall umbrella stand",
        prep="to the entrance and peered between the umbrellas in the stand",
        search_with={"part_umbrellas"},
        searchable=True,
        tags={"umbrella"},
    ),
}

CLUES = {
    "blue_thread": Clue(
        id="blue_thread",
        label="blue thread",
        memory_text="a bright blue thread had clung to the badge clip after it brushed the stage curtain",
        points_to="curtain_fold",
        tags={"thread", "flashback"},
    ),
    "cracker_crumbs": Clue(
        id="cracker_crumbs",
        label="cracker crumbs",
        memory_text="tiny cracker crumbs had dotted the bench where the snack box sat open",
        points_to="snack_box",
        tags={"crumbs", "flashback"},
    ),
    "rain_drop": Clue(
        id="rain_drop",
        label="rain drop",
        memory_text="one cold rain drop had landed on the badge while someone squeezed past the umbrella stand",
        points_to="umbrella_stand",
        tags={"rain", "flashback"},
    ),
}

METHODS = {
    "feel_fold": Method(
        id="feel_fold",
        label="feel inside the fold",
        verb="felt along the heavy cloth with careful fingers",
        success_text="At the very back of the cloth, {hero} fingers brushed metal. The {item} had slipped into the {place}.",
        fail_text="The cloth swung and sighed, but the {item} was not there in the {place}.",
        suits={"curtain_fold"},
        tags={"search"},
    ),
    "lift_box": Method(
        id="lift_box",
        label="lift the box",
        verb="lifted the box and looked underneath",
        success_text="Under the box, hidden by a napkin corner, gleamed the {item}. It had been resting by the {place}.",
        fail_text="They lifted and peered, but only crumbs waited by the {place}.",
        suits={"snack_box"},
        tags={"search"},
    ),
    "part_umbrellas": Method(
        id="part_umbrellas",
        label="part the umbrellas",
        verb="parted the umbrella handles and looked down into the stand",
        success_text="At the bottom of the stand, beside a wet leaf, sat the {item}. The {place} had swallowed it whole.",
        fail_text="The umbrellas clicked together again, and the {item} was nowhere in the {place}.",
        suits={"umbrella_stand"},
        tags={"search"},
    ),
    "peek_under_table": Method(
        id="peek_under_table",
        label="peek under a table",
        verb="peeked under the nearest table",
        success_text="They somehow found the {item} by the {place}.",
        fail_text="Dust bunnies blinked back, but the {item} was not by the {place}.",
        suits=set(),
        tags={"search"},
    ),
}

APPROACHES = {
    "remember": Approach(id="remember", label="trust the flashback", accuse_first=False, time_cost=0),
    "accuse": Approach(id="accuse", label="accuse the rival first", accuse_first=True, time_cost=2),
}

GIRL_NAMES = ["Nina", "Mira", "Tessa", "Lila", "Ruby", "Ivy", "Ada", "Nora"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Ben", "Theo", "Sam", "Finn", "Jude"]


# ---------------------------------------------------------------------------
# Per-world params
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        tournament="riddle_cup",
        item="badge",
        clue="blue_thread",
        hiding_place="curtain_fold",
        method="feel_fold",
        approach="remember",
        hero_name="Nina",
        hero_type="girl",
        partner_name="Owen",
        partner_type="boy",
        rival_name="Rafe",
        rival_type="boy",
    ),
    StoryParams(
        tournament="map_dash",
        item="badge",
        clue="cracker_crumbs",
        hiding_place="snack_box",
        method="lift_box",
        approach="remember",
        hero_name="Mira",
        hero_type="girl",
        partner_name="Theo",
        partner_type="boy",
        rival_name="Jude",
        rival_type="boy",
    ),
    StoryParams(
        tournament="code_circle",
        item="badge",
        clue="rain_drop",
        hiding_place="umbrella_stand",
        method="part_umbrellas",
        approach="accuse",
        hero_name="Ruby",
        hero_type="girl",
        partner_name="Eli",
        partner_type="boy",
        rival_name="Finn",
        rival_type="boy",
    ),
]


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "tournament": [
        (
            "What is a tournament?",
            "A tournament is a contest with rounds where people or teams try their best at the same game or challenge. The winners move on until the last round."
        )
    ],
    "notorious": [
        (
            "What does notorious mean?",
            "Notorious means a person is known for doing something bad or troublesome. It does not prove they did a new bad thing this time."
        )
    ],
    "flashback": [
        (
            "What is a flashback in a story?",
            "A flashback is when a story remembers something that happened earlier. That earlier moment can help explain a mystery or a choice in the present."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that points toward an answer. In a mystery, good clues help you find what really happened."
        )
    ],
    "accusation": [
        (
            "Why is it important not to accuse someone without proof?",
            "A guess can hurt someone's feelings and send you in the wrong direction. It is better to look for real clues first."
        )
    ],
    "memory": [
        (
            "How can memory help solve a mystery?",
            "A careful memory can bring back a detail you did not understand at first. Later, that detail can point to the right place to look."
        )
    ],
}
KNOWLEDGE_ORDER = ["tournament", "notorious", "flashback", "clue", "accusation", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    t = f["tournament"]
    clue = f["clue"]
    approach = f["approach"]
    outcome = f["outcome"]
    hero = f["hero"]
    partner = f["partner"]
    rival = f["rival"]
    base = (
        f'Write a short child-facing mystery story set during a school tournament. '
        f'Include the word "notorious" and use a flashback to help with the missing-item mystery.'
    )
    if outcome == "bad_ending":
        return [
            base,
            f"Tell a mystery where {hero.id} and {partner.id} lose the {t.label} after accusing the notorious {rival.id} too quickly, even though a flashback clue could have guided them sooner.",
            f'Write a gentle bad-ending mystery in which a missing team badge is found too late, teaching that a notorious reputation is not the same as proof.',
        ]
    return [
        base,
        f"Tell a mystery where {hero.id} remembers {clue.label} in a flashback and solves the final-round problem in the {t.label} without blaming the notorious child nearby.",
        f'Write a quiet school mystery that ends with children trusting a clue instead of a rumor during a tournament.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    partner = f["partner"]
    rival = f["rival"]
    t = f["tournament"]
    item = f["item"]
    clue = f["clue"]
    place = f["place"]
    approach = f["approach"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {partner.id}, two children in the {t.label}, and {rival.id}, the notorious child they first suspect."
        ),
        (
            f"Why did they need the {item.label}?",
            f"They needed it to enter the final round of the tournament. Without it, they could not step through the last door and keep competing."
        ),
        (
            "What was the mystery?",
            f"The mystery was that the {item.label} disappeared right before the final round. That made the children wonder whether it was stolen or only misplaced."
        ),
        (
            "What did the flashback help them remember?",
            f"The flashback brought back {clue.label} from earlier. That tiny detail pointed toward {place.phrase}, which gave the mystery a real clue instead of a guess."
        ),
    ]
    if approach.accuse_first:
        qa.append(
            (
                f"Why was accusing {rival.id} a mistake?",
                f"It was only a guess based on {rival.id}'s notorious reputation, not on proof. The false accusation hurt {rival.id}'s feelings and cost precious time in the tournament."
            )
        )
    else:
        qa.append(
            (
                "How did they solve the mystery?",
                f"They followed the remembered clue to {place.phrase} and searched in the right way. Because they trusted evidence, they found the {item.label} before the last bell."
            )
        )
    if outcome == "bad_ending":
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly because they found the {item.label} too late and were out of the tournament. They solved the mystery, but they also learned that a notorious name is not the same as guilt."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with the children reaching the final round in time. The ending shows they solved the mystery by trusting a careful flashback and a real clue."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tournament", "notorious", "flashback", "clue", "memory"}
    if world.facts.get("false_accusation"):
        tags.add("accusation")
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


# ---------------------------------------------------------------------------
# Trace / explanations
# ---------------------------------------------------------------------------
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(clue: Clue, place: HidingPlace, method: Method) -> str:
    if not clue_matches_place(clue, place):
        pointed = HIDING_PLACES[clue.points_to].label
        return (
            f"(No story: the clue '{clue.label}' points toward {pointed}, not {place.label}. "
            f"A mystery should follow a real clue, not a random hiding place.)"
        )
    if not method_suits_place(method, place):
        return (
            f"(No story: the method '{method.label}' does not make sense for {place.label}. "
            f"Pick a search method that actually suits that hiding place.)"
        )
    return "(No story: that clue, place, and method do not form a reasonable mystery.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
points(C, P) :- clue(C), place(P), clue_points(C, P).
works(M, P)  :- method(M), place(P), method_suits(M, P), place_accepts(P, M).
valid(T, C, P, M) :- tournament(T), points(C, P), works(M, P).

bad_ending :- chosen_approach(accuse).
solved     :- chosen_approach(remember).

outcome(bad_ending) :- bad_ending.
outcome(solved)     :- solved.

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in TOURNAMENTS:
        lines.append(asp.fact("tournament", tid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_points", cid, clue.points_to))
    for pid, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", pid))
        for mid in sorted(place.search_with):
            lines.append(asp.fact("place_accepts", pid, mid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for pid in sorted(method.suits):
            lines.append(asp.fact("method_suits", mid, pid))
    for aid in APPROACHES:
        lines.append(asp.fact("approach", aid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("chosen_approach", params.approach)
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a tournament mystery with a flashback clue and a possible bad ending."
    )
    ap.add_argument("--tournament", choices=TOURNAMENTS)
    ap.add_argument("--item", choices=ITEMS, default=None)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hiding-place", dest="hiding_place", choices=HIDING_PLACES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--approach", choices=APPROACHES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--partner-name")
    ap.add_argument("--partner-type", choices=["girl", "boy"])
    ap.add_argument("--rival-name")
    ap.add_argument("--rival-type", choices=["girl", "boy"])
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


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    item = args.item or "badge"

    if args.clue and args.hiding_place and args.method:
        clue = CLUES[args.clue]
        place = HIDING_PLACES[args.hiding_place]
        method = METHODS[args.method]
        if not valid_combo(clue, place, method):
            raise StoryError(explain_rejection(clue, place, method))

    combos = [
        combo for combo in valid_combos()
        if (args.tournament is None or combo[0] == args.tournament)
        and (args.clue is None or combo[1] == args.clue)
        and (args.hiding_place is None or combo[2] == args.hiding_place)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    tournament, clue_id, hiding_place, method = rng.choice(sorted(combos))
    approach = args.approach or rng.choice(sorted(APPROACHES.keys()))

    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    partner_type = args.partner_type or rng.choice(["girl", "boy"])
    rival_type = args.rival_type or rng.choice(["girl", "boy"])

    used: set[str] = set()
    hero_name = args.hero_name or _pick_name(rng, hero_type, used)
    used.add(hero_name)
    partner_name = args.partner_name or _pick_name(rng, partner_type, used)
    used.add(partner_name)
    rival_name = args.rival_name or _pick_name(rng, rival_type, used)

    return StoryParams(
        tournament=tournament,
        item=item,
        clue=clue_id,
        hiding_place=hiding_place,
        method=method,
        approach=approach,
        hero_name=hero_name,
        hero_type=hero_type,
        partner_name=partner_name,
        partner_type=partner_type,
        rival_name=rival_name,
        rival_type=rival_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        tournament = TOURNAMENTS[params.tournament]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        place = HIDING_PLACES[params.hiding_place]
        method = METHODS[params.method]
        approach = APPROACHES[params.approach]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if not valid_combo(clue, place, method):
        raise StoryError(explain_rejection(clue, place, method))

    world = tell(
        tournament=tournament,
        item=item,
        clue=clue,
        place=place,
        method=method,
        approach=approach,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        partner_name=params.partner_name,
        partner_type=params.partner_type,
        rival_name=params.rival_name,
        rival_type=params.rival_type,
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
        print(f"{len(combos)} compatible (tournament, clue, hiding_place, method) combos:\n")
        for tournament, clue, place, method in combos:
            print(f"  {tournament:12} {clue:14} {place:15} {method}")
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
            header = (
                f"### {p.hero_name} & {p.partner_name}: {p.tournament}, "
                f"{p.approach}, {outcome_of(p)}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
