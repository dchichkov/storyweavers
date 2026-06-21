#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py
==========================================================

A standalone story world for a cautionary folk tale about wanting to *acquire*
a bright little treasure the wrong way, then learning the right way.

Premise
-------
In a small village, a child sees a lovely thing glinting in a risky place:
inside a thorn hedge, beside a deep well, or high in an old orchard tree.
The child longs to acquire it at once. An elder warns that greedy hands and
hasty climbing lead to scratches, slips, and tears. The child may listen and
use the proper way, or may snatch at the prize and suffer a fright before a
grown-up sets matters right.

This world models:
- typed entities with physical meters and emotional memes
- a simple forward-chaining causal engine
- a reasonableness gate over which place/item/method combinations make sense
- an inline ASP twin for the same gate and outcome model
- story-grounded QA and world-knowledge QA generated from world state

Run it
------
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py --place well --prize coin --method hand
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py --place tree --prize bell --method shake_branch
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/acquire_cautionary_folk_tale.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: str = ""
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "grandmother"}
        male = {"boy", "father", "man", "uncle", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def elder_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type or "elder")
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    risk: str
    danger: str
    can_reach_by_hand: bool
    climbable: bool
    hookable: bool
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
class Prize:
    id: str
    label: str
    phrase: str
    owner_kind: str
    gleam: str
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
class Method:
    id: str
    label: str
    sense: int
    needs_climb: bool = False
    success_with: set[str] = field(default_factory=set)
    fail_text: str = ""
    success_text: str = ""
    rescue_text: str = ""
    qa_text: str = ""
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


def _r_injury_causes_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["injury"] >= THRESHOLD and ("fear", "child") not in world.fired:
        world.fired.add(("fear", "child"))
        child.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_lost_property_causes_sadness(world: World) -> list[str]:
    out: list[str] = []
    prize = world.get("prize")
    child = world.get("child")
    if prize.meters["kept"] >= THRESHOLD and prize.owner and prize.owner != child.id:
        sig = ("sad_owner", prize.owner)
        if sig not in world.fired:
            world.fired.add(sig)
            owner = world.get(prize.owner)
            owner.memes["sad"] += 1
            out.append("__owner_sad__")
    return out


CAUSAL_RULES = [
    Rule(name="injury_causes_fear", tag="physical", apply=_r_injury_causes_fear),
    Rule(name="lost_property_causes_sadness", tag="social", apply=_r_lost_property_causes_sadness),
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


PLACES = {
    "hedge": Place(
        id="hedge",
        label="thorn hedge",
        phrase="a thorn hedge at the edge of the lane",
        risk="thorns",
        danger="The hedge kept its secrets behind hard, hooked thorns.",
        can_reach_by_hand=True,
        climbable=False,
        hookable=True,
        tags={"thorn", "hedge"},
    ),
    "well": Place(
        id="well",
        label="old well",
        phrase="an old stone well behind the mill",
        risk="deep water",
        danger="The well was dark below, and the stones were slick with moss.",
        can_reach_by_hand=False,
        climbable=False,
        hookable=True,
        tags={"well", "water"},
    ),
    "tree": Place(
        id="tree",
        label="orchard tree",
        phrase="the oldest tree in the orchard",
        risk="high branch",
        danger="Its branches reached high, and the bark flaked under hurried shoes.",
        can_reach_by_hand=False,
        climbable=True,
        hookable=False,
        tags={"tree", "orchard"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        id="ribbon",
        label="ribbon",
        phrase="a red ribbon bright as a berry skin",
        owner_kind="wind",
        gleam="fluttered like a little flame",
        tags={"ribbon"},
    ),
    "coin": Prize(
        id="coin",
        label="coin",
        phrase="a silver coin bright as a fish scale",
        owner_kind="miller",
        gleam="winked in the light",
        tags={"coin"},
    ),
    "bell": Prize(
        id="bell",
        label="bell",
        phrase="a brass bell warm as sunrise",
        owner_kind="goat",
        gleam="glowed among the leaves",
        tags={"bell"},
    ),
}

METHODS = {
    "hand": Method(
        id="hand",
        label="snatch by hand",
        sense=1,
        success_with={"hedge"},
        fail_text="reached in with bare fingers, quick and greedy",
        success_text="slipped careful fingers in and drew the treasure out",
        rescue_text="washed the scratches, bound the little cuts, and took the prize away until calmer hands returned",
        qa_text="tried to grab it with bare hands",
        tags={"bare_hands", "greed"},
    ),
    "hook": Method(
        id="hook",
        label="use a shepherd's hook",
        sense=3,
        success_with={"hedge", "well"},
        fail_text="fumbled with the hook and nearly dropped the treasure deeper",
        success_text="used a shepherd's hook and lifted the treasure free without getting too close",
        rescue_text="steadied the hook, drew the prize out safely, and set it back with its owner",
        qa_text="used a shepherd's hook to lift it out",
        tags={"hook", "tool"},
    ),
    "climb": Method(
        id="climb",
        label="climb carefully",
        sense=2,
        needs_climb=True,
        success_with={"tree"},
        fail_text="scrambled up too fast and the branch barked under a slipping foot",
        success_text="climbed slowly, tested each branch, and brought the treasure down in both hands",
        rescue_text="helped the child down branch by branch and hung the prize back where it belonged",
        qa_text="climbed slowly and brought it down",
        tags={"climb", "care"},
    ),
    "shake_branch": Method(
        id="shake_branch",
        label="shake the branch",
        sense=1,
        success_with=set(),
        fail_text="shook the branch so roughly that leaves flew and the prize fell the wrong way",
        success_text="",
        rescue_text="picked the frightened child up from the ground and showed that rough hands make rough trouble",
        qa_text="shook the branch roughly",
        tags={"tree", "rough"},
    ),
}

CHILD_NAMES = ["Anya", "Mira", "Toma", "Niko", "Ivo", "Lena", "Pavel", "Sava", "Mila", "Dara"]
ELDER_TYPES = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]
TRAITS = ["eager", "curious", "bright-eyed", "restless", "quick", "hopeful"]


def method_fits_place(method: Method, place: Place) -> bool:
    if method.id == "hand":
        return place.can_reach_by_hand
    if method.id in {"hook"}:
        return place.hookable
    if method.id in {"climb", "shake_branch"}:
        return place.climbable
    return False


def owner_for(prize: Prize) -> tuple[str, str, str]:
    if prize.owner_kind == "miller":
        return ("Owner", "miller", "the miller")
    if prize.owner_kind == "goat":
        return ("Owner", "goat", "the old goat")
    return ("Owner", "wind", "the wandering wind")


def proper_way(place: Place) -> str:
    if place.id == "hedge":
        return "a hook and patient hands"
    if place.id == "well":
        return "a hook and steady hands"
    return "slow feet and both hands on the trunk"


def valid_combo(place_id: str, prize_id: str, method_id: str) -> bool:
    if place_id not in PLACES or prize_id not in PRIZES or method_id not in METHODS:
        return False
    method = METHODS[method_id]
    place = PLACES[place_id]
    return method_fits_place(method, place)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for prize_id in PRIZES:
            for method_id, method in METHODS.items():
                if valid_combo(place_id, prize_id, method_id) and method.sense >= 1:
                    combos.append((place_id, prize_id, method_id))
    return combos


def sensible_methods(place_id: str) -> list[str]:
    place = PLACES[place_id]
    return sorted(
        mid for mid, m in METHODS.items()
        if method_fits_place(m, place) and m.sense >= SENSE_MIN
    )


def safe_outcome(method: Method) -> bool:
    return method.sense >= SENSE_MIN


def explain_rejection(place: Place, method: Method) -> str:
    if method.id == "hand" and not place.can_reach_by_hand:
        return (f"(No story: {place.label} cannot be safely or honestly reached by hand. "
                "The child would only paw at empty air or lean into danger.)")
    if method.id in {"hook"} and not place.hookable:
        return (f"(No story: a hook makes sense at the hedge or well, but not at the {place.label}.)")
    if method.id in {"climb", "shake_branch"} and not place.climbable:
        return (f"(No story: climbing belongs in a tree, not at the {place.label}.)")
    return "(No story: this place and method do not belong together.)"


def explain_method(method: Method) -> str:
    good = ", ".join(sorted(mid for mid, m in METHODS.items() if m.sense >= SENSE_MIN))
    return (f"(Refusing method '{method.id}': it scores too low on common sense "
            f"(sense={method.sense} < {SENSE_MIN}). Try one of: {good}.)")


def predict_attempt(world: World, place: Place, method: Method) -> dict:
    sim = world.copy()
    attempt(sim, place, method, narrate=False)
    child = sim.get("child")
    return {
        "injury": child.meters["injury"],
        "fear": child.memes["fear"],
        "kept": sim.get("prize").meters["kept"],
    }


def opening(world: World, child: Entity, elder: Entity, place: Place, prize: Prize, owner: Entity) -> None:
    child.memes["wonder"] += 1
    world.say(
        f"In a village where ovens glowed at dusk and geese crossed the road as if they owned it, "
        f"there lived {child.id}, a {next((t for t in child.traits if t), 'little')} {child.type}."
    )
    world.say(
        f"One evening {child.pronoun()} walked with {child.pronoun('possessive')} {elder.elder_word} past "
        f"{place.phrase}. There {prize.phrase} {prize.gleam}, and {child.id} longed to acquire it at once."
    )
    world.say(place.danger)
    if owner.type == "wind":
        world.say("Some things in old tales seem ownerless, yet even the wind expects courtesy.")
    elif owner.type == "goat":
        world.say("It had once hung from the old goat's collar, and every child in the village knew its sound.")
    else:
        world.say("The miller had lost it at dawn, and had searched for it all day with a worried face.")


def warning(world: World, child: Entity, elder: Entity, place: Place, method: Method, prize: Prize) -> None:
    pred = predict_attempt(world, place, method)
    world.facts["predicted_injury"] = pred["injury"]
    child.memes["desire"] += 1
    elder.memes["care"] += 1
    world.say(
        f'"Do not hurry your hands," said the {elder.elder_word}. '
        f'"If you would acquire a thing, you must use {proper_way(place)}, not greedy fingers."'
    )
    if pred["injury"] >= THRESHOLD:
        world.say(
            f'The old one pointed toward {place.label} and added, '
            f'"That way leads to {place.risk} and tears before supper."'
        )


def choose_safe(world: World, child: Entity, elder: Entity, place: Place, method: Method, owner: Entity, prize: Prize) -> None:
    child.memes["obedience"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{child.id} looked again at the shining {prize.label}, then at the elder's steady hands, "
        f"and shame cooled the hot little wish in {child.pronoun('possessive')} chest."
    )
    if owner.type in {"miller", "goat"}:
        world.say(
            f'"Let us return it properly," said {child.id}. Together they {method.success_text}, '
            f"and carried it to {owner.label}."
        )
        prize.owner = owner.id
        prize.meters["returned"] += 1
        owner.memes["gratitude"] += 1
        child.memes["kindness"] += 1
        world.say(
            f"{owner.label.capitalize()} thanked the child and let {child.pronoun('object')} touch it for a moment, "
            f"so {child.id} learned that asking kindly can bring a brighter joy than grabbing."
        )
    else:
        world.say(
            f"Together they {method.success_text}. Yet {child.id} did not tie the {prize.label} into a sleeve or pocket."
        )
        prize.meters["returned"] += 1
        child.memes["wisdom"] += 1
        world.say(
            f"The elder looped it back where the hedge could keep it from the road, "
            f"and the ribbon fluttered there as if pleased by the gentle choice."
        )


def attempt(world: World, place: Place, method: Method, narrate: bool = True) -> None:
    child = world.get("child")
    prize = world.get("prize")
    child.memes["greed"] += 1
    if method.sense < SENSE_MIN:
        child.meters["injury"] += 1
        prize.meters["kept"] += 1
        if place.id == "hedge":
            child.meters["scratched"] += 1
        elif place.id == "well":
            child.meters["slipped"] += 1
        elif place.id == "tree":
            child.meters["fell"] += 1
        propagate(world, narrate=narrate)
    else:
        prize.meters["lifted"] += 1
        if prize.owner and prize.owner != child.id:
            prize.meters["returned"] += 1
        else:
            prize.meters["kept"] += 1
        child.memes["pride"] += 1
        propagate(world, narrate=narrate)


def foolish_turn(world: World, child: Entity, place: Place, method: Method, prize: Prize) -> None:
    attempt(world, place, method, narrate=False)
    if place.id == "hedge":
        pain = "The thorns bit into the child's wrist and left thin red lines."
    elif place.id == "well":
        pain = "Moss turned the stone sly under the child's shoes, and one foot slid hard against the rim."
    else:
        pain = "A flaking branch rolled under the child's foot, and down came the child in a shower of leaves."
    world.say(
        f"But desire ran faster than good sense. {child.id} {method.fail_text}, hoping to acquire the {prize.label} before another breath had passed."
    )
    world.say(pain)
    world.say(
        f"For one frightened blink, the bright little {prize.label} was in {child.pronoun('possessive')} hand, "
        f"yet it did not feel like treasure anymore."
    )


def rescue(world: World, child: Entity, elder: Entity, owner: Entity, place: Place, method: Method, prize: Prize) -> None:
    child.memes["greed"] = 0.0
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f"The {elder.elder_word} came at once, not with shouting, but with the speed of a hen gathering a chick from rain."
    )
    world.say(
        f"{elder.pronoun().capitalize()} {method.rescue_text}."
    )
    prize.meters["kept"] = 0.0
    prize.meters["returned"] += 1
    prize.owner = owner.id
    if owner.type in {"miller", "goat"}:
        owner.memes["gratitude"] += 1
    world.say(
        f'"A hand that grabs only grows smaller," said the {elder.elder_word}. '
        f'"A hand that asks, waits, and returns what is not its own may hold peace."'
    )
    if owner.type == "wind":
        world.say(
            f"{child.id} watched the ribbon stir again in the hedge and understood that not every lovely thing must be carried home."
        )
    else:
        world.say(
            f"When the {prize.label} was placed back with {owner.label}, the child felt lighter than when trying to carry it away."
        )


def ending(world: World, child: Entity, elder: Entity, owner: Entity, prize: Prize, place: Place, outcome: str) -> None:
    world.para()
    if outcome == "safe":
        world.say(
            f"After that evening, when {child.id} saw bright things in brambles, wells, or trees, "
            f"{child.pronoun()} did not rush to acquire them by force."
        )
        world.say(
            f"{child.pronoun().capitalize()} remembered the old road, the elder's voice, and the quiet shine of the {prize.label}, "
            f"and chose the slower path that leaves both hands and heart unhurt."
        )
    else:
        world.say(
            f"After that day, whenever anything glimmered from a hard place, {child.id} felt the old sting return to memory."
        )
        world.say(
            f"So in that village people would tell the tale at dusk: whoever longs to acquire a bright thing with a greedy hand may gain a fright instead, "
            f"but whoever asks and waits walks home whole."
        )


def tell(
    *,
    place: Place,
    prize_cfg: Prize,
    method: Method,
    child_name: str = "Anya",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "curious",
) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        phrase=child_name,
        role="child",
        traits=[trait],
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label=f"the {elder_type}",
        phrase=f"the {elder_type}",
        role="elder",
    ))
    owner_id, owner_type, owner_label = owner_for(prize_cfg)
    owner = world.add(Entity(
        id=owner_id,
        kind="character",
        type=owner_type,
        label=owner_label,
        phrase=owner_label,
        role="owner",
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.id,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        role="prize",
        owner=owner.id,
    ))
    place_ent = world.add(Entity(
        id="place",
        kind="thing",
        type=place.id,
        label=place.label,
        phrase=place.phrase,
        role="place",
    ))
    # initialize fields any rule may read before propagation
    child.meters["injury"] += 0.0
    child.meters["scratched"] += 0.0
    child.meters["slipped"] += 0.0
    child.meters["fell"] += 0.0
    child.memes["fear"] += 0.0
    child.memes["relief"] += 0.0
    child.memes["lesson"] += 0.0
    prize.meters["kept"] += 0.0
    prize.meters["returned"] += 0.0
    owner.memes["sad"] += 0.0
    owner.memes["gratitude"] += 0.0
    world.facts["child_name"] = child_name

    opening(world, child, elder, place, prize_cfg, owner)
    world.para()
    warning(world, child, elder, place, method, prize_cfg)

    if safe_outcome(method):
        world.say(
            f"{child_name} lowered {child.pronoun('possessive')} hand. The wish to acquire the {prize_cfg.label} was still there, "
            f"but it no longer ruled the whole body."
        )
        world.para()
        choose_safe(world, child, elder, place, method, owner, prize_cfg)
        outcome = "safe"
    else:
        world.say(
            f'{child_name} nodded with {child.pronoun("possessive")} mouth, but not with {child.pronoun("possessive")} heart.'
        )
        world.para()
        foolish_turn(world, child, place, method, prize_cfg)
        world.para()
        rescue(world, child, elder, owner, place, method, prize_cfg)
        outcome = "oops"

    ending(world, child, elder, owner, prize_cfg, place, outcome)
    world.facts.update(
        child=child,
        elder=elder,
        owner=owner,
        prize_cfg=prize_cfg,
        prize=prize,
        place_cfg=place,
        place=place_ent,
        method=method,
        outcome=outcome,
        injury=child.meters["injury"] >= THRESHOLD,
        fear=child.memes["fear"] >= THRESHOLD,
        returned=prize.meters["returned"] >= THRESHOLD,
        owner_sad=owner.memes["sad"] >= THRESHOLD,
        owner_grateful=owner.memes["gratitude"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    place: str
    prize: str
    method: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
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
    "thorn": [(
        "Why are thorns dangerous?",
        "Thorns are sharp points on some plants. They can scratch skin and catch on clothes very quickly."
    )],
    "well": [(
        "Why is an old well dangerous?",
        "An old well can be deep and slippery. Leaning over it can make a person fall or drop something into the dark water."
    )],
    "tree": [(
        "Why should you climb a tree slowly?",
        "A tree has branches that may bend, crack, or feel slick. Going slowly helps you test where your feet and hands are safe."
    )],
    "hook": [(
        "What is a shepherd's hook for?",
        "A shepherd's hook is a long curved stick or tool used to catch or lift something from a little distance. It helps a person reach without getting too close."
    )],
    "bare_hands": [(
        "Why can grabbing with bare hands be a bad idea?",
        "Bare hands are quick, but they are easy to hurt. When people grab in a hurry, they often miss danger that patient eyes would notice."
    )],
    "greed": [(
        "What does greed mean?",
        "Greed means wanting something so much that you stop thinking about what is right or safe. In cautionary tales, greed often brings trouble faster than joy."
    )],
    "care": [(
        "Why is asking and waiting wiser than grabbing?",
        "Asking and waiting give people time to notice danger and remember who something belongs to. That makes both the hands and the heart gentler."
    )],
    "ribbon": [(
        "What is a ribbon?",
        "A ribbon is a long narrow strip of cloth used for tying or decorating things. It can flutter and catch the eye in the wind."
    )],
    "coin": [(
        "What is a coin?",
        "A coin is a small piece of metal used as money. Because it is hard and shiny, people can spot it even in dirt or grass."
    )],
    "bell": [(
        "What is a bell used for?",
        "A bell rings when it moves. People tie little bells to animals or doors so they can hear where something is."
    )],
}
KNOWLEDGE_ORDER = ["thorn", "well", "tree", "hook", "bare_hands", "greed", "care", "ribbon", "coin", "bell"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    place = f["place_cfg"]
    prize = f["prize_cfg"]
    method = f["method"]
    if f["outcome"] == "safe":
        return [
            f'Write a short folk tale for a small child that includes the word "acquire" and a warning from an elder.',
            f"Tell a cautionary village tale where {world.facts['child_name']} wants to acquire a {prize.label} from a {place.label}, "
            f"but listens to {child.pronoun('possessive')} {elder.elder_word} and chooses the proper way.",
            f"Write a gentle folk-style story about a child, a shining treasure, and the lesson that patient hands are better than greedy ones.",
        ]
    return [
        f'Write a cautionary folk tale that includes the word "acquire" and shows a child trying to seize a bright object too fast.',
        f"Tell a village tale where {world.facts['child_name']} wants to acquire a {prize.label} from a {place.label}, ignores a warning, and learns a sharp lesson.",
        f"Write a simple folk tale with an elder's warning, a reckless choice, and an ending that teaches children to ask and wait.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    owner = f["owner"]
    prize = f["prize_cfg"]
    place = f["place_cfg"]
    method = f["method"]
    who = world.facts["child_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {who}, a child who wanted to acquire a shining {prize.label}, and the {elder.elder_word} who walked beside {child.pronoun('object')}. "
            f"The story follows the choice between a greedy reach and a patient one."
        ),
        (
            f"Why did {who} want the {prize.label}?",
            f"{who} wanted it because it shone so beautifully in {place.phrase}. "
            f"In the tale, the bright gleam woke wonder first, and then desire."
        ),
        (
            f"What warning did the {elder.elder_word} give?",
            f"The elder said that if a person would acquire a thing, it must be done with the proper way, not greedy fingers. "
            f"The warning tied safety and kindness together, because the place itself was risky."
        ),
    ]
    if f["outcome"] == "safe":
        if owner.type in {"miller", "goat"}:
            owner_phrase = f"{owner.label}"
        else:
            owner_phrase = "the place where even the wind seemed to keep it"
        qa.append((
            f"How did {who} solve the problem?",
            f"{who} listened and used {method.label} instead of rushing. "
            f"That let the child handle the {prize.label} safely and return it properly to {owner_phrase}."
        ))
        qa.append((
            f"What lesson did {who} learn?",
            f"{who} learned that asking, waiting, and using the proper tool bring a better ending than grabbing. "
            f"The happy ending proves that a calmer choice can still satisfy wonder without hurting anyone."
        ))
    else:
        injury = "got hurt" if f["injury"] else "was frightened"
        qa.append((
            f"What happened when {who} tried to take the {prize.label} the wrong way?",
            f"{who} {injury} while trying to {method.qa_text}. "
            f"The danger came true because the child hurried past the elder's warning and the place was not forgiving."
        ))
        qa.append((
            f"How did the {elder.elder_word} help?",
            f"The elder came quickly, cared for the child, and made sure the {prize.label} was put back properly. "
            f"That rescue changed the moment from greedy grabbing into a lesson about safety and respect."
        ))
        qa.append((
            f"What is the story's lesson?",
            f"The tale teaches that whoever tries to acquire a lovely thing with a greedy hand may win pain instead of joy. "
            f"It also teaches that patient asking and proper care leave both hands and heart in better shape."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set(world.facts["place_cfg"].tags) | set(world.facts["prize_cfg"].tags) | set(world.facts["method"].tags)
    tags.add("care")
    if world.facts["outcome"] != "safe":
        tags.add("greed")
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
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="hedge",
        prize="ribbon",
        method="hook",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        trait="curious",
        seed=1,
    ),
    StoryParams(
        place="well",
        prize="coin",
        method="hook",
        child_name="Niko",
        child_type="boy",
        elder_type="grandfather",
        trait="eager",
        seed=2,
    ),
    StoryParams(
        place="tree",
        prize="bell",
        method="climb",
        child_name="Lena",
        child_type="girl",
        elder_type="aunt",
        trait="hopeful",
        seed=3,
    ),
    StoryParams(
        place="hedge",
        prize="ribbon",
        method="hand",
        child_name="Ivo",
        child_type="boy",
        elder_type="mother",
        trait="quick",
        seed=4,
    ),
    StoryParams(
        place="tree",
        prize="bell",
        method="shake_branch",
        child_name="Dara",
        child_type="girl",
        elder_type="father",
        trait="restless",
        seed=5,
    ),
]


ASP_RULES = r"""
% place-method fit
fits(P, hand)         :- place(P), by_hand(P).
fits(P, hook)         :- place(P), hookable(P).
fits(P, climb)        :- place(P), climbable(P).
fits(P, shake_branch) :- place(P), climbable(P).

valid(P, Z, M) :- place(P), prize(Z), method(M), fits(P, M).

sensible(M) :- method(M), sense(M, S), sense_min(Min), S >= Min.

outcome(safe) :- chosen_method(M), sensible(M).
outcome(oops) :- chosen_method(M), not sensible(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.can_reach_by_hand:
            lines.append(asp.fact("by_hand", pid))
        if place.hookable:
            lines.append(asp.fact("hookable", pid))
        if place.climbable:
            lines.append(asp.fact("climbable", pid))
    for prize_id in PRIZES:
        lines.append(asp.fact("prize", prize_id))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_method", params.method)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    return "safe" if safe_outcome(METHODS[params.method]) else "oops"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Cautionary folk-tale storyworld: a child longs to acquire a bright thing and must choose patience or greed."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--method", choices=sorted(METHODS))
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=sorted(ELDER_TYPES))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.method:
        place = PLACES[args.place]
        method = METHODS[args.method]
        if not valid_combo(args.place, args.prize or next(iter(PRIZES)), args.method):
            raise StoryError(explain_rejection(place, method))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.prize is None or c[1] == args.prize)
        and (args.method is None or c[2] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prize_id, method_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(CHILD_NAMES)
    elder_type = args.elder_type or rng.choice(ELDER_TYPES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        prize=prize_id,
        method=method_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if not valid_combo(params.place, params.prize, params.method):
        raise StoryError(explain_rejection(PLACES[params.place], METHODS[params.method]))

    world = tell(
        place=PLACES[params.place],
        prize_cfg=PRIZES[params.prize],
        method=METHODS[params.method],
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        trait=params.trait,
    )
    return StorySample(
        params=params,
        story=world.render().replace("child", params.child_name),
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
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    py_sensible = {mid for mid, m in METHODS.items() if m.sense >= SENSE_MIN}
    cl_sensible = set(asp_sensible())
    if py_sensible == cl_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(cl_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {s}")
            break
    bad = [p for p in cases if asp_outcome(p) != outcome_of(p)]
    if not bad:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(bad)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, prize, method) combos:\n")
        for place, prize, method in combos:
            print(f"  {place:8} {prize:7} {method}")
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
            header = f"### {p.child_name}: {p.place}, {p.prize}, {p.method} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
