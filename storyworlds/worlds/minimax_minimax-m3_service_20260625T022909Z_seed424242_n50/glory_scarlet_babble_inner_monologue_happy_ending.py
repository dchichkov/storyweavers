#!/usr/bin/env python3
"""
storyworlds/worlds/glory_scarlet_babble_inner_monologue_happy_ending.py
======================================================================

A standalone *story world* sketch built from a generated seed.

Seed words:
    glory, scarlet, babble
Features:
    Inner Monologue, Happy Ending, Reconciliation
Style:
    Rhyming Story

Initial story (used to build the world model):
---
Once upon a sunlit garden day, a little fox kit named Pip found a scarlet
ribbon tangled in the holly. The ribbon glimmered like a tiny flag of glory
caught in a bramble, and Pip's paws itched to keep it forever. But the
ribbon belonged to the garden's old clock-tower bell-rope, and the bell could
not ring its noon without it.

Pip tugged and tugged, and a happy babble of birds watched from the high
lime tree. Inside Pip's head, a small worried voice whispered, "If I keep the
ribbon, the bell will be quiet, and everyone will miss their noon." Pip
pouted, and the scarlet tail-end fell still.

Then old Mrs. Wren, the gardener, came down the path. "Oh dear," she said,
"the bell-rope has wandered off again. The villagers need to hear their
noon." Pip looked at the ribbon, then at Mrs. Wren, and thought, "Maybe I
can share the glory with her."

Pip ran over and offered the scarlet ribbon back. Mrs. Wren smiled and
said, "Let's tie it together -- you hold one end at the garden gate so all
the passersby can see, and I will ring the bell at noon." Pip's heart
lifted, the babble of birds came back, and at noon the bell sang clear over
the garden. Pip and Mrs. Wren bowed to each other under the holly, and the
scarlet ribbon fluttered like a flag of small, well-shared glory.

This world therefore models:
    * a small garden place where an object of beauty is also an object of need
    * the child's inner monologue (a worried inner voice, then a kind inner voice)
    * a happy ending through reconciliation (sharing, not surrendering)
    * prose that rhymes at the end of clauses -- a "rhyming story" style
    * a state machine with physical meters (the ribbon's location) and
      emotional memes (the child's pride, worry, joy)
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
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"mother", "mom", "woman", "gardener", "wren", "girl"}
        male = {"father", "dad", "man", "boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type == "fox":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if getattr(self, "plural", False) else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "gardener": "the gardener"}.get(
            self.type, self.type
        )


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the garden"
    weather: str = "sunny"
    affords: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    """The pretty object the hero finds -- both prized and needed by someone."""
    id: str
    label: str
    phrase: str
    color: str             # the scarlet-like color word
    precious: str          # what makes it pretty (glory-like quality)
    needed_for: str        # what it does for the community
    owner_role: str        # "gardener", "watchman", "sexton"
    region: str = "anywhere"


@dataclass
class Hero:
    id: str
    type: str              # "fox", "girl", "boy"
    label: str             # "the fox kit", "the girl"
    name: str
    traits: list[str]


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.last_rhyme: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_held_pride(world: World) -> list[str]:
    """When the hero holds the treasure, they feel pride (glory-by-keeping)."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["held"] < THRESHOLD:
            continue
        if actor.memes["pride"] >= THRESHOLD:
            continue
        sig = ("pride", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] += 1
    return out


def _r_inner_worry(world: World) -> list[str]:
    """Once the hero knows the treasure is needed, an inner worried voice fires."""
    for actor in world.characters():
        if actor.memes["knew_needed"] < THRESHOLD:
            continue
        if actor.memes["inner_worry"] >= THRESHOLD:
            continue
        sig = ("inner_worry", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["inner_worry"] += 1
        return ["__inner_worry__"]
    return []


def _r_inner_kind(world: World) -> list[str]:
    """When worry + the helper are both present, a kind inner voice fires."""
    for actor in world.characters():
        if actor.memes["inner_worry"] < THRESHOLD:
            continue
        if actor.memes["met_helper"] < THRESHOLD:
            continue
        if actor.memes["inner_kind"] >= THRESHOLD:
            continue
        sig = ("inner_kind", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["inner_kind"] += 1
        return ["__inner_kind__"]
    return []


def _r_reconcile(world: World) -> list[str]:
    """Holding treasure + offered to share -> reconciliation meme rises."""
    for actor in world.characters():
        if actor.memes["held"] < THRESHOLD:
            continue
        if actor.memes["shared"] < THRESHOLD:
            continue
        if actor.memes["reconciled"] >= THRESHOLD:
            continue
        sig = ("reconciled", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["reconciled"] += 1
        actor.memes["joy"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="held_pride", tag="emotional", apply=_r_held_pride),
    Rule(name="inner_worry", tag="social", apply=_r_inner_worry),
    Rule(name="inner_kind", tag="social", apply=_r_inner_kind),
    Rule(name="reconcile", tag="emotional", apply=_r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def treasure_fits(treasure: Treasure, setting: Setting) -> bool:
    return True  # all current combos fit


def valid_combos() -> list[tuple[str, str]]:
    """(treasure, setting) pairs that pass the constraint gate."""
    out = []
    for s_id, s in SETTINGS.items():
        for t_id, t in TREASURES.items():
            if treasure_fits(t, s):
                out.append((s_id, t_id))
    return out


# ---------------------------------------------------------------------------
# Verbs (story beats)
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity, setting: Setting) -> None:
    trait = next((t for t in hero.traits if t != "little"), "playful")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"Once upon a {setting.weather} day in {setting.place}, "
        f"{hero.name} was a {desc} who noticed every pretty thing."
    )


def discovers(world: World, hero: Entity, treasure: Entity, t_def: Treasure) -> None:
    hero.memes["desire"] += 1
    hero.memes["held"] += 1
    world.facts["treasure_id"] = treasure.id
    world.facts["hero_id"] = hero.id
    world.facts["setting_id"] = world.setting.id if hasattr(world.setting, "id") else ""
    world.say(
        f"One morning {hero.name} found {t_def.phrase} tangled in the hedge, "
        f"shining a brave {t_def.color} like a flag of small {t_def.precious}."
    )


def babble_birds(world: World, treasure: Entity) -> None:
    """A happy babble of birds watches from above -- the seed-word 'babble'."""
    world.say(
        f"A happy babble of birds watched from the lime tree, "
        f"and {treasure.label} fluttered at the bramble's end."
    )


def inner_monologue_worry(world: World, hero: Entity, t_def: Treasure) -> None:
    """First inner voice: worried about keeping something that is needed."""
    hero.memes["knew_needed"] += 1
    propagate(world)
    if hero.memes["inner_worry"] >= THRESHOLD:
        sub = hero.pronoun("subject").capitalize()
        obj = hero.pronoun("object")
        world.say(
            f"Inside {hero.name}'s head, a small worried voice whispered, "
            f'"If I keep this, the {t_def.needed_for} will be quiet, '
            f'and everyone will miss their {t_def.needed_for}." '
            f"{sub} pouted, and the {t_def.color} tail-end fell still."
        )


def helper_arrives(world: World, helper: Entity, t_def: Treasure) -> None:
    for actor in world.characters():
        actor.memes["met_helper"] += 1
    helper.memes["arrived"] += 1
    world.say(
        f"Then old {helper.label_word} came down the path, looked at the "
        f"hedge, and sighed. "
        f'"Oh dear," {helper.pronoun("subject")} said, '
        f'"the {t_def.needed_for} has wandered off again, '
        f'and the village needs to hear it."'
    )


def inner_monologue_kind(world: World, hero: Entity, t_def: Treasure) -> None:
    """Second inner voice: a kind thought about sharing, not just surrender."""
    propagate(world)
    if hero.memes["inner_kind"] >= THRESHOLD:
        sub = hero.pronoun("subject").capitalize()
        world.say(
            f"Then a second small voice, a kind one this time, answered back: "
            f'"Maybe I do not have to give up the {t_def.precious} to do the right thing. '
            f'Maybe I can share the {t_def.precious} with {t_def.owner_role}, '
            f'and we can both be glad."'
        )
        sub = hero.pronoun("subject")
        world.say(f"{sub} felt the worry soften, just a little.")


def offer(world: World, hero: Entity, helper: Entity, treasure: Entity,
          t_def: Treasure) -> None:
    hero.memes["offered"] += 1
    treasure.memes["returned"] += 1
    world.say(
        f"{hero.name} ran over and offered {t_def.phrase} back to "
        f"{helper.label_word}, who smiled a wide and gentle smile."
    )


def reconcile(world: World, hero: Entity, helper: Entity, t_def: Treasure) -> None:
    """Reconciliation beat: a SHARED plan -- not surrender, not surrender-to-grab."""
    hero.memes["shared"] += 1
    helper.memes["shared"] += 1
    propagate(world)
    world.say(
        f'"Let us tie it together," {helper.label_word} said. '
        f'"You shall hold one end at the gate so all the passersby can see, '
        f'and I shall keep the other for the {t_def.needed_for} at noon."'
    )


def happy_ending(world: World, hero: Entity, helper: Entity, t_def: Treasure,
                 setting: Setting) -> None:
    """Happy Ending: image that proves the world changed -- bell rings,
    bow to each other, the scarlet ribbon flutters like shared glory."""
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At noon the {t_def.needed_for} sang clear over {setting.place}, "
        f"and {hero.name} and {helper.label_word} bowed to each other "
        f"under the hedge, both grinning."
    )
    world.say(
        f"The {t_def.color} {treasure.label if 'treasure' in str(treasure.id) else 'ribbon'} "
        f"fluttered like a flag of well-shared {t_def.precious}, "
        f"and the birds began their happy babble once more. "
        f"And so the {t_def.precious} belonged to the whole garden that day."
    )


def tell(setting: Setting, t_def: Treasure, hero: Hero,
         helper_name: str = "Mrs. Wren", helper_type: str = "gardener") -> World:
    world = World(setting)

    hero_e = world.add(Entity(
        id=hero.name, kind="character", type=hero.type, label=hero.label,
        traits=["little"] + hero.traits,
    ))
    helper = world.add(Entity(
        id=helper_name, kind="character", type=helper_type, label=helper_name,
    ))
    treasure = world.add(Entity(
        id="treasure", type="ribbon", label=t_def.label, phrase=t_def.phrase,
        owner=helper.id, region=t_def.region,
    ))

    world.para()
    introduce(world, hero_e, setting)
    discovers(world, hero_e, treasure, t_def)
    babble_birds(world, treasure)

    world.para()
    inner_monologue_worry(world, hero_e, t_def)
    helper_arrives(world, helper, t_def)

    world.para()
    inner_monologue_kind(world, hero_e, t_def)
    offer(world, hero_e, helper, treasure, t_def)
    reconcile(world, hero_e, helper, t_def)
    happy_ending(world, hero_e, helper, t_def, setting)

    world.facts.update(
        hero=hero_e, helper=helper, treasure=treasure,
        treasure_def=t_def, setting=setting,
        reconciled=hero_e.memes["reconciled"] >= THRESHOLD,
        worry=hero_e.memes["inner_worry"] >= THRESHOLD,
        kind=hero_e.memes["inner_kind"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(id="garden", place="the garden", weather="sunny",
                      affords={"ribbon"}),
    "village": Setting(id="village", place="the village green", weather="sunny",
                       affords={"ribbon"}),
    "orchard": Setting(id="orchard", place="the apple orchard", weather="sunny",
                       affords={"ribbon"}),
}

TREASURES = {
    "ribbon": Treasure(
        id="ribbon",
        label="ribbon",
        phrase="a long scarlet ribbon",
        color="scarlet",
        precious="glory",
        needed_for="noon bell",
        owner_role="gardener",
        region="anywhere",
    ),
    "bellrope": Treasure(
        id="bellrope",
        label="bell-rope",
        phrase="a braided scarlet bell-rope",
        color="scarlet",
        precious="glory",
        needed_for="tower bell",
        owner_role="sexton",
        region="anywhere",
    ),
    "streamer": Treasure(
        id="streamer",
        label="streamer",
        phrase="a long scarlet festival streamer",
        color="scarlet",
        precious="glory",
        needed_for="maypole dance",
        owner_role="watchman",
        region="anywhere",
    ),
}

HEROES = [
    Hero(id="Pip", type="fox", label="the fox kit", name="Pip",
         traits=["playful", "curious"]),
    Hero(id="Mia", type="girl", label="the girl", name="Mia",
         traits=["cheerful", "stubborn"]),
    Hero(id="Ben", type="boy", label="the boy", name="Ben",
         traits=["lively", "spirited"]),
]

HELPERS = [
    {"name": "Mrs. Wren", "type": "gardener", "label": "the gardener"},
    {"name": "Mr. Bell", "type": "sexton", "label": "the sexton"},
    {"name": "Old Tom", "type": "watchman", "label": "the watchman"},
]

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Ben", "Tim", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
FOX_NAMES = ["Pip", "Rusty", "Cinder", "Bram", "Fennel"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]


# ---------------------------------------------------------------------------
# Per-world parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    treasure: str
    name: str
    hero_type: str
    helper_name: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "glory": [("What does glory mean?",
               "Glory means a bright, beautiful feeling of doing something "
               "wonderful that other people can see and share.")],
    "scarlet": [("What color is scarlet?",
                 "Scarlet is a bright, deep red color, like a ripe berry or a "
                 "cardinal's feather.")],
    "babble": [("What does a babble of birds sound like?",
                "A babble of birds is the cheerful sound of many birds "
                "chattering and singing all at once, like a busy playground of "
                "tiny voices.")],
    "ribbon": [("Why do people tie ribbons on things?",
                "People tie ribbons on things to mark them as special, to "
                "celebrate, or to make them easy to see and hold.")],
    "bell": [("Why do villages ring bells at noon?",
              "Villages ring bells at noon to mark the middle of the day so "
              "everyone knows the time, even from far away.")],
    "sharing": [("What does it mean to share?",
                 "To share means to let someone else use or enjoy something "
                 "with you, so you both get a little of the good thing.")],
    "worry": [("Why do we worry about our choices?",
               "We worry because we want to do the right thing, and thinking "
               "about what could happen helps us choose well.")],
    "kind": [("What is a kind thought?",
              "A kind thought is a small idea in your head that wants the "
              "best for someone else, not just for yourself.")],
    "fox": [("What is a fox kit?",
             "A fox kit is a baby fox. Foxes are clever animals with red-brown "
             "fur and bushy tails.")],
}
KNOWLEDGE_ORDER = ["glory", "scarlet", "babble", "ribbon", "bell",
                   "sharing", "worry", "kind", "fox"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, tdef = f["hero"], f["treasure_def"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old on the theme '
        f'"a small glory to share" that includes the word "{tdef.color}".',
        f'Tell a gentle rhyming tale where a little {hero.type} named '
        f'{hero.name} finds {tdef.phrase} and learns to share the {tdef.precious} '
        f'with the {tdef.owner_role}, ending in a happy bow.',
        f'Write a simple rhyming story using the noun "babble" and the word '
        f'"{tdef.precious}" that ends with a small shared triumph.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, treasure, tdef = f["hero"], f["helper"], f["treasure"], f["treasure_def"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.name} finds {tdef.phrase} "
                f"at {place}?"
            ),
            answer=(
                f"It is about a little {hero.type} named {hero.name} and "
                f"{helper.label_word}. They meet at {place} on a sunny day "
                f"over a {tdef.color} {treasure.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.name} find tangled in the hedge at {place}?"
            ),
            answer=(
                f"{hero.name.capitalize()} found {tdef.phrase} tangled in the "
                f"hedge, shining a brave {tdef.color} like a flag of small "
                f"{tdef.precious}."
            ),
        ),
        QAItem(
            question=(
                f"What did the small worried voice inside {hero.name} say "
                f"about keeping the {tdef.color} {treasure.label}?"
            ),
            answer=(
                f"The worried voice whispered that if {hero.name} kept it, "
                f"the {tdef.needed_for} would be quiet, and everyone would "
                f"miss their {tdef.needed_for}."
            ),
        ),
    ]
    if f.get("kind"):
        qa.append(QAItem(
            question=(
                f"What was the second small voice inside {hero.name} about "
                f"the {tdef.precious} {treasure.label}?"
            ),
            answer=(
                f"The second, kind voice said that maybe {sub} did not have to "
                f"give up the {tdef.precious} to do the right thing -- maybe "
                f"{sub} could share it with the {tdef.owner_role}, and they "
                f"could both be glad."
            ),
        ))
    if f.get("reconciled"):
        qa.append(QAItem(
            question=(
                f"How did {hero.name} and {helper.label_word} share the "
                f"{tdef.color} {treasure.label} at {place}?"
            ),
            answer=(
                f"They agreed to tie it together: {hero.name} held one end at "
                f"the gate so all the passersby could see, and {helper.label_word} "
                f"kept the other end for the {tdef.needed_for} at noon. "
                f"The plan let them both have a piece of the {tdef.precious}."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did the rhyming story show that {hero.name} and "
                f"{helper.label_word} were happy at the end?"
            ),
            answer=(
                f"At noon the {tdef.needed_for} sang clear over {place}, and "
                f"{hero.name} and {helper.label_word} bowed to each other "
                f"under the hedge, both grinning. The {tdef.color} {treasure.label} "
                f"fluttered like a flag of well-shared {tdef.precious}, and the "
                f"happy babble of birds came back."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tdef = f["treasure_def"]
    tags = {"glory", "scarlet", "babble", "ribbon", "sharing"}
    if tdef.id == "bellrope":
        tags.add("bell")
    if tdef.id == "streamer":
        tags.add("kind")
    if f["hero"].type == "fox":
        tags.add("fox")
    if f.get("worry"):
        tags.add("worry")
    if f.get("kind"):
        tags.add("kind")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="garden",
        treasure="ribbon",
        name="Pip",
        hero_type="fox",
        helper_name="Mrs. Wren",
        helper_type="gardener",
        trait="playful",
    ),
    StoryParams(
        place="village",
        treasure="bellrope",
        name="Ben",
        hero_type="boy",
        helper_name="Mr. Bell",
        helper_type="sexton",
        trait="curious",
    ),
    StoryParams(
        place="orchard",
        treasure="streamer",
        name="Mia",
        hero_type="girl",
        helper_name="Old Tom",
        helper_type="watchman",
        trait="cheerful",
    ),
]


def explain_rejection(treasure: Treasure, setting: Setting) -> str:
    return (f"(No story: treasure '{treasure.id}' does not fit setting '{setting.id}'.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A treasure fits a setting when the setting affords the treasure's id.
fits(Setting, Treasure) :- setting(Setting), affords(Setting, Treasure),
                            treasure(Treasure).

% A hero-kind fits a hero-type.
fits_hero(Type, Kind) :- hero_type(Type), hero_kind(Kind).

% A story is valid when place+treasure fit AND helper is allowed.
valid(Place, Treasure, Type, Helper) :-
    fits(Place, Treasure), fits_hero(Type, _),
    helper_allowed(Helper).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_color", tid, t.color))
        lines.append(asp.fact("treasure_precious", tid, t.precious))
        lines.append(asp.fact("treasure_needed", tid, t.needed_for))
        lines.append(asp.fact("treasure_owner", tid, t.owner_role))
    for h in HEROES:
        lines.append(asp.fact("hero_type", h.type))
    for hp in HELPERS:
        lines.append(asp.fact("helper_allowed", hp["name"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show fits/2."))
    return sorted(set(asp.atoms(model, "fits")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: glory, scarlet, babble; inner monologue, "
                    "happy ending, reconciliation; rhyming-story style.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--treasure", choices=list(TREASURES))
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["fox", "girl", "boy"])
    ap.add_argument("--helper-name")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.treasure is None or c[1] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, treasure_id = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["fox", "girl", "boy"])
    if hero_type == "fox":
        name = args.name or rng.choice(FOX_NAMES)
    elif hero_type == "girl":
        name = args.name or rng.choice(GIRL_NAMES)
    else:
        name = args.name or rng.choice(BOY_NAMES)
    helper = next(h for h in HELPERS if h["type"] == TREASURES[treasure_id].owner_role)
    helper_name = args.helper_name or helper["name"]
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        treasure=treasure_id,
        name=name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper["type"],
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    hero = Hero(id=params.name, type=params.hero_type,
                label={"fox": "the fox kit", "girl": "the girl", "boy": "the boy"}[params.hero_type],
                name=params.name, traits=[params.trait])
    world = tell(SETTINGS[params.place], TREASURES[params.treasure], hero,
                 helper_name=params.helper_name, helper_type=params.helper_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, treasure) combos:\n")
        for place, treasure in triples:
            print(f"  {place:9} {treasure:10}")
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
            header = f"### {p.name}: {p.treasure} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
