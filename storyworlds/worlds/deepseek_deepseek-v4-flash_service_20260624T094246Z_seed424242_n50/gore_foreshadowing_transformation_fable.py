#!/usr/bin/env python3
"""
storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50/gore_foreshadowing_transformation_fable.py
================================================================================================================================

A standalone story world sketch for a fable about a rabbit who ignores a wise
owl's warning, eats forbidden glowing berries, and undergoes a thorny
transformation that draws blood (gore). The story includes foreshadowing (the
owl's prophecy) and a transformation that is reversed only when the rabbit
apologises, leaving a scar as a lasting lesson.

Domain: forest fable with mild gore and moral growth.
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

# Make the shared result containers importable when running directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# Mess kinds that the activity can cause.
MESS_KINDS = {"pricked", "blood", "thorny"}

# Body regions
REGIONS = {"mouth", "paws", "body"}


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"             # "character" | "thing"
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
        female = {"owl"}
        male = {"rabbit"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"owl": "owl", "rabbit": "rabbit"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain registries
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the forest"
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
    genders: set[str] = field(default_factory=lambda: {"rabbit"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


SETTINGS = {
    "forest": Setting(place="the forest", indoor=False, affords={"eat_berries"}),
}

ACTIVITIES = {
    "eat_berries": Activity(
        id="eat_berries",
        verb="eat the glowing berries",
        gerund="eating glowing berries",
        rush="reach for the berries",
        mess="pricked",
        soil="bleeding and thorny",
        zone={"mouth", "paws"},
        weather="",
        keyword="berries",
        tags={"berry", "thorn", "transformation"},
    ),
}

PRIZES = {
    "soft_fur": Prize(
        label="soft fur",
        phrase="his beautiful soft fur",
        type="fur",
        region="body",
        genders={"rabbit"},
    ),
}

GEAR = [
    Gear(
        id="healing_salve",
        label="a healing salve",
        covers={"body"},
        guards={"pricked", "blood", "thorny"},
        prep="use the healing salve I keep in the hollow tree",
        tail="flew to the hollow tree and fetched the healing salve",
    ),
]

RABBIT_NAMES = ["Briar", "Thistle", "Pip", "Flix", "Nutkin"]
OWL_NAMES = ["Hoot", "Sage", "Orm", "Elder"]
TRAITS = ["curious", "hungry", "stubborn", "brave"]


def valid_combos() -> list[tuple[str, str, str]]:
    """Only one combo in this domain, always valid."""
    return [("forest", "eat_berries", "soft_fur")]


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


def _r_thorns(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["pricked"] < THRESHOLD:
            continue
        # Transformation: thorns grow, blood appears
        if actor.meters["blood"] < THRESHOLD:
            continue
        sig = ("thorn_transform", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["thorny"] += 1
        # The prize (soft fur) is ruined
        for item in world.worn_items(actor):
            if item.region == "body":
                item.meters["dirty"] += 1
                item.meters["torn"] += 1
        out.append(
            f"Thorns burst through {actor.pronoun('possessive')} fur, "
            f"drawing tiny drops of blood."
        )
    return out


def _r_blood(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["pricked"] < THRESHOLD:
            continue
        sig = ("blood", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["blood"] += 1
        out.append(
            f"Red drops fell from {actor.pronoun('possessive')} paws "
            f"where the thorn had pricked."
        )
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="blood", tag="physical", apply=_r_blood),
    Rule(name="thorns", tag="physical", apply=_r_thorns),
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
# Prediction (used by the owl's warning)
# ---------------------------------------------------------------------------
def predict_transformation(world: World, actor: Entity, activity: Activity) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    thorny = sim.get(actor.id).meters.get("thorny", 0) >= THRESHOLD
    blood = sim.get(actor.id).meters.get("blood", 0) >= THRESHOLD
    return {"transformed": thorny, "bleeding": blood}


# ---------------------------------------------------------------------------
# Verbs
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "")
    desc = f"little {trait} {hero.type}".strip()
    world.say(f"{hero.id} was a {desc} who loved the taste of sweet things.")


def loves_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["love_play"] += 1
    world.say(
        f"More than anything, {hero.pronoun()} loved {activity.gerund}; "
        f"the berries shone like tiny suns and smelled of honey."
    )


def buys(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    # The owl didn't buy; the rabbit was born with soft fur. We skip this.
    pass


def loves_prize(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] += 1
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} was proud of {hero.pronoun('possessive')} {prize.label}, "
        f"which everyone said was the softest in the forest."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(
        f"One evening, {hero.id} hopped to the edge of the forest where the "
        f"glowing berries grew, and {parent.label_word} was perched on an old oak."
    )
    world.say("The air was still, and the berries hummed quietly.")


def wants(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id}'s nose twitched. {hero.pronoun('possessive').capitalize()} "
        f"paws reached out, but {parent.label_word} spread a wing."
    )


def warn(world: World, parent: Entity, hero: Entity, activity: Activity,
         prize: Entity) -> bool:
    pred = predict_transformation(world, hero, activity)
    if not pred["transformed"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.facts["predicted_bleeding"] = pred["bleeding"]
    clause = (
        f"The berry will prick you, then thorns will grow from your fur. "
        f"You will bleed, and your {prize.label} will be ruined."
    )
    world.say(
        f'"{clause}" said {parent.label_word}, {hero.pronoun("possessive")} "
        f'eyes full of knowing. "It tastes sweet, but it is a trick."'
    )
    return True


def defies(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"{hero.id} heard the warning, but the glow was too bright."
    )
    world.say(f"{hero.pronoun().capitalize()} {activity.rush},")


def grab_hand(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["grabbed_by"] += 1
    propagate(world, narrate=False)   # fires blood & thorn rules
    world.say(
        f"but the thorn caught {hero.pronoun('possessive')} paw first. "
        f"A sharp sting, and then the forest spun."
    )


def pout(world: World, hero: Entity, activity: Activity) -> None:
    if hero.memes["grabbed_by"] >= THRESHOLD:
        world.say(
            f'{hero.id} whimpered as thorns pushed through '
            f'{hero.pronoun("possessive")} fur. "I should have listened!" '
            f'cried {hero.pronoun("object")}.'
        )


def compromise(world: World, parent: Entity, hero: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = GEAR[0]  # only one gear: healing salve
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
    # Check if gear would prevent further damage (it won't reverse, but stops new thorns)
    # We'll accept: after using salve, thorns fall off, but scar remains.
    if predict_transformation(world, hero, activity)["transformed"]:
        # Even with salve, transformation already happened; but we still offer it.
        pass
    world.say(
        f'{parent.label_word.capitalize()} swooped down with a bundle of leaves. '
        f'"There is one way: {gear_def.prep}."'
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, prize: Entity,
           gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["love"] += 1
    hero.memes["conflict"] = 0.0
    # Apply salve – thorns recede, but scar remains (gore)
    hero.meters["thorny"] = max(hero.meters["thorny"] - 1, 0.0)
    hero.meters["blood"] = 0.0
    world.say(
        f"{hero.id} felt the salve cool on {hero.pronoun('possessive')} wounds. "
        f"The thorns softened and fell like dry leaves. "
        f"But a tiny red scar stayed on {hero.pronoun('possessive')} paw – "
        f"a reminder of the lesson."
    )
    world.say(
        f'"{parent.label_word.capitalize()}, I will never eat those berries again," '
        f'whispered {hero.id}. And they hopped home together under the moon.'
    )


# ---------------------------------------------------------------------------
# The screenplay
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Briar", hero_type: str = "rabbit",
         hero_traits: Optional[list[str]] = None,
         parent_type: str = "owl") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little"] + (hero_traits or ["curious", "stubborn"]),
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the wise owl",
    ))
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
    loves_prize(world, hero, prize)

    # Act 2: conflict
    world.para()
    arrive(world, hero, parent, activity)
    wants(world, hero, parent, activity)
    warn(world, parent, hero, activity, prize)
    defies(world, hero, activity)
    grab_hand(world, parent, hero, activity)

    # Act 3: resolution
    world.para()
    pout(world, hero, activity)
    gear_def = compromise(world, parent, hero, activity, prize)
    if gear_def:
        accept(world, parent, hero, activity, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, prize_cfg=prize_cfg,
                       activity=activity, setting=setting, gear=gear_def,
                       conflict=hero.memes["grabbed_by"] >= THRESHOLD,
                       resolved=gear_def is not None,
                       transformation=hero.meters["thorny"] >= THRESHOLD)
    return world


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
# QA generators
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "berry": [
        ("What are glowing berries?",
         "Glowing berries are special forest berries that shine with a golden "
         "light and smell very sweet. But they are dangerous to eat."),
    ],
    "thorn": [
        ("How can a thorn hurt you?",
         "A thorn is a sharp point on a plant. If it pricks your skin, it can "
         "draw blood and cause pain."),
    ],
    "transformation": [
        ("What does transformation mean?",
         "Transformation means changing shape or form. In the story, the rabbit "
         "grows thorns from his fur – that is a transformation."),
    ],
    "owl": [
        ("Why are owls often wise in stories?",
         "Owls are night creatures that see things others miss. In fables, they "
         "are wise teachers who warn about danger."),
    ],
    "blood": [
        ("Why does blood come when you are pricked?",
         "Blood is the red liquid inside your body. When you get a cut or prick, "
         "the blood comes out to clean the wound. It is part of healing."),
    ],
}
KNOWLEDGE_ORDER = ["berry", "thorn", "transformation", "owl", "blood"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act = f["hero"], f["parent"], f["activity"]
    kw = act.keyword
    return [
        f'Write a short fable for children about a rabbit and a wise owl, '
        f'including the word "{kw}".',
        f"Tell a story where a young rabbit ignores a warning about glowing "
        f"berries and suffers a thorny transformation, learning a lesson about obedience.",
        f'Write a simple story that uses the noun "{kw}" and ends with a scar that '
        f"reminds the character of the mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, act = f["hero"], f["parent"], f["prize"], f["activity"]
    pw = parent.label_word
    sub, obj, pos = (hero.pronoun("subject"), hero.pronoun("object"),
                     hero.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in hero.traits if t != "little"), hero.type)

    qa = [
        QAItem(
            question=f"Who is the story about in {place}?",
            answer=f"It is about a little {trait} {hero.type} named {hero.id} "
                   f"and a wise {pw}. They live in {place}."
        ),
        QAItem(
            question=f"What did {hero.id} love to do despite the warning?",
            answer=f"{trait.capitalize()} {hero.id} loved {act.gerund}. "
                   f"The berries glowed and smelled sweet, but {pw} warned {obj}."
        ),
        QAItem(
            question=f"What was {hero.id}'s softest treasure?",
            answer=f"{pos.capitalize()} {prize.label} was {pos} treasure, "
                   f"soft and beautiful."
        ),
    ]

    if f.get("transformation"):
        qa.append(QAItem(
            question=f"What happened to {hero.id} after eating the berry?",
            answer=f"Thorns grew from {pos} fur and drew blood. "
                   f"{sub} was hurt and {pos} {prize.label} was ruined. "
                   f"That was the transformation the {pw} had warned about."
        ))
    if f.get("resolved"):
        gear = f["gear"]
        qa.append(QAItem(
            question=f"How did the {gear.label} help {hero.id}?",
            answer=f"The {pw} used {gear.label} to soothe the wounds. "
                   f"The thorns fell off, but a small scar remained on {pos} paw "
                   f"as a reminder."
        ))
        qa.append(QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{sub} learned to listen to those who are wise and not to "
                   f"trust every sweet thing. The scar helped {obj} remember."
        ))

    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("gear"):
        tags.add(f["gear"].id)
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
# Trace dump
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


# ---------------------------------------------------------------------------
# CLI / main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fable story world: a rabbit, glowing berries, transformation, gore.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["rabbit"])
    ap.add_argument("--parent", choices=["owl"])
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true",
                    help="list compatible stories via clingo")
    ap.add_argument("--verify", action="store_true",
                    help="check ASP gate matches valid_combos()")
    ap.add_argument("--show-asp", action="store_true",
                    help="print ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    # Only one valid combo, always accepted.
    combos = valid_combos()
    place, activity, prize_id = rng.choice(sorted(combos))
    gender = "rabbit"
    name = args.name or rng.choice(RABBIT_NAMES)
    parent = args.parent or "owl"
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
    world = tell(SETTINGS[params.place],
                 ACTIVITIES[params.activity],
                 PRIZES[params.prize],
                 params.name,
                 params.gender,
                 [params.trait, "stubborn"],
                 params.parent)
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


# ---------------------------------------------------------------------------
# ASP twin (inline rules)
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A prize is at risk if the activity splashes its region.
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).

% Gear is a fix only if it guards the mess kind and covers the region.
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

    samples: list[StorySample] = []
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
