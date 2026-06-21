#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py
=======================================================================

A standalone story world for a nursery-rhyme-flavored quest with humor and a
bad ending. Grace sets out to carry a treat to a tiny party, meets one silly
hazard on the way, and the quest goes wrong in a way that is funny first and
disappointing after.

The world model is small on purpose:

- Grace has a quest, pride, alarm, embarrassment, and a bit of laugh-through-it.
- A treat has physical damage that can become smeared, nibbled, slumped, or
  fully ruined.
- A route affords one or more hazards.
- A carrier gives some protection, but not enough to make the ending happy.
  The best cases are merely "messy bad"; the worst are "ruined bad".

Run it
------
    python storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py --qa
    python storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/grace_quest_humor_bad_ending_nursery_rhyme.py --verify
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "hen", "goose_female"}
        male = {"boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Destination:
    id: str
    label: str
    phrase: str
    host: str
    closing_image: str
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
class Treat:
    id: str
    label: str
    phrase: str
    vulnerable_to: set[str]
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
class Route:
    id: str
    label: str
    phrase: str
    affords: set[str]
    roughness: int
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
class Hazard:
    id: str
    label: str
    phrase: str
    severity: int
    verb: str
    aftermath: str
    sound: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    stability: int
    covers: set[str]
    sense: int
    comic: str
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
class StoryParams:
    destination: str
    treat: str
    route: str
    hazard: str
    carrier: str
    parent: str
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


def carrier_bonus(carrier: Carrier, hazard_id: str) -> int:
    return 1 if hazard_id in carrier.covers else 0


def danger_score(route: Route, hazard: Hazard, carrier: Carrier) -> int:
    return route.roughness + hazard.severity - carrier.stability - carrier_bonus(carrier, hazard.id)


def outcome_of(params: StoryParams) -> str:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    route = ROUTES[params.route]
    hazard = HAZARDS[params.hazard]
    carrier = CARRIERS[params.carrier]
    if hazard.id not in route.affords:
        raise StoryError(explain_route_hazard(route, hazard))
    if hazard.id not in TREATS[params.treat].vulnerable_to:
        raise StoryError(explain_treat_hazard(TREATS[params.treat], hazard))
    if carrier.sense < SENSE_MIN:
        raise StoryError(explain_carrier(carrier.id))
    return "ruined" if danger_score(route, hazard, carrier) >= 3 else "messy"


def _r_damage(world: World) -> list[str]:
    treat = world.get("treat")
    if treat.meters["encounter"] < THRESHOLD:
        return []
    sig = ("damage", world.facts["hazard_id"])
    if sig in world.fired:
        return []
    world.fired.add(sig)
    score = max(1, int(world.facts["danger"]))
    hazard_id = world.facts["hazard_id"]
    if hazard_id not in set(treat.attrs.get("vulnerable_to", set())):
        return []
    treat.meters["damage"] += score
    if hazard_id == "gust":
        treat.meters["smeared"] += 1
    elif hazard_id == "goose":
        treat.meters["nibbled"] += 1
    elif hazard_id == "bump":
        treat.meters["slumped"] += 1
    return ["__damage__"]


def _r_bad_ending(world: World) -> list[str]:
    treat = world.get("treat")
    grace = world.get("Grace")
    if treat.meters["damage"] < THRESHOLD:
        return []
    sig = ("bad_end",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    grace.memes["alarm"] += 1
    grace.memes["embarrassment"] += 1
    grace.memes["grace"] += 1
    grace.memes["laughter"] += 1
    world.get("quest").meters["failed"] += 1
    if treat.meters["damage"] >= 3:
        treat.meters["ruined"] += 1
    return ["__bad__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="damage", tag="physical", apply=_r_damage),
    Rule(name="bad_ending", tag="social", apply=_r_bad_ending),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def introduce(world: World, grace: Entity, parent: Entity, treat: Treat,
              destination: Destination, carrier: Carrier) -> None:
    grace.memes["hope"] += 1
    grace.memes["pride"] += 1
    world.say(
        f"Little Grace tied on her bonnet with as much grace as she could show. "
        f"{parent.label_word.capitalize()} set {treat.phrase} in {carrier.phrase} "
        f"and said it was meant for {destination.phrase}."
    )
    world.say(
        f'"Take it there before the kettle sings," said {parent.label_word}. '
        f'Grace bobbed a curtsy and called it a quest.'
    )


def set_out(world: World, grace: Entity, route: Route, destination: Destination,
            carrier: Carrier) -> None:
    world.say(
        f"Off went Grace by {route.phrase}, step and skip, tip and trip. "
        f"{carrier.comic}"
    )
    world.say(
        f"She meant to reach {destination.label} with a neat small smile and a very grand heart."
    )


def boast(world: World, grace: Entity, treat: Treat) -> None:
    grace.memes["pride"] += 1
    world.say(
        f'"No wobble shall trouble me," sang Grace. '
        f'She peeped at the {treat.label} and walked as if she were queen of the lane.'
    )


def encounter(world: World, grace: Entity, treat_ent: Entity, route: Route,
              hazard: Hazard, carrier: Carrier) -> None:
    treat_ent.meters["encounter"] += 1
    world.say(
        f"But by {route.label} there came {hazard.phrase}. "
        f'{hazard.sound}! It happened all at once.'
    )
    propagate(world, narrate=False)


def describe_damage(world: World, treat: Treat, hazard: Hazard) -> None:
    treat_ent = world.get("treat")
    if treat_ent.meters["ruined"] >= THRESHOLD:
        if hazard.id == "goose":
            world.say(
                f"The goose gave a greedy bob and a gobble-gobble grin. "
                f"By the time Grace pulled the basket back, the {treat.label} was not a party treat at all."
            )
        elif hazard.id == "gust":
            world.say(
                f"The wind whisked and frisked till cream met chin and sleeve and sky. "
                f"The {treat.label} came down in a woeful blot."
            )
        else:
            world.say(
                f"The path gave a thump, the carrier gave a jump, and the {treat.label} folded in on itself. "
                f"It landed with a sad little splat."
            )
    else:
        if hazard.id == "goose":
            world.say(
                f"The goose only stole a mouthful, but it left the top all toothy and queer. "
                f"The sight was so rude that Grace nearly laughed before she sighed."
            )
        elif hazard.id == "gust":
            world.say(
                f"The wind did not take all of it, but it licked the topping sideways. "
                f"The {treat.label} leaned like a hat in a storm."
            )
        else:
            world.say(
                f"The bump did not toss it clear away, but it slumped and slid to one side. "
                f"The {treat.label} looked more sorry than splendid."
            )


def react(world: World, grace: Entity, parent: Entity) -> None:
    if grace.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f'Grace stopped, blinked twice, and made a small face. "Oh dear," she said, '
            f'"there goes my grand parade."'
        )
    if grace.memes["laughter"] >= THRESHOLD:
        world.say(
            f"Even then, a bubble of laughter rose in her chest, because the whole mishap was so silly to see."
        )
    world.say(
        f"Still, she picked up what she could with careful grace and went on, because a quest once started must be walked to its end."
    )


def bad_arrival(world: World, grace: Entity, destination: Destination, treat: Treat) -> None:
    treat_ent = world.get("treat")
    if treat_ent.meters["ruined"] >= THRESHOLD:
        world.say(
            f"At last she reached {destination.phrase}, but there was no fine treat left to set down. "
            f"{destination.host.capitalize()} stared, the cups stayed empty, and the merry little party went thin as steam."
        )
        world.say(
            f"{destination.closing_image} Grace curtsied anyway, but her quest had ended in crumbs."
        )
    else:
        world.say(
            f"At last she reached {destination.phrase} and set down the poor bent {treat.label}. "
            f"It was still there, but not fit for showing off."
        )
        world.say(
            f"{destination.closing_image} They nibbled politely, yet the feast felt spoiled, and Grace knew the quest had ended badly all the same."
        )


def tell(destination: Destination, treat: Treat, route: Route, hazard: Hazard,
         carrier: Carrier, parent_type: str = "mother") -> World:
    world = World()
    grace = world.add(Entity(id="Grace", kind="character", type="girl", role="hero", label="Grace"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    quest = world.add(Entity(id="quest", type="quest", label="the quest"))
    treat_ent = world.add(
        Entity(
            id="treat",
            type="treat",
            label=treat.label,
            phrase=treat.phrase,
            attrs={"vulnerable_to": set(treat.vulnerable_to)},
        )
    )
    world.add(Entity(id="route", type="route", label=route.label))
    world.add(Entity(id="hazard", type="hazard", label=hazard.label))
    world.add(Entity(id="carrier", type="carrier", label=carrier.label, attrs={"covers": set(carrier.covers)}))
    world.add(Entity(id="destination", type="destination", label=destination.label))

    world.facts.update(
        destination=destination,
        treat_cfg=treat,
        route_cfg=route,
        hazard_cfg=hazard,
        carrier_cfg=carrier,
        grace=grace,
        parent=parent,
        hazard_id=hazard.id,
        danger=danger_score(route, hazard, carrier),
        outcome="ruined" if danger_score(route, hazard, carrier) >= 3 else "messy",
    )

    introduce(world, grace, parent, treat, destination, carrier)
    set_out(world, grace, route, destination, carrier)
    world.para()
    boast(world, grace, treat)
    encounter(world, grace, treat_ent, route, hazard, carrier)
    describe_damage(world, treat, hazard)
    react(world, grace, parent)
    world.para()
    bad_arrival(world, grace, destination, treat)

    world.facts.update(
        damaged=treat_ent.meters["damage"] >= THRESHOLD,
        ruined=treat_ent.meters["ruined"] >= THRESHOLD,
        failed=world.get("quest").meters["failed"] >= THRESHOLD,
    )
    return world


DESTINATIONS = {
    "duck_tea": Destination(
        id="duck_tea",
        label="the duck tea",
        phrase="the duck tea by the reeds",
        host="the ducks",
        closing_image="The ducks looked at one another, the saucers shone, and the reeds nodded as if they knew better.",
        tags={"tea_party", "duck"},
    ),
    "moon_gate": Destination(
        id="moon_gate",
        label="the moon gate picnic",
        phrase="the moon gate picnic under the willow",
        host="the gate-keepers",
        closing_image="The willow leaves made a hush-hush ring above the cloth, and the plates waited for a treat that never truly came.",
        tags={"picnic", "willow"},
    ),
    "plum_fair": Destination(
        id="plum_fair",
        label="the plum fair",
        phrase="the plum fair in the village square",
        host="the fair folk",
        closing_image="The fair bunting fluttered over the square while the best plate sat sadly bare.",
        tags={"fair", "village"},
    ),
}

TREATS = {
    "tart": Treat(
        id="tart",
        label="tart",
        phrase="a wobbling plum tart",
        vulnerable_to={"bump", "goose"},
        tags={"tart", "pastry"},
    ),
    "jelly": Treat(
        id="jelly",
        label="jelly mold",
        phrase="a trembling jelly mold",
        vulnerable_to={"gust", "bump"},
        tags={"jelly", "wobble"},
    ),
    "seed_cake": Treat(
        id="seed_cake",
        label="seed cake",
        phrase="a seed cake with sugared top",
        vulnerable_to={"goose", "gust"},
        tags={"cake", "seed"},
    ),
}

ROUTES = {
    "cobble_lane": Route(
        id="cobble_lane",
        label="the cobble lane",
        phrase="the cobble lane past the pump",
        affords={"bump", "goose"},
        roughness=2,
        tags={"lane", "cobbles"},
    ),
    "windy_hill": Route(
        id="windy_hill",
        label="the windy hill",
        phrase="the windy hill above the mill",
        affords={"gust"},
        roughness=2,
        tags={"hill", "wind"},
    ),
    "plank_bridge": Route(
        id="plank_bridge",
        label="the plank bridge",
        phrase="the plank bridge over the brook",
        affords={"bump", "gust"},
        roughness=3,
        tags={"bridge", "brook"},
    ),
}

HAZARDS = {
    "gust": Hazard(
        id="gust",
        label="wind gust",
        phrase="a gust with naughty fingers",
        severity=2,
        verb="blew",
        aftermath="The topping went sideways.",
        sound="Whoof",
        tags={"wind"},
    ),
    "goose": Hazard(
        id="goose",
        label="goose",
        phrase="a fat white goose with a hungry eye",
        severity=2,
        verb="pecked",
        aftermath="A beak took a bite.",
        sound="Honk-honk",
        tags={"goose"},
    ),
    "bump": Hazard(
        id="bump",
        label="hard bump",
        phrase="a rude old bump underfoot",
        severity=1,
        verb="jolted",
        aftermath="The treat sagged to one side.",
        sound="Bump",
        tags={"bump"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a basket lined with a napkin",
        stability=2,
        covers={"gust", "goose"},
        sense=3,
        comic="The basket bumped against her skirt as if it wanted to march too.",
        tags={"basket"},
    ),
    "tin": Carrier(
        id="tin",
        label="cake tin",
        phrase="a round cake tin",
        stability=1,
        covers={"gust"},
        sense=3,
        comic="The tin gave a little ping at every step, like a shy bell.",
        tags={"tin"},
    ),
    "tray": Carrier(
        id="tray",
        label="tray",
        phrase="a shiny tray",
        stability=1,
        covers=set(),
        sense=2,
        comic="The tray shone so brightly that Grace kept admiring her own determined nose in it.",
        tags={"tray"},
    ),
    "wagon": Carrier(
        id="wagon",
        label="toy wagon",
        phrase="a toy wagon with red wheels",
        stability=0,
        covers={"goose"},
        sense=2,
        comic="The wagon squeaked behind her as though it had opinions about the whole mission.",
        tags={"wagon"},
    ),
    "head": Carrier(
        id="head",
        label="head-balance",
        phrase="her own head under a folded cloth",
        stability=0,
        covers=set(),
        sense=1,
        comic="She looked like a tiny queen balancing supper on her crown.",
        tags={"head"},
    ),
}


def sensible_carriers() -> list[Carrier]:
    return [c for c in CARRIERS.values() if c.sense >= SENSE_MIN]


def hazard_at_risk(route: Route, hazard: Hazard, treat: Treat) -> bool:
    return hazard.id in route.affords and hazard.id in treat.vulnerable_to


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for dest_id in DESTINATIONS:
        for treat_id, treat in TREATS.items():
            for route_id, route in ROUTES.items():
                for hazard_id, hazard in HAZARDS.items():
                    if not hazard_at_risk(route, hazard, treat):
                        continue
                    for carrier_id, carrier in CARRIERS.items():
                        if carrier.sense >= SENSE_MIN:
                            out.append((dest_id, treat_id, route_id, hazard_id, carrier_id))
    return out


def explain_treat_hazard(treat: Treat, hazard: Hazard) -> str:
    return (
        f"(No story: {treat.phrase} is not the sort of treat this {hazard.label} would reasonably ruin here. "
        f"Pick a treat that is vulnerable to {hazard.id}.)"
    )


def explain_route_hazard(route: Route, hazard: Hazard) -> str:
    return (
        f"(No story: {route.phrase} does not naturally give us {hazard.phrase}. "
        f"Pick a route that really affords that mishap.)"
    )


def explain_carrier(cid: str) -> str:
    carrier = CARRIERS[cid]
    better = ", ".join(sorted(c.id for c in sensible_carriers()))
    return (
        f"(Refusing carrier '{cid}': {carrier.label} is too silly to count as a sensible starting plan "
        f"(sense={carrier.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


KNOWLEDGE = {
    "goose": [
        (
            "Why do geese get into food?",
            "Geese are curious birds, and if they see something tasty they may peck at it quickly. That is why people keep picnic food covered around them."
        )
    ],
    "wind": [
        (
            "Why can wind spoil food?",
            "Wind can tip, blow, or smear light food, especially if it has cream or sugar on top. A cover helps because it blocks the gust from touching the food."
        )
    ],
    "bump": [
        (
            "Why does bumpy ground make carrying things hard?",
            "Bumpy ground makes your hands and feet jolt. When that happens, a wobbly treat can slide or slump."
        )
    ],
    "basket": [
        (
            "Why is a basket better than a tray for carrying a treat?",
            "A basket helps hold things in place, and a cloth inside can stop small slips. It still cannot fix every problem on a rough path."
        )
    ],
    "tin": [
        (
            "What does a cake tin do?",
            "A cake tin gives a treat hard sides, so wind cannot lick the top so easily. It does not make a bumpy bridge smooth."
        )
    ],
    "tray": [
        (
            "What is hard about carrying food on a tray?",
            "A tray is flat and open, so food can slide if you wobble. It is fine for careful steps, but it gives little protection from bumps or greedy birds."
        )
    ],
    "wagon": [
        (
            "Why can a toy wagon be funny but risky?",
            "A toy wagon looks helpful, but small wheels rattle over rough places. That can shake a treat even when the plan seems clever at first."
        )
    ],
    "quest": [
        (
            "What is a quest?",
            "A quest is a special job or journey with a goal at the end. In stories, the person on the quest has to keep going even when trouble pops up."
        )
    ],
    "grace": [
        (
            "What does grace mean?",
            "Grace can mean moving in a calm, careful, lovely way. It can also mean staying gentle after something goes wrong."
        )
    ],
}
KNOWLEDGE_ORDER = ["quest", "grace", "goose", "wind", "bump", "basket", "tin", "tray", "wagon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    destination = f["destination"]
    treat = f["treat_cfg"]
    route = f["route_cfg"]
    hazard = f["hazard_cfg"]
    carrier = f["carrier_cfg"]
    return [
        (
            f'Write a short nursery-rhyme-style story for a 3-to-5-year-old about Grace on a quest '
            f'to carry {treat.phrase} by {route.phrase}, with a funny mishap and a bad ending. '
            f'Include the word "grace".'
        ),
        (
            f"Tell a playful cautionary tale where Grace proudly carries {treat.phrase} in {carrier.phrase} "
            f"toward {destination.phrase}, but {hazard.phrase} ruins the plan."
        ),
        (
            f"Write a rhyme-like story with a silly middle turn and a disappointed ending, where Grace keeps walking "
            f"with grace even after her quest goes wrong."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    route = f["route_cfg"]
    treat = f["treat_cfg"]
    hazard = f["hazard_cfg"]
    carrier = f["carrier_cfg"]
    destination = f["destination"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            "It is about Grace, a little girl on a tiny quest to carry a treat to a party. She wants to look grand and finish the job properly."
        ),
        (
            "What was Grace trying to do?",
            f"Grace was trying to carry {treat.phrase} along {route.phrase} to {destination.phrase}. The whole trip was her quest."
        ),
        (
            "What went wrong on the way?",
            f"{hazard.phrase.capitalize()} struck while Grace was carrying the treat. That kind of mishap was exactly the danger on that route, so the treat was damaged."
        ),
        (
            "Why did the carrier not save the treat?",
            f"Grace used {carrier.phrase}, which helped a little but not enough. The path and hazard together were stronger than the protection it gave."
        ),
    ]
    if outcome == "ruined":
        qa.append(
            (
                "How did the quest end?",
                f"It ended badly because the {treat.label} was ruined before Grace arrived. She still finished the walk with grace, but there was no proper party treat left to share."
            )
        )
    else:
        qa.append(
            (
                "Was the treat completely lost?",
                f"No, but it was spoiled and shabby by the time Grace reached the party. That is still a bad ending, because the treat could not be proudly served the way she hoped."
            )
        )
    qa.append(
        (
            "Why is the story a little funny even though it ends badly?",
            f"The mishap is silly to picture, like a goose grabbing a bite or a wobble making the treat lean sideways. Grace even feels a bubble of laughter, because the accident is absurd as well as disappointing."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"quest", "grace"} | set(f["hazard_cfg"].tags) | set(f["carrier_cfg"].tags)
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
        if ent.attrs:
            shown = {}
            for k, v in ent.attrs.items():
                if v:
                    shown[k] = sorted(v) if isinstance(v, set) else v
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:11} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard_at_risk(R, H, T) :- route(R), hazard(H), treat(T), affords(R, H), vulnerable(T, H).
sensible(C) :- carrier(C), sense(C, S), sense_min(M), S >= M.
valid(D, T, R, H, C) :- destination(D), hazard_at_risk(R, H, T), sensible(C).

% --- outcome model ---------------------------------------------------------
cover_bonus(1) :- chosen_carrier(C), chosen_hazard(H), covers(C, H).
cover_bonus(0) :- not cover_bonus(1).
danger(V) :- chosen_route(R), roughness(R, RR), chosen_hazard(H), severity(H, HS),
             chosen_carrier(C), stability(C, ST), cover_bonus(B), V = RR + HS - ST - B.

outcome(ruined) :- danger(V), V >= 3.
outcome(messy)  :- danger(V), V < 3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for did in DESTINATIONS:
        lines.append(asp.fact("destination", did))
    for tid, treat in TREATS.items():
        lines.append(asp.fact("treat", tid))
        for h in sorted(treat.vulnerable_to):
            lines.append(asp.fact("vulnerable", tid, h))
    for rid, route in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("roughness", rid, route.roughness))
        for h in sorted(route.affords):
            lines.append(asp.fact("affords", rid, h))
    for hid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("severity", hid, hazard.severity))
    for cid, carrier in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("sense", cid, carrier.sense))
        lines.append(asp.fact("stability", cid, carrier.stability))
        for h in sorted(carrier.covers):
            lines.append(asp.fact("covers", cid, h))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_carriers() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(c for (c,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_hazard", params.hazard),
            asp.fact("chosen_carrier", params.carrier),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


CURATED = [
    StoryParams(
        destination="duck_tea",
        treat="seed_cake",
        route="cobble_lane",
        hazard="goose",
        carrier="basket",
        parent="mother",
    ),
    StoryParams(
        destination="moon_gate",
        treat="jelly",
        route="windy_hill",
        hazard="gust",
        carrier="tin",
        parent="father",
    ),
    StoryParams(
        destination="plum_fair",
        treat="tart",
        route="plank_bridge",
        hazard="bump",
        carrier="tray",
        parent="mother",
    ),
    StoryParams(
        destination="duck_tea",
        treat="jelly",
        route="plank_bridge",
        hazard="gust",
        carrier="wagon",
        parent="father",
    ),
    StoryParams(
        destination="moon_gate",
        treat="tart",
        route="cobble_lane",
        hazard="bump",
        carrier="basket",
        parent="mother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: Grace on a tiny quest, a silly mishap, and a bad nursery-rhyme ending."
    )
    ap.add_argument("--destination", choices=DESTINATIONS)
    ap.add_argument("--treat", choices=TREATS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.carrier and CARRIERS[args.carrier].sense < SENSE_MIN:
        raise StoryError(explain_carrier(args.carrier))
    if args.route and args.hazard:
        route = ROUTES[args.route]
        hazard = HAZARDS[args.hazard]
        if hazard.id not in route.affords:
            raise StoryError(explain_route_hazard(route, hazard))
    if args.treat and args.hazard:
        treat = TREATS[args.treat]
        hazard = HAZARDS[args.hazard]
        if hazard.id not in treat.vulnerable_to:
            raise StoryError(explain_treat_hazard(treat, hazard))

    combos = [
        combo
        for combo in valid_combos()
        if (args.destination is None or combo[0] == args.destination)
        and (args.treat is None or combo[1] == args.treat)
        and (args.route is None or combo[2] == args.route)
        and (args.hazard is None or combo[3] == args.hazard)
        and (args.carrier is None or combo[4] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    destination, treat, route, hazard, carrier = rng.choice(sorted(combos))
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        destination=destination,
        treat=treat,
        route=route,
        hazard=hazard,
        carrier=carrier,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.destination not in DESTINATIONS:
        raise StoryError(f"(Unknown destination: {params.destination})")
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent: {params.parent})")

    destination = DESTINATIONS[params.destination]
    treat = TREATS[params.treat]
    route = ROUTES[params.route]
    hazard = HAZARDS[params.hazard]
    carrier = CARRIERS[params.carrier]

    if hazard.id not in route.affords:
        raise StoryError(explain_route_hazard(route, hazard))
    if hazard.id not in treat.vulnerable_to:
        raise StoryError(explain_treat_hazard(treat, hazard))
    if carrier.sense < SENSE_MIN:
        raise StoryError(explain_carrier(carrier.id))

    world = tell(destination, treat, route, hazard, carrier, params.parent)
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {c.id for c in sensible_carriers()}
    asp_sens = set(asp_sensible_carriers())
    if py_sens == asp_sens:
        print(f"OK: sensible carriers match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible carriers: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = 0
    for params in cases:
        py_out = outcome_of(params)
        asp_out = asp_outcome(params)
        if py_out != asp_out:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(777))
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test produced an empty story.)")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True)
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generate(CURATED[0]), trace=False, qa=False)
        print("OK: smoke-tested normal generate()/emit().")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible carriers: {', '.join(asp_sensible_carriers())}\n")
        print(f"{len(combos)} compatible (destination, treat, route, hazard, carrier) combos:\n")
        for combo in combos:
            print(f"  {combo[0]:10} {combo[1]:9} {combo[2]:12} {combo[3]:6} {combo[4]}")
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
                f"### Grace: {p.treat} by {p.route} with {p.carrier} "
                f"({p.hazard}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
