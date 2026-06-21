#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py
==================================================================

A standalone storyworld for a small child-facing mystery tale: an important
object goes missing before a special event, whispers begin to circulate, and a
brave child makes a bid to solve the puzzle by following a sensible clue.

The world refuses weak mystery logic. A valid story needs:
- a setting that actually contains the chosen hideout,
- a cause that could plausibly move the missing object,
- the matching clue for that cause,
- and a hideout that the cause would plausibly use.

The turn is state-driven: fear rises when rumors circulate, certainty rises
when the real clue is noticed, and the ending depends on whether the hero's
bravery is enough for the hideout's darkness. When it is not, the child still
acts bravely by asking a grown-up to come along.

Words required by the seed are used naturally in the prose:
- exodus
- circulate
- bid

Run it
------
    python storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py
    python storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py --setting theater --missing bell --cause magpie --clue feather --hideout rafters
    python storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py --cause wind --missing bell
    python storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py --all
    python storyworlds/worlds/gpt-5.4/exodus_circulate_bid_bravery_mystery.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


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
        female = {"girl", "mother", "librarian", "curator", "caretaker_woman", "woman"}
        male = {"boy", "father", "caretaker", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "librarian": "librarian",
            "curator": "curator",
            "caretaker": "caretaker",
            "caretaker_woman": "caretaker",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    event: str
    adult_type: str
    mood: str
    hideouts: set[str] = field(default_factory=set)
    opening: str = ""
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
class MissingThing:
    id: str
    label: str
    phrase: str
    article: str
    tags: set[str] = field(default_factory=set)

    @property
    def the(self) -> str:
        return f"the {self.label}"
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
class Cause:
    id: str
    label: str
    verb_past: str
    clue: str
    hideouts: set[str] = field(default_factory=set)
    carries: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
    reveal: str = ""
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
class Clue:
    id: str
    label: str
    phrase: str
    detail: str
    cause: str
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
class Hideout:
    id: str
    label: str
    phrase: str
    darkness: int
    exodus: str
    finding: str
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
        self.history: list[str] = []
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

    def note(self, fact: str) -> None:
        self.history.append(fact)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.history = list(self.history)
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


def _r_rumor_spreads(world: World) -> list[str]:
    room = world.get("room")
    if room.memes["rumor"] < THRESHOLD:
        return []
    sig = ("rumor",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend"):
        world.get(eid).memes["fear"] += 1
    room.meters["mystery"] += 1
    return []


def _r_clue_gives_certainty(world: World) -> list[str]:
    clue = world.get("clue")
    if clue.meters["noticed"] < THRESHOLD:
        return []
    sig = ("clue", clue.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("hero").memes["certainty"] += 1
    world.get("friend").memes["hope"] += 1
    return []


def _r_found_brings_relief(world: World) -> list[str]:
    item = world.get("missing")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    for eid in ("hero", "friend", "adult"):
        world.get(eid).memes["relief"] += 1
    world.get("room").memes["rumor"] = 0.0
    world.get("room").meters["mystery"] = 0.0
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="rumor_spreads", tag="social", apply=_r_rumor_spreads),
    Rule(name="clue_gives_certainty", tag="social", apply=_r_clue_gives_certainty),
    Rule(name="found_brings_relief", tag="social", apply=_r_found_brings_relief),
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
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
        before = len(world.fired)
        # Rules above only mutate state; the fired set acts as the change signal.
        if len(world.fired) != before:
            changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_carry(cause: Cause, thing: MissingThing) -> bool:
    return bool(cause.carries & thing.tags)


def clue_matches(cause: Cause, clue: Clue) -> bool:
    return cause.clue == clue.id and clue.cause == cause.id


def hideout_allowed(setting: Setting, cause: Cause, hideout: Hideout) -> bool:
    return hideout.id in setting.hideouts and hideout.id in cause.hideouts


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for thing_id, thing in MISSING.items():
            for cause_id, cause in CAUSES.items():
                for clue_id, clue in CLUES.items():
                    for hideout_id, hideout in HIDEOUTS.items():
                        if can_carry(cause, thing) and clue_matches(cause, clue) and hideout_allowed(setting, cause, hideout):
                            combos.append((setting_id, thing_id, cause_id, clue_id, hideout_id))
    return sorted(combos)


def outcome_of(params: "StoryParams") -> str:
    hideout = HIDEOUTS[params.hideout]
    return "solo" if params.bravery >= hideout.darkness else "adult_helped"


def explain_rejection(setting: Setting, thing: MissingThing, cause: Cause, clue: Clue, hideout: Hideout) -> str:
    if not can_carry(cause, thing):
        return (
            f"(No story: {cause.label} would not plausibly carry {thing.the}. "
            f"Pick an object that fits what {cause.label} would take.)"
        )
    if not clue_matches(cause, clue):
        return (
            f"(No story: {clue.label} is not the right clue for {cause.label}. "
            f"A fair mystery needs the clue to match the true cause.)"
        )
    if hideout.id not in setting.hideouts:
        return (
            f"(No story: {hideout.phrase} is not part of {setting.place}. "
            f"Choose a hideout that exists in that setting.)"
        )
    if hideout.id not in cause.hideouts:
        return (
            f"(No story: {cause.label} would not plausibly stash things in {hideout.phrase}. "
            f"Choose a hideout that fits the cause.)"
        )
    return "(No story: the requested combination is not reasonable.)"


def predict_can_search_alone(world: World, bravery: int, hideout: Hideout) -> bool:
    sim = world.copy()
    sim.get("hero").memes["bravery"] = float(bravery)
    sim.get("hideout").meters["darkness"] = float(hideout.darkness)
    return sim.get("hero").memes["bravery"] >= sim.get("hideout").meters["darkness"]


def open_scene(world: World, hero: Entity, friend: Entity, adult: Entity, thing: MissingThing) -> None:
    world.say(
        f"{hero.id} and {friend.id} arrived at {world.setting.place}, where {world.setting.opening}."
    )
    world.say(
        f"That evening was meant for {world.setting.event}, and everyone needed {thing.the} before the doors opened."
    )
    world.say(
        f"{adult.label_word.capitalize()} had just set out the last chair when somebody noticed that {thing.the} was gone."
    )
    world.note("missing discovered")


def rumors_circulate(world: World, hero: Entity, friend: Entity, thing: MissingThing) -> None:
    room = world.get("room")
    room.memes["rumor"] += 1
    propagate(world, narrate=False)
    world.say(
        f"A small hush moved through the room. Then whispers began to circulate: maybe a ghost had slipped through the shadows and taken {thing.the}."
    )
    if hero.memes["fear"] >= THRESHOLD or friend.memes["fear"] >= THRESHOLD:
        world.say(
            f"{friend.id} edged closer to {hero.id}, and even the lamps seemed to hold their breath."
        )
    world.note("rumor circulated")


def brave_bid(world: World, hero: Entity, friend: Entity, adult: Entity, thing: MissingThing) -> None:
    world.say(
        f'{hero.id} looked at the dark corners, swallowed once, and made a brave bid to solve the mystery before {world.setting.event} had to be canceled.'
    )
    world.say(
        f'"I can look for clues," {hero.pronoun()} said. "{thing.the.capitalize()} has to be somewhere."'
    )
    friend.memes["trust"] += 1
    world.note("hero volunteered")


def notice_clue(world: World, hero: Entity, friend: Entity, clue_cfg: Clue, cause: Cause, hideout: Hideout) -> None:
    clue = world.get("clue")
    clue.meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near the floor, {hero.id} spotted {clue_cfg.phrase}. {clue_cfg.detail}"
    )
    if world.get("hero").memes["certainty"] >= THRESHOLD:
        world.say(
            f'"That is not a ghost clue," {hero.id} whispered. "It looks like something real went toward {hideout.phrase}."'
        )
    world.facts["trail_to"] = hideout.id
    world.note(f"clue noticed: {clue_cfg.id}")
    world.note(f"cause inferred: {cause.id}")


def choose_search(world: World, hero: Entity, friend: Entity, adult: Entity, bravery: int, hideout: Hideout) -> str:
    hero.memes["bravery"] = float(bravery)
    alone = predict_can_search_alone(world, bravery, hideout)
    if alone:
        world.say(
            f"{hero.id} held the little battery lantern up high and took the first careful steps toward {hideout.phrase}."
        )
        world.say(
            f"{friend.id} came right behind, quieter now, because the clue felt stronger than the rumor."
        )
        world.note("searched without adult")
        return "solo"
    world.say(
        f"{hero.id} started toward {hideout.phrase}, then stopped at the deepest patch of shadow."
    )
    world.say(
        f'"I still want to help," {hero.pronoun()} said, "but I want {adult.label_word} to come too."'
    )
    adult.memes["support"] += 1
    friend.memes["trust"] += 1
    world.note("asked adult for help")
    return "adult_helped"


def enter_hideout(world: World, hero: Entity, friend: Entity, adult: Entity, outcome: str, hideout: Hideout) -> None:
    world.para()
    if outcome == "solo":
        world.say(
            f"The lantern beam slid over {hideout.label}, and {hero.id} reached out with steady fingers."
        )
    else:
        world.say(
            f"Together, {adult.label_word}, {hero.id}, and {friend.id} moved toward {hideout.phrase} while the room stayed quiet behind them."
        )
    world.say(
        f"When they opened it, there was {hideout.exodus}."
    )
    world.get("hideout").meters["opened"] += 1
    world.note("hideout opened")


def reveal_solution(world: World, hero: Entity, friend: Entity, adult: Entity, thing: MissingThing, cause: Cause, hideout: Hideout) -> None:
    item = world.get("missing")
    item.meters["found"] += 1
    item.meters["hidden"] = 0.0
    world.get("cause").meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hideout.finding} There was {thing.the}, and beside it was {cause.reveal}"
    )
    world.say(
        f"It was not a ghost at all. {cause.label.capitalize()} had {cause.verb_past} {thing.the} away for perfectly ordinary reasons."
    )
    world.note("item found")
    world.note("cause revealed")


def explain_and_close(world: World, hero: Entity, friend: Entity, adult: Entity, thing: MissingThing, outcome: str) -> None:
    world.para()
    if outcome == "solo":
        world.say(
            f'{adult.label_word.capitalize()} laughed softly with relief. "So that was the whole mystery," {adult.pronoun()} said.'
        )
        world.say(
            f'"You were very brave," {adult.pronoun()} told {hero.id}. "You looked for a true clue instead of believing the whispers."'
        )
    else:
        world.say(
            f'{adult.label_word.capitalize()} squeezed {hero.id}\'s shoulder. "Asking for help was brave too," {adult.pronoun()} said.'
        )
        world.say(
            f'"You did not let the mystery grow bigger than the truth," {adult.pronoun()} added.'
        )
    world.say(
        f"Soon {thing.the} was back in its proper place, the ghost story stopped circulating, and {world.setting.event} began right on time."
    )
    world.say(
        f"The room no longer felt haunted. It felt warm, bright, and full of people who had learned to trust brave thinking."
    )
    world.note("ending resolved")


def tell(
    setting: Setting,
    thing: MissingThing,
    cause: Cause,
    clue_cfg: Clue,
    hideout: Hideout,
    hero_name: str = "Nora",
    hero_gender: str = "girl",
    friend_name: str = "Eli",
    friend_gender: str = "boy",
    adult_type: str = "librarian",
    bravery: int = 2,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, phrase=hero_name, role="hero"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the adult", phrase=adult_type, role="adult"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=setting.place))
    missing = world.add(Entity(id="missing", kind="thing", type="item", label=thing.label, phrase=thing.phrase))
    clue = world.add(Entity(id="clue", kind="thing", type="clue", label=clue_cfg.label, phrase=clue_cfg.phrase))
    hide = world.add(Entity(id="hideout", kind="thing", type="hideout", label=hideout.label, phrase=hideout.phrase))
    mover = world.add(Entity(id="cause", kind="thing", type=cause.id, label=cause.label, phrase=cause.label))

    room.memes["rumor"] = 0.0
    room.meters["mystery"] = 0.0
    missing.meters["hidden"] = 1.0
    missing.meters["found"] = 0.0
    clue.meters["noticed"] = 0.0
    hide.meters["darkness"] = float(hideout.darkness)
    hide.meters["opened"] = 0.0
    mover.meters["seen"] = 0.0
    hero.memes["bravery"] = float(bravery)
    hero.memes["fear"] = 0.0
    hero.memes["certainty"] = 0.0
    friend.memes["fear"] = 0.0
    friend.memes["hope"] = 0.0
    friend.memes["trust"] = 0.0
    adult.memes["support"] = 0.0

    world.facts.update(
        setting=setting,
        missing_cfg=thing,
        cause_cfg=cause,
        clue_cfg=clue_cfg,
        hideout_cfg=hideout,
        hero_name=hero_name,
        friend_name=friend_name,
        adult_type=adult_type,
        bravery=bravery,
    )

    open_scene(world, hero, friend, adult, thing)
    rumors_circulate(world, hero, friend, thing)

    world.para()
    brave_bid(world, hero, friend, adult, thing)
    notice_clue(world, hero, friend, clue_cfg, cause, hideout)
    outcome = choose_search(world, hero, friend, adult, bravery, hideout)

    enter_hideout(world, hero, friend, adult, outcome, hideout)
    reveal_solution(world, hero, friend, adult, thing, cause, hideout)
    explain_and_close(world, hero, friend, adult, thing, outcome)

    world.facts.update(
        hero=hero,
        friend=friend,
        adult=adult,
        room=room,
        missing=missing,
        clue=clue,
        hideout=hide,
        cause=mover,
        outcome=outcome,
        solved=missing.meters["found"] >= THRESHOLD,
        searched_alone=outcome == "solo",
    )
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the old library",
        event="the evening story circle",
        adult_type="librarian",
        mood="hushed and rustly",
        hideouts={"book_cart", "window_ledge"},
        opening="rain tapped at the high windows and the stacks made long, patient shadows",
    ),
    "theater": Setting(
        id="theater",
        place="the little town theater",
        event="the lantern play",
        adult_type="caretaker",
        mood="creaky and velvet-dark",
        hideouts={"prop_trunk", "rafters"},
        opening="the red curtains breathed softly whenever the draft slipped through",
    ),
    "museum": Setting(
        id="museum",
        place="the moon-room museum",
        event="the moonlight tour",
        adult_type="curator",
        mood="glassy and whispery",
        hideouts={"display_curtain", "window_ledge"},
        opening="silver light from the skylight made every case look secret",
    ),
}

MISSING = {
    "bell": MissingThing(
        id="bell",
        label="bell",
        phrase="a little silver bell",
        article="a",
        tags={"shiny", "jingle"},
    ),
    "ribbon": MissingThing(
        id="ribbon",
        label="ribbon",
        phrase="a blue satin ribbon",
        article="a",
        tags={"cloth", "light"},
    ),
    "map": MissingThing(
        id="map",
        label="map",
        phrase="a folded paper map",
        article="a",
        tags={"paper", "light"},
    ),
    "badge": MissingThing(
        id="badge",
        label="badge",
        phrase="a bright brass badge",
        article="a",
        tags={"shiny", "light"},
    ),
}

CAUSES = {
    "kitten": Cause(
        id="kitten",
        label="a striped kitten",
        verb_past="battted",
        clue="pawprints",
        hideouts={"book_cart", "prop_trunk", "display_curtain"},
        carries={"cloth", "light", "jingle"},
        tags={"animal", "kitten"},
        reveal="a striped kitten curled around it like it had found the coziest treasure in the world",
    ),
    "magpie": Cause(
        id="magpie",
        label="a glossy magpie",
        verb_past="snatched",
        clue="feather",
        hideouts={"rafters", "window_ledge"},
        carries={"shiny", "jingle"},
        tags={"bird", "magpie"},
        reveal="a glossy magpie, blinking as if it could not understand why everybody cared so much about one lovely shiny thing",
    ),
    "wind": Cause(
        id="wind",
        label="the drafty wind",
        verb_past="swept",
        clue="flutter",
        hideouts={"window_ledge", "display_curtain"},
        carries={"paper", "cloth", "light"},
        tags={"weather", "wind"},
        reveal="nothing alive at all, only the mischievous draft that slipped through a cracked window",
    ),
}

CLUES = {
    "pawprints": Clue(
        id="pawprints",
        label="pawprints",
        phrase="tiny dusty pawprints",
        detail="They hopped in a neat little line, as if soft feet had been hurrying away with a prize.",
        cause="kitten",
        tags={"pawprints", "animal"},
    ),
    "feather": Clue(
        id="feather",
        label="feather",
        phrase="one black-and-white feather",
        detail="It rocked in the air for a moment and then pointed upward, toward a higher perch.",
        cause="magpie",
        tags={"feather", "bird"},
    ),
    "flutter": Clue(
        id="flutter",
        label="flutter",
        phrase="a restless flutter of paper and cloth",
        detail="Each little twitch came from the same direction, where a thin draft kept slipping through.",
        cause="wind",
        tags={"flutter", "wind"},
    ),
}

HIDEOUTS = {
    "book_cart": Hideout(
        id="book_cart",
        label="the tall book cart",
        phrase="the tall book cart by the atlas shelf",
        darkness=1,
        exodus="a small exodus of dust bunnies and forgotten paper slips",
        finding="On the bottom shelf, tucked behind a pile of giant picture books, something glimmered",
        tags={"library", "cart"},
    ),
    "window_ledge": Hideout(
        id="window_ledge",
        label="the high window ledge",
        phrase="the high window ledge behind the curtain",
        darkness=1,
        exodus="an exodus of dry leaves and cool air from the cracked window",
        finding="Caught in the corner where the curtain met the ledge, they saw it at once",
        tags={"window", "draft"},
    ),
    "prop_trunk": Hideout(
        id="prop_trunk",
        label="the old prop trunk",
        phrase="the old prop trunk under the stage stairs",
        darkness=3,
        exodus="a soft exodus of dusty moths from the velvet lining",
        finding="Beneath a pirate hat and a cardboard moon, there it was",
        tags={"theater", "trunk"},
    ),
    "rafters": Hideout(
        id="rafters",
        label="the rafters",
        phrase="the rafters above the stage",
        darkness=3,
        exodus="an exodus of loose feathers and a nervous rustle from overhead",
        finding="Wedged beside a warm beam, shining in the lantern light, was the missing thing",
        tags={"theater", "high"},
    ),
    "display_curtain": Hideout(
        id="display_curtain",
        label="the silver display curtain",
        phrase="the silver display curtain near the moon case",
        darkness=2,
        exodus="an exodus of trapped dust and cold, secret-looking air",
        finding="Hidden in the fold where the curtain brushed the floor, they found it",
        tags={"museum", "curtain"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Zoe", "Anna", "Clara", "Ivy"]
BOY_NAMES = ["Eli", "Ben", "Max", "Theo", "Sam", "Leo", "Noah", "Finn"]


@dataclass
class StoryParams:
    setting: str
    missing: str
    cause: str
    clue: str
    hideout: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    bravery: int = 2
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


CURATED = [
    StoryParams(
        setting="theater",
        missing="bell",
        cause="magpie",
        clue="feather",
        hideout="rafters",
        hero_name="Nora",
        hero_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        bravery=3,
    ),
    StoryParams(
        setting="library",
        missing="ribbon",
        cause="kitten",
        clue="pawprints",
        hideout="book_cart",
        hero_name="Mia",
        hero_gender="girl",
        friend_name="Ben",
        friend_gender="boy",
        bravery=1,
    ),
    StoryParams(
        setting="museum",
        missing="map",
        cause="wind",
        clue="flutter",
        hideout="display_curtain",
        hero_name="Theo",
        hero_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        bravery=2,
    ),
    StoryParams(
        setting="museum",
        missing="badge",
        cause="wind",
        clue="flutter",
        hideout="window_ledge",
        hero_name="Clara",
        hero_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        bravery=1,
    ),
    StoryParams(
        setting="theater",
        missing="ribbon",
        cause="kitten",
        clue="pawprints",
        hideout="prop_trunk",
        hero_name="Leo",
        hero_gender="boy",
        friend_name="Anna",
        friend_gender="girl",
        bravery=2,
    ),
]


KNOWLEDGE = {
    "rumor": [
        (
            "What is a rumor?",
            "A rumor is a story people pass around before they know if it is true. It can make a mystery feel bigger than it really is."
        )
    ],
    "pawprints": [
        (
            "What can pawprints tell you?",
            "Pawprints can show that an animal walked through a place. They can also point to where the animal went next."
        )
    ],
    "feather": [
        (
            "Why can a feather be a clue?",
            "A feather can show that a bird has been nearby. If something shiny is missing, that can be a very useful clue."
        )
    ],
    "flutter": [
        (
            "How can wind move light things?",
            "Wind can push paper, ribbon, and other light things across a room. If there is a draft, it can sweep them into corners or onto ledges."
        )
    ],
    "kitten": [
        (
            "Why do kittens carry things away?",
            "Kittens sometimes bat and drag small things because they are playful and curious. They are not trying to make trouble; they are exploring."
        )
    ],
    "magpie": [
        (
            "Why might a magpie take a shiny thing?",
            "Magpies notice bright, sparkling objects. A shiny bell or badge can catch a bird's eye."
        )
    ],
    "wind": [
        (
            "What is a draft?",
            "A draft is a small stream of moving air that slips through a crack or open space. It can make curtains stir and light objects slide away."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is not pretending you are never scared. It is choosing a careful, good action even when you feel a little afraid."
        )
    ],
    "ask_help": [
        (
            "Can asking a grown-up for help be brave?",
            "Yes. Asking for help is brave when you know something is too dark, high, or hard to handle alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["rumor", "pawprints", "feather", "flutter", "kitten", "magpie", "wind", "bravery", "ask_help"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    thing = f["missing_cfg"]
    cause = f["cause_cfg"]
    outcome = f["outcome"]
    prompts = [
        f'Write a gentle mystery story for a 3-to-5-year-old where an important {thing.label} goes missing at {setting.place} and whispers begin to circulate.',
        f'Write a story that uses the words "exodus", "circulate", and "bid", and shows a child using bravery to solve a mystery.',
    ]
    if outcome == "solo":
        prompts.append(
            f"Tell a mystery where a brave child follows a real clue, enters a dark hiding place, and discovers that {cause.label} took the missing {thing.label}."
        )
    else:
        prompts.append(
            f"Tell a mystery where a child makes a brave bid to help, notices the true clue, and then wisely asks a grown-up to come along for the final search."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = world.get("hero")
    friend = world.get("friend")
    adult = world.get("adult")
    thing = f["missing_cfg"]
    cause = f["cause_cfg"]
    clue = f["clue_cfg"]
    hideout = f["hideout_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was the mystery in the story?",
            f"The mystery was that {thing.the} disappeared just before {world.setting.event}. That made everyone nervous because the event needed it to begin."
        ),
        (
            "Why did the room start to feel spooky?",
            f"It felt spooky because whispers began to circulate that a ghost had taken {thing.the}. The rumor made the children more afraid even before they had any real clue."
        ),
        (
            f"What clue did {hero.label} find?",
            f"{hero.label} found {clue.phrase}. That mattered because it matched {cause.label}, so it pointed to a real cause instead of a ghost."
        ),
        (
            f"Where did they find {thing.the}?",
            f"They found {thing.the} in {hideout.phrase}. The clue led them there step by step."
        ),
        (
            f"What had really happened to {thing.the}?",
            f"It was not stolen by a ghost at all. {cause.label.capitalize()} had {cause.verb_past} it away, which fit the clue they found and explained the mystery."
        ),
    ]
    if outcome == "solo":
        qa.append(
            (
                f"How did {hero.label} show bravery?",
                f"{hero.label} felt the mystery and the darkness, but still followed the clue into {hideout.phrase}. {hero.pronoun('subject').capitalize()} was brave because {hero.pronoun('subject')} looked for the truth instead of believing the rumor."
            )
        )
    else:
        qa.append(
            (
                f"How did {hero.label} show bravery if {hero.pronoun('subject')} asked for help?",
                f"{hero.label} was brave enough to start the search and brave enough to say when the shadows felt too big alone. Asking {adult.label_word} to come turned fear into a careful plan."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"rumor", "bravery"}
    cause_cfg = world.facts["cause_cfg"]
    clue_cfg = world.facts["clue_cfg"]
    tags |= set(cause_cfg.tags)
    tags |= set(clue_cfg.tags)
    if world.facts["outcome"] == "adult_helped":
        tags.add("ask_help")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    if world.history:
        lines.append("  history:")
        for h in world.history:
            lines.append(f"    - {h}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
can_carry(C, M) :- carries(C, T), item_tag(M, T).
clue_matches(C, Cl) :- cause_clue(C, Cl), clue_cause(Cl, C).
hideout_allowed(S, C, H) :- setting_hideout(S, H), cause_hideout(C, H).
valid(S, M, C, Cl, H) :- setting(S), missing(M), cause(C), clue(Cl), hideout(H),
                         can_carry(C, M), clue_matches(C, Cl), hideout_allowed(S, C, H).

outcome(solo) :- bravery(B), chosen_hideout(H), darkness(H, D), B >= D.
outcome(adult_helped) :- bravery(B), chosen_hideout(H), darkness(H, D), B < D.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for hideout in sorted(setting.hideouts):
            lines.append(asp.fact("setting_hideout", sid, hideout))
    for mid, thing in MISSING.items():
        lines.append(asp.fact("missing", mid))
        for tag in sorted(thing.tags):
            lines.append(asp.fact("item_tag", mid, tag))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_clue", cid, cause.clue))
        for hid in sorted(cause.hideouts):
            lines.append(asp.fact("cause_hideout", cid, hid))
        for tag in sorted(cause.carries):
            lines.append(asp.fact("carries", cid, tag))
    for clid, clue in CLUES.items():
        lines.append(asp.fact("clue", clid))
        lines.append(asp.fact("clue_cause", clid, clue.cause))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        lines.append(asp.fact("darkness", hid, hideout.darkness))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_hideout", params.hideout),
            asp.fact("bravery", params.bravery),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _random_case(seed: int) -> StoryParams:
    rng = random.Random(seed)
    args = build_parser().parse_args([])
    return resolve_params(args, rng)


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

    cases = list(CURATED)
    for seed in range(50):
        try:
            case = _random_case(seed)
            case.seed = seed
            cases.append(case)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story or not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("smoke test generated an incomplete sample")
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            emit(sample, trace=False, qa=True, header="### smoke")
        finally:
            sys.stdout = old
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    else:
        print("OK: generate()/emit() smoke test passed.")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child solves a gentle mystery by following the right clue."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--missing", choices=MISSING)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--bravery", type=int, choices=[1, 2, 3], help="1=timid, 3=very brave")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible mystery set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin against Python and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.missing and args.cause and args.clue and args.hideout:
        setting = SETTINGS[args.setting]
        thing = MISSING[args.missing]
        cause = CAUSES[args.cause]
        clue = CLUES[args.clue]
        hideout = HIDEOUTS[args.hideout]
        if not (can_carry(cause, thing) and clue_matches(cause, clue) and hideout_allowed(setting, cause, hideout)):
            raise StoryError(explain_rejection(setting, thing, cause, clue, hideout))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.missing is None or combo[1] == args.missing)
        and (args.cause is None or combo[2] == args.cause)
        and (args.clue is None or combo[3] == args.clue)
        and (args.hideout is None or combo[4] == args.hideout)
    ]
    if not combos:
        chosen_setting = SETTINGS[args.setting] if args.setting else next(iter(SETTINGS.values()))
        chosen_missing = MISSING[args.missing] if args.missing else next(iter(MISSING.values()))
        chosen_cause = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
        chosen_clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
        chosen_hideout = HIDEOUTS[args.hideout] if args.hideout else next(iter(HIDEOUTS.values()))
        raise StoryError(explain_rejection(chosen_setting, chosen_missing, chosen_cause, chosen_clue, chosen_hideout))

    setting_id, missing_id, cause_id, clue_id, hideout_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=hero_name)
    bravery = args.bravery if args.bravery is not None else rng.choice([1, 2, 3])

    return StoryParams(
        setting=setting_id,
        missing=missing_id,
        cause=cause_id,
        clue=clue_id,
        hideout=hideout_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        bravery=bravery,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.missing not in MISSING:
        raise StoryError(f"(Unknown missing item: {params.missing})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.hideout not in HIDEOUTS:
        raise StoryError(f"(Unknown hideout: {params.hideout})")
    if params.bravery not in {1, 2, 3}:
        raise StoryError("(Bravery must be 1, 2, or 3.)")

    setting = SETTINGS[params.setting]
    thing = MISSING[params.missing]
    cause = CAUSES[params.cause]
    clue = CLUES[params.clue]
    hideout = HIDEOUTS[params.hideout]
    if not (can_carry(cause, thing) and clue_matches(cause, clue) and hideout_allowed(setting, cause, hideout)):
        raise StoryError(explain_rejection(setting, thing, cause, clue, hideout))

    world = tell(
        setting=setting,
        thing=thing,
        cause=cause,
        clue_cfg=clue,
        hideout=hideout,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=setting.adult_type,
        bravery=params.bravery,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, missing, cause, clue, hideout) combos:\n")
        for setting, missing, cause, clue, hideout in combos:
            print(f"  {setting:8} {missing:7} {cause:7} {clue:10} {hideout}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = (
                f"### {p.hero_name} and {p.friend_name}: {p.missing} / {p.cause} "
                f"at {p.setting} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
