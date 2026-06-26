#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/burro_mister_magenta_bad_ending_comedy.py
========================================================================================================================

A comedy storyworld with a bad ending.  A child named Magenta, a burro, and a parent
named Mister.  The child loves painting everything magenta.  The parent tries to protect
a prized hat, but the burro's mischief and a series of silly compromises lead to a
hilarious mess where the hat is lost forever and everyone is covered in magenta paint.
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
from results import QAItem, StoryError, StorySample

THRESHOLD = 1.0
MESS_KINDS = {"magenta", "painted", "sticky", "silly"}

# ---------------------------------------------------------------------------
# Entity model
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
        if self.type in {"girl", "mother", "mom", "woman", "child", "Magenta"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "Mister"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)

# ---------------------------------------------------------------------------
# Dataclasses for domain knobs
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the farm"
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
    genders: set[str] = field(default_factory=lambda: {"girl", "boy", "Magenta"})

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

    def copy(self) -> World:
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules (comedy bad ending)
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_spread_paint(world: World) -> list[str]:
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
                sig = ("paint", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["dirty"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got covered in magenta paint."
                )
    return out

def _r_burro_mischief(world: World) -> list[str]:
    """If the burro exists and the child is misbehaving, the burro steals the prize."""
    out: list[str] = []
    burro = world.entities.get("burro")
    if burro is None:
        return out
    for actor in world.characters():
        if actor.memes["defiance"] >= THRESHOLD and actor.memes["grabbed_by"] >= THRESHOLD:
            sig = ("burro_steal", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            prize = world.entities.get("prize")
            if prize and prize.worn_by == actor.id:
                prize.worn_by = None
                prize.owner = "burro"
                burro.memes["tricks"] += 1
                out.append(
                    f"Suddenly the burro trotted over, snatched {actor.pronoun('possessive')} "
                    f"{prize.label}, and galloped toward the barn with it."
                )
    return out

def _r_bad_ending(world: World) -> list[str]:
    """If the prize is lost and no gear was used, everything turns magenta in a silly finale."""
    out: list[str] = []
    prize = world.entities.get("prize")
    if prize is None or prize.worn_by is not None:
        return out
    # Check if the child ever tried to do the activity without protection
    for actor in world.characters():
        if actor.memes["defiance"] >= THRESHOLD and actor.memes["joy"] < THRESHOLD:
            sig = ("bad_ending", actor.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            out.append(
                f"With the {prize.label} gone and no safe plan, the magenta paint "
                f"splattered everywhere. {actor.pronoun().capitalize()} ended up "
                f"completely magenta from head to toe. Mister sighed and said, "
                f"\"Well, that's a bad ending.\" The burro brayed with laughter."
            )
    return out

CAUSAL_RULES: list[Rule] = [
    Rule(name="spread_paint", tag="physical", apply=_r_spread_paint),
    Rule(name="burro_mischief", tag="social", apply=_r_burro_mischief),
    Rule(name="bad_ending", tag="plot", apply=_r_bad_ending),
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
# Constraint helpers – bad ending is inevitable if the child ignores warnings.
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone

def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None

# ---------------------------------------------------------------------------
# Storytelling verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity, burro: Entity, mister: Entity) -> None:
    world.say(
        f"{child.id} was a little {child.type} who loved bright colors, especially magenta. "
        f"The burro, who was always full of mischief, lived in the barn. "
        f"{mister.id} was {child.pronoun('possessive')} doting parent."
    )

def loves_activity(world: World, child: Entity, activity: Activity) -> None:
    child.memes["love_play"] += 1
    world.say(
        f"{child.pronoun().capitalize()} loved {activity.gerund}; the way the color "
        f"magenta turned everything into a magical mess made {child.pronoun('object')} giggle."
    )

def buys_prize(world: World, mister: Entity, child: Entity, prize: Prize) -> None:
    world.say(
        f"One day, {mister.id} bought {child.pronoun('object')} {prize.phrase}. "
        f"{child.pronoun().capitalize()} adored {prize.it()} and wore {prize.it()} everywhere."
    )

def arrive(world: World, child: Entity, mister: Entity, activity: Activity) -> None:
    world.say(
        f"When the sun was high, {child.id} and {mister.id} went to {world.setting.place}. "
        f"The burro watched from the fence, twitching {child.pronoun('possessive')} ears."
    )

def wants(world: World, child: Entity, mister: Entity, activity: Activity) -> None:
    child.memes["desire"] += 1
    world.say(
        f"{child.id} wanted to {activity.verb} right away, but {mister.id} shook {child.pronoun('possessive')} head."
    )

def warn(world: World, mister: Entity, child: Entity, activity: Activity, prize: Prize) -> bool:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_workload"] = pred["workload"]
    clause = f"You'll ruin your {prize.label} with that magenta paint"
    if pred["workload"] >= THRESHOLD:
        clause += ", and then I'll have to clean it up"
    world.say(f'"{clause}," {mister.id} said. "Let\'s think of a safer plan."')
    return True

def defies(world: World, child: Entity, activity: Activity) -> None:
    child.memes["defiance"] += 1
    world.say(
        f"{child.id} didn't want to wait. {child.pronoun().capitalize()} tried to {activity.rush}."
    )

def grab_hand(world: World, mister: Entity, child: Entity, activity: Activity) -> None:
    child.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    world.say(
        f"but {mister.id} grabbed {child.pronoun('possessive')} hand and said, "
        f"\"We can still have fun, but let's be careful.\""
    )

def pout(world: World, child: Entity, activity: Activity) -> None:
    if child.memes["defiance"] >= THRESHOLD:
        world.say(
            f'{child.id} pouted. "But I want to paint everything magenta NOW!"'
        )

def compromise(world: World, mister: Entity, child: Entity, activity: Activity,
               prize: Prize) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=child.id, caretaker=mister.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = child.id
    if predict_mess(world, child, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{mister.id} looked at the {prize.label}, then at the burro, and smiled. '
        f'"How about we {gear_def.prep} and then {activity.verb} together?"'
    )
    return gear_def

def accept(world: World, mister: Entity, child: Entity, activity: Activity, prize: Prize,
           gear_def: Gear) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id}'s face lit up. \"Yay!\" {child.pronoun()} said, and they "
        f"{gear_def.tail}. Soon {child.id} was {activity.gerund}, "
        f"and {mister.id} laughed. But the burro had other plans..."
    )

def bad_ending_finale(world: World, child: Entity, mister: Entity, burro: Entity, prize: Prize) -> None:
    world.say(
        f"The burro, still holding the {prize.label} in its teeth, trotted into "
        f"the magenta puddle. Paint splashed everywhere. "
        f"{child.pronoun().capitalize()} was now completely magenta. "
        f"{mister.id}'s clothes were ruined. The burro brayed and disappeared "
        f"into the barn with the {prize.label}. "
        f"{mister.id} sighed. \"Well, that's a bad ending.\""
    )

# ---------------------------------------------------------------------------
# Prediction helper
# ---------------------------------------------------------------------------
def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "soiled": bool(prize and prize.meters["dirty"] >= THRESHOLD),
        "workload": sum(e.meters["workload"] for e in sim.characters()),
    }

def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)

# ---------------------------------------------------------------------------
# Tell the story (always a bad ending comedy)
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         child_name: str = "Magenta", parent_name: str = "Mister") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    child = world.add(Entity(
        id=child_name, kind="character", type="child",
        traits=["little", "playful", "stubborn"],
    ))
    mister = world.add(Entity(
        id=parent_name, kind="character", type="Mister", label="the parent"
    ))
    burro = world.add(Entity(
        id="burro", kind="character", type="burro", label="the burro",
        traits=["mischievous"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=child.id, caretaker=mister.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1: setup
    introduce(world, child, burro, mister)
    loves_activity(world, child, activity)
    buys_prize(world, mister, child, prize)

    # Act 2: conflict – child wants to paint, Mister warns, child defies, burro steals
    world.para()
    arrive(world, child, mister, activity)
    wants(world, child, mister, activity)
    warn(world, mister, child, activity, prize)
    defies(world, child, activity)
    grab_hand(world, mister, child, activity)

    # Act 3: attempted compromise and bad ending
    world.para()
    pout(world, child, activity)
    gear_def = compromise(world, mister, child, activity, prize)
    if gear_def:
        accept(world, mister, child, activity, prize, gear_def)
    else:
        # No gear, burro steals and bad ending ensues
        # Manually trigger burro mischief and bad ending
        child.memes["defiance"] = THRESHOLD
        child.memes["grabbed_by"] = THRESHOLD
        propagate(world, narrate=True)
    # Force the bad ending finale
    if prize.worn_by is None or gear_def is None:
        bad_ending_finale(world, child, mister, burro, prize)
    else:
        # Even with gear, the burro still creates a mess for comedy
        world.say("But the burro kicked the paint bucket, and everything went magenta anyway!")
        bad_ending_finale(world, child, mister, burro, prize)

    world.facts.update(
        child=child, parent=mister, burro=burro, prize=prize,
        prize_cfg=prize_cfg, activity=activity, setting=setting,
        gear=gear_def,
        conflict=child.memes["grabbed_by"] >= THRESHOLD,
        resolved=gear_def is not None
    )
    return world

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "farm": Setting(place="the farm", indoor=False, affords={"paint_magenta"}),
    "barn": Setting(place="the barn", indoor=True, affords={"paint_magenta"}),
    "yard": Setting(place="the yard", indoor=False, affords={"paint_magenta"}),
}

ACTIVITIES = {
    "paint_magenta": Activity(
        id="paint_magenta",
        verb="paint everything magenta",
        gerund="painting everything magenta",
        rush="dip the brush into the magenta paint",
        mess="magenta",
        soil="covered in magenta paint",
        zone={"torso", "legs"},
        keyword="magenta",
        tags={"magenta", "paint", "mess"},
    ),
}

PRIZES = {
    "hat": Prize(label="hat", phrase="a splendid magenta hat",
                 type="hat", region="torso", genders={"Magenta"}),
    "shirt": Prize(label="shirt", phrase="a clean white shirt",
                   type="shirt", region="torso", genders={"Magenta"}),
    "scarf": Prize(label="scarf", phrase="a soft blue scarf",
                   type="scarf", region="torso", genders={"Magenta"}),
}

GEAR = [
    Gear(id="apron", label="a magenta-proof apron",
         covers={"torso"}, guards={"magenta", "painted"},
         prep="put on the magenta-proof apron",
         tail="put on the apron", plural=False),
    Gear(id="poncho", label="a plastic poncho",
         covers={"torso", "legs"}, guards={"magenta", "painted", "sticky"},
         prep="wrap up in the plastic poncho",
         tail="grabbed the poncho", plural=False),
]

GIRL_NAMES = ["Magenta"]
BOY_NAMES = ["Magenta"]
TRAITS = ["playful", "curious", "stubborn", "cheerful", "spirited", "lively"]

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
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None

# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "magenta": [("What color is magenta?",
                 "Magenta is a bright pinkish-purple color. It is very bold and fun.")],
    "paint": [("Why does paint get on clothes so easily?",
               "Paint is a liquid, so it can drip and splash. When it dries, it sticks to fabric.")],
    "burro": [("What is a burro?",
               "A burro is a small donkey. They are often playful and sometimes mischievous.")],
}
KNOWLEDGE_ORDER = ["magenta", "paint", "burro"]

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, parent, act, prize_cfg = f["child"], f["parent"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short comedy story about a child named {child.id}, a parent named {parent.id}, '
        f'and a mischievous burro, where a love for {act.gerund} leads to a bad ending.',
        f"Tell a funny tale where everyone ends up covered in magenta paint because of a burro's trick.",
        f'A story that uses the word "{act.keyword}" and has a silly, chaotic ending.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, prize, act = f["child"], f["parent"], f["prize"], f["activity"]
    sub, obj, pos = child.pronoun("subject"), child.pronoun("object"), child.pronoun("possessive")
    qa: list[QAItem] = [
        QAItem(
            question=f"Who tried to {act.verb} at {world.setting.place}?",
            answer=f"{child.id} wanted to {act.verb}. {parent.id} tried to stop {obj}."
        ),
        QAItem(
            question=f"What did the burro do with {pos} {prize.label}?",
            answer=f"The burro snatched {pos} {prize.label} and ran away with it."
        ),
    ]
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"Everyone ended up covered in magenta paint, and the burro kept the {prize.label}. "
               f"It was a silly, bad ending."
    ))
    return qa

def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out = []
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
# CLI / trace
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)

CURATED = [
    StoryParams(place="farm", activity="paint_magenta", prize="hat",
                name="Magenta", parent="Mister", trait="playful"),
    StoryParams(place="barn", activity="paint_magenta", prize="shirt",
                name="Magenta", parent="Mister", trait="curious"),
]

def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} splashes {sorted(activity.zone)}, "
                f"but {noun} sits on the {prize.region}. Not plausible.)")
    return (f"(No story: no gear protects {noun} from {activity.gerund}.)")

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
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1

# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Burro, Mister, Magenta – a comedy with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    prize = PRIZES[prize_id]
    name = args.name or "Magenta"
    parent = "Mister"
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, parent=parent, trait=trait,
    )

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:9} {act:8} {prize:8}")
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
```
