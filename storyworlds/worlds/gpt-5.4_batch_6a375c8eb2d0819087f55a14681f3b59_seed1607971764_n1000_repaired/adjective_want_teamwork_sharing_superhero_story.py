#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/adjective_want_teamwork_sharing_superhero_story.py
=============================================================================

A standalone story world for a tiny superhero tale about two children who help
someone recover a lost item. The key turn is not brute force but teamwork and
sharing: one child first wants all the credit and the only rescue gadget, then
learns that a real hero shares tools and listens to a partner.

The world model is small but stateful:

- typed entities with physical meters and emotional memes
- a short causal rule engine for wobble / failure / rescue / gratitude
- a reasonableness gate over which gadgets can rescue which missions
- an inline ASP twin for the same gate and a small risk classifier
- three Q&A sets generated from the simulated world state, not by parsing prose
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
    tags: set[str] = field(default_factory=set)
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class Mission:
    id: str
    item_label: str
    item_phrase: str
    owner_name: str
    owner_type: str
    owner_mood: str
    stuck_place: str
    scene_tail: str
    height: int
    delicate: bool
    problem_line: str
    success_line: str
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
class Gadget:
    id: str
    label: str
    phrase: str
    reach: int
    gentle: bool
    action: str
    handoff: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {
            "attempt_mode": "none",
            "mission_height": 0,
            "mission_delicate": False,
            "gadget_reach": 0,
            "gadget_gentle": False,
            "share_happened": False,
            "stool_held": False,
            "solo_wobble": False,
            "solo_failed": False,
            "rescued": False,
            "risk": "low",
        }

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
        clone = World(self.setting)
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


def _r_wobble(world: World) -> list[str]:
    target = world.get("target")
    hero = world.get("hero1")
    buddy = world.get("hero2")
    if target.meters["stuck"] < THRESHOLD:
        return []
    if world.facts["attempt_mode"] != "solo":
        return []
    if world.facts["mission_height"] < 2:
        return []
    sig = ("wobble", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.meters["wobble"] += 1
    hero.memes["fear"] += 1
    buddy.memes["fear"] += 1
    world.facts["solo_wobble"] = True
    return ["__wobble__"]


def _r_solo_fail(world: World) -> list[str]:
    target = world.get("target")
    hero = world.get("hero1")
    if target.meters["stuck"] < THRESHOLD:
        return []
    if world.facts["attempt_mode"] != "solo":
        return []
    sig = ("solo_fail", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["jiggled"] += 1
    hero.memes["frustration"] += 1
    world.facts["solo_failed"] = True
    return ["__solo_fail__"]


def _r_rescue(world: World) -> list[str]:
    target = world.get("target")
    hero = world.get("hero1")
    buddy = world.get("hero2")
    owner = world.get("owner")
    if target.meters["stuck"] < THRESHOLD:
        return []
    if world.facts["attempt_mode"] != "shared":
        return []
    if not world.facts["share_happened"]:
        return []
    if world.facts["gadget_reach"] < world.facts["mission_height"]:
        return []
    if world.facts["mission_delicate"] and not world.facts["gadget_gentle"]:
        return []
    if world.facts["mission_height"] >= 2 and not world.facts["stool_held"]:
        return []
    sig = ("rescue", target.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    target.meters["stuck"] = 0.0
    target.meters["rescued"] += 1
    hero.memes["pride"] += 1
    buddy.memes["pride"] += 1
    hero.memes["trust"] += 1
    buddy.memes["trust"] += 1
    owner.memes["relief"] += 1
    owner.memes["gratitude"] += 1
    world.facts["rescued"] = True
    return ["__rescue__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="solo_fail", tag="physical", apply=_r_solo_fail),
    Rule(name="rescue", tag="social", apply=_r_rescue),
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
            if not line.startswith("__"):
                world.say(line)
    return produced


def valid_combo(setting: Setting, mission: Mission, gadget: Gadget) -> bool:
    if mission.id not in setting.affords:
        return False
    if gadget.reach < mission.height:
        return False
    if mission.delicate and not gadget.gentle:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            for gid, gadget in GADGETS.items():
                if valid_combo(setting, mission, gadget):
                    combos.append((sid, mid, gid))
    return sorted(combos)


def risk_level(mission: Mission) -> str:
    return "high" if mission.height >= 2 else "low"


def predict_solo(world: World) -> dict:
    sim = world.copy()
    sim.facts["attempt_mode"] = "solo"
    propagate(sim, narrate=False)
    return {
        "wobble": sim.facts["solo_wobble"],
        "failed": sim.facts["solo_failed"],
        "rescued": sim.facts["rescued"],
    }


def introduce(world: World, hero1: Entity, hero2: Entity) -> None:
    world.say(
        f"After school in {world.setting.label}, {hero1.id} and {hero2.id} tied on their capes "
        f"and turned the day into a superhero patrol. {world.setting.scene}"
    )
    world.say(
        f'"What adjective fits our team today?" {hero2.id} asked. '
        f'"Helpful," {hero1.id} said, thumping {hero1.pronoun("possessive")} chest like a comic-book hero.'
    )


def hear_problem(world: World, owner: Entity, mission: Mission) -> None:
    owner.memes["worry"] += 1
    target = world.get("target")
    target.meters["stuck"] += 1
    world.say(
        f"Then they heard a small voice. {owner.id} stood nearby looking {mission.owner_mood}. "
        f"{mission.problem_line}"
    )


def boast(world: World, hero1: Entity, gadget: Gadget) -> None:
    hero1.memes["glory_want"] += 1
    world.say(
        f'{hero1.id} grabbed {gadget.phrase} and said, "I want {gadget.label} all to myself. '
        f"I can do this rescue alone!"
    )


def warn(world: World, hero2: Entity, hero1: Entity, mission: Mission, gadget: Gadget) -> None:
    pred = predict_solo(world)
    hero2.memes["care"] += 1
    lines = [f'{hero2.id} watched {mission.stuck_place} and shook {hero2.pronoun("possessive")} head.']
    if pred["wobble"]:
        lines.append(
            f'"If you do that alone, the stool may wobble," {hero2.pronoun()} said.'
        )
    else:
        lines.append(
            f'"If you do that alone, you may only jiggle it and not free it," {hero2.pronoun()} said.'
        )
    if mission.delicate:
        lines.append(
            f'"And {mission.item_label} needs a gentle rescue. Real heroes share and work as a team."'
        )
    else:
        lines.append(
            f'"Real heroes share and work as a team," {hero2.pronoun()} added.'
        )
    world.say(" ".join(lines))


def solo_try(world: World, hero1: Entity, mission: Mission, gadget: Gadget) -> None:
    world.facts["attempt_mode"] = "solo"
    world.say(
        f"{hero1.id} climbed one safe step on the little community stool and reached up with {gadget.label}. "
        f"{hero1.pronoun().capitalize()} {gadget.action} by {hero1.pronoun('object')}self."
    )
    propagate(world, narrate=False)
    if world.facts["solo_wobble"]:
        world.say(
            f"But the stool gave a nervous wiggle. {hero1.id}'s cape fluttered, and {hero1.pronoun()} froze."
        )
    if world.facts["solo_failed"]:
        if mission.delicate:
            world.say(
                f"{mission.item_label.capitalize()} only trembled where it was stuck. Pulling harder felt wrong, "
                f"because it might get bent or dropped."
            )
        else:
            world.say(
                f"{mission.item_label.capitalize()} only wiggled and stayed right where it was."
            )


def decide_share(world: World, hero1: Entity, hero2: Entity, gadget: Gadget, mission: Mission) -> None:
    world.facts["share_happened"] = True
    world.facts["stool_held"] = mission.height >= 2
    hero1.memes["humility"] += 1
    hero2.memes["trust"] += 1
    world.say(
        f'{hero1.id} took a careful breath. "You were right," {hero1.pronoun()} said. '
        f'"A one-hero rescue is not enough today."'
    )
    world.say(
        f"{hero1.id} {gadget.handoff} to {hero2.id}. Then {hero1.pronoun()} held the stool steady "
        f"with both hands while {hero2.id} aimed up high."
    )


def shared_try(world: World, hero1: Entity, hero2: Entity, owner: Entity, mission: Mission, gadget: Gadget) -> None:
    world.facts["attempt_mode"] = "shared"
    world.say(
        f"Now the rescue looked different. {hero1.id} kept the stool still, "
        f"{hero2.id} lifted {gadget.label}, and both children counted, "
        f'"One, two, three, team!"'
    )
    propagate(world, narrate=False)
    if world.facts["rescued"]:
        world.say(
            f"{hero2.id} {gadget.action}, {hero1.id} guided from below, and {mission.success_line} "
            f"{owner.id} hugged it to {owner.pronoun('possessive')} chest with a bright, shaky smile."
        )


def ending(world: World, hero1: Entity, hero2: Entity, owner: Entity, gadget: Gadget) -> None:
    world.say(
        f'"Thank you, heroes," {owner.id} said. "You saved the day."'
    )
    world.say(
        f"{hero1.id} did not snatch {gadget.label} back. Instead {hero1.pronoun()} and {hero2.id} held it together "
        f"for one last shining second, like a team trophy."
    )
    world.say(
        f"As they walked home, their capes bumped side by side, and the most powerful thing about them was not flying "
        f"or flashing or boasting. It was sharing."
    )
@dataclass
class StoryParams:
    setting: str
    mission: str
    gadget: str
    hero1_name: str
    hero1_type: str
    hero2_name: str
    hero2_type: str
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
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another on the same job instead of each person trying to do everything alone. A team can be steadier, safer, and smarter because everyone adds something useful."
        )
    ],
    "sharing": [
        (
            "Why is sharing helpful?",
            "Sharing lets more than one person use something important, like a tool or a turn. It also helps people feel included, so they can solve a problem together."
        )
    ],
    "grabber": [
        (
            "What is a grabber tool?",
            "A grabber is a long tool that helps you reach something without climbing high. It can be useful when a grown-up says it is safe to use."
        )
    ],
    "net": [
        (
            "What does a rescue net do?",
            "A rescue net catches or supports something gently so it does not fall hard. That makes it good for careful rescues."
        )
    ],
    "broom": [
        (
            "Why might a broom be too rough for some rescues?",
            "A broom can push hard instead of holding gently. That can bend or knock down something delicate."
        )
    ],
    "tree": [
        (
            "Why can a tree branch hold a toy up high?",
            "A branch sticks out and can catch a light toy or cloth item. Wind or a throw can leave the thing hanging there."
        )
    ],
    "book": [
        (
            "Why should library books be handled carefully?",
            "Library books belong to everyone who borrows them. Keeping them dry and unbent helps the next reader enjoy them too."
        )
    ],
    "ball": [
        (
            "Why can a ball get stuck in a fence corner?",
            "A round ball can roll into a tight space and wedge there. Then it needs a careful push or pull to come free."
        )
    ],
    "cape": [
        (
            "Why can cloth blow away in the wind?",
            "Light cloth catches moving air easily. A gust can lift it and carry it higher than you expect."
        )
    ],
}
KNOWLEDGE_ORDER = ["teamwork", "sharing", "grabber", "net", "broom", "tree", "book", "ball", "cape"]


def generation_prompts(world: World) -> list[str]:
    hero1 = world.facts["hero1"]
    hero2 = world.facts["hero2"]
    mission = world.facts["mission"]
    gadget = world.facts["gadget"]
    setting = world.facts["setting"]
    return [
        f'Write a short superhero story for ages 3 to 5 that includes the words "adjective" and "want".',
        f"Tell a gentle superhero rescue story set in {setting.label} where {hero1.id} first wants {gadget.label} alone, but learns to share it with {hero2.id}.",
        f"Write a child-facing story about teamwork and sharing where two caped kids rescue a {mission.item_label} and end by acting like a real team.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero1 = world.facts["hero1"]
    hero2 = world.facts["hero2"]
    owner = world.facts["owner"]
    mission = world.facts["mission"]
    gadget = world.facts["gadget"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two pretend superheroes, {hero1.id} and {hero2.id}, and {owner.id}, who needed help. The rescue mattered because {mission.item_label} was stuck {mission.scene_tail}."
        ),
        (
            f"What problem did {owner.id} have?",
            f"{owner.id} had lost {owner.pronoun('possessive')} {mission.item_label}, and it was stuck {mission.scene_tail}. That is why the two children changed from playing heroes to helping like heroes."
        ),
        (
            f"What did {hero1.id} want at first?",
            f"{hero1.id} wanted to use {gadget.label} alone and be the only hero of the rescue. That selfish start created the problem that teamwork later fixed."
        ),
    ]
    if world.facts["solo_wobble"]:
        out.append(
            (
                f"Why did {hero2.id} warn {hero1.id} not to do the rescue alone?",
                f"{hero2.id} could see the rescue was high enough to make the stool wobble if one child tried it alone. The warning was about safety as well as success, because a shaky rescue can go wrong quickly."
            )
        )
    else:
        out.append(
            (
                f"Why did {hero2.id} say the rescue needed a team?",
                f"{hero2.id} knew that trying alone might only jiggle the {mission.item_label} without freeing it. Two children working together could keep the rescue steadier and smarter."
            )
        )
    if world.facts["rescued"]:
        out.append(
            (
                "How did they solve the problem?",
                f"They solved it by sharing {gadget.label} and splitting the jobs. One child kept the stool still while the other used the tool gently, and that teamwork is what made the rescue work."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"The item came down safely, and {owner.id} thanked them like real heroes. The ending shows that their biggest superpower was sharing, not showing off."
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    mission = world.facts["mission"]
    gadget = world.facts["gadget"]
    tags = {"teamwork", "sharing"} | set(mission.tags)
    tags |= set(gadget.tags)
    if mission.id == "book_awning":
        tags.add("book")
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
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    shown_facts = {
        k: v for k, v in world.facts.items()
        if k in {"attempt_mode", "mission_height", "mission_delicate", "gadget_reach",
                 "gadget_gentle", "share_happened", "stool_held", "solo_wobble",
                 "solo_failed", "rescued", "risk"}
    }
    lines.append(f"  facts={shown_facts}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="park",
        mission="plush_tree",
        gadget="comet_claw",
        hero1_name="Maya",
        hero1_type="girl",
        hero2_name="Ben",
        hero2_type="boy",
    ),
    StoryParams(
        setting="courtyard",
        mission="book_awning",
        gadget="rocket_net",
        hero1_name="Leo",
        hero1_type="boy",
        hero2_name="Nia",
        hero2_type="girl",
    ),
    StoryParams(
        setting="schoolyard",
        mission="ball_fence",
        gadget="sticky_pole",
        hero1_name="Ruby",
        hero1_type="girl",
        hero2_name="Finn",
        hero2_type="boy",
    ),
    StoryParams(
        setting="courtyard",
        mission="cape_lamp",
        gadget="broom",
        hero1_name="Ava",
        hero1_type="girl",
        hero2_name="Sam",
        hero2_type="boy",
    ),
]


def explain_rejection(setting: Setting, mission: Mission, gadget: Gadget) -> str:
    if mission.id not in setting.affords:
        return (
            f"(No story: {setting.label} does not fit the mission '{mission.id}'. "
            f"That rescue does not happen in this place.)"
        )
    if gadget.reach < mission.height:
        return (
            f"(No story: {gadget.label} cannot reach {mission.item_label} where it is stuck. "
            f"Pick a gadget with enough reach.)"
        )
    if mission.delicate and not gadget.gentle:
        return (
            f"(No story: {mission.item_label} needs a gentle rescue, but {gadget.label} is too rough. "
            f"Pick a gentler gadget.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
valid(S, M, G) :- setting(S), mission(M), gadget(G),
                  affords(S, M),
                  reach(G, R), height(M, H), R >= H,
                  not needs_gentle(M).
valid(S, M, G) :- setting(S), mission(M), gadget(G),
                  affords(S, M),
                  reach(G, R), height(M, H), R >= H,
                  needs_gentle(M), gentle(G).

risk(M, high) :- mission(M), height(M, H), H >= 2.
risk(M, low)  :- mission(M), not risk(M, high).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for mid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, mid))
    for mid, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("height", mid, mission.height))
        if mission.delicate:
            lines.append(asp.fact("needs_gentle", mid))
    for gid, gadget in GADGETS.items():
        lines.append(asp.fact("gadget", gid))
        lines.append(asp.fact("reach", gid, gadget.reach))
        if gadget.gentle:
            lines.append(asp.fact("gentle", gid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_risks() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show risk/2."))
    return sorted(set(asp.atoms(model, "risk")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    py_risks = sorted((mid, risk_level(mission)) for mid, mission in MISSIONS.items())
    cl_risks = asp_risks()
    if py_risks == cl_risks:
        print(f"OK: risk classifier matches ({len(py_risks)} missions).")
    else:
        rc = 1
        print("MISMATCH in risk classifier:")
        print("  clingo:", cl_risks)
        print("  python:", py_risks)

    smoke_cases = list(CURATED)
    for seed in range(10):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        smoke_cases.append(params)

    try:
        sample = generate(smoke_cases[0])
        if not sample.story.strip():
            raise StoryError("empty story in smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke generation and emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Superhero story world: two children rescue a stuck item and learn that sharing beats showing off."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gadget", choices=GADGETS)
    ap.add_argument("--hero1-name")
    ap.add_argument("--hero1-type", choices=["girl", "boy"])
    ap.add_argument("--hero2-name")
    ap.add_argument("--hero2-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.mission and args.gadget:
        setting = SETTINGS[args.setting]
        mission = MISSIONS[args.mission]
        gadget = GADGETS[args.gadget]
        if not valid_combo(setting, mission, gadget):
            raise StoryError(explain_rejection(setting, mission, gadget))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mission is None or combo[1] == args.mission)
        and (args.gadget is None or combo[2] == args.gadget)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mission_id, gadget_id = rng.choice(combos)
    hero1_type = args.hero1_type or rng.choice(["girl", "boy"])
    hero2_type = args.hero2_type or rng.choice(["girl", "boy"])
    hero1_name = args.hero1_name or _pick_name(rng, hero1_type)
    hero2_name = args.hero2_name or _pick_name(rng, hero2_type, avoid=hero1_name)
    return StoryParams(
        setting=setting_id,
        mission=mission_id,
        gadget=gadget_id,
        hero1_name=hero1_name,
        hero1_type=hero1_type,
        hero2_name=hero2_name,
        hero2_type=hero2_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.mission not in MISSIONS:
        raise StoryError(f"(Unknown mission: {params.mission})")
    if params.gadget not in GADGETS:
        raise StoryError(f"(Unknown gadget: {params.gadget})")

    setting = SETTINGS[params.setting]
    mission = MISSIONS[params.mission]
    gadget = GADGETS[params.gadget]
    if not valid_combo(setting, mission, gadget):
        raise StoryError(explain_rejection(setting, mission, gadget))

    world = tell(
        setting=setting,
        mission=mission,
        gadget=gadget,
        hero1_name=params.hero1_name,
        hero1_type=params.hero1_type,
        hero2_name=params.hero2_name,
        hero2_type=params.hero2_type,
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
        print(asp_program("", "#show valid/3.\n#show risk/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        risks = dict(asp_risks())
        print(f"{len(combos)} compatible (setting, mission, gadget) combos:\n")
        for setting, mission, gadget in combos:
            print(f"  {setting:10} {mission:12} {gadget:11}  risk={risks.get(mission, '?')}")
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
            header = f"### {p.hero1_name} & {p.hero2_name}: {p.mission} in {p.setting} with {p.gadget}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    setting: Setting,
    mission: Mission,
    gadget: Gadget,
    hero1_name: str = "Maya",
    hero1_type: str = "girl",
    hero2_name: str = "Ben",
    hero2_type: str = "boy",
) -> World:
    world = World(setting)

    hero1 = world.add(Entity(id="hero1", kind="character", type=hero1_type, label=hero1_name, role="lead"))
    hero1.id = hero1_name
    del world.entities["hero1"]
    world.entities[hero1_name] = hero1

    hero2 = world.add(Entity(id="hero2", kind="character", type=hero2_type, label=hero2_name, role="partner"))
    hero2.id = hero2_name
    del world.entities["hero2"]
    world.entities[hero2_name] = hero2

    owner = world.add(
        Entity(
            id=mission.owner_name,
            kind="character",
            type=mission.owner_type,
            label=mission.owner_name,
            role="owner",
            tags=set(mission.tags),
        )
    )
    target = world.add(
        Entity(
            id="target",
            kind="thing",
            type="item",
            label=mission.item_label,
            attrs={"phrase": mission.item_phrase, "place": mission.stuck_place},
            tags=set(mission.tags),
        )
    )
    gadget_ent = world.add(
        Entity(
            id="gadget",
            kind="thing",
            type="gadget",
            label=gadget.label,
            attrs={"phrase": gadget.phrase},
            tags=set(gadget.tags),
        )
    )

    world.facts.update(
        hero1=hero1,
        hero2=hero2,
        owner=owner,
        target=target,
        gadget=gadget,
        gadget_entity=gadget_ent,
        mission=mission,
        setting=setting,
        mission_height=mission.height,
        mission_delicate=mission.delicate,
        gadget_reach=gadget.reach,
        gadget_gentle=gadget.gentle,
        risk=risk_level(mission),
    )

    introduce(world, hero1, hero2)
    hear_problem(world, owner, mission)

    world.para()
    boast(world, hero1, gadget)
    warn(world, hero2, hero1, mission, gadget)

    world.para()
    solo_try(world, hero1, mission, gadget)
    decide_share(world, hero1, hero2, gadget, mission)

    world.para()
    shared_try(world, hero1, hero2, owner, mission, gadget)
    ending(world, hero1, hero2, owner, gadget)

    return world


SETTINGS = {
    "park": Setting(
        id="park",
        label="the park",
        scene="The bench became mission control, and the slide shone like a silver launch ramp.",
        affords={"plush_tree", "ball_fence"},
    ),
    "courtyard": Setting(
        id="courtyard",
        label="the apartment courtyard",
        scene="The brick wall looked like a secret hero headquarters, and every flowerpot felt worth protecting.",
        affords={"book_awning", "cape_lamp"},
    ),
    "schoolyard": Setting(
        id="schoolyard",
        label="the schoolyard",
        scene="The painted games on the ground looked like maps for daring rescues.",
        affords={"ball_fence", "book_awning"},
    ),
}

MISSIONS = {
    "plush_tree": Mission(
        id="plush_tree",
        item_label="plush kitten",
        item_phrase="a soft plush kitten",
        owner_name="Ivy",
        owner_type="girl",
        owner_mood="worried",
        stuck_place="from a low branch in the little tree by the swings",
        scene_tail="by the swings",
        height=3,
        delicate=True,
        problem_line='"My plush kitten is hanging from a low branch in the little tree by the swings," she said.',
        success_line="the plush kitten slipped free at last",
        tags={"tree", "toy", "sharing", "teamwork"},
    ),
    "book_awning": Mission(
        id="book_awning",
        item_label="library book",
        item_phrase="a library book with a shiny blue cover",
        owner_name="Noah",
        owner_type="boy",
        owner_mood="upset",
        stuck_place="off the striped awning above the mailboxes",
        scene_tail="above the mailboxes",
        height=2,
        delicate=True,
        problem_line='"A gust flipped my library book onto the striped awning above the mailboxes," he said.',
        success_line="the library book slid down neatly into waiting hands",
        tags={"book", "sharing", "teamwork"},
    ),
    "ball_fence": Mission(
        id="ball_fence",
        item_label="soccer ball",
        item_phrase="a bright soccer ball",
        owner_name="Tomas",
        owner_type="boy",
        owner_mood="glum",
        stuck_place="out of the fence corner where two rails crossed",
        scene_tail="by the fence",
        height=1,
        delicate=False,
        problem_line='"My soccer ball is jammed in the fence corner," he said.',
        success_line="the soccer ball popped loose with a happy bounce",
        tags={"ball", "sharing", "teamwork"},
    ),
    "cape_lamp": Mission(
        id="cape_lamp",
        item_label="puppy cape",
        item_phrase="a tiny puppy cape with yellow stars",
        owner_name="Lena",
        owner_type="girl",
        owner_mood="anxious",
        stuck_place="from the crook of the lamp post by the gate",
        scene_tail="by the gate",
        height=2,
        delicate=False,
        problem_line='"My puppy\'s cape blew up onto the lamp post by the gate," she said.',
        success_line="the puppy cape fluttered down like a tiny flag",
        tags={"cape", "sharing", "teamwork"},
    ),
}

GADGETS = {
    "comet_claw": Gadget(
        id="comet_claw",
        label="the comet-claw",
        phrase="the comet-claw grabber",
        reach=3,
        gentle=True,
        action="hooked and lifted carefully",
        handoff="passed the comet-claw",
        tags={"grabber", "sharing"},
    ),
    "rocket_net": Gadget(
        id="rocket_net",
        label="the rocket-net",
        phrase="the rocket-net pole",
        reach=2,
        gentle=True,
        action="guided the net under it and tipped it down gently",
        handoff="handed the rocket-net",
        tags={"net", "sharing"},
    ),
    "broom": Gadget(
        id="broom",
        label="the broom",
        phrase="the broom from the corner shed",
        reach=3,
        gentle=False,
        action="pushed upward with the broom",
        handoff="offered the broom handle",
        tags={"broom", "sharing"},
    ),
    "sticky_pole": Gadget(
        id="sticky_pole",
        label="the sticky-pole",
        phrase="the short sticky-pole",
        reach=1,
        gentle=True,
        action="reached up with the sticky tip",
        handoff="gave the sticky-pole",
        tags={"pole", "sharing"},
    ),
}

GIRL_NAMES = ["Maya", "Nia", "Ruby", "Ava", "Zoe", "Lila", "Nora", "Iris"]
BOY_NAMES = ["Ben", "Leo", "Max", "Eli", "Owen", "Theo", "Finn", "Sam"]

if __name__ == "__main__":
    main()
