#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py
================================================================================

A standalone story world for a tiny fable-like laundromat mystery: two friends
bring a favorite item to the laundromat, the item seems to vanish, they joke
about a silly thief, then solve the mystery by following the right clue and
searching in the right place together.

This world keeps the domain small and constraint-checked:
- a missing item must be light or shaped in a way that could plausibly hide
  where the story says it hid;
- the clue must honestly point to that hiding place;
- the chosen search method must actually reveal the item.

The story is driven by simulated state: items tumble, cling, slip, or hide;
friends grow worried, curious, and then relieved; and the ending proves what
changed by showing the found item and the friends laughing together.

Run it
------
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py --item sock --hiding static_window
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py --item blanket_corner
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py --qa --json
    python storyworlds/worlds/gpt-5.4/rid_laundromat_humor_friendship_mystery_to_solve.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"          # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "hen", "goose", "sheep"}
        male = {"boy", "fox", "frog", "he"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    the: str
    kind: str
    size: str
    static_prone: bool
    can_tuck: bool
    can_fall: bool
    special: str
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]
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
class HidingCfg:
    id: str
    label: str
    place_text: str
    cause_text: str
    reveal_text: str
    needs_static: bool = False
    needs_tuckable: bool = False
    needs_fallable: bool = False
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
class ClueCfg:
    id: str
    label: str
    text: str
    points_to: set[str] = field(default_factory=set)
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
class SearchCfg:
    id: str
    label: str
    act_text: str
    success_text: str
    finds: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_hidden_worry(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["hidden"] < THRESHOLD:
        return []
    sig = ("hidden_worry", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["worry"] += 1
    friend.memes["curiosity"] += 1
    world.get("laundromat").meters["mystery"] += 1
    return []


def _r_friendship_steadies(world: World) -> list[str]:
    hero = world.get("hero")
    friend = world.get("friend")
    if hero.memes["worry"] < THRESHOLD or friend.memes["helping"] < THRESHOLD:
        return []
    sig = ("steady", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["steady"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    return []


def _r_found_relief(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["found"] < THRESHOLD:
        return []
    sig = ("found_relief", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero = world.get("hero")
    friend = world.get("friend")
    hero.memes["relief"] += 1
    friend.memes["relief"] += 1
    hero.memes["gratitude"] += 1
    friend.memes["friendship"] += 1
    world.get("laundromat").meters["mystery"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="hidden_worry", tag="mystery", apply=_r_hidden_worry),
    Rule(name="friendship_steadies", tag="social", apply=_r_friendship_steadies),
    Rule(name="found_relief", tag="ending", apply=_r_found_relief),
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
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def hide_possible(item: ItemCfg, hiding: HidingCfg) -> bool:
    if hiding.needs_static and not item.static_prone:
        return False
    if hiding.needs_tuckable and not item.can_tuck:
        return False
    if hiding.needs_fallable and not item.can_fall:
        return False
    return True


def clue_matches(hiding: HidingCfg, clue: ClueCfg) -> bool:
    return hiding.id in clue.points_to


def search_finds(hiding: HidingCfg, search: SearchCfg) -> bool:
    return hiding.id in search.finds


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for item_id, item in ITEMS.items():
        for hiding_id, hiding in HIDINGS.items():
            if not hide_possible(item, hiding):
                continue
            for clue_id, clue in CLUES.items():
                if clue_matches(hiding, clue):
                    combos.append((item_id, hiding_id, clue_id))
    return sorted(combos)


def valid_searches_for(hiding_id: str) -> list[str]:
    return sorted(sid for sid, s in SEARCHES.items() if search_finds(HIDINGS[hiding_id], s))


# ---------------------------------------------------------------------------
# Prediction helpers
# ---------------------------------------------------------------------------
def predict_clue(world: World, hiding_id: str) -> dict:
    sim = world.copy()
    hiding = HIDINGS[hiding_id]
    item = sim.get("item")
    item.attrs["hiding"] = hiding.id
    item.meters["hidden"] = 1.0
    if hiding.id == "static_window":
        item.meters["static"] = 1.0
    if hiding.id == "inside_sleeve":
        item.meters["tucked"] = 1.0
    if hiding.id == "behind_basket":
        item.meters["low"] = 1.0
    propagate(sim, narrate=False)
    plausible = [cid for cid, clue in CLUES.items() if clue_matches(hiding, clue)]
    return {
        "mystery": sim.get("laundromat").meters["mystery"],
        "plausible_clues": plausible,
    }


# ---------------------------------------------------------------------------
# Verbs / screenplay actions
# ---------------------------------------------------------------------------
def arrive(world: World, hero: Entity, friend: Entity, caretaker: Entity, item: ItemCfg) -> None:
    for ent in (hero, friend):
        ent.memes["friendship"] += 1
        ent.memes["joy"] += 1
    world.say(
        f"On soap-bright morning, {hero.id} and {friend.id} trotted into the laundromat with "
        f"{caretaker.label}. The washers hummed like fat silver bees, and a row of dryers "
        f"blinked warm orange eyes."
    )
    world.say(
        f"{hero.id} carried {item.the} as proudly as if it were a tiny banner. "
        f"{item.The} was {item.special}, and {hero.pronoun('subject')} did not want to lose it."
    )


def joke_setup(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f'{friend.id} sniffed the clean air and grinned. "This place smells like bubbles trying to sing," '
        f"{friend.pronoun('subject')} said."
    )
    world.say(
        f'{hero.id} laughed. "If the socks start dancing by themselves, we will know the soap has grown feet."'
    )


def load_machine(world: World, hero: Entity, friend: Entity, item_cfg: ItemCfg) -> None:
    item = world.get("item")
    item.meters["in_load"] = 1.0
    world.say(
        f"Together they fed shirts, towels, and {item_cfg.the} into a dryer. "
        f"The round door shut with a plump little kiss, and the clothes began to tumble."
    )


def notice_missing(world: World, hero: Entity, item_cfg: ItemCfg) -> None:
    item = world.get("item")
    item.meters["hidden"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"When the tumbling stopped, {hero.id} reached in for {item_cfg.the} and blinked. "
        f"{item_cfg.The} was gone."
    )
    world.say(
        f"{hero.id}'s ears drooped. \"Oh dear,\" {hero.pronoun('subject')} whispered. "
        f"\"How will I ever rid my mind of this worry if I cannot even find my own {item_cfg.label}?\""
    )


def make_funny_guess(world: World, friend: Entity) -> None:
    friend.memes["humor"] += 1
    world.say(
        f'{friend.id} widened {friend.pronoun("possessive")} eyes in a grand, silly way. '
        f'"Perhaps the Laundromat Nibbler took it," {friend.pronoun("subject")} said. '
        f'"Perhaps it eats only one thing from each load so it never gets too full."'
    )


def calm_with_friendship(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["helping"] += 1
    propagate(world, narrate=False)
    steady = ""
    if hero.memes["steady"] >= THRESHOLD:
        steady = f" The worry in {hero.id}'s face softened."
    world.say(
        f'{friend.id} bumped shoulders with {hero.id}. "Then we will solve the mystery together," '
        f'{friend.pronoun("subject")} said. "A good friend is better than ten nervous guesses."{steady}'
    )


def inspect_clue(world: World, hero: Entity, friend: Entity, clue: ClueCfg, hiding: HidingCfg) -> None:
    pred = predict_clue(world, hiding.id)
    world.facts["predicted_mystery"] = pred["mystery"]
    world.facts["possible_clues"] = list(pred["plausible_clues"])
    hero.memes["curiosity"] += 1
    friend.memes["curiosity"] += 1
    world.say(
        f"They looked carefully instead of panicking. Soon {clue.text}"
    )
    world.say(
        f'"That is no nibble mark," said {friend.id}. "It is a clue."'
    )


def search(world: World, hero: Entity, friend: Entity, search_cfg: SearchCfg, hiding: HidingCfg, item_cfg: ItemCfg) -> None:
    hero.memes["effort"] += 1
    friend.memes["helping"] += 1
    world.say(search_cfg.act_text)
    if not search_finds(hiding, search_cfg):
        raise StoryError(
            f"(No story: searching by '{search_cfg.id}' would not honestly find {item_cfg.the} in {hiding.place_text}.)"
        )
    item = world.get("item")
    item.meters["found"] = 1.0
    item.meters["hidden"] = 0.0
    item.attrs["found_at"] = hiding.id
    propagate(world, narrate=False)
    world.say(search_cfg.success_text.format(item=item_cfg.label))


def explain_cause(world: World, caretaker: Entity, item_cfg: ItemCfg, hiding: HidingCfg) -> None:
    item = world.get("item")
    if hiding.id == "static_window":
        item.meters["static"] += 1
    elif hiding.id == "inside_sleeve":
        item.meters["tucked"] += 1
    elif hiding.id == "behind_basket":
        item.meters["low"] += 1
    world.say(
        f'{caretaker.label.capitalize()} chuckled softly. "{hiding.cause_text}," {caretaker.pronoun("subject")} said. '
        f'"Nothing stole {item_cfg.the}. The laundromat only played a little trick."'
    )


def moral_ending(world: World, hero: Entity, friend: Entity, item_cfg: ItemCfg, hiding: HidingCfg) -> None:
    world.say(
        f"{hero.id} hugged {item_cfg.the}, and {friend.id} laughed so hard {friend.pronoun('subject')} nearly hiccuped."
    )
    world.say(
        f'"Farewell, Laundromat Nibbler," said {hero.id}. "We have found out where you hide your treasures."'
    )
    world.say(
        f"And the two friends folded the clothes side by side, wiser and cheerier than before. "
        f"They had rid the room of fear, not by shouting at shadows, but by looking closely and helping each other."
    )
    world.say(
        "So it is often in small mysteries: a steady friend and a careful eye can make a foolish monster disappear."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(
    item_cfg: ItemCfg,
    hiding_cfg: HidingCfg,
    clue_cfg: ClueCfg,
    search_cfg: SearchCfg,
    hero_name: str = "Pip",
    hero_type: str = "mouse",
    friend_name: str = "Tansy",
    friend_type: str = "duck",
    caretaker_type: str = "otter",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="hero", label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend", label=friend_name))
    caretaker = world.add(
        Entity(id="Caretaker", kind="character", type=caretaker_type, role="caretaker", label="old Otter")
    )
    laundromat = world.add(Entity(id="laundromat", kind="place", type="laundromat", label="the laundromat"))
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type=item_cfg.kind,
            label=item_cfg.label,
            role="missing_item",
            attrs={"hiding": hiding_cfg.id, "clue": clue_cfg.id, "search": search_cfg.id, "found_at": ""},
        )
    )

    laundromat.meters["mystery"] = 0.0
    item.meters["hidden"] = 0.0
    item.meters["found"] = 0.0
    item.meters["static"] = 0.0
    item.meters["tucked"] = 0.0
    item.meters["low"] = 0.0
    hero.memes["worry"] = 0.0
    hero.memes["steady"] = 0.0
    hero.memes["curiosity"] = 0.0
    friend.memes["helping"] = 0.0
    friend.memes["curiosity"] = 0.0

    arrive(world, hero, friend, caretaker, item_cfg)
    joke_setup(world, hero, friend)

    world.para()
    load_machine(world, hero, friend, item_cfg)
    notice_missing(world, hero, item_cfg)
    make_funny_guess(world, friend)
    calm_with_friendship(world, hero, friend)

    world.para()
    inspect_clue(world, hero, friend, clue_cfg, hiding_cfg)
    search(world, hero, friend, search_cfg, hiding_cfg, item_cfg)
    explain_cause(world, caretaker, item_cfg, hiding_cfg)

    world.para()
    moral_ending(world, hero, friend, item_cfg, hiding_cfg)

    world.facts.update(
        hero=hero,
        friend=friend,
        caretaker=caretaker,
        item_cfg=item_cfg,
        hiding_cfg=hiding_cfg,
        clue_cfg=clue_cfg,
        search_cfg=search_cfg,
        item=item,
        solved=item.meters["found"] >= THRESHOLD,
        mystery_level=laundromat.meters["mystery"],
        cause=hiding_cfg.cause_text,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
ITEMS = {
    "sock": ItemCfg(
        id="sock",
        label="sock",
        phrase="a striped little sock",
        the="the striped little sock",
        kind="sock",
        size="small",
        static_prone=True,
        can_tuck=True,
        can_fall=True,
        special="small enough to vanish from a careless glance and bright enough to be missed at once",
        tags={"sock", "cloth"},
    ),
    "scarf": ItemCfg(
        id="scarf",
        label="scarf",
        phrase="a cherry-red scarf",
        the="the cherry-red scarf",
        kind="scarf",
        size="long",
        static_prone=False,
        can_tuck=True,
        can_fall=False,
        special="soft and red as jam, with a loose end that liked to wander",
        tags={"scarf", "cloth"},
    ),
    "mitten": ItemCfg(
        id="mitten",
        label="mitten",
        phrase="a small blue mitten",
        the="the small blue mitten",
        kind="mitten",
        size="small",
        static_prone=True,
        can_tuck=True,
        can_fall=True,
        special="puffed with warmth and easy to lose between bigger things",
        tags={"mitten", "cloth"},
    ),
}

HIDINGS = {
    "static_window": HidingCfg(
        id="static_window",
        label="dryer window",
        place_text="the inside of the warm dryer window",
        cause_text="the dry spinning made a crackly static cling, and the item stuck flat against the glass",
        reveal_text="There it was, pressed against the window as flat as a sleepy leaf",
        needs_static=True,
        tags={"dryer", "static"},
    ),
    "inside_sleeve": HidingCfg(
        id="inside_sleeve",
        label="inside a shirt sleeve",
        place_text="inside the sleeve of a large shirt",
        cause_text="the turning load tucked the item into a sleeve, where it rode like a quiet stowaway",
        reveal_text="Out it slipped from a sleeve that had looked empty a moment before",
        needs_tuckable=True,
        tags={"shirt", "hidden"},
    ),
    "behind_basket": HidingCfg(
        id="behind_basket",
        label="behind the basket",
        place_text="behind the wicker laundry basket",
        cause_text="when the door opened, the item slid low and dropped behind the basket with a whisper",
        reveal_text="There it peeped from the floor, shy as a crumb-colored mouse",
        needs_fallable=True,
        tags={"basket", "floor"},
    ),
}

CLUES = {
    "glass_peek": ClueCfg(
        id="glass_peek",
        label="a bright patch on the glass",
        text="they saw a bright patch clinging to the dryer window, almost too flat to notice.",
        points_to={"static_window"},
        tags={"look", "glass"},
    ),
    "one_sleeve_lumpy": ClueCfg(
        id="one_sleeve_lumpy",
        label="one shirt sleeve looked oddly fat",
        text="one big shirt sleeve hung in a lumpy way, as if it were hiding a rolled-up secret.",
        points_to={"inside_sleeve"},
        tags={"shirt", "lump"},
    ),
    "lint_trail_low": ClueCfg(
        id="lint_trail_low",
        label="a lint trail on the floor",
        text="a tiny trail of lint led from the dryer door down toward the basket legs.",
        points_to={"behind_basket"},
        tags={"lint", "floor"},
    ),
}

SEARCHES = {
    "check_glass": SearchCfg(
        id="check_glass",
        label="press noses to the glass",
        act_text="They pressed their noses to the warm round glass and looked edge to edge.",
        success_text="At once they laughed. There was the {item}, flattened against the window like a shy flag.",
        finds={"static_window"},
        tags={"glass"},
    ),
    "shake_shirts": SearchCfg(
        id="shake_shirts",
        label="shake the shirts",
        act_text="They lifted the big shirts one by one and gave each sleeve a careful shake.",
        success_text="On the third shake, out tumbled the {item}, riding free from a sleeve.",
        finds={"inside_sleeve"},
        tags={"shirts"},
    ),
    "peek_behind_basket": SearchCfg(
        id="peek_behind_basket",
        label="peek behind the basket",
        act_text="They crouched low together and peeped behind the basket where the wheels kissed the floor.",
        success_text="There, hiding in the dustless corner, lay the {item}, waiting to be noticed.",
        finds={"behind_basket"},
        tags={"basket", "floor"},
    ),
}

HEROES = [
    ("Pip", "mouse"),
    ("Nell", "hen"),
    ("Milo", "fox"),
    ("Toby", "frog"),
]
FRIENDS = [
    ("Tansy", "duck"),
    ("Moss", "goose"),
    ("Wren", "sheep"),
    ("Bram", "fox"),
]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    item: str
    hiding: str
    clue: str
    search: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    caretaker_type: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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
    "laundromat": [
        (
            "What is a laundromat?",
            "A laundromat is a place with washing machines and dryers where people clean clothes. The machines wash, spin, and dry things that would take much longer by hand.",
        )
    ],
    "static": [
        (
            "Why can a sock stick to a dryer window?",
            "Dry clothes can build up static electricity while they tumble. That tiny crackly pull can make a light cloth cling to glass.",
        )
    ],
    "sleeve": [
        (
            "How can a small thing get lost inside a shirt sleeve?",
            "When clothes tumble together, a small cloth item can get tucked into a sleeve or fold. It is still there, but it is hidden inside bigger laundry.",
        )
    ],
    "basket": [
        (
            "Why do things sometimes fall behind a laundry basket?",
            "A small item can slide low when a basket is moved or when a dryer door opens. Then it can slip out of sight behind the basket.",
        )
    ],
    "friendship": [
        (
            "How can a friend help when you feel worried?",
            "A friend can stay calm, look with you, and help you think clearly. Sharing the problem often makes it feel smaller and easier to solve.",
        )
    ],
    "mystery": [
        (
            "What helps solve a mystery?",
            "Good mysteries are solved by noticing clues and checking what really happened. Guessing wildly can be funny, but careful looking finds the truth.",
        )
    ],
}
KNOWLEDGE_ORDER = ["laundromat", "static", "sleeve", "basket", "friendship", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    item = f["item_cfg"]
    hiding = f["hiding_cfg"]
    return [
        f'Write a short fable-like story set in a laundromat where two friends solve a funny mystery about a missing {item.label}. Include the word "rid".',
        f"Tell a child-friendly mystery where {hero.id} loses {item.the}, {friend.id} makes a silly guess, and the truth is found in {hiding.place_text}.",
        f"Write a gentle story with humor, friendship, and a mystery to solve, ending with the friends becoming calm and wise together.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    caretaker = f["caretaker"]
    item_cfg = f["item_cfg"]
    hiding = f["hiding_cfg"]
    clue = f["clue_cfg"]
    search = f["search_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} and {friend.id}, two friends at a laundromat. They work together when {item_cfg.the} seems to disappear.",
        ),
        (
            f"What was the mystery?",
            f"The mystery was that {item_cfg.the} seemed to be missing after the dryer stopped. That made {hero.id} worried because the item was special.",
        ),
        (
            f"Why did {friend.id} joke about a Laundromat Nibbler?",
            f"{friend.id} was trying to make {hero.id} smile instead of panic. The silly joke turned the fear into a puzzle the friends could solve together.",
        ),
        (
            "What clue helped them?",
            f"The clue was {clue.label}. It mattered because it pointed toward {hiding.place_text} instead of a make-believe thief.",
        ),
        (
            "How did they solve the mystery?",
            f"They chose to {search.label}. That worked because the missing item was really in {hiding.place_text}.",
        ),
        (
            f"Why was the item not truly stolen?",
            f"It was not stolen at all; {caretaker.label} explained that {hiding.cause_text}. The machines and moving clothes caused the trick, not a thief.",
        ),
        (
            "What changed by the end?",
            f"At first the laundromat felt full of worry and mystery, but by the end the friends had found the item and were laughing. Their careful search rid the room of fear and left them feeling wiser together.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"laundromat", "friendship", "mystery"}
    hiding = world.facts["hiding_cfg"]
    if hiding.id == "static_window":
        tags.add("static")
    elif hiding.id == "inside_sleeve":
        tags.add("sleeve")
    elif hiding.id == "behind_basket":
        tags.add("basket")
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


# ---------------------------------------------------------------------------
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        attrs = {k: v for k, v in ent.attrs.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if attrs:
            bits.append(f"attrs={attrs}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        item="sock",
        hiding="static_window",
        clue="glass_peek",
        search="check_glass",
        hero_name="Pip",
        hero_type="mouse",
        friend_name="Tansy",
        friend_type="duck",
        caretaker_type="otter",
    ),
    StoryParams(
        item="scarf",
        hiding="inside_sleeve",
        clue="one_sleeve_lumpy",
        search="shake_shirts",
        hero_name="Nell",
        hero_type="hen",
        friend_name="Moss",
        friend_type="goose",
        caretaker_type="otter",
    ),
    StoryParams(
        item="mitten",
        hiding="behind_basket",
        clue="lint_trail_low",
        search="peek_behind_basket",
        hero_name="Toby",
        hero_type="frog",
        friend_name="Wren",
        friend_type="sheep",
        caretaker_type="otter",
    ),
]


def explain_rejection(item: ItemCfg, hiding: HidingCfg, clue: Optional[ClueCfg] = None, search: Optional[SearchCfg] = None) -> str:
    if not hide_possible(item, hiding):
        if hiding.needs_static:
            return (
                f"(No story: {item.the} is not light and static-prone enough to plausibly cling to the dryer window. "
                f"Choose a lighter item, or a different hiding place.)"
            )
        if hiding.needs_tuckable:
            return (
                f"(No story: {item.the} would not honestly tuck itself inside a sleeve in this world. "
                f"Choose a smaller or more foldable item.)"
            )
        if hiding.needs_fallable:
            return (
                f"(No story: {item.the} would not plausibly slip behind the basket here. "
                f"Choose an item that could drop low and slide away.)"
            )
    if clue is not None and not clue_matches(hiding, clue):
        return (
            f"(No story: clue '{clue.id}' does not honestly point to {hiding.place_text}. "
            f"Pick a clue that matches the hiding place.)"
        )
    if search is not None and not search_finds(hiding, search):
        return (
            f"(No story: search '{search.id}' would not honestly find an item hidden in {hiding.place_text}. "
            f"Pick a matching search method.)"
        )
    return "(No story: the requested combination is unreasonable.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% plausibility of hiding places
hide_possible(I,H) :- item(I), hiding(H), needs_static(H), static_prone(I).
hide_possible(I,H) :- item(I), hiding(H), needs_tuckable(H), can_tuck(I).
hide_possible(I,H) :- item(I), hiding(H), needs_fallable(H), can_fall(I).
hide_possible(I,H) :- item(I), hiding(H), not needs_static(H), not needs_tuckable(H), not needs_fallable(H).

valid(I,H,C) :- hide_possible(I,H), clue_points(C,H).
good_search(H,S) :- search_finds(S,H).

% derived outcome
solved :- chosen_hiding(H), chosen_search(S), good_search(H,S).
outcome(solved) :- solved.
outcome(stuck) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.static_prone:
            lines.append(asp.fact("static_prone", item_id))
        if item.can_tuck:
            lines.append(asp.fact("can_tuck", item_id))
        if item.can_fall:
            lines.append(asp.fact("can_fall", item_id))
    for hiding_id, hiding in HIDINGS.items():
        lines.append(asp.fact("hiding", hiding_id))
        if hiding.needs_static:
            lines.append(asp.fact("needs_static", hiding_id))
        if hiding.needs_tuckable:
            lines.append(asp.fact("needs_tuckable", hiding_id))
        if hiding.needs_fallable:
            lines.append(asp.fact("needs_fallable", hiding_id))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        for hiding_id in sorted(clue.points_to):
            lines.append(asp.fact("clue_points", clue_id, hiding_id))
    for search_id, search in SEARCHES.items():
        lines.append(asp.fact("search", search_id))
        for hiding_id in sorted(search.finds):
            lines.append(asp.fact("search_finds", search_id, hiding_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_good_searches() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show good_search/2."))
    return sorted(set(asp.atoms(model, "good_search")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_hiding", params.hiding),
            asp.fact("chosen_search", params.search),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "solved" if search_finds(HIDINGS[params.hiding], SEARCHES[params.search]) else "stuck"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_search = set((hid, sid) for hid in HIDINGS for sid in SEARCHES if search_finds(HIDINGS[hid], SEARCHES[sid]))
    asp_search = set((h, s) for (h, s) in asp_good_searches())
    if py_search == asp_search:
        print(f"OK: search mapping matches ({len(py_search)} pairs).")
    else:
        rc = 1
        print("MISMATCH in search mapping:")
        if asp_search - py_search:
            print("  only in clingo:", sorted(asp_search - py_search))
        if py_search - asp_search:
            print("  only in python:", sorted(py_search - asp_search))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            continue
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a laundromat mystery solved by humor, clues, and friendship."
    )
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hiding", choices=HIDINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--search", choices=SEARCHES)
    ap.add_argument("--caretaker", choices=["otter", "goat"], help="grown-up helper species")
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
    if args.item and args.hiding:
        item = ITEMS[args.item]
        hiding = HIDINGS[args.hiding]
        if not hide_possible(item, hiding):
            raise StoryError(explain_rejection(item, hiding))
    if args.hiding and args.clue:
        hiding = HIDINGS[args.hiding]
        clue = CLUES[args.clue]
        if not clue_matches(hiding, clue):
            item = ITEMS[args.item] if args.item else next(iter(ITEMS.values()))
            raise StoryError(explain_rejection(item, hiding, clue=clue))
    combos = [
        combo for combo in valid_combos()
        if (args.item is None or combo[0] == args.item)
        and (args.hiding is None or combo[1] == args.hiding)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    item_id, hiding_id, clue_id = rng.choice(combos)
    search_choices = valid_searches_for(hiding_id)
    if args.search is not None:
        if args.search not in search_choices:
            raise StoryError(explain_rejection(ITEMS[item_id], HIDINGS[hiding_id], clue=CLUES[clue_id], search=SEARCHES[args.search]))
        search_id = args.search
    else:
        search_id = rng.choice(search_choices)

    hero_name, hero_type = rng.choice(HEROES)
    friend_name, friend_type = rng.choice([pair for pair in FRIENDS if pair[0] != hero_name])
    caretaker_type = args.caretaker or rng.choice(["otter", "goat"])

    return StoryParams(
        item=item_id,
        hiding=hiding_id,
        clue=clue_id,
        search=search_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        caretaker_type=caretaker_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        item_cfg = ITEMS[params.item]
        hiding_cfg = HIDINGS[params.hiding]
        clue_cfg = CLUES[params.clue]
        search_cfg = SEARCHES[params.search]
    except KeyError as err:
        raise StoryError(f"(No story: unknown parameter value {err.args[0]!r}.)") from None

    if not hide_possible(item_cfg, hiding_cfg):
        raise StoryError(explain_rejection(item_cfg, hiding_cfg))
    if not clue_matches(hiding_cfg, clue_cfg):
        raise StoryError(explain_rejection(item_cfg, hiding_cfg, clue=clue_cfg))
    if not search_finds(hiding_cfg, search_cfg):
        raise StoryError(explain_rejection(item_cfg, hiding_cfg, clue=clue_cfg, search=search_cfg))

    world = tell(
        item_cfg=item_cfg,
        hiding_cfg=hiding_cfg,
        clue_cfg=clue_cfg,
        search_cfg=search_cfg,
        hero_name=params.hero_name,
        hero_type=params.hero_type,
        friend_name=params.friend_name,
        friend_type=params.friend_type,
        caretaker_type=params.caretaker_type,
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
        print(asp_program("", "#show valid/3.\n#show good_search/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        searches = asp_good_searches()
        print(f"{len(combos)} compatible (item, hiding, clue) combos:\n")
        for item_id, hiding_id, clue_id in combos:
            fits = sorted(s for (h, s) in searches if h == hiding_id)
            print(f"  {item_id:8} {hiding_id:14} {clue_id:16} search=[{', '.join(fits)}]")
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
            header = f"### {p.hero_name} & {p.friend_name}: {p.item} hidden at {p.hiding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
