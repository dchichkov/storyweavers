#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py
=============================================================================

A standalone storyworld about two children playing superheroes in a cozy nook.
One child makes a hurtful comparative boast, the other pulls away, and then a
small superhero-style mishap in the nook can only be solved when they work
together and reconcile.

The world model tracks both physical meters and emotional memes. The story is
not a frozen template: the chosen powers determine the kind of boast, the nook
mishap, the way the rescue works, and how the apology lands.

Run it
------
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py --lead-power dash --helper-power lift --mishap bookslide
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py --lead-power dash --helper-power glow --mishap banner
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/comparative_nook_reconciliation_superhero_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Nook:
    id: str
    label: str
    scene: str
    fabric: str
    glow: str
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
class Power:
    id: str
    skill: str
    title: str
    label: str
    comparative: str
    move_text: str
    rescue_text: str
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
class Mishap:
    id: str
    label: str
    object_label: str
    opening: str
    needs: set[str]
    danger_text: str
    solved_text: str
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
class Apology:
    id: str
    offer: str
    line: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {
            "shared_fix": False,
            "apology_made": False,
            "boast_line": "",
            "hurt_child": "",
            "outcome": "unresolved",
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


def propagate(world: World) -> None:
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False

        for ent in list(world.entities.values()):
            if ent.memes["hurt"] >= THRESHOLD:
                sig = ("apart", ent.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    ent.meters["apart"] += 1
                    changed = True

        if world.facts["shared_fix"] and world.facts["apology_made"]:
            for role in ("lead", "helper"):
                kid = next((e for e in world.entities.values() if e.role == role), None)
                if kid is None:
                    continue
                sig = ("peace", kid.id)
                if sig not in world.fired:
                    world.fired.add(sig)
                    kid.memes["peace"] += 1
                    kid.memes["trust"] += 1
                    kid.meters["apart"] = 0.0
                    changed = True


def required_skills(mishap: Mishap) -> set[str]:
    return set(mishap.needs)


def pair_skills(lead: Power, helper: Power) -> set[str]:
    return {lead.skill, helper.skill}


def can_solve(lead: Power, helper: Power, mishap: Mishap) -> bool:
    return pair_skills(lead, helper) == required_skills(mishap)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for lead_id, lead in POWERS.items():
        for helper_id, helper in POWERS.items():
            if lead_id == helper_id:
                continue
            for mishap_id, mishap in MISHAPS.items():
                if can_solve(lead, helper, mishap):
                    combos.append((lead_id, helper_id, mishap_id))
    return sorted(combos)


def explain_rejection(lead: Power, helper: Power, mishap: Mishap) -> str:
    skills = ", ".join(sorted(pair_skills(lead, helper)))
    needs = ", ".join(sorted(required_skills(mishap)))
    if lead.id == helper.id:
        return ("(No story: the two heroes need different powers so the hurt friend "
                "can matter during the rescue.)")
    return (f"(No story: {mishap.label} needs the skills {{{needs}}}, but this hero "
            f"pair only brings {{{skills}}}. The reconciliation works best when both "
            f"children are truly needed.)")


def introduce(world: World, nook: Nook, lead: Entity, helper: Entity,
              lead_power: Power, helper_power: Power) -> None:
    lead.memes["joy"] += 1
    helper.memes["joy"] += 1
    lead.memes["trust"] = 1.0
    helper.memes["trust"] = 1.0
    world.say(
        f"After school, {lead.id} and {helper.id} tucked themselves into {nook.scene}. "
        f"{nook.fabric} and {nook.glow} turned the little nook into a secret hero base."
    )
    world.say(
        f"On one cushion lay a school poster with the word comparative in big blue letters. "
        f"Under it were examples like faster, brighter, and stronger."
    )
    world.say(
        f"{lead.id} tied on a cape and became {lead_power.title}. "
        f"{helper.id} pulled on a mask and became {helper_power.title}."
    )


def boast(world: World, lead: Entity, helper: Entity, lead_power: Power) -> None:
    lead.memes["pride"] += 1
    helper.memes["hurt"] += 1
    line = (f'"I am {lead_power.comparative} than anybody in this whole hideout," '
            f'{lead.id} announced. "I do not really need a partner today."')
    world.facts["boast_line"] = line
    world.facts["hurt_child"] = helper.id
    world.say(line)
    world.say(
        f"The words landed with a thud. {helper.id}'s smile folded up small, and "
        f"{helper.pronoun()} moved to the far pillow without answering."
    )
    propagate(world)


def mishap_happens(world: World, mishap: Mishap, helper: Entity) -> None:
    target = world.get("target")
    target.meters["stuck"] = 1.0
    target.meters["risk"] = 1.0
    world.say(mishap.opening)
    if helper.meters["apart"] >= THRESHOLD:
        world.say(
            f"{helper.id} stayed quiet in the corner for one breath, and the nook felt "
            f"much too small for heroes."
        )
    world.say(mishap.danger_text)


def attempt_alone(world: World, lead: Entity, lead_power: Power, mishap: Mishap) -> None:
    lead.memes["worry"] += 1
    world.say(
        f"{lead.id} sprang forward and {lead_power.move_text}, but that was not enough. "
        f"{mishap.label.capitalize()} needed more than one kind of hero trick."
    )


def apology(world: World, lead: Entity, helper: Entity, apology_cfg: Apology) -> None:
    world.facts["apology_made"] = True
    lead.memes["regret"] += 1
    helper.memes["hope"] += 1
    world.say(
        f"{lead.id} stopped, took a breath, and held out {apology_cfg.offer}. "
        f'"{apology_cfg.line} I was wrong to talk as if I was the only hero," '
        f"{lead.pronoun()} said."
    )


def team_fix(world: World, lead: Entity, helper: Entity, lead_power: Power,
             helper_power: Power, mishap: Mishap) -> None:
    target = world.get("target")
    world.facts["shared_fix"] = True
    target.meters["stuck"] = 0.0
    target.meters["safe"] = 1.0
    helper.memes["bravery"] += 1
    lead.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} looked at {lead.id}, then nodded. Together they moved at once: "
        f"{lead.id} {lead_power.rescue_text}, and {helper.id} {helper_power.rescue_text}."
    )
    world.say(mishap.solved_text)
    propagate(world)


def closing(world: World, nook: Nook, lead: Entity, helper: Entity, mishap: Mishap) -> None:
    lead.memes["joy"] += 1
    helper.memes["joy"] += 1
    target = world.get("target")
    if target.meters["safe"] >= THRESHOLD and lead.memes["peace"] >= THRESHOLD and helper.memes["peace"] >= THRESHOLD:
        world.facts["outcome"] = "reconciled"
        world.say(
            f"Then the two heroes sat shoulder to shoulder again in the {nook.label}, "
            f"with {mishap.object_label} safe between them."
        )
        world.say(
            f"{lead.id} bumped {helper.id}'s shoulder and smiled. "
            f'"A real hero team is better together," {lead.pronoun()} said. '
            f"This time, both of them laughed."
        )
    else:
        world.facts["outcome"] = "failed"
        world.say(
            f"The nook grew quiet again. {mishap.object_label.capitalize()} was still there, "
            f"but the brave feeling had gone out of the game."
        )


def tell(nook: Nook, lead_power: Power, helper_power: Power, mishap: Mishap,
         apology_cfg: Apology, lead_name: str, lead_gender: str,
         helper_name: str, helper_gender: str, parent_type: str) -> World:
    world = World()
    lead = world.add(Entity(
        id=lead_name,
        kind="character",
        type=lead_gender,
        role="lead",
        traits=["bold"],
        attrs={"power": lead_power.id},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["gentle"],
        attrs={"power": helper_power.id},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        role="parent",
        label="the parent",
    ))
    target = world.add(Entity(
        id="target",
        kind="thing",
        type="mission_object",
        label=mishap.object_label,
    ))
    world.facts.update(
        nook=nook,
        lead=lead,
        helper=helper,
        parent=parent,
        lead_power=lead_power,
        helper_power=helper_power,
        mishap=mishap,
        apology=apology_cfg,
    )

    introduce(world, nook, lead, helper, lead_power, helper_power)
    world.para()
    boast(world, lead, helper, lead_power)
    world.para()
    mishap_happens(world, mishap, helper)
    attempt_alone(world, lead, lead_power, mishap)
    world.para()
    apology(world, lead, helper, apology_cfg)
    team_fix(world, lead, helper, lead_power, helper_power, mishap)
    world.para()
    closing(world, nook, lead, helper, mishap)
    return world


NOOKS = {
    "pillow": Nook(
        id="pillow",
        label="pillow nook",
        scene="a pillow nook under the window seat",
        fabric="A blanket roof drooped low over stacked cushions",
        glow="a string of star lights made gold puddles on the pages of their comic books",
        tags={"nook"},
    ),
    "blanket": Nook(
        id="blanket",
        label="blanket nook",
        scene="a blanket nook between the sofa and the bookcase",
        fabric="Pinned quilts made soft walls on both sides",
        glow="a clip lamp shone across a parade of toy heroes",
        tags={"nook"},
    ),
    "book": Nook(
        id="book",
        label="book nook",
        scene="a book nook behind the big armchair",
        fabric="A curtain of scarves made a secret doorway",
        glow="the reading lamp painted a warm circle over the rug",
        tags={"nook"},
    ),
}

POWERS = {
    "dash": Power(
        id="dash",
        skill="speed",
        title="Captain Dash",
        label="super speed",
        comparative="faster",
        move_text="blurred around the cushions like a red streak",
        rescue_text="raced to block the rolling trouble before it could bump the wall",
        tags={"speed"},
    ),
    "glow": Power(
        id="glow",
        skill="glow",
        title="Star Glow",
        label="super light",
        comparative="brighter",
        move_text="lifted both hands and sent a warm beam across the fort",
        rescue_text="shone a clear beam into the deepest shadows of the nook",
        tags={"light"},
    ),
    "lift": Power(
        id="lift",
        skill="lift",
        title="Mighty Lift",
        label="super strength",
        comparative="stronger",
        move_text="planted both feet and tried to heave the trouble aside",
        rescue_text="heaved the heavy part up just enough to free the mission",
        tags={"strength"},
    ),
    "stretch": Power(
        id="stretch",
        skill="stretch",
        title="Reach Ranger",
        label="stretchy arms",
        comparative="longer",
        move_text="reached and reached, but could not quite manage the angle alone",
        rescue_text="slid a long careful arm into the narrow gap and hooked the prize gently",
        tags={"reach"},
    ),
}

MISHAPS = {
    "bookslide": Mishap(
        id="bookslide",
        label="the tumbling comic stack",
        object_label="their special comic box",
        opening="All at once, a stack of heavy comic books tipped from the top crate and began to slide toward their special comic box.",
        needs={"speed", "lift"},
        danger_text="If nobody caught the stack quickly and lifted it away, the box would be squashed at the mouth of the nook.",
        solved_text="The books thumped to a stop, the box came free, and not one treasured page was bent.",
        tags={"books"},
    ),
    "badge_gap": Mishap(
        id="badge_gap",
        label="the badge in the dark gap",
        object_label="their silver rescue badge",
        opening="Then their silver rescue badge skittered across the rug and slipped into a dark crack behind the bookcase.",
        needs={"glow", "stretch"},
        danger_text="The gap was too dim to see inside and too narrow for an ordinary arm.",
        solved_text="A bright gleam flashed in the crack, a careful hand reached in, and the badge came out sparkling with dust like moon sand.",
        tags={"dark", "badge"},
    ),
    "banner_snag": Mishap(
        id="banner_snag",
        label="the snagged victory banner",
        object_label="their paper victory banner",
        opening="A gust from the vent fluttered their paper victory banner high onto a lamp hook, where it wrapped itself in a tight little knot.",
        needs={"lift", "stretch"},
        danger_text="It was too high for a normal reach, and the knot would tear if anyone yanked too hard.",
        solved_text="One hero steadied the climb while the other reached the knot, and soon the banner floated down smooth and safe.",
        tags={"banner"},
    ),
    "alarm_button": Mishap(
        id="alarm_button",
        label="the lost alarm button",
        object_label="their red alarm button",
        opening="Right then, their red alarm button popped off the toy panel, bounced under the couch, and vanished into the shadows at the edge of the nook.",
        needs={"speed", "glow"},
        danger_text="It had gone somewhere dark and small, and it might roll deeper if they were too slow.",
        solved_text="A ribbon of light found the red shine at once, and a quick hand darted in before the button could roll away again.",
        tags={"alarm", "dark"},
    ),
}

APOLOGIES = {
    "cape": Apology(
        id="cape",
        offer="the bright blue spare cape",
        line="Here. You should wear this with me.",
        tags={"share"},
    ),
    "badge": Apology(
        id="badge",
        offer="the shiny team badge",
        line="This belongs to both of us.",
        tags={"share"},
    ),
    "cookie": Apology(
        id="cookie",
        offer="half of the star-shaped cookie from their snack plate",
        line="I saved the bigger half for you.",
        tags={"share"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo", "Owen"]

KNOWLEDGE = {
    "comparative": [
        (
            "What is a comparative word?",
            "A comparative word is a word we use when we compare two things, like faster, brighter, or stronger. It tells how one thing is more of something than another."
        )
    ],
    "nook": [
        (
            "What is a nook?",
            "A nook is a small cozy corner or tucked-away place. People often use a nook for reading, resting, or quiet play."
        )
    ],
    "speed": [
        (
            "Why can speed help in a rescue?",
            "Speed helps when something might roll, fall, or slip away. Getting there quickly can stop a small problem from becoming a bigger one."
        )
    ],
    "strength": [
        (
            "Why is strength useful when something heavy is stuck?",
            "Strength can help lift or steady heavy things safely. That makes room for someone to move the trapped thing free."
        )
    ],
    "light": [
        (
            "Why is light helpful in dark places?",
            "Light helps people see what is hidden in a dark place. When you can see clearly, you can move more carefully."
        )
    ],
    "reach": [
        (
            "Why is a long reach useful in a tight space?",
            "A long reach helps when something is far back in a narrow place. It lets you get to the object without pulling or shaking everything around it."
        )
    ],
    "share": [
        (
            "What can help two friends reconcile after hurt feelings?",
            "A true apology helps, and so does sharing in a kind way. Reconciliation means the people listen, make things right, and choose to be close again."
        )
    ],
}
KNOWLEDGE_ORDER = ["comparative", "nook", "speed", "strength", "light", "reach", "share"]


@dataclass
class StoryParams:
    nook: str
    lead_power: str
    helper_power: str
    mishap: str
    apology: str
    lead_name: str
    lead_gender: str
    helper_name: str
    helper_gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    nook = f["nook"]
    mishap = f["mishap"]
    lead_power = f["lead_power"]
    return [
        f'Write a short superhero story for a 3-to-5-year-old that includes the words "comparative" and "nook".',
        f"Tell a superhero story where {lead.id} hurts {helper.id}'s feelings with a comparative boast in a {nook.label}, and the two children must reconcile during a rescue.",
        f"Write a gentle action story where a hero claims to be {lead_power.comparative}, a mission goes wrong with {mishap.object_label}, and teamwork fixes both the problem and the friendship.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    helper = f["helper"]
    nook = f["nook"]
    mishap = f["mishap"]
    lead_power = f["lead_power"]
    helper_power = f["helper_power"]
    apology_cfg = f["apology"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {helper.id}, two children pretending to be superheroes in a {nook.label}. Their game turns into a real little mission when {mishap.object_label} gets into trouble."
        ),
        (
            f"Why were {helper.id}'s feelings hurt?",
            f"{lead.id} bragged about being {lead_power.comparative} and said {lead.pronoun('subject')} did not need a partner. That made {helper.id} feel pushed away instead of included."
        ),
        (
            f"What problem happened in the nook?",
            f"{mishap.opening} {mishap.danger_text} The mishap mattered because one hero alone could not solve it safely."
        ),
        (
            f"Why did {lead.id} need {helper.id} after all?",
            f"{lead.id}'s power was {lead_power.label}, but the mission also needed {helper_power.label}. The rescue only worked when both children used different strengths together."
        ),
        (
            "How did they reconcile?",
            f"{lead.id} apologized and offered {apology_cfg.offer}. Then {helper.id} chose to help, so the apology turned into action and their friendship felt warm again."
        ),
        (
            "How did the story end?",
            f"It ended with the two heroes sitting close together again in the nook with {mishap.object_label} safe between them. That ending image shows both the mission and the friendship were repaired."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"comparative", "nook"} | set(f["lead_power"].tags) | set(f["helper_power"].tags) | set(f["apology"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} hurt_child={world.facts.get('hurt_child')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        nook="pillow",
        lead_power="dash",
        helper_power="lift",
        mishap="bookslide",
        apology="badge",
        lead_name="Max",
        lead_gender="boy",
        helper_name="Lily",
        helper_gender="girl",
        parent="mother",
    ),
    StoryParams(
        nook="blanket",
        lead_power="glow",
        helper_power="stretch",
        mishap="badge_gap",
        apology="cape",
        lead_name="Mia",
        lead_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        parent="father",
    ),
    StoryParams(
        nook="book",
        lead_power="lift",
        helper_power="stretch",
        mishap="banner_snag",
        apology="cookie",
        lead_name="Theo",
        lead_gender="boy",
        helper_name="Nora",
        helper_gender="girl",
        parent="mother",
    ),
    StoryParams(
        nook="pillow",
        lead_power="dash",
        helper_power="glow",
        mishap="alarm_button",
        apology="cape",
        lead_name="Ava",
        lead_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        parent="father",
    ),
]


ASP_RULES = r"""
pair_skill(P1,S) :- power(P1), skill(P1,S).
need(M,S) :- mishap(M), requires(M,S).

valid(P1,P2,M) :- power(P1), power(P2), P1 != P2, mishap(M),
                  requires(M,S1), skill(P1,S1),
                  requires(M,S2), skill(P2,S2),
                  S1 != S2,
                  not extra_need_missing(P1,P2,M).

extra_need_missing(P1,P2,M) :- requires(M,S), not skill(P1,S), not skill(P2,S).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, power in POWERS.items():
        lines.append(asp.fact("power", pid))
        lines.append(asp.fact("skill", pid, power.skill))
    for mid, mishap in MISHAPS.items():
        lines.append(asp.fact("mishap", mid))
        for skill in sorted(mishap.needs):
            lines.append(asp.fact("requires", mid, skill))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a superhero nook quarrel that turns into reconciliation."
    )
    ap.add_argument("--nook", choices=NOOKS)
    ap.add_argument("--lead-power", choices=POWERS)
    ap.add_argument("--helper-power", choices=POWERS)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--apology", choices=APOLOGIES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible hero-pair and mishap combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.lead_power and args.helper_power and args.lead_power == args.helper_power:
        raise StoryError("(No story: the two heroes need different powers so the teamwork can matter.)")

    if args.lead_power and args.helper_power and args.mishap:
        lead = POWERS[args.lead_power]
        helper = POWERS[args.helper_power]
        mishap = MISHAPS[args.mishap]
        if not can_solve(lead, helper, mishap):
            raise StoryError(explain_rejection(lead, helper, mishap))

    combos = [
        combo for combo in valid_combos()
        if (args.lead_power is None or combo[0] == args.lead_power)
        and (args.helper_power is None or combo[1] == args.helper_power)
        and (args.mishap is None or combo[2] == args.mishap)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    lead_power, helper_power, mishap = rng.choice(combos)
    nook = args.nook or rng.choice(sorted(NOOKS))
    apology = args.apology or rng.choice(sorted(APOLOGIES))
    parent = args.parent or rng.choice(["mother", "father"])

    lead_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if lead_gender == "boy" else "boy" if rng.random() < 0.5 else lead_gender
    lead_name = pick_name(rng, lead_gender)
    helper_name = pick_name(rng, helper_gender, avoid=lead_name)

    return StoryParams(
        nook=nook,
        lead_power=lead_power,
        helper_power=helper_power,
        mishap=mishap,
        apology=apology,
        lead_name=lead_name,
        lead_gender=lead_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.nook not in NOOKS:
        raise StoryError(f"(No story: unknown nook '{params.nook}'.)")
    if params.lead_power not in POWERS:
        raise StoryError(f"(No story: unknown lead power '{params.lead_power}'.)")
    if params.helper_power not in POWERS:
        raise StoryError(f"(No story: unknown helper power '{params.helper_power}'.)")
    if params.mishap not in MISHAPS:
        raise StoryError(f"(No story: unknown mishap '{params.mishap}'.)")
    if params.apology not in APOLOGIES:
        raise StoryError(f"(No story: unknown apology '{params.apology}'.)")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown parent type '{params.parent}'.)")

    lead_power = POWERS[params.lead_power]
    helper_power = POWERS[params.helper_power]
    mishap = MISHAPS[params.mishap]
    if not can_solve(lead_power, helper_power, mishap):
        raise StoryError(explain_rejection(lead_power, helper_power, mishap))

    world = tell(
        nook=NOOKS[params.nook],
        lead_power=lead_power,
        helper_power=helper_power,
        mishap=mishap,
        apology_cfg=APOLOGIES[params.apology],
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in compatible combos:")
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
        print(f"SMOKE FAIL: default parameter resolution raised StoryError: {err}")

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise RuntimeError("empty story")
            if "comparative" not in sample.story or "nook" not in sample.story:
                raise RuntimeError("required seed words missing from story text")
            print(f"OK: smoke story {idx} generated ({params.lead_power}, {params.helper_power}, {params.mishap}).")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (lead_power, helper_power, mishap) combos:\n")
        for lead_power, helper_power, mishap in combos:
            print(f"  {lead_power:8} {helper_power:8} {mishap}")
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
            header = f"### {p.lead_name} & {p.helper_name}: {p.lead_power} + {p.helper_power} ({p.mishap})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
