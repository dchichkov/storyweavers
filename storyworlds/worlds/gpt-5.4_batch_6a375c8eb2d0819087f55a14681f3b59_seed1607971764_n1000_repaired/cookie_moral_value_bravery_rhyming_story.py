#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py
======================================================================

A standalone story world for a tiny rhyming tale about **a cookie, kindness,
and bravery**.

This world models a simple domain:

- a child and a grown-up make one special cookie for someone else,
- the child wants to keep it because it smells warm and sweet,
- a small, concrete obstacle makes the delivery feel scary,
- the child either shrinks back or bravely carries the cookie anyway,
- the ending proves what changed: the cookie is shared, and courage becomes
  easier next time.

The world is state-driven rather than template-swapped:

- physical meters track things like a cookie being baked, carried, cracked, or
  delivered;
- emotional memes track temptation, fear, kindness, honesty, and courage;
- a short forward-chaining rule system turns fear + support into brave action
  and delivered kindness into shared joy.

The prose aims for a child-facing, lightly rhyming story style.

Run it
------
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py --kind chocolate --worry dark_hall
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py --aid song
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cookie_moral_value_bravery_rhyming_story.py --verify
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
KINDNESS_MIN = 1
BRAVERY_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "grandmother", "teacher"}
        male = {"boy", "father", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)
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
class CookieKind:
    id: str
    label: str
    smell: str
    crumb: str
    shine: str
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
class Recipient:
    id: str
    label: str
    place: str
    need: str
    thanks: str
    relation_word: str
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
class Worry:
    id: str
    label: str
    place_detail: str
    sound: str
    needs: set[str]
    fear: int
    bravery_cost: int
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
class Aid:
    id: str
    label: str
    phrase: str
    action: str
    helps: set[str]
    support: int
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


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cookie = world.get("cookie")
    if cookie.meters["carried"] < THRESHOLD:
        return out
    if child.memes["kindness"] < KINDNESS_MIN:
        return out
    if child.memes["support"] + child.memes["resolve"] < child.meters["fear_need"]:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery"] += 1
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1)
    out.append("__brave__")
    return out


def _r_delivered(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    cookie = world.get("cookie")
    if child.memes["bravery"] < BRAVERY_MIN or cookie.meters["carried"] < THRESHOLD:
        return out
    sig = ("delivered",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cookie.meters["delivered"] += 1
    recipient = world.get("recipient")
    recipient.memes["comfort"] += 1
    child.memes["joy"] += 1
    child.memes["lesson"] += 1
    out.append("__delivered__")
    return out


def _r_shared_joy(world: World) -> list[str]:
    out: list[str] = []
    cookie = world.get("cookie")
    if cookie.meters["delivered"] < THRESHOLD:
        return out
    sig = ("shared_joy",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    adult = world.get("adult")
    adult.memes["pride"] += 1
    adult.memes["joy"] += 1
    out.append("__shared__")
    return out


CAUSAL_RULES = [
    Rule(name="brave_step", tag="social", apply=_r_brave),
    Rule(name="delivery", tag="physical", apply=_r_delivered),
    Rule(name="shared_joy", tag="social", apply=_r_shared_joy),
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


COOKIES = {
    "chocolate": CookieKind(
        id="chocolate",
        label="chocolate chip cookie",
        smell="smelled like brown sugar and warm cheer",
        crumb="soft brown crumbs",
        shine="the chips winked like tiny night stars",
        tags={"cookie", "baking"},
    ),
    "ginger": CookieKind(
        id="ginger",
        label="ginger cookie",
        smell="smelled spicy-sweet and bright",
        crumb="golden crumbs",
        shine="its sugar top gave a little light",
        tags={"cookie", "baking"},
    ),
    "oatmeal": CookieKind(
        id="oatmeal",
        label="oatmeal cookie",
        smell="smelled cozy, round, and sweet",
        crumb="oaty crumbs",
        shine="its top looked sunny and good to eat",
        tags={"cookie", "baking"},
    ),
}

RECIPIENTS = {
    "grandma": Recipient(
        id="grandma",
        label="Grandma",
        place="the little blue house next door",
        need="had a sniffly cold and was resting in a chair",
        thanks="Grandma laughed and said the warm cookie made the gray day glow",
        relation_word="grandma",
        tags={"sharing", "family"},
    ),
    "neighbor": Recipient(
        id="neighbor",
        label="Mr. Lee",
        place="the neat brick porch across the lane",
        need="had spent the morning sweeping leaves all alone",
        thanks="Mr. Lee smiled and said the kind surprise made the afternoon feel less lonely",
        relation_word="neighbor",
        tags={"sharing", "neighbor"},
    ),
    "teacher": Recipient(
        id="teacher",
        label="Ms. June",
        place="the school gate by the flower bed",
        need="had stayed late to hang bright drawings on the wall",
        thanks="Ms. June beamed and said the cookie was a sweet little thank-you",
        relation_word="teacher",
        tags={"sharing", "school"},
    ),
}

WORRIES = {
    "dark_hall": Worry(
        id="dark_hall",
        label="a dark hall",
        place_detail="the hall between the kitchen and the front door looked dim and tall",
        sound="the old floor made soft creak-creak sounds",
        needs={"light", "hand"},
        fear=2,
        bravery_cost=2,
        tags={"dark"},
    ),
    "bark_gate": Worry(
        id="bark_gate",
        label="a barky gate",
        place_detail="the gate by the hedge gave a sudden rattly shake",
        sound="a small dog yapped from the other yard",
        needs={"hand", "song"},
        fear=2,
        bravery_cost=2,
        tags={"dog"},
    ),
    "windy_steps": Worry(
        id="windy_steps",
        label="windy steps",
        place_detail="the porch steps were high, and the wind whisked at sleeves and toes",
        sound="the breeze went whooo around the rail",
        needs={"hand", "tray"},
        fear=1,
        bravery_cost=1,
        tags={"wind"},
    ),
    "quiet_evening": Worry(
        id="quiet_evening",
        label="a very quiet evening",
        place_detail="the lane felt extra still, with shadows stretched long on the stones",
        sound="everything was so hushed that the hush itself felt loud",
        needs={"song", "light"},
        fear=1,
        bravery_cost=1,
        tags={"quiet"},
    ),
}

AIDS = {
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a little lantern",
        action="clicked on the lantern so a warm gold circle slid along the floor",
        helps={"light"},
        support=1,
        tags={"light"},
    ),
    "hand_hold": Aid(
        id="hand_hold",
        label="hand hold",
        phrase="a steady hand",
        action="offered a steady hand and walked close beside the child",
        helps={"hand"},
        support=1,
        tags={"hand"},
    ),
    "song": Aid(
        id="song",
        label="song",
        phrase="a humming song",
        action="began a soft humming song that made each small step feel less alone",
        helps={"song"},
        support=1,
        tags={"song"},
    ),
    "tray": Aid(
        id="tray",
        label="tray",
        phrase="a small tray",
        action="set the cookie on a small tray so careful hands could carry it flat and proud",
        helps={"tray"},
        support=1,
        tags={"tray"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Noah", "Finn"]
TRAITS = ["gentle", "thoughtful", "cheerful", "careful", "kind"]


def aid_helps(aid: Aid, worry: Worry) -> bool:
    return bool(aid.helps & worry.needs)


def enough_support(aid1: Aid, aid2: Aid, worry: Worry) -> bool:
    support_tags = set(aid1.helps) | set(aid2.helps)
    return worry.needs.issubset(support_tags)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for kind_id in COOKIES:
        for recipient_id in RECIPIENTS:
            for worry_id, worry in WORRIES.items():
                for aid1_id, aid1 in AIDS.items():
                    for aid2_id, aid2 in AIDS.items():
                        if aid1_id == aid2_id:
                            continue
                        if enough_support(aid1, aid2, worry):
                            combos.append((kind_id, recipient_id, worry_id, f"{aid1_id}+{aid2_id}"))
    return combos


def predict_delivery(world: World, worry: Worry) -> dict:
    sim = world.copy()
    child = sim.get("child")
    cookie = sim.get("cookie")
    child.meters["fear_need"] = float(worry.bravery_cost)
    child.memes["fear"] = float(worry.fear)
    cookie.meters["carried"] += 1
    propagate(sim, narrate=False)
    return {
        "delivered": sim.get("cookie").meters["delivered"] >= THRESHOLD,
        "fear": sim.get("child").memes["fear"],
        "bravery": sim.get("child").memes["bravery"],
    }


def intro(world: World, child: Entity, adult: Entity, cookie_kind: CookieKind, recipient: Recipient) -> None:
    child.memes["joy"] += 1
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} and {child.pronoun('possessive')} {adult.label_word} baked a {cookie_kind.label} one rosy day. "
        f"It came out round and golden-brown, in the sweetest, steamiest way."
    )
    world.say(
        f"The cookie {cookie_kind.smell}, and {cookie_kind.shine}. "
        f"{recipient.label} {recipient.need}, so they said, \"This treat is not just yours or mine.\""
    )


def temptation(world: World, child: Entity, cookie_kind: CookieKind, recipient: Recipient) -> None:
    cookie = world.get("cookie")
    child.memes["temptation"] += 1
    cookie.meters["baked"] += 1
    world.say(
        f"{child.id} looked at the cookie and swallowed slow. \"It smells so good,\" {child.pronoun()} said. "
        f"\"Could I keep it here instead?\""
    )
    world.say(
        f"But then {child.pronoun()} remembered {recipient.label} and the reason for the bake. "
        f"A kind heart gave one gentle thump, enough to make the thought awake."
    )


def honest_choice(world: World, child: Entity, adult: Entity) -> None:
    child.memes["honesty"] += 1
    child.memes["resolve"] += 1
    world.say(
        f'"I do want the cookie," {child.id} said true. "But sharing it is the better thing to do."'
    )
    world.say(
        f'{adult.label_word.capitalize()} smiled. "That honest start is brave as well. '
        f'We tell the truth before we do the hard part, and that helps courage swell."'
    )


def obstacle(world: World, child: Entity, worry: Worry) -> None:
    child.memes["fear"] = float(worry.fear)
    child.meters["fear_need"] = float(worry.bravery_cost)
    world.say(
        f"They lifted the plate and started out, but soon they reached {worry.label}. "
        f"{worry.place_detail}, and {worry.sound}."
    )
    world.say(
        f"{child.id} took one tiny backward step. Fear fluttered up and made {child.pronoun('possessive')} knees feel small."
    )


def support(world: World, child: Entity, adult: Entity, aid1: Aid, aid2: Aid) -> None:
    child.memes["support"] = float(aid1.support + aid2.support)
    world.say(
        f"{adult.label_word.capitalize()} did not laugh and did not rush. "
        f"{adult.pronoun().capitalize()} {aid1.action}, then {aid2.action}."
    )
    world.say(
        f'"Brave does not mean never scared," {adult.label_word} said in a hush. '
        f'"Brave means kind feet keep moving on, even when the heart goes thump-thump-thush."'
    )


def carry_cookie(world: World, child: Entity) -> None:
    cookie = world.get("cookie")
    cookie.meters["carried"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} held the plate with careful hands. One step, then two, then three. "
        f"The cookie stayed warm. The child stayed kind. The path felt less scary to see."
    )


def scare_and_crack(world: World, worry: Worry) -> None:
    cookie = world.get("cookie")
    if worry.id == "bark_gate":
        cookie.meters["cracked"] += 1
        world.say(
            "At the gate, one yip made the plate give a hop, and a little edge gave a crack. "
            "But the cookie was still a cookie, and no one turned back."
        )


def deliver(world: World, child: Entity, recipient: Recipient, cookie_kind: CookieKind) -> None:
    recipient_ent = world.get("recipient")
    cookie = world.get("cookie")
    if cookie.meters["delivered"] < THRESHOLD:
        raise StoryError("The cookie never reached the recipient, so the story has no honest ending.")
    crack_line = ""
    if cookie.meters["cracked"] >= THRESHOLD:
        crack_line = f" Even with its little crack and a sprinkle of {cookie_kind.crumb}, it still looked made with care."
    world.say(
        f"At last they reached {recipient.place}, where {recipient.label} opened the door.{crack_line}"
    )
    world.say(
        f'{child.id} held up the cookie and said, "This one is for you." '
        f"{recipient.thanks}."
    )
    recipient_ent.memes["gratitude"] += 1


def ending(world: World, child: Entity, adult: Entity) -> None:
    world.say(
        f"On the walk back home, the night felt mild, and brave felt less like a mountain. "
        f"It felt like truth, and kindly feet, and courage pouring like a fountain."
    )
    world.say(
        f"Later, {adult.label_word} baked another small cookie just for {child.id}. "
        f"This time the first sweet bite tasted bright, because sharing had made the heart more wide."
    )


def tell(
    cookie_kind: CookieKind,
    recipient: Recipient,
    worry: Worry,
    aid1: Aid,
    aid2: Aid,
    *,
    child_name: str = "Lily",
    child_gender: str = "girl",
    adult_type: str = "mother",
    trait: str = "kind",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[trait],
        attrs={"trait": trait},
    ))
    adult = world.add(Entity(
        id="Adult",
        kind="character",
        type=adult_type,
        label="the adult",
        role="adult",
        attrs={},
    ))
    cookie = world.add(Entity(
        id="cookie",
        kind="thing",
        type="cookie",
        label=cookie_kind.label,
        role="gift",
        attrs={"kind": cookie_kind.id},
    ))
    recipient_ent = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient.id,
        label=recipient.label,
        role="recipient",
        attrs={"relation_word": recipient.relation_word},
    ))

    world.facts.update(
        cookie_kind=cookie_kind,
        recipient_cfg=recipient,
        worry_cfg=worry,
        aids=(aid1, aid2),
        child=child,
        adult=adult,
        recipient=recipient_ent,
    )

    intro(world, child, adult, cookie_kind, recipient)
    world.para()
    temptation(world, child, cookie_kind, recipient)
    honest_choice(world, child, adult)
    world.para()
    obstacle(world, child, worry)
    support(world, child, adult, aid1, aid2)

    pred = predict_delivery(world, worry)
    world.facts["predicted_delivery"] = pred["delivered"]
    world.facts["predicted_bravery"] = pred["bravery"]

    carry_cookie(world, child)
    scare_and_crack(world, worry)
    propagate(world, narrate=False)

    world.para()
    deliver(world, child, recipient, cookie_kind)
    ending(world, child, adult)

    world.facts.update(
        delivered=world.get("cookie").meters["delivered"] >= THRESHOLD,
        cracked=world.get("cookie").meters["cracked"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD,
        honest=child.memes["honesty"] >= THRESHOLD,
        learned=child.memes["lesson"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    kind: str
    recipient: str
    worry: str
    aid1: str
    aid2: str
    child_name: str
    child_gender: str
    adult: str
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
    "cookie": [
        ("What is a cookie?",
         "A cookie is a small sweet baked treat. It is usually made from dough and cooked until it is warm and firm."),
    ],
    "baking": [
        ("Why does a cookie smell good when it is baking?",
         "Heat wakes up the sweet smells in the dough, like sugar and spice. That is why the kitchen can smell cozy and warm."),
    ],
    "sharing": [
        ("Why is sharing a kind thing to do?",
         "Sharing means you choose to let someone else have part of a good thing. It shows you care about how another person feels."),
    ],
    "bravery": [
        ("What is bravery?",
         "Bravery is doing the right thing even when you feel scared. A brave person can have a shaky heart and still take a kind step."),
    ],
    "honesty": [
        ("Why can telling the truth be brave?",
         "Telling the truth can feel hard when you want something else or worry about what people will say. It is brave because you choose what is right instead of what is easiest."),
    ],
    "light": [
        ("Why can a light help when a place feels scary?",
         "A light helps you see what is around you. When you can see better, your body often feels calmer too."),
    ],
    "hand": [
        ("Why does holding a grown-up's hand help?",
         "A steady hand can make you feel safe and supported. It reminds you that you do not have to do a hard thing all alone."),
    ],
    "song": [
        ("How can a song help when you feel afraid?",
         "A soft song gives your mind something gentle to follow. The steady sound can help your breathing and make each step feel easier."),
    ],
    "tray": [
        ("Why use a tray to carry food?",
         "A tray gives the food a flat place to rest. That makes it easier to carry carefully without dropping or tipping it."),
    ],
    "dark": [
        ("Why can a dark hallway feel scary?",
         "In a dark hallway, you cannot see as much, so your imagination may fill in the missing parts. That can make an ordinary place feel bigger or stranger."),
    ],
    "dog": [
        ("Why can a barking dog surprise people?",
         "A sudden bark is loud and quick, so it can startle your body. Even a small dog can sound big when you are not expecting the noise."),
    ],
    "wind": [
        ("Why do windy steps feel tricky?",
         "Wind can tug at clothes and make you feel wobbly. Steps already need careful feet, so the extra moving air can feel harder."),
    ],
}
KNOWLEDGE_ORDER = [
    "cookie",
    "baking",
    "sharing",
    "bravery",
    "honesty",
    "light",
    "hand",
    "song",
    "tray",
    "dark",
    "dog",
    "wind",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    recipient = f["recipient_cfg"]
    cookie_kind = f["cookie_kind"]
    worry = f["worry_cfg"]
    aid1, aid2 = f["aids"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the word "cookie" and teaches bravery through kindness.',
        f"Tell a gentle rhyming story where {child.id} must carry a {cookie_kind.label} to {recipient.label} even though {worry.label} feels scary, and two simple kinds of help make the brave choice possible.",
        f'Write a child-facing poem-story about moral courage where a child admits wanting a cookie, chooses to share it, and learns that bravery can sound like truth and look like small steps.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    recipient_cfg = f["recipient_cfg"]
    cookie_kind = f["cookie_kind"]
    worry = f["worry_cfg"]
    aid1, aid2 = f["aids"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {adult.label_word}, and {recipient_cfg.label}. "
            f"They made one special {cookie_kind.label} for someone else.",
        ),
        (
            "Why did the cookie matter in this story?",
            f"The cookie was not just a snack. It was meant as a kind gift for {recipient_cfg.label}, who {recipient_cfg.need}.",
        ),
        (
            f"Did {child.id} want to keep the cookie?",
            f"Yes. {child.id} said the cookie smelled so good and admitted wanting it. "
            f"Telling the truth about that wish was the first brave thing {child.pronoun()} did.",
        ),
        (
            f"What made the trip feel scary?",
            f"The hard part was {worry.label}. {worry.place_detail}, and {worry.sound}, so the path felt bigger and scarier than before.",
        ),
        (
            f"How did the grown-up help {child.id} be brave?",
            f"{adult.label_word.capitalize()} used {aid1.phrase} and {aid2.phrase} to help. "
            f"That support made the scary part feel manageable, so bravery could grow into action.",
        ),
    ]
    if f.get("delivered"):
        answer = (
            f"{child.id} carried the cookie all the way to {recipient_cfg.label} and gave it away. "
            f"That was brave because {child.pronoun()} kept going even while feeling scared, and kind because the cookie was for someone else's comfort."
        )
        qa.append(("What brave thing did the child do?", answer))
    if f.get("cracked"):
        qa.append((
            "Did anything go a little wrong on the way?",
            f"Yes. The cookie got a small crack when the sudden moment made the plate hop. "
            f"But the child did not give up, so the kindness still reached the door.",
        ))
    qa.append((
        "What is the moral of the story?",
        "The story teaches that bravery is not only big roaring courage. It can be telling the truth, accepting help, and taking kind little steps even when your heart feels nervous.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"cookie", "baking", "sharing", "bravery", "honesty"}
    worry = f["worry_cfg"]
    aid1, aid2 = f["aids"]
    tags |= set(worry.tags)
    tags |= set(aid1.tags)
    tags |= set(aid2.tags)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        kind="chocolate",
        recipient="grandma",
        worry="dark_hall",
        aid1="lantern",
        aid2="hand_hold",
        child_name="Lily",
        child_gender="girl",
        adult="mother",
        trait="kind",
    ),
    StoryParams(
        kind="ginger",
        recipient="neighbor",
        worry="bark_gate",
        aid1="song",
        aid2="hand_hold",
        child_name="Ben",
        child_gender="boy",
        adult="father",
        trait="thoughtful",
    ),
    StoryParams(
        kind="oatmeal",
        recipient="teacher",
        worry="windy_steps",
        aid1="tray",
        aid2="hand_hold",
        child_name="Nora",
        child_gender="girl",
        adult="mother",
        trait="careful",
    ),
    StoryParams(
        kind="chocolate",
        recipient="neighbor",
        worry="quiet_evening",
        aid1="lantern",
        aid2="song",
        child_name="Leo",
        child_gender="boy",
        adult="father",
        trait="gentle",
    ),
]


def explain_combo(worry: Worry, aid1: Aid, aid2: Aid) -> str:
    have = sorted(set(aid1.helps) | set(aid2.helps))
    need = sorted(worry.needs)
    return (
        f"(No story: {worry.label} needs support for {need}, but the chosen aids only cover {have}. "
        f"Pick two aids that honestly help with the obstacle.)"
    )


ASP_RULES = r"""
need(W,N) :- worry(W), worry_needs(W,N).
supports(A,N) :- aid(A), aid_helps(A,N).

enough_support(W,A1,A2) :- worry(W), aid(A1), aid(A2), A1 != A2,
                           not missing_need(W,A1,A2).
missing_need(W,A1,A2) :- need(W,N), not supports(A1,N), not supports(A2,N).

valid(K,R,W,A1,A2) :- cookie_kind(K), recipient(R), enough_support(W,A1,A2).

fear_need(B) :- chosen_worry(W), bravery_cost(W,B).
support_total(S1 + S2) :- chosen_aid1(A1), chosen_aid2(A2), support(A1,S1), support(A2,S2).
delivered :- support_total(S), fear_need(B), S >= B.
outcome(delivered) :- delivered.
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for kind_id in COOKIES:
        lines.append(asp.fact("cookie_kind", kind_id))
    for recipient_id in RECIPIENTS:
        lines.append(asp.fact("recipient", recipient_id))
    for worry_id, worry in WORRIES.items():
        lines.append(asp.fact("worry", worry_id))
        lines.append(asp.fact("bravery_cost", worry_id, worry.bravery_cost))
        for need in sorted(worry.needs):
            lines.append(asp.fact("worry_needs", worry_id, need))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("support", aid_id, aid.support))
        for help_tag in sorted(aid.helps):
            lines.append(asp.fact("aid_helps", aid_id, help_tag))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_worry", params.worry),
        asp.fact("chosen_aid1", params.aid1),
        asp.fact("chosen_aid2", params.aid2),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "none"


def outcome_of(params: StoryParams) -> str:
    worry = WORRIES[params.worry]
    aid1 = AIDS[params.aid1]
    aid2 = AIDS[params.aid2]
    return "delivered" if enough_support(aid1=aid1, aid2=aid2, worry=worry) else "none"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"resolve_params unexpectedly failed for seed {seed}")
            break
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
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke-tested normal generation.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a cookie, kindness, and bravery in a rhyming tale."
    )
    ap.add_argument("--kind", choices=COOKIES)
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--worry", choices=WORRIES)
    ap.add_argument("--aid1", choices=AIDS)
    ap.add_argument("--aid2", choices=AIDS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.aid1 and args.aid2 and args.aid1 == args.aid2:
        raise StoryError("(No story: aid1 and aid2 must be different so they can provide two kinds of help.)")
    if args.worry and args.aid1 and args.aid2:
        worry = WORRIES[args.worry]
        aid1 = AIDS[args.aid1]
        aid2 = AIDS[args.aid2]
        if not enough_support(aid1=aid1, aid2=aid2, worry=worry):
            raise StoryError(explain_combo(worry, aid1, aid2))

    combos = [
        combo for combo in valid_combos()
        if (args.kind is None or combo[0] == args.kind)
        and (args.recipient is None or combo[1] == args.recipient)
        and (args.worry is None or combo[2] == args.worry)
    ]
    if args.aid1 is not None:
        combos = [combo for combo in combos if combo[3].split("+")[0] == args.aid1 or combo[3].split("+")[1] == args.aid1]
    if args.aid2 is not None:
        combos = [combo for combo in combos if combo[3].split("+")[0] == args.aid2 or combo[3].split("+")[1] == args.aid2]

    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    kind_id, recipient_id, worry_id, aid_pair = rng.choice(sorted(combos))
    first, second = aid_pair.split("+")
    if args.aid1 and args.aid2:
        aid1_id, aid2_id = args.aid1, args.aid2
    elif args.aid1:
        remaining = second if first == args.aid1 else first
        aid1_id, aid2_id = args.aid1, remaining
    elif args.aid2:
        remaining = second if first == args.aid2 else first
        aid1_id, aid2_id = remaining, args.aid2
    else:
        aid1_id, aid2_id = first, second

    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(name_pool)
    adult = args.adult or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    return StoryParams(
        kind=kind_id,
        recipient=recipient_id,
        worry=worry_id,
        aid1=aid1_id,
        aid2=aid2_id,
        child_name=child_name,
        child_gender=gender,
        adult=adult,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.kind not in COOKIES:
        raise StoryError(f"(No story: unknown kind '{params.kind}'.)")
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(No story: unknown recipient '{params.recipient}'.)")
    if params.worry not in WORRIES:
        raise StoryError(f"(No story: unknown worry '{params.worry}'.)")
    if params.aid1 not in AIDS or params.aid2 not in AIDS:
        raise StoryError("(No story: one of the chosen aids is unknown.)")
    if params.aid1 == params.aid2:
        raise StoryError("(No story: aid1 and aid2 must be different.)")
    worry = WORRIES[params.worry]
    aid1 = AIDS[params.aid1]
    aid2 = AIDS[params.aid2]
    if not enough_support(aid1=aid1, aid2=aid2, worry=worry):
        raise StoryError(explain_combo(worry, aid1, aid2))

    world = tell(
        cookie_kind=COOKIES[params.kind],
        recipient=RECIPIENTS[params.recipient],
        worry=worry,
        aid1=aid1,
        aid2=aid2,
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_type=params.adult,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (kind, recipient, worry, aid1, aid2) combos:\n")
        for kind_id, recipient_id, worry_id, aid1_id, aid2_id in combos:
            print(f"  {kind_id:10} {recipient_id:9} {worry_id:13} {aid1_id:10} {aid2_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.kind} / {p.recipient} / {p.worry} ({p.aid1}+{p.aid2})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
