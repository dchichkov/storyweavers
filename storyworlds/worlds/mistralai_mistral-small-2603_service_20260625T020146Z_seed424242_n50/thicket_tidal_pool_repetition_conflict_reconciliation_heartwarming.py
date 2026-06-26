#!/usr/bin/env python3
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
MESS_KINDS = {"tangled", "slimy"}
REGIONS = {"tide_pool"}

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
        female = {"girl", "keeper", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"keeper": "keeper", "father": "father"}.get(self.type, self.type)

@dataclass
class Setting:
    place: str = "the tidal pool thicket"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
    tide_rhythm: str = "ebb and flood"

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
        self.facts: dict = {'repetitions': 0, 'tension': 0}

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
        return any(g.protective and region in g.covers
                   for g in self.worn_items(actor))

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
        clone.fired = self.fired.copy()
        clone.facts = self.facts.copy()
        clone.paragraphs = [[]]
        return clone

@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_tangle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["tangled"] < THRESHOLD:
            continue
        sig = ("tangle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["tension"] += 0.5
        out.append(
            f"{actor.pronoun('subject').capitalize()} wriggled deeper into the thicket "
            f"and the swirling seaweed held {actor.pronoun('object')} tightly."
        )
    return out

def _r_fear(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["fear"] < THRESHOLD:
            continue
        sig = ("fear", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.facts["tension"] += 1.0
        return ["__tension__"]
    return []

CAUSAL_RULES: list[Rule] = [
    Rule(name="tangle", tag="physical", apply=_r_tangle),
    Rule(name="fear", tag="emotional", apply=_r_fear),
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
                produced.extend(s for s in sents if s != "__tension__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced

def predict_risk(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "tangled": bool(prize and prize.meters["tangled"] >= THRESHOLD),
        "severity": sum(e.memes.get("fear", 0) for e in sim.characters()),
    }

def setting_detail(setting: Setting, activity: Activity) -> str:
    details = []
    if activity.weather == "misty":
        details.append("The mist curled low over the water like a soft blanket.")
    if setting.tide_rhythm == "ebb and flood":
        details.append("Waves lapped gently at the edges of the thicket.")
    return " ".join(details)

def prize_was_safe(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive').capitalize()} {prize.label} remained unharmed"

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = activity.zone
    actor.meters[activity.mess] += 0.2
    actor.memes["determination"] += 0.3
    world.facts["repetitions"] += 1
    propagate(world, narrate=narrate)

def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    desc = f"little {trait} {hero.type}"
    world.say(
        f"{hero.id} was a {desc} who loved the quiet murmur of the tidal pool. "
        f"The thicket beckoned like a secret waiting to be found."
    )

def loves_spot(world: World, hero: Entity) -> None:
    hero.memes["awe"] += 1.0
    where = world.setting.place
    world.say(
        f"{hero.pronoun().capitalize()} loved scouting the edge of {where}. "
        f"Every rock and crevice told a story the {hero.type} was sure to understand."
    )

def buys_gift(world: World, adult: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"That morning, {adult.id} slipped {prize.phrase} into {hero.pronoun('possessive')} pack "
        f"before they left for {world.setting.place}."
    )

def arrives(world: World, hero: Entity, adult: Entity) -> None:
    day_note = {"misty": "misty dawn", "calm": "calm afternoon"}.get(world.weather, "sunlit morning")
    world.say(
        f"On a {day_note}, {hero.id} and {adult.id} made their way to {world.setting.place}. "
        f"The tide was {world.setting.tide_rhythm}."
    )
    world.say(setting_detail(world.setting, ACTIVITIES["explore"]))

def warns(world: World, adult: Entity, hero: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_risk(world, hero, activity, prize.id)
    if not (activity.mess in ("tangled", "slimy") and pred.get("severity", 0) >= 0.7):
        return False
    world.facts["predicted_risk"] = activity.soil
    world.facts["risk_level"] = min(1.0, pred["severity"] * 0.5)
    clause = f"You could get {prize.phrase} {activity.soil} in that thicket"
    world.say(f'"{clause}," {adult.id} cautioned, "and then we\’d need a long cleanup."')
    return True

def tries_again(world: World, hero: Entity, activity: Activity) -> None:
    world.facts["repetitions"] += 1
    hero.memes["determination"] += 0.5
    rep = world.facts["repetitions"]
    world.say(
        f"{hero.id} could almost see the {activity.keyword} through the green strands. "
        f"Once more {hero.pronoun()} gathered {hero.pronoun('possessive')} courage."
    )
    if rep > 3:
        hero.meters["tangled"] += 0.3
        world.say(
            f"The thicket seemed to tighten around {hero.pronoun('object')} with every step."
        )

def offers_gear(world: World, adult: Entity, hero: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = None
    for g in GEAR:
        if activity.mess in g.guards and "tide_pool" in g.covers:
            gear_def = g
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=f"{gear_def.id}_{hero.id}", type="gear", label=gear_def.label,
        owner=hero.id, caretaker=adult.id, region="tide_pool",
        protective=True, covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    sim = world.copy()
    _do_activity(sim, sim.get(hero.id), activity, narrate=False)
    if sim.entities[gear.id].meters.get(activity.mess, 0) < THRESHOLD:
        world.say(
            f"{adult.id} held out {gear_def.label}. \"Use this to part the thicket gently.\""
        )
        return gear_def
    gear.worn_by = None
    del world.entities[gear.id]
    return None

def grasps_hand(world: World, adult: Entity, hero: Entity) -> None:
    hero.memes["fear"] += 0.8
    propagate(world, narrate=False)
    world.say(
        f"{adult.pronoun('subject').capitalize()} reached for {hero.pronoun('possessive')} hand. "
        f'\"Come back to the path,\" {adult.pronoun()} urged softly.'
    )

def pouts(world: World, hero: Entity) -> None:
    if hero.memes.get("determination", 0) > 0.8:
        world.say(
            f'{hero.id} crossed {hero.pronoun("possessive")} arms. '
            f'"I almost had it! I will try once more!"'
        )

def reconciles(world: World, adult: Entity, hero: Entity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["relief"] = 1.0
    hero.memes["trust"] = 1.0
    hero.memes["determination"] = 0.0
    adult.memes["pride"] = 1.0
    where = world.setting.place
    world.say(
        f'"With care, " {adult.id} coached, "and a bit of patience, '
        f'{hero.pronoun()} found the {prize.label}."'
    )
    world.say(
        f"{hero.id} emerged with {prize.phrase}, its colors shimmering from the mist. "
        f"`Look, {adult.pronoun('object')}’," {hero.id} whispered. "
        f"You were right — the thicket has gifts for those who listen.`"
    )

def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Leo", hero_type: str = "boy",
         hero_traits: Optional[list[str]] = None,
         adult_type: str = "keeper",
         adult_name: str = "Mira") -> World:
    world = World(setting)
    world.weather = setting.indoor and "indoor" or "misty"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["stubborn", "inquisitive"]),
    ))
    adult = world.add(Entity(
        id=adult_name, kind="character", type=adult_type,
        label=adult_name, traits=["patient"],
    ))
    prize = world.add(Entity(
        id="voyager_shell", type=prize_cfg.type,
        label=prize_cfg.label, phrase=prize_cfg.phrase,
        region=prize_cfg.region, plural=prize_cfg.plural,
        caretaker=adult.id,
    ))

    introduce(world, hero)
    loves_spot(world, hero)
    buys_gift(world, adult, hero, prize)
    world.para()
    arrives(world, hero, adult)
    tries_again(world, hero, activity)
    warns(world, adult, hero, activity, prize)
    grasps_hand(world, adult, hero)
    world.para()
    pouts(world, hero)
    gear_def = offers_gear(world, adult, hero, activity, prize)
    if gear_def:
        reconciles(world, adult, hero, prize, gear_def)

    world.facts.update(
        hero=hero, adult=adult, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting, gear=gear_def,
        resolved=gear_def is not None,
    )
    return world

SETTINGS = {
    "tidal_pool_thicket": Setting(
        place="the tidal pool thicket",
        indoor=False,
        affords={"explore", "collect"},
        tide_rhythm="ebb and flood",
    ),
    "sea_cave": Setting(
        place="a sheltered sea cave",
        indoor=True,
        affords={"collect"},
        tide_rhythm="gentle current",
    ),
}

ACTIVITIES = {
    "explore": Activity(
        id="explore",
        verb="explore the thicket",
        gerund="exploring the thicket",
        rush="dash into the thicket",
        mess="tangled",
        soil="trapped in seaweed",
        zone={"tide_pool"},
        weather="misty",
        keyword="thicket",
        tags={"thicket", "tide", "exploration"},
    ),
    "search": Activity(
        id="search",
        verb="search for shells",
        gerund="searching for shells",
        rush="hurry along the rocks",
        mess="slimy",
        soil="covered in barnacles",
        zone={"tide_pool"},
        weather="misty",
        keyword="shells",
        tags={"shell", "tide", "collection"},
    ),
}

PRIZES = {
    "shell": Prize(
        label="shell",
        phrase="small turquoise shell",
        type="shell",
        region="tide_pool",
        genders={"girl", "boy"},
    ),
    "message": Prize(
        label="message",
        phrase="message in a bottle",
        type="bottle",
        region="tide_pool",
        plural=False,
    ),
    "pebble": Prize(
        label="pebble",
        phrase="smooth storytelling pebble",
        type="pebble",
        region="tide_pool",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="stick",
        label="a sturdy stick",
        covers={"tide_pool"},
        guards={"tangled"},
        prep="find a long stick to part the thicket",
        tail="handed the stick to {hero}",
        plural=False,
    ),
    Gear(
        id="net",
        label="small net",
        covers={"tide_pool"},
        guards={"slimy"},
        prep="grab a net to scoop without touching",
        tail="offered the net to {hero}",
        plural=False,
    ),
    Gear(
        id="gloves",
        label="thick gloves",
        covers={"tide_pool"},
        guards={"tangled", "slimy"},
        prep="put on these waterproof gloves",
        tail="brought along the gloves",
        plural=False,
    ),
]

NAMES_GIRL = ["Luna", "Mara", "Tessa", "Niamh", "Saoirse"]
NAMES_BOY = ["Leo", "Finn", "Cian", "Oisin", "Sol"]
TRAITS = ["inquisitive", "patient", "stonesetter", "tide-watcher"]

def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return "tide_pool" == prize.region

def compatible_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            return g
    return None

def valid_explores() -> list[tuple[str, str]]:
    valid = []
    for place_id, setting in SETTINGS.items():
        if "explore" not in setting.affords:
            continue
        act = ACTIVITIES["explore"]
        for prize_id, prize in PRIZES.items():
            if prize_at_risk(act, prize) and compatible_gear(act, prize):
                valid.append((place_id, prize_id))
    return valid

KNOWLEDGE = {
    "thicket": [
        ("What is a tidal pool thicket?",
         "A tidal pool thicket is a dense patch of seaweed and green plants "
         "trapped between tide rocks where small creatures hide."),
    ],
    "tangled": [
        ("Why does seaweed tangle people?",
         "Seaweed swirls gently with each wave but grips tight when grabbed; "
         "pulling only makes it tighter until the green strands are let loose."),
    ],
    "shell": [
        ("What makes a shell special?",
         "A shell collects the music of the waves; the clear turquoise kind "
         "often holds tiny echoes of sea storms inside."),
    ],
    "mist": [
        ("Why does mist make places peaceful?",
         "Mist softens edges and wraps the world in quiet, letting the mind notice "
         "things it would otherwise rush past."),
    ],
    "reconciliation": [
        ("What does reconciliation mean?",
         "Reconciliation is how people find gentle paths past disagreements — "
         "not giving up a hope but sharing a way to reach it."),
    ],
}
KNOWLEDGE_ORDER = ["thicket", "tangled", "shell", "mist", "reconciliation"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, adult, act = f["hero"], f["adult"], f["activity"]
    kw = act.keyword or "thicket"
    sub = hero.pronoun("subject")
    return [
        f'Write a heartwarming 3-to-5 year old tale about a {hero.type} who loves '
        f'{hero.pronoun("possessive")} quiet tidal place and one special gift inside '
        f'a tangled thicket.',
        f'A simple story where {hero.id} keeps trying to reach something in a '
        f'misty{kw[-5:]} and {adult.id} shows {hero.pronoun("object")} how to do it '
        f'gently; ends with both smiling by the water.',
        f'Create a gentle tale of repetition and patient caring around the tide '
        f'that rewards listening carefully.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, adult, prize, act = f["hero"], f["adult"], f["prize"], f["activity"]
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    what = "misty" if world.weather == "misty" else "quiet"
    kw = act.keyword or "thicket"
    qa: list[QAItem] = [
        QAItem(
            question=(
                f"Who went to {world.setting.place} and what did {hero.id} "
                f"{act.gerund}?"
            ),
            answer=(
                f"{hero.id.capitalize()} ventured to {world.setting.place} on a {what} "
                f"morning and longed to {act.verb}. {adult.id} accompanied "
                f"{hero.pronoun('object')} along the water's edge."
            ),
        ),
        QAItem(
            question=(
                f"Why did {hero.id} want {prize.phrase} so badly?"
            ),
            answer=(
                f"{sub.capitalize()} had spent many peaceful hours by the water and "
                f"was sure the {kw} held a secret {prize.label} for {obj}."
            ),
        ),
    ]
    if f.get("resolved"):
        gear = f["gear"]
        qa.extend([
            QAItem(
                question="How did the thicket finally let the child reach the prize?",
                answer=(
                    f"{adult.id} suggested using {gear.label} to part the strands gently. "
                    f"Once {hero.pronoun()} listened, {sub} could see and touch the "
                    f"{prize.label} without struggle."
                ),
            ),
            QAItem(
                question=(
                    f"How did {hero.id} feel after finding the {prize.label}?"
                ),
                answer=(
                    f"{hero.id} felt relieved and proud. {sub.capitalize()} thanked "
                    f"{adult.id} for teaching {hero.pronoun()} the calm way to explore."
                ),
            ),
        ])
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out

def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Storytelling prompts that would generate this tale =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions — grounded in the text you just read ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions — no story needed ===")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    lines.append(f"  facts: repetitions={world.facts.get('repetitions', 0):.1f} "
                 f"tension={world.facts.get('tension',0):.1f}")
    return "\n".join(lines)

CURATED = [
    StoryParams(
        place="tidal_pool_thicket",
        activity="explore",
        prize="shell",
        name="Leo",
        gender="boy",
        parent="keeper",
        trait="stonesetter",
    ),
    StoryParams(
        place="tidal_pool_thicket",
        activity="search",
        prize="pebble",
        name="Luna",
        gender="girl",
        parent="keeper",
        trait="tide-watcher",
    ),
]

ASP_RULES = r"""
% A prize is safe when its holder does not risk tangling.
safe(Prize) :- prize(Prize), region(Prize,"tide_pool").

% You may reach when the activity's guard neutralises potential mess.
may_reach(Act, Prize) :- activity(Act), prize(Prize),
                         mess_of(Act,M), guards_gear(G,M),
                         covers_gear(G,R), region(Prize,R).

% The story is valid when the child and the guide find a shared gentle path.
valid_story(Place, Prize, Name, Gender) :-
    setting(Place), prize(Prize), person(Name,Gender),
    affords(Place,"explore"), may_reach("explore", Prize).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards_gear", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers_gear", g.id, r))
    names = [(n, "girl") for n in NAMES_GIRL] + [(n, "boy") for n in NAMES_BOY]
    for name, gender in names:
        lines.append(asp.fact("person", name, gender))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

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

def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))

def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(
        (p.place, p.prize, p.name, p.gender) for p in CURATED
    )
    if clingo_set == python_set:
        print("OK: ASP gate matches curated set."
              f" ({len(clingo_set)} valid stories verified).")
        return 0
    print("ASP <> Python mismatch detected.\nCLINGO:", sorted(clingo_set))
    print("PYTHON:", sorted(python_set))
    return 1

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tidal thicket tales: heartwarming stories of repetition, "
                    "conflict, and reconciliation in tidal pools.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["keeper", "father"])
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
        if not (prize_at_risk(act, pr) and compatible_gear(act, pr)):
            msg = "The thicket’s seaweed would trap the prize "
            if pr.region != "tide_pool":
                msg += f"(prize sits on {pr.region}, but thicket mess affects tide_pool). "
            else:
                msg += "(gear cannot prevent the mess). "
            msg += "Try prized item near the water or a sturdier tool."
            raise StoryError(msg)

    choices = [
        p for p in valid_explores()
        if (args.place is None or p[0] == args.place)
        and (args.prize is None or p[1] == args.prize)
    ]
    if not choices:
        raise StoryError('No valid thicket story matches options.')

    place, prize_id = rng.choice(choices)
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or (
        rng.choice(NAMES_GIRL) if gender == "girl" else rng.choice(NAMES_BOY)
    )
    parent = args.parent or rng.choice(["keeper", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity="explore" if args.activity is None else args.activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        "boy" if params.gender == "boy" else "girl",
        [params.trait, "curious"],
        "keeper" if params.parent == "keeper" else "father",
        "Mira" if params.parent == "keeper" else "Finn",
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
        triples = asp_valid_stories()
        print(f"Tidal pool treasure trove: {len(triples)} heartwarming thicket quests\n")
        for place, prize, name, gender in triples:
            print(f"  • {name} the {gender} searches {PRIZES[prize].phrase} at "
                  f"{SETTINGS[place].place}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            key = sample.story.strip()
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples],
                            indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples, 1):
        header = ""
        if args.all:
            p = sample.params
            prize_phrase = PRIZES[p.prize].phrase
            header = f"### Quest {idx}: {p.name} seeks {prize_phrase} at {p.place}"
        elif len(samples) > 1:
            header = f"### Variant {idx}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples):
            print("\n" + "=" * 72 + "\n")

if __name__ == "__main__":
    main()
