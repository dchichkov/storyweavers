#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/nozzle_bad_ending_curiosity_tall_tale.py
=============================================================================================================================

A standalone *story world* sketch for a Tall Tale about a curious child and a
nozzle that leads to a bad ending.  The child loves to spray water (or paint,
or mud) and gets a precious new shirt.  Curiosity drives the child to try the
activity despite a warning; the result is always a mess and a ruined prize.

No compromise gear exists for these combos, so every story ends badly.
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
MESS_KINDS = {"wet", "painted", "muddy"}
REGIONS = {"feet", "legs", "torso", "head"}


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
# Domain dataclasses
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
    """Gear catalog – we intentionally leave it incomplete so no fix exists."""
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str = ""
    tail: str = ""
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


def _r_soak(world: World) -> list[str]:
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
                sig = ("soak", item.id, mess)
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


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
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
# Constraint helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    """Since our gear catalog has no gear matching both mess and region,
    this always returns None – meaning no fix is available."""
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


# ---------------------------------------------------------------------------
# Prediction (for parent’s warning)
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
# Verb helpers
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "spray": "the water made a shiny arc that looked like a rainbow",
        "paint": "the brush left bright trails on paper like tiny fireworks",
        "mud": "the squish between toes felt like walking on clouds",
    }.get(activity.id, "it made every day feel like an adventure")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the play table waited."
    if activity.weather == "rainy":
        return f"The air smelled fresh, and {setting.place} shone after the rain."
    return f"{setting.place.capitalize()} looked wide and ready for play."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# Screenplay beats
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a {trait} little {hero.type} who loved to explore everything new.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {hero.id}'s {parent.label_word} bought "
        f"{hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} as if the day had been made just for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"rainy": "One rainy day, ", "sunny": "One sunny day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


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
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But {hero.id} was too curious to wait. "
        f"{hero.pronoun().capitalize()} tried to {activity.rush}."
    )


def grab_hand(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] += 1
    # No conflict rule needed; the grab itself is narrated.
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand, but {hero.id} wriggled free in excitement."
    )


def bad_ending_consequence(world: World, hero: Entity, parent: Entity,
                           activity: Activity, prize: Entity) -> None:
    """The child ignores the warning and does the activity – bad ending."""
    world.say(
        f"Before {parent.label_word} could stop {hero.pronoun('object')}, "
        f"{hero.id} was already {activity.gerund}."
    )
    # Apply the activity in the world model (soak rules fire).
    _do_activity(world, hero, activity, narrate=True)
    # After the mess, describe the ruined prize and parent's reaction.
    world.say(
        f"When the {activity.id} settled, {hero.pronoun('possessive')} {prize.label} "
        f"was {activity.soil}. {parent.pronoun('possessive').capitalize()} "
        f"{parent.label_word} sighed and shook {parent.pronoun('possessive')} head."
    )
    world.say(
        f"{hero.id} hung {hero.pronoun('possessive')} head and knew the nozzle was "
        f"not a toy to play with alone."
    )


# ---------------------------------------------------------------------------
# The tell function (three acts, bad ending)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Billy", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None, parent_type: str = "father") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 – setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2 – conflict (desire + warning + defiance)
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)

    # Act 3 – bad ending (no compromise)
    world.para()
    grab_hand(world, parent, hero)
    bad_ending_consequence(world, hero, parent, activity, prize)

    # Record facts for Q&A
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=None,
                       conflict=True, resolved=False)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "backyard": Setting(place="the backyard", indoor=False, affords={"spray"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"paint"}),
    "garden": Setting(place="the garden", indoor=False, affords={"mud"}),
}

ACTIVITIES = {
    "spray": Activity(
        id="spray",
        verb="spray water with the hose nozzle",
        gerund="spraying water with the nozzle",
        rush="grab the nozzle and squeeze",
        mess="wet",
        soil="soaking wet",
        zone={"torso", "legs"},
        weather="sunny",
        keyword="nozzle",
        tags={"water", "wet", "nozzle"},
    ),
    "paint": Activity(
        id="paint",
        verb="paint with the new brush",
        gerund="painting with the new brush",
        rush="dip the brush in the paint",
        mess="painted",
        soil="covered in paint",
        zone={"torso"},
        weather="",
        keyword="paint",
        tags={"paint", "dirty", "brush"},
    ),
    "mud": Activity(
        id="mud",
        verb="play in the mud",
        gerund="playing in the mud",
        rush="jump into the mud",
        mess="muddy",
        soil="all muddy",
        zone={"legs", "feet"},
        weather="rainy",
        keyword="mud",
        tags={"mud", "dirty"},
    ),
}

# Gear catalog deliberately left with only boots that cover feet (does not
# protect legs or torso), so no fix exists for any of our combos.
GEAR = [
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"wet", "muddy"},
        prep="go home and put on our rain boots",
        tail="walked back home to get their rain boots",
        plural=True,
    ),
]

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a crisp new shirt",
        type="shirt",
        region="torso",
    ),
    "pants": Prize(
        label="pants",
        phrase="new blue pants",
        type="pants",
        region="legs",
        plural=True,
    ),
    "dress": Prize(
        label="dress",
        phrase="a pretty new dress",
        type="dress",
        region="legs",
        genders={"girl"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "stubborn", "playful", "spirited", "lively", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    """Return only combos where the activity risks the prize AND no gear fixes it."""
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize) is None:
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    """Everything needed to reproduce a single story (deterministic given these)."""
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "water": [("Why does water make things wet?",
               "Water is a liquid, so when it touches something dry it sticks to it and "
               "makes the surface feel wet.")],
    "wet": [("Is being wet always bad?",
             "Not always – being wet can be fun when you are swimming, but it can ruin "
             "clothes that you want to keep clean.")],
    "nozzle": [("What is a nozzle for?",
                "A nozzle is the end of a hose that controls how the water comes out. "
                "You can make a spray or a stream.")],
    "paint": [("Why can paint be messy?",
               "Paint is a colored liquid that dries hard. If it gets on clothes it is "
               "hard to wash out.")],
    "mud": [("What is mud?",
             "Mud is wet dirt. It is soft and sticks to clothes and shoes.")],
    "dirty": [("Why do we clean clothes?",
               "We clean clothes to take out the dirt and stains so they look nice and "
               "feel fresh.")],
}
KNOWLEDGE_ORDER = ["water", "wet", "nozzle", "paint", "mud", "dirty"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old about a {hero.type} named '
        f'{hero.id} who is curious about a {kw} and learns a hard lesson.',
        f"Tell a tall tale where a little {hero.type} gets a {kw} and, despite "
        f"a warning, tries to {act.verb} and ruins a brand-new {prize.label}.",
        f'Write a gentle cautionary story using the word "{kw}" where the main '
        f"character ends up soaked and sad.",
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
            question=f"Who is the story about?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} "
                   f"and {pos} {pw}. They go to {place}.",
        ),
        QAItem(
            question=f"What new {prize.label} did {hero.id}'s {pw} buy?",
            answer=f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                   f"{hero.id} loved it and wore it.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {act.keyword}?",
            answer=f"{trait.capitalize()} {hero.id} wanted to {act.verb}. "
                   f"{pos} {pw} warned that {pos} {prize.label} would get {act.soil}.",
        ),
        QAItem(
            question=f"Why did {hero.id} ignore the warning?",
            answer=f"{trait.capitalize()} {hero.id} was too curious to wait. "
                   f"The urge to {act.rush} was too strong.",
        ),
        QAItem(
            question=f"What happened when {hero.id} {act.gerund}?",
            answer=f"{pos.capitalize()} {prize.label} got {act.soil}. "
                   f"{pos} {pw} sighed and said the {act.keyword} was not a toy.",
        ),
    ]
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
    lines = ["== (1) Generation prompts ==\n"]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("\n== (2) Story questions ==\n")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("\n== (3) World knowledge ==\n")
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
    StoryParams(place="backyard", activity="spray", prize="shirt", name="Billy",
                 gender="boy", parent="father", trait="curious"),
    StoryParams(place="playroom", activity="paint", prize="shirt", name="Lily",
                 gender="girl", parent="mother", trait="spirited"),
    StoryParams(place="garden", activity="mud", prize="pants", name="Max",
                 gender="boy", parent="father", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region} – it would not get "
                f"{activity.mess}, so no bad ending. Try a prize worn on {sorted(activity.zone)}.)")
    return ("(No story: a gear exists that could fix this, but we only want bad endings. "
            "Choose a combo where no gear protects the prize.)")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk when the activity splashes the region it is worn on.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a compatible fix only when it both neutralises the mess kind AND
% covers the at-risk region.
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

% Valid bad-ending stories: prize at risk AND no fix exists.
valid_bad(Place, A, P) :- setting(Place), affords(Place, A),
                          prize_at_risk(A, P), not has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid_bad(Place, A, P), wears(Gender, P).
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


def asp_valid_bad_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_bad/3."))
    return sorted(set(asp.atoms(model, "valid_bad")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_bad_combos()), set(valid_combos())
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
        description="Story world: a curious child, a nozzle (or paint/mud), a bad ending. "
                    "Unspecified choices are picked at random (seeded).")
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
                    help="list the compatible (bad-ending) story set derived by clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check the inline ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print the full ASP program (facts + inline rules)")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr) is None):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: a {PRIZES[args.prize].label} isn't a typical "
                         f"{args.gender}'s item here; try --gender "
                         f"{' / '.join(sorted(PRIZES[args.prize].genders))}.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid bad-ending combination matches the given options.)")

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
        combos, stories = asp_valid_bad_combos(), asp_valid_stories()
        print(f"{len(combos)} bad-ending (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in combos:
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
