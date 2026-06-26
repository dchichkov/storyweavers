#!/usr/bin/env python3
"""
storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50/aspirate_mooshy_basement_stairs_teamwork_slice_of.py
=============================================================================================================================

Storyworld: "The Aspirate Mooshy Basement Stairs Teamwork Slice of Life"

Source tale (used to build the world model):
---
Once upon a time, there was a little boy named Arno. He liked big, careful
breaths that he called "aspirate" breaths -- the kind you take when something
is a little scary and you want your body to be ready. The basement stairs
were his favorite place to learn them, because the steps went down into a
soft, lamp-warm room where the wood was a little mooshy with old rain.

Arno wanted to bring the jars of jam his mother had canned down to the
basement shelf. The jars were slippery. Arno tried to carry them all at
once. He tripped on the third stair. One jar wobbled. He caught it with
both hands, but his foot slipped on the mooshy wood, and he sat down hard
on the step. His aspirate breath went out in a small huff.

His mother came and sat beside him on the stairs. She did not scold him.
She just said, "Let's do this together. One jar at a time, hand to hand."
Arno nodded. Together they figured out a small system: Arno held the
jars steady on each step while his mother kept one hand on the railing
and one on his shoulder. Step by step, jar by jar, they carried them all
down to the shelf, and the basement smelled like warm jam and rain.

Seed elements:
    aspirate -- the careful breath the boy uses when a task feels too big;
    mooshy   -- the soft, rain-damp feel of the basement stair wood;
    teamwork -- the family's joint method for the heavy carry.
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

# Magnitude at which an accumulated effect is "embedded enough" to be narrated.
THRESHOLD = 1.0

# Mess kinds that can foul stairs/objects (kept compact on purpose: this world
# is small).  "mooshy" is the central one -- it tracks slip/damp/squish state.
MESS_KINDS = {"mooshy", "sweaty", "sticky"}

# Body regions, used for the hand-load constraint (who can hold what).
REGIONS = {"hands", "arms", "legs", "torso"}


# ---------------------------------------------------------------------------
# Entity: characters and physical objects share one representation.
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
    type: str = "thing"            # boy, mother, jar, stair, shelf, ...
    label: str = ""                # short reference: "jar", "stair"
    phrase: str = ""               # full noun phrase: "a fat jar of plum jam"
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    helper: Optional[str] = None       # who can carry / steady this object
    held_by: Optional[str] = None      # current carrier (for jars, rails)
    region: str = ""                   # where on a body the object sits
    protective: bool = False           # something that shields (a railing grip)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother"}
        male = {"boy", "father", "dad", "man", "grandfather"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad",
                "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs.
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the basement stairs"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)
    mood: str = "lamp-warm"     # "lamp-warm" | "bright" | "cool"


@dataclass
class Task:
    """A heavy/awkward carrying task that the hero wants to do solo."""
    id: str
    verb: str            # "carry the jars down"
    gerund: str          # "carrying jars down the stairs"
    rush: str            # "lunge up the stairs to grab them all"
    mess: str            # mess kind key: "mooshy"
    soil: str            # how the load goes wrong: "slip on the mooshy step"
    zone: set[str]       # body regions the load taxes: {"hands", "arms"}
    weather: str         # "rainy" | "dry" | ""
    keyword: str = ""    # topic word for prompts
    tags: set[str] = field(default_factory=set)


@dataclass
class Load:
    """The thing(s) the hero is carrying, that one person alone cannot safely move."""
    label: str
    phrase: str
    type: str
    count: int = 1           # how many units -- teamwork matters more as it grows
    plural: bool = True
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Helper:
    """The joint-method offered as the compromise (parent + child)."""
    id: str
    label: str
    covers: set[str]     # what the helper steadies (body regions / load units)
    guards: set[str]     # mess kinds it neutralizes
    prep: str            # body of the offer: "we do it one jar at a time"
    tail: str            # closing clause: "carried them down together, one jar at a time"
    plural: bool = False


# ---------------------------------------------------------------------------
# World: entity store + narration history.
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

    def carried_by(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.held_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.carried_by(actor))

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
# Causal rules.
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_slip(world: World) -> list[str]:
    """If the actor is mooshy/messy AND carrying a load in the taxed region
    AND no protective grip covers that region, the load spills / the actor
    slips."""
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.carried_by(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("slip", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["wobble"] += 1
                out.append(f"The {item.label} wobbled on the mooshy step.")
    return out


def _r_workload(world: World) -> list[str]:
    """A wobbling / dropped load means more work for the helper who has to redo it."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["wobble"] < THRESHOLD or not item.helper:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        helper = world.get(item.helper)
        helper.meters["workload"] += 1
        out.append(f"That would mean doing the carry again with {helper.label}.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="slip", tag="physical", apply=_r_slip),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
def load_at_risk(task: Task, load: Load) -> bool:
    """Would this load actually tax the body regions the task stresses?"""
    return load.count >= 1 and task.zone  # any taxed region means solo carry is risky


def select_helper(task: Task, load: Load) -> Optional[Helper]:
    """A compatible fix: a helper who covers the taxed regions AND guards the
    mess kind the task produces.  Returns None when nothing fits."""
    for h in HELPERS:
        if task.mess in h.guards and task.zone <= h.covers:
            return h
    return None


def predict_mess(world: World, actor: Entity, task: Task, load_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, narrate=False)
    load = sim.entities.get(load_id)
    return {
        "wobble": bool(load and load.meters["wobble"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs: mutate state, optionally narrate.
# ---------------------------------------------------------------------------
def task_voice(task: Task) -> str:
    return {
        "jars": "the jars clinked softly against each other",
        "laundry": "the warm laundry smelled like the garden",
        "books": "the stack of books was taller than Arno's head",
    }.get(task.id, "the load felt heavier than it looked")


def setting_detail(setting: Setting, task: Task) -> str:
    if setting.mood == "lamp-warm":
        return (f"The basement stairs smelled like wood and a little rain, and "
                f"the lamp made the walls glow a soft yellow.")
    if setting.mood == "bright":
        return f"Bright light came down {setting.place}, and the steps looked pale and dry."
    return f"{setting.place.capitalize()} was cool and quiet, and the steps waited."


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    if task.id not in world.setting.affords:
        return
    world.zone = set(task.zone)
    actor.meters[task.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every good place to learn.")


def loves_breath(world: World, hero: Entity) -> None:
    hero.memes["aspirate"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} liked big, careful breaths he called "
        f'"aspirate" breaths -- the kind you take when something feels a '
        f"little scary and you want your body to be ready."
    )


def stairs_set(world: World, hero: Entity) -> None:
    hero.memes["stairs_known"] += 1
    world.say(
        f"The basement stairs were his favorite place to practice them, "
        f"because the steps went down into a soft, lamp-warm room where "
        f"the wood was a little mooshy with old rain."
    )


def has_load(world: World, parent: Entity, hero: Entity, load: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} had {load.phrase} ready "
        f"to go down to the basement shelf."
    )


def wants_to_carry(world: World, hero: Entity, parent: Entity, task: Task) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {task.verb} all by {hero.pronoun('object')}, "
        f"because the steps looked easy and the jars looked bright."
    )


def warn(world: World, parent: Entity, hero: Entity, task: Task, load: Entity) -> bool:
    pred = predict_mess(world, hero, task, load.id)
    if not pred["wobble"]:
        return False
    world.facts["predicted_soil"] = task.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get the {load.label} {task.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then we'll have to carry it all again together"
    world.say(
        f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. '
        f'"Let\'s think about an easier way."'
    )
    return True


def tries_alone(world: World, hero: Entity, task: Task) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to try was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {task.rush},")


def trip(world: World, parent: Entity, hero: Entity, task: Task) -> None:
    hero.meters["trip"] += 1
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"and {hero.pronoun('possessive')} foot slipped on the mooshy step. "
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} was "
        f"right there and caught {hero.pronoun('object')} with a steady hand."
    )


def huff(world: World, hero: Entity) -> None:
    if hero.memes["aspirate"] >= THRESHOLD and hero.meters["trip"] >= THRESHOLD:
        world.say(
            f"His aspirate breath whooshed out in a small huff, and "
            f"{hero.pronoun()} sat down hard on the step."
        )


def pout(world: World, hero: Entity, task: Task) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {task.verb} by myself!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, task: Task,
               load: Entity) -> Optional[Helper]:
    h = select_helper(task, load)
    if h is None:
        return None
    gear = world.add(Entity(
        id=h.id, type="helper-gear", label=h.label,
        owner=parent.id, helper=parent.id, protective=True,
        covers=set(h.covers), plural=h.plural,
    ))
    # The compromise's "coverage" is registered against the hero so the slip
    # rule sees a shielded grip on each taxed region.
    gear.held_by = hero.id
    if predict_mess(world, hero, task, load.id)["wobble"]:
        gear.held_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} sat '
        f'down beside {hero.pronoun("object")} on the step and smiled. '
        f'"How about we {h.prep}?" {parent.pronoun()} said.'
    )
    return h


def accept(world: World, parent: Entity, hero: Entity, task: Task, load: Entity,
           h: Helper) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} nodded. "
        f'"Yes -- together," {hero.pronoun()} said, taking another slow aspirate breath.'
    )
    world.say(
        f"They figured out a small teamwork rhythm: {hero.id} held the {load.label} "
        f"steady on each step while {hero.pronoun('possessive')} {parent.label_word} "
        f"kept one hand on the railing and one on {hero.pronoun('possessive')} shoulder."
    )
    world.say(
        f"Step by step, jar by jar, they {h.tail}, and the basement smelled "
        f"like warm jam and rain."
    )


# ---------------------------------------------------------------------------
# The screenplay.
# ---------------------------------------------------------------------------
def tell(setting: Setting, task: Task, load_cfg: Load,
         hero_name: str = "Arno", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = task.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["careful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    load = world.add(Entity(
        id="load", type=load_cfg.type, label=load_cfg.label,
        phrase=load_cfg.phrase, owner=parent.id, helper=parent.id,
        region="hands", plural=load_cfg.plural,
    ))

    # Act 1 -- setup.
    introduce(world, hero)
    loves_breath(world, hero)
    stairs_set(world, hero)
    has_load(world, parent, hero, load)

    # Act 2 -- conflict.
    world.para()
    world.say(setting_detail(world.setting, task))
    wants_to_carry(world, hero, parent, task)
    warn(world, parent, hero, task, load)
    tries_alone(world, hero, task)
    trip(world, parent, hero, task)
    huff(world, hero)

    # Act 3 -- resolution.
    world.para()
    pout(world, hero, task)
    h = compromise(world, parent, hero, task, load)
    if h:
        accept(world, parent, hero, task, load, h)

    world.facts.update(hero=hero, parent=parent, load=load, load_cfg=load_cfg,
                       task=task, setting=setting, helper=h,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=h is not None)
    return world


# ---------------------------------------------------------------------------
# Content registries.
# ---------------------------------------------------------------------------
SETTINGS = {
    "basement-stairs": Setting(
        place="the basement stairs", indoor=True, mood="lamp-warm",
        affords={"jars", "laundry", "books"},
    ),
    "cellar-stairs": Setting(
        place="the cellar stairs", indoor=True, mood="cool",
        affords={"jars", "laundry"},
    ),
    "porch-stairs": Setting(
        place="the porch stairs", indoor=False, mood="bright",
        affords={"laundry", "books"},
    ),
}

TASKS = {
    # "jars" -- the seed-task: many slippery units, hand/arms taxed.
    "jars": Task(
        id="jars",
        verb="carry the jars down",
        gerund="carrying jars down the stairs",
        rush="lunge up the steps and grab all the jars at once",
        mess="mooshy",
        soil="wobbling on the mooshy wood",
        zone={"hands", "arms"},
        weather="rainy",
        keyword="jars",
        tags={"jar", "mooshy", "stairs"},
    ),
    # "laundry" -- a soft, warm carry; load is awkward rather than slippery.
    "laundry": Task(
        id="laundry",
        verb="bring the laundry down",
        gerund="bringing the laundry down",
        rush="scoop up the whole basket at once",
        mess="sweaty",
        soil="slipping on the damp laundry",
        zone={"hands", "arms"},
        weather="",
        keyword="laundry",
        tags={"laundry", "warm"},
    ),
    # "books" -- heavy stack, no mess, but the height of the stack is the risk.
    "books": Task(
        id="books",
        verb="carry the books down",
        gerund="carrying books down the stairs",
        rush="balance the whole stack on one arm",
        mess="sticky",
        soil="toppling on the dusty stairs",
        zone={"hands", "arms", "torso"},
        weather="dry",
        keyword="books",
        tags={"books", "stack"},
    ),
}

# Each helper covers all taxed regions for the task AND guards the mess kind.
HELPERS = [
    Helper(
        id="jar-pace",
        label="one jar at a time",
        covers={"hands", "arms"},
        guards={"mooshy", "sweaty"},
        prep="do it one jar at a time, hand to hand",
        tail="carried them down together, one jar at a time",
    ),
    Helper(
        id="rail-shoulder",
        label="the railing-and-shoulder grip",
        covers={"hands", "arms", "torso"},
        guards={"mooshy", "sweaty", "sticky"},
        prep="use the railing with one hand and my shoulder with the other",
        tail="carried them down together with the railing-and-shoulder grip",
    ),
    Helper(
        id="basket-pass",
        label="the basket-pass",
        covers={"hands"},
        guards={"sweaty"},
        prep="pass the basket to each other step by step",
        tail="passed the basket down step by step",
    ),
    Helper(
        id="two-stack",
        label="the two-stack split",
        covers={"hands", "arms", "torso"},
        guards={"sticky"},
        prep="split the stack in two and each take half",
        tail="carried the stacks down together, half each",
    ),
]

LOADS = {
    "jars": Load(
        label="jars",
        phrase="a row of fat jars of plum jam",
        type="jars",
        count=3,
        plural=True,
        genders={"girl", "boy"},
    ),
    "basket": Load(
        label="laundry basket",
        phrase="a big warm laundry basket",
        type="basket",
        count=1,
        plural=False,
        genders={"girl", "boy"},
    ),
    "books": Load(
        label="books",
        phrase="a tall stack of picture books",
        type="books",
        count=5,
        plural=True,
        genders={"girl", "boy"},
    ),
}

BOY_NAMES = ["Arno", "Theo", "Finn", "Ben", "Sam", "Leo", "Eli", "Noah", "Max", "Jack"]
GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
TRAITS = ["careful", "curious", "stubborn", "playful", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str]]:
    """(place, task, load) triples that pass the reasonableness constraint."""
    out = []
    for place, setting in SETTINGS.items():
        for tid in setting.affords:
            t = TASKS[tid]
            for lid, load in LOADS.items():
                if load_at_risk(t, load) and select_helper(t, load):
                    out.append((place, tid, lid))
    return out


# ---------------------------------------------------------------------------
# Per-world parameters.
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    task: str
    load: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation.
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "aspirate": [
        ("What is an aspirate breath?",
         "An aspirate breath is a big, careful breath you take on purpose "
         "before doing something hard, so your body feels ready and calm."),
        ("Why do people take a big breath when they are nervous?",
         "A slow big breath fills the lungs with fresh air and tells the body "
         "to slow down, which can make a tricky moment feel easier."),
    ],
    "mooshy": [
        ("What does mooshy mean?",
         "Mooshy means soft, damp, and a little squishy under your feet, "
         "the way old wood feels when a little rain has touched it."),
        ("Why can mooshy wood be slippery?",
         "When wood gets damp, the surface becomes smooth and slick, so shoes "
         "and bare feet can slide on it more easily than on dry wood."),
    ],
    "stairs": [
        ("Why are stairs a good place to practice being careful?",
         "Stairs go up and down, so a slip on a step can turn into a fall. "
         "Going slowly and holding on keeps your balance safe."),
    ],
    "jar": [
        ("Why are jars tricky to carry down stairs?",
         "Jars are round and smooth, so they roll and wobble in your hands. "
         "On stairs, a wobble can grow into a slip if you are moving too fast."),
    ],
    "laundry": [
        ("Why is a heavy laundry basket hard to carry alone?",
         "A full basket is bulky, and you cannot see your feet over the top, "
         "so it is hard to feel where the steps are."),
    ],
    "books": [
        ("Why is a tall stack of books hard to balance?",
         "A tall stack is top-heavy, so small bumps on the stairs can make "
         "the whole stack tip forward unless you split it up."),
    ],
    "teamwork": [
        ("What is teamwork?",
         "Teamwork is when two or more people share a job, each doing a part, "
         "so the work goes more safely and easily than it would alone."),
        ("Why does teamwork make carrying things easier?",
         "When two people share a carry, each one holds less weight, can see "
         "the steps better, and can steady the other if something wobbles."),
    ],
}
KNOWLEDGE_ORDER = ["aspirate", "mooshy", "stairs", "jar", "laundry", "books", "teamwork"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, task, load = f["hero"], f["parent"], f["task"], f["load_cfg"]
    kw = task.keyword or task.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a small '
        f'helper, a big carry, a teamwork rhythm" that includes the words '
        f'"aspirate" and "mooshy".',
        f"Tell a gentle slice-of-life story where a {hero.type} named {hero.id} "
        f"wants to {task.verb} alone, but {hero.pronoun('possessive')} "
        f"{parent.label_word} teaches {hero.pronoun('object')} a teamwork rhythm "
        f"on the basement stairs.",
        f'Write a quiet, warm story set on the basement stairs that uses the '
        f'word "{kw}" and ends with a small teamwork carry done together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, load, task = f["hero"], f["parent"], f["load"], f["task"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    mood = world.setting.mood
    day = {"rainy": "rainy day", "sunny": "sunny day", "": "quiet day"}.get(world.weather, "quiet day")

    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} tries to {task.verb} "
                f"alone on {place}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They are on {place} on a {day}, and the lamp "
                f"makes the wood look {mood}."
            ),
        ),
        QAItem(
            question=(
                f"What special kind of breath did {trait} {hero.id} practice "
                f"before going down {place}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} practiced big, careful breaths "
                f"{sub} called 'aspirate' breaths -- the kind you take when "
                f"something feels a little scary and you want your body to be ready."
            ),
        ),
        QAItem(
            question=(
                f"What did the wood on {place} feel like on the rainy day when "
                f"{hero.id} tried to {task.verb}?"
            ),
            answer=(
                f"The wood felt mooshy -- soft and damp with old rain. That "
                f"made the steps a little slippery under {pos} feet."
            ),
        ),
        QAItem(
            question=(
                f"What was {hero.id} trying to {task.verb} when the carry got "
                f"too big on {place}?"
            ),
            answer=(
                f"{sub.capitalize()} was trying to {task.verb} -- "
                f"{load.phrase}. The load was awkward, and the mooshy step "
                f"made the wobble worse."
            ),
        ),
    ]

    if f.get("conflict"):
        soil = f.get("predicted_soil", "wobbling")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was worried because if {hero.id} tried "
               f"to {task.verb} alone, the {load.label} would get {soil}")
        why += (f", and they would have to do the carry again together. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {task.rush.rstrip(', ')}, "
                f"{pos} foot slipped on the mooshy step, and {pos} {pw} caught "
                f"{obj} with a steady hand on the railing.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about the {load.label} on "
                f"{place}?"
            ),
            answer=why,
        ))

    if f.get("resolved"):
        h = f["helper"]
        qa.append(QAItem(
            question=(
                f"What teamwork rhythm did {trait} {hero.id} and {pos} {pw} "
                f"use to finish the carry on {place}?"
            ),
            answer=(
                f"They used {h.label}. {hero.id} held the {load.label} steady "
                f"on each step while {pos} {pw} kept one hand on the railing "
                f"and one on {pos} shoulder. Step by step, they carried the "
                f"load down together."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after the teamwork carry on "
                f"{place}?"
            ),
            answer=(
                f"{hero.id} felt proud and calm. {sub.capitalize()} took another "
                f"slow aspirate breath, and the basement smelled like warm "
                f"{task.keyword or 'jam'} and rain."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["task"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="basement-stairs",
        task="jars",
        load="jars",
        name="Arno",
        gender="boy",
        parent="mother",
        trait="careful",
    ),
    StoryParams(
        place="cellar-stairs",
        task="laundry",
        load="basket",
        name="Mia",
        gender="girl",
        parent="mother",
        trait="spirited",
    ),
    StoryParams(
        place="porch-stairs",
        task="books",
        load="books",
        name="Finn",
        gender="boy",
        parent="father",
        trait="curious",
    ),
]


def explain_rejection(task: Task, load: Load) -> str:
    if not load_at_risk(task, load):
        return (f"(No story: {task.gerund} taxes {sorted(task.zone)}, but the "
                f"given load does not strain a child there -- the carry "
                f"would not be a real teamwork problem. Try a load with "
                f"count >= 1 in {sorted(task.zone)}.)")
    return (f"(No story: nothing in the helper catalog steadies {load.label} "
            f"through {sorted(task.zone)} while guarding {task.mess}. The "
            f"teamwork offer must actually cover the at-risk regions.)")


def explain_gender(load_id: str, gender: str) -> str:
    ok = " / ".join(sorted(LOADS[load_id].genders))
    return (f"(No story: a {LOADS[load_id].label} isn't a typical {gender}'s "
            f"carry here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# ASP twin.
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A load is at risk when the task taxes the regions it relies on.
load_at_risk(T, L) :- task(T), load(L), count(L, N), N >= 1, taxes(T, R).

% A helper is a compatible fix only when it covers every taxed region AND
% guards the mess kind the task produces.
protects(H, T, L) :- helper(H), load_at_risk(T, L),
                     mess_of(T, M), guards(H, M),
                     covers(H, R) : taxes(T, R).
has_fix(T, L) :- protects(_, T, L).

valid(Place, T, L) :- affords(Place, T), load_at_risk(T, L), has_fix(T, L).
valid_story(Place, T, L, Gender) :- valid(Place, T, L), wears(Gender, L).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, t.mess))
        for r in sorted(t.zone):
            lines.append(asp.fact("taxes", tid, r))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("count", lid, l.count))
        if l.plural:
            lines.append(asp.fact("load_plural", lid))
        for g in sorted(l.genders):
            lines.append(asp.fact("wears", g, lid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for m in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, m))
        for r in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, r))
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
        description="Story world sketch: aspirate breaths, mooshy basement "
                    "stairs, teamwork. Unspecified choices are picked at random.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
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
    if args.task and args.load:
        t, l = TASKS[args.task], LOADS[args.load]
        if not (load_at_risk(t, l) and select_helper(t, l)):
            raise StoryError(explain_rejection(t, l))
    if args.gender and args.load and args.gender not in LOADS[args.load].genders:
        raise StoryError(explain_gender(args.load, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.load is None or c[2] == args.load)
              and (args.gender is None or args.gender in LOADS[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, task, load_id = rng.choice(sorted(combos))
    load = LOADS[load_id]
    gender = args.gender or rng.choice(sorted(load.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        task=task,
        load=load_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], TASKS[params.task],
                 LOADS[params.load], params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
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
        print(f"{len(triples)} compatible (place, task, load) combos "
              f"({len(stories)} with gender):\n")
        for place, task, load in triples:
            genders = sorted(g for (pl, t, ld, g) in stories
                             if (pl, t, ld) == (place, task, load))
            print(f"  {place:16} {task:9} {load:7}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.task} at {p.place} (load: {p.load})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
