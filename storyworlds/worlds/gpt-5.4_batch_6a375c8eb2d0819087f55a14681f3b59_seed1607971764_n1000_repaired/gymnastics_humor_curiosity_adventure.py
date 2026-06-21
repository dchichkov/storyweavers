#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py
==================================================================

A standalone story world for a tiny, child-facing adventure set in a gymnastics
hall. Two children turn practice into a pretend quest. A funny little mystery
appears somewhere in the gym, curiosity pulls one child toward a silly shortcut,
and a calm coach redirects that energy into a safe gymnastics solution.

The world is built around three ideas:

* **gymnastics** is part of the action, not just decoration;
* **curiosity** drives the middle turn;
* **humor** softens the mistake so the ending still feels adventurous.

The reasonableness gate is simple and concrete: each mystery location has a
*kind* (high / pit / tunnel), and a route is only valid when it actually handles
that kind. Low-common-sense routes are known to the world but refused.

Run it
------
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py --all
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py --trace
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py --asp
    python storyworlds/worlds/gpt-5.4/gymnastics_humor_curiosity_adventure.py --verify
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
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
CURIOUS_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "steady", "sensible", "thoughtful"}


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "coach_woman"}
        male = {"boy", "man", "coach_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def role_word(self) -> str:
        if self.role == "coach":
            return "coach"
        return self.type
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Theme:
    id: str
    scene: str
    rig: str
    pair_call: str
    goal: str
    trail: str
    role_plural: str
    role_single: str
    ending: str
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


@dataclass
class Mystery:
    id: str
    hint: str
    sound: str
    reveal: str
    funny_image: str
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
class Location:
    id: str
    label: str
    kind: str
    place_text: str
    danger_text: str
    shortcut_text: str
    mishap_text: str
    reveal_text: str
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
class Route:
    id: str
    sense: int
    handles: set[str]
    text: str
    qa_text: str
    style_text: str
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
        return [e for e in self.entities.values() if e.role in {"instigator", "cautioner"}]

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


def _r_tumble_reaction(world: World) -> list[str]:
    out: list[str] = []
    instigator_id = world.facts.get("instigator_id")
    if not instigator_id or instigator_id not in world.entities:
        return out
    actor = world.get(instigator_id)
    if actor.meters["tumbled"] < THRESHOLD:
        return out
    sig = ("tumble_reaction", actor.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    actor.memes["embarrassed"] += 1
    actor.memes["relief"] += 1
    for kid in world.kids():
        kid.memes["surprise"] += 1
        kid.memes["relief"] += 1
    out.append("__tumble__")
    return out


def _r_found_joy(world: World) -> list[str]:
    out: list[str] = []
    mystery_id = world.facts.get("mystery_entity_id")
    if not mystery_id or mystery_id not in world.entities:
        return out
    mystery_ent = world.get(mystery_id)
    if mystery_ent.meters["found"] < THRESHOLD:
        return out
    sig = ("found_joy", mystery_ent.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
    out.append("__found__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="tumble_reaction", tag="social", apply=_r_tumble_reaction),
    Rule(name="found_joy", tag="social", apply=_r_found_joy),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(location: Location, route: Route) -> bool:
    return location.kind in route.handles


def sensible_routes() -> list[Route]:
    return [route for route in ROUTES.values() if route.sense >= SENSE_MIN]


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, cautioner_age: int, trait: str) -> bool:
    older = relation == "siblings" and cautioner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if older else 0.0)
    return older and authority > CURIOUS_INIT


def predict_mishap(world: World, location_id: str) -> dict:
    sim = world.copy()
    actor = sim.get(sim.facts["instigator_id"])
    location_ent = sim.get(location_id)
    unsafe_shortcut(sim, actor, location_ent, narrate=False)
    return {
        "tumbled": actor.meters["tumbled"] >= THRESHOLD,
        "danger": location_ent.meters["wobble"] + actor.meters["tumbled"],
    }


def introduce(world: World, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["curiosity"] += 1
    world.say(
        f"After warm-ups, {a.id} and {b.id} looked around the gymnastics hall and decided it was really {theme.scene}. "
        f"{theme.rig}"
    )
    world.say(
        f'"{theme.pair_call}!" {a.id} whispered. "Today we find {theme.goal}."'
    )


def mystery_appears(world: World, b: Entity, mystery: Mystery, location: Location, theme: Theme) -> None:
    world.say(
        f"As they followed {theme.trail}, {b.id} stopped. From {location.place_text} came {mystery.sound}."
    )
    world.say(
        f'{b.id} pointed. "Did you hear that? Maybe {mystery.hint} is hiding there."'
    )


def tempt(world: World, a: Entity, location: Location) -> None:
    a.memes["curiosity"] += 1
    world.say(
        f"{a.id}'s curiosity bounced higher than {a.pronoun('possessive')} toes. "
        f'"I can get there first," {a.pronoun()} said. "I will just {location.shortcut_text}."'
    )


def warn(world: World, b: Entity, a: Entity, location: Location, coach: Entity) -> None:
    pred = predict_mishap(world, "location")
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = ""
    if b.memes["caution"] >= 6:
        extra = f" {b.id} planted both feet and would not budge."
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{coach.role_word.capitalize()} {coach.id} said we wait for the safe turn. '
        f'If you do that, {location.danger_text}."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity, coach: Entity) -> None:
    a.memes["patience"] += 1
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f"{a.id} looked again, then let out a long puff of air. "
        f'"Okay," {a.pronoun()} said. "Adventure can wait one tiny minute."'
    )
    world.say(
        f"They called for {coach.role_word} {coach.id} instead of rushing ahead."
    )


def unsafe_shortcut(world: World, a: Entity, location_ent: Entity, narrate: bool = True) -> None:
    location_ent.meters["wobble"] += 1
    a.meters["tumbled"] += 1
    propagate(world, narrate=narrate)


def defy(world: World, a: Entity, b: Entity, location: Location) -> None:
    a.memes["defiance"] += 1
    older_sib = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older_sib:
        world.say(
            f'"Just watch me," {a.id} said. Because {a.pronoun()} was the older sibling, '
            f"{b.id} could not stop {a.pronoun('object')} in time."
        )
    else:
        world.say(
            f'"Just watch me," {a.id} said, and before anyone could answer, {a.pronoun()} darted off.'
        )


def tumble(world: World, a: Entity, location_ent: Entity, location: Location) -> None:
    unsafe_shortcut(world, a, location_ent, narrate=False)
    world.say(location.mishap_text.format(name=a.id))
    if location.kind == "pit":
        world.say(
            f"When {a.id} popped up again, only {a.pronoun('possessive')} grin was showing above the foam cubes."
        )
    elif location.kind == "tunnel":
        world.say(
            f"{bystander_laugh_line(a)}"
        )
    else:
        world.say(
            f"{a.id} landed on the crash mat with a surprised " + '"oof!"'
        )


def bystander_laugh_line(a: Entity) -> str:
    return f"{a.id} blinked at the ceiling for one puzzled second and then started laughing too."


def coach_arrives(world: World, coach: Entity, a: Entity) -> None:
    coach.memes["calm"] += 1
    world.say(
        f"{coach.role_word.capitalize()} {coach.id} was beside {a.id} in two quick steps."
    )
    world.say(
        f'"Curious is fine," {coach.pronoun()} said, helping {a.pronoun("object")} up. '
        f'"But in gymnastics, curious feet still need a plan."'
    )


def safe_route(world: World, coach: Entity, a: Entity, b: Entity, route: Route, location: Location) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f"Then {coach.id} {route.text}"
    )
    world.say(
        f"Soon {a.id} and {b.id} were moving like {route.style_text}, careful and bright-eyed."
    )


def reveal(world: World, a: Entity, b: Entity, mystery_ent: Entity, mystery: Mystery, location: Location, theme: Theme) -> None:
    mystery_ent.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At last they reached {location.reveal_text} and found {mystery.reveal}."
    )
    world.say(
        f"{mystery.funny_image} {a.id} laughed so hard {a.pronoun('possessive')} knees almost folded."
    )
    world.say(
        f'"Quest complete!" {b.id} cheered. The {theme.role_plural} had solved their mystery the safe way.'
    )


def ending(world: World, coach: Entity, a: Entity, b: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["confidence"] += 1
    world.say(
        f'After that, whenever a new puzzle twinkled from somewhere strange, {a.id} and {b.id} asked first and tried second.'
    )
    world.say(
        f"Then they hurried back onto the course, and the {theme.role_plural} {theme.ending}."
    )


def tell(
    theme: Theme,
    mystery: Mystery,
    location: Location,
    route: Route,
    *,
    instigator: str = "Milo",
    instigator_gender: str = "boy",
    cautioner: str = "Zoe",
    cautioner_gender: str = "girl",
    trait: str = "steady",
    coach_name: str = "Ana",
    coach_gender: str = "coach_woman",
    relation: str = "friends",
    instigator_age: int = 6,
    cautioner_age: int = 6,
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        attrs={"relation": relation},
        traits=["bold"],
    ))
    b = world.add(Entity(
        id=cautioner,
        kind="character",
        type=cautioner_gender,
        role="cautioner",
        age=cautioner_age,
        attrs={"relation": relation},
        traits=[trait],
    ))
    coach = world.add(Entity(
        id=coach_name,
        kind="character",
        type=coach_gender,
        role="coach",
        label="the coach",
    ))
    location_ent = world.add(Entity(
        id="location",
        kind="thing",
        type="place",
        label=location.label,
    ))
    mystery_ent = world.add(Entity(
        id="mystery",
        kind="thing",
        type="mystery",
        label=mystery.id,
    ))

    a.memes["curiosity"] = CURIOUS_INIT
    b.memes["caution"] = initial_caution(trait)
    coach.memes["calm"] = 1.0
    location_ent.meters["wobble"] = 0.0
    mystery_ent.meters["found"] = 0.0
    world.facts.update(
        instigator_id=a.id,
        cautioner_id=b.id,
        mystery_entity_id=mystery_ent.id,
        relation=relation,
    )

    introduce(world, a, b, theme)
    mystery_appears(world, b, mystery, location, theme)

    world.para()
    tempt(world, a, location)
    warn(world, b, a, location, coach)

    averted = would_avert(relation, instigator_age, cautioner_age, trait)

    if averted:
        back_down(world, a, b, coach)
        world.para()
        safe_route(world, coach, a, b, route, location)
        reveal(world, a, b, mystery_ent, mystery, location, theme)
        world.para()
        ending(world, coach, a, b, theme)
        outcome = "averted"
    else:
        defy(world, a, b, location)
        world.para()
        tumble(world, a, location_ent, location)
        coach_arrives(world, coach, a)
        world.para()
        safe_route(world, coach, a, b, route, location)
        reveal(world, a, b, mystery_ent, mystery, location, theme)
        world.para()
        ending(world, coach, a, b, theme)
        outcome = "tumbled"

    world.facts.update(
        theme=theme,
        mystery_cfg=mystery,
        location_cfg=location,
        route=route,
        instigator=a,
        cautioner=b,
        coach=coach,
        location=location_ent,
        mystery=mystery_ent,
        outcome=outcome,
        found=mystery_ent.meters["found"] >= THRESHOLD,
        tumbled=a.meters["tumbled"] >= THRESHOLD,
        averted=averted,
    )
    return world


THEMES = {
    "jungle": Theme(
        id="jungle",
        scene="a jungle gym on the edge of a secret map",
        rig="The low beam became a fallen log, the bars became vine gates, and the stacked mats became misty hills.",
        pair_call="Trail scouts",
        goal="the hidden camp",
        trail="the chalk arrow trail",
        role_plural="scouts",
        role_single="scout",
        ending="swung, tiptoed, and padded on toward the hidden camp",
    ),
    "castle": Theme(
        id="castle",
        scene="a cliffside castle full of brave surprises",
        rig="The beam became a narrow bridge, the bars became the front gate, and the blue mats became sleeping dragon hills.",
        pair_call="Castle seekers",
        goal="the whispering tower",
        trail="the ribbon path",
        role_plural="seekers",
        role_single="seeker",
        ending="crossed the bridge and marched toward the whispering tower",
    ),
    "space": Theme(
        id="space",
        scene="a moon outpost above a field of stars",
        rig="The beam became a moon ridge, the bars became rocket rails, and the foam pit became a sea of soft meteors.",
        pair_call="Moon rangers",
        goal="the lost signal",
        trail="the silver tape trail",
        role_plural="rangers",
        role_single="ranger",
        ending="bounded over the moon ridge and set off after the lost signal",
    ),
}

MYSTERIES = {
    "duck": Mystery(
        id="duck",
        hint="a tiny royal duck",
        sound="a squeaky quack-quack",
        reveal="a rubber duck wearing a tiny paper crown",
        funny_image="The duck's crown kept tipping over one eye, which made it look terribly important and terribly silly at the same time.",
        tags={"duck", "humor"},
    ),
    "bell": Mystery(
        id="bell",
        hint="a secret treasure bell",
        sound="a bright little jingle",
        reveal="a silver bell tied to a blue ribbon",
        funny_image="Every time the bell rang, it bounced against the ribbon as if it were laughing first.",
        tags={"bell", "sound"},
    ),
    "monkey": Mystery(
        id="monkey",
        hint="a sneaky monkey explorer",
        sound="a muffled giggle and a soft zip",
        reveal="a plush monkey with one sock on its head",
        funny_image="The sock hat was so crooked that even Coach had to hide a smile behind a hand.",
        tags={"monkey", "humor"},
    ),
}

LOCATIONS = {
    "high_rings": Location(
        id="high_rings",
        label="ring straps",
        kind="high",
        place_text="the ring straps above the landing mat",
        danger_text="those blocks could wobble and send you flopping onto the mat",
        shortcut_text="drag two foam blocks together and climb the wobbly stack",
        mishap_text="{name} scrambled up, reached, and then the top block sighed sideways like a sleepy cheese sandwich.",
        reveal_text="the dangling ring strap",
        tags={"rings", "high"},
    ),
    "foam_pit_edge": Location(
        id="foam_pit_edge",
        label="foam pit edge",
        kind="pit",
        place_text="the far edge of the foam pit",
        danger_text="the bounce could shoot you straight into the cubes",
        shortcut_text="bounce from the springboard and grab over the foam pit",
        mishap_text="Boing! {name} sprang, missed, and vanished into the foam cubes until only two shoes and one shocked giggle were left.",
        reveal_text="the far edge of the foam pit",
        tags={"foam_pit", "pit"},
    ),
    "rolled_tunnel": Location(
        id="rolled_tunnel",
        label="rolled mat tunnel",
        kind="tunnel",
        place_text="inside a rolled mat tunnel near the wall",
        danger_text="the tunnel could roll and spit you back out backward",
        shortcut_text="dive into the dark tunnel without checking first",
        mishap_text="{name} ducked inside too fast, the tunnel rolled a little, and {name} popped back out backward like a very surprised caterpillar.",
        reveal_text="the shadowy middle of the mat tunnel",
        tags={"tunnel", "dark"},
    ),
}

ROUTES = {
    "lower_rings": Route(
        id="lower_rings",
        sense=3,
        handles={"high"},
        text="steadied the landing mat, lowered the rings to a child-safe height, and let them reach one careful hand at a time.",
        qa_text="lowered the rings and guided them one careful reach at a time",
        style_text="true explorers on a careful climb",
        tags={"coach", "rings"},
    ),
    "panel_steps": Route(
        id="panel_steps",
        sense=3,
        handles={"high"},
        text="set firm panel steps beside the mat and showed them how to climb up and down without any wobbling.",
        qa_text="set firm panel steps beside the mat and showed them how to climb safely",
        style_text="mountain climbers crossing a tiny summit",
        tags={"steps", "balance"},
    ),
    "mat_bridge": Route(
        id="mat_bridge",
        sense=3,
        handles={"pit"},
        text="laid a bridge of flat mats to the edge, held a spotting hand out, and walked them there heel-to-toe.",
        qa_text="laid a bridge of flat mats to the pit edge and spotted them as they walked",
        style_text="captains crossing a floating bridge",
        tags={"foam_pit", "bridge"},
    ),
    "coach_grabber": Route(
        id="coach_grabber",
        sense=2,
        handles={"pit"},
        text="knelt by the foam pit, reached with the long gym grabber, and brought the mystery close before anyone leaned too far.",
        qa_text="used the long gym grabber so nobody had to lean over the pit",
        style_text="careful treasure fishers at the edge of the sea",
        tags={"foam_pit", "tool"},
    ),
    "headlamp_crawl": Route(
        id="headlamp_crawl",
        sense=3,
        handles={"tunnel"},
        text="held the tunnel still, clipped on a bright head-lamp, and had them bear-crawl through on hands and knees.",
        qa_text="held the tunnel still and sent them through with a head-lamp and a bear crawl",
        style_text="cave adventurers with glowing eyes",
        tags={"tunnel", "headlamp"},
    ),
    "steady_tunnel": Route(
        id="steady_tunnel",
        sense=2,
        handles={"tunnel"},
        text="braced the tunnel with both hands and invited them to peek and crawl slowly after counting to three together.",
        qa_text="braced the tunnel and had them crawl slowly after checking inside",
        style_text="quiet cave explorers moving nose first",
        tags={"tunnel", "coach"},
    ),
    "rolling_stool": Route(
        id="rolling_stool",
        sense=1,
        handles={"high"},
        text="rolled over a slippery stool and let them wobble on that instead",
        qa_text="used a rolling stool",
        style_text="wobblers",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Zoe", "Mia", "Ava", "Nora", "Lila", "Ruby", "Ella", "June"]
BOY_NAMES = ["Milo", "Ben", "Leo", "Finn", "Owen", "Theo", "Max", "Sam"]
TRAITS = ["careful", "steady", "curious", "thoughtful", "bouncy", "sensible"]


@dataclass
class StoryParams:
    theme: str
    mystery: str
    location: str
    route: str
    instigator: str
    instigator_gender: str
    cautioner: str
    cautioner_gender: str
    coach_name: str
    coach_gender: str
    trait: str
    relation: str = "friends"
    instigator_age: int = 6
    cautioner_age: int = 6
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
    "gymnastics": [
        (
            "What is gymnastics?",
            "Gymnastics is a kind of movement and sport where people balance, swing, roll, jump, and climb with control. It works best when children listen carefully and use the equipment the safe way."
        )
    ],
    "rings": [
        (
            "What are gymnastics rings?",
            "Gymnastics rings are two strong loops that hang down for swinging and holding. They feel exciting, but they should be used only the way a coach shows you."
        )
    ],
    "foam_pit": [
        (
            "What is a foam pit for?",
            "A foam pit is a big area full of soft foam cubes that helps make practice safer. Even so, children should still go near it only with the rules and a coach."
        )
    ],
    "tunnel": [
        (
            "Why should you check a dark tunnel before crawling in?",
            "You should check first so you know it is steady and clear. Looking before rushing keeps your body and your head safe."
        )
    ],
    "headlamp": [
        (
            "What does a head-lamp do?",
            "A head-lamp is a light you wear on your head so you can see while your hands stay free. It helps people look carefully in dark places."
        )
    ],
    "balance": [
        (
            "Why does balance matter in gymnastics?",
            "Balance helps your body stay where you want it to stay. If something wobbles, good balance and a safe setup stop a surprise tumble."
        )
    ],
    "coach": [
        (
            "What does a coach do in gymnastics?",
            "A coach teaches how to move safely and carefully. A coach also changes the equipment so a child can try something in the right way."
        )
    ],
    "curiosity": [
        (
            "Is curiosity a good thing?",
            "Yes, curiosity is good because it helps you notice and learn new things. It works best when you ask questions and stay safe while you explore."
        )
    ],
    "humor": [
        (
            "Why do funny moments help in a story?",
            "A funny moment can make people relax after a surprise. It can turn a mistake into something gentle that still teaches a lesson."
        )
    ],
    "duck": [
        (
            "Why might a rubber duck squeak?",
            "A rubber duck squeaks because air gets pushed through a tiny hole when you squeeze it. That is why it can sound like a toy quack."
        )
    ],
    "bell": [
        (
            "How does a bell make a sound?",
            "A bell rings when it shakes and the metal vibrates. Those tiny vibrations make the jingly sound you hear."
        )
    ],
    "monkey": [
        (
            "Why do stuffed toys make people laugh sometimes?",
            "Stuffed toys can look funny when they are wearing the wrong thing or sitting in a silly place. A surprising picture can make a whole room smile."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "gymnastics",
    "coach",
    "curiosity",
    "humor",
    "rings",
    "foam_pit",
    "tunnel",
    "headlamp",
    "balance",
    "duck",
    "bell",
    "monkey",
]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    if not sensible_routes():
        return combos
    for theme_id in THEMES:
        for mystery_id in MYSTERIES:
            for location_id, location in LOCATIONS.items():
                for route_id, route in ROUTES.items():
                    if route.sense >= SENSE_MIN and hazard_at_risk(location, route):
                        combos.append((theme_id, mystery_id, location_id, route_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    theme = f["theme"]
    mystery = f["mystery_cfg"]
    location = f["location_cfg"]
    route = f["route"]
    if f["outcome"] == "averted":
        return [
            'Write a short adventure story for a 3-to-5-year-old that includes the word "gymnastics", plus humor and curiosity.',
            f"Tell a gentle gymnastics adventure where {a.id} and {b.id} hear {mystery.sound} at {location.place_text}, but one child waits for the coach instead of rushing.",
            f"Write a curious, funny story where children solve a gym mystery safely, and the coach helps them use {route.id.replace('_', ' ')}."
        ]
    return [
        'Write a short adventure story for a 3-to-5-year-old that includes the word "gymnastics", plus humor and curiosity.',
        f"Tell a gymnastics quest where {a.id} gets too curious about a mystery at {location.place_text}, takes a silly shortcut, and then learns the safer way.",
        f"Write a funny adventure where a coach turns a clumsy moment into a safe victory and the children still solve the mystery."
    ]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two siblings"
        if a.type == "girl" and b.type == "girl":
            return "two siblings"
        return "a brother and a sister"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["cautioner"]
    coach = f["coach"]
    theme = f["theme"]
    mystery = f["mystery_cfg"]
    location = f["location_cfg"]
    route = f["route"]
    pair = pair_noun(a, b, f["relation"])
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and their coach {coach.id}. They turned gymnastics practice into {theme.scene}."
        ),
        (
            "What made them curious?",
            f"They heard {mystery.sound} coming from {location.place_text}. That strange sound made the place feel like part of a real adventure."
        ),
        (
            f"What risky idea did {a.id} have?",
            f"{a.id} wanted to {location.shortcut_text}. {b.id} warned that {location.danger_text}."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"Why did {a.id} stop and wait?",
                f"{a.id} listened when {b.id} warned {a.pronoun('object')}, so the risky shortcut never happened. Waiting changed the story because it gave the coach time to set up a safer plan."
            )
        )
    else:
        qa.append(
            (
                f"What happened when {a.id} rushed ahead?",
                f"{a.id} had a silly tumble instead of reaching the mystery. The moment was funny and gentle, but it showed that curiosity without a plan can go wrong fast."
            )
        )
    qa.append(
        (
            "How did the coach help them solve the problem?",
            f"Coach {coach.id} {route.qa_text}. That let the children reach the mystery safely instead of guessing with their bodies."
        )
    )
    qa.append(
        (
            "What did they find, and why was it funny?",
            f"They found {mystery.reveal}. It felt funny because {mystery.funny_image}"
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the children still on their adventure, but now they asked first and tried second. The last image proves they changed, because they went back to gymnastics with curiosity and better judgment together."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"gymnastics", "coach", "curiosity", "humor"}
    tags |= set(f["location_cfg"].tags)
    tags |= set(f["route"].tags)
    tags |= set(f["mystery_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(location: Location, route: Route) -> str:
    if route.sense < SENSE_MIN:
        return (
            f"(Refusing route '{route.id}': it scores too low on common sense "
            f"(sense={route.sense} < {SENSE_MIN}). Pick a steadier route.)"
        )
    return (
        f"(No story: route '{route.id}' does not honestly solve a {location.kind} mystery at {location.label}. "
        f"Choose a route that handles {location.kind}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.cautioner_age, params.trait):
        return "averted"
    return "tumbled"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
sensible(R) :- route(R), sense(R, S), sense_min(M), S >= M.
valid(T, M, L, R) :- theme(T), mystery(M), location(L), route(R),
                     sensible(R), handles(R, K), kind(L, K).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
cautioner_older :- relation(siblings), instigator_age(IA), cautioner_age(CA), CA > IA.
bonus(4) :- cautioner_older.
bonus(0) :- not cautioner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- cautioner_older, authority(A), curious_init(CU), A > CU.

outcome(averted) :- averted.
outcome(tumbled) :- not averted.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for mystery_id in MYSTERIES:
        lines.append(asp.fact("mystery", mystery_id))
    for location_id, location in LOCATIONS.items():
        lines.append(asp.fact("location", location_id))
        lines.append(asp.fact("kind", location_id, location.kind))
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("sense", route_id, route.sense))
        for kind in sorted(route.handles):
            lines.append(asp.fact("handles", route_id, kind))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("curious_init", int(CURIOUS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(route for (route,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("trait", params.trait),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("cautioner_age", params.cautioner_age),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated empty story.")
    if "gymnastics" not in sample.story.lower():
        raise StoryError('Smoke test failed: story did not include the required word "gymnastics".')
    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        emit(sample, trace=False, qa=True, header="### smoke")
    finally:
        sys.stdout = old
    if "### smoke" not in buf.getvalue():
        raise StoryError("Smoke test failed: emit() produced no visible output.")


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

    c_sens = set(asp_sensible())
    p_sens = {route.id for route in sensible_routes()}
    if c_sens == p_sens:
        print(f"OK: sensible routes match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible routes: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(80):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a funny gymnastics mystery driven by curiosity and a safer second try."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--location", choices=LOCATIONS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--coach-gender", dest="coach_gender", choices=["coach_woman", "coach_man"])
    ap.add_argument("--relation", choices=["friends", "siblings"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [name for name in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if name != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.location and args.route:
        location = LOCATIONS[args.location]
        route = ROUTES[args.route]
        if route.sense < SENSE_MIN or not hazard_at_risk(location, route):
            raise StoryError(explain_rejection(location, route))
    if args.route and ROUTES[args.route].sense < SENSE_MIN:
        location = LOCATIONS[args.location] if args.location else next(iter(LOCATIONS.values()))
        raise StoryError(explain_rejection(location, ROUTES[args.route]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.location is None or combo[2] == args.location)
        and (args.route is None or combo[3] == args.route)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme_id, mystery_id, location_id, route_id = rng.choice(sorted(combos))
    instigator, instigator_gender = _pick_child(rng)
    cautioner, cautioner_gender = _pick_child(rng, avoid=instigator)
    coach_gender = args.coach_gender or rng.choice(["coach_woman", "coach_man"])
    coach_name = rng.choice(["Ana", "Rosa", "Marta"] if coach_gender == "coach_woman" else ["Ben", "Luis", "Omar"])
    trait = rng.choice(TRAITS)
    relation = args.relation or rng.choice(["friends", "siblings"])
    instigator_age, cautioner_age = rng.sample([4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme_id,
        mystery=mystery_id,
        location=location_id,
        route=route_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        cautioner=cautioner,
        cautioner_gender=cautioner_gender,
        coach_name=coach_name,
        coach_gender=coach_gender,
        trait=trait,
        relation=relation,
        instigator_age=instigator_age,
        cautioner_age=cautioner_age,
    )


def _require_lookup(table: dict, key: str, label: str):
    if key not in table:
        raise StoryError(f"(No story: unknown {label} '{key}'.)")
    return table[key]


def generate(params: StoryParams) -> StorySample:
    theme = _require_lookup(THEMES, params.theme, "theme")
    mystery = _require_lookup(MYSTERIES, params.mystery, "mystery")
    location = _require_lookup(LOCATIONS, params.location, "location")
    route = _require_lookup(ROUTES, params.route, "route")
    if route.sense < SENSE_MIN or not hazard_at_risk(location, route):
        raise StoryError(explain_rejection(location, route))

    world = tell(
        theme=theme,
        mystery=mystery,
        location=location,
        route=route,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        cautioner=params.cautioner,
        cautioner_gender=params.cautioner_gender,
        trait=params.trait,
        coach_name=params.coach_name,
        coach_gender=params.coach_gender,
        relation=params.relation,
        instigator_age=params.instigator_age,
        cautioner_age=params.cautioner_age,
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


CURATED = [
    StoryParams(
        theme="jungle",
        mystery="duck",
        location="high_rings",
        route="lower_rings",
        instigator="Milo",
        instigator_gender="boy",
        cautioner="Zoe",
        cautioner_gender="girl",
        coach_name="Ana",
        coach_gender="coach_woman",
        trait="steady",
        relation="friends",
        instigator_age=6,
        cautioner_age=6,
    ),
    StoryParams(
        theme="castle",
        mystery="bell",
        location="foam_pit_edge",
        route="mat_bridge",
        instigator="Ava",
        instigator_gender="girl",
        cautioner="Ben",
        cautioner_gender="boy",
        coach_name="Ben",
        coach_gender="coach_man",
        trait="curious",
        relation="friends",
        instigator_age=6,
        cautioner_age=5,
    ),
    StoryParams(
        theme="space",
        mystery="monkey",
        location="rolled_tunnel",
        route="headlamp_crawl",
        instigator="Leo",
        instigator_gender="boy",
        cautioner="Mia",
        cautioner_gender="girl",
        coach_name="Rosa",
        coach_gender="coach_woman",
        trait="thoughtful",
        relation="friends",
        instigator_age=7,
        cautioner_age=6,
    ),
    StoryParams(
        theme="jungle",
        mystery="bell",
        location="high_rings",
        route="panel_steps",
        instigator="Nora",
        instigator_gender="girl",
        cautioner="Ella",
        cautioner_gender="girl",
        coach_name="Omar",
        coach_gender="coach_man",
        trait="careful",
        relation="siblings",
        instigator_age=5,
        cautioner_age=7,
    ),
    StoryParams(
        theme="castle",
        mystery="duck",
        location="rolled_tunnel",
        route="steady_tunnel",
        instigator="Theo",
        instigator_gender="boy",
        cautioner="June",
        cautioner_gender="girl",
        coach_name="Marta",
        coach_gender="coach_woman",
        trait="sensible",
        relation="siblings",
        instigator_age=4,
        cautioner_age=6,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible routes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, mystery, location, route) combos:\n")
        for theme_id, mystery_id, location_id, route_id in combos:
            print(f"  {theme_id:8} {mystery_id:7} {location_id:14} {route_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            header = (
                f"### {p.instigator} & {p.cautioner}: {p.mystery} at {p.location} "
                f"({p.theme}, {p.route}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
