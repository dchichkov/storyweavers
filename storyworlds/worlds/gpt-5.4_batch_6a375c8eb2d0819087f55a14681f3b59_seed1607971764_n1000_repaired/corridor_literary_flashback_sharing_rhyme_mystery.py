#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py
================================================================================

A standalone story world for a small child-facing mystery in a corridor after a
literary event. A child finds a rhyming clue, remembers an earlier moment, and
solves the mystery by sharing what they know.

Domain ingredients from the seed:
- required words: "corridor", "literary"
- narrative features: Flashback, Sharing, Rhyme
- style: Mystery

Run it
------
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py --item bookmark --helper librarian
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py --item lantern   # rejected
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py --all
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/corridor_literary_flashback_sharing_rhyme_mystery.py --verify
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
HELPFUL_MIN = 2


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
        female = {"girl", "mother", "woman", "librarian_f"}
        male = {"boy", "father", "man", "caretaker_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "librarian_f": "librarian",
            "caretaker_m": "caretaker",
            "teacher": "teacher",
        }
        return mapping.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Venue:
    id: str
    label: str
    literary_event: str
    corridor_detail: str
    owner_phrase: str
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
class LostItem:
    id: str
    label: str
    phrase: str
    owner: str
    rhyme_top: str
    rhyme_bottom: str
    clue_kind: str
    portable: bool = True
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    fits: set[str] = field(default_factory=set)
    reveal_line: str = ""
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
class Helper:
    id: str
    label: str
    type: str
    role_phrase: str
    helpful: int
    can_reach_high: bool = False
    knows_event: bool = False
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
class ShareMethod:
    id: str
    label: str
    works_for: set[str] = field(default_factory=set)
    line: str = ""
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
    def __init__(self, venue: Venue) -> None:
        self.venue = venue
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
        clone = World(self.venue)
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


def _r_memory_unlock(world: World) -> list[str]:
    child = world.get("child")
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return []
    sig = ("memory", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["memory"] += 1
    world.facts["flashback_ready"] = True
    return []


def _r_shared_focus(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    clue = world.get("clue")
    if child.memes["shared"] < THRESHOLD or clue.meters["found"] < THRESHOLD:
        return []
    sig = ("shared_focus", helper.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    helper.memes["attention"] += 1
    world.facts["paired_search"] = True
    return []


def _r_solution(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    item = world.get("item")
    if child.memes["shared"] < THRESHOLD:
        return []
    if helper.memes["attention"] < THRESHOLD:
        return []
    if child.memes["memory"] < THRESHOLD and not helper.attrs.get("knows_event", False):
        return []
    if helper.attrs.get("helpful", 0) < HELPFUL_MIN:
        return []
    sig = ("solved", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["recovered"] += 1
    child.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.facts["solved"] = True
    return []


CAUSAL_RULES = [
    Rule(name="memory_unlock", tag="meme", apply=_r_memory_unlock),
    Rule(name="shared_focus", tag="social", apply=_r_shared_focus),
    Rule(name="solution", tag="social", apply=_r_solution),
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


def place_fits(item: LostItem, hiding: HidingPlace) -> bool:
    return item.clue_kind in hiding.fits


def helpful_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.helpful >= HELPFUL_MIN]


def share_works(item: LostItem, share: ShareMethod) -> bool:
    return item.clue_kind in share.works_for


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue_id in VENUES:
        for item_id, item in LOST_ITEMS.items():
            for hiding_id, hiding in HIDING_PLACES.items():
                if not place_fits(item, hiding):
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper.helpful < HELPFUL_MIN:
                        continue
                    combos.append((venue_id, item_id, hiding_id, helper_id))
    return combos


def predict_solution(world: World, share: ShareMethod) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.memes["shared"] += 1
    sim.facts["share_method"] = share.id
    propagate(sim, narrate=False)
    item = sim.get("item")
    return {
        "solved": item.meters["recovered"] >= THRESHOLD,
        "memory": child.memes["memory"] >= THRESHOLD,
    }


def discover_clue(world: World, child: Entity, clue: Entity, venue: Venue, hiding: HidingPlace) -> None:
    clue.meters["found"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"After {venue.literary_event}, {child.id} walked slowly down the {venue.label}. "
        f"{venue.corridor_detail} Near {hiding.phrase}, {child.pronoun()} spotted a tiny clue."
    )
    world.say(
        f"It was {clue.phrase}, and across it ran a neat little rhyme: "
        f'"{clue.attrs["rhyme_top"]}"'
    )
    propagate(world, narrate=False)


def feel_mystery(world: World, child: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} looked left and right. The corridor felt hush-hush and mysterious, "
        f"as if the floor itself were keeping a secret."
    )


def flashback(world: World, child: Entity, item: LostItem, hiding: HidingPlace) -> None:
    if child.memes["memory"] < THRESHOLD:
        return
    child.memes["clarity"] += 1
    world.say(
        f"Then a flashback fluttered into {child.pronoun('possessive')} mind. "
        f"Earlier that afternoon, during the literary gathering, {child.pronoun()} had seen "
        f"{item.owner} pause by {hiding.phrase} and softly finish the rhyme: "
        f'"{item.rhyme_bottom}"'
    )


def worry_alone(world: World, child: Entity, item: LostItem) -> None:
    child.memes["worry"] += 1
    world.say(
        f"{child.id} could have tucked the clue away and kept the mystery alone, "
        f"but that made {child.pronoun('object')} feel smaller instead of braver."
    )
    world.say(
        f"If {child.pronoun()} wanted to help {item.owner}, {child.pronoun()} needed another pair of eyes."
    )


def choose_helper(world: World, child: Entity, helper_ent: Entity, helper: Helper, share: ShareMethod) -> None:
    child.memes["trust"] += 1
    world.say(
        f"{child.id} hurried to {helper.label}, {helper.role_phrase}. "
        f'{share.line.format(child=child.id, helper=helper.label)}'
    )
    child.memes["shared"] += 1
    world.facts["shared_with"] = helper.id
    world.facts["share_method"] = share.id
    propagate(world, narrate=False)


def search_together(world: World, child: Entity, helper: Helper, helper_ent: Entity,
                    item: LostItem, hiding: HidingPlace) -> None:
    helper_ent.memes["care"] += 1
    world.say(
        f"{helper.label.capitalize()} listened all the way through. Instead of hushing {child.id}, "
        f"{helper_ent.pronoun()} nodded and said the rhyme with {child.pronoun('object')}, "
        f"one line each, until the clue sounded like a map."
    )
    if helper.can_reach_high:
        action = f"reached above {hiding.phrase}"
    else:
        action = f"looked carefully behind {hiding.phrase}"
    world.say(
        f"Together they went back down the corridor. {helper.label.capitalize()} {action}, "
        f"and {child.id} pointed to the exact spot from the flashback."
    )
    propagate(world, narrate=False)


def recover_item(world: World, child: Entity, helper: Helper, helper_ent: Entity,
                 item_ent: Entity, item: LostItem, hiding: HidingPlace, venue: Venue) -> None:
    if item_ent.meters["recovered"] < THRESHOLD:
        raise StoryError("The mystery did not resolve; this parameter set is not storyworthy.")
    item_ent.meters["hidden"] = 0.0
    world.say(
        f"There it was: {item.phrase}, tucked {hiding.reveal_line}. "
        f"The missing thing had been safe all along, only out of sight."
    )
    world.say(
        f"{item.owner} came hurrying back with a worried face, then smiled so wide that the whole "
        f"{venue.label} seemed brighter. {helper.label.capitalize()} handed it over, and {child.id} "
        f"felt the mysterious flutter in {child.pronoun('possessive')} chest turn into warm relief."
    )


def closing(world: World, child: Entity, item: LostItem) -> None:
    child.memes["joy"] += 1
    world.say(
        f'Before leaving, {child.id} read the little rhyme again: "{item.rhyme_top} / {item.rhyme_bottom}." '
        f"This time it did not sound spooky at all. It sounded like a door opening because someone had chosen to share."
    )


def tell(venue: Venue, item: LostItem, hiding: HidingPlace, helper: Helper, share: ShareMethod,
         child_name: str = "Mina", child_type: str = "girl", parent_type: str = "teacher") -> World:
    world = World(venue=venue)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        traits=["observant", "gentle"],
        attrs={},
    ))
    helper_ent = world.add(Entity(
        id="helper",
        kind="character",
        type=helper.type,
        label=helper.label,
        role="helper",
        attrs={
            "helpful": helper.helpful,
            "knows_event": helper.knows_event,
            "can_reach_high": helper.can_reach_high,
        },
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="lost_item",
        label=item.label,
        phrase=item.phrase,
        role="missing",
        attrs={"owner": item.owner},
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="paper",
        label="clue slip",
        phrase=f"a clue slip that mentioned the {item.label}",
        attrs={"rhyme_top": item.rhyme_top, "rhyme_bottom": item.rhyme_bottom},
    ))
    corridor = world.add(Entity(
        id="corridor",
        kind="thing",
        type="place",
        label=venue.label,
        phrase=venue.label,
    ))

    item_ent.meters["hidden"] = 1.0
    item_ent.attrs["place"] = hiding.id
    item_ent.attrs["clue_kind"] = item.clue_kind
    clue.meters["found"] = 0.0
    child.memes["memory"] = 0.0
    child.memes["shared"] = 0.0
    helper_ent.memes["attention"] = 0.0
    world.facts["solved"] = False
    world.facts["flashback_ready"] = False
    world.facts["paired_search"] = False

    discover_clue(world, child, clue, venue, hiding)
    feel_mystery(world, child)
    world.para()
    flashback(world, child, item, hiding)
    worry_alone(world, child, item)
    choose_helper(world, child, helper_ent, helper, share)
    world.para()
    search_together(world, child, helper, helper_ent, item, hiding)
    recover_item(world, child, helper, helper_ent, item_ent, item, hiding, venue)
    closing(world, child, item)

    world.facts.update(
        venue=venue,
        item_cfg=item,
        hiding_cfg=hiding,
        helper_cfg=helper,
        share_cfg=share,
        child=child,
        helper=helper_ent,
        item=item_ent,
        clue=clue,
        shared=child.memes["shared"] >= THRESHOLD,
        recovered=item_ent.meters["recovered"] >= THRESHOLD,
        flashback=child.memes["memory"] >= THRESHOLD,
    )
    return world


VENUES = {
    "school": Venue(
        id="school",
        label="school corridor",
        literary_event="the afternoon literary fair",
        corridor_detail="Paper stars from the reading hour still hung above the doors.",
        owner_phrase="the visiting poet",
        tags={"corridor", "literary", "school"},
    ),
    "library": Venue(
        id="library",
        label="library corridor",
        literary_event="the little literary club",
        corridor_detail="Soft lamp light touched the framed book covers on the wall.",
        owner_phrase="the librarian",
        tags={"corridor", "literary", "library"},
    ),
    "museum": Venue(
        id="museum",
        label="museum corridor",
        literary_event="the museum's literary treasure walk",
        corridor_detail="Glass cases threw quiet squares of light across the floor.",
        owner_phrase="the storyteller",
        tags={"corridor", "literary", "museum"},
    ),
}

LOST_ITEMS = {
    "bookmark": LostItem(
        id="bookmark",
        label="bookmark",
        phrase="a silver bookmark shaped like a moon",
        owner="the visiting poet",
        rhyme_top="Moon by the door, do not ignore",
        rhyme_bottom="Look by the stand where umbrellas snore",
        clue_kind="slim",
        tags={"bookmark", "rhyme"},
    ),
    "notebook": LostItem(
        id="notebook",
        label="notebook",
        phrase="a red notebook with a cloth band",
        owner="the storyteller",
        rhyme_top="Red little book with a ribbon bright",
        rhyme_bottom="Rest where the cart hides out of sight",
        clue_kind="medium",
        tags={"notebook", "rhyme"},
    ),
    "poem_card": LostItem(
        id="poem_card",
        label="poem card",
        phrase="a cream poem card with gold letters",
        owner="the librarian",
        rhyme_top="Golden words and paper light",
        rhyme_bottom="Wait on the sill beside the night",
        clue_kind="flat",
        tags={"poem", "rhyme"},
    ),
    "lantern": LostItem(
        id="lantern",
        label="lantern",
        phrase="a brass lantern",
        owner="the caretaker",
        rhyme_top="Lantern bright, lantern tall",
        rhyme_bottom="Hide by the echoing hall",
        clue_kind="bulky",
        tags={"decoy"},
    ),
}

HIDING_PLACES = {
    "umbrella_stand": HidingPlace(
        id="umbrella_stand",
        label="umbrella stand",
        phrase="the umbrella stand",
        fits={"slim"},
        reveal_line="between two folded umbrellas",
        tags={"umbrella_stand"},
    ),
    "return_cart": HidingPlace(
        id="return_cart",
        label="book return cart",
        phrase="the book return cart",
        fits={"medium"},
        reveal_line="under the bottom shelf of the cart",
        tags={"cart"},
    ),
    "windowsill": HidingPlace(
        id="windowsill",
        label="windowsill",
        phrase="the long windowsill",
        fits={"flat"},
        reveal_line="under the curtain edge on the sill",
        tags={"windowsill"},
    ),
}

HELPERS = {
    "librarian": Helper(
        id="librarian",
        label="the librarian",
        type="librarian_f",
        role_phrase="who always knew where books liked to wander",
        helpful=3,
        can_reach_high=True,
        knows_event=True,
        tags={"librarian"},
    ),
    "older_friend": Helper(
        id="older_friend",
        label="an older friend named Theo",
        type="boy",
        role_phrase="who had stayed behind to stack chairs",
        helpful=2,
        can_reach_high=False,
        knows_event=False,
        tags={"friend"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="the caretaker",
        type="caretaker_m",
        role_phrase="who carried a ring of softly chiming keys",
        helpful=2,
        can_reach_high=True,
        knows_event=False,
        tags={"caretaker"},
    ),
    "sleepy_visitor": Helper(
        id="sleepy_visitor",
        label="a sleepy visitor",
        type="man",
        role_phrase="who was already buttoning a coat and hurrying home",
        helpful=1,
        can_reach_high=False,
        knows_event=False,
        tags={"visitor"},
    ),
}

SHARE_METHODS = {
    "show_slip": ShareMethod(
        id="show_slip",
        label="show the slip",
        works_for={"slim", "medium", "flat"},
        line='"I found this clue," said {child}, holding the little paper up for {helper} to see.',
        qa_text="showed the clue slip",
        tags={"sharing"},
    ),
    "say_rhyme": ShareMethod(
        id="say_rhyme",
        label="say the rhyme aloud",
        works_for={"slim", "medium", "flat"},
        line='"Listen," said {child}, and then {child} whispered the rhyme aloud to {helper}.',
        qa_text="recited the rhyme aloud",
        tags={"sharing", "rhyme"},
    ),
    "trace_letters": ShareMethod(
        id="trace_letters",
        label="trace the letters with a finger",
        works_for={"flat"},
        line='{child} traced the gold letters with a careful finger and showed them to {helper}.',
        qa_text="traced the clue letters and shared them",
        tags={"sharing", "letters"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Esme", "Tara", "Lucy", "Ivy"]
BOY_NAMES = ["Theo", "Ben", "Milo", "Finn", "Leo", "Owen", "Eli", "Max"]
TRAITS = ["observant", "careful", "quiet", "curious", "thoughtful"]


@dataclass
class StoryParams:
    venue: str
    item: str
    hiding: str
    helper: str
    share: str
    child_name: str
    child_type: str
    parent_type: str = "teacher"
    trait: str = "observant"
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
    "bookmark": [
        (
            "What is a bookmark?",
            "A bookmark is a small strip or card you keep in a book to remember your place. It helps you come back to the right page later.",
        )
    ],
    "notebook": [
        (
            "What is a notebook for?",
            "A notebook is for writing ideas, lists, or stories on paper pages. People use one when they want to save words for later.",
        )
    ],
    "poem": [
        (
            "What is a poem?",
            "A poem is a short piece of writing that plays with sound, feeling, and meaning. Some poems use rhythm or rhyme to make the words memorable.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching ending sounds, like 'light' and 'night.' Rhymes can help people remember lines more easily.",
        )
    ],
    "sharing": [
        (
            "Why is sharing information helpful in a mystery?",
            "Sharing lets more than one person think about the clue. A helper may notice something you missed or know something important.",
        )
    ],
    "librarian": [
        (
            "What does a librarian do?",
            "A librarian helps people find books and take care of them. Librarians also know a lot about where reading things belong.",
        )
    ],
    "corridor": [
        (
            "What is a corridor?",
            "A corridor is a long hallway that connects rooms or doors. People walk through it to get from one place to another.",
        )
    ],
    "literary": [
        (
            "What does literary mean?",
            "Literary means connected to books, stories, poems, or reading. A literary event is something about words and writing.",
        )
    ],
}

KNOWLEDGE_ORDER = ["corridor", "literary", "bookmark", "notebook", "poem", "rhyme", "sharing", "librarian"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    venue = f["venue"]
    item = f["item_cfg"]
    helper = f["helper_cfg"]
    share = f["share_cfg"]
    return [
        'Write a gentle mystery story for a 3-to-5-year-old that uses the words "corridor" and "literary."',
        f"Tell a child-friendly mystery where {child.id} finds a rhyming clue in a {venue.label}, has a flashback, and solves the problem by sharing it with {helper.label}.",
        f"Write a short story about a lost {item.label}, a corridor clue, and a child who {share.label} so the mystery can be solved.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper_ent = f["helper"]
    helper_cfg = f["helper_cfg"]
    venue = f["venue"]
    item = f["item_cfg"]
    hiding = f["hiding_cfg"]
    share = f["share_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a careful child in a {venue.label}, and {helper_cfg.label}, who helped solve the mystery. Together they worked out where the missing {item.label} had gone.",
        ),
        (
            f"What made the corridor feel mysterious?",
            f"{child.id} found a tiny clue with a rhyme on it, and the quiet corridor seemed full of secrets. The rhyme made the place feel like a puzzle instead of an ordinary hallway.",
        ),
        (
            "What was the flashback about?",
            f"{child.id} remembered seeing {item.owner} earlier near {hiding.phrase}. That memory mattered because it turned the rhyme from a strange note into a real clue.",
        ),
        (
            f"How did {child.id} help solve the mystery?",
            f"{child.id} {share.qa_text} to {helper_cfg.label} instead of keeping the clue alone. Sharing brought in another pair of eyes, and together they searched the right place from the flashback.",
        ),
    ]
    if f.get("recovered"):
        qa.append(
            (
                f"Where was the missing {item.label}?",
                f"It was hidden by {hiding.phrase}. It had not been stolen at all; it was simply tucked out of sight until {child.id} and {helper_cfg.label} looked carefully.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"The mystery ended warmly, with the missing {item.label} returned to {item.owner}. The last image is {child.id} reading the rhyme again, no longer frightened because the secret had been solved by sharing.",
            )
        )
    if helper_ent.attrs.get("knows_event", False):
        qa.append(
            (
                f"Why was {helper_cfg.label} a good person to tell?",
                f"{helper_cfg.label.capitalize()} already knew the literary event and listened closely. That made it easier to connect {child.id}'s clue to the right hiding place.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"corridor", "literary", "rhyme", "sharing"}
    item = f["item_cfg"]
    helper = f["helper_cfg"]
    if item.id == "bookmark":
        tags.add("bookmark")
    if item.id == "notebook":
        tags.add("notebook")
    if item.id == "poem_card":
        tags.add("poem")
    if helper.id == "librarian":
        tags.add("librarian")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        venue="school",
        item="bookmark",
        hiding="umbrella_stand",
        helper="librarian",
        share="say_rhyme",
        child_name="Mina",
        child_type="girl",
        parent_type="teacher",
        trait="observant",
    ),
    StoryParams(
        venue="library",
        item="poem_card",
        hiding="windowsill",
        helper="older_friend",
        share="trace_letters",
        child_name="Theo",
        child_type="boy",
        parent_type="teacher",
        trait="careful",
    ),
    StoryParams(
        venue="museum",
        item="notebook",
        hiding="return_cart",
        helper="caretaker",
        share="show_slip",
        child_name="Lila",
        child_type="girl",
        parent_type="teacher",
        trait="thoughtful",
    ),
]


def explain_item_rejection(item: LostItem) -> str:
    if item.clue_kind == "bulky":
        return (
            f"(No story: {item.phrase} is too bulky for this gentle clue mystery. "
            "This world only models slim paper-like lost things that can plausibly be hidden by a rhyming corridor clue.)"
        )
    return "(No story: this item does not fit the clue mystery.)"


def explain_place_rejection(item: LostItem, hiding: HidingPlace) -> str:
    return (
        f"(No story: {item.phrase} does not plausibly fit at {hiding.phrase}. "
        "Pick a hiding place that matches the size and shape of the lost paper item.)"
    )


def explain_helper_rejection(helper: Helper) -> str:
    return (
        f"(No story: {helper.label} is too distracted to help solve the mystery here "
        f"(helpful={helper.helpful} < {HELPFUL_MIN}). The story needs a helper who can really join the search.)"
    )


def explain_share_rejection(item: LostItem, share: ShareMethod) -> str:
    return (
        f"(No story: the sharing method '{share.id}' does not fit a {item.label}. "
        "This clue has to be shared in a way that actually passes the rhyme or letters along.)"
    )


def outcome_of(params: StoryParams) -> str:
    helper = HELPERS[params.helper]
    return "solved" if helper.helpful >= HELPFUL_MIN else "stuck"


ASP_RULES = r"""
% --- gate ---------------------------------------------------------------
paper_item(I) :- item(I), clue_kind(I, K), K != bulky.
fits(I,H) :- clue_kind(I,K), place_fits(H,K).
good_helper(H) :- helper(H), helpful(H,N), helpful_min(M), N >= M.
share_ok(S,I) :- share(S), clue_kind(I,K), works_for(S,K).

valid(V,I,H,Hp,S) :- venue(V), paper_item(I), fits(I,H), good_helper(Hp), share_ok(S,I).

% --- outcome model ------------------------------------------------------
flashback.
shared :- chosen_share(S), share_ok(S, I), chosen_item(I).
attentive :- chosen_helper(H), good_helper(H).
solved :- flashback, shared, attentive.
outcome(solved) :- solved.
#show valid/5.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for venue_id in VENUES:
        lines.append(asp.fact("venue", venue_id))
    for item_id, item in LOST_ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("clue_kind", item_id, item.clue_kind))
    for hid_id, hiding in HIDING_PLACES.items():
        lines.append(asp.fact("hiding_place", hid_id))
        for kind in sorted(hiding.fits):
            lines.append(asp.fact("place_fits", hid_id, kind))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        lines.append(asp.fact("helpful", helper_id, helper.helpful))
    for share_id, share in SHARE_METHODS.items():
        lines.append(asp.fact("share", share_id))
        for kind in sorted(share.works_for):
            lines.append(asp.fact("works_for", share_id, kind))
    lines.append(asp.fact("helpful_min", HELPFUL_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_item", params.item),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_share", params.share),
            "#show outcome/1.",
        ]
    )
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = {
        (venue, item, hiding, helper, share)
        for venue, item, hiding, helper in valid_combos()
        for share, share_cfg in SHARE_METHODS.items()
        if share_works(LOST_ITEMS[item], share_cfg)
    }
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid combinations ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "corridor" not in sample.story or "literary" not in sample.story:
            raise StoryError("smoke test story missing required surface words")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a corridor mystery with a rhyme, a flashback, and sharing."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--item", choices=LOST_ITEMS)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--share", choices=SHARE_METHODS)
    ap.add_argument("--parent", choices=["teacher"])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item:
        item = LOST_ITEMS[args.item]
        if item.clue_kind == "bulky":
            raise StoryError(explain_item_rejection(item))
    if args.item and args.hiding:
        item = LOST_ITEMS[args.item]
        hiding = HIDING_PLACES[args.hiding]
        if not place_fits(item, hiding):
            raise StoryError(explain_place_rejection(item, hiding))
    if args.helper:
        helper = HELPERS[args.helper]
        if helper.helpful < HELPFUL_MIN:
            raise StoryError(explain_helper_rejection(helper))
    if args.item and args.share:
        item = LOST_ITEMS[args.item]
        share = SHARE_METHODS[args.share]
        if not share_works(item, share):
            raise StoryError(explain_share_rejection(item, share))

    base = [
        combo
        for combo in valid_combos()
        if (args.venue is None or combo[0] == args.venue)
        and (args.item is None or combo[1] == args.item)
        and (args.hiding is None or combo[2] == args.hiding)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not base:
        raise StoryError("(No valid combination matches the given options.)")

    venue_id, item_id, hiding_id, helper_id = rng.choice(sorted(base))
    share_options = [
        sid
        for sid, share in SHARE_METHODS.items()
        if share_works(LOST_ITEMS[item_id], share)
        and (args.share is None or sid == args.share)
    ]
    if not share_options:
        raise StoryError("(No valid sharing method matches the given options.)")

    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    parent_type = args.parent or "teacher"

    return StoryParams(
        venue=venue_id,
        item=item_id,
        hiding=hiding_id,
        helper=helper_id,
        share=rng.choice(sorted(share_options)),
        child_name=child_name,
        child_type=child_type,
        parent_type=parent_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        venue = VENUES[params.venue]
        item = LOST_ITEMS[params.item]
        hiding = HIDING_PLACES[params.hiding]
        helper = HELPERS[params.helper]
        share = SHARE_METHODS[params.share]
    except KeyError as err:
        raise StoryError(f"Unknown parameter choice: {err}") from err

    if item.clue_kind == "bulky":
        raise StoryError(explain_item_rejection(item))
    if not place_fits(item, hiding):
        raise StoryError(explain_place_rejection(item, hiding))
    if helper.helpful < HELPFUL_MIN:
        raise StoryError(explain_helper_rejection(helper))
    if not share_works(item, share):
        raise StoryError(explain_share_rejection(item, share))

    world = tell(
        venue=venue,
        item=item,
        hiding=hiding,
        helper=helper,
        share=share,
        child_name=params.child_name,
        child_type=params.child_type,
        parent_type=params.parent_type,
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
        print(asp_program("#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, item, hiding, helper, share) combos:\n")
        for venue, item, hiding, helper, share in combos:
            print(f"  {venue:8} {item:10} {hiding:15} {helper:12} {share}")
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
            header = (
                f"### {p.child_name}: {p.item} in {p.venue} "
                f"(hidden at {p.hiding}, helper {p.helper}, share {p.share})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
