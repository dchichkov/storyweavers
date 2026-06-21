#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py
========================================================================================

A standalone story world about two children at a family day held by a company's
subsidiary. They arrive ready to play superheroes, a small hurt feeling comes
between them, and a mission at the outing gives them a chance to practice
kindness and reconciliation.

The world is constrained rather than purely templated:

- an outing place only affords certain superhero-style missions
- each mission has a concrete physical need
- a kindness action is only valid when it truly solves that mission's need

So the turn of the story is state-driven: one child first tries to be a lone
hero, the attempt strains or worsens the problem, then an apology plus a
fitting kind action lets the pair succeed together. The ending image proves the
change: they patrol side by side again.

Run it
------
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py --outing rooftop --mission banner
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py --outing makers --mission seedlings
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/subsidiary_outing_reconciliation_kindness_superhero_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Outing:
    id: str
    place: str
    opener: str
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
class Mission:
    id: str
    title: str
    need: str
    problem: str
    solo_fail: str
    teamwork_win: str
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
class Kindness:
    id: str
    label: str
    supports: set[str] = field(default_factory=set)
    act_text: str = ""
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
    def __init__(self, outing: Outing) -> None:
        self.outing = outing
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
        return [e for e in self.entities.values() if e.role in {"lead", "friend"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.outing)
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


def _r_hurt_distance(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    team = world.get("team")
    if friend.memes["hurt"] < THRESHOLD:
        return []
    sig = ("hurt_distance",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.meters["distance"] += 1
    lead.memes["lonely"] += 1
    return []


def _r_solo_strain(world: World) -> list[str]:
    lead = world.get("lead")
    mission = world.get("mission")
    if lead.meters["solo_try"] < THRESHOLD or mission.meters["solved"] >= THRESHOLD:
        return []
    sig = ("solo_strain", int(lead.meters["solo_try"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lead.meters["strain"] += 1
    mission.meters["wobble"] += 1
    world.get("friend").memes["worry"] += 1
    return []


def _r_apology_softens(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    if lead.memes["apology"] < THRESHOLD:
        return []
    sig = ("apology_softens",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 1.0)
    friend.memes["hope"] += 1
    return []


def _r_kindness_reconciles(world: World) -> list[str]:
    lead = world.get("lead")
    friend = world.get("friend")
    team = world.get("team")
    mission = world.get("mission")
    if lead.memes["apology"] < THRESHOLD or team.meters["helping"] < THRESHOLD:
        return []
    sig = ("kindness_reconciles",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    team.meters["distance"] = 0.0
    team.meters["together"] += 1
    friend.memes["trust"] += 1
    lead.memes["relief"] += 1
    friend.memes["relief"] += 1
    mission.meters["solved"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="hurt_distance", tag="social", apply=_r_hurt_distance),
    Rule(name="solo_strain", tag="physical", apply=_r_solo_strain),
    Rule(name="apology_softens", tag="social", apply=_r_apology_softens),
    Rule(name="kindness_reconciles", tag="social", apply=_r_kindness_reconciles),
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


def mission_supported(outing: Outing, mission: Mission) -> bool:
    return mission.id in outing.affords


def kindness_fits(mission: Mission, kindness: Kindness) -> bool:
    return mission.need in kindness.supports


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for outing_id, outing in OUTINGS.items():
        for mission_id, mission in MISSIONS.items():
            if not mission_supported(outing, mission):
                continue
            for kindness_id, kindness in KINDNESS_ACTS.items():
                if kindness_fits(mission, kindness):
                    combos.append((outing_id, mission_id, kindness_id))
    return combos


def predict_repair(world: World, mission_id: str, kindness_id: str, misstep: int) -> dict:
    sim = world.copy()
    lead = sim.get("lead")
    team = sim.get("team")
    mission = sim.get("mission")
    lead.meters["solo_try"] += 1
    propagate(sim, narrate=False)
    if misstep:
        lead.meters["solo_try"] += 1
        mission.meters["wobble"] += 1
        propagate(sim, narrate=False)
    lead.memes["apology"] += 1
    team.meters["helping"] += 1
    propagate(sim, narrate=False)
    return {
        "solved": mission.meters["solved"] >= THRESHOLD,
        "strain": lead.meters["strain"],
        "distance": team.meters["distance"],
        "kindness": kindness_id,
        "mission": mission_id,
    }


def introduce(world: World, lead: Entity, friend: Entity, outing: Outing, mentor: Entity) -> None:
    for kid in (lead, friend):
        kid.memes["joy"] += 1
    world.say(
        f"On Saturday, {lead.id} and {friend.id} hurried into {outing.place} for a family outing. "
        f"{outing.opener}"
    )
    world.say(
        f"{mentor.label_word.capitalize()} worked there, and today the whole subsidiary had turned itself "
        f"into a training ground for junior heroes."
    )
    world.say(
        f"{lead.id} wore a bright cape, and {friend.id} wore a paper mask with a silver star on it. "
        f"They had promised to patrol together."
    )


def slight(world: World, lead: Entity, friend: Entity) -> None:
    team = world.get("team")
    lead.memes["pride"] += 1
    friend.memes["hurt"] += 1
    team.meters["distance"] += 0.0
    world.say(
        f"But when the sign-up bell rang, {lead.id} dashed ahead to grab the first shiny hero badge "
        f"and called over {lead.pronoun('possessive')} shoulder, \"Come on!\""
    )
    world.say(
        f"{friend.id} had been reaching for the same badge so they could match. "
        f"The small moment made {friend.pronoun('object')} feel left behind."
    )
    propagate(world, narrate=False)


def mentor_briefing(world: World, mentor: Entity, mission: Mission) -> None:
    world.say(
        f'{mentor.label_word.capitalize()} pointed to the next challenge board. '
        f'"Junior Heroes, your mission is {mission.title}," {mentor.pronoun()} said.'
    )
    world.say(mission.problem)


def solo_attempt(world: World, lead: Entity, friend: Entity, mission: Mission) -> None:
    lead.meters["solo_try"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{lead.id} puffed up {lead.pronoun('possessive')} chest and said, "
        f"\"I can handle this alone.\" {friend.id} stayed a step back, still hurt."
    )
    world.say(mission.solo_fail)


def extra_misstep(world: World, lead: Entity, mission: Mission) -> None:
    lead.meters["solo_try"] += 1
    mission.meters["wobble"] += 1
    lead.memes["pride"] += 1
    propagate(world, narrate=False)
    world.say(
        f"For another second, {lead.id} tried to fix it without help. That only made the trouble wobble more."
    )


def realization(world: World, lead: Entity, friend: Entity) -> None:
    world.say(
        f"Then {lead.id} looked at {friend.id}'s face and understood the real problem. "
        f"It was not only the mission. It was the hurt that had opened up between them."
    )


def apologize_and_invite(world: World, lead: Entity, friend: Entity) -> None:
    lead.memes["apology"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{lead.id} took a breath. "I am sorry I rushed ahead and acted like the only hero," '
        f'{lead.pronoun()} said. "Will you help me?"'
    )
    world.say(
        f"{friend.id}'s shoulders loosened a little. The apology made room for kindness to step in."
    )


def kind_action(world: World, lead: Entity, friend: Entity, mission: Mission, kindness: Kindness) -> None:
    team = world.get("team")
    team.meters["helping"] += 1
    lead.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    propagate(world, narrate=False)
    world.say(kindness.act_text.format(lead=lead.id, friend=friend.id))
    world.say(mission.teamwork_win)
    if mission.meters["solved"] < THRESHOLD:
        mission.meters["solved"] += 1


def close_story(world: World, lead: Entity, friend: Entity, mentor: Entity, mission: Mission, kindness: Kindness) -> None:
    lead.memes["joy"] += 1
    friend.memes["joy"] += 1
    lead.memes["trust"] += 1
    friend.memes["trust"] += 1
    world.say(
        f'{mentor.label_word.capitalize()} clapped and smiled. "That is real hero work," '
        f'{mentor.pronoun()} said. "Strong hands matter, but kind hearts matter too."'
    )
    world.say(
        f"{lead.id} fastened the shiny badge onto the front of {friend.id}'s cape instead of keeping it alone."
    )
    world.say(
        f"After that, the two junior heroes crossed the outing side by side, "
        f"{mission.ending_image}"
    )
    world.say(
        f"They did not need to be the biggest hero in the subsidiary that day. "
        f"They only needed to be kind enough to be a team again."
    )


def tell(
    outing: Outing,
    mission: Mission,
    kindness: Kindness,
    *,
    lead_name: str = "Nova",
    lead_gender: str = "girl",
    friend_name: str = "Max",
    friend_gender: str = "boy",
    mentor_type: str = "mother",
    trait: str = "brave",
    misstep: int = 0,
) -> World:
    world = World(outing)
    lead = world.add(Entity(id="lead", kind="character", type=lead_gender, role="lead", label=lead_name))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, role="friend", label=friend_name))
    mentor = world.add(Entity(id="mentor", kind="character", type=mentor_type, role="mentor", label="the grown-up"))
    team = world.add(Entity(id="team", type="team", label="the hero team"))
    mission_ent = world.add(Entity(id="mission", type="mission", label=mission.title))

    for ent in (lead, friend, mentor, team, mission_ent):
        ent.attrs.setdefault("name", ent.label)
        ent.meters["ready"] += 0.0
        ent.memes["ready"] += 0.0

    lead.attrs["display"] = lead_name
    friend.attrs["display"] = friend_name
    mentor.attrs["display"] = mentor.label_word
    lead.traits = [trait, "eager"]
    friend.traits = ["steady"]
    world.facts["mission_id"] = mission.id
    world.facts["kindness_id"] = kindness.id
    world.facts["misstep"] = misstep

    introduce(world, lead, friend, outing, mentor)
    world.para()
    slight(world, lead, friend)
    mentor_briefing(world, mentor, mission)
    world.para()
    solo_attempt(world, lead, friend, mission)
    if misstep:
        extra_misstep(world, lead, mission)
    realization(world, lead, friend)
    apologize_and_invite(world, lead, friend)
    kind_action(world, lead, friend, mission_ent, kindness)
    world.para()
    close_story(world, lead, friend, mentor, mission, kindness)

    outcome = "earned_reconcile" if misstep else "quick_reconcile"
    world.facts.update(
        outing=outing,
        mission_cfg=mission,
        kindness=kindness,
        lead=lead,
        friend=friend,
        mentor=mentor,
        team=team,
        mission=mission_ent,
        outcome=outcome,
        reconciled=team.meters["together"] >= THRESHOLD,
        solved=mission_ent.meters["solved"] >= THRESHOLD,
    )
    return world


OUTINGS = {
    "rooftop": Outing(
        id="rooftop",
        place="the rooftop garden above the company offices",
        opener="Planters lined the railings, bright capes fluttered in the wind, and a cardboard skyline glittered in the sun.",
        affords={"banner", "seedlings"},
        tags={"outing", "garden", "subsidiary"},
    ),
    "makers": Outing(
        id="makers",
        place="the makers hall inside the company's little subsidiary",
        opener="Tables were covered with safe craft gadgets, paper shields, and boxes of silver tape for superhero inventions.",
        affords={"robot", "snacks"},
        tags={"outing", "crafts", "subsidiary"},
    ),
    "riverside": Outing(
        id="riverside",
        place="the riverside lawn beside the glass-front subsidiary",
        opener="Streamers snapped in the breeze, picnic blankets dotted the grass, and children dashed between booths like tiny heroes on patrol.",
        affords={"banner", "snacks"},
        tags={"outing", "lawn", "subsidiary"},
    ),
}

MISSIONS = {
    "banner": Mission(
        id="banner",
        title="Banner Rescue",
        need="steady",
        problem="A welcome banner had slipped loose, and one flapping corner kept smacking the stand instead of staying tied.",
        solo_fail="The loose corner yanked away, and the stand gave a nervous shiver.",
        teamwork_win="Together they held the banner steady long enough to tie it neatly back into place.",
        ending_image="with the banner shining over them like a city-sky flag",
        tags={"banner", "wind"},
    ),
    "seedlings": Mission(
        id="seedlings",
        title="Seedling Save",
        need="gentle",
        problem="A tray of tiny bean seedlings had tipped, and soft green stems lay across the path like little citizens needing rescue.",
        solo_fail="Trying to scoop everything up quickly bent the tray and made the damp soil spread farther.",
        teamwork_win="Working carefully together, they tucked each seedling back into the tray and brushed the path clean.",
        ending_image="while the rescued seedlings nodded in their cups like a row of grateful green sidekicks",
        tags={"plants", "garden"},
    ),
    "robot": Mission(
        id="robot",
        title="Robot Parade Repair",
        need="fix",
        problem="The paper robot for the parade had lost a star-shaped chest plate, and one side drooped whenever anyone tried to roll it forward.",
        solo_fail="The star plate slid off again, and the wheel cover skittered across the floor.",
        teamwork_win="One child held the robot still while the other lined up the star plate and fastened it tight.",
        ending_image="with the little robot rolling behind them like a brave metal puppy",
        tags={"robot", "crafts"},
    ),
    "snacks": Mission(
        id="snacks",
        title="Snack Crate Carry",
        need="carry",
        problem="A crate full of juice boxes and fruit cups needed to reach the picnic table, but it was too heavy and tippy for one small hero.",
        solo_fail="The crate tipped toward the grass, and the juice boxes thumped against one another.",
        teamwork_win="With one handle in each pair of hands, they carried the crate safely to the picnic table.",
        ending_image="while the rescued snacks waited in neat rows for every hungry hero",
        tags={"snacks", "sharing"},
    ),
}

KINDNESS_ACTS = {
    "hold_corner": Kindness(
        id="hold_corner",
        label="hold the flapping corner",
        supports={"steady"},
        act_text="{friend} hurried over and held the wild corner still while {lead} tied the knot.",
        qa_text="held the flapping corner still so the banner could be tied",
        tags={"cooperate", "kindness"},
    ),
    "kneel_gather": Kindness(
        id="kneel_gather",
        label="kneel and gather gently",
        supports={"gentle"},
        act_text="{lead} knelt beside {friend}, and together they used slow hands to lift each tiny seedling without squashing it.",
        qa_text="knelt down and gathered the seedlings gently together",
        tags={"plants", "kindness"},
    ),
    "share_tape": Kindness(
        id="share_tape",
        label="share the silver tape",
        supports={"fix"},
        act_text="{friend} offered the silver tape and steadied the robot while {lead} pressed the star plate back where it belonged.",
        qa_text="shared the silver tape and steadied the robot during the repair",
        tags={"crafts", "kindness"},
    ),
    "take_handle": Kindness(
        id="take_handle",
        label="take the other handle",
        supports={"carry"},
        act_text="{friend} stepped in, took the other handle, and matched {lead}'s steps so the crate would not tip.",
        qa_text="took the other handle so they could carry the crate together",
        tags={"sharing", "kindness"},
    ),
}

GIRL_NAMES = ["Nova", "Mira", "Ruby", "Skye", "Luna", "Zuri", "Piper", "Ivy"]
BOY_NAMES = ["Max", "Leo", "Finn", "Theo", "Eli", "Jude", "Kai", "Ben"]
TRAITS = ["brave", "eager", "sparky", "zoomy", "bold"]


@dataclass
class StoryParams:
    outing: str
    mission: str
    kindness: str
    lead_name: str
    lead_gender: str
    friend_name: str
    friend_gender: str
    mentor: str
    trait: str
    misstep: int = 0
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
    "subsidiary": [
        (
            "What is a subsidiary?",
            "A subsidiary is a smaller company or office that belongs to a bigger company. It can still have its own building, workers, and special events.",
        )
    ],
    "outing": [
        (
            "What is an outing?",
            "An outing is a little trip people take together for fun or for a special activity. Families, classes, or work groups can go on an outing.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means choosing to help, comfort, or include someone. Small kind actions can make a big difference in how another person feels.",
        )
    ],
    "apology": [
        (
            "Why can saying sorry help?",
            "A real apology shows that you understand you hurt someone. It helps rebuild trust because your words match the wish to make things better.",
        )
    ],
    "banner": [
        (
            "Why is it easier for two people to hold a banner than one?",
            "A banner can flap and pull in the wind, so one person can steady it while the other ties it. Teamwork keeps the banner from twisting away.",
        )
    ],
    "plants": [
        (
            "Why do seedlings need gentle hands?",
            "Seedlings are baby plants with soft stems and roots. If you squeeze or tug them too hard, they can break.",
        )
    ],
    "robot": [
        (
            "What is a parade robot in a pretend game?",
            "It is a toy or craft robot people decorate for fun and roll along in a parade. In a superhero game, it can feel like a helper sidekick.",
        )
    ],
    "sharing": [
        (
            "Why does carrying something heavy together help?",
            "When two people share the weight, each person has less to hold. That makes the load steadier and safer to move.",
        )
    ],
}
KNOWLEDGE_ORDER = ["subsidiary", "outing", "kindness", "apology", "banner", "plants", "robot", "sharing"]


def lead_name(ent: Entity) -> str:
    return ent.attrs.get("display", ent.label or ent.id)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = lead_name(f["lead"])
    friend = lead_name(f["friend"])
    outing = f["outing"]
    mission = f["mission_cfg"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "subsidiary" and "outing".',
        f"Tell a gentle superhero story where {lead} and {friend} go to a family outing at a company subsidiary, hurt each other's feelings, and make up while solving {mission.title}.",
        f"Write a child-facing story about reconciliation and kindness at {outing.place}, ending with two young heroes working side by side again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = lead_name(f["lead"])
    friend = lead_name(f["friend"])
    mentor = f["mentor"]
    mission = f["mission_cfg"]
    kindness = f["kindness"]
    misstep = f["misstep"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two junior heroes, {lead} and {friend}, at a family outing. A grown-up guide from the subsidiary helps set the mission, but the children solve the heart of the problem themselves.",
        ),
        (
            "Why did {friend} feel hurt?".format(friend=friend),
            f"{friend} felt hurt because {lead} rushed ahead and acted like the badge and the mission belonged to only one hero. That small selfish moment made {friend} feel left behind.",
        ),
        (
            "What mission were they given?",
            f"They were given {mission.title}. The problem was concrete and physical, so they could not fix it with bragging alone.",
        ),
        (
            "Why did {lead} need to say sorry?".format(lead=lead),
            f"{lead} needed to say sorry because the real trouble was not only the wobbly mission task. {lead} had also hurt {friend}'s feelings by forgetting to be a partner.",
        ),
        (
            "How did kindness help them finish the mission?",
            f"They succeeded when {lead} apologized and {kindness.qa_text}. The kind action solved the physical problem, and the apology repaired the space between them too.",
        ),
    ]
    if misstep:
        qa.append(
            (
                "Did the problem get better right away?",
                f"No. {lead} tried for one more moment to be a lone hero, and that made the trouble wobble more. The turn came only after {lead} stopped, understood the hurt, and asked for help.",
            )
        )
    else:
        qa.append(
            (
                "What changed the story from a quarrel into a happy ending?",
                f"The change happened when {lead} noticed {friend}'s hurt face and chose humility instead of showing off. A true apology opened the door, and kindness let them walk through it together.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {lead} and {friend} moving through the outing side by side again. The ending image shows reconciliation because they are a team, not two separate heroes anymore.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"subsidiary", "outing", "kindness", "apology"}
    tags |= set(world.facts["mission_cfg"].tags)
    tags |= set(world.facts["kindness"].tags)
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
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        outing="rooftop",
        mission="banner",
        kindness="hold_corner",
        lead_name="Nova",
        lead_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        mentor="mother",
        trait="brave",
        misstep=0,
    ),
    StoryParams(
        outing="rooftop",
        mission="seedlings",
        kindness="kneel_gather",
        lead_name="Theo",
        lead_gender="boy",
        friend_name="Mira",
        friend_gender="girl",
        mentor="father",
        trait="eager",
        misstep=1,
    ),
    StoryParams(
        outing="makers",
        mission="robot",
        kindness="share_tape",
        lead_name="Ruby",
        lead_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        mentor="mother",
        trait="sparky",
        misstep=0,
    ),
    StoryParams(
        outing="makers",
        mission="snacks",
        kindness="take_handle",
        lead_name="Kai",
        lead_gender="boy",
        friend_name="Luna",
        friend_gender="girl",
        mentor="father",
        trait="zoomy",
        misstep=1,
    ),
    StoryParams(
        outing="riverside",
        mission="banner",
        kindness="hold_corner",
        lead_name="Zuri",
        lead_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        mentor="mother",
        trait="bold",
        misstep=0,
    ),
]


def explain_rejection(outing: Optional[Outing], mission: Optional[Mission], kindness: Optional[Kindness]) -> str:
    if outing and mission and not mission_supported(outing, mission):
        offered = ", ".join(sorted(outing.affords))
        return (
            f"(No story: {outing.id} does not support the mission '{mission.id}'. "
            f"That outing can honestly host: {offered}.)"
        )
    if mission and kindness and not kindness_fits(mission, kindness):
        needs = ", ".join(sorted(kindness.supports))
        return (
            f"(No story: kindness action '{kindness.id}' does not solve the need for mission '{mission.id}'. "
            f"The mission needs '{mission.need}', but that action supports: {needs}.)"
        )
    return "(No story: this combination is not reasonable in this world.)"


def outcome_of(params: StoryParams) -> str:
    return "earned_reconcile" if params.misstep else "quick_reconcile"


ASP_RULES = r"""
valid(O, M, K) :- outing(O), mission(M), kindness(K), affords(O, M), supports(K, Need), needs(M, Need).

outcome(quick_reconcile) :- misstep(0).
outcome(earned_reconcile) :- misstep(1).

#show valid/3.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for outing_id, outing in OUTINGS.items():
        lines.append(asp.fact("outing", outing_id))
        for mission_id in sorted(outing.affords):
            lines.append(asp.fact("affords", outing_id, mission_id))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("needs", mission_id, mission.need))
    for kindness_id, kindness in KINDNESS_ACTS.items():
        lines.append(asp.fact("kindness", kindness_id))
        for need in sorted(kindness.supports):
            lines.append(asp.fact("supports", kindness_id, need))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("misstep", params.misstep)))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: valid combo gate matches ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in clingo:", sorted(cl - py))

    for params in CURATED:
        if asp_outcome(params) != outcome_of(params):
            rc = 1
            print(f"MISMATCH in outcome for {params}")
            break
    else:
        print(f"OK: outcome model matches on {len(CURATED)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated empty story.)")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: superhero children at a subsidiary family outing repair a friendship through kindness."
    )
    ap.add_argument("--outing", choices=OUTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--kindness", choices=KINDNESS_ACTS)
    ap.add_argument("--mentor", choices=["mother", "father"])
    ap.add_argument("--misstep", type=int, choices=[0, 1], help="0 = quick apology, 1 = one extra proud mistake first")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (outing, mission, kindness) triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    outing = OUTINGS.get(args.outing) if args.outing else None
    mission = MISSIONS.get(args.mission) if args.mission else None
    kindness = KINDNESS_ACTS.get(args.kindness) if args.kindness else None

    if outing and mission and not mission_supported(outing, mission):
        raise StoryError(explain_rejection(outing, mission, kindness))
    if mission and kindness and not kindness_fits(mission, kindness):
        raise StoryError(explain_rejection(outing, mission, kindness))

    combos = [
        combo
        for combo in valid_combos()
        if (args.outing is None or combo[0] == args.outing)
        and (args.mission is None or combo[1] == args.mission)
        and (args.kindness is None or combo[2] == args.kindness)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    outing_id, mission_id, kindness_id = rng.choice(sorted(combos))
    lead_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    lead = _pick_name(rng, lead_gender)
    friend = _pick_name(rng, friend_gender, avoid=lead)
    return StoryParams(
        outing=outing_id,
        mission=mission_id,
        kindness=kindness_id,
        lead_name=lead,
        lead_gender=lead_gender,
        friend_name=friend,
        friend_gender=friend_gender,
        mentor=args.mentor or rng.choice(["mother", "father"]),
        trait=rng.choice(TRAITS),
        misstep=args.misstep if args.misstep is not None else rng.choice([0, 1]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.outing not in OUTINGS:
        raise StoryError(f"(Unknown outing: {params.outing})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.kindness not in KINDNESS_ACTS:
        raise StoryError(f"(Unknown kindness action: {params.kindness})")
    if params.mentor not in {"mother", "father"}:
        raise StoryError(f"(Unknown mentor type: {params.mentor})")
    if params.misstep not in {0, 1}:
        raise StoryError("(misstep must be 0 or 1.)")

    outing = OUTINGS[params.outing]
    mission = MISSIONS[params.mission]
    kindness = KINDNESS_ACTS[params.kindness]
    if not mission_supported(outing, mission) or not kindness_fits(mission, kindness):
        raise StoryError(explain_rejection(outing, mission, kindness))

    world = tell(
        outing=outing,
        mission=mission,
        kindness=kindness,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        mentor_type=params.mentor,
        trait=params.trait,
        misstep=params.misstep,
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
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (outing, mission, kindness) combos:\n")
        for outing_id, mission_id, kindness_id in combos:
            print(f"  {outing_id:10} {mission_id:10} {kindness_id}")
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
            header = f"### {p.lead_name} & {p.friend_name}: {p.outing} / {p.mission} / {p.kindness} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
