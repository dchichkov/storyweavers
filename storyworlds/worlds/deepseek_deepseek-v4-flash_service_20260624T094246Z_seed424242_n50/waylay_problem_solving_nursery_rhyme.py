#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/waylay_problem_solving_nursery_rhyme.py
============================================================================================================================

A nursery‑rhyme‑style story world where a little one is waylaid by a grumpy
frog and uses problem‑solving (riddles) to reach the berry patch.

Seed words: waylay, Problem Solving, Nursery Rhyme.
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
MESS_KINDS = {"wet", "dirty", "stained", "torn"}
REGIONS = {"feet", "legs", "torso", "hands"}


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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mum", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# World objects
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
        self.riddle: tuple[str, str] = ("", "")   # question, answer

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
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
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
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


RIDDLES = [
    ("What has a face and two hands, but no arms or legs?",
     "A clock."),
    ("What has a head and a tail, but no body?",
     "A coin."),
    ("What has a ring but no finger?",
     "A telephone."),
    ("What has a bed but never sleeps?",
     "A river."),
]


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


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
# Nursery rhyme prose helpers
# ---------------------------------------------------------------------------
def rhyme_setting(setting: Setting, activity: Activity) -> str:
    if setting.place == "the lane":
        return "Down the sunny lane they strolled, / Where daisies white and buttercups bold."
    if setting.place == "the wood":
        return "Through the quiet, shady wood, / Where moss and ferns in silence stood."
    if setting.place == "the meadow":
        return "Across the meadow, fresh and green, / The prettiest place they'd ever seen."
    return f"To {setting.place} they went with cheer, / A lovely time of year."


def rhyme_hero_intro(hero: Entity) -> str:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    return f"There was a {desc} named {hero.id}, / Who loved to play and never hid."


def rhyme_loves_activity(hero: Entity, activity: Activity) -> str:
    return (
        f"{hero.pronoun().capitalize()} loved to {activity.verb} each day, / "
        f"And {activity.gerund} was {hero.pronoun('possessive')} favorite way."
    )


def rhyme_buys(parent: Entity, hero: Entity, prize: Prize) -> str:
    return (
        f"One fine day, {hero.id}'s {parent.label_word} bought / "
        f"{prize.phrase} – just what {hero.pronoun()} sought."
    )


def rhyme_loves_prize(hero: Entity, prize: Entity) -> str:
    return (
        f"{hero.pronoun().capitalize()} loved that {prize.label} through and through, / "
        f"And took it everywhere {hero.pronoun()} knew."
    )


def rhyme_waylay(hero: Entity, parent: Entity, frog: Entity) -> str:
    return (
        f"But waylaying the path was a grumpy frog, / "
        f"Sitting square on a mossy log.\n"
        f'"No one may pass," the frog did croak, / '
        f'"Unless you answer a riddle I spoke."'
    )


def rhyme_warn(parent: Entity, hero: Entity, prize: Entity, riddle: tuple[str, str]) -> str:
    return (
        f'"{hero.pronoun().capitalize()} dear, be careful, do not dive, / '
        f'If you try to wade, the {prize.label} will not survive.\n'
        f"The frog's riddle is our only way – / "
        f"Let's think and solve it, come what may.\""
    )


def rhyme_defy(hero: Entity) -> str:
    return (
        f"But {hero.id} was stubborn, bold, and fast, / "
        f"{hero.pronoun().capitalize()} thought to charge right past."
    )


def rhyme_grab(parent: Entity, hero: Entity) -> str:
    return (
        f"Yet {hero.pronoun('possessive')} {parent.label_word} held {hero.pronoun('possessive')} hand, / "
        f"Soft and gentle, made a stand.\n"
        f'"Patience now, let\'s use our wit, / '
        f"The clever answer is the key to it.\""
    )


def rhyme_solve(hero: Entity, parent: Entity, riddle: tuple[str, str]) -> str:
    q, a = riddle
    return (
        f"The riddle was: “{q}”\n"
        f"{hero.id} thought and thought – then gave a shout, / "
        f'"{a}" – that\'s what it\'s about!\n'
        f"The frog blinked twice and hopped aside, / "
        f"Now the lane was open, free, and wide."
    )


def rhyme_resolve(hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> str:
    return (
        f"Off they went with happy cheer, / "
        f"To {activity.verb} as the day was clear.\n"
        f"The {prize.label} stayed clean, the frog was gone, / "
        f"And {hero.id} and {parent.label_word} danced on."
    )


# ---------------------------------------------------------------------------
# Verb helpers
# ---------------------------------------------------------------------------
def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


# ---------------------------------------------------------------------------
# The screenplay (nursery rhyme style)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Pip", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
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

    # Add a frog (waylayer) as a non‑character entity
    frog = world.add(Entity(
        id="frog",
        kind="thing",
        type="frog",
        label="grumpy frog",
        phrase="a grumpy frog on a mossy log",
        region="",
    ))

    # Pick a random riddle
    riddle = random.choice(RIDDLES)
    world.riddle = riddle
    world.facts["riddle_question"] = riddle[0]
    world.facts["riddle_answer"] = riddle[1]

    # Act 1 – Setup
    world.say(rhyme_setting(setting, activity))
    world.say(rhyme_hero_intro(hero))
    world.say(rhyme_loves_activity(hero, activity))
    world.say(rhyme_buys(parent, hero, prize_cfg))
    world.say(rhyme_loves_prize(hero, prize))

    world.para()
    world.say(rhyme_waylay(hero, parent, frog))

    # Act 2 – Conflict
    hero.memes["desire"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {activity.verb} right then, / "
        f"But the frog said, 'Riddle first, my friend.'"
    )
    warn_said = rhyme_warn(parent, hero, prize, riddle)
    world.say(warn_said)
    hero.memes["defiance"] += 1
    world.say(rhyme_defy(hero))
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(rhyme_grab(parent, hero))

    # Act 3 – Resolution
    world.para()
    world.say(rhyme_solve(hero, parent, riddle))
    # The solving action clears conflict
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(rhyme_resolve(hero, parent, prize, activity))

    # Record facts
    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, frog=frog,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=True)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "lane": Setting(place="the lane", indoor=False, affords={"berry_picking"}),
    "wood": Setting(place="the wood", indoor=False, affords={"mushroom_hunting"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"flower_gathering"}),
}

ACTIVITIES = {
    "berry_picking": Activity(
        id="berry_picking",
        verb="pick berries",
        gerund="picking berries",
        rush="rush to the berry bush",
        mess="stained",
        soil="sticky and stained",
        zone={"hands", "feet"},
        weather="sunny",
        keyword="berries",
        tags={"berry", "stain"},
    ),
    "mushroom_hunting": Activity(
        id="mushroom_hunting",
        verb="hunt for mushrooms",
        gerund="hunting mushrooms",
        rush="dash into the wood",
        mess="dirty",
        soil="muddy and dirty",
        zone={"legs", "feet"},
        weather="rainy",
        keyword="mushroom",
        tags={"mushroom", "dirt"},
    ),
    "flower_gathering": Activity(
        id="flower_gathering",
        verb="gather flowers",
        gerund="gathering flowers",
        rush="run to the flower patch",
        mess="torn",
        soil="torn and dusty",
        zone={"torso", "hands"},
        weather="sunny",
        keyword="flowers",
        tags={"flower", "torn"},
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="a waterproof apron",
        covers={"torso"},
        guards={"stained", "torn"},
        prep="put on this waterproof apron",
        tail="slipped on the waterproof apron",
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"dirty", "stained"},
        prep="pull on your rain boots",
        tail="pulled on their rain boots",
        plural=True,
    ),
    Gear(
        id="gloves",
        label="sturdy gloves",
        covers={"hands"},
        guards={"stained", "dirty"},
        prep="wear these sturdy gloves",
        tail="put on the sturdy gloves",
        plural=True,
    ),
]

PRIZES = {
    "basket": Prize(
        label="basket",
        phrase="a little red basket",
        type="basket",
        region="hands",
        plural=False,
    ),
    "bowl": Prize(
        label="bowl",
        phrase="a pretty blue bowl",
        type="bowl",
        region="hands",
        plural=False,
    ),
    "jar": Prize(
        label="jar",
        phrase="a shiny glass jar",
        type="jar",
        region="hands",
        plural=False,
    ),
}

NAMES = {"girl": ["Lily", "Rose", "Daisy", "Poppy", "Belle"],
         "boy": ["Pip", "Tom", "Sam", "Max", "Finn"]}
TRAITS = ["curious", "stubborn", "brave", "cheerful", "spirited"]


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
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "berry": [("What grows on a berry bush?",
               "Little red and blue fruits that taste sweet. Birds and children love them.")],
    "stain": [("Why can berry juice leave a stain?",
               "Berry juice is very colorful and can soak into cloth, making it hard to wash out.")],
    "mushroom": [("Where do mushrooms grow?",
                  "Mushrooms like to grow in dark, damp woods, under trees and dead leaves.")],
    "dirt": [("Why are muddy clothes dirty?",
              "Mud is wet earth that sticks to things, and it takes scrubbing to get them clean.")],
    "flower": [("Why do flowers have petals?",
                "Petals are the bright, soft parts of a flower that attract bees and butterflies.")],
    "torn": [("How do clothes get torn?",
              "When you brush against sharp thorns or rough rocks, the fabric can rip.")],
    "riddle": [("What is a riddle?",
                "A riddle is a fun puzzle that uses words. You have to guess the answer.")],
    "frog": [("What sound does a frog make?",
              "Frogs croak, ribbit, or chirp. They live near ponds and in damp places.")],
}
KNOWLEDGE_ORDER = ["berry", "stain", "mushroom", "dirt", "flower", "torn", "riddle", "frog"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short nursery‑rhyme story about a {hero.type} named {hero.id} '
        f'who is waylaid by a grumpy frog and must solve a riddle to {act.verb}.',
        f"Tell a rhyming tale that includes the words '{kw}' and 'riddle'.",
        f'Create a gentle problem‑solving story where a parent and child work '
        f'together to answer a frog\'s riddle and reach the {prize.label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    rq, ra = world.riddle
    qa = [
        QAItem(
            question=f"Who was waylaid by a grumpy frog while going to {place}?",
            answer=f"A little {trait} {hero.type} named {hero.id} was waylaid by a grumpy frog "
                   f"on the way to {place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.pronoun().capitalize()} wanted to {act.verb} and was carrying "
                   f"{pos} {prize.label}.",
        ),
        QAItem(
            question=f"What did the frog demand before letting anyone pass?",
            answer=f"The frog demanded that the traveller answer a riddle. The riddle was: “{rq}”",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"How did {hero.id} feel when {pw} told {obj} not to rush?",
            answer=f"{hero.pronoun().capitalize()} felt defiant and wanted to run past, "
                   f"but {pw} gently took {pos} hand and said they should solve the riddle instead.",
        ))
    qa.append(QAItem(
        question=f"What answer did {hero.id} give to the frog's riddle?",
        answer=f"{hero.pronoun().capitalize()} thought hard and said, “{ra}”. The frog hopped away, "
               f"and they could {act.verb} at last.",
    ))
    qa.append(QAItem(
        question=f"How did the story end for {hero.id} and {pw}?",
        answer=f"They picked {act.keyword} happily together, the {prize.label} stayed clean, "
               f"and they danced home as the sun went down.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("riddle")
    tags.add("frog")
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
    lines.append("== (3) World‑knowledge questions ==")
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
    StoryParams(place="lane", activity="berry_picking", prize="basket",
                name="Pip", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="wood", activity="mushroom_hunting", prize="bowl",
                name="Lily", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="meadow", activity="flower_gathering", prize="jar",
                name="Tom", gender="boy", parent="father", trait="cheerful"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% prize_at_risk when activity splashes the region the prize is worn on
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% gear protects if it guards the mess kind and covers the at‑risk region
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).

valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp  # noqa: F811 (lazy)
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
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo matches valid_combos() ({len(clingo_set)} combos).")
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
        description="Nursery‑rhyme story world: waylay, riddle, problem‑solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(
                f"(No story: {act.gerund} affects {sorted(act.zone)}, "
                f"but {pr.label} is worn on {pr.region}. "
                f"No protective gear covers both the mess and the region.)")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"(No story: {PRIZES[args.prize].label} isn't typical for {args.gender}.)")

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
    name = args.name or rng.choice(NAMES[gender])
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
