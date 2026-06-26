#!/usr/bin/env python3
"""
storyworlds/worlds/spread_mystery.py
====================================

A standalone storyworld script about a child solving the mystery of a spreading
mess.  The seed word "spread" drives the core mechanic: a stain, footprint, or
spill spreads across a cherished item until the child finds the cause.
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
MESS_KINDS = {"inky", "muddy", "sticky"}
REGIONS = {"feet", "legs", "torso"}


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
        female = {"girl", "mother", "mom", "woman"}
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Parametrization
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the playroom"
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    """The messy event that spreads mysteriously."""
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
    """The item the child loves that gets stained."""
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    """Protective clothing that allows safe investigation."""
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
        self.clue_found: bool = False

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
        clone.clue_found = self.clue_found
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


def _r_spread(world: World) -> list[str]:
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
                sig = ("spread", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 0.5
                item.meters["dirty"] += 0.5
                out.append(
                    f"The {item.label} was getting {mess} — the mess was spreading."
                )
    return out


def _r_clue_found(world: World) -> list[str]:
    """When child's investigation reaches threshold, a clue is discovered."""
    for actor in world.characters():
        if actor.memes["investigation"] >= THRESHOLD and not world.clue_found:
            world.clue_found = True
            world.facts["clue"] = actor.facts.get("clue_source", "the source")
            return [f"Then {actor.id} spotted {world.facts['clue']}."]
    return []


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


CAUSAL_RULES: list[Rule] = [
    Rule(name="spread", tag="physical", apply=_r_spread),
    Rule(name="clue_found", tag="social", apply=_r_clue_found),
    Rule(name="workload", tag="physical", apply=_r_workload),
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
# Reasonableness helpers
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


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
# Screenplay
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "leak": "the tiny blue spot looked like a secret",
        "mud": "the brown footprints told a little story",
        "spill": "the sticky circle sparkled in the light",
    }.get(activity.id, "it made the room feel like a puzzle")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was cozy, and the carpet waited below."
    return f"{setting.place.capitalize()} looked full of possibilities."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved solving small mysteries.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and "
        f"wore {prize.it()} every chance {hero.pronoun()} got."
    )


def find_mystery(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(
        f"One morning, {hero.id} noticed something odd. "
        f"On {hero.pronoun('possessive')} {prize.label} there was a {activity.mess} spot "
        f"that seemed to be growing. 'How did that get there?' {hero.pronoun()} wondered."
    )
    world.say(
        f"The {activity.keyword} began to spread across the {prize.label}."
    )
    hero.memes["curiosity"] += 1
    prize.meters[activity.mess] += 0.5


def investigate(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"{hero.id} decided to be a detective. {hero.pronoun().capitalize()} looked "
        f"around the {world.setting.place.removeprefix('the ')} for clues."
    )
    hero.memes["investigation"] += 1
    world.facts["clue_source"] = "a leaky pen in the drawer" if activity.id == "leak" \
        else "a muddy paw print by the door" if activity.id == "mud" \
        else "the spilled juice cup on the table"


def warn(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    pred = {"soiled": prize.meters["dirty"] >= THRESHOLD}
    if not pred["soiled"]:
        return
    world.say(
        f'"{hero.pronoun("possessive").capitalize()} {prize.label} is getting really '
        f'{activity.soil}," {parent.label_word} said. "We need to find the cause '
        f'before the mess spreads more."'
    )
    world.facts["predicted_soil"] = activity.soil


def find_clue(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    clue = world.facts["clue_source"]
    world.say(
        f"After more searching, {hero.id} found {clue}. "
        f'"Aha! That\'s the source!" {hero.pronoun()} exclaimed.'
    )
    hero.memes["joy"] += 1


def compromise(world: World, parent: Entity, hero: Entity, prize: Entity, activity: Activity) -> Optional[Gear]:
    gear_def = select_gear(activity, PRIZES[prize.type])  # hack: need prize_id
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=hero.id, caretaker=parent.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = hero.id
    world.say(
        f'"Let\'s put on {gear_def.label} first, then we can clean together '
        f'and solve this mystery," {parent.label_word} suggested.'
    )
    return gear_def


def resolve_and_clean(world: World, hero: Entity, parent: Entity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} and {parent.label_word} put on {gear_def.label} and carefully "
        f"cleaned the {prize.label}. The {world.facts['predicted_soil']} was gone!"
    )
    world.say(
        f"{hero.id} smiled. 'We solved the mystery of the spreading mess!' "
        f"{hero.pronoun().capitalize()} hugged {hero.pronoun('possessive')} {parent.label_word}."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Lily", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "determined"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))

    # Act 1 - setup
    introduce(world, hero)
    loves_prize(world, hero, prize)
    world.para()

    # Act 2 - mystery appears and spreads
    find_mystery(world, hero, parent, prize, activity)
    investigate(world, hero, parent, activity)
    warn(world, parent, hero, prize, activity)
    propagate(world)
    world.para()

    # Act 3 - clue found and resolution
    find_clue(world, hero, parent, activity)
    gear_def = compromise(world, parent, hero, prize, activity)
    if gear_def:
        resolve_and_clean(world, hero, parent, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       resolved=gear_def is not None)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"leak"}),
    "hallway": Setting(place="the hallway", indoor=True, affords={"mud"}),
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"spill"}),
    "garden": Setting(place="the garden", indoor=False, affords={"mud"}),
}

ACTIVITIES = {
    "leak": Activity(
        id="leak", verb="find the leaky marker", gerund="finding leaky markers",
        rush="search everywhere", mess="inky", soil="inky and dark",
        zone={"torso"}, weather="", keyword="ink", tags={"ink", "spread"},
    ),
    "mud": Activity(
        id="mud", verb="trace the muddy footprints", gerund="tracing muddy footprints",
        rush="follow the prints", mess="muddy", soil="muddy and wet",
        zone={"feet"}, weather="rainy", keyword="mud", tags={"mud", "spread"},
    ),
    "spill": Activity(
        id="spill", verb="find the spilled juice", gerund="finding spilled juice",
        rush="look around the table", mess="sticky", soil="sticky and stained",
        zone={"legs"}, weather="", keyword="juice", tags={"sticky", "spread"},
    ),
}

GEAR = [
    Gear(id="apron", label="a painting apron", covers={"torso"}, guards={"inky"},
         prep="put on the painting apron",
         tail="put on the apron and got the cleaning cloth"),
    Gear(id="boots", label="old rain boots", covers={"feet"}, guards={"muddy"},
         prep="put on old rain boots",
         tail="wore the boots and grabbed a mop"),
    Gear(id="playclothes", label="old play clothes", covers={"legs", "torso"},
         guards={"sticky", "muddy", "inky"},
         prep="go change into your old play clothes",
         tail="changed into play clothes and got a sponge"),
]

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a favorite white shirt", type="shirt", region="torso"),
    "socks": Prize(label="socks", phrase="colorful new socks", type="socks", region="feet", plural=True),
    "pants": Prize(label="pants", phrase="comfy blue pants", type="pants", region="legs", plural=True),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "determined", "playful", "brave", "clever"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "ink": [("What is ink?", "Ink is a colored liquid used in pens and markers. It can stain clothes."),
            ("Why does ink spread on fabric?", "The fibers in fabric soak up the liquid ink, making it spread like a tiny river.")],
    "mud": [("What is mud?", "Mud is wet dirt. It can leave footprints and stains.")],
    "sticky": [("Why are sticky spills hard to clean?", "Spills like juice have sugar that dries and glues the stain to the fabric.")],
    "spread": [("What does 'spread' mean in a mess?", "Spread means the mess gets bigger over time, like a drop of ink growing on a paper.")],
}
KNOWLEDGE_ORDER = ["ink", "mud", "sticky", "spread"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize_cfg"]
    kw = act.keyword or act.mess
    return [
        f'Write a short mystery story for a child about "{kw}" and solving a spreading mess.',
        f"Tell a gentle story where a {hero.type} named {hero.id} investigates a mysterious "
        f"{act.mess} on {hero.pronoun('possessive')} {prize.label} and cleans it with {parent.label_word}.",
        f"Write a simple story that includes the word '{kw}' and teaches how to solve a problem by looking for clues.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"), hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who found the mysterious {act.mess} on their {prize.label} in {place}?",
            answer=f"A little {trait} {hero.type} named {hero.id} found a {act.mess} spot "
                   f"on {pos} {prize.label} and decided to investigate.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find that solved the mystery of the spreading {act.keyword}?",
            answer=f"{hero.id} discovered {world.facts.get('clue', 'a hidden source')} after searching carefully.",
        ),
        QAItem(
            question=f"How did {hero.id} and {pw} clean the {prize.label} and stop the {act.keyword} from spreading?",
            answer=f"They used {world.facts['gear'].label if world.facts.get('gear') else 'a cloth'} "
                   f"and worked together to remove the {act.soil} mess.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
    lines.append("== (3) World-knowledge questions ==")
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


# ---------------------------------------------------------------------------
# Clingo ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P),
                   mess_of(A,M), guards(G,M),
                   covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,Gender) :- valid(Place,A,P), wears(Gender,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
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


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery of the spreading mess storyworld.")
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
            raise StoryError("Invalid combination.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError("Gender mismatch.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination.")
    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id,
                       name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait], params.parent)
    return StorySample(params=params, story=world.render(),
                       prompts=generation_prompts(world),
                       story_qa=story_qa(world),
                       world_qa=world_knowledge_qa(world),
                       world=world)


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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(f"  {t[0]:9} {t[1]:8} {t[2]:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        curated = [
            StoryParams(place="bedroom", activity="leak", prize="shirt",
                        name="Lily", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="hallway", activity="mud", prize="socks",
                        name="Max", gender="boy", parent="father", trait="determined"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### variant {i+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
