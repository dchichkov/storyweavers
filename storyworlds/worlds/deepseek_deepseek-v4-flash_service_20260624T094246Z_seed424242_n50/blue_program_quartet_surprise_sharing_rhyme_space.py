#!/usr/bin/env python3
"""
storyworlds/worlds/blue_program_quartet_surprise_sharing_rhyme_space.py
========================================================================

A standalone *story world* sketch for "The Blue Planet Quartet" tale and
close, *constraint-checked* variations of it.

Initial story (used to build a world model):
---
Once upon a time, there were four friends who called themselves the Space
Quartet. They lived on a starbase orbiting a beautiful blue planet. Commander
Blue gave them a special star map that showed all the secret places in the
galaxy. The Quartet loved that map and carried it everywhere.

One day, a new exploration program was uploaded to the station. It promised
to take them to a new galaxy! The Quartet wanted to try it right away, but
Commander Blue said no. "The program is still in testing," she said. "Space
dust could damage your star map, and then you would lose the way."

The Quartet was disappointed. "But we want to explore!" they said. Commander
Blue smiled. "How about we share what we know and write a rhyme to remember
the safe route? Then we can use the program together, carefully."

The Quartet agreed. They shared their knowledge, wrote a fun rhyme, and used
the program safely. What a surprise - the new galaxy was full of friendly
aliens and a twin blue planet!

Causal state updates:
---
    do activity                  -> actor.<mess> += 1
                                    actor.curiosity += 1
    actor messy + carried item   -> item.<mess>++, item.damaged++   only if the
                                    item's zone is in the splash zone and no
                                    protective gear covers that zone
    carried item damaged         -> item.commander.workload += 1   (more work
                                    for the commander)

Scripted social/emotional beats:
---
    warning ignored              -> actor.defiance += 1
    commander grabs a defiant    -> actor.conflict += 1
      child/group
    compromise accepted          -> actor.joy/teamwork += 1;
                                    actor.conflict -> 0
    rhyme shared                 -> actor.rhyme_memory += 1
    surprise discovered          -> actor.surprise += 1
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

# Make the shared result containers importable when this script is run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"dusty", "smudged", "scratched"}
REGIONS = {"hands", "chest", "belt"}


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
        female = {"commander", "captain", "woman"}
        male = {"commander", "captain", "man"}
        if self.type in female and self.id in ("Commander Blue", "Captain Nova"):
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"commander": "Commander"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the starbase"
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
    weather: str = "stellar"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "nonbinary"})


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
                item.meters["damaged"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and damaged."
                )
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["damaged"] < THRESHOLD or not item.caretaker:
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


# ---------------------------------------------------------------------------
# Prediction
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["damaged"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "explore": "the stars whizzed past like friendly fireflies",
        "scan": "the scanner hummed a gentle tune that felt like a lullaby",
    }.get(activity.id, "it made the day feel full of wonder")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the viewport showed the blue planet below."
    return f"{setting.place.capitalize()} stretched wide and ready for adventure."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe and clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["curiosity"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was one of the Space Quartet, four friends who explored "
        f"the galaxy together from their starbase."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_explore"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund} among the stars; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, commander: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Commander Blue gave {hero.id} and the Quartet {prize.phrase} as a "
        f"gift for their勇敢探索."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"carried {prize.it()} everywhere, as if the stars themselves "
        f"had made it for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, commander: Entity, activity: Activity) -> None:
    day = "One stellar morning, "
    world.say(
        f"{day}{hero.id} and Commander Blue gathered at the console "
        f"on {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, commander: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but "
        f"Commander Blue raised a gentle hand."
    )


def warn(world: World, commander: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"The {activity.mess} space dust could damage your {prize.label}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I would have to repair {prize.it()}"
    world.say(f'"{clause}," Commander Blue said. "Let us think first."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} heard the warning, but the wish to explore was "
        f"still tugging hard."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, commander: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but Commander Blue gently touched {hero.pronoun('possessive')} "
        f"shoulder and said, 'You can want to {activity.verb}, and we can "
        f"still choose the safe way together.'"
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} looked down and sighed. "But I really want to '
            f'{activity.verb}!" {hero.pronoun()} said.'
        )


def compromise(world: World, commander: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=commander.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'Commander Blue looked at the {prize.label}, then back at {hero.id}, '
        f'and smiled. "How about we {gear_def.prep} and {activity.verb} '
        f'together? We can share what we know and learn a rhyme to remember '
        f'the safe route."'
    )
    return gear_def


def accept(world: World, commander: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["teamwork"] += 1
    hero.memes["rhyme_memory"] += 1
    hero.memes["surprise"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up and {hero.pronoun()} hugged Commander Blue. "
        f'"Yay, let us do it!" {hero.pronoun()} said.'
    )
    world.say(
        f"They {gear_def.tail}. Together they chanted the rhyme: "
        f"'Blue planet bright, share the light, explore with care, '
        f'we will get there!'"
    )
    world.say(
        f"Then they used the program. What a surprise - the new galaxy "
        f"glowed with twin blue planets full of friendly stars! "
        f"{hero.pronoun().capitalize()} {activity.gerund}, "
        f"{prize_was_clean(hero, prize)}, and Commander Blue smiled beside "
        f"{hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Astra", hero_type: str = "explorer",
         hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["curious"] + (hero_traits or ["brave", "eager"]),
    ))
    commander = world.add(Entity(
        id="Commander Blue", kind="character", type="commander",
        label="Commander Blue",
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=commander.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, commander, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2
    world.para()
    arrive(world, hero, commander, activity)
    wants(world, hero, commander, activity)
    warn(world, commander, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, commander, hero, activity)

    # Act 3
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, commander, hero, activity, prize)
    if gear_def:
        accept(world, commander, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, commander=commander, prize=prize,
                       prize_cfg=prize_cfg, activity=activity,
                       setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "starbase": Setting(place="the starbase", indoor=True, affords={"explore", "scan"}),
    "ship": Setting(place="the starship", indoor=True, affords={"explore"}),
    "station": Setting(place="the space station", indoor=True, affords={"scan"}),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="explore the new galaxy using the star program",
        gerund="exploring new galaxies",
        rush="start the program immediately",
        mess="dusty",
        soil="dusty and scratched",
        zone={"hands", "chest"},
        weather="stellar",
        keyword="explore",
        tags={"explore", "dusty", "stars"},
    ),
    "scan": Activity(
        id="scan",
        verb="scan the new star cluster with the program",
        gerund="scanning star clusters",
        rush="turn on the scanner at once",
        mess="smudged",
        soil="smudged and blurry",
        zone={"hands"},
        weather="stellar",
        keyword="scan",
        tags={"scan", "smudged", "stars"},
    ),
}

GEAR = [
    Gear(
        id="case",
        label="a protective star case",
        covers={"hands"},
        guards={"dusty", "smudged", "scratched"},
        prep="put your map in the protective star case",
        tail="placed the map in the protective star case",
    ),
    Gear(
        id="pouch",
        label="a clear shield pouch",
        covers={"chest"},
        guards={"dusty", "scratched"},
        prep="wear the clear shield pouch over your badge",
        tail="wore the clear shield pouch over the badge",
    ),
    Gear(
        id="gloves",
        label="clean handling gloves",
        covers={"hands"},
        guards={"smudged", "dusty"},
        prep="put on the clean handling gloves",
        tail="put on the clean handling gloves",
        plural=True,
    ),
]

PRIZES = {
    "map": Prize(
        label="star map",
        phrase="a beautiful star map that glowed with tiny lights",
        type="map",
        region="hands",
    ),
    "badge": Prize(
        label="space badge",
        phrase="a shiny space badge with a blue planet emblem",
        type="badge",
        region="chest",
    ),
    "log": Prize(
        label="captain's log",
        phrase="a special captain's log with a silver cover",
        type="log",
        region="hands",
    ),
}

HERO_NAMES = ["Astra", "Orion", "Nova", "Sol", "Luna", "Vega", "Rigel", "Lyra", "Zara", "Kai"]
TRAITS = ["curious", "brave", "eager", "playful", "bright", "gentle", "bold", "cheerful"]


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
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "explore": [("What does it mean to explore space?",
                 "To explore space means to travel among the stars and discover "
                 "new planets, galaxies, and wonders. It is like going on a "
                 "great adventure.")],
    "dusty": [("Why is space dusty?",
               "Space has tiny particles called cosmic dust. When you travel "
               "through space, this dust can settle on things like maps and "
               "badges, making them dusty.")],
    "stars": [("What are stars made of?",
               "Stars are giant balls of hot gas, mostly hydrogen and helium. "
               "They shine because of nuclear reactions deep inside them.")],
    "map": [("What is a star map?",
             "A star map is a special chart that shows where stars, planets, "
             "and galaxies are located. Explorers use it to find their way.")],
    "badge": [("What is a space badge?",
               "A space badge is a pin or emblem that space explorers wear to "
               "show they are part of a crew or have completed a mission.")],
    "rhyme": [("Why do people use rhymes?",
               "Rhymes help people remember things. A short, catchy rhyme is "
               "easier to recall than a long list of instructions.")],
    "surprise": [("What does it feel like to discover a surprise?",
                  "Discovering a surprise feels exciting and wonderful, like "
                  "finding something you did not expect that makes you happy.")],
    "sharing": [("Why is sharing important?",
                 "Sharing helps us work together and learn from each other. "
                 "When we share, everyone can enjoy and benefit.")],
}
KNOWLEDGE_ORDER = ["explore", "stars", "dusty", "map", "badge", "rhyme", "surprise", "sharing"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, commander, act, prize = f["hero"], f["commander"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short story for a 3-to-5-year-old on the theme "a quartet, '
        f'a program, a surprise" that includes the word "{kw}".',
        f"Tell a gentle space story where a young explorer named {hero.id} "
        f"wants to {act.verb} but Commander Blue worries about "
        f"{hero.pronoun('possessive')} {prize.phrase}, and they find a "
        f"happy compromise through sharing and a rhyme.",
        f'Write a simple rhyming story that uses the noun "{kw}" and ends '
        f"with a surprise discovery in a new galaxy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, commander, prize, act = f["hero"], f["commander"], f["prize"], f["activity"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "curious"), hero.type)
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who is the story about when {hero.id} visits {place} to "
                f"{act.verb} with {pos} {prize.label}?"
            ),
            answer=(
                f"It is about a {trait} young explorer named {hero.id} and "
                f"Commander Blue. They are on {place}, and {hero.id} has "
                f"{pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do among the stars "
                f"before Commander Blue worried about {pos} {prize.label}?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved {act.gerund} among "
                f"the stars. That wish became tricky because {pos} "
                f"{prize.label} could get damaged by space dust."
            ),
        ),
        QAItem(
            question=(
                f"What special {prize.label} did Commander Blue give "
                f"{hero.id} before the {act.keyword or act.mess} "
                f"at {place}?"
            ),
            answer=(
                f"Commander Blue gave {hero.id} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and carried {prize.it()} "
                f"everywhere."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "dusty and scratched")
        work = f.get("predicted_workload", 0)
        why = (f"Commander Blue was concerned because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then Commander Blue would have to repair {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"When {hero.id} tried to {act.rush.rstrip(', ')}, Commander Blue "
                f"gently stopped {obj} and reminded {obj} they could still "
                f"{act.verb} while choosing a safer way.")
        qa.append(QAItem(
            question=(
                f"Why did Commander Blue worry about {hero.id}'s {prize.label} "
                f"when {hero.id} wanted to {act.verb} at {place}?"
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
                f"How did {gear.label} help {hero.id} {act.verb} at {place} "
                f"without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"They agreed to use {gear.label} first, so {hero.id} could "
                f"{act.verb} at {place} without damaging {pos} {prize.label}. "
                f"The plan let {obj} explore while {pos} {prize.label} stayed safe."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What surprise did {hero.id} discover after using the "
                f"program safely with Commander Blue?"
            ),
            answer=(
                f"The surprise was a new galaxy with twin blue planets full "
                f"of friendly stars! {hero.id} was amazed and happy."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"What rhyme did {hero.id} and Commander Blue chant "
                f"to remember the safe route?"
            ),
            answer=(
                f"They chanted: 'Blue planet bright, share the light, explore "
                f"with care, we will get there!' The rhyme helped them "
                f"remember the way."
            ),
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    tags.add("rhyme")
    tags.add("surprise")
    tags.add("sharing")
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:18} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starbase", activity="explore", prize="map", name="Astra", trait="brave"),
    StoryParams(place="station", activity="scan", prize="log", name="Orion", trait="curious"),
    StoryParams(place="ship", activity="explore", prize="badge", name="Nova", trait="eager"),
    StoryParams(place="starbase", activity="scan", prize="map", name="Luna", trait="gentle"),
    StoryParams(place="station", activity="explore", prize="log", name="Kai", trait="bold"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "are" if prize.plural else "is"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} touches {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so Commander Blue has no honest warning. "
                f"Try a prize carried on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must "
            f"actually cover the at-risk item, so this argument is rejected.)")


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
valid_story(Place, A, P) :- valid(Place, A, P).
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
# Standard storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a quartet, a program, a surprise. "
                    "Unspecified choices are picked at random (seeded).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, activity, prize_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(HERO_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name,
                 hero_traits=[params.trait, "eager"])
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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:10} {act:8} {prize:8}")
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
