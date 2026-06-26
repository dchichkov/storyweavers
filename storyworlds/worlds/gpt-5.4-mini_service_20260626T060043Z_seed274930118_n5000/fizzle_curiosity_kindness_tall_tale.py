#!/usr/bin/env python3
"""
storyworlds/worlds/fizzle_curiosity_kindness_tall_tale.py
==========================================================

A standalone storyworld for a tall-tale style tale of curiosity, kindness, and
one spectacular fizzle.

Premise:
- A curious child hears a strange fizzle and wants to investigate.
- The fizzing thing could splash the child's nice clothes.
- A kind helper suggests a safer, clever way to look, so nobody gets doused.

The world is small and classical:
- one child
- one grown-up helper
- one fizzy object
- one treasured item at risk
- one compatible protective fix

The prose aims for a tall-tale feel: larger-than-life language, vivid sensory
details, and a bright ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["wet", "dirty", "sparkle", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "kindness", "joy", "worry", "conflict", "trust", "calm"]:
            self.memes.setdefault(k, 0.0)

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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: callable


def _r_fizzle_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["sparkle"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got splashed by the fizzle.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] += 1
        out.append(f"That would mean extra work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["worry"] < THRESHOLD or actor.memes["curiosity"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("fizzle_soak", "physical", _r_fizzle_soak),
    Rule("workload", "physical", _r_workload),
    Rule("conflict", "social", _r_conflict),
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


def activity_delight(activity: Activity) -> str:
    return {
        "fizzle": "the fizzle sounded like a tiny thunderstorm trapped in a glass jar",
        "bubbles": "the bubbles danced up like silver minnows",
        "kettle": "the little song of the steam could wake a sleeping rooster",
    }.get(activity.id, "it made the whole day feel grand")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the air smelled warm and sweet."
    if activity.weather == "sunny":
        return f"The sun stood high over {setting.place}, shining like a gold coin."
    return f"{setting.place.capitalize()} looked ready for a tale to tumble through it."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["sparkle"] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} with eyes sharp as buttons and a heart full of wondering.")


def loves_curiosity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to ask about every whiff, whistle, and {activity.keyword or activity.id}; "
        f"{activity_delight(activity)}."
    )


def kindness_trait(world: World, helper: Entity) -> None:
    helper.memes["kindness"] += 1
    world.say(f"{helper.id} was known for {helper.pronoun('possessive')} kindness, the sort that could calm a stampeding goose.")


def buys(world: World, helper: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"That morning, {hero.id}'s {helper.label} brought home {hero.pronoun('object')} {prize.phrase}.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["trust"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} proudly, "
        f"as if {prize.it()} were fit for a parade behind the moon."
    )


def arrive(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    day = {"sunny": "One sunny day, ", "rainy": "One rainy day, "}.get(world.weather, "One day, ")
    go = "were in" if world.setting.indoor else "went to"
    world.say(f"{day}{hero.id} and {hero.pronoun('possessive')} {helper.label} {go} {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, helper: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, because curiosity was tugging at {hero.pronoun('possessive')} sleeve."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(
        f'"{You\'ll get your {prize.label} {activity.soil}," {helper.label} said, '
        f'"and I would rather not spend the whole afternoon scrubbing it clean."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} heard that, but curiosity kept tapping louder than a woodpecker on a church bell.")
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush},")
    

def grab_hand(world: World, helper: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {helper.label} held {hero.pronoun('possessive')} hand and said, "
        f"\"We can look at the fizzle without letting it splash the whole town.\""
    )


def compromise(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=helper.id,
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
        f'{helper.id} smiled like sunrise on a fence rail and said, '
        f'"How about we {gear_def.prep} and then {activity.verb} together?"'
    )
    return gear_def


def accept(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["trust"] += 1
    hero.memes["worry"] = 0.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id}'s face lit up bright as a lantern in a barn dance. "
        f"{hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {helper.label} and said, "
        f"\"Yes, please!\""
    )
    world.say(
        f"Together they {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{prize.label} stayed clean, and the fizzle sounded merry instead of messy."
    )


def tell(
    setting: Setting,
    activity: Activity,
    prize_cfg: Prize,
    hero_name: str = "Nell",
    hero_type: str = "girl",
    hero_traits: Optional[list[str]] = None,
    helper_type: str = "grandmother",
) -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "bright-eyed"]),
    ))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="grandma"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_curiosity(world, hero, activity)
    kindness_trait(world, helper)
    buys(world, helper, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, helper, activity)
    wants(world, hero, helper, activity)
    warn(world, helper, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, helper, hero, activity)

    world.para()
    gear_def = compromise(world, helper, hero, activity, prize)
    if gear_def:
        accept(world, helper, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        helper=helper,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["worry"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"fizzle"}),
    "porch": Setting(place="the porch", indoor=False, affords={"fizzle"}),
    "fair": Setting(place="the county fair", indoor=False, affords={"fizzle"}),
    "garden": Setting(place="the garden", indoor=False, affords={"fizzle"}),
}

ACTIVITIES = {
    "fizzle": Activity(
        id="fizzle",
        verb="peek into the fizzling jar",
        gerund="peeking into the fizzling jar",
        rush="dash toward the fizzling jar",
        mess="wet",
        soil="wet and sticky",
        zone={"torso", "legs"},
        weather="sunny",
        keyword="fizzle",
        tags={"fizzle", "curiosity"},
    ),
    "sparkle": Activity(
        id="sparkle",
        verb="watch the sparkling spoon",
        gerund="watching the sparkling spoon",
        rush="run up to the sparkling spoon",
        mess="wet",
        soil="damp",
        zone={"torso"},
        weather="sunny",
        keyword="sparkle",
        tags={"fizzle", "curiosity"},
    ),
}

PRIZES = {
    "dress": Prize(label="dress", phrase="a fine blue dress", type="dress", region="legs", genders={"girl"}),
    "shirt": Prize(label="shirt", phrase="a crisp white shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a bright yellow apron", type="apron", region="torso"),
    "boots": Prize(label="boots", phrase="sturdy little boots", type="boots", region="feet", plural=True),
}

GEAR = [
    Gear(
        id="apron",
        label="an oilcloth apron",
        covers={"torso", "legs"},
        guards={"wet"},
        prep="put on the oilcloth apron first",
        tail="went back to the table with the oilcloth apron on",
    ),
    Gear(
        id="boots",
        label="rain boots",
        covers={"feet"},
        guards={"wet"},
        prep="pull on the rain boots first",
        tail="clomped back to the jar in rain boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Nell", "Mina", "Pearl", "Ruby", "Lottie", "June", "Mabel", "Ada"]
BOY_NAMES = ["Otis", "Bram", "Clive", "Wes", "Hugo", "Judd", "Miles"]
TRAITS = ["curious", "bright-eyed", "spry", "spirited", "bold", "little"]


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
    helper: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "fizzle": [("What does fizzle mean?", "To fizzle is to make a soft sizzling or popping sound, like bubbles waking up in a jar.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn about something new.")],
    "kindness": [("What is kindness?", "Kindness means being gentle, helpful, and caring toward someone else.")],
    "wet": [("What does it mean when something is wet?", "Wet means covered with water or a liquid, so it feels damp.")],
}
KNOWLEDGE_ORDER = ["fizzle", "curiosity", "kindness", "wet"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, helper, act, prize = f["hero"], f["helper"], f["activity"], f["prize_cfg"]
    return [
        f'Write a tall-tale style story for a small child about "{act.keyword}" that includes curiosity and kindness.',
        f"Tell a story where {hero.id} wants to {act.verb}, but {helper.label} helps {hero.pronoun('object')} stay safe around {prize.phrase}.",
        f"Make a playful story with a fizzle, a warning, and a kind compromise that ends with {hero.id} smiling.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, act = f["hero"], f["helper"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} goes to {world.setting.place} to {act.verb}?",
            answer=f"It is about {hero.id}, a little {hero.type}, and {helper.label}, who is kind and careful.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} because curiosity was buzzing in {hero.pronoun('possessive')} head.",
        ),
        QAItem(
            question=f"What treasured thing did {helper.label} buy for {hero.id}?",
            answer=f"{helper.label} bought {hero.pronoun('object')} {prize.phrase}, and {hero.id} loved it right away.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help {hero.id} around the fizzling jar?",
            answer=f"By putting on {gear.label}, {hero.id} could {act.verb} without getting {prize.label} wet and sticky.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and brave, because kindness helped curiosity turn into a safe adventure.",
        ))
    if f.get("conflict"):
        soil = f.get("predicted_soil", "wet and sticky")
        qa.append(QAItem(
            question=f"Why did {helper.label} worry about {prize.label}?",
            answer=f"{helper.label} worried because if {hero.id} got too close to the fizzling jar, {prize.label} would get {soil}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["activity"].tags)
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach {noun}, so there is no honest worry to solve.)"
    return f"(No story: no gear in this world reasonably protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} is not a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
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
    ap = argparse.ArgumentParser(description="Tall-tale story world of curiosity, kindness, and one fizzle.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["grandmother", "grandfather"])
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
    helper = args.helper or rng.choice(["grandmother", "grandfather"])
    trait = rng.choice([t for t in TRAITS if t != "little"])
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, helper=helper, trait=trait)


CURATED = [
    StoryParams(place="kitchen", activity="fizzle", prize="shirt", name="Nell", gender="girl", helper="grandmother", trait="curious"),
    StoryParams(place="porch", activity="fizzle", prize="dress", name="Mabel", gender="girl", helper="grandmother", trait="bright-eyed"),
    StoryParams(place="garden", activity="sparkle", prize="apron", name="Otis", gender="boy", helper="grandfather", trait="spirited"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        params.gender,
        [params.trait, "curious"],
        params.helper,
    )
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
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
