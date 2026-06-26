#!/usr/bin/env python3
"""
storyworlds/worlds/plead_latte_moral_value_magic_space_adventure.py
====================================================================

A small space-adventure story world about a child, a pleading wish, a magic
latte, and the moral choice to share.

Premise:
- A young space adventurer wants a glowing latte on a flight through the stars.
- The latte is lovely and magical, but it can spill in zero gravity.
- A captain warns that the last latte should go to the tired helper who fixed
  the ship's beacon.
- The child pleads, learns patience and fairness, and finds a kind compromise.

The story engine models:
- physical meters such as spill and glow
- emotional memes such as plea, worry, fairness, and joy
- a compatible fix: a magnetic cup that prevents a spill
- a moral turn: the hero chooses to share the latte

This world keeps the tone child-friendly and adventurous, with star maps,
moon docks, and a gentle moral center.
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
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pilot"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "captain": "captain", "pilot": "pilot"}.get(self.type, self.type)


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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

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


MESS_KINDS = {"spilled", "foamy", "sticky"}


def _r_spill(world: World) -> list[str]:
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
                sig = ("spill", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That would mean more worry for {carer.label}.")
    return out


def _r_moral(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["plea"] < THRESHOLD or actor.memes["fairness"] < THRESHOLD:
            continue
        sig = ("moral", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["moral_value"] += 1
        return ["__moral__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("spill", "physical", _r_spill),
    Rule("worry", "physical", _r_worry),
    Rule("moral", "social", _r_moral),
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
                produced.extend(s for s in sents if s != "__moral__")
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
        "worry": sum(e.memes["worry"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "stargaze": "the stars blinked like tiny lanterns",
        "drift": "the ship drifted softly like a sleepy cloud",
        "dock": "the moon dock gleamed with silver rails",
        "repair": "the beacon clicked and hummed like a friendly robot",
        "sip": "the warm sip felt cozy in the cold ship",
    }.get(activity.id, "the whole journey felt bright and brave")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the consoles glowed and the windows showed the stars."
    if activity.weather == "still":
        return f"{setting.place.capitalize()} floated quietly in the dark, with far-off stars all around."
    return f"{setting.place.capitalize()} looked like a doorway to a thousand stars."


def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed safe"


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
    world.say(f"{hero.id} was a {desc} who loved the space lanes and shiny glass domes.")


def loves_goal(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["hope"] += 1
    where = "through space" if not world.setting.indoor else "inside the station"
    world.say(
        f"{hero.pronoun().capitalize()} loved drifting {where} and {activity.gerund}; "
        f"{activity_delight(activity)}."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That morning, {hero.id}'s {parent.label_word} brought {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and held {prize.it()} close "
        f"like a tiny treasure from the stars."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"still": "One quiet day, "}.get(world.weather, "One day, ")
    go = "floated to" if not world.setting.indoor else "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["plea"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} "
        f"{parent.label_word} raised a careful hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    clause = f"You'll get your {prize.label} {activity.soil}"
    if pred["worry"] >= THRESHOLD:
        clause += ", and then the crew will have more work"
    world.say(f"\"{clause},\" {hero.pronoun('possessive')} {parent.label_word} said. \"Let's choose wisely.\"")
    return True


def pleads(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["plea"] += 1
    world.say(
        f"{hero.id} heard the warning and still felt the wish pulling hard. "
        f'{hero.pronoun().capitalize()} pleaded, "Please, I really want to {activity.verb}!"'
    )


def share_warning(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["fairness"] += 1
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} pointed to the tired helper, "
        f"who had fixed the beacon for everyone. \"The last {prize.label} should be shared fairly,\" "
        f"{parent.pronoun()} said."
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, '
        f'"How about we {gear_def.prep} so the {prize.label} stays safe?"'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["fairness"] += 1
    hero.memes["plea"] = 0.0
    world.say(
        f"{hero.id}'s eyes lit up and {hero.pronoun()} hugged {hero.pronoun('possessive')} "
        f"{parent.label_word}. \"Okay! Let's do the kind way,\" {hero.pronoun()} said."
    )
    world.say(
        f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize_was_safe(hero, prize)}, and the tired helper got a warm share too."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Nova", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    helper = world.add(Entity(id="Helper", kind="character", type="pilot", label="the helper"))

    introduce(world, hero)
    loves_goal(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)
    helper.memes["tired"] += 1
    world.say(f"The helper was tired after fixing the beacon, but still smiled at the little traveler.")

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    pleads(world, hero, activity)
    share_warning(world, parent, hero, prize)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["plea"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "station": Setting(place="the star station", indoor=True, affords={"sip", "repair", "dock"}),
    "moonport": Setting(place="the moon port", indoor=False, affords={"dock", "stargaze"}),
    "orbital_garden": Setting(place="the orbital garden", indoor=False, affords={"stargaze", "drift"}),
}


ACTIVITIES = {
    "sip": Activity(
        id="sip",
        verb="sip the latte",
        gerund="sipping a warm latte",
        rush="grab the cup",
        mess="spilled",
        soil="spilled",
        zone={"hands", "torso"},
        weather="still",
        keyword="latte",
        tags={"latte", "magic"},
    ),
    "dock": Activity(
        id="dock",
        verb="dock the tiny ship",
        gerund="docking tiny ships",
        rush="race to the dock",
        mess="spilled",
        soil="sloshed",
        zone={"hands"},
        weather="still",
        keyword="dock",
        tags={"space", "ship"},
    ),
    "repair": Activity(
        id="repair",
        verb="repair the beacon",
        gerund="repairing the beacon",
        rush="dash to the beacon",
        mess="sticky",
        soil="sticky",
        zone={"hands", "torso"},
        weather="still",
        keyword="beacon",
        tags={"magic", "repair"},
    ),
    "stargaze": Activity(
        id="stargaze",
        verb="watch the stars",
        gerund="watching the stars",
        rush="lean out the window",
        mess="foamy",
        soil="foamy",
        zone={"hands"},
        weather="still",
        keyword="stars",
        tags={"space"},
    ),
    "drift": Activity(
        id="drift",
        verb="drift past the moon",
        gerund="drifting past the moon",
        rush="float into the corridor",
        mess="spilled",
        soil="spilled",
        zone={"hands", "torso"},
        weather="still",
        keyword="moon",
        tags={"space"},
    ),
}

GEAR = [
    Gear(
        id="mug",
        label="a magnetic mug",
        covers={"hands"},
        guards={"spilled"},
        prep="put the latte in a magnetic mug first",
        tail="put the latte in the magnetic mug and floated back to the window",
    ),
    Gear(
        id="lid",
        label="a snap-on lid",
        covers={"hands"},
        guards={"spilled", "foamy"},
        prep="snap on a lid before the sip",
        tail="snapped on the lid and came back to the table",
    ),
    Gear(
        id="tray",
        label="a steady tray",
        covers={"hands", "torso"},
        guards={"spilled", "sticky"},
        prep="carry it on a steady tray",
        tail="carried it on the steady tray and walked back beside the stars",
        plural=False,
    ),
]

PRIZES = {
    "latte": Prize(
        label="latte",
        phrase="a glowing magic latte",
        type="latte",
        region="hands",
        plural=False,
    ),
    "cup": Prize(
        label="cup",
        phrase="a small moon cup of latte",
        type="cup",
        region="hands",
        plural=False,
    ),
}

GIRL_NAMES = ["Nova", "Luna", "Mira", "Zia", "Iris", "Rae", "Kira"]
BOY_NAMES = ["Orion", "Pax", "Jett", "Finn", "Kai", "Timo"]
TRAITS = ["brave", "curious", "kind", "gentle", "lively", "patient"]


def valid_combos() -> list[tuple[str, str]]:
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


KNOWLEDGE = {
    "latte": [("What is a latte?", "A latte is a warm coffee drink made with milk, often with soft foam on top.")],
    "magic": [("What is magic in a story?", "Magic in a story is a special kind of wonder that can make unusual things happen.")],
    "space": [("What is space?", "Space is the huge area beyond Earth where the stars, planets, and moons are.")],
    "ship": [("What is a ship in space?", "A space ship is a craft that carries people through the stars.")],
    "beacon": [("What is a beacon?", "A beacon is a bright light or signal that helps people find their way.")],
}

KNOWLEDGE_ORDER = ["latte", "magic", "space", "ship", "beacon"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or prize.label
    return [
        f'Write a short space adventure for a 3-to-5-year-old that includes the word "{kw}" and a gentle moral choice.',
        f"Tell a story where a {hero.type} named {hero.id} wants to {act.verb}, pleads for a magic {prize.label}, and learns to share.",
        f"Write a child-friendly story on a star station where {hero.id} and {hero.pronoun('possessive')} {parent.label_word} choose the safe and kind way.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to {place} to {act.verb} with {pos} {prize.label}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} and {pos} {pw}. They visit {place} for a starry adventure.",
        ),
        QAItem(
            question=f"What did {trait} {hero.id} want before {pw} worried about the magic {prize.label}?",
            answer=f"{trait.capitalize()} {hero.id} wanted to {act.verb}. The wish was exciting, but the {prize.label} could spill without help.",
        ),
        QAItem(
            question=f"Why did {hero.id} plead to keep the {prize.label} during the trip at {place}?",
            answer=(
                f"{pos.capitalize()} {hero.id} pleaded because {hero.id} really wanted the glowing {prize.label}. "
                f"But the captain worried it would spill, and the helper needed fairness after fixing the beacon."
            ),
        ),
    ]
    if f.get("conflict"):
        soil = f.get("predicted_soil", "messy")
        worry = f.get("predicted_worry", 0)
        why = f"{pos.capitalize()} {pw} was careful because if {hero.id} tried to {act.verb}, {pos} {prize.label} would get {soil}"
        if worry >= THRESHOLD:
            why += ", and then the crew would have more work."
        why += f" So {pw} reminded {obj} to choose the kind way, not just the quick way."
        qa.append(QAItem(
            question=f"Why did {hero.id}'s {pw} say no at first?",
            answer=why,
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} with the {prize.label}?",
            answer=f"They used {gear.label} so the {prize.label} stayed safe while {hero.id} went on with the adventure.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and proud because {sub} chose a kind answer and shared the {prize.label} with the tired helper.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add("magic")
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
    StoryParams(place="station", activity="sip", prize="latte", name="Nova", gender="girl", parent="captain", trait="brave"),
    StoryParams(place="station", activity="repair", prize="latte", name="Orion", gender="boy", parent="captain", trait="kind"),
    StoryParams(place="moonport", activity="dock", prize="cup", name="Mira", gender="girl", parent="captain", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach where {noun} {verb}. Try a prize held in the activity zone.)"
    return f"(No story: no gear in this world truly keeps {noun} safe from {activity.gerund}. Choose a different pair.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world about pleading, a latte, and a moral choice.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "stubborn"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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
        print(f"{len(triples)} compatible (place, activity, prize) combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories if (pl, a, pr) == (place, act, prize))
            print(f"  {place:12} {act:8} {prize:8}  [{', '.join(genders)}]")
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
