#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/vicious_piccalilli_extinction_friendship_myth.py
================================================================================================================================

A mythic TinyStory: two friends must protect the last jar of Piccalilli from a
vicious wyrm, lest the precious recipe be lost to extinction.  The story uses
state simulation and a forward‑chaining rule engine.  Supports --all, --qa,
--asp, --verify, etc.

Seed words: vicious, piccalilli, extinction.  Style: Myth.  Feature: Friendship.
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

# Physical meter keys
MESS_KINDS = {"scorched", "shattered", "frozen"}

# Body regions (mythic gear covers)
REGIONS = {"hands", "arms", "torso"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
    type: str = "thing"                 # hero, friend, wyrm, gear, prize
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
        female = {"heroine", "sister", "goddess"}
        male = {"hero", "brother", "god"}
        creature = {"fox", "bird", "wyrm"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in creature:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the Sunken Valley"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str           # e.g. "gather the Last Piccalilli"
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
    genders: set[str] = field(default_factory=lambda: {"hero", "heroine"})


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
# Causal Rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_ruin(world: World) -> list[str]:
    """If a character is messy and prize is uncovered, the prize gets ruined."""
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
                sig = ("ruin", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["ruined"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"was {mess} – the {item.label} would be lost."
                )
    return out


def _r_grief(world: World) -> list[str]:
    """If a prize is ruined and belongs to a friend, the friend's grief grows."""
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["ruined"] < THRESHOLD or not item.owner:
            continue
        sig = ("grief", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner = world.get(item.owner)
        owner.memes["grief"] += 1
        out.append(f"Grief filled {owner.id}.")
    return out


def _r_wyrm_rage(world: World) -> list[str]:
    """If the wyrm is enraged, she attacks the friend."""
    for actor in world.characters():
        if actor.memes["enrage"] < THRESHOLD:
            continue
        sig = ("strike", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["fear"] += 1
        return ["__strike__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("ruin", "physical", _r_ruin),
    Rule("grief", "emotional", _r_grief),
    Rule("wyrm_rage", "social", _r_wyrm_rage),
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
                produced.extend(s for s in sents if s != "__strike__")
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
def predict_ruin(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "ruined": bool(prize and prize.meters["ruined"] >= THRESHOLD),
        "grief": sum(e.memes["grief"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs (mythic lore)
# ---------------------------------------------------------------------------
def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was still, and the hearth flickered."
    if activity.weather == "stormy":
        return f"Storm clouds gathered over {setting.place}, and the wind howled like old sorrows."
    return f"{setting.place.capitalize()} shimmered in a twilight glow."


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"In the age before the Great Forgetting, a {hero.traits[0]} {hero.type} "
        f"named {hero.id} lived among the {friend.traits[0]} {friend.type}s. "
        f"{hero.id} and {friend.id} were the truest of friends."
    )


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"{hero.id} loved {activity.gerund} with {friend_ref(world, hero)}; "
        f"it was a ritual of joy passed down through generations."
    )


def friend_ref(world: World, hero: Entity) -> str:
    # find friend
    for e in world.characters():
        if e.id != hero.id and e.type != "wyrm":
            return e.id
    return "a companion"


def the_last_piccalilli(world: World, friend: Entity, prize: Entity) -> None:
    world.say(
        f"The last jar of Piccalilli, {prize.phrase}, was kept in a hollow oak. "
        f"{friend.id} had watched over it for moons."
    )


def warns(world: World, friend: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"\"{friend.id},\" said the {friend.traits[0]} {friend.type}, "
        f"\"if we do not {activity.verb}, the wyrm will devour the Piccalilli "
        f"and its taste will vanish from the earth forever.\""
    )


def arrive(world: World, hero: Entity, friend: Entity, wyrm: Entity) -> None:
    world.say(
        f"One stormy dusk, they reached the wyrm's lair. "
        f"The {wyrm.traits[0]} {wyrm.type} lay coiled around the Piccalilli jar, "
        f"its breath foul as burnt honey."
    )


def defiance(world: World, hero: Entity, wyrm: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} stepped forward, heart pounding. \"We will {activity.verb} "
        f"or perish!\" The {wyrm.type} hissed and lunged."
    )


def friend_stands(world: World, friend: Entity, wyrm: Entity) -> None:
    friend.memes["bravery"] += 1
    world.say(
        f"But {friend.id} threw a handful of enchanted herbs into the wyrm's face, "
        f"shouting a challenge."
    )


def enrage(world: World, wyrm: Entity) -> None:
    wyrm.memes["enrage"] += 1
    propagate(world, narrate=False)
    world.say(
        f"The wyrm roared, and its tail struck the ground, shaking the cave."
    )


def bargain_or_gear(world: World, hero: Entity, friend: Entity, wyrm: Entity,
                    activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=friend.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_ruin(world, hero, activity, prize.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{friend.id} recalled the old pact: \"We can {gear_def.prep}, and "
        f"the Piccalilli will be safe.\""
    )
    return gear_def


def friendship_triumph(world: World, hero: Entity, friend: Entity, wyrm: Entity,
                       prize: Entity, gear_def: Gear) -> None:
    hero.memes["love"] += 1
    friend.memes["love"] += 1
    hero.memes["fear"] = 0
    friend.memes["fear"] = 0
    wyrm.memes["enrage"] = 0
    world.say(
        f"Using {gear_def.label}, {hero.id} and {friend.id} worked together. "
        f"The wyrm, seeing their unity, slunk away. The Piccalilli was saved; "
        f"no extinction would claim it. And their friendship grew stronger "
        f"than any myth."
    )


# ---------------------------------------------------------------------------
# The Tell (mythic three‑act structure)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lyra", hero_type: str = "heroine",
         hero_traits: Optional[list[str]] = None,
         friend_name: str = "Kael", friend_type: str = "fox",
         friend_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    world.weather = "stormy" if activity.weather else ""

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["brave"] + (hero_traits or ["kind", "curious"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["wise"] + (friend_traits or ["loyal", "cunning"]),
    ))
    wyrm = world.add(Entity(
        id="Wyrm", kind="character", type="wyrm",
        traits=["vicious", "ancient"],
        label="vicious wyrm",
        phrase="the vicious wyrm with scales of obsidian",
    ))
    prize = world.add(Entity(
        id="jar", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=friend.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    introduce(world, hero, friend)
    loves_activity(world, hero, activity)
    the_last_piccalilli(world, friend, prize)
    warns(world, friend, hero, prize, activity)

    world.para()
    # Act 2
    arrive(world, hero, friend, wyrm)
    defiance(world, hero, wyrm, activity)
    friend_stands(world, friend, wyrm)
    enrage(world, wyrm)

    world.para()
    # Act 3
    gear_def = bargain_or_gear(world, hero, friend, wyrm, activity, prize)
    if gear_def:
        friendship_triumph(world, hero, friend, wyrm, prize, gear_def)
    else:
        # safety fallback: direct friendship wins
        world.say(
            f"But {friend.id} whispered the old song, and the wyrm remembered "
            f"its own lost friend. It retreated. The Piccalilli endured."
        )
        hero.memes["love"] += 1
        friend.memes["love"] += 1
        prize.meters["ruined"] = 0  # not ruined

    world.facts.update(hero=hero, friend=friend, wyrm=wyrm, prize=prize,
                       prize_cfg=prize_cfg, activity=activity, setting=setting,
                       gear=gear_def)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "sunken_valley": Setting(place="the Sunken Valley", indoor=False, affords={"gather", "defend"}),
    "whispering_wood": Setting(place="the Whispering Wood", indoor=False, affords={"gather"}),
    "crystal_cavern": Setting(place="the Crystal Cavern", indoor=True, affords={"defend"}),
}

ACTIVITIES = {
    "gather": Activity(
        id="gather",
        verb="gather the Last Piccalilli",
        gerund="gathering the Last Piccalilli",
        rush="reach for the jar",
        mess="scorched",
        soil="scorched and lost",
        zone={"hands"},
        weather="stormy",
        keyword="piccalilli",
        tags={"piccalilli", "harvest"},
    ),
    "defend": Activity(
        id="defend",
        verb="defend the Piccalilli from the wyrm",
        gerund="defending the Piccalilli from the wyrm",
        rush="stand between wyrm and jar",
        mess="shattered",
        soil="shattered and spilled",
        zone={"torso"},
        weather="stormy",
        keyword="vicious",
        tags={"vicious", "wyrm"},
    ),
}

PRIZES = {
    "piccalilli_jar": Prize(
        label="Piccalilli jar",
        phrase="a small clay jar of golden Piccalilli, rich with ancient spices",
        type="jar",
        region="hands",
        plural=False,
        genders={"hero", "heroine"},
    ),
}

GEAR = [
    Gear(
        id="ash_cloak",
        label="Ash Cloak",
        covers={"hands", "torso"},
        guards={"scorched", "shattered"},
        prep="wear the Ash Cloak woven from phoenix feathers",
        tail="wrapped themselves in the Ash Cloak",
    ),
    Gear(
        id="song_shield",
        label="Song Shield",
        covers={"arms", "torso"},
        guards={"frozen", "shattered"},
        prep="sing the Song of Shielding",
        tail="sang the Song of Shielding together",
        plural=True,
    ),
]

HERO_NAMES = ["Lyra", "Orin", "Sera", "Finn", "Mira"]
FRIEND_NAMES = ["Kael", "Nyx", "Thorn", "Pip", "Ember"]
TRAITS = ["kind", "curious", "fearless", "patient", "clever"]
WYRM_TRAITS = ["vicious", "ancient", "jealous", "hungry"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    friend_name: str
    friend_type: str
    trait: str
    wyrm_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "piccalilli": [("What is Piccalilli?",
                    "Piccalilli is a spicy, tangy relish made from chopped vegetables, "
                    "pickled in vinegar and turmeric. In this myth it is a rare treasure.")],
    "vicious": [("What does 'vicious' mean?",
                 "Vicious means fierce, cruel, or dangerous. The wyrm was vicious "
                 "because it wanted to destroy the Piccalilli and harm the friends.")],
    "extinction": [("What is extinction?",
                    "Extinction means something disappears forever. If the wyrm "
                    "had eaten the last Piccalilli, the recipe would have become extinct.")],
    "friendship": [("Why is friendship important?",
                    "Friendship helps people face dangers together. In the story, "
                    "friendship defeated the wyrm and saved the Piccalilli.")],
}
KNOWLEDGE_ORDER = ["piccalilli", "vicious", "extinction", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act = f["hero"], f["friend"], f["activity"]
    return [
        f'Write a short myth for children about friendship saving the last {act.keyword} '
        f'from a {f["wyrm"].traits[0]} wyrm.',
        f'Tell a story set in {world.setting.place} where {hero.id} and {friend.id} '
        f'protect the Piccalilli together.',
        f'Include the words "{act.keyword}", "vicious", and "extinction" in the tale.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, wyrm, prize = f["hero"], f["friend"], f["wyrm"], f["prize"]
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    fsub, fpos = friend.pronoun("subject"), friend.pronoun("possessive")
    place = world.setting.place
    qa: list[QAItem] = [
        QAItem(
            question=f"Who were the two friends in the myth of the Piccalilli in {place}?",
            answer=f"The friends were a {hero.traits[0]} {hero.type} named {hero.id} "
                   f"and a {friend.traits[0]} {friend.type} named {friend.id}."
        ),
        QAItem(
            question=f"What did the vicious wyrm threaten to do in {place}?",
            answer=f"The {wyrm.traits[0]} wyrm threatened to destroy the last jar of "
                   f"Piccalilli, which would have meant its extinction."
        ),
        QAItem(
            question=f"How did the friends save the Piccalilli from extinction?",
            answer=f"They used a {f.get('gear', 'plan')} to protect the jar, "
                   f"and together they faced the wyrm. The wyrm, seeing their "
                   f"friendship, retreated."
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question=f"What was the {f['gear'].label} and how did it help?",
            answer=f"The {f['gear'].label} was a magical item that guarded "
                   f"the Piccalilli from the wyrm's fiery breath."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add("friendship")
    tags.add("extinction")
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
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- mythic world state ---"]
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
    lines.append(f"  rules fired: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated set
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="sunken_valley",
        activity="gather",
        prize="piccalilli_jar",
        name="Lyra",
        gender="heroine",
        friend_name="Kael",
        friend_type="fox",
        trait="brave",
        wyrm_trait="vicious",
    ),
    StoryParams(
        place="crystal_cavern",
        activity="defend",
        prize="piccalilli_jar",
        name="Orin",
        gender="hero",
        friend_name="Nyx",
        friend_type="bird",
        trait="fearless",
        wyrm_trait="jealous",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} affects {sorted(activity.zone)}, but " \
           f"the {prize.label} is worn on {prize.region}. No honest conflict.)"


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
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic world: friends, a vicious wyrm, and the last Piccalilli.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["hero", "heroine"])
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-type", choices=["fox", "bird"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["hero", "heroine"])
    name = args.name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    friend_type = args.friend_type or rng.choice(["fox", "bird"])
    trait = rng.choice(TRAITS)
    wyrm_trait = rng.choice(WYRM_TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, friend_name=friend_name,
        friend_type=friend_type, trait=trait, wyrm_trait=wyrm_trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
        params.name, params.gender, [params.trait],
        params.friend_name, params.friend_type, ["loyal"],
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
        combos, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(combos)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in combos:
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
            header = f"### {p.name} & {p.friend_name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
