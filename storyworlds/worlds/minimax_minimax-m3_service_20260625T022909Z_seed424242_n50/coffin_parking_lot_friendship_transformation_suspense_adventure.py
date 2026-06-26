#!/usr/bin/env python3
"""
storyworlds/worlds/coffin_parking_lot_friendship_transformation_suspense_adventure.py
======================================================================================

A small standalone story world for the seed phrase
"coffin in the parking lot", told as a gentle Adventure for young readers
that blends Friendship, Transformation, and Suspense.

Initial story (used to build the world model):
---
It was a quiet evening, and the parking lot behind the bakery was wide and
empty. Mira, a curious little girl with a flashlight, and Ben, her best
friend who liked to bring tools, met by the old oak tree at the corner of
the lot. Mira's grandmother had told her that a small wooden coffin had
been left near the trash bins, and that it was a sign to be brave.

When the two friends walked closer, the parking lot grew quieter. A thin
fog rolled between the cars, and Ben's flashlight made long shadows.
Mira's heart beat faster, but Ben squeezed her hand. Together they
tiptoed past the buses, peeked behind the dumpsters, and finally found
a tiny wooden box resting against a tire. It was the size of a storybook
and smelled of pine and rain.

Mira knelt and lifted the lid. Inside was not a scary thing at all, but
a small velvet pouch with a single acorn inside. The acorn glowed softly,
and a piece of paper said: "Plant me, and grow a friend." The friends
dug a hole at the edge of the lot, planted the acorn, and watered it
with their water bottles. By the time the streetlights clicked on, a
tender green sprout had pushed up through the asphalt. Mira and Ben
smiled, and the parking lot felt like the beginning of a long adventure.

Causal state updates:
---
    friend alone in scary place          -> friend.fear += 1
    friend with ally at their side       -> ally.support += 1 ; friend.fear eases
    friend discovers the box             -> friend.curiosity += 1
    friend opens the box                 -> friend.courage += 1
    ally stays at friend's side           -> ally.loyalty += 1
    acorn is planted                     -> lot.sprout += 1 (transformation)
    sprout grows                         -> friend.wonder += 1
    dusk falls over the parking lot      -> lot.suspense += 1

Scripted social/emotional beats:
---
    ally squeezes friend's hand          -> friend.bond += 1
    friends share the discovery           -> friends.teamwork += 1
    both laugh at the end                -> joy += 1, suspense -> 0
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
SUSPENSE_KINDS = {"dark", "fog", "quiet", "creak"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    ally_of: Optional[str] = None
    region: str = ""              # body region (kept for symmetry with puddles)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    id: str
    place: str
    landmark: str
    scent: str
    sound: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Coffin:
    """The little wooden box that drives the suspense -> transformation turn."""
    id: str
    label: str
    material: str
    size: str
    lining: str
    payload: str
    note: str
    effect: str              # the transformation key: "sprout" | "bird" | "lantern"


@dataclass
class Ally:
    id: str
    label: str
    item: str                # flashlight, compass, snack, kite
    item_role: str           # what the item does in the scene
    item_tail: str           # closing clause describing the item's payoff
    plural: bool = False


@dataclass
class SuspenseBeat:
    """A small moment of mystery layered over the parking lot scene."""
    id: str
    setup: str               # the line that raises the suspense meter
    gloss: str               # child-facing explanation of why it is suspenseful
    kind: str                # one of SUSPENSE_KINDS


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.beats: list[SuspenseBeat] = []
        self.suspense: set[str] = set()
        self.facts: dict = {}

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
        clone.suspense = set(self.suspense)
        clone.beats = list(self.beats)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward-chained)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_alone_is_scary(world: World) -> list[str]:
    """A friend alone in a suspenseful place gains fear."""
    out: list[str] = []
    suspense = any(b in world.suspense for b in SUSPENSE_KINDS)
    if not suspense:
        return out
    for actor in world.characters():
        if actor.memes.get("ally_present", 0) >= THRESHOLD:
            continue
        sig = ("alone_scary", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_ally_calms(world: World) -> list[str]:
    """An ally at the side of a fearful friend eases the fear and bonds them."""
    out: list[str] = []
    chars = world.characters()
    for actor in chars:
        ally_id = actor.ally_of
        if not ally_id or actor.memes["fear"] < THRESHOLD:
            continue
        if actor.memes.get("ally_present", 0) < THRESHOLD:
            continue
        sig = ("ally_calms", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] = max(0.0, actor.memes["fear"] - 1)
        actor.memes["bond"] += 1
        ally = world.get(ally_id)
        ally.memes["loyalty"] += 1
        out.append("__bond__")
    return out


def _r_discovery(world: World) -> list[str]:
    """Once the box is found, curiosity fires (a forward-chained emotion)."""
    out: list[str] = []
    for actor in world.characters():
        if world.entities.get("coffin") is None:
            continue
        if actor.memes.get("found", 0) < THRESHOLD:
            continue
        sig = ("discovery", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["curiosity"] += 1
    return out


def _r_opening(world: World) -> list[str]:
    """Opening the box marks the courage beat -- only if fear is below threshold."""
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("opened", 0) < THRESHOLD:
            continue
        sig = ("opening", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["courage"] += 1
    return out


def _r_plant_grows(world: World) -> list[str]:
    """Planting the acorn seeds the transformation, which then yields wonder."""
    out: list[str] = []
    lot = world.entities.get("lot")
    if lot is None or lot.meters.get("planted", 0) < THRESHOLD:
        return out
    sig = ("sprout",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    lot.meters["sprout"] += 1
    for actor in world.characters():
        actor.memes["wonder"] += 1
    out.append("__sprout__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="alone_scary", tag="emotion", apply=_r_alone_is_scary),
    Rule(name="ally_calms", tag="social", apply=_r_ally_calms),
    Rule(name="discovery", tag="emotion", apply=_r_discovery),
    Rule(name="opening", tag="courage", apply=_r_opening),
    Rule(name="plant_grows", tag="transform", apply=_r_plant_grows),
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
def coffin_fits(beat: SuspenseBeat) -> bool:
    return beat.kind in SUSPENSE_KINDS


def coffin_for_coffin(c: Coffin, beat: SuspenseBeat) -> bool:
    """Reasonableness: the suspense beat must not be 'creak' (the coffin is
    silent in this story); 'dark', 'fog', and 'quiet' are valid."""
    return beat.kind in {"dark", "fog", "quiet"}


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for sid, s in SETTINGS.items():
        for cid in s.affords:
            for bid in SUSPENSE_BEATS:
                if coffin_for_coffin(COFFINS[cid], bid):
                    out.append((sid, cid, bid))
    return out


# ---------------------------------------------------------------------------
# Prediction: the ally runs the model forward to see if the friend panics.
# ---------------------------------------------------------------------------
def predict_fear(world: World, friend: Entity) -> dict:
    sim = world.copy()
    sim.suspense = set(world.suspense)
    propagate(sim, narrate=False)
    friend_sim = sim.get(friend.id)
    return {
        "fear": friend_sim.memes.get("fear", 0.0),
        "wonder": friend_sim.memes.get("wonder", 0.0),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def setting_opener(setting: Setting) -> str:
    return (f"It was a quiet evening, and {setting.place} was wide and mostly empty. "
            f"Near {setting.landmark}, the air smelled of {setting.scent}, and the only "
            f"sound was {setting.sound}.")


def introduce_pair(world: World, friend: Entity, ally: Entity) -> None:
    sub = friend.pronoun().capitalize()
    ally_sub = ally.pronoun().capitalize()
    world.say(
        f"{sub} was a little {friend.traits[0] if friend.traits else 'curious'} "
        f"{friend.type} who liked small adventures, and {ally_sub} was "
        f"{friend.pronoun('possessive')} best friend, who always brought "
        f"a {ally.item} just in case."
    )


def gather(world: World, friend: Entity, ally: Entity) -> None:
    world.say(
        f"They met by {world.setting.landmark} at the edge of {world.setting.place}."
    )


def raise_suspense(world: World, friend: Entity, beat: SuspenseBeat) -> None:
    world.beats.append(beat)
    world.suspense.add(beat.kind)
    world.say(beat.setup)
    world.say(beat.gloss)


def ally_joins(world: World, friend: Entity, ally: Entity) -> None:
    friend.memes["ally_present"] += 1
    ally.memes["ally_present"] += 1
    world.say(
        f"{ally.pronoun().capitalize()} saw {friend.pronoun('possessive')} face and "
        f"came right over, swinging {ally.pronoun('possessive')} {ally.item}."
    )
    world.say(
        f'"{ally.item.capitalize()} ready, {friend.id}?" {ally.pronoun()} said with a '
        f"small smile, and {friend.pronoun()} nodded."
    )


def tiptoe(world: World, friend: Entity, ally: Entity) -> None:
    world.say(
        f"Together they tiptoed past the parked cars, peeked behind the bins, "
        f"and listened for the tiniest sound. The {ally.item} was {ally.item_role}."
    )


def find_box(world: World, friend: Entity, ally: Entity, coffin: Coffin) -> None:
    friend.memes["found"] += 1
    ally.memes["found"] += 1
    world.facts["coffin_id"] = coffin.id
    world.say(
        f"At last they spotted a {coffin.size} {coffin.label} resting against an old "
        f"tire. It was made of {coffin.material}, and the {coffin.lining} made it "
        f"look almost like a small storybook."
    )


def kneel_and_open(world: World, friend: Entity, ally: Entity, coffin: Coffin) -> None:
    friend.memes["opened"] += 1
    ally.memes["opened"] += 1
    world.say(
        f"{friend.pronoun().capitalize()} knelt, took a slow breath, and lifted the "
        f"lid. Inside was not a scary thing at all, but {coffin.payload}."
    )
    world.say(
        f'A small piece of paper tucked beside it read, "{coffin.note}"'
    )


def ally_reaction(world: World, friend: Entity, ally: Entity, coffin: Coffin) -> None:
    world.say(
        f"{ally.pronoun().capitalize()} grinned. \"This is the best part,\" "
        f"{ally.pronoun()} said. \"{ally.item_tail.capitalize()}.\""
    )


def plant(world: World, friend: Entity, ally: Entity, coffin: Coffin) -> None:
    lot = world.entities.get("lot")
    lot.meters["planted"] += 1
    world.say(
        f"They found a soft spot at the edge of {world.setting.place}, dug a tiny hole "
        f"with their hands, and nestled the {coffin.payload.split('with a ')[-1].split(' inside')[0]} "
        f"into the crumbly dirt. They poured a little water from their bottles over it."
    )


def grow(world: World, friend: Entity, ally: Entity, coffin: Coffin) -> None:
    propagate(world, narrate=False)              # fires the sprout -> wonder rule
    world.say(
        f"Just as the streetlights above {world.setting.place} blinked on, a tender "
        f"green shoot pushed up through the ground and gave a small, brave wiggle."
    )


def close(world: World, friend: Entity, ally: Entity) -> None:
    friend.memes["joy"] += 1
    ally.memes["joy"] += 1
    friend.memes["fear"] = 0.0
    world.say(
        f"{friend.pronoun().capitalize()} and {ally.pronoun('object')} looked at each "
        f"other and laughed. The parking lot, which had felt so quiet a moment ago, "
        f"now felt like the start of a long and friendly adventure."
    )
    world.say(
        f"They promised to come back the next evening to see how tall their new "
        f"little friend had grown."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, coffin: Coffin, beat: SuspenseBeat, ally: Ally,
         friend_name: str = "Mira", friend_type: str = "girl",
         ally_name: str = "Ben", ally_type: str = "boy",
         friend_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=(friend_traits or ["curious", "brave"]),
    ))
    ally = world.add(Entity(
        id=ally_name, kind="character", type=ally_type,
        ally_of=friend.id, label="best friend",
    ))
    lot = world.add(Entity(
        id="lot", kind="place", type="parking_lot", label="the parking lot",
        phrase=setting.place,
    ))
    world.add(Entity(
        id=coffin.id, kind="thing", type="coffin",
        label=coffin.label, phrase=f"a small {coffin.label}",
    ))

    # Act 1 -- setup: who they are, where they are.
    world.say(setting_opener(setting))
    introduce_pair(world, friend, ally)
    gather(world, friend, ally)

    # Act 2 -- suspense + friendship turn.
    world.para()
    raise_suspense(world, friend, beat)
    ally_joins(world, friend, ally)
    tiptoe(world, friend, ally)
    find_box(world, friend, ally, coffin)
    kneel_and_open(world, friend, ally, coffin)
    ally_reaction(world, friend, ally, coffin)

    # Act 3 -- transformation: plant the seed, watch it grow, share the wonder.
    world.para()
    plant(world, friend, ally, coffin)
    grow(world, friend, ally, coffin)
    close(world, friend, ally)

    # Record facts for the Q&A generators.
    world.facts.update(
        friend=friend, ally=ally, coffin=coffin, beat=beat, ally_def=ally,
        setting=setting, suspense_kind=beat.kind, lot=lot,
        fear_unbound=friend.memes["fear"] >= THRESHOLD,
        wonder=friend.memes["wonder"] >= THRESHOLD,
        bond=friend.memes["bond"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bakery_lot": Setting(
        id="bakery_lot",
        place="the parking lot behind the bakery",
        landmark="the old oak tree at the corner of the lot",
        scent="warm bread and a little bit of rain",
        sound="the soft pop of the bakery's last light",
        affords={"acorn", "lantern", "feather"},
    ),
    "school_lot": Setting(
        id="school_lot",
        place="the empty parking lot by the school",
        landmark="the blue bike rack near the back gate",
        scent="cut grass and a trace of chalk",
        sound="the chain of a flag swaying in the breeze",
        affords={"acorn", "lantern", "feather"},
    ),
    "library_lot": Setting(
        id="library_lot",
        place="the little parking lot by the library",
        landmark="the low stone wall that circles the library",
        scent="old books and pine needles",
        sound="a sprinkler hissing on the lawn next door",
        affords={"acorn", "lantern", "feather"},
    ),
}

COFFINS = {
    "acorn": Coffin(
        id="acorn",
        label="wooden coffin",
        material="warm pine with tiny brass nails",
        size="about the size of a storybook",
        lining="velvet lining the color of moss",
        payload="a small velvet pouch holding a single acorn",
        note="Plant me, and grow a friend.",
        effect="sprout",
    ),
    "lantern": Coffin(
        id="lantern",
        label="wooden coffin",
        material="cedar with a moon carved on the lid",
        size="smaller than a lunchbox",
        lining="a small cushion of dried lavender",
        payload="a tiny folded paper lantern with a tealight",
        note="Light me, and find your way home.",
        effect="lantern",
    ),
    "feather": Coffin(
        id="feather",
        label="wooden coffin",
        material="birch with a smooth, pale finish",
        size="just big enough to fit in two small hands",
        lining="a scrap of soft cotton",
        payload="one warm feather and a spool of red thread",
        note="Tie me where you are afraid.",
        effect="thread",
    ),
}

ALLIES = [
    Ally(
        id="flashlight",
        label="flashlight",
        item="flashlight",
        item_role="making long, brave shadows on the asphalt",
        item_tail="the beam made the shadows feel small, not big",
    ),
    Ally(
        id="compass",
        label="compass",
        item="compass",
        item_role="pointing gently back toward the oak tree",
        item_tail="the needle stayed steady, like a friend holding your hand",
    ),
    Ally(
        id="snack",
        label="snack",
        item="paper bag of crackers",
        item_role="rustling softly to remind them they were not alone",
        item_tail="the crinkle of the bag was a friendly little drum",
    ),
    Ally(
        id="kite",
        label="kite",
        item="folded paper kite",
        item_role="ready to fly when the moment felt safe again",
        item_tail="it promised that there would be wind for a second adventure",
    ),
]

SUSPENSE_BEATS = {
    "dark": SuspenseBeat(
        id="dark",
        setup="The light above the corner of the lot buzzed and went out with a small click.",
        gloss="It was the kind of quiet that makes your ears listen harder.",
        kind="dark",
    ),
    "fog": SuspenseBeat(
        id="fog",
        setup="A thin fog rolled between the parked cars, soft as a held breath.",
        gloss="Everything looked a little bigger when it was wrapped in fog.",
        kind="fog",
    ),
    "quiet": SuspenseBeat(
        id="quiet",
        setup="For a long moment, the lot was so quiet they could hear each other's hearts.",
        gloss="Sometimes the quietest places have the most to say.",
        kind="quiet",
    ),
    # 'creak' is intentionally rejected by coffin_for_coffin (see constraint).
    "creak": SuspenseBeat(
        id="creak",
        setup="A wooden door creaked somewhere behind the trash bins.",
        gloss="Old doors can be the loudest storytellers in a parking lot.",
        kind="creak",
    ),
}

GIRL_NAMES = ["Mira", "Lila", "Nora", "Zoe", "Maya", "Anna", "Rose", "Ava"]
BOY_NAMES = ["Ben", "Sam", "Leo", "Finn", "Theo", "Eli", "Noah", "Jack"]


# ---------------------------------------------------------------------------
# Per-story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    coffin: str
    suspense: str
    ally: str
    friend_name: str
    friend_gender: str
    ally_name: str
    ally_gender: str
    friend_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    friend, ally, coffin, beat = f["friend"], f["ally"], f["coffin"], f["beat"]
    return [
        f'Write a gentle adventure for a 4-to-6-year-old on the theme "two '
        f'friends, one mystery, a kind surprise" that uses the word "coffin".',
        f"Tell a small adventure where {friend.id} and {ally.id} find a tiny "
        f"coffin in {world.setting.place} and turn the mystery into a friendship.",
        f'Write a quiet, suspenseful story set in a parking lot that ends with '
        f"a small transformation -- something brave and green growing in an "
        f"unexpected place.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    friend, ally, coffin, beat = f["friend"], f["ally"], f["coffin"], f["beat"]
    pos = friend.pronoun("possessive")
    sub = friend.pronoun("subject")
    obj = friend.pronoun("object")
    pos_a = ally.pronoun("possessive")
    sub_a = ally.pronoun("subject")
    place = world.setting.place
    landmark = world.setting.landmark
    item = ally.item
    qa: list[QAItem] = []

    qa.append(QAItem(
        question=(
            f"Who goes to {landmark} in {place} at the start of the story about "
            f"the little {coffin.label}?"
        ),
        answer=(
            f"{friend.id} and {pos} best friend {ally.id} meet at {landmark} in "
            f"{place} on a quiet evening, ready for a small adventure."
        ),
    ))

    qa.append(QAItem(
        question=(
            f"What makes the parking lot feel suspenseful for {friend.id} and "
            f"{ally.id} before they find the {coffin.label}?"
        ),
        answer=(
            f"The {beat.kind} {beat.gloss.rstrip('.')} That is what made the "
            f"lot feel a little spooky before they spotted the {coffin.label}."
        ),
    ))

    qa.append(QAItem(
        question=(
            f"How does {ally.id} help {friend.id} feel less afraid in "
            f"{place} when the {beat.kind} settles in?"
        ),
        answer=(
            f"{sub_a.capitalize()} comes over with {pos_a} {item}, says a small "
            f"cheerful line, and tiptoes beside {friend.id}. {sub.capitalize()} "
            f"feels braver with {ally.id} at {pos} side."
        ),
    ))

    qa.append(QAItem(
        question=(
            f"What do {friend.id} and {ally.id} find inside the small "
            f"{coffin.label} in {place}?"
        ),
        answer=(
            f"Inside the {coffin.label} is {coffin.payload}, with a paper that "
            f'reads, "{coffin.note}" It looks like an invitation, not a fright.'
        ),
    ))

    qa.append(QAItem(
        question=(
            f"How is the suspense of the {coffin.label} in {place} turned "
            f"into a friendship moment between {friend.id} and {ally.id}?"
        ),
        answer=(
            f"Instead of being scared, the two friends work as a team: {ally.id} "
            f"brings {pos_a} {item}, {friend.id} opens the lid, and together "
            f"they plant what they find. The mystery becomes a shared project."
        ),
    ))

    qa.append(QAItem(
        question=(
            f"What small transformation happens at the edge of {place} after "
            f"the friends open the {coffin.label}?"
        ),
        answer=(
            f"They plant the {coffin.payload.split('with a ')[-1].split(' inside')[0]}, "
            f"pour a little water, and a tender green shoot wiggles up through "
            f"the ground just as the lights come on."
        ),
    ))

    qa.append(QAItem(
        question=(
            f"How does the story about {friend.id} and {ally.id} in {place} "
            f"end, and why does the parking lot feel different by then?"
        ),
        answer=(
            f"The friends laugh and promise to come back the next evening to see "
            f"how tall their new little friend has grown. The lot, which had "
            f"felt so quiet and strange, now feels like the start of a long "
            f"and friendly adventure."
        ),
    ))

    return qa


def KNOWLEDGE() -> list[QAItem]:
    """(3) Generic, child-level world knowledge about the domain."""
    return [
        QAItem(
            question="What is a coffin?",
            answer=("A coffin is a small box, often made of wood, that holds "
                    "something special. In a story it can also be a tiny box "
                    "that hides a kind surprise."),
        ),
        QAItem(
            question="Why does a parking lot feel different at night?",
            answer=("At night a parking lot is mostly empty, the lights are far "
                    "apart, and the air is quiet, so little sounds seem bigger "
                    "than they really are."),
        ),
        QAItem(
            question="What is friendship?",
            answer=("Friendship is when two people choose to look out for each "
                    "other, share what they find, and stay close when things "
                    "feel a little scary."),
        ),
        QAItem(
            question="What is a transformation in a story?",
            answer=("A transformation is when something changes into something "
                    "new, like a tiny seed turning into a green shoot, or a "
                    "scary moment turning into a kind one."),
        ),
        QAItem(
            question="Why is suspense fun in a children's story?",
            answer=("Suspense is a small safe question in a story -- 'what is "
                    "inside the box?' It makes the listener lean in, and the "
                    "answer usually feels like a warm surprise."),
        ),
        QAItem(
            question="What is an adventure?",
            answer=("An adventure is a small trip into the unknown with a "
                    "friend at your side, where you pay attention, stay brave, "
                    "and come back with a story to tell."),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE()


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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.ally_of:
            bits.append(f"ally_of={e.ally_of}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  suspense kinds: {sorted(world.suspense)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="bakery_lot", coffin="acorn", suspense="fog", ally="flashlight",
        friend_name="Mira", friend_gender="girl",
        ally_name="Ben", ally_gender="boy", friend_trait="curious",
    ),
    StoryParams(
        place="school_lot", coffin="lantern", suspense="dark", ally="compass",
        friend_name="Lila", friend_gender="girl",
        ally_name="Sam", ally_gender="boy", friend_trait="brave",
    ),
    StoryParams(
        place="library_lot", coffin="feather", suspense="quiet", ally="snack",
        friend_name="Nora", friend_gender="girl",
        ally_name="Theo", ally_gender="boy", friend_trait="gentle",
    ),
]


def explain_rejection(coffin: Coffin, beat: SuspenseBeat) -> str:
    return (f"(No story: the {coffin.label} holds {coffin.payload.split(' with ')[0]}, "
            f"which fits a '{beat.kind}' beat poorly. Try a 'dark', 'fog', or "
            f"'quiet' suspense beat so the box and the mood agree.)")


def explain_coffin_mismatch(place: str, coffin: str) -> str:
    return (f"(No story: {place} does not host the {coffin} coffin variant. "
            f"Try {', '.join(sorted(SETTINGS[place].affords))}.)")


# ---------------------------------------------------------------------------
# Inline ASP twin of the reasonableness gate
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A coffin variant is allowed in a setting only when the setting affords it.
coffin_in(Place, C) :- setting(Place), coffin(C), affords(Place, C).

% A suspense beat is acceptable when the coffin does not produce noise
% (the creak beat would clash with a silent wooden box).
beat_ok(C, B) :- coffin(C), suspense(B), not noisy_beat(B), beat(C, B).
beat_ok(C, B) :- coffin(C), suspense(B), noisy_beat(B), open_lid(C).

% A full story needs: setting that affords the coffin, a beat the coffin accepts.
valid(Place, C, B) :- coffin_in(Place, C), beat_ok(C, B).

% Gender pairing: the friend and ally must not share the same pronoun in the
% curated pairs (kept simple; this is a one-line mirror of the curated list).
gender_pair(G1, G2) :- gender(G1), gender(G2), G1 != G2.
valid_story(Place, C, B, G1, G2) :- valid(Place, C, B), gender_pair(G1, G2).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    from storyworlds import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in COFFINS.items():
        lines.append(asp.fact("coffin", cid))
        lines.append(asp.fact("open_lid", cid))    # all three open cleanly
    for bid, b in SUSPENSE_BEATS.items():
        lines.append(asp.fact("suspense", bid))
        lines.append(asp.fact("beat", cid_default:= "acorn", bid))   # placeholder
        if b.kind == "creak":
            lines.append(asp.fact("noisy_beat", bid))
    for g in ("girl", "boy"):
        lines.append(asp.fact("gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    from storyworlds import asp
    program = asp_program("#show valid/3.")
    model = asp.one_model(program)
    triples: set[tuple] = set()
    for place, coffin in asp.atoms(model, "coffin_in"):
        for p, c, b in asp.atoms(model, "valid"):
            if (p, c) == (place, coffin):
                triples.add((p, c, b))
    return sorted(triples)


def asp_valid_stories() -> list[tuple]:
    from storyworlds import asp
    program = asp_program("#show valid_story/5.")
    model = asp.one_model(program)
    return sorted(set(asp.atoms(model, "valid_story")))


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
        description="Story world: two friends find a small coffin in a "
                    "parking lot and turn the mystery into a transformation. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--coffin", choices=COFFINS)
    ap.add_argument("--suspense", choices=SUSPENSE_BEATS)
    ap.add_argument("--ally", choices=[a.id for a in ALLIES])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--ally-name")
    ap.add_argument("--ally-gender", choices=["girl", "boy"])
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
    if args.coffin and args.suspense:
        if not coffin_for_coffin(COFFINS[args.coffin], SUSPENSE_BEATS[args.suspense]):
            raise StoryError(explain_rejection(COFFINS[args.coffin],
                                               SUSPENSE_BEATS[args.suspense]))
    if args.place and args.coffin and args.coffin not in SETTINGS[args.place].affords:
        raise StoryError(explain_coffin_mismatch(args.place, args.coffin))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.coffin is None or c[1] == args.coffin)
              and (args.suspense is None or c[2] == args.suspense)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, coffin, suspense = rng.choice(sorted(combos))
    ally = next(a for a in ALLIES if a.id == args.ally) if args.ally else rng.choice(ALLIES)
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    ally_gender = args.ally_gender or ("boy" if friend_gender == "girl" else "girl")
    friend_name = args.friend_name or rng.choice(
        GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    ally_name = args.ally_name or rng.choice(
        GIRL_NAMES if ally_gender == "girl" else BOY_NAMES)
    trait = rng.choice(["curious", "brave", "gentle", "bright", "cheerful"])
    return StoryParams(
        place=place, coffin=coffin, suspense=suspense, ally=ally.id,
        friend_name=friend_name, friend_gender=friend_gender,
        ally_name=ally_name, ally_gender=ally_gender,
        friend_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], COFFINS[params.coffin], SUSPENSE_BEATS[params.suspense],
        next(a for a in ALLIES if a.id == params.ally),
        params.friend_name, params.friend_gender,
        params.ally_name, params.ally_gender,
        [params.friend_trait, "lively"],
    )
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, coffin, suspense) combos "
              f"({len(stories)} with gender pairing):\n")
        for place, coffin, beat in triples:
            print(f"  {place:12} coffin={coffin:7} suspense={beat}")
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
            header = f"### {p.friend_name} & {p.ally_name}: {p.coffin} coffin at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
