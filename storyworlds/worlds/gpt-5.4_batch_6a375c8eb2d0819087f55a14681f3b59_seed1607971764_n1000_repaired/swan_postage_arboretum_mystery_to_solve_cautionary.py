#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py
=================================================================================

A standalone story world for a child-sized ghost-story mystery in an arboretum:
some important postage goes missing near a pond at dusk, a swan seems to glide
through the mist like a little ghost, and two children must solve the mystery
without doing anything unsafe.

The world models:
- typed entities with physical meters and emotional memes
- a cautionary choice about reaching near water
- a grounded mystery whose clues come from simulated state
- a problem-solving resolution using calm grown-up help and the right tool

Run it
------
    python storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py
    python storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py --area moon_pond --postage stamp_sheet
    python storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py --response hand_reach
    python storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py --all --qa
    python storyworlds/worlds/gpt-5.4/swan_postage_arboretum_mystery_to_solve_cautionary.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
NERVE_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "steady", "patient", "thoughtful"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    paper: bool = False
    floats: bool = False
    water_place: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man", "ranger_male"}
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
            "ranger_female": "ranger",
            "ranger_male": "ranger",
        }.get(self.type, self.type)
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
class Area:
    id: str
    place: str
    eerie: str
    bench: str
    water_name: str
    drifting: str
    clue_place: str
    risk: int
    severity: int
    has_water: bool = True
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
class Postage:
    id: str
    label: str
    phrase: str
    purpose: str
    drift_text: str
    recover_text: str
    paper: bool = True
    floats: bool = True
    plural: bool = False
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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"finder", "cautioner"}]

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
    item = world.get("postage")
    area = world.get("area")
    if item.meters["drifting"] >= THRESHOLD:
        sig = ("missing", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["missing"] += 1
            area.meters["mystery"] += 1
            for kid in world.kids():
                kid.memes["wonder"] += 1
            out.append("__missing__")
    return out


def _r_wet(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("postage")
    area = world.get("area")
    if item.meters["missing"] >= THRESHOLD and area.water_place:
        sig = ("wet", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            item.meters["wet"] += 1
            out.append("__wet__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("finder")
    area = world.get("area")
    if child.meters["leaning"] >= THRESHOLD and area.meters["edge_risk"] >= THRESHOLD:
        sig = ("fear", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__fear__")
    return out


CAUSAL_RULES = [
    Rule(name="missing", tag="physical", apply=_r_missing),
    Rule(name="wet", tag="physical", apply=_r_wet),
    Rule(name="fear", tag="emotional", apply=_r_fear),
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


AREAS = {
    "moon_pond": Area(
        id="moon_pond",
        place="the moon pond in the arboretum",
        eerie="Mist curled over the dark water until the pond looked like a silver mirror.",
        bench="an old green bench beside the map sign",
        water_name="the pond",
        drifting="a cool gust skimmed over the pond",
        clue_place="the wet stones by the reeds",
        risk=2,
        severity=2,
        has_water=True,
        tags={"arboretum", "pond", "water"},
    ),
    "willow_cove": Area(
        id="willow_cove",
        place="willow cove in the arboretum",
        eerie="Long willow branches brushed together with a hush that sounded almost like whispering.",
        bench="a curved bench under the willow tree",
        water_name="the cove",
        drifting="a small swirl of wind came sliding under the branches",
        clue_place="the muddy edge under the willow leaves",
        risk=2,
        severity=3,
        has_water=True,
        tags={"arboretum", "water", "willow"},
    ),
    "lily_walk": Area(
        id="lily_walk",
        place="lily walk in the arboretum",
        eerie="The lamps were coming on one by one, and every pale flower seemed to glow by itself.",
        bench="a stone seat near the little footbridge",
        water_name="the narrow canal",
        drifting="an evening breeze slipped along the canal",
        clue_place="the damp boards by the footbridge",
        risk=1,
        severity=1,
        has_water=True,
        tags={"arboretum", "canal", "water"},
    ),
    "fern_court": Area(
        id="fern_court",
        place="fern court in the arboretum",
        eerie="The glass roof held the last light, and the ferns made soft shadows on the path.",
        bench="a bench near the greenhouse door",
        water_name="the dry path",
        drifting="the warm air barely moved at all",
        clue_place="the gravel path",
        risk=0,
        severity=0,
        has_water=False,
        tags={"arboretum", "greenhouse"},
    ),
}

POSTAGE = {
    "stamp_sheet": Postage(
        id="stamp_sheet",
        label="postage stamps",
        phrase="a little sheet of postage stamps",
        purpose="mailing thank-you cards from the arboretum mailbox",
        drift_text="The little sheet skittered away like a pale leaf.",
        recover_text="The stamps were damp at the corners but still together.",
        paper=True,
        floats=True,
        plural=True,
        tags={"postage", "stamp"},
    ),
    "postcard": Postage(
        id="postcard",
        label="postcard",
        phrase="a picture postcard with fresh postage on it",
        purpose="mailing a postcard to Grandma",
        drift_text="The postcard slid off the bench and fluttered toward the water.",
        recover_text="The postcard was spotted with water, but the address could still be read.",
        paper=True,
        floats=True,
        plural=False,
        tags={"postage", "postcard"},
    ),
    "envelope": Postage(
        id="envelope",
        label="envelope",
        phrase="a small envelope with stamps already pressed on",
        purpose="mailing a note to a friend",
        drift_text="The envelope lifted, turned once in the air, and sailed toward the reeds.",
        recover_text="The envelope was a little wrinkled, but the stamps stayed on.",
        paper=True,
        floats=True,
        plural=False,
        tags={"postage", "envelope"},
    ),
    "token": Postage(
        id="token",
        label="wooden token",
        phrase="a wooden token from the gift shop",
        purpose="holding a place in line",
        drift_text="The token clacked on the bench.",
        recover_text="The token was dry.",
        paper=False,
        floats=False,
        plural=False,
        tags={"token"},
    ),
}

RESPONSES = {
    "ranger_grabber": Response(
        id="ranger_grabber",
        sense=3,
        power=3,
        text="called the night ranger, who came with a long grabber and lifted the postage out without anyone leaning over the edge",
        fail="called the night ranger, but by the time the grabber reached the spot the postage had already gone under the dark water",
        qa_text="the ranger used a long grabber to lift the postage out safely",
        tags={"ranger", "tool", "safety"},
    ),
    "pond_net": Response(
        id="pond_net",
        sense=2,
        power=2,
        text="asked the ranger for the little pond net by the gate, and together they scooped the postage from the reeds",
        fail="tried the little pond net, but the postage had drifted too far past the reeds",
        qa_text="they used the ranger's pond net to scoop the postage out",
        tags={"ranger", "tool", "safety"},
    ),
    "hand_reach": Response(
        id="hand_reach",
        sense=1,
        power=1,
        text="leaned down and snatched the postage with bare fingers",
        fail="leaned down with bare fingers, but the postage slipped deeper into the water",
        qa_text="they reached with bare hands",
        tags={"unsafe", "water"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Ivy", "June", "Wren", "Clara", "Elsie"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Jude", "Finn", "Eli", "Noah", "Ben"]
TRAITS = ["careful", "steady", "patient", "curious", "thoughtful", "brave"]


@dataclass
class StoryParams:
    area: str
    postage: str
    response: str
    finder: str
    finder_gender: str
    cautioner: str
    cautioner_gender: str
    ranger_gender: str
    trait: str
    delay: int = 0
    finder_age: int = 6
    cautioner_age: int = 5
    relation: str = "siblings"
    trust: int = 6
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


def valid_combo(area_id: str, postage_id: str) -> bool:
    if area_id not in AREAS or postage_id not in POSTAGE:
        return False
    area = AREAS[area_id]
    item = POSTAGE[postage_id]
    return area.has_water and item.paper and item.floats


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for area_id in AREAS:
        for postage_id in POSTAGE:
            if valid_combo(area_id, postage_id):
                combos.append((area_id, postage_id))
    return combos


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avoid_reach(relation: str, finder_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > finder_age
    authority = initial_caution(trait) + 1.0 + (3.0 if older else 0.0)
    return older and authority > NERVE_INIT


def mystery_severity(area: Area, delay: int) -> int:
    return area.severity + delay


def is_recovered(response: Response, area: Area, delay: int) -> bool:
    return response.power >= mystery_severity(area, delay)


def explain_rejection(area: Area, item: Postage) -> str:
    if not area.has_water:
        return (
            f"(No story: {area.place} has no pond or canal edge, so the postage would not drift "
            f"into a spooky waterside mystery. Pick a watery part of the arboretum instead.)"
        )
    if not item.paper:
        return (
            f"(No story: {item.label} is not paper postage, so it cannot flutter off and become the "
            f"kind of missing-paper mystery this world models.)"
        )
    return "(No story: this combination does not make a sensible postage mystery.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a safer choice like {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avoid_reach(params.relation, params.finder_age, params.cautioner_age, params.trait):
        return "averted"
    return "recovered" if is_recovered(RESPONSES[params.response], AREAS[params.area], params.delay) else "lost"


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def predict_reach(world: World) -> dict:
    sim = world.copy()
    child = sim.get("finder")
    area = sim.get("area")
    item = sim.get("postage")
    child.meters["leaning"] += 1
    area.meters["edge_risk"] = float(area.attrs["risk"])
    propagate(sim, narrate=False)
    slips = area.attrs["risk"] + sim.facts["delay"] >= 3
    lost = slips or (item.meters["wet"] >= THRESHOLD and sim.facts["delay"] >= 1)
    return {
        "slips": slips,
        "lost": lost,
        "fear": child.memes["fear"] + sum(k.memes["fear"] for k in sim.kids()),
    }


def play_setup(world: World, finder: Entity, cautioner: Entity, area: Area, item: Postage) -> None:
    finder.memes["joy"] += 1
    cautioner.memes["joy"] += 1
    world.say(
        f"At dusk, {finder.id} and {cautioner.id} wandered through {area.place}. "
        f"{area.eerie}"
    )
    world.say(
        f"They had stopped at {area.bench} because {finder.id} wanted to finish {item.purpose}."
    )


def notice_swan(world: World, finder: Entity) -> None:
    swan = world.get("swan")
    finder.memes["wonder"] += 1
    world.say(
        f"Out on the water, a white swan drifted so quietly that for a moment it looked like a little ghost boat."
    )
    world.say(
        f'"Did you see that swan?" {finder.id} whispered. "It looks like it knows all the secret paths."'
    )


def set_down_postage(world: World, finder: Entity, item: Postage, area: Area) -> None:
    world.say(
        f"{finder.id} set {item.phrase} on the bench for one tiny moment. Then {area.drifting}."
    )
    postage = world.get("postage")
    postage.meters["drifting"] += 1
    propagate(world, narrate=False)
    world.say(item.drift_text)
    world.say("When the children looked again, the postage was gone.")


def warn(world: World, cautioner: Entity, finder: Entity, area: Area) -> None:
    pred = predict_reach(world)
    cautioner.memes["caution"] += 1
    world.facts["predicted_slip"] = pred["slips"]
    if pred["slips"]:
        world.say(
            f'{cautioner.id} caught {finder.id}\'s sleeve. "Don\'t lean over {area.water_name}," '
            f'{cautioner.pronoun()} said. "The stones are wet, and you could slip."'
        )
    else:
        world.say(
            f'{cautioner.id} lowered {cautioner.pronoun("possessive")} voice. "Let\'s not grab at the dark water," '
            f'{cautioner.pronoun()} said. "We should solve this carefully."'
        )


def defy(world: World, finder: Entity, cautioner: Entity) -> None:
    finder.memes["defiance"] += 1
    relation = finder.attrs.get("relation", "friends")
    if relation == "siblings" and finder.age > cautioner.age:
        world.say(
            f'"I can reach it fast," {finder.id} said. Because {finder.id} was the older one this time, '
            f'{cautioner.id} could not stop {finder.pronoun("object")} right away.'
        )
    else:
        world.say(f'"I can reach it fast," {finder.id} said, stepping toward the edge anyway.')


def back_down(world: World, finder: Entity, cautioner: Entity) -> None:
    finder.memes["relief"] += 1
    cautioner.memes["relief"] += 1
    finder.memes["defiance"] = 0.0
    world.say(
        f'{finder.id} started forward, then looked at {cautioner.id} and stopped. '
        f'The whispery water did not seem brave anymore, only slippery.'
    )
    world.say(
        f'"You\'re right," {finder.pronoun()} said. "A mystery is better than a splash."'
    )


def inspect_clue(world: World, finder: Entity, cautioner: Entity, area: Area) -> None:
    swan = world.get("swan")
    finder.memes["wonder"] += 1
    cautioner.memes["wonder"] += 1
    world.say(
        f"Together they peered at {area.clue_place}. There, beside the faint ripples, lay one white feather from the swan."
    )
    world.say(
        f'"A ghost would not leave a feather," said {cautioner.id}. "Something real moved the postage."'
    )
    world.facts["clue"] = "feather"


def reach_attempt(world: World, finder: Entity, area: Area) -> None:
    area_ent = world.get("area")
    area_ent.meters["edge_risk"] = float(area.attrs["risk"])
    finder.meters["leaning"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{finder.id} bent toward {area.water_name}, and the black water shivered under the reeds."
    )


def call_ranger(world: World, ranger: Entity, response: Response) -> None:
    world.say(
        f'Just then a ranger\'s lantern bobbed along the path. "{ranger.id}," '
        f'called the children, "our postage vanished!"'
    )
    world.say(
        f"{ranger.id} listened, looked at the feather and the ripples, and nodded as if the arboretum had already whispered the answer."
    )


def recover(world: World, ranger: Entity, response: Response, item: Postage) -> None:
    postage = world.get("postage")
    postage.meters["recovered"] += 1
    postage.meters["missing"] = 0.0
    world.say(
        f"{ranger.id} {response.text}."
    )
    world.say(
        f"{item.recover_text} It had caught in the reeds instead of being stolen by a ghost."
    )


def lose(world: World, ranger: Entity, response: Response, area: Area, item: Postage) -> None:
    postage = world.get("postage")
    postage.meters["lost"] += 1
    world.say(f"{ranger.id} {response.fail}.")
    world.say(
        f"A slow circle spread across {area.water_name}, and the postage was gone for good."
    )


def lesson(world: World, ranger: Entity, finder: Entity, cautioner: Entity, item: Postage) -> None:
    for kid in (finder, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    world.say(
        f'{ranger.id} knelt so the lantern light was warm instead of spooky. '
        f'"Paper and water are bad partners," {ranger.pronoun()} said softly. '
        f'"And no piece of postage is worth leaning over dark water for."'
    )
    world.say(
        f'{finder.id} and {cautioner.id} nodded. The mystery had felt ghostly, but the answer had been wind, water, and one patient look.'
    )


def replacement(world: World, ranger: Entity, finder: Entity, cautioner: Entity, item: Postage) -> None:
    for kid in (finder, cautioner):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
    world.say(
        f"Then {ranger.id} opened a little ranger satchel and brought out fresh postage from the visitor desk."
    )
    world.say(
        f"This time the children tucked {item.label} inside a stiff little mail folder before walking to the red arboretum mailbox."
    )
    world.say(
        f"The swan glided past once more, white as moonlight, and now it looked less like a ghost and more like a quiet neighbor keeping watch."
    )


def sad_end(world: World, ranger: Entity, finder: Entity, cautioner: Entity, item: Postage) -> None:
    for kid in (finder, cautioner):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f'{ranger.id} touched the railing and said, "We can replace paper, but we do not lean into dark water for it."'
    )
    world.say(
        f"So the children walked back through the arboretum without their first mailing. Later they used new postage at a dry table inside, and they never again left paper loose by the pond."
    )


def tell(
    area: Area,
    item: Postage,
    response: Response,
    finder_name: str = "Lila",
    finder_gender: str = "girl",
    cautioner_name: str = "Owen",
    cautioner_gender: str = "boy",
    ranger_gender: str = "ranger_female",
    trait: str = "careful",
    delay: int = 0,
    finder_age: int = 6,
    cautioner_age: int = 5,
    relation: str = "siblings",
    trust: int = 6,
) -> World:
    world = World()
    finder = world.add(
        Entity(
            id="finder",
            kind="character",
            type=finder_gender,
            label=finder_name,
            role="finder",
            age=finder_age,
            attrs={"relation": relation},
            traits=["eager"],
        )
    )
    cautioner = world.add(
        Entity(
            id="cautioner",
            kind="character",
            type=cautioner_gender,
            label=cautioner_name,
            role="cautioner",
            age=cautioner_age,
            attrs={"relation": relation, "trust": trust},
            traits=[trait],
        )
    )
    ranger_type = "ranger_female" if ranger_gender == "girl" else "ranger_male"
    ranger_name = "Ranger Mae" if ranger_gender == "girl" else "Ranger Ben"
    ranger = world.add(
        Entity(
            id="ranger",
            kind="character",
            type=ranger_type,
            label=ranger_name,
            role="helper",
            traits=["calm"],
        )
    )
    area_ent = world.add(
        Entity(
            id="area",
            kind="thing",
            type="place",
            label=area.place,
            water_place=area.has_water,
            attrs={"risk": area.risk},
        )
    )
    swan = world.add(
        Entity(
            id="swan",
            kind="thing",
            type="animal",
            label="swan",
            attrs={"white": True},
        )
    )
    postage = world.add(
        Entity(
            id="postage",
            kind="thing",
            type="postage",
            label=item.label,
            paper=item.paper,
            floats=item.floats,
        )
    )

    finder.id = finder_name
    cautioner.id = cautioner_name
    ranger.id = ranger_name
    world.entities[finder_name] = world.entities.pop("finder")
    world.entities[cautioner_name] = world.entities.pop("cautioner")
    world.entities[ranger_name] = world.entities.pop("ranger")
    world.entities["area"] = area_ent
    world.entities["swan"] = swan
    world.entities["postage"] = postage

    world.facts["delay"] = delay
    world.facts["relation"] = relation
    world.facts["predicted_slip"] = False
    world.facts["clue"] = ""
    world.facts["response_used"] = response.id

    play_setup(world, finder, cautioner, area, item)
    notice_swan(world, finder)

    world.para()
    set_down_postage(world, finder, item, area)
    warn(world, cautioner, finder, area)
    inspect_clue(world, finder, cautioner, area)

    averted = would_avoid_reach(relation, finder.age, cautioner.age, trait)

    world.para()
    if averted:
        back_down(world, finder, cautioner)
        call_ranger(world, ranger, response)
        recover(world, ranger, response, item)
        lesson(world, ranger, finder, cautioner, item)
        world.para()
        replacement(world, ranger, finder, cautioner, item)
        outcome = "averted"
    else:
        defy(world, finder, cautioner)
        reach_attempt(world, finder, area)
        call_ranger(world, ranger, response)
        if is_recovered(response, area, delay):
            recover(world, ranger, response, item)
            lesson(world, ranger, finder, cautioner, item)
            world.para()
            replacement(world, ranger, finder, cautioner, item)
            outcome = "recovered"
        else:
            lose(world, ranger, response, area, item)
            sad_end(world, ranger, finder, cautioner, item)
            outcome = "lost"

    world.facts.update(
        area=area,
        postage_cfg=item,
        response=response,
        finder=finder,
        cautioner=cautioner,
        ranger=ranger,
        swan=swan,
        outcome=outcome,
        mystery=postage.meters["missing"] >= THRESHOLD or postage.meters["recovered"] >= THRESHOLD or postage.meters["lost"] >= THRESHOLD,
        recovered=postage.meters["recovered"] >= THRESHOLD,
        lost=postage.meters["lost"] >= THRESHOLD,
        averted=outcome == "averted",
        clue=world.facts.get("clue", "feather"),
        delay=delay,
    )
    return world


KNOWLEDGE = {
    "arboretum": [
        (
            "What is an arboretum?",
            "An arboretum is a place where many kinds of trees and plants are grown and cared for. People can walk there, learn there, and notice nature quietly.",
        )
    ],
    "postage": [
        (
            "What is postage?",
            "Postage is what lets a letter or card be mailed. It is often a stamp or a mark that shows the mail can travel to someone else.",
        )
    ],
    "stamp": [
        (
            "Why should paper postage be kept dry?",
            "Paper gets soft and tears when it is wet. If stamps or envelopes get soaked, they can wrinkle or stop working well.",
        )
    ],
    "postcard": [
        (
            "What is a postcard?",
            "A postcard is a small card with space for a message and an address. You can mail it without putting it in an envelope.",
        )
    ],
    "envelope": [
        (
            "What is an envelope for?",
            "An envelope holds a letter or note so it stays together on its trip. You usually put postage on the outside.",
        )
    ],
    "pond": [
        (
            "Why can pond edges be slippery?",
            "Pond edges can be wet with moss, mud, or splashed water. That makes them slick, so people should not lean too close.",
        )
    ],
    "water": [
        (
            "What should you do if something falls near dark water?",
            "Stop and call a grown-up for help. Safe tools and careful hands are better than leaning in and risking a fall.",
        )
    ],
    "swan": [
        (
            "What is a swan?",
            "A swan is a large water bird with a long neck. It glides on ponds and lakes very quietly, which can make it seem mysterious.",
        )
    ],
    "ranger": [
        (
            "What does a park ranger do?",
            "A ranger helps care for a park or garden and keeps people safe there. Rangers often know the paths, animals, and the safest tools to use.",
        )
    ],
    "tool": [
        (
            "Why is a long grabber or net safer than reaching by hand?",
            "A long tool lets you stay back from the edge while you pick something up. That keeps your feet on solid ground and your body safer.",
        )
    ],
    "safety": [
        (
            "Why is it smart to ask for help with a mystery?",
            "Another person may see clues you missed and know a safer way to solve the problem. Careful thinking is part of being brave.",
        )
    ],
}
KNOWLEDGE_ORDER = ["arboretum", "postage", "stamp", "postcard", "envelope", "pond", "water", "swan", "ranger", "tool", "safety"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    area: Area = f["area"]
    item: Postage = f["postage_cfg"]
    finder: Entity = f["finder"]
    cautioner: Entity = f["cautioner"]
    outcome = f["outcome"]
    if outcome == "lost":
        return [
            f'Write a child-friendly ghost-story mystery set in an arboretum where some {item.label} goes missing near water and a swan seems spooky at first.',
            f"Tell a cautionary story where {finder.id} thinks a ghost stole the postage, but the real problem is wind and water, and the first mailing is lost.",
            f'Write a mystery-to-solve story using the words "swan", "postage", and "arboretum", ending with a calm safety lesson about not leaning over dark water.',
        ]
    return [
        f'Write a gentle ghost-story mystery set in {area.place} where a child loses {item.label} and must solve what happened.',
        f"Tell a story where {finder.id} and {cautioner.id} see a swan in the mist, think something spooky may be happening, and then solve the mystery by looking for clues.",
        f'Write a cautionary problem-solving story that uses the words "swan", "postage", and "arboretum" and ends with a safe mailing at the mailbox.',
    ]


def relation_pair(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder: Entity = f["finder"]
    cautioner: Entity = f["cautioner"]
    ranger: Entity = f["ranger"]
    area: Area = f["area"]
    item: Postage = f["postage_cfg"]
    response: Response = f["response"]
    relation = world.facts.get("relation", "friends")
    pair = relation_pair(finder, cautioner, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {finder.id} and {cautioner.id}, in an arboretum at dusk. A calm ranger helps them when the mystery grows too hard to solve alone.",
        ),
        (
            "What was the mystery?",
            f"The postage disappeared after a gust of wind near the water. Because the swan was gliding through mist, the children first wondered if something ghostly had taken it.",
        ),
        (
            "What clue helped them think more carefully?",
            f"They found a white swan feather near the ripples. That clue showed that something real had been near the water, so they stopped imagining a ghost and started solving the problem.",
        ),
        (
            f"Why did {cautioner.id} warn {finder.id} not to lean over the edge?",
            f"{cautioner.id} knew the stones by {area.water_name} were wet and slippery. The warning came before the reaching because solving the mystery safely mattered more than hurrying.",
        ),
    ]
    outcome = f["outcome"]
    if outcome == "averted":
        qa.append(
            (
                f"How was the problem solved?",
                f"{finder.id} stopped before reaching, and the ranger came with help. {response.qa_text.capitalize()}, so the mystery was solved without anyone leaning over the dark water.",
            )
        )
    elif outcome == "recovered":
        qa.append(
            (
                f"How did the ranger help solve the mystery?",
                f"{response.qa_text.capitalize()}. The children learned that the wind had pushed the postage into the reeds, where it only looked vanished from far away.",
            )
        )
    else:
        qa.append(
            (
                "Did they get the postage back?",
                f"No. They tried to solve it, but the postage drifted away for good. Even so, the ranger taught them the more important lesson: paper can be replaced, but children should not lean into dark water.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            "The ending proved what changed: the children treated the swan as a quiet part of the garden instead of a ghost, and they handled mailing more carefully than before.",
        )
    )
    return qa


def world_knowledge_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["area"].tags) | set(f["postage_cfg"].tags) | {"swan"}
    tags |= set(f["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        flags = [name for name, on in (("paper", e.paper), ("floats", e.floats), ("water_place", e.water_place)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:12} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
paper_postage(P) :- postage(P), paper(P), floats(P).
valid(A, P) :- area(A), has_water(A), paper_postage(P).

sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), finder_age(FA), cautioner_age(CA), CA > FA.
bonus(3) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), nerve_init(N), A > N.

severity(V + D) :- chosen_area(A), area_severity(A, V), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
recovered :- resp_power(P), severity(S), P >= S.

outcome(averted) :- averted.
outcome(recovered) :- not averted, recovered.
outcome(lost) :- not averted, not recovered.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for aid, area in AREAS.items():
        lines.append(asp.fact("area", aid))
        if area.has_water:
            lines.append(asp.fact("has_water", aid))
        lines.append(asp.fact("area_severity", aid, area.severity))
    for pid, item in POSTAGE.items():
        lines.append(asp.fact("postage", pid))
        if item.paper:
            lines.append(asp.fact("paper", pid))
        if item.floats:
            lines.append(asp.fact("floats", pid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("nerve_init", int(NERVE_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_area", params.area),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("finder_age", params.finder_age),
            asp.fact("cautioner_age", params.cautioner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: missing postage, a misty swan, and a safe mystery in an arboretum."
    )
    ap.add_argument("--area", choices=AREAS)
    ap.add_argument("--postage", choices=POSTAGE)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the postage drifts before help arrives")
    ap.add_argument("--relation", choices=["siblings", "friends"])
    ap.add_argument("--finder")
    ap.add_argument("--cautioner")
    ap.add_argument("--finder-gender", choices=["girl", "boy"])
    ap.add_argument("--cautioner-gender", choices=["girl", "boy"])
    ap.add_argument("--ranger-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.area and args.postage:
        if not valid_combo(args.area, args.postage):
            raise StoryError(explain_rejection(AREAS[args.area], POSTAGE[args.postage]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.area is None or combo[0] == args.area)
        and (args.postage is None or combo[1] == args.postage)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    area_id, postage_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    finder_gender = args.finder_gender or rng.choice(["girl", "boy"])
    cautioner_gender = args.cautioner_gender or rng.choice(["girl", "boy"])
    finder = args.finder or rng.choice(GIRL_NAMES if finder_gender == "girl" else BOY_NAMES)
    cautioner_pool = [n for n in (GIRL_NAMES if cautioner_gender == "girl" else BOY_NAMES) if n != finder]
    cautioner = args.cautioner or rng.choice(cautioner_pool)
    ranger_gender = args.ranger_gender or rng.choice(["girl", "boy"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = args.relation or rng.choice(["siblings", "friends"])
    finder_age, cautioner_age = rng.sample([4, 5, 6, 7, 8], 2)
    trust = rng.randint(2, 9)
    return StoryParams(
        area=area_id,
        postage=postage_id,
        response=response_id,
        finder=finder,
        finder_gender=finder_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        ranger_gender=ranger_gender,
        trait=trait,
        delay=delay,
        finder_age=finder_age,
        cautioner_age=cautioner_age,
        relation=relation,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.area not in AREAS:
        raise StoryError(f"(Unknown area: {params.area})")
    if params.postage not in POSTAGE:
        raise StoryError(f"(Unknown postage: {params.postage})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if not valid_combo(params.area, params.postage):
        raise StoryError(explain_rejection(AREAS[params.area], POSTAGE[params.postage]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        area=AREAS[params.area],
        item=POSTAGE[params.postage],
        response=RESPONSES[params.response],
        finder_name=params.finder,
        finder_gender=params.finder_gender,
        cautioner_name=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        ranger_gender=params.ranger_gender,
        trait=params.trait,
        delay=params.delay,
        finder_age=params.finder_age,
        cautioner_age=params.cautioner_age,
        relation=params.relation,
        trust=params.trust,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_pairs(world)],
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
    StoryParams(
        area="moon_pond",
        postage="stamp_sheet",
        response="ranger_grabber",
        finder="Lila",
        finder_gender="girl",
        cautioner="Owen",
        cautioner_gender="boy",
        ranger_gender="girl",
        trait="careful",
        delay=0,
        finder_age=5,
        cautioner_age=7,
        relation="siblings",
        trust=7,
    ),
    StoryParams(
        area="willow_cove",
        postage="postcard",
        response="pond_net",
        finder="Theo",
        finder_gender="boy",
        cautioner="Mina",
        cautioner_gender="girl",
        ranger_gender="boy",
        trait="thoughtful",
        delay=0,
        finder_age=7,
        cautioner_age=6,
        relation="friends",
        trust=5,
    ),
    StoryParams(
        area="willow_cove",
        postage="envelope",
        response="pond_net",
        finder="Noah",
        finder_gender="boy",
        cautioner="Ivy",
        cautioner_gender="girl",
        ranger_gender="girl",
        trait="patient",
        delay=1,
        finder_age=8,
        cautioner_age=6,
        relation="siblings",
        trust=4,
    ),
    StoryParams(
        area="lily_walk",
        postage="postcard",
        response="ranger_grabber",
        finder="June",
        finder_gender="girl",
        cautioner="Clara",
        cautioner_gender="girl",
        ranger_gender="girl",
        trait="steady",
        delay=0,
        finder_age=4,
        cautioner_age=7,
        relation="siblings",
        trust=8,
    ),
]


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

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    for s in range(150):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        with redirect_stdout(io.StringIO()):
            emit(smoke, trace=True, qa=True, header="### smoke")
        print("OK: smoke generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/2.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (area, postage) combos:\n")
        for area_id, postage_id in combos:
            print(f"  {area_id:12} {postage_id}")
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
            header = f"### {p.finder} & {p.cautioner}: {p.postage} at {p.area} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
