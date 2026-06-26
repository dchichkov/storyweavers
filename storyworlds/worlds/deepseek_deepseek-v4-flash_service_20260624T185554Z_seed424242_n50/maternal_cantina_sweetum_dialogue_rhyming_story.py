#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/maternal_cantina_sweetum_dialogue_rhyming_story.py
==============================================================================================================================

A rhyming storyworld about a child, a mother, and a sweetum at the cantina.
The simulated state drives prose in rhyming couplets.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
MESS_KINDS = {"sticky", "crumbly"}
REGIONS = {"hands", "face", "lap"}


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


@dataclass
class Setting:
    place: str = "the cantina"
    indoor: bool = True
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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sticky(world: World) -> list[str]:
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
                sig = ("sticky", item.id, mess)
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
    Rule(name="sticky", tag="physical", apply=_r_sticky),
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Rhyming prose helpers
# ---------------------------------------------------------------------------
def _rhyme_intro(name: str, trait: str, gender: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name} was a {trait} little one, {pronoun} always loved to run.\n"
        f"At the cantina {pronoun} would go, for a sweetum yes or no."
    )


def _rhyme_love_activity(name: str, gender: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name} loved the sweetums so, {pronoun} loved the sticky show.\n"
        f"\"Let me have a sweetum please!\" {pronoun} would say with sticky ease."
    )


def _rhyme_buy(name: str, mom: str, prize_phrase: str) -> str:
    return (
        f"That day, {mom} smiled and bought a treat,\n"
        f"{prize_phrase}, so sticky and sweet."
    )


def _rhyme_love_prize(name: str, gender: str, prize_label: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name} held the {prize_label} tight, eyes so bright.\n"
        f"\"Mine!\" {pronoun} squealed with all {pronoun} might."
    )


def _rhyme_arrive(name: str, mom: str, place: str, activity: Activity) -> str:
    return (
        f"One sunny day, to {place} they came,\n"
        f"{name} and {mom}, calling the treat's name.\n"
        f"The counters gleamed, the smells were grand,\n"
        f"A sweetum waiting in the land."
    )


def _rhyme_wants(name: str, mom: str, verb: str) -> str:
    return (
        f"{name} wanted to {verb} right there,\n"
        f"But {mom} said, \"Wait, we must take care.\""
    )


def _rhyme_warn(mom: str, name: str, soil: str, prize_label: str) -> str:
    return (
        f"\"{name}, if you eat that now,\n"
        f"your {prize_label} will be {soil}, I vow.\n"
        f"And then I'll have to scrub and clean,\n"
        f"Is that the best you've ever seen?\""
    )


def _rhyme_defy(name: str, gender: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name} pouted, stomped a foot,\n"
        f"\"I don't care!\" {pronoun} gave a hoot.\n"
        f"{pronoun.capitalize()} tried to grab the sticky prize,\n"
        f"With longing in {pronoun.pronoun('possessive')} eyes."
    )


def _rhyme_grab(name: str, mom: str, gender: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"But {mom} caught {pronoun} by the hand,\n"
        f"\"Slow down, sweetie, understand.\"\n"
        f"\"You can want it, oh so much,\n"
        f"but let's find a way that's such.\""
    )


def _rhyme_pout(name: str, gender: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name} crossed {pronoun.pronoun('possessive')} arms, a grumpy face,\n"
        f"\"But I want it now!\" {pronoun} said with grace."
    )


def _rhyme_compromise(mom: str, gear_label: str, verb: str) -> str:
    return (
        f"{mom} said, \"How about this clever plan?\n"
        f"Use {gear_label} first, then eat, dear fan.\n"
        f"Your hands and face will stay so clean,\n"
        f"the sweetum won't be mean!\"" if gear_label == "a napkin" else
        f"{mom} said, \"How about this clever plan?\n"
        f"Use {gear_label} first, then eat, dear fan.\""
    )


def _rhyme_accept(name: str, mom: str, gender: str, gear_tail: str, gerund: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"{name}'s face lit up, a happy glow,\n"
        f"\"Yes!\" {pronoun} shouted, \"Let's go!\"\n"
        f"They {gear_tail}, and soon {pronoun} was {gerund},\n"
        f"Sticky joy, but hands not suffering."
    )


def _rhyme_end(name: str, gender: str, prize_label: str) -> str:
    pronoun = "she" if gender == "girl" else "he"
    return (
        f"And when the sweetum was all done,\n"
        f"{name} smiled at the golden sun.\n"
        f"{pronoun.capitalize()} hugged {pronoun.pronoun('possessive')} {prize_label} (clean and fine),\n"
        f"\"Thanks, Mom, that plan was divine!\""
    )


# ---------------------------------------------------------------------------
# The screenplay – driven by state, output is rhyming couplets
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["playful", "stubborn"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the mother"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    world.say(_rhyme_intro(hero.id, hero.traits[1] if len(hero.traits) > 1 else "playful", hero.type))
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
        world.say(_rhyme_end(hero.id, hero.type, prize.label))

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(_rhyme_love_activity(hero.id, hero.type))


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(_rhyme_buy(hero.id, parent.label_word, prize.phrase))


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(_rhyme_love_prize(hero.id, hero.type, prize.label))


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(_rhyme_arrive(hero.id, parent.label_word, world.setting.place, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(_rhyme_wants(hero.id, parent.label_word, activity.verb))


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(_rhyme_warn(parent.label_word, hero.id, activity.soil, prize.label))
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(_rhyme_defy(hero.id, hero.type))


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(_rhyme_grab(hero.id, parent.label_word, hero.type))


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(_rhyme_pout(hero.id, hero.type))


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
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(_rhyme_compromise(parent.label_word, gear_def.label, activity.verb))
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(_rhyme_accept(hero.id, parent.label_word, hero.type,
                            gear_def.tail, activity.gerund))


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "cantina": Setting(place="the cantina", indoor=True, affords={"order_sweetum"}),
}

ACTIVITIES = {
    "order_sweetum": Activity(
        id="order_sweetum",
        verb="buy a sweetum",
        gerund="eating a sweetum",
        rush="grab the sweetum",
        mess="sticky",
        soil="sticky and gooey",
        zone={"hands", "face"},
        weather="sunny",
        keyword="sweetum",
        tags={"sweetum", "sticky"},
    ),
}

PRIZES = {
    "sweetum": Prize(
        label="sweetum",
        phrase="a big, sticky sweetum",
        type="sweetum",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="napkin",
        label="a napkin",
        covers={"hands", "face"},
        guards={"sticky"},
        prep="wrap a napkin around your hands",
        tail="wrapped a napkin around his hands",
        plural=False,
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo"]
TRAITS = ["playful", "curious", "stubborn", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


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
    "sweetum": [("What is a sweetum?",
                 "A sweetum is a sticky, sweet treat you can buy at a cantina. It is fun to eat but can make a mess.")],
    "sticky": [("Why do sticky things get on your hands?",
                "Sticky things like sweetums have a gooey coating that comes off on your skin when you hold them.")],
    "cantina": [("What is a cantina?",
                 "A cantina is a little place where you can buy food and treats like sweetums.")],
    "napkin": [("What does a napkin do?",
                "A napkin is a piece of cloth or paper that you use to wipe your hands and face, so they stay clean.")],
}
KNOWLEDGE_ORDER = ["sweetum", "sticky", "cantina", "napkin"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a rhyming story for a child about a "{kw}" and a wise mother.',
        f"Tell a short poem where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} "
        f"{parent.label_word} suggests using a napkin.",
        f'Create a gentle rhyming tale that includes the word "{kw}" and ends with a hug.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} visits {place} to {act.verb}?",
            answer=(
                f"It is about a little {hero.type} named {hero.id} and {pos} {pw}. "
                f"They go to {place} where {hero.id} wants a {prize.label}."
            ),
        ),
        QAItem(
            question=f"What did {hero.id} love to do before {pw} worried about {pos} {prize.label}?",
            answer=(
                f"{hero.id} loved having a {prize.label} and {act.gerund}. "
                f"{pos.capitalize()} {pw} was concerned because the treat would get {act.soil}."
            ),
        ),
        QAItem(
            question=f"What new {prize.label} did {hero.id}'s {pw} buy for {pos}?",
            answer=(
                f"{pos.capitalize()} {pw} bought {prize.phrase}. "
                f"{hero.id} held it tight and was very happy."
            ),
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} worry about {pos} {prize.label}?",
            answer=(
                f"{pos.capitalize()} {pw} knew that if {hero.id} ate it right away, "
                f"the {prize.label} would get {act.soil} and make a mess. "
                f"Then {pw} would have to clean it."
            ),
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} enjoy the {prize.label} without mess?",
            answer=(
                f"They used the {gear.label} to cover {hero.pronoun('possessive')} hands and face, "
                f"so the sticky sweetum did not get on {pos} clothes or skin."
            ),
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel after {pw} suggested the {gear.label} plan?",
            answer=(
                f"{hero.id} felt happy and hugged {pw}. "
                f"At the end, {sub} was {act.gerund} with a clean {prize.label}."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        place="cantina",
        activity="order_sweetum",
        prize="sweetum",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="playful",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} is on the {prize.region} -- not at risk. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: no gear protects {noun} from {activity.mess} on {prize.region}.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {prize_id} isn't typical for a {gender}; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# ASP
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
        description="Rhyming story: a child, a sweetum, a mother. Random if unspecified.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother"])
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
    parent = args.parent or "mother"
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
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
