#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chemical_category_kindness_repetition_fairy_tale.py
==============================================================================================================

A small fairy-tale story world about a child, a chemical mishap, a category
problem, and a gentle fix made from kindness and repetition.

Seed-image premise:
- In a moonlit fairy kitchen, a child apprentice wants to make a bright
  chemical potion.
- The trouble is that the ingredients must be sorted into the right category.
- The child keeps things calm by repeating a kind little rhyme and following a
  safer step-by-step method.
- A parent worries about a treasured cloth, then the two find a compromise.

The world is intentionally narrow so every generated story has a clear turn:
the child wants to do the messy magic, the parent warns, the child resists,
then a kind repeated routine and the right gear make the ending safe.

This script follows the Storyweavers storyworld contract:
- typed entities with physical meters and emotional memes
- a reasonableness gate in Python plus an inline ASP twin
- StoryParams / generate / emit / CLI
- self-contained stdlib prose engine, with clingo imported only in ASP helpers
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

CATEGORIES = ("flower", "berry", "leaf", "sparkle")
MATERIALS = {
    "flower": "flower dust",
    "berry": "berry syrup",
    "leaf": "leaf powder",
    "sparkle": "moon salt",
}


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
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "witch"}
        male = {"boy", "father", "man", "king", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "queen": "queen", "king": "king"}.get(self.type, self.type)


@dataclass
class Setting:
    place: str
    indoor: bool
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("chemical", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["stained"] = item.meters.get("stained", 0.0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got stained.")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        out.append(f"{actor.id} kept speaking softly, and the room felt gentler.")
    return out


def _r_repetition(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("repetition", 0.0) < THRESHOLD:
            continue
        sig = ("repetition", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["careful_steps"] = actor.meters.get("careful_steps", 0.0) + 1
        out.append(f"{actor.id} repeated the little rhyme again, and the steps stayed careful.")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_kindness,
    _r_repetition,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
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
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["chemical"] = actor.meters.get("chemical", 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return "A round wooden table waited by the window, where moonlight made the bowls shine."
    return "The herb garden was bright with dew, and the little paths curled around the roses."


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "gentle")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved fairy-tale work and careful hands."
    )


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved to {activity.verb}, because every little bubble felt like a secret song."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One spring morning, {hero.id}'s {parent.label_word} bought {hero.pronoun('object')} {prize.phrase}."
    )


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} adored {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One day, "
    go = "went to"
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label_word} {go} {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity.verb} right away, but {hero.pronoun('possessive')} {parent.label_word} lifted a careful hand."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"You\'ll get your {prize.label} {activity.soil}," {hero.pronoun("possessive")} {parent.label_word} said.'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(
        f"{hero.id} frowned, because the potion idea still tugged at {hero.pronoun('possessive')} thoughts."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {activity.rush}.")


def grab_conflict(world: World, parent: Entity, hero: Entity) -> None:
    hero.memes["grabbed_by"] = hero.memes.get("grabbed_by", 0.0) + 1
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label_word} gently held {hero.pronoun('possessive')} hand and said, "
        f"\"We can be kind and still be careful.\""
    )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{hero.pronoun("possessive").capitalize()} {parent.label_word} smiled and said, '
        f"\"How about we {gear_def.prep} and sort the ingredients by category first?\""
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    hero.memes["repetition"] = hero.memes.get("repetition", 0.0) + 1
    world.say(
        f"{hero.id} nodded, then repeated the little rhyme three times: "
        f"\"Flower with flower, berry with berry, leaf with leaf, and sparkle with sparkle.\""
    )
    world.say(
        f"After that, {hero.id} was {activity.gerund}, {prize.label} stayed clean, and the potion shone in a happy, harmless glow."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["gentle", "brave"])))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
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

    intro(world, hero)
    loves(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_conflict(world, parent, hero)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=True,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "cottage": Setting(place="the mossy cottage", indoor=True, affords={"brew", "sort"}),
    "garden": Setting(place="the moonlit garden", indoor=False, affords={"brew", "sort"}),
}

ACTIVITIES = {
    "brew": Activity(
        id="brew",
        verb="brew a bright potion",
        gerund="brewing bright potions",
        rush="dash to the bubbling cauldron",
        mess="stained",
        soil="stained and sticky",
        zone={"torso", "hands"},
        keyword="chemical",
        tags={"chemical", "category"},
    ),
    "sort": Activity(
        id="sort",
        verb="sort the ingredients",
        gerund="sorting ingredients by category",
        rush="grab every jar at once",
        mess="stained",
        soil="spilled and stained",
        zone={"hands"},
        keyword="category",
        tags={"chemical", "category"},
    ),
}

PRIZES = {
    "cloak": Prize(
        label="cloak",
        phrase="a silver cloak",
        type="cloak",
        region="torso",
    ),
    "apron": Prize(
        label="apron",
        phrase="a white apron",
        type="apron",
        region="torso",
    ),
    "sleeves": Prize(
        label="sleeves",
        phrase="a clean white sleeve-smock",
        type="smock",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="apron",
        label="an apron",
        covers={"torso"},
        guards={"stained"},
        prep="put on an apron first",
        tail="went to fetch the apron",
    ),
    Gear(
        id="cloth",
        label="a cloth cloak-cover",
        covers={"torso"},
        guards={"stained"},
        prep="lay a cloth cloak-cover over the prize first",
        tail="found the cloth cloak-cover",
    ),
]

GIRL_NAMES = ["Mira", "Lena", "Tessa", "Nina", "Elsa", "Iris"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Milo", "Bram", "Noel"]
TRAITS = ["gentle", "curious", "brave", "patient", "bright", "cheerful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, prize_id))
    return combos


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach a {prize.label} worn on the {prize.region}.)"
    return f"(No story: no chosen gear can keep a {prize.label} safe during {activity.gerund}.)"


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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
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


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set((p, a, pr) for p, pr in valid_combos() for a in [next(act for act, cfg in ACTIVITIES.items() if cfg.id in ACTIVITIES and any((p == pl and pr == pr_id) for pl, pr_id in valid_combos()))])
    # Simpler: derive python tuple set directly from registries.
    python_set = set()
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    python_set.add((place, act_id, prize_id))
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a fairy-tale story for a child about "{act.keyword}" and a kind, careful choice.',
        f"Tell a small story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} {parent.label_word} worries about {prize.phrase}.",
        f"Write a gentle tale that includes a chemical problem, a category rule, and a happy compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label_word} worry about the {prize.label}?",
            answer=f"{parent.label_word.capitalize()} worried because the {prize.label} could get {act.soil} during the chemical work.",
        ),
        QAItem(
            question=f"What kind of plan helped {hero.id} finish the work safely?",
            answer=f"They used {gear.label} and sorted the ingredients by category before mixing.",
        ),
        QAItem(
            question=f"What repeated words did {hero.id} say near the end?",
            answer='They repeated a little rhyme: "Flower with flower, berry with berry, leaf with leaf, and sparkle with sparkle."',
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chemical?",
            answer="A chemical is a substance that can mix with other substances and change into something new.",
        ),
        QAItem(
            question="What is a category?",
            answer="A category is a group of things that belong together because they are alike.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means using gentle words and helpful actions to care for someone else.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means doing or saying something again and again.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="cottage", activity="brew", prize="cloak", name="Mira", gender="girl", parent="mother", trait="gentle"),
    StoryParams(place="garden", activity="sort", prize="apron", name="Theo", gender="boy", parent="father", trait="curious"),
    StoryParams(place="cottage", activity="sort", prize="sleeves", name="Lena", gender="girl", parent="mother", trait="patient"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about chemical work, category sorting, kindness, and repetition.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(explain_gender(args.prize, args.gender))

    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    if args.place and place != args.place:
                        continue
                    if args.activity and act_id != args.activity:
                        continue
                    if args.prize and prize_id != args.prize:
                        continue
                    if args.gender and args.gender not in prize.genders:
                        continue
                    combos.append((place, act_id, prize_id))
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
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print(f"  {t[0]:8} {t[1]:8} {t[2]:8}")
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
