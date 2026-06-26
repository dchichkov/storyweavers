#!/usr/bin/env python3
"""
storyworlds/worlds/cortisone_friendship_cautionary_tall_tale.py
================================================================

A tall tale world about two friends, a jar of cortisone, and a lesson
in moderation.  The seed word "cortisone" drives the domain; the story
is a cautionary friendship fable told in an exaggerated, frontier style.
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

MESS_KINDS = {"gooey", "sticky", "messy"}

REGIONS = {"leg", "arm", "head"}


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
        female = {"gal", "woman", "mother"}
        male = {"fella", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


# ---------------------------------------------------------------------------
# Parametrization knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the ranch"
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
    genders: set[str] = field(default_factory=lambda: {"fella", "gal"})


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
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }


# ---------------------------------------------------------------------------
# Verbs (tall‑tale flavored)
# ---------------------------------------------------------------------------
def tall_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "big"), "strong")
    world.say(
        f"{hero.id} was the {trait}est {hero.type} in the whole county, "
        f"with a laugh that could shake the cornfield."
    )


def tall_bond(world: World, hero1: Entity, hero2: Entity) -> None:
    world.say(
        f"{hero1.id} and {hero2.id} were tighter than bark on a hickory tree. "
        f"They'd been friends since they could crawl, and everyone knew it."
    )


def tall_injury(world: World, hero: Entity) -> None:
    world.say(
        f"One scorching afternoon, {hero.id} was chopping wood when a log "
        f"rolled and gouged a scrape on {hero.pronoun('possessive')} leg. "
        f"That scrape was the size of a silver dollar, and it stung like a hornet."
    )


def tall_cortisone_intro(world: World, parent: Entity, prize_entity: Entity) -> None:
    world.say(
        f"{parent.label} had a jar of cortisone cream so powerful, "
        f"it could heal a scrape overnight. The jar was as big as a pumpkin "
        f"and sat on the shelf like a golden treasure."
    )
    prize_entity.worn_by = None  # it's a jar, not worn


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def want_cortisone(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} grabbed the jar and wanted to {activity.verb} the scrape "
        f"right then, but {friend.id} held up a hand."
    )


def warn_tall(world: World, friend: Entity, hero: Entity, activity: Activity,
              prize_entity: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize_entity.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll get your {prize_entity.label} {activity.soil}"
    if pred["workload"] >= THRESHOLD:
        clause += f", and then I'll have to clean {prize_entity.it()}"
    world.say(
        f'"{clause}," {friend.id} said. "Cortisone is strong medicine. "
        f"Use it like a sprinkler, not a fire hose!"'
    )
    return True


def defies_tall(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} didn't listen. {hero.pronoun().capitalize()} dipped two fingers "
        f"in the jar and slapped a gob of cortisone on the scrape."
    )
    world.say(f"The goo was thick and sticky, and it oozed down {hero.pronoun('possessive')} leg.")


def grab_hand_tall(world: World, friend: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"'{friend.id} grabbed {hero.pronoun('possessive')} hand and said, "
        f'"Hold on, partner! That\'s enough cortisone for a whole herd!"'
    )


def pout_tall(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["conflict"] >= THRESHOLD:
        world.say(
            f'{hero.id} pouted. "But it hurts! I want to be better fast!"'
        )


def compromise_tall(world: World, friend: Entity, hero: Entity, activity: Activity,
                    prize_entity: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize_entity)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=friend.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize_entity.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{friend.id} looked at the mess and said, "How about we wrap that "
        f'scrape with {gear_def.prep} first, then just a dab of cortisone? '
        f'That way your {prize_entity.label} stays clean."'
    )
    return gear_def


def accept_tall(world: World, friend: Entity, hero: Entity, activity: Activity,
                prize_entity: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded and grinned. 'Alright, I trust you, partner.' "
        f"They {gear_def.tail}. A tiny dab of cortisone did the trick. "
        f"The scrape healed by sundown, and {hero.pronoun('possessive')} "
        f"{prize_entity.label} stayed clean."
    )
    world.say(
        f"The two friends sat on the porch, watching the stars, and "
        f"{friend.id} said, 'That's what friends are for — to keep each other "
        f"from using a whole pumpkin of cortisone.'"
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Big Hank", hero_type: str = "fella",
         hero_traits: Optional[list[str]] = None,
         friend_name: str = "Slim Jim", friend_type: str = "fella") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["big"] + (hero_traits or ["strong", "stubborn"]),
    ))
    friend = world.add(Entity(
        id=friend_name, kind="character", type=friend_type,
        traits=["wise", "cautious"],
    ))
    # Prize is the jar of cortisone itself (a prized possession)
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=friend.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1
    tall_intro(world, hero)
    tall_bond(world, hero, friend)
    world.para()

    # Act 2
    tall_injury(world, hero)
    tall_cortisone_intro(world, friend, prize)
    want_cortisone(world, hero, friend, activity)
    warn_tall(world, friend, hero, activity, prize)
    defies_tall(world, hero, activity)
    grab_hand_tall(world, friend, hero, activity)

    # Act 3
    world.para()
    pout_tall(world, hero, activity)
    gear_def = compromise_tall(world, friend, hero, activity, prize)
    if gear_def:
        accept_tall(world, friend, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero, friend=friend, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, gear=gear_def,
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ranch": Setting(place="the ranch", indoor=False, affords={"soothe"}),
    "barn": Setting(place="the barn", indoor=True, affords={"soothe"}),
}

ACTIVITIES = {
    "soothe": Activity(
        id="soothe",
        verb="slather cortisone on",
        gerund="slathering cortisone on",
        rush="slap the cream on",
        mess="gooey",
        soil="sticky and gooey",
        zone={"leg"},
        weather="",
        keyword="cortisone",
        tags={"cortisone", "gooey"},
    ),
}

PRIZES = {
    "jar": Prize(
        label="cortisone jar",
        phrase="a huge jar of cortisone cream",
        type="jar",
        region="leg",
        genders={"fella", "gal"},
    ),
}

GEAR = [
    Gear(
        id="rag",
        label="a clean rag",
        covers={"leg"},
        guards={"gooey"},
        prep="a clean rag",
        tail="wrapped the leg in a clean rag",
    ),
]

GIRL_NAMES = ["Big Betty", "Tall Sally", "Mighty Mae"]
BOY_NAMES = ["Big Hank", "Lanky Lou", "Slim Jim", "Gus"]
TRAITS = ["strong", "stubborn", "reckless", "brave", "funny"]


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
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "cortisone": [
        ("What is cortisone?",
         "Cortisone is a medicine that helps heal skin scrapes and rashes. "
         "It comes as a cream, and you should use only a little bit."),
    ],
    "gooey": [
        ("Why does too much cream make things gooey?",
         "If you put on too much cream, it does not soak in and stays on top "
         "of your skin, making everything sticky and messy."),
    ],
    "friendship": [
        ("Why is it important to listen to a friend?",
         "Friends give good advice because they care about you. Listening to "
         "them can help you avoid mistakes."),
    ],
}

KNOWLEDGE_ORDER = ["cortisone", "gooey", "friendship"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, act = f["hero"], f["friend"], f["activity"]
    return [
        f'Write a tall tale about two friends and a jar of cortisone that '
        f'teaches a cautionary lesson about listening to advice.',
        f'Create an exaggerated frontier story where {hero.id} uses too much '
        f'cortisone and learns from {friend.id} a lesson in moderation.',
        f'Tell a friendship fable set on a ranch, using the word "cortisone", '
        f'with a comically large jar and a messy consequence.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, act = f["hero"], f["friend"], f["prize"], f["activity"]
    trait = next((t for t in hero.traits if t != "big"), "strong")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who are the two friends in the story?",
            answer=f"The story is about {hero.id}, a {trait} {hero.type}, "
                   f"and {friend.id}, a wise friend. They live on {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the cortisone?",
            answer=f"{hero.id} wanted to {act.verb} the scrape with the cortisone, "
                   f"but {friend.id} warned {hero.pronoun('object')} not to use too much.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {friend.id} grab {hero.id}'s hand?",
            answer=f"{friend.id} grabbed {hero.pronoun('possessive')} hand because "
                   f"{hero.id} was about to use way too much cortisone, which would "
                   f"make a sticky mess and ruin the prize.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the friends solve the problem?",
            answer=f"They used a {gear.label} and just a tiny dab of cortisone. "
                   f"The scrape healed, and {hero.pronoun('possessive')} "
                   f"{prize.label} stayed clean.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Curated examples
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(
        place="ranch",
        activity="soothe",
        prize="jar",
        hero_name="Big Hank",
        hero_type="fella",
        friend_name="Slim Jim",
        friend_type="fella",
        trait="stubborn",
    ),
    StoryParams(
        place="barn",
        activity="soothe",
        prize="jar",
        hero_name="Big Betty",
        hero_type="gal",
        friend_name="Tall Sally",
        friend_type="gal",
        trait="reckless",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get "
                f"{activity.mess}, so the friend has no honest warning. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: nothing in the gear catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk item, so this argument is rejected.)")


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


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall tale world: cortisone, friendship, cautionary.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--activity", choices=list(ACTIVITIES))
    ap.add_argument("--prize", choices=list(PRIZES))
    ap.add_argument("--hero-type", choices=["fella", "gal"])
    ap.add_argument("--friend-type", choices=["fella", "gal"])
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
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
    hero_type = args.hero_type or rng.choice(["fella", "gal"])
    friend_type = args.friend_type or rng.choice(["fella", "gal"])
    if hero_type == "fella":
        hero_name = args.hero_name or rng.choice(BOY_NAMES)
    else:
        hero_name = args.hero_name or rng.choice(GIRL_NAMES)
    if friend_type == "fella":
        friend_name = args.friend_name or rng.choice(BOY_NAMES)
    else:
        friend_name = args.friend_name or rng.choice(GIRL_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        hero_name=hero_name,
        hero_type=hero_type,
        friend_name=friend_name,
        friend_type=friend_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.hero_name, params.hero_type,
                 [params.trait, "stubborn"], params.friend_name, params.friend_type)
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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
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
            header = f"### {p.hero_name} and {p.friend_name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
