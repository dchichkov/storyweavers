#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py
=========================================================================================

A standalone story world for a tiny detective-style mystery at a cliff lookout.

Seed requirements
-----------------
- Uses the words: barbaric, breather, excrement
- Setting: cliff lookout
- Features: Inner Monologue, Reconciliation
- Style: Detective Story

World premise
-------------
A child at a cliff lookout finds a nasty mess and jumps to the wrong conclusion.
The child's detective-like inner monologue follows physical clues in the world:
splatter, feathers, hoofprints, fish smell, and who was carrying what. The turn
comes when a more careful clue reveals the mess was animal excrement, not a rude
human act. The ending reconciles the child with the person they wrongly suspected.

Reasonableness constraint
-------------------------
Not every suspect/animal/location/clue combination makes sense. The world only
generates cases where:
- the animal can actually reach the messy spot,
- the suspect is plausibly present there,
- the surface carries the kind of misleading clue that could cause the mistaken
  accusation,
- and the world includes a stronger clue that can overturn the mistake.

Run it
------
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py --animal gull --spot bench
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py --suspect painter --spot steps
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py --qa --json
    python storyworlds/worlds/gpt-5.4/barbaric_breather_excrement_cliff_lookout_inner_monologue.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "painter_woman"}
        male = {"boy", "father", "man", "groundskeeper_man", "fisher_man"}
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


@dataclass
class Spot:
    id: str
    label: str
    phrase: str
    surface: str
    reachable_by: set[str] = field(default_factory=set)
    misleading_clues: set[str] = field(default_factory=set)
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
class Animal:
    id: str
    label: str
    kind_word: str
    trace: str
    sign: str
    smell: str
    real_clue: str
    reaches: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    label: str
    type: str
    carried_item: str
    misleading_clue: str
    tidy_reply: str
    apology_reply: str
    helper_action: str
    present_at: set[str] = field(default_factory=set)
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
class Reconcile:
    id: str
    action: str
    ending: str
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
        new = World()
        new.entities = copy.deepcopy(self.entities)
        new.fired = set(self.fired)
        new.paragraphs = [[]]
        new.facts = copy.deepcopy(self.facts)
        return new


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


def _r_mistake_hurts(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["blamed"] < THRESHOLD:
        return out
    sig = ("mistake_hurts", suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    detective.memes["guilt"] += 1
    out.append("__hurt__")
    return out


def _r_truth_relieves(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.meters["truth_found"] < THRESHOLD:
        return out
    sig = ("truth_relieves", suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["relief"] += 1
    suspect.memes["relief"] += 1
    out.append("__relief__")
    return out


def _r_reconcile_clears(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.memes["apologized"] < THRESHOLD:
        return out
    sig = ("reconcile_clears", suspect.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["friendship"] += 1
    suspect.memes["friendship"] += 1
    detective.memes["guilt"] = 0.0
    suspect.memes["hurt"] = 0.0
    out.append("__reconciled__")
    return out


CAUSAL_RULES = [
    Rule(name="mistake_hurts", tag="social", apply=_r_mistake_hurts),
    Rule(name="truth_relieves", tag="social", apply=_r_truth_relieves),
    Rule(name="reconcile_clears", tag="social", apply=_r_reconcile_clears),
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


def animal_reaches_spot(animal: Animal, spot: Spot) -> bool:
    return spot.id in animal.reaches and animal.id in spot.reachable_by


def suspect_present(suspect: Suspect, spot: Spot) -> bool:
    return spot.id in suspect.present_at


def misleading_fit(suspect: Suspect, spot: Spot) -> bool:
    return suspect.misleading_clue in spot.misleading_clues


def valid_case(animal: Animal, suspect: Suspect, spot: Spot) -> bool:
    return animal_reaches_spot(animal, spot) and suspect_present(suspect, spot) and misleading_fit(suspect, spot)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id, animal in ANIMALS.items():
        for suspect_id, suspect in SUSPECTS.items():
            for spot_id, spot in SPOTS.items():
                if valid_case(animal, suspect, spot):
                    combos.append((animal_id, suspect_id, spot_id))
    return combos


def explain_rejection(animal: Animal, suspect: Suspect, spot: Spot) -> str:
    if not animal_reaches_spot(animal, spot):
        return (
            f"(No story: a {animal.label} would not reasonably leave a mess on {spot.phrase}. "
            f"That animal cannot reach that spot at this cliff lookout.)"
        )
    if not suspect_present(suspect, spot):
        return (
            f"(No story: {suspect.label} is not a plausible suspect for {spot.phrase}. "
            f"This person would not normally be there in time to be blamed.)"
        )
    if not misleading_fit(suspect, spot):
        return (
            f"(No story: {suspect.label}'s {suspect.carried_item} would not leave the kind of clue "
            f"seen on {spot.phrase}, so the mistaken accusation would feel unfair and ungrounded.)"
        )
    return "(No story: this mystery setup is not reasonable.)"


def predict_mistake(world: World) -> dict:
    sim = world.copy()
    detective = sim.get("detective")
    suspect = sim.get("suspect")
    detective.memes["blamed"] += 1
    propagate(sim, narrate=False)
    return {
        "hurt": suspect.memes["hurt"] >= THRESHOLD,
        "guilt": detective.memes["guilt"],
    }


def introduce(world: World, detective: Entity, pal: Entity, guardian: Entity, spot: Spot) -> None:
    detective.memes["curiosity"] += 1
    pal.memes["calm"] += 1
    world.say(
        f"By late afternoon, {detective.id}, {pal.id}, and {detective.pronoun('possessive')} "
        f"{guardian.label_word} stood at the cliff lookout where the sea kept thumping the rocks below."
    )
    world.say(
        f"{detective.id} loved pretending to be a detective, especially in places that felt full of windy secrets."
    )
    world.say(
        f"Then {detective.pronoun()} saw a smeared mess on {spot.phrase}, right across the {spot.surface}, and stopped short."
    )


def discover(world: World, detective: Entity, pal: Entity, spot: Spot) -> None:
    world.say(
        f'"That is a barbaric mess," {detective.id} whispered. "{spot.label.capitalize()} should not look like that."'
    )
    world.say(
        f"{pal.id} made a small face and leaned back from it. The salty air could not hide how unpleasant it looked."
    )


def inspect(world: World, detective: Entity, suspect: Entity, suspect_cfg: Suspect, animal_cfg: Animal, spot: Spot) -> None:
    detective.memes["suspicion"] += 1
    world.facts["first_guess"] = suspect_cfg.id
    world.say(
        f"Near the mess, {detective.id} noticed {suspect_cfg.misleading_clue} and also saw {suspect_cfg.label} nearby with {suspect_cfg.carried_item}."
    )
    world.say(
        f'{detective.id} thought, "A real detective starts with what is right in front of {detective.pronoun("object")}."'
    )
    world.say(
        f'{detective.id} thought again, "Maybe {suspect_cfg.label} did it. Maybe this was not an accident at all."'
    )


def accuse(world: World, detective: Entity, suspect: Entity, suspect_cfg: Suspect) -> None:
    pred = predict_mistake(world)
    world.facts["predicted_hurt"] = pred["hurt"]
    detective.memes["blamed"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} pointed toward the clue. "Did you make this mess?" {detective.pronoun()} asked. '
        f'"It looked like somebody did something rude on purpose."'
    )
    world.say(
        f'{suspect_cfg.label.capitalize()} blinked and answered, "{suspect_cfg.tidy_reply}"'
    )


def breather(world: World, guardian: Entity, detective: Entity, pal: Entity) -> None:
    detective.memes["uncertain"] += 1
    pal.memes["care"] += 1
    world.say(
        f'{guardian.label_word.capitalize()} rested a hand on {detective.id}\'s shoulder. "Take a breather," '
        f'{guardian.pronoun()} said softly. "Good detectives look twice."'
    )
    world.say(
        f"{pal.id} nodded. The case did not feel solved anymore."
    )


def truth_clue(world: World, detective: Entity, pal: Entity, animal_cfg: Animal, spot: Spot) -> None:
    detective.meters["truth_found"] += 1
    world.facts["real_clue"] = animal_cfg.real_clue
    propagate(world, narrate=False)
    world.say(
        f"When {detective.id} crouched lower, {detective.pronoun()} found {animal_cfg.real_clue} near {spot.phrase}."
    )
    world.say(
        f'{detective.id} thought, "Wait. Paint does not leave {animal_cfg.trace}. Boots do not leave {animal_cfg.sign}. '
        f'This is excrement from a {animal_cfg.kind_word}, not a person\'s nasty prank."'
    )
    world.say(
        f"The sharper clue changed the whole case in one breath."
    )


def explain_truth(world: World, guardian: Entity, animal_cfg: Animal, spot: Spot) -> None:
    world.say(
        f'{guardian.label_word.capitalize()} knelt beside the mark and said, "See the {animal_cfg.trace}? '
        f'That tells us a {animal_cfg.label} was here. The mess is animal excrement, and {spot.label} just ended up underneath."'
    )


def apology(world: World, detective: Entity, suspect: Entity, suspect_cfg: Suspect) -> None:
    detective.memes["apologized"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} felt hot in the cheeks. "I am sorry," {detective.pronoun()} said. '
        f'"I made a guess before I had the real clue."'
    )
    world.say(
        f'{suspect_cfg.label.capitalize()} gave a slower smile this time and said, "{suspect_cfg.apology_reply}"'
    )


def reconcile(world: World, detective: Entity, pal: Entity, suspect_cfg: Suspect, reconcile_cfg: Reconcile) -> None:
    world.say(
        f"To show there were no hard feelings, {suspect_cfg.label} {suspect_cfg.helper_action}."
    )
    world.say(
        reconcile_cfg.action
    )
    world.say(
        reconcile_cfg.ending
    )


def tell(
    spot: Spot,
    animal_cfg: Animal,
    suspect_cfg: Suspect,
    reconcile_cfg: Reconcile,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    pal_name: str = "Ben",
    pal_type: str = "boy",
    guardian_type: str = "mother",
) -> World:
    world = World()
    detective = world.add(Entity(id="detective", kind="character", type=detective_type, label=detective_name, role="detective"))
    pal = world.add(Entity(id="pal", kind="character", type=pal_type, label=pal_name, role="pal"))
    guardian = world.add(Entity(id="guardian", kind="character", type=guardian_type, label="the parent", role="guardian"))
    suspect = world.add(Entity(id="suspect", kind="character", type=suspect_cfg.type, label=suspect_cfg.label, role="suspect"))
    mess = world.add(Entity(id="mess", kind="thing", type="mess", label="mess", role="evidence"))
    lookout = world.add(Entity(id="lookout", kind="thing", type="place", label="cliff lookout"))
    animal = world.add(Entity(id="animal", kind="thing", type="animal", label=animal_cfg.label))

    detective.attrs["display_name"] = detective_name
    pal.attrs["display_name"] = pal_name
    guardian.attrs["setting"] = "cliff lookout"
    suspect.attrs["carried_item"] = suspect_cfg.carried_item
    mess.attrs["spot"] = spot.id
    mess.attrs["source"] = animal_cfg.id
    mess.meters["gross"] = 1.0
    lookout.meters["windy"] = 1.0
    animal.meters["nearby"] = 1.0
    detective.memes["confidence"] = 1.0
    pal.memes["trust"] = 1.0
    suspect.memes["patience"] = 1.0

    world.facts.update(
        spot=spot,
        animal_cfg=animal_cfg,
        suspect_cfg=suspect_cfg,
        reconcile_cfg=reconcile_cfg,
        detective=detective,
        pal=pal,
        guardian=guardian,
        suspect=suspect,
        outcome="unresolved",
        predicted_hurt=False,
        first_guess="",
        real_clue="",
    )

    introduce(world, detective, pal, guardian, spot)
    discover(world, detective, pal, spot)

    world.para()
    inspect(world, detective, suspect, suspect_cfg, animal_cfg, spot)
    accuse(world, detective, suspect, suspect_cfg)
    breather(world, guardian, detective, pal)

    world.para()
    truth_clue(world, detective, pal, animal_cfg, spot)
    explain_truth(world, guardian, animal_cfg, spot)
    apology(world, detective, suspect, suspect_cfg)

    world.para()
    reconcile(world, detective, pal, suspect_cfg, reconcile_cfg)

    world.facts["outcome"] = "reconciled"
    return world


SPOTS = {
    "bench": Spot(
        id="bench",
        label="bench",
        phrase="the wooden bench at the edge of the lookout",
        surface="slats",
        reachable_by={"gull", "cormorant"},
        misleading_clues={"white_paint", "fish_smear"},
        tags={"bench", "lookout"},
    ),
    "railing": Spot(
        id="railing",
        label="railing",
        phrase="the lookout railing above the drop",
        surface="top rail",
        reachable_by={"gull", "cormorant"},
        misleading_clues={"white_paint", "fish_smear"},
        tags={"railing", "lookout"},
    ),
    "steps": Spot(
        id="steps",
        label="steps",
        phrase="the stone steps leading up to the lookout",
        surface="top step",
        reachable_by={"goat"},
        misleading_clues={"muddy_prints", "wheel_grease"},
        tags={"steps", "lookout"},
    ),
}

ANIMALS = {
    "gull": Animal(
        id="gull",
        label="gull",
        kind_word="gull",
        trace="small white feathers caught in the splatter",
        sign="feathers",
        smell="sharp and salty",
        real_clue="small white feathers caught in the mess",
        reaches={"bench", "railing"},
        tags={"gull", "bird", "excrement"},
    ),
    "cormorant": Animal(
        id="cormorant",
        label="cormorant",
        kind_word="cormorant",
        trace="a dark feather and a strong fish smell",
        sign="dark feather",
        smell="fishy",
        real_clue="a dark feather and a strong fish smell",
        reaches={"bench", "railing"},
        tags={"cormorant", "bird", "fish", "excrement"},
    ),
    "goat": Animal(
        id="goat",
        label="goat",
        kind_word="goat",
        trace="tiny hoof marks and round pellets",
        sign="hoof marks",
        smell="earthy",
        real_clue="tiny hoof marks beside a line of round pellets",
        reaches={"steps"},
        tags={"goat", "hoof", "excrement"},
    ),
}

SUSPECTS = {
    "painter": Suspect(
        id="painter",
        label="the painter",
        type="painter_woman",
        carried_item="a tin of white paint",
        misleading_clue="white_paint",
        tidy_reply="No, I was fixing the faded lookout sign. I would never leave a dirty surprise behind.",
        apology_reply="Thank you for saying so. A rushed guess can sting, but a careful apology helps.",
        helper_action="opened her bag and offered a rag and a bottle of water",
        present_at={"bench", "railing"},
        tags={"paint", "painter"},
    ),
    "fisher": Suspect(
        id="fisher",
        label="the fisher",
        type="fisher_man",
        carried_item="a bucket that smelled like fish",
        misleading_clue="fish_smear",
        tidy_reply="No, I only stopped to watch the tide before walking home. The fish smell came from my bucket, not from that mess.",
        apology_reply="That is all right. The sea leaves strong clues, and they can fool you if you hurry.",
        helper_action="set down his bucket far away and fetched a fresh newspaper to cover the mess",
        present_at={"bench", "railing"},
        tags={"fish", "fisher"},
    ),
    "groundskeeper": Suspect(
        id="groundskeeper",
        label="the groundskeeper",
        type="groundskeeper_man",
        carried_item="muddy work boots and a grease cart",
        misleading_clue="muddy_prints",
        tidy_reply="No, I was tightening the loose step. My boots are muddy, but I did not make that mess.",
        apology_reply="You were trying to solve it. Next time, solve it all the way.",
        helper_action="parked his little cart and brought a scoop and a bag",
        present_at={"steps"},
        tags={"boots", "groundskeeper"},
    ),
}

RECONCILES = {
    "shared_clean": Reconcile(
        id="shared_clean",
        action="Together they cleaned the spot while the wind pushed the last smell out toward the sea.",
        ending="When they were done, the cliff lookout looked calm again, and the case ended not with anger, but with everyone standing a little closer than before.",
        tags={"clean", "reconciliation"},
    ),
    "binocular_lesson": Reconcile(
        id="binocular_lesson",
        action="Afterward, the suspect let the children look through a pair of binoculars so they could spot birds before they landed again.",
        ending="From then on, the lookout felt less like a place of blame and more like a place where careful eyes could make peace.",
        tags={"binoculars", "reconciliation"},
    ),
    "note_of_apology": Reconcile(
        id="note_of_apology",
        action="Later, the children tucked a neat little sorry note under the cleaned railing, just for fun, as if closing a case file.",
        ending="The detective game still felt thrilling, but now the best part was knowing that being right mattered less than being fair.",
        tags={"note", "reconciliation"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mina", "Ava", "Zoe", "Tess"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam"]


@dataclass
class StoryParams:
    animal: str
    suspect: str
    spot: str
    reconcile: str
    detective_name: str
    detective_gender: str
    pal_name: str
    pal_gender: str
    guardian: str
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
    "gull": [(
        "Why do gulls leave messes on benches and rails?",
        "Gulls often perch on high places near the sea, like rails and benches. If a gull rests there, it can leave droppings underneath without meaning to be rude."
    )],
    "cormorant": [(
        "What is a cormorant?",
        "A cormorant is a dark seabird that dives for fish. Because it eats fish and rests near the shore, it can leave a strong fishy smell behind."
    )],
    "goat": [(
        "What clues can tell you a goat has been nearby?",
        "Goats can leave tiny hoof marks and little round droppings. Those clues help you tell an animal was there even if you do not see it anymore."
    )],
    "excrement": [(
        "What does excrement mean?",
        "Excrement is another word for poop or droppings. People use that word when they want to talk clearly about animal waste."
    )],
    "paint": [(
        "Why can white paint fool someone in a mystery?",
        "White paint can look like part of a splatter from far away. A detective has to come closer and check whether the clue is really paint or something else."
    )],
    "fish": [(
        "Why can a fish smell be a confusing clue?",
        "A fish smell can come from a bird, a bucket, or the sea itself. That is why one clue alone is not always enough to solve a case."
    )],
    "hoof": [(
        "What are hoof marks?",
        "Hoof marks are prints left by animals with hard feet, like goats. They look different from shoe prints and can help solve a mystery."
    )],
    "reconciliation": [(
        "What is reconciliation?",
        "Reconciliation means making peace after hurt feelings or a disagreement. It often starts when someone admits a mistake and the other person accepts the apology."
    )],
    "detective": [(
        "What does a good detective do before making a claim?",
        "A good detective checks more than one clue and stays calm. Looking twice can stop a wrong guess from hurting someone."
    )],
}
KNOWLEDGE_ORDER = ["detective", "gull", "cormorant", "goat", "excrement", "paint", "fish", "hoof", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    pal = f["pal"]
    suspect_cfg = f["suspect_cfg"]
    animal_cfg = f["animal_cfg"]
    spot = f["spot"]
    return [
        f'Write a short detective-style story for a 3-to-5-year-old set at a cliff lookout. Include the words "barbaric", "breather", and "excrement".',
        f"Tell a gentle mystery where {detective.label} wrongly suspects {suspect_cfg.label} after seeing a mess on {spot.phrase}, then follows a better clue and makes peace.",
        f"Write a story with inner monologue in which {detective.label} thinks like a detective, discovers the mess came from a {animal_cfg.label}, and ends in reconciliation with {pal.label} nearby.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    pal = f["pal"]
    guardian = f["guardian"]
    suspect_cfg = f["suspect_cfg"]
    animal_cfg = f["animal_cfg"]
    spot = f["spot"]
    suspect = f["suspect"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.label}, who wanted to solve a mystery at a cliff lookout, {pal.label}, and {detective.pronoun('possessive')} {guardian.label_word}. It also includes {suspect_cfg.label}, who was blamed before the real clue was found."
        ),
        (
            f"What was the mystery at the cliff lookout?",
            f"There was a nasty mess on {spot.phrase}, and at first it looked as if a person might have made it on purpose. That is why the scene felt like a detective case instead of an ordinary cleanup."
        ),
        (
            f"Why did {detective.label} suspect {suspect_cfg.label} at first?",
            f"{detective.label} saw {suspect_cfg.misleading_clue.replace('_', ' ')} near the mess and also noticed {suspect_cfg.label} carrying {suspect_cfg.carried_item}. Those first clues seemed to fit together, so the wrong guess felt possible for a moment."
        ),
        (
            "What clue solved the case?",
            f"The stronger clue was {f.get('real_clue')}. That showed the mess was animal excrement from a {animal_cfg.kind_word}, not something the suspect had done."
        ),
        (
            "Why did the grown-up tell the child to take a breather?",
            f"{guardian.label_word.capitalize()} could see the case had been rushed. Taking a breather helped {detective.label} slow down, look again, and notice the clue that had been missed."
        ),
    ]
    if f.get("predicted_hurt"):
        qa.append((
            f"How did the wrong accusation affect {suspect_cfg.label}?",
            f"It hurt {suspect_cfg.label}'s feelings, even though {suspect.pronoun()} stayed calm. A wrong accusation can sting because being blamed for a rude act feels unfair."
        ))
    qa.append((
        "How was the problem fixed in the end?",
        f"{detective.label} apologized after learning the truth, and {suspect_cfg.label} accepted the apology. Then they worked together so the scene ended in reconciliation instead of blame."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "excrement", "reconciliation"}
    tags |= set(f["animal_cfg"].tags)
    tags |= set(f["suspect_cfg"].tags)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:18}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        animal="gull",
        suspect="painter",
        spot="bench",
        reconcile="shared_clean",
        detective_name="Nora",
        detective_gender="girl",
        pal_name="Ben",
        pal_gender="boy",
        guardian="mother",
    ),
    StoryParams(
        animal="cormorant",
        suspect="fisher",
        spot="railing",
        reconcile="binocular_lesson",
        detective_name="Mina",
        detective_gender="girl",
        pal_name="Leo",
        pal_gender="boy",
        guardian="father",
    ),
    StoryParams(
        animal="goat",
        suspect="groundskeeper",
        spot="steps",
        reconcile="note_of_apology",
        detective_name="Ava",
        detective_gender="girl",
        pal_name="Sam",
        pal_gender="boy",
        guardian="mother",
    ),
]


ASP_RULES = r"""
% Registry-driven reasonableness gate.
valid_case(A, S, P) :- animal(A), suspect(S), spot(P),
                       reaches(A, P), reachable_by(P, A),
                       present_at(S, P), misfit(S, C), misleading(P, C).

% Outcome model.
first_guess_hurts(A, S, P) :- valid_case(A, S, P).
truth_found(A, S, P) :- valid_case(A, S, P).
outcome(reconciled) :- first_guess_hurts(A, S, P), truth_found(A, S, P).

% Per-scenario predicate for verify.
scenario_ok :- chosen_animal(A), chosen_suspect(S), chosen_spot(P), valid_case(A, S, P).
scenario_outcome(reconciled) :- scenario_ok.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for spot_id, spot in SPOTS.items():
        lines.append(asp.fact("spot", spot_id))
        for animal in sorted(spot.reachable_by):
            lines.append(asp.fact("reachable_by", spot_id, animal))
        for clue in sorted(spot.misleading_clues):
            lines.append(asp.fact("misleading", spot_id, clue))
    for animal_id, animal in ANIMALS.items():
        lines.append(asp.fact("animal", animal_id))
        for spot in sorted(animal.reaches):
            lines.append(asp.fact("reaches", animal_id, spot))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("misfit", suspect_id, suspect.misleading_clue))
        for spot in sorted(suspect.present_at):
            lines.append(asp.fact("present_at", suspect_id, spot))
    for rec_id in RECONCILES:
        lines.append(asp.fact("reconcile", rec_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid_case/3."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_suspect", params.suspect),
        asp.fact("chosen_spot", params.spot),
    ])
    model = asp.one_model(asp_program(scenario, "#show scenario_outcome/1."))
    rows = asp.atoms(model, "scenario_outcome")
    return rows[0][0] if rows else "?"


def outcome_of(params: StoryParams) -> str:
    animal = ANIMALS.get(params.animal)
    suspect = SUSPECTS.get(params.suspect)
    spot = SPOTS.get(params.spot)
    if not animal or not suspect or not spot:
        return "?"
    return "reconciled" if valid_case(animal, suspect, spot) else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(30):
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
        print(f"OK: ASP outcome matches Python on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during verify smoke test.")
        emit(sample, trace=False, qa=False, header="### verify smoke test")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:  # pragma: no cover - verify surface
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective-style cliff-lookout story world with inner monologue and reconciliation."
    )
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("--reconcile", choices=RECONCILES)
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--pal-name")
    ap.add_argument("--pal-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.animal and args.suspect and args.spot:
        animal = ANIMALS[args.animal]
        suspect = SUSPECTS[args.suspect]
        spot = SPOTS[args.spot]
        if not valid_case(animal, suspect, spot):
            raise StoryError(explain_rejection(animal, suspect, spot))

    combos = [
        c for c in valid_combos()
        if (args.animal is None or c[0] == args.animal)
        and (args.suspect is None or c[1] == args.suspect)
        and (args.spot is None or c[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, suspect_id, spot_id = rng.choice(sorted(combos))
    reconcile_id = args.reconcile or rng.choice(sorted(RECONCILES))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or _pick_name(rng, detective_gender)
    pal_gender = args.pal_gender or rng.choice(["girl", "boy"])
    pal_name = args.pal_name or _pick_name(rng, pal_gender, avoid=detective_name)
    guardian = args.guardian or rng.choice(["mother", "father"])

    return StoryParams(
        animal=animal_id,
        suspect=suspect_id,
        spot=spot_id,
        reconcile=reconcile_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        pal_name=pal_name,
        pal_gender=pal_gender,
        guardian=guardian,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal '{params.animal}'.)")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect '{params.suspect}'.)")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot '{params.spot}'.)")
    if params.reconcile not in RECONCILES:
        raise StoryError(f"(Unknown reconcile mode '{params.reconcile}'.)")

    animal_cfg = ANIMALS[params.animal]
    suspect_cfg = SUSPECTS[params.suspect]
    spot = SPOTS[params.spot]
    reconcile_cfg = RECONCILES[params.reconcile]

    if not valid_case(animal_cfg, suspect_cfg, spot):
        raise StoryError(explain_rejection(animal_cfg, suspect_cfg, spot))

    world = tell(
        spot=spot,
        animal_cfg=animal_cfg,
        suspect_cfg=suspect_cfg,
        reconcile_cfg=reconcile_cfg,
        detective_name=params.detective_name,
        detective_type=params.detective_gender,
        pal_name=params.pal_name,
        pal_type=params.pal_gender,
        guardian_type=params.guardian,
    )

    detective = world.facts["detective"]
    pal = world.facts["pal"]
    rendered = world.render()
    rendered = rendered.replace("detective", detective.label)
    rendered = rendered.replace("pal", pal.label)

    return StorySample(
        params=params,
        story=rendered,
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
        print(asp_program("", "#show valid_case/3.\n#show scenario_outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (animal, suspect, spot) mystery combos:\n")
        for animal, suspect, spot in combos:
            print(f"  {animal:10} {suspect:14} {spot}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.animal} / {p.suspect} at {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
