#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py
=============================================================

A standalone story world about a child-sized adventure course where **registration**
is not paperwork for its own sake: it is how a team gets the right map, badge, and
shared gear to solve one obstacle safely.

This world builds complete, TinyStories-style variants around one core shape:

- two children arrive excited for an adventure trail
- one wants to rush ahead without registration
- they try, and the trail blocks them because they lack the shared kit
- a calm guide sends them back to the registration table
- after signing in, they get the proper buddy gear
- they solve the obstacle together and end on a bright adventure image

The reasonableness gate is simple and concrete:
a challenge is only valid when the chosen registration kit actually gives the
shared tool that challenge needs. Random generation picks only those combinations.

Run it
------
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py --route cave --challenge dark_tunnel
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py --kit bridge_kit
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py --all
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/registration_teamwork_adventure.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    portable: bool = False
    wearable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "guide_f"}
        male = {"boy", "father", "man", "guide_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        if self.type == "guide_f" or self.type == "guide_m":
            return "guide"
        return self.type
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
class Route:
    id: str
    place: str
    opening: str
    prize: str
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
class Challenge:
    id: str
    label: str
    scene: str
    hazard: str
    need: str
    teamwork_action: str
    success: str
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
class Kit:
    id: str
    label: str
    item: str
    item_phrase: str
    need: str
    register_text: str
    use_text: str
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
        return [e for e in self.entities.values() if e.role in {"rusher", "partner"}]

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


def _r_registration_supplies(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    if team.meters["registered"] < THRESHOLD:
        return out
    if world.facts.get("kit_id") is None:
        return out
    if ("registration_supplies",) in world.fired:
        return out
    world.fired.add(("registration_supplies",))
    kit = world.facts["kit_cfg"]
    team.attrs["badge"] = "trail badge"
    team.attrs["map"] = "trail map"
    team.attrs["shared_item"] = kit.item
    team.meters["has_map"] += 1
    team.meters["has_badge"] += 1
    team.meters["has_item"] += 1
    for kid in world.kids():
        kid.memes["prepared"] += 1
    out.append("__registered__")
    return out


def _r_attempt_without_gear(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    obstacle = world.get("obstacle")
    if team.meters["attempted"] < THRESHOLD:
        return out
    if team.meters["has_item"] >= THRESHOLD:
        return out
    if ("blocked",) in world.fired:
        return out
    world.fired.add(("blocked",))
    obstacle.meters["blocked"] += 1
    team.meters["stuck"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    out.append("__blocked__")
    return out


def _r_teamwork_success(world: World) -> list[str]:
    out: list[str] = []
    team = world.get("team")
    obstacle = world.get("obstacle")
    if team.meters["attempted"] < THRESHOLD:
        return out
    if team.meters["has_item"] < THRESHOLD:
        return out
    if team.memes["teamwork"] < THRESHOLD:
        return out
    if ("success",) in world.fired:
        return out
    world.fired.add(("success",))
    obstacle.meters["cleared"] += 1
    team.meters["progress"] += 1
    team.meters["stuck"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
        kid.memes["pride"] += 1
        kid.memes["worry"] = 0.0
    out.append("__success__")
    return out


CAUSAL_RULES = [
    Rule(name="registration_supplies", tag="physical", apply=_r_registration_supplies),
    Rule(name="attempt_without_gear", tag="physical", apply=_r_attempt_without_gear),
    Rule(name="teamwork_success", tag="social", apply=_r_teamwork_success),
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


def kit_fits(kit: Kit, challenge: Challenge) -> bool:
    return kit.need == challenge.need


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for route_id in ROUTES:
        for challenge_id, challenge in CHALLENGES.items():
            for kit_id, kit in KITS.items():
                if kit_fits(kit, challenge):
                    combos.append((route_id, challenge_id, kit_id))
    return combos


def explain_rejection(challenge: Challenge, kit: Kit) -> str:
    return (
        f"(No story: {kit.label} gives {kit.item_phrase}, but {challenge.label} needs "
        f"{challenge.need.replace('_', ' ')} help. Registration should hand the team "
        f"the tool that actually solves the obstacle.)"
    )


def predict_attempt(world: World) -> dict:
    sim = world.copy()
    team = sim.get("team")
    team.meters["attempted"] += 1
    propagate(sim, narrate=False)
    return {
        "blocked": sim.get("obstacle").meters["blocked"] >= THRESHOLD,
        "stuck": sim.get("team").meters["stuck"],
    }


def open_scene(world: World, a: Entity, b: Entity, route: Route) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"{a.id} and {b.id} came to {route.place} with quick feet and bright eyes. "
        f"{route.opening}"
    )
    world.say(
        f"At the gate stood a little registration table with clipboards, pencils, "
        f"and a bell shaped like a star."
    )


def goal_scene(world: World, a: Entity, b: Entity, route: Route, challenge: Challenge) -> None:
    world.say(
        f'"If we make it past the {challenge.label}, we can reach {route.prize}," '
        f"{b.id} said."
    )
    world.say(
        f"The children could already see part of the trail ahead: {challenge.scene}"
    )


def rush_decision(world: World, a: Entity, b: Entity, challenge: Challenge) -> None:
    a.memes["impatience"] += 1
    world.say(
        f'{a.id} bounced on {a.pronoun("possessive")} toes. "Let\'s go now," '
        f"{a.pronoun()} said. \"We can do registration later.\""
    )
    pred = predict_attempt(world)
    world.facts["predicted_blocked"] = pred["blocked"]
    b.memes["caution"] += 1
    world.say(
        f'{b.id} looked at the path and then at the empty hands between them. '
        f'"The sign says teams should check in first," {b.pronoun()} said.'
    )


def first_attempt(world: World, a: Entity, b: Entity, challenge: Challenge) -> None:
    team = world.get("team")
    team.meters["attempted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But excitement pulled them forward. They hurried to the {challenge.label}, "
        f"and {challenge.hazard}"
    )
    if world.get("obstacle").meters["blocked"] >= THRESHOLD:
        world.say(
            f"They stopped short. Without the right trail gear, they could not get past it."
        )


def guide_redirect(world: World, guide: Entity, a: Entity, b: Entity, challenge: Challenge) -> None:
    guide.memes["care"] += 1
    world.say(
        f"A park guide in a green vest came over with a kind smile. "
        f"\"Adventurers still need registration,\" {guide.pronoun()} said."
    )
    world.say(
        f"\"The table gives each team what it needs for the {challenge.label}. "
        f"You are not in trouble. You just need to start the right way.\""
    )
    for kid in (a, b):
        kid.memes["relief"] += 1


def do_registration(world: World, guide: Entity, a: Entity, b: Entity, kit: Kit) -> None:
    team = world.get("team")
    team.meters["registered"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {a.id} and {b.id} went back to the registration table. They printed "
        f"their names carefully, rang the little star bell, and stood shoulder to shoulder."
    )
    world.say(
        f"{guide.pronoun().capitalize()} handed them a trail badge, a folded map, "
        f"and {kit.register_text}"
    )


def regroup(world: World, a: Entity, b: Entity, kit: Kit) -> None:
    team = world.get("team")
    team.memes["teamwork"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f'{a.id} looked at {b.id} and grinned. "This time we do it together," '
        f"{a.pronoun()} said."
    )
    world.say(
        f"{b.id} nodded, and together they studied the map and checked {kit.item_phrase}."
    )


def clear_obstacle(world: World, a: Entity, b: Entity, challenge: Challenge, kit: Kit) -> None:
    team = world.get("team")
    if team.meters["attempted"] < THRESHOLD:
        team.meters["attempted"] += 1
    else:
        team.meters["attempted"] += 1
    team.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They returned to the {challenge.label}. {kit.use_text}, and {challenge.teamwork_action}."
    )
    world.say(challenge.success)


def ending(world: World, a: Entity, b: Entity, route: Route) -> None:
    world.say(
        f"Beyond the obstacle, the trail opened wide. Soon the two teammates reached "
        f"{route.prize} together."
    )
    world.say(
        f"They tapped their badges, laughed, and hurried on with the map between them, "
        f"feeling like real adventurers at last."
    )


def tell(
    route: Route,
    challenge: Challenge,
    kit: Kit,
    *,
    rusher_name: str = "Nia",
    rusher_gender: str = "girl",
    partner_name: str = "Owen",
    partner_gender: str = "boy",
    guide_name: str = "Guide Mara",
    guide_gender: str = "guide_f",
    trait: str = "brave",
) -> World:
    world = World()
    a = world.add(
        Entity(
            id=rusher_name,
            kind="character",
            type=rusher_gender,
            role="rusher",
            traits=[trait],
            attrs={"checked_in": False},
        )
    )
    b = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=["careful"],
            attrs={"checked_in": False},
        )
    )
    guide = world.add(
        Entity(
            id=guide_name,
            kind="character",
            type=guide_gender,
            role="guide",
            label="the guide",
            traits=["kind", "calm"],
            attrs={},
        )
    )
    world.add(
        Entity(
            id="team",
            kind="thing",
            type="team",
            label="the team",
            attrs={"members": [a.id, b.id], "badge": "", "map": "", "shared_item": ""},
        )
    )
    world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=challenge.label,
            attrs={"need": challenge.need},
        )
    )

    world.facts["kit_id"] = kit.id
    world.facts["route"] = route
    world.facts["challenge"] = challenge
    world.facts["kit_cfg"] = kit
    world.facts["rusher"] = a
    world.facts["partner"] = b
    world.facts["guide"] = guide

    open_scene(world, a, b, route)
    goal_scene(world, a, b, route, challenge)

    world.para()
    rush_decision(world, a, b, challenge)
    first_attempt(world, a, b, challenge)
    guide_redirect(world, guide, a, b, challenge)

    world.para()
    do_registration(world, guide, a, b, kit)
    regroup(world, a, b, kit)

    world.para()
    clear_obstacle(world, a, b, challenge, kit)
    ending(world, a, b, route)

    world.facts.update(
        registered=world.get("team").meters["registered"] >= THRESHOLD,
        blocked=world.get("obstacle").meters["blocked"] >= THRESHOLD,
        cleared=world.get("obstacle").meters["cleared"] >= THRESHOLD,
        teamwork=world.get("team").memes["teamwork"] >= THRESHOLD,
        has_map=world.get("team").meters["has_map"] >= THRESHOLD,
        has_badge=world.get("team").meters["has_badge"] >= THRESHOLD,
        item=world.get("team").attrs.get("shared_item", ""),
    )
    return world


ROUTES = {
    "cave": Route(
        id="cave",
        place="the Pine Ridge Adventure Trail",
        opening="Colorful flags fluttered over the trees, and a painted arrow pointed toward the whisper cave.",
        prize="the echo stone at the finish arch",
        tags={"trail", "adventure"},
    ),
    "creek": Route(
        id="creek",
        place="the Meadow Adventure Trail",
        opening="Tall grass bent in the breeze, and bright stepping signs pointed toward the silver creek loop.",
        prize="the bell at the far lookout stump",
        tags={"trail", "adventure"},
    ),
    "tower": Route(
        id="tower",
        place="the Lantern Hill Adventure Trail",
        opening="Little lanterns bobbed on posts, and a ribbon sign curled upward toward the old watchtower path.",
        prize="the gold compass stamp at the tower gate",
        tags={"trail", "adventure"},
    ),
}

CHALLENGES = {
    "dark_tunnel": Challenge(
        id="dark_tunnel",
        label="dark tunnel",
        scene="a short stone passage where the middle looked shadowy and cool",
        hazard="the shadows swallowed the painted arrows halfway in",
        need="light",
        teamwork_action="one child held the lantern high while the other followed the arrows on the map",
        success="The hidden arrows gleamed again, and the tunnel turned from scary to exciting.",
        tags={"light", "teamwork"},
    ),
    "wobble_bridge": Challenge(
        id="wobble_bridge",
        label="wobble bridge",
        scene="a rope bridge over a shallow stream, shaking whenever the wind puffed through",
        hazard="the bridge swayed so much that one child alone could not steady it",
        need="balance",
        teamwork_action="they stretched the balance pole between them and stepped in the same slow rhythm",
        success="The bridge settled under their shared steps, and they crossed with water sparkling below.",
        tags={"bridge", "teamwork"},
    ),
    "high_marker": Challenge(
        id="high_marker",
        label="high marker",
        scene="a tall post with the next trail symbol clipped far above their heads",
        hazard="the clue was too high for either child to reach alone",
        need="reach",
        teamwork_action="they braced the stool together, and one child climbed just enough to unclip the marker",
        success="The marker popped free into waiting hands, and the next part of the trail was clear.",
        tags={"reach", "teamwork"},
    ),
}

KITS = {
    "lantern_kit": Kit(
        id="lantern_kit",
        label="lantern kit",
        item="lantern",
        item_phrase="a little hand lantern with a warm yellow glow",
        need="light",
        register_text="a little hand lantern with a warm yellow glow",
        use_text="They clicked on the lantern and its soft beam found every painted arrow",
        tags={"light", "registration"},
    ),
    "bridge_kit": Kit(
        id="bridge_kit",
        label="bridge kit",
        item="balance pole",
        item_phrase="a striped balance pole light enough for two small hands",
        need="balance",
        register_text="a striped balance pole light enough for two small hands",
        use_text="They lifted the balance pole together, one at each end",
        tags={"bridge", "registration"},
    ),
    "stool_kit": Kit(
        id="stool_kit",
        label="stool kit",
        item="folding stool",
        item_phrase="a sturdy folding stool with red feet",
        need="reach",
        register_text="a sturdy folding stool with red feet",
        use_text="They opened the stool, pressed all four feet firmly to the ground, and held it steady together",
        tags={"reach", "registration"},
    ),
}

GIRL_NAMES = ["Nia", "Lila", "Maya", "Tara", "Zoe", "Ivy", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Finn", "Leo", "Max", "Eli", "Theo", "Jack", "Noah"]
TRAITS = ["brave", "eager", "curious", "quick", "hopeful"]


@dataclass
class StoryParams:
    route: str
    challenge: str
    kit: str
    rusher_name: str
    rusher_gender: str
    partner_name: str
    partner_gender: str
    guide_name: str
    guide_gender: str
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
    "registration": [
        (
            "What is registration?",
            "Registration is when you check in and give your name before joining an activity. It helps grown-ups know who is playing and what each team needs."
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when people help each other to do one job together. Sharing the work can make hard things safer and easier."
        )
    ],
    "light": [
        (
            "Why is a lantern helpful in a dark place?",
            "A lantern gives light so you can see where to go. Seeing clearly helps people notice signs and stay safe."
        )
    ],
    "bridge": [
        (
            "Why should people move carefully on a wobbly bridge?",
            "A wobbly bridge can shake and throw off your balance. Slow, steady steps help your body stay safe."
        )
    ],
    "reach": [
        (
            "Why is it better to use a stool than to jump for something high?",
            "A stool gives you a steady way to reach up. Jumping can make you slip or miss what you need."
        )
    ],
    "map": [
        (
            "What does a trail map do?",
            "A trail map shows where the path goes and what comes next. It helps adventurers know which way to walk."
        )
    ],
}
KNOWLEDGE_ORDER = ["registration", "teamwork", "light", "bridge", "reach", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["rusher"]
    b = f["partner"]
    route = f["route"]
    challenge = f["challenge"]
    return [
        (
            'Write an adventure story for a 3-to-5-year-old that includes the word '
            '"registration" and shows two children learning to start a trail the right way.'
        ),
        (
            f"Tell a gentle teamwork adventure where {a.id} wants to rush ahead, but "
            f"{b.id} helps {a.pronoun('object')} go back for registration before facing a {challenge.label}."
        ),
        (
            f"Write a simple trail story set at {route.place} where checking in gives a team "
            f"the exact tool they need to finish an obstacle together."
        ),
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two girls"
    if a.type == "boy" and b.type == "boy":
        return "two boys"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["rusher"]
    b = f["partner"]
    guide = f["guide"]
    route = f["route"]
    challenge = f["challenge"]
    kit = f["kit_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(a, b)}, {a.id} and {b.id}, on an adventure trail with {guide.id}. They learn how to begin the trail as a team."
        ),
        (
            "Why did the children stop at first?",
            f"They hurried to the {challenge.label} before registration, so they did not have the right shared tool. The obstacle showed them that excitement alone was not enough."
        ),
        (
            "What did the guide tell them about registration?",
            f"{guide.id} explained that registration gives each team what it needs for the trail. That made registration feel like part of the adventure, not just waiting at a table."
        ),
        (
            "What did they get after registration?",
            f"After signing in, they got a trail badge, a map, and {kit.item_phrase}. Those things helped them know where to go and how to work together."
        ),
        (
            f"How did {a.id} and {b.id} solve the {challenge.label}?",
            f"They used {kit.item_phrase}, and they solved it together instead of alone. {challenge.teamwork_action[0].upper()}{challenge.teamwork_action[1:]}."
        ),
        (
            "How did the story end?",
            f"They reached {route.prize} together and felt like real adventurers. The ending shows that teamwork and registration helped them finish the trail the right way."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"registration", "teamwork", "map"}
    tags |= set(f["challenge"].tags)
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
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        shown_attrs = {k: v for k, v in e.attrs.items() if v}
        if shown_attrs:
            bits.append(f"attrs={shown_attrs}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="cave",
        challenge="dark_tunnel",
        kit="lantern_kit",
        rusher_name="Nia",
        rusher_gender="girl",
        partner_name="Owen",
        partner_gender="boy",
        guide_name="Guide Mara",
        guide_gender="guide_f",
        trait="eager",
    ),
    StoryParams(
        route="creek",
        challenge="wobble_bridge",
        kit="bridge_kit",
        rusher_name="Leo",
        rusher_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
        guide_name="Guide Ben",
        guide_gender="guide_m",
        trait="quick",
    ),
    StoryParams(
        route="tower",
        challenge="high_marker",
        kit="stool_kit",
        rusher_name="Maya",
        rusher_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
        guide_name="Guide Mara",
        guide_gender="guide_f",
        trait="curious",
    ),
]


ASP_RULES = r"""
fits(K, C) :- kit(K), gives_need(K, N), challenge_needs(C, N).
valid(R, C, K) :- route(R), challenge(C), kit(K), fits(K, C).

chosen_valid :- chosen_route(R), chosen_challenge(C), chosen_kit(K), valid(R, C, K).
blocked      :- chosen_route(_), chosen_challenge(_), chosen_kit(_), not chosen_valid.
registered   :- chosen_valid.
succeeds     :- registered, chosen_valid.

#show valid/3.
#show succeeds/0.
#show blocked/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id in ROUTES:
        lines.append(asp.fact("route", route_id))
    for challenge_id, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", challenge_id))
        lines.append(asp.fact("challenge_needs", challenge_id, challenge.need))
    for kit_id, kit in KITS.items():
        lines.append(asp.fact("kit", kit_id))
        lines.append(asp.fact("gives_need", kit_id, kit.need))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_succeeds(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_challenge", params.challenge),
            asp.fact("chosen_kit", params.kit),
        ]
    )
    model = asp.one_model(asp_program(extra))
    return bool(asp.atoms(model, "succeeds"))


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

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        default_params.seed = 123
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE resolve failed: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False)
        except Exception as err:
            rc = 1
            print(f"SMOKE generate/emit failed for {params}: {err}")

    outcome_bad = 0
    for params in smoke_cases:
        py_ok = (params.route, params.challenge, params.kit) in python_set
        asp_ok = asp_succeeds(params)
        if py_ok != asp_ok:
            outcome_bad += 1
    if outcome_bad == 0:
        print(f"OK: ASP success parity matches Python gate on {len(smoke_cases)} smoke cases.")
    else:
        rc = 1
        print(f"MISMATCH: {outcome_bad}/{len(smoke_cases)} success checks differ.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: registration turns two eager children into a prepared adventure team."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--kit", choices=KITS)
    ap.add_argument("--guide", choices=["guide_f", "guide_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid route/challenge/kit combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.challenge and args.kit:
        challenge = CHALLENGES[args.challenge]
        kit = KITS[args.kit]
        if not kit_fits(kit, challenge):
            raise StoryError(explain_rejection(challenge, kit))

    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.kit is None or combo[2] == args.kit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, challenge_id, kit_id = rng.choice(sorted(combos))
    rusher_name, rusher_gender = _pick_kid(rng)
    partner_name, partner_gender = _pick_kid(rng, avoid=rusher_name)
    guide_gender = args.guide or rng.choice(["guide_f", "guide_m"])
    guide_name = "Guide Mara" if guide_gender == "guide_f" else "Guide Ben"
    trait = rng.choice(TRAITS)
    return StoryParams(
        route=route_id,
        challenge=challenge_id,
        kit=kit_id,
        rusher_name=rusher_name,
        rusher_gender=rusher_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route: {params.route})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.kit not in KITS:
        raise StoryError(f"(Unknown kit: {params.kit})")

    route = ROUTES[params.route]
    challenge = CHALLENGES[params.challenge]
    kit = KITS[params.kit]
    if not kit_fits(kit, challenge):
        raise StoryError(explain_rejection(challenge, kit))

    world = tell(
        route=route,
        challenge=challenge,
        kit=kit,
        rusher_name=params.rusher_name,
        rusher_gender=params.rusher_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
        guide_name=params.guide_name,
        guide_gender=params.guide_gender,
        trait=params.trait,
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
        print(f"{len(combos)} compatible (route, challenge, kit) combos:\n")
        for route_id, challenge_id, kit_id in combos:
            print(f"  {route_id:8} {challenge_id:13} {kit_id}")
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
            header = f"### {p.rusher_name} & {p.partner_name}: {p.challenge} on {p.route} ({p.kit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
