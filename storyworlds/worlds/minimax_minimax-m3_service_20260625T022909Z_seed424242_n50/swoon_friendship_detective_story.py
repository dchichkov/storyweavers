#!/usr/bin/env python3
"""
storyworlds/worlds/swoon_friendship_detective_story.py
=====================================================

A standalone *story world* sketch for a "swoon + friendship + detective" tale
and close, *constraint-checked* variations of it.

Initial story (used to build a world model):
---
Once upon a time there was a little bright girl named Pip. She wore a small
felt detective cap that her best friend, the boy next door named Kit, had
made for her as a birthday gift. They had a secret rule: when one of them
needed help, the other would tilt their own cap and say the words
"case opened" out loud.

One summer afternoon, Pip was practicing cartwheels in the park when a
sudden dizzy spell made her sit down on the grass, pale and blinking. Kit
saw her from across the path and ran over. He noticed three small things at
once: the empty water bottle on the bench beside her, the warm sun beating
down on her neck, and the way she kept gripping the bench with both hands
as if the world was tilting. He said softly, "Case opened, Pip," and tipped
his own cap to her.

Pip told him she felt like she might swoon, and Kit guessed she had been
turning cartwheels without drinking any water on a hot day. He gave her his
last sip of cool water, took off his jacket and folded it into a pillow,
and sat beside her so she could lean on his shoulder. Within a few minutes
the dizzy feeling faded and Pip could stand up again. They walked home
together slowly, both wearing their caps, and Pip said, "Case closed,
friend."

Causal state updates:
---
    do cartwheels on a hot day         -> actor.heat += 1
                                       -> actor.thirst += 1
    heat + thirst + low water         -> actor.dizziness += 1
    a friend notices                   -> friend.care += 1
    a friend offers water              -> actor.thirst -> 0 ; actor.dizziness -> 0
    a friend makes a shoulder pillow   -> actor.comfort += 1

Scripted social/emotional beats:
---
    dizzy spell seen                   -> actor.vulnerability += 1
    friend arrives with the case line  -> actor.reassurance += 1
    friend names the cause             -> actor.trust += 1
    recovery together                  -> actor.friendship += 1
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Physical meter keys we treat as a body condition.
CONDITIONS = {"heat", "thirst", "dizziness"}

# Emotional meme keys we treat as social state.
SOCIAL_MEMES = {"care", "vulnerability", "reassurance", "trust", "friendship"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, detective, friend ...
    label: str = ""                # short reference, e.g. "friend"
    phrase: str = ""               # full noun phrase, e.g. "the kind boy next door"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))  # physical
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))   # emotional

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "detective_girl"}
        male = {"boy", "father", "dad", "man", "detective_boy"}
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
# Parametrization knobs -- the swappable vocabulary of this little domain.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the park"
    indoor: bool = False
    weather: str = ""              # "sunny" | "rainy" | "warm" | ""
    affords: set[str] = field(default_factory=set)   # which activities this place supports


@dataclass
class Activity:
    """A dizzy-making thing the hero loves to do."""
    id: str
    verb: str            # after "was ..."
    gerund: str          # after "was ..."
    rush: str            # after "kept ..."
    effort: str          # physical-effort kind key, one of EFFORT_KINDS
    needs_water: bool    # whether the activity normally demands drinking water
    weather: str         # "sunny" | "warm" | ""
    keyword: str = ""    # topic word for generation prompts
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    """A named plausible reason for the swoon (what the friend will diagnose)."""
    id: str
    label: str           # short noun phrase
    phrase: str          # fuller description
    condition: str       # condition key the activity raises
    remedy: str          # remedy noun
    remedy_action: str   # the verb the friend does with the remedy
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Remedy:
    """The helpful thing the friend offers that solves the spell."""
    id: str
    label: str
    phrase: str
    target_condition: str   # which condition it neutralizes
    prep: str               # body of the offer: "drink some cool water"
    tail: str               # closing clause: "shared the last cool water"
    plural: bool = False


@dataclass
class Clue:
    """A small thing the detective-friend notices at the scene."""
    id: str
    label: str
    phrase: str
    hints_at: str           # which cause it points toward
    place: str              # which setting it must be present in


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    # -- narration helpers --------------------------------------------------
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
        """Throwaway clone used for forward-simulation (prediction)."""
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules: forward-chained to a fixpoint.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dizziness(world: World) -> list[str]:
    """heat + thirst + no remedy yet -> dizziness."""
    actor = next((e for e in world.characters() if e.id == "Hero"), None)
    if actor is None:
        return []
    if actor.meters["heat"] < THRESHOLD or actor.meters["thirst"] < THRESHOLD:
        return []
    if any(e.id.startswith("remedy_") and e.worn_by == actor.id for e in world.entities.values()):
        return []
    if actor.meters["dizziness"] >= THRESHOLD:
        return []
    sig = ("dizziness", actor.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    actor.meters["dizziness"] += 1
    actor.memes["vulnerability"] += 1
    return [f"{actor.pronoun().capitalize()} felt the world tilt a little."]


def _r_remedy(world: World) -> list[str]:
    """a remedy worn by the hero clears its target condition."""
    out: list[str] = []
    actor = next((e for e in world.characters() if e.id == "Hero"), None)
    if actor is None:
        return []
    for item in list(world.entities.values()):
        if not item.id.startswith("remedy_") or item.worn_by != actor.id:
            continue
        target = item.type  # we encode the target condition in the type
        sig = ("remedy", item.id, target)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if actor.meters[target] >= THRESHOLD:
            actor.meters[target] = 0.0
        out.append(f"The {item.label} did its quiet work.")
    return out


def _r_comfort(world: World) -> list[str]:
    """dizziness cleared -> comfort rises; friendship rises if friend is present."""
    actor = next((e for e in world.characters() if e.id == "Hero"), None)
    friend = next((e for e in world.characters() if e.id == "Friend"), None)
    if actor is None or friend is None:
        return []
    if actor.meters["dizziness"] >= THRESHOLD:
        return []
    sig = ("comfort", actor.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    actor.meters["comfort"] += 1
    actor.memes["reassurance"] += 1
    friend.memes["care"] += 1
    actor.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    return [f"The dizzy spell eased off, and the two friends breathed easier."]


CAUSAL_RULES: list[Rule] = [
    Rule(name="dizziness", tag="physical", apply=_r_dizziness),
    Rule(name="remedy", tag="physical", apply=_r_remedy),
    Rule(name="comfort", tag="social", apply=_r_comfort),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    """Apply all rules until nothing new fires (forward chaining to fixpoint)."""
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers -- what is a *reasonable* swoon, friend, and fix.
# ---------------------------------------------------------------------------
def cause_matches(cause: Condition := None, activity: Activity, setting: Setting) -> bool:
    """Would this cause plausibly explain a swoon during this activity in this setting?"""
    # a condition key must be one of the activity's effects and the setting must
    # plausibly trigger it (e.g. sun + heat).
    return cause.condition in CONDITIONS and _activity_raises(activity, cause.condition)


def _activity_raises(activity: Activity, condition: str) -> bool:
    """A simple table: which activities push which body conditions up."""
    table = {
        "cartwheels": {"heat", "thirst"},
        "running": {"heat", "thirst"},
        "skipping": {"heat"},
        "hide_and_seek": {"heat", "thirst"},
        "reading_quietly": {"thirst"},
    }
    return condition in table.get(activity.id, set())


def select_remedy(cause: Cause, available: list[Remedy]) -> Optional[Remedy]:
    """A remedy that actually neutralises the cause's condition."""
    for r in available:
        if r.target_condition == cause.condition:
            return r
    return None


def clue_hints(clue: Clue, cause: Cause) -> bool:
    """Does this clue point toward this cause at the right scene?"""
    return clue.hints_at == cause.id


# ---------------------------------------------------------------------------
# Prediction: the friend runs the world model forward on a copy to foresee the
# spell before deciding what to say.
# ---------------------------------------------------------------------------
def predict_spell(world: World, hero: Entity, activity: Activity) -> dict:
    """Simulate the activity silently and report whether the hero would swoon."""
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    return {
        "dizzy": sim.get(hero.id).meters["dizziness"] >= THRESHOLD,
        "thirst": sim.get(hero.id).meters["thirst"] >= THRESHOLD,
        "heat": sim.get(hero.id).meters["heat"] >= THRESHOLD,
    }


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def activity_detail(activity: Activity) -> str:
    return {
        "cartwheels": "the world spun every time she tipped upside down",
        "running": "the path flashed by under her shoes",
        "skipping": "the rope sang tap-tap-tap on the warm ground",
        "hide_and_seek": "every hiding spot felt like a tiny secret room",
        "reading_quietly": "the pages turned slowly and the sun made the paper glow",
    }.get(activity.id, "the afternoon felt full of motion")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"{setting.place.capitalize()} was cool and quiet."
    if setting.weather in {"sunny", "warm"}:
        return f"The sun pressed warmly on everything, and {setting.place} felt like one big bright blanket."
    return f"{setting.place.capitalize()} looked wide and ready for play."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["heat"] += 1
    actor.meters["thirst"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} with a small felt detective cap pulled over one ear.")


def has_friend(world: World, hero: Entity, friend: Entity) -> None:
    friend.memes["care"] += 1
    world.say(
        f"{friend.id} was the {friend.label} next door, and the two of them shared "
        f"a secret rule about {hero.pronoun('possessive')} detective cap."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved afternoons of {activity.gerund}; "
        f"{activity_detail(activity)}."
    )


def wears_cap(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{hero.id} wore the small felt detective cap that {friend.id} had made "
        f"for {hero.pronoun('object')} as a birthday gift."
    )


def arrive(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"One {world.weather or 'warm'} afternoon, {hero.id} and {friend.id} went "
        f"{where} to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def plays(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["play"] += 1
    world.say(
        f"{hero.id} spent a long while {activity.gerund}, laughing each time "
        f"{hero.pronoun()} tipped into another spin."
    )


def spell_begins(world: World, hero: Entity, cause: Cause) -> None:
    hero.meters["dizziness"] += 1
    hero.memes["vulnerability"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then a slow, swimmy feeling crept into {hero.pronoun('possessive')} head, "
        f"and {hero.pronoun()} sat down on the grass, blinking hard."
    )
    world.say(
        f"{hero.pronoun().capitalize()} whispered that {hero.pronoun()} thought "
        f"{hero.pronoun()} might swoon."
    )


def friend_sees(world: World, friend: Entity, clue: Clue, cause: Cause) -> None:
    friend.memes["care"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{friend.id} saw {friend.pronoun('possessive')} friend from across the path "
        f"and noticed three small things: the {clue.label} {clue.phrase}, "
        f"the warm sun on {clue.label} the bench, and the way {friend.pronoun('object')} "
        f"sat gripping the seat."
    )


def case_opened(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["reassurance"] += 1
    hero.memes["trust"] += 1
    world.say(
        f"{friend.id} walked over, tilted {friend.pronoun('possessive')} own detective cap, "
        f'and said softly, "Case opened, {hero.id}."'
    )


def diagnose(world: World, friend: Entity, hero: Entity, cause: Cause,
              activity: Activity) -> None:
    friend.memes["trust"] += 1
    hero.memes["trust"] += 1
    guess = {
        "thirst": (
            f"too many spins without a single sip of water, on a day this warm"
        ),
        "heat": (
            f"a lot of {activity.gerund} under a sun this bright, with no shade"
        ),
        "dizziness": (
            f"the spinning finally caught up with you, after no water at all"
        ),
    }.get(cause.condition, f"{activity.gerund} on a {world.weather or 'warm'} day")
    world.say(
        f'"{friend.id.capitalize()} guessed it was {guess}," '
        f"{friend.pronoun()} said, kneeling beside {hero.pronoun('object')}."
    )


def offer_remedy(world: World, friend: Entity, hero: Entity, remedy: Remedy) -> None:
    remedy_entity = world.add(Entity(
        id=f"remedy_{remedy.id}", type=remedy.target_condition,
        label=remedy.label, phrase=remedy.phrase,
        worn_by=hero.id, plural=remedy.plural,
    ))
    remedy_entity.worn_by = hero.id
    world.say(
        f"{friend.pronoun().capitalize()} {remedy.prep}, and {hero.id} took it slowly."
    )


def make_pillow(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["care"] += 1
    hero.meters["comfort"] += 1
    world.say(
        f"{friend.id} folded {friend.pronoun('possessive')} light jacket into a soft "
        f"pillow and slipped it behind {hero.pronoun('possessive')} back."
    )


def lean(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["reassurance"] += 1
    friend.memes["friendship"] += 1
    hero.memes["friendship"] += 1
    world.say(
        f"{hero.id} leaned on {friend.pronoun('possessive')} shoulder, "
        f"and the two of them sat very still for a few minutes."
    )


def recover(world: World, hero: Entity, friend: Entity, activity: Activity,
            remedy: Remedy) -> None:
    propagate(world, narrate=False)
    world.say(
        f"The swimmy feeling faded, and {hero.id} could stand up again."
    )
    world.say(
        f"They walked home together slowly, both of them still wearing their small "
        f"detective caps, and {hero.id} said, "
        f'"Case closed, friend. Thank you for the {remedy.label}."'
    )


# ---------------------------------------------------------------------------
# The screenplay: coarse three-act shape, driven entirely by the verbs above.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, cause: Cause, remedy: Remedy,
         clue: Clue, hero_name: str = "Pip", hero_type: str = "girl",
         friend_name: str = "Kit", friend_type: str = "boy",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else (setting.weather or activity.weather)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["bright", "spirited"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type, label="the friend",
        traits=["little", "kind", "watchful"],
    ))

    # Act 1 -- setup: who, what they love, the friendship rule.
    introduce(world, hero)
    has_friend(world, hero, friend)
    wears_cap(world, hero, friend)
    loves_activity(world, hero, activity)

    # Act 2 -- conflict: the activity runs into a spell; the friend investigates.
    world.para()
    arrive(world, hero, friend, activity)
    plays(world, hero, activity)
    spell_begins(world, hero, cause)
    friend_sees(world, friend, clue, cause)
    case_opened(world, friend, hero)
    diagnose(world, friend, hero, cause, activity)

    # Act 3 -- resolution: a remedy that fits the cause; a pillow; recovery.
    world.para()
    offer_remedy(world, friend, hero, remedy)
    make_pillow(world, friend, hero)
    lean(world, hero, friend)
    recover(world, hero, friend, activity, remedy)

    # Record facts for the Q&A generators (grounded in the simulated world).
    world.facts.update(
        hero=hero, friend=friend, activity=activity, cause=cause,
        remedy=remedy, clue=clue, setting=setting,
        conflict=hero.meters["dizziness"] >= THRESHOLD,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(place="the park", indoor=False, weather="sunny",
                    affords={"cartwheels", "running", "skipping", "hide_and_seek"}),
    "garden": Setting(place="the garden", indoor=False, weather="warm",
                      affords={"cartwheels", "skipping", "reading_quietly"}),
    "backyard": Setting(place="the backyard", indoor=False, weather="sunny",
                        affords={"running", "hide_and_seek", "skipping"}),
    "library": Setting(place="the library", indoor=True, weather="",
                       affords={"reading_quietly"}),
    "playground": Setting(place="the playground", indoor=False, weather="warm",
                          affords={"running", "hide_and_seek", "cartwheels"}),
}

ACTIVITIES = {
    "cartwheels": Activity(
        id="cartwheels", verb="doing cartwheels", gerund="doing cartwheels",
        rush="tipping into another spin", effort="spinning",
        needs_water=True, weather="sunny", keyword="cartwheels",
        tags={"spin", "dizzy", "play"},
    ),
    "running": Activity(
        id="running", verb="running", gerund="running laps",
        rush="sprinting another lap", effort="sprinting",
        needs_water=True, weather="sunny", keyword="running",
        tags={"run", "dizzy"},
    ),
    "skipping": Activity(
        id="skipping", verb="skipping rope", gerund="skipping rope",
        rush="skipping faster and faster", effort="skipping",
        needs_water=False, weather="warm", keyword="skipping",
        tags={"skip", "play"},
    ),
    "hide_and_seek": Activity(
        id="hide_and_seek", verb="playing hide and seek", gerund="playing hide and seek",
        rush="running to the next hiding spot", effort="sprinting",
        needs_water=True, weather="sunny", keyword="hide and seek",
        tags={"play", "dizzy"},
    ),
    "reading_quietly": Activity(
        id="reading_quietly", verb="reading quietly", gerund="reading a picture book",
        rush="turning another page", effort="sitting",
        needs_water=False, weather="", keyword="reading",
        tags={"read", "quiet"},
    ),
}

CAUSES = {
    "thirst": Cause(
        id="thirst", label="thirst", phrase="not drinking any water",
        condition="thirst", remedy="water", remedy_action="drink",
        genders={"girl", "boy"},
    ),
    "heat": Cause(
        id="heat", label="too much sun", phrase="playing under a hot sun",
        condition="heat", remedy="water", remedy_action="sip",
        genders={"girl", "boy"},
    ),
    "dizziness": Cause(
        id="dizziness", label="spinning too much", phrase="spinning more than the body can take",
        condition="dizziness", remedy="rest", remedy_action="sit still",
        genders={"girl", "boy"},
    ),
}

REMEDIES = {
    "water": Remedy(
        id="water", label="cool water", phrase="a small bottle of cool water",
        target_condition="thirst",
        prep="offered a small bottle of cool water",
        tail="shared the last cool water",
        plural=False,
    ),
    "shade": Remedy(
        id="shade", label="shade", phrase="a shady patch under the old tree",
        target_condition="heat",
        prep="led the way to a shady patch under the old tree",
        tail="sat together in the cool shade",
        plural=False,
    ),
    "rest": Remedy(
        id="rest", label="quiet rest", phrase="a few quiet minutes of rest",
        target_condition="dizziness",
        prep="asked everyone to be very still and quiet for a moment",
        tail="shared a few quiet minutes together",
        plural=True,
    ),
}

CLUES = {
    "bottle": Clue(
        id="bottle", label="empty water bottle", phrase="sitting on the bench beside her",
        hints_at="thirst", place="park",
    ),
    "sun": Clue(
        id="sun", label="warm sun", phrase="beating down on the grass",
        hints_at="heat", place="garden",
    ),
    "rope": Clue(
        id="rope", label="skipping rope", phrase="lying in a tangled loop nearby",
        hints_at="dizziness", place="backyard",
    ),
    "book": Clue(
        id="book", label="picture book", phrase="still open on the bench beside her",
        hints_at="thirst", place="library",
    ),
    "shed": Clue(
        id="shed", label="play shed", phrase="with the door left open in the sun",
        hints_at="heat", place="playground",
    ),
}

GIRL_NAMES = ["Pip", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Kit", "Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli"]


def valid_combos() -> list[tuple]:
    """(place, activity, cause, remedy, clue) tuples that pass the constraints."""
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for cause_id, cause in CAUSES.items():
                if not _activity_raises(act, cause.condition):
                    continue
                remedy = select_remedy(cause, list(REMEDIES.values()))
                if remedy is None:
                    continue
                # the clue must be available at this place
                clues_here = [c for c in CLUES.values() if c.place == place]
                for clue in clues_here:
                    if clue_hints(clue, cause):
                        out.append((place, act_id, cause_id, remedy.id, clue.id))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific; the generic StorySample/QAItem live in
# storyworlds/results.py).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    cause: str
    remedy: str
    clue: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "swoon": [
        ("What does it mean to swoon?",
         "To swoon is to feel so dizzy or tired that you have to sit or lie down "
         "for a little while until the feeling passes.")],
    "dizzy": [
        ("Why do people feel dizzy after spinning around?",
         "When you spin quickly, the liquid inside your ears sloshes around, and "
         "your eyes and ears send mixed messages to your brain, so it feels like "
         "the world is tilting.")],
    "detective": [
        ("What does a detective do?",
         "A detective looks closely at small clues and tries to figure out what "
         "happened, just like a careful puzzle solver.")],
    "friendship": [
        ("What makes a good friend?",
         "A good friend notices when you need help, comes over to ask, and stays "
         "with you until you feel better.")],
    "water": [
        ("Why is drinking water important on a hot day?",
         "Drinking water replaces the wetness your body loses as sweat, so you "
         "stay cool and your head does not feel swimmy.")],
    "shade": [
        ("What is shade?",
         "Shade is the cool, dark place you find under a tree or awning when the "
         "sun is too bright and hot.")],
    "cartwheels": [
        ("What is a cartwheel?",
         "A cartwheel is a sideways roll where you put your hands on the ground "
         "and your legs go up over your head one after the other.")],
    "skipping": [
        ("What is a skipping rope?",
         "A skipping rope is a long rope you swing over your head and under your "
         "feet while you hop, sometimes fast and sometimes slow.")],
    "hide_and_seek": [
        ("What is hide and seek?",
         "Hide and seek is a game where one person counts and the others hide, "
         "and then the counter tries to find them one by one.")],
}
KNOWLEDGE_ORDER = ["swoon", "dizzy", "detective", "friendship", "water",
                   "shade", "cartwheels", "skipping", "hide_and_seek"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    act, cause, remedy = f["activity"], f["cause"], f["remedy"]
    kw = act.keyword or act.id
    return [
        f'Write a short gentle story for a 3-to-5-year-old about friendship '
        f'and feeling dizzy, that includes the word "{kw}".',
        f"Tell a detective-style story where {hero.id} gets a dizzy spell while "
        f"{hero.pronoun('subject')} is {act.gerund}, and {friend.id} notices small "
        f"clues and figures out the cause, then helps with {remedy.label}.",
        f'Write a simple story that uses the word "swoon" and ends with two '
        f"friends walking home together slowly, both wearing detective caps.",
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, friend = f["hero"], f["friend"]
    act, cause, remedy, clue = f["activity"], f["cause"], f["remedy"], f["clue"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    fsub, fobj, fpos = (friend.pronoun("subject"), friend.pronoun("object"),
                       friend.pronoun("possessive"))
    place = world.setting.place
    day = {"sunny": "sunny afternoon", "warm": "warm afternoon",
           "rainy": "rainy afternoon"}.get(world.weather, "afternoon")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} feels dizzy at {place} "
                f"and {friend.id} comes to help?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"the {friend.label} next door, named {friend.id}. They share a "
                f"secret rule about their detective caps."
            ),
        ),
        QAItem(
            question=(
                f"What was {trait} {hero.id} doing {day} at {place} before the "
                f"dizzy spell began?"
            ),
            answer=(
                f"{hero.id} was {act.gerund} for a long time. {activity_detail(act)} "
                f"That long, busy play is what set up the spell."
            ),
        ),
        QAItem(
            question=(
                f"Why did {hero.id} think {sub} might swoon while {act.gerund} "
                f"at {place}?"
            ),
            answer=(
                f"A slow, swimmy feeling crept into {pos} head, and {sub} had to "
                f"sit down on the grass and grip the bench to keep from tipping "
                f"over. {sub.capitalize()} whispered that {sub} thought {sub} might swoon."
            ),
        ),
        QAItem(
            question=(
                f"What three small clues did {friend.id} notice when {fsub} saw "
                f"{hero.id} feeling dizzy at {place}?"
            ),
            answer=(
                f"{friend.id} noticed the {clue.label} {clue.phrase}, the warm sun "
                f"on {clue.label} the bench, and the way {hero.id} sat gripping the "
                f"seat. Each small thing pointed to the same answer."
            ),
        ),
        QAItem(
            question=(
                f"What secret phrase did {friend.id} say when {fsub} tipped "
                f"{fpos} detective cap to {hero.id}?"
            ),
            answer=(
                f'{friend.id} said softly, "Case opened, {hero.id}." That was '
                f"their special rule for when one of them needed help."
            ),
        ),
        QAItem(
            question=(
                f"What did {friend.id} guess was the cause of {pos} dizzy spell?"
            ),
            answer=(
                f"{friend.id} guessed it was {cause.phrase} on a {day} at {place}. "
                f"That was the cause of the spell, and it told {friend.id} what "
                f"{fsub} needed to do next."
            ),
        ),
        QAItem(
            question=(
                f"How did {friend.id} help {hero.id} recover from the spell at {place}?"
            ),
            answer=(
                f"{friend.id} {remedy.prep}, then folded {fpos} jacket into a soft "
                f"pillow behind {hero.pronoun('possessive')} back. {hero.id} leaned "
                f"on {friend.id}'s shoulder, the dizzy feeling faded, and they "
                f"walked home together slowly."
            ),
        ),
        QAItem(
            question=(
                f"How did the two friends feel at the end of the {day} at {place}?"
            ),
            answer=(
                f"{hero.id} and {friend.id} both felt their friendship stronger, "
                f"and they walked home together slowly, still wearing their small "
                f"detective caps. {hero.id} said, \"Case closed, friend.\""
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = set(f["activity"].tags) | {"friendship", "swoon", "dizzy", "detective"}
    tags.add(f["cause"].id)
    tags.add(f["remedy"].id)
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="park", activity="cartwheels", cause="thirst",
        remedy="water", clue="bottle",
        hero_name="Pip", hero_gender="girl",
        friend_name="Kit", friend_gender="boy",
    ),
    StoryParams(
        place="garden", activity="reading_quietly", cause="thirst",
        remedy="water", clue="book",
        hero_name="Mia", hero_gender="girl",
        friend_name="Nora", friend_gender="girl",
    ),
    StoryParams(
        place="playground", activity="running", cause="heat",
        remedy="shade", clue="shed",
        hero_name="Ben", hero_gender="boy",
        friend_name="Sam", friend_gender="boy",
    ),
    StoryParams(
        place="backyard", activity="skipping", cause="dizziness",
        remedy="rest", clue="rope",
        hero_name="Zoe", hero_gender="girl",
        friend_name="Ella", friend_gender="girl",
    ),
    StoryParams(
        place="park", activity="hide_and_seek", cause="thirst",
        remedy="water", clue="bottle",
        hero_name="Leo", hero_gender="boy",
        friend_name="Max", friend_gender="boy",
    ),
]


def explain_rejection(activity: Activity, cause: Cause) -> str:
    return (f"(No story: {activity.gerund} doesn't raise {cause.condition}, "
            f"so the detective friend has no honest cause to name. "
            f"Try a cause that matches {activity.id}.)")


def explain_clue(clue: Clue, place: str) -> str:
    return (f"(No story: the {clue.label} belongs at {clue.place}, not at "
            f"{place}. Pick a clue that lives where the story happens.)")


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of the reasonableness gate.
# Inline rules; facts emitted from the registries.  The shared `asp` helper is
# imported lazily so the prose engine runs without clingo.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% An activity raises the conditions in EFFORT for that activity.
raises(A, C) :- activity(A), effect_of(A, C).

% A cause is plausible when it names a condition the activity raises.
plausible_cause(A, Cause) :- raises(A, C), cause(Cause, C).

% A remedy fits a cause when its target_condition matches the cause's condition.
fits(R, Cause) :- remedy(R, T), cause(Cause, C), T = C.

% A clue points at a cause when hints_at matches.
points_at(Clue, Cause) :- clue(Clue), hints(Clue, Cause).

% A story is valid when the place affords the activity, the cause is plausible
% for the activity, the remedy fits the cause, and the clue lives at the place
% and points at the cause.
valid(Place, A, Cause, R, Clue) :-
    affords(Place, A), plausible_cause(A, Cause), fits(R, Cause),
    clue_at(Place, Clue), points_at(Clue, Cause).
"""


def asp_facts() -> str:
    """Emit the registries above as ASP base facts."""
    import asp
    lines: list[str] = []
    effect_table = {
        "cartwheels": {"heat", "thirst"},
        "running": {"heat", "thirst"},
        "skipping": {"heat"},
        "hide_and_seek": {"heat", "thirst"},
        "reading_quietly": {"thirst"},
    }
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for c in sorted(effect_table.get(aid, set())):
            lines.append(asp.fact("effect_of", aid, c))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid, c.condition))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid, r.target_condition))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_at", c.place, cid))
        lines.append(asp.fact("hints", cid, c.hints_at))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    """Clingo's version of valid_combos(): 5-tuples (place, activity, cause, remedy, clue)."""
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    """Check the inline ASP gate agrees with the Python valid_combos()."""
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
# Standard storyworld interface (see storyworlds/AGENTS.md).
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a swoon, a friend, a detective-style care. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    """Fill in any unspecified choices at random, keeping the combo reasonable."""
    if args.activity and args.cause:
        act, c = ACTIVITIES[args.activity], CAUSES[args.cause]
        if not _activity_raises(act, c.condition):
            raise StoryError(explain_rejection(act, c))
    if args.clue and args.place and CLUES[args.clue].place != args.place:
        raise StoryError(explain_clue(CLUES[args.clue], args.place))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.cause is None or c[2] == args.cause)
              and (args.remedy is None or c[3] == args.remedy)
              and (args.clue is None or c[4] == args.clue)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, cause_id, remedy_id, clue_id = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = args.friend_name or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place, activity=activity, cause=cause_id, remedy=remedy_id, clue=clue_id,
        hero_name=hero_name, hero_gender=hero_gender,
        friend_name=friend_name, friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity],
        CAUSES[params.cause], REMEDIES[params.remedy], CLUES[params.clue],
        params.hero_name, params.hero_gender,
        params.friend_name, params.friend_gender,
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, cause, remedy, clue) combos:\n")
        for place, act, cause_id, remedy_id, clue_id in triples:
            print(f"  {place:10} {act:16} {cause_id:9} {remedy_id:6} {clue_id}")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
