#!/usr/bin/env python3
"""
storyworlds/worlds/coarse_magic_myth.py
======================================

A small mythic storyworld about coarse magic: a young seeker, a risky spell,
and a careful compromise that keeps a treasured thing safe.

The premise is built from a simple seed-tale:
- A young hero is eager to use a rough, ancient magic.
- A wiser elder warns that the spell would harm a cherished object.
- They choose a fitting safeguard so the hero can still complete the act.

The world is intentionally compact and constraint-checked: only combinations
where the risk is real and the protective fix truly helps are allowed.

Style goal:
- mythic, child-facing, concrete
- short, complete stories with a clear turn and ending image
- simulated state drives the narration
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "singed": 0.0, "dusty": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "desire": 0.0, "warning": 0.0, "defiance": 0.0,
                          "conflict": 0.0, "love": 0.0, "calm": 0.0, "grabbed_by": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "priestess"}
        male = {"boy", "father", "man", "king", "priest"}
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
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
        self.fired: set[tuple] = set()
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("wet", "singed", "dusty"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("spoil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{item.label.capitalize()} got {mess} and dirty.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("grabbed_by", 0.0) < THRESHOLD or actor.memes.get("defiance", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("conflict", 0.0) >= THRESHOLD and actor.memes.get("calm", 0.0) >= THRESHOLD:
            sig = ("settle", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.memes["conflict"] = 0.0
            out.append(f"{actor.id} grew calm again.")
    return out


CAUSAL_RULES = [
    _r_spoil,
    _r_grab_conflict,
    _r_calm,
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
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def title_case(name: str) -> str:
    return name[:1].upper() + name[1:]


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "young")
    world.say(f"{title_case(hero.id)} was a little {trait} {hero.type} who lived by old stones and old songs.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb} because {activity.keyword} felt like a small miracle.")


def gives_prize(world: World, giver: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"One feast day, {giver.label} gave {hero.id} {hero.pronoun('object')} {prize.phrase}.")
    prize.worn_by = hero.id


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    world.say(f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} wherever {hero.pronoun()} went.")


def arrive(world: World, hero: Entity, elder: Entity, activity: Activity) -> None:
    day = {"rainy": "On a rain-bright day, ", "sunny": "On a sun-warm day, "}.get(activity.weather and "sunny", "One day, ")
    go = "went to" if not world.setting.indoor else "came into"
    world.say(f"{day}{hero.id} and {elder.label} {go} {world.setting.place}.")
    world.say(f"The air there was still, and {world.setting.place} felt ready for old magic.")


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {activity.verb} at once, but {hero.pronoun('possessive')} heart was racing too fast.")


def warn(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    elder.memes["warning"] += 1
    clause = f'“If you {activity.verb}, your {prize.label} will get {activity.soil},” {elder.label} said.'
    if pred["soiled"]:
        clause += " “We must choose a gentler way.”"
    world.say(clause)
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"{hero.id} did not want to wait. {hero.pronoun().capitalize()} tried to {activity.rush}.")


def grab_hand(world: World, elder: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {elder.label} caught {hero.pronoun('possessive')} hand and said, "
        f'“You can still {activity.verb}, but we will do it safely.”'
    )


def settle(world: World, hero: Entity) -> None:
    hero.memes["calm"] += 1
    hero.memes["conflict"] = 0.0


def compromise(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=hero.id,
        caretaker=elder.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    if predict_mess(world, hero, activity, prize.id)["soiled"]:
        del world.entities[gear.id]
        return None
    settle(world, hero)
    world.say(f"{elder.label} brought out {gear.label} and helped {hero.id} wear it.")
    return gear_def


def resolve(world: World, elder: Entity, hero: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    world.say(f"{hero.id} smiled, and {hero.pronoun()} hugged {hero.pronoun('possessive')} {elder.label}.")
    world.say(
        f"Together they {gear_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"while {prize.label} stayed clean and bright."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "iara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, elder_type: str = "priestess") -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["brave", "curious"]),
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the priestess",
    ))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_activity(world, hero, activity)
    gives_prize(world, elder, hero, prize)
    loves_prize(world, hero, prize)

    world.para()
    arrive(world, hero, elder, activity)
    wants(world, hero, activity)
    warn(world, elder, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, elder, hero, activity)

    world.para()
    gear_def = compromise(world, elder, hero, activity, prize)
    if gear_def:
        resolve(world, elder, hero, activity, prize, gear_def)

    world.facts.update(
        hero=hero,
        elder=elder,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        conflict=hero.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "shrine": Setting(place="the shrine courtyard", affords={"rain", "sparks", "wind"}),
    "grove": Setting(place="the moonlit grove", affords={"rain", "wind"}),
    "hill": Setting(place="the high hill", affords={"wind", "sparks"}),
}

ACTIVITIES = {
    "rain": Activity(
        id="rain",
        verb="call the rain",
        gerund="calling the rain",
        rush="call the rain at once",
        mess="wet",
        soil="soaked through",
        zone={"torso", "legs"},
        weather="rainy",
        keyword="rain",
        tags={"rain", "water"},
    ),
    "sparks": Activity(
        id="sparks",
        verb="wake the sparks",
        gerund="waking the sparks",
        rush="strike the stone for sparks",
        mess="singed",
        soil="singed at the hem",
        zone={"torso"},
        weather="",
        keyword="sparks",
        tags={"fire", "sparks"},
    ),
    "wind": Activity(
        id="wind",
        verb="call the wind",
        gerund="calling the wind",
        rush="lift the staff to the wind",
        mess="dusty",
        soil="gray with dust",
        zone={"torso", "head"},
        weather="",
        keyword="wind",
        tags={"wind", "sky"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a coarse wool cloak", type="cloak", region="torso"),
    "wreath": Prize(label="wreath", phrase="a woven leaf wreath", type="wreath", region="head"),
    "torch": Prize(label="torch", phrase="a bright torch with a dry wick", type="torch", region="torso"),
}

GEAR = [
    Gear(
        id="rainmantle",
        label="a waxed rain mantle",
        covers={"torso", "legs"},
        guards={"wet"},
        prep="wrap the rain mantle around the cloak",
        tail="walked back to the shrine court and cast the rain together",
    ),
    Gear(
        id="hood",
        label="a soot-dark hood",
        covers={"torso", "head"},
        guards={"singed"},
        prep="tie on the soot-dark hood",
        tail="stood under the night sky and woke the sparks carefully",
    ),
    Gear(
        id="veil",
        label="a dust veil",
        covers={"head", "torso"},
        guards={"dusty"},
        prep="pull the dust veil over the wreath",
        tail="climbed the hill and called the wind without losing the wreath",
    ),
]

HERO_NAMES = ["iara", "thalia", "selene", "lyra", "dione", "nysa"]
TRAITS = ["brave", "curious", "gentle", "stubborn", "lively", "bold"]


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
    "rain": [("What is rain?", "Rain is water that falls from clouds in the sky.")],
    "wind": [("What is wind?", "Wind is moving air that can make leaves dance and flags flutter.")],
    "sparks": [("What are sparks?", "Sparks are tiny glowing bits that jump from fire or struck metal.")],
    "cloak": [("What is a cloak?", "A cloak is a loose outer garment that hangs over your clothes.")],
    "wreath": [("What is a wreath?", "A wreath is a circle made of flowers, leaves, or other woven things.")],
    "torch": [("What is a torch?", "A torch is a stick with a burning top that gives light.")],
    "wet": [("Why does wet cloth feel heavy?", "Wet cloth feels heavy because it holds water in its fibers.")],
    "singed": [("What does singed mean?", "Singed means brushed by heat or flame so the edge is scorched.")],
    "dusty": [("What does dusty mean?", "Dusty means covered with fine dry powder or dirt.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, act, prize = f["hero"], f["elder"], f["activity"], f["prize"]
    return [
        f'Write a short myth for a child about {hero.id}, a {hero.type} who wants to {act.verb}, and a {prize.label} that must stay safe.',
        f"Tell a gentle mythic story where {hero.id} and {elder.label} must find a safer way to {act.verb} without ruining {prize.phrase}.",
        f'Write a simple myth with old stones, {act.keyword}, and a careful compromise that keeps the {prize.label} clean.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, act = f["hero"], f["elder"], f["prize"], f["activity"]
    qa = [
        QAItem(
            question=f"Who was the story about in the shrine court?",
            answer=f"It was about {hero.id}, a little {next((t for t in hero.traits if t != 'little'), 'young')} {hero.type}, and {elder.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {act.verb} in the old place where the story happened.",
        ),
        QAItem(
            question=f"What treasured thing did {hero.id} wear that could get ruined?",
            answer=f"{hero.id} wore {prize.phrase}, which could be harmed by the magic.",
        ),
    ]
    if f.get("conflict"):
        qa.append(QAItem(
            question=f"Why did {elder.label} warn {hero.id}?",
            answer=f"{elder.label} warned {hero.id} because if {hero.id} tried to {act.verb}, the {prize.label} would get {act.soil} and lose its beauty.",
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the two of them solve the problem?",
            answer=f"They used {gear.label} so {hero.id} could still {act.verb} while the {prize.label} stayed safe.",
        ))
        qa.append(QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt happy and calm, and the end of the story shows {hero.id} still able to {act.gerund} with {elder.label} nearby.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    if world.facts["prize"].label in KNOWLEDGE:
        tags.add(world.facts["prize"].label)
    out: list[QAItem] = []
    for key in ["rain", "wind", "sparks", "cloak", "wreath", "torch", "wet", "singed", "dusty"]:
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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


CURATED = [
    StoryParams(place="shrine", activity="rain", prize="cloak", name="iara", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="hill", activity="wind", prize="wreath", name="lyra", gender="girl", parent="father", trait="curious"),
    StoryParams(place="shrine", activity="sparks", prize="torch", name="thalia", gender="girl", parent="mother", trait="lively"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not threaten the {prize.label}.)"
    return f"(No story: no gear in this world both guards {activity.mess} and fits the {prize.label}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(PRIZES[prize_id].genders))
    return f"(No story: a {PRIZES[prize_id].label} isn't a typical {gender}'s item here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic coarse-magic story world.")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


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
            print(f"  {place:8} {act:8} {prize:8}  [{', '.join(genders)}]")
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
