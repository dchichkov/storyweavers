#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/perambulator_repetition_suspense_mystery.py
==================================================================================================================

A standalone *story world* sketch for a gentle mystery about a mysterious
perambulator, built with Repetition and Suspense to keep the style close to
Mystery.

Initial story (used to build a world model):
---
Once there was a little curious girl named Ella who loved mysteries. Every
morning she peeked out the window at the old garden. The perambulator stood
under the oak tree. But the next morning — the perambulator was near the
fence! "Mama," Ella whispered, "the perambulator moved again."

That evening Ella wanted to watch the perambulator at dusk. "Stay inside,"
Mama said gently. "It is cold, and your blanket will get dusty sitting by
the window so long."

Ella pulled the blanket tight. "But I need to see what moves it!" Mama
looked at the determined face. "How about we put on your warm coat and
watch from the porch together?" Ella hugged her. "Yes, let's solve
the mystery!"

They sat on the porch, coat wrapped snug, flashlight ready. As the stars
came out, a little hedgehog poked its nose from under the perambulator.
It pushed the old wheels! The perambulator rolled a tiny bit. Ella gasped
and laughed. "The hedgehog is the mover!"

Every night after, Ella and Mama left a small bowl of water near the
perambulator. The hedgehog came, the perambulator stayed, and the mystery
was solved.

Causal state updates:
---
    do activity                    -> actor.meters[activity_tag] += 1
                                     actor.memes[curiosity] += 1
    actor outside + worn item      -> item.meters[dusty]++, item.meters[tangled]++
                                     only if item region is exposed and no
                                     protective gear covers that region
    worn item dusty                -> item.caretaker.workload += 1
    warning ignored                -> actor.memes[defiance] += 1
    parent holds child back        -> actor.memes[conflict] += 1
    compromise accepted            -> actor.memes[joy] += 1 ; conflict -> 0
    mystery_solved                 -> actor.memes[wonder] += 1 ; parent.memes[pride] += 1
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

# Physical meter keys that count as a "trace" the activity leaves on worn items.
MESS_KINDS = {"dusty", "tangled", "wrinkled", "damp"}

# Body regions.
REGIONS = {"feet", "legs", "torso"}


# ---------------------------------------------------------------------------
# Entities: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # girl, boy, mother, father, blanket, coat, ...
    label: str = ""                # short reference, e.g. "blanket", "warm coat"
    phrase: str = ""               # full noun phrase, e.g. "a soft blue blanket"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""               # feet | legs | torso
    protective: bool = False
    covers: set[str] = field(default_factory=set)   # regions the gear shields
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the garden"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str            # after "wanted to ..."
    gerund: str          # after "loved ... and ..."
    rush: str            # after "tried to ..."
    mess: str            # one of MESS_KINDS
    soil: str            # how the prize gets affected
    zone: set[str]       # body regions the activity exposes
    weather: str         # "foggy" | "cool" | ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


# ---------------------------------------------------------------------------
# World entity store + narration history.
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

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules (forward chaining to fixpoint).
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    """Actor outside + worn item in the zone & uncovered -> dusty/tangled etc."""
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["needs_clean"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess}."
                )
    return out


def _r_workload(world: World) -> list[str]:
    """Worn item needs_clean -> caretaker workload."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["needs_clean"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_hold_conflict(world: World) -> list[str]:
    """Parent held the child while child is defiant -> conflict."""
    for actor in world.characters():
        if actor.memes["held_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soil", tag="physical", apply=_r_soil),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="hold_conflict", tag="social", apply=_r_hold_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraint helpers.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction: run the world forward on a copy.
# ---------------------------------------------------------------------------
def predict_trace(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["needs_clean"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs (mutate state and optionally narrate).
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "watch": "the quiet dusk felt like a secret waiting to be discovered",
        "search": "every leaf and shadow seemed to hold a tiny clue",
        "track": "the faint marks on the ground told a story of the night",
    }.get(activity.id, "it felt like a real mystery")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was cozy, and the window framed the darkening sky."
    if activity.weather == "foggy":
        return f"The air was misty, and {setting.place} looked like a place where secrets hid."
    return f"{setting.place.capitalize()} lay quiet under the evening light, full of soft shadows."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, perambulator: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(
        f"{hero.id} was a {desc} who loved mysteries. "
        f"Every morning {hero.pronoun()} peeked out the window at "
        f"{world.setting.place}."
    )
    world.say(
        f"The {perambulator.label} stood under the old oak tree — "
        f"or did it? Some mornings it seemed to be in a different spot."
    )


def loves_mystery(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_mystery"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def owns_perambulator(world: World, hero: Entity, perambulator: Entity) -> None:
    perambulator.owner = hero.id
    world.say(
        f"The {perambulator.label} had been in the family for years. "
        f"{hero.id} thought of it as a quiet friend — "
        f"one that moved when nobody was looking."
    )


def first_discovery(world: World, hero: Entity, parent: Entity,
                    perambulator: Entity) -> None:
    world.say(
        f"One evening, {hero.id} tugged {hero.pronoun('possessive')} "
        f"{parent.label_word}'s sleeve. "
        f'"Mama, the {perambulator.label} moved again."'
    )
    world.say(
        f"{parent.label_word.capitalize()} looked out. "
        f"The {perambulator.label} was indeed a little closer to the fence "
        f"than it had been that morning."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"foggy": "One foggy evening, ", "cool": "One cool evening, "}.get(
        world.weather, "One evening, "
    )
    go = "sat by the window" if world.setting.indoor else "stood at the garden door"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} looking out at {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right then, "
        f"but {hero.pronoun('possessive')} {parent.label_word} "
        f"shook {hero.pronoun('possessive')} head softly."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity,
         prize: Entity) -> bool:
    pred = predict_trace(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"Stay inside. Your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I will have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let us wait until morning."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} heard the warning, but the mystery pulled harder. "
        f"{hero.pronoun().capitalize()} tried to {activity.rush}."
    )


def hold_back(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["held_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} gently "
        f"held {hero.pronoun('possessive')} shoulder and said, "
        f'"You can want to {activity.verb}, and we can still be careful."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} bit {hero.pronoun("possessive")} lip. '
            f'"But the {activity.keyword} — I need to know!" '
            f'{hero.pronoun()} whispered.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_trace(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked '
        f'at the {prize.label}, then at the dark garden, and smiled. '
        f'"How about we {gear_def.prep} and {activity.verb} together, just for a little while?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity,
           prize: Entity, gear_def: Gear, perambulator: Entity) -> None:
    hero.memes["joy"] += 1
    hero.memes["wonder"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s eyes widened. "
        f'"{gear_def.label.capitalize()} first, then the mystery!" '
        f"{hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} "
        f"{parent.label_word}."
    )
    world.say(
        f"They {gear_def.tail}. "
        f"The {perambulator.label} sat quietly under the stars. "
        f"Then — a tiny rustle. A small nose poked out from beneath the wheels."
    )


def reveal(world: World, hero: Entity, parent: Entity, perambulator: Entity) -> None:
    world.facts["mystery_solved"] = True
    world.facts["reveal_animal"] = "a little hedgehog"
    world.say(
        f"It was a little hedgehog! It had made a nest under the "
        f"{perambulator.label}. When it pushed against the wheels, "
        f"the {perambulator.label} rolled a tiny bit."
    )
    world.say(
        f"{hero.id} gasped and laughed. "
        f'"The hedgehog is the mover! Every night!" '
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} "
        f"hugged {hero.pronoun('object')} close."
    )


def epilogue(world: World, hero: Entity, parent: Entity, perambulator: Entity) -> None:
    world.say(
        f"After that, they left a small bowl of water near the "
        f"{perambulator.label}. The hedgehog came, the "
        f"{perambulator.label} stayed, and every evening "
        f"{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} watched the garden together."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Ella", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "patient"]),
    ))
    parent = world.add(Entity(
        id="Parent", kind="character", type=parent_type, label="the parent"
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    perambulator = world.add(Entity(
        id="perambulator", kind="thing", type="perambulator",
        label="perambulator",
        phrase="an old perambulator with big wheels and a faded hood",
        owner=hero.id,
    ))

    # Act 1 — setup
    introduce(world, hero, perambulator)
    loves_mystery(world, hero, activity)
    owns_perambulator(world, hero, perambulator)
    first_discovery(world, hero, parent, perambulator)

    # Repetition: the perambulator keeps moving.
    world.para()
    world.say(
        f"The next morning it was by the gate. The morning after that, "
        f"it was under the willow. '{hero_name},' "
        f"{parent.label_word} said, 'the {perambulator.label} is at the gate again.' "
        f"Every day the {perambulator.label} sat in a new place."
    )

    # Act 2 — tension
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    hold_back(world, parent, hero, activity)

    # Act 3 — resolution
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def, perambulator)
        reveal(world, hero, parent, perambulator)
        world.para()
        epilogue(world, hero, parent, perambulator)

    world.facts.update(
        hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, gear=gear_def,
        perambulator=perambulator,
        conflict=hero.memes["held_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden", indoor=False, affords={"watch", "search", "track"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"watch", "search"}),
    "park": Setting(place="the park", indoor=False, affords={"search", "track"}),
    "porch": Setting(place="the porch", indoor=False, affords={"watch"}),
    "attic": Setting(place="the attic", indoor=True, affords={"search"}),
}

ACTIVITIES = {
    "watch": Activity(
        id="watch",
        verb="watch the perambulator at dusk",
        gerund="watching the perambulator at dusk",
        rush="tiptoe to the window",
        mess="dusty",
        soil="dusty from the window ledge",
        zone={"torso", "legs"},
        weather="foggy",
        keyword="perambulator",
        tags={"perambulator", "dusk", "dusty"},
    ),
    "search": Activity(
        id="search",
        verb="search for clues in the garden",
        gerund="searching for clues in the garden",
        rush="sneak into the garden",
        mess="tangled",
        soil="tangled and dusty",
        zone={"feet", "legs"},
        weather="foggy",
        keyword="perambulator",
        tags={"perambulator", "clues", "garden"},
    ),
    "track": Activity(
        id="track",
        verb="track the wheel marks",
        gerund="tracking the wheel marks",
        rush="follow the trail",
        mess="damp",
        soil="damp from the grass",
        zone={"feet", "legs"},
        weather="foggy",
        keyword="perambulator",
        tags={"perambulator", "tracks", "grass"},
    ),
}

GEAR = [
    Gear(
        id="coat",
        label="warm coat",
        covers={"torso"},
        guards={"dusty", "damp"},
        prep="put on your warm coat",
        tail="put on the warm coat and stepped onto the porch",
    ),
    Gear(
        id="boots",
        label="warm boots",
        covers={"feet"},
        guards={"damp", "tangled"},
        prep="put on your warm boots",
        tail="put on the warm boots and stepped into the garden",
    ),
    Gear(
        id="blanketwrap",
        label="a thick blanket",
        covers={"torso", "legs"},
        guards={"dusty", "damp", "wrinkled"},
        prep="wrap up in a thick blanket",
        tail="wrapped up in the thick blanket and sat by the window",
        plural=False,
    ),
]

PRIZES = {
    "blanket": Prize(
        label="blanket",
        phrase="a soft blue blanket with fringe",
        type="blanket",
        region="legs",
        plural=False,
    ),
    "nightgown": Prize(
        label="nightgown",
        phrase="a cozy nightgown with little stars",
        type="nightgown",
        region="torso",
        genders={"girl"},
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a warm knitted scarf",
        type="scarf",
        region="torso",
        genders={"girl", "boy"},
    ),
    "robe": Prize(
        label="robe",
        phrase="a soft flannel robe",
        type="robe",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GIRL_NAMES = ["Ella", "Maya", "Nora", "Lily", "Zoe", "Ava", "Rose", "Ivy", "Lucy", "Mila"]
BOY_NAMES = ["Leo", "Finn", "Max", "Sam", "Theo", "Jack", "Noah", "Eli", "Ben", "Oli"]
TRAITS = ["curious", "patient", "brave", "thoughtful", "observant", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "perambulator": [
        ("What is a perambulator?",
         "A perambulator is an old-fashioned baby carriage with big wheels "
         "and a hood. Long ago, grown-ups pushed babies in them on walks."),
        ("Why is a perambulator mysterious?",
         "A perambulator can be mysterious because it is old and quiet, "
         "and if it moves when no one is pushing it, that is a puzzle to solve."),
    ],
    "dusk": [
        ("What is dusk?",
         "Dusk is the time just after the sun goes down when the sky "
         "turns purple and the world grows dark and quiet."),
    ],
    "clues": [
        ("What are clues?",
         "Clues are small pieces of information that help you solve a "
         "mystery, like footprints or a sound or a change in a room."),
    ],
    "tracks": [
        ("What are tracks?",
         "Tracks are marks left behind by something that moved, like "
         "footprints in mud or wheel marks on the ground."),
    ],
    "hedgehog": [
        ("What is a hedgehog?",
         "A hedgehog is a small, round animal covered in tiny spikes. "
         "It comes out at night and curls up when it is scared."),
    ],
    "dusty": [
        ("Why do things get dusty?",
         "Things get dusty when they sit still for a long time or when "
         "you take them outside where there is dirt and wind."),
    ],
}
KNOWLEDGE_ORDER = ["perambulator", "dusk", "clues", "tracks", "hedgehog", "dusty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize_cfg = (
        f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    )
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a mystery, '
        f'a perambulator, a discovery" that includes the word "{kw}".',
        f"Tell a gentle mystery where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize_cfg.phrase}, and they solve the mystery together.",
        f'Write a simple story that uses the noun "{kw}" and ends with a child '
        f"and parent discovering what moves the perambulator at night.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (
        hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    )
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    weather = {"foggy": "foggy evening", "cool": "cool evening"}.get(
        world.weather, "quiet evening"
    )
    perambulator = f["perambulator"]

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about and what mystery do they notice "
                f"in {place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} "
                f"and {pos} {pw}. They notice that the {perambulator.label} "
                f"in {place} moves to a different spot every night."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} want to do on the {weather} to "
                f"solve the mystery of the {perambulator.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} wanted to {act.verb} "
                f"to see what moved the {perambulator.label}. "
                f"But {pos} {pw} worried {pos} {prize.label} would get "
                f"dusty or cold."
            ),
        ),
        QAItem(
            question=(
                f"What did {hero.id} wear that {pw} wanted to keep clean?"
            ),
            answer=(
                f"{hero.id} had {prize.phrase}. {pos.capitalize()} "
                f"{pw} did not want it to get {act.soil} "
                f"during the {act.keyword} mystery."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "dusty")
        why = (
            f"{pos.capitalize()} {pw} was worried because if {hero.id} went to "
            f"{act.verb}, {pos} {prize.label} would get {soil}. "
        )
        why += (
            f"When {hero.id} tried to {act.rush.rstrip(', ')}, "
            f"{pos} {pw} gently held {obj} back and suggested a plan."
        )
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb}?"
            ),
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        gear_plan = gear.label
        if gear_plan.startswith(("a ", "an ")):
            gear_plan = gear_plan.split(" ", 1)[1]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} help {trait} {hero.id} {act.verb} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} without {pos} {prize.label} getting dusty. "
                f"The plan let {obj} solve the mystery while staying warm."
            ),
        ))
        if f.get("mystery_solved"):
            animal = f.get("reveal_animal", "a little animal")
            qa.append(QAItem(
                question=(
                    f"What did {trait} {hero.id} and {pos} {pw} discover "
                    f"was moving the {perambulator.label}?"
                ),
                answer=(
                    f"They discovered that {animal} had made a nest under "
                    f"the {perambulator.label}. Every night it pushed the "
                    f"wheels a little, and that is why the {perambulator.label} moved."
                ),
            ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    if f.get("mystery_solved"):
        tags.add("hedgehog")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:14} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="garden", activity="watch", prize="blanket",
        name="Ella", gender="girl", parent="mother", trait="curious",
    ),
    StoryParams(
        place="backyard", activity="search", prize="scarf",
        name="Leo", gender="boy", parent="father", trait="brave",
    ),
    StoryParams(
        place="porch", activity="watch", prize="robe",
        name="Maya", gender="girl", parent="mother", trait="patient",
    ),
    StoryParams(
        place="park", activity="track", prize="blanket",
        name="Finn", gender="boy", parent="father", trait="observant",
    ),
    StoryParams(
        place="garden", activity="search", prize="nightgown",
        name="Nora", gender="girl", parent="mother", trait="thoughtful",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (
            f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
            f"but {noun} {verb} on the {prize.region} -- it would not get "
            f"{activity.mess}, so the parent has no honest warning. "
            f"Try a prize worn on {sorted(activity.zone)}.)"
        )
    return (
        f"(No story: nothing in the gear catalog protects {noun} "
        f"({prize.region}) from {activity.gerund}. "
        f"The compromise must actually cover the at-risk item.)"
    )


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (
        f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s "
        f"item here; try --gender {ok}.)"
    )


# ---------------------------------------------------------------------------
# Clingo (ASP) reasoner.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


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
        description="Story world sketch: a child, a perambulator, a mystery. "
                    "Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.activity is None or c[1] == args.activity)
        and (args.prize is None or c[2] == args.prize)
        and (args.gender is None or args.gender in PRIZES[c[2]].genders)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity],
        PRIZES[params.prize], params.name, params.gender,
        [params.trait, "curious"], params.parent,
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(
                g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize)
            )
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
                f"### {p.name}: {p.activity} at {p.place} "
                f"(prize: {p.prize})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
