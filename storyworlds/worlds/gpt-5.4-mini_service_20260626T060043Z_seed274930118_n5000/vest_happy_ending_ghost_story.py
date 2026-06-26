#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/vest_happy_ending_ghost_story.py
===============================================================================================================

A small story world with a ghost-story mood, a vest, and a happy ending.

Premise:
- A child loves a special vest.
- A gentle ghost stirs up a spooky-seeming errand at dusk.
- The vest is at risk of getting dusty or damp.
- A sensible grown-up offers a simple fix.
- The ending proves the little world changed: fear softens into friendship.

This script follows the Storyweavers contract:
- self-contained stdlib script
- lazy ASP import through storyworlds/asp.py
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- Python reasonableness gate plus inline ASP_RULES twin
"""

from __future__ import annotations

import argparse
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
        if not self.meters:
            self.meters = {"dusty": 0.0, "wet": 0.0, "dirty": 0.0, "workload": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "curiosity": 0.0, "conflict": 0.0, "love": 0.0}

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
    place: str = "the old house"
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


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("dusty", 0.0) < THRESHOLD and actor.meters.get("wet", 0.0) < THRESHOLD:
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
            item.meters["dusty"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.id}'s {item.label} got dusty.")
    return out


def _r_workload(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.meters["workload"] = carer.meters.get("workload", 0.0) + 1
        out.append(f"That would mean more work for {carer.id}.")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("fear", 0.0) < THRESHOLD or actor.memes.get("curiosity", 0.0) < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [
    _r_soil,
    _r_workload,
    _r_fear,
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
                produced.extend(s for s in sents if s != "__fear__")
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
    sim = world_copy(world)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def world_copy(world: World) -> World:
    import copy
    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.weather = world.weather
    clone.paragraphs = [[]]
    return clone


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["curiosity"] = actor.memes.get("curiosity", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "quiet")
    world.say(f"{hero.id} was a little {trait} {hero.type} who liked the house when the lamps were low.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    prize.worn_by = hero.id
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} everywhere.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One foggy evening, {hero.id} and {hero.pronoun('possessive')} {parent.id} went to {world.setting.place}.")
    world.say("The stairs creaked, and even the wallpaper seemed to whisper.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but the hallway felt spooky and still.")
    world.say(f"{hero.pronoun().capitalize()} took a careful breath and stepped closer anyway.")


def warn(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(f'"You\'ll get your {prize.label} {activity.soil}," {parent.id} said softly. "Let\'s be smart about it."')
    return True


def ghost_appears(world: World, ghost: Entity, hero: Entity) -> None:
    ghost.memes["love"] = ghost.memes.get("love", 0.0) + 1
    world.say(f"A small ghost drifted out of the shadows. It was not scary at all.")
    world.say(f'"I only wanted to help," the ghost whispered. "I can carry the lantern if you can see me."')


def surprise(world: World, hero: Entity, ghost: Entity) -> None:
    hero.memes["fear"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} blinked, then smiled. The ghost was lonely, not mean.")
    world.say(f"{hero.id} waved, and the ghost waved back from the dust.")


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
    world.say(f'{parent.id} smiled. "How about we {gear_def.prep} first?"')
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.say(f'{hero.id} nodded and hugged {hero.pronoun("possessive")} {parent.id}. "Okay," {hero.pronoun()} said.')
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {activity.gerund}, while {prize.label} stayed clean and bright.")
    world.say("The little ghost floated beside them, happy to be seen at last.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Mina",
         hero_type: str = "girl", hero_traits: Optional[list[str]] = None,
         parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "foggy"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"])
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label="the ghost"))

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

    introduce(world, hero)
    world.say("She loved quiet rooms, moonlit windows, and the soft sound of old floorboards.")
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    ghost_appears(world, ghost, hero)
    surprise(world, hero, ghost)

    world.para()
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        parent=parent,
        ghost=ghost,
        prize=prize,
        prize_cfg=prize_cfg,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "old_house": Setting(place="the old house", indoor=True, affords={"attic"}),
    "quiet_attic": Setting(place="the quiet attic", indoor=True, affords={"attic"}),
    "moonlit_hall": Setting(place="the moonlit hall", indoor=True, affords={"hall"}),
}

ACTIVITIES = {
    "attic": Activity(
        id="attic",
        verb="search the attic",
        gerund="searching the attic",
        rush="run up the dusty stairs",
        mess="dusty",
        soil="all dusty",
        zone={"torso"},
        weather="foggy",
        keyword="ghost",
        tags={"ghost", "dust", "attic"},
    ),
    "hall": Activity(
        id="hall",
        verb="follow the ghost light",
        gerund="following the ghost light",
        rush="hurry down the hallway",
        mess="dusty",
        soil="dusty and dim",
        zone={"torso"},
        weather="foggy",
        keyword="ghost",
        tags={"ghost", "hall", "light"},
    ),
}

PRIZES = {
    "vest": Prize(
        label="vest",
        phrase="a bright little vest",
        type="vest",
        region="torso",
        genders={"girl", "boy"},
    ),
}

GEAR = [
    Gear(
        id="smock",
        label="an old smock",
        covers={"torso"},
        guards={"dusty"},
        prep="put on an old smock first",
        tail="went back for the old smock",
    ),
]

NAMES_GIRL = ["Mina", "Nora", "Lily", "Ivy", "Ada"]
NAMES_BOY = ["Finn", "Theo", "Ben", "Leo", "Owen"]
TRAITS = ["brave", "curious", "quiet", "cheerful", "gentle"]


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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


KNOWLEDGE = {
    "ghost": [("What is a ghost?",
               "A ghost is a spooky story creature. In gentle stories, a ghost can be kind, lonely, and friendly.")],
    "attic": [("What is an attic?",
               "An attic is the room up under a house roof. People often store old boxes there.")],
    "dust": [("Why does dust make things look old?",
              "Dust is tiny soft bits that settle on surfaces, so things can look gray or dull when they are dusty.")],
    "vest": [("What is a vest?",
               "A vest is a sleeveless piece of clothing that covers your middle and keeps you neat or warm.")],
    "light": [("Why do people use lanterns in the dark?",
              "Lanterns help people see the floor, steps, and doors when it is too dark to look around safely.")],
}
KNOWLEDGE_ORDER = ["ghost", "attic", "dust", "vest", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short ghost story for a small child that includes the word "{act.keyword}" and ends happily.',
        f"Tell a gentle spooky story where {hero.id} wants to {act.verb} while wearing {prize.phrase}, and a grown-up helps.",
        f"Write a moonlit story about a {hero.type} named {hero.id}, a friendly ghost, and a {prize.label} that stays safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type}, and {hero.pronoun('possessive')} {parent.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the old house?",
            answer=f"{hero.id} wanted to {act.verb}. The old house felt spooky, but {hero.id} kept going.",
        ),
        QAItem(
            question=f"What special clothes did {hero.id} wear?",
            answer=f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}, and it stayed bright through the story.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry?",
            answer=f"{parent.id} worried because {hero.id}'s {prize.label} could get {f.get('predicted_soil', 'dusty')} in the attic or hallway.",
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did {gear.label} help?",
            answer=f"They put on {gear.label} first, so {hero.id} could {act.verb} without ruining the {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"The ending was happy: {hero.id} and the ghost became friends, and the {prize.label} stayed clean.",
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} would not reach the {prize.label}, so there is no honest spooky problem.)"
    return f"(No story: no gear in this tiny world can properly protect the {prize.label} from {activity.gerund}.)"


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


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


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
    c, p = set(asp_valid_combos()), set(valid_combos())
    if c == p:
        print(f"OK: clingo gate matches valid_combos() ({len(c)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if c - p:
        print("  only in clingo:", sorted(c - p))
    if p - c:
        print("  only in python:", sorted(p - c))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with a vest and a happy ending.")
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
        raise StoryError("(No story: that vest choice does not fit the requested gender in this tiny world.)")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


CURATED = [
    StoryParams(place="old_house", activity="attic", prize="vest", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="quiet_attic", activity="attic", prize="vest", name="Finn", gender="boy", parent="father", trait="brave"),
]


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
            print(f"  {place:11} {act:8} {prize:8}  [{', '.join(genders)}]")
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
