#!/usr/bin/env python3
"""
storyworlds/worlds/shush_orthodontic_standard_ize_repetition_fable.py
======================================================================

A small fable-style story world about repetition, a gentle shush, and an
orthodontic fix that helps a child choose a better way.

Premise used to build the world model:
---
A young hare named Tansy wears orthodontic braces and loves to repeat the same
loud snack-chant at every meal. On a windy afternoon in the orchard, Tansy
crunches too many hard hazelnuts, and the braces start to ache. The old owl
shushes Tansy, warns that repeating the hard crunching will bend the braces
and make the mouth sore, then offers orthodontic wax and a calmer, standard-ized
snack tray with soft pear slices. Tansy learns that a repeated habit is not
always a wise one, and the orchard settles into a kinder rhythm.
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
REGIONS = {"mouth", "head", "torso", "paws"}
MESS_KINDS = {"strained", "smeared", "scuffed"}


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
        female = {"girl", "mother", "mom", "woman", "owl"}
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
        return self.label or self.type


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


def _r_strain(world: World) -> list[str]:
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
                sig = ("strain", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got strained.")
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
        carer.meters["worry"] += 1
        out.append(f"That would be hard on {carer.label_word}.")
    return out


def _r_shush(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["shushed_by"] < THRESHOLD or actor.memes["repetition"] < THRESHOLD:
            continue
        sig = ("calm", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] += 1
        actor.memes["noise"] = 0.0
        return ["__calm__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule("strain", "physical", _r_strain),
    Rule("worry", "physical", _r_worry),
    Rule("shush", "social", _r_shush),
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
                produced.extend(s for s in sents if s != "__calm__")
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
    return {"soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
            "worry": sum(e.meters["worry"] for e in sim.characters())}


def activity_delight(activity: Activity) -> str:
    return {
        "crunching": "the crisp crack of nuts felt grand at first",
        "chanting": "the repeated rhythm made the orchard feel loud and proud",
        "marching": "the steady steps made the path feel like a parade",
        "sorting": "the neat rows made everything look calm and fair",
    }.get(activity.id, "it made the day feel busy")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place} was small and quiet, with sunlight on the floor."
    if activity.weather == "windy":
        return f"The wind moved through {setting.place} and shook the leaves like little bells."
    return f"{setting.place.capitalize()} waited in a hush, ready for the lesson of the day."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    actor.memes["repetition"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    world.say(f"{hero.id} was a little {trait} {hero.type} who remembered every sound it liked to repeat.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One week, {hero.id}'s {parent.label_word} brought home {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = {"windy": "One windy afternoon, ", "sunny": "One sunny afternoon, "}.get(world.weather, "One afternoon, ")
    go = "went to" if not world.setting.indoor else "were in"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} again and again, as if one round were never enough.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_worry"] = pred["worry"]
    world.say(f'"Shush, little one," {parent.label_word} said. "If you keep {activity.gerund}, your {prize.label} will get {activity.soil}."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But the old habit was strong, and {hero.id} tried to {activity.rush} anyway.")


def shush(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["shushed_by"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {hero.pronoun('possessive')} {parent.label_word} lifted a finger and said, \"Shush.\"")


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
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} laid out {gear_def.label} and a calmer plan.")
    world.say(f'"How about we {gear_def.prep} and choose the safer way?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s ears perked up, and {hero.pronoun()} nodded to {hero.pronoun('possessive')} {parent.label_word}.")
    world.say(f'"All right," {hero.pronoun("subject")} said. "I can do it the better way."')
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {prize_was_clean(hero, prize)}, and the orchard sounded kind again.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Tansy",
         hero_type: str = "hare", hero_traits: Optional[list[str]] = None,
         parent_type: str = "owl") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["eager", "repetitive"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the owl"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    shush(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["shushed_by"] >= THRESHOLD,
                       resolved=gear_def is not None)
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", indoor=False, affords={"crunching", "chanting", "sorting"}),
    "schoolyard": Setting(place="the schoolyard", indoor=False, affords={"marching", "chanting", "sorting"}),
    "workroom": Setting(place="the workroom", indoor=True, affords={"sorting"}),
}

ACTIVITIES = {
    "crunching": Activity(
        id="crunching",
        verb="crunch the hard hazelnuts",
        gerund="crunching hard hazelnuts",
        rush="dash to another nut pile",
        mess="strained",
        soil="strained and sore",
        zone={"mouth"},
        weather="windy",
        keyword="repetition",
        tags={"repetition", "teeth", "food"},
    ),
    "chanting": Activity(
        id="chanting",
        verb="chant the same little rhyme",
        gerund="chanting the same rhyme",
        rush="call the rhyme louder",
        mess="smeared",
        soil="noisy and smeared with spit",
        zone={"mouth", "head"},
        weather="windy",
        keyword="shush",
        tags={"repetition", "sound", "shush"},
    ),
    "marching": Activity(
        id="marching",
        verb="march in a neat line",
        gerund="marching in a neat line",
        rush="skip out of line",
        mess="scuffed",
        soil="scuffed and dusty",
        zone={"paws"},
        weather="sunny",
        keyword="standard-ize",
        tags={"order", "standard-ize"},
    ),
    "sorting": Activity(
        id="sorting",
        verb="sort pebbles into equal rows",
        gerund="sorting pebbles into equal rows",
        rush="scatter the pebbles",
        mess="scuffed",
        soil="scuffed and out of order",
        zone={"paws", "torso"},
        weather="",
        keyword="standard-ize",
        tags={"order", "standard-ize"},
    ),
}

PRIZES = {
    "braces": Prize(label="braces", phrase="shiny orthodontic braces", type="braces", region="mouth"),
    "retainer": Prize(label="retainer", phrase="an orthodontic retainer", type="retainer", region="mouth"),
    "apron": Prize(label="apron", phrase="a neat little apron", type="apron", region="torso"),
}

GEAR = [
    Gear(id="wax", label="orthodontic wax", covers={"mouth"}, guards={"strained", "smeared"}, prep="put on orthodontic wax first", tail="walked back with the wax in place"),
    Gear(id="quiet", label="a quiet counting card", covers={"head"}, guards={"smeared"}, prep="hold a quiet counting card instead of chanting", tail="counted in a quieter way"),
    Gear(id="straight_row", label="a row of little chalk marks", covers={"paws", "torso"}, guards={"scuffed"}, prep="draw a row of little chalk marks first", tail="followed the chalk marks"),
]

GIRL_NAMES = ["Tansy", "Mira", "Poppy", "Lina", "Nell"]
BOY_NAMES = ["Rowan", "Otto", "Finn", "Milo", "Bram"]
TRAITS = ["curious", "eager", "thoughtful", "stubborn", "cheerful"]


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


KNOWLEDGE = {
    "repetition": [("What is repetition?", "Repetition is when something happens or is said more than once."),],
    "shush": [("What does it mean to shush?", "To shush means to ask for quiet in a gentle way."),],
    "standard-ize": [("What does it mean to standardize something?", "To standardize means to make things follow one simple, regular pattern so they match."),],
    "orthodontic": [("What is orthodontic treatment for?", "Orthodontic treatment helps teeth grow straighter and fit together better."),],
    "teeth": [("Why do braces need care?", "Braces need care because they help guide teeth, and hard bumps can make them sore."),],
    "food": [("Why are soft foods easier to chew?", "Soft foods are easier to chew because they do not press so hard on your teeth."),],
    "order": [("Why can neat rows be helpful?", "Neat rows can help you see what belongs where and make counting easier."),],
}
KNOWLEDGE_ORDER = ["repetition", "shush", "standard-ize", "orthodontic", "teeth", "food", "order"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short fable for a child about "{act.keyword}" and a gentle "{parent.label_word}" who says "shush".',
        f"Tell a small moral story about {hero.id}, who keeps {act.gerund}, but learns a better way when {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f'Write a story that uses the words "{act.keyword}", "shush", and "standard-ize" and ends with a kinder habit.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive")
    day = {"windy": "windy afternoon", "sunny": "sunny afternoon"}.get(world.weather, "day")
    qa = [
        QAItem(
            question=f"Who is the fable about when {hero.id} goes to {world.setting.place} to {act.verb} with {pos} {prize.label}?",
            answer=f"It is about a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type} named {hero.id}, plus {pos} {pw}. They visit {world.setting.place} on a {day}, and {hero.id} is wearing {pos} {prize.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} keep wanting to do at {world.setting.place} before {pw} said shush?",
            answer=f"{hero.id} kept wanting to {act.verb}. The repeating habit sounded strong, but it could make the braces hurt.",
        ),
        QAItem(
            question=f"Why did {pw} warn {hero.id} about {pos} {prize.label}?",
            answer=f"{pw.capitalize()} warned {hero.id} because if {hero.id} kept {act.gerund}, {pos} {prize.label} would get {act.soil}. That would leave the mouth sore and make more work for {pw}.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        gear_name = gear.label
        qa.append(QAItem(
            question=f"How did {gear_name} help {hero.id} {act.verb} without hurting {pos} {prize.label}?",
            answer=f"They used {gear_name} first, so {hero.id} could still {act.verb} without making {pos} {prize.label} sore. The safer plan matched the problem instead of fighting it.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel after the owl helped {sub} choose a better plan?",
            answer=f"{hero.id} felt happy and calmer. By the end, {sub} was {act.gerund}, and {pw} was smiling because the repeat habit had turned into a wiser one.",
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
    StoryParams(place="orchard", activity="crunching", prize="braces", name="Tansy", gender="girl", parent="owl", trait="curious"),
    StoryParams(place="orchard", activity="chanting", prize="retainer", name="Rowan", gender="boy", parent="owl", trait="eager"),
    StoryParams(place="schoolyard", activity="marching", prize="apron", name="Mira", gender="girl", parent="owl", trait="thoughtful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.region}, so {noun} would not get {activity.mess}. Try a prize worn on the {prize.region}.)"
    return f"(No story: nothing in the gear catalog protects {noun} from {activity.gerund}. The fable needs a real fix, not a pretend one.)"


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
    ap = argparse.ArgumentParser(description="A fable about repetition, shush, and an orthodontic fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["owl"])
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
    parent = args.parent or "owl"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, [params.trait, "repetitive"], params.parent)
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
            print(f"  {place:10} {act:10} {prize:10}  [{', '.join(genders)}]")
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
