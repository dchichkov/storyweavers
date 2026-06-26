#!/usr/bin/env python3
"""
storyworlds/worlds/naughty_pile_inner_monologue_sound_effects_sharing.py
========================================================================

A standalone *story world* sketch for a tall‑tale about a naughty leaf pile,
with inner monologue, sound effects, and a sharing compromise.

Initial story (used to build a world model):
---
Once upon a time there was a little girl named Lily. She loved jumping into
things. One day her mother bought her a cozy red sweater. Lily wore it
everywhere.

Lily and her mother went to the backyard. There lay a huge, mischievous pile
of leaves.
"Let's jump in the leaf pile!" Lily said.
Her mother warned, "That pile is naughty – it will cover your sweater with
leaves and make you itch."
But Lily ran toward the pile. CRUNCH! The pile threw a handful of leaves.
Her mother grabbed her hand. "Share a cookie with the pile first, and put on
the leaf‑proof suit. Then it will be friendly."

Lily pouted. Then she put on the leaf‑proof suit, shared a cookie, and the
pile gave a happy WHOOSH! Lily jumped – SWOOSH! – and the leaves tickled her
suit. She and her mother laughed and shared the pile.
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
MESS_KINDS = {"leafy"}
REGIONS = {"feet", "legs", "torso"}


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
# Domain types
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the backyard"
    indoor: bool = False
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
    weather: str = ""
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
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_pile_naughty_mess(world: World) -> list[str]:
    """If pile is naughty and child inside zone, item gets leafy."""
    out: list[str] = []
    pile = world.entities.get("pile")
    if not pile or pile.memes["naughty"] < THRESHOLD:
        return out
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("leaf_mess", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and dirty."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean more work for {carer.label}.")
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
    Rule(name="pile_naughty_mess", tag="physical", apply=_r_pile_naughty_mess),
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
# Prediction
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Activity delight and detail helpers
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "leaf_jump": "the leaves crackled and snorted like tiny reindeer",
    }.get(activity.id, "it felt like a laughing drum")


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"{setting.place.capitalize()} smelled of earth and crunch."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


# ---------------------------------------------------------------------------
# Activity verb
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    # make the pile naughty if it exists
    pile = world.entities.get("pile")
    if pile:
        pile.memes["naughty"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every good place to play.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved playing outside and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That week, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} as if the day had been made specially for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))
    # introduce the naughty pile
    pile = world.add(Entity(
        id="pile", kind="thing", type="pile", label="naughty leaf pile",
        traits=["naughty", "huge"],
        memes=defaultdict(float, naughty=0.5)  # already half naughty
    ))
    world.say(f"There, a {pile.label} waited, snorting tiny leaves.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"That naughty pile will cover your {prize.label} with leaves"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to shake them out"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said.')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to jump was too big.")
    # inner monologue
    world.say(f'"{hero.pronoun().capitalize()} thought: I can outsmart that pile!"')
    # sound effect
    world.say(f"{hero.pronoun().capitalize()} ran toward the pile – CRUNCH!")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand. 'The pile just threw a WHOOSH of leaves!'"
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted. "But I want to jump!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    # Find gear that covers torso/legs and guards leafy
    gear_def = None
    for g in GEAR:
        if "leafy" in g.guards and prize.region in g.covers:
            gear_def = g
            break
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    # check if gear alone fixes it; also add sharing element
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    # sharing offer
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled. '
        f'"How about we {gear_def.prep}, and share a cookie with the pile first? '
        f'Then it will be friendly."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    # share the cookie
    pile = world.entities.get("pile")
    if pile:
        pile.memes["naughty"] = 0.0
        hero.memes["generosity"] += 1
        world.say(f"{hero.id} handed a cookie to the pile. The pile gave a gentle FWOOMP!")
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, we shared and we are ready!"'
    )
    world.say(
        f"They {gear_def.tail}. Now the pile was calm. {hero.id} "
        f"{activity.gerund} – SWOOSH! – {prize_was_clean(hero, prize)}, "
        f"and everyone laughed and took turns sharing the pile."
    )


# ---------------------------------------------------------------------------
# tell
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"leaf_jump"}),
    "forest": Setting(place="the forest path", indoor=False, affords={"leaf_jump"}),
}

ACTIVITIES = {
    "leaf_jump": Activity(
        id="leaf_jump",
        verb="jump into the leaf pile",
        gerund="jumping in the leaf pile",
        rush="run towards the big leaf pile",
        mess="leafy",
        soil="covered in leaves",
        zone={"legs", "torso"},
        weather="",
        keyword="leaf pile",
        tags={"leaf", "pile"},
    ),
}

PRIZES = {
    "sweater": Prize(
        label="sweater",
        phrase="a cozy red sweater",
        type="sweater",
        region="torso",
    ),
    "pants": Prize(
        label="pants",
        phrase="new green pants",
        type="pants",
        region="legs",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="leaf_suit",
        label="a leaf-proof suit",
        covers={"torso", "legs"},
        guards={"leafy"},
        prep="put on the leaf-proof suit",
        tail="ran back to get the leaf-proof suit",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


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
# StoryParams
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
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "leaf": [
        ("What do leaves feel like?",
         "Leaves are light, crinkly, and can be crunchy or soft. They come off trees in autumn."),
    ],
    "pile": [
        ("What is a pile?",
         "A pile is a heap of things, like a pile of leaves, toys, or sand."),
    ],
    "sharing": [
        ("Why is sharing nice?",
         "Sharing makes everyone feel included and can turn a grumpy thing into a happy one."),
    ],
    "sound": [
        ("Why do leaves make sounds?",
         "Dry leaves crackle, rustle, and pop when you step on them or toss them. "
         "They are natural noise makers."),
    ],
}
KNOWLEDGE_ORDER = ["leaf", "pile", "sharing", "sound"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short tall‑tale story for a 3‑to‑5‑year-old that includes '
        f'the words "{kw}" and "share".',
        f"Tell a story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but the pile is naughty. Use inner monologue and sound effects like CRUNCH.",
        f'Write a story that begins with a naughty pile of leaves and ends with everyone sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} in {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place}, and {hero.id} is "
                f"wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do outside "
                f"before {pw} worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved playing outside and "
                f"{act.gerund}. That wish was tricky because the pile was naughty."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} buy before "
                f"the leaf pile play at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and wore {prize.it()}."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "covered in leaves")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} was upset because the naughty pile would "
                f"make {pos} {prize.label} {soil}. When {hero.id} tried to "
                f"{act.rush.rstrip(', ')}, {pos} {pw} grabbed {pos} hand."
            ),
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=(
                f"How did {gear.label} and sharing a cookie help {trait} {hero.id} "
                f"enjoy the pile without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"{hero.id} put on {gear.label} and shared a cookie with the pile. "
                f"This made the pile friendly, so {sub} could jump without mess."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} and the pile agreed to share?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw}. They all took turns "
                f"sharing the pile and laughing."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    if world.facts["activity"]:
        tags.update(world.facts["activity"].tags)
    tags.add("sharing")
    tags.add("sound")
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="backyard",
        activity="leaf_jump",
        prize="sweater",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="playful",
    ),
    StoryParams(
        place="forest",
        activity="leaf_jump",
        prize="pants",
        name="Max",
        gender="boy",
        parent="father",
        trait="curious",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: jumping splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get {activity.mess}.")
    return (f"(No story: no gear protects {noun} from {activity.gerund}.)")


# ---------------------------------------------------------------------------
# ASP twin
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
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale: a child, a naughty leaf pile, sharing, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: {PRIZES[args.prize].label} not typical for {args.gender}.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
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
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
