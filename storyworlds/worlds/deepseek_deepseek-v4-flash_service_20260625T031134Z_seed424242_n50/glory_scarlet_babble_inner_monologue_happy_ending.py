#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50/glory_scarlet_babble_inner_monologue_happy_ending.py
==============================================================================================================

A standalone story world for a rhyming tale about a little scarlet bird who learns to
find glory in quiet listening rather than loud babble, told with inner monologue,
reconciliation, and a happy ending.

Initial story (used to build a world model):
---
Once upon a time, in a bright green tree,
Lived a little scarlet bird, as bright as can be.
His name was Pip, and he loved to babble all day,
He chirped and he chattered, come what may.
"I am the greatest! I sing the best song!
My scarlet feathers make me so strong!"
Pip would shout from the highest limb,
Making all the other creatures feel dim.

One day, wise old Owl perched on a branch near,
And heard Pip's babble loud and clear.
"Dear little Pip," said Owl with a sigh,
"Your babble is noise, not a lullaby.
Glory is earned by those who can listen,
Not by those who just babble and glisten."
Pip felt a pang, a sting in his chest,
He flew to his nest, feeling truly distressed.

Tears fell like rain on his scarlet chest,
He whispered to himself, "Am I just a pest?
All my loud babble, my glorious song,
Was it so very, very wrong?"
His heart felt heavy, his feathers drooped low,
He wanted to change, but he didn't know how.
He sat in the dark, and in the quiet he found,
A different kind of sound underground.

The next day, Pip flew to Owl with a bow,
"I'm sorry for my babble, I see it now.
Can you teach me, Owl, to listen with care?
To trade all my glory for a friendship that's fair?"
Owl smiled and said, "The first step is begun,
For glory is found when the babble is done."
And from that day on, Pip chirped soft and low,
Finding joy in the quiet, letting his friendships grow.

Causal state updates:
---
    actor babbles (loud speech)    -> actor.volume += 1  ; actor.pride += 1
                                     (onlookers lose interest) ; actor.isolation += 1
    actor hears wise counsel       -> actor.regret += 1  ; actor.pride -= 1
    actor retreats to nest         -> actor.sadness += 1 ; actor.inner_monologue_active = True
    actor reflects (inner monologue) -> actor.understanding += 1  ; actor.sadness -= 1
    actor apologizes               -> actor.reconciliation += 1  ; actor.humility += 1
    actor listens quietly          -> actor.volume -= 1  ; actor.friendship += 1
                                     ; actor.joy += 1 ; actor.isolation -= 1
Scripted social/emotional beats:
---
    loud babble attracts negative attention -> onlookers leave
    wise elder offers guidance              -> actor feels shame, then hope
    inner monologue of regret               -> actor decides to change
    apology and reconciliation              -> tension resolved, friendships restored
    quiet listening rewarded                -> true glory found in connection
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
MESS_KINDS = {"loud", "sad", "prideful"}
REGIONS = {"voice", "heart", "mind"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bird", "owl", "finch", "robin"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the tree"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Character:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"bird"})


@dataclass
class Lesson:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}
        self.inner_monologue_active: bool = False
        self.reconciliation_achieved: bool = False

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
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.inner_monologue_active = self.inner_monologue_active
        clone.reconciliation_achieved = self.reconciliation_achieved
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


def _r_babble_effect(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["loud"] < THRESHOLD:
            continue
        sig = ("babble", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["pride"] += 1
        actor.memes["isolation"] += 1
        out.append(f"{actor.pronoun('possessive').capitalize()} loud babble made the others fly away.")
    return out


def _r_counsel_effect(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["received_counsel"] < THRESHOLD:
            continue
        sig = ("counsel", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["regret"] += 1
        actor.memes["pride"] -= 1
        out.append("__regret__")
    return out


def _r_reflection(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["retreated"] < THRESHOLD:
            continue
        sig = ("reflect", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.inner_monologue_active = True
        actor.memes["understanding"] += 1
        actor.memes["sadness"] -= 1
        out.append("__inner_monologue__")
    return out


def _r_apology(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["apologized"] < THRESHOLD:
            continue
        sig = ("apology", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["reconciliation"] += 1
        actor.memes["humility"] += 1
        world.reconciliation_achieved = True
        out.append("__reconciliation__")
    return out


def _r_listening(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["loud"] >= THRESHOLD:
            continue
        sig = ("listen", actor.id)
        if sig in world.fired:
            continue
        if world.reconciliation_achieved:
            world.fired.add(sig)
            actor.memes["joy"] += 1
            actor.memes["friendship"] += 1
            actor.memes["isolation"] -= 1
            out.append("And his quiet heart found true glory at last.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="babble_effect", tag="social", apply=_r_babble_effect),
    Rule(name="counsel_effect", tag="social", apply=_r_counsel_effect),
    Rule(name="reflection", tag="inner", apply=_r_reflection),
    Rule(name="apology", tag="social", apply=_r_apology),
    Rule(name="listening", tag="social", apply=_r_listening),
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
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
def matching_lesson(activity: Activity, character_type: str) -> Optional[Lesson]:
    for lesson in LESSONS:
        if activity.mess in lesson.guards and character_type in lesson.covers:
            return lesson
    return None


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(f"In a bright green tree, lived {hero.phrase},")
    world.say(f"A little {hero.type} with a heart so true.")


def loves_babble(world: World, hero: Entity) -> None:
    hero.memes["pride"] += 1
    hero.meters["loud"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to babble and chatter all day,")
    world.say(f'"{hero.id} is the greatest!" {hero.pronoun()} would say.')
    world.say(f'"{hero.pronoun().capitalize()} is the best, with feathers so bright,"')
    world.say("He chirped and he chattered from morning to night.")


def wise_counsel(world: World, elder: Entity, hero: Entity) -> None:
    hero.memes["received_counsel"] += 1
    world.say(f"Then wise old {elder.label} perched on a bough,")
    world.say(f'"Dear {hero.id}, your babble is too loud now."')
    world.say(f'"Glory is earned by those who can listen, not just babble on."')
    propagate(world, narrate=False)


def retreat(world: World, hero: Entity) -> None:
    hero.memes["sadness"] += 1
    hero.memes["retreated"] += 1
    world.say(f"{hero.pronoun().capitalize()} felt a pang, a sting in {hero.pronoun('possessive')} chest,")
    world.say(f"{hero.pronoun().capitalize()} flew to {hero.pronoun('possessive')} nest, feeling truly distressed.")


def inner_monologue(world: World, hero: Entity) -> None:
    propagate(world, narrate=False)
    if world.inner_monologue_active:
        world.say(f'Tears fell like rain on {hero.pronoun("possessive")} scarlet chest,')
        world.say(f"{hero.pronoun().capitalize()} whispered to {hero.pronoun('object')}self, 'Am I just a pest?'")
        world.say("'All my loud babble, my glorious song,'")
        world.say("'Was it so very, very wrong?'")
        world.say("'I want to be quiet, I want to be still,'")
        world.say("'I want to listen, I want to feel.'")


def apologize(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["apologized"] += 1
    world.say(f"The next day, {hero.id} flew to {elder.label} with a bow,")
    world.say(f'"I\'m sorry for my babble, I see it now."')
    propagate(world, narrate=False)


def happy_ending(world: World, hero: Entity, elder: Entity) -> None:
    world.say(f"{elder.label} smiled and said, 'The first step is done,'")
    world.say("'For glory is found when the babble is done.'")
    world.say(f"From that day on, {hero.id} chirped soft and low,")
    world.say(f"Finding joy in the quiet, letting {hero.pronoun('possessive')} friendships grow.")
    propagate(world, narrate=True)


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, char_cfg: Character,
         hero_name: str = "Pip", hero_type: str = "bird",
         hero_traits: Optional[list[str]] = None, elder_type: str = "owl") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little", "scarlet"] + (hero_traits or ["proud", "noisy"]),
        phrase=f"{hero_name} the {hero_type}, with feathers of scarlet bright",
    ))
    elder = world.add(Entity(
        id="Elder", kind="character", type=elder_type, label=elder_type,
        phrase=f"a wise old {elder_type} with eyes so deep",
    ))

    # Act 1: Setup
    introduce(world, hero)
    world.say(f"His feathers were {activity.mess}, his voice was so strong,")
    loves_babble(world, hero)

    # Act 2: Conflict
    world.para()
    wise_counsel(world, elder, hero)
    retreat(world, hero)

    # Act 3: Inner Monologue
    world.para()
    inner_monologue(world, hero)

    # Act 4: Reconciliation & Happy Ending
    world.para()
    apologize(world, hero, elder)
    happy_ending(world, hero, elder)

    world.facts.update(hero=hero, elder=elder, char_cfg=char_cfg,
                       activity=activity, setting=setting,
                       reconciliation=world.reconciliation_achieved)
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "tree": Setting(place="the tree", affords={"sing", "chirp", "babble"}),
    "forest": Setting(place="the forest", affords={"sing", "chirp", "babble"}),
    "garden": Setting(place="the garden", affords={"sing", "chirp", "babble"}),
}

ACTIVITIES = {
    "sing": Activity(
        id="sing",
        verb="sing a loud song",
        gerund="singing loudly",
        rush="chirp as loud as he could",
        mess="loud",
        soil="loud and boastful",
        zone={"voice"},
        keyword="babble",
        tags={"babble", "song"},
    ),
    "chirp": Activity(
        id="chirp",
        verb="chirp all day long",
        gerund="chirping and chattering",
        rush="babble without stopping",
        mess="loud",
        soil="too noisy",
        zone={"voice"},
        keyword="chirp",
        tags={"babble", "noise"},
    ),
    "babble": Activity(
        id="babble",
        verb="babble and boast",
        gerund="babbling about his glory",
        rush="shout from the highest branch",
        mess="loud",
        soil="full of pride and noise",
        zone={"voice", "heart"},
        keyword="babble",
        tags={"babble", "pride"},
    ),
}

LESSONS = [
    Lesson(
        id="quiet_listening",
        label="quiet listening",
        covers={"bird", "owl", "finch", "robin"},
        guards={"loud", "prideful"},
        prep="listen with a quiet heart",
        tail="listened to the gentle sounds of the forest",
    ),
    Lesson(
        id="humble_song",
        label="humble song",
        covers={"bird"},
        guards={"loud"},
        prep="sing a gentle melody",
        tail="sang a quiet tune that everyone loved",
    ),
]

CHARACTERS = {
    "bird": Character(
        label="scarlet bird",
        phrase="a little scarlet bird, as bright as can be",
        type="bird",
        region="voice",
    ),
    "finch": Character(
        label="golden finch",
        phrase="a golden finch with a feathery crown",
        type="finch",
        region="voice",
    ),
    "robin": Character(
        label="robin redbreast",
        phrase="a robin redbreast with a speckled chest",
        type="robin",
        region="voice",
    ),
}

BIRD_NAMES = ["Pip", "Flit", "Zippy", "Cheep", "Scarlet", "Sunny", "Berry", "Rusty", "Blaze", "Crimson"]
TRAITS = ["proud", "noisy", "bright", "loud", "boastful", "shy", "eager", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for char_id, char in CHARACTERS.items():
                if matching_lesson(act, char_id):
                    combos.append((place, act_id, char_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    character: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "babble": [("What does it mean to babble?",
                "To babble means to talk a lot without stopping, like a bird "
                "who chirps and chatters all day long without listening.")],
    "glory": [("What is true glory?",
               "True glory is not about being the loudest or the best. It is "
               "about being kind, listening to others, and having good friends.")],
    "scarlet": [("What color is scarlet?",
                 "Scarlet is a bright, beautiful red color, like a strawberry "
                 "or a maple leaf in the fall.")],
    "listening": [("Why is listening important?",
                   "Listening is important because it helps us understand others, "
                   "make friends, and learn new things without just talking all the time.")],
    "reconciliation": [("What does it mean to reconcile?",
                        "To reconcile means to say sorry and make peace after "
                        "an argument, so everyone can be friends again.")],
    "inner_monologue": [("What is an inner monologue?",
                         "An inner monologue is when you think to yourself "
                         "quietly, having a conversation in your own mind to "
                         "figure out how you feel.")],
}

KNOWLEDGE_ORDER = ["babble", "glory", "scarlet", "listening", "reconciliation", "inner_monologue"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act, char_cfg = f["hero"], f["activity"], f["char_cfg"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old about a {char_cfg.label} '
        f'named {hero.id} who learns to stop babbling and find true glory in listening.',
        f"Tell a gentle rhyming story where a little {hero.type} named {hero.id} "
        f"feels sad after being told to be quiet, has an inner monologue of regret, "
        f"and makes friends through a heartfelt apology.",
        f"Write a simple rhyming story that uses the words 'glory', 'scarlet', and "
        f"'babble' and ends with a happy reconciliation between a young bird and a wise elder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, act, char_cfg = f["hero"], f["elder"], f["activity"], f["char_cfg"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)

    qa: list[QAItem] = [
        QAItem(
            question=f"Who is the story about when {hero.id} lives in {place} with {pos} bright feathers?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id}, with {pos} "
                   f"bright scarlet feathers, who lives in {place}."
        ),
        QAItem(
            question=f"What did {hero.id} love to do that made {pos} babble so loud?",
            answer=f"{hero.pronoun('possessive').capitalize()} {trait} {hero.type} loved "
                   f"{act.gerund}, and would babble all day about how great {sub} was."
        ),
        QAItem(
            question=f"How did {hero.id} feel after {elder.label} told {obj} to stop babbling?",
            answer=f"{sub.capitalize()} felt sad and upset. A pang of regret filled "
                   f"{pos} chest, and {sub} flew to {pos} nest to think alone."
        ),
        QAItem(
            question=f"What did {hero.id} think about during the inner monologue in {pos} nest?",
            answer=f"{sub.capitalize()} whispered to {obj}self, wondering if all "
                   f"{pos} loud babble was wrong. {sub} decided {sub} wanted to change "
                   f"and listen instead."
        ),
        QAItem(
            question=f"How did {hero.id} reconcile with {elder.label} at the end?",
            answer=f"{sub.capitalize()} flew to {elder.label}, bowed, and said sorry. "
                   f"The wise {elder.type} forgave {obj}, and they became friends. "
                   f"{hero.id} learned to sing softly and listen."
        ),
    ]
    if f.get("reconciliation"):
        qa.append(QAItem(
            question=f"What was the happy ending for {hero.id} after the reconciliation?",
            answer=f"{hero.pronoun('possessive').capitalize()} heart found true glory "
                   f"in quiet connection. {sub.capitalize()} chirped softly, making "
                   f"friends and feeling happy, letting {pos} friendships grow."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
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
# CLI / trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  Inner Monologue Active: {world.inner_monologue_active}")
    lines.append(f"  Reconciliation Achieved: {world.reconciliation_achieved}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set
CURATED = [
    StoryParams(
        place="tree",
        activity="babble",
        character="bird",
        name="Pip",
        trait="proud",
    ),
    StoryParams(
        place="forest",
        activity="sing",
        character="finch",
        name="Sunny",
        trait="noisy",
    ),
    StoryParams(
        place="garden",
        activity="chirp",
        character="robin",
        name="Rusty",
        trait="boastful",
    ),
]


def explain_rejection(activity: Activity, char_cfg: Character) -> str:
    if not matching_lesson(activity, char_cfg.type):
        return (f"(No story: a {char_cfg.label}'s voice region and {activity.gerund} "
                f"don't have a matching lesson plan. Try a different character or activity.)")
    return "(No story: the combination is invalid for unknown reasons.)"


# ---------------------------------------------------------------------------
# ASP Twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
valid(Place, A, C) :- setting(Place), affords(Place, A),
                      activity(A), character(C),
                      mess_of(A, M), guards(L, M),
                      covers(L, C).
valid_story(Place, A, C) :- valid(Place, A, C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for cid, char_cfg in CHARACTERS.items():
        lines.append(asp.fact("character", cid))
        lines.append(asp.fact("type_of", cid, char_cfg.type))
    for l in LESSONS:
        lines.append(asp.fact("lesson", l.id))
        for m in sorted(l.guards):
            lines.append(asp.fact("guards", l.id, m))
        for c in sorted(l.covers):
            lines.append(asp.fact("covers", l.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: a little scarlet bird who babbles, "
                    "learns through inner monologue, and finds reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--character", choices=CHARACTERS)
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true",
                    help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.character:
        act, char_cfg = ACTIVITIES[args.activity], CHARACTERS[args.character]
        if not matching_lesson(act, char_cfg.type):
            raise StoryError(explain_rejection(act, char_cfg))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.character is None or c[2] == args.character)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, char_id = rng.choice(sorted(combos))
    char_cfg = CHARACTERS[char_id]
    name = args.name or rng.choice(BIRD_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        character=char_id,
        name=name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 CHARACTERS[params.character], params.name,
                 CHARACTERS[params.character].type,
                 [params.trait], "owl")
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, character) combos:\n")
        for place, act, char in triples:
            print(f"  {place:8} {act:8} {char:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (character: {p.character})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
