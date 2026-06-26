#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/weekly_crooked_quest_problem_solving_detective_story.py
=====================================================================================================================================

A standalone story world sketch for a weekly detective quest in a crooked town.
A child detective loves solving weekly mysteries. One week a crooked clue leads
to a problem, but a clever compromise saves the day.
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
MESS_KINDS = {"torn", "lost", "smudged"}
REGIONS = {"hands", "pocket", "bag"}


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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str = "the crooked town"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    """A weekly mystery the hero loves to solve."""
    id: str
    verb: str            # after "wanted to ..."             : "solve the weekly mystery"
    gerund: str          # after "loved ... and ..."         : "solving weekly mysteries"
    rush: str            # after "tried to ..."              : "dash to the crooked clue"
    mess: str            # mess kind key                     : "torn"
    soil: str            # how the prize gets ruined         : "torn and smudged"
    zone: set[str]       # body regions the activity affects : {"hands", "pocket"}
    weather: str         # "foggy" | "sunny" | ""
    keyword: str = ""    # topic word for generation prompts : "mystery"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The detective kit the hero loves and carries."""
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    """Protective gear offered as the compromise (e.g., a magnifying glass case)."""
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


def prize_at_risk(mystery: Mystery, prize: Prize) -> bool:
    return prize.region in mystery.zone


def select_gear(mystery: Mystery, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mystery.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, mystery: Mystery, prize_id: str) -> dict:
    sim = world.copy()
    _do_mystery(sim, sim.get(actor.id), mystery, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


def mystery_delight(mystery: Mystery) -> str:
    return {
        "missing_cat": "the clues were like tiny puzzles waiting to be solved",
        "crooked_sign": "the crooked sign pointed to a secret path",
        "stolen_cookies": "the crumbs told a story of a sneaky thief",
        "lost_key": "the key was hidden where only a clever eye could find it",
    }.get(mystery.id, "the mystery made every corner feel exciting")


def setting_detail(setting: Setting, mystery: Mystery) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the clue board waited."
    if mystery.weather == "foggy":
        return f"The fog made {setting.place} look like a secret world."
    return f"{setting.place.capitalize()} was full of hidden clues."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_mystery(world: World, actor: Entity, mystery: Mystery, narrate: bool = True) -> None:
    if mystery.id not in world.setting.affords:
        return
    world.zone = set(mystery.zone)
    actor.meters[mystery.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who noticed every crooked clue in town.")


def loves_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["love_play"] += 1
    where = "inside" if world.setting.indoor else "outside"
    world.say(
        f"{hero.pronoun().capitalize()} loved playing {where} and {mystery.gerund}; "
        f"{mystery_delight(mystery)}."
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
        f"carried {prize.it()} everywhere, ready for the weekly quest."
    )


def arrive(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    day = {"foggy": "One foggy morning, ", "sunny": "One sunny morning, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} "
        f"{parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, mystery))


def wants(world: World, hero: Entity, parent: Entity, mystery: Mystery) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {mystery.verb} right away, but "
        f"{hero.pronoun('possessive')} {parent.label_word} held up a gentle hand."
    )


def warn(world: World, parent: Entity, hero: Entity, mystery: Mystery, prize: Entity) -> bool:
    pred = predict_mess(world, hero, mystery, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = mystery.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize.label} {mystery.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let\'s think first."')
    return True


def defies(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to solve the mystery was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {mystery.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, mystery: Mystery) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can want to {mystery.verb}, and we can still choose the safe way."'
    )


def pout(world: World, hero: Entity, mystery: Mystery) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {mystery.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, parent: Entity, hero: Entity, mystery: Mystery,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(mystery, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, mystery, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} looked at the '
        f'{prize.label}, then back at {hero.id}, and smiled. '
        f'"How about we {gear_def.prep} and {mystery.verb} together?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, mystery: Mystery, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged "
        f"{hero.pronoun('possessive')} {parent.label_word}. "
        f'"Yay, let\'s do it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {mystery.gerund}, "
        f"{prize_was_clean(hero, prize)}, and {parent.label_word} was helping "
        f"{hero.pronoun('object')} follow the crooked clues."
    )


def tell(setting: Setting, mystery: Mystery, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else mystery.weather

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

    introduce(world, hero)
    loves_mystery(world, hero, mystery)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, mystery)
    wants(world, hero, parent, mystery)
    warn(world, parent, hero, mystery, prize)
    defies(world, hero, mystery)
    grab_hand(world, parent, hero, mystery)

    world.para()
    pout(world, hero, mystery)
    gear_def = compromise(world, parent, hero, mystery, prize)
    if gear_def:
        accept(world, parent, hero, mystery, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       mystery=mystery, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "crooked_town": Setting(place="the crooked town", indoor=False, affords={"missing_cat", "crooked_sign", "stolen_cookies", "lost_key"}),
    "library": Setting(place="the library", indoor=True, affords={"missing_cat", "lost_key"}),
    "park": Setting(place="the park", indoor=False, affords={"crooked_sign", "stolen_cookies"}),
}

MYSTERIES = {
    "missing_cat": Mystery(
        id="missing_cat",
        verb="solve the mystery of the missing cat",
        gerund="solving the mystery of the missing cat",
        rush="dash to the crooked alley",
        mess="torn",
        soil="torn and smudged",
        zone={"hands", "pocket"},
        weather="foggy",
        keyword="mystery",
        tags={"cat", "clue"},
    ),
    "crooked_sign": Mystery(
        id="crooked_sign",
        verb="follow the crooked sign",
        gerund="following the crooked sign",
        rush="run to the crooked signpost",
        mess="lost",
        soil="lost and dirty",
        zone={"pocket", "bag"},
        weather="foggy",
        keyword="crooked",
        tags={"sign", "path"},
    ),
    "stolen_cookies": Mystery(
        id="stolen_cookies",
        verb="find the stolen cookies",
        gerund="finding the stolen cookies",
        rush="sneak to the cookie jar",
        mess="smudged",
        soil="smudged and crumbly",
        zone={"hands"},
        weather="sunny",
        keyword="cookies",
        tags={"cookie", "thief"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        verb="find the lost key",
        gerund="finding the lost key",
        rush="search under the crooked bench",
        mess="lost",
        soil="lost and dusty",
        zone={"pocket", "bag"},
        weather="",
        keyword="key",
        tags={"key", "lock"},
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="detective gloves",
        covers={"hands"},
        guards={"torn", "smudged"},
        prep="put on your detective gloves",
        tail="put on the detective gloves",
    ),
    Gear(
        id="pouch",
        label="a clue pouch",
        covers={"pocket"},
        guards={"lost"},
        prep="use your clue pouch",
        tail="used the clue pouch",
    ),
    Gear(
        id="backpack",
        label="a small backpack",
        covers={"bag"},
        guards={"lost"},
        prep="take your small backpack",
        tail="took the small backpack",
    ),
]

PRIZES = {
    "notebook": Prize(
        label="notebook",
        phrase="a shiny detective notebook",
        type="notebook",
        region="pocket",
    ),
    "magnifying_glass": Prize(
        label="magnifying glass",
        phrase="a new magnifying glass with a bright lens",
        type="magnifying_glass",
        region="hands",
    ),
    "badge": Prize(
        label="badge",
        phrase="a shiny detective badge",
        type="badge",
        region="pocket",
    ),
    "flashlight": Prize(
        label="flashlight",
        phrase="a small detective flashlight",
        type="flashlight",
        region="bag",
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "clever", "stubborn", "brave", "spirited", "lively"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = MYSTERIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "cat": [("What is a clue?",
             "A clue is a small piece of information that helps you solve a mystery.")],
    "crooked": [("What does crooked mean?",
                 "Crooked means not straight. A crooked sign points in a funny direction.")],
    "cookie": [("Why do detectives look for crumbs?",
               "Crumbs are tiny pieces of food that can show where someone has been.")],
    "key": [("What is a key for?",
             "A key opens a lock. If you find the right key, you can open a door or a box.")],
    "detective": [("What does a detective do?",
                   "A detective looks for clues and solves mysteries.")],
    "gloves": [("Why do detectives wear gloves?",
                "Gloves keep your hands clean and protect important clues from getting smudged.")],
    "pouch": [("What is a clue pouch for?",
               "A clue pouch holds small items you find so you don't lose them.")],
    "backpack": [("Why use a backpack for a mystery?",
                  "A backpack lets you carry your tools and clues without dropping them.")],
}
KNOWLEDGE_ORDER = ["cat", "crooked", "cookie", "key", "detective", "gloves", "pouch", "backpack"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["mystery"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a child, a '
        f'mystery, a compromise" that includes the word "{kw}".',
        f"Tell a gentle story where a {hero.type} named {hero.id} wants to "
        f"{act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries "
        f"about {prize.phrase}, and they find a happy compromise.",
        f'Write a simple story that uses the noun "{kw}" and ends with a parent '
        f"and child pausing to choose a safer way to solve the mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["mystery"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    where = "inside" if world.setting.indoor else "outside"
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    day = {"foggy": "foggy morning", "sunny": "sunny morning"}.get(world.weather, "play day")
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a little {trait} {hero.type} named {hero.id} and "
                f"{pos} {pw}. They go to {place} on a {day}, and {hero.id} is "
                f"carrying {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do {where} in {place} before "
                f"{pw} worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved playing {where} and "
                f"{act.gerund}. That wish became tricky because {pos} "
                f"{prize.label} could get {act.soil}."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} buy for the "
                f"{trait} {hero.type} before "
                f"the {act.keyword or act.mess} mystery at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and carried {prize.it()} for the quest."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was upset because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then {pw} would have to clean {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, {pos} {pw} "
                f"held {pos} hand and reminded {obj} they could still want to "
                f"{act.verb} while choosing a safer way.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} worry about {pos} {prize.label} "
                f"when {trait} {hero.id} wanted to {act.verb} at {place}?"
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
                f"How did {gear.label} help {trait} {hero.id} {act.verb} at {place} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without ruining {pos} {prize.label}. "
                f"The plan let {obj} solve the mystery while {pos} {prize.label} stayed clean."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after {pw} agreed to the {gear_plan} "
                f"plan for the {act.keyword or act.mess} mystery at {place}?"
            ),
            answer=(
                f"{hero.id} felt happy and hugged {pos} {pw} once they agreed "
                f"on the plan for {pos} {prize.label}. At the end, {sub} was "
                f"{act.gerund} with {pw} helping nearby."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["mystery"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
        place="crooked_town",
        mystery="missing_cat",
        prize="notebook",
        name="Lily",
        gender="girl",
        parent="mother",
        trait="curious",
    ),
    StoryParams(
        place="park",
        mystery="crooked_sign",
        prize="magnifying_glass",
        name="Tim",
        gender="boy",
        parent="father",
        trait="clever",
    ),
    StoryParams(
        place="library",
        mystery="lost_key",
        prize="flashlight",
        name="Mia",
        gender="girl",
        parent="aunt",
        trait="brave",
    ),
    StoryParams(
        place="crooked_town",
        mystery="stolen_cookies",
        prize="badge",
        name="Ben",
        gender="boy",
        parent="uncle",
        trait="spirited",
    ),
]


def explain_rejection(mystery: Mystery, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(mystery, prize):
        return (f"(No story: {mystery.gerund} affects {sorted(mystery.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{mystery.mess}, so the parent has no honest warning. "
                f"Try a prize carried on {sorted(mystery.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {mystery.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


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
    for aid, a in MYSTERIES.items():
        lines.append(asp.fact("mystery", aid))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a weekly mystery, a compromise. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
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
    if args.mystery and args.prize:
        act, pr = MYSTERIES[args.mystery], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mystery, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        mystery=mystery,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery],
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
        print(f"{len(triples)} compatible (place, mystery, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:15} {act:15} {prize:15}  [{', '.join(genders)}]")
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
            header = f"### {p.name}: {p.mystery} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
