#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50/nummy_catalogue_tartar_happy_ending_space_adventure.py
==============================================================================================================================

A tiny space-adventure storyworld about a curious crew, a nummy catalogue,
a tartar sauce spill, and a happy ending.

Seed tale:
---
On a small starship, a child named Mina loved browsing the ship's nummy
catalogue, a bright booklet full of space snacks. She also loved crispy moon
cakes with tartar sauce, because it made the cakes feel extra fancy.

One day, Mina carried the catalogue to the snack console while the ship drifted
near a sparkly comet field. She wanted to order her favorite meal right away,
but the captain warned her that tartar sauce could drip onto the catalogue and
make the pages sticky. Mina frowned and reached for the bottle anyway.

Then the ship hit a tiny bump, the sauce wobbled, and the captain caught the
bottle before it splashed. Together they found a safer tray, cleaned the page,
and Mina still got her nummy meal. In the end, the catalogue stayed neat, the
snacks were served, and Mina smiled at the stars.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain-girl"}
        male = {"boy", "father", "man", "captain-boy"}
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
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("sticky", "wet"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1.0
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1.0
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0.0) < THRESHOLD or actor.memes.get("wants_now", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1.0
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("soil", "physical", _r_soil),
    Rule("work", "physical", _r_work),
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
        "soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD),
        "workload": sum(e.meters.get("workload", 0.0) for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "snack": "the smell of warm space bread and sweet sauce made everyone smile",
        "catalogue": "the bright pages were full of shiny pictures and funny names",
        "comet": "the glittery stars outside the window made the whole ship feel magical",
    }.get(activity.id, "it made the voyage feel exciting")


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little space traveler who noticed every shiny thing on the ship.")


def loves_things(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    world.say(f"{hero.pronoun().capitalize()} loved browsing the nummy catalogue and {activity.gerund}; {activity_delight(activity)}.")


def catalog_buy(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One day, {hero.id}'s {parent.label} bought {hero.pronoun('object')} {prize.phrase}.")


def prize_love(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and carried {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One bright orbiting day, {hero.id} and {hero.pronoun('possessive')} {parent.label} were on {world.setting.place}.")
    world.say("Outside the window, a comet field twinkled like a pocket full of stars.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["wants_now"] = hero.memes.get("wants_now", 0.0) + 1.0
    world.say(f"{hero.id} wanted to {activity.verb} right away, but the snack tray was still closed.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    world.say(f'"You\'ll get your {prize.label} {activity.soil}," {parent.label} said. "Let\'s keep the pages clean."')
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1.0
    world.say(f"{hero.id} frowned and tried to {activity.rush}.")


def grab(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1.0
    propagate(world, narrate=False)
    world.say(f"Then {hero.pronoun('possessive')} {parent.label} gently grabbed the bottle before it could splash the catalogue.")


def pout(world: World, hero: Entity) -> None:
    if hero.memes.get("conflict", 0.0) >= THRESHOLD:
        world.say(f"{hero.id} pouted for a moment, because the snack still felt far away.")


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
    world.say(f'{hero.pronoun("possessive").capitalize()} {parent.label} smiled. "How about we {gear_def.prep} and {activity.verb} together?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up and {hero.pronoun()} hugged {hero.pronoun('possessive')} {parent.label}.")
    world.say(f'They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {hero.pronoun("possessive")} {prize.label} stayed neat, and the stars looked extra bright.')


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "captain") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, kind_hint: str = "character"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="captain"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        worn_by=hero.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_things(world, hero, activity)
    catalog_buy(world, parent, hero, prize)
    prize_love(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab(world, parent, hero)

    world.para()
    pout(world, hero)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes.get("grabbed_by", 0.0) >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "starship": Setting(place="the starship", affords={"snack", "catalogue"}),
    "orbital_kitchen": Setting(place="the orbital kitchen", affords={"snack"}),
    "comet_deck": Setting(place="the comet deck", affords={"comet", "snack"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="eat the nummy snack",
        gerund="eating nummy snacks",
        rush="dash to the snack tray",
        mess="sticky",
        soil="sticky and smudged",
        zone={"hands", "torso"},
        keyword="nummy",
        tags={"nummy", "sticky"},
    ),
    "catalogue": Activity(
        id="catalogue",
        verb="browse the catalogue",
        gerund="flipping through the catalogue",
        rush="run to the catalogue drawer",
        mess="sticky",
        soil="sticky",
        zone={"hands"},
        keyword="catalogue",
        tags={"catalogue", "paper"},
    ),
    "comet": Activity(
        id="comet",
        verb="watch the comet sparkle",
        gerund="watching the comet sparkle",
        rush="dash to the window",
        mess="wet",
        soil="damp",
        zone={"hands", "torso"},
        keyword="comet",
        tags={"comet", "space"},
    ),
}

PRIZES = {
    "catalogue": Prize(label="catalogue", phrase="a bright nummy catalogue", type="catalogue", region="hands"),
    "tray": Prize(label="snack tray", phrase="a shiny snack tray", type="tray", region="hands"),
    "scarf": Prize(label="scarf", phrase="a soft travel scarf", type="scarf", region="torso"),
}

GEAR = [
    Gear(id="napkin_gloves", label="napkin gloves", covers={"hands"}, guards={"sticky"}, prep="put on napkin gloves first", tail="put on the napkin gloves"),
    Gear(id="tray_lid", label="a tray lid", covers={"hands"}, guards={"sticky"}, prep="cover the bottle with a tray lid", tail="slid the lid over the tray"),
    Gear(id="seal_cloth", label="a seal cloth", covers={"torso", "hands"}, guards={"wet", "sticky"}, prep="use a seal cloth before the snack", tail="wrapped the cloth around the tray"),
]

HERO_NAMES = ["Mina", "Tavi", "Rin", "Kia", "Noa"]
TRAITS = ["curious", "cheerful", "brave", "merry"]


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
    "nummy": [("What does nummy mean?", "Nummy means tasty and yummy, like a snack that smells good and makes your tummy feel happy.")],
    "catalogue": [("What is a catalogue?", "A catalogue is a book or list that shows things you can choose from.")],
    "tartar": [("What is tartar sauce?", "Tartar sauce is a creamy sauce often served with fish or crispy snacks.")],
    "sticky": [("Why do sticky things make a mess?", "Sticky things can cling to pages, hands, and clothes, so they are hard to clean up.")],
    "space": [("What is a comet?", "A comet is a space rock made of ice and dust that can glow when it gets close to the sun.")],
}
KNOWLEDGE_ORDER = ["nummy", "catalogue", "tartar", "sticky", "space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short space-adventure story for a small child that includes the words "nummy", "catalogue", and "tartar".',
        f"Tell a gentle spaceship story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label} worries about {prize.phrase}.",
        f"Write a happy-ending story set on {world.setting.place} about a child, a sticky mistake, and a safer plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about on the starship?",
            answer=f"It is about {hero.id}, a little space traveler, and the {parent.label} who helps keep the ship safe.",
        ),
        QAItem(
            question=f"What did {hero.id} love to browse?",
            answer=f"{hero.id} loved the nummy catalogue full of shiny space snacks.",
        ),
        QAItem(
            question=f"What was the tasty thing that made the captain worry?",
            answer=f"The captain worried about tartar sauce because it could make the {prize.label} sticky if it spilled.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {parent.label} warn {hero.id}?",
            answer=f"{parent.label} warned {hero.id} because if {hero.id} went to {act.verb}, the {prize.label} could get {act.soil} and would need cleaning.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the crew keep the {prize.label} safe?",
            answer=f"They used {gear.label} first, so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} enjoying the snack, the catalogue staying neat, and the stars shining outside the window.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    if "tartar" in world.facts["prize"].label:
        tags.add("tartar")
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="starship", activity="snack", prize="catalogue", name="Mina", gender="girl", parent="captain", trait="curious"),
    StoryParams(place="comet_deck", activity="catalogue", prize="tray", name="Tavi", gender="boy", parent="captain", trait="cheerful"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not endanger {noun}, so there is no honest warning to make.)"
    return f"(No story: nothing in the gear catalog protects {noun} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    return f"(No story: {PRIZES[prize_id].label} does not depend on gender here, but you requested {gender}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world with a nummy catalogue and a tartar-sauce mishap.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or "captain"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:12} {act:10} {prize}")
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
