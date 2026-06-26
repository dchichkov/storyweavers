#!/usr/bin/env python3
"""
storyworlds/worlds/spirit_sandbox_reconciliation_transformation_myth.py
========================================================================

A myth-style storyworld about a child, a Sand Spirit, reconciliation,
and transformation.  Set in a sandbox, the story follows a three-act
shape: desire, conflict, and a magical compromise that changes the sandbox
into a shining kingdom.

Seed: spirit  |  Setting: sandbox  |  Features: Reconciliation, Transformation  |  Style: Myth
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
MESS_KINDS = {"sandy", "scattered"}
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
    magical: bool = False                      # marks items from the spirit
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "spiritess"}
        male = {"boy", "father", "spirit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"spirit": "sand spirit", "spiritess": "sand spirit"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain dataclasses
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the sandbox"
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
    weather: str
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
class Charm:
    """Magical protective item offered by the spirit."""
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


def _r_spirit_reconciliation(world: World) -> list[str]:
    """When the spirit's anger is high and the child is defiant, the spirit
    grabs the child's hand (handled elsewhere).  After acceptance, anger
    goes to zero and joy rises, and the sandbox transforms."""
    for e in world.entities.values():
        if e.type not in ("spirit", "spiritess"):
            continue
        if e.memes["anger"] >= THRESHOLD and world.entities.get("child", None):
            child = world.entities["child"]
            if child.memes.get("accepted", 0) >= THRESHOLD:
                sig = ("reconcile", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.memes["anger"] = 0.0
                e.memes["joy"] += 1
                child.memes["joy"] += 1
                world.facts["reconciled"] = True
                return ["The sand spirit smiled, and the sandbox began to glow with a soft golden light."]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="soak", tag="physical", apply=_r_soak),
    Rule(name="workload", tag="physical", apply=_r_workload),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
    Rule(name="spirit_reconciliation", tag="myth", apply=_r_spirit_reconciliation),
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


def select_charm(activity: Activity, prize: Prize) -> Optional[Charm]:
    for charm in CHARMS:
        if activity.mess in charm.guards and prize.region in charm.covers:
            return charm
    return None


# ---------------------------------------------------------------------------
# Prediction (parent foresees mess)
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
# Verbs
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "dig": "the warm sand slipped through tiny fingers like golden sugar",
        "build": "the sand rose into towers and walls like a real castle",
        "sift": "the grains danced in the sun like tiny stars",
        "bury": "the sand covered toes in a cozy blanket",
    }.get(activity.id, "the sand felt alive with possibility")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} waited, clean and quiet."
    return f"The sun shone, and the {setting.place} sparkled with tiny flakes of mica."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved the sandy kingdom behind the house.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    where = "outside"
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
        f"wore {prize.it()} as if the day had been made specially for {hero.pronoun('object')}."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    go = "went to" if not world.setting.indoor else "were in"
    world.say(
        f"One sunny day, {hero.id} and {hero.pronoun('possessive')} "
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
    clause = f"Your {prize.label} will get {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'd have to clean {prize.it()}"
    world.say(f'"{clause}," {hero.pronoun("possessive")} {parent.label_word} said. "Let's think first."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} heard the warning, but the wish to play was still tugging hard.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {hero.pronoun('possessive')} {parent.label_word} grabbed "
        f"{hero.pronoun('possessive')} hand and said, "
        f'"You can want to {activity.verb}, and we can still choose the safe way."'
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted and crossed {hero.pronoun("possessive")} arms. '
            f'"But I really want to {activity.verb}!" {hero.pronoun()} said.'
        )


def spirit_appears(world: World, hero: Entity) -> None:
    """The Sand Spirit appears when the child is defiant and the mess is
    predicted.  We add the spirit entity here."""
    spirit_gender = random.choice(["spirit", "spiritess"])
    if spirit_gender == "spiritess":
        spirit = world.add(Entity(id="Spirit", kind="character", type="spiritess",
                                  label="the sand spirit", memes=defaultdict(float, {"anger": 1.0})))
    else:
        spirit = world.add(Entity(id="Spirit", kind="character", type="spirit",
                                  label="the sand spirit", memes=defaultdict(float, {"anger": 1.0})))
    world.say(
        f"Just then, a shimmering shape rose from the sand. It was {spirit.label}!"
    )
    world.say(
        f'"Stop!" {spirit.pronoun("subject").capitalize()} said. '
        f'"Your digging will break the hidden sand palace beneath."'
    )


def spirit_grab(world: World, spirit: Entity, hero: Entity) -> None:
    """Spirit grabs the child's hand (magically) to stop them."""
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Before {hero.id} could move, a soft sand tendril curled around "
        f"{hero.pronoun('possessive')} wrist. "
        f'"{hero.pronoun().capitalize()} must listen," whispered {spirit.label}.'
    )


def spirit_compromise(world: World, spirit: Entity, hero: Entity,
                      activity: Activity, prize: Entity) -> Optional[Charm]:
    """Spirit offers a magical charm that protects the prize and helps rebuild."""
    charm_def = select_charm(activity, prize)
    if charm_def is None:
        return None
    charm = world.add(Entity(
        id=charm_def.id, type="charm", label=charm_def.label,
        owner=hero.id, protective=True, covers=set(charm_def.covers),
        plural=charm_def.plural, magical=True,
    ))
    charm.worn_by = hero.id
    # Check that charm actually prevents the mess
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        charm.worn_by = None
        del world.entities[charm.id]
        return None
    world.say(
        f'{spirit.pronoun("possessive").capitalize()} face softened. '
        f'"I know you love to {activity.verb}. Wear this {charm_def.label}, '
        f'and the sand will not touch your prize. Then help me rebuild the palace."'
    )
    return charm_def


def accept_and_transform(world: World, spirit: Entity, hero: Entity,
                         activity: Activity, charm_def: Charm) -> None:
    hero.memes["accepted"] = 1.0
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f'{hero.id} nodded and put on the {charm_def.label}.')
    world.say(f'"I promise to help!" {hero.pronoun("subject")} said.')
    propagate(world, narrate=True)   # triggers reconciliation rule
    world.say(
        f"Together, {hero.id} and {spirit.label} rebuilt the sand palace. "
        f"Towers rose, flags of shell fluttered, and the whole sandbox "
        f"shone like a kingdom of light."
    )
    world.say(
        f"{hero.pronoun().capitalize()} {activity.gerund} with joy, "
        f"{prize_was_clean(hero, world.entities['prize'])}, and the sand "
        f"spirit laughed beside {hero.pronoun('object')}."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lila", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "sunny"

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

    # Spirit enters
    spirit_appears(world, hero)
    spirit = world.get("Spirit")
    spirit_grab(world, spirit, hero)

    world.para()
    pout(world, hero, activity)
    charm_def = spirit_compromise(world, spirit, hero, activity, prize)
    if charm_def:
        accept_and_transform(world, spirit, hero, activity, charm_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, charm=charm_def,
                       spirit=spirit,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=charm_def is not None,
                       reconciled=world.facts.get("reconciled", False))
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "sandbox": Setting(place="the sandbox", indoor=False, affords={"dig", "build", "sift"}),
    "beach_sandbox": Setting(place="the beach sandbox", indoor=False, affords={"dig", "build", "bury"}),
    "indoor_sandbox": Setting(place="the indoor sand table", indoor=True, affords={"sift", "build"}),
}

ACTIVITIES = {
    "dig": Activity(
        id="dig", verb="dig in the sand", gerund="digging in the sand",
        rush="run to the sandpile", mess="sandy", soil="sandy and dirty",
        zone={"feet", "legs"}, weather="sunny", keyword="sand", tags={"sand", "dig"}
    ),
    "build": Activity(
        id="build", verb="build a sandcastle", gerund="building sandcastles",
        rush="start piling up the sand", mess="sandy", soil="covered in sand",
        zone={"feet", "legs", "torso"}, weather="sunny", keyword="castle", tags={"sand", "castle"}
    ),
    "sift": Activity(
        id="sift", verb="sift the sand", gerund="sifting sand",
        rush="grab the sieve", mess="sandy", soil="sandy",
        zone={"torso", "head"}, weather="sunny", keyword="sift", tags={"sand", "sift"}
    ),
    "bury": Activity(
        id="bury", verb="bury feet in the sand", gerund="burying feet in the sand",
        rush="sit and push sand over toes", mess="sandy", soil="sandy",
        zone={"feet"}, weather="sunny", keyword="bury", tags={"sand", "bury"}
    ),
}

CHARMS = [
    Charm(id="sand_boots", label="sand boots", covers={"feet"},
          guards={"sandy"}, prep="put on the sand boots",
          tail="slipped on the sand boots", plural=True),
    Charm(id="sand_smock", label="a sandy smock", covers={"torso"},
          guards={"sandy"}, prep="wear this sandy smock",
          tail="put on the sandy smock", plural=False),
    Charm(id="sand_hat", label="a wide sand hat", covers={"head"},
          guards={"sandy"}, prep="put on the wide sand hat",
          tail="set the sand hat on their head", plural=False),
    Charm(id="sand_apron", label="a sand-proof apron", covers={"legs", "torso"},
          guards={"sandy"}, prep="wrap on the sand apron",
          tail="tied the sand apron around them", plural=False),
]

PRIZES = {
    "sandals": Prize(label="sandals", phrase="new white sandals", type="sandals", region="feet", plural=True),
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "shorts": Prize(label="shorts", phrase="new blue shorts", type="shorts", region="legs", plural=True),
    "hat": Prize(label="hat", phrase="a lovely sun hat", type="hat", region="head"),
}

GIRL_NAMES = ["Lila", "Mira", "Nia", "Sela", "Tala", "Rina", "Ona", "Kira", "Luna", "Zara"]
BOY_NAMES = ["Kai", "Rio", "Milo", "Nico", "Leo", "Finn", "Jax", "Toby", "Eli", "Ollie"]
TRAITS = ["curious", "stubborn", "playful", "brave", "kind", "dreamy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_charm(act, prize):
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
    "sand": [("What is sand made of?",
              "Sand is made of tiny bits of rock, shells, and minerals, all ground "
              "down over a very long time by water and wind.")],
    "castle": [("Why do people build sandcastles?",
                "Building a sandcastle is a fun way to create something beautiful "
                "with your hands, and it can look like a real castle for a little while.")],
    "sift": [("What does it mean to sift sand?",
              "To sift sand means to shake it through a sieve so the tiny grains "
              "fall through and any little stones or shells stay behind.")],
    "bury": [("Why is it fun to bury feet in sand?",
              "Burying your feet in sand feels cool and soft, like a warm blanket, "
              "and it is a silly way to play on the beach.")],
    "spirit": [("What is a sand spirit?",
                "In stories, a sand spirit is a magical being that lives in the "
                "sand and protects the hidden worlds beneath the surface.")],
}
KNOWLEDGE_ORDER = ["sand", "castle", "sift", "bury", "spirit"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short myth-style story for a child that includes the words '
        f'"{kw}" and "spirit".',
        f"Tell a story where a {hero.type} named {hero.id} meets a sand spirit "
        f"while wanting to {act.verb} in {act.id}, and they reconcile through "
        f"a magical transformation.",
        f'Write a simple fable that uses the noun "{kw}" and ends with the sandbox '
        f"shining like a golden kingdom.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    spirit = f.get("spirit", None)
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
                f"{pos} {pw}. They go to {place} on a sunny day, and {hero.id} is "
                f"wearing {pos} {prize.label}."
            ),
        ),
        QAItem(
            question=(
                f"What did {trait} {hero.id} love to do outside before "
                f"the sand spirit appeared?"
            ),
            answer=(
                f"{trait.capitalize()} {hero.id} loved playing outside and "
                f"{act.gerund}. That wish became tricky because the sand spirit "
                f"warned that the {pos} {prize.label} would get sandy."
            ),
        ),
        QAItem(
            question=(
                f"What new {prize.label} did {hero.id}'s {pw} buy for the "
                f"{trait} {hero.type} before the play at {place}?"
            ),
            answer=(
                f"{pos.capitalize()} {pw} bought {obj} {prize.phrase}. "
                f"{hero.id} loved {prize.it()} and wore {prize.it()} for the outing."
            ),
        ),
    ]

    if spirit and f.get("conflict"):
        soil = f.get("predicted_soil", "sandy")
        work = f.get("predicted_workload", 0)
        why = (f"{pos.capitalize()} {pw} was upset because if {hero.id} went to "
               f"{act.verb}, {pos} {prize.label} would get {soil}")
        why += (f", and then {pw} would have to clean {prize.it()}. "
                if work >= THRESHOLD else ". ")
        why += (f"The sand spirit also appeared and warned that digging would "
                f"break the hidden palace. When {hero.id} tried to {act.rush.rstrip(', ')}, "
                f"the spirit gently stopped {obj}.")
        qa.append(QAItem(
            question=(
                f"Why did {hero.id}'s {pw} and the sand spirit worry about "
                f"{pos} {prize.label} when {trait} {hero.id} wanted to "
                f"{act.verb} at {place}?"
            ),
            answer=why,
        ))

    if f.get("resolved"):
        charm = f["charm"]
        charm_name = charm.label
        qa.append(QAItem(
            question=(
                f"How did the {charm_name} help {trait} {hero.id} {act.verb} at "
                f"{place} without ruining {pos} {prize.label}?"
            ),
            answer=(
                f"The sand spirit gave {hero.id} a {charm_name} that kept the "
                f"sand away from {pos} {prize.label}. {hero.id} put it on and "
                f"could {act.verb} safely while helping rebuild the sand palace."
            ),
        ))
        qa.append(QAItem(
            question=(
                f"How did {trait} {hero.id} feel after helping the sand spirit "
                f"rebuild the palace at {place}?"
            ),
            answer=(
                f"{hero.id} felt happy and proud. The sand spirit smiled, and "
                f"the whole sandbox glowed with golden light. {sub} and the "
                f"spirit played together until sunset."
            ),
        ))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    tags.add("spirit")  # always include spirit knowledge
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
        if e.magical:
            bits.append("magical")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="sandbox", activity="dig", prize="sandals", name="Lila",
                gender="girl", parent="mother", trait="curious"),
    StoryParams(place="sandbox", activity="build", prize="shirt", name="Kai",
                gender="boy", parent="father", trait="brave"),
    StoryParams(place="indoor_sandbox", activity="sift", prize="hat", name="Mira",
                gender="girl", parent="mother", trait="kind"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so there is no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the charm catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return (f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s "
            f"item here; try --gender {ok}.)")


# ---------------------------------------------------------------------------
# ASP (Clingo) twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(C, A, P) :- charm(C), prize_at_risk(A, P),
                     mess_of(A, M), guards(C, M),
                     covers(C, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp as _asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(_asp.fact("setting", pid))
        if s.indoor:
            lines.append(_asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(_asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(_asp.fact("activity", aid))
        lines.append(_asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(_asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(_asp.fact("prize", pid))
        lines.append(_asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(_asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(_asp.fact("wears", g, pid))
    for c in CHARMS:
        lines.append(_asp.fact("charm", c.id))
        for m in sorted(c.guards):
            lines.append(_asp.fact("guards", c.id, m))
        for r in sorted(c.covers):
            lines.append(_asp.fact("covers", c.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid/3."))
    return sorted(set(_asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp as _asp
    model = _asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(_asp.atoms(model, "valid_story")))


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
        description="Myth-style story world: a child, a sand spirit, reconciliation, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include QA sets")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    ap.add_argument("--asp", action="store_true", help="list compatible combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP gate matches Python")
    ap.add_argument("--show-asp", action="store_true", help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_charm(act, pr)):
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
            print(f"  {place:15} {act:8} {prize:8}  [{', '.join(genders)}]")
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
