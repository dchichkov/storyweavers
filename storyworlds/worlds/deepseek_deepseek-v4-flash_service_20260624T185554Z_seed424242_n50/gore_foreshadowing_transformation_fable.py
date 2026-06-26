#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50/gore_foreshadowing_transformation_fable.py
=============================================================================================================================

A story world in the style of a fable: a child, a warning, a magical transformation.
Features gore (a small cut) and transformation (child becomes a butterfly) foreshadowed
by an owl's cryptic advice.

Domain model
============
- Entity: every being or object has physical (meters) and emotional (memes) dimensions.
- Activities: dancing on stones (causes blood), dancing safely (no blood).
- Injury leads to transformation when courage is high.
- The "gear" (sturdy shoes) prevents injury and avoids transformation.
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
MESS_KINDS = {"blood", "sweat"}

REGIONS = {"feet", "wings"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"               # "character" | "thing"
    type: str = "thing"               # girl, boy, owl, butterfly, shoes
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
        female = {"girl", "owl", "butterfly"}
        male = {"boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type


# ---------------------------------------------------------------------------
# Setting, Activity, Prize, Gear
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the meadow"
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
    weather: str = "sunny"
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    """The precious thing that gets hurt or soiled."""
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    """Protective item offered as a compromise."""
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


def _r_cut(world: World) -> list[str]:
    """Dancing on stones without protection causes a cut (blood)."""
    out = []
    for actor in world.characters():
        if actor.meters["blood"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("cut", item.id)
            if sig not in world.fired:
                world.fired.add(sig)
                item.meters["blood"] += 1
                item.meters["dirty"] += 1
                out.append(f"A tiny drop of blood showed on {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_gore_warn(world: World) -> list[str]:
    """Foreshadowing: the owl's warning about blood."""
    for actor in world.characters():
        if actor.type == "owl" and actor.memes["advice"] >= THRESHOLD:
            sig = ("warned", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out = ["The owl's words echoed: 'Stones can bite when feet do not wear wisdom.'"]
                return out
    return []


def _r_transform(world: World) -> list[str]:
    """When the child is hurt and has high bravery, she transforms into a butterfly."""
    for actor in world.characters():
        if actor.type in ("girl", "boy") and actor.meters["blood"] >= THRESHOLD and actor.memes["bravery"] >= THRESHOLD:
            sig = ("transform", actor.id)
            if sig not in world.fired:
                world.fired.add(sig)
                # remove old entity, add butterfly
                old = actor
                butterfly = Entity(
                    id=f"{actor.id}_butterfly",
                    kind="character",
                    type="butterfly",
                    label="a butterfly",
                    phrase="a beautiful butterfly with bright wings",
                    owner=actor.owner,
                    caretaker=actor.caretaker,
                    traits=["magical", "free"],
                    region="wings",
                    plural=False,
                )
                world.add(butterfly)
                # transfer emotional state
                butterfly.memes["joy"] = actor.memes["joy"] + 1
                # narrate
                return [f"Suddenly, {actor.id} shrank and lightened. Wings sprouted, "
                        f"and {actor.pronoun()} became {butterfly.label}. "
                        "The blood was gone, replaced by colors."]
    return []


CAUSAL_RULES = [
    Rule("cut", "physical", _r_cut),
    Rule("gore_warn", "foreshadow", _r_gore_warn),
    Rule("transform", "magic", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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
# Prediction (simpler: only gore, no workload)
# ---------------------------------------------------------------------------
def predict_gore(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "cut": bool(prize and prize.meters["blood"] >= THRESHOLD),
    }


# ---------------------------------------------------------------------------
# Verb functions
# ---------------------------------------------------------------------------
def activity_delight(activity: Activity) -> str:
    return {
        "dance_stones": "each step on the round stones felt like a tiny drum",
        "dance_grass": "the grass tickled and felt soft",
    }.get(activity.id, "the world felt full of rhythm")


def setting_detail(setting: Setting, activity: Activity) -> str:
    return f"The {setting.place} was peaceful, and the stones sparkled in the sun."


def prize_was_clean(hero: Entity, prize: Entity) -> str:
    return f"{hero.pronoun('possessive')} {prize.label} stayed clean"


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved to dance more than anything else in the world.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund}; {activity_delight(activity)}.")


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label_word} gave {hero.pronoun('object')} {prize.phrase} as a gift.")


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    prize.worn_by = hero.id
    world.say(f"{hero.id} adored {prize.phrase} and wore {prize.it()} every day.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One sunny morning, {hero.id} and {hero.pronoun('possessive')} {parent.label_word} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def foreshadow(world: World, owl: Entity, hero: Entity, activity: Activity) -> None:
    """The owl gives a cryptic warning."""
    world.say(f"An old owl perched on a branch and watched. '{hero.id}, be careful – the stones can bite when feet do not wear wisdom.'")
    owl.memes["advice"] += 1
    propagate(world)


def deny_warning(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} shook {hero.pronoun('possessive')} head. 'I am not afraid of stones.'")


def dance_on_stones(world: World, hero: Entity, activity: Activity) -> None:
    """The child dances and gets hurt."""
    _do_activity(world, hero, activity)


def accept_gear(world: World, hero: Entity, gear: Entity, parent: Entity) -> None:
    world.say(f"{parent.label_word} said, 'You must wear these sturdy shoes. They protect your feet.'")
    world.say(f"{hero.id} agreed and put on {gear.label}.")


def transform(world: World, hero: Entity) -> None:
    """The magical transformation after injury."""
    hero.memes["bravery"] += 1  # the hurt made her brave
    propagate(world)


# ---------------------------------------------------------------------------
# The fable screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mara", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, parent_type: str = "mother") -> World:
    world = World(setting)
    world.weather = "sunny"

    hero = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["daring", "loving"]),
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="her mother"))
    owl = world.add(Entity(id="Owl", kind="character", type="owl", label="a wise owl"))
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

    # Act 1: setup
    introduce(world, hero)
    loves_activity(world, hero, activity)
    buys(world, parent, hero, prize)
    loves_prize(world, hero, prize)

    # Act 2: conflict
    world.para()
    arrive(world, hero, parent, activity)

    # Foreshadowing
    foreshadow(world, owl, hero, activity)

    # The child disregards the warning
    deny_warning(world, hero)

    # Try to dance on stones (gore)
    dance_on_stones(world, hero, activity)

    # Act 3: resolution
    world.para()
    # If gear was used, no transformation; otherwise transformation
    # (We decide based on params: if prize is "shoes", gear protects; else no gear)
    # Simulate: if predict_gore says cut will happen and no gear, then transform
    pred = predict_gore(world, hero, activity, prize.id)
    if pred["cut"]:
        # No gear applied -> transformation
        transform(world, hero)
    else:
        # Gear was used -> safe dancing
        gear_entity = world.add(Entity(
            id="sturdy_shoes",
            kind="thing",
            type="shoes",
            label="sturdy shoes",
            phrase="a pair of sturdy shoes",
            owner=hero.id,
            caretaker=parent.id,
            protective=True,
            covers={"feet"},
            plural=True,
        ))
        gear_entity.worn_by = hero.id
        accept_gear(world, hero, gear_entity, parent)
        # then dance safely (no mess)
        world.say(f"{hero.id} danced on the stones safely, and {prize_was_clean(hero, prize)}.")

    # Record facts
    world.facts.update(hero=hero, parent=parent, owl=owl, prize=prize,
                       prize_cfg=prize_cfg, activity=activity, setting=setting)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", indoor=False, affords={"dance_stones"}),
}

ACTIVITIES = {
    "dance_stones": Activity(
        id="dance_stones",
        verb="dance on the shiny stones",
        gerund="dancing on the stones",
        rush="run to the stones",
        mess="blood",
        soil="bloody",
        zone={"feet"},
        weather="sunny",
        keyword="stones",
        tags={"stone", "blood"},
    ),
}

GEAR = [
    Gear(
        id="sturdy_shoes",
        label="sturdy shoes",
        covers={"feet"},
        guards={"blood"},
        prep="put on our sturdy shoes",
        tail="put on the sturdy shoes",
        plural=True,
    ),
]

PRIZES = {
    "shoes": Prize(
        label="shoes",
        phrase="pretty white shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
    "dress": Prize(
        label="dress",
        phrase="a new blue dress",
        type="dress",
        region="legs",
        genders={"girl"},
    ),
}

GIRL_NAMES = ["Mara", "Lena", "Suki", "Fia", "Tara"]
BOY_NAMES = ["Kai", "Riku", "Elio", "Oren", "Nilo"]
TRAITS = ["daring", "brave", "curious", "gentle", "stubborn"]


def valid_combos() -> list[tuple[str, str]]:
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
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "stone": [("Why are stones hard?",
               "Stones are made of rock, which is very hard because it is pressed together for thousands of years.")],
    "blood": [("What happens when you cut your foot?",
               "The skin breaks and a little blood comes out. The body can heal it with a scab.")],
    "butterfly": [("How does a butterfly grow?",
                   "A butterfly starts as a tiny egg, then becomes a caterpillar, spins a cocoon, and finally emerges as a beautiful butterfly.")],
    "owl": [("Why are owls wise?",
             "Owls have large eyes and sharp hearing, so they see and hear many things. In stories, they give good advice.")],
}

KNOWLEDGE_ORDER = ["stone", "blood", "butterfly", "owl"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, act = f["hero"], f["activity"]
    return [
        f'Write a short fable for children that includes the words "{act.keyword}" and "wings".',
        f"Tell a story where a {hero.type} named {hero.id} ignores a warning and learns a magical lesson.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pos = hero.pronoun("possessive")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about a {hero.type} named {hero.id} who loves {act.gerund}.",
        ),
        QAItem(
            question=f"What did {hero.id} love to do?",
            answer=f"{hero.id} loved {act.gerund}. {pos} {parent.label_word} gave {hero.pronoun('object')} {prize.phrase}.",
        ),
    ]
    # Check if transformation happened
    if any(e.type == "butterfly" for e in world.entities.values()):
        qa.append(QAItem(
            question=f"What happened after {hero.id} got a cut?",
            answer=f"{hero.id} was hurt, but because {hero.pronoun()} was brave, {hero.pronoun()} turned into a butterfly with bright wings.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set()
    if world.facts["activity"].id == "dance_stones":
        tags.add("stone")
        tags.add("blood")
    # if transformation occurred, add butterfly
    if any(e.type == "butterfly" for e in world.entities.values()):
        tags.add("butterfly")
        tags.add("owl")
    out = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
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
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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
        print(f"OK: clingo matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Interface functions
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable story world: a child, a warning, a transformation.")
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
            raise StoryError("No valid combination.")
    if args.gender and args.prize and args.gender not in PRIZES[args.prize].genders:
        raise StoryError(f"Gender {args.gender} not allowed for prize {args.prize}")

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)
              and (args.gender is None or args.gender in PRIZES[c[2]].genders)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")

    place, activity, prize_id = rng.choice(sorted(combos))
    prize = PRIZES[prize_id]
    gender = args.gender or rng.choice(sorted(prize.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize_id,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 PRIZES[params.prize], params.name, params.gender,
                 [params.trait, "daring"], params.parent)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:9} {act:8} {prize:8}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        # only one curated story for this small domain
        sample = generate(StoryParams(
            place="meadow",
            activity="dance_stones",
            prize="shoes",
            name="Mara",
            gender="girl",
            parent="mother",
            trait="daring",
        ))
        samples.append(sample)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
