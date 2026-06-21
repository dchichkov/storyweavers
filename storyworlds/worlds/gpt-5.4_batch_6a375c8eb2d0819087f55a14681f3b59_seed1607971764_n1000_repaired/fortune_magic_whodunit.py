#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py
====================================================

A standalone story world about a little magic mystery: a child magician is about
to give a gentle fortune show when an important prop disappears. A friend plays
detective, follows a real clue through a magical place, and solves the whodunit.

The world is constraint-checked. Not every culprit would steal every object, and
not every recovery method makes sense for every magical creature. The story only
generates combinations where:
- the missing item is genuinely tempting to the culprit, and
- the chosen method can honestly coax that culprit to give it back.

Run it
------
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --venue tent --item fortune_cards
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --culprit magpie --item moon_ribbon
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --method jingle_ball   # rejected for some culprits
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/fortune_magic_whodunit.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Venue:
    id: str
    place: str
    scene: str
    hideouts: dict[str, str]
    difficulty: int = 1
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
    use: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Culprit:
    id: str
    label: str
    kind: str
    clue: str
    clue_object: str
    likes: set[str]
    stealth: int
    suspect_line: str
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
    works_for: set[str]
    action: str
    qa_action: str
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
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


def _r_missing(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    magician = world.get("magician")
    room = world.get("venue")
    if item.meters["missing"] >= THRESHOLD:
        sig = ("missing",)
        if sig not in world.fired:
            world.fired.add(sig)
            magician.memes["worry"] += 1
            room.meters["show_risk"] += 1
    return out


def _r_clue(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    detective = world.get("detective")
    culprit = world.get("culprit")
    if clue.meters["seen"] >= THRESHOLD:
        sig = ("clue_seen", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["curiosity"] += 1
            detective.memes["certainty"] += 1
    return out


def _r_recovered(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    magician = world.get("magician")
    detective = world.get("detective")
    venue = world.get("venue")
    if item.meters["found"] >= THRESHOLD:
        sig = ("found",)
        if sig not in world.fired:
            world.fired.add(sig)
            magician.memes["relief"] += 1
            detective.memes["pride"] += 1
            magician.memes["worry"] = 0.0
            venue.meters["show_risk"] = 0.0
    return out


CAUSAL_RULES = [
    Rule(name="missing", tag="physical", apply=_r_missing),
    Rule(name="clue", tag="social", apply=_r_clue),
    Rule(name="recovered", tag="physical", apply=_r_recovered),
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


def item_tempts(culprit: Culprit, item: MissingItem) -> bool:
    return bool(culprit.likes & item.tags)


def method_fits(culprit: Culprit, method: Method) -> bool:
    return culprit.id in method.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue_id in VENUES:
        for item_id, item in ITEMS.items():
            for culprit_id, culprit in CULPRITS.items():
                for method_id, method in METHODS.items():
                    if item_tempts(culprit, item) and method_fits(culprit, method):
                        combos.append((venue_id, item_id, culprit_id, method_id))
    return combos


OBSERVANT_TRAITS = {"keen", "observant", "patient"}
QUICK_SOLVE_MIN = 3


def trait_bonus(trait: str) -> int:
    return 2 if trait in OBSERVANT_TRAITS else 1


def investigation_score(venue: Venue, culprit: Culprit, trait: str) -> int:
    clue_strength = 2
    return clue_strength + trait_bonus(trait) - venue.difficulty - culprit.stealth


def outcome_of(params: "StoryParams") -> str:
    venue = VENUES[params.venue]
    culprit = CULPRITS[params.culprit]
    score = investigation_score(venue, culprit, params.helper_trait)
    return "quick_solve" if score >= 0 else "late_solve"


def predict_solution(world: World, trait: str) -> dict:
    sim = world.copy()
    culprit = sim.get("culprit")
    venue = VENUES[sim.facts["venue_cfg"].id]
    score = investigation_score(venue, CULPRITS[culprit.id], trait)
    return {"quick": score >= 0, "score": score}


def introduce(world: World, magician: Entity, detective: Entity, adult: Entity,
              venue: Venue, item: MissingItem) -> None:
    magician.memes["joy"] += 1
    detective.memes["joy"] += 1
    world.say(
        f"At {venue.place}, {magician.id} had built a tiny magic booth with velvet cloth, "
        f"paper stars, and a sign that promised a kind fortune for every guest."
    )
    world.say(
        f"{venue.scene} {detective.id} straightened the lantern cards while "
        f"{adult.label_word} set out tea-cup candles that glowed without any flame."
    )
    world.say(
        f"The most important prop was {item.phrase}, because {magician.id} used it {item.use}."
    )


def vanish(world: World, magician: Entity, item: MissingItem) -> None:
    ent = world.get("item")
    ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when {magician.id} turned back to the table, {item.the} was gone."
    )
    world.say(
        f'"My show cannot begin without it," {magician.id} whispered, and the little mystery began at once.'
    )


def suspect_and_clue(world: World, detective: Entity, culprit: Culprit, venue: Venue) -> None:
    clue_ent = world.get("clue")
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} narrowed {detective.pronoun("possessive")} eyes. '
        f'"Someone took it on purpose," {detective.pronoun()} said.'
    )
    world.say(culprit.suspect_line)
    world.say(
        f"Then {detective.pronoun()} spotted {culprit.clue} leading toward {venue.hideouts[culprit.id]}."
    )


def investigate(world: World, magician: Entity, detective: Entity, adult: Entity,
                culprit: Culprit, method: Method, venue: Venue, quick: bool) -> None:
    detective.memes["focus"] += 1
    pred = predict_solution(world, world.facts["helper_trait"])
    world.facts["predicted_score"] = pred["score"]
    if quick:
        world.say(
            f'{detective.id} did not chase every silly guess. "{culprit.clue_object.capitalize()} means only one thing," '
            f'{detective.pronoun()} said, and hurried toward {venue.hideouts[culprit.id]}.'
        )
    else:
        world.say(
            f"They checked two wrong corners first: under the table cloth and behind the trick mirror. "
            f"Nothing was there except dust and one lost marble."
        )
        world.say(
            f"Only then did {detective.id} remember {culprit.clue_object} and lead everyone toward "
            f"{venue.hideouts[culprit.id]}."
        )
    adult.memes["calm"] += 1
    world.say(
        f"There they found {culprit.label} with {world.facts['item_cfg'].the} tucked close."
    )
    world.say(
        f"{adult.label_word.capitalize()} stayed calm and used {method.label}: {method.action}."
    )


def recover(world: World, magician: Entity, detective: Entity, culprit: Culprit,
            item: MissingItem, quick: bool) -> None:
    item_ent = world.get("item")
    culprit_ent = world.get("culprit")
    item_ent.meters["found"] += 1
    culprit_ent.memes["mischief"] = 0.0
    culprit_ent.memes["content"] += 1
    propagate(world, narrate=False)
    if culprit.id == "magpie":
        why = "It had wanted the glitter."
    elif culprit.id == "kitten":
        why = "It had wanted something soft and fluttery to pounce on."
    else:
        why = "It had loved the tickly rush of paper and sparkle."
    world.say(
        f"The little thief let go at once. {why}"
    )
    if quick:
        world.say(
            f"{magician.id} hugged the prop to {magician.pronoun('possessive')} chest, and the mystery was solved before the first guests reached the booth."
        )
    else:
        world.say(
            f"By then a few guests were already waiting, but they smiled when {magician.id} lifted the prop high and called, "
            f'"Mystery solved!"'
        )
    world.say(
        f"Soon the fortune show began after all, and every listener left with a bright prediction and a softer voice."
    )


def ending_image(world: World, magician: Entity, detective: Entity, adult: Entity,
                 item: MissingItem, outcome: str) -> None:
    magician.memes["gratitude"] += 1
    detective.memes["joy"] += 1
    adult.memes["love"] += 1
    if outcome == "quick_solve":
        world.say(
            f"At the end, {detective.id} sat beside the booth wearing a paper detective badge, while {magician.id} traced a shining circle in the air with {item.the} and promised one extra fortune for the best helper."
        )
    else:
        world.say(
            f"At the end, the candles were burning low, but the booth still glimmered. {detective.id} kept the paper detective badge, and {magician.id} laughed every time a guest asked to hear the story of the solved mystery one more time."
        )


def tell(venue: Venue, item: MissingItem, culprit: Culprit, method: Method,
         magician_name: str = "Mira", magician_gender: str = "girl",
         detective_name: str = "Theo", detective_gender: str = "boy",
         helper_trait: str = "observant", adult_type: str = "mother") -> World:
    world = World(venue)
    magician = world.add(Entity(
        id=magician_name,
        kind="character",
        type=magician_gender,
        role="magician",
        traits=["creative"],
        attrs={},
    ))
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=[helper_trait],
        attrs={},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        role="adult",
        label="the adult",
        attrs={},
    ))
    venue_ent = world.add(Entity(
        id="venue",
        type="place",
        label=venue.place,
        attrs={"difficulty": venue.difficulty},
    ))
    item_ent = world.add(Entity(
        id="item",
        type="prop",
        label=item.label,
        attrs={"tags": sorted(item.tags)},
    ))
    culprit_ent = world.add(Entity(
        id="culprit",
        type=culprit.kind,
        label=culprit.label,
        attrs={"actual": True},
    ))
    clue_ent = world.add(Entity(
        id="clue",
        type="clue",
        label=culprit.clue_object,
        attrs={},
    ))

    item_ent.meters["missing"] = 0.0
    item_ent.meters["found"] = 0.0
    culprit_ent.memes["mischief"] = 1.0
    clue_ent.meters["seen"] = 0.0
    magician.memes["worry"] = 0.0
    detective.memes["certainty"] = 0.0
    venue_ent.meters["show_risk"] = 0.0

    world.facts.update(
        venue_cfg=venue,
        item_cfg=item,
        culprit_cfg=culprit,
        method_cfg=method,
        helper_trait=helper_trait,
        magician=magician,
        detective=detective,
        adult=adult,
    )

    introduce(world, magician, detective, adult, venue, item)
    world.para()
    vanish(world, magician, item)
    suspect_and_clue(world, detective, culprit, venue)

    world.para()
    outcome = "quick_solve" if predict_solution(world, helper_trait)["quick"] else "late_solve"
    investigate(world, magician, detective, adult, culprit, method, venue, outcome == "quick_solve")
    recover(world, magician, detective, culprit, item, outcome == "quick_solve")

    world.para()
    ending_image(world, magician, detective, adult, item, outcome)

    world.facts.update(
        outcome=outcome,
        clue_text=culprit.clue,
        hideout=venue.hideouts[culprit.id],
        method_text=method.qa_action,
        item_found=item_ent.meters["found"] >= THRESHOLD,
    )
    return world


VENUES = {
    "tent": Venue(
        id="tent",
        place="the moonfair tent",
        scene="Around them, ribbons of harmless magic floated like sleepy fish.",
        hideouts={
            "magpie": "the high crossbeam above the curtain",
            "kitten": "the costume basket behind the stage screen",
            "wind_sprite": "the cluster of silver lanterns near the flap",
        },
        difficulty=1,
        tags={"fair", "magic"},
    ),
    "library": Venue(
        id="library",
        place="the enchanted library nook",
        scene="Around them, whispering books blinked tiny stars along their spines.",
        hideouts={
            "magpie": "the window ledge above the map shelf",
            "kitten": "the blanket basket by the reading chair",
            "wind_sprite": "the turning mobile of paper moons",
        },
        difficulty=0,
        tags={"library", "magic"},
    ),
    "garden": Venue(
        id="garden",
        place="the twilight garden stage",
        scene="Around them, glowing moth-lights drifted between rose arches.",
        hideouts={
            "magpie": "the pear tree branch over the stage",
            "kitten": "the bench piled with velvet capes",
            "wind_sprite": "the misty fountain rim",
        },
        difficulty=2,
        tags={"garden", "magic"},
    ),
}

ITEMS = {
    "fortune_charm": MissingItem(
        id="fortune_charm",
        label="fortune charm",
        phrase="a silver fortune charm shaped like a star",
        use="to tap each tiny card before reading it aloud",
        tags={"shiny", "metal", "fortune"},
    ),
    "crystal_pendulum": MissingItem(
        id="crystal_pendulum",
        label="crystal pendulum",
        phrase="a crystal pendulum on a moon-thread chain",
        use="to swing over the table and choose the next lucky message",
        tags={"shiny", "crystal", "fortune"},
    ),
    "moon_ribbon": MissingItem(
        id="moon_ribbon",
        label="moon ribbon",
        phrase="a moon ribbon sewn with silver bells",
        use="to tie back the velvet curtain before every show",
        tags={"fabric", "fluttery"},
    ),
    "fortune_cards": MissingItem(
        id="fortune_cards",
        label="fortune cards",
        phrase="a fan of painted fortune cards",
        use="to let guests pick their own magical future",
        tags={"paper", "light", "fortune"},
    ),
}

CULPRITS = {
    "magpie": Culprit(
        id="magpie",
        label="a glossy magpie",
        kind="bird",
        clue="one black feather and a blink of stolen glitter",
        clue_object="a black feather",
        likes={"shiny", "metal", "crystal"},
        stealth=1,
        suspect_line="Was it the rabbit puppet? Was it the broom? No. A thief that loved sparkle had passed this way.",
        tags={"bird", "shiny"},
    ),
    "kitten": Culprit(
        id="kitten",
        label="a soot-gray kitten",
        kind="cat",
        clue="tiny paw prints and one snagged silver thread",
        clue_object="tiny paw prints",
        likes={"fabric", "fluttery"},
        stealth=0,
        suspect_line="A broom would not leave paw prints, and a rabbit puppet would not hide under cloth. This smelled like kitten trouble.",
        tags={"cat", "pet"},
    ),
    "wind_sprite": Culprit(
        id="wind_sprite",
        label="a wind sprite no bigger than a teacup",
        kind="sprite",
        clue="a cold twirl of blue sparkles among the dust",
        clue_object="blue sparkles",
        likes={"paper", "light", "fortune"},
        stealth=2,
        suspect_line="Nothing with paws could make the air shiver like that. Something magical and breezy was nearby.",
        tags={"sprite", "magic", "air"},
    ),
}

METHODS = {
    "trade_shiny": Method(
        id="trade_shiny",
        label="a polished brass button",
        works_for={"magpie"},
        action="Dad held out a polished brass button, brighter than a new coin, and the bird hopped over to trade",
        qa_action="used a polished brass button to tempt the magpie into trading",
        tags={"trade", "shiny"},
    ),
    "jingle_ball": Method(
        id="jingle_ball",
        label="a jingle ball",
        works_for={"kitten"},
        action="Mom rolled a jingle ball across the floor, and the kitten pounced after it instead",
        qa_action="rolled a jingle ball so the kitten chased that instead of the missing prop",
        tags={"toy", "kitten"},
    ),
    "humming_jar": Method(
        id="humming_jar",
        label="a humming jar",
        works_for={"wind_sprite"},
        action="Dad uncorked a humming jar that sang a soft note, and the sprite drifted close to listen",
        qa_action="opened a humming jar whose soft song drew the wind sprite close",
        tags={"jar", "magic"},
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Ava", "Elsie", "June", "Tess", "Pia"]
BOY_NAMES = ["Theo", "Milo", "Owen", "Finn", "Jude", "Arlo", "Bram", "Leo"]
TRAITS = ["keen", "observant", "patient", "curious", "thoughtful", "careful"]


@dataclass
class StoryParams:
    venue: str
    item: str
    culprit: str
    method: str
    magician_name: str
    magician_gender: str
    detective_name: str
    detective_gender: str
    helper_trait: str
    adult: str
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
    "fortune": [
        (
            "What is a fortune in a story like this?",
            "A fortune is a little guess or prediction about what might happen later. In gentle stories, it is usually playful and kind, not scary."
        )
    ],
    "magpie": [
        (
            "Why might a magpie take a shiny thing?",
            "Magpies are birds that often notice glittering objects. A shiny trinket can catch their eye the way a bright toy catches yours."
        )
    ],
    "kitten": [
        (
            "Why do kittens chase ribbons and bells?",
            "Kittens love things that flutter, roll, or jingle because those motions wake up their play instincts. They often pounce first and think later."
        )
    ],
    "wind_sprite": [
        (
            "What is a wind sprite in a magic story?",
            "A wind sprite is a tiny make-believe creature made of breeze and sparkle. It likes light things that flutter and spin in the air."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. In a whodunit, clues help you learn who did it and where they went."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks closely, asks good questions, and follows clues. The best detectives stay calm instead of making wild guesses."
        )
    ],
    "magic": [
        (
            "What kind of magic is in this story?",
            "It is cozy story magic: glowing lights, tiny sprites, and gentle tricks that make the place feel wondrous. The magic is there to create mystery, not danger."
        )
    ],
}
KNOWLEDGE_ORDER = ["fortune", "clue", "detective", "magpie", "kitten", "wind_sprite", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    venue = f["venue_cfg"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    magician = f["magician"]
    detective = f["detective"]
    return [
        f'Write a short whodunit for a 3-to-5-year-old set in {venue.place} that includes the word "fortune" and a gentle touch of magic.',
        f"Tell a child-friendly mystery where {magician.id} loses {item.the} before a magic show and {detective.id} follows a clue to discover that {culprit.label} took it.",
        f"Write a cozy magical detective story with a missing prop, one real clue, and an ending where the show can begin after the mystery is solved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    magician = f["magician"]
    detective = f["detective"]
    adult = f["adult"]
    item = f["item_cfg"]
    culprit = f["culprit_cfg"]
    venue = f["venue_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {magician.id}, who was getting ready for a magic fortune show, and {detective.id}, who helped solve the mystery. {adult.label_word.capitalize()} stayed calm and helped them search."
        ),
        (
            f"What went missing before the show?",
            f"{item.the.capitalize()} went missing just as the show was about to begin. That mattered because {magician.id} used it {item.use}."
        ),
        (
            f"How did {detective.id} know where to look?",
            f"{detective.id} found {culprit.clue}. That clue pointed toward {venue.hideouts[culprit.id]}, so {detective.pronoun()} had a real reason to search there."
        ),
        (
            "Who took the missing prop?",
            f"{culprit.label.capitalize()} took it. The thief was drawn to the prop because it matched what that little creature likes best."
        ),
        (
            f"How did they get {item.the} back?",
            f"{adult.label_word.capitalize()} {method.qa_action}. That worked because it suited the creature who had taken the prop."
        ),
    ]
    if outcome == "quick_solve":
        qa.append(
            (
                "Did the show start on time?",
                f"Yes, almost. They solved the mystery before the first guests reached the booth, so the magic show could begin without much delay."
            )
        )
    else:
        qa.append(
            (
                "Was the mystery solved quickly?",
                f"Not at first. They checked a few wrong places before the clue finally led them to the right hiding spot, so the show started a little late."
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the missing prop safely back in {magician.id}'s hands and the fortune show beginning after all. The ending image shows that worry turned into relief and the mystery became a happy story to tell."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"fortune", "clue", "detective", "magic"}
    culprit = world.facts["culprit_cfg"].id
    tags.add(culprit)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v not in ([], {}, "", None)}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="library",
        item="fortune_cards",
        culprit="wind_sprite",
        method="humming_jar",
        magician_name="Mira",
        magician_gender="girl",
        detective_name="Theo",
        detective_gender="boy",
        helper_trait="keen",
        adult="father",
    ),
    StoryParams(
        venue="tent",
        item="fortune_charm",
        culprit="magpie",
        method="trade_shiny",
        magician_name="Lila",
        magician_gender="girl",
        detective_name="Milo",
        detective_gender="boy",
        helper_trait="observant",
        adult="mother",
    ),
    StoryParams(
        venue="garden",
        item="moon_ribbon",
        culprit="kitten",
        method="jingle_ball",
        magician_name="Nora",
        magician_gender="girl",
        detective_name="Finn",
        detective_gender="boy",
        helper_trait="curious",
        adult="mother",
    ),
    StoryParams(
        venue="garden",
        item="fortune_cards",
        culprit="wind_sprite",
        method="humming_jar",
        magician_name="June",
        magician_gender="girl",
        detective_name="Arlo",
        detective_gender="boy",
        helper_trait="careful",
        adult="father",
    ),
    StoryParams(
        venue="tent",
        item="crystal_pendulum",
        culprit="magpie",
        method="trade_shiny",
        magician_name="Pia",
        magician_gender="girl",
        detective_name="Leo",
        detective_gender="boy",
        helper_trait="patient",
        adult="mother",
    ),
]


def explain_item_culprit(item: MissingItem, culprit: Culprit) -> str:
    return (
        f"(No story: {culprit.label} would not be tempted by {item.the}. "
        f"This culprit follows {', '.join(sorted(culprit.likes))}, so choose a matching missing prop.)"
    )


def explain_method(culprit: Culprit, method: Method) -> str:
    good = ", ".join(sorted(m.id for m in METHODS.values() if culprit.id in m.works_for))
    return (
        f"(No story: {method.label} is not a sensible way to recover an item from {culprit.label}. "
        f"Try one of: {good}.)"
    )


ASP_RULES = r"""
clue_strength(2).

attracted(C, I) :- culprit(C), item(I), likes(C, T), item_tag(I, T).
usable(M, C) :- method(M), works_for(M, C).
valid(V, I, C, M) :- venue(V), item(I), culprit(C), method(M), attracted(C, I), usable(M, C).

trait_bonus(T, 2) :- trait(T), observant_trait(T).
trait_bonus(T, 1) :- trait(T), not observant_trait(T).

score(S) :- chosen_venue(V), difficulty(V, D),
            chosen_culprit(C), stealth(C, St),
            chosen_trait(T), trait_bonus(T, B),
            clue_strength(CS),
            S = CS + B - D - St.

outcome(quick_solve) :- score(S), S >= 0.
outcome(late_solve) :- score(S), S < 0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id, venue in VENUES.items():
        lines.append(asp.fact("venue", venue_id))
        lines.append(asp.fact("difficulty", venue_id, venue.difficulty))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("stealth", culprit_id, culprit.stealth))
        for tag in sorted(culprit.likes):
            lines.append(asp.fact("likes", culprit_id, tag))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        for culprit_id in sorted(method.works_for):
            lines.append(asp.fact("works_for", method_id, culprit_id))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(OBSERVANT_TRAITS):
        lines.append(asp.fact("observant_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_venue", params.venue),
            asp.fact("chosen_culprit", params.culprit),
            asp.fact("chosen_trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a magical fortune whodunit. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--magician-name")
    ap.add_argument("--detective-name")
    ap.add_argument("--magician-gender", choices=["girl", "boy"])
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.culprit:
        item = ITEMS[args.item]
        culprit = CULPRITS[args.culprit]
        if not item_tempts(culprit, item):
            raise StoryError(explain_item_culprit(item, culprit))
    if args.culprit and args.method:
        culprit = CULPRITS[args.culprit]
        method = METHODS[args.method]
        if not method_fits(culprit, method):
            raise StoryError(explain_method(culprit, method))

    combos = [
        c for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.item is None or c[1] == args.item)
        and (args.culprit is None or c[2] == args.culprit)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, item_id, culprit_id, method_id = rng.choice(sorted(combos))
    magician_gender = args.magician_gender or rng.choice(["girl", "boy"])
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    magician_name = args.magician_name or _pick_name(rng, magician_gender)
    detective_name = args.detective_name or _pick_name(rng, detective_gender, avoid=magician_name)
    helper_trait = rng.choice(TRAITS)
    adult = args.adult or rng.choice(["mother", "father"])
    return StoryParams(
        venue=venue_id,
        item=item_id,
        culprit=culprit_id,
        method=method_id,
        magician_name=magician_name,
        magician_gender=magician_gender,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_trait=helper_trait,
        adult=adult,
    )


def generate(params: StoryParams) -> StorySample:
    if params.venue not in VENUES:
        raise StoryError(f"(Unknown venue: {params.venue})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Unknown culprit: {params.culprit})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    venue = VENUES[params.venue]
    item = ITEMS[params.item]
    culprit = CULPRITS[params.culprit]
    method = METHODS[params.method]

    if not item_tempts(culprit, item):
        raise StoryError(explain_item_culprit(item, culprit))
    if not method_fits(culprit, method):
        raise StoryError(explain_method(culprit, method))

    world = tell(
        venue=venue,
        item=item,
        culprit=culprit,
        method=method,
        magician_name=params.magician_name,
        magician_gender=params.magician_gender,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_trait=params.helper_trait,
        adult_type=params.adult,
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

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
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

    smoke_params = CURATED[0]
    try:
        sample = generate(smoke_params)
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=False, qa=False, header="")
        if not sample.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, culprit, method) combos:\n")
        for venue, item, culprit, method in combos:
            print(f"  {venue:8} {item:17} {culprit:12} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
                f"### {p.magician_name} & {p.detective_name}: {p.item} at {p.venue} "
                f"({p.culprit}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
