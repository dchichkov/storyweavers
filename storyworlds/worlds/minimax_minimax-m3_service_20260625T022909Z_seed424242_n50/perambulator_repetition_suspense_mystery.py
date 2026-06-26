#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/perambulator_repetition_suspense_mystery.py
======================================================================================================================

A standalone *story world* sketch for "The Perambulator" tale and close,
constraint-checked variations of it.

Initial story (used to build a world model):
---
Once upon a time, there was a small, careful girl named Nora who lived in a tall,
narrow house at the edge of Maple Lane. Nora was just tall enough now to push
the handle of the family's heavy old perambulator, and she was proud of that.

In the mornings her father would wheel the perambulator out to the gate and
Nora would wheel it back up the garden path, around the lavender bush, and into
the little wooden shed beside the kitchen door. She did this every morning.

One morning Nora pushed the perambulator up the path, and she noticed that the
left wheel did not sing the way it used to. She stopped. She looked. She tilted
the perambulator back on its two wheels. She listened. She turned it slowly.
She could not find what was wrong.

She brought the perambulator to her father. Her father smiled and said,
"Let's find the missing thing together." They looked at the shed. They looked
at the path. They looked at the lavender bush. They looked at the gate. They
looked, and they listened, and they did not find it.

Then her father reached under the seat, and pulled out a small, smooth, blue
marble that Nora's little brother had hidden there the day before. Nora's eyes
went wide. "So THAT was the mystery of the squeaky wheel," she said, and she
hugged the perambulator like a friend.

Causal state updates:
---
    wheel rolls on path          -> wheel.song += 1
    wheel silent                 -> suspicion += 1
    stop, look, tilt, listen     -> carefulness += 1
    finding the hidden thing     -> relief += 1, mystery cleared

Scripted social/emotional beats:
---
    repeating the search         -> calm persistence
    clue noticed                 -> curiosity += 1
    resolution                   -> joy += 1
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

THRESHOLD = 1.0

# Hidden-object kinds that can lodge inside a perambulator and silence a wheel.
HIDDEN_KINDS = {"marble", "pebble", "acorn", "button", "leaf"}

# Body regions of the perambulator (each one can hold a hidden thing).
REGIONS = {"front_wheel", "back_wheel", "under_seat", "handle", "basket"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, father, perambulator ...
    label: str = ""                # short reference, e.g. "perambulator", "marble"
    phrase: str = ""               # full noun phrase
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    region: str = ""                  # which part of the perambulator this is
    hidden_in: Optional[str] = None   # id of the perambulator hiding this thing
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"father": "dad", "mother": "mom"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the garden path"
    indoor: bool = False
    affordance: str = "wheel"      # the action the place supports: "wheel"


@dataclass
class Route:
    """A short list of waypoints the hero pushes the perambulator through."""
    waypoints: list[str]           # e.g. ["the gate", "the lavender bush", "the shed"]
    length: int


@dataclass
class Pram:
    """The perambulator at the centre of every story."""
    id: str
    label: str
    phrase: str
    wheel_song: str                # onomatopoeia: "soft chug-chug", "tiny rattle"
    broken_sound: str              # what an unbalanced wheel does: "small clunk"
    colors: set[str] = field(default_factory=set)
    wheel_count: int = 4
    plural: bool = False


@dataclass
class HiddenThing:
    """A small object that can lodge in a wheel region and silence it."""
    id: str
    label: str
    phrase: str
    owner_role: str = "little brother"   # who typically put it there
    seed_region: str = "front_wheel"     # default hiding spot


@dataclass
class Helper:
    """A second character who helps search for the missing thing."""
    id: str
    type: str          # father | mother | older sister
    phrase: str


# ---------------------------------------------------------------------------
# World: entity store + narration history.
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting, route: Route) -> None:
        self.setting = setting
        self.route = route
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = "clear"
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def hidden_things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.hidden_in]

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
        clone = World(self.setting, self.route)
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


def _r_wheel_silent(world: World) -> list[str]:
    """A hidden thing in a wheel region silences the wheel's song."""
    out: list[str] = []
    for pram in [e for e in world.entities.values() if e.type == "perambulator"]:
        for thing in world.hidden_things():
            sig = ("silent", pram.id, thing.id)
            if sig in world.fired:
                continue
            if thing.hidden_in != pram.id:
                continue
            if thing.region not in {"front_wheel", "back_wheel"}:
                continue
            world.fired.add(sig)
            pram.meters["song"] = 0.0
            pram.meters["broken"] += 1
            out.append("__silent__")
    return out


def _r_suspicion(world: World) -> list[str]:
    """Wheel broken -> suspicion rises; the child wonders what changed."""
    for pram in [e for e in world.entities.values() if e.type == "perambulator"]:
        if pram.meters["broken"] < THRESHOLD:
            continue
        sig = ("suspicion", pram.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for actor in world.characters():
            actor.memes["suspicion"] += 1
        return ["__suspicion__"]
    return []


def _r_search(world: World) -> list[str]:
    """Repeated stop/look/listen -> carefulness rises; the search is real."""
    for actor in world.characters():
        if actor.memes["search_steps"] < 3:
            continue
        sig = ("search", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["carefulness"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    """When a hidden thing is found and removed -> relief + cleared mystery."""
    for thing in list(world.hidden_things()):
        if thing.meters["found"] < THRESHOLD:
            continue
        sig = ("relief", thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for actor in world.characters():
            actor.memes["relief"] += 1
            actor.memes["suspicion"] = 0.0
        return ["__relief__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="silent", tag="physical", apply=_r_wheel_silent),
    Rule(name="suspicion", tag="emotional", apply=_r_suspicion),
    Rule(name="search", tag="emotional", apply=_r_search),
    Rule(name="relief", tag="emotional", apply=_r_relief),
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
# Constraint helpers.
# ---------------------------------------------------------------------------
def hidden_kind_fits(thing: HiddenThing, pram: Pram) -> bool:
    """A hidden object only matters if its region is one the pram actually has.

    Both perambulators have front_wheel and back_wheel, but the basket/handle
    only exist on full-sized ones.  We require that the thing's seed region is
    a region on this pram."""
    available = {"front_wheel", "back_wheel", "under_seat", "handle", "basket"}
    if pram.wheel_count < 4:
        available = {"front_wheel", "back_wheel", "under_seat", "handle"}
    return thing.seed_region in available


def select_helper(hero: Entity, helper_type: Optional[str]) -> Helper:
    """Pick a helper consistent with the hero and an optional pin."""
    options = [h for h in HELPERS if helper_type is None or h.type == helper_type]
    if not options:
        options = HELPERS
    cfg = random.choice(options)
    return cfg


def explain_rejection(thing: HiddenThing, pram: Pram) -> str:
    return (
        f"(No story: a {thing.label} could not lodge in this kind of "
        f"{pram.label} because it doesn't have a '{thing.seed_region}'. "
        f"Try a different hidden object.)"
    )


# ---------------------------------------------------------------------------
# Prediction: simulate the wheel roll silently to see whether the song is broken.
# ---------------------------------------------------------------------------
def predict_broken(world: World, pram_id: str, thing_id: str) -> dict:
    sim = world.copy()
    thing = sim.entities[thing_id]
    thing.hidden_in = pram_id
    _r_wheel_silent(sim)
    pram = sim.entities[pram_id]
    return {"broken": pram.meters["broken"] >= THRESHOLD}


# ---------------------------------------------------------------------------
# Verbs: each mutates state and (optionally) narrates.
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every small sound in the lane.")


def knows_the_routine(world: World, hero: Entity, pram: Entity, route: Route) -> None:
    hero.memes["routine"] += 1
    world.say(
        f"Every morning {hero.pronoun('subject')} wheeled the "
        f"{pram.label} up {world.setting.place}, past {route.waypoints[0]}, "
        f"and on to {route.waypoints[-1]}."
    )
    world.say(
        f"The {pram.label} had a {pram.wheel_song} that went with each step, and "
        f"{hero.id} liked that song very much."
    )


def father_brings_out(world: World, helper: Entity, pram: Entity) -> None:
    helper.memes["carefulness"] += 1
    world.say(
        f"That morning {helper.id} wheeled the {pram.label} out to the gate, and "
        f"{helper.pronoun('subject')} handed {helper.pronoun('object')} the handle."
    )


def hero_takes_over(world: World, hero: Entity, pram: Entity) -> None:
    world.say(
        f"{hero.id} gripped the handle with both hands, smiled, and pushed off."
    )


def route_journey(world: World, hero: Entity, pram: Entity, route: Route) -> None:
    world.say(
        f"{hero.id.capitalize()} rolled the {pram.label} along "
        f"{world.setting.place}, past {route.waypoints[0]}, by "
        f"{route.waypoints[1] if len(route.waypoints) > 1 else 'the bend'}, and on."
    )
    pram.meters["song"] += 1
    world.say(
        f"At first the {pram.wheel_song} was right on time, the way it always was."
    )


def notices_silence(world: World, hero: Entity, pram: Entity, route: Route) -> None:
    hero.memes["suspicion"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"But then, near {route.waypoints[0]}, {hero.id} heard something different."
    )
    world.say(
        f"One wheel of the {pram.label} was quiet. Instead of its usual "
        f"{pram.wheel_song}, it gave a small {pram.broken_sound} with every turn."
    )
    propagate(world, narrate=False)


def search(world: World, hero: Entity, helper: Entity, pram: Entity,
           route: Route) -> None:
    """The repeated search -- stops at each waypoint (Suspense + Repetition)."""
    stops = route.waypoints
    for wp in stops:
        hero.memes["search_steps"] += 1
        world.say(
            f"They stopped at {wp}. {hero.id} looked at the {pram.label}. "
            f"{hero.id} listened. {hero.id} tilted it back on two wheels and "
            f"turned it slowly. {hero.id} did not see what was wrong."
        )
        propagate(world, narrate=False)


def helper_looks(world: World, helper: Entity, pram: Entity, hero: Entity) -> None:
    helper.memes["carefulness"] += 1
    helper.memes["search_steps"] += 1
    world.say(
        f'{helper.id} crouched down and looked under the seat. '
        f'"{I do not see it yet,"} {helper.pronoun("subject")} said kindly. '
        f'"Let us look again, slowly."'
    )


def father_finds(world: World, helper: Entity, pram: Entity, thing: Entity) -> None:
    """Reach into the wheel region and pull out the hidden thing -- resolution."""
    thing.meters["found"] += 1
    world.say(
        f"Then {helper.id} reached carefully into the wheel housing, felt around, "
        f"and pulled out {thing.phrase}."
    )
    propagate(world, narrate=False)


def reveal(world: World, hero: Entity, helper: Entity, pram: Entity,
           thing: Entity, route: Route) -> None:
    world.say(
        f"{hero.id} gasped. \"That is the mystery of the {pram.broken_sound},\" "
        f"{hero.pronoun('subject')} said, very quietly at first."
    )
    world.say(
        f"{helper.id} smiled and nodded. {helper.pronoun('subject').capitalize()} "
        f"told {hero.id} that {thing.owner_role} had hidden {thing.it()} there the "
        f"day before, and the wheel had not been able to sing over it."
    )


def song_returns(world: World, hero: Entity, helper: Entity, pram: Entity,
                 route: Route) -> None:
    """The closing image: the wheel's song comes back, and they push on."""
    pram.meters["song"] += 1
    pram.meters["broken"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id.capitalize()} set the {pram.label} down. "
        f"The first push made a clean, happy {pram.wheel_song}, the way it used to."
    )
    world.say(
        f"{hero.id} hugged the {pram.label} once, like an old friend, and then "
        f"{hero.pronoun('subject')} and {helper.id} wheeled it the rest of the way "
        f"to {route.waypoints[-1]}, humming a little as they went."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, route: Route, pram_cfg: Pram, thing_cfg: HiddenThing,
         helper_cfg: Helper, hero_name: str = "Nora", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting, route)
    world.weather = "clear"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["careful", "observant"]),
    ))
    helper = world.add(Entity(
        id="Helper", kind="character", type=helper_cfg.type, label="the helper",
        phrase=helper_cfg.phrase,
    ))
    pram = world.add(Entity(
        id="pram", type="perambulator", label=pram_cfg.label,
        phrase=pram_cfg.phrase, owner="family",
        meters={"song": 0.0, "broken": 0.0},
        plural=pram_cfg.plural,
    ))
    thing = world.add(Entity(
        id="thing", type="hidden_object", label=thing_cfg.label,
        phrase=thing_cfg.phrase, owner=thing_cfg.owner_role,
        region=thing_cfg.seed_region,
    ))
    # Place the hidden thing inside the perambulator so the search has stakes.
    thing.hidden_in = pram.id

    # Act 1 -- setup: routine, the perambulator's song, the helper's hand-off.
    introduce(world, hero)
    knows_the_routine(world, hero, pram, route)
    father_brings_out(world, helper, pram)
    hero_takes_over(world, hero, pram)

    # Act 2 -- the search: journey, notice silence, repeat at each waypoint.
    world.para()
    route_journey(world, hero, pram, route)
    notices_silence(world, hero, pram, route)
    search(world, hero, helper, pram, route)
    helper_looks(world, helper, pram, hero)

    # Act 3 -- resolution: reach in, find the thing, song returns.
    world.para()
    father_finds(world, helper, pram, thing)
    reveal(world, hero, helper, pram, thing, route)
    song_returns(world, hero, helper, pram, route)

    # Record facts for Q&A generation.
    world.facts.update(
        hero=hero, helper=helper, pram=pram, thing=thing,
        pram_cfg=pram_cfg, thing_cfg=thing_cfg, helper_cfg=helper_cfg,
        setting=setting, route=route,
        suspicion=hero.memes["suspicion"] >= THRESHOLD,
        resolved=thing.meters["found"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden_path": Setting(place="the garden path", indoor=False, affordance="wheel"),
    "driveway": Setting(place="the long driveway", indoor=False, affordance="wheel"),
    "lane": Setting(place="the quiet lane", indoor=False, affordance="wheel"),
}

ROUTES = {
    # Two-stop routes (gate -> shed) -- for shorter stories.
    "short": Route(waypoints=["the gate", "the little wooden shed"], length=2),
    # Three-stop routes (gate -> bush -> door) -- more waypoints = more suspense.
    "long": Route(waypoints=["the gate", "the lavender bush", "the kitchen door"], length=3),
}

PRAMS = {
    "old_pram": Pram(
        id="old_pram",
        label="old perambulator",
        phrase="the family's heavy old perambulator",
        wheel_song="soft chug-chug",
        broken_sound="clunk",
        colors={"blue", "green"},
        wheel_count=4,
    ),
    "light_pram": Pram(
        id="light_pram",
        label="light perambulator",
        phrase="the family's light blue perambulator",
        wheel_song="tiny rattle",
        broken_sound="tap",
        colors={"blue"},
        wheel_count=3,                # no basket region
    ),
}

HIDDEN_THINGS = {
    "marble": HiddenThing(
        id="marble", label="marble", phrase="a small, smooth, blue marble",
        owner_role="little brother", seed_region="front_wheel",
    ),
    "pebble": HiddenThing(
        id="pebble", label="pebble", phrase="a tiny round pebble",
        owner_role="little brother", seed_region="back_wheel",
    ),
    "acorn": HiddenThing(
        id="acorn", label="acorn", phrase="a fat little acorn",
        owner_role="little sister", seed_region="under_seat",
    ),
    "button": HiddenThing(
        id="button", label="button", phrase="a bright yellow button",
        owner_role="little brother", seed_region="basket",
    ),
    "leaf": HiddenThing(
        id="leaf", label="leaf", phrase="a crinkly dry leaf",
        owner_role="the cat", seed_region="front_wheel",
    ),
}

HELPERS = [
    Helper(id="Father", type="father", phrase="her father, who was very patient"),
    Helper(id="Mother", type="mother", phrase="her mother, who was very patient"),
    Helper(id="Sister", type="older sister", phrase="her older sister, who was very patient"),
]

GIRL_NAMES = ["Nora", "Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "observant", "patient", "quiet", "thoughtful", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    """(place, route, pram, thing) -- only compatible stories."""
    combos = []
    for place, setting in SETTINGS.items():
        for route_id, route in ROUTES.items():
            for pram_id, pram in PRAMS.items():
                for thing_id, thing in HIDDEN_THINGS.items():
                    if hidden_kind_fits(thing, pram):
                        combos.append((place, route_id, pram_id, thing_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters (domain-specific).
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    route: str
    pram: str
    thing: str
    helper: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation -- three deliberately separate sets.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "perambulator": [
        ("What is a perambulator?",
         "A perambulator is a small wheeled cart used for pushing a baby or "
         "toddler around, with a seat, a handle for pushing, and wheels that "
         "turn as you walk."),
    ],
    "wheel": [
        ("Why does a wheel sometimes squeak?",
         "A wheel can squeak when something small gets caught in it, like a "
         "pebble or a piece of grit, or when the metal pin in the middle needs "
         "a drop of oil."),
    ],
    "marble": [
        ("What is a marble?",
         "A marble is a small, round glass ball that children like to roll and "
         "collect. It is hard and smooth, and it can roll a long way."),
    ],
    "pebble": [
        ("What is a pebble?",
         "A pebble is a small, smooth stone you can pick up off the ground, "
         "usually round from being tumbled in water."),
    ],
    "acorn": [
        ("What is an acorn?",
         "An acorn is the seed of an oak tree. It has a little brown cap and "
         "squirrels love to hide them for the winter."),
    ],
    "button": [
        ("What is a button?",
         "A button is a small, flat disk with holes in the middle, used to "
         "fasten a coat or shirt."),
    ],
    "leaf": [
        ("Why are some leaves dry and crinkly?",
         "A leaf goes dry and crinkly in autumn when it loses its water and "
         "lets go of the tree, ready to fall."),
    ],
    "routine": [
        ("Why do children like doing the same small job each morning?",
         "Repeating a small job each morning helps a child feel capable and "
         "important, and the familiar pattern feels safe and steady."),
    ],
    "suspense": [
        ("What does suspense mean in a story?",
         "Suspense is the feeling of waiting to find out what happens next, "
         "like when you have stopped to listen for a missing sound."),
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is a small puzzle -- something happened that you cannot "
         "explain yet, and you have to look carefully to find the answer."),
    ],
    "careful": [
        ("Why does being careful help when something is wrong?",
         "Being careful -- slowing down, looking, and listening -- gives your "
         "eyes and ears a chance to notice the small thing that was missed."),
    ],
}
KNOWLEDGE_ORDER = ["perambulator", "wheel", "marble", "pebble", "acorn",
                   "button", "leaf", "routine", "suspense", "mystery", "careful"]


def generation_prompts(world: World) -> list[str]:
    """(1) The 'asks' that would make a story like this one."""
    f = world.facts
    hero, helper, thing, pram = f["hero"], f["helper"], f["thing_cfg"], f["pram_cfg"]
    route = f["route"]
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small '
        f'mystery at home" that includes the word "perambulator".',
        f'Tell a gentle mystery story where a careful {hero.type} named '
        f'{hero.id} notices that the {pram.label} sounds different, and '
        f'searches with {helper.label_word} until they find {thing.phrase}.',
        f'Write a simple story that uses the noun "{thing.label}" and ends '
        f'with the {pram.label}\'s song returning after a careful search.',
    ]


def story_qa(world: World) -> list[QAItem]:
    """(2) Questions answerable from the text/world of THIS story."""
    f = world.facts
    hero, helper, thing, pram = (f["hero"], f["helper"], f["thing_cfg"],
                                 f["pram_cfg"])
    route = f["route"]
    pw = helper.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    waypoints = route.waypoints

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"What small job did {trait} {hero.id} do every morning at "
                f"{world.setting.place} before the {pram.label} sounded wrong?"
            ),
            answer=(
                f"Every morning {hero.id} wheeled the {pram.label} up "
                f"{world.setting.place}, past {waypoints[0]}, and on to "
                f"{waypoints[-1]}, listening to its {pram.wheel_song}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} notice was different about the "
                f"{pram.label} near {waypoints[0]}?"
            ),
            answer=(
                f"Near {waypoints[0]}, one wheel of the {pram.label} had stopped "
                f"singing. Instead of its usual {pram.wheel_song}, it gave a "
                f"small {pram.broken_sound} with every turn."
            ),
        ),
        QAItem(
            question=(
                f"How did {trait} {hero.id} and {pw} search for the missing "
                f"thing in the {pram.label}?"
            ),
            answer=(
                f"They stopped at each waypoint -- {', '.join(waypoints[:-1])}, "
                f"and finally {waypoints[-1]} -- and at each stop {hero.id} "
                f"looked, listened, tilted the {pram.label} back on two wheels, "
                f"and turned it slowly. They did not see what was wrong at "
                f"first, so they tried again, slowly."
            ),
        ),
    ]

    if f.get("resolved"):
        qa.append(QAItem(
            question=(
                f"What did {pw} finally find inside the {pram.label}, and how "
                f"did it explain the {pram.broken_sound}?"
            ),
            answer=(
                f"{pw.capitalize()} reached into the {pram.label} and pulled out "
                f"{thing.phrase}, which {thing.owner_role} had hidden there the "
                f"day before. The wheel had not been able to sing over it, which "
                f"is why the {pram.broken_sound} had appeared."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel when the {pram.label}\'s song "
                f"came back at the end of the search?"
            ),
            answer=(
                f"{hero.id} felt relieved and happy. The first push after the "
                f"thing was gone made a clean {pram.wheel_song} again, and "
                f"{hero.id} hugged the {pram.label} before rolling it on to "
                f"{waypoints[-1]}."
            ),
        ))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    """(3) Generic, child-level questions about the world's elements."""
    f = world.facts
    tags = {f["pram_cfg"].id, f["thing_cfg"].id}
    tags.add("perambulator")
    tags.add("wheel")
    tags.add("mystery")
    tags.add("suspense")
    tags.add("careful")
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
# CLI / trace.
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# Curated, constraint-valid set (used by --all).
CURATED = [
    StoryParams(
        place="garden_path", route="long", pram="old_pram",
        thing="marble", helper="father",
        name="Nora", gender="girl", trait="careful",
    ),
    StoryParams(
        place="driveway", route="short", pram="light_pram",
        thing="pebble", helper="mother",
        name="Tim", gender="boy", trait="observant",
    ),
    StoryParams(
        place="lane", route="long", pram="old_pram",
        thing="acorn", helper="father",
        name="Lily", gender="girl", trait="patient",
    ),
    StoryParams(
        place="garden_path", route="short", pram="old_pram",
        thing="button", helper="Sister",
        name="Ben", gender="boy", trait="thoughtful",
    ),
    StoryParams(
        place="lane", route="short", pram="light_pram",
        thing="leaf", helper="mother",
        name="Mia", gender="girl", trait="gentle",
    ),
]


def explain_rejection(thing: HiddenThing, pram: Pram) -> str:
    return (
        f"(No story: a {thing.label} cannot lodge in the {pram.label} because "
        f"it has no '{thing.seed_region}'. Try a different hidden object.)"
    )


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner -- the declarative twin of valid_combos().
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A hidden thing fits a perambulator only if the pram has the right region.
fits(P, T) :- pram(P), thing(T), has_region(P, R), seed_region(T, R).

% A story is valid when its (place, route, pram, thing) tuple is all consistent.
valid(Place, Route, P, T) :- setting(Place), route(Route), fits(P, T).

% Show one tuple at a time.
"""

ASP_FACTS = ""

def _build_asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("affordance", sid, s.affordance))
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        lines.append(asp.fact("route_length", rid, r.length))
    for pid, p in PRAMS.items():
        lines.append(asp.fact("pram", pid))
        available = {"front_wheel", "back_wheel", "under_seat", "handle", "basket"}
        if p.wheel_count < 4:
            available = {"front_wheel", "back_wheel", "under_seat", "handle"}
        for r in sorted(available):
            lines.append(asp.fact("has_region", pid, r))
    for tid, t in HIDDEN_THINGS.items():
        lines.append(asp.fact("thing", tid))
        lines.append(asp.fact("seed_region", tid, t.seed_region))
    return "\n".join(lines)


def asp_facts() -> str:
    return _build_asp_facts()


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
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
# Standard storyworld interface.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a small mystery around a perambulator. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--pram", choices=PRAMS)
    ap.add_argument("--thing", choices=HIDDEN_THINGS)
    ap.add_argument("--helper", choices=[h.type for h in HELPERS])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    """Fill in any unspecified choices at random, keeping the combo reasonable.

    Raises StoryError if the explicit options describe an invalid story."""
    if args.pram and args.thing and not hidden_kind_fits(HIDDEN_THINGS[args.thing],
                                                        PRAMS[args.pram]):
        raise StoryError(explain_rejection(HIDDEN_THINGS[args.thing],
                                           PRAMS[args.pram]))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.route is None or c[1] == args.route)
              and (args.pram is None or c[2] == args.pram)
              and (args.thing is None or c[3] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, route_id, pram_id, thing_id = rng.choice(sorted(combos))
    helper_type = args.helper or rng.choice([h.type for h in HELPERS])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        route=route_id,
        pram=pram_id,
        thing=thing_id,
        helper=helper_type,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    """Build the simulated world from params and bundle story + the 3 Q&A sets."""
    helper_cfg = next(h for h in HELPERS if h.type == params.helper)
    world = tell(
        SETTINGS[params.place],
        ROUTES[params.route],
        PRAMS[params.pram],
        HIDDEN_THINGS[params.thing],
        helper_cfg,
        params.name,
        params.gender,
        [params.trait, "observant"],
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, route, pram, thing) tuples:\n")
        for place, route, pram, thing in triples:
            print(f"  {place:13} {route:7} {pram:11}  thing={thing}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2,
                             ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (f"### {p.name}: {p.thing} in {p.pram} on {p.route} "
                      f"({p.place})")
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
