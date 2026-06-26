#!/usr/bin/env python3
"""
storyworlds/worlds/glory_scarlet_babble.py
==========================================

A rhyming story world about a little knight who dreams of glory, wears a
scarlet cloak, and babbles endlessly. The world model tracks inner monologue,
reconciliation with a parent, and a happy ending.

Inspired by: "glory, scarlet, babble; Inner Monologue, Happy Ending, Reconciliation"
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
# Entities: characters and objects
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    # Physical / emotional meters
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"knight", "boy", "king"}
        female = {"girl", "queen", "mother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str
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
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})


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


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in {"muddy", "dusty", "wet"}:
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
    out = []
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


def _r_inner_doubt(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes["fear"] >= THRESHOLD and actor.memes["inner_courage"] < THRESHOLD:
            sig = ("inner_doubt", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["inner_courage"] += 0.5
            out.append(f"\"Maybe I'm not brave enough,\" {actor.id} thought.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="inner_doubt", tag="social", apply=_r_inner_doubt),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Rhyming story helpers
# ---------------------------------------------------------------------------
def rhyme_line(a: str, b: str) -> str:
    """Return two lines that rhyme (we pre-author rhymes per beat)."""
    return f"{a}\n{b}"

def introduce_rhyme(hero: Entity) -> tuple[str, str]:
    return (f"Little {hero.id} the {hero.type}, brave and small,",
            f"Dreamed of glory, ready for a call.")

def loves_activity_rhyme(hero: Entity, activity: Activity) -> tuple[str, str]:
    return (f"{hero.pronoun().capitalize()} loved to {activity.verb} and babble all day,",
            f"Talking and playing in the sun's warm ray.")

def buys_rhyme(parent: Entity, hero: Entity, prize: Entity) -> tuple[str, str]:
    return (f"{hero.id}'s {parent.label_word} gave a special prize,",
            f"A {prize.label} of scarlet, a lovely surprise.")

def loves_prize_rhyme(hero: Entity, prize: Entity) -> tuple[str, str]:
    return (f"{hero.pronoun().capitalize()} wore the {prize.label} with pride and glee,",
            f"Thinking \"This is the glory meant for me.\"")

def arrive_rhyme(hero: Entity, parent: Entity, activity: Activity) -> tuple[str, str]:
    day = "sunny" if activity.weather else "fine"
    return (f"One {day} day they came to the field so wide,",
            f"{hero.id} felt excitement, could not hide.")

def wants_rhyme(hero: Entity, activity: Activity) -> tuple[str, str]:
    return (f"\"I want to {activity.verb}!\" {hero.pronoun()} said with a shout,",
            f"\"I'll show my glory without any doubt!\"")

def warn_rhyme(parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> tuple[str, str]:
    return (f"\"But your {prize.label} will get {activity.soil},\" {parent.label_word} said,",
            f"\"And you'll be sad when it's dirty and red.\"")

def babble_rhyme(hero: Entity, activity: Activity) -> tuple[str, str]:
    return (f"{hero.id} kept babbling, words like a stream,",
            f"\"I don't care, I'll follow my dream!\"")

def grab_hand_rhyme(parent: Entity, hero: Entity) -> tuple[str, str]:
    return (f"{parent.label_word.capitalize()} took {hero.pronoun('possessive')} hand, gentle and slow,",
            f"\"There's a better way, let's take it slow.\"")

def inner_monologue_rhyme(hero: Entity) -> tuple[str, str]:
    return (f"Inside, {hero.id} thought, \"Am I really brave?\"",
            f"A tiny doubt in the heart's dark cave.")

def compromise_rhyme(hero: Entity, parent: Entity, gear: Gear) -> tuple[str, str]:
    return (f"\"Let's {gear.prep},\" {parent.label_word} said with a smile,",
            f"\"Then you can play for a little while.\"")

def accept_rhyme(hero: Entity, parent: Entity) -> tuple[str, str]:
    return (f"{hero.id} smiled, \"Okay, we'll do it your way,\"",
            f"\"And still have glory at the end of day.\"")

def happy_ending_rhyme(hero: Entity, activity: Activity, prize: Entity) -> tuple[str, str]:
    return (f"So they {activity.verb} together, happy and free,",
            f"The {prize.label} stayed clean, a victory!")


# ---------------------------------------------------------------------------
# The screenplay (rhyming beats)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Finn", hero_type: str = "knight",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "chatty"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1: setup
    line1, line2 = introduce_rhyme(hero)
    world.say(line1); world.say(line2)
    line1, line2 = loves_activity_rhyme(hero, activity)
    world.say(line1); world.say(line2)
    line1, line2 = buys_rhyme(parent, hero, prize)
    world.say(line1); world.say(line2)
    line1, line2 = loves_prize_rhyme(hero, prize)
    world.say(line1); world.say(line2)

    world.para()
    line1, line2 = arrive_rhyme(hero, parent, activity)
    world.say(line1); world.say(line2)
    line1, line2 = wants_rhyme(hero, activity)
    world.say(line1); world.say(line2)

    # Parent warns
    line1, line2 = warn_rhyme(parent, hero, activity, prize)
    world.say(line1); world.say(line2)

    # Hero babbles
    line1, line2 = babble_rhyme(hero, activity)
    world.say(line1); world.say(line2)
    hero.memes["defiance"] += 1

    # Parent grabs hand
    line1, line2 = grab_hand_rhyme(parent, hero)
    world.say(line1); world.say(line2)
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)

    # Inner monologue
    world.para()
    line1, line2 = inner_monologue_rhyme(hero)
    world.say(line1); world.say(line2)
    hero.memes["inner_courage"] += 1

    # Resolution: find gear (we always have a matching gear for valid combos)
    gear_def = select_gear(activity, prize_cfg)
    if gear_def:
        gear_entity = world.add(Entity(
            id=gear_def.id, type="gear", label=gear_def.label,
            owner=hero.id, caretaker=parent.id, protective=True,
            covers=set(gear_def.covers), plural=gear_def.plural,
        ))
        gear_entity.worn_by = hero.id
        line1, line2 = compromise_rhyme(hero, parent, gear_def)
        world.say(line1); world.say(line2)
        world.para()
        line1, line2 = accept_rhyme(hero, parent)
        world.say(line1); world.say(line2)
        line1, line2 = happy_ending_rhyme(hero, activity, prize)
        world.say(line1); world.say(line2)
        hero.memes["joy"] += 1
        hero.memes["conflict"] = 0.0
    else:
        # Should not happen for valid params
        raise StoryError("No gear found – incompatible combo.")

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=True)
    return world


# ---------------------------------------------------------------------------
# Constraint helpers
# ---------------------------------------------------------------------------
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
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "castle": Setting(place="the castle courtyard", indoor=False, affords={"joust", "parade"}),
    "forest": Setting(place="the enchanted forest", indoor=False, affords={"quest", "sing"}),
    "village": Setting(place="the village green", indoor=False, affords={"parade", "sing"}),
}

ACTIVITIES = {
    "joust": Activity(
        id="joust",
        verb="joust with toy lances",
        gerund="jousting with wooden lances",
        rush="gallop toward the dummy",
        mess="dusty",
        soil="dusty and dirty",
        zone={"torso", "legs"},
        weather="sunny",
        keyword="joust",
        tags={"glory", "joust"},
    ),
    "parade": Activity(
        id="parade",
        verb="march in a tiny parade",
        gerund="marching in a play parade",
        rush="start marching proudly",
        mess="dusty",
        soil="dusty and dirty",
        zone={"legs", "feet"},
        weather="sunny",
        keyword="parade",
        tags={"glory", "parade"},
    ),
    "quest": Activity(
        id="quest",
        verb="go on a forest quest",
        gerund="going on a forest quest",
        rush="run into the woods",
        mess="muddy",
        soil="muddy and messy",
        zone={"feet", "legs", "torso"},
        weather="rainy",
        keyword="quest",
        tags={"glory", "quest"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing a brave song",
        gerund="singing brave songs",
        rush="open mouth and belt out",
        mess="dry",
        soil="fine",
        zone={},
        weather="",
        keyword="sing",
        tags={"glory", "song"},
    ),
}

PRIZES = {
    "cloak": Prize(
        label="scarlet cloak",
        phrase="a bright scarlet cloak with golden trim",
        type="cloak",
        region="torso",
    ),
    "ribbon": Prize(
        label="scarlet ribbon",
        phrase="a shiny scarlet ribbon for the hair",
        type="ribbon",
        region="torso",
    ),
    "cape": Prize(
        label="scarlet cape",
        phrase="a flowing scarlet cape",
        type="cape",
        region="torso",
    ),
    "boots": Prize(
        label="scarlet boots",
        phrase="a pair of scarlet boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="old_cloak",
        label="an old cloak",
        covers={"torso"},
        guards={"dusty", "muddy"},
        prep="put on an old cloak first",
        tail="put on the old cloak",
    ),
    Gear(
        id="waders",
        label="rain waders",
        covers={"legs", "feet"},
        guards={"muddy", "wet"},
        prep="put on the rain waders",
        tail="put on the rain waders",
    ),
    Gear(
        id="play_clothes",
        label="old play clothes",
        covers={"legs", "torso"},
        guards={"dusty", "muddy", "dry"},
        prep="change into old play clothes",
        tail="changed into old play clothes",
        plural=True,
    ),
]

GIRL_NAMES = ["Elara", "Lyra", "Nora", "Tessa", "Mira"]
BOY_NAMES = ["Finn", "Kai", "Rory", "Jasper", "Orin"]
TRAITS = ["brave", "chatty", "bold", "dreamy", "eager"]


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
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "glory": [
        ("What does 'glory' mean for a little knight?",
         "Glory means being brave and doing something wonderful, like winning a "
         "contest or helping a friend, so everyone cheers."),
    ],
    "scarlet": [
        ("What color is scarlet?",
         "Scarlet is a bright, rich red, like the color of a rose or a sunset."),
    ],
    "babble": [
        ("What does 'babble' mean?",
         "Babble means to talk a lot, often quickly and excitedly, like when you "
         "are so happy you can't stop telling stories."),
    ],
    "joust": [
        ("What is a joust?",
         "A joust is a pretend fight on horseback using long poles called lances. In a story, "
         "it is a way to show courage and skill."),
    ],
    "parade": [
        ("What is a parade?",
         "A parade is a cheerful march where people walk together, often carrying flags "
         "or wearing special clothes, to celebrate something."),
    ],
    "quest": [
        ("What is a quest?",
         "A quest is an adventurous journey to find something or solve a problem. Knights "
         "often go on quests."),
    ],
    "sing": [
        ("Why do people sing brave songs?",
         "Singing a brave song can make you feel strong and happy, and it helps you "
         "share your feelings with others."),
    ],
}
KNOWLEDGE_ORDER = ["glory", "scarlet", "babble", "joust", "parade", "quest", "sing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f"Write a rhyming story for a child about a {hero.type} named {hero.id} "
        f"who loves to {act.verb} and babble about glory.",
        f"Tell a gentle rhyming tale where {hero.id} wears a {prize.label} and learns "
        f"that listening to {parent.label_word} is part of being brave.",
        f"Create a short rhyming story that includes the words 'glory', 'scarlet', "
        f"and 'babble', with a happy reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    pos = hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the little {hero.type} in the story?",
            answer=f"The little {hero.type} is named {hero.id}. {hero.pronoun().capitalize()} "
                   f"wears a {prize.label} and loves to babble about glory."
        ),
        QAItem(
            question=f"What did {hero.id} dream of doing?",
            answer=f"{hero.id} dreamed of {act.gerund} and winning glory. "
                   f"{hero.pronoun().capitalize()} talked and talked about it."
        ),
        QAItem(
            question=f"Why did {pos} {pw} worry when {hero.id} wanted to {act.verb}?",
            answer=f"{pos.capitalize()} {pw} worried because {pos} {prize.label} would get "
                   f"{act.soil}, and then it would be dirty."
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id}?",
            answer=f"{hero.pronoun().capitalize()} put on {gear.label}, and then {hero.pronoun()} "
                   f"could {act.verb} without ruining {pos} {prize.label}."
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"{hero.pronoun().capitalize()} and {pos} {pw} reconciled and played "
                   f"together. {hero.pronoun().capitalize()} felt brave and happy, "
                   f"and {pos} {prize.label} stayed clean."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("glory")
    tags.add("scarlet")
    tags.add("babble")
    out = []
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
    lines.append("== (3) World-knowledge questions ==")
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


# Curated story set (all valid combos)
CURATED = [
    StoryParams(place="castle", activity="joust", prize="cloak",
                name="Finn", gender="boy", parent="mother", trait="brave"),
    StoryParams(place="forest", activity="quest", prize="cape",
                name="Elara", gender="girl", parent="father", trait="eager"),
    StoryParams(place="village", activity="parade", prize="ribbon",
                name="Nora", gender="girl", parent="mother", trait="chatty"),
    StoryParams(place="castle", activity="parade", prize="boots",
                name="Kai", gender="boy", parent="father", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the parent has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


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
    lines = []
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
        description="Rhyming story world: a child, a scarlet prize, babble, and glory.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true", help="render the curated set")
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
        raise StoryError(explain_gender(args.prize, args.gender))

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
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "chatty"], params.parent)
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

    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
