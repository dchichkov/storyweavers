#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ulterior_advise_going_inner_monologue_space_adventure.py
==============================================================================================================

A standalone story world for a small Space Adventure domain with inner monologue,
gentle advice, and a small hidden ulterior motive.

Seed tale imagined from the prompt:
---
A young spacer is going on a first trip outside the ship. Their mentor advises
them to stay near the handrail and not rush into the dark. The child thinks
quietly to themselves about an ulterior reason for the trip: they want to find a
lost charm floating near the satellite dish. With the right tether and a calm
plan, they go out safely, find the charm, and return feeling braver.

World model:
---
- A hero can go on an EVA in one place.
- Going outside without the right gear risks drifting, dropping a prize, or
  getting scared.
- A mentor may advise a safer path.
- The hero's inner monologue can reveal worry, hope, and an ulterior motive.
- A compatible piece of gear can make the adventure safe and let the hero
  succeed.

Story shape:
---
setup -> advice and inner monologue -> tension about the risky going -> safe
resolution with gear and a found prize
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"risk": 0.0, "drift": 0.0, "shiver": 0.0, "lost": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "hope": 0.0, "worry": 0.0, "resolve": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "astronaut-girl"}
        male = {"boy", "father", "dad", "man", "astronaut-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the space station"
    outer: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    zone: set[str]
    keyword: str
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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for act in world.facts.get("activity", []):
            if actor.memes["resolve"] < THRESHOLD:
                continue
            if actor.meters["risk"] < THRESHOLD:
                continue
            sig = ("risk", actor.id, act.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(f"{actor.id} kept steady in the quiet dark.")
    return out


def _r_drift(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("drift", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["lost"] += 1
            actor.meters["drift"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} started to slip away.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("risk", "physical", _r_risk),
    Rule("drift", "physical", _r_drift),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def goal_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "lost": bool(prize.meters["lost"] >= THRESHOLD),
        "drift": sum(e.meters["drift"] for e in sim.characters()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["risk"] += 1
    actor.memes["hope"] += 1
    propagate(world, narrate=narrate)


def introduction(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little spacer with a bright helmet and a head full of questions."
    )


def loves_space(world: World, hero: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, because the stars made the whole world feel huge."
    )


def buy_prize(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"Before the trip, {hero.pronoun('possessive')} {parent.label} gave {hero.pronoun('object')} {prize.phrase}."
    )


def prize_loved(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and kept {prize.it()} close like a tiny lucky star."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place} to {activity.verb}."
    )
    world.say(
        "Outside the hatch, the dark looked deep and quiet, with silver dust shining like sugar."
    )


def advise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict(world, hero, activity, prize.id)
    if not pred["lost"]:
        return False
    world.facts["predicted_lost"] = True
    world.say(
        f'"Go slowly and stay near the rail," {parent.label} advised. "I do not want your {prize.label} to float off."'
    )
    return True


def inner_monologue(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} nodded, but inside {hero.pronoun('possessive')} helmet {hero.pronoun()} thought, "
        f'"I am going for the mission, but I also have an ulterior reason."'
    )
    world.say(
        f'"If I can reach the dish, maybe I can find the little charm that slipped away when I was last going out," {hero.pronoun()} thought.'
    )


def choose_to_go(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["resolve"] += 1
    world.say(
        f"{hero.id} took a breath and decided to keep going, one careful step at a time."
    )
    world.say(
        f"{hero.pronoun().capitalize()} reached for the hatch and began to {activity.rush}."
    )


def offer_gear(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
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
    if predict(world, hero, activity, prize.id)["lost"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"{parent.label} smiled and handed over {gear_def.label}. "
        f'"That will help you go safely," {parent.label} said.'
    )
    return gear


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} slipped on {gear_def.label}, and the little fear in {hero.pronoun('possessive')} chest got quieter."
    )
    world.say(
        f"They went on with the plan. Soon {hero.id} was {activity.gerund}, and the {prize.label} stayed safe."
    )
    world.say(
        f"At the dish, {hero.id} found the lost charm after all, so the ulterior reason turned into a happy surprise."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", trait: str = "curious") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", trait],
    ))
    parent = world.add(Entity(id="Mentor", kind="character", type=parent_type, label="the mentor"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduction(world, hero)
    loves_space(world, hero, activity)
    buy_prize(world, parent, hero, prize)
    prize_loved(world, hero, prize)
    world.para()
    arrive(world, hero, parent, activity)
    advise(world, parent, hero, activity, prize)
    inner_monologue(world, hero, activity)
    choose_to_go(world, hero, activity)
    world.para()
    gear_def = offer_gear(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "station": Setting(place="the space station", outer=True, affords={"eva", "dockwalk"}),
    "moonbase": Setting(place="the moonbase", outer=True, affords={"eva", "survey"}),
    "shipyard": Setting(place="the shipyard hangar", outer=True, affords={"dockwalk", "repairwalk"}),
}

ACTIVITIES = {
    "eva": Activity(
        id="eva",
        verb="go on a spacewalk",
        gerund="going on a spacewalk",
        rush="float out through the hatch",
        danger="drifting into the dark",
        zone={"torso", "hands"},
        keyword="eva",
        tags={"space", "dark"},
    ),
    "dockwalk": Activity(
        id="dockwalk",
        verb="go along the docking rail",
        gerund="going along the docking rail",
        rush="step out along the rail",
        danger="dropping something into space",
        zone={"hands", "torso"},
        keyword="dock",
        tags={"space", "rail"},
    ),
    "survey": Activity(
        id="survey",
        verb="go survey the crater rim",
        gerund="going to survey the crater rim",
        rush="hurry toward the rim",
        danger="losing track of the path",
        zone={"boots", "hands"},
        keyword="moon",
        tags={"moon", "rock"},
    ),
    "repairwalk": Activity(
        id="repairwalk",
        verb="go fix the outside antenna",
        gerund="going to fix the outside antenna",
        rush="hurry to the antenna",
        danger="scratching the suit",
        zone={"hands", "torso"},
        keyword="antenna",
        tags={"space", "tools"},
    ),
}

PRIZES = {
    "charm": Prize(
        label="charm",
        phrase="a tiny silver charm",
        type="charm",
        region="hands",
    ),
    "map": Prize(
        label="map",
        phrase="a folded star map",
        type="map",
        region="torso",
    ),
    "badge": Prize(
        label="badge",
        phrase="a shiny badge",
        type="badge",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="tether",
        label="a safety tether",
        covers={"hands", "torso"},
        guards={"eva", "dock"},
        prep="clip on a safety tether first",
        tail="went on with the tether clipped tight",
    ),
    Gear(
        id="maggloves",
        label="magnetic gloves",
        covers={"hands"},
        guards={"dock", "antenna", "eva"},
        prep="put on magnetic gloves first",
        tail="kept a firm grip with the magnetic gloves",
    ),
    Gear(
        id="visor",
        label="a bright visor",
        covers={"torso", "hands"},
        guards={"moon", "eva"},
        prep="fasten a bright visor first",
        tail="moved ahead with the visor shining softly",
    ),
]

GIRL_NAMES = ["Mina", "Tia", "Luna", "Nova", "Zuri"]
BOY_NAMES = ["Kai", "Oren", "Pax", "Jett", "Rio"]
TRAITS = ["curious", "brave", "careful", "playful", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if goal_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


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
    "space": [("What is outer space?", "Outer space is the big dark place beyond Earth's air, where stars, moons, and planets are found.")],
    "eva": [("What is a spacewalk?", "A spacewalk is when an astronaut goes outside a spacecraft while wearing a spacesuit.")],
    "tether": [("What does a safety tether do?", "A safety tether helps keep a person from floating away when they are working outside in space.")],
    "visor": [("Why do astronauts wear visors?", "Visors help block bright light and protect an astronaut's eyes while they are working in space.")],
    "maggloves": [("Why are gloves useful in space?", "Gloves help astronauts hold tools and rails safely while they work outside.")],
    "charm": [("What is a charm?", "A charm is a small object people keep because it feels special or lucky.")],
    "map": [("What is a map for?", "A map shows where things are, so it helps people find their way.")],
}

KNOWLEDGE_ORDER = ["space", "eva", "tether", "maggloves", "visor", "charm", "map"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short space adventure for a young child where {hero.id} is going to {act.verb} and quietly thinks about an ulterior reason for the trip.',
        f"Tell a gentle story about {hero.id}, {hero.pronoun('possessive')} mentor, and {hero.pronoun('possessive')} {prize.label}, with advice, inner monologue, and a safe going-out plan.",
        f'Write a small story set at {world.setting.place} that uses the word "going" and ends with something found in space.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about when {hero.id} is going to {act.verb}?",
            answer=f"It is about {hero.id}, a little spacer who is going to {act.verb} with help from {parent.label}.",
        ),
        QAItem(
            question=f"What did the mentor advise {hero.id} to do before going outside?",
            answer=f"The mentor advised {hero.id} to go slowly and stay near the rail so the trip would be safe.",
        ),
        QAItem(
            question=f"What was {hero.id}'s hidden, or ulterior, reason for going out?",
            answer=f"{hero.id} wanted to find the lost {prize.label} near the dish, even while the bigger mission was to go outside safely.",
        ),
        QAItem(
            question=f"How did {hero.id} feel before going out?",
            answer=f"{hero.id} felt a mix of hope and worry, because {hero.pronoun('possessive')} inner monologue was full of careful thoughts.",
        ),
    ]
    if f.get("gear"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help the going-out plan?",
            answer=f"{gear.label} helped by keeping {hero.id} safe while {hero.pronoun('subject')} went outside, so the {prize.label} stayed safe too.",
        ))
        qa.append(QAItem(
            question=f"What happened at the end after {hero.id} kept going?",
            answer=f"{hero.id} found the lost {prize.label} and came back feeling braver than before.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- zone(A, R), worn_on(P, R).
fix(A, P) :- prize_at_risk(A, P), gear(G), guards(G, K), keyword(A, K), covers(G, R), worn_on(P, R).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), fix(A, P).
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
        lines.append(asp.fact("keyword", aid, a.keyword))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for k in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, k))
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
    ap = argparse.ArgumentParser(description="Space adventure story world with inner monologue and advice.")
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


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} does not make {prize.label} honestly at risk in this world.)"


def valid_gender(prize_id: str, gender: str) -> bool:
    return gender in PRIZES[prize_id].genders


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (goal_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and not valid_gender(args.prize, args.gender):
        raise StoryError("(No story: the chosen prize does not fit that gender in this setup.)")
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
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize],
                 params.name, params.gender, params.parent, params.trait)
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


CURATED = [
    StoryParams(place="station", activity="eva", prize="charm", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="moonbase", activity="survey", prize="badge", name="Kai", gender="boy", parent="father", trait="careful"),
    StoryParams(place="shipyard", activity="dockwalk", prize="map", name="Luna", gender="girl", parent="mother", trait="steady"),
]


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
            print(f"  {place:9} {act:10} {prize:8}  [{', '.join(genders)}]")
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
