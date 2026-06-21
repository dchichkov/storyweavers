#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py
============================================================================

A standalone story world for a tiny child-facing detective tale about three
friends -- Piggie, Minus, and Chipper -- solving a small mystery by working
together.

Premise
-------
Something important for a village event has gone missing. Piggie notices the
first clue, Minus studies the tiny signs, and Chipper does the careful reaching
or climbing needed to get the object back. The turn is detective-like: the team
first fears a thief, then reads the clues closely and realizes the item was
misplaced by chance -- rolled away, blown aside, or carried off by a curious
bird. The ending image proves the change: the worried owner smiles again, and
the three detectives go home trusting teamwork more than guesses.

Run it
------
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py --place green --item bell --spot nest
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py --item ribbon --spot bench
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/piggie_minus_chipper_teamwork_detective_story.py --verify
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
        male = {"boy", "father", "man"}
        female = {"girl", "mother", "woman"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    opening: str
    event: str
    affords: set[str] = field(default_factory=set)
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    owner_name: str
    owner_type: str
    event_use: str
    first_worry: str
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
class Spot:
    id: str
    label: str
    clue1: str
    clue2: str
    theory: str
    cause_word: str
    retrieve: str
    final_image: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
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


def _r_case_worry(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    if item.meters["missing"] < THRESHOLD:
        return []
    sig = ("worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["worry"] += 1
    for eid in ("Piggie", "Minus", "Chipper"):
        world.get(eid).memes["curiosity"] += 1
    return []


def _r_theory(world: World) -> list[str]:
    if world.facts.get("clues_found", 0) < 2:
        return []
    sig = ("theory", "case")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("Piggie", "Minus", "Chipper"):
        world.get(eid).memes["confidence"] += 1
    world.facts["theory_ready"] = True
    return []


def _r_found(world: World) -> list[str]:
    item = world.get("item")
    owner = world.get("owner")
    if not world.facts.get("retrieval_done"):
        return []
    sig = ("found", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["missing"] = 0.0
    item.meters["found"] += 1
    owner.memes["relief"] += 1
    owner.memes["worry"] = 0.0
    for eid in ("Piggie", "Minus", "Chipper"):
        world.get(eid).memes["pride"] += 1
        world.get(eid).memes["teamwork"] += 1
    world.facts["solved"] = True
    return []


CAUSAL_RULES = [
    Rule(name="case_worry", tag="emotional", apply=_r_case_worry),
    Rule(name="theory", tag="cognitive", apply=_r_theory),
    Rule(name="found", tag="resolution", apply=_r_found),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


PLACES = {
    "green": Place(
        id="green",
        label="the village green",
        opening="Morning sunlight lay across the village green, where little booths and ribbons were being set out for the fair.",
        event="the opening song at the fair",
        affords={"bench", "nest"},
        tags={"fair", "outdoors"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard path",
        opening="The apple orchard path smelled sweet, and paper lanterns were waiting to be hung between the trees for the evening party.",
        event="the orchard party",
        affords={"bench", "nest", "reeds"},
        tags={"orchard", "outdoors"},
    ),
    "pond": Place(
        id="pond",
        label="the pond walk",
        opening="At the pond walk, the board path curved beside the water, and everyone was getting ready for the little boat parade.",
        event="the little boat parade",
        affords={"reeds", "bench"},
        tags={"pond", "water"},
    ),
}

ITEMS = {
    "bell": ItemCfg(
        id="bell",
        label="bell",
        phrase="a brass bell with a red cord",
        owner_name="Mrs. Wren",
        owner_type="woman",
        event_use="ring to start the parade",
        first_worry="Without it, the parade could not begin on time.",
        tags={"shiny", "light", "roundish", "metal", "sound"},
    ),
    "ribbon": ItemCfg(
        id="ribbon",
        label="ribbon",
        phrase="a long blue ribbon",
        owner_name="Mr. Reed",
        owner_type="man",
        event_use="tie around the winner's basket",
        first_worry="Without it, the prize basket would look plain and unfinished.",
        tags={"bright", "light", "cloth", "floatable"},
    ),
    "whistle": ItemCfg(
        id="whistle",
        label="whistle",
        phrase="a wooden whistle on a green string",
        owner_name="Aunt Maple",
        owner_type="woman",
        event_use="call the children together for the picnic game",
        first_worry="Without it, nobody would know when the game was supposed to start.",
        tags={"light", "floatable", "wood", "sound"},
    ),
    "medal": ItemCfg(
        id="medal",
        label="medal",
        phrase="a shiny round medal",
        owner_name="Coach Pine",
        owner_type="man",
        event_use="hang around the winner's neck",
        first_worry="Without it, the race would have no grand finishing moment.",
        tags={"shiny", "light", "roundish", "metal"},
    ),
}

SPOTS = {
    "bench": Spot(
        id="bench",
        label="under a park bench",
        clue1="Piggie saw a thin scrape line on the boards and a tiny flash far underneath.",
        clue2="Minus knelt down and found a little track in the dust showing something small had rolled away, not been carried off.",
        theory="The thing had not been stolen at all. It had rolled out of sight when nobody was looking.",
        cause_word="rolled",
        retrieve="Chipper lay flat and reached in with a hooked twig while Minus called left and right and Piggie held the lantern steady.",
        final_image="The lost thing came sliding out over the sun-warmed boards.",
        tags={"low", "rolling"},
    ),
    "nest": Spot(
        id="nest",
        label="in a crooked nest",
        clue1="Piggie heard an excited caw above them and noticed one bright strand tucked high in the leaves.",
        clue2="Minus studied the bark and found a feather snagged beside a fresh scratch, proof that a curious bird had carried the object up.",
        theory="No sneaky thief had taken it. A bird had borrowed something pretty for its nest.",
        cause_word="bird",
        retrieve="Chipper scampered up the trunk, while Piggie spread a cloth below and Minus pointed to the safest branch.",
        final_image="Chipper came down grinning, the missing thing wrapped carefully in the cloth.",
        tags={"high", "bird"},
    ),
    "reeds": Spot(
        id="reeds",
        label="among the pond reeds",
        clue1="Piggie sniffed the air and noticed a wet trail ending where the wind brushed the reeds into soft whispers.",
        clue2="Minus found the smallest bend in the mud and a loop of color caught low by the water, showing the breeze had pushed the object aside.",
        theory="Nobody had meant to hide it. A gust had carried it to the edge of the pond.",
        cause_word="wind",
        retrieve="Chipper used a long branch to hook the object in, while Piggie braced the branch and Minus told him exactly where the color glimmered.",
        final_image="The reeds parted, and the missing thing bobbed back toward shore.",
        tags={"water", "wind"},
    ),
}


def item_fits_spot(item: ItemCfg, spot: Spot) -> bool:
    tags = item.tags
    if spot.id == "bench":
        return "roundish" in tags
    if spot.id == "nest":
        return "light" in tags and ("shiny" in tags or "bright" in tags)
    if spot.id == "reeds":
        return "floatable" in tags or ("light" in tags and "cloth" in tags)
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for spot_id, spot in SPOTS.items():
                if spot_id in place.affords and item_fits_spot(item, spot):
                    combos.append((place_id, item_id, spot_id))
    return combos


def explain_rejection(place: Place, item: ItemCfg, spot: Spot) -> str:
    if spot.id not in place.affords:
        return (
            f"(No story: {place.label} does not have the right kind of hiding place for "
            f"{spot.label}. Pick a place that actually affords that clue trail.)"
        )
    return (
        f"(No story: {item.phrase} is not a plausible mystery for {spot.label}. "
        f"This detective world only allows clues that fit the object's size and nature.)"
    )


def infer_cause(spot_id: str) -> str:
    return {
        "bench": "rolled",
        "nest": "bird",
        "reeds": "wind",
    }[spot_id]


def predict_solution(world: World, spot_id: str) -> dict:
    sim = world.copy()
    sim.facts["clues_found"] = 2
    propagate(sim, narrate=False)
    sim.facts["retrieval_done"] = True
    sim.facts["predicted_spot"] = spot_id
    propagate(sim, narrate=False)
    return {
        "theory_ready": bool(sim.facts.get("theory_ready")),
        "solved": bool(sim.facts.get("solved")),
    }


def open_case(world: World, item_cfg: ItemCfg) -> None:
    owner = world.get("owner")
    item = world.get("item")
    item.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(world.place.opening)
    world.say(
        f"But then {owner.id} stopped short. {owner.pronoun().capitalize()} was carrying "
        f"{item_cfg.phrase} only a moment before, and now it was gone."
    )
    world.say(
        f'"My {item_cfg.label}!" {owner.id} cried. "{item_cfg.first_worry}"'
    )


def call_detectives(world: World, item_cfg: ItemCfg) -> None:
    piggie = world.get("Piggie")
    minus = world.get("Minus")
    chipper = world.get("Chipper")
    for det in (piggie, minus, chipper):
        det.memes["care"] += 1
    world.say(
        f"Piggie, Minus, and Chipper looked at one another the way real detectives do when a case lands right in front of them."
    )
    world.say(
        f'"First we look, then we think, then we help," Piggie said. '
        f'Minus nodded. Chipper tapped {chipper.pronoun("possessive")} little notebook and whispered, "Case of the Missing {item_cfg.label.capitalize()}."'
    )


def first_clue(world: World, spot: Spot) -> None:
    piggie = world.get("Piggie")
    piggie.memes["focus"] += 1
    world.facts["clues_found"] += 1
    world.history.append("piggie_found_clue")
    world.say(spot.clue1)


def wrong_guess(world: World, item_cfg: ItemCfg) -> None:
    world.say(
        f"For one worried minute, the three friends wondered if someone had taken the {item_cfg.label} on purpose."
    )


def second_clue(world: World, spot: Spot) -> None:
    minus = world.get("Minus")
    minus.memes["focus"] += 1
    world.facts["clues_found"] += 1
    world.history.append("minus_found_clue")
    propagate(world, narrate=False)
    world.say(spot.clue2)
    world.say(spot.theory)


def plan_search(world: World, spot: Spot) -> None:
    pred = predict_solution(world, spot.id)
    world.facts["predicted_solved"] = pred["solved"]
    world.say(
        f'"Then {spot.label}," Minus said. "That is where our clues point."'
    )
    if pred["solved"]:
        world.say(
            'Piggie drew a small circle in the dust with one hoof. "Good. We do it together."'
        )


def retrieval(world: World, spot: Spot, item_cfg: ItemCfg) -> None:
    chipper = world.get("Chipper")
    chipper.memes["focus"] += 1
    world.para()
    world.say(spot.retrieve)
    world.say(spot.final_image)
    world.facts["retrieval_done"] = True
    world.facts["found_spot"] = spot.id
    propagate(world, narrate=False)
    world.say(
        f'It was the missing {item_cfg.label} all right.'
    )


def return_item(world: World, item_cfg: ItemCfg) -> None:
    owner = world.get("owner")
    world.para()
    world.say(
        f"{owner.id}'s whole face softened when Piggie carried the {item_cfg.label} back."
    )
    world.say(
        f'"You solved it," {owner.pronoun()} said. "{selfsame_event_line(world.place, item_cfg)}"'
    )
    world.say(
        "Minus smiled because the clues had mattered. Chipper smiled because careful paws had mattered. Piggie smiled because nobody had been left to worry alone."
    )
    world.say(
        "From then on, whenever the three friends took a case, they remembered that the best detective tool was not the notebook or the lantern. It was teamwork."
    )


def selfsame_event_line(place: Place, item_cfg: ItemCfg) -> str:
    return f"Now we can {item_cfg.event_use} at {place.event}"


def tell(place: Place, item_cfg: ItemCfg, spot: Spot) -> World:
    world = World(place)
    world.facts["clues_found"] = 0
    world.facts["retrieval_done"] = False
    world.facts["theory_ready"] = False
    world.facts["solved"] = False
    world.facts["predicted_solved"] = False
    world.facts["found_spot"] = ""
    world.facts["cause"] = infer_cause(spot.id)
    world.facts["item_cfg"] = item_cfg
    world.facts["spot_cfg"] = spot
    world.facts["place_cfg"] = place

    world.add(Entity(
        id="Piggie",
        kind="character",
        type="animal",
        role="detective",
        label="Piggie",
        traits=["kind", "observant"],
    ))
    world.add(Entity(
        id="Minus",
        kind="character",
        type="animal",
        role="detective",
        label="Minus",
        traits=["careful", "tiny-eyed"],
    ))
    world.add(Entity(
        id="Chipper",
        kind="character",
        type="animal",
        role="detective",
        label="Chipper",
        traits=["nimble", "brave"],
    ))
    owner = world.add(Entity(
        id=item_cfg.owner_name,
        kind="character",
        type=item_cfg.owner_type,
        role="owner",
        label="the owner",
    ))
    owner.memes["worry"] = 0.0
    owner.memes["relief"] = 0.0
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="object",
        label=item_cfg.label,
        attrs={"phrase": item_cfg.phrase},
    ))
    item.meters["missing"] = 0.0
    item.meters["found"] = 0.0

    open_case(world, item_cfg)
    call_detectives(world, item_cfg)

    world.para()
    first_clue(world, spot)
    wrong_guess(world, item_cfg)
    second_clue(world, spot)
    plan_search(world, spot)

    retrieval(world, spot, item_cfg)
    return_item(world, item_cfg)

    world.facts.update(
        owner=owner,
        item=item,
        solved=bool(world.facts.get("solved")),
        theory_ready=bool(world.facts.get("theory_ready")),
        teamwork_used=all(world.get(eid).memes["focus"] >= THRESHOLD or eid == "Piggie" and world.get(eid).memes["focus"] >= THRESHOLD for eid in ("Piggie", "Minus", "Chipper")),
    )
    return world


KNOWLEDGE = {
    "fair": [
        (
            "What does a detective do?",
            "A detective looks for clues and thinks carefully about what they mean. Good detectives do not only guess. They check the signs and follow them step by step."
        )
    ],
    "bird": [
        (
            "Why do some birds carry shiny things?",
            "Some birds are curious about bright or shiny objects and may pick them up. They are not trying to be mean. They are only interested in the sparkle."
        )
    ],
    "wind": [
        (
            "How can wind move a small object?",
            "A strong breeze can push or slide a light thing along the ground or water. That is why light objects should be watched carefully outside."
        )
    ],
    "rolling": [
        (
            "Why do round things roll away?",
            "Round things move easily when they are bumped or set on a slant. If nobody notices, they can slip under a bench or table very quickly."
        )
    ],
    "water": [
        (
            "What are reeds?",
            "Reeds are tall plants that grow near water. Thin things can get caught in them because the stems stand close together."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help in different ways to do one job together. One friend might notice, another might think, and another might reach or carry."
        )
    ],
}
KNOWLEDGE_ORDER = ["fair", "teamwork", "bird", "wind", "rolling", "water"]


@dataclass
class StoryParams:
    place: str
    item: str
    spot: str
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


def generation_prompts(world: World) -> list[str]:
    item_cfg: ItemCfg = world.facts["item_cfg"]
    spot: Spot = world.facts["spot_cfg"]
    place: Place = world.facts["place_cfg"]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old about piggie, minus, and chipper solving a missing-{item_cfg.label} mystery with teamwork.',
        f"Tell a small village detective story where Piggie notices the first clue, Minus reads the tiny evidence, and Chipper gets the missing {item_cfg.label} back from {spot.label}.",
        f'Write a child-facing mystery set at {place.label} that includes the words "piggie", "minus", and "chipper" and ends by showing that teamwork solved the case.'
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    item_cfg: ItemCfg = world.facts["item_cfg"]
    spot: Spot = world.facts["spot_cfg"]
    place: Place = world.facts["place_cfg"]
    owner: Entity = world.get("owner")
    cause = world.facts["cause"]
    qa: list[tuple[str, str]] = [
        (
            "Who are the detectives in the story?",
            "The detectives are Piggie, Minus, and Chipper. They work as a team instead of one friend trying to solve the mystery alone."
        ),
        (
            f"What was missing at {place.label}?",
            f"The missing thing was {item_cfg.phrase}. {owner.id} needed it to {item_cfg.event_use}."
        ),
        (
            "Why did the friends first feel worried?",
            f"They worried because the missing {item_cfg.label} was important for the event. For a moment they even wondered if someone had taken it on purpose."
        ),
        (
            "How did Piggie help solve the case?",
            f"Piggie noticed the first clue: {spot.clue1.split('. ')[0].lower()}. That clue started the search in the right direction."
        ),
        (
            "How did Minus help solve the case?",
            f"Minus studied the tiny signs and explained what had really happened. That turned a frightened guess into a proper detective theory."
        ),
        (
            "How did Chipper help solve the case?",
            f"Chipper did the careful reaching and climbing part of the job. The clues mattered first, and then Chipper's quick body helped bring the item back safely."
        ),
        (
            "What really happened to the missing thing?",
            explanation_for_cause(item_cfg, spot, cause),
        ),
        (
            "How did the story end?",
            f"It ended happily because the {item_cfg.label} came back in time for {place.event}. The owner stopped worrying, and the three detectives learned that teamwork was their best tool."
        ),
    ]
    return qa


def explanation_for_cause(item_cfg: ItemCfg, spot: Spot, cause: str) -> str:
    if cause == "rolled":
        return (
            f"The {item_cfg.label} had rolled away and hidden {spot.label}. Minus knew this because the tiny marks showed rolling, not stealing."
        )
    if cause == "bird":
        return (
            f"A curious bird had carried the {item_cfg.label} up to {spot.label}. The feather and scratch on the bark showed that the mystery was mischief from above, not a thief."
        )
    return (
        f"The wind had pushed the {item_cfg.label} into {spot.label}. The wet trail and bent mud showed that the breeze, not a person, moved it there."
    )


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"teamwork", "fair"} | set(world.facts["spot_cfg"].tags)
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:12} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  facts: {{'clues_found': {world.facts.get('clues_found')}, 'cause': '{world.facts.get('cause')}', 'found_spot': '{world.facts.get('found_spot')}', 'solved': {world.facts.get('solved')}}}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="green", item="bell", spot="bench"),
    StoryParams(place="green", item="medal", spot="nest"),
    StoryParams(place="pond", item="ribbon", spot="reeds"),
    StoryParams(place="orchard", item="whistle", spot="reeds"),
    StoryParams(place="orchard", item="bell", spot="nest"),
]


ASP_RULES = r"""
compatible(I, bench) :- roundish(I).
compatible(I, nest)  :- light(I), shiny(I).
compatible(I, nest)  :- light(I), bright(I).
compatible(I, reeds) :- floatable(I).
compatible(I, reeds) :- light(I), cloth(I).

valid(P, I, S) :- place(P), item(I), spot(S), affords(P, S), compatible(I, S).

cause(I, bench, rolled) :- valid(_, I, bench).
cause(I, nest, bird)    :- valid(_, I, nest).
cause(I, reeds, wind)   :- valid(_, I, reeds).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for spot_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, spot_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact(tag, item_id))
    for spot_id in SPOTS:
        lines.append(asp.fact("spot", spot_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_cause(place: str, item: str, spot: str) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_place", place),
        asp.fact("chosen_item", item),
        asp.fact("chosen_spot", spot),
        "chosen_valid :- valid(P, I, S), chosen_place(P), chosen_item(I), chosen_spot(S).",
        "chosen_cause(C) :- chosen_valid, cause(I, S, C), chosen_item(I), chosen_spot(S).",
    ])
    model = asp.one_model(asp_program(extra, "#show chosen_cause/1."))
    out = asp.atoms(model, "chosen_cause")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: Piggie, Minus, and Chipper solve a tiny mystery with teamwork."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--spot", choices=SPOTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible detective cases derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.spot:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        spot = SPOTS[args.spot]
        if not (args.spot in place.affords and item_fits_spot(item, spot)):
            raise StoryError(explain_rejection(place, item, spot))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.spot is None or combo[2] == args.spot)
    ]
    if not combos:
        raise StoryError("(No valid detective case matches the given options.)")

    place_id, item_id, spot_id = rng.choice(sorted(combos))
    return StoryParams(place=place_id, item=item_id, spot=spot_id)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.spot not in SPOTS:
        raise StoryError(f"(Unknown spot: {params.spot})")
    place = PLACES[params.place]
    item = ITEMS[params.item]
    spot = SPOTS[params.spot]
    if (params.place, params.item, params.spot) not in set(valid_combos()):
        raise StoryError(explain_rejection(place, item, spot))

    world = tell(place, item, spot)
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for place_id, item_id, spot_id in sorted(py):
        py_cause = infer_cause(spot_id)
        cl_cause = asp_cause(place_id, item_id, spot_id)
        if py_cause != cl_cause:
            rc = 1
            print(f"MISMATCH cause for {(place_id, item_id, spot_id)}: python={py_cause} clingo={cl_cause}")
            break
    else:
        print(f"OK: cause model matches on {len(py)} valid cases.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        print("OK: curated smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on curated params: {err}")

    try:
        params = resolve_params(build_parser().parse_args([]), random.Random(123))
        params.seed = 123
        sample = generate(params)
        if not sample.story.strip():
            raise StoryError("(Default smoke test produced an empty story.)")
        print("OK: default seeded smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED on default generation: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show cause/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible detective cases:\n")
        for place_id, item_id, spot_id in combos:
            print(f"  {place_id:8} {item_id:8} {spot_id:6}  cause={infer_cause(spot_id)}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place}: missing {p.item} at {p.spot}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
