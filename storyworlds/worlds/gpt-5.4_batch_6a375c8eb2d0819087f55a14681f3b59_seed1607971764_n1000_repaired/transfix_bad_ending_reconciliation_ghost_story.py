#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py
============================================================================

A standalone story world for a gentle ghost story about a child, a keepsake
taken from the wrong place, a frightening haunting, and either a sad ending or
a reconciliation that sets the house at peace.

The domain models a small haunted-house logic:

- A ghost is tied to a keepsake and a resting place in the house.
- A child moves the keepsake for play or curiosity.
- The house grows colder and stranger as the ghost's grief rises.
- An apology and a sensible repair/return can reconcile the living and the dead.
- Hiding the mistake leaves the house lonely and haunted: the bad ending.

Run it
------
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py --haunt attic --keepsake locket --response return_apology
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py --response joke
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py --all
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/transfix_bad_ending_reconciliation_ghost_story.py --verify
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
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    owner: str = ""
    anchor_site: str = ""
    fragile: bool = False
    luminous: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother"}
        male = {"boy", "father", "man", "grandfather"}
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
class Haunt:
    id: str
    room: str
    detail: str
    hush: str
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
class Keepsake:
    id: str
    label: str
    phrase: str
    use: str
    fragile: bool
    anchor_site: str
    ghost_name: str
    ghost_type: str
    memory: str
    final_image: str
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
class Motive:
    id: str
    lead: str
    action: str
    risk: int
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
class Response:
    id: str
    sense: int
    calms: int
    repairs: bool
    text: str
    success: str
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


def _r_grief_chill(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    house = world.get("house")
    if ghost.memes["grief"] >= THRESHOLD:
        sig = ("chill",)
        if sig not in world.fired:
            world.fired.add(sig)
            house.meters["cold"] += 1
            house.meters["whispers"] += 1
            out.append("__haunt__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    house = world.get("house")
    ghost = world.get("ghost")
    if house.meters["cold"] >= THRESHOLD and ghost.meters["manifest"] >= THRESHOLD:
        sig = ("fear",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_peace(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("ghost")
    house = world.get("house")
    if ghost.memes["comfort"] >= THRESHOLD and ghost.memes["grief"] <= 0:
        sig = ("peace",)
        if sig not in world.fired:
            world.fired.add(sig)
            house.meters["cold"] = 0.0
            house.meters["whispers"] = 0.0
            house.meters["peace"] += 1
            out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="grief_chill", tag="physical", apply=_r_grief_chill),
    Rule(name="fear", tag="emotional", apply=_r_fear),
    Rule(name="peace", tag="physical", apply=_r_peace),
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


def keepsake_belongs_in_haunt(keepsake: Keepsake, haunt: Haunt) -> bool:
    return keepsake.anchor_site == haunt.id


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def haunting_severity(motive: Motive, delay: int, broken: bool) -> int:
    return motive.risk + delay + (1 if broken else 0)


def can_reconcile(response: Response, motive: Motive, delay: int, broken: bool) -> bool:
    needed = haunting_severity(motive, delay, broken)
    if broken and not response.repairs:
        return False
    return response.calms >= needed


def predict_haunt(world: World, motive: Motive, broken: bool) -> dict:
    sim = world.copy()
    _take_keepsake(sim, motive=motive, broken=broken, narrate=False)
    return {
        "cold": sim.get("house").meters["cold"],
        "fear": sim.get("child").memes["fear"],
        "manifest": sim.get("ghost").meters["manifest"],
    }


def _take_keepsake(world: World, motive: Motive, broken: bool, narrate: bool = True) -> None:
    child = world.get("child")
    keepsake = world.get("keepsake")
    ghost = world.get("ghost")
    house = world.get("house")
    keepsake.attrs["moved"] = True
    ghost.memes["grief"] += 1
    ghost.meters["manifest"] += 1
    house.meters["disturbed"] += 1
    child.memes["wonder"] += 1
    if broken:
        keepsake.meters["broken"] += 1
        ghost.memes["grief"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, child: Entity, caretaker: Entity, haunt: Haunt) -> None:
    world.say(
        f"On a windy evening, {child.id} and {child.pronoun('possessive')} {caretaker.label_word} "
        f"were staying in an old house with {haunt.detail}. {haunt.hush}"
    )
    world.say(
        f"{child.id} liked pretending not to be scared, but every long hallway in that house "
        f"seemed to listen back."
    )


def discover(world: World, child: Entity, haunt: Haunt, keepsake: Keepsake) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"While {caretaker_phrase(world)} folded blankets downstairs, {child.id} wandered to "
        f"the {haunt.room} and found {keepsake.phrase} resting there."
    )
    world.say(
        f"It looked as if it had been waiting a very long time. {child.id} lifted it gently and "
        f"wondered who had once used it {keepsake.use}."
    )


def caretaker_phrase(world: World) -> str:
    return world.get("caretaker").label_word.capitalize()


def tempt(world: World, child: Entity, motive: Motive, keepsake: Keepsake) -> None:
    world.say(
        f'{motive.lead} "{keepsake.label.capitalize()}s should not sit alone in the dark," '
        f"{child.id} whispered."
    )
    world.say(
        f"{child.id} {motive.action}."
    )


def warn(world: World, child: Entity, caretaker: Entity, motive: Motive, keepsake: Keepsake, haunt: Haunt) -> None:
    pred = predict_haunt(world, motive=motive, broken=keepsake.fragile and motive.id == "play")
    world.facts["predicted_cold"] = pred["cold"]
    world.facts["predicted_fear"] = pred["fear"]
    child.memes["doubt"] += 1
    world.say(
        f'From the stairs, {caretaker.label_word.capitalize()} called, "If you found something old in the '
        f'{haunt.room}, leave it there for now."'
    )
    world.say(
        f"{child.id} paused. The warning made the house feel even stiller, as if the shadows themselves "
        f"were listening."
    )


def defy(world: World, child: Entity, keepsake: Keepsake) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"But the strange little treasure seemed to transfix {child.id}. Instead of putting {keepsake.label} "
        f"back, {child.pronoun()} carried it away."
    )


def haunting(world: World, child: Entity, ghost: Entity, haunt: Haunt, keepsake: Keepsake) -> None:
    _take_keepsake(world, motive=MOTIVES[world.facts["motive"].id], broken=world.facts["broken"], narrate=False)
    world.say(
        f"That night the {haunt.room} door opened by itself. A thin white figure stood in the doorway, "
        f"pale as window frost."
    )
    world.say(
        f"It was {ghost.id}, and {ghost.pronoun()} did not shout or rush. {ghost.pronoun().capitalize()} only "
        f"looked at the empty place where {keepsake.phrase} had been, and the whole house turned cold."
    )
    if world.facts["broken"]:
        world.say(
            f"When {child.id} saw the crack running through the {keepsake.label}, {child.pronoun()} understood "
            f"why the ghost looked so terribly sad."
        )
    else:
        world.say(
            f"{child.id} felt the sorrow before {child.pronoun()} understood it. This was not a monster hunting "
            f"for children. This was someone looking for what had been taken."
        )


def plea(world: World, ghost: Entity, keepsake: Keepsake) -> None:
    ghost.memes["longing"] += 1
    world.say(
        f'"Please," the ghost whispered, voice soft as dust, "bring back my {keepsake.label}. '
        f'It is all I have left of {world.facts["keepsake_cfg"].memory}."'
    )


def hide_from_truth(world: World, child: Entity, caretaker: Entity, haunt: Haunt) -> None:
    child.memes["shame"] += 1
    world.say(
        f"{child.id} pulled the blanket over {child.pronoun('possessive')} head and told {caretaker.label_word} "
        f"that nothing was wrong."
    )
    world.say(
        f"But by morning the windows were pearled with ice from the inside, and nobody wanted to go near "
        f"the {haunt.room}."
    )


def bad_ending(world: World, child: Entity, ghost: Entity, haunt: Haunt) -> None:
    world.get("house").meters["haunted"] += 1
    child.memes["fear"] += 1
    ghost.memes["grief"] += 1
    world.say(
        f"{caretaker_phrase(world)} packed their bags before breakfast. As they left, {child.id} glanced back and "
        f"saw {ghost.id} standing at the top of the stairs, lonelier than before."
    )
    world.say(
        f"No one in the village would rent the house after that. On windy nights, the {haunt.room} window still "
        f"glows pale, and the house keeps its grief."
    )


def ask_for_help(world: World, child: Entity, caretaker: Entity) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"At last {child.id} began to cry and told {caretaker.label_word} everything."
    )
    world.say(
        f"Instead of scolding, {caretaker.label_word} took {child.pronoun('possessive')} hand and said, "
        f'"Then we will make it right."'
    )


def reconcile(world: World, child: Entity, caretaker: Entity, ghost: Entity, keepsake: Keepsake, response: Response, haunt: Haunt) -> None:
    child.memes["care"] += 1
    ghost.memes["comfort"] += 1
    ghost.memes["grief"] = 0.0
    if world.facts["broken"] and response.repairs:
        keepsake.meters["broken"] = 0.0
        keepsake.meters["mended"] += 1
    keepsake.attrs["moved"] = False
    propagate(world, narrate=False)
    world.say(
        f"{response.text}".replace("{child}", child.id).replace("{caretaker}", caretaker.label_word)
        .replace("{keepsake}", keepsake.label).replace("{room}", haunt.room)
    )
    world.say(
        f"{response.success}".replace("{ghost}", ghost.id).replace("{keepsake}", keepsake.label)
    )
    world.say(
        f"The cold loosened at once. The old house no longer felt hungry for footsteps or tears."
    )


def farewell(world: World, child: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    child.memes["relief"] += 1
    child.memes["lesson"] += 1
    world.say(
        f'{ghost.id} smiled for the first time. "Thank you," {ghost.pronoun()} said, and {ghost.pronoun()} grew '
        f"thin as moonlight on glass."
    )
    world.say(
        f"After that, {child.id} passed the old resting place softly and never touched what was not "
        f"{child.pronoun('possessive')} to take. Sometimes the house smelled faintly of lavender, and "
        f"{keepsake.final_image}."
    )
@dataclass
class StoryParams:
    haunt: str
    keepsake: str
    motive: str
    response: str
    child_name: str
    child_type: str
    caretaker_type: str
    delay: int = 0
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
    "ghost": [(
        "What is a ghost in a story?",
        "In a story, a ghost is the spirit of someone who has died. Ghost stories often use cold air, whispers, or old rooms to show that a memory has not rested."
    )],
    "attic": [(
        "What is an attic?",
        "An attic is a room just under the roof of a house. People often store old trunks, boxes, and keepsakes there."
    )],
    "hallway": [(
        "What is a hallway?",
        "A hallway is the long space that connects rooms in a house. In stories, a quiet hallway can feel spooky because sound carries through it."
    )],
    "nursery": [(
        "What is a nursery?",
        "A nursery is a room for a baby or very young child. In old houses, a nursery can hold toys, songs, and strong family memories."
    )],
    "locket": [(
        "What is a locket?",
        "A locket is a small piece of jewelry that opens. People often keep a tiny picture or a little memory inside."
    )],
    "music_box": [(
        "What is a music box?",
        "A music box is a small box that plays a tune when it is wound or opened. Because it holds a remembered song, it can feel special and precious."
    )],
    "toy_boat": [(
        "What is a toy boat?",
        "A toy boat is a small model boat made for play or for keeping as a treasure. Old toys can matter a lot when they remind someone of a person they loved."
    )],
    "apology": [(
        "Why can an apology help fix a mistake?",
        "An apology shows that you understand the hurt you caused. When you also try to make things right, the other person can begin to feel safe again."
    )],
    "repair": [(
        "What does it mean to mend something?",
        "To mend something means to fix what was torn, cracked, or broken. Repairing an object can also show care for the person it belongs to."
    )],
    "song": [(
        "Why can a song feel comforting?",
        "A soft song can remind someone of love and home. In stories, music can calm fear and help sad feelings settle."
    )],
    "memory": [(
        "Why do people keep keepsakes?",
        "People keep keepsakes because objects can hold memories of people, places, and moments they do not want to forget."
    )],
}
KNOWLEDGE_ORDER = [
    "ghost", "attic", "hallway", "nursery", "locket", "music_box", "toy_boat",
    "memory", "apology", "repair", "song"
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    haunt = f["haunt"]
    keepsake_cfg = f["keepsake_cfg"]
    outcome = f["outcome"]
    if outcome == "haunted":
        return [
            f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "transfix". A child takes a keepsake from an old {haunt.room}, meets a sad ghost, and the story ends badly.',
            f"Tell a spooky story where {child.id} is transfixed by {keepsake_cfg.phrase}, ignores a warning, and leaves a ghost lonelier than before.",
            f"Write a haunted-house story with a bad ending first: the child hides the truth, the family leaves, and the house stays sorrowful.",
        ]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "transfix". A child takes a keepsake from an old {haunt.room}, frightens a ghost, and then makes peace.',
        f"Tell a spooky but tender story where {child.id} is transfixed by {keepsake_cfg.phrase}, then apologizes and helps return it.",
        f"Write a reconciliation ghost story in which a frightened child learns that haunting sorrow can be eased by honesty, repair, and care.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    ghost = f["ghost"]
    haunt = f["haunt"]
    keepsake_cfg = f["keepsake_cfg"]
    motive = f["motive"]
    response = f["response"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in an old house, and {ghost.id}, the ghost tied to a treasured {keepsake_cfg.label}. Their trouble begins when {child.id} carries the keepsake away from the {haunt.room}."
        ),
        (
            f"Why did {child.id} take the {keepsake_cfg.label}?",
            f"{child.id} took it because {motive.lead.lower()} {child.pronoun()} {motive.action}. The keepsake seemed mysterious and special, so curiosity pushed past caution."
        ),
        (
            f"Why did the ghost appear?",
            f"{ghost.id} appeared because the {keepsake_cfg.label} had been moved from the {haunt.room}, where it belonged. The haunting came from grief, not from a wish to hurt anyone."
        ),
    ]
    if f["broken"]:
        qa.append((
            f"Why did the haunting feel even worse after {child.id} touched the keepsake?",
            f"The keepsake was fragile, and it cracked while {child.id} had it. That made the ghost's sorrow deeper, because the object was both taken away and damaged."
        ))
    if f["outcome"] == "haunted":
        qa.append((
            "How did the story end?",
            f"It ended sadly: {child.id} hid the truth, the family left the house, and {ghost.id} remained alone there. The ending stays cold because the mistake was never repaired."
        ))
        qa.append((
            f"Why could nobody make the house peaceful again that night?",
            f"They did not truly make things right. Without an honest apology and the right return or repair, the ghost's grief kept filling the house."
        ))
    else:
        qa.append((
            f"How did {child.id} and {caretaker.label_word} fix the problem?",
            f"{response.qa_text} That mattered because the ghost did not only want the object back; {ghost.pronoun()} also needed to know the living understood the hurt they had caused."
        ))
        qa.append((
            "What changed at the end of the story?",
            f"The cold and whispers stopped, and the house felt peaceful again. Reconciliation changed the ending because honesty and care answered the ghost's sorrow."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"ghost", "memory"} | set(f["haunt"].tags) | set(f["keepsake_cfg"].tags)
    if f["outcome"] == "reconciled":
        tags |= set(f["response"].tags)
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.anchor_site:
            bits.append(f"anchor_site={ent.anchor_site}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        haunt="attic",
        keepsake="locket",
        motive="comfort",
        response="return_apology",
        child_name="Mira",
        child_type="girl",
        caretaker_type="mother",
        delay=0,
    ),
    StoryParams(
        haunt="nursery",
        keepsake="music_box",
        motive="play",
        response="mend_return",
        child_name="Owen",
        child_type="boy",
        caretaker_type="father",
        delay=0,
    ),
    StoryParams(
        haunt="hallway",
        keepsake="toy_boat",
        motive="show",
        response="sing_song",
        child_name="June",
        child_type="girl",
        caretaker_type="mother",
        delay=1,
    ),
    StoryParams(
        haunt="nursery",
        keepsake="music_box",
        motive="play",
        response="return_apology",
        child_name="Theo",
        child_type="boy",
        caretaker_type="father",
        delay=1,
    ),
    StoryParams(
        haunt="attic",
        keepsake="locket",
        motive="comfort",
        response="joke",
        child_name="Elsie",
        child_type="girl",
        caretaker_type="mother",
        delay=1,
    ),
]


def explain_rejection(haunt: Haunt, keepsake: Keepsake) -> str:
    return (
        f"(No story: {keepsake.phrase} belongs in the {HAUNTS[keepsake.anchor_site].room}, "
        f"not in the {haunt.room}. The haunting only makes sense when the ghost's keepsake is taken "
        f"from its own resting place.)"
    )


def explain_response(response_id: str) -> str:
    r = RESPONSES[response_id]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try a response that actually returns or repairs the keepsake, such as {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if params.haunt not in HAUNTS or params.keepsake not in KEEPSAKES or params.motive not in MOTIVES or params.response not in RESPONSES:
        raise StoryError("(No story: unknown parameter value.)")
    keepsake = KEEPSAKES[params.keepsake]
    haunt = HAUNTS[params.haunt]
    if not keepsake_belongs_in_haunt(keepsake, haunt):
        raise StoryError(explain_rejection(haunt, keepsake))
    return "reconciled" if can_reconcile(RESPONSES[params.response], MOTIVES[params.motive], params.delay, keepsake.fragile and params.motive == "play") else "haunted"


ASP_RULES = r"""
belongs(K,H) :- anchor(K,H).
valid(H,K,M) :- haunt(H), keepsake(K), motive(M), belongs(K,H).

sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.

broken :- chosen_keepsake(K), fragile(K), chosen_motive(play).
severity(V) :- chosen_motive(M), risk(M,R), delay(D), broken, V = R + D + 1.
severity(V) :- chosen_motive(M), risk(M,R), delay(D), not broken, V = R + D.

repair_needed :- broken.
repair_missing :- repair_needed, chosen_response(R), not repairs(R).
can_reconcile :- chosen_response(R), calm_power(R,C), severity(V), C >= V, not repair_missing.

outcome(reconciled) :- can_reconcile.
outcome(haunted) :- not can_reconcile.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for haunt_id in HAUNTS:
        lines.append(asp.fact("haunt", haunt_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("anchor", keepsake_id, keepsake.anchor_site))
        if keepsake.fragile:
            lines.append(asp.fact("fragile", keepsake_id))
    for motive_id, motive in MOTIVES.items():
        lines.append(asp.fact("motive", motive_id))
        lines.append(asp.fact("risk", motive_id, motive.risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("calm_power", response_id, response.calms))
        if response.repairs:
            lines.append(asp.fact("repairs", response_id))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_keepsake", params.keepsake),
        asp.fact("chosen_motive", params.motive),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        try:
            py = outcome_of(params)
            cl = asp_outcome(params)
        except StoryError as err:
            rc = 1
            print(err)
            mismatch += 1
            continue
        if py != cl:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child disturbs a ghost's keepsake and must face either a sad haunting or a reconciliation."
    )
    ap.add_argument("--haunt", choices=HAUNTS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--caretaker-type", choices=["mother", "father"])
    ap.add_argument("--child-name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the child waits before trying to fix the mistake")
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
    if args.haunt and args.keepsake:
        haunt = HAUNTS[args.haunt]
        keepsake = KEEPSAKES[args.keepsake]
        if not keepsake_belongs_in_haunt(keepsake, haunt):
            raise StoryError(explain_rejection(haunt, keepsake))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.haunt is None or combo[0] == args.haunt)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.motive is None or combo[2] == args.motive)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    haunt_id, keepsake_id, motive_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    caretaker_type = args.caretaker_type or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        haunt=haunt_id,
        keepsake=keepsake_id,
        motive=motive_id,
        response=response_id,
        child_name=child_name,
        child_type=child_type,
        caretaker_type=caretaker_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.haunt not in HAUNTS:
        raise StoryError(f"(No story: unknown haunt '{params.haunt}'.)")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(No story: unknown keepsake '{params.keepsake}'.)")
    if params.motive not in MOTIVES:
        raise StoryError(f"(No story: unknown motive '{params.motive}'.)")
    if params.response not in RESPONSES:
        raise StoryError(f"(No story: unknown response '{params.response}'.)")

    haunt = HAUNTS[params.haunt]
    keepsake = KEEPSAKES[params.keepsake]
    motive = MOTIVES[params.motive]
    response = RESPONSES[params.response]

    if not keepsake_belongs_in_haunt(keepsake, haunt):
        raise StoryError(explain_rejection(haunt, keepsake))

    world = tell(
        haunt=haunt,
        keepsake_cfg=keepsake,
        motive=motive,
        response=response,
        child_name=params.child_name,
        child_type=params.child_type,
        caretaker_type=params.caretaker_type,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (haunt, keepsake, motive) combos:\n")
        for haunt, keepsake, motive in combos:
            print(f"  {haunt:8} {keepsake:10} {motive}")
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
            header = f"### {p.child_name}: {p.keepsake} in the {p.haunt} ({p.motive}, {p.response}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")






def tell(
    haunt: Haunt,
    keepsake_cfg: Keepsake,
    motive: Motive,
    response: Response,
    child_name: str = "Mira",
    child_type: str = "girl",
    caretaker_type: str = "mother",
    delay: int = 0,
) -> World:
    world = World()
    broken = keepsake_cfg.fragile and motive.id == "play"
    world.facts["broken"] = broken
    world.facts["motive"] = motive
    world.facts["keepsake_cfg"] = keepsake_cfg

    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_type, role="caretaker", label="the parent"))
    ghost = world.add(
        Entity(
            id=keepsake_cfg.ghost_name,
            kind="character",
            type=keepsake_cfg.ghost_type,
            role="ghost",
            anchor_site=haunt.id,
            attrs={"memory": keepsake_cfg.memory},
        )
    )
    keepsake = world.add(
        Entity(
            id="keepsake",
            type="keepsake",
            label=keepsake_cfg.label,
            owner=ghost.id,
            anchor_site=keepsake_cfg.anchor_site,
            fragile=keepsake_cfg.fragile,
            attrs={"moved": False},
        )
    )
    house = world.add(Entity(id="house", type="house", label="the house"))
    world.facts["child"] = child
    world.facts["caretaker"] = caretaker
    world.facts["ghost"] = ghost
    world.facts["haunt"] = haunt
    world.facts["response"] = response
    world.facts["delay"] = delay

    introduce(world, child, caretaker, haunt)
    discover(world, child, haunt, keepsake_cfg)

    world.para()
    tempt(world, child, motive, keepsake_cfg)
    warn(world, child, caretaker, motive, keepsake_cfg, haunt)
    defy(world, child, keepsake_cfg)

    world.para()
    haunting(world, child, ghost, haunt, keepsake_cfg)
    plea(world, ghost, keepsake_cfg)

    outcome = "reconciled" if can_reconcile(response, motive, delay, broken) else "haunted"

    if outcome == "haunted":
        world.para()
        hide_from_truth(world, child, caretaker, haunt)
        bad_ending(world, child, ghost, haunt)
    else:
        world.para()
        ask_for_help(world, child, caretaker)
        reconcile(world, child, caretaker, ghost, keepsake, response, haunt)
        world.para()
        farewell(world, child, ghost, keepsake_cfg)

    world.facts.update(
        outcome=outcome,
        child=child,
        caretaker=caretaker,
        ghost=ghost,
        keepsake=keepsake,
        ignited=False,
        haunted=outcome == "haunted",
        reconciled=outcome == "reconciled",
        severity=haunting_severity(motive, delay, broken),
        response_used=response,
    )
    return world


HAUNTS = {
    "attic": Haunt(
        id="attic",
        room="attic",
        detail="slanted ceilings and trunks with brass corners",
        hush="Above them, the attic boards ticked as if small feet were pacing there.",
        tags={"attic", "house"},
    ),
    "hallway": Haunt(
        id="hallway",
        room="upstairs hallway",
        detail="a row of narrow portraits and a runner carpet faded thin in the middle",
        hush="Each portrait seemed to watch the stairs with patient, dusty eyes.",
        tags={"hallway", "house"},
    ),
    "nursery": Haunt(
        id="nursery",
        room="old nursery",
        detail="moonlit wallpaper with peeling stars and a rocking chair by the window",
        hush="Now and then the rocking chair moved once, then went still again.",
        tags={"nursery", "house"},
    ),
}

KEEPSAKES = {
    "locket": Keepsake(
        id="locket",
        label="locket",
        phrase="a silver locket on a blue ribbon",
        use="close to someone's heart",
        fragile=False,
        anchor_site="attic",
        ghost_name="Clara",
        ghost_type="girl",
        memory="my mother singing me to sleep",
        final_image="the locket lay quiet in its ribbon nest",
        tags={"locket", "memory"},
    ),
    "music_box": Keepsake(
        id="music_box",
        label="music box",
        phrase="a tiny painted music box",
        use="until a soft tune floated out",
        fragile=True,
        anchor_site="nursery",
        ghost_name="Edith",
        ghost_type="girl",
        memory="my bedtime song",
        final_image="the music box rested shut, safe beside the window",
        tags={"music_box", "music"},
    ),
    "toy_boat": Keepsake(
        id="toy_boat",
        label="toy boat",
        phrase="a little wooden toy boat with a chipped sail",
        use="across the edge of a dusty trunk",
        fragile=True,
        anchor_site="hallway",
        ghost_name="Jonah",
        ghost_type="boy",
        memory="my brother's last birthday gift",
        final_image="the toy boat sat straight again, as if waiting for a quiet sea",
        tags={"toy_boat", "toy"},
    ),
}

MOTIVES = {
    "comfort": Motive(
        id="comfort",
        lead="The house felt lonely, and",
        action="decided to keep it by the bed for company",
        risk=1,
        tags={"curiosity"},
    ),
    "play": Motive(
        id="play",
        lead="The object seemed made for stories, and",
        action="carried it off to use in a midnight game",
        risk=2,
        tags={"play"},
    ),
    "show": Motive(
        id="show",
        lead="It seemed too strange to hide away, so",
        action="hurried downstairs to show it off",
        risk=1,
        tags={"show"},
    ),
}

RESPONSES = {
    "return_apology": Response(
        id="return_apology",
        sense=3,
        calms=3,
        repairs=False,
        text="{child} and {caretaker} carried the {keepsake} back to the {room}, set it in its old place, and spoke a careful apology into the dark.",
        success="{ghost} bent over the {keepsake}, and the sorrow in the room eased like a knot coming loose.",
        fail="{ghost} listened, but the hurt was still too deep to mend that night.",
        qa_text="They returned the keepsake and apologized where it belonged.",
        tags={"apology", "return"},
    ),
    "mend_return": Response(
        id="mend_return",
        sense=3,
        calms=4,
        repairs=True,
        text="{caretaker} fetched a small repair tin, and together {child} and {caretaker} mended the {keepsake} before carrying it back to the {room}.",
        success="{ghost} touched the mended {keepsake} with trembling fingers, and peace moved through the house from stair to stair.",
        fail="{ghost} saw the effort, but grief still clung to the room.",
        qa_text="They mended the keepsake and returned it with an apology.",
        tags={"repair", "apology", "return"},
    ),
    "sing_song": Response(
        id="sing_song",
        sense=2,
        calms=2,
        repairs=False,
        text="{child} and {caretaker} brought the {keepsake} back to the {room}, then sang softly so the frightened house would not feel alone.",
        success="{ghost} listened, lifted their face, and the dark corners seemed less sharp.",
        fail="{ghost} listened, but the hurt was still too deep to mend that night.",
        qa_text="They returned the keepsake and sang softly to comfort the ghost.",
        tags={"song", "return"},
    ),
    "joke": Response(
        id="joke",
        sense=1,
        calms=0,
        repairs=False,
        text="{child} tried to make jokes about ghosts and hide the {keepsake} under a pillow.",
        success="{ghost} laughed anyway.",
        fail="{ghost} only looked sadder.",
        qa_text="The child tried to joke instead of making things right.",
        tags={"joke"},
    ),
}


GIRL_NAMES = ["Mira", "Lucy", "Nora", "Ivy", "Tessa", "Mabel", "June", "Elsie"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Sam", "Jasper", "Milo", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for haunt_id, haunt in HAUNTS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            if not keepsake_belongs_in_haunt(keepsake, haunt):
                continue
            for motive_id in MOTIVES:
                combos.append((haunt_id, keepsake_id, motive_id))
    return combos

if __name__ == "__main__":
    main()
